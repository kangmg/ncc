#set page(paper: "a4", margin: 2.2cm)
#set text(font: "Libertinus Serif", size: 11pt)
#set par(justify: true)
#set heading(numbering: "1.")

#align(center)[
  #text(size: 17pt, weight: "bold")[aseview: A Lightweight Trajectory Viewer for ASE]
  #v(4pt)
  Mingi Kang \
  #text(size: 9pt)[Example manuscript typeset by the author in Typst]
]

= Summary
`aseview` renders ASE trajectories in the browser without a desktop GUI. This
manuscript was written in Typst by the author; the journal compiles it as-is and
adds a cover page with the citation metadata.

= Statement of need
Remote clusters rarely offer a display. A static HTML viewer removes the need for
X forwarding when inspecting optimisation and MD trajectories.

= Usage
```python
from aseview import view
view("relax.traj")
```

= Availability
Source code: https://github.com/kangmg/aseview (MIT licence).
