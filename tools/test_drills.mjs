import { test } from "node:test"
import assert from "node:assert/strict"
import { createRequire } from "node:module"

const require = createRequire(import.meta.url)
const drills = require("../docs/javascripts/drills.js")
const sayit = require("../docs/javascripts/sayit.js")
const speak = require("../docs/javascripts/speak.js")
require("../docs/javascripts/translate.js")

const { normalize, grade, numberToFrench, matchInteger, matchPrice, matchPhone, matchTime, matchNumber, genNumber, leitnerPick, leitnerUpdate } = drills

test("normalize", () => {
  assert.equal(normalize("  Je   vais.  "), "je vais")
  assert.equal(normalize("L\u2019eau"), "l'eau")
  assert.equal(normalize("a b"), "a b")
})

test("grade right", () => {
  assert.equal(grade("suis", ["suis"]), "right")
  assert.equal(grade("  Suis ", ["suis"]), "right")
  assert.equal(grade("j\u2019ai", ["j'ai"]), "right")
  assert.equal(grade("été", ["été"]), "right")
  assert.equal(grade("vont", ["vais", "vont"]), "right")
  assert.equal(grade("je   vais", ["je vais"]), "right")
  assert.equal(grade("Il y a.", ["il y a"]), "right")
})

test("grade almost", () => {
  assert.equal(grade("etes", ["êtes"]), "almost")
  assert.equal(grade("ETES", ["êtes"]), "almost")
  assert.equal(grade("ÉTÉ", ["été"]), "almost")
  assert.equal(grade("cafe", ["café"]), "almost")
})

test("grade wrong", () => {
  assert.equal(grade("est", ["es"]), "wrong")
  assert.equal(grade("", ["es"]), "wrong")
})

test("grade loose ignores punctuation", () => {
  assert.equal(grade("je voudrais un cafe s'il vous plait", ["Je voudrais un café, s'il vous plaît."], { loose: true }), "almost")
  assert.equal(grade("Ou est la gare", ["Où est la gare?"], { loose: true }), "almost")
  assert.equal(grade("Où est la gare", ["Où est la gare?"], { loose: true }), "right")
})

test("number words", () => {
  const cases = { 0: "zéro", 16: "seize", 17: "dix-sept", 21: "vingt et un", 61: "soixante et un", 70: "soixante-dix", 71: "soixante et onze", 80: "quatre-vingts", 81: "quatre-vingt-un", 99: "quatre-vingt-dix-neuf", 100: "cent", 200: "deux cents", 201: "deux cent un", 1000: "mille", 2000: "deux mille", 80000: "quatre-vingt mille", 1998: "mille neuf cent quatre-vingt-dix-huit" }
  for (const [n, w] of Object.entries(cases)) assert.equal(numberToFrench(Number(n)), w)
})

test("integer and year matchers", () => {
  assert.ok(matchInteger("1 234", 1234))
  assert.ok(matchInteger("1234", 1234))
  assert.ok(matchInteger("1 234", 1234))
  assert.ok(!matchInteger("1235", 1234))
  assert.ok(!matchInteger("abc", 1234))
})

test("price matcher", () => {
  assert.ok(matchPrice("4,50", 450))
  assert.ok(matchPrice("4.50", 450))
  assert.ok(matchPrice("4,50 $", 450))
  assert.ok(matchPrice("4,5", 450))
  assert.ok(matchPrice("12,99$", 1299))
  assert.ok(matchPrice("4", 400))
  assert.ok(!matchPrice("4,05", 450))
  assert.ok(!matchPrice("", 450))
})

test("phone matcher", () => {
  assert.ok(matchPhone("514 555-0142", "5145550142"))
  assert.ok(matchPhone("5145550142", "5145550142"))
  assert.ok(matchPhone("(514) 555 0142", "5145550142"))
  assert.ok(!matchPhone("514 555-0143", "5145550142"))
})

test("time matcher", () => {
  assert.ok(matchTime("14 h 30", 14, 30))
  assert.ok(matchTime("14h30", 14, 30))
  assert.ok(matchTime("14:30", 14, 30))
  assert.ok(matchTime("14 h", 14, 0))
  assert.ok(matchTime("9 h 05", 9, 5))
  assert.ok(!matchTime("14 h 31", 14, 30))
  assert.ok(!matchTime("fourteen", 14, 30))
})

test("generated numbers match their own display", () => {
  for (let stage = 1; stage <= 16; stage++) {
    for (let i = 0; i < 200; i++) {
      const it = genNumber(stage)
      assert.ok(matchNumber(it, it.display), it.kind + " " + it.display)
      assert.ok(it.spoken.length > 0)
    }
  }
})

test("leitner", () => {
  const ids = ["a", "b", "c"]
  const boxes = { a: 4, b: 1, c: 4 }
  let b = 0
  for (let i = 0; i < 300; i++) if (leitnerPick(ids, boxes, Math.random) === "b") b++
  assert.ok(b > 100)
  assert.notEqual(leitnerPick(ids, boxes, () => 0, "a"), "a")
  const m = {}
  leitnerUpdate(m, "x", "right")
  assert.equal(m.x, 2)
  leitnerUpdate(m, "x", "almost")
  assert.equal(m.x, 1)
})

test("sayit compare", () => {
  const { compareWords, tokenize } = sayit
  assert.deepEqual(tokenize("J\u2019ai l'eau, qu'il vient."), ["j'", "ai", "l'", "eau", "qu'", "il", "vient"])
  assert.deepEqual(tokenize("Aujourd'hui, peut-être"), ["aujourd'hui", "peut", "être"])
  let r = compareWords("Je voudrais un café", "je voudrais un café")
  assert.ok(r.allMatched)
  assert.equal(r.summary, "All words matched")
  r = compareWords("Je voudrais un café", "je voudrais café")
  assert.deepEqual(r.missing, ["un"])
  assert.equal(r.summary, "Missed: un")
  r = compareWords("J'ai l'eau", "j ai l eau")
  assert.deepEqual(r.missing, ["j'", "l'"])
  r = compareWords("J'ai l'eau", "J\u2019ai l\u2019eau")
  assert.ok(r.allMatched)
  r = compareWords("Bonjour", "bonjour tout le monde")
  assert.deepEqual(r.missing, [])
  assert.deepEqual(r.extra, ["tout", "le", "monde"])
})

test("fr line parsing", () => {
  const { parseFrLine, parseFrBlock } = speak
  let l = parseFrLine("Serveuse: Bonjour! Qu'est-ce que je vous sers? | Hello! What can I get you?")
  assert.equal(l.speaker, "Serveuse")
  assert.equal(l.fr, "Bonjour! Qu'est-ce que je vous sers?")
  assert.equal(l.gloss, "Hello! What can I get you?")
  l = parseFrLine("Marc: Chu ben fatigué. {qc} | I'm really tired.")
  assert.equal(l.speaker, "Marc")
  assert.equal(l.fr, "Chu ben fatigué.")
  assert.ok(l.qc)
  assert.ok(!l.x)
  l = parseFrLine("Il y a deux choses : le pain et le lait.")
  assert.equal(l.speaker, "")
  assert.equal(l.fr, "Il y a deux choses : le pain et le lait.")
  assert.equal(l.gloss, "")
  l = parseFrLine("Agente-2: Je suis allée. {x} {qc}")
  assert.equal(l.speaker, "Agente-2")
  assert.ok(l.x && l.qc)
  assert.equal(l.fr, "Je suis allée.")
  assert.equal(parseFrLine("# a comment"), null)
  assert.equal(parseFrLine("   "), null)
  l = parseFrLine("Merci | thanks | really")
  assert.equal(l.gloss, "thanks | really")
  const g = parseFrBlock("# c\nA: un\nB: deux\n\n\nC: trois | three\n")
  assert.equal(g.length, 2)
  assert.equal(g[0].lines.length, 2)
  assert.equal(g[1].lines[0].gloss, "three")
})

test("voice picking", () => {
  const v = (name, lang) => ({ name, lang, voiceURI: name })
  const all = [v("Microsoft Hortense", "fr-FR"), v("Microsoft Caroline", "fr-CA"), v("Microsoft Sylvie Online (Natural)", "fr-CA"), v("Microsoft Antoine Online (Natural)", "fr-CA"), v("Zira", "en-US")]
  const qc = speak.pickVoices(all, "qc", "")
  assert.match(qc[0].name, /Sylvie|Antoine/)
  assert.notEqual(qc[0], qc[1])
  assert.equal(qc[1].lang, "fr-CA")
  const fr = speak.pickVoices(all, "fr", "")
  assert.equal(fr[0].name, "Microsoft Hortense")
  assert.deepEqual(speak.pickVoices([v("Zira", "en-US")], "qc", ""), [null, null])
})
