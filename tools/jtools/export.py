from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

from . import assets, cite, config, knowledge, model, pdf, render


def _write_json(name: str, data) -> None:
    config.GENERATED.mkdir(parents=True, exist_ok=True)
    (config.GENERATED / name).write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")


def _public_dir(article: model.Article, version: model.Version) -> tuple[Path, str]:
    rel = f"/papers/{article.id}/v{version.number}/"
    return config.SITE / "public" / rel.strip("/"), config.base_path(rel)


def _copy_public(version: model.Version, dest: Path) -> None:
    problems = assets.file_problems(version.dir)
    if problems:
        raise ValueError("; ".join(problems))
    for item in assets.manuscript_files(version.dir):
        if item.suffix.lower() not in {".yml", ".yaml", ".typ"}:
            target = dest / item.relative_to(version.dir)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, target)


def related_articles(tagged: dict[str, list[str]], limit: int = 3) -> dict[str, list[str]]:
    def jaccard(a: set[str], b: set[str]) -> float:
        return len(a & b) / len(a | b) if a | b else 0.0

    related = {}
    for key, tags in tagged.items():
        scored = [(jaccard(set(tags), set(other)), k) for k, other in tagged.items() if k != key]
        related[key] = [k for score, k in sorted(scored, key=lambda s: (-s[0], s[1])) if score > 0][:limit]
    return related


def export_version(article: model.Article, version: model.Version, with_pdf: bool) -> dict:
    paper = version.paper
    authors, affiliations = model.resolve_authors(paper)
    withdrawn = article.record["status"] == "withdrawn"
    data = {
        "version": version.number,
        "key": article.key(version.number),
        "published": version.entry["published"],
        "doi": version.entry.get("doi"),
        "changelog": version.entry.get("changelog") or paper.get("changelog"),
        "title": paper["title"],
        "subtitle": paper.get("subtitle"),
        "article_type": paper["article_type"],
        "type_label": model.ARTICLE_TYPES[paper["article_type"]],
        "language": paper.get("language", "en"),
        "language_name": model.language_name(paper.get("language", "en")),
        "authors": [
            {k: a.get(k) for k in ("name", "github", "orcid", "corresponding", "equal_contribution")}
            | {"affiliations": a["affiliation_indices"]}
            for a in authors
        ],
        "affiliations": affiliations,
        "tags": model.canonical_tags(paper["tags"]),
        "license": paper.get("license", config.journal()["defaults"]["license"]),
        "body_kind": version.body_kind,
        "url": cite.article_url(article, version.number),
        "ai": model.ai_info(paper),
    }
    if withdrawn:
        return data

    dest, public = _public_dir(article, version)
    _copy_public(version, dest)
    workdir = config.BUILD / "html" / article.key(version.number)
    html = render.render_html(paper, version.dir, workdir, public)
    data |= {
        "abstract_html": html["abstract"],
        "body_html": html["body"],
        "toc_graphic": public + paper["toc_graphic"] if paper.get("toc_graphic") else None,
        "cite": cite.citation_data(article, version),
        "supporting_information": [
            {"url": i["url"] if "url" in i else config.site_url(f"/papers/{article.id}/v{version.number}/{i['file']}"),
             "file": i.get("file", i["description"]), "description": i["description"]}
            for i in paper.get("supporting_information", [])
        ],
        "mint_doi": paper.get("mint_doi", True),
        "pdf": None,
        "translation": None,
    }
    if with_pdf:
        pdf_name = f"{article.key(version.number)}.pdf"
        pdf.build_pdf(article, version, dest / pdf_name)
        data["pdf"] = public + pdf_name
    if version.translation:
        tr = version.translation
        overrides = pdf.translation_overrides(version)
        tr_html = render.render_html(paper, version.dir, workdir / "translation", public, overrides)
        disclaimer = config.journal()["translation"]["disclaimer"].format(
            language=data["language_name"], model=tr.get("model", "AI")
        )
        data["translation"] = {
            "language": config.journal()["translation"]["target"],
            "title": tr["title"],
            "abstract_html": tr_html["abstract"],
            "body_html": tr_html["body"] if version.body_kind in ("sections", "markdown") else "",
            "model": tr.get("model"),
            "date": tr.get("date"),
            "machine_translated": tr.get("machine_translated", True),
            "disclaimer": disclaimer,
            "pdf": None,
        }
        if with_pdf:
            pdf_name = f"{article.key(version.number)}-en.pdf"
            pdf.build_pdf(article, version, dest / pdf_name, translated=True)
            data["translation"]["pdf"] = public + pdf_name
    return data


def export_article(article: model.Article, with_pdf: bool) -> dict:
    record = article.record
    versions = [export_version(article, v, with_pdf) for v in article.versions]
    return {
        "id": article.id,
        "example": article.example,
        "status": record["status"],
        "withdrawn": record.get("withdrawn"),
        "submitted": record["submitted"],
        "accepted": record["accepted"],
        "issue": record.get("issue"),
        "concept_doi": record.get("concept_doi"),
        "year": article.year,
        "volume": article.volume,
        "number": article.number,
        "latest": article.latest.number,
        "versions": versions,
    }


def build_all(with_pdf: bool = True) -> None:
    for path in (config.GENERATED, config.PUBLIC_PAPERS):
        if path.exists():
            shutil.rmtree(path)
    articles = model.discover_articles()
    examples = model.discover_examples()

    exported = []
    for article in articles + examples:
        print(f"building {article.id}", file=sys.stderr)
        exported.append(export_article(article, with_pdf))

    real = [a for a in exported if not a["example"] and a["status"] == "published"]
    tagged = {a["id"]: a["versions"][-1]["tags"] for a in real}
    related = related_articles(tagged)
    for a in exported:
        a["subjects"] = model.subjects_for(a["versions"][-1]["tags"])
        a["related"] = related.get(a["id"], [])
    subjects = [
        s | {"articles": [a["id"] for a in real if s["id"] in a["subjects"]]}
        for s in config.journal()["subjects"]
    ]

    authors: dict[str, dict] = {}
    for a in exported:
        if a["example"]:
            continue
        for person in a["versions"][-1]["authors"]:
            handle = person.get("github")
            if handle:
                entry = authors.setdefault(handle.lower(), {"github": handle, "name": person["name"], "orcid": person.get("orcid"), "articles": []})
                entry["articles"].append(a["id"])

    j = config.journal()
    pages = {}
    for name, filename in (("guide", "AUTHOR_GUIDE.md"), ("policy", "POLICY.md"), ("agents", "AGENT_GUIDE.md"),
                           ("why", "WHY.md"), ("knowledge", "KNOWLEDGE_BASE.md")):
        path = config.ROOT / filename
        if path.exists():
            pages[name] = render.render_document(path)

    knowledge.build(articles, [a for a in exported if not a["example"]])
    _write_json("articles.json", [a for a in exported if not a["example"]])
    _write_json("examples.json", [a for a in exported if a["example"]])
    _write_json("subjects.json", subjects)
    _write_json("authors.json", sorted(authors.values(), key=lambda x: x["name"]))
    _write_json("pages.json", pages)
    _write_json("journal.json", {
        "journal": j["journal"], "site": j["site"], "github": j["github"], "seed_tags": j["seed_tags"],
        "comments": j["comments"], "doi": {"delay_days": j["doi"]["delay_days"], "sandbox": j["doi"]["sandbox"]},
        "translation": {"target": j["translation"]["target"], "model": j["translation"]["model"]},
    })
    print(f"exported {len(articles)} articles, {len(examples)} examples", file=sys.stderr)
