# Scenarios: board loading

```text
SCN-BRD-1 verifies BRD-1, COL-1, COL-4, COL-5, DAT-2, DAT-3, DAT-1, PRP-3
Given start at board.
Then place title "Board".
Then no text "Backlog".
After 400 ms.
Then text "Loading cards…" is shown.
Then column "Backlog" cards none.
After 300 ms.
Then column "Backlog" starts SL-101, SL-102, SL-103.
Then text "10 cards" is shown.
Then text "No cards" is shown.
Then text "0 cards" is shown.
Then text "Limit 3" is shown.
After 699 ms.
Then no text "Still loading…".
After 1 ms.
Then text "Still loading…" is shown.
After 800 ms.
Then no text "Still loading…".
Then text "27 cards" is shown.
Then announcement "27 cards".

SCN-BRD-2 verifies BRD-2, BRD-3, PRP-2
Given profile board-down.
Given start at board.
After 400 ms.
Then text "Couldn't load the board." is shown.
After 5000 ms.
Then requests loadBoard 1.
When retry-place.
After 400 ms.
Then no text "Couldn't load the board.".
Then requests loadBoard 2.

SCN-BRD-3 verifies COL-2, COL-3, DAT-2, PRP-2
Given profile column-down.
Given start at board.
After 2200 ms.
Then text "Couldn't load Ready." is shown.
Then text "20 cards" is shown.
Then column "Backlog" starts SL-101.
Then requests loadColumn 5.
When retry-column Ready.
Then no text "Couldn't load Ready.".
After 300 ms.
Then text "27 cards" is shown.
Then requests loadColumn 6.

SCN-BRD-4 verifies DAT-1, DAT-2
Given profile empty.
Given start at board.
After 2200 ms.
Then text "This board has no cards yet." is shown.
Then text "0 cards" is shown.
Then action "Select all in Backlog" is absent.
```
