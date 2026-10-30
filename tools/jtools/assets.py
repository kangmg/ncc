from __future__ import annotations

from pathlib import Path
from typing import Final

MAX_FILE_BYTES: Final = 5 * 1024 * 1024
MAX_TOTAL_BYTES: Final = 15 * 1024 * 1024
MAX_FILES: Final = 10
MANUSCRIPT_SUFFIXES: Final = {".md", ".typ", ".pdf", ".png", ".jpg", ".jpeg", ".svg", ".webp", ".bib", ".json", ".yaml", ".yml"}
SI_SUFFIXES: Final = {".xyz", ".cif", ".pdb", ".mol", ".sdf", ".gif", ".csv", ".txt", ".json", ".pdf"}


def manuscript_files(base: Path) -> list[Path]:
    """Return submitted assets, excluding journal metadata and translations."""
    return sorted(p for p in base.rglob("*") if p.is_file()
                  and p != base / "paper.yml"
                  and not (p.parent == base and p.match("translation.*.yml")))


def file_problems(base: Path) -> list[str]:
    """Enforce the direct manuscript budget for both Issues and pull requests."""
    files = manuscript_files(base)
    problems = []
    total = 0
    if len(files) > MAX_FILES:
        problems.append(f"manuscript has more than {MAX_FILES} files")
    for path in files:
        rel = path.relative_to(base)
        if path.is_symlink() or not path.resolve().is_relative_to(base.resolve()):
            problems.append(f"asset `{rel}` must be a regular file inside the manuscript folder")
            continue
        allowed = SI_SUFFIXES if rel.parts[0] == "si" else MANUSCRIPT_SUFFIXES
        if path.suffix.lower() not in allowed:
            problems.append(f"asset `{rel}` has an unsupported extension; small SI belongs under si/, larger data and archives in an external repository")
        with path.open("rb") as stream:
            signature = stream.read(8)
        if signature.startswith((b"PK\x03\x04", b"PK\x05\x06", b"PK\x07\x08", b"\x1f\x8b", b"7z\xbc\xaf\x27\x1c", b"Rar!")):
            problems.append(f"asset `{rel}` is an archive, even though its name may use a manuscript extension")
        size = path.stat().st_size
        total += size
        if size > MAX_FILE_BYTES:
            problems.append(f"asset `{rel}` exceeds 5 MiB")
    if total > MAX_TOTAL_BYTES:
        problems.append("manuscript assets exceed 15 MiB in total")
    return problems
