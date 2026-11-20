// Terminal adapter: fires intents, advances the clock and observes a terminal build.
// It runs the build on a pseudo-terminal, sends real key bytes and rebuilds the character
// grid itself. It reads the key map from spec/modality/terminal.md (TRM-8, TRM-9).
// The semantic dump of the build (TRM-H5) is checked against the grid (TRM-H6).
// It holds no expectations about what Slate does.
import { spawn } from "node:child_process";
import { createInterface } from "node:readline";
import { fileURLToPath } from "node:url";
import { readPackage } from "../lib/model.mjs";
import { createScreen } from "../lib/vt.mjs";

const REPO = fileURLToPath(new URL("../../", import.meta.url)).replace(/\/$/, "");
const COLS = 120;
const ROWS = 40;

/** TRM-9: "Enter 0x0D. Shift+Tab ESC [ Z. ..." -> { Enter: "\r", ... } */
export function parseKeyBytes(text) {
  const keys = { '"x"': "x", '"/"': "/" };
  const body = text.replace(/\s+/g, " ");
  const re = /([A-Z][A-Za-z+]*(?:\+"x")?) ((?:0x[0-9A-F]{2}|ESC(?: \S)+?))(?: alone)?\./g;
  let m;
  while ((m = re.exec(body))) {
    const spec = m[2];
    keys[m[1]] = spec.startsWith("0x")
      ? String.fromCharCode(parseInt(spec, 16))
      : `\x1b${spec.slice(4).replace(/ /g, "")}`;
  }
  keys['Shift+"x"'] = "X";
  return keys;
}

/** TRM-8: the first binding of each intent and context. */
export function parseBindings(model) {
  const out = {};
  for (const b of model.bindings.filter((x) => x.sheet === "TRM-8")) {
    (out[b.intent] ??= []).push({ context: b.context, text: b.binding });
  }
  return out;
}

// TRM-2: the written form of an address.
const personId = (name) =>
  name === "Unassigned" ? "none" : name.split(" ")[0].normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();
export function addressOf(p) {
  if (p.place === "card") return `card/${p.id}`;
  const q = [];
  if (p.text) q.push(`q=${encodeURIComponent(p.text).replace(/%20/g, "+")}`);
  if (p.labels.length) q.push(`labels=${p.labels.join(",")}`);
  if (p.assignees.length) q.push(`who=${p.assignees.map(personId).join(",")}`);
  return q.length ? `board?${q.join("&")}` : "board";
}

/** True if `text` is painted in the lines, whole or cut with "…" (TRM-A4). */
function painted(lines, text) {
  const flat = lines.map((l) => l.trim()).join(" ").replace(/\s+/g, " ");
  const want = String(text).replace(/\s+/g, " ").trim();
  if (want === "" || flat.includes(want)) return true;
  const cut = /(\S.*?)…/g;
  let m;
  while ((m = cut.exec(flat))) {
    if (m[1].length >= 3 && want.includes(m[1].trim().slice(-Math.min(12, m[1].trim().length)))) return true;
  }
  for (const piece of lines.map((l) => l.trim()).filter((l) => l.endsWith("…"))) {
    if (want.startsWith(piece.slice(0, -1).trim().split(/\]\s|\)\s|: /).pop())) return true;
  }
  return false;
}

export function createTerminalAdapter({ command } = {}) {
  const model = readPackage(REPO);
  const sheet = model.entries.find((e) => e.id === "TRM-9");
  const KEYS = parseKeyBytes(sheet.body);
  const BINDINGS = parseBindings(model);
  const argv = (command ?? "/opt/homebrew/bin/python3 tui/slate.py").split(" ");

  const helper = spawn("/opt/homebrew/bin/python3", [`${REPO}/tools/adapters/pty_helper.py`], {
    stdio: ["pipe", "pipe", "inherit"],
  });
  const lines = createInterface({ input: helper.stdout });
  const waiting = [];
  lines.on("line", (l) => waiting.shift()?.(JSON.parse(l)));
  let screen = createScreen(COLS, ROWS);
  let heard = 0;
  let integrity = [];

  const call = (cmd) =>
    new Promise((resolve) => {
      waiting.push((r) => {
        if (r.output) screen.write(Buffer.from(r.output, "base64").toString("utf8"));
        resolve(r);
      });
      helper.stdin.write(`${JSON.stringify(cmd)}\n`);
    });
  const frame = async (cmd) => {
    const r = await call(cmd);
    if (!r.line) throw new Error("the build gave no frame line in 10 s");
    return r;
  };
  const key = (name) => {
    const bytes = KEYS[name] ?? (name.length === 1 ? name : null);
    if (bytes == null) throw new Error(`TRM-9 has no bytes for the key ${name}`);
    return frame({ keys: Buffer.from(bytes, "utf8").toString("base64") });
  };
  const dump = async () => {
    const r = await call({ control: { dump: true } });
    if (!r.line) throw new Error("the build gave no semantic dump");
    return JSON.parse(r.line);
  };

  /** The key name of the first key binding of an intent (TRM-8), for an argument if it names a direction. */
  const keyOf = (intent, arg) => {
    const dirs = { up: "Up", down: "Down", left: "Left", right: "Right", first: "Home", last: "End" };
    if (arg && dirs[arg]) return dirs[arg];
    for (const b of BINDINGS[intent] ?? []) {
      if (/^activate/.test(b.text)) continue;
      const m = /^(Control\+[A-Z]|Shift\+"x"|"[^"]"|[A-Z][a-z]+)/.exec(b.text);
      if (m) return m[1];
    }
    throw new Error(`TRM-8 has no key for ${intent}`);
  };

  const matches = (p, t) =>
    p && (t.role == null || p.role === t.role || (t.role === "link" && p.role === "up-link")) && p.name === t.name &&
    (t.group == null || p.group === t.group);

  /** Move focus with Tab until it is on the target. */
  async function focusPart(target) {
    for (let i = 0; i < 80; i++) {
      const d = await dump();
      if (d.focus != null && matches(d.parts[d.focus], target)) return true;
      if (!d.parts.some((p) => matches(p, target) && !p.disabled)) return false;
      await key("Tab");
    }
    return false;
  }
  const activate = async (target) => {
    if (await focusPart(target)) await key("Enter");
  };
  const focusedCard = (
    d,
  ) => (d.focus != null && d.parts[d.focus].role === "card" ? d.parts[d.focus].name.split(" ")[0] : null);

  /** Put focus on a card: Tab to the focus stop, then move between cards by keys. */
  async function focusCard(id) {
    for (let i = 0; i < 80; i++) {
      const d = await dump();
      const at = focusedCard(d);
      if (at === id) return;
      if (at == null) {
        await key("Tab");
        continue;
      }
      const from = d.cards.find((c) => c.id === at);
      const to = d.cards.find((c) => c.id === id);
      if (!to) throw new Error(`card ${id} is not shown`);
      const ci = (c) => d.columns.indexOf(c.column);
      const inCol = (c) => d.cards.filter((x) => x.column === c.column).findIndex((x) => x.id === c.id);
      if (ci(from) !== ci(to)) await key(ci(to) > ci(from) ? "Right" : "Left");
      else await key(inCol(to) > inCol(from) ? "Down" : "Up");
    }
    throw new Error(`cannot put focus on card ${id}`);
  }

  /** Type text into a field: focus it, empty it, then one key for each character. */
  async function fill(name, text) {
    if (!(await focusPart({ role: "field", name }))) throw new Error(`no field "${name}"`);
    await key("Control+U");
    for (const ch of text) await key(ch === "\n" ? "Enter" : ch === " " ? "Space" : ch);
  }

  const fire = {
    "open-home": () => activate({ role: "link", name: "Slate" }),
    "go-back": () => key(keyOf("go-back")),
    "go-forward": () => key(keyOf("go-forward")),
    reload: async () => {
      await key(keyOf("reload"));
      heard = 0;
    },
    "enter-address": async ([raw]) => {
      await key(keyOf("enter-address"));
      for (const ch of raw) await key(ch);
      await key("Enter");
    },
    dismiss: () => key(keyOf("dismiss")),
    undo: () => key(keyOf("undo")),
    "notice-action": async () => {
      const d = await dump();
      if (d.notice?.action) await activate({ role: "action", name: d.notice.action });
    },
    "dismiss-notice": () => activate({ role: "action", name: "Dismiss" }),
    "retry-place": () => activate({ role: "action", name: "Try again" }),
    "ask-filter": () => key(keyOf("ask-filter")),
    "change-filter-text": ([text]) => fill("Filter cards", text),
    "commit-filter": async () => {
      await focusPart({ role: "field", name: "Filter cards" });
      await key(keyOf("commit-filter"));
    },
    "toggle-label-filter": ([label]) => activate({ role: "toggle", name: label, group: "Labels" }),
    "toggle-assignee-filter": ([name]) => activate({ role: "toggle", name, group: "Assignee" }),
    "clear-filters": async () => {
      const d = await dump();
      await activate({
        role: "action",
        name: d.parts.some((p) => p.name === "Clear filters") ? "Clear filters" : "Show all cards",
      });
    },
    "focus-card": ([id]) => focusCard(id),
    "move-focus": ([dir]) => key(keyOf("move-focus", dir)),
    "open-card": async ([id]) => {
      if (id && focusedCard(await dump()) !== id) await focusCard(id);
      await key(keyOf("open-card"));
    },
    "toggle-select": async ([id]) => {
      if (id) await focusCard(id);
      await key(keyOf("toggle-select"));
    },
    "select-column": ([name]) => activate({ role: "action", name: `Select all in ${name}` }),
    "clear-selection": () => activate({ role: "action", name: "Clear selection" }),
    "bulk-move": ([name]) => activate({ role: "action", name, group: "Move selected to" }),
    "bulk-label": ([label]) => activate({ role: "toggle", name: label, group: "Label selected" }),
    "pick-up": async ([id]) => {
      if (id) await focusCard(id);
      await key(keyOf("pick-up"));
    },
    carry: ([dir]) => key(keyOf("carry", dir)),
    drop: () => key(keyOf("drop")),
    "cancel-carry": () => key(keyOf("cancel-carry")),
    "delete-card": async ([id]) => {
      const d = await dump();
      if (d.parts.some((p) => p.role === "action" && p.name === "Delete card")) {
        return activate({ role: "action", name: "Delete card" });
      }
      if (id) await focusCard(id);
      await key(keyOf("delete-card"));
    },
    "retry-column": ([name]) => activate({ role: "action", name: `Retry ${name}` }),
    "go-up": () => activate({ role: "up-link", name: "← Board" }),
    "edit-title": () => activate({ role: "action", name: "Edit title" }),
    "change-title-text": ([text]) => fill("Title", text),
    "commit-title": () => key(keyOf("commit-title")),
    "leave-title": () => key(keyOf("leave-title")),
    "toggle-label": ([label]) => activate({ role: "toggle", name: label, group: "Labels" }),
    "choose-assignee": ([name]) => activate({ role: "choice", name }),
    "edit-description": () => activate({ role: "action", name: "Edit description" }),
    "change-description-text": ([text]) => fill("Description", text),
    "commit-description": () => activate({ role: "action", name: "Save" }),
    "cancel-description": () => activate({ role: "action", name: "Cancel" }),
    "change-comment-text": ([text]) => fill("Add a comment", text),
    "commit-comment": () => activate({ role: "action", name: "Add comment" }),
    "retry-comments": () => activate({ role: "action", name: "Retry" }),
    "open-board-link": () => activate({ role: "link", name: "Go to the board" }),
  };

  /** TRM-H6: what the dump says must be on the grid. Returns the list of places where it is not. */
  function crossCheck(d) {
    const bad = [];
    const marks = { on: "[x]", off: "[ ]", mixed: "[-]", chosen: "(o)", "not chosen": "( )" };
    for (const p of d.parts) {
      if (!Array.isArray(p.rect)) {
        bad.push(`${p.role} "${p.name}" has no rect`);
        continue;
      }
      const area = screen.rect(p.rect);
      const shown = p.role === "text" ? p.text ?? p.name : p.name;
      if (p.role === "card") {
        // TRM-14 puts the marks between the identifier and the title, so the two are checked apart.
        const [id, ...title] = String(p.name).split(" ");
        if (!painted(area, id) || !painted(area, title.join(" "))) {
          bad.push(`card "${p.name}" is not painted in its rect`);
        }
        continue;
      }
      if (p.role !== "placeholder" && !painted(area, shown)) {
        bad.push(`${p.role} "${String(shown).slice(0, 40)}" is not painted in its rect`);
      }
      if (p.state && marks[p.state] && !area.join(" ").includes(marks[p.state])) {
        bad.push(`${p.role} "${p.name}" does not show ${marks[p.state]}`);
      }
      if (p.role === "field" && p.text && !painted(area, p.text)) bad.push(`field "${p.name}" does not show its text`);
    }
    for (const c of d.cards) {
      if (!c.inView) continue;
      const area = screen.rect(c.rect).join(" ");
      if (!area.includes(c.id)) bad.push(`card ${c.id} is not painted in its rect`);
      if (!area.includes(c.selected ? "[x]" : "[ ]")) bad.push(`card ${c.id} does not show its selection mark`);
      for (const mk of c.marks) if (!area.includes(mk)) bad.push(`card ${c.id} does not show mark "${mk}"`);
    }
    if (d.notice && !screen.text().includes(d.notice.text.slice(0, 30))) bad.push("the notice text is not painted");
    if (d.focus != null) {
      const [r, c, h, w] = d.parts[d.focus].rect ?? [0, 0, 0, 0];
      const inside = screen.row + 1 >= r && screen.row + 1 < r + h && screen.col + 1 >= c && screen.col + 1 <= c + w;
      if (!screen.cursorShown || !inside) {
        bad.push(`the cursor is not in the part that has focus (${d.parts[d.focus].role} "${d.parts[d.focus].name}")`);
      }
    } else if (screen.cursorShown) bad.push("the cursor is shown, and no part has focus");
    if (screen.unknown.length) {
      bad.push(`control sequences outside TRM-12: ${[...new Set(screen.unknown)].slice(0, 5).join(" ")}`);
    }
    return bad;
  }

  return {
    modality: "terminal",
    capabilities: ["keys"],
    addressOf,
    screenText: () => screen.text(),
    integrity: () => integrity,
    async start({ profile, at }) {
      screen = createScreen(COLS, ROWS);
      heard = 0;
      const address = at.raw ?? addressOf(at);
      const r = await call({
        spawn: [...argv, "--profile", profile, "--address", address, "--harness"],
        cols: COLS,
        rows: ROWS,
        cwd: REPO,
      });
      if (!r.line) throw new Error(`the build did not start: ${screen.text().trim().slice(0, 300)}`);
    },
    async advance(ms) {
      await frame({ control: { advance: ms } });
    },
    async fire(intent, args, via) {
      if (via === "pointer" || !fire[intent]) {
        throw new Error(`the terminal adapter has no binding for ${intent}${via ? ` via ${via}` : ""}`);
      }
      await fire[intent](args);
    },
    async observe() {
      const d = await dump();
      const bad = crossCheck(d);
      integrity = integrity.concat(bad);
      const f = d.focus != null ? d.parts[d.focus] : null;
      const parts = d.parts.filter((p) => p.role !== "card");
      const texts = [];
      for (const p of d.parts) {
        if (p.role === "text" || p.role === "mark") texts.push(p.text ?? p.name);
        // The web adapter gives the identifier and the title of a card as two texts.
        else if (p.role === "card") texts.push(p.name.split(" ")[0], p.name.split(" ").slice(1).join(" "));
        else if (p.role !== "field" && p.role !== "placeholder") texts.push(p.name);
      }
      for (const c of d.cards) texts.push(...c.marks);
      const said = d.announcements.slice(heard);
      heard = d.announcements.length;
      return {
        title: d.title,
        address: d.address,
        depth: d.depth,
        scrollTop: d.scrollTop,
        focus: f && { role: f.role, name: f.role === "card" ? f.name.split(" ")[0] : f.name },
        parts,
        texts,
        columns: d.columns.map((name) => ({ name, cards: d.cards.filter((c) => c.column === name).map((c) => c.id) })),
        cards: d.cards.map((c) => ({ id: c.id, selected: c.selected, marks: c.marks, inView: c.inView })),
        notice: d.notice,
        requests: d.requests,
        announcements: said,
        integrity: bad,
      };
    },
    async close() {
      await call({ close: true });
      helper.stdin.end();
    },
  };
}
