## Article types

| Type | Use it for | Typical length |
|---|---|---|
| Research Article | A complete study with methods, results, and discussion | 2,000 to 6,000 words |
| Letter | One sharp result that deserves quick publication | up to 2,000 words |
| Computational Note | A focused calculation: a convergence test, a benchmark, a method detail | up to 2,500 words |
| Software | A tool or library: what it does, why it is needed, how to use it | up to 2,000 words |
| Negative Result | An approach that did not work, documented so others can skip it | any |
| Tutorial | A worked, reproducible walkthrough | any |
| Perspective | An argued opinion on a direction in the field | up to 3,000 words |

## The manuscript file

Every manuscript is one `paper.yml`. Figures and other files sit next to it and are referenced by relative path.
The full machine-readable rules are in `schema/paper.schema.json`; a commented template is in
`templates/paper.template.yml`.

### Required fields

| Field | Content |
|---|---|
| `title` | The article title |
| `article_type` | One of `research-article`, `letter`, `computational-note`, `software`, `negative-result`, `tutorial`, `perspective` |
| `authors` | A list; each author has a `name`, and at least one author has a `github` handle |
| `abstract` | At least 50 characters; Markdown and math allowed |
| `tags` | One to twelve free-form keywords; they place the article in the journal's [subjects](https://kangmg.github.io/ncc/subjects/) |
| `data_availability` | Where readers find inputs, outputs, and scripts |
| `ai_use` | How AI tools were used in the work or the writing, or "None" |
| a body | Exactly one of `sections`, `body_file`, or `pdf` (below) |

All submission types, including tutorials and perspectives, must share computational results or a tool the authors
built. Opinion-only essays without computation are outside the screening criteria.

### Optional fields

`language` (default `en`), `subtitle`, `affiliations`, author `orcid`/`email`/`corresponding`,
`license` (default `CC-BY-4.0`; also `CC-BY-SA-4.0`, `CC0-1.0`), `toc_graphic` (graphical abstract),
`ai_contributions` (structured AI disclosure; required when AI did more than light editing),
`references` or `bibliography`, `code_availability`, `acknowledgments`, `funding`, `competing_interests`,
`supporting_information`, `mint_doi` (default `true`), and `changelog` for revised versions.

### Supporting information and manuscript assets

Small supporting information (SI) files may live under `si/` beside `paper.yml`. Allowed extensions are
`.xyz`, `.cif`, `.pdb`, `.mol`, `.sdf`, `.gif`, `.csv`, `.txt`, `.json`, and `.pdf`.
For larger SI, use an external public HTTPS URL, preferably a version DOI for the exact dataset or release:

```yaml
supporting_information:
  - file: si/structure.xyz
    description: Relaxed structure.
  - url: https://doi.org/10.5281/zenodo.1234567
    description: Inputs, outputs, and analysis scripts for this version.
```

Each entry has `description` and exactly one of `file` or `url`. Pull requests use `file` for local SI.
In the Issue form's **Supporting information** field, enter one `URL | description` per line for external SI.
For small local SI, attach a GitHub file link using the same syntax, with an explicit extension-bearing filename
in the link; a GIF link label must end in `.gif`. These attachments are fetched into `si/` and count toward the
limits below. External SI records are linked, not automatically downloaded.
For field-based revisions, a blank field retains the existing list; `None` clears it. A complete `paper.yml`
is authoritative unless a separate **Supporting information** field is supplied, which replaces its list.
Required data must be public when the article is published, even if a data DOI is still pending.

Manuscript assets and local SI share limits of 5 MiB per file, 15 MiB per version, and 10 files per version.
The budget applies to the whole version, including retained files in a revision.
These limits exclude `paper.yml`, `translation.*.yml`, and generated PDFs. A submitted PDF counts toward all
three limits. ZIP and other direct archive uploads are rejected; link external SI records instead.
External records may contain archives. The journal archives manuscript source, local SI, direct assets, and article PDFs. External SI remains an independent
linked record and isn't copied into the journal archive.

### Three ways to supply the body

1. **`sections`** (recommended). A list of `{title, body}` written in Markdown. The journal typesets both the
   web page and the PDF, so the article gets full HTML, search, and a consistent layout.
2. **`body_file`**. A `.md` file (treated like sections) or a `.typ` Typst file. Typst manuscripts are compiled as
   written and appear as a PDF behind a journal cover page.
3. **`pdf`**. A finished PDF from LaTeX, Word, or anything else. The article page shows the metadata, the abstract,
   and the PDF with a journal cover page.

## Writing in Markdown

| You want | Write |
|---|---|
| Inline math | `$E_a = E_\text{TS} - E_\text{IS}$` |
| Display math | `$$ ... $$` on its own lines |
| A citation | `[@perdew1996]`, several: `[@perdew1996; @larsen2017]` |
| A figure | `![Caption text.](figures/parity.svg){#fig:parity width=70%}` on its own line |
| A figure reference | `Figure @fig:parity` (becomes "Figure 1") |
| A table caption | a line `: Caption text. {#tbl:setup}` directly under the table |
| A table reference | `Table @tbl:setup` |
| Code | fenced blocks with a language name |

Figures and tables are numbered automatically in order of appearance. SVG, PNG, and JPEG figures work; prefer SVG
or PNG at 300 dpi. Raw HTML and raw LaTeX are not allowed; use Markdown.

## References

List references under `references`. A DOI is enough; the metadata is fetched when the article is built:

```yaml
references:
  - id: perdew1996
    doi: 10.1103/PhysRevLett.77.3865
  - id: mycode
    text: "M. Kang, aseview, version 0.3 (2026), https://github.com/kangmg/aseview"
```

Alternatively, point `bibliography` at a BibTeX or CSL-JSON file. References are formatted in ACS style.

## Language and AI translation

Write in any language and set `language` (for example `ko`). When a non-English manuscript is accepted, the journal
produces an English translation with an AI model. The translation is shown by default on the article page and as a
separate PDF, always with this notice: it was produced by AI, it may contain mistranslations, and the original is
the version of record. Readers can switch to the original at any time. If you prefer to provide your own
translation, attach `translation.en.yml` and set `machine_translated: false` in it.

## Versions, withdrawal, and DOIs

Each accepted revision becomes a new version (v2, v3, ...) and all earlier versions stay readable. Include a
`changelog`. Withdrawn articles keep a notice page with the title, authors, dates, and reason. DOIs are registered on
Zenodo by a daily scheduled job once 14 days have elapsed from the recorded version date, subject to the DOI
configuration and independent of any data DOI. This isn't an exact wall-clock publication guarantee, and the
recorded date isn't automatically corrected to the merge date. The current configuration uses Zenodo sandbox
(`doi.sandbox: true`), not production registration.
Each version gets its own DOI and a concept DOI points to
the latest version. Set `mint_doi: false` if you do not want a DOI.

## Working with AI agents

AI agents may design and run the study, write the manuscript, and submit it. A human author stays responsible, and
the agent's part is disclosed in `ai_contributions`: the level (`assisted`, `substantial`, or `agent-led`), each agent
with its model and roles and what humans checked; run logs are strongly recommended for agent-led work. The full rules, including the
commands an agent runs, are in the [guide for AI agents](https://kangmg.github.io/ncc/agents/).

## Submitting

- **Issue form (recommended, no clone needed)**: open "Submit a manuscript" in the GitHub repository. Paste Markdown
  sections or a complete `paper.yml`, or attach a PDF or `.typ`/`.md` file and individual figures within the limits above.
  Add external SI URLs or small local SI attachment links in **Supporting information**. The bot replies with a preview.
- **Pull request (optional)**: add `submissions/<short-name>/paper.yml` with its files. Run `uv run jtools validate submissions/<short-name>`
  locally to check it first. Revisions by pull request add a `papers/<id>/v<n>/` folder with a `changelog`.

### Optional partial and sparse clone for a pull request

An ordinary clone includes local SI. To avoid downloading unrelated manuscript and SI blobs, combine a partial
clone with sparse checkout; this isn't the default for every clone. Fork the repository on GitHub first, then:

```bash
git clone --filter=blob:none --sparse https://github.com/YOUR-HANDLE/ncc.git
cd ncc
git sparse-checkout set tools schema templates
uv sync
git switch -c submit/my-note
mkdir -p submissions/my-note
cp templates/paper.template.yml submissions/my-note/paper.yml
# Edit your paper.yml and add only your manuscript assets and optional si/ files.
uv run jtools validate --resolve-dois submissions/my-note
git add submissions/my-note
git commit -m "Submission: <title>"
git push -u origin submit/my-note
gh pr create --repo kangmg/ncc --title "[Submission] <title>"
```

Root configuration and documentation files remain included. Validate only your own target in this checkout;
global validation and builds need the omitted `examples/`, `site/`, and `papers/` trees.
For a revision, first run `git sparse-checkout add papers/<id>/v<N>` for your own new version path, then create,
validate, and stage only that folder and open a `[Revision]` pull request. Partial and sparse clones reduce client
downloads, not server storage: local SI still grows the Git repository and its history on the server.

## Checklist

- The title says what was found, not only what was done.
- The abstract states the system, the method, and the main number.
- Every figure has a caption that can be read without the text.
- Required inputs, outputs, and scripts are publicly available by article publication and linked in the data availability statement.
- AI use is declared, and `ai_contributions` is filled in if AI did more than light editing.
