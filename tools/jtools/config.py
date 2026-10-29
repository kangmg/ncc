from __future__ import annotations

import os
from functools import cache
from pathlib import Path

import yaml

ROOT = Path(os.environ.get("JOURNAL_ROOT", Path(__file__).parents[2])).resolve()
PAPERS = ROOT / "papers"
EXAMPLES = ROOT / "examples"
SCHEMA = ROOT / "schema"
TEMPLATES = ROOT / "templates"
BUILD = ROOT / "build"
SITE = ROOT / "site"
GENERATED = SITE / "src" / "generated"
PUBLIC_PAPERS = SITE / "public" / "papers"
CACHE = ROOT / ".cache"


class _StringDateLoader(yaml.SafeLoader):
    """SafeLoader that keeps ISO dates as strings so JSON Schema sees them unchanged."""


_StringDateLoader.yaml_implicit_resolvers = {
    key: [(tag, regexp) for tag, regexp in resolvers if tag != "tag:yaml.org,2002:timestamp"]
    for key, resolvers in yaml.SafeLoader.yaml_implicit_resolvers.items()
}


def load_yaml(path: Path) -> dict:
    with open(path, encoding="utf-8") as fh:
        data = yaml.load(fh, Loader=_StringDateLoader)
    return data if data is not None else {}


def loads_yaml(text: str):
    return yaml.load(text, Loader=_StringDateLoader)


class _Dumper(yaml.SafeDumper):
    pass


def _str_presenter(dumper, value: str):
    style = "|" if "\n" in value else None
    return dumper.represent_scalar("tag:yaml.org,2002:str", value, style=style)


_Dumper.add_representer(str, _str_presenter)


def dump_yaml(data, path: Path | None = None) -> str:
    text = yaml.dump(data, Dumper=_Dumper, sort_keys=False, allow_unicode=True, width=100)
    if path is not None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    return text


@cache
def journal() -> dict:
    return load_yaml(ROOT / "journal.yml")


@cache
def tag_aliases() -> dict[str, str]:
    mapping: dict[str, str] = {}
    for canonical, aliases in load_yaml(ROOT / "tags.yml").items():
        mapping[canonical.lower()] = canonical
        for alias in aliases or []:
            mapping[str(alias).lower()] = canonical
    return mapping


def site_url(path: str = "") -> str:
    cfg = journal()["site"]
    return f"{cfg['url'].rstrip('/')}{cfg.get('base', '')}{path}"


def base_path(path: str = "") -> str:
    return f"{journal()['site'].get('base', '')}{path}"
