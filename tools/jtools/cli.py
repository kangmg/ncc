from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import config, model


def cmd_validate(args) -> int:
    from . import validate

    targets = [Path(p) for p in args.paths] or validate.default_targets()
    findings = validate.validate_paths(targets, resolve_dois=args.resolve_dois)
    for f in findings:
        print(f)
    errors = sum(f.level == "error" for f in findings)
    print(f"{len(targets)} manuscript(s) checked, {errors} error(s), {len(findings) - errors} warning(s)")
    return 1 if errors else 0


def cmd_build(args) -> int:
    from . import export

    export.build_all(with_pdf=not args.no_pdf)
    return 0


def cmd_pdf(args) -> int:
    from . import pdf

    path = Path(args.path).resolve()
    article = model.load_article(path) if (path / "record.yml").exists() else model.load_example(path)
    version = article.versions[(args.version or article.latest.number) - 1]
    out = Path(args.out or config.BUILD / f"{article.key(version.number)}.pdf")
    pdf.build_pdf(article, version, out, translated=args.translated)
    print(out)
    return 0


def cmd_translate(args) -> int:
    from . import translate

    if args.pending:
        target = config.journal()["translation"]["target"]
        dirs = [v.dir for a in model.discover_articles() for v in a.versions
                if v.language.split("-")[0] != target and v.translation is None and a.record["status"] == "published"]
    else:
        dirs = [Path(p) for p in args.paths]
    for d in dirs:
        out = translate.translate_version(d, force=args.force)
        if out:
            print(out)
    return 0


def cmd_doi(args) -> int:
    from . import zenodo

    if args.action == "due":
        for article, version in zenodo.due_versions():
            print(article.key(version.number))
    elif args.action == "mint":
        zenodo.mint_due(dry_run=args.dry_run)
    elif args.action == "withdraw":
        zenodo.mark_withdrawn(args.id)
    return 0


def _event_issue(path: str) -> dict:
    event = json.loads(Path(path).read_text(encoding="utf-8"))
    return event["issue"] if "issue" in event else event


def cmd_issue(args) -> int:
    from . import issue

    data = _event_issue(args.event)
    if args.action == "preview":
        result = issue.preview(data, Path(args.out))
        report = issue.report_markdown(result, args.artifact_url)
        Path(args.report).write_text(report, encoding="utf-8")
        has_pdf = bool(result.get("pdf"))
        print(json.dumps({"ok": not any(f.level == "error" for f in result["findings"]), "pdf": has_pdf, "kind": result["kind"]}))
        return 0
    try:
        summary = issue.apply(data)
    except issue.IssueError as exc:
        Path(args.summary).write_text(f"Could not apply issue #{data['number']}: {exc}\n", encoding="utf-8")
        print(f"error: {exc}", file=sys.stderr)
        return 2
    errors = [f for f in summary["findings"] if f.level == "error"]
    lines = [f"Publishes {summary['kind']} for **{summary['id']}**" + (f" (v{summary['version']})" if summary["version"] else ""),
             "", f"Closes #{data['number']}"]
    if summary["findings"]:
        lines += ["", "Validation findings:"] + [f"- {f}" for f in summary["findings"]]
    Path(args.summary).write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"id": summary["id"], "version": summary["version"], "kind": summary["kind"],
                      "dir": str(Path(summary["dir"]).relative_to(config.ROOT)), "errors": len(errors)}))
    return 1 if errors else 0


def cmd_authorship(args) -> int:
    from . import issue

    problems = []
    articles = {p.split("/")[1] for p in args.paths if p.startswith("papers/") and len(p.split("/")) > 2}
    for article_id in sorted(articles):
        if (config.PAPERS / article_id / "record.yml").exists():
            try:
                issue.check_authorised(issue.find_article(article_id), args.login)
            except issue.IssueError as exc:
                problems.append(str(exc))
    submissions = {p.split("/")[1] for p in args.paths if p.startswith("submissions/") and len(p.split("/")) > 2}
    for name in sorted(submissions):
        paper_path = config.ROOT / "submissions" / name / "paper.yml"
        if paper_path.exists():
            paper = config.load_yaml(paper_path)
            if args.login.lower() not in issue.human_handles(paper) | issue.agent_handles(paper):
                print(f"warning: @{args.login} is not listed as an author or agent account of submissions/{name}")
    for p in problems:
        print(f"error: {p}")
    return 1 if problems else 0


def cmd_review(args) -> int:
    from . import review

    try:
        result = review.review(Path(args.path))
    except review.ReviewError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    Path(args.report).parent.mkdir(parents=True, exist_ok=True)
    Path(args.report).write_text(review.report_markdown(result), encoding="utf-8")
    print(json.dumps({"recommendation": result["recommendation"], "hidden_text": result["hidden_text"]}))
    return 0


def cmd_domain(args) -> int:
    from . import domain

    for path in domain.move(args.url, args.base):
        print(path.relative_to(config.ROOT))
    print(f"site root is now {domain.site_root(args.url, args.base)}/")
    return 0


def cmd_promote(args) -> int:
    from . import issue

    for item in issue.promote_submissions():
        print(item)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="jtools", description="Notes in Chemical Computation tooling")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("validate", help="validate articles, examples, or given manuscript folders")
    p.add_argument("paths", nargs="*")
    p.add_argument("--resolve-dois", action="store_true", help="fail on reference DOIs that do not resolve (needs network)")
    p.set_defaults(func=cmd_validate)

    p = sub.add_parser("build", help="render every article and export site data")
    p.add_argument("--no-pdf", action="store_true")
    p.set_defaults(func=cmd_build)

    p = sub.add_parser("pdf", help="typeset one article or example")
    p.add_argument("path")
    p.add_argument("--version", type=int)
    p.add_argument("--translated", action="store_true")
    p.add_argument("--out")
    p.set_defaults(func=cmd_pdf)

    p = sub.add_parser("translate", help="AI-translate non-English versions into English")
    p.add_argument("paths", nargs="*")
    p.add_argument("--pending", action="store_true", help="translate every published version that lacks one")
    p.add_argument("--force", action="store_true")
    p.set_defaults(func=cmd_translate)

    p = sub.add_parser("doi", help="Zenodo DOI registration")
    p.add_argument("action", choices=["due", "mint", "withdraw"])
    p.add_argument("id", nargs="?")
    p.add_argument("--dry-run", action="store_true")
    p.set_defaults(func=cmd_doi)

    p = sub.add_parser("issue", help="process a GitHub issue event")
    p.add_argument("action", choices=["preview", "apply"])
    p.add_argument("--event", required=True, help="path to the GitHub event JSON (or an issue JSON)")
    p.add_argument("--out", default=str(config.BUILD / "preview"))
    p.add_argument("--report", default=str(config.BUILD / "preview-report.md"))
    p.add_argument("--artifact-url")
    p.add_argument("--summary", default=str(config.BUILD / "apply-summary.md"))
    p.set_defaults(func=cmd_issue)

    p = sub.add_parser("authorship", help="check that a GitHub user may change the given paths")
    p.add_argument("login")
    p.add_argument("paths", nargs="*")
    p.set_defaults(func=cmd_authorship)

    p = sub.add_parser("promote", help="assign IDs to pull-request submissions and register new version folders")
    p.set_defaults(func=cmd_promote)

    p = sub.add_parser("review", help="AI screening of a manuscript folder (scope and spam, not quality)")
    p.add_argument("path", help="folder with paper.yml, e.g. build/preview/paper or submissions/<name>")
    p.add_argument("--report", default=str(config.BUILD / "review.md"))
    p.set_defaults(func=cmd_review)

    p = sub.add_parser("domain", help="move the site to another address, e.g. a custom domain")
    p.add_argument("url", help="scheme and host, e.g. https://journal.example.com")
    p.add_argument("--base", default="", help='path under the host; "" for a custom domain (default), "/journal" for a project page')
    p.set_defaults(func=cmd_domain)

    args = parser.parse_args(argv)
    if args.command == "doi" and args.action == "withdraw" and not args.id:
        parser.error("doi withdraw needs an article ID")
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
