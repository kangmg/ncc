from __future__ import annotations

import re
import subprocess
from pathlib import Path

from . import config, model, refs

READER = "markdown-raw_html-raw_attribute-raw_tex+tex_math_dollars+autolink_bare_uris"
CSL = config.TEMPLATES / "csl" / "american-chemical-society.csl"

STANDALONE_IMAGE = re.compile(r"^[ \t]*!\[[^\]]*\]\([^)]+\)(\{[^}]*\})?[ \t]*$", re.M)
TABLE_CAPTION = re.compile(r"^[ \t]*(?:Table)?:[ \t]+.*$", re.M)
LABEL = re.compile(r"\{[^}]*#((?:fig|tbl):[A-Za-z0-9_.:-]+)[^}]*\}")
IMAGE_TARGET = re.compile(r"(!\[[^\]]*\]\()([^)\s]+)")
PREFIXED_REF = re.compile(r"\b(Figure|Fig\.|Table|Tab\.|그림|표)\s*@((?:fig|tbl):[A-Za-z0-9_.:-]*[A-Za-z0-9_])")
BARE_REF = re.compile(r"@((?:fig|tbl):[A-Za-z0-9_.:-]*[A-Za-z0-9_])")

BACKMATTER = [
    ("acknowledgments", "Acknowledgments"),
    ("funding", "Funding"),
    ("data_availability", "Data Availability"),
    ("code_availability", "Code Availability"),
    ("ai_use", "Use of AI Tools"),
    ("competing_interests", "Competing Interests"),
]


class RenderError(RuntimeError):
    pass


def number_labels(markdown: str) -> dict[str, int]:
    numbers: dict[str, int] = {}
    counts = {"fig": 0, "tbl": 0}
    for kind, pattern in (("fig", STANDALONE_IMAGE), ("tbl", TABLE_CAPTION)):
        for match in pattern.finditer(markdown):
            counts[kind] += 1
            label = LABEL.search(match.group(0))
            if label and label.group(1).startswith(kind):
                numbers[label.group(1)] = counts[kind]
    return numbers


def preprocess(markdown: str, target: str, image_prefix: str | None = None) -> str:
    numbers = number_labels(markdown)
    words = {"fig": "Figure", "tbl": "Table"}

    def text_for(label: str, word: str | None = None) -> str:
        number = numbers.get(label, "??")
        word = word or words[label.split(":")[0]]
        if target == "html" and label in numbers and label.startswith("fig"):
            return f"[{word} {number}](#{label})"
        return f"{word} {number}"

    out = PREFIXED_REF.sub(lambda m: text_for(m.group(2), m.group(1)), markdown)
    out = BARE_REF.sub(lambda m: text_for(m.group(1)), out)
    out = re.sub(r"[ \t]*\{#tbl:[A-Za-z0-9_.:-]+\}", "", out)
    if image_prefix is not None:
        def rewrite(m: re.Match) -> str:
            src = m.group(2)
            if src.startswith(("http://", "https://", "/", "data:")):
                return m.group(0)
            return f"{m.group(1)}{image_prefix}{src}"
        out = IMAGE_TARGET.sub(rewrite, out)
    return out


def pandoc(markdown: str, to: str, args: list[str] | None = None) -> str:
    cmd = ["pandoc", "-f", READER, "-t", to, "--wrap=preserve", *(args or [])]
    proc = subprocess.run(cmd, input=markdown, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RenderError(f"pandoc failed ({to}): {proc.stderr.strip()}")
    return proc.stdout


def body_markdown(paper: dict, base: Path, overrides: dict | None = None) -> str:
    src = {**paper, **(overrides or {})}
    parts: list[str] = []
    if "sections" in src:
        for section in src["sections"]:
            parts.append(f"# {section['title']}\n\n{section['body'].strip()}\n")
    elif "body" in src:
        parts.append(src["body"])
    elif src.get("body_file", "").endswith(".md"):
        parts.append((base / src["body_file"]).read_text(encoding="utf-8"))
    back = []
    for key, label in BACKMATTER:
        if src.get(key):
            back.append(f"## {label}\n\n{str(src[key]).strip()}\n")
        if key == "ai_use" and (statement := model.ai_statement(paper)):
            back.append(f"## AI Contribution\n\n{statement}\n")
    if src.get("supporting_information"):
        rows = "\n".join(f"- [{i['file']}]({i['file']}): {i['description']}" for i in src["supporting_information"])
        back.append(f"## Supporting Information\n\n{rows}\n")
    if back:
        parts.append("::: {.backmatter}\n\n" + "\n".join(back) + "\n:::\n")
    return "\n".join(parts)


def citation_args(paper: dict, base: Path, workdir: Path) -> list[str]:
    bib = refs.bibliography_args(paper, base, workdir)
    if not bib:
        return []
    return ["--citeproc", "--csl", str(CSL), *bib, "-M", "reference-section-title=References", "-M", "link-citations=true"]


def render_html(paper: dict, base: Path, workdir: Path, image_prefix: str, overrides: dict | None = None) -> dict:
    workdir.mkdir(parents=True, exist_ok=True)
    src = {**paper, **(overrides or {})}
    cite = citation_args(paper, base, workdir)
    body_md = preprocess(body_markdown(paper, base, overrides), "html", image_prefix)
    body = pandoc(body_md, "html5", ["--math-method=katex", "--shift-heading-level-by=1", *cite]) if body_md.strip() else ""
    abstract = pandoc(src["abstract"], "html5", ["--math-method=katex"])
    return {"body": body, "abstract": abstract}


def render_typst(paper: dict, base: Path, workdir: Path, overrides: dict | None = None) -> dict:
    workdir.mkdir(parents=True, exist_ok=True)
    src = {**paper, **(overrides or {})}
    cite = citation_args(paper, base, workdir)
    body_md = preprocess(body_markdown(paper, base, overrides), "typst")
    body = pandoc(body_md, "typst", cite) if body_md.strip() else ""
    abstract = pandoc(src["abstract"], "typst")
    return {"body": body, "abstract": abstract}


def render_document(markdown_path: Path) -> str:
    return pandoc(markdown_path.read_text(encoding="utf-8"), "html5", ["--shift-heading-level-by=1", "--section-divs"])
