from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from . import config

ARTICLE_TYPES = {
    "research-article": "Research Article",
    "letter": "Letter",
    "computational-note": "Computational Note",
    "software": "Software",
    "negative-result": "Negative Result",
    "tutorial": "Tutorial",
    "perspective": "Perspective",
    "editorial": "Editorial",
}

LANGUAGE_NAMES = {
    "en": "English", "ko": "Korean", "ja": "Japanese", "zh": "Chinese", "de": "German",
    "fr": "French", "es": "Spanish", "it": "Italian", "pt": "Portuguese", "ru": "Russian",
    "vi": "Vietnamese", "th": "Thai", "id": "Indonesian", "hi": "Hindi", "ar": "Arabic",
}

AI_LEVELS = {
    "none": "No AI involvement",
    "assisted": "AI-assisted",
    "substantial": "Substantial AI contribution",
    "agent-led": "Agent-led",
}

ID_RE = re.compile(r"^\d{4}-\d{4}$")
_CJK = re.compile(r"[\u3040-\u30ff\u3400-\u9fff\uac00-\ud7af]")


@dataclass
class Version:
    number: int
    dir: Path
    paper: dict
    entry: dict
    translation: dict | None = None

    @property
    def language(self) -> str:
        return self.paper.get("language", "en")

    @property
    def body_kind(self) -> str:
        if "sections" in self.paper:
            return "sections"
        if "pdf" in self.paper:
            return "pdf"
        return "typst" if self.paper["body_file"].endswith(".typ") else "markdown"


@dataclass
class Article:
    id: str
    dir: Path
    record: dict
    versions: list[Version] = field(default_factory=list)
    example: bool = False

    @property
    def latest(self) -> Version:
        return self.versions[-1]

    @property
    def year(self) -> int:
        if self.example:
            return int(config.journal()["journal"]["founded"])
        return int(self.id.split("-")[0])

    @property
    def number(self) -> str:
        return "e000" if self.example else self.id.split("-")[1]

    @property
    def volume(self) -> int:
        return self.year - int(config.journal()["journal"]["founded"]) + 1

    def key(self, version: int | None = None) -> str:
        return self.id if version is None else f"{self.id}v{version}"


def language_name(code: str) -> str:
    return LANGUAGE_NAMES.get(code.split("-")[0], code)


def load_translation(version_dir: Path) -> dict | None:
    target = config.journal()["translation"]["target"]
    path = version_dir / f"translation.{target}.yml"
    return config.load_yaml(path) if path.exists() else None


def load_article(article_dir: Path) -> Article:
    record = config.load_yaml(article_dir / "record.yml")
    article = Article(id=record["id"], dir=article_dir, record=record)
    for entry in sorted(record["versions"], key=lambda e: e["version"]):
        vdir = article_dir / f"v{entry['version']}"
        paper = config.load_yaml(vdir / "paper.yml")
        article.versions.append(Version(entry["version"], vdir, paper, entry, load_translation(vdir)))
    return article


def discover_articles() -> list[Article]:
    if not config.PAPERS.exists():
        return []
    dirs = sorted(d for d in config.PAPERS.iterdir() if d.is_dir() and ID_RE.match(d.name))
    return [load_article(d) for d in dirs]


def load_example(example_dir: Path) -> Article:
    paper = config.load_yaml(example_dir / "paper.yml")
    entry = {"version": 1, "published": "2026-01-01", "doi": None, "changelog": "Example."}
    record = {
        "id": f"example-{example_dir.name}",
        "status": "published",
        "submitted": "2026-01-01",
        "accepted": "2026-01-01",
        "versions": [entry],
    }
    version = Version(1, example_dir, paper, entry, load_translation(example_dir))
    return Article(id=record["id"], dir=example_dir, record=record, versions=[version], example=True)


def discover_examples() -> list[Article]:
    if not config.EXAMPLES.exists():
        return []
    return [load_example(d) for d in sorted(config.EXAMPLES.iterdir()) if (d / "paper.yml").exists()]


def canonical_tag(tag: str) -> str:
    return config.tag_aliases().get(tag.strip().lower(), tag.strip())


def canonical_tags(tags: list[str]) -> list[str]:
    seen: list[str] = []
    for tag in tags:
        name = canonical_tag(tag)
        if name not in seen:
            seen.append(name)
    return seen


def split_name(author: dict) -> tuple[str, str]:
    if author.get("family"):
        return author.get("given", ""), author["family"]
    name = author["name"].strip()
    if " " in name:
        given, family = name.rsplit(" ", 1)
        return given, family
    if _CJK.search(name) and len(name) > 1:
        return name[1:], name[0]
    return "", name


def resolve_authors(paper: dict) -> tuple[list[dict], list[str]]:
    """Authors with 1-based affiliation indices, plus the ordered affiliation texts."""
    table = {str(k): v for k, v in (paper.get("affiliations") or {}).items()}
    ordered: list[str] = []
    authors = []
    for author in paper["authors"]:
        indices = []
        for ref in author.get("affiliations", []):
            text = table.get(str(ref), str(ref))
            if text not in ordered:
                ordered.append(text)
            indices.append(ordered.index(text) + 1)
        given, family = split_name(author)
        authors.append({**author, "given": given, "family": family, "affiliation_indices": indices})
    return authors, ordered


def subjects_for(tags: list[str]) -> list[str]:
    tagset = set(canonical_tags(tags))
    return [s["id"] for s in config.journal()["subjects"] if tagset.intersection(s["tags"])]


def ai_info(paper: dict) -> dict | None:
    ai = paper.get("ai_contributions")
    if not ai:
        return None
    return {
        "level": ai["level"],
        "label": AI_LEVELS[ai["level"]],
        "agents": [{k: a.get(k) for k in ("name", "model", "provider", "github")} | {"roles": a["roles"]}
                   for a in ai.get("agents", [])],
        "oversight": ai.get("oversight"),
        "logs": ai.get("logs"),
    }


def ai_statement(paper: dict) -> str | None:
    info = ai_info(paper)
    if info is None:
        return None
    lines = [f"**Level:** {info['label']}."]
    if info["agents"]:
        described = []
        for agent in info["agents"]:
            detail = ", ".join(x for x in (agent["model"], agent["provider"]) if x)
            described.append(f"{agent['name']}{f' ({detail})' if detail else ''}: {', '.join(agent['roles'])}")
        lines.append("**Agents:** " + "; ".join(described) + ".")
    if info["oversight"]:
        lines.append(f"**Human oversight:** {info['oversight'].strip()}")
    if info["logs"]:
        lines.append(f"**Agent logs:** <{info['logs']}>")
    return "\n\n".join(lines)
