# ui-spec-language

A text spec format that anchors a UI design without code or mockups, tested by rebuilding one app on a second stack from the spec alone.

The format and the process are defined in
[Text based UI design specs](docs/Text%20based%20UI%20design%20specs.md). A
small complete example is in
[Tessera worked example in consensus format](docs/Tessera%20worked%20example%20in%20consensus%20format.md).

The repository context is in [CONTEXT.md](CONTEXT.md). Decisions on points
that the report leaves open are in [DECISIONS.md](DECISIONS.md).

## Set up

```sh
just setup
```

This installs the one development dependency (Playwright, with install scripts
off) and downloads the Chromium build that it needs.

## Run the reference build

```sh
just serve
```

Then open <http://localhost:8000/web/>. Slate runs on the fixture in
`fixture/`. It has no back end, and a reload starts the data again.

## Check

```sh
just check
```

One command runs the markdown lint, the code lint, the tests, the trigger lint
of the specification, the public scenarios on each build, the closure check
and the generation of `trace.md`.

## What is where

| Path | Content |
| --- | --- |
| `docs/` | The report that defines the format, and its worked example |
| `spec/`, `fixture/`, `scenarios/`, `sidecar/` | The specification package of Slate |
| `web/` | The reference build |
| `tui/` | The terminal port, built from the package alone |
| `tools/` | The parser, the lint, the trace generator, the scenario runner, the adapters, the cold-read harness and the isolation tool |
| `probes/` | Held-out probes. Implementing agents never get this folder |
| `gate/` | The record of each acceptance gate run |
| `records/` | Evidence: the extraction probe log, the second extraction, isolation manifests and audits |
| `trace.md` | Generated: each identifier with its checks and its verdict on each build |
| `FINDINGS.md` | What the experiment showed |

## Apply the tooling to another application

The tools read a package, not Slate. To use them for your own application:

1. Write the fixture first: a data set, a table of latency and faults, and
   vectors for the service double (`fixture/`). Give your build a controlled
   clock and the controls of `fixture/harness.md`.
2. Write the package in the notation of `spec/conventions.md`. Keep the two
   closed lists (`Intents:` and `Events:`) in `spec/app.md`, one file for
   each place in `spec/places/`, and one sheet for each modality in
   `spec/modality/`.
3. Run `node tools/parse.mjs --summary` until it reports no problems, then
   `node tools/lint.mjs` until it reports no failures.
4. Write scenarios in the grammar of `scenarios/README.md`. Each one cites
   the identifiers that it verifies.
5. Write an adapter for your stack in `tools/adapters/`. An adapter has
   `start`, `advance`, `fire`, `observe`, `addressOf` and `close`. It binds
   each intent as your modality sheet says, and it returns what the user
   perceives. It holds no expectations. `tools/adapters/web.mjs` is the
   model for a browser. `tools/adapters/terminal.mjs` is the model for a
   build with no accessibility tree.
6. Run `node tools/run.mjs --build <name> --out out/results-<name>.json`,
   then `node tools/closure.mjs --build <name>` and `node tools/trace.mjs`.
7. Have another person or an isolated agent write probes from the running
   build (`tools/probe-guide.md`), and keep them where implementers cannot
   read them. `node tools/isolate.mjs` runs an agent in a directory that
   holds only the files you name, with a canary test and a transcript audit.
8. Run the gate: `node tools/coldread.mjs seal`, then
   `node tools/coldread.mjs run --run 01`. Revise the package until every
   must-level probe is answered correctly by every gating reader.

Three parts are specific to Slate and need a change for another
application: the role selectors in the web adapter, the value shapes in
`tools/closure.mjs`, and the one-paragraph description for the control
reader in `tools/coldread.mjs`.
