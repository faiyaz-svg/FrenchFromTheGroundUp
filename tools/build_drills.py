"""Merge the per-stage drill items into the files the practice pages load.

Each stage writes tools/drills_src/NN.json:

    {"conjugation": [...], "gender": [...], "fill": [...],
     "dictation": [...], "quebec-words": [...]}

This script joins them, in stage order, into docs/assets/drills/<name>.json
as {"items": [...]}, and drops exact duplicates. With --tracked, only source
files committed to git are used, so drafts on disk are left out.

Run from the repo root:  .venv/Scripts/python tools/build_drills.py [--tracked]
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "tools" / "drills_src"
OUT = ROOT / "docs" / "assets" / "drills"
FILES = {
    "conjugation": "conjugation.json",
    "gender": "gender.json",
    "fill": "fill.json",
    "dictation": "dictation.json",
    "quebec-words": "quebec-words.json",
}
REQUIRED = {
    "conjugation": ("verb", "tense", "person", "answer", "stage"),
    "gender": ("noun", "answer", "stage"),
    "fill": ("q", "a", "stage"),
    "dictation": ("fr", "stage"),
    "quebec-words": ("qc", "std", "en", "stage"),
}


def tracked_sources() -> set[str]:
    out = subprocess.run(["git", "ls-files", "tools/drills_src"], cwd=ROOT, capture_output=True, text=True, check=True)
    return {line.strip() for line in out.stdout.splitlines() if line.strip()}


def main() -> int:
    only_tracked = "--tracked" in sys.argv
    sources = sorted(SRC.glob("*.json"))
    if only_tracked:
        keep = tracked_sources()
        sources = [p for p in sources if p.relative_to(ROOT).as_posix() in keep]
    merged: dict[str, list] = {k: [] for k in FILES}
    seen: dict[str, set] = {k: set() for k in FILES}
    problems = 0
    for path in sources:
        data = json.loads(path.read_text(encoding="utf-8"))
        for kind, items in data.items():
            if kind not in FILES:
                print(f"{path.name}: unknown drill kind {kind!r}")
                problems += 1
                continue
            for i, item in enumerate(items):
                missing = [f for f in REQUIRED[kind] if f not in item]
                if missing:
                    print(f"{path.name}: {kind}[{i}] is missing {', '.join(missing)}")
                    problems += 1
                    continue
                if kind == "gender" and item["answer"] not in ("le", "la"):
                    print(f"{path.name}: gender[{i}] answer must be le or la")
                    problems += 1
                    continue
                if kind == "fill" and not isinstance(item["a"], list):
                    print(f"{path.name}: fill[{i}] 'a' must be a list")
                    problems += 1
                    continue
                key = json.dumps(item, sort_keys=True, ensure_ascii=False)
                if key in seen[kind]:
                    continue
                seen[kind].add(key)
                merged[kind].append(item)
    if problems:
        print(f"{problems} problem(s); nothing written")
        return 1
    if not any(merged.values()):
        print("no drill sources found; nothing written")
        return 0
    OUT.mkdir(parents=True, exist_ok=True)
    for kind, name in FILES.items():
        items = sorted(merged[kind], key=lambda it: it["stage"])
        text = json.dumps({"items": items}, ensure_ascii=False, indent=1)
        (OUT / name).write_text(text + "\n", encoding="utf-8", newline="\n")
        print(f"{name}: {len(items)} items")
    return 0


if __name__ == "__main__":
    sys.exit(main())
