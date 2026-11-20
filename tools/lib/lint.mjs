// The trigger lint and the other mechanical checks of a specification package.
import { identifiers, parseEars } from "./model.mjs";

const STACK_WORDS =
  /\b(click|clicks|tap|keydown|Enter key|Escape|Tab key|Ctrl|Control\+|px|hover|DOM|CSS|HTML|browser|URL|mouse|checkbox)\b|#\//;

/** @returns {{failures: object[], warnings: object[]}} */
export function lint(model) {
  const failures = model.problems.map((p) => ({ rule: "parse", at: `${p.file}:${p.line}`, text: p.problem }));
  const warnings = [];
  const fail = (rule, item, text) => failures.push({ rule, id: item.id, at: `${item.file}:${item.line}`, text });

  const states = new Map(); // "Region.State" -> { region, leaves }
  const placeOf = new Map();
  for (const r of model.regions) {
    const place = /^spec\/places\/(\w+)\.md$/.exec(r.file)?.[1] ?? null;
    placeOf.set(r.name, place);
    for (const s of r.all) {
      states.set(`${r.name}.${s}`, {
        region: r.name,
        leaves: r.leaves.filter((x) => x === s || x.startsWith(`${s}.`)),
      });
    }
  }
  const triggers = new Set([...model.intents.map((i) => i.phrase), ...model.events.map((e) => e.phrase)]);

  const scopeOf = (item, text) => {
    if (!text) return null;
    const names = text.split(/ or |, /).map((x) => x.trim());
    const out = [];
    for (const n of names) {
      const full = states.has(n)
        ? n
        : [...states.keys()].find((k) =>
          k.endsWith(`.${n}`) && names.some((o) => states.has(o) && states.get(o).region === states.get(k).region)
        );
      if (!full) fail("scope", item, `"${n}" is not a state of a States line`);
      else out.push(states.get(full));
    }
    return out;
  };

  // The claims: every rule and table that names a trigger.
  const claims = [];
  for (const r of model.rules) {
    const e = parseEars(r.body);
    r.ears = e;
    if (e.form === "unknown") fail("ears", r, "the sentence has no EARS form");
    const scope = scopeOf(r, e.scope);
    if (e.trigger && !triggers.has(e.trigger)) {
      fail("trigger", r, `"${e.trigger}" is not in the Intents or Events list`);
    }
    if (e.trigger) claims.push({ kind: "rule", item: r, trigger: e.trigger, scope });
  }
  for (const t of model.tables) {
    if (!triggers.has(t.decides)) fail("trigger", t, `"${t.decides}" is not in the Intents or Events list`);
    if (!t.rows.length) fail("table", t, "the table has no rows");
    else if (t.id !== "MEM-T1" && !/^otherwise/.test(t.rows[t.rows.length - 1].when)) {
      warnings.push({ rule: "table", id: t.id, text: 'the last row is not "otherwise"' });
    }
    claims.push({ kind: "table", item: t, trigger: t.decides, scope: scopeOf(t, t.scope) });
  }

  // Two scopes exclude each other if they are disjoint states of one region, or states of two places.
  const exclusive = (a, b) => {
    if (!a?.length || !b?.length) return false;
    const pa = new Set(a.map((s) => placeOf.get(s.region)));
    const pb = new Set(b.map((s) => placeOf.get(s.region)));
    if (![...pa, ...pb].includes(null) && ![...pa].some((p) => pb.has(p))) return true;
    const ra = new Set(a.map((s) => s.region));
    if (ra.size !== 1 || b.some((s) => !ra.has(s.region))) return false;
    const la = new Set(a.flatMap((s) => s.leaves));
    return !b.some((s) => s.leaves.some((x) => la.has(x)));
  };
  const cites = (table, rule) => new RegExp(`\\b${rule.id}\\b`).test(table.text);

  // Lint 1: two claims on one state and trigger need a table or an "overrides" reference.
  for (let i = 0; i < claims.length; i++) {
    for (let j = i + 1; j < claims.length; j++) {
      const a = claims[i];
      const b = claims[j];
      if (a.trigger !== b.trigger || exclusive(a.scope, b.scope)) continue;
      let ok = false;
      if (a.kind === "rule" && b.kind === "rule") ok = a.item.overrides === b.item.id || b.item.overrides === a.item.id;
      else if (a.kind === "table" && b.kind === "table") {
        ok = a.item.owns.length > 0 && b.item.owns.length > 0 && !a.item.owns.some((x) => b.item.owns.includes(x));
      } else {
        const [t, r] = a.kind === "table" ? [a.item, b.item] : [b.item, a.item];
        ok = cites(t, r) || r.overrides === t.id || (t.owns.length > 0 && !r.sets.some((x) => t.owns.includes(x)));
      }
      if (!ok) {
        fail(
          "trigger-conflict",
          a.item,
          `${a.item.id} and ${b.item.id} both claim "${a.trigger}" with no table and no "overrides"`,
        );
      }
    }
  }

  // Lint 3: a rule that sets a region that a table owns.
  for (const t of model.tables) {
    for (const r of model.rules) {
      const hit = r.sets.find((x) => t.owns.includes(x));
      if (hit && !cites(t, r) && r.overrides !== t.id) {
        fail("owned-region", r, `${r.id} sets "${hit}", which ${t.id} owns`);
      }
    }
  }

  // Lint 2: an identifier with no check.
  const ids = identifiers(model);
  const known = new Set(ids.map((x) => x.id));
  const checked = new Set();
  for (const s of model.scenarios) {
    for (const v of s.verifies) {
      if (!known.has(v)) fail("unknown-identifier", s, `${s.id} verifies ${v}, which does not exist`);
      checked.add(v);
      checked.add(v.replace(/\.\d+$/, ""));
    }
    for (const step of s.steps) {
      if (!/^Then /.test(step.text)) continue;
      const unquoted = step.text.replace(/"[^"]*"/g, "");
      const name = [...states.keys()].find((k) => unquoted.includes(k));
      if (name) fail("state-in-scenario", s, `${s.id} names the state ${name} in a Then step`);
    }
    for (const step of s.steps) {
      const m = /^When ([a-z-]+)/.exec(step.text);
      if (m && !model.intents.some((i) => i.id === m[1])) {
        fail("unknown-intent", s, `${s.id} uses "${m[1]}", which is not an intent`);
      }
    }
  }
  for (const x of ids) {
    if (x.kind === "row" || x.kind === "entry") continue;
    if (x.kind === "commitment") {
      const c = model.commitments.find((k) => k.id === x.id);
      if (!/Check: (token|outline|inspection)\.?$/.test(c.body.trim())) {
        fail("no-check", x, `${x.id} has no check method`);
      }
      continue;
    }
    if (checked.has(x.id)) continue;
    if (x.level === "must") fail("no-check", x, `${x.id} is must-level and no scenario verifies it`);
    else warnings.push({ rule: "no-check", id: x.id, text: `${x.id} is should-level and no scenario verifies it` });
  }

  // Each rule has one identifier, and an identifier is used one time.
  const seen = new Set();
  for (const x of ids) {
    if (seen.has(x.id)) fail("duplicate", x, `${x.id} is defined twice`);
    seen.add(x.id);
  }
  for (const r of model.rules) {
    if (r.overrides && !known.has(r.overrides)) {
      fail("overrides", r, `${r.id} overrides ${r.overrides}, which does not exist`);
    }
  }

  // The core names no stack words.
  for (const item of [...model.rules, ...model.statements, ...model.tasks, ...model.commitments]) {
    if (item.file.startsWith("spec/modality/")) continue;
    const m = STACK_WORDS.exec(item.body);
    if (m) fail("stack-word", item, `${item.id} has the stack word "${m[0]}"`);
  }
  for (const t of model.tables) {
    const m = STACK_WORDS.exec(t.text);
    if (m) fail("stack-word", t, `${t.id} has the stack word "${m[0]}"`);
  }
  return { failures, warnings };
}
