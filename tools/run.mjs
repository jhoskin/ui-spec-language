#!/usr/bin/env node
// The scenario runner. It runs the scenarios (or probes) of a package on one build
// through the adapter of that stack, and writes the verdicts.
//   node tools/run.mjs --build web|terminal [--scenarios probes/open-neutral] [--only SCN-NAV-1]
//        [--out out/results-web.json] [--command "python3 tui/slate.py"] [--quiet]
import { mkdirSync, writeFileSync } from "node:fs";
import { dirname } from "node:path";
import { parseArgs } from "node:util";
import { readPackage, readScenarioDir } from "./lib/model.mjs";
import { runScenario } from "./lib/scenario.mjs";

const { values: o } = parseArgs({
  options: {
    build: { type: "string", default: "web" },
    package: { type: "string", default: "." },
    only: { type: "string" },
    out: { type: "string" },
    quiet: { type: "boolean", default: false },
    command: { type: "string" },
    scenarios: { type: "string" },
    jitter: { type: "string" },
  },
});

const adapters = {
  web: async () => (await import("./adapters/web.mjs")).createWebAdapter(),
  terminal: async () => (await import("./adapters/terminal.mjs")).createTerminalAdapter({ command: o.command }),
};
if (!adapters[o.build]) throw new Error(`no adapter for build "${o.build}"`);

const model = readPackage(o.package);
// --scenarios <dir> runs the files of that directory (neutral probes) in place of the public scenarios.
const all = o.scenarios ? readScenarioDir(o.scenarios) : model.scenarios;
const scenarios = all.filter((s) => !o.only || o.only.split(",").includes(s.id));
const adapter = await adapters[o.build]();
// --jitter <ms> waits in real time after each intent and each clock advance. A build that
// reads real time in place of the controlled clock then gives another result.
if (o.jitter) {
  const wait = () => new Promise((r) => setTimeout(r, Number(o.jitter)));
  for (const name of ["fire", "advance"]) {
    const real = adapter[name].bind(adapter);
    adapter[name] = async (...args) => {
      await real(...args);
      await wait();
    };
  }
}
const results = [];
// For the closure check: every text and every part name that an observation showed.
const seen = new Set();
const observe = adapter.observe.bind(adapter);
adapter.observe = async () => {
  const obs = await observe();
  for (const t of obs.texts) seen.add(t);
  for (const p of obs.parts) seen.add(p.name);
  if (obs.notice) seen.add(obs.notice.text);
  return obs;
};
for (const scn of scenarios) {
  const r = await runScenario(scn, adapter, { capabilities: adapter.capabilities });
  results.push(r);
  if (!o.quiet || r.outcome === "failed") {
    console.log(`${r.outcome.padEnd(12)} ${r.id}${r.reason ? `  (${r.reason})` : ""}`);
    for (const f of r.failures) console.log(`             ${f.step}\n               saw: ${f.saw}`);
  }
}
await adapter.close();
const count = (x) => results.filter((r) => r.outcome === x).length;
console.log(`${o.build}: ${count("passed")} passed, ${count("failed")} failed, ${count("inapplicable")} inapplicable`);
if (o.out) {
  mkdirSync(dirname(o.out), { recursive: true });
  writeFileSync(o.out, `${JSON.stringify({ build: o.build, results }, null, 1)}\n`);
  writeFileSync(o.out.replace(/results-/, "texts-"), `${JSON.stringify([...seen].sort(), null, 1)}\n`);
}
process.exit(count("failed") ? 1 : 0);
