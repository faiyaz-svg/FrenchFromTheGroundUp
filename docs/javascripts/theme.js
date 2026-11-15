// Give every stage page a level and a stage number. Pages under /NN-.../ get
// body[data-stage] = N and body[data-level] = a1 (stages 1-4), a2 (5-8),
// b1 (9-12) or b2 (13-16). Start-here, practice and reference pages get
// neither. The colours are in stylesheets/site.css.
document$.subscribe(() => {
  const parts = location.pathname.split("/")
  let stage = 0
  for (const part of parts) {
    const m = /^(\d{2})-/.exec(part)
    if (m) {
      const n = Number(m[1])
      if (n >= 1 && n <= 16) stage = n
      break
    }
  }
  if (stage) {
    const level = ["a1", "a2", "b1", "b2"][Math.floor((stage - 1) / 4)]
    document.body.setAttribute("data-stage", String(stage))
    document.body.setAttribute("data-level", level)
  } else {
    document.body.removeAttribute("data-stage")
    document.body.removeAttribute("data-level")
  }
})
