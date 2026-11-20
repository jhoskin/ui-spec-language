# Acceptance gate record

The gate has two steps: the trigger lint, and a cold read of the open probe
set (39 probes, all must-level) by readers who have only the specification
package. A control reader on each model has no specification. A version
passes when every gating reader answers every must-level probe correctly.

Readers: Claude Opus 5.5, Sonnet 5.5 and Haiku 5.5 gate. A local qwen3.6
answers and does not gate. Every reader runs with no tools. All three gating
readers come from one vendor.

## Runs

| Run | Lint failures | Opus | Sonnet | Haiku | qwen | Control Opus | Control Sonnet | Control Haiku | Blocked probes | Result |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 01 | 0 | 37.5 | 37 | 35 | no answer | 15.5 | 18 | 7 | 8 | blocked |
| 02 | 0 | 38 | 38 | 39 | 26.5 | 18 | 18 | 10.5 | 2 | blocked |
| 03 | 0 | 39 | 39 | 39 | 23 | 20 | 18 | 11 | 0 | pass |

Scores are out of 39. The probe bank did not change between runs (hash
`508142991fb0` in each `meta.json`). The package hash of each run is in its
`meta.json`.

| Run | Guesses (Opus, Sonnet, Haiku) | Ambiguities listed | Contradictions listed |
| --- | --- | --- | --- |
| 01 | 2, 1, 2 | 5, 6, 6 | 0, 2, 2 |
| 02 | 0, 0, 0 | 4, 5, 6 | 1, 0, 2 |
| 03 | 0, 0, 0 | 3, 7, 7 | 0, 0, 4 |

## What blocked each run, and what changed

Run 01, 8 probes:

- 3 probes needed card data. The harness did not give the readers
  `fixture/data.json`, which is part of the package. Harness fault. Fixed.
- 4 probes had a full answer from Haiku that the grader marked down for
  leaving out the "Dismiss" action, which the question did not ask about. The
  grader now grades only the facts that the question asks for, and the reader
  is told to name each action of a notice. Harness fault. Fixed.
- 1 probe had a history answer in other words than the key. The reader is now
  told to give a history change as a number of entries. Harness fault. Fixed.
- qwen gave no answer: the call ran into a time limit. The harness now reads
  its reply as a stream.
- Specification changes from the ambiguity lists: a line on a timer that is
  due exactly at a clock time; TSK-4 wording; a note that Title.Editing always
  has focus in its field; a platform default for the undo chord in a field.

Run 02, 2 probes:

- Opus left one question out. The harness now asks a reader again for the
  questions that it left out. Harness fault. Fixed.
- Sonnet put a card that came back after a failed move at the wrong place
  ("position 7", but between the wrong neighbours). MOV-2 got an example with
  the fixture values. Specification change.

Run 03: pass. Four answers were compared by hand with the reference build
(PRB-003, PRB-021, PRB-031, PRB-044). The three readers agree on each, and
each is what the reference build does.

## What the numbers say

- The specification readers score 39 of 39. The control readers score 11 to
  20 of 39. The gain over the control is 19 to 28 probes, which is more than
  half of the probe count for two of three models.
- The control readers answer 11 to 20 probes correctly from convention alone.
  The probe author marked 10 of the 39 as conventional.
- Only one of the ten blocks led to a change of a rule. Eight were
  faults of the harness and one was a reader slip. The gate measured the instrument as much as the text.
- The grader is a model. Its grades for one and the same answer differed
  between runs. Each grade below 1 was read by hand.

## Open ambiguities

`ambiguities.md` lists each ambiguity and contradiction that a reader named in
run 03, with a decision: closed in the text, or logged with a reason.
