from __future__ import annotations

import datetime as dt
import io
import mimetypes
import re
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlparse

import requests

from . import assets, config, model, validate

NO_RESPONSE = "_No response_"
TYPE_BY_LABEL = {label: key for key, label in model.ARTICLE_TYPES.items()}
ALLOWED_HOSTS = {"github.com", "user-images.githubusercontent.com", "private-user-images.githubusercontent.com",
                 "objects.githubusercontent.com"}
MAX_DOWNLOAD = assets.MAX_FILE_BYTES
LINK_RE = re.compile(r"(!?)\[([^\]]*)\]\((https?://[^)\s]+)\)")
IMG_TAG_RE = re.compile(r"<img\b[^>]*?\bsrc=\"(https?://[^\"]+)\"[^>]*>", re.I)
ALT_RE = re.compile(r"\balt=\"([^\"]*)\"", re.I)
BARE_URL_RE = re.compile(r"(?<![(\"])\bhttps://github\.com/user-attachments/(?:assets|files)/\S+")
FENCE_RE = re.compile(r"^```[a-zA-Z]*\n(.*?)\n```\s*$", re.S)
KINDS = ("submission", "revision", "withdrawal")
AI_LEVEL_BY_LABEL = {
    "None": "none", "Assisted": "assisted", "Substantial": "substantial", "Agent-led": "agent-led",
}


class IssueError(RuntimeError):
    pass


@dataclass
class Conversion:
    paper: dict
    findings: list[validate.Finding] = field(default_factory=list)
    downloaded: list[str] = field(default_factory=list)


def parse_form(body: str) -> dict[str, str | None]:
    fields: dict[str, str | None] = {}
    current = None
    lines: list[str] = []
    for line in (body or "").replace("\r\n", "\n").split("\n"):
        heading = re.match(r"^###\s+(.+?)\s*$", line)
        if heading:
            if current is not None:
                fields[current] = _clean("\n".join(lines))
            current, lines = heading.group(1), []
        elif current is not None:
            lines.append(line)
    if current is not None:
        fields[current] = _clean("\n".join(lines))
    return fields


def _clean(value: str) -> str | None:
    value = value.strip()
    if not value or value == NO_RESPONSE:
        return None
    fenced = FENCE_RE.match(value)
    return fenced.group(1).strip() if fenced else value


def checked(value: str | None) -> list[str]:
    return [m.group(1).strip() for m in re.finditer(r"^- \[[xX]\]\s+(.+)$", value or "", re.M)]


def parse_authors(text: str) -> tuple[list[dict], dict[str, str]]:
    authors, affiliations = [], {}
    for line in (text or "").splitlines():
        if not line.strip():
            continue
        cols = [c.strip() for c in line.split("|")] + [""] * 5
        name, github, orcid, affs, flags = cols[:5]
        author: dict = {"name": name}
        if github:
            author["github"] = github.lstrip("@")
        if orcid:
            author["orcid"] = orcid.removeprefix("https://orcid.org/")
        refs = []
        for aff in (a.strip() for a in affs.split(";") if a.strip()):
            key = next((k for k, v in affiliations.items() if v == aff), None)
            if key is None:
                key = str(len(affiliations) + 1)
                affiliations[key] = aff
            refs.append(int(key))
        if refs:
            author["affiliations"] = refs
        if "corresponding" in flags.lower():
            author["corresponding"] = True
        authors.append(author)
    return authors, affiliations


def parse_references(text: str | None, dest: Path) -> tuple[list[dict], str | None]:
    if not text:
        return [], None
    if re.search(r"@\w+\s*\{", text):
        (dest / "references.bib").write_text(text + "\n", encoding="utf-8")
        return [], "references.bib"
    refs = []
    for i, line in enumerate(l.strip() for l in text.splitlines() if l.strip()):
        match = re.match(r"^([A-Za-z0-9_:.-]+)\s*[:=]\s*(.+)$", line)
        key, value = (match.group(1), match.group(2).strip()) if match else (f"ref{i + 1}", line)
        doi = re.sub(r"^(https?://(dx\.)?doi\.org/|doi:\s*)", "", value, flags=re.I)
        if re.match(r"^10\.\d{4,9}/\S+$", doi):
            refs.append({"id": key, "doi": doi})
        else:
            refs.append({"id": key, "text": value})
    return refs, None


def parse_sections(markdown: str) -> list[dict]:
    parts = re.split(r"^##\s+(.+?)\s*$", markdown.strip(), flags=re.M)
    sections = []
    if parts[0].strip():
        sections.append({"title": "Main Text", "body": parts[0].strip()})
    for title, body in zip(parts[1::2], parts[2::2]):
        sections.append({"title": title.strip(), "body": body.strip()})
    return sections


def _download(url: str, dest_dir: Path, stem: str, *, supplementary: bool = False) -> Path:
    host = urlparse(url).hostname or ""
    if host not in ALLOWED_HOSTS:
        raise IssueError(f"refusing to download from {host}; attach files to the issue instead")
    with requests.get(url, stream=True, timeout=60, allow_redirects=True) as resp:
        resp.raise_for_status()
        final_host = urlparse(resp.url).hostname or ""
        if not (final_host in ALLOWED_HOSTS or final_host.endswith(".githubusercontent.com")):
            raise IssueError(f"attachment redirected to unexpected host {final_host}")
        content_type = resp.headers.get("Content-Type", "").split(";")[0].strip()
        suffix = Path(urlparse(url).path).suffix or mimetypes.guess_extension(content_type) or ""
        if supplementary and not Path(urlparse(url).path).suffix:
            suffix = Path(stem).suffix
        if suffix == ".svg+xml":
            suffix = ".svg"
        allowed = assets.SI_SUFFIXES if supplementary else assets.MANUSCRIPT_SUFFIXES
        if suffix.lower() not in allowed or (Path(stem).suffix and Path(stem).suffix.lower() not in allowed):
            raise IssueError("unsupported attachment type; use manuscript files or supported small SI, not archives")
        data = io.BytesIO()
        for chunk in resp.iter_content(65536):
            data.write(chunk)
            if data.tell() > MAX_DOWNLOAD:
                raise IssueError(f"attachment larger than 5 MiB: {url}")
    safe = re.sub(r"[^A-Za-z0-9_.-]+", "-", stem).strip("-.") or "file"
    if data.getvalue().startswith((b"PK\x03\x04", b"PK\x05\x06", b"PK\x07\x08", b"\x1f\x8b", b"7z\xbc\xaf\x27\x1c", b"Rar!")):
        raise IssueError("archive attachments are not accepted, even when renamed")
    target = dest_dir / (safe if safe.endswith(suffix) else safe + suffix)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data.getvalue())
    return target


def _check_budget(dest: Path) -> None:
    problems = assets.file_problems(dest)
    if problems:
        raise IssueError("; ".join(problems))


def localise_images(markdown: str, dest: Path, conv: Conversion, download: bool) -> str:
    markdown = IMG_TAG_RE.sub(
        lambda m: f"![{(ALT_RE.search(m.group(0)) or [None, 'figure'])[1]}]({m.group(1)})", markdown
    )
    counter = {"n": 0}

    def replace(m: re.Match) -> str:
        bang, alt, url = m.groups()
        if not bang:
            return m.group(0)
        counter["n"] += 1
        if not download:
            return m.group(0)
        path = _download(url, dest / "figures", f"figure-{counter['n']}")
        _check_budget(dest)
        conv.downloaded.append(str(path.relative_to(dest)))
        return f"![{alt}]({path.relative_to(dest).as_posix()})"

    return LINK_RE.sub(replace, markdown)


def attachments(text: str | None) -> list[tuple[str, str]]:
    found = [(m.group(2) or Path(urlparse(m.group(3)).path).name, m.group(3)) for m in LINK_RE.finditer(text or "")]
    found += [(Path(urlparse(u).path).name, u) for u in BARE_URL_RE.findall(text or "")]
    found += [((ALT_RE.search(m.group(0)) or [None, "figure"])[1], m.group(1)) for m in IMG_TAG_RE.finditer(text or "")]
    return found


def fetch_files(text: str | None, dest: Path, conv: Conversion, download: bool) -> list[str]:
    files: list[str] = []
    for name, url in attachments(text):
        if Path(name).suffix.lower() not in assets.MANUSCRIPT_SUFFIXES:
            raise IssueError("attach individual manuscript files here; use Supporting information for small SI, external records for archives")
        if not download:
            files.append(name)
            continue
        if len(assets.manuscript_files(dest)) >= assets.MAX_FILES:
            raise IssueError(f"manuscript has more than {assets.MAX_FILES} files")
        is_image = re.search(r"\.(png|jpe?g|gif|svg|webp)$", name, re.I) or "/assets/" in url
        path = _download(url, dest / ("figures" if is_image else ""), name)
        _check_budget(dest)
        files.append(str(path.relative_to(dest)))
        conv.downloaded.append(str(path.relative_to(dest)))
    return files


def parse_supporting_information(text: str, dest: Path | None = None, download: bool = False) -> list[dict[str, str]]:
    """Download explicitly attached GitHub SI; preserve external records as links."""
    if text.strip().lower() == "none":
        return []
    entries = []
    for line in text.splitlines():
        if not line.strip():
            continue
        target, separator, description = line.partition("|")
        target, description = target.strip(), description.strip()
        attachment = LINK_RE.fullmatch(target)
        url = attachment.group(3) if attachment else target
        parsed = urlparse(url)
        if not separator or parsed.scheme != "https" or not parsed.hostname or not description:
            raise IssueError("Supporting information: use HTTPS URL | description, one entry per line")
        if parsed.hostname == "github.com" and parsed.path.startswith("/user-attachments/"):
            name = attachment.group(2) if attachment else Path(parsed.path).name
            if Path(name).suffix.lower() not in assets.SI_SUFFIXES:
                raise IssueError("SI attachments need a filename with a supported extension, for example [structure.xyz](URL)")
            if download:
                if dest is None:
                    raise IssueError("SI download requires a manuscript folder")
                path = _download(url, dest / "si", name, supplementary=True)
                _check_budget(dest)
                entries.append({"file": path.relative_to(dest).as_posix(), "description": description})
            else:
                entries.append({"file": "si/" + Path(name).name, "description": description})
        else:
            entries.append({"url": url, "description": description})
    return entries


def parse_agents(text: str | None) -> list[dict]:
    agents = []
    for line in (text or "").splitlines():
        if not line.strip():
            continue
        cols = [c.strip() for c in line.split("|")] + [""] * 5
        name, model_name, provider, roles, github = cols[:5]
        agent: dict = {"name": name, "roles": [r.strip().lower() for r in roles.split(",") if r.strip()]}
        if model_name:
            agent["model"] = model_name
        if provider:
            agent["provider"] = provider
        if github:
            agent["github"] = github.lstrip("@")
        agents.append(agent)
    return agents


def parse_ai_contributions(fields: dict) -> dict | None:
    label = (fields.get("AI contribution level") or "").split(":")[0].strip()
    if label not in AI_LEVEL_BY_LABEL:
        return None
    ai: dict = {"level": AI_LEVEL_BY_LABEL[label]}
    agents = parse_agents(fields.get("AI agents"))
    if agents:
        ai["agents"] = agents
    for name, key in (("Human oversight", "oversight"), ("Agent logs", "logs")):
        if fields.get(name):
            ai[key] = fields[name]
    return ai


def _tags(fields: dict) -> list[str]:
    tags = checked(fields.get("Topic tags"))
    tags += [t.strip() for t in (fields.get("Additional tags") or "").split(",") if t.strip()]
    return tags


def _body_from_format(fmt: str, fields: dict, dest: Path, conv: Conversion, download: bool, files: list[str]) -> dict:
    manuscript = fields.get("Manuscript") or ""
    if fmt.startswith("Markdown sections"):
        if not manuscript.strip():
            raise IssueError("Manuscript is empty; write sections starting with `## Title`")
        return {"sections": parse_sections(localise_images(manuscript, dest, conv, download))}
    if fmt.startswith("Attached PDF"):
        pdfs = [f for f in files if f.lower().endswith(".pdf")]
        if not pdfs:
            raise IssueError("Manuscript format is 'Attached PDF' but no PDF was attached under Files")
        if download and pdfs[0] != "manuscript.pdf":
            shutil.move(dest / pdfs[0], dest / "manuscript.pdf")
        return {"pdf": "manuscript.pdf"}
    if fmt.startswith("Attached Markdown or Typst"):
        bodies = [f for f in files if f.lower().endswith((".typ", ".md"))]
        if not bodies:
            raise IssueError("no .typ or .md file found under Files")
        return {"body_file": bodies[0]}
    return {}


def convert_submission(fields: dict, dest: Path, download: bool = True) -> Conversion:
    dest.mkdir(parents=True, exist_ok=True)
    conv = Conversion(paper={})
    fmt = fields.get("Manuscript format") or ""
    files = fetch_files(fields.get("Files"), dest, conv, download)

    if fmt.startswith("Complete paper.yml"):
        loaded = config.loads_yaml(localise_images(fields.get("Manuscript") or "", dest, conv, download))
        if not isinstance(loaded, dict):
            raise IssueError("the pasted paper.yml is not a YAML mapping")
        paper = loaded
    else:
        authors, affiliations = parse_authors(fields.get("Authors") or "")
        paper = {
            "title": fields.get("Title"),
            "article_type": TYPE_BY_LABEL.get(fields.get("Article type") or "", fields.get("Article type")),
            "language": (fields.get("Manuscript language") or "en").strip().lower(),
            "authors": authors,
        }
        if affiliations:
            paper["affiliations"] = affiliations
        paper["abstract"] = fields.get("Abstract")
        paper["tags"] = _tags(fields)
        paper["license"] = fields.get("License") or config.journal()["defaults"]["license"]
        paper |= _body_from_format(fmt, fields, dest, conv, download, files)
        refs, bib = parse_references(fields.get("References"), dest)
        if refs:
            paper["references"] = refs
        if bib:
            paper["bibliography"] = bib
        paper["data_availability"] = fields.get("Data availability")
        if fields.get("Code availability"):
            paper["code_availability"] = fields["Code availability"]
        paper["ai_use"] = fields.get("Use of AI tools")
        paper["ai_contributions"] = parse_ai_contributions(fields)
        paper["mint_doi"] = bool(checked(fields.get("DOI")))
    if fields.get("Supporting information"):
        paper["supporting_information"] = parse_supporting_information(fields["Supporting information"] or "", dest, download)
    _check_budget(dest)
    conv.paper = {k: v for k, v in paper.items() if v is not None}
    return conv


def convert_revision(fields: dict, previous: model.Version, dest: Path, download: bool = True) -> Conversion:
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(previous.dir, dest, ignore=shutil.ignore_patterns("translation.*.yml"))
    conv = Conversion(paper=dict(previous.paper))
    fmt = fields.get("Manuscript format") or ""
    if fields.get("Supporting information") and (dest / "si").exists():
        shutil.rmtree(dest / "si")
    files = fetch_files(fields.get("Files"), dest, conv, download)
    if fmt.startswith("Complete paper.yml"):
        conv.paper = config.loads_yaml(localise_images(fields.get("Manuscript") or "", dest, conv, download))
    elif not fmt.startswith("No change"):
        for key in ("sections", "body_file", "pdf"):
            conv.paper.pop(key, None)
        conv.paper |= _body_from_format(fmt, fields, dest, conv, download, files)
    for label, key in (("Title", "title"), ("Abstract", "abstract")):
        if fields.get(label):
            conv.paper[key] = fields[label]
    refs, bib = parse_references(fields.get("References"), dest)
    if refs:
        conv.paper["references"] = refs
    if bib:
        conv.paper["bibliography"] = bib
    if fields.get("Supporting information"):
        conv.paper["supporting_information"] = parse_supporting_information(fields["Supporting information"] or "", dest, download)
    if fields.get("Data availability"):
        conv.paper["data_availability"] = fields["Data availability"]
    _check_budget(dest)
    conv.paper["changelog"] = fields.get("Changelog")
    return conv


def issue_kind(issue: dict) -> str:
    labels = {l["name"] for l in issue.get("labels", [])}
    for kind in KINDS:
        if kind in labels:
            return kind
    title = (issue.get("title") or "").strip().lower()
    for kind in KINDS:
        if title.startswith(f"[{kind}]"):
            return kind
    raise IssueError("issue has none of the labels submission / revision / withdrawal "
                     "and its title does not start with [Submission], [Revision], or [Withdrawal]")


def human_handles(paper: dict) -> set[str]:
    return {a["github"].lower() for a in paper.get("authors", []) if a.get("github")}


def agent_handles(paper: dict) -> set[str]:
    return {a["github"].lower() for a in (paper.get("ai_contributions") or {}).get("agents", []) if a.get("github")}


def check_authorised(article: model.Article, login: str, agents_allowed: bool = True) -> None:
    maintainer = config.journal()["journal"]["maintainer"]["github"].lower()
    allowed = human_handles(article.latest.paper) | {maintainer}
    if agents_allowed:
        allowed |= agent_handles(article.latest.paper)
    if login.lower() not in allowed:
        who = "a listed author or agent" if agents_allowed else "a listed human author"
        raise IssueError(f"@{login} is not {who} of {article.id}")


def find_article(article_id: str | None) -> model.Article:
    article_id = (article_id or "").strip()
    if not model.ID_RE.match(article_id) or not (config.PAPERS / article_id / "record.yml").exists():
        raise IssueError(f"unknown article ID `{article_id}`")
    return model.load_article(config.PAPERS / article_id)


def next_id(year: int | None = None) -> str:
    year = year or dt.date.today().year
    numbers = [int(d.name.split("-")[1]) for d in config.PAPERS.glob(f"{year}-*") if model.ID_RE.match(d.name)]
    return f"{year}-{max(numbers, default=0) + 1:04d}"


def write_paper(conv: Conversion, dest: Path) -> None:
    config.dump_yaml(conv.paper, dest / "paper.yml")
    conv.findings += validate.validate_paper(conv.paper, dest, "paper.yml", resolve_dois=True)


def apply(issue: dict, today: dt.date | None = None) -> dict:
    """Turn an accepted issue into repository changes. Returns a summary for the PR body."""
    today = today or dt.date.today()
    kind = issue_kind(issue)
    fields = parse_form(issue.get("body") or "")
    login = issue["user"]["login"]

    if kind == "submission":
        article_id = next_id(today.year)
        vdir = config.PAPERS / article_id / "v1"
        conv = convert_submission(fields, vdir)
        write_paper(conv, vdir)
        record = {
            "id": article_id, "status": "published",
            "submitted": issue["created_at"][:10], "accepted": today.isoformat(),
            "issue": issue["number"], "concept_doi": None, "zenodo_concept_id": None,
            "versions": [{"version": 1, "published": today.isoformat(), "doi": None, "zenodo_id": None,
                          "changelog": "Initial version."}],
        }
        config.dump_yaml(record, config.PAPERS / article_id / "record.yml")
        return {"kind": kind, "id": article_id, "version": 1, "dir": vdir, "findings": conv.findings}

    article = find_article(fields.get("Article ID"))
    check_authorised(article, login, agents_allowed=kind == "revision")

    if kind == "revision":
        number = article.latest.number + 1
        vdir = article.dir / f"v{number}"
        conv = convert_revision(fields, article.latest, vdir)
        write_paper(conv, vdir)
        article.record["versions"].append({
            "version": number, "published": today.isoformat(), "doi": None, "zenodo_id": None,
            "changelog": fields.get("Changelog") or "",
        })
        config.dump_yaml(article.record, article.dir / "record.yml")
        return {"kind": kind, "id": article.id, "version": number, "dir": vdir, "findings": conv.findings}

    article.record["status"] = "withdrawn"
    article.record["withdrawn"] = {"date": today.isoformat(), "reason": fields.get("Reason") or "Withdrawn by the authors."}
    config.dump_yaml(article.record, article.dir / "record.yml")
    return {"kind": kind, "id": article.id, "version": None, "dir": article.dir, "findings": []}


def promote_submissions(today: dt.date | None = None) -> list[str]:
    """Assign IDs to pull-request submissions in submissions/ and register new version folders."""
    today = today or dt.date.today()
    changed = []
    root = config.ROOT / "submissions"
    for sub in sorted(root.glob("*/paper.yml")) if root.exists() else []:
        article_id = next_id(today.year)
        target = config.PAPERS / article_id / "v1"
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(sub.parent), str(target))
        config.dump_yaml({
            "id": article_id, "status": "published", "submitted": today.isoformat(), "accepted": today.isoformat(),
            "issue": None, "concept_doi": None, "zenodo_concept_id": None,
            "versions": [{"version": 1, "published": today.isoformat(), "doi": None, "zenodo_id": None,
                          "changelog": "Initial version."}],
        }, config.PAPERS / article_id / "record.yml")
        changed.append(article_id)
    for article in model.discover_articles():
        known = {v["version"] for v in article.record["versions"]}
        extra = sorted(int(d.name[1:]) for d in article.dir.glob("v*") if d.name[1:].isdigit() and int(d.name[1:]) not in known)
        for number in extra:
            paper = config.load_yaml(article.dir / f"v{number}" / "paper.yml")
            article.record["versions"].append({
                "version": number, "published": today.isoformat(), "doi": None, "zenodo_id": None,
                "changelog": paper.get("changelog", ""),
            })
            changed.append(f"{article.id}v{number}")
        if extra:
            config.dump_yaml(article.record, article.dir / "record.yml")
    return changed


PREVIEW_MARKER = "<!-- journal-preview -->"


def _synthetic_article(paper_dir: Path, paper: dict, today: dt.date) -> model.Article:
    entry = {"version": 1, "published": today.isoformat(), "doi": None, "changelog": "Preview."}
    record = {"id": f"{today.year}-0000", "status": "published", "submitted": today.isoformat(),
              "accepted": today.isoformat(), "versions": [entry]}
    version = model.Version(1, paper_dir, paper, entry, None)
    return model.Article(id=record["id"], dir=paper_dir, record=record, versions=[version])


def preview(issue: dict, outdir: Path, today: dt.date | None = None) -> dict:
    from . import pdf

    today = today or dt.date.today()
    if outdir.exists():
        shutil.rmtree(outdir)
    outdir.mkdir(parents=True)
    result: dict = {"kind": None, "findings": [], "paper": None, "pdf": None, "downloaded": []}
    try:
        kind = issue_kind(issue)
        result["kind"] = kind
        fields = parse_form(issue.get("body") or "")
        login = issue["user"]["login"]
        paper_dir = outdir / "paper"
        if kind == "withdrawal":
            article = find_article(fields.get("Article ID"))
            check_authorised(article, login, agents_allowed=False)
            result["summary"] = f"Withdrawal of {article.id}: {article.latest.paper['title']}"
            return result
        if kind == "revision":
            article = find_article(fields.get("Article ID"))
            check_authorised(article, login)
            conv = convert_revision(fields, article.latest, paper_dir)
        else:
            conv = convert_submission(fields, paper_dir)
            if login.lower() not in human_handles(conv.paper) | agent_handles(conv.paper):
                conv.findings.append(validate.Finding(
                    "warning", "Authors", f"the submitter @{login} is not listed as an author or as an agent account"))
        write_paper(conv, paper_dir)
        result.update(paper=conv.paper, findings=conv.findings, downloaded=conv.downloaded)
        if not any(f.level == "error" for f in conv.findings):
            article = _synthetic_article(paper_dir, conv.paper, today)
            note = f"Preview generated from issue #{issue['number']}. Not published; dates and article number are placeholders."
            result["pdf"] = pdf.build_pdf(article, article.latest, outdir / "preview.pdf", status_note=note)
    except Exception as exc:  # report every failure back to the author instead of crashing the workflow
        result["findings"].append(validate.Finding("error", "conversion", str(exc)))
    return result


def report_markdown(result: dict, artifact_url: str | None = None) -> str:
    errors = [f for f in result["findings"] if f.level == "error"]
    warnings = [f for f in result["findings"] if f.level == "warning"]
    status = "Ready for screening" if not errors else "Needs changes"
    lines = [PREVIEW_MARKER, f"### Automated check: {status}", ""]
    if result.get("summary"):
        lines += [result["summary"], ""]
    if errors:
        lines += ["**Errors** (edit the issue to fix them; this comment updates automatically):", ""]
        lines += [f"- {f.where}: {f.message}" for f in errors] + [""]
    if warnings:
        lines += ["**Warnings:**", ""] + [f"- {f.where}: {f.message}" for f in warnings] + [""]
    paper = result.get("paper")
    if paper:
        kind = "sections" if "sections" in paper else ("PDF" if "pdf" in paper else paper.get("body_file", "?"))
        lines += [
            "| Field | Value |", "|---|---|",
            f"| Title | {paper.get('title', '')} |",
            f"| Type | {model.ARTICLE_TYPES.get(paper.get('article_type', ''), paper.get('article_type', ''))} |",
            f"| Authors | {', '.join(a.get('name', '') for a in paper.get('authors', []))} |",
            f"| Language | {model.language_name(paper.get('language', 'en'))} |",
            f"| Tags | {', '.join(model.canonical_tags(paper.get('tags', [])))} |",
            f"| Body | {kind} |",
            f"| DOI requested | {'yes' if paper.get('mint_doi', True) else 'no'} |",
            f"| AI contribution | {(model.ai_info(paper) or {}).get('label', 'not stated')} |",
            "",
        ]
        if paper.get("language", "en").split("-")[0] != config.journal()["translation"]["target"]:
            lines += ["An English AI translation will be generated at acceptance and labelled as machine-translated.", ""]
        lines += ["<details><summary>Generated paper.yml</summary>", "", "```yaml", config.dump_yaml(paper).rstrip(), "```", "</details>", ""]
    if result.get("pdf") and artifact_url:
        lines += [f"Typeset preview (PDF): [download the workflow artifact]({artifact_url})", ""]
    lines.append("_Submissions that pass these checks are screened by the AI editorial agent (scope and spam, not quality). "
                 "The maintainer makes the final decision with the `accepted` label or a `/accept` comment._")
    return "\n".join(lines) + "\n"
