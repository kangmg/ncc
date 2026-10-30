"""Build NCC's pure-vector README header using only the Python standard library.

The double-well surface is a conceptual illustration, not manuscript data.
Run this file to regenerate ../ncc-header.svg; edit the SVG directly if preferred.
"""

from pathlib import Path


def project(u: float, v: float) -> tuple[float, float]:
    energy = 0.9 * (u * u - 1) ** 2 + 0.20 * v * v
    return 928 + 164 * u + 63 * v, 354 - 53 * u + 44 * v - 180 * energy


def curve(points: list[tuple[float, float]]) -> str:
    return "M" + " L".join(f"{x:.2f} {y:.2f}" for x, y in points)


def samples(low: float, high: float, count: int) -> list[float]:
    return [low + (high - low) * i / (count - 1) for i in range(count)]


def build() -> str:
    mesh: list[str] = []
    for v in samples(-1.5, 1.5, 27):
        d = curve([project(u, v) for u in samples(-1.3, 1.3, 101)])
        mesh.append(f'      <path d="{d}"/>')
    for u in samples(-1.3, 1.3, 35):
        d = curve([project(u, v) for v in samples(-1.5, 1.5, 81)])
        mesh.append(f'      <path d="{d}"/>')
    route = curve([project(u, 0) for u in samples(-1.05, 1.05, 121)])
    points = []
    for u in [-1.05, -0.75, -0.45, 0, 0.45, 0.75, 1.05]:
        x, y = project(u, 0)
        points.append(f'      <circle cx="{x:.2f}" cy="{y:.2f}" r="4.5"/>')
    end_x, end_y = project(1.05, 0)
    mesh_markup = "\n".join(mesh)
    points_markup = "\n".join(points)
    return f'''<svg xmlns="http://www.w3.org/2000/svg"
     width="1200" height="500" viewBox="0 0 1200 500"
     role="img" aria-labelledby="ncc-header-title ncc-header-desc">
  <title id="ncc-header-title">Notes in Chemical Computation</title>
  <desc id="ncc-header-desc">Small findings deserve to be shared. Open science, open source. A gold reaction path crosses a conceptual energy surface and leads to an openly shared research note.</desc>
  <defs>
    <linearGradient id="ncc-background" x1="0" y1="0" x2="1200" y2="420" gradientUnits="userSpaceOnUse">
      <stop offset="0" stop-color="#1c3558"/>
      <stop offset="0.55" stop-color="#28517d"/>
      <stop offset="1" stop-color="#3f739d"/>
    </linearGradient>
    <linearGradient id="ncc-mesh-fade" x1="660" y1="0" x2="920" y2="0" gradientUnits="userSpaceOnUse">
      <stop offset="0" stop-color="#000000"/>
      <stop offset="1" stop-color="#ffffff"/>
    </linearGradient>
    <mask id="ncc-mesh-mask" maskUnits="userSpaceOnUse" x="640" y="60" width="560" height="440">
      <rect x="640" y="60" width="560" height="440" fill="url(#ncc-mesh-fade)"/>
    </mask>
    <clipPath id="ncc-canvas-clip"><rect width="1200" height="500"/></clipPath>
  </defs>

  <rect width="1200" height="500" fill="url(#ncc-background)"/>

  <g id="conceptual-energy-surface" transform="translate(130 88) scale(0.84)" clip-path="url(#ncc-canvas-clip)" aria-hidden="true">
    <g mask="url(#ncc-mesh-mask)" fill="none" stroke="#b4cbee" stroke-width="0.75" stroke-opacity="0.38" stroke-linejoin="round">
{mesh_markup}
    </g>
    <path id="reaction-path" d="{route}" fill="none" stroke="#d7ae62" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round"/>
    <g fill="#ffffff" stroke="#d7ae62" stroke-width="1.2">
{points_markup}
    </g>
    <g id="version-branches" fill="none" stroke="#d7ae62" stroke-width="1.8" stroke-linecap="round">
      <path d="M{end_x:.2f} {end_y:.2f} L1128 264 M{end_x:.2f} {end_y:.2f} H1134 M{end_x:.2f} {end_y:.2f} L1128 324"/>
      <circle cx="1128" cy="264" r="5" fill="#28517d"/>
      <circle cx="1134" cy="{end_y:.2f}" r="5" fill="#28517d"/>
      <circle cx="1128" cy="324" r="5" fill="#28517d"/>
    </g>

    <g id="shared-research-note" transform="translate(1042 322) rotate(12 56 72)">
      <path d="M10 10 H122 V154 H10 Z" fill="#d6e2ef" stroke="#8daed3" stroke-width="1"/>
      <path d="M5 5 H117 V149 H5 Z" fill="#f3f6fa" stroke="#8daed3" stroke-width="1"/>
      <path d="M0 0 H112 V144 H0 Z" fill="#ffffff" stroke="#b4cbee" stroke-width="1"/>
      <g fill="none" stroke="#8daed3" stroke-width="0.9">
        <rect x="12" y="12" width="88" height="46"/>
        <ellipse cx="56" cy="35" rx="32" ry="16" transform="rotate(-12 56 35)"/>
        <ellipse cx="56" cy="35" rx="24" ry="12" transform="rotate(-12 56 35)"/>
        <ellipse cx="56" cy="35" rx="16" ry="8" transform="rotate(-12 56 35)"/>
        <ellipse cx="56" cy="35" rx="8" ry="4" transform="rotate(-12 56 35)"/>
        <path d="M15 72 V102 H98 M18 98 C30 98 32 73 43 73 S57 96 67 96 S79 86 87 86 S93 99 98 99"/>
        <ellipse cx="34" cy="122" rx="21" ry="12"/>
        <ellipse cx="34" cy="122" rx="14" ry="8"/>
        <ellipse cx="34" cy="122" rx="7" ry="4"/>
        <ellipse cx="80" cy="122" rx="16" ry="12"/>
        <ellipse cx="80" cy="122" rx="10" ry="8"/>
        <ellipse cx="80" cy="122" rx="4" ry="4"/>
      </g>
    </g>
  </g>

  <g id="journal-name" fill="#ffffff" font-family="Georgia, 'Times New Roman', serif" font-size="80" font-weight="700" letter-spacing="-1.2">
    <text x="48" y="113">Notes in</text>
    <text x="48" y="197">Chemical Computation</text>
  </g>
  <g id="journal-purpose" fill="#d6e2ef" font-family="Helvetica, Arial, sans-serif" font-size="40" font-weight="500">
    <text x="50" y="303">Small findings deserve</text>
    <text x="50" y="345">to be shared.</text>
  </g>
  <g id="open-values" fill="#d7ae62" font-family="Helvetica, Arial, sans-serif" font-size="34" font-weight="600" letter-spacing="2.5">
    <path d="M50 378 H670" fill="none" stroke="#d7ae62" stroke-width="2"/>
    <text x="50" y="418">OPEN SCIENCE</text>
    <text x="362" y="418" text-anchor="middle">·</text>
    <text x="670" y="418" text-anchor="end">OPEN SOURCE</text>
  </g>
</svg>
'''


if __name__ == "__main__":
    destination = Path(__file__).resolve().parent.parent / "ncc-header.svg"
    destination.write_text(build(), encoding="utf-8")
    print(destination)
