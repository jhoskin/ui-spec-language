#!/usr/bin/env node
// Reads a specification package and prints the structured model as JSON.
//   node tools/parse.mjs [package directory] [--summary]
import { parseArgs } from "node:util";
import { identifiers, readPackage } from "./lib/model.mjs";

const { values, positionals } = parseArgs({ options: { summary: { type: "boolean" } }, allowPositionals: true });
const model = readPackage(positionals[0] ?? ".");
if (values.summary) {
  const n = (k) => model[k].length;
  console.log(
    `regions ${n("regions")}, intents ${n("intents")}, events ${n("events")}, faces ${n("faces")}, rules ${
      n("rules")
    }, ` +
      `tables ${n("tables")}, data rules and properties ${n("statements")}, tasks ${n("tasks")}, commitments ${
        n("commitments")
      }, ` +
      `sheet and fixture entries ${n("entries")}, bindings ${n("bindings")}, scenarios ${n("scenarios")}, ` +
      `identifiers ${identifiers(model).length}, problems ${n("problems")}`,
  );
} else console.log(JSON.stringify(model, null, 1));
process.exit(model.problems.length ? 1 : 0);
