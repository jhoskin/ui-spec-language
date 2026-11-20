import assert from "node:assert/strict";
import { mkdirSync, mkdtempSync, readFileSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { test } from "node:test";
import { lint } from "../lib/lint.mjs";
import { identifiers, parseEars, parseStates, readPackage } from "../lib/model.mjs";

const repo = new URL("../../", import.meta.url).pathname;

/** Write a small package to a temporary directory. */
function pkg(files) {
  const root = mkdtempSync(join(tmpdir(), "pkg-"));
  for (const [name, text] of Object.entries(files)) {
    mkdirSync(join(root, name, ".."), { recursive: true });
    writeFileSync(join(root, name), `# T\n\n\`\`\`text\n${text}\n\`\`\`\n`);
  }
  return readPackage(root);
}
const BASE = `Lamp  States: Off | On (Dim | Bright)
Intents:
  press   the user presses the switch
Events:
  the timer ends`;

test("States line: nested states give leaves", () => {
  assert.deepEqual(parseStates("Empty | Grid (Idle | More) | Done").leaves, [
    "Empty",
    "Grid.Idle",
    "Grid.More",
    "Done",
  ]);
});

test("EARS forms", () => {
  assert.deepEqual(parseEars("While Lamp.Off, when the user presses the switch, Lamp shall show On."), {
    form: "state-event",
    scope: "Lamp.Off",
    trigger: "the user presses the switch",
  });
  assert.equal(parseEars("If the load fails, then Slate shall show an alert.").form, "unwanted");
  assert.equal(parseEars("Slate shall keep the address.").form, "ubiquitous");
  assert.equal(parseEars("The lamp turns on.").form, "unknown");
});

test("the worked example of the report parses", () => {
  const text = readFileSync(join(repo, "docs/Tessera worked example in consensus format.md"), "utf8");
  const root = mkdtempSync(join(tmpdir(), "tessera-"));
  mkdirSync(join(root, "spec"));
  writeFileSync(join(root, "spec/all.md"), text);
  const m = readPackage(root);
  assert.equal(m.rules.length, 36);
  assert.equal(m.rules.find((r) => r.id === "TAG-2").overrides, "TAG-1");
  assert.deepEqual(m.regions.find((r) => r.name === "Category").leaves, [
    "Empty",
    "FirstLoading",
    "FirstFailed",
    "Grid.Idle",
    "Grid.More",
    "Grid.MoreFailed",
    "Grid.Complete",
  ]);
  assert.equal(m.tables.find((t) => t.id === "NAV-T1").rows.length, 7);
  assert.equal(m.scenarios.length, 6);
  assert.deepEqual(m.scenarios[0].verifies, ["GRD-3", "GRD-4", "PRP-2", "FIX-6"]);
  assert.equal(m.tasks.length, 4);
});

test("lint 1: two rules on one state and trigger fail; a table or overrides clears them", () => {
  const two = `${BASE}
AAA-1 [must] origin: extracted  sets: Lamp
  While Lamp.Off, when the user presses the switch, Lamp shall show Lamp.On.Dim.
AAA-2 [must] origin: extracted  sets: Lamp
  When the user presses the switch, Lamp shall show Lamp.On.Bright.`;
  const f = lint(pkg({ "spec/a.md": two })).failures.filter((x) => x.rule === "trigger-conflict");
  assert.equal(f.length, 1);
  const over = two.replace(
    "AAA-2 [must] origin: extracted  sets: Lamp",
    "AAA-2 [must] origin: extracted  sets: Lamp  overrides AAA-1",
  );
  assert.equal(lint(pkg({ "spec/a.md": over })).failures.filter((x) => x.rule === "trigger-conflict").length, 0);
  const disjoint = two.replace("  When the user presses", "  While Lamp.On, when the user presses");
  assert.equal(lint(pkg({ "spec/a.md": disjoint })).failures.filter((x) => x.rule === "trigger-conflict").length, 0);
});

test("lint 2: a must-level identifier with no check fails", () => {
  const spec = `${BASE}
AAA-1 [must] origin: extracted  sets: Lamp
  While Lamp.Off, when the user presses the switch, Lamp shall show Lamp.On.Dim.`;
  assert.equal(lint(pkg({ "spec/a.md": spec })).failures.filter((x) => x.rule === "no-check").length, 1);
  const scn = `SCN-A-1 verifies AAA-1
Given start at board.
When press.
Then text "Dim" is shown.`;
  assert.equal(lint(pkg({ "spec/a.md": spec, "scenarios/a.md": scn })).failures.length, 0);
});

test("lint 3: a rule that sets a region that a table owns fails, unless the table cites it", () => {
  const spec = `${BASE}
AAA-T1 [must] decides: the timer ends  owns: Lamp
  1 Lamp.On     show Lamp.Off
  2 otherwise   nothing
AAA-1 [should] origin: extracted  sets: Lamp
  While Lamp.Off, when the user presses the switch, Lamp shall show Lamp.On.Dim.`;
  assert.equal(lint(pkg({ "spec/a.md": spec })).failures.filter((x) => x.rule === "owned-region").length, 1);
  const cited = spec.replace("2 otherwise   nothing", "2 otherwise   nothing (AAA-1 turns it on)");
  assert.equal(lint(pkg({ "spec/a.md": cited })).failures.filter((x) => x.rule === "owned-region").length, 0);
});

test("lint: unknown state, unknown trigger, state name in a Then step, stack word", () => {
  const spec = `${BASE}
AAA-1 [should] origin: extracted  sets: Lamp
  While Lamp.Broken, when the user claps, Lamp shall show a px value.`;
  const scn = `SCN-A-1 verifies AAA-1
Then text Lamp.On.Dim is shown.`;
  const rules = lint(pkg({ "spec/a.md": spec, "scenarios/a.md": scn })).failures.map((x) => x.rule);
  for (const r of ["scope", "trigger", "state-in-scenario", "stack-word"]) assert.ok(rules.includes(r), r);
});

test("the Slate package: the lint has no failures and every must-level identifier has a check", () => {
  const model = readPackage(repo);
  assert.deepEqual(lint(model).failures, []);
  assert.ok(identifiers(model).length > 150);
});
