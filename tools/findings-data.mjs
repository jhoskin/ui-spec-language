#!/usr/bin/env node
// Prints the numbers that FINDINGS.md reports, from the result files in out/.
//   node tools/findings-data.mjs
import { readFileSync } from "node:fs";
import { identifiers, readPackage } from "./lib/model.mjs";

const load = (f) => JSON.parse(readFileSync(`out/${f}.json`, "utf8")).results;
const model = readPackage(".");
const builds = { web: load("results-web"), port: load("results-terminal"), control: load("results-control") };
const must = identifiers(model).filter((x) => x.level === "must" && !["row", "entry", "commitment"].includes(x.kind));

/** A failure that is only a mismatch of dump and grid is not a behavior failure. */
const behavior = (r) => r.failures.some((f) => !f.step.startsWith("(harness"));

function verdict(id, kind, results, lenient) {
  const scns = model.scenarios.filter((s) => s.verifies.some((v) => v === id || (kind === "table" && v.startsWith(`${id}.`)))).map((s) => s.id);
  const seen = results.filter((r) => scns.includes(r.id));
  if (!seen.length) return "not run";
  if (seen.some((r) => r.outcome === "failed" && (!lenient || behavior(r)))) return "failed";
  if (seen.some((r) => r.outcome === "passed" || r.outcome === "failed")) return "passed";
  return "inapplicable";
}

const out = { mustIdentifiers: must.length, verdicts: {}, tasks: {}, probes: {}, scenarios: {} };
for (const [name, results] of Object.entries(builds)) {
  const count = { passed: 0, failed: 0, inapplicable: 0, "not run": 0 };
  const lenient = { passed: 0, failed: 0, inapplicable: 0, "not run": 0 };
  const failed = [];
  const inapplicable = [];
  for (const x of must) {
    const v = verdict(x.id, x.kind, results, false);
    count[v] += 1;
    lenient[verdict(x.id, x.kind, results, true)] += 1;
    if (v === "failed") failed.push(x.id);
    if (v === "inapplicable") inapplicable.push(x.id);
  }
  out.verdicts[name] = { strict: count, withoutHarnessMismatch: lenient, inapplicable, failed: name === "control" ? failed.length : failed };
  out.tasks[name] = Object.fromEntries(model.tasks.map((t) => [t.id, verdict(t.id, "task", results, true)]));
  const n = (o) => results.filter((r) => r.outcome === o).length;
  out.scenarios[name] = { passed: n("passed"), failed: n("failed"), inapplicable: n("inapplicable"), failedOnBehavior: results.filter((r) => r.outcome === "failed" && behavior(r)).length };
}
const burned = ["PRB-025"];
for (const [name, file] of [["port", "terminal"], ["control", "control"], ["web", "web"]]) {
  const open = load(`results-${file}-probes-open`);
  const sealed = load(`results-${file}-probes-sealed`);
  const tally = (rs) => ({
    passed: rs.filter((r) => r.outcome === "passed").length,
    failed: rs.filter((r) => r.outcome === "failed").map((r) => r.id),
    inapplicable: rs.filter((r) => r.outcome === "inapplicable").map((r) => r.id),
  });
  out.probes[name] = {
    burned: tally(open.filter((r) => burned.includes(r.id))),
    unburned: tally(open.filter((r) => !burned.includes(r.id))),
    sealed: tally(sealed),
  };
  if (name === "control") for (const k of Object.keys(out.probes.control)) out.probes.control[k].failed = out.probes.control[k].failed.length;
}
console.log(JSON.stringify(out, null, 1));
