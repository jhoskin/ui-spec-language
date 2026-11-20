import assert from "node:assert/strict";
import { test } from "node:test";
import { rig } from "./helpers.js";

test("open from the board: ready at once, comments load, up goes Back and focuses the card", () => {
  const t = rig().ready();
  t.app.filterText("title");
  t.app.commitFilter();
  t.app.openCard("SL-114");
  assert.equal(t.hist.entries.length, 2);
  assert.equal(t.nav.address(), "#/card/SL-114");
  assert.equal(t.m().state, "Ready");
  assert.equal(t.m().column, "Ready");
  assert.equal(t.m().comments.state, "Loading");
  assert.equal(t.fx.focus, "title");
  t.clock.advance(300);
  assert.equal(t.m().comments.heading, "2 comments");
  assert.equal(t.m().comments.items[0].time, "10 Nov 2026, 12:44");
  t.app.dismiss("other");
  assert.equal(t.hist.at, 0);
  assert.equal(t.nav.address(), "#/?q=title");
  assert.equal(t.fx.focus, "card:SL-114");
  assert.equal(t.fx.scroll, "restore+show");
});

test("direct link: loading, then ready; up adds an entry; lower-case id is rewritten", () => {
  const t = rig({ address: "#/card/sl-114" });
  t.app.start();
  assert.equal(t.nav.address(), "#/card/SL-114");
  assert.equal(t.m().state, "Loading");
  t.clock.advance(250);
  assert.equal(t.m().state, "Loading");
  t.clock.advance(150);
  assert.equal(t.m().state, "Ready");
  t.app.goUp();
  assert.equal(t.hist.entries.length, 2);
  assert.equal(t.nav.address(), "#/");
  assert.equal(t.fx.focus, "title");
  assert.equal(t.col("ready").state, "Loading");
});

test("unknown card and unknown page", () => {
  let t = rig({ address: "#/card/SL-999" });
  t.app.start();
  t.clock.advance(400);
  assert.equal(t.m().title, "Card not found");
  assert.equal(t.m().text, "There is no card SL-999 on this board.");
  assert.equal(t.nav.address(), "#/card/SL-999");
  t = rig({ address: "#/nope" });
  t.app.start();
  assert.equal(t.m().title, "Page not found");
  assert.equal(t.nav.address(), "#/nope");
});

test("title: commit, refuse, cancel, leave, failed save with Retry", () => {
  const t = rig().ready();
  t.app.openCard("SL-114");
  t.app.editTitle();
  assert.equal(t.fx.focus, "title-field");
  t.app.titleText("   ");
  t.app.commitTitle();
  assert.equal(t.m().editTitle.message, "A title needs at least 1 character.");
  t.app.titleText("x".repeat(81));
  t.app.commitTitle();
  assert.equal(t.m().editTitle.message, "A title can have at most 80 characters.");
  t.app.leaveTitle();
  assert.equal(t.m().editTitle, null);
  assert.equal(t.m().title, "Card title overflows on narrow screens");
  t.app.editTitle();
  t.app.titleText("  A   flaky  title ");
  t.app.commitTitle();
  assert.equal(t.m().title, "A flaky title");
  assert.equal(t.m().pending.title, true);
  t.app.editTitle();
  assert.equal(t.m().editTitle, null);
  t.clock.advance(400);
  assert.equal(t.m().title, "Card title overflows on narrow screens");
  assert.deepEqual(t.m().notice, { kind: "error", text: "Couldn't save the title of SL-114.", action: "Retry" });
  t.app.noticeAction();
  t.clock.advance(400);
  assert.equal(t.m().title, "A flaky title");
  assert.equal(t.m().notice, null);
  t.app.editTitle();
  t.app.titleText("Left the field");
  t.app.leaveTitle();
  assert.equal(t.m().title, "Left the field");
});

test("labels on a card: limit 3 turns the others off; fixed order", () => {
  const t = rig().ready();
  t.app.openCard("SL-104");
  t.app.toggleLabel("bug");
  assert.deepEqual(t.m().labels.filter((l) => l.on).map((l) => l.id), ["bug", "api", "perf"]);
  assert.equal(t.m().labelNote, "Label limit reached (3)");
  assert.equal(t.m().labels.find((l) => l.id === "ui").off, true);
  t.app.toggleLabel("ui");
  assert.equal(t.ops().filter((o) => o === "saveLabels").length, 1);
});

test("comment: field off while sending; failure puts the text back in the field", () => {
  const t = rig().ready();
  t.app.openCard("SL-101");
  t.clock.advance(300);
  assert.equal(t.m().comments.state, "None");
  t.app.commentText("  a flaky one ");
  t.app.commitComment();
  assert.equal(t.m().comments.items[0].time, "Sending…");
  assert.equal(t.m().comments.fieldOff, true);
  t.clock.advance(500);
  assert.equal(t.m().comments.state, "None");
  assert.equal(t.m().comments.draft, "a flaky one");
  assert.equal(t.m().comments.error, "Couldn't add the comment. Your text is back in the field.");
  assert.equal(t.fx.focus, "comment-field");
  t.app.commitComment();
  t.clock.advance(500);
  assert.equal(t.m().comments.heading, "1 comment");
  assert.equal(t.m().comments.items[0].time, "20 Nov 2026, 09:00");
  assert.equal(t.m().comments.items[0].author, "Mika Ito");
  assert.equal(t.fx.focus, "comment-field");
});

test("comments of SL-120 fail once; Retry loads them", () => {
  const t = rig().ready();
  t.app.openCard("SL-120");
  t.clock.advance(300);
  assert.equal(t.m().comments.state, "Failed");
  assert.equal(t.m().comments.fieldOff, true);
  t.app.retryComments();
  t.clock.advance(300);
  assert.equal(t.m().comments.heading, "2 comments");
});

test("delete from the card place: up, notice with Undo on the board", () => {
  const t = rig().ready();
  t.app.openCard("SL-110");
  t.app.deleteCard("SL-110");
  assert.equal(t.m().place, "board");
  assert.equal(t.hist.at, 0);
  assert.equal(t.fx.focus, "title");
  assert.equal(t.m().notice.text, "Deleted SL-110.");
  t.forward();
  assert.equal(t.m().title, "Card not found");
  assert.equal(t.m().notice.text, "Deleted SL-110.");
  t.app.undo();
  assert.equal(t.m().state, "Ready");
});

test("delete after a direct link replaces the entry", () => {
  const t = rig({ address: "#/card/SL-110" });
  t.app.start();
  t.clock.advance(400);
  t.app.deleteCard("SL-110");
  assert.equal(t.hist.entries.length, 1);
  assert.equal(t.nav.address(), "#/");
  t.clock.advance(2200);
  assert.equal(t.ids("backlog").includes("SL-110"), false);
});

test("an edit made after a direct link shows on the board that loads later", () => {
  const t = rig({ address: "#/card/SL-103" });
  t.app.start();
  t.clock.advance(400);
  t.app.setAssignee("ben");
  t.app.goUp();
  t.clock.advance(300);
  assert.equal(t.col("backlog").cards[2].assignee, "Ben Okafor");
});

test("notice stays across places; selection does not", () => {
  const t = rig().ready();
  t.app.toggleSelect("SL-102");
  t.app.deleteCard("SL-101");
  t.app.openCard("SL-102");
  assert.equal(t.m().notice.text, "Deleted SL-101.");
  t.app.goUp();
  assert.equal(t.m().selection, null);
  assert.equal(t.m().notice.text, "Deleted SL-101.");
});

test("dismiss on the card place: an open description edit is cancelled before go up", () => {
  const t = rig().ready();
  t.app.openCard("SL-101");
  t.app.editDescription();
  t.app.descriptionText("draft");
  t.app.dismiss("other");
  assert.equal(t.m().place, "card");
  assert.equal(t.m().editDescription, null);
  assert.equal(t.m().description, "Let a user download every card on the board as one CSV file.");
  t.app.commentText("kept");
  t.app.dismiss("comment-field");
  assert.equal(t.m().place, "card");
  t.app.dismiss("other");
  assert.equal(t.m().place, "board");
});

test("a failed comments load is sent again only by Retry", () => {
  const t = rig().ready();
  t.app.openCard("SL-120");
  t.clock.advance(300);
  t.app.goUp();
  t.app.openCard("SL-120");
  t.clock.advance(300);
  assert.equal(t.m().comments.state, "Failed");
  assert.equal(t.ops().filter((o) => o === "loadComments").length, 1);
});
