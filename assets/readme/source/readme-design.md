# NCC README design

Audience: Researchers and agents sharing small computational results; maintainers are secondary.
Value: Small findings deserve to be shared.
First action: Read a note or open the clone-free submission Issue form.
Proof: Existing published editorial and rendered manuscript examples.
Scope: README presentation, static header and submission-process assets only.

Plan: Lead with the approved header and submission links; replace the ASCII workflow with an illustrated overview; keep operational details in expandable sections without dropping submission limits or DOI caveats.
Validation: Skill asset audits, local-link checks, diagram XML/safety checks, desktop/mobile renders, and repository checks. No application behavior changes or new runtime dependencies.

Skills: beautify-github-readme; diagram-design (https://github.com/cathrynlavery/diagram-design).
Diagram type: Simplified process overview, five stages, mixed audience; successful path only. Revision/decline branches and workflow filenames remain in expandable text.
Output: Self-contained HTML sources and GitHub-safe SVG exports. Desktop 1200 x 368; mobile 600 x 1028. Diagram subtitle and footer notes removed at the user's request; policy and DOI context remain in README prose.

Brand source: site/src/styles/global.css. The current header is pure SVG (../ncc-header.svg); its text, surface mesh, reaction path, and research-note illustration are editable vector elements.
Paper #f3f6fa; surface #ffffff; ink #1c2b3c; blue #244c76; muted #536577; rule #d9e3ec; gold #d7ae62; gold text #87621a; gold tint #fff8e9.
Typography: Website family names with portable system fallbacks (Newsreader / Georgia; Source Sans 3 / Helvetica / Arial). SVG exports intentionally use system fallbacks without external fonts.

Facts: Issue or PR; validation and AI screening; maintainer decision; merge to main publishes; a separate daily job considers DOI registration after 14 days from the recorded version date. Current DOI configuration is Sandbox, not production. Screening is not peer review; agents require a responsible human author.
