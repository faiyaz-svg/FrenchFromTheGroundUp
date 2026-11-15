"""Tests for anki/build_decks.py and anki/rows_from_lessons.py.

Run: .venv/Scripts/python -m unittest anki.test_build_decks
  or .venv/Scripts/python -m pytest -q anki
"""

from __future__ import annotations

import io
import json
import sqlite3
import sys
import tempfile
import unittest
import zipfile
from contextlib import closing
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_decks as bd  # noqa: E402
import rows_from_lessons as rl  # noqa: E402

LESSON = """\
# A lesson

## New words

| French | English | Notes |
|---|---|---|
| *le café* | coffee | |
| *l'eau* (f.) | water | |
| *beau / belle* | beautiful | |
| *magasiner* | to shop | Quebec; France: *faire du shopping* |

## Key terms

- **Term**: a definition.

Next: [Next](02-next.md)
"""


def apkg_db(data: bytes) -> bytes:
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        return zf.read("collection.anki2")


class DeckTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.cards = self.dir / "cards"
        self.out = self.dir / "out"
        self.cards.mkdir()

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def write(self, name: str, rows: list[str]) -> Path:
        path = self.cards / name
        path.write_text("\n".join(rows) + "\n", encoding="utf-8")
        return path

    def test_header_is_optional(self) -> None:
        with_header = self.write("a.tsv", ["id\tfrench\tenglish\tnotes\ttags", "c1\tle café\tcoffee\t\ta1"])
        without = self.write("b.tsv", ["c1\tle café\tcoffee\t\ta1"])
        for path in (with_header, without):
            cards, errors = bd.read_cards(path)
            self.assertEqual(errors, [])
            self.assertEqual([c.id for c in cards], ["c1"])
            self.assertEqual(cards[0].notes, "")

    def test_errors_are_reported(self) -> None:
        path = self.write("a.tsv", [
            "c1\tfront\tback\t\tt",
            "c1\tfront\tback\t\tt",
            "Bad_Id\tfront\tback\t\tt",
            "c2\tonly\tfour\tcolumns",
            "c3\t\tback\t\tt",
        ])
        cards, errors = bd.read_cards(path)
        text = "\n".join(errors)
        self.assertIn("duplicate id", text)
        self.assertIn("lowercase slug", text)
        self.assertIn("5 tab-separated columns", text)
        self.assertIn("french is empty", text)
        self.assertEqual([c.id for c in cards], ["c1"])

    def test_tts_tag_is_on_the_french_side(self) -> None:
        model = bd.make_model()
        self.assertEqual(len(model.templates), 2)
        french_first, english_first = model.templates
        self.assertIn("{{tts fr_CA:French}}", french_first["qfmt"])
        self.assertNotIn("{{tts fr_CA:French}}", english_first["qfmt"])
        self.assertIn("{{tts fr_CA:French}}", english_first["afmt"])
        self.assertEqual([f["name"] for f in model.fields], ["French", "English", "Notes"])

    def test_both_directions_are_built(self) -> None:
        path = self.write("a.tsv", ["c1\tle café\tcoffee\t\ta1", "c2\tl'eau\twater\tfeminine\ta1"])
        cards, errors = bd.read_cards(path)
        self.assertEqual(errors, [])
        data = bd.build_apkg("a", cards, 1_700_000_000)
        with closing(sqlite3.connect(":memory:")) as conn:
            conn.deserialize(apkg_db(data))
            notes = conn.execute("SELECT count(*) FROM notes").fetchone()[0]
            ords = sorted({o for (o,) in conn.execute("SELECT ord FROM cards")})
            n_cards = conn.execute("SELECT count(*) FROM cards").fetchone()[0]
            (models,) = conn.execute("SELECT models FROM col").fetchone()
        self.assertEqual(notes, 2)
        self.assertEqual(n_cards, 4)
        self.assertEqual(ords, [0, 1])
        self.assertIn(str(bd.MODEL_ID), json.loads(models))

    def test_guids_are_stable_between_builds(self) -> None:
        path = self.write("a.tsv", ["c1\tle café\tcoffee\t\ta1", "c2\tl'eau\twater\t\ta1"])
        cards, _ = bd.read_cards(path)

        def guids(timestamp: int) -> list[str]:
            data = bd.build_apkg("a", cards, timestamp)
            with closing(sqlite3.connect(":memory:")) as conn:
                conn.deserialize(apkg_db(data))
                return [g for (g,) in conn.execute("SELECT guid FROM notes ORDER BY id")]

        self.assertEqual(guids(1_700_000_000), guids(1_800_000_000))
        self.assertEqual(len(set(guids(1_700_000_000))), 2)

    def test_rebuild_is_byte_identical(self) -> None:
        path = self.write("a.tsv", ["c1\tle café\tcoffee\t\ta1"])
        cards, _ = bd.read_cards(path)
        self.out.mkdir()
        target = self.out / "a.apkg"
        self.assertTrue(bd.write_deck("a", cards, target, now=1_700_000_000))
        first = target.read_bytes()
        self.assertFalse(bd.write_deck("a", cards, target, now=1_800_000_000))
        self.assertEqual(target.read_bytes(), first)

    def test_ids_are_stable(self) -> None:
        stem = "01-first-sounds-and-greetings"
        self.assertEqual(bd.deck_id(stem), bd.deck_id(stem))
        self.assertNotEqual(bd.deck_id(stem), bd.deck_id("09-work-and-the-future"))
        self.assertTrue((1 << 30) <= bd.deck_id(stem) < (1 << 31))


class NewWordsTests(unittest.TestCase):
    def test_parse_new_words(self) -> None:
        rows = rl.parse_new_words(LESSON)
        self.assertEqual([r.french for r in rows], ["le café", "l'eau", "beau, belle", "magasiner"])
        self.assertEqual([r.english for r in rows], ["coffee", "water", "beautiful", "to shop"])
        self.assertEqual(rows[1].notes, "feminine")
        self.assertEqual(rows[3].notes, "Quebec; France: faire du shopping")
        self.assertEqual(rows[0].notes, "")

    def test_french_section_name(self) -> None:
        text = LESSON.replace("## New words", "## Nouveaux mots")
        self.assertEqual(len(rl.parse_new_words(text)), 4)

    def test_no_section(self) -> None:
        self.assertEqual(rl.parse_new_words("# Title\n\nText.\n"), [])

    def test_ids_are_ascii_slugs(self) -> None:
        self.assertEqual(rl.slug("le café"), "le-cafe")
        self.assertEqual(rl.slug("l'été"), "l-ete")

    def test_stage_rows(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            docs = Path(tmp)
            folder = {"folder": "01-x", "lessons": [["one", "One", ["grammar"]], ["two", "Two", ["words", "review"]]]}
            (docs / "01-x").mkdir()
            (docs / "01-x" / "01-one.md").write_text(LESSON, encoding="utf-8")
            lines = rl.stage_rows(folder, "a1", docs, None)
            self.assertEqual(len(lines), 4)
            first = lines[0].split("\t")
            self.assertEqual(first[0], "l01-le-cafe")
            self.assertEqual(first[4], "a1 lesson01 grammar")
            # The output is a valid card file.
            card_file = docs / "01-x.tsv"
            card_file.write_text(rl.HEADER + "\n" + "\n".join(lines) + "\n", encoding="utf-8")
            cards, errors = bd.read_cards(card_file)
            self.assertEqual(errors, [])
            self.assertEqual(len(cards), 4)


if __name__ == "__main__":
    unittest.main()
