"""Draw tense timelines as SVGs.

Each figure is a time arrow with a "now" mark, and events drawn as dots
(a finished action at one point) or bars (something in progress or a habit).

Writes:
  docs/assets/figures/06-habits-memories-and-food/imparfait-vs-passe-compose.svg

Run from the repo root:  .venv/Scripts/python tools/figures/timelines.py
"""

from __future__ import annotations

from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parents[2]
FIG = ROOT / "docs" / "assets" / "figures"

INK = "#111111"
MUTED = "#555555"
PAPER = "#ffffff"
A2 = "#f26b1d"      # orange line (A2)
A2_TEXT = "#a84105"
FONT = "Figtree, Helvetica, Arial, sans-serif"


def text(x, y, s, size, weight=400, fill=INK, anchor="middle", italic=False):
    style = ' font-style="italic"' if italic else ""
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-family="{FONT}" font-size="{size}" '
            f'font-weight="{weight}" fill="{fill}" text-anchor="{anchor}"{style}>{escape(s)}</text>')


def frame(w, h, title, desc):
    return [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" '
        f'role="img" aria-labelledby="t d">',
        f'<title id="t">{escape(title)}</title>',
        f'<desc id="d">{escape(desc)}</desc>',
        f'<rect x="0" y="0" width="{w}" height="{h}" fill="{PAPER}"/>',
    ]


def arrow(parts, x1, x2, y, now_x):
    parts.append(f'<line x1="{x1}" y1="{y}" x2="{x2}" y2="{y}" stroke="{INK}" stroke-width="2"/>')
    parts.append(f'<polygon points="{x2},{y} {x2 - 12},{y - 6} {x2 - 12},{y + 6}" fill="{INK}"/>')
    parts.append(f'<line x1="{now_x}" y1="{y - 14}" x2="{now_x}" y2="{y + 14}" stroke="{INK}" stroke-width="3"/>')
    parts.append(text(now_x, y + 34, "now", 15, 700))
    parts.append(text(x1, y + 34, "past", 15, 600, MUTED, anchor="start"))


def imparfait_vs_pc():
    w, h = 760, 300
    parts = frame(w, h, "Imparfait and passé composé on a timeline",
                  "The imparfait is a long bar for what was going on, the background. "
                  "The passé composé is a dot for one finished event that happened during it.")
    y = 170
    arrow(parts, 40, 720, y, 640)
    # The background: imparfait as a bar.
    bx1, bx2 = 90, 560
    parts.append(f'<rect x="{bx1}" y="{y - 46}" width="{bx2 - bx1}" height="18" fill="{A2}"/>')
    parts.append(text((bx1 + bx2) / 2, y - 60, "Il pleuvait. (it was raining: imparfait, the background)", 16, 600, A2_TEXT))
    # The event: passé composé as a dot.
    ex = 330
    parts.append(f'<line x1="{ex}" y1="{y - 28}" x2="{ex}" y2="{y}" stroke="{INK}" stroke-width="1.5" stroke-dasharray="3 3"/>')
    parts.append(f'<circle cx="{ex}" cy="{y}" r="9" fill="{INK}"/>')
    parts.append(text(ex, y + 64, "Je suis sorti. (I went out: passé composé, one event)", 16, 600))
    parts.append(text(w / 2, 280, "Bar = what was going on.  Dot = what happened.", 15, 400, MUTED))
    parts.append("</svg>")
    out = FIG / "06-habits-memories-and-food" / "imparfait-vs-passe-compose.svg"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(parts) + "\n", encoding="utf-8", newline="\n")
    print("wrote", out.relative_to(ROOT))


if __name__ == "__main__":
    imparfait_vs_pc()
