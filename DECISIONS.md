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

## D-004 The fixture is data, and each build writes its own service double

`fixture/service.json` holds the latency of each operation, the faults and the
profiles. `fixture/vectors.json` holds timed calls and the correct replies.
The reference double is in `web/src/double/`. It is not part of the package.
A port writes its own double and must pass the vectors.

Reason: a port on an unrelated stack cannot run the reference double. Without
the vectors, a difference between two doubles looks like a specification fault.

## D-005 Fault profiles are chosen through the harness, not through the interface

The profiles `column-down`, `board-down`, `card-down` and `empty` give the
board its partial, error and empty states. An adapter names the profile at the
start. Slate has no control for it.

Reason: a control for faults is not part of the design under test.

## D-006 Slate design decisions

These are the deliberate decisions of the reference build. Several differ from
common convention on purpose. The specification must carry each of them.

Board:

- Card detail is a place with its own address, not a dialog.
- The text filter matches the title and the identifier, not the description.
  Each word must occur. Letter case is ignored.
- Label filters combine with "all". Assignee filters combine with "any".
- A filter change rewrites the current history entry.
- The text filter applies 250 ms after the last change. A commit applies it at
  once and, if exactly one card is left, focuses that card. It does not open it.
- A selected card that a filter hides leaves the selection.
- The pointer drag and its keyboard equivalent share one carry state. Nothing
  is saved before the drop.
- A carry to the next column keeps the position number. It does not go to the
  top or the end.
- With a filter, a dropped card goes directly after the visible card above it.
  At the visible top it goes to the absolute top of the column.
- The limit of a column counts hidden cards too. A drop into a full column is
  refused with a notice and no request.
- The notice for a save comes when the save succeeds, not at the user action.
- A notice has at most one action. A bulk move with a failed card offers
  "Retry" and no "Undo".
- An undo raises no notice.
- A notice lasts 8 s. Pointer and focus do not pause it. An error notice stays
  until the user answers it.
- Notices stay when the place changes. The selection does not.
- A delete is sent when its notice ends. "Undo" sends nothing. A reload during
  the notice brings the card back.
- A card that returns after a failed save goes to its old position number,
  counted in the column as it is then.
- A bulk move takes the cards in board order, puts them at the end of the
  target and stops at the limit. Cards that did not move stay selected.
- A bulk label removes the label if every selected card has it. If not, it
  adds the label where it is missing and where the card has fewer than 3.
- A card that saves a move cannot be picked up or deleted.
- Dismiss on the board has an order: carry, filter text, filter focus,
  selection.

Card:

- Opened from the board, the card shows at once from the data that the board
  holds. Only comments load.
- The title commits on Enter and when focus leaves the field. A bad title that
  loses focus is dropped without a message.
- The description commits only on its commit intent. Focus can leave the field
  and the draft stays.
- Labels show in the fixed board order, not the order added. The limit is 3.
- Comments show oldest first with absolute UTC times.
- While a comment is sent, the field is off. A failed comment puts its text
  back in the field and shows the message in place, not as a notice.
- "Delete card" has no confirmation. It goes up to the board and shows the
  notice there.
- Dismiss on the card place goes up to the board.
- The up-link goes Back if the card was opened from the board. If not, it adds
  an entry. A delete after a direct link replaces the entry.

Reason: the test needs decisions that an implementer would get wrong by guess.

## D-007 Identifier syntax

- A rule: three letters, a hyphen and a number (`CRY-1`). Numbers are never used again.
- A table: the area, `-T` and a number (`CRY-T1`). A row: the table and `.n` (`CRY-T1.2`).
- A state: `Region.State` (`Column.Loading.Slow`). A face item: the state and
  the item number (`Board.Ready.2d`).
- A scenario: `SCN-<AREA>-<n>`. A probe: `PRB-<n>`.

Reason: the report gives examples and leaves the syntax open. One fixed
pattern for each kind lets the parser and the lint find each identifier.

## D-008 Rule header line

Each rule has one header line before its EARS sentence: identifier, level,
capability, `origin:`, `sets:` and `overrides`. A table header has `decides:`
and `owns:`.

Reason: the trigger lint must know the state, the trigger and the regions
that a rule changes. EARS prose does not give the regions in a form that a
program can read.

## D-009 Intents and events are closed lists with fixed words

`spec/app.md` lists each intent with an identifier and a phrase, and each
event with a phrase. A rule names a trigger in the same words. A scenario
names an intent by its identifier.

Reason: the lint groups rules by trigger, and the adapters bind intents.

## D-010 Layout intent stays in the core

`spec/appearance.md` holds layout intent words. A modality sheet may replace
a word as a listed adaptation. FINDINGS counts the replaced words.

Reason: this is the moderator rule of the report, and the count is the
evidence that the report asks for.

## D-011 The matrix is a sidecar and is not normative

`sidecar/matrix.md` is an authoring worksheet. The port implementer gets it.
The lint does not read it.

Reason: the report puts the matrix outside the normative text.

## D-012 Timelines are in the fixture file

The timelines of the requests are in `fixture/fixture.md` (FIX-L1 to FIX-L9),
as in the worked example.

## D-013 Scenarios and probes use one grammar

The grammar is in `scenarios/README.md`. A step names an intent, a clock
advance or one observation. The address is asserted by its parts, so that a
scenario holds no written address. A scenario for one modality has a mark
such as `[web]`.

Reason: the core must hold no address, and one runner must run the same
scenario on each stack.

## D-014 Isolated roles drive the reference build through files

A sandboxed role cannot run a browser. It writes a request file with raw web
actions, and a helper outside the sandbox runs the request and writes the raw
observations (`tools/lib/raw-driver.mjs`). The helper has no intent layer and
no expectations.

Reason: the sandbox denies network and reads outside the work directory.

## D-015 What the lint treats as a conflict

The report says: fail two rules on one state and trigger with no table and no
"overrides" reference. It does not say when two states can hold at one time,
or how a table and a rule share a trigger. The lint uses these rules:

- Two scopes exclude each other if they are disjoint states of one region, or
  states of two places. A rule with no "While" applies in every state.
- Two rules that do not exclude each other and have one trigger fail, unless
  one overrides the other.
- Two tables on one trigger pass only if each owns something and they own
  different things.
- A rule and a table on one trigger pass if the table cites the rule, or the
  table owns something that the rule does not set.
- A rule that sets what a table owns fails, unless the table cites the rule.

"owns:" names an aspect (`arrival focus`, `card state`), not a whole region.
A table that only decides a trigger has `owns: -`.

Reason: with whole regions in "owns:", 130 rules failed, because many rules
set the focus or the notice in their own situation. The report does not say
how large an owned region is. FINDINGS reports this.

## D-016 A terminal build is observed on a pseudo-terminal, and its semantic dump is checked against the grid

The terminal adapter sends real key bytes, rebuilds the character grid with
its own interpreter, and reads roles, names, states and focus from a semantic
dump that the build writes. The adapter fails a check when a name, a state
mark or the cursor of the dump is not on the grid.

Reason: a terminal has no accessibility tree. A dump alone is self-report. A
grid alone has no roles.

## D-017 Probes have a raw form and a neutral form

The probe author writes raw web actions and raw observations, because the
closed intent list is part of the specification. A translator turns each probe
into the scenario grammar. A translation is accepted only if it passes on the
reference build.

## D-018 Text from isolated roles is kept as it came

`records/extraction-second/` and `probes/` hold text that an isolated role
wrote. Nobody edits it for style, and the markdown lint does not read it.
