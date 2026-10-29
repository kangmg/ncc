# Design: Notes in Chemical Computation

## 1. Intent
Reads like a scholarly publisher's journal site (Nature, ACS, RSC, Elsevier): a coloured journal masthead with
the title as wordmark, a section navigation bar, a journal cover and facts on the home page, tables of contents
with article type, open-access mark, citation line, and PDF links, and article pages with an outline, a boxed
abstract with graphical abstract, and a tools column. Content first; navy for identity, blue for links and buttons,
gold for the cover and thin accents, including the warning banner's left border.

## 2. Colour roles
All roles use `light-dark()`; the reader's choice is stored in `localStorage.theme` and applied as
`data-theme` on `<html>` before first paint, otherwise the system setting wins.

| Role | Light | Dark |
|---|---|---|
| canvas `--bg` / surface `--surface` | #FFFFFF / #FFFFFF | #202D3C / #29394C |
| tint `--tint` (abstract, list abstracts, cite box) | #F3F6FA | #29394C |
| text `--text` | #1C2B3C | #F0F4F8 |
| muted `--muted` | #536577 | #C0CCDA |
| hairline `--border` | #D9E3EC | #4D6074 |
| rule `--rule` (2px section rules, table rules) | #1C2B3C | #C9D3DF |
| ink `--ink` (links, labels) | #215B9A | #C0D9F5 |
| primary button / text | #2866A3 / #FFFFFF | #A9C0E0 / #112139 |
| secondary button border | #8DAED3 | #6F8DB5 |
| masthead gradient (110 degrees) | #1C3558 -> #28517D -> #3F739D | #293E57 -> #34516E -> #426D91 |
| `--band-deep` (utility strip, footer) | #162B47 | #29394C |
| gold `--gold` (2px masthead/footer rules, cover, PDF header) | #D7AE62 | #D7AE62 |
| open access `--oa` | #87621A | #E6C27E |
| search background / text | #FFFFFF / #1C2B3C | #2D425B / #F0F4F8 |
| caution background / text / left border | #FFF8E9 / #6A4A12 / #D7AE62 | #40392F / #F3E3C3 / #B8934E |
| danger (example, withdrawn) | #FDEBEC / #9F2F2D | #3D1F1F / #F2A7A5 |

## 3. Type
Wordmark, titles, section heads, article body: Newsreader (variable), fallback AppleMyungjo / Noto Serif KR.
UI and metadata: Source Sans 3 (variable), fallback Apple SD Gothic Neo / Noto Sans KR. Mono: ui-monospace.
Article body 18px/1.68 serif; UI 16px sans. Citation lines in italic, as journals set them.

## 4. Layout
Layout: utility strip (open-access line, GitHub, feed, theme toggle) / masthead band (wordmark + volume line,
search) / section nav (links scroll sideways on phones, primary "Submit manuscript" pinned right) / main max 1240px /
footer band (four link columns + licence line).
Article: outline 180px + main + tools 280px at >=1180px; outline hidden below 1180px; tools drop below main
under 960px.

## 5. Screens
- Home. Primary action: Submit a manuscript. Priorities: journal identity (cover, tagline, facts), latest
  articles, subjects. Left out: hero imagery, metrics we do not have (impact factor, downloads), testimonials.
- Article. Primary action: Download PDF. Priorities: title + authors, abstract, body.
  Required: type, open-access mark, citation line, dates, version, DOI (or "pending"), cite formats, subjects,
  versions list, licence, AI contribution, AI-translation notice and language switch, example/withdrawn banners.
- Subjects. Curated sections from `journal.yml`; each lists its description, keywords, count, recent articles.
- Tag (keyword) pages list articles and the subjects the keyword belongs to.
- Why this journal, Knowledge base: Markdown documents (WHY.md, KNOWLEDGE_BASE.md) rendered in the doc layout.

## 6. Components
Buttons (primary blue, secondary blue outline), theme toggle (pill on the band, icon + next theme label), masthead
search (posts `q` to /search/, which triggers Pagefind), table-of-contents entries (kicker, title, authors,
citation, Abstract disclosure, PDF, Full text), chips for keywords, notices (tonal background; the home warning
has a gold left border), tabs (language, cite format), breadcrumbs, the typographic cover (SVG potential-energy surface).

## 7. Surfaces
Flat content surfaces. 1px hairlines, 2px text-colour rules above section heads, 2px gold rules on the masthead
and footer, radius 4px, no blur. The masthead has a subtle navy-to-blue gradient. The cover uses #244C76 and
a soft shadow. The desktop introduction has a 56px cover-to-text gap, title line-height 1.22, and body
line-height 1.75. Buttons and navigation have 150ms hover transitions; reduced motion disables transitions
and button movement.

## 8. Accepted debt
None yet.
