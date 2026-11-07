"""Regenerate editable SVG sources from the checked example outputs."""
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from tactile import estimate


def draw(name, title, subtitle):
    data = estimate(json.loads((HERE.parent / f"examples/{name}.json").read_text()))
    x0, y0, spacing = 275, 145, 100
    x, y = (v * spacing / 5 for v in data["center_mm"])
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="760" height="460" viewBox="0 0 760 460">',
        '<rect width="760" height="460" fill="#10252d"/>',
        '<g font-family="DejaVu Sans,sans-serif">',
        f'<text x="36" y="48" font-size="32" fill="#f1fbfa" font-weight="700">{title}</text>',
        f'<text x="36" y="78" font-size="22" fill="#a8d7d3">{subtitle}</text>',
    ]
    for c in range(3):
        parts.append(f'<text x="{x0+c*spacing}" y="101" text-anchor="middle" fill="#bfdfdf" font-size="21">{c*5}</text>')
    for r, row in enumerate(data["taxel_forces_n"]):
        cy = y0 + r * spacing
        parts.append(f'<text x="207" y="{cy+9}" text-anchor="end" fill="#bfdfdf" font-size="21">{r*5}</text>')
        for c, force in enumerate(row):
            cx = x0 + c * spacing
            fill = '#257c77' if force else '#1c3a44'
            parts.append(f'<rect x="{cx-40}" y="{cy-38}" width="80" height="76" rx="10" fill="{fill}" stroke="#3c6970"/>')
            parts.append(f'<text x="{cx}" y="{cy+29}" text-anchor="middle" fill="#ffffff" font-size="22">{force:g} N</text>')
    parts += [
        '<text x="558" y="118" fill="#bfdfdf" font-size="22">x (mm)</text>',
        '<text x="84" y="254" fill="#bfdfdf" font-size="22">y (mm)</text>',
        f'<circle cx="{x0+x:.2f}" cy="{y0+y:.2f}" r="10" fill="#ffcb73" stroke="#10252d" stroke-width="3"/>',
        '<circle cx="46" cy="420" r="9" fill="#ffcb73"/>',
        f'<text x="66" y="427" fill="#f1fbfa" font-size="22">Load center: ({data["center_mm"][0]:.2f}, {data["center_mm"][1]:.2f}) mm</text>',
        '</g></svg>',
    ]
    (HERE / f"tactile-{name}.svg").write_text("\n".join(parts)+"\n", encoding="utf-8")


if __name__ == "__main__":
    draw("single-patch", "One patch, unequal loads", "The 2 N cell pulls the estimate to the right")
    draw("two-contacts", "Two touches, one centroid", "The center falls on a cell that reads 0 N")
