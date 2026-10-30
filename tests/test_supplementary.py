from pathlib import Path
from zipfile import ZipFile

import pytest

from jtools import assets, config, export, issue, model, render, validate


@pytest.mark.parametrize("with_pdf", [False, True])
def test_small_si_validates_exports_and_renders(tmp_path, monkeypatch, with_pdf):
    paper = dict(model.discover_articles()[0].latest.paper)
    paper.pop("body_file", None)
    paper.pop("pdf", None)
    paper.pop("toc_graphic", None)
    paper["sections"] = [{"title": "Results", "body": "A hydrogen atom."}]
    paper["supporting_information"] = [{"file": "si/atom.xyz", "description": "Structure"}]
    (tmp_path / "si").mkdir()
    (tmp_path / "si" / "atom.xyz").write_text("1\nHydrogen\nH 0 0 0\n")
    version = model.Version(1, tmp_path, paper, {"published": "2026-10-30"}, None)
    article = model.discover_articles()[0]
    public = tmp_path.parent / (tmp_path.name + "-public")
    monkeypatch.setattr(export, "_public_dir", lambda a, v: (public, "/journal/papers/test/v1/"))

    data = export.export_version(article, version, with_pdf)

    assert not [f for f in validate.validate_paper(paper, tmp_path, "p") if f.level == "error"]
    assert (public / "si" / "atom.xyz").read_bytes() == (tmp_path / "si" / "atom.xyz").read_bytes()
    assert data["supporting_information"][0]["url"] == config.site_url(f"/papers/{article.id}/v1/si/atom.xyz")
    assert 'href="/journal/papers/test/v1/si/atom.xyz"' in data["body_html"]
    if with_pdf:
        with ZipFile(public / f"{article.key(1)}-files.zip") as bundle:
            assert set(bundle.namelist()) == {f"{article.key(1)}.pdf", "si/atom.xyz"}
            assert bundle.read("si/atom.xyz") == (tmp_path / "si" / "atom.xyz").read_bytes()
            assert bundle.read(f"{article.key(1)}.pdf") == (public / f"{article.key(1)}.pdf").read_bytes()
        assert data["bundle"] == f"/journal/papers/test/v1/{article.key(1)}-files.zip"
    else:
        assert data["bundle"] is None


@pytest.mark.parametrize("rel", ["si/../outside.xyz", "si/missing.xyz"])
def test_local_si_invalid_path_rejected(tmp_path, rel):
    paper = dict(model.discover_articles()[0].latest.paper)
    paper["supporting_information"] = [{"file": rel, "description": "Structure"}]
    assert any(f.level == "error" for f in validate.validate_paper(paper, tmp_path, "p"))


def test_si_budget_includes_small_structure(tmp_path):
    (tmp_path / "si").mkdir()
    with (tmp_path / "si" / "large.xyz").open("wb") as stream:
        stream.truncate(assets.MAX_FILE_BYTES + 1)
    assert assets.file_problems(tmp_path)


def test_issue_si_attachment_downloads_but_external_record_does_not(tmp_path, monkeypatch):
    class Response:
        url = "https://github.com/user-attachments/assets/opaque-id"
        headers = {"Content-Type": "application/octet-stream"}

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return None

        def raise_for_status(self):
            pass

        def iter_content(self, size):
            return iter([b"GIF89a"])

    calls = []

    def get(url, **kwargs):
        calls.append(url)
        return Response()

    monkeypatch.setattr(issue.requests, "get", get)
    text = "[motion.gif](https://github.com/user-attachments/assets/opaque-id) | Motion\nhttps://zenodo.org/records/123 | Dataset"

    entries = issue.parse_supporting_information(text, tmp_path, True)

    assert entries == [{"file": "si/motion.gif", "description": "Motion"},
                       {"url": "https://zenodo.org/records/123", "description": "Dataset"}]
    assert (tmp_path / "si" / "motion.gif").read_bytes() == b"GIF89a"
    assert calls == ["https://github.com/user-attachments/assets/opaque-id"]


@pytest.mark.parametrize("replacement", ["None", "https://zenodo.org/records/123 | Replacement"])
def test_revision_clearing_si_removes_inherited_files(tmp_path, monkeypatch, replacement):
    old = tmp_path / "old"
    (old / "si").mkdir(parents=True)
    for i in range(assets.MAX_FILES):
        (old / "si" / f"atom{i}.xyz").write_text("1\nH\nH 0 0 0\n")
    paper = dict(model.discover_articles()[0].latest.paper)
    paper["supporting_information"] = [{"file": f"si/atom{i}.xyz", "description": "Atom"} for i in range(assets.MAX_FILES)]
    previous = model.Version(1, old, paper, {"published": "2026-10-30"}, None)

    def download(url, dest, stem):
        dest.mkdir(parents=True, exist_ok=True)
        path = dest / stem
        path.write_text("<svg/>")
        return path

    monkeypatch.setattr(issue, "_download", download)
    conv = issue.convert_revision({"Manuscript format": "No change", "Supporting information": replacement,
                                   "Files": "[plot.svg](https://github.com/user-attachments/files/123/plot.svg)"}, previous, tmp_path / "new")

    assert conv.paper["supporting_information"] == ([] if replacement == "None" else [{"url": "https://zenodo.org/records/123", "description": "Replacement"}])
    assert not (tmp_path / "new" / "si").exists()
    assert (tmp_path / "new" / "figures" / "plot.svg").is_file()
