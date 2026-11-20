# How to write a probe

A probe is one held-out question about what a user of Slate perceives in one
situation, with the answer taken from the running application. Readers who
have never seen the application answer the question from a written
specification. A second build is checked against the same probe.

You write probes from the running application and its source. You have not
seen the specification, and you must not try to guess its wording.

## What makes a good probe

- It asks about one decision that a competent implementer could get wrong: an
  order, a position, a count, a string, where focus goes, what the address
  and the history do, when a request is sent, what a timer does on each side
  of its limit, what survives Back, Forward, a reload or a direct address.
- The situation is exact and can be repeated: a fixture profile, a start
  address, and a list of raw actions with clock advances.
- The answer is one observable fact, not an opinion.
- You have run it. The checks pass on the running application.

Cover all of these areas, with no more than 8 probes in one area: board
loading and failures; filter; focus and keys on the board; selection and bulk
actions; moving a card by keys and by pointer; save failures, rollback and
retry; delete and undo; the notice; the card place (title, labels, assignee,
description); comments; navigation, history, reload and unknown addresses.

## Level

- `must`: a wrong answer can block or mislead a user (data in the wrong
  place, a lost edit, a wrong message, lost focus, a wrong history step).
- `should`: the rest (wording of a quiet text, an announcement).

## File format

Write one file for each probe: `probes/PRB-001.json`, `probes/PRB-002.json`, ...

```json
{
  "id": "PRB-001",
  "level": "must",
  "area": "delete",
  "situation": [
    "Start at the board with the default data and wait until every column is loaded.",
    "Put focus on card SL-101 and press Delete."
  ],
  "question": "Which part has focus now, and is a request sent to the service at this moment?",
  "answer": "Focus is on card SL-102, the next card in the column. No delete request is sent yet.",
  "conventional": false,
  "request": {
    "profile": "default",
    "start": "#/",
    "steps": [
      { "advance": 2200 },
      { "focus": { "card": "SL-101" } },
      { "key": "Delete" }
    ]
  },
  "checks": [
    { "focus": { "role": "group", "name": "SL-102 Fix login redirect loop" } },
    { "requests": { "op": "deleteCard", "count": 0 } }
  ]
}
```

- `situation`: plain sentences that a reader can follow. Say what the user
  does (keys, pointer, text typed) and how long the clock runs. Do not say
  what happens.
- `question`: asks what the user perceives at the end.
- `answer`: the key. Short and exact. Quote strings exactly.
- `conventional`: true if you think most applications behave this way.
- `request`: a request for the raw driver (`driver-guide.md`).
- `checks`: facts about the observation after the last step. Each must hold.

| Check | Holds when |
| --- | --- |
| `{ "focus": { "role": "...", "name": "..." } }` | the focus has that role and name (as the driver reports them) |
| `{ "focus": null }` | no part has focus |
| `{ "address": "#/?q=x" }` | the address is exactly this |
| `{ "historyDelta": 1 }` | the history length is the start length plus this number |
| `{ "windowTitle": "..." }` | the window title is exactly this |
| `{ "screenHas": "text" }` | the accessibility tree text contains this |
| `{ "screenLacks": "text" }` | the accessibility tree text does not contain this |
| `{ "requests": { "op": "moveCards", "count": 1 } }` | the request log has that many requests of the operation |
| `{ "announced": "text" }` | an announcement since the start is exactly this |
| `{ "order": { "column": "Ready", "cards": ["SL-111", "SL-112"] } }` | the column shows exactly these cards from the top |

## Check your probes

Run this in your work directory. It runs every probe through the driver and
prints the checks that do not hold.

```sh
/opt/homebrew/bin/python3 check_probes.py
```

Fix a probe until it passes. A probe that does not pass is dropped.
