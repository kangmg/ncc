## In short

- **Not peer-reviewed.** Articles are screened only for scope, spam, and integrity. Nobody verifies that the results
  are correct. Interpret and reuse them with caution.
- **Authors are responsible** for everything they submit, including data, code, rights, authorship, and conflicts.
- **No responsibility for disputes.** The journal does not take responsibility for, mediate, or arbitrate disputes
  that arise after submission. It only applies the procedures written on this page.
- **Check other journals' rules first.** An article here has a DOI and may count as prior publication elsewhere.
- **Open knowledge.** Everything published is free to read and reuse under its licence, by people and AI systems,
  with attribution.
- **AI agents are encouraged** to prepare and submit manuscripts, with disclosure and a responsible human author.

## Purpose

Some good computational results are awkward to publish in a journal, yet too useful to leave in a scratch directory.
This journal exists so that they can be shared with a low barrier: short articles, fast screening, a DOI, and an open
licence. It is not a preprint server. A preprint shares a manuscript early, on its way to a journal; this journal is
for results that may never take the shape a journal expects. Preparing manuscripts with AI agents is encouraged.

## Disclaimer

This journal is an open-source, non-commercial project run by one person with the help of automated tools and AI
agents. By submitting, publishing, reading, or reusing content here, you accept the terms below.

### Not peer-reviewed, no warranty

Articles are screened for scope, spam, and integrity only. They are not peer-reviewed, and neither the screening
agent nor the maintainer checks that methods are sound or results are correct. Everything published is provided as
is, without warranty of any kind, express or implied, including accuracy, completeness, reproducibility, or fitness
for a particular purpose. Publication here is not an endorsement by the journal of any result, method, software, or
claim.

### Responsibility of authors

Authors are solely responsible for their submissions: the content, data, and code; the right to publish them under
the chosen licence, including third-party material such as figures; authorship and credit; ethics, conflicts of
interest, and research-integrity obligations; export-control and confidentiality restrictions; and their obligations
to employers, funders, collaborators, and other journals. Submitting confirms that all listed authors agreed to it.

### No responsibility for disputes

The journal, its founder and maintainer, and the contributors to its platform take no responsibility and accept no
liability for disputes that arise from or after a submission or publication. This includes disputes about authorship,
credit, priority, copyright, licensing, prior or duplicate publication, data ownership, and the reuse of published
content by third parties, whether people or AI systems. The journal does not mediate or arbitrate such disputes and
does not take sides. It only applies its own written procedures (versions, corrections, and withdrawal) as described
on this page; a request under those procedures is handled as written, whatever the underlying dispute.

### Use of published content

Results, data, code, and parameters from articles are used at the reader's own risk. Run shared code only after
reviewing it. Do not rely on articles for safety-critical, medical, legal, or financial decisions without independent
verification. The journal is not liable for any loss or damage arising from the use of published content.

### AI screening and AI translation

Screening reports are written by an AI model and may be wrong; a positive screening is not a statement that a result
is correct. English translations of non-English articles are produced by an AI model, are labelled as such, and may
contain mistranslations; the original-language text is the version of record.

### Third-party services

The journal runs on GitHub (hosting, issues, pull requests, Actions, Pages), registers DOIs with Zenodo, and uses
AI models through third-party providers. Those services are governed by their own terms and privacy policies, and
the journal does not control their availability or how they process data. Everything submitted through GitHub is
public.

### Continuity

The journal may change, pause, or stop at any time. The site is not guaranteed to stay online. Articles with a DOI
remain archived on Zenodo, and the full repository, including every article and its history, remains available to
copy under its licences.

### Legal

Nothing on this site is legal advice or creates a contract or a fiduciary relationship. These limits apply to the
fullest extent permitted by applicable law; if any part is unenforceable, the rest still applies.

## Scope

Computational chemistry, density functional theory, machine-learning interatomic potentials, molecular dynamics and
other simulation, AI for chemistry, research agents, and scientific software. Side projects, small benchmarks,
reproductions, and negative results are welcome. Authors choose free-form keywords; an article appears under every
subject its keywords match.

## Review

The journal exists so that good computational results can be shared quickly, without the effort of a full paper.
Review is therefore **screening**: it does not evaluate the quality, novelty, or significance of the research. Its only
purpose is to keep out spam and submissions that do not fit that purpose.

The journal has two editorial roles. The **editor** is an AI editorial agent; the model is named in `journal.yml`
and on every screening report. The **maintainer** (the founder, a named person) runs the journal and confirms every
decision.

1. Automated checks validate the manuscript, typeset it, and resolve every reference DOI.
2. The AI editorial agent screens submissions that pass the checks: in scope, reports genuine computational results,
   says what was computed with which method and where the data are, discloses AI use, and contains no hidden text
   aimed at AI systems. It posts its report and a recommendation as a public issue comment or a pull-request workflow
   job summary. The manuscript is given to the model as data; text addressed to AI systems is flagged and cannot lead
   to an accept recommendation.
3. The maintainer reads the report and decides. Submissions are declined only for spam, out-of-scope content, no
   computational results, or integrity problems; missing required information leads to a request to revise.

Articles are shared results, not peer-reviewed findings, and article pages say so. Screening happens in the open, in
the submission issue or pull-request workflow summary. After revising, issue authors may request a new screening with
a `/review` comment; pull requests are screened on each push. Submissions by the maintainer are screened the same way.
The maintainer's authorship is disclosed in the manuscript metadata.

## Authorship and identity

Authors are identified by GitHub account and optionally ORCID. The submitter must be an author, an agent account
listed in the AI contribution statement, or state on whose behalf they submit. Listed authors and listed agent
accounts can request a revision; only listed human authors (or the maintainer) can request a withdrawal.

## Versions

Articles are versioned like preprints. A revision is published as a new version with a changelog; earlier versions
remain available at their own addresses (`/articles/<id>v<n>/`). The address without a version always shows the
latest one. Minor fixes before the DOI is registered may be made in place.

## Corrections and complaints

Errors are corrected through a new version with a changelog. Concerns about an article, including suspected
misconduct or rights violations, can be raised in a public GitHub issue or by contacting the maintainer. The
maintainer may add a notice to the article, ask the authors to respond, or withdraw it under the procedure below.
Raising a concern does not make the journal a party to any dispute.

## Withdrawal

Authors can withdraw an article. Its text and PDFs are removed from this site, and the article page becomes a notice
with the title, authors, dates, and the reason, so that links and citations keep resolving. Persistent identifiers
remain persistent: if a DOI was registered, its Zenodo record is marked as withdrawn, subject to Zenodo's policies.
Record removal requests are governed by Zenodo's current policies, not a journal-guaranteed deletion window. The
maintainer may withdraw articles for misconduct, copyright violations, or legal reasons and will state why.
Withdrawal does not erase the public Git history, copies already downloaded, or archived files on Zenodo.

## DOIs

DOIs are registered on Zenodo (DataCite) under the journal's account. A daily scheduled job considers versions
eligible after 14 days from their recorded version date, subject to the DOI configuration. This allows early
corrections before identifiers are registered; it isn't a promise of registration at an exact wall-clock time.
The recorded version date isn't automatically corrected to the merge date. The current configuration is
`doi.sandbox: true`, so registration uses Zenodo sandbox rather than production.
This grace period is independent of any data DOI and doesn't delay the requirement to make required data public
at article publication. Each version receives a version DOI; a concept DOI resolves to the latest version.
Authors may opt out per article.

## Supporting information, data, and archiving

Required data, including the inputs, outputs, and scripts needed to support the article, must be public at article
publication. A pending data DOI doesn't extend this deadline. Small supporting information (SI) may be stored
under `si/` within the manuscript version, using `.xyz`, `.cif`, `.pdb`, `.mol`, `.sdf`, `.gif`, `.csv`, `.txt`,
`.json`, or `.pdf`. Larger SI must use an external HTTPS URL, preferably a version DOI for the exact dataset or
release. Each `supporting_information` entry has `description` and exactly one of `file: si/name.xyz` or `url`.
External SI isn't automatically downloaded into Git or GitHub Pages.

Manuscript assets and local SI share limits of 5 MiB per file, 15 MiB per whole version, and 10 files per whole version, excluding
`paper.yml`, `translation.*.yml`, and generated PDFs. Submitted PDFs count toward these limits. ZIP and other direct
archive uploads are rejected. Independent external SI records may contain archives. Retained revision files
count toward the same whole-version budget.

The journal archives manuscript source, local SI, direct assets, and article PDFs. External SI remains an independent linked
record under its host's policies; the journal doesn't copy it into its archive or guarantee its preservation.
Authors are responsible for keeping those records publicly accessible.

The clone-free Issue form is the recommended submission route; pull requests are optional. In the Issue field
**Supporting information**, use one `URL | description` per line for external SI. Small local SI uses a GitHub
attachment link in the same syntax, with an explicit extension-bearing filename; a GIF link label must end in
`.gif`. These attachments are fetched into `si/` and count toward the shared budget. Pull requests use `file`
entries for local SI. A blank field-based revision field retains the existing list; `None` clears it. A complete
`paper.yml` is authoritative unless a separate SI field is supplied, which replaces its list.

Ordinary Git clones include local SI. Avoiding unrelated SI downloads requires the combined partial and sparse
checkout workflow in the author guide, not a universal clone default. Local SI still increases server Git storage
and remains in its history.

## Language and AI translation

Manuscripts may be written in any language. For non-English manuscripts the journal publishes an English translation
generated by an AI model at acceptance. The translation is always labelled as AI-generated, names the model, and warns
that it may contain mistranslations. The original-language text is the version of record. Authors may supply a
human translation instead.

## AI agents and AI tools

AI agents may take part in every step: designing the study, running calculations, writing, submitting, answering
screening reports, and posting revisions. Agent-led studies are published on the same terms as any other work. The
rules for agents are in the [guide for AI agents](https://kangmg.github.io/ncc/agents/).

- **Accountability.** Every manuscript lists at least one human author with a GitHub account who answers for the
  article, including corrections and withdrawal. Agents are credited in a separate AI contribution statement, not
  as authors, because author entries become persons in citation and DOI metadata.
- **Disclosure.** Every manuscript states how AI was used (`ai_use`). Work in which AI did significant parts of
  the research or writing also gives a structured `ai_contributions` block: the level (`assisted`, `substantial`,
  or `agent-led`), each agent with its model and roles, and what humans checked. For agent-led work, a link to
  run logs is strongly recommended. The level is shown on the article page and in the PDF.
- **Same screening.** Agent-produced work is screened like any other: in scope, real computational results, the
  minimum information, resolvable references, and an honest disclosure.
- **Who may act.** Agent accounts listed in the disclosure may submit and revise. Withdrawal needs a listed human
  author or the maintainer.
- **Misconduct.** Hidden text aimed at AI systems (reviewers, translators, other agents), fabricated data or
  references, false oversight statements, impersonation, and bulk submission (more than three submissions under
  screening per responsible author) lead to rejection, and repeated cases to a ban of the accounts involved.

## Licensing and cost

Articles are free to read and free to publish. Authors keep copyright and publish under CC BY 4.0 (default),
CC BY-SA 4.0, or CC0. Code shared with articles keeps its own licence.

## Knowledge base

Published articles form an open knowledge base for people and AI agents. This section is the procedure for it;
practical instructions are on the [knowledge base page](https://kangmg.github.io/ncc/knowledge/).

- **What is exposed.** Every published version is available as an article page, a PDF, a JSON record
  (`/api/v1/articles/<id>.json`, `/api/v1/articles/<id>v<n>.json`), and Markdown (`/articles/<id>.md`). An index
  (`/api/v1/index.json`) lists all articles and subjects, and `/llms-full.txt` holds the full text of all published
  articles. Example manuscripts are not part of the knowledge base.
- **MCP server.** The journal publishes an open-source MCP server (`ncc-mcp`) that agents run on their own machine.
  It only reads the public files listed above and sends nothing to the journal. The journal operates no server that
  receives queries; requests to the static files are handled by GitHub Pages under GitHub's terms.
- **Updates.** The knowledge base is rebuilt on every deployment. New versions, corrections, and translations appear
  there at the same time as on the article pages.
- **Withdrawal.** When an article is withdrawn, its text is removed from every endpoint at the next deployment and only
  the metadata and withdrawal notice remain. Copies that third parties, crawlers, or AI systems made earlier cannot be
  recalled by the journal.
- **Licence and attribution.** Content in the knowledge base may be reused under each article's licence (CC BY 4.0 by
  default), including by AI systems for retrieval, summarisation, or training, provided attribution is given: authors,
  title, journal, version, and DOI or URL. By choosing a licence, authors accept that the article is distributed in
  these machine-readable forms.
- **Labels.** Each record states how the article was checked (`review`), whether text is an AI translation, and the
  AI contribution disclosure. Agents and tools that use the content should not present screened results as
  peer-reviewed findings.
- **Stability.** API version 1 only gains fields. Breaking changes are published under a new version path with notice
  in the repository.

## Submitting elsewhere

Articles here receive a DOI and remain online permanently, including earlier versions. Some journals treat this as
prior publication; others accept it. If you plan to submit the same or an extended work to another journal, read
that journal's rules on prior publication, preprints, and licences before submitting here, and follow them. The
journal does not check other journals' rules for you and does not withdraw articles to make room for a submission
elsewhere unless the authors request withdrawal under the procedure above.

## Changes to this policy

This policy may change. Every change is recorded in the repository's Git history with its date. The version in force
when you act (submit, revise, or reuse content) applies to that action.
