// Speech for the French book: voice choice, the header voice control, the
// rendering of ```fr blocks, click-to-hear italics and window.FMSpeak.
// Works as a plain script. The pure helpers are exported for node tests.
(function () {
  "use strict"

  var VOICE_KEY = "frenchftgu-voice-v1"
  var SPEAKER_RE = /^([\p{L}0-9-]+):\s+(.*)$/u

  // ---------- pure helpers ----------

  // One fr-block line -> { speaker, fr, gloss, qc, x } or null for blank/comment.
  function parseFrLine(raw) {
    var s = String(raw).trim()
    if (!s || s.charAt(0) === "#") return null
    var gloss = ""
    var i = s.indexOf(" | ")
    if (i >= 0) {
      gloss = s.slice(i + 3).trim()
      s = s.slice(0, i).trim()
    }
    var qc = false
    var x = false
    var m
    while ((m = /\s*\{(qc|x)\}\s*$/.exec(s))) {
      if (m[1] === "qc") qc = true
      else x = true
      s = s.slice(0, m.index)
    }
    var speaker = ""
    var sm = SPEAKER_RE.exec(s)
    if (sm) {
      speaker = sm[1]
      s = sm[2]
    }
    s = s.trim()
    if (!s) return null
    return { speaker: speaker, fr: s, gloss: gloss, qc: qc, x: x }
  }

  // Whole block text -> array of groups, each { lines: [...] }.
  function parseFrBlock(text) {
    var groups = []
    var cur = []
    String(text).split(/\r?\n/).forEach(function (raw) {
      var t = raw.trim()
      if (!t) {
        if (cur.length) groups.push({ lines: cur })
        cur = []
        return
      }
      var line = parseFrLine(raw)
      if (line) cur.push(line)
    })
    if (cur.length) groups.push({ lines: cur })
    return groups
  }

  function frLang(v) {
    return String(v.lang || "").toLowerCase().replace("_", "-")
  }
  function isFrench(v) {
    return frLang(v).indexOf("fr") === 0
  }
  function voiceScore(v, variety) {
    var lang = frLang(v)
    var name = v.name || ""
    var natural = /natural|online/i.test(name)
    var score = 0
    if (variety === "qc") {
      if (lang === "fr-ca") {
        score = 50
        if (/sylvie|antoine|jean|thierry/i.test(name)) score += 40
        if (natural) score += 20
      } else {
        score = 10 + (natural ? 2 : 0)
      }
    } else {
      if (lang === "fr-fr") {
        score = 50
        if (natural) score += 20
      } else {
        score = 10 + (natural ? 2 : 0)
      }
    }
    return score
  }
  // Returns [first, second] voices (second may equal first or be null).
  function pickVoices(all, variety, uri) {
    var fr = (all || []).filter(isFrench)
    if (!fr.length) return [null, null]
    var ranked = fr
      .map(function (v, i) { return { v: v, i: i, s: voiceScore(v, variety) } })
      .sort(function (a, b) { return b.s - a.s || a.i - b.i })
      .map(function (o) { return o.v })
    var first = ranked[0]
    if (uri) {
      var chosen = fr.filter(function (v) { return v.voiceURI === uri })[0]
      if (chosen) {
        first = chosen
        ranked = [chosen].concat(ranked.filter(function (v) { return v !== chosen }))
      }
    }
    var region = frLang(first)
    var second =
      ranked.filter(function (v) { return v !== first && frLang(v) === region })[0] ||
      ranked.filter(function (v) { return v !== first })[0] ||
      first
    return [first, second]
  }

  var api = { parseFrLine: parseFrLine, parseFrBlock: parseFrBlock, pickVoices: pickVoices }
  if (typeof module !== "undefined" && module.exports) module.exports = api
  if (typeof window === "undefined" || typeof document === "undefined") return

  // ---------- browser part ----------

  var synth = window.speechSynthesis || null
  var settings = { variety: "qc", rate: 1, voice: "", noteDismissed: false }
  var voiceList = []
  var ready = false
  var readyCbs = []
  var changeCbs = []
  var generation = 0
  var currentUtter = null

  function loadSettings() {
    try {
      var raw = localStorage.getItem(VOICE_KEY)
      if (raw) {
        var o = JSON.parse(raw)
        if (o && (o.variety === "qc" || o.variety === "fr")) settings.variety = o.variety
        if (o && (o.rate === 1 || o.rate === 0.75)) settings.rate = o.rate
        if (o && typeof o.voice === "string") settings.voice = o.voice
        if (o && o.noteDismissed) settings.noteDismissed = true
      }
    } catch (e) { /* storage blocked */ }
  }
  function saveSettings() {
    try {
      localStorage.setItem(VOICE_KEY, JSON.stringify(settings))
    } catch (e) { /* storage blocked */ }
  }
  loadSettings()

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

  var ICONS = {
    play: "M8 5v14l11-7z",
    stop: "M6 6h12v12H6z",
    mic: "M12 14a3 3 0 0 0 3-3V6a3 3 0 0 0-6 0v5a3 3 0 0 0 3 3zm5-3a5 5 0 0 1-10 0H5a7 7 0 0 0 6 6.92V21h2v-3.08A7 7 0 0 0 19 11h-2z",
    voice: "M3 9v6h4l5 5V4L7 9H3zm13.5 3A4.5 4.5 0 0 0 14 8v8a4.5 4.5 0 0 0 2.5-4z",
  }
  function icon(name) {
    var span = document.createElement("span")
    span.className = "fm-icon"
    span.setAttribute("aria-hidden", "true")
    span.innerHTML = '<svg viewBox="0 0 24 24" width="18" height="18" focusable="false"><path d="' + ICONS[name] + '" fill="currentColor"/></svg>'
    return span
  }
  function setIcon(btn, name) {
    var old = btn.querySelector(".fm-icon")
    var next = icon(name)
    if (old) btn.replaceChild(next, old)
    else btn.insertBefore(next, btn.firstChild)
  }

  function frenchVoices() {
    return voiceList.filter(isFrench)
  }
  function chosen() {
    return pickVoices(voiceList, settings.variety, settings.voice)
  }

  function loadVoices() {
    if (!synth) return
    var v = synth.getVoices()
    if (v && v.length) voiceList = v
    if (v && v.length && !ready) fireReady()
    changeCbs.forEach(function (cb) { try { cb() } catch (e) { /* ignore */ } })
  }
  function fireReady() {
    ready = true
    var cbs = readyCbs
    readyCbs = []
    cbs.forEach(function (cb) { try { cb() } catch (e) { /* ignore */ } })
  }
  if (synth) {
    if (synth.addEventListener) synth.addEventListener("voiceschanged", loadVoices)
    else synth.onvoiceschanged = loadVoices
    loadVoices()
    setTimeout(function () {
      loadVoices()
      if (!ready) fireReady()
    }, 1500)
  } else {
    ready = true
  }

  function onReady(cb) {
    if (ready) cb()
    else readyCbs.push(cb)
  }

  function stop() {
    generation++
    if (synth) {
      try { synth.cancel() } catch (e) { /* ignore */ }
    }
  }

  // Resolves true when the text finished, false when it was cut off or failed.
  function speak(text, o) {
    o = o || {}
    return new Promise(function (resolve) {
      if (!synth || !text) return resolve(false)
      var gen = ++generation
      try { synth.cancel() } catch (e) { /* ignore */ }
      setTimeout(function () {
        if (gen !== generation) return resolve(false)
        var u = new SpeechSynthesisUtterance(String(text))
        var pair = chosen()
        var v = o.voice || (o.speaker === 1 ? pair[1] : pair[0])
        if (v) {
          u.voice = v
          u.lang = v.lang
        } else {
          u.lang = settings.variety === "qc" ? "fr-CA" : "fr-FR"
        }
        u.rate = o.rate || settings.rate
        u.onend = function () { resolve(gen === generation) }
        u.onerror = function () { resolve(false) }
        currentUtter = u
        try {
          synth.speak(u)
        } catch (e) {
          resolve(false)
        }
      }, 30)
    })
  }

  window.FMSpeak = {
    speak: speak,
    stop: stop,
    voices: frenchVoices,
    onReady: onReady,
    icon: icon,
    setIcon: setIcon,
    settings: function () { return { variety: settings.variety, rate: settings.rate, voice: settings.voice } },
    parseFrLine: parseFrLine,
    parseFrBlock: parseFrBlock,
    pickVoices: pickVoices,
  }

  // ---------- base path ----------

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

  // ---------- header voice control ----------

  function option(value, label, selected) {
    var o = h("option", { value: value, text: label })
    if (selected) o.selected = true
    return o
  }

  function buildControl() {
    if (document.getElementById("fm-voice")) return
    var wrap = h("div", { id: "fm-voice", class: "fm-voice" })
    var btn = h("button", { type: "button", class: "fm-voice-btn", "aria-expanded": "false", "aria-controls": "fm-voice-panel", "aria-label": "Voice settings" })
    btn.appendChild(icon("voice"))
    btn.appendChild(h("span", { class: "fm-voice-label", text: "Voice" }))
    var panel = h("div", { id: "fm-voice-panel", class: "fm-voice-panel", hidden: true })

    var variety = h("select", { id: "fm-voice-variety" }, [
      option("qc", "Quebec", settings.variety === "qc"),
      option("fr", "France", settings.variety === "fr"),
    ])
    var rate = h("select", { id: "fm-voice-rate" }, [
      option("1", "Normal", settings.rate === 1),
      option("0.75", "Slow", settings.rate === 0.75),
    ])
    var voice = h("select", { id: "fm-voice-name" })
    function fillVoices() {
      voice.textContent = ""
      voice.appendChild(option("", "Automatic", !settings.voice))
      frenchVoices().forEach(function (v) {
        voice.appendChild(option(v.voiceURI, v.name + " (" + v.lang + ")", v.voiceURI === settings.voice))
      })
    }
    fillVoices()
    changeCbs.push(fillVoices)

    variety.addEventListener("change", function () {
      settings.variety = variety.value
      settings.voice = ""
      saveSettings()
      fillVoices()
    })
    rate.addEventListener("change", function () {
      settings.rate = Number(rate.value) === 0.75 ? 0.75 : 1
      saveSettings()
    })
    voice.addEventListener("change", function () {
      settings.voice = voice.value
      saveSettings()
    })
    var test = h("button", { type: "button", class: "fm-btn", text: "Test voice" })
    test.addEventListener("click", function () { speak("Bonjour, ça va bien?") })

    function field(label, control) {
      return h("label", { class: "fm-voice-field" }, [h("span", { text: label }), control])
    }
    panel.appendChild(field("Accent", variety))
    panel.appendChild(field("Speed", rate))
    panel.appendChild(field("Voice", voice))
    panel.appendChild(test)

    function close() {
      panel.hidden = true
      btn.setAttribute("aria-expanded", "false")
    }
    btn.addEventListener("click", function () {
      var open = panel.hidden
      panel.hidden = !open
      btn.setAttribute("aria-expanded", String(open))
    })
    document.addEventListener("click", function (e) {
      if (!wrap.contains(e.target)) close()
    })
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && !panel.hidden) {
        close()
        btn.focus()
      }
    })
    wrap.appendChild(btn)
    wrap.appendChild(panel)

    var header = document.querySelector(".md-header__inner")
    var search = header && (header.querySelector('[data-md-component="search"]') || header.querySelector(".md-search"))
    if (header && search) {
      header.insertBefore(wrap, search)
    } else if (header) {
      header.appendChild(wrap)
    } else {
      wrap.classList.add("fm-voice-fixed")
      document.body.appendChild(wrap)
    }
  }

  // ---------- note when no French voice exists ----------

  function maybeNote() {
    if (settings.noteDismissed || document.querySelector(".fm-novoice")) return
    onReady(function () {
      if (frenchVoices().length) return
      if (settings.noteDismissed || document.querySelector(".fm-novoice")) return
      var target = document.querySelector(".md-content__inner") || document.querySelector("article")
      if (!target || !target.querySelector("pre.fr, .fm-fr, .fm-say, .fm-tool")) return
      var link = h("a", { href: baseUrl() + "00-start-here/set-up-voices-and-audio/", text: "Set up voices and audio" })
      var close = h("button", { type: "button", class: "fm-btn", text: "Dismiss" })
      var note = h("div", { class: "fm-note fm-novoice", role: "note" }, [
        h("span", { text: "No French voice was found on this device, so audio may not play. " }),
        link,
        h("span", { text: " explains how to add one. " }),
        close,
      ])
      close.addEventListener("click", function () {
        settings.noteDismissed = true
        saveSettings()
        note.remove()
      })
      target.insertBefore(note, target.firstChild)
    })
  }

  // ---------- fr blocks ----------

  function renderBlock(pre) {
    var code = pre.querySelector("code") || pre
    var raw = code.textContent
    var groups = parseFrBlock(raw)
    var box = h("div", { class: "fm-fr", "data-raw": raw.replace(/\s+$/, "") })
    var speakers = {}
    var nSpeakers = 0
    var rows = []
    var hasGloss = false

    var bar = h("div", { class: "fm-fr-bar" })
    var playAll = h("button", { type: "button", class: "fm-btn fm-playall", "aria-label": "Play all lines" })
    playAll.appendChild(icon("play"))
    playAll.appendChild(h("span", { text: "Play all" }))
    var tr = h("button", { type: "button", class: "fm-btn fm-trans", "aria-pressed": "false", text: "Show translation" })
    bar.appendChild(playAll)

    groups.forEach(function (g) {
      var gd = h("div", { class: "fm-fr-group" })
      g.lines.forEach(function (ln) {
        var idx = 0
        if (ln.speaker) {
          if (!(ln.speaker in speakers)) speakers[ln.speaker] = nSpeakers++ % 2
          idx = speakers[ln.speaker]
        }
        var row = h("div", { class: "fm-fr-row" + (ln.x ? " fm-fr-x" : ""), "data-fr": ln.fr, "data-speaker": String(idx) })
        if (ln.speaker) row.appendChild(h("span", { class: "fm-fr-who", text: ln.speaker }))
        var text = h("span", { class: "fm-fr-text", lang: "fr" }, [h("span", { class: "fm-fr-line", text: ln.fr })])
        if (ln.qc) text.appendChild(h("span", { class: "fm-fr-tag", text: "casual Quebec" }))
        row.appendChild(text)
        if (!ln.x) {
          var p = h("button", { type: "button", class: "fm-btn fm-play", "aria-label": "Play: " + ln.fr })
          p.appendChild(icon("play"))
          row.appendChild(p)
          row.appendChild(h("span", { class: "fm-mic-slot" }))
          rows.push({ row: row, btn: p, fr: ln.fr, speaker: idx })
        }
        if (ln.gloss) {
          hasGloss = true
          row.appendChild(h("span", { class: "fm-fr-en", text: ln.gloss }))
        }
        gd.appendChild(row)
      })
      box.appendChild(gd)
    })
    if (hasGloss) bar.appendChild(tr)
    box.insertBefore(bar, box.firstChild)

    tr.addEventListener("click", function () {
      var on = tr.getAttribute("aria-pressed") !== "true"
      tr.setAttribute("aria-pressed", String(on))
      tr.textContent = on ? "Hide translation" : "Show translation"
      box.classList.toggle("fm-fr-open", on)
    })

    var playing = false
    function mark(r, on) {
      r.row.classList.toggle("fm-playing", on)
      setIcon(r.btn, on ? "stop" : "play")
    }
    rows.forEach(function (r) {
      r.btn.addEventListener("click", function () {
        if (r.row.classList.contains("fm-playing")) {
          stop()
          return
        }
        mark(r, true)
        speak(r.fr, { speaker: r.speaker }).then(function () { mark(r, false) })
      })
    })
    function setPlayAll(on) {
      playing = on
      setIcon(playAll, on ? "stop" : "play")
      playAll.lastChild.textContent = on ? "Stop" : "Play all"
    }
    playAll.addEventListener("click", function () {
      if (playing) {
        stop()
        return
      }
      setPlayAll(true)
      var chain = Promise.resolve(true)
      rows.forEach(function (r) {
        chain = chain.then(function (ok) {
          if (!ok) return false
          mark(r, true)
          return speak(r.fr, { speaker: r.speaker }).then(function (done) {
            mark(r, false)
            return done
          })
        })
      })
      chain.then(function () { setPlayAll(false) })
    })

    pre.replaceWith(box)
    return box
  }

  // ---------- inline italics and .fr paragraphs ----------

  var EM_SKIP = "nav, code, pre, .fm-no-speak, .md-header, .md-sidebar, .fm-fr, .md-footer, .headerlink"

  function cleanText(el) {
    return el.textContent.replace(/\s+/g, " ").trim()
  }

  var cleanups = []

  function init() {
    cleanups.forEach(function (fn) { try { fn() } catch (e) { /* ignore */ } })
    cleanups = []
    stop()
    buildControl()

    var root = document.querySelector(".md-content") || document
    var created = false
    root.querySelectorAll("pre.fr").forEach(function (pre) {
      try {
        renderBlock(pre)
        created = true
      } catch (e) { /* leave the plain block */ }
    })

    var typeset = document.querySelectorAll(".md-typeset")
    typeset.forEach(function (ts) {
      ts.querySelectorAll("em").forEach(function (em) {
        if (em.closest(EM_SKIP) || em.classList.contains("fm-say")) return
        var t = cleanText(em)
        if (!/\p{L}/u.test(t)) return
        em.classList.add("fm-say")
        em.setAttribute("role", "button")
        em.setAttribute("tabindex", "0")
        em.setAttribute("lang", "fr")
        em.setAttribute("title", "Click to hear")
      })
      ts.querySelectorAll("p.fr").forEach(function (p) {
        if (p.querySelector(".fm-para-play")) return
        var text = cleanText(p)
        var b = h("button", { type: "button", class: "fm-btn fm-play fm-para-play", "aria-label": "Play this paragraph" })
        b.appendChild(icon("play"))
        b.addEventListener("click", function () {
          stop()
          speak(text)
        })
        p.insertBefore(b, p.firstChild)
        p.setAttribute("lang", "fr")
      })
    })

    function trigger(el) {
      var t = cleanText(el)
      el.classList.add("fm-playing")
      speak(t).then(function () { el.classList.remove("fm-playing") })
    }
    function onClick(e) {
      var el = e.target.closest && e.target.closest("em.fm-say")
      if (!el) return
      if (el.closest("a")) return
      trigger(el)
    }
    function onKey(e) {
      if (e.key !== "Enter" && e.key !== " ") return
      var el = e.target.closest && e.target.closest("em.fm-say")
      if (!el || e.target !== el) return
      e.preventDefault()
      trigger(el)
    }
    document.addEventListener("click", onClick)
    document.addEventListener("keydown", onKey)
    cleanups.push(function () {
      document.removeEventListener("click", onClick)
      document.removeEventListener("keydown", onKey)
    })

    if (created) {
      try {
        document.dispatchEvent(new CustomEvent("fm-fr-rendered"))
      } catch (e) { /* old browser */ }
    }
    maybeNote()
  }

  var d$ = window.document$
  if (d$ && typeof d$.subscribe === "function") d$.subscribe(init)
  else if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init)
  else init()
})()
