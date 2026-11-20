# Decisions

Each entry records a choice on a point that the report leaves open, or a
choice about how this repository does the work. Each entry has a reason.

## D-001 The two source documents stay unchanged

The files in `docs/` are the content of the `<report>` and `<worked_example>`
blocks of the task text, extracted with `awk` and compared with `cmp`. Nobody
edits them. They win over all other text in this repository.

Reason: they define the format under test.

## D-002 Stacks and dependencies

- Reference build: JavaScript with ES modules, no framework, no build step.
- Tooling: Node built-in modules. One development dependency, `playwright`
  1.65.0, for the web adapter.
- Terminal port: Python standard library only.
- Gates: `markdownlint-cli2`, `deno lint`, `deno fmt --check`, `node --test`,
  `ty`, `python3 -m unittest`.

Reason: the owner wants few dependencies and standard command-line tools. A
Python terminal build shares no language and no rendering model with the
reference build.

## D-003 No JavaScript type check

Reason: a type check needs one more dependency. The pure core has unit tests.
