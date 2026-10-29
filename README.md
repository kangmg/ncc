# Notes in Chemical Computation

An open, GitHub-native journal for computational chemistry, simulation, and AI for science.
Authors submit through issues or pull requests, an AI editorial agent screens them for scope and spam, the maintainer approves, and the site, PDFs, AI translations, and
Zenodo DOIs are produced automatically.

- Site: https://kangmg.github.io/journal/
- For authors: [AUTHOR_GUIDE.md](AUTHOR_GUIDE.md), [examples/](examples/), [templates/paper.template.yml](templates/paper.template.yml)
- AI agents: [AGENT_GUIDE.md](AGENT_GUIDE.md) (submission contract), [AGENTS.md](AGENTS.md) (repository instructions),
  and on the site `/agents/`, `/agents.md`, `/llms.txt`, `/schema/paper.schema.json`
- Knowledge base: [KNOWLEDGE_BASE.md](KNOWLEDGE_BASE.md) (`/api/v1/index.json`, `/articles/<id>.md`, `/llms-full.txt`) and the MCP
  server `ncc-mcp` (`uvx --from "jtools[mcp] @ git+https://github.com/kangmg/journal" ncc-mcp`)
- Why this journal: [WHY.md](WHY.md)
- Policies: [POLICY.md](POLICY.md), including the disclaimer

## How it works

```
Issue form ──► submission-preview.yml ──► bot comment: validation + paper.yml + preview PDF
                     (edit issue → re-check)   └► AI screening report comment (first pass; `/review` to redo)
Maintainer: label `accepted` or comment /accept
          └► editorial.yml ──► papers/<id>/v1 + record.yml (+ AI translation) ──► pull request
Pull request (submissions/<name>/) ──► pr-check.yml (scope, authorship, schema, PDFs, AI screening in job summary)
Merge to main ──► deploy.yml ──► assign IDs, translate, render HTML + Typst PDFs, Astro site ──► Pages
Daily ──► doi.yml ──► Zenodo DOI for versions older than the grace period ──► record.yml ──► redeploy
```

Merging into `main` is the only publication gate. Other commands in an issue (owner only): `/revise` and `/decline`.

## Repository layout

| Path | Content |
|---|---|
| `journal.yml` | Name, maintainer, URLs, subjects, review and translation models, DOI settings |
| `tags.yml` | Canonical tag names and aliases; `journal.yml` maps tags to subjects |
| `schema/` | JSON Schemas for `paper.yml` and `record.yml` |
| `papers/<YYYY-NNNN>/record.yml` | Editorial record: dates, status, versions, DOIs (bot-managed) |
| `papers/<YYYY-NNNN>/v<n>/` | One folder per version: `paper.yml`, figures, `translation.en.yml` |
| `submissions/` | Pull-request submissions waiting for an ID (moved into `papers/` on merge) |
| `examples/` | Rendered example manuscripts for each body format |
| `AUTHOR_GUIDE.md`, `AGENT_GUIDE.md`, `POLICY.md`, `WHY.md`, `KNOWLEDGE_BASE.md` | Rendered at `/guide/`, `/agents/`, `/policy/`, `/why/`, `/knowledge/` |
| `templates/typst/journal.typ` | PDF template; `templates/csl/` holds the ACS citation style |
| `tools/jtools/` | Python CLI: validate, build, pdf, translate, doi, issue, promote, authorship |
| `site/` | Astro site that renders the exported data |
| `.github/` | Issue forms and workflows |

## Local use

Requirements: [uv](https://docs.astral.sh/uv/), pandoc 3.x, Typst 0.15+, Node 22+.

```bash
uv sync
uv run jtools validate                 # all articles and examples
uv run jtools pdf examples/research-article --out /tmp/example.pdf
uv run jtools build                    # HTML, PDFs, subjects -> site/src/generated, site/public/papers
cd site && npm install && npm run dev  # http://localhost:4321/journal/
uv run pytest -q
```

## One-time setup on GitHub

1. Create the repository `kangmg/journal` (public) and push this folder.
2. Settings → Pages → Source: **GitHub Actions**.
3. Settings → Actions → General → Workflow permissions: **Read and write**, and tick
   **Allow GitHub Actions to create and approve pull requests** (needed by `editorial.yml`).
4. Create labels: `submission`, `revision`, `withdrawal`, `accepted`, `ready-for-review`, `needs-changes`,
   `revision-requested`, `declined`.
   ```bash
   for l in submission revision withdrawal accepted ready-for-review needs-changes revision-requested declined; do gh label create "$l" --repo kangmg/journal --force; done
   ```
5. Zenodo: create a token with `deposit:write` and `deposit:actions` on https://sandbox.zenodo.org and save it as the
   secret `ZENODO_SANDBOX_TOKEN`. Run the DOI workflow manually with `dry_run`, then for real against the sandbox.
   When satisfied, create a token on https://zenodo.org, save it as `ZENODO_TOKEN`, and set `doi.sandbox: false` in
   `journal.yml`. Optionally create a Zenodo community and set `doi.community`.
6. AI translation uses GitHub Models through the workflow's built-in token (`models: read`); no secret is needed.
   To use another OpenAI-compatible provider, set `TRANSLATE_BASE_URL`, `TRANSLATE_MODEL`, and `TRANSLATE_API_KEY`.
7. Optional: enable Discussions and fill the `comments.giscus` ids in `journal.yml`.

## Changing the name

Edit `journal.yml` (title, abbreviation, `github.repo`). Everything else reads from it.

## Moving to a custom domain

The site, PDFs, citations, feeds, and DOI metadata read the address from `journal.yml`. One command updates it
and the addresses spelled out in the guides, issue forms, and schema:

```bash
uv run jtools domain https://journal.example.com     # custom domain at the root
uv run jtools domain https://kangmg.github.io --base /journal   # back to the project page
```

Then, once:

1. At the domain registrar, add DNS records: for the apex domain, `A` records to `185.199.108.153`,
   `185.199.109.153`, `185.199.110.153`, `185.199.111.153`; for a subdomain, a `CNAME` to `kangmg.github.io`.
2. In the repository: Settings, Pages, Custom domain: enter the domain, wait for the DNS check, enable
   "Enforce HTTPS". No `CNAME` file is needed because the site is deployed by a workflow.
3. Commit and push the changes from `jtools domain`; the deploy workflow rebuilds every page and PDF.

Published papers are not rewritten. Their old links and the URLs already registered with Zenodo keep
working because GitHub Pages redirects the github.io address to the custom domain.
