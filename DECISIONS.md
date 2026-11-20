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
