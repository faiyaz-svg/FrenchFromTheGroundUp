"""Style and template check for the book's pages (the STYLE.md self-check, as a script).

Run from the repo root:
  .venv/Scripts/python tools/lint.py                              every page in docs/
  .venv/Scripts/python tools/lint.py docs/01-first-sounds-and-greetings
  .venv/Scripts/python tools/lint.py docs/01-first-sounds-and-greetings/01-french-sound-map.md

It checks the English prose only. French (fr fences, italics, .fr paragraphs,
the French column of New words tables, lines that look French) goes to
tools/check_french.py. Checks:
  - typography everywhere: em dashes, en dashes outside numeric ranges, curly
    quotes, emoji
  - English prose: banned and sparing words, bold-label bullets, Title Case headings
  - balanced <details> and <div>
  - lessons: required sections (English or French names), Next line, practice
    routine adding up to 30 minutes, prose word count, .fr/.en pairs, the fr
    fence line format, the New words table
Some hits are false positives (a word in a quotation, a name); read each one.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

BANNED = re.compile(
    r"\b(delve|tapestry|testament|pivotal|underscores?|underscored|intricat\w*|meticulous\w*|showcas\w*|"
    r"garner\w*|bolster\w*|interplay|vibrant|multifaceted|realms?|groundbreaking|renowned|nestled|"
    r"seamless\w*|commendable|noteworthy|invaluable|transformative|unparalleled|unveil\w*|harness\w*|"
    r"elucidat\w*|burgeoning|foster\w*|leverag\w*|quietly|deep dive|boasts?|journey|unlock\w*|elevat(?:e|es|ed|ing)\b|"
    r"key (?:role|factor|takeaway|insight|concept)s?|"
    r"serves? as|stands? as|functions? as|important to note|worth noting|worth mentioning|in summary|"
    r"in conclusion|to sum up|not only|let'?s dive|let'?s unpack|clearly|obviously|it is easy|"
    r"simply|trivially|great question|i hope this helps|"
    r"timeless|beloved|iconic|masterpiece|breathtaking|hauntingly|game-changing|supercharge\w*|revolutioni[sz]e)\b",
    re.I,
)
SPARING = re.compile(
    r"\b(crucial|vital|essential|comprehensive|notably|additionally|moreover|furthermore|consequently|"
    r"ultimately|enhance\w*|valuable|insights?|remarkable|nuanced|significant|robust|powerful|lush|"
    r"just|master(?:ed|ing|s)?)\b",
    re.I,
)

# Words allowed to keep a capital in a heading (besides the first word).
HEADING_OK = {
    "City",
    "I", "A1", "A2", "B1", "B2", "C1", "C2", "CEFR", "OQLF", "IPA", "SLE", "CV", "TV", "FAQ", "PDF", "URL",
    "Mauril", "Radio-Canada", "Anki", "Windows", "Edge", "Chrome", "Firefox", "Android", "iPhone", "YouTube",
    "Google", "Microsoft", "Duolingo", "Usito", "Termium", "Lexique", "LanguageTool", "TMU", "Meetup",
    "French", "English", "Canada", "Canadian", "Ontario", "Ontarians", "Franco-Ontarians", "Toronto",
    "Montreal", "Montréal", "Quebec", "Québec", "Quebecers", "Québécois", "Quebecois", "France", "Paris",
    "Ottawa", "Gatineau", "Charter", "Say", "Hockey", "Canadiens", "Alliance", "Française", "Airbnb",
    "VS", "Code", "Zensical", "Latin", "Europe", "European", "Parti", "Radio", "Telefilm", "Netflix", "Tou.tv",
    "Spotify", "Wikipedia", "Gmail", "Outlook", "Word", "Excel", "PowerPoint", "Zoom", "Teams", "Slack",
    "Hydro-Québec", "Desjardins", "Metro", "Montreal's", "Quebec's", "Canada's", "France's", "Ontario's",
    "Jean-Talon", "Plateau", "Mile", "End", "Old", "Port", "Vieux-Montréal", "Mont-Royal", "Mount", "Royal",
}
# Headings that are the book's fixed French section names or French sentences are checked
# like English ones: only the first word and proper nouns are capitalised.
SHORT_CAPS = re.compile(r"^[A-Z0-9][A-Z0-9.\-/]+$")

# Section names, English and French. Stages 11 to 16 use the French names.
SECTIONS = {
    "routine": ["## Practice routine (30 min)", "## Routine (30 min)"],
    "move on": ["## Move on when", "## Pour passer à la suite"],
    "new words": ["## New words", "## Nouveaux mots"],
    "key terms": ["## Key terms", "## Termes clés"],
}
GOAL_MARKERS = ["After this lesson you can", "Après cette leçon", "## Objectif"]
BEFORE_MARKERS = ["Before this:", "Avant cette leçon", "## Avant de commencer"]
KEY_TERMS_HEADINGS = {"## Key terms", "## Termes clés"}
NEW_WORDS_HEADINGS = {"## New words", "## Nouveaux mots"}
NEXT_LINE = re.compile(r"^(Next|Suite)[ \xa0]?: ", re.M)

FR_WORDS = {
    "le", "la", "les", "l", "de", "des", "du", "un", "une", "et", "est", "que", "qui", "pour", "dans", "vous",
    "je", "tu", "il", "elle", "nous", "ils", "ne", "pas", "en", "au", "aux", "sur", "avec", "ce", "cette",
    "ces", "se", "sa", "son", "ses", "mon", "ma", "mes", "ou", "où", "par", "plus", "sont", "ont", "avoir",
    "être", "à", "d", "n", "qu", "c", "j", "s", "m", "t", "y", "on", "mais", "donc", "très", "bien",
}

SPEAKER = re.compile(r"^([^\W_][\w-]*):(?= )")
LANG_PARA = re.compile(r"\{:\s*\.(fr|en)\s*\}\s*$")
EMOJI = re.compile("[\U0001F300-\U0001FAFF\u2600-\u27bf]")


def is_french(text: str) -> bool:
    """A cheap test: does this line read as French? Used to keep English-only checks off French."""
    words = re.findall(r"[^\W\d_]+", text.lower())
    if len(words) < 4:
        return False
    return sum(w in FR_WORDS for w in words) / len(words) >= 0.25


def strip_french(line: str) -> str:
    """Remove inline French (italics, code, guillemets) from an English line."""
    line = re.sub(r"`[^`]*`", "", line)
    line = re.sub(r"(?<!\*)\*(?!\*)[^*]+\*(?!\*)", "", line)
    line = re.sub(r"_[^_]+_", "", line) if "_" in line and "http" not in line else line
    line = re.sub(r"«[^»]*»", "", line)
    return line


def paragraphs(lines: list[str]) -> list[tuple[int, list[str]]]:
    """Split the non-fence lines into blank-line separated blocks: (first line number, lines)."""
    blocks, cur, start = [], [], 0
    for no, line in lines:
        if line.strip():
            if not cur:
                start = no
            cur.append(line)
        elif cur:
            blocks.append((start, cur))
            cur = []
    if cur:
        blocks.append((start, cur))
    return blocks


def prose_words(blocks: list[tuple[int, list[str]]]) -> int:
    count = 0
    for _, block in blocks:
        if any(LANG_PARA.search(ln) and LANG_PARA.search(ln).group(1) == "fr" for ln in block[-1:]):
            continue
        text = "\n".join(ln for ln in block if not ln.lstrip().startswith("|"))
        text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r"\{:[^}]*\}", " ", text)
        text = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", text)
        text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)
        count += len(re.findall(r"[A-Za-z0-9']+", text))
    return count


def practice_minutes(text: str) -> list[int]:
    totals = []
    for block in re.findall(r'<div class="practice" markdown>(.*?)</div>', text, flags=re.S):
        mins = 0
        for row in block.splitlines():
            m = re.match(r"^\|\s*(\d+)\s*\|", row)
            if m:
                mins += int(m.group(1))
        totals.append(mins)
    return totals


def check_fr_line(line: str) -> str | None:
    """Check one line of a fr fence against the spec: [Speaker:] French [{qc}] [{x}] [| English]."""
    if not line.strip() or line.lstrip().startswith("#"):
        return None
    if line != line.strip():
        return "leading or trailing space"
    if "|" in line and line.count(" | ") != 1:
        return "the gloss separator is one ' | ' (space, bar, space)"
    french, _, gloss = line.partition(" | ")
    if " | " in line and not gloss.strip():
        return "empty English gloss"
    if "|" in gloss:
        return "stray '|' in the gloss"
    french = french.strip()
    m = SPEAKER.match(french)
    if m:
        french = french[m.end():].strip()
    elif re.match(r"^[^\W_][\w-]*:\S", french) and not re.match(r"^https?:", french):
        return "speaker label needs a space after the colon"
    flags_ok = re.fullmatch(r"(.*?)(?:\s+\{qc\})?(?:\s+\{x\})?", french)
    body = flags_ok.group(1) if flags_ok else french
    if "{" in body or "}" in body:
        return "flags are {qc} and {x}, in that order, at the end of the French part"
    if not body.strip():
        return "no French text"
    return None


def heading_issue(line: str) -> bool:
    # Generated "Stage N: Title" headings: check the title part only.
    line = re.sub(r"^(#+\s*)Stage \d+:\s*", r"\1", line)
    words = re.sub(r"[()\[\]]", " ", line.lstrip("#")).split()
    for w in words[1:]:
        core = w.strip(".,:;!?\"'«»")
        if not core or not core[:1].isupper():
            continue
        if core in HEADING_OK or SHORT_CAPS.match(core) or core[:1].isdigit():
            continue
        if "-" in core and all(p[:1].isupper() for p in core.split("-") if p):
            # Hyphenated proper names such as Saint-Laurent: allow only if listed.
            if core in HEADING_OK:
                continue
        return True
    return False


def check(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    issues: list[str] = []
    LINT_OK = {w.lower() for w in re.findall(r"<!-- lint-ok: (\w+)", text)}
    section = ""
    in_fence = ""
    en_lines: list[tuple[int, str]] = []  # non-fence lines, for paragraph checks
    table_state = ""
    for no, line in enumerate(text.splitlines(), 1):
        fence = re.match(r"^\s*(```+|~~~+)\s*([\w-]*)", line)
        if fence:
            if not in_fence:
                in_fence = fence.group(2) or "plain"
            else:
                in_fence = ""
            continue
        # Typography applies everywhere, fences included.
        if "\u2014" in line:
            issues.append(f"{no}: em dash")
        if "\u2013" in line and not re.search(r"\d\u2013\d", line):
            issues.append(f"{no}: en dash outside a numeric range")
        if re.search("[\u201c\u201d\u2018\u2019]", line):
            issues.append(f"{no}: curly quote")
        if EMOJI.search(line):
            issues.append(f"{no}: emoji or symbol")
        if in_fence:
            if in_fence == "fr":
                problem = check_fr_line(line)
                if problem:
                    issues.append(f"{no}: fr fence: {problem}")
            continue
        en_lines.append((no, line))

        if line.startswith("## "):
            section = line.strip()
            table_state = ""

        # New words table: header and first column.
        if section in NEW_WORDS_HEADINGS and line.lstrip().startswith("|"):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if table_state == "":
                table_state = "header"
                if [c.lower() for c in cells] not in (["french", "english", "notes"], ["français", "anglais", "notes"]):
                    issues.append(f"{no}: New words header must be | French | English | Notes |")
            elif table_state == "header":
                table_state = "rows"
            else:
                if len(cells) != 3:
                    issues.append(f"{no}: New words row needs 3 cells")
                elif not re.match(r"^\*[^*]+\*", cells[0]):
                    issues.append(f"{no}: New words French cell should start with an italic word")

        # English-only checks: skip French lines and inline French.
        prose = strip_french(line)
        if section in NEW_WORDS_HEADINGS and line.lstrip().startswith("|"):
            cells = line.strip().strip("|").split("|")
            prose = strip_french("|".join(cells[1:]))
        if not is_french(prose) and not (LANG_PARA.search(line) and LANG_PARA.search(line).group(1) == "fr"):
            for m in BANNED.finditer(prose):
                issues.append(f"{no}: banned '{m.group(0)}'")
            for m in SPARING.finditer(prose):
                if m.group(0).lower().startswith("master") and "master volume" in prose.lower():
                    continue
                # A page can allow a "use rarely" word it needs, with a reason, e.g.
                # <!-- lint-ok: just (it translates venir de) -->
                if m.group(0).lower() in LINT_OK:
                    continue
                issues.append(f"{no}: use rarely '{m.group(0)}'")
        # The key terms list is the one place where "- **Term**: ..." is the format.
        if section not in KEY_TERMS_HEADINGS and path.name != "glossary.md" and (
            re.match(r"^\s*[-*] \*\*[^*]+:\*\*", line) or re.match(r"^\s*[-*] \*\*[^*]+\*\*[ \xa0]?:", line)
        ):
            issues.append(f"{no}: bold label bullet")
        if re.match(r"^#{2,6} ", line) and heading_issue(line):
            issues.append(f"{no}: Title Case? {line.strip()}")

    if in_fence:
        issues.append(f"unclosed {in_fence} fence")
    if text.count("<details") != text.count("</details>"):
        issues.append("unbalanced <details>")
    if len(re.findall(r"<div ", text)) != text.count("</div>"):
        issues.append("unbalanced <div>")

    blocks = paragraphs(en_lines)
    # Each .fr paragraph is followed by its .en paragraph, and each .en has a .fr before it.
    kinds = []
    for start, block in blocks:
        m = LANG_PARA.search(block[-1])
        kinds.append((start, m.group(1) if m else ""))
    for i, (start, kind) in enumerate(kinds):
        if kind == "fr" and (i + 1 >= len(kinds) or kinds[i + 1][1] != "en"):
            issues.append(f"{start}: .fr paragraph is not followed by an .en paragraph")
        if kind == "en" and (i == 0 or kinds[i - 1][1] != "fr"):
            issues.append(f"{start}: .en paragraph is not preceded by a .fr paragraph")

    # Template checks apply to lessons: files in a stage folder (01-... to 16-...) other than index.md.
    if path.name != "index.md" and re.match(r"(0[1-9]|1[0-6])-", path.parent.name):
        if not any(marker in text for marker in GOAL_MARKERS):
            issues.append("missing the goal ('After this lesson you can', 'Après cette leçon' or '## Objectif')")
        if not any(marker in text for marker in BEFORE_MARKERS):
            issues.append("missing the 'Before this:' line (or '## Avant de commencer')")
        for key, names in SECTIONS.items():
            if not any(re.search(rf"^{re.escape(n)}\s*$", text, re.M) for n in names):
                issues.append(f"missing section '{names[0]}' (or '{names[1]}')")
        if not NEXT_LINE.search(text):
            issues.append("missing 'Next:' line")
        if not re.search(r"^(# .+)$", text, re.M):
            issues.append("missing the H1 title")
        if not re.search(r'class="tag tag-', text):
            issues.append("missing the tag line under the title")
        for total in practice_minutes(text):
            if total != 30:
                issues.append(f"practice routine adds up to {total} minutes, not 30")
        if not practice_minutes(text):
            issues.append("practice routine box (<div class=\"practice\") not found")
        words = prose_words(blocks)
        if words > 1500:
            issues.append(f"{words} words of prose (cap 1500)")
        elif words < 500:
            issues.append(f"{words} words of prose (short?)")
    return issues


def main() -> None:
    paths = []
    for arg in sys.argv[1:] or ["docs"]:
        p = Path(arg)
        paths += sorted(p.rglob("*.md")) if p.is_dir() else [p]
    total = 0
    for path in paths:
        if path.name == "style-sample.md":
            continue
        found = check(path)
        total += len(found)
        print(f"== {path}: {len(found)} issue(s)")
        for item in found[:40]:
            print("   ", item)
    print(f"{total} issue(s) in {len(paths)} file(s)")


if __name__ == "__main__":
    main()
