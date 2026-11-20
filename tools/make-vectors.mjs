#!/usr/bin/env node
// Writes fixture/vectors.json from the reference service double.
// A vector is a list of timed calls and the replies that a correct double gives.
// Run this only when the fixture changes on purpose, and review the diff.
import { readFileSync, writeFileSync } from "node:fs";
import { createManualClock } from "../web/src/double/clock.js";
import { createService } from "../web/src/double/service.js";

const root = new URL("../fixture/", import.meta.url);
const data = JSON.parse(readFileSync(new URL("data.json", root)));
const config = JSON.parse(readFileSync(new URL("service.json", root)));

/** Run timed calls on a fresh double. Returns the replies in the order of delivery. */
export function runVector(vector, make = createService) {
  const start = Date.parse(config.clockStart);
  const clock = createManualClock(start);
  const service = make({ data, config, profile: vector.profile, clock });
  const replies = [];
  let last = 0;
  vector.calls.forEach((c, i) => {
    clock.advance(c.at - last);
    last = c.at;
    service.call(c.op, c.args, (reply) => replies.push({ at: clock.now() - start, call: i, reply }));
  });
  clock.advance(10000);
  return replies;
}

const move = (card, column, index) => ({ card, column, index });
const vectors = [
  {
    name: "board, then three columns; Done is slow",
    profile: "default",
    calls: [
      { at: 0, op: "loadBoard", args: {} },
      { at: 400, op: "loadColumn", args: { column: "done" } },
      { at: 400, op: "loadColumn", args: { column: "progress" } },
      { at: 400, op: "loadColumn", args: { column: "review" } },
    ],
  },
  {
    name: "a move of SL-107 fails one time; the next move is saved",
    profile: "default",
    calls: [
      { at: 0, op: "moveCards", args: { moves: [move("SL-107", "progress", 0)] } },
      { at: 400, op: "loadColumn", args: { column: "progress" } },
      { at: 700, op: "moveCards", args: { moves: [move("SL-107", "progress", 0)] } },
      { at: 1100, op: "loadColumn", args: { column: "progress" } },
    ],
  },
  {
    name: "three moves in one call: the fault hits one item only",
    profile: "default",
    calls: [
      {
        at: 0,
        op: "moveCards",
        args: { moves: [move("SL-118", "review", 0), move("SL-107", "review", 1), move("SL-119", "review", 1)] },
      },
      { at: 400, op: "loadColumn", args: { column: "review" } },
      { at: 400, op: "loadColumn", args: { column: "progress" } },
    ],
  },
  {
    name: "a title with FLAKY in any case fails one time",
    profile: "default",
    calls: [
      { at: 0, op: "saveTitle", args: { card: "SL-119", title: "A Flaky title" } },
      { at: 400, op: "loadCard", args: { card: "SL-119" } },
      { at: 650, op: "saveTitle", args: { card: "SL-119", title: "A Flaky title" } },
      { at: 1050, op: "loadCard", args: { card: "SL-119" } },
    ],
  },
  {
    name: "a comment with flaky fails one time; the time of a comment is the reply time",
    profile: "default",
    calls: [
      { at: 0, op: "addComment", args: { card: "SL-119", text: "flaky text" } },
      { at: 60000, op: "addComment", args: { card: "SL-119", text: "flaky text" } },
      { at: 60500, op: "loadComments", args: { card: "SL-119" } },
      { at: 60500, op: "loadCard", args: { card: "SL-119" } },
    ],
  },
  {
    name: "delete of SL-125 fails one time; a deleted card is not found",
    profile: "default",
    calls: [
      { at: 0, op: "deleteCard", args: { card: "SL-125" } },
      { at: 400, op: "loadCard", args: { card: "SL-125" } },
      { at: 650, op: "deleteCard", args: { card: "SL-125" } },
      { at: 1050, op: "loadCard", args: { card: "SL-125" } },
    ],
  },
  {
    name: "comments of SL-120 fail one time",
    profile: "default",
    calls: [
      { at: 0, op: "loadComments", args: { card: "SL-120" } },
      { at: 300, op: "loadComments", args: { card: "SL-120" } },
    ],
  },
  {
    name: "labels, assignee and description are saved; two calls at one time reply in call order",
    profile: "default",
    calls: [
      {
        at: 0,
        op: "saveLabels",
        args: { changes: [{ card: "SL-118", labels: ["bug", "ui"] }, { card: "SL-119", labels: [] }] },
      },
      { at: 0, op: "saveAssignee", args: { card: "SL-118", assignee: null } },
      { at: 0, op: "saveDescription", args: { card: "SL-118", description: "New text" } },
      { at: 400, op: "loadColumn", args: { column: "progress" } },
    ],
  },
  {
    name: "an unknown card is not found",
    profile: "default",
    calls: [{ at: 0, op: "loadCard", args: { card: "SL-999" } }],
  },
  {
    name: "profile column-down: Ready fails one time",
    profile: "column-down",
    calls: [
      { at: 0, op: "loadColumn", args: { column: "review" } },
      { at: 0, op: "loadColumn", args: { column: "ready" } },
      { at: 300, op: "loadColumn", args: { column: "review" } },
    ],
  },
  {
    name: "profile board-down: the board fails one time",
    profile: "board-down",
    calls: [{ at: 0, op: "loadBoard", args: {} }, { at: 400, op: "loadBoard", args: {} }],
  },
  {
    name: "profile card-down: the first card load fails",
    profile: "card-down",
    calls: [
      { at: 0, op: "loadCard", args: { card: "SL-119" } },
      { at: 250, op: "loadCard", args: { card: "SL-119" } },
    ],
  },
  {
    name: "profile empty: no cards",
    profile: "empty",
    calls: [
      { at: 0, op: "loadBoard", args: {} },
      { at: 0, op: "loadColumn", args: { column: "backlog" } },
      { at: 0, op: "loadCard", args: { card: "SL-101" } },
    ],
  },
];

if (import.meta.main) {
  for (const v of vectors) v.replies = runVector(v);
  writeFileSync(new URL("vectors.json", root), `${JSON.stringify({ vectors }, null, 1)}\n`);
  console.log(`${vectors.length} vectors written`);
}
