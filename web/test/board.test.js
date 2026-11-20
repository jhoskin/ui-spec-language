import assert from "node:assert/strict";
import { test } from "node:test";
import { rig } from "./helpers.js";

test("filter: words in title or id, labels all, assignee any; address rewritten", () => {
  const t = rig().ready();
  t.app.filterText("fix  login");
  assert.equal(t.m().filter.count, "27 cards");
  t.clock.advance(249);
  assert.equal(t.nav.address(), "#/");
  t.clock.advance(1);
  assert.equal(t.nav.address(), "#/?q=fix+login");
  assert.equal(t.m().filter.count, "2 of 27 cards");
  assert.equal(t.hist.entries.length, 1);
  assert.equal(t.col("backlog").count, "1 of 10 cards");
  assert.equal(t.col("progress").state, "NoMatch");
  assert.equal(t.col("review").state, "Empty");
  t.app.clearFilters();
  assert.equal(t.fx.focus, "filter");
  t.app.toggleLabelFilter("ui");
  t.app.toggleLabelFilter("bug");
  assert.equal(t.nav.address(), "#/?labels=bug,ui");
  assert.equal(t.m().filter.count, "4 of 27 cards");
  t.app.toggleWhoFilter("none");
  t.app.toggleWhoFilter("ana");
  assert.equal(t.nav.address(), "#/?labels=bug,ui&who=ana,none");
  assert.equal(t.m().filter.count, "1 of 27 cards");
  t.app.filterText("sl-11");
  t.app.commitFilter();
  assert.equal(t.m().filter.count, "0 of 27 cards");
  assert.equal(t.m().line.text, "No cards match these filters.");
});

test("commit with one card left focuses it and does not open it", () => {
  const t = rig().ready();
  t.app.filterText("redirect");
  t.app.commitFilter();
  assert.equal(t.fx.focus, "card:SL-102");
  assert.equal(t.m().place, "board");
});

test("unknown filter values leave the address", () => {
  const t = rig({ address: "#/?labels=ui,nope&who=zed&x=1" }).ready();
  assert.equal(t.nav.address(), "#/?labels=ui");
});

test("carry with keys: preview only, same index across columns, drop saves, notice at the reply", () => {
  const t = rig().ready();
  t.app.pickUp("SL-103");
  t.app.carry("right");
  assert.deepEqual(t.ids("ready").slice(0, 4), ["SL-111", "SL-112", "SL-103", "SL-113"]);
  assert.deepEqual(t.ops().filter((o) => o === "moveCards"), []);
  t.app.drop();
  assert.equal(t.col("ready").cards[2].pending, true);
  assert.equal(t.m().notice, null);
  t.clock.advance(400);
  assert.deepEqual(t.m().notice, { kind: "info", text: "Moved SL-103 to Ready.", action: "Undo" });
  t.app.undo();
  assert.equal(t.ids("backlog")[2], "SL-103");
  assert.equal(t.m().notice, null);
  t.clock.advance(400);
  assert.equal(t.m().notice, null);
  assert.equal(t.fx.focus, "card:SL-103");
});

test("cancel carry and drop in place send nothing", () => {
  const t = rig().ready();
  t.app.pickUp("SL-101");
  t.app.carry("down");
  t.app.cancelCarry();
  assert.equal(t.ids("backlog")[0], "SL-101");
  t.app.pickUp("SL-101");
  t.app.carry("up");
  t.app.drop();
  assert.equal(t.ops().includes("moveCards"), false);
  assert.equal(t.m().notice, null);
});

test("move with a filter: directly after the visible card above, top means absolute top", () => {
  const t = rig().ready();
  t.app.toggleLabelFilter("bug");
  assert.deepEqual(t.ids("backlog"), ["SL-102", "SL-106", "SL-109"]);
  t.app.pickUp("SL-109");
  t.app.carry("up");
  t.app.drop();
  t.clock.advance(400);
  t.app.pickUp("SL-106");
  t.app.carry("up");
  t.app.carry("up");
  t.app.drop();
  t.clock.advance(400);
  t.app.clearFilters();
  assert.deepEqual(t.ids("backlog").slice(0, 5), ["SL-106", "SL-101", "SL-102", "SL-109", "SL-103"]);
});

test("a full column refuses a drop with a notice and no request", () => {
  const t = rig().ready();
  t.app.pickUp("SL-111");
  t.app.carry("right");
  t.app.drop();
  t.clock.advance(400);
  assert.equal(t.ids("progress").length, 3);
  t.app.pickUp("SL-112");
  t.app.carry("right");
  t.app.drop();
  assert.deepEqual(t.m().notice, { kind: "info", text: "In progress is full (3 cards).", action: null });
  assert.equal(t.ops().filter((o) => o === "moveCards").length, 1);
  assert.equal(t.ids("ready")[0], "SL-112");
  t.clock.advance(7999);
  assert.ok(t.m().notice);
  t.clock.advance(1);
  assert.equal(t.m().notice, null);
});

test("a failed move rolls back; Retry repeats it", () => {
  const t = rig().ready();
  t.app.pickUp("SL-107");
  t.app.carry("right");
  t.app.drop();
  assert.equal(t.ids("ready")[6], "SL-107");
  assert.equal(t.app.model().columns[1].cards[6].pending, true);
  t.app.pickUp("SL-107");
  assert.equal(t.m().carrying, false);
  t.clock.advance(400);
  assert.equal(t.ids("backlog")[6], "SL-107");
  assert.deepEqual(t.m().notice, {
    kind: "error",
    text: "Couldn't move SL-107. It is back in Backlog.",
    action: "Retry",
  });
  t.clock.advance(60000);
  assert.ok(t.m().notice);
  t.app.noticeAction();
  t.clock.advance(400);
  assert.equal(t.ids("ready")[6], "SL-107");
  assert.equal(t.m().notice.text, "Moved SL-107 to Ready.");
});

test("delete waits for the notice to end; Undo sends nothing", () => {
  const t = rig().ready();
  t.app.deleteCard("SL-101");
  assert.equal(t.fx.focus, "card:SL-102");
  assert.equal(t.m().notice.text, "Deleted SL-101.");
  assert.equal(t.m().filter.count, "26 cards");
  t.app.undo();
  assert.equal(t.ids("backlog")[0], "SL-101");
  assert.equal(t.fx.focus, "card:SL-101");
  t.clock.advance(20000);
  assert.equal(t.ops().includes("deleteCard"), false);
  t.app.deleteCard("SL-101");
  t.clock.advance(7999);
  assert.equal(t.ops().includes("deleteCard"), false);
  t.clock.advance(1);
  assert.equal(t.ops().includes("deleteCard"), true);
});

test("a new notice sends a waiting delete; a failed delete puts the card back", () => {
  const t = rig().ready();
  t.app.deleteCard("SL-125");
  t.app.deleteCard("SL-124");
  assert.equal(t.ops().filter((o) => o === "deleteCard").length, 1);
  t.clock.advance(400);
  assert.equal(t.m().notice.text, "Couldn't delete SL-125. It is back in Done.");
  // Back at its old index (5), counted in the column as it is now.
  assert.equal(t.ids("done").indexOf("SL-125"), 5);
  assert.equal(t.ops().filter((o) => o === "deleteCard").length, 2);
  t.app.noticeAction();
  assert.equal(t.ids("done").includes("SL-125"), false);
  t.clock.advance(400);
  assert.equal(t.m().notice, null);
});

test("bulk move: board order, end of target, stops at the limit, the rest stay selected", () => {
  const t = rig().ready();
  for (const id of ["SL-112", "SL-102", "SL-101"]) t.app.toggleSelect(id);
  assert.equal(t.m().selection.count, "3 selected");
  t.app.bulkMove("progress");
  assert.deepEqual(t.ids("progress"), ["SL-118", "SL-119", "SL-101"]);
  assert.equal(t.m().selection.count, "2 selected");
  t.clock.advance(400);
  assert.deepEqual(t.m().notice, {
    kind: "info",
    text: "Moved 1 of 3 cards to In progress. In progress is full (3 cards).",
    action: "Undo",
  });
  t.app.bulkMove("progress");
  assert.equal(t.m().notice.text, "In progress is full (3 cards).");
  t.app.bulkMove("review");
  t.clock.advance(400);
  assert.equal(t.m().notice.text, "Moved 2 cards to Review.");
  assert.deepEqual(t.ids("review"), ["SL-102", "SL-112"]);
  assert.equal(t.m().selection, null);
  t.app.undo();
  assert.equal(t.ids("backlog")[0], "SL-102");
  assert.equal(t.ids("ready")[1], "SL-112");
  assert.equal(t.m().selection, null);
});

test("bulk move with one failed save: Retry, no Undo, the failed card is selected again", () => {
  const t = rig().ready();
  for (const id of ["SL-106", "SL-107", "SL-108"]) t.app.toggleSelect(id);
  t.app.bulkMove("review");
  assert.equal(t.m().selection, null);
  t.clock.advance(400);
  assert.deepEqual(t.m().notice, {
    kind: "error",
    text: "Moved 2 of 3 cards to Review. Couldn't move SL-107.",
    action: "Retry",
  });
  assert.deepEqual(t.ids("review"), ["SL-106", "SL-108"]);
  // Back at its old index (6), counted in the column as it is now.
  assert.equal(t.ids("backlog")[6], "SL-107");
  assert.equal(t.m().selection.count, "1 selected");
  t.app.noticeAction();
  t.clock.advance(400);
  assert.equal(t.m().notice.text, "Moved 1 card to Review.");
});

test("bulk label: adds where missing, removes when all have it, obeys the limit of 3", () => {
  const t = rig().ready();
  for (const id of ["SL-109", "SL-110", "SL-104"]) t.app.toggleSelect(id);
  assert.equal(t.m().selection.labels.find((l) => l.id === "perf").state, "mixed");
  t.app.bulkLabel("docs");
  assert.equal(t.m().notice, null);
  t.clock.advance(300);
  assert.equal(t.m().notice.text, 'Added "docs" to 2 of 3 cards. A card can have at most 3 labels.');
  assert.equal(t.m().selection.count, "3 selected");
  t.app.toggleSelect("SL-109");
  t.app.bulkLabel("docs");
  t.clock.advance(300);
  assert.equal(t.m().notice.text, 'Removed "docs" from 2 cards.');
  assert.deepEqual(t.col("backlog").cards[3].labels, ["api", "perf"]);
});

test("a selected card that a filter hides leaves the selection", () => {
  const t = rig().ready();
  t.app.toggleSelect("SL-101");
  t.app.toggleSelect("SL-102");
  t.app.toggleLabelFilter("bug");
  assert.equal(t.m().selection.count, "1 selected");
  t.app.clearFilters();
  assert.equal(t.m().selection.count, "1 selected");
  t.app.selectColumn("progress");
  t.app.selectColumn("progress");
  assert.equal(t.m().selection.count, "1 selected");
});

test("dismiss on the board: carry, then filter text, then filter focus, then selection", () => {
  const t = rig().ready();
  t.app.toggleSelect("SL-101");
  t.app.filterText("login");
  t.clock.advance(250);
  t.app.pickUp("SL-102");
  t.app.dismiss("other");
  assert.equal(t.m().carrying, false);
  assert.equal(t.m().filter.text, "login");
  t.app.dismiss("filter");
  assert.equal(t.m().filter.text, "");
  assert.equal(t.nav.address(), "#/");
  t.app.toggleSelect("SL-101");
  t.app.dismiss("filter");
  // The card that had focus last was the one picked up.
  assert.equal(t.fx.focus, "card:SL-102");
  assert.ok(t.m().selection);
  t.app.dismiss("other");
  assert.equal(t.m().selection, null);
});

test("focus moves by card, skips columns with no visible card, does not wrap", () => {
  const t = rig().ready();
  t.app.moveFocus("SL-119", "right");
  assert.equal(t.fx.focus, "card:SL-121");
  t.app.moveFocus("SL-110", "right");
  assert.equal(t.fx.focus, "card:SL-117");
  t.fx.focus = null;
  t.app.moveFocus("SL-101", "up");
  t.app.moveFocus("SL-101", "left");
  assert.equal(t.fx.focus, null);
});

test("profiles: a failed column is partial, a failed board has Try again, an empty board has a line", () => {
  let t = rig({ profile: "column-down" }).ready();
  assert.equal(t.col("ready").state, "Failed");
  assert.equal(t.m().filter.count, "20 cards");
  t.app.retryColumn("ready");
  assert.equal(t.col("ready").state, "Loading");
  t.clock.advance(300);
  assert.equal(t.m().filter.count, "27 cards");
  t = rig({ profile: "board-down" }).ready();
  assert.equal(t.m().state, "Failed");
  t.app.retryPlace();
  t.clock.advance(400);
  assert.equal(t.m().state, "Ready");
  t = rig({ profile: "empty" }).ready();
  assert.equal(t.m().line.text, "This board has no cards yet.");
  assert.equal(t.m().filter.count, "0 cards");
});
