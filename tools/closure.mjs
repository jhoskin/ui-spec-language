#!/usr/bin/env node
// The closure check: a build shows no text outside the inventory.
// It compares every text that the scenario run observed (out/texts-<build>.json) with the
// quoted strings of the package and the values of the fixture data. Numbers, card
// identifiers and fixture values are replaced by marks on both sides before the comparison.
//   node tools/closure.mjs --build web [--package .]
import { readdirSync, readFileSync, statSync } from "node:fs";
import { join } from "node:path";
import { parseArgs } from "node:util";

const { values: o } = parseArgs({
  options: { build: { type: "string", default: "web" }, package: { type: "string", default: "." } },
});
const root = o.package;
const data = JSON.parse(readFileSync(join(root, "fixture/data.json"), "utf8"));

const values = [
  ...data.cards.flatMap((c) => [c.title, c.description, ...c.comments.map((m) => m.text)]),
  ...data.people.map((p) => p.name),
  ...data.columns.map((c) => c.name),
  ...data.labels,
  // Text that a scenario types is a value too.
  ...files(join(root, "scenarios")).flatMap((f) =>
    [...readFileSync(f, "utf8").matchAll(/^When change-\w+-text "(.*)"\.$/gm)].map((m) =>
      m[1].replace(/\s+/g, " ").trim()
    )
  ),
].filter(Boolean).sort((a, b) => b.length - a.length);

/** Replace what varies with marks, so that "Moved SL-103 to Ready." equals "Moved SL-107 to Review.". */
function shape(text) {
  let s = text.replace(/SL-\d+/g, "<id>");
  for (const v of values) s = s.split(v).join("<v>");
  return s.replace(/\d+ \w{3} \d{4}, \d\d:\d\d/g, "<time>").replace(/\d+/g, "<n>").replace(
    /<n> (card|comment|label)s?\b/g,
    "<n> $1s",
  )
    .replace(/\s+/g, " ").trim();
}

function files(dir) {
  return readdirSync(dir).flatMap((f) => {
    const p = join(dir, f);
    return statSync(p).isDirectory() ? files(p) : p.endsWith(".md") ? [p] : [];
  });
}

const inventory = new Set(["<v>", "<id>", "<n>", ""]);
for (const f of [...files(join(root, "spec")), join(root, "fixture/fixture.md")]) {
  // A string can run over two lines, and it can hold a quoted label name:
  // "Removed "bug" from 3 cards." The inner quotes are set aside while the strings are cut.
  const text = readFileSync(f, "utf8").replace(/\n\s+/g, " ").replace(/"(\w+)" (to|from) /g, "\u00ab$1\u00bb $2 ");
  for (const m of text.matchAll(/"([^"\n]*)"/g)) inventory.add(shape(m[1].replace(/[\u00ab\u00bb]/g, '"')));
}
// Texts that are made of parts that the faces give one by one.
for (
  const extra of [
    "<id> · <v>",
    "<v> · <time>",
    "<v> · Sending…",
    "<id> <v>",
    "Select <id>",
    "Select all in <v>",
    "Retry <v>",
    "Limit <n>",
    "<n> selected",
    "<n> of <n> cards",
    "<n> cards",
    "<n> comments",
  ]
) inventory.add(extra);

const seen = JSON.parse(readFileSync(`out/texts-${o.build}.json`, "utf8"));
const outside = seen.filter((t) => !inventory.has(shape(t)));
for (const t of outside) console.log(`outside the inventory: "${t}"`);
console.log(`${o.build}: ${seen.length} texts observed, ${outside.length} outside the inventory`);
process.exit(outside.length ? 1 : 0);
