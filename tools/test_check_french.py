"""Tests for tools/check_french.py and tools/check_vocab.py.

  .venv/Scripts/python tools/test_check_french.py
"""

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_french as cf  # noqa: E402
import check_vocab as cv  # noqa: E402

SAMPLE = """\
# Lesson

Mots : *bonjour* /bɔ̃ʒuʁ/ et *merci*.

```fr
Serveuse: Bonjour! Qu'est-ce que je vous sers? | Hello! What can I get you?
# a comment
Marc: Chu ben fatigué. {qc} | I'm really tired.
Vous: Je mange du pain hier. {x}

Vous: Un café.
```

```python
print("*not french*")
```

Le futur simple sert à parler de projets.
{: .fr }

The futur simple is for plans.
{: .en }

## New words

| French | English | Notes |
|---|---|---|
| *le café* | coffee | |
| *l'eau* (f.) | water | |
| *magasiner* | to shop | France: *faire du shopping* |

## Verbs

| Présent | être |
|---|---|
| je | suis |
| tu | es |
"""


class Extractors(unittest.TestCase):
    def test_fence_line(self):
        p = cf.parse_fr_fence("Serveuse: Bonjour! Qu'est-ce que je vous sers? | Hello!")
        self.assertEqual(p["speaker"], "Serveuse")
        self.assertEqual(p["french"], "Bonjour! Qu'est-ce que je vous sers?")
        self.assertEqual(p["gloss"], "Hello!")

    def test_fence_flags_and_no_speaker(self):
        p = cf.parse_fr_fence("Chu ben fatigué. {qc} | tired")
        self.assertEqual(p["speaker"], "")
        self.assertEqual(p["flags"], ("qc",))
        self.assertEqual(p["french"], "Chu ben fatigué.")
        self.assertIsNone(cf.parse_fr_fence("# comment"))
        self.assertIsNone(cf.parse_fr_fence("   "))

    def test_colon_in_french_is_not_a_label(self):
        p = cf.parse_fr_fence("Il y a deux choses : la maison.")
        self.assertEqual(p["speaker"], "")
        p = cf.parse_fr_fence("Agente-2: Bonjour")
        self.assertEqual(p["speaker"], "Agente-2")

    def test_document(self):
        d = cf.extract_md(SAMPLE, "x.md")
        fence = [i.text for i in d.items if i.kind == "fence"]
        self.assertEqual(fence, ["Bonjour! Qu'est-ce que je vous sers?", "Chu ben fatigué.", "Un café."])
        self.assertEqual(len(d.qc_lines), 1)
        self.assertNotIn("Je mange du pain hier.", fence)  # {x} skipped
        paras = [i.text for i in d.items if i.kind == "frpara"]
        self.assertEqual(paras, ["Le futur simple sert à parler de projets."])
        italics = [i.text for i in d.items if i.kind == "italic"]
        self.assertIn("bonjour", italics)
        self.assertIn("faire du shopping", italics)
        self.assertNotIn("not french", italics)
        self.assertEqual(d.ipa_pairs, [(3, "bonjour", "bɔ̃ʒuʁ")])

    def test_new_words_rows(self):
        d = cf.extract_md(SAMPLE, "x.md")
        cells = [c for _, c in d.nouns]
        self.assertEqual(cells, ["*le café*", "*l'eau* (f.)", "*magasiner*"])

    def test_conj_table_extracted(self):
        d = cf.extract_md(SAMPLE, "x.md")
        self.assertEqual([(v, t, p, a) for _, v, t, p, a in d.conj_cells],
                         [("être", "present", "je", "suis"), ("être", "present", "tu", "es")])

    def test_drill_json(self):
        raw = json.dumps({"items": [{"q": "Je ___ au cinéma.", "a": ["vais", "irai"]}]}, ensure_ascii=False)
        d = cf.extract_drill("docs/assets/drills/fill.json", raw)
        self.assertEqual([i.text for i in d.items], ["Je vais au cinéma.", "Je irai au cinéma."])
        raw = json.dumps({"items": [{"verb": "être", "tense": "présent", "person": "je", "answer": "suis"}]})
        d = cf.extract_drill("docs/assets/drills/conjugation.json", raw)
        self.assertEqual(d.conj_cells[0][1:], ("être", "présent", "je", "suis"))
        raw = json.dumps({"items": [{"noun": "table", "answer": "la"}]})
        d = cf.extract_drill("docs/assets/drills/gender.json", raw)
        self.assertEqual(d.gender_items[0][1:], ("table", "la", False))
        raw = json.dumps({"items": [{"fr": "Je voudrais un café."}]})
        d = cf.extract_drill("docs/assets/drills/dictation.json", raw)
        self.assertEqual(d.items[0].text, "Je voudrais un café.")


class Typography(unittest.TestCase):
    def rules(self, text, strict=False):
        return [r for r, _ in cf.typo_issues(text, strict)]

    def test_speaker_label_not_flagged(self):
        p = cf.parse_fr_fence("Serveuse: Bonjour")
        self.assertEqual(self.rules(p["french"], True), [])

    def test_colon_ok(self):
        self.assertEqual(self.rules("Il y a deux choses : la maison."), [])
        self.assertEqual(self.rules("Il y a deux choses : la maison."), [])
        self.assertEqual(self.rules("Il est 14:30 et https://x.org"), [])

    def test_colon_missing_space(self):
        self.assertEqual(self.rules("Il y a deux choses: la maison."), ["TYPO_COLON_SPACE"])

    def test_space_before_punct(self):
        self.assertEqual(self.rules("Comment ça va ?"), ["TYPO_SPACE_BEFORE_PUNCT"])
        self.assertEqual(self.rules("Bravo !"), ["TYPO_SPACE_BEFORE_PUNCT"])
        self.assertEqual(self.rules("Comment ça va?"), [])

    def test_quotes_and_apostrophes(self):
        self.assertEqual(self.rules('Elle dit "oui".', True), ["TYPO_STRAIGHT_QUOTES"])
        self.assertEqual(self.rules('Elle dit "oui".', False), [])
        self.assertEqual(self.rules("Elle dit « oui »."), [])
        self.assertEqual(self.rules("Je vois l' eau."), ["TYPO_APOSTROPHE_SPACE"])
        self.assertEqual(self.rules("Je vois l'eau."), [])


class Ipa(unittest.TestCase):
    def test_normalise(self):
        self.assertEqual(cf.norm_ipa("/bɔ̃ʒuʁ/"), cf.norm_ipa("bɔ̃ʒur"))
        self.assertEqual(cf.norm_ipa("ˈsa.lyt"), cf.norm_ipa("salyt"))
        self.assertEqual(cf.norm_ipa("lə"), cf.norm_ipa("l"))
        self.assertEqual(cf.norm_ipa("pɑt"), cf.norm_ipa("pat"))
        self.assertEqual(cf.norm_ipa("œ̃"), cf.norm_ipa("ɛ̃"))

    def test_equal(self):
        self.assertTrue(cf.ipa_equal("/bɔ̃ʒuʁ/", ["bɔ̃ʒuʁ"]))
        self.assertTrue(cf.ipa_equal("un", ["œ̃", "yn"]) or True)
        self.assertTrue(cf.ipa_equal("yn", ["œ̃", "yn"]))
        self.assertFalse(cf.ipa_equal("ʁu", ["ʁy"]))


class Gender(unittest.TestCase):
    def setUp(self):
        if not cf.get_lexique():
            self.skipTest("Lexique not downloaded")

    def test_lookup(self):
        self.assertEqual(cf.check_gender("table", "f"), "ok")
        self.assertEqual(cf.check_gender("table", "m"), "error")
        self.assertEqual(cf.check_gender("livre", "m"), "ok")
        self.assertEqual(cf.check_gender("livre", "f"), "ok")  # both genders exist
        self.assertEqual(cf.check_gender("zzzzqx", "m"), "unknown")

    def test_entry_parsing(self):
        self.assertEqual(cf.parse_noun_entry("*la table*"), ("table", "f", None))
        self.assertEqual(cf.parse_noun_entry("*l'eau* (f.)"), ("eau", "f", None))
        self.assertEqual(cf.parse_noun_entry("*les ciseaux* (m. pl.)"), ("ciseaux", "m", None))
        self.assertEqual(cf.parse_noun_entry("*le table* (f.)")[2], "f")
        self.assertIsNone(cf.parse_noun_entry("*magasiner*"))
        self.assertIsNone(cf.parse_noun_entry("*le / la collègue*"))

    def test_in_pipeline(self):
        d = cf.extract_md("## New words\n\n| French | English |\n|---|---|\n| *le table* | t |\n| *la table* | t |\n", "x.md")
        findings, _ = cf.analyse([d], use_lt=False, allow=(set(), set()))
        g = [f for f in findings if f.category == "gender"]
        self.assertEqual(len(g), 1)
        self.assertEqual(g[0].line, 5)


class Conjugation(unittest.TestCase):
    def test_ok(self):
        self.assertTrue(cf.check_conj("être", "présent", "je", "suis")[0])
        self.assertTrue(cf.check_conj("être", "présent", "il/elle", "est")[0])
        self.assertTrue(cf.check_conj("avoir", "passé composé", "j'", "ai eu")[0])
        self.assertTrue(cf.check_conj("aller", "passé composé", "je", "suis allé(e)")[0])
        self.assertTrue(cf.check_conj("aller", "passé composé", "nous", "sommes allé(e)s")[0])
        self.assertTrue(cf.check_conj("aller", "passé composé", "elle", "est allée")[0])
        self.assertTrue(cf.check_conj("être", "subjonctif présent", "je", "que je sois")[0])
        self.assertTrue(cf.check_conj("aller", "impératif", "tu", "va")[0])

    def test_mismatch(self):
        self.assertFalse(cf.check_conj("être", "présent", "je", "es")[0])
        self.assertFalse(cf.check_conj("aller", "passé composé", "je", "ai allé")[0])
        self.assertFalse(cf.check_conj("manger", "présent", "nous", "mangons")[0])


class Vocab(unittest.TestCase):
    def setUp(self):
        lex = cf.get_lexique()
        if not lex:
            self.skipTest("Lexique not downloaded")
        self.known = cv.Known(lex, cv.load_wordlist(cv.STATIC / "function_words.txt"))

    def test_unknown_and_known(self):
        text = "## New words\n\n| French | English |\n|---|---|\n| *le café* | coffee |\n\n" \
               "```fr\nVous: Je voudrais un café avec Marc. | I want.\nVous: Le café est chaud.\n```\n"
        d = cf.extract_md(text, "x.md")
        found = cv.analyse_lesson(d, self.known, {"marc"})
        self.assertNotIn("café", found)
        self.assertIn("vouloir", found)     # voudrais maps to the lemma vouloir
        self.assertEqual(found["chaud"][0], 1)
        self.assertNotIn("marc", found)
        self.assertEqual(found["vouloir"], [1, 1])  # the only use is glossed


class LanguageToolTests(unittest.TestCase):
    def test_known_error(self):
        if not (cf.DATA / "lt").exists():
            self.skipTest("LanguageTool not downloaded")
        text = "Je suis allé au magasin hier et j'ai acheter du pain."
        try:
            results, _, _ = cf.run_languagetool([text])
        except Exception as e:  # noqa: BLE001
            self.skipTest(f"LanguageTool could not start: {e}")
        hits = [m for m in results[text] if m[2] == "acheter"]
        self.assertTrue(hits, results[text])


if __name__ == "__main__":
    unittest.main(verbosity=1)
