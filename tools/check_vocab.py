"""Vocabulary ledger: which French words does a lesson use that the reader has not met?

Run from the repo root:
  .venv/Scripts/python tools/check_vocab.py                 stages 1-8
  .venv/Scripts/python tools/check_vocab.py --max-stage 4
  .venv/Scripts/python tools/check_vocab.py --stage 3       report only stage 3
  .venv/Scripts/python tools/check_vocab.py --strict        exit 1 if anything is unknown

Lessons are walked in book order (tools/lessons.yml: folder order, then lesson order).
Known words = tools/data_static/function_words.txt + every lemma in the `## New words`
tables of earlier lessons and the current one. French tokens come from fr fences and
italics. Each unknown lemma is listed per lesson, most frequent first; "glossed" means
every use was on a fr line that has an English gloss. Warnings only unless --strict.
"""

from __future__ import annotations

import argparse
import re
import sys
import unicodedata
from collections import Counter
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_french as cf  # noqa: E402

ROOT = cf.ROOT
STATIC = ROOT / "tools" / "data_static"
TOKEN = re.compile(r"[^\W\d_]+")


def load_wordlist(path: Path) -> set[str]:
    out = set()
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.split(" #")[0].strip()
            if line and not line.startswith("#"):
                out.add(unicodedata.normalize("NFC", line.lower()))
    return out


def lesson_sequence(max_stage: int):
    """Yield (stage_num, folder, lesson_num, slug, title, path) in book order."""
    data = yaml.safe_load((ROOT / "tools" / "lessons.yml").read_text(encoding="utf-8"))
    for fo in data["folders"]:
        folder = fo["folder"]
        m = re.match(r"(\d+)-", folder)
        stage = int(m.group(1)) if m else 0
        if stage > max_stage:
            continue
        for k, entry in enumerate(fo["lessons"], 1):
            slug, title = entry[0], entry[1]
            yield stage, folder, k, slug, title, ROOT / "docs" / folder / f"{k:02d}-{slug}.md"


def tokens_of(text: str) -> list[tuple[str, bool]]:
    """Split French text into (token, sentence_start) pairs. Apostrophes and hyphens split words."""
    out = []
    start = True
    pos = 0
    for m in TOKEN.finditer(text):
        between = text[pos:m.start()]
        if re.search(r"[.?!…:]", between):
            start = True
        out.append((m.group(0), start))
        start = False
        pos = m.end()
    return out


def entry_words(cell: str) -> list[str]:
    """Words introduced by a New words French cell."""
    t = cf.straighten(cf.strip_md(cell)).lower()
    t = re.sub(r"\([^)]*\)", " ", t)
    return [w for w, _ in tokens_of(t)]


class Known:
    def __init__(self, lex, function_words: set[str]):
        self.lex = lex
        self.forms = set(function_words)
        self.lemmas: set[str] = set()

    def lemmas_of(self, word: str) -> set[str]:
        rows = self.lex.get(word, [])
        return {r[0] for r in rows}

    def add_entry(self, cell: str) -> None:
        for w in entry_words(cell):
            self.forms.add(w)
            self.lemmas |= self.lemmas_of(w)

    def is_known(self, word: str) -> bool:
        if word in self.forms:
            return True
        return bool(self.lemmas_of(word) & self.lemmas)

    def display_lemma(self, word: str) -> str:
        rows = self.lex.get(word, [])
        if not rows:
            return word
        best = max(rows, key=lambda r: r[4])
        return best[0]


def analyse_lesson(doc: cf.Doc, known: Known, names: set[str]):
    """Return Counter lemma -> [total, glossed] for unknown words in one lesson."""
    for _, cell in doc.nouns:
        known.add_entry(cell)
    table_lines = {ln for ln, _ in doc.nouns}
    found: dict[str, list[int]] = {}
    for it in doc.items:
        if it.kind not in ("fence", "italic", "frpara") or it.mode == "qc":
            continue
        if it.kind == "italic" and it.line in table_lines:
            continue
        text = cf.straighten(it.text)
        for tok, start in tokens_of(text):
            low = unicodedata.normalize("NFC", tok).lower()
            if len(low) == 1 and low in "cdjlmnst" or low in names:
                continue
            if tok[0].isupper() and not start:
                continue
            if known.is_known(low):
                continue
            if tok[0].isupper() and start and low not in known.lex:
                continue
            lemma = known.display_lemma(low)
            rec = found.setdefault(lemma, [0, 0])
            rec[0] += 1
            rec[1] += 1 if it.glossed else 0
    return found


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Vocabulary ledger for the French lessons.")
    ap.add_argument("--max-stage", type=int, default=8)
    ap.add_argument("--stage", type=int, help="report only this stage (earlier stages still count as known)")
    ap.add_argument("--strict", action="store_true")
    ns = ap.parse_args(argv)
    lex = cf.get_lexique()
    if not lex:
        print("Lexique is missing. Run tools/fetch_data.py first.")
        return 2
    known = Known(lex, load_wordlist(STATIC / "function_words.txt"))
    names = load_wordlist(STATIC / "names.txt")
    total_unknown = 0
    missing = 0
    for stage, folder, num, slug, title, path in lesson_sequence(ns.max_stage):
        if not path.exists():
            missing += 1
            continue
        doc = cf.extract_md(path.read_text(encoding="utf-8"), cf.rel(path))
        found = analyse_lesson(doc, known, names)
        if ns.stage is not None and stage != ns.stage:
            continue
        if not found:
            continue
        total_unknown += len(found)
        print(f"\n{cf.rel(path)}  ({len(found)} unknown lemmas)")
        for lemma, (n, g) in sorted(found.items(), key=lambda kv: (-kv[1][0], kv[0])):
            tag = ""
            if g == n:
                tag = " (glossed)"
            elif g:
                tag = f" ({g} glossed)"
            print(f"  {lemma} x{n}{tag}")
    print(f"\nVocabulary ledger: {total_unknown} unknown lemmas, {missing} lessons not written yet.")
    return 1 if (ns.strict and total_unknown) else 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
