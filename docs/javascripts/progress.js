// Make the checkboxes on the progress page clickable and remember them in
// this browser (localStorage). Each device keeps its own list. On any page
// with a line map (the home page), finished stations are filled in.
const FM_PROGRESS_KEY = "frenchftgu-progress-v1"

function fmLoadProgress() {
  try {
    return JSON.parse(localStorage.getItem(FM_PROGRESS_KEY)) || {}
  } catch (e) {
    return {}
  }
}

function fmSaveProgress(state) {
  try {
    localStorage.setItem(FM_PROGRESS_KEY, JSON.stringify(state))
  } catch (e) {
    // Storage blocked (private mode): ticks last until the page closes.
  }
}

// The site's base path, such as "/FrenchFromTheGroundUp/".
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

function fmBasePath() {
  if (FM_SITE_ROOT) return new URL(FM_SITE_ROOT).pathname

  try {
    const el = document.getElementById("__config")
    if (el) {
      const cfg = JSON.parse(el.textContent)
      if (cfg && typeof cfg.base === "string") {
        return new URL(cfg.base.replace(/\/?$/, "/"), location.href).pathname
      }
    }
  } catch (e) {
    // Fall through to the path-based guess.
  }
  const key = "/FrenchFromTheGroundUp/"
  const i = location.pathname.indexOf(key)
  return i >= 0 ? location.pathname.slice(0, i + key.length) : "/"
}

// A lesson's key: its URL path without the base, such as "01-first-sounds-and-greetings/01-french-sound-map/".
function fmLessonKey(pathname) {
  const base = fmBasePath()
  let key = pathname.startsWith(base) ? pathname.slice(base.length) : pathname.replace(/^\//, "")
  if (key && !key.endsWith("/")) key += "/"
  return key
}

document$.subscribe(() => {
  const state = fmLoadProgress()

  // Stations on a line map.
  document.querySelectorAll(".fm-st[data-lesson]").forEach((st) => {
    const key = st.getAttribute("data-lesson")
    st.classList.toggle("fm-done", state[key] === true)
  })

  const article = document.querySelector("article.md-content__inner")
  if (!article || !location.pathname.replace(/\/$/, "").endsWith("/progress")) return

  const items = article.querySelectorAll("li.task-list-item")
  let total = 0

  items.forEach((li) => {
    const box = li.querySelector("input[type=checkbox]")
    const link = li.querySelector("a")
    if (!box || !link) return
    const key = fmLessonKey(new URL(link.href, location.href).pathname)
    total += 1
    box.disabled = false
    box.classList.add("fm-progress-box")
    if (key in state) box.checked = state[key]
    box.addEventListener("change", () => {
      state[key] = box.checked
      fmSaveProgress(state)
      updateCount()
    })
  })

  const count = document.createElement("p")
  count.className = "fm-progress-count"
  const h1 = article.querySelector("h1")
  if (h1) h1.after(count)

  function updateCount() {
    const checked = article.querySelectorAll("input.fm-progress-box:checked").length
    count.textContent = `Finished in this browser: ${checked} of ${total} written lessons.`
  }
  updateCount()
})
