from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Literal

import requests

TOKEN = re.compile(r"[a-z0-9]+(?:[-.][a-z0-9]+)*")
WEIGHTS = {"title": 4.0, "keywords": 3.0, "subjects": 2.0, "abstract": 1.0, "authors": 2.0}


def default_site() -> str:
    site = os.environ.get("NCC_SITE") or json.loads(Path(__file__).with_name("site.json").read_text())["site"]
    return site.rstrip("/") + "/"


def tokens(text: str) -> list[str]:
    return TOKEN.findall(text.lower())


def rank(articles: list[dict], query: str, subject: str | None = None, limit: int = 10) -> list[dict]:
    terms = tokens(query)
    scored = []
    for article in articles:
        if article.get("status") != "published" or (subject and subject not in article.get("subjects", [])):
            continue
        fields = {
            "title": article.get("title") or "",
            "keywords": " ".join(article.get("keywords", [])),
            "subjects": " ".join(article.get("subjects", [])),
            "abstract": article.get("abstract") or "",
            "authors": " ".join(article.get("authors", [])),
        }
        score = 0.0
        for name, text in fields.items():
            words = tokens(text)
            score += WEIGHTS[name] * sum(words.count(t) for t in terms)
            if query.strip() and query.lower() in text.lower():
                score += WEIGHTS[name]
        if score > 0 or not terms:
            scored.append((score, article.get("published", ""), article))
    scored.sort(key=lambda s: (s[0], s[1]), reverse=True)
    return [dict(a) | {"score": round(s, 2)} for s, _, a in scored[:limit]]


class Journal:
    def __init__(self, site: str) -> None:
        self.site = site
        self._index: dict | None = None

    def get(self, path: str) -> requests.Response:
        resp = requests.get(self.site + path.lstrip("/"), timeout=30)
        resp.raise_for_status()
        return resp

    def index(self) -> dict:
        index = self._index
        if index is None:
            index = self._index = self.get("api/v1/index.json").json()
        return index

    def article(self, article_id: str, version: int | None = None) -> dict:
        key = f"{article_id}v{version}" if version else article_id
        if not re.fullmatch(r"\d{4}-\d{4}(?:v\d+)?", key):
            raise ValueError("article_id looks like 2026-0001; version is a positive integer")
        return self.get(f"api/v1/articles/{key}.json").json()


def create_server(site: str | None = None):
    from mcp.server.mcpserver import MCPServer

    journal = Journal(site or default_site())
    server = MCPServer(
        "notes-in-chemical-computation",
        instructions=(
            "Open knowledge base of Notes in Chemical Computation, a journal of short computational chemistry results. "
            "Articles are screened for scope and spam, not peer-reviewed. When you use an article, cite it with its "
            "version and DOI (cite_article) and respect its licence (usually CC BY 4.0)."
        ),
    )

    @server.tool()
    def search_articles(query: str, subject: str | None = None, limit: int = 10) -> list[dict]:
        """Search published articles by title, keywords, subjects, authors, and abstract. Optionally restrict to a
        subject id from list_subjects. Returns summaries with id, title, abstract, DOI, and URLs."""
        return rank(journal.index()["articles"], query, subject, max(1, min(limit, 50)))

    @server.tool()
    def get_article(article_id: str, version: int | None = None) -> dict:
        """Full record of one article: metadata, abstract, full text in Markdown, references, data and code
        availability, AI disclosure, citation formats, and version history. Omit version for the latest."""
        return journal.article(article_id, version)

    @server.tool()
    def list_subjects() -> list[dict]:
        """The journal's subjects with descriptions, keywords, and the ids of their articles."""
        return journal.index()["subjects"]

    @server.tool()
    def recent_articles(limit: int = 10) -> list[dict]:
        """Most recently published articles, newest first."""
        published = [a for a in journal.index()["articles"] if a.get("status") == "published"]
        return published[: max(1, min(limit, 50))]

    @server.tool()
    def cite_article(article_id: str, version: int | None = None, style: Literal["acs", "bibtex", "ris"] = "acs") -> str:
        """Citation for an article version in ACS, BibTeX, or RIS format."""
        record = journal.article(article_id, version)
        if not record.get("citation"):
            raise ValueError(f"{article_id} has no citation (status: {record.get('status')})")
        return record["citation"][style]

    @server.resource("ncc://articles/{article_id}")
    def article_markdown(article_id: str) -> str:
        """An article as Markdown with YAML front matter."""
        if not re.fullmatch(r"\d{4}-\d{4}(?:v\d+)?", article_id):
            raise ValueError("article_id looks like 2026-0001 or 2026-0001v2")
        return journal.get(f"articles/{article_id}.md").text

    return server


def main() -> None:
    create_server().run()


if __name__ == "__main__":
    main()
