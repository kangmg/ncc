from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import requests

from . import config

CSL_ACCEPT = "application/vnd.citationstyles.csl+json"
NAME_FIELDS = {"author", "editor"}
DATE_FIELDS = {"issued"}
TEXT_FIELDS = {
    "type", "title", "container-title", "container-title-short", "volume", "issue", "page",
    "DOI", "URL", "publisher", "number", "note", "edition", "genre",
}


def clean_csl(item: dict) -> dict:
    out = {}
    for key, value in item.items():
        if key in NAME_FIELDS or key in DATE_FIELDS:
            out[key] = value
        elif key in TEXT_FIELDS:
            if isinstance(value, list):
                value = value[0] if value else ""
            if value != "":
                out[key] = value
    return out


def _cache_path(doi: str) -> Path:
    digest = hashlib.sha1(doi.lower().encode()).hexdigest()[:16]
    return config.CACHE / "doi" / f"{digest}.json"


def resolve_doi(doi: str) -> dict | None:
    cache = _cache_path(doi)
    if cache.exists():
        return json.loads(cache.read_text(encoding="utf-8"))
    try:
        resp = requests.get(f"https://doi.org/{doi}", headers={"Accept": CSL_ACCEPT}, timeout=30)
        resp.raise_for_status()
        data = resp.json()
    except (requests.RequestException, ValueError) as exc:
        print(f"warning: could not resolve DOI {doi}: {exc}", file=sys.stderr)
        return None
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return data


def csl_items(paper: dict) -> list[dict]:
    items = []
    for ref in paper.get("references", []):
        extra = {k: v for k, v in ref.items() if k not in ("id", "doi", "text")}
        if ref.get("doi"):
            resolved = clean_csl(resolve_doi(ref["doi"]) or {"type": "article-journal", "title": ref["doi"]})
            item = {**resolved, **extra, "id": ref["id"], "DOI": ref["doi"]}
        elif ref.get("text"):
            item = {"type": "article", "title": ref["text"], **extra, "id": ref["id"]}
        else:
            item = {"type": "article", **extra, "id": ref["id"]}
        items.append(item)
    return items


def bibliography_args(paper: dict, base: Path, workdir: Path) -> list[str]:
    args: list[str] = []
    items = csl_items(paper)
    if items:
        path = workdir / "references.json"
        path.write_text(json.dumps(items, ensure_ascii=False, indent=1), encoding="utf-8")
        args += ["--bibliography", str(path)]
    if paper.get("bibliography"):
        args += ["--bibliography", str(base / paper["bibliography"])]
    return args
