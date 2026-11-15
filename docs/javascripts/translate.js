// English toggle for pages that have .fr and .en blocks (stages 11 to 16).
// Adds body class fm-show-en; the CSS in tools.css does the hiding.
(function () {
  "use strict"
  if (typeof window === "undefined" || typeof document === "undefined") return

  var KEY = "frenchftgu-lang-v1"

  function load() {
    try {
      return localStorage.getItem(KEY) === "en" ? "en" : "fr"
    } catch (e) {
      return "fr"
    }
  }
  function save(v) {
    try {
      localStorage.setItem(KEY, v)
    } catch (e) { /* storage blocked */ }
  }

  function init() {
    document.querySelectorAll(".fm-lang").forEach(function (el) { el.remove() })
    var ts = document.querySelector(".md-content .md-typeset") || document.querySelector(".md-typeset")
    var hasPairs = ts && ts.querySelector(".fr:not(pre)") && ts.querySelector(".en")
    if (!hasPairs) {
      document.body.classList.remove("fm-show-en")
      return
    }
    var lang = load()
    var btn = document.createElement("button")
    btn.type = "button"
    btn.className = "fm-btn fm-lang-btn"
    var bar = document.createElement("div")
    bar.className = "fm-lang"
    bar.appendChild(btn)

    function paint() {
      var en = lang === "en"
      document.body.classList.toggle("fm-show-en", en)
      btn.textContent = en ? "Français" : "English"
      btn.setAttribute("aria-pressed", String(en))
      btn.setAttribute("aria-label", en ? "Show the French text" : "Show the English text")
    }
    btn.addEventListener("click", function () {
      lang = lang === "en" ? "fr" : "en"
      save(lang)
      paint()
    })
    paint()

    var h1 = ts.querySelector("h1")
    if (h1 && h1.parentNode) h1.parentNode.insertBefore(bar, h1.nextSibling)
    else ts.insertBefore(bar, ts.firstChild)
  }

  var d$ = window.document$
  if (d$ && typeof d$.subscribe === "function") d$.subscribe(init)
  else if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init)
  else init()
})()
