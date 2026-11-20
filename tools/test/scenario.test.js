import assert from "node:assert/strict";
import { test } from "node:test";
import { readPackage } from "../lib/model.mjs";
import { judge, parseStep, runScenario, tokens } from "../lib/scenario.mjs";

test("tokens keep quoted text together", () => {
  assert.deepEqual(tokens(' "In progress" 3 bug'), ["In progress", "3", "bug"]);
});

test("steps parse", () => {
  assert.deepEqual(parseStep('Given start at board text "fix login" labels bug,ui assignees "Ana Ruiz",Unassigned.'), {
    kind: "start",
    at: { place: "board", text: "fix login", labels: ["bug", "ui"], assignees: ["Ana Ruiz", "Unassigned"] },
  });
  assert.deepEqual(parseStep("When carry-to Ready 3 via pointer."), {
    kind: "fire",
    intent: "carry-to",
    args: ["Ready", "3"],
    via: "pointer",
  });
  assert.deepEqual(parseStep('Then toggle "bug" in "Label selected" is mixed.'), {
    kind: "check",
    what: "part",
    role: "toggle",
    name: "bug",
    group: "Label selected",
    state: "mixed",
  });
  assert.deepEqual(parseStep('Then notice "Added "docs" to 2 cards." with no action.'), {
    kind: "check",
    what: "notice",
    text: 'Added "docs" to 2 cards.',
    action: null,
  });
  assert.throws(() => parseStep("Then the board looks nice."));
});

test("every step of every public scenario is in the grammar", () => {
  const model = readPackage(new URL("../../", import.meta.url).pathname);
  for (const s of model.scenarios) for (const step of s.steps) parseStep(step.text);
});

const obs = {
  title: "Board",
  address: "#/",
  depth: 3,
  focus: { role: "card", name: "SL-1" },
  parts: [{ role: "toggle", name: "bug", group: "Labels", state: "on", disabled: false }],
  texts: ["27 cards"],
  columns: [{ name: "Ready", cards: ["SL-1", "SL-2"] }],
  cards: [{ id: "SL-1", selected: true, marks: ["Saving…"] }],
  notice: null,
  requests: [{ op: "moveCards" }],
  announcements: [],
};

test("judge reports what it saw in place of the expectation", () => {
  const j = (text) => judge(parseStep(text), obs, { D: 2 }, { addressOf: () => "#/" });
  assert.equal(j('Then text "27 cards" is shown.'), "");
  assert.equal(j('Then text "7 cards" is shown.'), 'no text "7 cards"');
  assert.equal(j('Then column "Ready" starts SL-1.'), "");
  assert.equal(j('Then column "Ready" cards SL-1.'), 'column "Ready" has SL-1, SL-2');
  assert.equal(j("Then history depth is D plus 1."), "");
  assert.equal(j("Then focus place title."), 'focus card "SL-1"');
  assert.equal(j('Then card SL-1 has mark "Saving…".'), "");
  assert.equal(j("Then no notice."), "");
  assert.equal(j("Then requests moveCards 2."), "requests moveCards 1");
  assert.equal(j('Then toggle "bug" in "Labels" is off.'), 'toggle "bug" is on');
  assert.equal(j("Then address board."), "");
});

test("the runner holds the expectations; the adapter only acts and observes", async () => {
  const calls = [];
  const adapter = {
    modality: "fake",
    addressOf: () => "#/",
    start: (x) => calls.push(["start", x.profile]),
    advance: (ms) => calls.push(["advance", ms]),
    fire: (intent, args) => calls.push([intent, ...args]),
    observe: () => obs,
  };
  const scn = {
    id: "SCN-X-1",
    verifies: [],
    marks: [],
    steps: [
      "Given profile empty.",
      "Given start at board.",
      "After 5 ms.",
      "When drop.",
      'Then text "27 cards" is shown.',
      "Then no notice.",
    ].map((text) => ({ text })),
  };
  const r = await runScenario(scn, adapter);
  assert.equal(r.outcome, "passed");
  assert.deepEqual(calls, [["start", "empty"], ["advance", 5], ["drop"]]);
  const pointer = await runScenario({ ...scn, marks: ["pointer"] }, adapter, { capabilities: [] });
  assert.equal(pointer.outcome, "inapplicable");
});
