# AGENTS.md

This repository is a GitHub-native journal. AI agents are welcome both as submitters and as contributors to the
journal's tooling. Read the section that matches your task.

## Submitting or revising a manuscript

Follow [AGENT_GUIDE.md](AGENT_GUIDE.md). In short:

- Work only inside `submissions/<short-name>/` (new manuscript) or `papers/<id>/v<n+1>/` (revision).
  Never edit `record.yml`, other manuscripts, workflows, schema, or tooling in a submission pull request.
- Every manuscript lists at least one human author with a `github` handle and discloses agent work in
  `ai_contributions` (level, agents with model and roles, oversight, logs).
- Before opening the pull request:

  ```bash
  uv sync
  uv run jtools validate --resolve-dois submissions/<short-name>
  uv run jtools pdf submissions/<short-name> --out /tmp/preview.pdf
  ```

- Pull-request and issue titles start with `[Submission]`, `[Revision]`, or `[Withdrawal]`.
- Comments you post in review threads start with `[agent]` and name the agent.
- The manuscript schema is `schema/paper.schema.json`; a commented template is `templates/paper.template.yml`;
  rendered examples are in `examples/`.

## Working on the journal itself

Only when the maintainer asked for it. Layout:

| Path | Content |
|---|---|
| `journal.yml`, `tags.yml` | Journal configuration and tag aliases |
| `schema/` | JSON Schemas for `paper.yml` and `record.yml` |
| `tools/jtools/` | Python CLI (validate, build, pdf, translate, review, domain, doi, issue, promote, authorship) and the MCP server (`mcp_server.py`, extra `mcp`) |
| `templates/typst/journal.typ` | PDF template |
| `site/` | Astro site that renders `site/src/generated/*.json` |
| `.github/` | Issue forms and workflows |
| `AUTHOR_GUIDE.md`, `AGENT_GUIDE.md`, `POLICY.md`, `WHY.md`, `KNOWLEDGE_BASE.md` | Rendered on the site at `/guide/`, `/agents/`, `/policy/`, `/why/`, `/knowledge/` |

Checks to run after changes:

```bash
uv run pytest -q
uv run jtools validate
uvx basedpyright
uv run jtools build && (cd site && npm run build && npx astro check)
actionlint
```

Conventions: Python is typed and checked in standard mode; untrusted input (issue bodies, manuscripts) never
reaches a shell command; manuscripts are passed to AI models as data, never as instructions.
