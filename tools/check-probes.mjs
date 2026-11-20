#!/usr/bin/env node
// Runs the raw form of each probe on the reference build and prints the identifiers of the
// probes whose checks do not hold. It prints no content of a probe.
//   node tools/check-probes.mjs --set open|sealed [--drop]
// --drop moves each probe that fails to probes/dropped/ (a probe is never edited to pass).
import { mkdirSync, renameSync } from "node:fs";
import { join } from "node:path";
import { fileURLToPath } from "node:url";
import { parseArgs } from "node:util";
import { chromium } from "playwright";
import { loadProbes } from "./coldread.mjs";
import { evaluate } from "./lib/probe.mjs";
import { runRequest } from "./lib/raw-driver.mjs";
import { serve } from "./lib/serve.mjs";

const REPO = fileURLToPath(new URL("../", import.meta.url));
const { values: o } = parseArgs({
  options: { set: { type: "string", default: "open" }, drop: { type: "boolean", default: false } },
});
const server = await serve();
const browser = await chromium.launch();
const failed = [];
const probes = loadProbes(o.set);
for (const p of probes) {
  let bad;
  try {
    bad = evaluate(p, await runRequest(browser, server.url, p.request));
  } catch (e) {
    bad = [{ check: "(run)", saw: e.message }];
  }
  if (bad.length) failed.push(p.id);
}
await browser.close();
await server.close();
if (o.drop && failed.length) {
  mkdirSync(join(REPO, "probes/dropped"), { recursive: true });
  for (const id of failed) {
    renameSync(join(REPO, "probes", o.set, `${id}.json`), join(REPO, "probes/dropped", `${id}.json`));
  }
}
console.log(JSON.stringify({ set: o.set, probes: probes.length, failed }));
process.exit(failed.length && !o.drop ? 1 : 0);
