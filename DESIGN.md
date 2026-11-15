# Design

The look of the French From the Ground Up site. The idea is a metro map. Each CEFR level is a line with its own colour. Each lesson is a station. The home page is the map and fills in as lessons are done.

All styles live in `docs/stylesheets/site.css`. Line strips on lesson and stage pages are drawn by `docs/javascripts/lines.js` from `docs/assets/lines.json`.

## Principles

- Flat. No shadows, no gradients, no glows, no blur.
- Square corners. The only round shape is the station dot.
- High contrast. Ink on paper, thick colour bars, no pale grey text.
- One colour at a time. The page takes the colour of its level, and that is the only accent.
- Colour is never the only signal. Done, here and planned also differ by fill, size and outline.
- Plain words. No stock icons, no emoji, no decoration that does not carry meaning.

## Lines and colours

`theme.js` sets `body[data-level]` to a1, a2, b1 or b2 (stages 1-4, 5-8, 9-12, 13-16). The CSS turns that into three tokens: `--fm-line` (fills and thick bars), `--fm-line-text` (thin lines and text accents) and `--fm-line-on` (text placed on a fill). Pages without a level use neutral grey.

| Level | Line | Fill | Text on paper | Text on fill |
|---|---|---|---|---|
| A1 | Green | `#1f9d55` | `#0f6a35` (6.7:1) | `#111` (5.4:1) |
| A2 | Orange | `#f26b1d` | `#a84105` (6.1:1) | `#111` (6.2:1) |
| B1 | Yellow | `#f5c400` | `#7a5a00` (6.4:1) | `#111` (11.5:1) |
| B2 | Blue | `#1d5fd1` | `#1d5fd1` (5.8:1) | `#fff` (5.8:1) |

Fills are used only for bars 4px or thicker, dots, badges and block headers. Underlines and small accents use the text colour, because yellow on white is only 1.6:1. Dark mode lifts the text colours (`#4cc47f`, `#ff8c4a`, `#f5c400`, `#7aa5ff`, all above 7:1 on `#141414`).

Neutral tokens:

| Token | Light | Dark |
|---|---|---|
| `--fm-ink` | `#111` | `#f2f2f0` |
| `--fm-paper` | `#fff` | `#141414` |
| `--fm-panel` | `#f3f3f1` | `#1f1f1e` |
| `--fm-muted` | `#555` | `#b5b5b0` |
| `--fm-rule` | `#c9c9c5` | `#3a3a38` |

The header, tabs and footer are near-black in both modes.

## Type

One family: Figtree (Google Fonts), weights 400, 600, 700, 800, italic 400 and 700. It covers French accents and the guillemets. Fallback: Segoe UI, Helvetica Neue, Arial. Code uses Cascadia Mono or Consolas.

| Use | Size | Weight |
|---|---|---|
| Base | 18px (17px on phones), line height 1.6 | 400 |
| H1 | 2.3rem | 800 |
| H2 | 1.55rem, 4px line-colour rule under it | 800 |
| H3 | 1.2rem, 6px line-colour bar on the left | 800 |
| H4 | 1rem | 800 |
| Tabs, nav | 0.72 to 0.8rem | 600 to 800 |

Italics are reserved for French, so French words always stand out. The French column of a New words table is italic.

## Components

- **Line map** (`.fm-map`). Four lines. Each has a coloured header block, a thick left bar in the line colour, and one segment per stage. A segment is a linked stage name and a row of stations that wraps. Planned stations are dimmed with a dashed ring.
- **Station** (`.fm-st`). A round dot with white fill and a 3px dark ring, with its lesson number below. Done: dot filled with the line colour. Here: larger dot with a dark tag reading "You are here". Planned: 45% opacity, dashed ring, no link.
- **Line strip** (`.fm-strip`). The stations of one stage, under the H1. Drawn by `lines.js`. Before it loads, the H1 shows a short 5rem bar in the line colour.
- **Boxes.** Admonitions are flat panels with an 8px bar in the line colour (red for warnings). Answers (`??? success "Answer"`) are collapsed white boxes with a 2px ink frame.
- **Tables.** 2px ink frame, panel header with a 4px line-colour rule, thin row rules.
- **Task lists.** Material checkboxes in the line text colour (Move on when).
- **French block** (`pre.fr`, then speak.js). A panel with an 8px line-colour bar. Paragraph pairs (`.fr`, `.en`) get a 5px bar and the English one is muted. Only one shows at a time.
- **Previous and next.** Two square buttons with a 3px frame. Next is filled with the line colour.
- **Links.** Ink text with a 2px underline in the line text colour. Hover adds a pale line-colour wash.
- **Focus.** A 3px outline in the line text colour.

## Layout

Content is 46rem wide. On phones the side gutter is 16px, nothing scrolls sideways, and the station rows wrap. The theme is checked at 360px.

## What to avoid

- Gradients, glows, shadows, blur, glassy cards.
- Emoji and stock icons. The only icons are Material's own for search, menu and fold arrows.
- Rounded pills and rounded cards. Corners stay square.
- Pastel fills behind body text.
- Transit agency names, logos, route symbols or typefaces. The colours and shapes here are our own.
- Yellow text on white. Use the ochre text colour.
- Using the line colour for meaning other than level (no green for "correct").
- Animated decoration. The map does not move.
