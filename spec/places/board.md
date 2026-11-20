# Board

The board shows every card in its column. It has a filter bar, a selection
with bulk actions, and a carry state for moves.

## States

```text
Board      States: Loading | Failed | Ready
Column     States: Loading (Fresh | Slow) | Failed | Empty | NoMatch | Cards
Filter     States: Off | On
Selection  States: None | Some
Carry      States: Idle | Carrying
```

There is one Column region for each column. Filter is On when a text, a label
or an assignee filter is applied. Column.Empty has no cards. Column.NoMatch has
cards, and the filter hides all of them.

## Faces

```text
Board.Loading face
  1 r1 P place title "Board"
  2 r2 Q three placeholder columns

Board.Failed face
  1 r1 P place title "Board"
  2 r2 N alert "Couldn't load the board."
  3 r3 N action "Try again"

Board.Ready face
  1 r2 N place title "Board"
  2 r3 N filter bar, pinned:
      a r1 N field, name "Filter cards"
      b r2 N group "Labels": one toggle for each label, in board order (FIX-3)
      c r3 N group "Assignee": one toggle for each person in order (FIX-2), then "Unassigned"
      d r5 N action "Clear filters", while Filter.On or the field has text
      e r4 Q status line: the count line (DAT-2)
  3 r4 N selection bar, in Selection.Some only:
      a r1 N text "3 selected"
      b r2 N group "Move selected to": one action for each column, with the column name
      c r3 N group "Label selected": one toggle for each label; on if every selected card has
             the label, mixed if some have it, off if none has it
      d r4 N action "Clear selection"
  4 r1 P the columns in order (FIX-1)
  5 r5 N board line, when every column has answered:
      a if no column has a card: text "This board has no cards yet."
      b if Filter.On, there are cards and none is visible: text "No cards match these filters."
        and action "Show all cards"

Column face, in every state
  1 r1 N heading: the column name
  2 r3 Q the column count (DAT-3), in Empty, NoMatch and Cards only
  3 r4 Q text "Limit 3", if the column has a limit
  4 r5 N action "Select all", name "Select all in Backlog", in Cards only
  5 r2 P the body, by state:
      Loading.Fresh  three placeholder cards
      Loading.Slow   three placeholder cards, then Q text "Still loading…"
      Failed         alert "Couldn't load Ready.", then action "Retry", name "Retry Ready"
      Empty          Q text "No cards"
      NoMatch        Q text "No matching cards"
      Cards          the visible cards from the top

Card item face (a card in a column; name "SL-101 Export board as CSV")
  a r5 N toggle, name "Select SL-101"; on while the card is selected
  b r3 Q the identifier "SL-101"
  c r1 P the title, a link to the card
  d r4 N the labels of the card, in board order
  e r2 Q the name of the assignee, or "Unassigned"
  f r6 Q the comment count (DAT-14); absent at 0
  g r7 Q mark "Moving", while the card is carried
  h r7 Q mark "Saving…", while a move save of the card has no reply
```

## Loading

```text
BRD-1 [must] origin: extracted  sets: Board, Column
  While Board.Loading, when the board load succeeds, Slate shall show Board.Ready with each
  column in Column.Loading.Fresh, and request each column that has no request yet.
BRD-2 [must] origin: extracted  sets: Board
  If the board load fails, then Slate shall show Board.Failed.
BRD-3 [must] origin: extracted  sets: Board
  While Board.Failed, when the user retries the place, Slate shall show Board.Loading and
  request the board again.
COL-1 [must] origin: extracted  sets: Column
  While Column.Loading.Fresh, when a column load is slow, Slate shall show Column.Loading.Slow.
  A column load is slow 1000 ms after its request, if no reply came.
COL-2 [must] origin: extracted  sets: Column
  If a column load fails, then Slate shall show Column.Failed for that column. The other
  columns do not change.
COL-3 [must] origin: extracted  sets: Column
  While Column.Failed, when the user retries a column, Slate shall show Column.Loading.Fresh
  and request the column again.
COL-4 [must] origin: extracted  sets: Column
  When a column load succeeds, Slate shall show the cards of the column in the order of the
  reply. A card that the session holds keeps its session values. A card that has a delete
  that waits or was sent is not shown.
COL-5 [should] origin: extracted  sets: announcement
  When the last column answers, Slate shall announce the count line. The last column answers
  when a column load succeeds, no column is in Column.Loading and Board is shown. A load that
  fails announces nothing.
```

The board data and the columns are requested one time in a session. A column
is requested when Board is first shown, not when Card is shown.

## Filter

```text
FLT-1 [must] origin: extracted  sets: Filter
  While Board.Ready, when the user changes the filter text, Slate shall show or remove
  "Clear filters" at once and start the filter delay again. The filter delay ends 250 ms after
  the last change.
FLT-2 [must] origin: extracted  sets: Filter
  While Board.Ready, when the filter delay ends, Slate shall apply the filter.
FLT-3 [must] origin: extracted  sets: Filter, focus
  While Board.Ready, when the user commits the filter, Slate shall apply the filter at once.
  If exactly one card is visible after that, Slate shall focus that card and make it the focus
  stop. Slate shall not open it.
FLT-4 [must] origin: extracted  sets: Filter
  While Board.Ready, when the user toggles a label filter, Slate shall change that toggle and
  apply the filter at once, with the text that the field has.
FLT-5 [must] origin: extracted  sets: Filter
  While Board.Ready, when the user toggles an assignee filter, Slate shall change that toggle
  and apply the filter at once, with the text that the field has.
FLT-6 [must] origin: extracted  sets: Filter, focus
  While Board.Ready, when the user clears the filters, Slate shall empty the field, set every
  filter toggle to off, apply the filter at once and focus the filter field. The actions
  "Clear filters" and "Show all cards" are this intent.
FLT-7 [should] origin: extracted  sets: focus
  While Board.Ready, when the user asks for the filter, Slate shall focus the filter field,
  unless Carry.Carrying.
FLT-8 [must] origin: extracted  sets: Filter, Column, Selection, Carry, address, announcement
  When the filter applies, Slate shall take the text of the field (DAT-4) and the toggles that
  are on, show only the cards that match (DAT-5), rewrite the current history entry to the
  address of the board with that filter, cancel a carry, remove each hidden card from the
  selection, and announce the count line. Slate shall not move the focus.
```

## Focus on cards

```text
FCS-1 [must] origin: extracted  sets: focus
  While Board.Ready, Slate shall keep the visible cards as one focus stop: the card that had
  focus last, or, if that card is not visible, the first visible card in board order.
FCS-2 [must] origin: extracted  sets: focus
  While Carry.Idle, when the user moves focus between cards, Slate shall focus: for up or down,
  the next visible card in that direction in the column; for first or last, the first or last
  visible card of the column; for left or right, the card in the nearest column on that side
  that has a visible card, at the same position among the visible cards, or the last card if
  that column has fewer. If there is no such card, nothing changes. Focus does not wrap.
FCS-3 [must] origin: extracted  sets: focus
  While Carry.Idle, when the user puts focus on a card, Slate shall make that card the focus stop.
```

## Open a card

```text
OPN-1 [must] origin: extracted  sets: Place
  While Carry.Idle, when the user opens a card, Slate shall show Card for that card in a new
  history entry that has the "opened from the board" mark. The address of the board entry
  does not change.
```

## Selection

```text
SEL-1 [must] origin: extracted  sets: Selection, focus
  While Carry.Idle, when the user toggles the selection of a card, Slate shall add the card to
  the selection, or remove it if it is selected. Focus goes to that card.
SEL-2 [must] origin: extracted  sets: Selection
  While Carry.Idle, when the user selects a column, Slate shall add every visible card of the
  column to the selection. If every visible card of the column is selected, Slate shall remove
  them from the selection.
SEL-3 [must] origin: extracted  sets: Selection, focus
  While Selection.Some, when the user clears the selection, Slate shall remove every card from
  the selection and focus the place title.
SEL-4 [must] origin: extracted  sets: Selection
  While Selection.Some, Slate shall remove a card from the selection when the card becomes
  hidden or is deleted. The card is not selected again when it becomes visible.
```

## Carry

One carry state serves the pointer drag and its keyboard equivalent. Slate
sends no request before the drop.

```text
CRY-1 [must] origin: extracted  sets: Carry, focus
  While Carry.Idle, when the user picks up a card, Slate shall show Carry.Carrying with mark
  "Moving" on the card and make the card the focus stop. If the card has mark "Saving…",
  nothing changes.
CRY-2 [must] origin: extracted  sets: Carry
  While Carry.Carrying, when the user carries the card one step, Slate shall show the card: for
  up or down, one position up or down among the visible cards of its column, and not past the
  top or the end; for left or right, in the nearest column on that side that is loaded
  (Empty, NoMatch or Cards), at the same position among the visible cards, or at the end if
  the column has fewer. If there is no such column, nothing changes.
CRY-3 [must] [pointer] origin: extracted  sets: Carry
  While Carry.Carrying, when the user carries the card to a position, Slate shall show the card
  at that position of that column, if the column is loaded.
CRY-5 [must] origin: extracted  sets: Carry
  While Carry.Carrying, when the user cancels the carry, Slate shall show Carry.Idle with the
  card at the position it had before the pick up. Slate shall send no request and raise no notice.
CRY-6 [must] origin: extracted  sets: Carry
  While Carry.Carrying, Slate shall ignore these intents: open-card, move-focus, focus-card,
  toggle-select, select-column, bulk-move, bulk-label, delete-card, pick-up, ask-filter.
```

```text
CRY-T1 [must] decides: the user drops the card  owns: -
  1 the card is in the column and at the position among
    the visible cards that it had before the pick up      Carry.Idle; nothing else changes
  2 the column is another column and it is full (DAT-7)   Carry.Idle; the card at the position it
                                                          had; raise Info "In progress is full
                                                          (3 cards)." with no action; no request
  3 otherwise                                             Carry.Idle; the card at the drop position
                                                          (DAT-6) with mark "Saving…"; request the
                                                          move; focus stays on the card
```

## Move saves

```text
MOV-1 [must] origin: extracted  sets: Notice
  When a move save succeeds, Slate shall remove mark "Saving…" and raise Info
  "Moved SL-103 to Ready." with action "Undo" (MOV-3).
MOV-2 [must] origin: extracted  sets: Column, Notice
  If a move save fails, then Slate shall put the card back (DAT-8), remove mark "Saving…" and
  raise Error "Couldn't move SL-107. It is back in Backlog." with action "Retry". "Retry" does
  CRY-T1 rows 2 and 3 again for the same column and position number. Row 2 applies only if
  the card is not in that column now.
  Fail: the notice comes at the drop, before the reply.
MOV-3 [must] origin: extracted  sets: Column, focus
  When the undo of a move starts, Slate shall put each moved card back at the
  position it had before the move (DAT-8) with mark "Saving…", request the move, and focus the
  first of these cards in board order if it is visible. Slate shall not check a limit. Slate
  shall raise no notice when this save succeeds.
MOV-4 [must] origin: extracted  sets: Column, Notice
  If an undo save fails, then Slate shall put each failed card back where it was before the
  undo and raise Error "Couldn't undo the move of SL-103." or, for more than one card,
  "Couldn't undo the move of 2 cards.", with action "Retry". "Retry" does MOV-3 for the
  failed cards.
```

## Bulk actions

```text
BLK-T1 [must] decides: the user moves the selected cards to a column  owns: -
  Candidates: the selected cards that are not in the target column and have no mark
  "Saving…", in board order.
  1 Carry.Carrying, or there is no candidate   nothing
  2 the target column is full (DAT-7)          raise Info "In progress is full (3 cards)." with no
                                               action; no request
  3 otherwise                                  the first candidates that fit under the limit (all, if
                                               there is no limit) go to the end of the target in
                                               board order with mark "Saving…" and leave the
                                               selection at once; one request for all of them; the
                                               other selected cards stay selected

BLK-T2 [must] decides: a bulk move save answers  owns: -
  1 one card or more failed            put each failed card back (DAT-8) and select it again if it
                                       is visible; raise Error "Moved 2 of 3 cards to Review.
                                       Couldn't move SL-107." with action "Retry", which does BLK-T1
                                       for the failed cards and the same column; several failed
                                       cards show as "SL-107, SL-108", in board order
  2 fewer cards moved than there
    were candidates                    raise Info "Moved 1 of 3 cards to In progress. In progress is
                                       full (3 cards)." with action "Undo" (MOV-3)
  3 otherwise                          raise Info "Moved 2 cards to Review." with action "Undo" (MOV-3)

BLK-T3 [must] decides: the user labels the selected cards  owns: -
  1 Carry.Carrying                              nothing
  2 every selected card has the label           remove the label from each selected card; one request
  3 no selected card that lacks the label has
    fewer than 3 labels                         raise Info "A card can have at most 3 labels." with
                                                no action; no request
  4 otherwise                                   add the label to each selected card that lacks it and
                                                has fewer than 3 labels; one request
  The selection stays. SEL-4 applies at once.
```

```text
BLK-4 [must] origin: extracted  sets: Notice
  When a label save for the selection succeeds, Slate shall raise Info with no action:
  after BLK-T3.2, "Removed "bug" from 3 cards."; after BLK-T3.4, "Added "docs" to 2 cards.",
  or, if some cards that lack the label had 3 labels, "Added "docs" to 2 of 3 cards. A card can
  have at most 3 labels.". Count words are in DAT-13.
```

The undo of a move starts when the user activates "Undo" of a move notice
(NTC-4, NTC-5). The undo of a delete starts in the same way.

A notice has at most one action. A bulk move with a failed card has "Retry"
and no "Undo". The cards that moved stay moved.

## Delete

```text
DEL-1 [must] origin: extracted  sets: Column, Notice, focus
  While Board.Ready, when the user deletes a card, Slate shall remove the card at once, raise
  Info "Deleted SL-101." with action "Undo" (DEL-3), and focus the next visible card of the
  column, or the one before if there is none, or the place title if the column has no visible
  card. Slate shall send no request yet. If Carry.Carrying or the card has mark "Saving…",
  nothing changes.
DEL-2 [must] origin: extracted  sets: request
  When a delete notice ends, Slate shall request the delete, unless the notice ended by its
  action "Undo". A delete notice ends by its time (NTC-2) or when another notice is raised (NTC-1).
  Fail: the request is sent at the delete intent.
DEL-3 [must] origin: extracted  sets: Column, focus
  When the undo of a delete starts, Slate shall put the card back (DAT-8) and,
  if Board is shown and the card is visible, focus it and make it the focus stop. Slate shall
  send no request.
DEL-4 [must] origin: extracted  sets: Column, Notice
  If a delete save fails, then Slate shall put the card back (DAT-8) and raise Error
  "Couldn't delete SL-125. It is back in Done." with action "Retry". "Retry" removes the card
  again and requests the delete at once, with no notice.
DEL-5 [must] origin: extracted  sets: Place
  Slate shall treat a card that has a delete that waits or was sent as not there: it is in no
  column, it does not count, and its address shows Missing.Card.
```
