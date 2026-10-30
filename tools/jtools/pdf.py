from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

from pypdf import PdfReader

from . import cite, config, model, render


class PdfError(RuntimeError):
    pass


def _typst(main: Path, out: Path, root: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    proc = subprocess.run(
        ["typst", "compile", "--root", str(root), str(main), str(out)], capture_output=True, text=True
    )
    if proc.returncode != 0:
        raise PdfError(f"typst failed for {main}:\n{proc.stderr.strip()}")


def _copy_assets(src: Path, dst: Path) -> None:
    for item in src.rglob("*"):
        if item.is_file() and item.suffix not in {".yml", ".yaml"}:
            target = dst / item.relative_to(src)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, target)


def supplied_pdf(version: model.Version, workdir: Path) -> Path:
    paper = version.paper
    if "pdf" in paper:
        return version.dir / paper["pdf"]
    out = workdir / "author-compiled.pdf"
    _typst(version.dir / paper["body_file"], out, version.dir)
    return out


def build_pdf(article: model.Article, version: model.Version, out: Path, translated: bool = False,
              status_note: str | None = None) -> Path:
    suffix = "-en" if translated else ""
    workdir = config.BUILD / "typst" / f"{article.key(version.number)}{suffix}"
    if workdir.exists():
        shutil.rmtree(workdir)
    workdir.mkdir(parents=True)
    _copy_assets(version.dir, workdir)

    meta = cite.typst_meta(article, version, translated, status_note)
    (workdir / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
    overrides = translation_overrides(version) if translated else None
    pdf_paper = {**version.paper, "supporting_information": [
        {"url": item["url"] if "url" in item else config.site_url(f"/papers/{article.id}/v{version.number}/{item['file']}"),
         "description": item["description"]} for item in version.paper.get("supporting_information", [])]}

    template = "/" + str((config.TEMPLATES / "typst" / "journal.typ").relative_to(config.ROOT))
    lines = [f'#import "{template}": article, embed-pdf', '#let meta = json("meta.json")']
    if version.body_kind in ("sections", "markdown"):
        typ = render.render_typst(pdf_paper, version.dir, workdir, overrides)
        (workdir / "body.typ").write_text(typ["body"], encoding="utf-8")
        lines += [f"#show: article.with(meta: meta, abstract: [{typ['abstract']}])", '#include "body.typ"']
    else:
        typ = render.render_typst(pdf_paper, version.dir, workdir, overrides)
        supplied = supplied_pdf(version, workdir)
        shutil.copy2(supplied, workdir / "supplied.pdf")
        pages = len(PdfReader(str(supplied)).pages)
        note = "The English translation covers the title and abstract only." if translated else ""
        lines += [
            f"#show: article.with(meta: meta, abstract: [{typ['abstract']}])",
            f"#text(size: 9pt, style: \"italic\")[The author-supplied manuscript follows ({pages} pages). {note}]",
            '#embed-pdf(read("supplied.pdf", encoding: none), ' + str(pages) + ")",
        ]
        if pdf_paper.get("supporting_information"):
            si_paper = {"abstract": "", "supporting_information": pdf_paper["supporting_information"]}
            si_typ = render.render_typst(si_paper, version.dir, workdir)
            (workdir / "supporting.typ").write_text(si_typ["body"], encoding="utf-8")
            lines += ['#pagebreak()', '#include "supporting.typ"']
    main = workdir / "main.typ"
    main.write_text("\n".join(lines) + "\n", encoding="utf-8")
    _typst(main, out, config.ROOT)
    return out


def translation_overrides(version: model.Version) -> dict:
    tr = version.translation or {}
    keys = ("title", "abstract", "sections", "acknowledgments", "funding", "data_availability",
            "code_availability", "ai_use", "competing_interests")
    return {k: tr[k] for k in keys if k in tr}
