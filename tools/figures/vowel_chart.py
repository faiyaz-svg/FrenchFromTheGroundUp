"""Draw the French vowel chart as an SVG.

Writes docs/assets/figures/01-first-sounds-and-greetings/vowel-chart.svg:
the oral vowels placed by tongue height (top to bottom) and tongue position
(front to back), with rounded vowels to the right of each pair, and the
nasal vowels in a box beside it. Each vowel has an example word.

Run from the repo root:  .venv/Scripts/python tools/figures/vowel_chart.py
"""

from __future__ import annotations

from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs" / "assets" / "figures" / "01-first-sounds-and-greetings" / "vowel-chart.svg"

INK = "#111111"
MUTED = "#555555"
PAPER = "#ffffff"
LINE = "#1f9d55"  # A1 green
FONT = "Figtree, Helvetica, Arial, sans-serif"

# Chart corners (x, y): a trapezoid, wide at the top, as in standard IPA charts.
TOP_LEFT, TOP_RIGHT = (90, 70), (430, 70)
BOTTOM_LEFT, BOTTOM_RIGHT = (230, 370), (430, 370)

# Oral vowels: symbol, example word, height (0 = top, 3 = bottom), side, rounded.
# side: 0 = front, 1 = central, 2 = back.
ORAL = [
    ("i", "si", 0, 0, False),
    ("y", "tu", 0, 0, True),
    ("u", "vous", 0, 2, True),
    ("e", "thé", 1, 0, False),
    ("ø", "deux", 1, 0, True),
    ("o", "eau", 1, 2, True),
    ("ə", "le", 1.5, 1, False),
    ("ɛ", "père", 2, 0, False),
    ("œ", "sœur", 2, 0, True),
    ("ɔ", "bol", 2, 2, True),
    ("a", "patte", 3, 0, False),
]
NASAL = [("ɑ̃", "blanc"), ("ɛ̃", "vin"), ("ɔ̃", "bon"), ("œ̃", "brun")]


def lerp(a: tuple[float, float], b: tuple[float, float], t: float) -> tuple[float, float]:
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def point(height: float, side: int) -> tuple[float, float]:
    """Position on the chart: interpolate the left and right edges by height."""
    t = height / 3
    left = lerp(TOP_LEFT, BOTTOM_LEFT, t)
    right = lerp(TOP_RIGHT, BOTTOM_RIGHT, t)
    return lerp(left, right, side / 2)


def text(x: float, y: float, s: str, size: int, weight: int = 400, fill: str = INK,
         anchor: str = "middle", italic: bool = False) -> str:
    style = ' font-style="italic"' if italic else ""
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-family="{FONT}" font-size="{size}" '
            f'font-weight="{weight}" fill="{fill}" text-anchor="{anchor}"{style}>{escape(s)}</text>')


def main() -> None:
    w, h = 720, 430
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" '
        f'role="img" aria-labelledby="t d">',
        '<title id="t">French vowel chart</title>',
        '<desc id="d">Oral vowels placed by tongue height and position, with example words, '
        'and the nasal vowels in a separate box.</desc>',
        f'<rect x="0" y="0" width="{w}" height="{h}" fill="{PAPER}"/>',
    ]
    # Trapezoid and the inner height lines.
    poly = " ".join(f"{x},{y}" for x, y in (TOP_LEFT, TOP_RIGHT, BOTTOM_RIGHT, BOTTOM_LEFT))
    parts.append(f'<polygon points="{poly}" fill="none" stroke="{INK}" stroke-width="2"/>')
    for hh in (1, 2):
        a, b = point(hh, 0), point(hh, 2)
        parts.append(f'<line x1="{a[0]:.1f}" y1="{a[1]:.1f}" x2="{b[0]:.1f}" y2="{b[1]:.1f}" '
                     f'stroke="{MUTED}" stroke-width="1" stroke-dasharray="4 4"/>')
    # Axis labels.
    parts.append(text(TOP_LEFT[0], 40, "front of the mouth", 15, 600, MUTED, anchor="start"))
    parts.append(text(TOP_RIGHT[0], 40, "back", 15, 600, MUTED, anchor="end"))
    for label, hh in (("closed", 0), ("half closed", 1), ("half open", 2), ("open", 3)):
        x, y = point(hh, 0)
        parts.append(text(x - 14, y + 5, label, 14, 600, MUTED, anchor="end"))
    # Vowels. Unrounded on the left of a pair, rounded on the right.
    for sym, word, hh, side, rounded in ORAL:
        x, y = point(hh, side)
        if side == 0:
            x += 66 if rounded else 24
        elif side == 2:
            x -= 26
        dot_x = x
        parts.append(f'<circle cx="{dot_x:.1f}" cy="{y:.1f}" r="4" fill="{LINE}"/>')
        parts.append(text(dot_x, y - 10, sym, 24, 700))
        parts.append(text(dot_x, y + 22, word, 14, 400, MUTED, italic=True))
    parts.append(text(260, 410, "In each pair on the left side, the second vowel is said with rounded lips.", 13, 400, MUTED))
    # Nasal vowels box.
    bx, by, bw, bh = 500, 70, 190, 300
    parts.append(f'<rect x="{bx}" y="{by}" width="{bw}" height="{bh}" fill="none" stroke="{INK}" stroke-width="2"/>')
    parts.append(f'<rect x="{bx}" y="{by}" width="{bw}" height="10" fill="{LINE}"/>')
    parts.append(text(bx + bw / 2, by + 40, "Nasal vowels", 17, 700))
    for i, (sym, word) in enumerate(NASAL):
        y = by + 95 + i * 55
        parts.append(text(bx + 60, y, sym, 26, 700))
        parts.append(text(bx + 120, y, word, 16, 400, MUTED, anchor="start", italic=True))
    parts.append("</svg>")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(parts) + "\n", encoding="utf-8", newline="\n")
    print("wrote", OUT.relative_to(ROOT))


if __name__ == "__main__":
    main()
