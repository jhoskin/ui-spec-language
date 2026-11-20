#!/usr/bin/env node
// Writes the inventory-only package for a control build: places, regions, states, faces
// and the intent names. Rules, tables, events, data rules, tasks, properties, scenarios
// and notes are left out. The fixture file loses its timelines.
//   node tools/dev/inventory.mjs <output directory>
import { cpSync, mkdirSync, readdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const REPO = fileURLToPath(new URL("../../", import.meta.url));
const out = process.argv[2];
const KEEP = /^(\w+\s+States: |.+ face\b|Intents:|Board --open)/;

function inventoryOf(file) {
  const lines = readFileSync(join(REPO, file), "utf8").split("\n");
  const kept = [lines[0], ""];
  let block = null;
  for (const line of lines.slice(1)) {
    if (block && line.startsWith("```")) {
      // A block can hold several items. Keep the items that are inventory.
      const items = block.join("\n").split(/\n\n+/).filter((item) => KEEP.test(item.trimStart()));
      if (items.length) kept.push("```text", items.join("\n\n"), "```", "");
      block = null;
    } else if (block) block.push(line);
    else if (line.startsWith("```text")) block = [];
  }
  return `${kept.join("\n").trimEnd()}\n`;
}

const write = (rel, text) => {
  mkdirSync(dirname(join(out, rel)), { recursive: true });
  writeFileSync(join(out, rel), text);
};
for (const f of ["spec/app.md", ...readdirSync(join(REPO, "spec/places")).map((x) => `spec/places/${x}`)]) {
  write(f, inventoryOf(f));
}
for (
  const f of [
    "spec/conventions.md",
    "spec/modality/terminal.md",
    "fixture/data.json",
    "fixture/service.json",
    "fixture/vectors.json",
    "fixture/harness.md",
  ]
) {
  mkdirSync(dirname(join(out, f)), { recursive: true });
  cpSync(join(REPO, f), join(out, f));
}
const fixture = readFileSync(join(REPO, "fixture/fixture.md"), "utf8");
write("fixture/fixture.md", `${fixture.slice(0, fixture.indexOf("## Timelines")).trimEnd()}\n`);
console.log(`inventory written to ${out}`);
