// Parses and runs scenarios and probes (grammar: scenarios/README.md).
// The runner holds every expectation. An adapter fires intents, advances the
// clock and observes; it decides nothing.

/** Split `a "b c" d,e` into tokens; quoted tokens keep their spaces. */
export function tokens(text) {
  const out = [];
  const re = /"((?:[^"\\]|\\.)*)"|([^\s"]+)/g;
  let m;
  while ((m = re.exec(text))) out.push(m[1] !== undefined ? m[1] : m[2]);
  return out;
}

const list = (text) => text.split(",").map((x) => x.trim().replace(/^"|"$/g, "")).filter(Boolean);

function addressParts(rest) {
  const parts = { place: "board", text: "", labels: [], assignees: [] };
  const m = /^card (\S+)$/.exec(rest);
  if (m) return { place: "card", id: m[1] };
  let s = rest.replace(/^board\s*/, "");
  let t;
  if ((t = /^text "([^"]*)"\s*/.exec(s))) {
    parts.text = t[1];
    s = s.slice(t[0].length);
  }
  if ((t = /^labels (\S+)\s*/.exec(s))) {
    parts.labels = list(t[1]);
    s = s.slice(t[0].length);
  }
  if ((t = /^assignees (.+)$/.exec(s))) {
    parts.assignees = list(t[1]);
    s = "";
  }
  if (s.trim()) throw new Error(`cannot read the address "${rest}"`);
  return parts;
}

/** Turn one step sentence into a step object. Throws if the grammar does not allow it. */
export function parseStep(text) {
  const s = text.replace(/\.$/, "");
  let m;
  if ((m = /^Given profile (\S+)$/.exec(s))) return { kind: "profile", name: m[1] };
  if ((m = /^Given start at address "(.*)"$/.exec(s))) return { kind: "start", at: { raw: m[1] } };
  if ((m = /^Given start at (.+)$/.exec(s))) return { kind: "start", at: addressParts(m[1]) };
  if ((m = /^Given focus on card (\S+)$/.exec(s))) {
    return { kind: "fire", intent: "focus-card", args: [m[1]], via: null };
  }
  if ((m = /^After (\d+) ms$/.exec(s))) return { kind: "advance", ms: Number(m[1]) };
  if ((m = /^Remember history depth as (\w+)$/.exec(s))) return { kind: "remember", name: m[1] };
  if ((m = /^When ([a-z-]+)(.*?)( via (pointer|keys))?$/.exec(s))) {
    return { kind: "fire", intent: m[1], args: tokens(m[2]), via: m[4] ?? null };
  }
  if (!s.startsWith("Then ")) throw new Error(`not a step: ${text}`);
  const t = s.slice(5);
  const check = (c) => ({ kind: "check", ...c });
  if ((m = /^place title "(.*)"$/.exec(t))) return check({ what: "title", text: m[1] });
  if ((m = /^address is "(.*)"$/.exec(t))) return check({ what: "address-raw", text: m[1] });
  if ((m = /^address (.+)$/.exec(t))) return check({ what: "address", parts: addressParts(m[1]) });
  if ((m = /^history depth is (\w+)(?: plus (\d+))?$/.exec(t))) {
    return check({ what: "depth", name: m[1], plus: Number(m[2] ?? 0) });
  }
  if (t === "focus none") return check({ what: "focus", role: null });
  if (t === "focus place title") return check({ what: "focus", role: "place title" });
  if ((m = /^focus card (\S+)$/.exec(t))) return check({ what: "focus", role: "card", name: m[1] });
  if ((m = /^focus ([a-z -]+) "(.*)"$/.exec(t))) return check({ what: "focus", role: m[1], name: m[2] });
  if ((m = /^column "(.*)" (cards|starts) (.+)$/.exec(t))) {
    return check({ what: "column", name: m[1], exact: m[2] === "cards", ids: m[3] === "none" ? [] : list(m[3]) });
  }
  if ((m = /^text "(.*)" is shown$/.exec(t))) return check({ what: "text", text: m[1], shown: true });
  if ((m = /^no text "(.*)"$/.exec(t))) return check({ what: "text", text: m[1], shown: false });
  if (t === "no notice") return check({ what: "notice", text: null });
  if ((m = /^notice "(.*)" with (?:"(.*)"|no action)$/.exec(t))) {
    return check({ what: "notice", text: m[1], action: m[2] ?? null });
  }
  if ((m = /^card (\S+) has mark "(.*)"$/.exec(t))) return check({ what: "card-mark", id: m[1], mark: m[2] });
  if ((m = /^card (\S+) has no mark$/.exec(t))) return check({ what: "card-mark", id: m[1], mark: null });
  if ((m = /^card (\S+) is (not )?selected$/.exec(t))) {
    return check({ what: "card-selected", id: m[1], selected: !m[2] });
  }
  if ((m = /^field "(.*)" has text "(.*)"$/.exec(t))) return check({ what: "field-text", name: m[1], text: m[2] });
  if ((m = /^scroll is (not )?top$/.exec(t))) return check({ what: "scroll-top", top: !m[1] });
  if ((m = /^card (\S+) is in view$/.exec(t))) return check({ what: "in-view", id: m[1] });
  if ((m = /^requests (\w+) (\d+)$/.exec(t))) return check({ what: "requests", op: m[1], count: Number(m[2]) });
  if ((m = /^announcement "(.*)"$/.exec(t))) return check({ what: "announcement", text: m[1] });
  if (
    (m = /^([a-z -]+?) "(.*?)"(?: in "(.*)")? is (on|off|mixed|chosen|not chosen|disabled|enabled|shown|absent)$/.exec(
      t,
    ))
  ) {
    return check({ what: "part", role: m[1], name: m[2], group: m[3] ?? null, state: m[4] });
  }
  throw new Error(`not a step: ${text}`);
}

const same = (a, b) => JSON.stringify(a) === JSON.stringify(b);
const roleIs = (have, want) =>
  have === want || (want === "link" && have === "up-link") || (want === "up-link" && have === "link");

/** Compare one check with an observation. Returns "" or what was seen in its place. */
export function judge(c, o, memory, adapter) {
  const findPart = () =>
    o.parts.filter((p) => roleIs(p.role, c.role) && p.name === c.name && (c.group == null || p.group === c.group));
  switch (c.what) {
    case "title":
      return o.title === c.text ? "" : `place title "${o.title}"`;
    case "address-raw":
      return o.address === c.text ? "" : `address "${o.address}"`;
    case "address": {
      const want = adapter.addressOf(c.parts);
      return o.address === want ? "" : `address "${o.address}", not "${want}"`;
    }
    case "depth": {
      const want = memory[c.name] + c.plus;
      return o.depth === want ? "" : `history depth ${o.depth}, not ${want}`;
    }
    case "focus": {
      if (c.role == null) return o.focus == null ? "" : `focus ${o.focus.role} "${o.focus.name}"`;
      if (!o.focus) return "focus none";
      const ok = roleIs(o.focus.role, c.role) && (c.name == null || o.focus.name === c.name);
      return ok ? "" : `focus ${o.focus.role} "${o.focus.name}"`;
    }
    case "column": {
      const col = o.columns.find((x) => x.name === c.name);
      if (!col) return `no column "${c.name}"`;
      const have = c.exact ? col.cards : col.cards.slice(0, c.ids.length);
      return same(have, c.ids) ? "" : `column "${c.name}" has ${col.cards.join(", ") || "no cards"}`;
    }
    case "text":
      return o.texts.includes(c.text) === c.shown ? "" : c.shown ? `no text "${c.text}"` : `text "${c.text}" is shown`;
    case "notice":
      if (c.text == null) return o.notice ? `notice "${o.notice.text}"` : "";
      if (!o.notice) return "no notice";
      return o.notice.text === c.text && o.notice.action === c.action
        ? ""
        : `notice "${o.notice.text}" with ${o.notice.action ? `"${o.notice.action}"` : "no action"}`;
    case "card-mark": {
      const card = o.cards.find((x) => x.id === c.id);
      if (!card) return `no card ${c.id}`;
      if (c.mark == null) return card.marks.length ? `card ${c.id} has mark "${card.marks.join('", "')}"` : "";
      return card.marks.includes(c.mark)
        ? ""
        : `card ${c.id} has ${card.marks.length ? `mark "${card.marks.join('", "')}"` : "no mark"}`;
    }
    case "card-selected": {
      const card = o.cards.find((x) => x.id === c.id);
      if (!card) return `no card ${c.id}`;
      return card.selected === c.selected ? "" : `card ${c.id} is ${card.selected ? "" : "not "}selected`;
    }
    case "field-text": {
      const f = o.parts.find((p) => p.role === "field" && p.name === c.name);
      if (!f) return `no field "${c.name}"`;
      return f.text === c.text ? "" : `field "${c.name}" has text "${f.text}"`;
    }
    case "scroll-top":
      return o.scrollTop === c.top ? "" : `scroll is ${o.scrollTop ? "" : "not "}top`;
    case "in-view": {
      const card = o.cards.find((x) => x.id === c.id);
      return card?.inView ? "" : card ? `card ${c.id} is not in view` : `no card ${c.id}`;
    }
    case "requests": {
      const n = o.requests.filter((r) => r.op === c.op).length;
      return n === c.count ? "" : `requests ${c.op} ${n}`;
    }
    case "announcement":
      return o.announcements.includes(c.text) ? "" : `announcements: ${JSON.stringify(o.announcements)}`;
    case "part": {
      const found = findPart();
      if (c.state === "absent") return found.length ? `${c.role} "${c.name}" is shown` : "";
      if (!found.length) return `no ${c.role} "${c.name}"`;
      const p = found[0];
      const ok = {
        shown: true,
        on: p.state === "on",
        off: p.state === "off",
        mixed: p.state === "mixed",
        chosen: p.state === "chosen",
        "not chosen": p.state === "not chosen",
        disabled: p.disabled === true,
        enabled: p.disabled !== true,
      }[c.state];
      return ok ? "" : `${c.role} "${c.name}" is ${p.state ?? ""}${p.disabled ? " disabled" : ""}`.trim();
    }
    default:
      return `unknown check ${c.what}`;
  }
}

/**
 * Run one scenario on an adapter.
 * @returns {{id: string, outcome: "passed"|"failed"|"inapplicable", failures: object[], observed: object[]}}
 */
export async function runScenario(scn, adapter, { capabilities = [] } = {}) {
  const result = { id: scn.id, verifies: scn.verifies, outcome: "passed", failures: [], observed: [] };
  const need = scn.marks.filter((m) => m !== adapter.modality && !capabilities.includes(m));
  if (need.length) return { ...result, outcome: "inapplicable", reason: `needs [${need.join("], [")}]` };
  let steps;
  try {
    steps = scn.steps.map((s) => ({ ...parseStep(s.text), source: s.text, line: s.line }));
  } catch (e) {
    return { ...result, outcome: "failed", failures: [{ step: "(grammar)", saw: e.message }] };
  }
  let profile = "default";
  const memory = {};
  let obs = null;
  let heard = [];
  try {
    for (const step of steps) {
      if (step.kind === "profile") profile = step.name;
      else if (step.kind === "start") {
        await adapter.start({ profile, at: step.at });
        obs = null;
        heard = [];
      } else if (step.kind === "advance") {
        await adapter.advance(step.ms);
        obs = null;
      } else if (step.kind === "fire") {
        await adapter.fire(step.intent, step.args, step.via);
        obs = null;
      } else if (step.kind === "remember") {
        memory[step.name] = (await adapter.observe()).depth;
      } else {
        if (!obs) {
          obs = await adapter.observe();
          heard = heard.concat(obs.announcements);
          // A terminal build reports its own semantics. The adapter checks them against the grid.
          for (const x of obs.integrity ?? []) {
            result.failures.push({ step: `(harness, before) ${step.source}`, saw: x });
          }
        }
        const saw = judge(step, { ...obs, announcements: heard }, memory, adapter);
        result.observed.push({ step: step.source, saw: saw || "as expected" });
        if (saw) result.failures.push({ step: step.source, line: step.line, saw });
      }
    }
  } catch (e) {
    result.failures.push({ step: "(run)", saw: String(e.message).split("\n")[0] });
  }
  if (result.failures.length) result.outcome = "failed";
  return result;
}
