"""Build Anki decks from the card files in anki/cards/.

Each anki/cards/<stem>.tsv becomes docs/downloads/anki/<stem>.apkg, one deck
per stage. The card files come from the lessons' "New words" tables
(anki/rows_from_lessons.py). Run it from the repo root:

    .venv/Scripts/python anki/build_decks.py

File format:

- UTF-8, tab-separated, 5 columns: id<TAB>french<TAB>english<TAB>notes<TAB>tags.
  A first row exactly "id french english notes tags" is a header and is skipped.
- Notes may be empty; french and english may not.
- A field can't contain a tab or a newline: write <br> for a line break.
- Blank lines and lines starting with # are skipped.

Each row makes one note with two cards: French to English, and English to
French. Audio uses Anki's built-in text to speech, {{tts fr_CA:French}}, so
there are no audio files. It needs Anki 2.1.20 or later, AnkiDroid 2.17 or
later, or AnkiMobile.

The build checks every file first and writes nothing if any file has an error.
Each error is printed as path:line: message, and the exit code is 1.

Re-importing an updated deck updates the cards in place, because each note's
GUID comes from the file stem and the card id. Anki only updates a note when
the file's copy is newer, so a deck whose content changed gets the current
time as its timestamp. A deck whose content did not change keeps its previous
timestamp, so rebuilding it gives a byte-identical file.

Needs Python 3.11 or later (sqlite3 serialize) and genanki 0.13.1.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import itertools
import json
import re
import sqlite3
import sys
import time
import zipfile
from contextlib import closing
from dataclasses import dataclass, field
from pathlib import Path

import genanki
import yaml

ROOT = Path(__file__).resolve().parent.parent
CARDS_DIR = ROOT / "anki" / "cards"
OUT_DIR = ROOT / "docs" / "downloads" / "anki"
LESSONS = ROOT / "tools" / "lessons.yml"

BOOK_TITLE = "French From the Ground Up"

# The note type is shared by every deck. Its ID must never change: Anki uses it
# to recognise the note type when a deck is imported again.
MODEL_ID = 2_037_450_284
MODEL_NAME = "French From the Ground Up (two-way)"

HEADER = ["id", "french", "english", "notes", "tags"]
ID_RE = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
TAG_RE = re.compile(r"[A-Za-z0-9_-]+(?:::[A-Za-z0-9_-]+)*")

FRENCH_TO_ENGLISH = {
    "name": "French to English",
    "qfmt": '{{tts fr_CA:French}}\n<div class="front fr">{{French}}</div>',
    "afmt": (
        "{{FrontSide}}\n"
        '<hr id="answer">\n'
        '<div class="back">{{English}}</div>\n'
        '{{#Notes}}<div class="notes">{{Notes}}</div>{{/Notes}}'
    ),
}
ENGLISH_TO_FRENCH = {
    "name": "English to French",
    "qfmt": '<div class="front">{{English}}</div>',
    "afmt": (
        "{{FrontSide}}\n"
        '<hr id="answer">\n'
        "{{tts fr_CA:French}}\n"
        '<div class="back fr">{{French}}</div>\n'
        '{{#Notes}}<div class="notes">{{Notes}}</div>{{/Notes}}'
    ),
}

CARD_CSS = """\
.card {
  font-family: Figtree, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
    "Helvetica Neue", Arial, sans-serif;
  font-size: 22px;
  line-height: 1.5;
  text-align: center;
  color: #111;
  background-color: #fff;
}
.front, .back, .notes, hr#answer {
  max-width: 36em;
  margin-left: auto;
  margin-right: auto;
}
.fr {
  font-style: italic;
}
hr#answer {
  border: none;
  border-top: 2px solid #111;
  margin-top: 1em;
  margin-bottom: 1em;
}
.notes {
  margin-top: 1.2em;
  font-size: 15px;
  color: #4d4d4d;
}
.card.nightMode, .card.night_mode, .nightMode .card, .night_mode .card {
  color: #eee;
  background-color: #1e1e1e;
}
.nightMode hr#answer, .night_mode hr#answer {
  border-top-color: #858585;
}
.nightMode .notes, .night_mode .notes {
  color: #b3b3b3;
}
"""

# Fixed zip entry date, so identical content gives identical bytes.
ZIP_DATE = (1980, 1, 1, 0, 0, 0)


@dataclass
class Card:
    line: int
    id: str
    french: str
    english: str
    notes: str = ""
    tags: list[str] = field(default_factory=list)


def display_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def folder_titles() -> dict[str, str]:
    """Readable deck titles from tools/lessons.yml, such as '01 First sounds and greetings'."""
    try:
        data = yaml.safe_load(LESSONS.read_text(encoding="utf-8"))
        return {f["folder"]: f"{n:02d} {f['title']}" for n, f in enumerate(data["folders"], 1)}
    except (OSError, KeyError, TypeError, yaml.YAMLError):
        return {}


def folder_title(stem: str) -> str:
    return folder_titles().get(stem, stem)


def deck_name(stem: str) -> str:
    return f"{BOOK_TITLE}::{folder_title(stem)}"


def deck_id(stem: str) -> int:
    """A stable deck ID in the range [2**30, 2**31), from the SHA-1 of the stem."""
    h = int(hashlib.sha1(("french:" + stem).encode("utf-8")).hexdigest()[:8], 16)
    return (1 << 30) + h % (1 << 30)


def read_cards(path: Path) -> tuple[list[Card], list[str]]:
    """Read and check one card file. Returns (cards, errors)."""
    where = display_path(path)
    cards: list[Card] = []
    errors: list[str] = []
    first_line: dict[str, int] = {}

    try:
        raw = path.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError as exc:
        return [], [f"{where}: not valid UTF-8 ({exc})"]

    reader = csv.reader(io.StringIO(raw, newline=""), delimiter="\t", quoting=csv.QUOTE_NONE)
    for row in reader:
        line = reader.line_num
        if not row or (len(row) == 1 and not row[0].strip()):
            continue
        if row[0].startswith("#") or (line == 1 and [c.strip() for c in row] == HEADER):
            continue
        loc = f"{where}:{line}"
        if len(row) != 5:
            errors.append(f"{loc}: expected 5 tab-separated columns (id, french, english, notes, tags), found {len(row)}")
            continue

        card_id, french, english, notes, tags = (col.strip() for col in row)
        row_ok = True

        if not ID_RE.fullmatch(card_id):
            errors.append(f"{loc}: id {card_id!r} must be a lowercase slug such as l01-le-cafe")
            row_ok = False
        elif card_id in first_line:
            errors.append(f"{loc}: duplicate id {card_id!r} (first used on line {first_line[card_id]})")
            row_ok = False
        else:
            first_line[card_id] = line

        for name, value, required in (("french", french, True), ("english", english, True), ("notes", notes, False)):
            if not value:
                if required:
                    errors.append(f"{loc}: {name} is empty")
                    row_ok = False
                continue
            bad_tags = genanki.Note._find_invalid_html_tags_in_field(value)
            if bad_tags:
                errors.append(f"{loc}: {name}: invalid HTML {' '.join(bad_tags)!r} (write < as &lt;)")
                row_ok = False

        tag_list = tags.split()
        for tag in tag_list:
            if not TAG_RE.fullmatch(tag):
                errors.append(f"{loc}: tag {tag!r} may only use letters, digits, - and _ (and :: for nested tags)")
                row_ok = False

        if row_ok:
            all_tags = list(dict.fromkeys(tag_list + [path.stem]))
            cards.append(Card(line, card_id, french, english, notes, all_tags))

    return cards, errors


def make_model() -> genanki.Model:
    return genanki.Model(
        MODEL_ID,
        MODEL_NAME,
        fields=[{"name": "French"}, {"name": "English"}, {"name": "Notes"}],
        templates=[FRENCH_TO_ENGLISH, ENGLISH_TO_FRENCH],
        css=CARD_CSS,
    )


def make_deck(stem: str, cards: list[Card]) -> genanki.Deck:
    title = folder_title(stem)
    deck = genanki.Deck(deck_id(stem), deck_name(stem), description=f"Vocabulary for {title} in {BOOK_TITLE}.")
    model = make_model()
    for position, card in enumerate(cards):
        deck.add_note(genanki.Note(
            model=model,
            fields=[card.french, card.english, card.notes],
            tags=card.tags,
            guid=genanki.guid_for("french", stem, card.id),
            due=position,  # new cards come up in file order
        ))
    return deck


def build_apkg(stem: str, cards: list[Card], timestamp: int) -> bytes:
    """Return the .apkg file contents for one deck."""
    package = genanki.Package(make_deck(stem, cards))
    with closing(sqlite3.connect(":memory:")) as conn:
        cursor = conn.cursor()
        package.write_to_db(cursor, timestamp, itertools.count(timestamp * 1000))
        conn.commit()
        db_bytes = conn.serialize()

    entries = [("collection.anki2", db_bytes), ("media", json.dumps({}).encode("utf-8"))]
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        for name, data in entries:
            info = zipfile.ZipInfo(name, date_time=ZIP_DATE)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 0
            info.external_attr = 0
            zf.writestr(info, data)
    return buf.getvalue()


def previous_timestamp(apkg: bytes) -> int | None:
    """Read the build timestamp from an .apkg this script wrote, or None."""
    try:
        with zipfile.ZipFile(io.BytesIO(apkg)) as zf:
            db_bytes = zf.read("collection.anki2")
        with closing(sqlite3.connect(":memory:")) as conn:
            conn.deserialize(db_bytes)
            (models_json,) = conn.execute("SELECT models FROM col").fetchone()
        return int(json.loads(models_json)[str(MODEL_ID)]["mod"])
    except Exception:
        return None


def write_deck(stem: str, cards: list[Card], out_path: Path, now: int | None = None) -> bool:
    """Write one deck. Returns True if the file changed, False if it didn't."""
    old = out_path.read_bytes() if out_path.exists() else None
    if old is not None:
        old_ts = previous_timestamp(old)
        if old_ts is not None and build_apkg(stem, cards, old_ts) == old:
            return False
    timestamp = int(time.time()) if now is None else now
    out_path.write_bytes(build_apkg(stem, cards, timestamp))
    return True


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build docs/downloads/anki/<stem>.apkg from anki/cards/<stem>.tsv.")
    parser.add_argument("--cards", type=Path, default=CARDS_DIR, help="folder of .tsv card files")
    parser.add_argument("--out", type=Path, default=OUT_DIR, help="output folder")
    args = parser.parse_args(argv)
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(errors="backslashreplace")

    paths = sorted(args.cards.glob("*.tsv"))
    if not paths:
        print(f"No .tsv files in {display_path(args.cards)}", file=sys.stderr)
        return 1

    decks: list[tuple[str, list[Card]]] = []
    errors: list[str] = []
    for path in paths:
        cards, file_errors = read_cards(path)
        errors.extend(file_errors)
        decks.append((path.stem, cards))

    if errors:
        for message in errors:
            print(message, file=sys.stderr)
        print(f"{len(errors)} error(s); no decks written.", file=sys.stderr)
        return 1

    args.out.mkdir(parents=True, exist_ok=True)
    for stem, cards in decks:
        if not cards:
            print(f"{stem}: no cards, skipped")
            continue
        out_path = args.out / f"{stem}.apkg"
        changed = write_deck(stem, cards, out_path)
        status = "" if changed else " (unchanged)"
        print(f"{deck_name(stem)}: {len(cards)} notes -> {display_path(out_path)}{status}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
