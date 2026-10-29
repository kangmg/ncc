"""Move the journal to another address, e.g. from a GitHub project page to a custom domain.

The site, PDFs, citations, feeds, and DOI metadata read the address from journal.yml. Documents that are
also read on GitHub (guides, issue forms, schema `$id`) spell the address out, so they are rewritten here.
"""

from __future__ import annotations

import re
from pathlib import Path

from . import config

SKIP_DIRS = {".git", ".venv", "node_modules", "build", "dist", "generated", ".astro", ".cache", "__pycache__", "papers", "tests"}
TEXT_SUFFIXES = {".md", ".yml", ".yaml", ".json"}


def site_root(url: str, base: str) -> str:
    base = base.strip("/")
    return url.rstrip("/") + (f"/{base}" if base else "")


def update_journal_yml(text: str, url: str, base: str) -> str:
    base = f"/{base.strip('/')}" if base.strip("/") else ""
    text, n_url = re.subn(r'^(\s+url:\s*)"[^"]*"', lambda m: f'{m.group(1)}"{url.rstrip("/")}"', text, count=1, flags=re.M)
    text, n_base = re.subn(r'^(\s+base:\s*)"[^"]*"', lambda m: f'{m.group(1)}"{base}"', text, count=1, flags=re.M)
    if n_url != 1 or n_base != 1:
        raise ValueError("journal.yml must contain quoted site.url and site.base values")
    return text


def _text_files(root: Path):
    for path in sorted(root.rglob("*")):
        rel = path.relative_to(root)
        if path.is_file() and path.suffix in TEXT_SUFFIXES and not SKIP_DIRS.intersection(rel.parts[:-1]):
            yield path


def rewrite_site_root(root: Path, old: str, new: str) -> list[Path]:
    """Published papers are skipped: their text is the version of record, and GitHub Pages redirects
    the old github.io address to the custom domain, so their links keep working."""
    pattern = re.compile(re.escape(old.rstrip("/")) + r"(?![\w.-])")
    changed = []
    for path in _text_files(root):
        text = path.read_text(encoding="utf-8")
        updated = pattern.sub(new.rstrip("/"), text)
        if updated != text:
            path.write_text(updated, encoding="utf-8")
            changed.append(path)
    return changed


def move(url: str, base: str) -> list[Path]:
    site = config.journal()["site"]
    old = site_root(site["url"], site.get("base") or "")
    new = site_root(url, base)
    changed = rewrite_site_root(config.ROOT, old, new)
    journal_yml = config.ROOT / "journal.yml"
    journal_yml.write_text(update_journal_yml(journal_yml.read_text(encoding="utf-8"), url, base), encoding="utf-8")
    config.journal.cache_clear()
    return [journal_yml, *[p for p in changed if p != journal_yml]]
