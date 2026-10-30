from __future__ import annotations

import datetime as dt
import os
import sys
import tempfile
import json
from pathlib import Path
from urllib.parse import quote

import requests

from . import assets, cite, config, model, pdf, render

LICENSES = {"CC-BY-4.0": "cc-by-4.0", "CC-BY-SA-4.0": "cc-by-sa-4.0", "CC0-1.0": "cc-zero"}
ISO639_3 = {"en": "eng", "ko": "kor", "ja": "jpn", "zh": "zho", "de": "deu", "fr": "fra", "es": "spa"}


class ZenodoError(RuntimeError):
    pass


class Client:
    def __init__(self) -> None:
        cfg = config.journal()["doi"]
        self.sandbox = bool(cfg["sandbox"])
        self.base = "https://sandbox.zenodo.org/api" if self.sandbox else "https://zenodo.org/api"
        token = os.environ.get("ZENODO_SANDBOX_TOKEN" if self.sandbox else "ZENODO_TOKEN")
        if not token:
            raise ZenodoError(f"set {'ZENODO_SANDBOX_TOKEN' if self.sandbox else 'ZENODO_TOKEN'}")
        self.session = requests.Session()
        self.session.headers["Authorization"] = f"Bearer {token}"

    def _call(self, method: str, url: str, **kwargs) -> dict:
        if not url.startswith("http"):
            url = self.base + url
        resp = self.session.request(method, url, timeout=120, **kwargs)
        if resp.status_code >= 400:
            raise ZenodoError(f"{method} {url} -> {resp.status_code}: {resp.text[:800]}")
        return resp.json() if resp.content else {}

    def create(self) -> dict:
        return self._call("POST", "/deposit/depositions", json={})

    def new_version(self, deposition_id: int) -> dict:
        resp = self._call("POST", f"/deposit/depositions/{deposition_id}/actions/newversion")
        draft = self._call("GET", resp["links"]["latest_draft"])
        for f in draft.get("files", []):
            self._call("DELETE", f"/deposit/depositions/{draft['id']}/files/{f['id']}")
        return draft

    def reserve_doi(self, draft: dict) -> str:
        reserved = draft.get("metadata", {}).get("prereserve_doi", {}).get("doi")
        if reserved:
            return reserved
        metadata = {**draft.get("metadata", {}), "prereserve_doi": True}
        metadata.pop("doi", None)
        updated = self._call("PUT", f"/deposit/depositions/{draft['id']}", json={"metadata": metadata})
        return updated["metadata"]["prereserve_doi"]["doi"]

    def upload(self, draft: dict, path: Path, name: str | None = None) -> None:
        with open(path, "rb") as fh:
            self._call("PUT", f"{draft['links']['bucket']}/{name or path.name}", data=fh)

    def set_metadata(self, deposition_id: int, metadata: dict) -> dict:
        return self._call("PUT", f"/deposit/depositions/{deposition_id}", json={"metadata": metadata})

    def publish(self, deposition_id: int) -> dict:
        return self._call("POST", f"/deposit/depositions/{deposition_id}/actions/publish")

    def edit(self, deposition_id: int) -> dict:
        return self._call("POST", f"/deposit/depositions/{deposition_id}/actions/edit")


def deposition_metadata(article: model.Article, version: model.Version, doi: str) -> dict:
    j = config.journal()
    paper = version.paper
    authors, affiliations = model.resolve_authors(paper)
    creators = []
    for a in authors:
        creator = {"name": f"{a['family']}, {a['given']}".rstrip(", ")}
        if a["affiliation_indices"]:
            creator["affiliation"] = "; ".join(affiliations[i - 1] for i in a["affiliation_indices"])
        if a.get("orcid"):
            creator["orcid"] = a["orcid"]
        creators.append(creator)
    abstract = render.pandoc(paper["abstract"], "html5")
    notes = f"Published in {j['journal']['title']} ({cite.article_url(article, version.number)})."
    if version.translation:
        notes += " An AI-generated English translation is included and may contain mistranslations."
    related = [{"identifier": cite.article_url(article, version.number), "relation": "isIdenticalTo", "resource_type": "publication-article"}]
    if paper.get("code_availability", "").startswith("http"):
        related.append({"identifier": paper["code_availability"].split()[0], "relation": "isSupplementedBy", "resource_type": "software"})
    for item in paper.get("supporting_information", []):
        if "url" in item:
            related.append({"identifier": item["url"], "relation": "isSupplementedBy"})
    metadata = {
        "upload_type": "publication",
        "publication_type": "article",
        "title": paper["title"],
        "creators": creators,
        "description": abstract,
        "access_right": "open",
        "license": LICENSES[paper.get("license", j["defaults"]["license"])],
        "keywords": model.canonical_tags(paper["tags"]),
        "publication_date": version.entry["published"],
        "journal_title": j["journal"]["title"],
        "journal_volume": str(article.volume),
        "journal_pages": article.number,
        "version": f"v{version.number}",
        "language": ISO639_3.get(paper.get("language", "en").split("-")[0], "eng"),
        "related_identifiers": related,
        "notes": notes,
        "doi": doi,
    }
    if j["doi"].get("community"):
        metadata["communities"] = [{"identifier": j["doi"]["community"]}]
    return metadata


def due_versions(today: dt.date | None = None) -> list[tuple[model.Article, model.Version]]:
    cfg = config.journal()["doi"]
    if not cfg["enabled"]:
        return []
    today = today or dt.date.today()
    delay = dt.timedelta(days=int(cfg["delay_days"]))
    due = []
    for article in model.discover_articles():
        if article.record["status"] != "published":
            continue
        for version in article.versions:
            if version.entry.get("doi") or not version.paper.get("mint_doi", True):
                continue
            if dt.date.fromisoformat(version.entry["published"]) + delay <= today:
                due.append((article, version))
    return due


def _save_record(article: model.Article) -> None:
    config.dump_yaml(article.record, article.dir / "record.yml")


def mint(client: Client, article: model.Article, version: model.Version) -> str:
    problems = assets.file_problems(version.dir)
    if problems:
        raise ZenodoError("; ".join(problems))
    parent = next((v.entry["zenodo_id"] for v in reversed(article.versions[: version.number - 1]) if v.entry.get("zenodo_id")), None)
    draft = client.new_version(parent) if parent else client.create()
    doi = client.reserve_doi(draft)
    version.entry["doi"] = doi
    with tempfile.TemporaryDirectory() as tmp:
        tmpdir = Path(tmp)
        main_pdf = pdf.build_pdf(article, version, tmpdir / f"{article.key(version.number)}.pdf")
        client.upload(draft, main_pdf)
        if version.translation:
            en_pdf = pdf.build_pdf(article, version, tmpdir / f"{article.key(version.number)}-en.pdf", translated=True)
            client.upload(draft, en_pdf)
        client.upload(draft, version.dir / "paper.yml")
        manifest = {}
        for path in assets.manuscript_files(version.dir):
            rel = path.relative_to(version.dir).as_posix()
            name = "source--" + quote(rel, safe="")
            manifest[name] = rel
            client.upload(draft, path, name=name)
        manifest_path = tmpdir / "source-manifest.json"
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        client.upload(draft, manifest_path)
        for path in version.dir.glob("translation.*.yml"):
            client.upload(draft, path)
    client.set_metadata(draft["id"], deposition_metadata(article, version, doi))
    published = client.publish(draft["id"])
    version.entry["doi"] = published.get("doi", doi)
    version.entry["zenodo_id"] = published["id"]
    article.record["concept_doi"] = published.get("conceptdoi") or article.record.get("concept_doi")
    concept = published.get("conceptrecid")
    article.record["zenodo_concept_id"] = int(concept) if concept else article.record.get("zenodo_concept_id")
    _save_record(article)
    return version.entry["doi"]


def mint_due(dry_run: bool = False) -> list[str]:
    due = due_versions()
    if not due:
        print("no versions are due for a DOI", file=sys.stderr)
        return []
    if dry_run:
        for article, version in due:
            print(f"would mint DOI for {article.key(version.number)} (published {version.entry['published']})")
        return []
    client = Client()
    minted = []
    for article, version in due:
        doi = mint(client, article, version)
        print(f"minted {doi} for {article.key(version.number)}")
        minted.append(doi)
    return minted


def mark_withdrawn(article_id: str) -> None:
    article = model.load_article(config.PAPERS / article_id)
    reason = article.record.get("withdrawn", {}).get("reason", "Withdrawn by the authors.")
    client = Client()
    for version in article.versions:
        dep_id = version.entry.get("zenodo_id")
        if not dep_id:
            continue
        draft = client.edit(dep_id)
        metadata = dict(draft["metadata"])
        if not metadata["title"].startswith("[WITHDRAWN]"):
            metadata["title"] = f"[WITHDRAWN] {metadata['title']}"
        metadata["notes"] = f"This article was withdrawn on {article.record['withdrawn']['date']}. Reason: {reason}"
        client.set_metadata(dep_id, metadata)
        client.publish(dep_id)
        print(f"marked Zenodo record {dep_id} as withdrawn")
    print(
        "Zenodo keeps published files. Record removal is governed by Zenodo's current policies; "
        "the journal does not guarantee a deletion window.",
        file=sys.stderr,
    )
