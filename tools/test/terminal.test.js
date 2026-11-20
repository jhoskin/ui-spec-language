// The terminal adapter against a stub build: pseudo-terminal, frames, grid and dump check.
import assert from "node:assert/strict";
import { test } from "node:test";
import { createTerminalAdapter, parseKeyBytes } from "../adapters/terminal.mjs";
import { readPackage } from "../lib/model.mjs";
import { createScreen } from "../lib/vt.mjs";

test("the grid is rebuilt from cursor moves, erase and text", () => {
  const s = createScreen(20, 4);
  s.write("\x1b[2J\x1b[2;3Hhello\x1b[1mX\x1b[0m\x1b[2;5H\x1b[K\x1b[?25l");
  s.write("\x1b[4;1Hé…·\x1b[9");
  s.write("9z");
  assert.equal(s.line(1).trimEnd(), "  he");
  assert.equal(s.line(3).trimEnd(), "é…·");
  assert.equal(s.cursorShown, false);
  assert.deepEqual(s.unknown, ['"\\u001b[99z"']);
  assert.deepEqual(s.rect([2, 3, 1, 2]), ["he"]);
});

test("the key bytes come from TRM-9", () => {
  const model = readPackage(new URL("../../", import.meta.url).pathname);
  const keys = parseKeyBytes(model.entries.find((e) => e.id === "TRM-9").body);
  assert.equal(keys.Enter, "\r");
  assert.equal(keys["Shift+Tab"], "\x1b[Z");
  assert.equal(keys.Escape, "\x1b");
  assert.equal(keys.Delete, "\x1b[3~");
  assert.equal(keys.Left, "\x1b[D");
  assert.equal(keys["Control+Z"], "\x1a");
  assert.equal(keys['Shift+"x"'], "X");
});

test("adapter on the stub: keys, text, clock, focus, and the dump agrees with the grid", async () => {
  const a = await createTerminalAdapter({ command: "/opt/homebrew/bin/python3 tools/test/stub_tui.py" });
  await a.start({ profile: "default", at: { place: "board", text: "", labels: [], assignees: [] } });
  let o = await a.observe();
  assert.equal(o.title, "Board");
  assert.equal(o.focus, null);
  await a.fire("change-filter-text", ["fix login"]);
  o = await a.observe();
  assert.deepEqual(o.focus, { role: "field", name: "Filter cards" });
  assert.equal(o.parts.find((p) => p.role === "field").text, "fix login");
  assert.match(a.screenText(), /Filter cards: fix login/);
  await a.fire("toggle-label-filter", ["bug"]);
  o = await a.observe();
  assert.equal(o.parts.find((p) => p.name === "bug").state, "on");
  assert.ok(o.texts.includes("waiting"));
  await a.advance(499);
  assert.ok((await a.observe()).texts.includes("waiting"));
  await a.advance(1);
  o = await a.observe();
  assert.ok(o.texts.includes("done"));
  assert.deepEqual(a.integrity(), []);
  await a.close();
});

test("a dump that does not match the paint is reported", async () => {
  const a = await createTerminalAdapter({ command: "/opt/homebrew/bin/python3 tools/test/stub_tui.py --lie" });
  await a.start({ profile: "default", at: { place: "board", text: "", labels: [], assignees: [] } });
  await a.fire("toggle-label-filter", ["bug"]);
  const o = await a.observe();
  assert.deepEqual(o.integrity, ['toggle "bug" does not show [x]']);
  await a.close();
});
