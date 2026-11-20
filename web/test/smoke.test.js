import assert from "node:assert/strict";
import { test } from "node:test";
import { rig } from "./helpers.js";

test("board loads: meta, then columns, done is slow", () => {
  const t = rig();
  t.app.start();
  assert.equal(t.m().state, "Loading");
  t.clock.advance(400);
  assert.equal(t.m().state, "Ready");
  assert.equal(t.col("backlog").state, "Loading");
  assert.equal(t.m().filter.count, "Loading cards…");
  t.clock.advance(300);
  assert.equal(t.ids("backlog").length, 10);
  assert.equal(t.col("review").state, "Empty");
  assert.equal(t.col("done").state, "Loading");
  t.clock.advance(700);
  assert.equal(t.col("done").slow, true);
  t.clock.advance(800);
  assert.equal(t.m().filter.count, "27 cards");
});
