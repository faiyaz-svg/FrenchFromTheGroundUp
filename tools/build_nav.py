"""Update the site navigation, the progress page, the home line map and the stage pages.

Reads tools/lessons.yml and writes:
  - the nav block in mkdocs.yml (between "# nav:start" and "# nav:end")
  - docs/progress.md (written lessons only, keeping any ticked boxes)
  - the line map in docs/index.md (between "lines:start" and "lines:end")
  - docs/assets/lines.json (stages and lessons, read by the lesson-page line strip)
  - the lesson list in each docs/<folder>/index.md (between the
    "lessons:start" and "lessons:end" comments); a missing index.md is
    created as a skeleton

Only pages that exist are linked or added to the nav, so the site never
has links to lessons that haven't been written. Planned lessons show on the
map as stations without a link.

Run from the repo root:  .venv/Scripts/python tools/build_nav.py
With --tracked, only pages committed to git count, so drafts on disk stay
out of the nav.
"""

from __future__ import annotations

import html
import json
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
MKDOCS = ROOT / "mkdocs.yml"
LESSONS = ROOT / "tools" / "lessons.yml"
PROGRESS = DOCS / "progress.md"
HOME = DOCS / "index.md"
LINES_JSON = DOCS / "assets" / "lines.json"

NAV_START = "# nav:start"
NAV_END = "# nav:end"
LIST_START = "<!-- lessons:start -->"
LIST_END = "<!-- lessons:end -->"
HOME_START = "<!-- lines:start -->"
HOME_END = "<!-- lines:end -->"

START_HERE = [
    ("How to use this book", "00-start-here/index.md"),
    ("The 30-minute routine", "00-start-here/the-30-minute-routine.md"),
    ("Set up voices and audio", "00-start-here/set-up-voices-and-audio.md"),
    ("Set up keyboard and Anki", "00-start-here/set-up-keyboard-and-anki.md"),
    ("Set up Mauril and free media", "00-start-here/set-up-mauril-and-free-media.md"),
    ("Standard and Quebec French", "00-start-here/standard-vs-quebec-french.md"),
    ("Practising with people in Toronto", "00-start-here/practising-with-people-in-toronto.md"),
    ("Levels and goals", "00-start-here/levels-and-goals.md"),
    ("Credits and sources", "00-start-here/credits-and-sources.md"),
    ("Progress", "progress.md"),
]

# The practice tools tab: drills that run in the browser.
PRACTICE = [
    ("Practice tools", "practice/index.md"),
    ("Conjugation", "practice/conjugation.md"),
    ("Le or la", "practice/le-or-la.md"),
    ("Fill in the blank", "practice/fill-in-the-blank.md"),
    ("Dictation", "practice/dictation.md"),
    ("Numbers", "practice/numbers.md"),
    ("Quebec words", "practice/quebec-words.md"),
    ("Say it", "practice/say-it.md"),
]

REFERENCE = [
    ("Reference", "reference/index.md"),
    ("Glossary", "reference/glossary.md"),
    ("Verb tables", "reference/verb-tables.md"),
    ("IPA chart", "reference/ipa-chart.md"),
    ("Quebec and France words", "reference/quebec-and-france-words.md"),
    ("False friends", "reference/false-friends.md"),
    ("Email formulas", "reference/email-formulas.md"),
    ("Numbers, dates and times", "reference/numbers-dates-and-times.md"),
    ("Linking words", "reference/linking-words.md"),
    ("Common mistakes", "reference/common-mistakes.md"),
    ("Montreal phrasebook", "reference/montreal-phrasebook.md"),
    ("Media", "reference/media.md"),
]

AREAS = {"sounds", "grammar", "words", "listen", "speak", "read", "write", "quebec"}
EXTRA_FLAGS = {"review"}
LEVELS = {
    "a1": ("A1", "Green line"),
    "a2": ("A2", "Orange line"),
    "b1": ("B1", "Yellow line"),
    "b2": ("B2", "Blue line"),
}

# Set by --tracked: the paths (relative to docs/) that git knows about.
TRACKED: set[str] | None = None


@dataclass
class Lesson:
    num: int
    slug: str
    title: str
    path: str  # relative to docs/
    flags: list[str]

    @property
    def exists(self) -> bool:
        return exists(self.path)

    @property
    def area(self) -> str:
        return next(flag for flag in self.flags if flag in AREAS)

    @property
    def url(self) -> str:
        """The page's URL path relative to the site root, with a trailing slash."""
        return self.path.removesuffix(".md") + "/"

    def notes(self) -> str:
        """The area and any extra flags, as shown after the title in lists."""
        return ", ".join([self.area] + [flag for flag in self.flags if flag in EXTRA_FLAGS])


@dataclass
class Folder:
    num: int
    folder: str
    level: str
    title: str
    tab: str
    summary: str
    before: str
    lessons: list[Lesson] = field(default_factory=list)

    @property
    def heading(self) -> str:
        return f"Stage {self.num}: {self.title}"


def parse_lesson(entry: list, folder: str, number: int) -> Lesson:
    # A title with an unquoted comma turns into extra list items, so check the shape.
    if not 2 <= len(entry) <= 3 or (len(entry) == 3 and not isinstance(entry[2], list)):
        raise SystemExit(f"bad lesson entry {entry!r}: quote titles that contain commas")
    slug, title = entry[0], entry[1]
    flags = list(entry[2]) if len(entry) > 2 else []
    areas = [flag for flag in flags if flag in AREAS]
    if len(areas) != 1 or not set(flags) <= AREAS | EXTRA_FLAGS:
        raise SystemExit(f"bad flags in lesson entry {entry!r}: need one area, then optional review")
    return Lesson(number, slug, title, f"{folder}/{number:02d}-{slug}.md", flags)


def load_folders() -> list[Folder]:
    data = yaml.safe_load(LESSONS.read_text(encoding="utf-8"))
    folders = []
    for n, f in enumerate(data["folders"], 1):
        if f["level"] not in LEVELS:
            raise SystemExit(f"bad level {f['level']!r} in {f['folder']}")
        folder = Folder(
            num=n,
            folder=f["folder"],
            level=f["level"],
            title=f["title"],
            tab=f.get("tab", f["title"]),
            summary=f.get("summary", ""),
            before=f.get("before", ""),
        )
        folder.lessons = [parse_lesson(e, f["folder"], i) for i, e in enumerate(f["lessons"], 1)]
        folders.append(folder)
    return folders


def exists(path: str) -> bool:
    if TRACKED is not None:
        return path in TRACKED
    return (DOCS / path).is_file()


def tracked_paths() -> set[str]:
    out = subprocess.run(
        ["git", "ls-files", "docs"], cwd=ROOT, capture_output=True, text=True, check=True
    ).stdout
    return {line.removeprefix("docs/") for line in out.splitlines()}


def q(text: str) -> str:
    """Quote a title for YAML (JSON strings are valid YAML)."""
    return json.dumps(text, ensure_ascii=False)


def build_nav(folders: list[Folder]) -> str:
    # The home page is the index of the "Start here" tab, so there is no
    # separate "Home" tab; the site title in the header also links home.
    lines = [NAV_START, "nav:", "  - Start here:", "      - index.md"]
    for title, path in START_HERE:
        if exists(path):
            lines.append(f"      - {q(title)}: {path}")

    for f in folders:
        index = f"{f.folder}/index.md"
        if not exists(index):
            continue
        lines.append(f"  - {q(f.tab)}:")
        lines.append(f"      - {index}")
        for lesson in f.lessons:
            if lesson.exists:
                lines.append(f"      - {q(lesson.title)}: {lesson.path}")

    for tab, pages in (("Practice tools", PRACTICE), ("Reference", REFERENCE)):
        found = [(t, p) for t, p in pages if exists(p)]
        if not found:
            continue
        lines.append(f"  - {tab}:")
        for title, path in found:
            if path.endswith("/index.md"):
                lines.append(f"      - {path}")
            else:
                lines.append(f"      - {q(title)}: {path}")

    lines.append(NAV_END)
    return "\n".join(lines)


def write_nav(folders: list[Folder]) -> None:
    text = MKDOCS.read_text(encoding="utf-8")
    pattern = re.compile(re.escape(NAV_START) + r".*?" + re.escape(NAV_END), re.S)
    if not pattern.search(text):
        raise SystemExit(f"mkdocs.yml has no '{NAV_START}' ... '{NAV_END}' block")
    MKDOCS.write_text(pattern.sub(lambda _: build_nav(folders), text), encoding="utf-8", newline="\n")


def ticked_paths() -> set[str]:
    if not PROGRESS.is_file():
        return set()
    done = set()
    for line in PROGRESS.read_text(encoding="utf-8").splitlines():
        m = re.match(r"\s*- \[[xX]\] \[.*?\]\((.*?)\)", line)
        if m:
            done.add(m.group(1))
    return done


def write_progress(folders: list[Folder]) -> None:
    done = ticked_paths()
    total = sum(len(f.lessons) for f in folders)
    written = sum(1 for f in folders for lesson in f.lessons if lesson.exists)
    out = [
        "# Progress",
        "",
        "Tick each lesson when you finish it. On the website, ticks are saved in the "
        "browser you use, so each device keeps its own list, and the stations on the "
        "home map fill in too. In VS Code, change `[ ]` to `[x]` in `docs/progress.md`.",
        "",
        f"Lessons written so far: {written} of {total}. New lessons appear here as they are added.",
        "",
    ]
    last_level = ""
    for f in folders:
        lessons = [lesson for lesson in f.lessons if lesson.exists]
        if not lessons:
            continue
        if f.level != last_level:
            last_level = f.level
            name, line = LEVELS[f.level]
            out += [f"## {name} {line.lower()}", ""]
        out += [f"### {f.heading}", ""]
        for lesson in lessons:
            box = "x" if lesson.path in done else " "
            out.append(f"- [{box}] [{lesson.title}]({lesson.path}) ({lesson.notes()})")
        out.append("")
    PROGRESS.write_text("\n".join(out).rstrip() + "\n", encoding="utf-8", newline="\n")


def lesson_list(f: Folder) -> str:
    lines = [LIST_START, "## Lessons", ""]
    for lesson in f.lessons:
        rel = lesson.path.removeprefix(f.folder + "/")
        text = f"[{lesson.title}]({rel})" if lesson.exists else f"{lesson.title} (not written yet)"
        lines.append(f"{lesson.num}. {text} ({lesson.notes()})")
    lines += ["", LIST_END]
    return "\n".join(lines)


def write_folder_index(f: Folder) -> None:
    path = DOCS / f.folder / "index.md"
    block = lesson_list(f)
    if not path.is_file():
        path.parent.mkdir(parents=True, exist_ok=True)
        skeleton = [
            f"# {f.heading}",
            "",
            f.summary,
            "",
            f"Before this stage: {f.before}",
            "",
            block,
            "",
            "## Cheat sheet",
            "",
            "<!-- to be written -->",
            "",
            "## Listen and watch at this level",
            "",
            "<!-- to be written -->",
            "",
        ]
        path.write_text("\n".join(skeleton), encoding="utf-8", newline="\n")
        return
    text = path.read_text(encoding="utf-8")
    pattern = re.compile(re.escape(LIST_START) + r".*?" + re.escape(LIST_END), re.S)
    if pattern.search(text):
        text = pattern.sub(lambda _: block, text)
    else:
        text = text.rstrip() + "\n\n" + block + "\n"
    path.write_text(text, encoding="utf-8", newline="\n")


def esc(text: str) -> str:
    return html.escape(text, quote=True)


def line_map(folders: list[Folder]) -> str:
    """The home page's line map: one line per level, one segment per stage, one station per lesson."""
    out = [HOME_START, '<div class="fm-map">']
    i = 0
    while i < len(folders):
        level = folders[i].level
        name, line = LEVELS[level]
        out.append(f'<section class="fm-line" data-level="{level}">')
        out.append(f'<h2 class="fm-line-name">{name} <span>{line}</span></h2>')
        while i < len(folders) and folders[i].level == level:
            f = folders[i]
            out.append(f'<div class="fm-seg" data-stage="{f.num}">')
            label = f"{f.num} · {esc(f.title)}"
            if exists(f"{f.folder}/index.md"):
                out.append(f'<a class="fm-seg-name" href="{f.folder}/">{label}</a>')
            else:
                out.append(f'<span class="fm-seg-name">{label}</span>')
            out.append('<ol class="fm-stations">')
            for lesson in f.lessons:
                dot = f'<span class="fm-dot"></span><span class="fm-st-num">{lesson.num}</span>'
                if lesson.exists:
                    out.append(
                        f'<li><a class="fm-st" href="{lesson.url}" data-lesson="{lesson.url}" '
                        f'title="{esc(lesson.title)}">{dot}</a></li>'
                    )
                else:
                    out.append(
                        f'<li><span class="fm-st fm-planned" title="{esc(lesson.title)}">{dot}</span></li>'
                    )
            out.append("</ol>")
            out.append("</div>")
            i += 1
        out.append("</section>")
    out += ["</div>", HOME_END]
    return "\n".join(out)


def write_home(folders: list[Folder]) -> bool:
    if not HOME.is_file():
        return False
    text = HOME.read_text(encoding="utf-8")
    pattern = re.compile(re.escape(HOME_START) + r".*?" + re.escape(HOME_END), re.S)
    if not pattern.search(text):
        return False
    HOME.write_text(pattern.sub(lambda _: line_map(folders), text), encoding="utf-8", newline="\n")
    return True


def write_lines_json(folders: list[Folder]) -> None:
    data = {
        "stages": [
            {
                "num": f.num,
                "folder": f.folder,
                "level": f.level,
                "title": f.title,
                "lessons": [
                    {
                        "num": lesson.num,
                        "path": lesson.url,
                        "title": lesson.title,
                        "area": lesson.area,
                        "published": lesson.exists,
                    }
                    for lesson in f.lessons
                ],
            }
            for f in folders
        ]
    }
    LINES_JSON.parent.mkdir(parents=True, exist_ok=True)
    LINES_JSON.write_text(
        json.dumps(data, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8", newline="\n"
    )


def main() -> None:
    global TRACKED
    if "--tracked" in sys.argv[1:]:
        TRACKED = tracked_paths()
    folders = load_folders()
    for f in folders:
        # A stage page appears once it has a lesson or an overview page. On disk
        # the skeleton is always created, so the nav lists every stage.
        if TRACKED is None or any(lesson.exists for lesson in f.lessons) or exists(f"{f.folder}/index.md"):
            write_folder_index(f)
    write_progress(folders)
    mapped = write_home(folders)
    write_lines_json(folders)
    write_nav(folders)
    total = sum(len(f.lessons) for f in folders)
    written = sum(1 for f in folders for lesson in f.lessons if lesson.exists)
    note = "" if mapped else " (docs/index.md has no line map markers yet)"
    print(f"{len(folders)} stages, {written} of {total} lessons written; nav, progress, map and lists updated{note}")


if __name__ == "__main__":
    main()
