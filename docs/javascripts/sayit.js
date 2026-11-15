// Say it: speech recognition for fr rows and the "say-it" practice page.
// If the browser has no speech recognition, nothing is added.
// The pure compare function is exported for node tests.
(function () {
  "use strict"

  // ---------- pure helpers ----------

  var ELISIONS = ["l", "j", "d", "m", "t", "s", "n", "c", "qu", "jusqu", "lorsqu", "puisqu"]

  // Lowercase, straight apostrophes, no punctuation, elisions split off.
  function tokenize(s) {
    var t = String(s)
      .normalize("NFC")
      .toLowerCase()
      .replace(/[\u2018\u2019\u02bc`]/g, "'")
      .replace(/[  ]/g, " ")
      .replace(/-/g, " ")
      .replace(/[^\p{L}\p{N}' ]/gu, " ")
    var out = []
    t.split(/\s+/).forEach(function (w) {
      w = w.replace(/^'+|'+$/g, "")
      if (!w) return
      var i = w.indexOf("'")
      while (i > 0 && ELISIONS.indexOf(w.slice(0, i)) >= 0) {
        out.push(w.slice(0, i + 1))
        w = w.slice(i + 1)
        i = w.indexOf("'")
      }
      if (w) out.push(w)
    })
    return out
  }

  // Align target and heard words with a longest common subsequence.
  function compareWords(target, heard) {
    var a = tokenize(target)
    var b = tokenize(heard)
    var n = a.length
    var m = b.length
    var dp = []
    for (var i = 0; i <= n; i++) {
      dp.push(new Array(m + 1).fill(0))
    }
    for (i = n - 1; i >= 0; i--) {
      for (var j = m - 1; j >= 0; j--) {
        dp[i][j] = a[i] === b[j] ? dp[i + 1][j + 1] + 1 : Math.max(dp[i + 1][j], dp[i][j + 1])
      }
    }
    var tokens = a.map(function (w) { return { word: w, ok: false } })
    var usedB = new Array(m).fill(false)
    i = 0
    j = 0
    while (i < n && j < m) {
      if (a[i] === b[j]) {
        tokens[i].ok = true
        usedB[j] = true
        i++
        j++
      } else if (dp[i + 1][j] >= dp[i][j + 1]) {
        i++
      } else {
        j++
      }
    }
    var missing = tokens.filter(function (t) { return !t.ok }).map(function (t) { return t.word })
    var extra = b.filter(function (w, k) { return !usedB[k] })
    var allMatched = missing.length === 0 && extra.length === 0
    var summary
    if (missing.length) summary = "Missed: " + missing.join(", ")
    else if (extra.length) summary = "All words matched. Extra: " + extra.join(", ")
    else summary = "All words matched"
    return { tokens: tokens, missing: missing, extra: extra, allMatched: allMatched, summary: summary }
  }

  var api = { compareWords: compareWords, tokenize: tokenize }
  if (typeof module !== "undefined" && module.exports) module.exports = api
  if (typeof window === "undefined" || typeof document === "undefined") return

  // ---------- browser part ----------

  window.FMSay = api
  window.FMTools = window.FMTools || {}

  var Rec = window.SpeechRecognition || window.webkitSpeechRecognition
  var supported = !!Rec
  api.supported = supported

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

  var current = null // { rec, done() }

  function abortCurrent() {
    if (!current) return
    var c = current
    current = null
    try { c.rec.abort() } catch (e) { /* already stopped */ }
    c.done()
  }

  var ERRORS = {
    "no-speech": "I did not hear anything. Try again, a bit closer to the microphone.",
    "not-allowed": "The browser blocked the microphone. Allow it in the site settings and try again.",
    "service-not-allowed": "The browser blocked speech recognition. Allow the microphone in the site settings.",
    "network": "Speech recognition needs an internet connection here.",
    "audio-capture": "No microphone was found.",
  }

  function showResult(box, target, heardText, cmp) {
    box.textContent = ""
    box.className = "fm-say-result " + (cmp.allMatched ? "fm-say-ok" : "fm-say-miss")
    box.appendChild(h("div", { class: "fm-say-heard", text: "Heard: " + heardText }))
    var words = h("div", { class: "fm-say-words", "aria-hidden": "true" })
    cmp.tokens.forEach(function (t) {
      words.appendChild(h("span", { class: "fm-say-w " + (t.ok ? "fm-w-ok" : "fm-w-miss") + (/'$/.test(t.word) ? " fm-w-elide" : ""), text: t.word }))
    })
    box.appendChild(words)
    box.appendChild(h("div", { class: "fm-say-summary", role: "status", text: cmp.summary }))
  }

  // Start listening for target. Calls onDone(cmp or null) when finished.
  function listen(target, btn, box, onDone) {
    abortCurrent()
    if (window.FMSpeak) window.FMSpeak.stop()
    var lang = "fr-CA"
    var retried = false
    var finished = false

    function end(cmp) {
      if (finished) return
      finished = true
      btn.classList.remove("fm-listening")
      btn.setAttribute("aria-pressed", "false")
      if (current && current.rec === rec) current = null
      if (onDone) onDone(cmp)
    }

    var rec
    function begin() {
      rec = new Rec()
      rec.lang = lang
      rec.interimResults = false
      rec.continuous = false
      rec.maxAlternatives = 3
      var got = false
      var failed = false
      rec.onresult = function (ev) {
        got = true
        var res = ev.results[ev.results.length - 1]
        var best = null
        var bestText = ""
        for (var i = 0; i < res.length; i++) {
          var text = res[i].transcript
          var cmp = compareWords(target, text)
          var score = cmp.missing.length * 2 + cmp.extra.length
          if (!best || score < best.score) {
            best = { cmp: cmp, score: score }
            bestText = text
          }
        }
        showResult(box, target, bestText, best.cmp)
        end(best.cmp)
      }
      rec.onerror = function (ev) {
        var code = ev && ev.error
        if (code === "aborted") return
        if (code === "language-not-supported" && !retried) {
          retried = true
          lang = "fr-FR"
          rec.onend = null
          rec.onresult = null
          begin()
          return
        }
        failed = true
        box.className = "fm-say-result fm-say-error"
        box.textContent = ERRORS[code] || "Something went wrong with the microphone (" + (code || "unknown") + ")."
        end(null)
      }
      rec.onend = function () {
        if (failed || got) return end(null)
        if (!finished) {
          box.className = "fm-say-result fm-say-error"
          box.textContent = ERRORS["no-speech"]
          end(null)
        }
      }
      current = { rec: rec, done: function () {
        if (!finished) {
          finished = true
          btn.classList.remove("fm-listening")
          btn.setAttribute("aria-pressed", "false")
        }
      } }
      box.className = "fm-say-result fm-say-listening"
      box.textContent = "Listening..."
      btn.classList.add("fm-listening")
      btn.setAttribute("aria-pressed", "true")
      try {
        rec.start()
      } catch (e) {
        box.className = "fm-say-result fm-say-error"
        box.textContent = "Could not start the microphone. Try again."
        end(null)
      }
    }
    begin()
  }

  function makeMic(target, resultBox, onDone) {
    var b = h("button", { type: "button", class: "fm-btn fm-mic", "aria-pressed": "false", "aria-label": "Say it: " + target })
    if (window.FMSpeak) b.appendChild(window.FMSpeak.icon("mic"))
    else b.textContent = "Mic"
    b.addEventListener("click", function () {
      if (b.classList.contains("fm-listening")) {
        abortCurrent()
        resultBox.textContent = ""
        resultBox.className = "fm-say-result"
        return
      }
      listen(target, b, resultBox, onDone)
    })
    return b
  }
  api.makeMic = makeMic

  function fillSlots() {
    if (!supported) return
    document.querySelectorAll(".fm-fr-row .fm-mic-slot").forEach(function (slot) {
      if (slot.dataset.ready) return
      slot.dataset.ready = "1"
      var row = slot.closest(".fm-fr-row")
      var target = row.getAttribute("data-fr")
      var box = h("div", { class: "fm-say-result", "aria-live": "polite" })
      row.appendChild(box)
      slot.appendChild(makeMic(target, box))
    })
  }

  // ---------- practice tool ----------

  // kit comes from drills.js: { h, runTool, ... }.
  window.FMTools["say-it"] = function (root, kit) {
    if (!supported) {
      root.appendChild(h("p", { class: "fm-note", text: "This browser cannot listen to you. Try Chrome, Edge or Safari." }))
      return
    }
    kit.runTool(root, "say-it", {
      file: "dictation",
      itemId: function (it) { return it.fr },
      mode: "custom",
      render: function (item, ui) {
        var box = h("div", { class: "fm-say-result", "aria-live": "polite" })
        var play = h("button", { type: "button", class: "fm-btn", text: "Hear it" })
        play.addEventListener("click", function () { window.FMSpeak && window.FMSpeak.speak(item.fr) })
        var slow = h("button", { type: "button", class: "fm-btn", text: "Hear it slowly" })
        slow.addEventListener("click", function () { window.FMSpeak && window.FMSpeak.speak(item.fr, { rate: 0.75 }) })
        var mic = makeMic(item.fr, box, function (cmp) {
          if (!cmp) return
          ui.answer(cmp.allMatched ? "right" : "wrong", item.fr)
        })
        var skip = h("button", { type: "button", class: "fm-btn", text: "Skip" })
        skip.addEventListener("click", function () { ui.answer("wrong", item.fr) })
        return h("div", { class: "fm-say-card" }, [
          h("p", { class: "fm-say-target", lang: "fr", text: item.fr }),
          h("p", { class: "fm-say-en", text: item.en || "" }),
          h("div", { class: "fm-tool-row" }, [play, slow, mic, skip]),
          box,
        ])
      },
    })
  }

  // ---------- page hook ----------

  function init() {
    abortCurrent()
    fillSlots()
  }
  document.addEventListener("fm-fr-rendered", fillSlots)
  var d$ = window.document$
  if (d$ && typeof d$.subscribe === "function") d$.subscribe(init)
  else if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init)
  else init()
})()
