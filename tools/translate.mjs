#!/usr/bin/env node
// Turns raw probes into the neutral scenario grammar, so that one probe runs on each stack.
// A translator model with no tools gets one probe, the package and the grammar. A
// translation is kept only if it parses and passes on the reference build (D-017).
//   node tools/translate.mjs --set open|sealed [--only PRB-001]
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { fileURLToPath } from "node:url";
import { parseArgs } from "node:util";
import { createWebAdapter } from "./adapters/web.mjs";
import { loadProbes, packageText } from "./coldread.mjs";
import { prepare, resultOf, runClaude } from "./isolate.mjs";
import { parseStep, runScenario } from "./lib/scenario.mjs";

const REPO = fileURLToPath(new URL("../", import.meta.url)).replace(/\/$/, "");
const { values: o } = parseArgs({
  options: {
    set: { type: "string", default: "open" },
    only: { type: "string" },
    model: { type: "string", default: "sonnet" },
  },
});

const prompt = (pkg, probe, feedback) =>
  `Below is the specification package of an application named Slate, and one probe. The probe is written as raw actions on the web build (keys, pointer, addresses) with checks on raw observations. Rewrite the probe in the scenario grammar of scenarios/README.md, so that it can run on any stack.

Rules:
- Use intents of spec/app.md for the actions, by the bindings of spec/modality/web.md. A raw "focus" on a card is "Given focus on card <id>.". An "advance" is "After <n> ms.". The start address becomes "Given start at board ..." or "Given start at card <id>." by its parts.
- Keep every check of the probe, and add Then steps for each fact of the answer, as far as the grammar can say them. Do not assert anything that the probe does not check or state.
- A history check becomes "Remember history depth as D." right after the start, and "Then history depth is D plus <n>.".
- If a step needs the pointer, add "via pointer" and put [pointer] in the header.
- If the probe cannot be said in the grammar (for example it checks a window title or a key that has no intent), reply with exactly: UNTRANSLATABLE: <the reason in one sentence>.
- The header is "${probe.id} verifies <identifiers of the rules, tables or data rules that decide the answer>".

Reply with the scenario only, as plain lines: the header, then one step for each line. No code fence and no other text.

${pkg}

## Probe

${
    JSON.stringify(
      {
        situation: probe.situation,
        question: probe.question,
        answer: probe.answer,
        request: probe.request,
        checks: probe.checks,
      },
      null,
      1,
    )
  }
${
    feedback
      ? `\n## Your last translation did not pass on the reference build\n\n${feedback}\n\nThe reference build is right. Correct the translation.`
      : ""
  }`;

const probes = loadProbes(o.set).filter((p) => !o.only || o.only.split(",").includes(p.id));
const outDir = join(REPO, "probes", `${o.set}-neutral`);
mkdirSync(outDir, { recursive: true });
const pkg = packageText();
const adapter = await createWebAdapter();
const statusFile = join(REPO, "probes", `translation-${o.set}.json`);
let status = {};
try {
  status = JSON.parse(readFileSync(statusFile, "utf8"));
} catch { /* first run */ }

async function translate(probe) {
  let feedback = "";
  for (let attempt = 1; attempt <= 3; attempt++) {
    const env = prepare(`translator-${probe.id}`, `${o.set}-${attempt}`, []);
    const text = resultOf(
      await runClaude({ ...env, prompt: prompt(pkg, probe, feedback), model: o.model, tools: "none" }),
    ).trim();
    if (text.startsWith("UNTRANSLATABLE")) {
      return { status: "untranslatable", reason: text.slice(15).trim(), attempts: attempt };
    }
    const lines = text.replace(/```\w*/g, "").split("\n").map((l) => l.trim()).filter(Boolean);
    const header = /^(PRB-\d+)((?: \[\w+\])*) verifies (.*)$/.exec(lines[0] ?? "");
    try {
      if (!header) throw new Error("the first line is not a header");
      lines.slice(1).forEach(parseStep);
    } catch (e) {
      feedback = `It is not in the grammar: ${e.message}`;
      continue;
    }
    const scn = {
      id: probe.id,
      marks: [...header[2].matchAll(/\[(\w+)\]/g)].map((x) => x[1]),
      verifies: header[3].split(",").map((x) => x.trim()),
      steps: lines.slice(1).map((text) => ({ text })),
    };
    const r = await runScenario(scn, adapter, { capabilities: adapter.capabilities });
    if (r.outcome === "passed") {
      writeFileSync(join(outDir, `${probe.id}.md`), `# ${probe.id}\n\n\`\`\`text\n${lines.join("\n")}\n\`\`\`\n`);
      return { status: "ok", attempts: attempt, checks: lines.filter((l) => l.startsWith("Then ")).length };
    }
    feedback = r.failures.map((f) => `${f.step}\n  saw: ${f.saw}`).join("\n");
  }
  return { status: "failed", attempts: 3 };
}

// One probe at a time: the web adapter runs one scenario at a time.
for (const probe of probes) {
  status[probe.id] = await translate(probe);
  console.error(`${probe.id}: ${status[probe.id].status}`);
  writeFileSync(statusFile, `${JSON.stringify(status, null, 1)}\n`);
}
await adapter.close();
writeFileSync(statusFile, `${JSON.stringify(status, null, 1)}\n`);
const n = (s) => Object.values(status).filter((x) => x.status === s).length;
console.log(`${o.set}: ${n("ok")} translated, ${n("untranslatable")} untranslatable, ${n("failed")} failed`);
