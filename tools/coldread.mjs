#!/usr/bin/env node
// The cold-read harness.
//
//   node tools/coldread.mjs seal [--seed 20261120]
//       moves a quarter of probes/open to probes/sealed, by a seeded shuffle within each
//       area and level, and writes the hash of the sealed set.
//   node tools/coldread.mjs run --run 01 [--set open|sealed] [--readers opus,sonnet,haiku,qwen]
//       gives the probe questions to readers who have only the specification package, and
//       to control readers who have no specification. A grader compares each answer with
//       the key. The record goes to gate/run-<id>/.
//
// A reader gets no tools. The report shows questions, answers and grades. It does not
// show the key, so that the specification author revises from the reference build.
import { createHash } from "node:crypto";
import { existsSync, mkdirSync, readdirSync, readFileSync, renameSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { fileURLToPath } from "node:url";
import { parseArgs } from "node:util";
import { prepare, resultOf, runClaude } from "./isolate.mjs";

const REPO = fileURLToPath(new URL("../", import.meta.url)).replace(/\/$/, "");
const sha = (text) => createHash("sha256").update(text).digest("hex");
const GATING = ["opus", "sonnet", "haiku"];

const DESCRIPTION =
  "Slate is a kanban issue tracker in a web browser. It has a board with five columns of cards, with drag and keyboard moves, a filter bar (text, labels, assignee), multi-select with bulk move and bulk label, a card detail view with title, description, labels, assignee and comments, optimistic saves with undo, and mock data with no real back end.";

/** The package files that a reader gets, in reading order. */
export function packageText(root = REPO) {
  const files = ["spec/conventions.md", "spec/app.md"];
  for (const dir of ["spec/places", "spec"]) {
    for (const f of readdirSync(join(root, dir)).sort()) {
      const p = `${dir}/${f}`;
      if (f.endsWith(".md") && !files.includes(p)) files.push(p);
    }
  }
  files.push(
    "spec/modality/web.md",
    "fixture/fixture.md",
    "fixture/harness.md",
    "fixture/data.json",
    "fixture/service.json",
  );
  for (const f of readdirSync(join(root, "scenarios")).sort()) files.push(`scenarios/${f}`);
  return files.map((f) => `<file name="${f}">\n${readFileSync(join(root, f), "utf8")}\n</file>`).join("\n\n");
}

export function loadProbes(set, root = REPO) {
  const dir = join(root, "probes", set);
  if (!existsSync(dir)) return [];
  return readdirSync(dir).filter((f) => f.endsWith(".json")).sort().map((f) =>
    JSON.parse(readFileSync(join(dir, f), "utf8"))
  );
}

/** A small seeded generator (mulberry32). */
function rng(seed) {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

/** Choose a quarter of the probes, spread over area and level. */
export function chooseSealed(probes, seed) {
  const next = rng(seed);
  const groups = new Map();
  for (const p of probes) {
    const key = `${p.level}/${p.area}`;
    groups.set(key, [...(groups.get(key) ?? []), p.id]);
  }
  const want = Math.round(probes.length / 4);
  const pool = [];
  for (const key of [...groups.keys()].sort()) {
    const ids = groups.get(key).sort();
    for (let i = ids.length - 1; i > 0; i--) {
      const j = Math.floor(next() * (i + 1));
      [ids[i], ids[j]] = [ids[j], ids[i]];
    }
    ids.forEach((id, i) => pool.push({ id, turn: i, order: next() }));
  }
  pool.sort((a, b) => a.turn - b.turn || a.order - b.order);
  return pool.slice(0, want).map((x) => x.id).sort();
}

const questions = (probes) =>
  probes.map((p) => `### ${p.id}\nSituation:\n${p.situation.map((s) => `- ${s}`).join("\n")}\nQuestion: ${p.question}`)
    .join("\n\n");

const FORMAT = `Answer every question. Reply with one JSON object and nothing else:
{"answers": [{"id": "PRB-001", "answer": "<what the user perceives, short and exact; quote strings exactly>", "basis": "STATED" | "DERIVED" | "GUESS", "cites": ["<identifiers>"]}], "ambiguities": ["<a place where the text can be read in two ways>"], "contradictions": ["<two statements that disagree, with their identifiers>"]}
Give every fact that the question asks for, and no more. For a notice, give its exact text and name each of its actions. For a change of the history, give the number of entries compared with the start. For an order of cards, list the identifiers.
basis: STATED if the text says it directly, DERIVED if you combined statements, GUESS if the text does not decide it.`;

const readerPrompt = (pkg, probes) =>
  `You are a cold reader. You have never seen the application. Below is the complete specification package of an application named Slate. Answer the questions from the package alone. Do not use what applications usually do, unless the package says that a platform default applies.\n\n${pkg}\n\n## Questions\n\nEach question gives a situation on the web build (keys and pointer as in spec/modality/web.md) and asks what the user perceives.\n\n${
    questions(probes)
  }\n\n${FORMAT}`;

const controlPrompt = (probes) =>
  `You have no specification. ${DESCRIPTION}\n\nAnswer each question with what you think such an application does. Use convention and your best judgment.\n\n## Questions\n\n${
    questions(probes)
  }\n\n${FORMAT}`;

const graderPrompt = (items) =>
  `You grade answers against a key. For each item, compare the answer with the key on the facts that the question asks for. Wording does not matter. A quoted string must match exactly, except for quote marks and a final full stop.
Grade only the facts that the question asks for. A fact that the key adds beyond the question does not count against an answer that omits it. A correct extra fact in the answer does not count against it.
Grade 1: every fact that the question asks for is in the answer as the key gives it, and nothing in the answer contradicts the key.
Grade 0.5: part of the facts are right and none is wrong, or the answer is right but hedges between two outcomes.
Grade 0: a fact is wrong, or the answer does not decide.
Reply with one JSON object and nothing else: {"grades": [{"n": <item number>, "grade": 0 | 0.5 | 1, "why": "<one short clause>"}]}

${items.map((x, i) => `Item ${i + 1}\nQuestion: ${x.question}\nKey: ${x.key}\nAnswer: ${x.answer}`).join("\n\n")}`;

function parseJson(text) {
  const a = text.indexOf("{");
  const b = text.lastIndexOf("}");
  if (a < 0 || b < 0) return null;
  try {
    return JSON.parse(text.slice(a, b + 1));
  } catch {
    return null;
  }
}

async function askClaude(role, run, model, prompt) {
  const env = prepare(role, run, []);
  const t = await runClaude({ ...env, prompt, model, tools: "none" });
  const calls = t.split("\n").filter((l) => l.includes('"type":"tool_use"')).length;
  return { text: resultOf(t), toolCalls: calls };
}

async function askOllama(model, prompt) {
  try {
    return await callOllama(model, prompt);
  } catch (e) {
    return { text: "", toolCalls: 0, error: String(e.message) };
  }
}

async function callOllama(model, prompt) {
  // The reply is read as a stream, so that a slow local model does not hit a time limit.
  const r = await fetch("http://127.0.0.1:11434/api/generate", {
    method: "POST",
    body: JSON.stringify({ model, prompt, stream: true, options: { num_ctx: 65536, temperature: 0 } }),
  });
  let text = "";
  let rest = "";
  for await (const chunk of r.body) {
    rest += Buffer.from(chunk).toString("utf8");
    const lines = rest.split("\n");
    rest = lines.pop();
    for (const line of lines) if (line.trim()) text += JSON.parse(line).response ?? "";
  }
  return { text, toolCalls: 0 };
}

async function main() {
  const { values: o, positionals } = parseArgs({
    options: {
      seed: { type: "string", default: "20261120" },
      run: { type: "string" },
      set: { type: "string", default: "open" },
      readers: { type: "string", default: "opus,sonnet,haiku,qwen" },
      "no-controls": { type: "boolean", default: false },
    },
    allowPositionals: true,
  });

  if (positionals[0] === "seal") {
    const probes = loadProbes("open");
    const ids = chooseSealed(probes, Number(o.seed));
    mkdirSync(join(REPO, "probes/sealed"), { recursive: true });
    const hash = createHash("sha256");
    for (const id of ids) {
      hash.update(readFileSync(join(REPO, "probes/open", `${id}.json`)));
      renameSync(join(REPO, "probes/open", `${id}.json`), join(REPO, "probes/sealed", `${id}.json`));
    }
    const record = { seed: Number(o.seed), total: probes.length, sealed: ids.length, sha256: hash.digest("hex") };
    writeFileSync(join(REPO, "probes/sealed.json"), `${JSON.stringify(record, null, 2)}\n`);
    console.log(JSON.stringify(record));
    return;
  }

  const probes = loadProbes(o.set);
  const dir = join(REPO, "gate", `run-${o.run}`);
  mkdirSync(join(dir, "answers"), { recursive: true });
  const pkg = packageText();
  const readers = o.readers.split(",");
  const answers = {};
  const jobs = [];
  for (const r of readers) {
    jobs.push((async () => {
      const prompt = readerPrompt(pkg, probes);
      const ask = (
        text,
        n,
      ) => (r === "qwen" ? askOllama("qwen3.6:latest", text) : askClaude(`reader-${r}${n}`, o.run, r, text));
      const out = await ask(prompt, "");
      answers[r] = {
        ...(parseJson(out.text) ?? { answers: [], unreadable: out.text.slice(0, 2000) }),
        toolCalls: out.toolCalls,
      };
      // A reader that left questions out is asked one more time for those questions only.
      const missing = probes.filter((p) => !answers[r].answers.some((a) => a.id === p.id && a.answer));
      if (missing.length && missing.length < probes.length) {
        const again = parseJson((await ask(readerPrompt(pkg, missing), "-again")).text);
        answers[r].answers = [...answers[r].answers.filter((a) => a.answer), ...(again?.answers ?? [])];
        answers[r].askedAgain = missing.map((p) => p.id);
      }
      console.error(`reader ${r}: ${answers[r].answers.length} answers`);
    })());
    if (!o["no-controls"] && r !== "qwen") {
      jobs.push((async () => {
        const out = await askClaude(`control-${r}`, o.run, r, controlPrompt(probes));
        answers[`control-${r}`] = { ...(parseJson(out.text) ?? { answers: [] }), toolCalls: out.toolCalls };
        console.error(`control ${r}: ${answers[`control-${r}`].answers.length} answers`);
      })());
    }
  }
  await Promise.all(jobs);

  // Grade each reader in one call. The grader sees the question, the key and the answer only.
  const grades = {};
  await Promise.all(
    Object.keys(answers).map(async (r) => {
      const items = probes.map((p) => ({
        question: p.question,
        key: p.answer,
        answer: answers[r].answers.find((a) => a.id === p.id)?.answer ?? "(no answer)",
      }));
      const out = await askClaude(`grader-${r}`, o.run, "sonnet", graderPrompt(items));
      const g = parseJson(out.text)?.grades ?? [];
      grades[r] = Object.fromEntries(
        probes.map((p, i) => [p.id, g.find((x) => x.n === i + 1) ?? { grade: 0, why: "no grade" }]),
      );
      console.error(`graded ${r}`);
    }),
  );

  for (const r of Object.keys(answers)) {
    writeFileSync(join(dir, "answers", `${r}.json`), `${JSON.stringify(answers[r], null, 1)}\n`);
  }
  writeFileSync(join(dir, "grades.json"), `${JSON.stringify(grades, null, 1)}\n`);

  const gating = readers.filter((r) => GATING.includes(r));
  const score = (r, level) =>
    probes.filter((p) => !level || p.level === level).reduce((n, p) => n + (grades[r]?.[p.id]?.grade ?? 0), 0);
  const count = (level) => probes.filter((p) => !level || p.level === level).length;
  const blocked = probes.filter((p) => p.level === "must" && gating.some((r) => grades[r][p.id].grade < 1));
  const meta = {
    run: o.run,
    set: o.set,
    date: new Date().toISOString(),
    probes: probes.length,
    mustProbes: count("must"),
    probeBankSha256: sha(probes.map((p) => JSON.stringify(p)).join("\n")),
    packageSha256: sha(pkg),
    readers,
    gating,
    scores: Object.fromEntries(Object.keys(answers).map((r) => [r, { all: score(r), must: score(r, "must") }])),
    toolCalls: Object.fromEntries(Object.keys(answers).map((r) => [r, answers[r].toolCalls])),
    mustBlocked: blocked.map((p) => p.id),
    pass: blocked.length === 0,
  };
  writeFileSync(join(dir, "meta.json"), `${JSON.stringify(meta, null, 2)}\n`);

  const md = [
    `# Gate run ${o.run}`,
    "",
    `Set: ${o.set}. Probes: ${probes.length}, of which ${count("must")} are must-level.`,
    "",
  ];
  md.push(
    `Result: ${meta.pass ? "pass" : `blocked by ${blocked.length} must-level probes`}.`,
    "",
    "| Reader | Score, all probes | Score, must-level | Guesses | Ambiguities | Contradictions |",
    "| --- | --- | --- | --- | --- | --- |",
  );
  for (const r of Object.keys(answers).sort()) {
    const a = answers[r];
    md.push(
      `| ${r} | ${score(r)} of ${probes.length} | ${score(r, "must")} of ${count("must")} | ${
        a.answers.filter((x) => x.basis === "GUESS").length
      } | ${a.ambiguities?.length ?? 0} | ${a.contradictions?.length ?? 0} |`,
    );
  }
  md.push("", "A probe that a control reader answers correctly marks a decision that convention carries.", "");
  const shown = o.set === "sealed" ? [] : probes.filter((p) => gating.some((r) => grades[r][p.id].grade < 1));
  if (o.set === "sealed") md.push("The sealed set shows no questions here.", "");
  if (shown.length) md.push("## Wrong and split answers", "");
  for (const p of shown) {
    md.push(
      `### ${p.id} (${p.level}, ${p.area})`,
      "",
      ...p.situation.map((s) => `- ${s}`),
      "",
      `Question: ${p.question}`,
      "",
    );
    for (const r of readers) {
      const a = answers[r].answers.find((x) => x.id === p.id);
      md.push(
        `- ${r}, grade ${grades[r][p.id].grade}, ${a?.basis ?? "none"}, cites ${
          (a?.cites ?? []).join(" ") || "nothing"
        }: ${a?.answer ?? "(no answer)"}`,
      );
    }
    md.push("");
  }
  md.push("## Ambiguities and contradictions that the readers listed", "");
  for (const r of readers) {
    for (const x of answers[r].ambiguities ?? []) md.push(`- ${r}, ambiguity: ${x}`);
    for (const x of answers[r].contradictions ?? []) md.push(`- ${r}, contradiction: ${x}`);
  }
  md.push("");
  writeFileSync(join(dir, "report.md"), md.join("\n"));
  console.log(JSON.stringify({ pass: meta.pass, blocked: meta.mustBlocked, scores: meta.scores }));
}

if (import.meta.main) await main();
