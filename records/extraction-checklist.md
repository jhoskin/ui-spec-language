# Forgotten-state checklist

Extraction step 5, applied to the reference build. Each line names where the
specification covers the item, or says that the item does not exist.

## Each place: ideal, loading, empty, partial, error

| Place | Ideal | Loading | Empty | Partial | Error |
| --- | --- | --- | --- | --- | --- |
| Board | Board.Ready, Column.Cards | Board.Loading; Column.Loading.Fresh and Slow | profile `empty`: board line; Column.Empty; Column.NoMatch; board line for no match | one Column.Failed among loaded columns (profile `column-down`) | Board.Failed (profile `board-down`) |
| Card | Card.Ready, Comments.Some | Card.Loading; Comments.Loading | Comments.None; "No description" | Comments.Failed with the card shown | Card.Failed (profile `card-down`) |
| Missing | Missing.Page, Missing.Card | none | none | none | none |

## Each request: slow, failed, retried, abandoned, late

| Request | Slow | Failed | Retried | Abandoned | Late |
| --- | --- | --- | --- | --- | --- |
| loadBoard | no slow mark | BRD-2 | BRD-3 | never (FIX-19) | reply on Card: CRD-T1 applies again |
| loadColumn | COL-1 at 1000 ms | COL-2 | COL-3 | never | reply on Card changes the data |
| loadCard | no slow mark | CRD-T1.2 | CRD-2 | never | CRD-1 |
| loadComments | no slow mark | CRD-3 | CRD-4 | never | reply after go up changes the data |
| moveCards | no slow mark | MOV-2, BLK-T2.1, MOV-4 | "Retry" | never | notice shows in any place |
| saveTitle | no slow mark | TTL-4 | "Retry" | never | notice shows in any place |
| addComment | no slow mark | CMT-T1 | the user commits again | never | CMT-T1.2 |
| deleteCard | no slow mark | DEL-4 | "Retry" | never; a reload before the request sends nothing | notice shows in any place |
| saveDescription, saveLabels, saveAssignee | no slow mark | no fault in the fixture; no rule | none | never | SAV-1 |

## Each region under step, Back, Forward, reload and direct address

MEM-T1 has one row for each region that holds state.

## Every key in every focus context

The bindings are in WEB-4 with a context for each. Keys with no binding in a
context keep the platform default. Checked in the probe log: Tab order,
Escape in each field, Escape on a card, Escape with focus on the page, Enter
and Space on a card with and without a carry, the undo chord in and outside a
field.

## Each limit at 0, 1, the limit and the limit plus 1

| Limit | 0 | 1 | At the limit | Limit plus 1 |
| --- | --- | --- | --- | --- |
| Labels on a card (3) | "no labels" shows nothing | one label | Labels.Full, LBL-1 | toggle is disabled; BLK-T3.3 and BLK-4 for bulk |
| Cards in In progress (3) | not reached in the fixture | not reached | DAT-7, CRY-T1.2, BLK-T1.2 | refused; BLK-T2.2 for a partial bulk move |
| Title length (80) | TTL-T1.1 | good | good | TTL-T1.2 |
| Count words | "0 cards", "No comments yet" | "1 card", "1 comment" | none | none |
| Selection | Selection.None | "1 selected" | no limit | none |

## Each timer on both sides of its threshold

| Timer | Before | At |
| --- | --- | --- |
| Filter delay, 250 ms | SCN-FLT-1 at 249 ms: not applied | at 250 ms: applied |
| Notice time, 8 s | SCN-CRY-5 at 7999 ms: shown | at 8000 ms: ended |
| Slow mark, 1000 ms | SCN-BRD-1 at 999 ms: no text | at 1000 ms: "Still loading…" |
| Delete request | SCN-DEL-1 at 7999 ms: no request | at 8000 ms: request |

## Accidents found and removed

The probe of the running build (records/extraction-probe-log.md) found
behavior that was not intended. Each was fixed in the reference build before
the specification was written.

- A pointer press on a card gave it focus but did not make it the focus stop.
- A pointer click on the toggle of a card left focus on the toggle, so card
  keys did not work.
- The scroll position of an entry was saved late, so a fast open and Back
  restored an older position.
- Dismiss with an open description edit and focus outside the field went up
  and dropped the draft. It now cancels the edit (DIS-T1.6).
- Dismiss on Missing.Card went up. It now does nothing (DIS-T1.9).
