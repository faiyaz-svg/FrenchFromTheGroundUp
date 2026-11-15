# French From the Ground Up

A self-study French textbook that takes a complete beginner to B2: speaking, listening and writing French for Montreal, Quebec and bilingual work in Canada. It teaches standard French and, from the first stage, how to understand Quebec French. There are 16 stages on four lines (A1 to B2), about 200 lessons, and each lesson has a 30-minute practice routine. Every French line plays in your browser, and you can speak a line and check it.

Read it online: https://faiyaz-svg.github.io/FrenchFromTheGroundUp/

The sibling books: [Math From the Ground Up](https://faiyaz-svg.github.io/MathFromTheGroundUp/), [CS From the Ground Up](https://faiyaz-svg.github.io/CSFromTheGroundUp/) and [Music From the Ground Up](https://faiyaz-svg.github.io/MusicFromTheGroundUp/).

## Preview locally

```bash
py -m venv .venv
.venv/Scripts/python -m pip install -r requirements-dev.txt
.venv/Scripts/zensical serve
```

Then open http://127.0.0.1:8000/FrenchFromTheGroundUp/. The writing rules are in `STYLE.md`, the lesson layout in `LESSON_TEMPLATE.md` and the site design in `DESIGN.md`.

## Credits

- Audio comes from the voices already on your device (the browser's speech synthesis). No audio files are shipped.
- The French is checked locally with [LanguageTool](https://languagetool.org/) and [verbecc](https://github.com/bretttolbert/verbecc). Vocabulary and noun genders are checked against [Lexique](http://www.lexique.org/) (CC BY-SA 4.0), and pronunciations against [ipa-dict](https://github.com/open-dict-data/ipa-dict) (MIT). These are check tools only and are not part of the site.
- The full list is on the credits page of the book.
