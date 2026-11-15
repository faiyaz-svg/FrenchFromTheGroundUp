"""Check the French in the lessons: grammar and spelling (LanguageTool),
verb conjugations (verbecc), IPA (ipa-dict), typography, and noun genders (Lexique).

Run from the repo root:
  .venv/Scripts/python tools/check_french.py                 all of docs/
  .venv/Scripts/python tools/check_french.py docs/01-x/02-y.md
  .venv/Scripts/python tools/check_french.py --no-lt         skip LanguageTool (fast)
  .venv/Scripts/python tools/check_french.py --json          machine output

Needs the data from `tools/fetch_data.py` (Lexique, ipa-dict, LanguageTool).

French is read from:
  fr fences      one utterance per line: [Speaker:] French [{qc}] [{x}] [| gloss]
  italics        *mot*  (French by convention)
  .fr paragraphs a paragraph whose last line is {: .fr }
  New words      the first column of the `## New words` / `## Nouveaux mots` table
  drill JSON     docs/assets/drills/*.json

Errors (exit code 1): LanguageTool matches on sentences, conjugation mismatches,
typography problems, definite gender errors. Warnings (exit 0): single-word
spelling, IPA differences, unknown words.
"""

from __future__ import annotations

import argparse
import itertools
import json
import logging
import os
import re
import sys
import time
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "tools" / "data"
ALLOW_FILE = ROOT / "tools" / "french_allow.txt"
os.environ.setdefault("LTP_PATH", str(DATA / "lt"))
logging.getLogger("verbecc").setLevel(logging.WARNING)


# ---------------------------------------------------------------- helpers

def deacc(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s) if not unicodedata.combining(c))


def straighten(s: str) -> str:
    return s.replace("’", "'").replace("‘", "'")


def strip_md(s: str) -> str:
    """Remove inline Markdown (links, emphasis, code) from French text."""
    s = re.sub(r"`[^`]*`", "", s)
    s = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", s)
    s = s.replace("**", "").replace("*", "")
    return re.sub(r"\s+", " ", s).strip()


# ---------------------------------------------------------------- items

@dataclass
class Item:
    kind: str          # fence, italic, frpara, newword, drill
    path: str
    line: int
    text: str
    mode: str = "full"  # full = grammar and spelling, spell = spelling only
    flags: tuple = ()
    speaker: str = ""
    strict_quotes: bool = False
    glossed: bool = False


@dataclass
class Finding:
    severity: str      # error or warning
    category: str      # lt, spelling, conj, ipa, typo, gender, vocab
    path: str
    line: int
    text: str
    rule: str
    message: str

    def as_dict(self) -> dict:
        return self.__dict__.copy()


@dataclass
class Doc:
    path: str
    items: list = field(default_factory=list)
    ipa_pairs: list = field(default_factory=list)      # (line, word, ipa)
    conj_cells: list = field(default_factory=list)     # (line, verb, tense, person, answer)
    nouns: list = field(default_factory=list)          # (line, cell_text)
    newwords: list = field(default_factory=list)       # (line, cell_text)
    qc_lines: list = field(default_factory=list)       # (line, text)
    gender_items: list = field(default_factory=list)   # (line, noun, answer, elided)
    gender_marks: list = field(default_factory=list)


FENCE_OPEN = re.compile(r"^(\s*)(`{3,}|~{3,})\s*([\w-]*)")
SPEAKER = re.compile(r"^([\w-]+):(?=\s)")
FLAG = re.compile(r"\{(qc|x)\}")


def parse_fr_fence(line: str):
    """Return dict(speaker, french, flags, gloss) for a fence line, or None for blank or comment."""
    s = line.strip()
    if not s or s.startswith("#"):
        return None
    gloss = ""
    if " | " in s:
        s, gloss = s.split(" | ", 1)
        gloss = gloss.strip()
    flags = tuple(sorted(set(FLAG.findall(s))))
    s = FLAG.sub("", s).strip()
    speaker = ""
    m = SPEAKER.match(s)
    if m:
        speaker = m.group(1)
        s = s[m.end():].strip()
    return {"speaker": speaker, "french": s, "flags": flags, "gloss": gloss}


ITALIC = re.compile(r"(?<![*\\])\*(?=[^\s*])([^*\n]*?[^\s*])\*(?!\*)")
IPA_PAIR = re.compile(r"\*([^*\n]+)\*\s*/([^/\n]+)/")
HEADING = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
NEWWORDS_HEAD = re.compile(r"^(new words|nouveaux mots)\b", re.I)


def split_row(line: str) -> list[str]:
    s = line.strip()
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|"):
        s = s[:-1]
    return [c.strip() for c in s.split("|")]


def is_sep_row(cells: list[str]) -> bool:
    return bool(cells) and all(re.fullmatch(r":?-{2,}:?", c.strip()) or c.strip() == "" for c in cells) \
        and any(c.strip() for c in cells)


def clean_cell(c: str) -> str:
    return strip_md(c)


def italic_spans(line: str) -> list[str]:
    no_code = re.sub(r"`[^`]*`", lambda m: " " * len(m.group(0)), line)
    return [m.group(1) for m in ITALIC.finditer(no_code)]


def spell_candidates(span: str) -> list[str]:
    """Turn an italic span into the strings to spell-check (may be several)."""
    out = []
    for part in re.split(r"\s+/\s+|\s*,\s*|\s+ou\s+", span):
        p = part.strip().strip(".;:!?…")
        p = re.sub(r"\([^)]*\)", "", p).strip()
        if len(p) < 2 or re.search(r"[\d_\[\]{}<>=+]", p) or p.startswith("-") or p.endswith("-"):
            continue
        if "…" in p or "..." in p:
            continue
        out.append(p)
    return out


def classify_mode(text: str) -> str:
    words = text.split()
    if len(words) >= 5 or re.search(r"[.?!…]$", text.strip()):
        return "full"
    return "spell"


def extract_md(text: str, path: str) -> Doc:
    doc = Doc(path)
    lines = text.splitlines()
    n = len(lines)
    # front matter
    start = 0
    if lines and lines[0].strip() == "---":
        for k in range(1, n):
            if lines[k].strip() == "---":
                start = k + 1
                break
    # pass 1: mark fenced regions and .fr paragraphs
    fr_lines: dict[int, str] = {}       # 0-based index -> info for fr fence content lines
    skip = set(range(start))            # lines not scanned for italics / tables
    i = start
    in_fence = None
    fence_info = ""
    while i < n:
        raw = lines[i]
        if in_fence is None:
            m = FENCE_OPEN.match(raw)
            if m:
                in_fence = (m.group(2)[0], len(m.group(2)))
                fence_info = m.group(3)
                skip.add(i)
                i += 1
                continue
        else:
            m = FENCE_OPEN.match(raw)
            if m and m.group(2)[0] == in_fence[0] and len(m.group(2)) >= in_fence[1] and not m.group(3):
                in_fence = None
                skip.add(i)
                i += 1
                continue
            skip.add(i)
            if fence_info == "fr":
                fr_lines[i] = raw
            i += 1
            continue
        i += 1
    # .fr paragraphs
    fr_paras = []   # (first_idx, last_idx)
    i = start
    while i < n:
        if i in skip or not lines[i].strip():
            i += 1
            continue
        j = i
        while j + 1 < n and lines[j + 1].strip() and (j + 1) not in skip:
            j += 1
        if re.fullmatch(r"\{:\s*\.fr\s*\}", lines[j].strip()) and j > i:
            fr_paras.append((i, j - 1))
            for k in range(i, j + 1):
                skip.add(k)
        i = j + 1
    # fr fence items
    for idx, raw in fr_lines.items():
        p = parse_fr_fence(raw)
        if not p or not p["french"]:
            continue
        if "x" in p["flags"]:
            continue
        if "qc" in p["flags"]:
            doc.qc_lines.append((idx + 1, p["french"]))
            doc.items.append(Item("fence", path, idx + 1, p["french"], "qc", p["flags"], p["speaker"], True,
                                  bool(p["gloss"])))
            continue
        mode = "full" if len(p["french"].split()) >= 2 else "spell"
        doc.items.append(Item("fence", path, idx + 1, p["french"], mode, p["flags"], p["speaker"], True,
                              bool(p["gloss"])))
    for a, b in fr_paras:
        para = strip_md(" ".join(lines[a:b + 1]))
        if para:
            doc.items.append(Item("frpara", path, a + 1, para, "full", (), "", True))
    # pass 2: tables, new words, italics
    in_html_comment = False
    section_newwords = False
    i = start
    while i < n:
        raw = lines[i]
        if i in skip:
            i += 1
            continue
        if "<!--" in raw and "-->" not in raw:
            in_html_comment = True
        if in_html_comment:
            if "-->" in raw:
                in_html_comment = False
            i += 1
            continue
        raw_nc = re.sub(r"<!--.*?-->", "", raw)
        hm = HEADING.match(raw_nc)
        if hm:
            section_newwords = bool(NEWWORDS_HEAD.match(hm.group(2)))
        # table block
        if raw_nc.lstrip().startswith("|"):
            j = i
            while j < n and lines[j].lstrip().startswith("|") and j not in skip:
                j += 1
            handle_table(doc, lines, i, j, section_newwords)
            for k in range(i, j):
                for span in italic_spans(lines[k]):
                    add_italic(doc, path, k + 1, span)
                for m in IPA_PAIR.finditer(re.sub(r"`[^`]*`", "", lines[k])):
                    doc.ipa_pairs.append((k + 1, m.group(1).strip(), m.group(2).strip()))
            i = j
            continue
        for span in italic_spans(raw_nc):
            add_italic(doc, path, i + 1, span)
        for m in IPA_PAIR.finditer(re.sub(r"`[^`]*`", "", raw_nc)):
            doc.ipa_pairs.append((i + 1, m.group(1).strip(), m.group(2).strip()))
        i += 1
    return doc


def add_italic(doc: Doc, path: str, line: int, span: str) -> None:
    span = span.strip()
    full_mode = classify_mode(span)
    if full_mode == "full":
        doc.items.append(Item("italic", path, line, span, "full"))
        return
    for cand in spell_candidates(span):
        doc.items.append(Item("italic", path, line, cand, "spell"))


def handle_table(doc: Doc, lines: list[str], a: int, b: int, in_newwords: bool) -> None:
    rows = [(k, split_row(lines[k])) for k in range(a, b)]
    if len(rows) < 2:
        return
    header_idx, header = rows[0]
    body = [(k, c) for k, c in rows[1:] if not is_sep_row(c)]
    if in_newwords:
        for k, cells in body:
            if cells and cells[0]:
                doc.nouns.append((k + 1, cells[0]))
                if "*" not in cells[0]:
                    doc.items.append(Item("newword", doc.path, k + 1, strip_md(cells[0]), "spell"))
        return
    detect_conj_table(doc, lines, a, header, body)


TENSES = [  # (name in header text, normalised key)
    ("conditionnel passe", "conditionnel passe"),
    ("conditionnel present", "conditionnel present"),
    ("conditionnel", "conditionnel present"),
    ("subjonctif passe", "subjonctif passe"),
    ("subjonctif present", "subjonctif present"),
    ("subjonctif", "subjonctif present"),
    ("plus-que-parfait", "plus-que-parfait"),
    ("passe compose", "passe compose"),
    ("passe simple", "passe simple"),
    ("futur anterieur", "futur anterieur"),
    ("futur simple", "futur simple"),
    ("imparfait", "imparfait"),
    ("imperatif", "imperatif"),
    ("present", "present"),
]


def find_tense(text: str) -> str | None:
    t = deacc(text).lower()
    for name, key in TENSES:
        if name in t:
            return key
    return None


PRONOUN_CELL = re.compile(
    r"^(?:que\s+|qu')?\(?(j'|je|tu|il\s*/\s*elle\s*/\s*on|il\s*/\s*elle|elle\s*/\s*il|ils\s*/\s*elles|il|elle|on|nous|vous|ils|elles)\)?\s*(.*)$",
    re.I,
)


def detect_conj_table(doc: Doc, lines: list[str], a: int, header: list[str], body) -> None:
    header_text = " ".join(header)
    tense = find_tense(header_text)
    # context: the 3 previous non-blank lines
    ctx = []
    k = a - 1
    while k >= 0 and len(ctx) < 3:
        if lines[k].strip():
            ctx.append(lines[k])
        k -= 1
    if tense is None:
        return
    verb_cols: dict[int, str] = {}
    for ci, h in enumerate(header):
        if ci == 0:
            continue
        hv = infinitive_in(clean_cell(h))
        if hv:
            verb_cols[ci] = hv
    default_verb = None
    if not verb_cols:
        default_verb = infinitive_in(clean_cell(header_text))
        if not default_verb:
            for c in ctx:
                default_verb = infinitive_in(strip_md(c), prefer_marked=c)
                if default_verb:
                    break
    if not verb_cols and not default_verb:
        return
    for k, cells in body:
        if not cells:
            continue
        c0 = clean_cell(cells[0])
        pm = PRONOUN_CELL.match(straighten(c0))
        if not pm:
            continue
        person = pm.group(1)
        rest = pm.group(2).strip()
        if rest:  # "| je suis |" form
            if default_verb:
                doc.conj_cells.append((k + 1, default_verb, tense, person, rest))
            continue
        if verb_cols:
            for ci, v in verb_cols.items():
                if ci < len(cells) and cells[ci].strip():
                    doc.conj_cells.append((k + 1, v, tense, person, clean_cell(cells[ci])))
        elif default_verb and len(cells) > 1 and cells[1].strip():
            doc.conj_cells.append((k + 1, default_verb, tense, person, clean_cell(cells[1])))


# ---------------------------------------------------------------- conjugation

_conj = None
_conj_cache: dict = {}
_infinitives = None

TENSE_MAP = {
    "present": ("indicatif", "present"),
    "passe compose": ("indicatif", "passe-compose"),
    "imparfait": ("indicatif", "imparfait"),
    "futur simple": ("indicatif", "futur-simple"),
    "futur anterieur": ("indicatif", "futur-anterieur"),
    "plus-que-parfait": ("indicatif", "plus-que-parfait"),
    "passe simple": ("indicatif", "passe-simple"),
    "conditionnel present": ("conditionnel", "present"),
    "conditionnel passe": ("conditionnel", "passe"),
    "subjonctif present": ("subjonctif", "present"),
    "subjonctif passe": ("subjonctif", "passe"),
    "imperatif": ("imperatif", "imperatif-present"),
    "imperatif present": ("imperatif", "imperatif-present"),
    "imperatif passe": ("imperatif", "imperatif-passe"),
}


def get_conjugator():
    global _conj
    if _conj is None:
        # verbecc writes verbecc.log into the current folder, so import it from tools/data
        DATA.mkdir(parents=True, exist_ok=True)
        here = os.getcwd()
        os.chdir(DATA)
        try:
            from verbecc import CompleteConjugator
            _conj = CompleteConjugator(lang="fr")
        finally:
            os.chdir(here)
    return _conj


def known_infinitives() -> set:
    global _infinitives
    if _infinitives is None:
        try:
            _infinitives = {v.lower() for v in get_conjugator().get_infinitives()}
        except Exception:  # noqa: BLE001
            _infinitives = set()
    return _infinitives


def infinitive_in(text: str, prefer_marked: str | None = None) -> str | None:
    """Find a known infinitive in a header or context line. Italic or bold words win."""
    infs = known_infinitives()
    t = straighten(text).lower()
    cands = []
    if prefer_marked:
        for m in re.finditer(r"\*+([^*]+)\*+", prefer_marked):
            cands.append(straighten(m.group(1)).lower().strip())
    cands.append(t.strip())
    for c in cands:
        if c in infs:
            return c
    for c in cands[-1:]:
        words = re.findall(r"[^\W\d_]+(?:'[^\W\d_]+)?", c)
        for w in words:
            if w in infs and len(w) > 3:
                return w
    return None


def conj_table(verb: str):
    if verb in _conj_cache:
        return _conj_cache[verb]
    result = None
    try:
        r = get_conjugator().conjugate(verb)
        d = json.loads(r.to_json())
        if d["verb"].get("predicted"):
            result = "predicted"
        else:
            result = {}
            for mood, tenses in d["moods"].items():
                for tname, entries in tenses.items():
                    result[(deacc(mood), deacc(tname))] = entries
    except Exception:  # noqa: BLE001
        result = None
    _conj_cache[verb] = result
    return result


PRON_PREFIX = re.compile(r"^(?:que\s+|qu')?(?:j'|je\s+|tu\s+|il\s+|elle\s+|on\s+|nous\s+|vous\s+|ils\s+|elles\s+)")
REFL_PREFIX = re.compile(r"^(?:me\s+|te\s+|se\s+|nous\s+|vous\s+|m'|t'|s')")


def strip_pronoun(form: str) -> str:
    f = straighten(form).lower().strip()
    f = PRON_PREFIX.sub("", f)
    return f.strip()


def persons_for(person: str) -> list[str]:
    p = straighten(person).lower().strip()
    p = re.sub(r"^(que\s+|qu')", "", p).strip("() ")
    if p == "j'":
        p = "je"
    parts = [x.strip() for x in re.split(r"\s*[/,]\s*", p) if x.strip()]
    out = []
    for x in parts:
        out.append("je" if x == "j'" else x)
    return out


def expand_parens(s: str) -> list[str]:
    """allé(e)s -> allés, allées. Each parenthesised group is optional."""
    groups = re.findall(r"\(([es]+)\)", s)
    if not groups:
        return [s]
    parts = re.split(r"\([es]+\)", s)
    out = []
    for combo in itertools.product([False, True], repeat=len(groups)):
        t = parts[0]
        for g, use, tail in zip(groups, combo, parts[1:]):
            t += (g if use else "") + tail
        out.append(t)
    return out


def answer_variants(answer: str) -> list[str]:
    """Split an answer cell into the forms it claims."""
    a = straighten(answer).lower().strip().rstrip(".")
    segs = [x.strip() for x in re.split(r"\s+/\s+|\s+ou\s+|;|,", a) if x.strip()]
    if not segs:
        return []
    out = []
    first = segs[0]
    for k, sg in enumerate(segs):
        if k > 0 and " " not in sg and " " in first:
            sg = first.rsplit(" ", 1)[0] + " " + sg
        out.append(sg)
    result = []
    for sg in out:
        for e in expand_parens(sg):
            result.append(strip_pronoun(e))
    return result


def conj_expected(verb: str, tense: str, person: str):
    """Return (set_of_forms, status). status: ok, unknown_verb, unknown_tense, predicted, unknown_person."""
    key = TENSE_MAP.get(deacc(tense).lower())
    if not key:
        return set(), "unknown_tense"
    tbl = conj_table(verb)
    if tbl is None:
        return set(), "unknown_verb"
    if tbl == "predicted":
        return set(), "predicted"
    entries = tbl.get(key)
    if entries is None:
        return set(), "unknown_tense"
    pers = persons_for(person)
    forms = set()
    for e in entries:
        if e.get("pr") in pers:
            for c in e["c"]:
                forms.add(strip_pronoun(c) if key[0] != "imperatif" else straighten(c).lower().strip())
    if not forms:
        return set(), "unknown_person"
    if verb.startswith("se ") or verb.startswith("s'"):
        forms |= {REFL_PREFIX.sub("", f) for f in forms}
    return forms, "ok"


def check_conj(verb: str, tense: str, person: str, answer: str):
    """Return (ok, expected_forms, status). ok is None when the check cannot run."""
    forms, status = conj_expected(verb, tense, person)
    if status != "ok":
        return None, forms, status
    claims = answer_variants(answer)
    if not claims:
        return None, forms, "empty"
    bad = [c for c in claims if c not in forms]
    return (not bad), forms, "ok"


# ---------------------------------------------------------------- typography

TYPO_SPACE = re.compile(r"[   ][?!;]")
TYPO_COLON = re.compile(r"(?<=[^\s\d]):(?=\s)")
TYPO_APOS = re.compile(r"\b(?:[cdjlmnst]|qu|jusqu|lorsqu|puisqu)['’][  ]+(?=[A-Za-zÀ-ÿ])", re.I)
TYPO_CURLY = re.compile(r"[‘’“”]")


def typo_issues(text: str, strict_quotes: bool = False) -> list[tuple[str, str]]:
    """Typography problems in one piece of French text (speaker label already removed)."""
    out = []
    if TYPO_SPACE.search(text):
        out.append(("TYPO_SPACE_BEFORE_PUNCT", "space before ? ! or ; (the book uses no space)"))
    if TYPO_COLON.search(text):
        out.append(("TYPO_COLON_SPACE", "missing space before a colon (write 'mot : suite')"))
    if TYPO_APOS.search(text):
        out.append(("TYPO_APOSTROPHE_SPACE", "space after an apostrophe (l' eau)"))
    if TYPO_CURLY.search(text):
        out.append(("TYPO_CURLY_QUOTE", "curly quote or apostrophe (use straight ' or guillemets)"))
    if strict_quotes and '"' in text:
        out.append(("TYPO_STRAIGHT_QUOTES", 'straight double quotes in French text (use guillemets)'))
    return out


# ---------------------------------------------------------------- Lexique, genders

_lex = None


def get_lexique():
    """by_ortho: dict word -> list of (lemme, cgram, genre, nombre, freq). None if the data is missing."""
    global _lex
    if _lex is not None:
        return _lex or None
    f = DATA / "Lexique383.tsv"
    if not f.exists():
        _lex = False
        return None
    by = {}
    with open(f, encoding="utf-8") as fh:
        head = fh.readline().rstrip("\n").split("\t")
        ix = {h: i for i, h in enumerate(head)}
        for line in fh:
            c = line.rstrip("\n").split("\t")
            try:
                fr = float(c[ix["freqfilms2"]] or 0) + float(c[ix["freqlivres"]] or 0)
            except ValueError:
                fr = 0.0
            by.setdefault(unicodedata.normalize("NFC", c[ix["ortho"]]).lower(), []).append(
                (c[ix["lemme"]], c[ix["cgram"]], c[ix["genre"]], c[ix["nombre"]], fr))
    _lex = by
    return by


def noun_genders(noun: str, lex=None) -> set:
    lex = lex if lex is not None else get_lexique()
    if not lex:
        return set()
    rows = lex.get(unicodedata.normalize("NFC", straighten(noun)).lower(), [])
    noms = [g for (_, cg, g, _, _) in rows if cg == "NOM"]
    if "" in noms:  # Lexique leaves genre blank when a noun takes both (livre, tour, poele)
        return {"m", "f"}
    return {g for g in noms if g in ("m", "f")}


def check_gender(noun: str, claimed: str, lex=None) -> str:
    """ok, error (Lexique has only the other gender) or unknown."""
    g = noun_genders(noun, lex)
    if not g:
        return "unknown"
    return "ok" if claimed in g else "error"


MARK = re.compile(r"\(\s*(m|f)\s*\.[^)]*\)", re.I)


def parse_noun_entry(cell: str):
    """Parse a New words French cell. Return (noun, gender_from_article_or_mark, conflict) or None."""
    t = straighten(strip_md(cell)).strip()
    if not t or "/" in t or "," in t:
        return None
    mark = MARK.search(t)
    mgender = mark.group(1).lower() if mark else None
    t2 = re.sub(r"\([^)]*\)", "", t).strip()
    am = re.match(r"^(le|la|un|une)\s+([^\W\d_][\w'-]*)", t2, re.I)
    gender = None
    noun = None
    if am:
        gender = "m" if am.group(1).lower() in ("le", "un") else "f"
        noun = am.group(2)
    else:
        lm = re.match(r"^l'([^\W\d_][\w-]*)", t2, re.I)
        pm = re.match(r"^(les|des)\s+([^\W\d_][\w'-]*)", t2, re.I)
        if lm and mgender:
            noun = lm.group(1)
        elif pm and mgender:
            noun = pm.group(2)
        elif mgender and re.fullmatch(r"[^\W\d_][\w-]*", t2):
            noun = t2
        else:
            return None
    conflict = bool(gender and mgender and gender != mgender)
    return noun.lower(), (gender or mgender), (mgender if conflict else None)


# ---------------------------------------------------------------- IPA

_ipa = None


def get_ipa():
    global _ipa
    if _ipa is not None:
        return _ipa or None
    f = DATA / "fr_FR.txt"
    if not f.exists():
        _ipa = False
        return None
    d = {}
    with open(f, encoding="utf-8") as fh:
        for line in fh:
            if "\t" not in line:
                continue
            w, p = line.rstrip("\n").split("\t", 1)
            d[unicodedata.normalize("NFC", w).lower()] = [x.strip() for x in p.split(",") if x.strip()]
    _ipa = d
    return d


def norm_ipa(s: str) -> str:
    """Normalise an IPA string for comparison with ipa-dict."""
    s = unicodedata.normalize("NFD", s)
    s = re.sub(r"[/\[\]ˈˌ.‿͡'ː\s_-]", "", s)
    for a, b in (("r", "ʁ"), ("ɹ", "ʁ"), ("ʀ", "ʁ"), ("ɑ", "a"),
                 ("ɡ", "g"), ("œ̃", "ɛ̃"), ("ə", "")):
        s = s.replace(a, b)
    return unicodedata.normalize("NFC", s)


def ipa_equal(book: str, dict_forms: list[str]) -> bool:
    b = norm_ipa(book)
    return any(b == norm_ipa(d) for d in dict_forms)


# ---------------------------------------------------------------- drill JSON

def line_of(raw_lines: list[str], needle: str) -> int:
    for k, ln in enumerate(raw_lines, 1):
        if needle in ln:
            return k
    return 1


def extract_drill(path: str, raw: str) -> Doc:
    doc = Doc(path)
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return doc
    rl = raw.splitlines()
    name = Path(path).name
    for it in data.get("items", []):
        if name == "conjugation.json":
            ln = line_of(rl, json.dumps(it.get("answer", ""), ensure_ascii=False))
            ln = next((k for k, l in enumerate(rl, 1)
                       if it.get("verb", "\0") in l and it.get("person", "\0") in l and it.get("answer", "\0") in l
                       and it.get("tense", "\0") in l), ln)
            doc.conj_cells.append((ln, it["verb"], it["tense"], it["person"], it["answer"]))
        elif name == "gender.json":
            ln = line_of(rl, json.dumps(it.get("noun", ""), ensure_ascii=False))
            doc.gender_items.append((ln, it["noun"], it["answer"], bool(it.get("elided"))))
        elif name == "fill.json":
            ln = line_of(rl, json.dumps(it.get("q", ""), ensure_ascii=False)[1:-1])
            for ans in it.get("a", []):
                sent = it["q"].replace("___", ans)
                doc.items.append(Item("drill", path, ln, sent, "full", (), "", False))
        elif name == "dictation.json":
            ln = line_of(rl, json.dumps(it.get("fr", ""), ensure_ascii=False)[1:-1])
            doc.items.append(Item("drill", path, ln, it["fr"], "full", (), "", False))
    return doc


# ---------------------------------------------------------------- LanguageTool

def load_allow(path: Path = ALLOW_FILE):
    """Return (rules, pairs): rules = set of rule ids; pairs = set of (rule, exact text)."""
    rules, pairs = set(), set()
    if not path.exists():
        return rules, pairs
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.split(" #")[0].strip() if " #" in raw else raw.strip()
        if not line or line.startswith("#"):
            continue
        if " | " in line:
            rule, text = line.split(" | ", 1)
            pairs.add((rule.strip(), text.strip()))
        else:
            rules.add(line)
    return rules, pairs


def run_languagetool(texts: list[str]):
    """Check unique texts in batches. Return (results, version, start_seconds).
    results: dict text -> list of (rule_id, message, matched, issue_type, offset)."""
    import language_tool_python
    t0 = time.time()
    tool = language_tool_python.LanguageTool("fr")
    start = time.time() - t0
    version = getattr(tool, "language_tool_download_version", "") or ""
    results: dict[str, list] = {t: [] for t in texts}
    try:
        for b in range(0, len(texts), 60):
            batch = texts[b:b + 60]
            joined = ""
            spans = []
            for t in batch:
                spans.append((len(joined), len(joined) + len(t)))
                joined += t + "\n\n"
            for m in tool.check(joined):
                for t, (s, e) in zip(batch, spans):
                    if s <= m.offset and m.offset + m.error_length <= e:
                        results[t].append((m.rule_id, m.message, m.matched_text, m.rule_issue_type or "",
                                           m.offset - s))
                        break
    finally:
        tool.close()
    return results, version, start


def is_spelling(rule_id: str, issue_type: str) -> bool:
    r = rule_id.upper()
    return issue_type == "misspelling" or "SPELL" in r or "MORFOLOGIK" in r or "HUNSPELL" in r


# ---------------------------------------------------------------- the run

def collect_files(args: list[str]) -> list[Path]:
    paths = [Path(a) for a in args] if args else [ROOT / "docs"]
    out = []
    for p in paths:
        p = p if p.is_absolute() else (Path.cwd() / p)
        if p.is_dir():
            for f in sorted(p.rglob("*")):
                if f.suffix == ".md" or (f.suffix == ".json" and f.parent.name == "drills"):
                    if "site" not in f.parts[len(ROOT.parts):][:1]:
                        out.append(f)
        elif p.exists():
            out.append(p)
    return out


def rel(p: Path) -> str:
    try:
        return p.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return p.as_posix()


def analyse(docs: list[Doc], use_lt: bool, allow=None):
    """Run all checks. Return (findings, info)."""
    findings: list[Finding] = []
    info = {"lt_version": "", "lt_start": 0.0, "qc": []}
    rules_allow, pairs_allow = allow if allow is not None else load_allow()
    lex = get_lexique()
    ipa = get_ipa()

    for d in docs:
        info["qc"].extend((d.path, ln, t) for ln, t in d.qc_lines)
        # typography
        for it in d.items:
            if it.kind in ("fence", "frpara", "drill", "italic") or it.kind == "newword":
                text = it.text
                for rule, msg in typo_issues(text, it.strict_quotes):
                    if rule in rules_allow or (rule, text) in pairs_allow:
                        continue
                    findings.append(Finding("error", "typo", it.path, it.line, text, rule, msg))
        # conjugations
        for ln, verb, tense, person, answer in d.conj_cells:
            ok, forms, status = check_conj(verb, tense, person, answer)
            label = f"{verb} {tense} {person}: {answer}"
            if ok is False:
                exp = ", ".join(sorted(forms))
                findings.append(Finding("error", "conj", d.path, ln, label, "CONJ_MISMATCH",
                                        f"expected: {exp}"))
            elif ok is None and status in ("unknown_verb", "predicted"):
                findings.append(Finding("warning", "conj", d.path, ln, label, "CONJ_UNKNOWN_VERB",
                                        "verb not in verbecc, not checked"))
        # ipa
        if ipa:
            for ln, word, book in d.ipa_pairs:
                w = unicodedata.normalize("NFC", straighten(word)).lower()
                if " " in w or w not in ipa:
                    continue
                if not ipa_equal(book, ipa[w]):
                    findings.append(Finding("warning", "ipa", d.path, ln, f"{word} /{book}/", "IPA_DIFF",
                                            "dictionary: " + ", ".join(ipa[w])))
        # genders
        if lex:
            for ln, cell in d.nouns:
                pe = parse_noun_entry(cell)
                if not pe:
                    continue
                noun, gender, conflict = pe
                if conflict:
                    findings.append(Finding("error", "gender", d.path, ln, strip_md(cell), "GENDER_CONFLICT",
                                            f"article and ({conflict}.) mark disagree"))
                    continue
                if check_gender(noun, gender, lex) == "error":
                    have = "/".join(sorted(noun_genders(noun, lex)))
                    findings.append(Finding("error", "gender", d.path, ln, strip_md(cell), "GENDER",
                                            f"Lexique has {noun} as {have}, the book says {gender}"))
            for ln, noun, answer, elided in d.gender_items:
                claimed = "m" if answer.lower() == "le" else "f" if answer.lower() == "la" else None
                if claimed and check_gender(noun, claimed, lex) == "error":
                    have = "/".join(sorted(noun_genders(noun, lex)))
                    findings.append(Finding("error", "gender", d.path, ln, f"{answer} {noun}", "GENDER",
                                            f"Lexique has {noun} as {have}"))
    if use_lt:
        lt_items = [it for d in docs for it in d.items if it.mode != "qc"]
        texts = sorted({it.text for it in lt_items})
        results, version, start = run_languagetool(texts) if texts else ({}, "", 0.0)
        info["lt_version"], info["lt_start"] = version, start
        for it in lt_items:
            for rule, msg, matched, itype, off in results.get(it.text, []):
                spell = is_spelling(rule, itype)
                if it.mode == "spell" and not spell:
                    continue
                if rule in rules_allow or (rule, it.text) in pairs_allow or (rule, matched) in pairs_allow:
                    continue
                if it.mode == "spell" or (spell and it.kind == "italic"):
                    findings.append(Finding("warning", "spelling", it.path, it.line, it.text, rule,
                                            f"{msg} ({matched})"))
                else:
                    findings.append(Finding("error", "lt", it.path, it.line, it.text, rule,
                                            f"{msg} ({matched})"))
    return findings, info


def load_docs(files: list[Path]) -> list[Doc]:
    docs = []
    for f in files:
        raw = f.read_text(encoding="utf-8")
        if f.suffix == ".json":
            docs.append(extract_drill(rel(f), raw))
        else:
            docs.append(extract_md(raw, rel(f)))
    return docs


CATEGORY_TITLES = {
    "lt": "Grammar and spelling (LanguageTool)",
    "spelling": "Spelling in italics and word lists (warnings)",
    "conj": "Conjugations",
    "typo": "Typography",
    "gender": "Noun genders",
    "ipa": "IPA differences (for human review)",
}


def print_report(findings: list[Finding], info: dict, nfiles: int) -> None:
    for cat, title in CATEGORY_TITLES.items():
        group = [f for f in findings if f.category == cat]
        if not group:
            continue
        print(f"\n== {title}: {len(group)}")
        for f in sorted(group, key=lambda x: (x.path, x.line)):
            tag = "E" if f.severity == "error" else "w"
            print(f"{f.path}:{f.line}: {tag} [{f.rule}] {f.message}")
            print(f"    {f.text}")
    if info["qc"]:
        print(f"\n== Casual Quebec lines ({{qc}}, not grammar-checked): {len(info['qc'])}")
        for p, ln, t in info["qc"]:
            print(f"{p}:{ln}: {t}")
    errs = sum(1 for f in findings if f.severity == "error")
    warns = len(findings) - errs
    print(f"\nChecked {nfiles} files: {errs} errors, {warns} warnings, {len(info['qc'])} {{qc}} lines.")
    if info.get("lt_version"):
        print(f"LanguageTool {info['lt_version']} started in {info['lt_start']:.1f} s.")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Check the French in the lessons.")
    ap.add_argument("paths", nargs="*")
    ap.add_argument("--no-lt", action="store_true", help="skip LanguageTool")
    ap.add_argument("--json", action="store_true", help="machine output")
    ns = ap.parse_args(argv)
    files = collect_files(ns.paths)
    docs = load_docs(files)
    findings, info = analyse(docs, not ns.no_lt)
    errs = sum(1 for f in findings if f.severity == "error")
    if ns.json:
        print(json.dumps({
            "files": len(files),
            "errors": errs,
            "warnings": len(findings) - errs,
            "findings": [f.as_dict() for f in findings],
            "qc": [{"path": p, "line": ln, "text": t} for p, ln, t in info["qc"]],
        }, ensure_ascii=False, indent=2))
    else:
        print_report(findings, info, len(files))
    return 1 if errs else 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
