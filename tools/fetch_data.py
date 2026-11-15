"""Download the data the French checkers need into tools/data/ (gitignored).

Run from the repo root:
  .venv/Scripts/python tools/fetch_data.py

Fetches (each skipped if already present):
  Lexique 3.83 TSV   CC BY-SA 4.0   http://www.lexique.org/
  ipa-dict fr_FR.txt MIT            https://github.com/open-dict-data/ipa-dict
  LanguageTool       LGPL 2.1+      downloaded by language_tool_python into tools/data/lt/
"""

from __future__ import annotations

import os
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "tools" / "data"
LT_DIR = DATA / "lt"

FILES = [
    (
        "Lexique383.tsv",
        ["https://www.lexique.org/databases/Lexique383/Lexique383.tsv",
         "http://www.lexique.org/databases/Lexique383/Lexique383.tsv"],
        "CC BY-SA 4.0 (New, Pallier, et al., lexique.org)",
    ),
    (
        "fr_FR.txt",
        ["https://raw.githubusercontent.com/open-dict-data/ipa-dict/master/data/fr_FR.txt"],
        "MIT (open-dict-data/ipa-dict)",
    ),
]


def download(urls: list[str], dest: Path) -> bool:
    for url in urls:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "french-book-checker"})
            with urllib.request.urlopen(req, timeout=120) as r, open(dest, "wb") as f:
                while True:
                    chunk = r.read(1 << 16)
                    if not chunk:
                        break
                    f.write(chunk)
            print(f"  ok: {url}")
            return True
        except Exception as e:  # noqa: BLE001
            print(f"  failed: {url} ({e})")
            if dest.exists():
                dest.unlink()
    return False


def setup_languagetool() -> None:
    os.environ["LTP_PATH"] = str(LT_DIR)
    LT_DIR.mkdir(parents=True, exist_ok=True)
    if any(LT_DIR.glob("LanguageTool-*")):
        print("LanguageTool: already present in tools/data/lt/")
        return
    print("LanguageTool: downloading (about 200 MB) ...")
    import language_tool_python

    tool = language_tool_python.LanguageTool("fr")
    tool.close()
    print("LanguageTool: installed (LGPL 2.1+)")


def main() -> int:
    DATA.mkdir(parents=True, exist_ok=True)
    bad = 0
    for name, urls, licence in FILES:
        dest = DATA / name
        if dest.exists() and dest.stat().st_size > 0:
            print(f"{name}: present, {dest.stat().st_size / 1e6:.1f} MB, {licence}")
            continue
        print(f"{name}: downloading")
        if download(urls, dest):
            print(f"{name}: {dest.stat().st_size / 1e6:.1f} MB, {licence}")
        else:
            bad += 1
    try:
        setup_languagetool()
    except Exception as e:  # noqa: BLE001
        print(f"LanguageTool setup failed: {e}")
        bad += 1
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
