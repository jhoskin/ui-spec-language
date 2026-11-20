#!/usr/bin/env node
// The trigger lint. It fails:
//   1. two rules on one state and trigger with no decision table and no "overrides" reference;
//   2. an identifier with no check;
//   3. a rule that sets a region that a table owns.
// It also checks the notation: EARS form, known states and triggers, stack words in the core.
//   node tools/lint.mjs [package directory]
import { lint } from "./lib/lint.mjs";
import { readPackage } from "./lib/model.mjs";

const { failures, warnings } = lint(readPackage(process.argv[2] ?? "."));
for (const w of warnings) console.log(`warning  ${w.rule}  ${w.text}`);
for (const f of failures) console.log(`FAIL  ${f.rule}  ${f.at ?? ""}  ${f.text}`);
console.log(`${failures.length} failures, ${warnings.length} warnings`);
process.exit(failures.length ? 1 : 0);
