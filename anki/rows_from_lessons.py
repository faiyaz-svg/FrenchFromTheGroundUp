"""Make the Anki card files from the lessons' "New words" tables.

Reads tools/lessons.yml (reading order), and for every lesson file that exists
reads the table under "## New words" (or "## Nouveaux mots"):

    | French | English | Notes |
    |---|---|---|
    | *le café* | coffee | |
    | *l'eau* (f.) | water | |

and writes anki/cards/<stage-folder>.tsv with the columns
id, french, english, notes, tags. anki/build_decks.py turns those files into decks.

- Markdown stars are removed, so the text to speech field is plain French.
- A gender mark such as (f.) moves from the French field to the notes.
- "beau / belle" becomes "beau, belle" so it reads well aloud.
- With --tracked, only lessons committed to git count (it reads `git ls-files`).

Run from the repo root:  .venv/Scripts/python anki/rows_from_lessons.py [--tracked]
"""

from __future__ import annotations

import argparse
import html
import re
import subprocess
import sys
import unicodedata
from dataclasses import dataclass
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
LESSONS = ROOT / "tools" / "lessons.yml"
CARDS_DIR = ROOT / "anki" / "cards"
HEADER = "id\tfrench\tenglish\tnotes\ttags"

SECTION = re.compile(r"^## (?:New words|Nouveaux mots)[ \t]*$", re.M)
GENDER = re.compile(r"\s*\((m|f)\.(?:\s*pl\.)?\)")
GENDER_WORD = {"m": "masculine", "f": "feminine"}


@dataclass
class Row:
    french: str
    english: str
    notes: str


def split_cells(line: str) -> list[str]:
    """Split a table row on unescaped bars."""
    inner = line.strip()
    if inner.startswith("|"):
        inner = inner[1:]
    if inner.endswith("|") and not inner.endswith("\\|"):
        inner = inner[:-1]
    return [c.strip().replace("\\|", "|") for c in re.split(r"(?<!\\)\|", inner)]


def plain(text: str) -> str:
    """Drop Markdown emphasis and backticks."""
    return re.sub(r"[*`]", "", text).strip()


def parse_new_words(text: str) -> list[Row]:
    """The rows of the New words table in a lesson's text."""
    m = SECTION.search(text)
    if not m:
        return []
    rest = text[m.end():]
    end = re.search(r"^## |^(?:Next|Suite)[ \xa0]?: ", rest, re.M)
    body = rest[: end.start()] if end else rest
    rows: list[Row] = []
    seen_header = seen_rule = False
    for line in body.splitlines():
        if not line.lstrip().startswith("|"):
            continue
        cells = split_cells(line)
        if not seen_header:
            seen_header = True
            continue
        if not seen_rule:
            seen_rule = True
            if all(re.fullmatch(r":?-{3,}:?", c) for c in cells if c):
                continue
        if len(cells) < 2:
            continue
        french, english = cells[0], cells[1]
        notes = cells[2] if len(cells) > 2 else ""
        gender = GENDER.search(french)
        gender_note = ""
        if gender:
            gender_note = GENDER_WORD[gender.group(1)]
            french = GENDER.sub("", french)
        french = plain(french).replace(" / ", ", ")
        english = plain(english)
        notes = plain(notes)
        if gender_note:
            notes = f"{gender_note}; {notes}" if notes else gender_note
        if french and english:
            rows.append(Row(french, english, notes))
    return rows


def slug(text: str) -> str:
    ascii_text = unicodedata.normalize("NFD", text).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", ascii_text.lower()).strip("-") or "x"


def tsv_field(text: str) -> str:
    return html.escape(text, quote=False).replace("\t", " ").replace("\n", "<br>")


def tracked_paths() -> set[str]:
    out = subprocess.run(
        ["git", "ls-files", "docs"], cwd=ROOT, capture_output=True, text=True, check=True
    ).stdout
    return {line.removeprefix("docs/") for line in out.splitlines()}


def stage_rows(folder: dict, level: str, docs: Path, tracked: set[str] | None) -> list[str]:
    """The TSV lines (without header) for one stage."""
    lines: list[str] = []
    used_ids: set[str] = set()
    seen_pairs: set[tuple[str, str]] = set()
    for num, entry in enumerate(folder["lessons"], 1):
        rel = f"{folder['folder']}/{num:02d}-{entry[0]}.md"
        path = docs / rel
        if not path.is_file() or (tracked is not None and rel not in tracked):
            continue
        area = next((f for f in entry[2] if f != "review"), "") if len(entry) > 2 else ""
        tags = " ".join(t for t in (level, f"lesson{num:02d}", area) if t)
        for row in parse_new_words(path.read_text(encoding="utf-8")):
            pair = (row.french.lower(), row.english.lower())
            if pair in seen_pairs:
                continue
            seen_pairs.add(pair)
            base = f"l{num:02d}-{slug(row.french)}"
            card_id, n = base, 2
            while card_id in used_ids:
                card_id, n = f"{base}-{n}", n + 1
            used_ids.add(card_id)
            lines.append("\t".join([card_id, tsv_field(row.french), tsv_field(row.english), tsv_field(row.notes), tags]))
    return lines


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Write anki/cards/<stage>.tsv from the New words tables.")
    parser.add_argument("--tracked", action="store_true", help="only lessons committed to git")
    parser.add_argument("--docs", type=Path, default=DOCS)
    parser.add_argument("--out", type=Path, default=CARDS_DIR)
    args = parser.parse_args(argv)
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(errors="backslashreplace")

    tracked = tracked_paths() if args.tracked else None
    data = yaml.safe_load(LESSONS.read_text(encoding="utf-8"))
    args.out.mkdir(parents=True, exist_ok=True)
    total = 0
    for folder in data["folders"]:
        lines = stage_rows(folder, folder["level"], args.docs, tracked)
        if not lines:
            continue
        (args.out / f"{folder['folder']}.tsv").write_text(
            HEADER + "\n" + "\n".join(lines) + "\n", encoding="utf-8", newline="\n"
        )
        total += len(lines)
        print(f"{folder['folder']}: {len(lines)} notes")
    print(f"{total} notes written to {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
