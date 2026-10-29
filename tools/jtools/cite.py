from __future__ import annotations

import re

from . import config, model

LICENSE_URLS = {
    "CC-BY-4.0": "https://creativecommons.org/licenses/by/4.0/",
    "CC-BY-SA-4.0": "https://creativecommons.org/licenses/by-sa/4.0/",
    "CC0-1.0": "https://creativecommons.org/publicdomain/zero/1.0/",
}
LICENSE_NAMES = {"CC-BY-4.0": "CC BY 4.0", "CC-BY-SA-4.0": "CC BY-SA 4.0", "CC0-1.0": "CC0 1.0"}


def initials(given: str) -> str:
    parts = [p for p in re.split(r"[\s]+", given) if p]
    out = []
    for part in parts:
        out.append("-".join(f"{seg[0]}." for seg in part.split("-") if seg))
    return " ".join(out)


def acs_author(author: dict) -> str:
    if not author["given"]:
        return author["family"]
    return f"{author['family']}, {initials(author['given'])}"


def article_url(article: model.Article, version: int | None = None) -> str:
    prefix = "/examples/" if article.example else "/articles/"
    key = article.id.removeprefix("example-") if article.example else article.key(version)
    return config.site_url(f"{prefix}{key}/")


def citation_data(article: model.Article, version: model.Version) -> dict:
    j = config.journal()["journal"]
    authors, _ = model.resolve_authors(version.paper)
    doi = version.entry.get("doi")
    title = version.paper["title"]
    acs_names = "; ".join(acs_author(a) for a in authors)
    url = article_url(article, version.number)
    locator = f"https://doi.org/{doi}" if doi else url
    acs = f"{acs_names} {title}. {j['abbreviation']} {article.year}, {article.volume}, {article.number}. {locator}"
    bib_key = re.sub(r"[^a-z0-9]", "", authors[0]["family"].lower()) or "article"
    bib_authors = " and ".join(f"{a['family']}, {a['given']}".rstrip(", ") for a in authors)
    bib_fields = {
        "title": "{" + title + "}",
        "author": bib_authors,
        "journal": j["title"],
        "year": str(article.year),
        "volume": str(article.volume),
        "pages": article.number,
        "note": f"Version {version.number}",
        "url": url,
    }
    if doi:
        bib_fields["doi"] = doi
    bibtex = f"@article{{{bib_key}{article.year}_{article.number},\n" + ",\n".join(
        f"  {k} = {{{v}}}" for k, v in bib_fields.items()
    ) + "\n}\n"
    ris_lines = ["TY  - JOUR", f"TI  - {title}"]
    ris_lines += [f"AU  - {a['family']}, {a['given']}".rstrip(", ") for a in authors]
    ris_lines += [
        f"JO  - {j['title']}", f"JA  - {j['abbreviation']}", f"PY  - {article.year}",
        f"VL  - {article.volume}", f"SP  - {article.number}", f"UR  - {url}",
    ]
    if doi:
        ris_lines.append(f"DO  - {doi}")
    ris_lines.append("ER  - ")
    return {"acs": acs, "bibtex": bibtex, "ris": "\n".join(ris_lines) + "\n"}


def license_line(paper: dict, year: int) -> str:
    lic = paper.get("license", config.journal()["defaults"]["license"])
    return f"© {year} The Authors. Published under {LICENSE_NAMES[lic]} ({LICENSE_URLS[lic]})."


EXAMPLE_NOTE = "Example manuscript. This document demonstrates the submission format; its data are illustrative and it is not a published article."


def _ai_line(paper: dict) -> str | None:
    info = model.ai_info(paper)
    if info is None or info["level"] == "none":
        return None
    names = ", ".join(a["name"] for a in info["agents"])
    return f"{info['label']}" + (f" ({names})" if names else "")


def typst_meta(article: model.Article, version: model.Version, translated: bool = False, status_note: str | None = None) -> dict:
    j = config.journal()
    paper = version.paper
    tr = version.translation if translated else None
    authors, affiliations = model.resolve_authors(paper)
    corresponding = next((a.get("email") for a in authors if a.get("corresponding") and a.get("email")), None)
    title = tr["title"] if tr else paper["title"]
    notice = None
    if tr:
        notice = j["translation"]["disclaimer"].format(
            language=model.language_name(paper.get("language", "en")), model=tr.get("model", "AI")
        )
    return {
        "journal": {"title": j["journal"]["title"], "abbrev": j["journal"]["abbreviation"]},
        "title": title,
        "short_title": title if len(title) < 70 else title[:67].rstrip() + "...",
        "subtitle": paper.get("subtitle"),
        "type_label": model.ARTICLE_TYPES[paper["article_type"]],
        "authors": [
            {
                "name": a["name"],
                "sup": ",".join(str(i) for i in a["affiliation_indices"]),
                "corresponding": bool(a.get("corresponding")),
            }
            for a in authors
        ],
        "affiliations": affiliations,
        "corresponding_email": corresponding,
        "keywords": model.canonical_tags(paper["tags"]),
        "dates": {
            "submitted": article.record["submitted"],
            "accepted": article.record["accepted"],
            "published": version.entry["published"],
        },
        "version": version.number,
        "doi": version.entry.get("doi"),
        "citation": citation_data(article, version)["acs"],
        "license_line": license_line(paper, article.year),
        "ai_line": _ai_line(paper),
        "year": article.year,
        "volume": article.volume,
        "number": article.number,
        "url": article_url(article, version.number),
        "lang": "en" if tr else paper.get("language", "en").split("-")[0],
        "notice": notice,
        "status_note": status_note or (EXAMPLE_NOTE if article.example else None),
    }
