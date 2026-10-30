Notes in Chemical Computation is a small, non-commercial journal for computational chemistry that would otherwise go
unpublished. This page explains why it exists, how it works, what it is not, and how you can check every claim made
here.

## Sharing results should be cheap

Computational chemists often hold results worth sharing: a careful benchmark, a convergence study, a reproduction of
a published number, a negative result, a small tool. Turning them into a paper means framing a story, polishing
prose, formatting for a journal, and waiting through review. That costs more time and effort than many of these
results can justify, so most of them stay in scratch directories where nobody can find, cite, or build on them.

Notes in Chemical Computation exists to make sharing them fast and easy. An article can be short: what was computed,
how, what came out, and where the data are. It is published as HTML and PDF, versioned like a preprint, and given a
DOI.

This is not a preprint server. A preprint shares a manuscript early, on its way to a journal. This journal is for
results that may never take the shape a journal expects, and it aims for a low barrier rather than a stage on the way
somewhere else.

## Agents are encouraged

Writing up results is exactly the kind of work AI agents do well. Authors are encouraged to let agents turn
notebooks and output files into manuscripts and submit them. The only conditions are that agent use is disclosed and
that a named human author stands behind the article.

## Open knowledge

Published articles form an open knowledge base. Every article is available as structured data and plain Markdown,
and an MCP server lets AI agents search and read the journal directly, with citations and DOIs attached. Reuse is
free under each article's licence, with attribution.

## What screening is for, and what it is not

Screening does not evaluate the quality, novelty, or importance of the research. Its only purpose is to keep out spam
and submissions that do not fit the journal's purpose.

1. **Automated checks:** required metadata, a typeset preview, and resolution of every reference DOI.
2. **AI screening:** an AI agent checks that the submission is in scope, reports genuine computational results, says
   enough about methods and data for a reader to know what was done, discloses AI use, and contains no hidden text
   aimed at AI systems. Its report is posted publicly.
3. **Confirmation:** the founder and maintainer confirms each decision before anything is published.

Readers should treat articles as shared results, not as peer-reviewed findings, and article pages say so.

## What this journal is not

- It is not a commercial publisher. Publishing and reading are free, with no paid fast track and no advertising.
- It does not send unsolicited invitations to submit, review, or join an editorial board. Such an email in its name is
  not from us.
- It is not indexed in Web of Science or Scopus and has no impact factor, and it will not claim otherwise.
- It does not do peer review. A result shared here can later grow into a full paper submitted elsewhere, and its
  versions here stay online as a record.
- It does not arbitrate disputes. Authors are responsible for their submissions, including authorship, rights, and
  conflicts that arise later; see the [disclaimer](https://kangmg.github.io/ncc/policy/#disclaimer).
- If you plan to submit the same work to another journal, check that journal's rules on prior publication first. An
  article here has a DOI and may count as published.

## How to check us

- Founder and maintainer: Mingi Kang ([GitHub @kangmg](https://github.com/kangmg)), computational chemist.
- Every submission, screening report, and decision is a public GitHub issue or pull request, and every change to an
  article is in the Git history.
- DOIs are registered on Zenodo, operated by CERN.
- The platform is [open source](https://github.com/kangmg/ncc).
- Articles are CC BY 4.0 by default, and authors keep their copyright.
- Policies are written down in the [editorial policy](https://kangmg.github.io/ncc/policy/).
