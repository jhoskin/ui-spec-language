# App

This file gives the chart of places, the regions of the whole app, the closed
lists of intents and events, and the rules and tables that apply in all places.

## Chart

```text
Board --open a card--> Card        Card --up-link--> Board
any place --home link--> Board     Missing --board link--> Board
an address that names no place --> Missing.Page
an address of a card that does not exist --> Missing.Card
```

## Regions

```text
Place    States: Board | Card | Missing
Notice   States: None | Info | Error
Header   States: Shown
```

The regions of each place are in `places/`.

## Intents

An intent is one thing that a user means to do. The modality sheet binds each
intent to keys, to the pointer, or to both.

```text
Intents:
  open-home                the user opens the home link
  go-back                  the user goes Back
  go-forward               the user goes Forward
  reload                   the user reloads
  enter-address            the user enters an address
  dismiss                  the user dismisses
  undo                     the user asks to undo
  notice-action            the user activates the notice action
  dismiss-notice           the user dismisses the notice
  retry-place              the user retries the place
  ask-filter               the user asks for the filter
  change-filter-text       the user changes the filter text
  commit-filter            the user commits the filter
  toggle-label-filter      the user toggles a label filter
  toggle-assignee-filter   the user toggles an assignee filter
  clear-filters            the user clears the filters
  focus-card               the user puts focus on a card
  move-focus               the user moves focus between cards
  open-card                the user opens a card
  toggle-select            the user toggles the selection of a card
  select-column            the user selects a column
  clear-selection          the user clears the selection
  bulk-move                the user moves the selected cards to a column
  bulk-label               the user labels the selected cards
  pick-up                  the user picks up a card
  carry                    the user carries the card one step
  carry-to                 the user carries the card to a position
  drop                     the user drops the card
  cancel-carry             the user cancels the carry
  delete-card              the user deletes a card
  retry-column             the user retries a column
  go-up                    the user goes up
  edit-title               the user edits the title
  change-title-text        the user changes the title text
  commit-title             the user commits the title
  leave-title              the user moves focus out of the title field
  toggle-label             the user toggles a label of the card
  choose-assignee          the user chooses an assignee
  edit-description         the user edits the description
  change-description-text  the user changes the description text
  commit-description       the user commits the description
  cancel-description       the user cancels the description
  change-comment-text      the user changes the comment text
  commit-comment           the user commits the comment
  retry-comments           the user retries the comments
  open-board-link          the user opens the board link
```

## Events

An event is a trigger that does not come from the user.

```text
Events:
  the board load succeeds        the board load fails
  a column load succeeds         a column load fails
  a column load is slow          the last column answers
  the card load answers          the comments load answers
  the filter delay ends          the filter applies
  a move save succeeds           a move save fails
  a bulk move save answers       an undo save fails
  a label save for the selection succeeds
  a title save fails             a save succeeds
  a comment save succeeds        a comment save fails
  a delete notice ends           a delete save fails
  the undo of a move starts      the undo of a delete starts
  a notice is raised             the notice time ends
  the part that has focus is removed
  Slate shows an address         Slate arrives in a place
```

## Faces

```text
Header.Shown face (on every place, not pinned)
  1 r1 P link "Slate", the home link

Notice.Info face (pinned)
  1 r1 N text
  2 r2 N action, if the rule that raised the notice names one

Notice.Error face (pinned)
  1 r1 N text
  2 r2 N action, if the rule that raised the notice names one
  3 r3 Q action "Dismiss"

Notice.None face: nothing.
```

## Navigation

```text
NAV-1 [must] origin: extracted  sets: Place
  When Slate shows an address, Slate shall rewrite the current history entry to the written
  form of that address (DAT-16) and add no entry. A filter value that names no label or no
  person is dropped when the board data is loaded, not before.
NAV-2 [must] origin: extracted  sets: Place
  When the user opens the board link, Slate shall show Board with no filter in a new history entry.
NAV-3 [must] origin: extracted  sets: Place
  When the user enters an address, Slate shall show the place of that address in a new history
  entry that has no "opened from the board" mark.
```

```text
NAV-T2 [must] decides: the user opens the home link  owns: -
  1 the address is Board with no filter    scroll to the top; nothing else changes
  2 otherwise                              show Board with no filter in a new history entry

NAV-T3 [must] decides: the user goes up  owns: -
  1 the entry has the "opened from the board" mark    go Back
  2 otherwise    show Board in a new history entry, with the filter that Board had when it was
                 last shown in this session, or with no filter if Board was not shown

NAV-T1 [must] decides: Slate arrives in a place  owns: arrival scroll, arrival focus
  1 the first paint after a start or a reload         top; focus is not moved
  2 Board, directly after Card (go up, Back or
    Forward), and the card of that place is visible   scroll restored for Back or Forward, not changed
                                                      for a new entry; then that card in view; focus
                                                      that card, and it becomes the focus stop
  3 any other Back or Forward                         scroll restored; focus the place title
  4 otherwise                                         top; focus the place title
```

Row 2 looks at the moment of arrival. A card in a column that still loads is
not visible, so row 3 or row 4 applies. A place that shows no place title at
the arrival (Card.Loading) gets focus "none", and Slate does not move the focus
when the place title shows later.

## Memory

A step is an arrival by open-card, go-up, open-home or open-board-link.
"Direct" is an address that the user enters while Slate runs.

```text
MEM-T1 [must] decides: Slate arrives in a place  owns: memory
  region                          step      Back/Forward  reload        direct
  scroll                          NAV-T1    NAV-T1        top           top
  filter that is applied          address   address       address       address
  filter text not yet applied     lost      lost          lost          lost
  selection                       cleared   cleared       cleared       cleared
  carry                           cancelled cancelled     cancelled     cancelled
  notice                          kept      kept          removed       kept
  title edit, description edit,
    comment text, messages        lost      lost          lost          lost
  session data: edits, moves,
    loaded columns and comments,
    used faults                   kept      kept          start again   kept
  focus stop                      kept      kept          first visible kept
  "opened from the board" mark    kept      kept          kept          none
  filter of Board when last shown kept      kept          none          kept
```

A reload while a delete notice is shown sends no delete. The card is there
again after the reload (DEL-2).

## Notice

```text
NTC-1 [must] origin: extracted  sets: Notice
  When a notice is raised, Slate shall end the notice that is shown, if there is one, and show
  the new notice.
NTC-2 [must] origin: extracted  sets: Notice
  While Notice.Info, when the notice time ends, Slate shall end the notice. The notice time is
  8 s from the time the notice is raised. The pointer and the focus do not stop or restart it.
NTC-3 [must] origin: extracted  sets: Notice
  While Notice.Error, Slate shall keep the notice until the user activates its action, the user
  dismisses the notice, or another notice is raised.
NTC-4 [must] origin: extracted  sets: Notice
  When the user activates the notice action, Slate shall end the notice and then do the action
  that the rule that raised the notice names.
NTC-5 [must] origin: extracted  sets: Notice
  When the user asks to undo, Slate shall do as NTC-4 if the notice has the action "Undo".
  If not, Slate shall do nothing.
NTC-6 [must] origin: extracted  sets: Notice
  While Notice.Error, when the user dismisses the notice, Slate shall end the notice.
NTC-7 [should] origin: extracted  sets: Notice
  While Notice.Info or Notice.Error, Slate shall announce the text of the notice one time when
  it is raised: politely for Info, at once for Error.
```

## Focus

```text
FOC-1 [must] origin: extracted  sets: focus
  When the part that has focus is removed, Slate shall focus the same part if it is shown again
  in the same change (a card that moved or came back), and the place title if not. A rule that names a
  focus target for that change wins over this rule.
```

## Dismiss

```text
DIS-T1 [must] decides: the user dismisses  owns: -
  1 Carry.Carrying                                        cancel the carry (CRY-5)
  2 Board.Ready, focus in the filter field, the field
    has text                                              clear the text and apply the filter at once;
                                                          focus stays
  3 Board.Ready, focus in the filter field                focus the focus stop; if there is no visible
                                                          card, the place title
  4 Board.Ready, Selection.Some                           clear the selection; focus is not moved
  5 Card.Ready, Title.Editing, focus in the title field   Title.Shown with the old title; focus the
                                                          place title
  6 Card.Ready, Description.Editing                       Description.Shown with the old text; focus
                                                          action "Edit description"
  7 Card.Ready, focus in the comment field                nothing
  8 Card.Loading, Card.Failed or Card.Ready               go up (NAV-T3)
  9 otherwise                                             nothing
```

The dismiss intent does not end a notice. Title.Editing always has focus in the
title field, because a move of focus out of the field ends the edit (TTL-3).

## Properties

```text
PRP-1 [must] Always, under all faults: after the user opens a card from the board, one Back
  shows Board at the address it had.
PRP-2 [must] Always, under all faults: Slate sends a failed request again only when the user
  activates "Retry" or "Try again". An arrival in a place does not send it again.
PRP-3 [must] Always: the total in the count line is the number of cards in the columns that
  are loaded.
PRP-4 [must] Eventually, under all faults: each "Saving…" and "Sending…" mark is removed when
  the reply to its request comes.
```
