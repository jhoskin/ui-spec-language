# Slate terminal build: notes

Layout of the code: `clock.py` (controlled clock), `service.py` (service
double), `address.py` (TRM-2), `model.py` (state, intents, key map, semantic
face; no terminal code), `view.py` (layout on a grid, parts, rects, dump; no
terminal code), `keys.py` (TRM-9 bytes to key names), `slate.py` (raw mode,
painting, harness channel). Tests are in `tests/`.

## The ten choices I was least sure of

1. **When the filter applies.** The face shows "Clear filters" "while Filter.On
   or the field has text", so I read the field as a draft. Typing changes only
   the draft. Enter (commit-filter) applies it. A label or assignee toggle
   applies at once, together with the text in the field. Applying the filter
   rewrites the current history entry instead of adding a new one, scrolls to the
   top, and removes hidden cards from the selection. Text matches when every
   word appears in the identifier or the title. Labels match when the card has
   any chosen label, assignees when the card has any chosen person, and the two
   groups must both match.

2. **Count texts (DAT-2, DAT-3, DAT-14), which the inventory does not give.**
   The count line is "27 cards", or "Showing 5 of 27 cards" with Filter.On. The
   column count is "10", or "3 of 10" with Filter.On. The comment count is
   "1 comment" or "2 comments". The comment time (DAT-9) is "10 Nov 2026, 12:44"
   in UTC, with no leading zero on the day.

3. **How long a notice lasts, and its texts.** An info notice is gone 8000 ms
   after it is raised. An error notice stays until it is dismissed or replaced.
   The texts I made up are:
   - "Moved SL-103 to Ready." (this one is from the spec), "Moved 3 cards to
     Review.", with Undo
   - "Moved SL-103 back to Backlog." after an undo
   - "Couldn't move SL-107.", with Try again
   - "Added bug to 3 cards." and "Removed bug from 3 cards.", with Undo
   - "Deleted SL-103."
   - "Couldn't delete SL-125.", with Try again
   - "Couldn't save the labels / the assignee / the description.", with Try again

   A failed title save goes back to Title.Editing with the alert "Couldn't save
   the title.". A failed comment shows the alert "Couldn't add the comment." and
   keeps the text. A blank title gives "Title can't be empty.".

4. **The column limit is enforced.** A bulk move that would put more than 3
   cards in In progress is refused with the error notice "In progress has a
   limit of 3 cards.". A carry skips a full column. A card whose move save has
   no reply yet cannot be picked up again, so a card item never needs both
   "Moving" and "Saving…".

5. **The rows of DIS-T1 (Escape).** I know only rows .1 (cancel carry), .6
   (cancel description) and .8 (go up). The order I chose is: cancel carry, then
   cancel title editing, then cancel description editing, then clear the
   selection, then dismiss the notice, then go up (Card place only). The address
   prompt takes Escape first (TRM-6).

6. **Delete.** There is no confirmation and no undo, because the service has no
   way to create a card. The card goes away at once and deleteCard is sent at
   once. On a failure the card comes back with an error notice. Deleting from the
   Card place returns to the board. If the card was opened from the board, the
   build goes back and removes the card's history entry. Otherwise it rewrites
   the entry to "board".

7. **Loading and caching.**
   - After loadBoard the five columns load at the same time, in board order.
   - Board data is kept for the session, so going back to the board reloads
     nothing. Edits on the Card place update that kept copy.
   - The Card place always calls loadCard and loadComments together, and also
     loadBoard if the board was never loaded (it needs the label, person and
     column names).
   - Undo and moves change the board at once and are reverted on failure. The
     build does not reload columns after a move.
   - Column.Loading.Slow starts 1000 ms after the column load starts.

8. **Focus rules (FCS).**
   - At start and after a reload, focus is none.
   - After a navigation the user makes, focus goes to the place title as soon as
     there is one (Card.Loading has none).
   - Going back or up to the board puts focus on the card the user came from.
   - Home and End go to the first and last visible card in board order, not in
     the column.
   - Left and Right keep the position, clamped, and skip columns with no visible
     card.
   - leave-title (Tab out of the title field) commits a changed, non-blank
     title; otherwise it cancels.
   - The terminal cursor sits at the first cell of the focused part (TRM-7),
     even in fields. Typing always adds at the end of the text.

9. **What the dump lists as parts.**
   - The location line, the announcement row and the group captions
     ("Labels:", "Move selected to:") are painted but not listed as parts.
   - Each column is a part with the role "column", and its heading is another
     part.
   - "Select all" and the column "Retry" are painted with their full names
     ("[Select all in Backlog]", "[Retry Ready]"), cut to fit, so the name is
     inside the rect.
   - A disabled action is painted "[Add comment] (off)".
   - A notice part's rect includes its "i " or "! " start.
   - While the address prompt is open it takes the notice row, and the dump's
     notice is null.
   - Frame lines start at {"frame": 1}.
   - On a screen that is too small, the dump has one text part, title null and
     no columns.

10. **History and addresses.**
    - Opening the address of the current entry (for example the home link while
      on "board") changes the current entry instead of adding one.
    - The board address is written in canonical form: labels in board order,
      people in fixture order with "none" last, and parts that name nothing
      dropped.
    - "card/x" with any non-empty x that has no "/" is a card address with the
      upper-cased identifier. "card/" and "Board" are Missing.Page.
    - Selection is kept across navigation within a session.
    - Without --harness, Control+Q quits (no binding is given for quitting).
      With --harness it does nothing.

## Testing note

The sandbox refuses pseudo-terminals: `pty.openpty()` raises "out of pty
devices". So `tests/test_pty.py` runs the same harness cases in two ways:

- `PtyTest`, in a 120×40 pseudo-terminal. It is skipped here.
- `PipeHarnessTest`, which always runs. The real `slate.py --harness` gets pipes
  as stdin and stdout, with the size from COLUMNS and LINES (the build reads
  these only when stdout is not a terminal). Control goes on descriptors 3 and 4.

Both feed the output to a strict emulator. It fails on any control sequence
that TRM-12 does not allow, and it checks each dump against the emulated screen
(TRM-H6) and the cursor position. Raw mode itself was not tested, because
`tty.setraw` needs a terminal.
