from __future__ import annotations

import datetime as dt
import json
import re
import shutil
from pathlib import Path

from . import config, model, render, review

API_VERSION = "1"
FENCE = re.compile(r"^\s*(```|~~~)")
HEADING = re.compile(r"^(#{1,5}) ")


def _abs(path: str | None) -> str | None:
    if not path:
        return None
    return config.journal()["site"]["url"].rstrip("/") + path


def demote_headings(markdown: str) -> str:
    out, fenced = [], False
    for line in markdown.splitlines():
        if FENCE.match(line):
            fenced = not fenced
        out.append(f"#{line}" if not fenced and HEADING.match(line) else line)
    return "\n".join(out)


def _text(version: model.Version, overrides: dict | None = None) -> str:
    if overrides and version.body_kind in ("sections", "markdown"):
        return render.body_markdown(version.paper, version.dir, overrides)
    return review.body_text(version.paper, version.dir, 10**7)


def article_record(article: model.Article, version: model.Version, exported: dict) -> dict:
    paper = version.paper
    data = exported["versions"][version.number - 1]
    withdrawn = article.record["status"] == "withdrawn"
    record = {
        "api_version": API_VERSION,
        "id": article.id,
        "version": version.number,
        "latest_version": article.latest.number,
        "status": article.record["status"],
        "title": paper["title"],
        "subtitle": paper.get("subtitle"),
        "article_type": paper["article_type"],
        "language": paper.get("language", "en"),
        "authors": [{k: a.get(k) for k in ("name", "orcid", "github")} for a in data["authors"]],
        "affiliations": data["affiliations"],
        "subjects": exported["subjects"],
        "keywords": data["tags"],
        "submitted": article.record["submitted"],
        "accepted": article.record["accepted"],
        "published": data["published"],
        "doi": data["doi"],
        "concept_doi": article.record.get("concept_doi"),
        "url": data["url"],
        "json": config.site_url(f"/api/v1/articles/{article.key(version.number)}.json"),
        "markdown": config.site_url(f"/articles/{article.key(version.number)}.md"),
        "license": data["license"],
        "review": "editorial content, not screened" if paper["article_type"] == "editorial" else "screening, not peer review",
        "versions": [
            {"version": v.number, "published": v.entry["published"], "doi": v.entry.get("doi"),
             "url": exported["versions"][v.number - 1]["url"], "changelog": v.entry.get("changelog")}
            for v in article.versions
        ],
    }
    if withdrawn:
        return record | {"withdrawn": article.record.get("withdrawn")}
    tr = version.translation
    record |= {
        "pdf": _abs(data.get("pdf")),
        "citation": data.get("cite"),
        "abstract": str(paper["abstract"]).strip(),
        "text": _text(version),
        "references": [{k: r[k] for k in ("id", "doi", "title") if k in r} for r in paper.get("references", [])],
        "data_availability": paper.get("data_availability"),
        "code_availability": paper.get("code_availability"),
        "ai_use": paper.get("ai_use"),
        "ai_contributions": paper.get("ai_contributions"),
        "translation": None if not tr else {
            "language": config.journal()["translation"]["target"],
            "machine_translated": tr.get("machine_translated", True),
            "model": tr.get("model"),
            "title": tr["title"],
            "abstract": str(tr["abstract"]).strip(),
            "text": _text(version, {k: tr[k] for k in ("sections",) if k in tr}) if "sections" in tr else None,
        },
    }
    return record


def to_markdown(record: dict) -> str:
    front = {k: record.get(k) for k in ("id", "version", "title", "doi", "url", "license", "published", "language", "review")}
    front["authors"] = [a["name"] for a in record["authors"]]
    front["subjects"] = record["subjects"]
    front["keywords"] = record["keywords"]
    lines = ["---", config.dump_yaml(front).rstrip(), "---", "", f"# {record['title']}", ""]
    lines.append(", ".join(front["authors"]))
    if record.get("citation"):
        lines += ["", f"Cite as: {record['citation']['acs']}"]
    if record["status"] == "withdrawn":
        reason = (record.get("withdrawn") or {}).get("reason", "")
        return "\n".join(lines + ["", f"This article was withdrawn. {reason}".strip(), ""])
    tr = record.get("translation")
    if tr:
        lines += ["", f"An English machine translation ({tr['model']}) is available; the original-language text below is the version of record."]
    lines += ["", "## Abstract", "", record["abstract"], "", demote_headings(record["text"]).strip()]
    if record["references"]:
        lines += ["", "## References", ""]
        lines += [f"- [{r['id']}] " + (f"https://doi.org/{r['doi']}" if r.get("doi") else r.get("title", "")) for r in record["references"]]
    return "\n".join(lines).rstrip() + "\n"


def summary(record: dict) -> dict:
    keys = ("id", "version", "status", "title", "article_type", "language", "subjects", "keywords", "published",
            "doi", "url", "json", "markdown", "license", "review")
    out = {k: record.get(k) for k in keys}
    out["authors"] = [a["name"] for a in record["authors"]]
    out["abstract"] = record.get("abstract")
    out["ai_level"] = (record.get("ai_contributions") or {}).get("level")
    return out


def build(articles: list[model.Article], exported: list[dict]) -> int:
    public = config.SITE / "public"
    api = public / "api" / "v1"
    md_dir = public / "articles"
    for path in (api, md_dir):
        if path.exists():
            shutil.rmtree(path)
    (api / "articles").mkdir(parents=True)
    md_dir.mkdir(parents=True)
    by_id = {a["id"]: a for a in exported}
    j = config.journal()
    latest_records = []
    for article in articles:
        exp = by_id[article.id]
        for version in article.versions:
            record = article_record(article, version, exp)
            key = article.key(version.number)
            (api / "articles" / f"{key}.json").write_text(json.dumps(record, ensure_ascii=False, indent=1), encoding="utf-8")
            (md_dir / f"{key}.md").write_text(to_markdown(record), encoding="utf-8")
            if version.number == article.latest.number:
                (api / "articles" / f"{article.id}.json").write_text(json.dumps(record, ensure_ascii=False, indent=1), encoding="utf-8")
                (md_dir / f"{article.id}.md").write_text(to_markdown(record), encoding="utf-8")
                latest_records.append(record)
    latest_records.sort(key=lambda r: (r["published"], r["id"]), reverse=True)
    index = {
        "api_version": API_VERSION,
        "generated": dt.date.today().isoformat(),
        "journal": {"title": j["journal"]["title"], "abbreviation": j["journal"]["abbreviation"], "site": config.site_url("/"),
                    "policy": config.site_url("/policy/#knowledge-base"), "default_license": j["defaults"]["license"]},
        "subjects": [{k: s[k] for k in ("id", "name", "description", "tags")}
                     | {"articles": [r["id"] for r in latest_records if s["id"] in r["subjects"] and r["status"] == "published"]}
                     for s in j["subjects"]],
        "articles": [summary(r) for r in latest_records],
    }
    (api / "index.json").write_text(json.dumps(index, ensure_ascii=False, indent=1), encoding="utf-8")
    full = [f"# {j['journal']['title']}: full text of published articles",
            "",
            f"Generated {index['generated']}. Each article is reusable under its licence with attribution; cite the version and DOI.",
            f"Index: {config.site_url('/api/v1/index.json')}"]
    for record in latest_records:
        if record["status"] == "published":
            full += ["", "---", "", to_markdown(record).strip()]
    (public / "llms-full.txt").write_text("\n".join(full) + "\n", encoding="utf-8")
    return len(latest_records)
