// Practice drills: conjugation, le or la, fill in the blank, dictation, numbers
// and Quebec words (say-it lives in sayit.js). A page holds
// <div class="fm-tool" data-tool="..."></div>. Drill data comes from
// assets/drills/<name>.json. Progress is saved in localStorage under
// "frenchftgu-practice-v1:<tool>". Pure helpers are exported for node tests.
(function () {
  "use strict"

  var PREFIX = "frenchftgu-practice-v1"

  // ---------- grading ----------

  function normalize(s) {
    s = String(s == null ? "" : s)
      .normalize("NFC")
      .replace(/[\u2018\u2019\u02bc]/g, "'")
      .replace(/[   ]/g, " ")
      .replace(/\s+/g, " ")
      .trim()
    s = s.replace(/\.$/, "")
    if (s) s = s.charAt(0).toLowerCase() + s.slice(1)
    return s
  }
  function stripAccents(s) {
    return String(s).normalize("NFD").replace(/[̀-ͯ]/g, "")
  }
  function stripPunct(s) {
    return String(s)
      .replace(/[.,;:!?«»"()]/g, " ")
      .replace(/\s+/g, " ")
      .trim()
  }
  // opts.loose: ignore punctuation (used for dictation).
  function grade(input, answers, opts) {
    var list = Array.isArray(answers) ? answers : [answers]
    var loose = opts && opts.loose
    function prep(s) {
      s = normalize(s)
      if (loose) s = stripPunct(s)
      return s
    }
    var a = prep(input)
    var i
    for (i = 0; i < list.length; i++) {
      if (a === prep(list[i])) return "right"
    }
    var fold = function (s) { return stripAccents(prep(s)).toLowerCase() }
    var b = fold(input)
    for (i = 0; i < list.length; i++) {
      if (b === fold(list[i])) return "almost"
    }
    return "wrong"
  }

  // ---------- French number words ----------

  var UNITS = ["zéro", "un", "deux", "trois", "quatre", "cinq", "six", "sept", "huit", "neuf", "dix", "onze", "douze", "treize", "quatorze", "quinze", "seize", "dix-sept", "dix-huit", "dix-neuf"]
  var TENS = { 2: "vingt", 3: "trente", 4: "quarante", 5: "cinquante", 6: "soixante" }

  function lt100(n, final) {
    if (n < 20) return UNITS[n]
    var t = Math.floor(n / 10)
    var u = n % 10
    if (t <= 6) {
      if (u === 0) return TENS[t]
      if (u === 1) return TENS[t] + " et un"
      return TENS[t] + "-" + UNITS[u]
    }
    if (t === 7) {
      if (n === 71) return "soixante et onze"
      return "soixante-" + UNITS[n - 60]
    }
    if (n === 80) return final ? "quatre-vingts" : "quatre-vingt"
    return "quatre-vingt-" + UNITS[n - 80]
  }
  function lt1000(n, final) {
    var c = Math.floor(n / 100)
    var r = n % 100
    if (c === 0) return lt100(r, final)
    var head = c === 1 ? "cent" : UNITS[c] + " cent" + (r === 0 && final ? "s" : "")
    return r ? head + " " + lt100(r, final) : head
  }
  // 0 to 999 999.
  function numberToFrench(n) {
    n = Math.floor(n)
    if (n < 0 || n > 999999) return String(n)
    if (n === 0) return UNITS[0]
    if (n < 1000) return lt1000(n, true)
    var th = Math.floor(n / 1000)
    var r = n % 1000
    var head = th === 1 ? "mille" : lt1000(th, false) + " mille"
    return r ? head + " " + lt1000(r, true) : head
  }

  var DIGIT_WORDS = ["zéro", "un", "deux", "trois", "quatre", "cinq", "six", "sept", "huit", "neuf"]

  function pad2(n) {
    return (n < 10 ? "0" : "") + n
  }
  function fmtInt(n) {
    return String(n).replace(/\B(?=(\d{3})+(?!\d))/g, " ")
  }

  // ---------- number items and answer matchers ----------

  var CLEAN_SPACE = /[\s   ]/g

  function matchInteger(input, n) {
    var s = String(input).replace(CLEAN_SPACE, "")
    return /^\d+$/.test(s) && Number(s) === n
  }
  function matchPrice(input, cents) {
    var s = String(input).toLowerCase().replace(/dollars?|\$/g, "").replace(CLEAN_SPACE, "").replace(",", ".")
    if (!/^\d+(\.\d{1,2})?$/.test(s)) return false
    return Math.round(parseFloat(s) * 100) === cents
  }
  function matchPhone(input, digits) {
    return String(input).replace(/\D/g, "") === String(digits)
  }
  function matchTime(input, hh, mm) {
    var s = String(input).toLowerCase().replace(CLEAN_SPACE, "")
    var m = /^(\d{1,2})(?:h|:|heures?)(\d{1,2})?$/.exec(s)
    if (!m) return false
    return Number(m[1]) === hh && Number(m[2] || 0) === mm
  }
  function matchNumber(item, input) {
    var d = item.data
    switch (item.kind) {
      case "int":
      case "year":
        return matchInteger(input, d.n)
      case "price":
        return matchPrice(input, d.cents)
      case "phone":
        return matchPhone(input, d.digits)
      case "time":
        return matchTime(input, d.h, d.m)
    }
    return false
  }

  var BANDS = [20, 69, 100, 1000, 9999, 99999]
  function bandIndex(stage) {
    if (stage <= 1) return 0
    if (stage === 2) return 1
    if (stage <= 4) return 2
    if (stage <= 6) return 3
    if (stage <= 8) return 4
    return 5
  }
  function rint(rand, n) {
    return Math.floor(rand() * n)
  }

  function genNumber(stage, rand) {
    rand = rand || Math.random
    stage = stage || 1
    var kinds = [["int", 4]]
    if (stage >= 2) kinds.push(["phone", 1])
    if (stage >= 3) kinds.push(["price", 2])
    if (stage >= 4) kinds.push(["time", 2])
    if (stage >= 5) kinds.push(["year", 1])
    var total = kinds.reduce(function (a, k) { return a + k[1] }, 0)
    var roll = rand() * total
    var kind = "int"
    for (var i = 0; i < kinds.length; i++) {
      roll -= kinds[i][1]
      if (roll < 0) {
        kind = kinds[i][0]
        break
      }
    }
    var item
    if (kind === "int") {
      var band = BANDS[rint(rand, bandIndex(stage) + 1)]
      var n = rint(rand, band + 1)
      item = { kind: kind, data: { n: n }, display: fmtInt(n), spoken: numberToFrench(n), hint: "A number." }
    } else if (kind === "year") {
      var y = 1900 + rint(rand, 131)
      item = { kind: kind, data: { n: y }, display: String(y), spoken: numberToFrench(y), hint: "A year." }
    } else if (kind === "price") {
      var dollars = 1 + rint(rand, stage < 5 ? 20 : 200)
      var cl = [0, 25, 50, 75, 99, 95, 49, rint(rand, 100)]
      var c = cl[rint(rand, cl.length)]
      var cents = dollars * 100 + c
      var spoken = numberToFrench(dollars) + (dollars === 1 ? " dollar" : " dollars") + (c ? " " + numberToFrench(c) : "")
      item = { kind: kind, data: { cents: cents }, display: dollars + "," + pad2(c) + " $", spoken: spoken, hint: "A price. Type it like 4,50 $." }
    } else if (kind === "phone") {
      var areas = ["514", "438", "450", "613", "416", "819"]
      var area = areas[rint(rand, areas.length)]
      var last = "01" + pad2(rint(rand, 100))
      var digits = area + "555" + last
      var words = function (s) { return s.split("").map(function (ch) { return DIGIT_WORDS[Number(ch)] }).join(" ") }
      item = {
        kind: kind,
        data: { digits: digits },
        display: area + " 555-" + last,
        spoken: words(area) + ", " + words("555") + ", " + words(last),
        hint: "A phone number. Type the 10 digits.",
      }
    } else {
      var hh = 1 + rint(rand, 23)
      var mm = stage < 6 ? [0, 15, 30, 45][rint(rand, 4)] : rint(rand, 60)
      var hw = numberToFrench(hh).replace(/ et un$/, " et une").replace(/(^|[ -])un$/, "$1une")
      var sp = hw + (hh === 1 ? " heure" : " heures") + (mm ? " " + numberToFrench(mm) : "")
      item = { kind: kind, data: { h: hh, m: mm }, display: hh + " h" + (mm ? " " + pad2(mm) : ""), spoken: sp, hint: "A time. Type it like 14 h 30." }
    }
    return item
  }

  // ---------- Leitner queue ----------

  function leitnerWeight(box) {
    if (box === undefined || box === null) return 6
    return { 1: 8, 2: 4, 3: 2, 4: 1 }[box] || 1
  }
  // ids: array of strings; boxes: map id -> box; avoid: id not to repeat.
  function leitnerPick(ids, boxes, rand, avoid) {
    rand = rand || Math.random
    var pool = ids.length > 1 && avoid !== undefined ? ids.filter(function (id) { return id !== avoid }) : ids
    if (!pool.length) return undefined
    var weights = pool.map(function (id) { return leitnerWeight((boxes || {})[id]) })
    var total = weights.reduce(function (a, b) { return a + b }, 0)
    var roll = rand() * total
    for (var i = 0; i < pool.length; i++) {
      roll -= weights[i]
      if (roll < 0) return pool[i]
    }
    return pool[pool.length - 1]
  }
  function leitnerUpdate(boxes, id, result) {
    var cur = boxes[id] || 1
    boxes[id] = result === "right" ? Math.min(cur + 1, 4) : 1
    return boxes
  }

  var api = {
    normalize: normalize,
    stripAccents: stripAccents,
    grade: grade,
    numberToFrench: numberToFrench,
    matchInteger: matchInteger,
    matchPrice: matchPrice,
    matchPhone: matchPhone,
    matchTime: matchTime,
    matchNumber: matchNumber,
    genNumber: genNumber,
    leitnerPick: leitnerPick,
    leitnerUpdate: leitnerUpdate,
  }
  if (typeof module !== "undefined" && module.exports) module.exports = api
  if (typeof window === "undefined" || typeof document === "undefined") return

  // ---------- browser helpers ----------

  function store(name, fallback) {
    try {
      var raw = localStorage.getItem(PREFIX + ":" + name)
      return raw === null ? fallback : JSON.parse(raw)
    } catch (e) {
      return fallback
    }
  }
  function save(name, value) {
    try {
      localStorage.setItem(PREFIX + ":" + name, JSON.stringify(value))
    } catch (e) { /* storage blocked: the drill still works for this visit */ }
  }

  function h(tag, attrs, kids) {
    var el = document.createElement(tag)
    for (var k in attrs || {}) {
      var v = attrs[k]
      if (k === "text") el.textContent = v
      else if (k.indexOf("on") === 0) el.addEventListener(k.slice(2), v)
      else if (v !== false && v !== null && v !== undefined) el.setAttribute(k, v === true ? "" : v)
    }
    ;(kids || []).forEach(function (c) {
      if (c) el.appendChild(typeof c === "string" ? document.createTextNode(c) : c)
    })
    return el
  }

  // The site root, worked out once from this script's own URL (javascripts/x.js).
  // The __config base is relative to the first page loaded, so it goes stale
  // after instant navigation; the script URL does not.
  var FM_SITE_ROOT = (function () {
    try {
      var s = typeof document !== "undefined" && document.currentScript && document.currentScript.src
      if (s) return new URL("../", s).href
    } catch (e) { /* fall through */ }
    return null
  })()

  function baseUrl() {
    if (FM_SITE_ROOT) return FM_SITE_ROOT

    try {
      var el = document.getElementById("__config")
      if (el) {
        var cfg = JSON.parse(el.textContent)
        if (cfg && typeof cfg.base === "string") return new URL(cfg.base.replace(/\/?$/, "/"), location.href).href
      }
    } catch (e) { /* fall through */ }
    var marker = "/FrenchFromTheGroundUp/"
    var i = location.pathname.indexOf(marker)
    if (i >= 0) return location.origin + location.pathname.slice(0, i + marker.length)
    return location.origin + "/"
  }

  var cleanups = []
  function onCleanup(fn) {
    cleanups.push(fn)
  }
  function onDocKey(fn) {
    var handler = function (e) {
      var t = e.target
      if (e.ctrlKey || e.metaKey || e.altKey) return
      if (t && /^(INPUT|SELECT|TEXTAREA)$/.test(t.tagName)) return
      fn(e)
    }
    document.addEventListener("keydown", handler)
    onCleanup(function () { document.removeEventListener("keydown", handler) })
  }

  var ACCENTS = ["é", "è", "ê", "à", "â", "ç", "ô", "î", "û", "ù", "ë", "ï", "œ"]

  function accentRow(input) {
    var row = h("div", { class: "fm-accents", role: "group", "aria-label": "Accent letters" })
    ACCENTS.forEach(function (ch) {
      var b = h("button", { type: "button", class: "fm-btn fm-accent", text: ch, "aria-label": "Insert " + ch })
      b.addEventListener("mousedown", function (e) { e.preventDefault() })
      b.addEventListener("click", function () {
        if (input.readOnly || input.disabled) return
        var s = input.selectionStart
        var e = input.selectionEnd
        if (s === null || s === undefined) {
          s = e = input.value.length
        }
        input.value = input.value.slice(0, s) + ch + input.value.slice(e)
        input.focus()
        input.setSelectionRange(s + 1, s + 1)
      })
      row.appendChild(b)
    })
    return row
  }

  function shuffle(a) {
    a = a.slice()
    for (var i = a.length - 1; i > 0; i--) {
      var j = Math.floor(Math.random() * (i + 1))
      var t = a[i]
      a[i] = a[j]
      a[j] = t
    }
    return a
  }

  function say(text, opts) {
    if (window.FMSpeak) return window.FMSpeak.speak(text, opts)
    return Promise.resolve(false)
  }

  // ---------- the drill engine ----------

  // cfg: file | gen, itemId, mode ("type" | "choice" | "custom"), prompt,
  // grade, reveal, extra, choices, render, controls, autoplay, loose.
  function runTool(root, name, cfg) {
    var state = store(name, null) || {}
    state.stage = Number(state.stage) >= 1 && Number(state.stage) <= 16 ? Number(state.stage) : 16
    state.boxes = state.boxes && typeof state.boxes === "object" ? state.boxes : {}
    var counts = { right: 0, almost: 0, wrong: 0 }
    var asked = 0
    var retry = []
    var lastId
    var items = []
    var byId = {}
    var timers = []
    var keyFn = null
    var answered = false

    root.textContent = ""
    var wrap = h("div", { class: "fm-drill" })
    var stageSel = h("select", { id: "fm-stage-" + name, class: "fm-select" })
    for (var s = 1; s <= 16; s++) {
      var o = h("option", { value: String(s), text: "Stage " + s })
      if (s === state.stage) o.selected = true
      stageSel.appendChild(o)
    }
    var stats = h("p", { class: "fm-stats", "aria-live": "off" })
    var reset = h("button", { type: "button", class: "fm-btn", text: "Reset progress" })
    var top = h("div", { class: "fm-drill-top" }, [
      h("label", { class: "fm-field", for: "fm-stage-" + name }, [h("span", { text: "Up to stage" })]),
      stageSel,
      stats,
      reset,
    ])
    top.firstChild.appendChild(stageSel)
    var card = h("div", { class: "fm-drill-card" })
    wrap.appendChild(top)
    wrap.appendChild(card)
    root.appendChild(wrap)

    function paintStats() {
      stats.textContent = "Right " + counts.right + "  |  Almost " + counts.almost + "  |  Wrong " + counts.wrong
    }
    paintStats()
    function persist() {
      save(name, { stage: state.stage, boxes: state.boxes })
    }

    function pool() {
      return items.filter(function (it) { return (it.stage || 1) <= state.stage })
    }

    function pickItem() {
      if (cfg.gen) {
        if (retry.length && retry[0].due <= asked) return retry.shift().item
        return cfg.gen(state.stage)
      }
      var p = pool()
      if (!p.length) return null
      if (retry.length && retry[0].due <= asked) {
        var r = retry.shift().item
        if (p.indexOf(r) >= 0) return r
      }
      var ids = p.map(cfg.itemId)
      var id = leitnerPick(ids, state.boxes, Math.random, lastId)
      lastId = id
      return byId[id]
    }

    function clearTimers() {
      timers.forEach(clearTimeout)
      timers = []
    }
    onCleanup(function () {
      clearTimers()
      keyFn = null
      if (window.FMSpeak) window.FMSpeak.stop()
    })

    function finish(result, item, revealText, feedbackEl, nextBtn) {
      if (answered) return
      answered = true
      counts[result]++
      asked++
      if (!cfg.gen) {
        leitnerUpdate(state.boxes, cfg.itemId(item), result)
        persist()
      }
      if (result !== "right") retry.push({ item: item, due: asked + (Math.max(pool().length, 4) > 4 ? 3 : 1) })
      paintStats()
      feedbackEl.className = "fm-feedback fm-" + result
      var msg
      if (result === "right") msg = "Right."
      else if (result === "almost") msg = "Almost, check the accent. Correct: " + revealText
      else msg = "Not quite. Answer: " + revealText
      feedbackEl.textContent = msg
      var extra = cfg.extra ? cfg.extra(item) : ""
      if (extra) feedbackEl.appendChild(h("span", { class: "fm-feedback-extra", text: " " + extra }))
      nextBtn.hidden = false
      nextBtn.focus()
    }

    function next() {
      clearTimers()
      keyFn = null
      answered = false
      card.textContent = ""
      var item = pickItem()
      if (!item) {
        card.appendChild(h("p", { class: "fm-note", text: "There is nothing to practise up to this stage yet. Pick a later stage." }))
        return
      }
      var feedback = h("div", { class: "fm-feedback", role: "status", "aria-live": "polite" })
      var nextBtn = h("button", { type: "button", class: "fm-btn fm-next", text: "Next", hidden: true })
      nextBtn.addEventListener("click", next)
      var done = function (result, revealText) { finish(result, item, revealText, feedback, nextBtn) }

      if (cfg.mode === "custom") {
        card.appendChild(cfg.render(item, { answer: done }))
      } else if (cfg.mode === "choice") {
        var ch = cfg.choices(item, pool(), items)
        card.appendChild(cfg.prompt(item))
        var btns = h("div", { class: "fm-choices" })
        var buttons = []
        ch.labels.forEach(function (label, i) {
          var b = h("button", { type: "button", class: "fm-btn fm-choice" })
          b.appendChild(h("span", { class: "fm-choice-key", text: String(i + 1) }))
          b.appendChild(h("span", { class: "fm-choice-label", text: label }))
          b.addEventListener("click", function () {
            if (answered) return
            buttons.forEach(function (x, k) {
              x.disabled = true
              if (k === ch.correct) x.classList.add("fm-correct")
            })
            if (i !== ch.correct) b.classList.add("fm-wrong")
            done(i === ch.correct ? "right" : "wrong", cfg.reveal(item))
          })
          buttons.push(b)
          btns.appendChild(b)
        })
        card.appendChild(btns)
        keyFn = function (e) {
          var k = Number(e.key)
          if (!answered && k >= 1 && k <= buttons.length) {
            e.preventDefault()
            buttons[k - 1].click()
          }
        }
      } else {
        card.appendChild(cfg.prompt(item))
        var controls = cfg.controls ? cfg.controls(item) : []
        if (controls.length) card.appendChild(h("div", { class: "fm-tool-row" }, controls))
        var input = h("input", {
          type: "text",
          class: "fm-input",
          autocomplete: "off",
          autocapitalize: "none",
          autocorrect: "off",
          spellcheck: "false",
          lang: "fr",
          "aria-label": "Your answer",
        })
        var check = h("button", { type: "button", class: "fm-btn fm-check", text: "Check" })
        function submit() {
          if (answered || !input.value.trim()) return
          input.readOnly = true
          var res = cfg.grade(item, input.value)
          done(res, cfg.reveal(item))
        }
        input.addEventListener("keydown", function (e) {
          if (e.key === "Enter") {
            e.preventDefault()
            submit()
          }
        })
        check.addEventListener("click", submit)
        card.appendChild(h("div", { class: "fm-answer-row" }, [input, check]))
        card.appendChild(accentRow(input))
        timers.push(setTimeout(function () {
          if (document.body.contains(input) && !answered) input.focus()
          if (cfg.autoplay) cfg.autoplay(item)
        }, 50))
      }
      card.appendChild(feedback)
      card.appendChild(nextBtn)
    }

    onDocKey(function (e) {
      if (keyFn) keyFn(e)
    })

    stageSel.addEventListener("change", function () {
      state.stage = Number(stageSel.value)
      persist()
      retry = []
      next()
    })
    reset.addEventListener("click", function () {
      state.boxes = {}
      counts = { right: 0, almost: 0, wrong: 0 }
      asked = 0
      retry = []
      persist()
      paintStats()
      next()
    })

    if (cfg.gen) {
      next()
      return
    }
    card.appendChild(h("p", { class: "fm-note", text: "Loading..." }))
    fetch(baseUrl() + "assets/drills/" + cfg.file + ".json")
      .then(function (r) {
        if (!r.ok) throw new Error("status " + r.status)
        return r.json()
      })
      .then(function (d) {
        items = (d && d.items) || []
        items.forEach(function (it) { byId[cfg.itemId(it)] = it })
        if (document.body.contains(root)) next()
      })
      .catch(function () {
        card.textContent = ""
        card.appendChild(h("p", { class: "fm-note", text: "The exercises could not be loaded. Check your connection and reload the page." }))
      })
  }

  // ---------- the tools ----------

  function bigPrompt(lead, big, sub) {
    var box = h("div", { class: "fm-prompt" })
    if (lead) box.appendChild(h("p", { class: "fm-prompt-lead", text: lead }))
    if (big) box.appendChild(h("p", { class: "fm-prompt-big", lang: "fr", text: big }))
    if (sub) box.appendChild(h("p", { class: "fm-prompt-sub", text: sub }))
    return box
  }

  function elideJe(person, answer) {
    if (person === "je" && /^[aeiouhéèêàâîôû]/i.test(answer)) return "j'"
    return person + " "
  }

  var TOOLS = {
    conjugation: function (root) {
      runTool(root, "conjugation", {
        file: "conjugation",
        mode: "type",
        itemId: function (it) { return it.verb + "|" + it.tense + "|" + it.person },
        prompt: function (it) {
          var pre = elideJe(it.person, it.answer)
          return bigPrompt("Type the missing verb form.", pre + "___", it.verb + ", " + it.tense + (it.en ? " (" + it.en + ")" : ""))
        },
        grade: function (it, v) { return grade(v, [it.answer]) },
        reveal: function (it) { return elideJe(it.person, it.answer) + it.answer },
      })
    },

    "le-or-la": function (root) {
      runTool(root, "le-or-la", {
        file: "gender",
        mode: "choice",
        itemId: function (it) { return it.noun },
        prompt: function (it) {
          var word = it.elided ? "l'" + it.noun : it.noun
          return bigPrompt("Masculine (le) or feminine (la)?", word, it.en || "")
        },
        choices: function (it) { return { labels: ["le", "la"], correct: it.answer === "le" ? 0 : 1 } },
        reveal: function (it) {
          if (it.elided) return "l'" + it.noun + " (" + (it.answer === "le" ? "masculine" : "feminine") + ")"
          return it.answer + " " + it.noun
        },
      })
    },

    fill: function (root) {
      runTool(root, "fill", {
        file: "fill",
        mode: "type",
        itemId: function (it) { return it.q },
        prompt: function (it) {
          return bigPrompt("Fill in the blank.", it.q, it.hint ? "Verb or hint: " + it.hint : "")
        },
        grade: function (it, v) { return grade(v, it.a) },
        reveal: function (it) { return it.q.replace("___", it.a[0]) },
        extra: function (it) { return it.en || "" },
      })
    },

    dictation: function (root) {
      runTool(root, "dictation", {
        file: "dictation",
        mode: "type",
        itemId: function (it) { return it.fr },
        prompt: function () { return bigPrompt("Listen and type what you hear.", "", "Punctuation does not matter. Accents do.") },
        controls: function (it) {
          var play = h("button", { type: "button", class: "fm-btn", text: "Play" })
          play.addEventListener("click", function () { say(it.fr) })
          var slow = h("button", { type: "button", class: "fm-btn", text: "Play slowly" })
          slow.addEventListener("click", function () { say(it.fr, { rate: 0.75 }) })
          return [play, slow]
        },
        autoplay: function (it) { say(it.fr) },
        grade: function (it, v) { return grade(v, [it.fr], { loose: true }) },
        reveal: function (it) { return it.fr },
        extra: function (it) { return it.en || "" },
      })
    },

    numbers: function (root) {
      runTool(root, "numbers", {
        gen: function (stage) { return genNumber(stage) },
        mode: "type",
        prompt: function (it) { return bigPrompt("Listen and type the digits.", "", it.hint) },
        controls: function (it) {
          var play = h("button", { type: "button", class: "fm-btn", text: "Play" })
          play.addEventListener("click", function () { say(it.spoken) })
          var slow = h("button", { type: "button", class: "fm-btn", text: "Play slowly" })
          slow.addEventListener("click", function () { say(it.spoken, { rate: 0.75 }) })
          return [play, slow]
        },
        autoplay: function (it) { say(it.spoken) },
        grade: function (it, v) { return matchNumber(it, v) ? "right" : "wrong" },
        reveal: function (it) { return it.display },
        extra: function (it) { return "(" + it.spoken + ")" },
      })
    },

    "quebec-words": function (root) {
      runTool(root, "quebec-words", {
        file: "quebec-words",
        mode: "choice",
        itemId: function (it) { return it.qc },
        prompt: function (it) {
          return bigPrompt("What is the standard French for this Quebec word?", it.qc, it.en ? "(" + it.en + ")" : "")
        },
        choices: function (it, pool, all) {
          var src = all.length >= 4 ? all : pool
          var others = shuffle(src.filter(function (x) { return x.std !== it.std }).map(function (x) { return x.std }))
          var seen = {}
          var picks = []
          others.forEach(function (s) {
            if (!seen[s] && picks.length < 3) {
              seen[s] = true
              picks.push(s)
            }
          })
          var labels = shuffle([it.std].concat(picks))
          return { labels: labels, correct: labels.indexOf(it.std) }
        },
        reveal: function (it) { return it.qc + " = " + it.std },
        extra: function (it) { return it.note ? "(" + it.note + ")" : "" },
      })
    },
  }

  var kit = { h: h, store: store, save: save, runTool: runTool, baseUrl: baseUrl, accentRow: accentRow }
  window.FMDrills = api
  window.FMTools = window.FMTools || {}

  function init() {
    cleanups.forEach(function (fn) { try { fn() } catch (e) { /* ignore */ } })
    cleanups = []
    document.querySelectorAll(".fm-tool[data-tool]").forEach(function (el) {
      var name = el.getAttribute("data-tool")
      var build = window.FMTools[name] || TOOLS[name]
      if (el.dataset.built) return
      el.dataset.built = "1"
      if (!build) {
        el.textContent = "This practice tool is not available."
        return
      }
      try {
        build(el, kit)
      } catch (e) {
        el.textContent = "This practice tool could not start in this browser."
      }
    })
  }

  var d$ = window.document$
  if (d$ && typeof d$.subscribe === "function") d$.subscribe(init)
  else if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init)
  else init()
})()
