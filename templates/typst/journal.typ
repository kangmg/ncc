#let ink = rgb("#1C3558")
#let gold = rgb("#D7AE62")
#let muted = rgb("#536577")
#let hairline = rgb("#D9E3EC")
#let tint = rgb("#F3F6FA")
#let caution-bg = rgb("#fbf3db")
#let caution-ink = rgb("#7a5200")

#let serif = ("Libertinus Serif", "Noto Serif CJK KR", "Noto Serif KR", "AppleMyungjo", "Noto Serif CJK JP", "Noto Serif CJK SC")
#let sans = ("Helvetica Neue", "Helvetica", "Arial", "Liberation Sans", "DejaVu Sans", "Noto Sans CJK KR", "Apple SD Gothic Neo")

#let meta-line(label, value) = if value != none and value != "" [
  #text(fill: muted)[#label] #value
]

#let notice-box(body, fill: caution-bg, color: caution-ink) = block(
  width: 100%, fill: fill, inset: (x: 10pt, y: 8pt), radius: 3pt,
  text(font: sans, size: 8pt, fill: color, body),
)

#let front-matter(meta, abstract) = {
  set par(justify: false, first-line-indent: 0pt)
  line(length: 100%, stroke: 1.6pt + gold)
  v(2pt)
  grid(
    columns: (1fr, auto),
    align: (left + bottom, right + bottom),
    text(font: sans, size: 12pt, weight: "bold", fill: ink, meta.journal.title),
    text(font: sans, size: 8pt, fill: muted)[Open Access #h(6pt) | #h(6pt) #upper(meta.type_label)],
  )
  v(-4pt)
  line(length: 100%, stroke: 0.8pt + ink)
  v(4pt)

  if meta.status_note != none {
    notice-box(fill: rgb("#fdebec"), color: rgb("#9f2f2d"), meta.status_note)
    v(4pt)
  }
  if meta.notice != none {
    notice-box[*AI translation.* #meta.notice]
    v(4pt)
  }

  v(6pt)
  text(font: sans, size: 17pt, weight: "bold", hyphenate: false, meta.title)
  if meta.subtitle != none {
    linebreak()
    text(font: sans, size: 12pt, fill: muted, meta.subtitle)
  }
  v(8pt)

  let names = meta.authors.map(a => {
    let marks = a.sup
    if a.corresponding { marks = if marks == "" { "*" } else { marks + ",*" } }
    [#a.name#super(typographic: false, size: 0.7em, marks)]
  })
  text(font: sans, size: 10pt, names.join(", "))
  v(2pt)
  set text(size: 7.5pt, font: sans, fill: muted)
  for (i, aff) in meta.affiliations.enumerate() [
    #super(typographic: false, size: 0.8em, str(i + 1))#aff \
  ]
  if meta.corresponding_email != none [
    \*Corresponding author: #link("mailto:" + meta.corresponding_email)[#meta.corresponding_email]
  ]
  v(8pt)

  block(width: 100%, fill: tint, inset: 12pt, radius: 3pt)[
    #set text(font: serif, size: 9.5pt, fill: black)
    #set par(justify: true)
    #text(font: sans, size: 8pt, weight: "bold", fill: ink, tracking: 0.06em)[ABSTRACT] \
    #abstract
    #v(4pt)
    #text(font: sans, size: 7.5pt, fill: muted)[*Keywords:* #meta.keywords.join(", ")]
  ]
  v(6pt)

  text(font: sans, size: 7.5pt, fill: muted)[
    Received #meta.dates.submitted #h(6pt) | #h(6pt) Accepted #meta.dates.accepted #h(6pt) | #h(6pt)
    Published #meta.dates.published #h(6pt) | #h(6pt) Version #meta.version
    #if meta.doi != none [ #h(6pt) | #h(6pt) DOI #link("https://doi.org/" + meta.doi)[#meta.doi] ]
    \
    *Cite as:* #meta.citation \
    #meta.license_line
    #if meta.at("ai_line", default: none) != none [ \ *AI contribution:* #meta.ai_line ]
  ]
  v(2pt)
  line(length: 100%, stroke: 0.5pt + hairline)
  v(6pt)
}

#let article(meta: (:), abstract: [], body) = {
  set document(title: meta.title, author: meta.authors.map(a => a.name), keywords: meta.keywords)
  set page(
    paper: "a4",
    margin: (x: 2cm, top: 2.2cm, bottom: 2cm),
    header: context {
      if counter(page).get().first() > 1 {
        set text(font: sans, size: 7.5pt, fill: muted)
        [#meta.journal.abbrev #meta.year, #meta.volume, #meta.number #h(1fr) #meta.short_title]
      }
    },
    footer: context {
      set text(font: sans, size: 7.5pt, fill: muted)
      [#meta.url #h(1fr) #counter(page).display()]
    },
  )
  set text(font: serif, size: 10pt, lang: meta.lang)
  set par(justify: true, leading: 0.6em, spacing: 0.9em)
  show heading: set text(font: sans, fill: ink)
  show heading.where(level: 1): it => block(above: 1.5em, below: 0.7em, text(size: 11pt, weight: "bold", it.body))
  show heading.where(level: 2): it => block(above: 1.1em, below: 0.5em, text(size: 9pt, weight: "bold", it.body))
  show link: set text(fill: ink)
  show raw: set text(size: 8.5pt)
  set super(typographic: false, size: 0.7em)
  set figure(gap: 8pt)
  set figure.caption(separator: [. ])
  show figure.caption: set text(font: sans, size: 8pt)
  show figure.caption: it => align(left, it)
  show figure.where(kind: table): set figure.caption(position: top)
  set table(stroke: none, inset: (x: 6pt, y: 4pt))
  show table: it => block(stroke: (top: 0.8pt, bottom: 0.8pt), it)
  set math.equation(numbering: none)

  front-matter(meta, abstract)
  body
}

#let embed-pdf(data, pages) = {
  for i in range(pages) {
    page(margin: 0pt, header: none, footer: none,
      image(data, format: "pdf", page: i + 1, width: 100%, height: 100%, fit: "contain"))
  }
}
