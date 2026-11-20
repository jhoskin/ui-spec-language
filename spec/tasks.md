# Tasks

A task is a user goal with a start state, steps, an outcome and a step count.
One step is one user intention. A task does not replace a must-level rule.

```text
TSK-1 Find a card and open it. Start: Board.Ready, no filter, all columns loaded.
  Steps: ask for the filter; enter "webhook"; commit; open the card that has focus.  Count: 4
  Outcome: Card shows SL-112 "Document the webhook API" in a new history entry. One Back
  shows Board with filter text "webhook" and focus on SL-112.
TSK-2 Move a card and take it back. Start: Board.Ready, focus on SL-103.
  Steps: pick up; carry right; drop; undo, after the notice shows.  Count: 4
  Outcome: SL-103 is at position 3 of Backlog. No notice shows.
TSK-3 Move three cards at once. Start: Board.Ready, no selection.
  Steps: select SL-106; select SL-107; select SL-108; move the selected cards to Review;
  retry, after the notice shows.  Count: 5
  Outcome: Review is SL-106, SL-108, SL-107. Notice "Moved 1 card to Review."
TSK-4 Rename a card. Start: Card.Ready for SL-105.
  Steps: edit the title; enter "Write the onboarding guide"; commit.  Count: 3
  Outcome: the place title is "Write the onboarding guide". Mark "Saving…" goes after 400 ms.
TSK-5 Add a comment. Start: Card.Ready for SL-101, Comments.None.
  Steps: enter "Looks fine."; commit.  Count: 2
  Outcome: "1 comment"; the comment shows "Mika Ito" and the time of the reply.
TSK-6 Delete a card and take it back. Start: Board.Ready, focus on SL-101.
  Steps: delete; undo.  Count: 2
  Outcome: SL-101 is at position 1 of Backlog and has focus. No delete request was sent.
TSK-7 Narrow the board and widen it again. Start: Board.Ready, no filter.
  Steps: toggle label filter bug; toggle assignee filter Ana Ruiz; clear the filters.  Count: 3
  Outcome: "27 cards"; focus in the filter field; the address is Board with no filter; the
  history depth did not change.
```
