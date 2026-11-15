/* Line strip: the stations of the current stage, drawn under the H1.
   Lesson pages mark "You are here". Stage index pages show no marker.
   Data comes from assets/lines.json. */
(function () {
  var PROGRESS_KEY = "frenchftgu-progress-v1";
  var cache = null;

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

  function basePath() {
    if (FM_SITE_ROOT) return new URL(FM_SITE_ROOT).pathname;

    try {
      var el = document.getElementById("__config");
      if (el) {
        var cfg = JSON.parse(el.textContent);
        if (cfg && typeof cfg.base === "string") {
          var url = new URL(cfg.base.replace(/\/?$/, "/"), location.href);
          return url.pathname;
        }
      }
    } catch (e) {}
    var key = "/FrenchFromTheGroundUp/";
    var i = location.pathname.indexOf(key);
    if (i >= 0) return location.pathname.slice(0, i + key.length);
    return "/";
  }

  function loadData(base) {
    if (!cache) {
      cache = fetch(base + "assets/lines.json")
        .then(function (r) { return r.ok ? r.json() : null; })
        .catch(function () { return null; });
    }
    return cache;
  }

  function doneMap() {
    try {
      return JSON.parse(localStorage.getItem(PROGRESS_KEY) || "{}") || {};
    } catch (e) {
      return {};
    }
  }

  function el(tag, cls, text) {
    var n = document.createElement(tag);
    if (cls) n.className = cls;
    if (text != null) n.textContent = text;
    return n;
  }

  function pagePath(base) {
    var p = location.pathname;
    if (p.indexOf(base) === 0) p = p.slice(base.length);
    p = p.replace(/index\.html$/, "").replace(/^\/+/, "");
    if (p && !/\/$/.test(p)) p += "/";
    return p;
  }

  function build(stage, base, current) {
    var done = doneMap();
    var nav = el("nav", "fm-strip");
    nav.setAttribute("data-level", stage.level);
    nav.setAttribute("aria-label", "Stage " + stage.num + " line");
    var title = el("p", "fm-strip-title");
    title.appendChild(el("span", "fm-badge", stage.level.toUpperCase()));
    title.appendChild(document.createTextNode("Stage " + stage.num + " · " + stage.title));
    nav.appendChild(title);
    var ol = el("ol", "fm-stations");
    stage.lessons.forEach(function (l) {
      var li = document.createElement("li");
      var isHere = current && l.path === current;
      var node;
      if (l.published) {
        node = el("a", "fm-st");
        node.setAttribute("href", base + l.path);
      } else {
        node = el("span", "fm-st fm-planned");
      }
      node.setAttribute("title", l.title);
      if (done[l.path]) node.className += " fm-done";
      if (isHere) {
        li.className = "fm-here";
        node.setAttribute("aria-current", "step");
      }
      node.appendChild(el("span", "fm-dot"));
      node.appendChild(el("span", "fm-st-num", String(l.num)));
      if (isHere) node.appendChild(el("span", "fm-here-tag", "You are here"));
      li.appendChild(node);
      ol.appendChild(li);
    });
    nav.appendChild(ol);
    return nav;
  }

  function render() {
    var old = document.querySelectorAll(".fm-strip");
    for (var i = 0; i < old.length; i++) old[i].remove();
    var h1 = document.querySelector(".md-content__inner h1");
    if (!h1) return;
    var base = basePath();
    var path = pagePath(base);
    var parts = path.split("/").filter(Boolean);
    if (!parts.length || !/^\d\d-/.test(parts[0]) || parts.length > 2) return;
    loadData(base).then(function (data) {
      if (!data || !data.stages) return;
      var stage = null;
      for (var s = 0; s < data.stages.length; s++) {
        if (data.stages[s].folder === parts[0]) stage = data.stages[s];
      }
      if (!stage || !stage.lessons.length) return;
      var h = document.querySelector(".md-content__inner h1");
      if (!h || document.querySelector(".fm-strip")) return;
      var current = parts.length === 2 ? path : null;
      h.parentNode.insertBefore(build(stage, base, current), h.nextSibling);
    });
  }

  if (window.document$ && window.document$.subscribe) {
    window.document$.subscribe(render);
  } else {
    document.addEventListener("DOMContentLoaded", render);
  }
})();
