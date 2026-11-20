# Findings

This file reports the first end-to-end test of the consensus specification
format: one application (Slate), one reference build, one specification
package, one port to an unrelated stack from the text alone, and one control
port from the inventory alone.

## Summary

The port worked. An agent that saw only the package built a terminal version
of Slate that gives the reference verdict on 107 of 108 must-level
identifiers, with the last one inapplicable under a listed adaptation. It
passes 42 of 43 applicable held-out probes. A control port that had the
inventory but no rules passes 11 of 43.

The format carried the design. The machinery around it is the weak part. Most
gate failures came from my harness, not from the text. The lint needed
choices that the report does not make. A stack with no accessibility tree
needs the implementer to write half of the adapter. One real defect in the
port passed every public scenario and was found only by a held-out probe.

Read every number with these limits: one application, one port, one model
vendor for the author, the readers, the implementers and the grader, and a
probe set that the readers answered at the ceiling.

## The numbers

### Verdict agreement on must-level rules

The package has 108 must-level identifiers (rules, tables, data rules,
properties, tasks). An identifier has the verdict of the public scenarios that
verify it. All runs use the fixture and the controlled clock.

| Build | Same verdict as the reference | Failed | Inapplicable |
| --- | --- | --- | --- |
| Reference (web) | 108 | 0 | 0 |
| Terminal port | 107 | 0 | 1 |
| Control port (inventory only) | 19 | 88 | 1 |

A second pass on the port with real-time pauses after each step gives the
same result, so the port reads no real time.

The control number is coarse. One scenario verifies several identifiers, and
one failed step fails all of them. The scenario counts are the fairer measure:
the port passes 45 of 45 applicable public scenarios and the control port
passes 13.

### Rules made inapplicable

| Rule or check | Why | Listed adaptation |
| --- | --- | --- |
| CRY-3 (carry to a position with the pointer) | A terminal has no pointer | Yes: TRM-A1. The carry by keys reaches each position |
| SCN-CRY-3 (the pointer scenario) | Same | Yes: TRM-A1, TRM-A2 |
| SCN-NAV-4 (written web addresses) | It holds web address forms | Its identifiers are verified by SCN-NAV-9 with terminal forms |

Rules made inapplicable with a listed adaptation: 1. Without one: 0.

Layout-intent words that the terminal sheet had to replace: 2 ("centered
column with a maximum width" and "the row scrolls sideways", TRM-A7). The
other words (pinned, stack, row of columns of equal width, at the start side,
above the content) held as they were.

### Tasks

| Task | Steps | Reference | Port | Control port |
| --- | --- | --- | --- | --- |
| TSK-1 Find a card and open it | 4 | outcome reached | outcome reached | not reached |
| TSK-2 Move a card and take it back | 4 | outcome reached | outcome reached | not reached |
| TSK-3 Move three cards at once | 5 | outcome reached | outcome reached | not reached |
| TSK-4 Rename a card | 3 | outcome reached | outcome reached | not reached |
| TSK-5 Add a comment | 2 | outcome reached | outcome reached | not reached |
| TSK-6 Delete a card and take it back | 2 | outcome reached | outcome reached | not reached |
| TSK-7 Narrow the board and widen it again | 3 | outcome reached | outcome reached | not reached |

One step is one intent. The step counts are the same on the port, and the
terminal sheet lists no changed count. The number of key presses differs
(Tab to a control, then Enter), and this test did not count key presses.

### Held-out probes

52 probes: 39 open, 13 sealed. 45 have a neutral form that runs on each
stack. Seven are specific to the web sheet (five check the window title, one
the Tab order, one a platform default inside a field).

| Group | Probes with a neutral form | Port passes | Control port passes | Inapplicable (pointer) |
| --- | --- | --- | --- | --- |
| Burned (caused a specification change) | 1 | 1 | 0 | 0 |
| Open, not burned | 32 | 29 of 30 | 6 of 30 | 2 |
| Sealed (never seen by the author before the end) | 12 | 12 of 12 | 5 of 12 | 0 |

The sealed group is the cleanest evidence. The author never saw those probes,
no revision could fit them, and the port passes all 12.

Before two adapter and grammar fixes, the port passed 10 of 12 sealed probes.
Both failures were faults of my tooling, described below.

### The cold read

| Set | Probes | Opus | Sonnet | Haiku | qwen3.6 (not gating) | Controls with no specification |
| --- | --- | --- | --- | --- | --- | --- |
| Open, run 03 (accepted) | 39 | 39 | 39 | 39 | 23 | 11 to 20 |
| Sealed, one run | 13 | 13 | 13 | 13 | 8.5 | 3 to 4 |

The text carries 19 to 28 of 39 open decisions that convention does not, and
9 to 10 of 13 sealed ones. `gate/README.md` has every run.

### Extraction

| Measure | Value |
| --- | --- |
| Statements of the second extraction that agree with the first | 114 of 138 |
| Decisions that the first extraction missed | 15 |
| Contradictions between the two | 7 (the build sided with the second extraction in 5) |
| Accidents in the reference build found by extraction and removed | 10 |

One author's extraction was wrong or silent on 22 points. The double
extraction earned its cost.

### Cost

No person reviewed anything in this test, so there is no review time to
report. That is a gap in the evidence: the report's question about authoring
and review cost for people is still open.

| Step | Wall clock | Notes |
| --- | --- | --- |
| Whole test, first commit to this file | about 3.3 hours | One agent session with isolated runs |
| Reference build with fixture and tests | about 40 minutes | About 2,000 lines |
| Specification package and scenarios | about 40 minutes | About 16,500 words, 47 scenarios |
| Tooling | in parallel with the above | About 3,100 lines, more than the application |
| Second extraction (Sonnet 5.5) | 14 minutes | About 2 USD as the CLI reports it |
| Probe author (Opus 5.5) | 13 minutes | About 3.5 USD |
| Gate: 4 cold reads | about 8 minutes each | 7 reader calls and 7 grader calls each |
| Terminal port (Opus 5.5) | 36 minutes | About 3,000 lines of Python |
| Control port (Opus 5.5) | 22 minutes | About 2,700 lines |

The tooling is larger than the application. For one small application the
machinery does not pay for itself. It is reusable; see the README.

## Each mismatch, classified

### On the port

| Mismatch | Found by | Class |
| --- | --- | --- |
| After a drop into a full column is refused, the port counts the card twice ("4 cards", "28 cards") | Probe PRB-022 | Defect of the port. CRY-T1.2 and DAT-2 are clear. No public scenario checks a count after a refused drop, so the defect passed all of them |
| A card name was not found on the grid when a mark stood between identifier and title | First scenario run | Fault of the adapter (fix 1). TRM-14 allows the layout |
| A probe looked for a card title as a text | Sealed probe PRB-012 | Fault of the adapter (fix 2). The web adapter gave titles as texts and the terminal adapter did not |
| A probe entered a web address on the terminal build | Sealed probe PRB-052 | Gap of the scenario grammar. It had no way to name an entered address by its parts |
| Commit of a description with Control+S, not Control+Enter | Sheet | Permitted idiom (TRM-A5) |
| Titles cut with "…" | Sheet | Permitted idiom (TRM-A4) |
| The columns scroll as one area; Card does not scroll | Sheet | Permitted idiom (TRM-A3) |

### In the text, from the port implementer's notes

The implementer wrote down 30 choices and 5 disagreements (`tui/NOTES.md`).
These are the ones that matter:

| Point | Class |
| --- | --- |
| TRM-7 puts the cursor at the first cell of the focused part; TRM-A6 puts it at the end of the draft | Unclear wording: two sheet entries disagree |
| TTL-3 says "Slate shall not move the focus"; the binding of leave-title is Tab, which moves it | Unclear wording |
| NAV-T1.1 "focus is not moved" after a reload, against FOC-1 for a removed part | Unclear wording |
| DIS-T1 rows 6 and 7: which wins with focus in the comment field while a description edit is open | Unclear wording. The table order decides it, and a scenario confirms it, but the note under the table does not say it |
| TRM-H5 lists cards in "parts" and in "cards", and does not say what to do with a part that is scrolled out of view | Gap in the harness binding |
| What a "Move selected to" action does for a column that is not loaded | Gap. The implementer disabled it. The reference build does not |
| What happens when a save with no fault in the fixture fails | Gap, known. No check can decide it |
| A read from the terminal that holds two keys | Gap in the harness binding |

No rule was misread in a way that a scenario or probe caught, other than the
count defect.

### What the control port got wrong

The control port shows what the rules add to the inventory. It had every
string of every face. It lacked the behavior:

- The filter applied only on commit, labels combined with "any", and the count
  line read "Showing 5 of 27 cards".
- It invented notice texts ("Moved SL-103 back to Backlog." after an undo) and
  gave bulk label an "Undo".
- A delete was sent at once.
- A failed title save went back to the edit.
- Focus after a delete, a dismiss and an undo went to other parts.
- A failed comments load was sent again on each visit.

One leak: the control port used 8000 ms for a notice. That number is in
`spec/conventions.md`, in a line that I added during the gate. The control
got a behavior from a file that should hold only notation.

## Where the format was ambiguous or awkward to apply

### The trigger lint needs decisions that the report does not make

- The report says to fail two rules on one state and trigger. It does not say
  when two states can hold at one time. Slate has regions that are active
  together (Carry, Selection, Filter, Notice). I had to define when two scopes
  exclude each other (D-015).
- "A rule that sets a region that a table owns": with whole regions in
  "owns", 130 rules failed on the first run, because many rules set the focus
  or the notice in their own situation. I changed "owns" to name a narrow
  aspect. After that the third lint rule finds almost nothing. As written, it
  is either too strict to use or too loose to help.
- The lint cannot read which regions a rule changes from EARS prose. Each
  rule needs a header line with "sets:" (D-008). That is one more thing to
  keep true by hand.
- The lint did not find the one real conflict of wording that a reader found
  (FLT-8 "shall not move the focus" against FLT-3). The two rules have
  different triggers, and one calls the other.

### EARS needs two closed lists that the report does not name

"When" takes an intent from a closed list. Slate also needs triggers that are
not user intents: a reply, a failure, a timer, a notice that ends. I added a
closed list of events. Without it, a third of the rules have no trigger that
a lint can check.

### "An identifier with no check" drives the fixture

MOV-4 (a failed undo) could not happen on the first fixture. The lint was
right to fail it. The only fix was a new fault in the fixture. Three saves
(description, labels, assignee) have no fault at all, so their failure
behavior has no rule. The fixture decides what the specification can say.

### The fixture had to be written twice

The service double is part of the fixture, but a port on another stack cannot
run it. I made the fixture data (a latency and fault table, and vectors of
timed calls). Each build writes its own double and must pass the vectors.
This worked: both terminal builds passed all 14 vectors, and no mismatch came
from the double. The report should say this.

### A stack with no accessibility tree

The report says "the character grid plus a semantic dump". The dump must come
from the build, so the implementer writes half of the adapter. I checked each
name, state mark and the cursor against a grid that the adapter rebuilds from
real terminal output. That check caught nothing false on the port. Limits:

- The dump schema is long (TRM-H5) and is the most stack-specific text in the
  package.
- The dump does not expose the texts inside a card item (assignee, comment
  count), so a scenario cannot check them on the terminal. One scenario passed
  for a weak reason: it looked for "Unassigned" and found the filter toggle.
- The sandbox does not allow a pseudo-terminal, so the implementer could not
  test raw mode. It worked on the first try outside the sandbox.

### Scenarios and probes

- A scenario must not name a state, and a text check is exact. Both are good
  rules. But a check for "one part has this text" is weak when two parts have
  the same text.
- The grammar had no stack-neutral form for an entered address, and none for a
  window title or a Tab order. Seven probes had no neutral form.
- The frame rule ("nothing else changed") has no check. I planned a step for
  it and dropped it. The closure check covers texts only: 218 texts on the
  reference, 0 outside the inventory.
- A verdict belongs to a scenario, not to an identifier. A scenario that
  verifies eight identifiers gives all eight one verdict.

### The gate

- Ten probe blocks in three runs. Eight were faults of the harness: the
  readers did not get the fixture data file, the grader marked down facts that
  the question did not ask for, and a reader left a question out. One was a
  reader slip. One led to a change of a rule.
- The grader is a model. It gave different grades to the same answer in
  different runs.
- Both probe sets are at the ceiling for the specification readers. The gate
  shows that the text carries the decisions. It cannot say which parts of the
  format did the work.
- The readers listed 13 ambiguities in the accepted version. Three are real
  conflicts of wording (`gate/ambiguities.md`). The gate passed with them
  open, because no probe asked about them.
- The probe author marked 50 of 52 probes must-level. The level means little
  when the author has no rule levels to follow.
- The reader instruction and the convention line on timers were changed
  during the gate. Changes to the instrument and to the text are mixed in the
  same runs.

### What text did not carry

- The pointer: where exactly a card lands when the pointer is at the middle
  of another card (AMB-1). The readers all flagged it.
- Focus after a pointer click on a control that then goes away (AMB-2,
  AMB-11). It depends on a platform default.
- Appearance: every VIS commitment is "should", has no automated check, and is
  inapplicable on the terminal. This test says nothing about look.

## The weakest parts of the format

1. Region ownership and the third lint rule. The idea does not fit an
   application with regions that are active at one time.
2. The observation contract for a stack with no accessibility tree. It is
   long, written for one stack, and partly self-report.
3. The acceptance gate as an instrument. It is sensitive to what the readers
   are given and to the grader, and it is at the ceiling.
4. The link between the fixture and what can be specified. A behavior that
   the fixture cannot cause has no rule and no check.
5. Public scenarios as the only source of verdicts. The port implementer used
   them as tests, so the port passes all of them. The one defect that mattered
   was outside them. Only the held-out probes found it.
6. The size of the machinery next to a small application.

## What this test does not show

- One port by one model. Agreement between two builds from one vendor can
  come from shared defaults. The control port is the guard, and it scored far
  lower, but it is one build.
- No person wrote, read or reviewed anything. Cost for people is not measured.
- Appearance, motion and pointer feel are not tested.
- The reference build was written by the specification author for this test,
  with deliberate decisions. A grown application has more accidents.
- No change request was run. The report's questions about maintenance are
  open.

## Deviations from the plan, stated plainly

- The control port run has one flagged read outside its directory: its own
  session task folder. The sandbox denied it and nothing was read. My rule
  said that one hit voids a run. I kept the run. The record is in
  `records/isolation/control-port-01/run.json`.
- I saw the questions and the readers' answers of the open probes during the
  gate, and four grader notes that quote parts of a key. I did not open the
  key files or the sealed set before the final run.
- One public scenario (SCN-NAV-9, terminal address forms) and one grammar
  step were added after the port was delivered. Neither was given to the
  implementer.
- The terminal adapter was changed two times after the freeze. Neither change
  touches an expectation about Slate.
- One commit was made before its check had passed (a file was not
  formatted). The next commit fixed it before anything was pushed.
- No probe was edited. No probe was wrong on the reference build.
- qwen3.6 gave no answer in run 01 (a time limit) and is not a gating reader.
  All gating readers are from one vendor.
