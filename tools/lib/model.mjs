// Reads a specification package into a structured model.
// The notation is in spec/conventions.md. Only `text` blocks are read.
import { existsSync, readdirSync, readFileSync, statSync } from "node:fs";
import { join, relative } from "node:path";

const RULE =
  /^([A-Z]{3}-\d+) \[(must|should)\](?: \[(\w+)\])? origin: (\w+)\s+sets: (.*?)(?:\s+overrides ([A-Z]{3}-T?\d+(?:\.\d+)?))?$/;
const TABLE = /^([A-Z]{3}-T\d+) \[(must|should)\] decides: (.*?)(?:\s{2,}scope: (.*?))?\s{2,}owns: (.*)$/;
// The worked example of the report writes rules and tables with no "origin:", "sets:",
// "decides:" or "owns:". These loose forms are read too, so that the parser serves both.
const LOOSE_RULE = /^([A-Z]{3}-\d+) \[(must|should)\] (?:overrides ([A-Z]{3}-\d+)\. )?(.+)$/;
const LOOSE_TABLE = /^([A-Z]{3}-T\d+) (.+)$/;
const LOOSE_ENTRY = /^([A-Z]{3}-[A-Z]?\d+) (.+)$/;
const SIMPLE = /^(PRP|DAT)-(\d+) \[(must|should)\] (.*)$/;
const VIS = /^(VIS-\d+) \[(must|should)\] \[(\w+)\] (.*)$/;
const ENTRY = /^((?:WEB|TRM|FIX|HAR)-[A-Z]?\d+) (.*)$/;
const TASK = /^(TSK-\d+) (.*)$/;
const STATES = /^(\w+)\s+States: (.*)$/;
const FACE = /^(.+?) face\b(.*)$/;
const SCN = /^((?:SCN|PRB)-[A-Za-z0-9-]+)((?: \[\w+\])*) verifies (.*)$/;

function walk(dir) {
  if (!existsSync(dir)) return [];
  const out = [];
  for (const name of readdirSync(dir).sort()) {
    const p = join(dir, name);
    if (statSync(p).isDirectory()) out.push(...walk(p));
    else if (name.endsWith(".md")) out.push(p);
  }
  return out;
}

/** The `text` blocks of a markdown file, each as a list of { text, line }. */
function blocks(file) {
  const out = [];
  let cur = null;
  readFileSync(file, "utf8").split("\n").forEach((text, i) => {
    if (cur && text.startsWith("```")) {
      out.push(cur);
      cur = null;
    } else if (cur) cur.push({ text, line: i + 1 });
    else if (text.startsWith("```text")) cur = [];
  });
  return out;
}

/** "A | B (B1 | B2) | C" -> leaf names with their path: ["A", "B.B1", "B.B2", "C"]. */
export function parseStates(text) {
  const leaves = [];
  const all = [];
  let i = 0;
  const list = (prefix) => {
    for (;;) {
      const m = /^\s*(\w+)\s*/.exec(text.slice(i));
      if (!m) throw new Error(`bad States line near "${text.slice(i)}"`);
      i += m[0].length;
      const name = prefix ? `${prefix}.${m[1]}` : m[1];
      all.push(name);
      if (text[i] === "(") {
        i += 1;
        list(name);
        if (text[i] !== ")") throw new Error("missing )");
        i += 1;
        while (text[i] === " ") i += 1;
      } else leaves.push(name);
      if (text[i] === "|") i += 1;
      else return;
    }
  };
  list("");
  return { leaves, all };
}

/** Split an EARS sentence into its state scope and its trigger. */
export function parseEars(body) {
  const s = body.replace(/\s+/g, " ").trim();
  let m = /^While (.+?), when (.+?), [A-Z]\w+ shall /.exec(s);
  if (m) return { form: "state-event", scope: m[1], trigger: m[2] };
  m = /^When (.+?), [A-Z]\w+ shall /.exec(s);
  if (m) return { form: "event", scope: null, trigger: m[1] };
  m = /^If (.+?), then [A-Z]\w+ shall /.exec(s);
  if (m) return { form: "unwanted", scope: null, trigger: m[1] };
  m = /^While (.+?), [A-Z]\w+ shall /.exec(s);
  if (m) return { form: "state", scope: m[1], trigger: null };
  if (/^[A-Z]\w+ shall /.test(s)) return { form: "ubiquitous", scope: null, trigger: null };
  return { form: "unknown", scope: null, trigger: null };
}

const indent = (t) => t.length - t.trimStart().length;

/**
 * @param {string} root the package directory (it holds spec/, fixture/, scenarios/)
 * @returns the model: regions, intents, events, faces, rules, tables, simple rules, tasks,
 *          commitments, entries, bindings, scenarios, and parse problems
 */
export function readPackage(root) {
  const model = {
    root,
    regions: [],
    intents: [],
    events: [],
    faces: [],
    rules: [],
    tables: [],
    statements: [],
    tasks: [],
    commitments: [],
    entries: [],
    bindings: [],
    scenarios: [],
    problems: [],
  };
  const files = [...walk(join(root, "spec")), ...walk(join(root, "fixture")), ...walk(join(root, "scenarios"))];
  for (const file of files) {
    const rel = relative(root, file);
    for (const block of blocks(file)) readBlock(model, rel, block);
  }
  return model;
}

function readBlock(model, file, lines) {
  let cur = null; // the item that takes continuation lines
  let mode = null;
  const where = (l) => ({ file, line: l.line });
  for (const l of lines) {
    const t = l.text;
    const flat = t.trim();
    if (flat === "") {
      if (mode !== "scenario") cur = null;
      if (mode !== "scenario") mode = null;
      else {
        cur = null;
        mode = null;
      }
      continue;
    }
    let m;
    if (indent(t) === 0) {
      if ((m = RULE.exec(t))) {
        cur = {
          id: m[1],
          level: m[2],
          capability: m[3] ?? null,
          origin: m[4],
          sets: split(m[5]),
          overrides: m[6] ?? null,
          body: "",
          fail: null,
          ...where(l),
        };
        model.rules.push(cur);
        mode = "rule";
      } else if ((m = TABLE.exec(t))) {
        cur = {
          id: m[1],
          level: m[2],
          decides: m[3].trim(),
          scope: m[4]?.trim() ?? null,
          owns: split(m[5]).filter((x) => x !== "-"),
          rows: [],
          text: "",
          ...where(l),
        };
        model.tables.push(cur);
        mode = "table";
      } else if ((m = SIMPLE.exec(t))) {
        cur = {
          id: `${m[1]}-${m[2]}`,
          kind: m[1] === "PRP" ? "property" : "data",
          level: m[3],
          body: m[4],
          ...where(l),
        };
        model.statements.push(cur);
        mode = "text";
      } else if ((m = VIS.exec(t))) {
        cur = { id: m[1], level: m[2], capability: m[3], body: m[4], ...where(l) };
        model.commitments.push(cur);
        mode = "text";
      } else if ((m = TASK.exec(t))) {
        cur = { id: m[1], body: m[2], ...where(l) };
        model.tasks.push(cur);
        mode = "text";
      } else if ((m = LOOSE_RULE.exec(t)) && !/^(PRP|DAT|VIS)-/.test(t)) {
        cur = {
          id: m[1],
          level: m[2],
          capability: null,
          origin: null,
          sets: [],
          overrides: m[3] ?? null,
          body: m[4],
          fail: null,
          ...where(l),
        };
        model.rules.push(cur);
        mode = "rule";
      } else if ((m = LOOSE_TABLE.exec(t))) {
        cur = {
          id: m[1],
          level: "must",
          decides: null,
          scope: null,
          owns: [],
          rows: [],
          text: "",
          title: m[2],
          ...where(l),
        };
        model.tables.push(cur);
        mode = "table";
      } else if ((m = SCN.exec(t))) {
        cur = {
          id: m[1],
          marks: [...m[2].matchAll(/\[(\w+)\]/g)].map((x) => x[1]),
          verifies: split(m[3]),
          steps: [],
          ...where(l),
        };
        model.scenarios.push(cur);
        mode = "scenario";
      } else if ((m = ENTRY.exec(t))) {
        cur = { id: m[1], body: m[2], ...where(l) };
        model.entries.push(cur);
        mode = "entry";
      } else if ((m = LOOSE_ENTRY.exec(t))) {
        cur = { id: m[1], body: m[2], ...where(l) };
        model.entries.push(cur);
        mode = "entry";
      } else if (flat === "Intents:") mode = "intents";
      else if (flat === "Events:") mode = "events";
      else if ((m = STATES.exec(t))) {
        try {
          model.regions.push({ name: m[1], ...parseStates(m[2]), ...where(l) });
        } catch (e) {
          model.problems.push({ ...where(l), problem: e.message });
        }
        cur = null;
        mode = null;
      } else if ((m = FACE.exec(t))) {
        cur = { name: m[1].trim(), note: m[2].trim(), items: [], ...where(l) };
        model.faces.push(cur);
        mode = "face";
      } else if (mode === "scenario" && cur) cur.steps.push({ text: flat, line: l.line });
      else {
        cur = null;
        mode = "prose";
      }
      continue;
    }
    // an indented line
    if (mode === "intents") {
      m = /^\s+([a-z-]+)\s{2,}(.+)$/.exec(t);
      if (m) model.intents.push({ id: m[1], phrase: m[2].trim(), ...where(l) });
      else model.problems.push({ ...where(l), problem: "bad intent line" });
    } else if (mode === "events") {
      for (const phrase of flat.split(/\s{2,}/)) model.events.push({ phrase, ...where(l) });
    } else if (mode === "rule" && cur) {
      if (flat.startsWith("Fail:")) cur.fail = flat.slice(5).trim();
      else cur.body += (cur.body ? " " : "") + flat;
    } else if (mode === "table" && cur) {
      cur.text += `${flat}\n`;
      m = /^\s{2}(\d+) (.*)$/.exec(t);
      const grid = cur.id.startsWith("MEM-") && indent(t) === 2 && !/^region\b/.test(flat);
      if (m && indent(t) === 2) {
        const parts = m[2].split(/\s{2,}/);
        cur.rows.push({ id: `${cur.id}.${m[1]}`, when: parts[0].trim(), then: parts.slice(1).join(" ").trim() });
      } else if (grid) {
        const parts = flat.split(/\s{2,}/);
        cur.rows.push({ id: `${cur.id}.${cur.rows.length + 1}`, when: parts[0], then: parts.slice(1).join(" | ") });
      } else if (cur.rows.length && indent(t) > 2) {
        const row = cur.rows[cur.rows.length - 1];
        const parts = flat.split(/\s{2,}/);
        if (parts.length > 1) {
          row.when += ` ${parts[0]}`;
          row.then += ` ${parts.slice(1).join(" ")}`;
        } else if (indent(t) < 30) row.when += ` ${flat}`;
        else row.then += ` ${flat}`;
      }
    } else if (mode === "face" && cur) {
      m = /^\s+(\d+|[a-z]) (?:r(\d+) )?(?:([PNQ]) )?(.*)$/.exec(t);
      if (m && indent(t) <= 6) {
        cur.items.push({
          key: m[1],
          rank: m[2] ? Number(m[2]) : null,
          emphasis: m[3] ?? null,
          text: m[4],
          depth: indent(t),
        });
      } else if (cur.items.length) cur.items[cur.items.length - 1].text += ` ${flat}`;
      else cur.note += ` ${flat}`;
    } else if (mode === "entry" && cur) {
      cur.body += `\n${flat}`;
      m = /^\s+([a-z]+(?:-[a-z]+)*)\s{2,}(.+?)\s{2,}(.+)$/.exec(t);
      if (m && m[1] !== "intent") {
        model.bindings.push({ sheet: cur.id, intent: m[1], context: m[2].trim(), binding: m[3].trim(), ...where(l) });
      } else if (
        model.bindings.length && indent(t) > 30 && model.bindings[model.bindings.length - 1].sheet === cur.id
      ) {
        model.bindings[model.bindings.length - 1].binding += ` ${flat}`;
      }
    } else if (mode === "scenario" && cur) cur.steps.push({ text: flat, line: l.line });
    else if (cur && "body" in cur) cur.body += ` ${flat}`;
  }
}

/** Read only the scenarios (or neutral probes) of the markdown files in one directory. */
export function readScenarioDir(dir) {
  const model = {
    scenarios: [],
    problems: [],
    rules: [],
    tables: [],
    statements: [],
    tasks: [],
    commitments: [],
    entries: [],
    bindings: [],
    regions: [],
    faces: [],
    intents: [],
    events: [],
  };
  for (const file of walk(dir)) for (const block of blocks(file)) readBlock(model, relative(dir, file), block);
  return model.scenarios;
}

function split(text) {
  return text.split(",").map((x) => x.trim()).filter(Boolean);
}

/** Every identifier of the model that a check can cite, with its level and kind. */
export function identifiers(model) {
  const out = [];
  for (const r of model.rules) out.push({ id: r.id, level: r.level, kind: "rule", file: r.file, line: r.line });
  for (const t of model.tables) {
    out.push({ id: t.id, level: t.level, kind: "table", file: t.file, line: t.line });
    for (const row of t.rows) {
      out.push({ id: row.id, level: t.level, kind: "row", parent: t.id, file: t.file, line: t.line });
    }
  }
  for (const s of model.statements) out.push({ id: s.id, level: s.level, kind: s.kind, file: s.file, line: s.line });
  for (const t of model.tasks) out.push({ id: t.id, level: "must", kind: "task", file: t.file, line: t.line });
  for (const c of model.commitments) {
    out.push({ id: c.id, level: c.level, kind: "commitment", file: c.file, line: c.line });
  }
  for (const e of model.entries) out.push({ id: e.id, level: null, kind: "entry", file: e.file, line: e.line });
  return out;
}
