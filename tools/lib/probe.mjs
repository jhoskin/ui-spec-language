// Held-out probes in their raw form: evaluation of the checks of a probe on the
// observations of the raw driver.

/** The cards that a column shows, read from the accessibility tree text. */
export function columnCards(screen, column) {
  const lines = screen.split("\n");
  const start = lines.findIndex((l) => l.trim().startsWith(`- region "${column}"`));
  if (start < 0) return null;
  const depth = lines[start].length - lines[start].trimStart().length;
  const out = [];
  for (const l of lines.slice(start + 1)) {
    if (l.trim() && l.length - l.trimStart().length <= depth) break;
    const m = /- group "(SL-\d+) /.exec(l);
    if (m) out.push(m[1]);
  }
  return out;
}

/** Returns the list of checks that do not hold, each with what was seen. */
export function evaluate(probe, result) {
  if (!Array.isArray(result) || result[result.length - 1].error) {
    return [{ check: "(run)", saw: result?.error ?? result[result.length - 1].error }];
  }
  const first = result[0];
  const last = result[result.length - 1];
  const said = result.flatMap((r) => r.announcements ?? []);
  const bad = [];
  for (const c of probe.checks ?? []) {
    let ok = true;
    let saw = "";
    if ("focus" in c) {
      ok = c.focus == null
        ? last.focus == null
        : last.focus?.role === c.focus.role && last.focus?.name === c.focus.name;
      saw = JSON.stringify(last.focus);
    } else if ("address" in c) [ok, saw] = [last.address === c.address, last.address];
    else if ("historyDelta" in c) {
      [ok, saw] = [
        last.historyLength - first.historyLength === c.historyDelta,
        last.historyLength - first.historyLength,
      ];
    } else if ("windowTitle" in c) [ok, saw] = [last.windowTitle === c.windowTitle, last.windowTitle];
    else if ("screenHas" in c) ok = last.screen.includes(c.screenHas);
    else if ("screenLacks" in c) ok = !last.screen.includes(c.screenLacks);
    else if ("requests" in c) {
      const n = last.requests.filter((r) => r.op === c.requests.op).length;
      [ok, saw] = [n === c.requests.count, n];
    } else if ("announced" in c) [ok, saw] = [said.includes(c.announced), JSON.stringify(said)];
    else if ("order" in c) {
      const cards = columnCards(last.screen, c.order.column);
      [ok, saw] = [JSON.stringify(cards) === JSON.stringify(c.order.cards), JSON.stringify(cards)];
    } else [ok, saw] = [false, "unknown check"];
    if (!ok) bad.push({ check: c, saw });
  }
  return bad;
}
