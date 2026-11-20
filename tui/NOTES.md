# Notes on the terminal build of Slate

## Layout of the code

- `slate.py`: the entry point (TRM-H1).
- `terminal.py`: decodes keys (TRM-9), paints (TRM-12), handles raw mode, the alternate screen, the
  real-time loop and the harness channel on descriptors 3 and 4 (TRM-H2 to TRM-H4).
- `app.py`: the application logic: history, places, loads, filter, selection, carry, saves,
  notice and focus. It does not touch the terminal.
- `view.py`: builds the character grid and the parts (layout, TRM-10, TRM-13, TRM-14) that
  the painter and the dump (TRM-H5) both use.
- `clock.py`, `service.py`: the clock and the service double. They are built from `fixture/`.
- `tests/`: the vector test, the public scenarios (run step by step through the key
  bindings), extra rule tests, and a test of the real process through `--harness`.

## Testing without a pseudo-terminal

The sandbox does not allow a pseudo-terminal. `os.openpty()`, `pty.fork()` and
`open("/dev/ptmx")` all fail with "Operation not permitted". So `tests/test_harness_process.py`
runs the real `slate.py --harness` with pipes as its terminal:

- Without a tty, the build skips raw mode and paints at 120 x 40, the size that the checks use.
- A small VT parser rebuilds the grid. The test checks that only TRM-12 sequences are used,
  the frame lines, the dump against the painted grid (TRM-H6), and the cursor position.

Raw mode (`tty.setraw`) and the window size read on a real terminal were therefore not
exercised by a test.

The scenario tests also run a TRM-H6 check after every step on the in-memory grid.

## Choices where the specification does not decide

1. **TRM-H3** The first frame line is `{"frame": 1}`. "One more than the last" is read with
   an implied last of 0.
2. **TRM-H5, TRM-H6, TRM-A3** A part in the area of the columns that is not fully in view is
   left out of `parts`. Otherwise its rect would lie on the filter bar or the notice row,
   where something else is painted. `cards` lists every card item of the loaded columns,
   with its virtual rect and `inView`. There is no part with the role "column"; the dump
   field `columns` gives the column names.
3. **TRM-A3** Scroll has no binding of its own. Slate keeps the part that has focus in view
   after every input, both keys and clock advances. NAV-T2.1 sets the scroll to the top and
   leaves focus where it is (on the home link, after it is activated).
4. **NAV-T1.2** "Scroll not changed for a new entry" (go up with no mark): the new Board
   entry starts at the top, then the card is brought into view.
5. **NAV-T1.1** "Focus is not moved": focus is none after a start and after a reload. The
   parts that had focus before the reload are gone.
6. **TRM-H5 roles and groups**
   - The count line has the role "status line". The column counts, the comment count,
     "3 selected" and the other quiet texts have the role "text".
   - Parts that show text (text, status line, alert, mark, notice) have `name` = `text` =
     the whole text.
   - The notice is one part with the role "notice", whose name is its text.
   - The notice actions have the group "Notice". This tells "Retry" of a notice apart from
     "Retry" of the comments.
   - Parts inside a column have the group null.
   - A card part has the state null; its selection is in `cards[].selected`.
   - A placeholder has the name null.
7. **TRM-H5** The address in the location line (TRM-4) and the announcement row (TRM-11) are
   not parts. If they were, a text such as "Couldn't load the board." would still count as
   "shown" after the alert is gone. The group names are painted as prefixes ("Labels:",
   "Move selected to:") but are not parts.
8. **Role "alert"** ("announced at once each time it shows") An alert is announced when it
   appears in a frame where it was not shown before. A title message or a comment message
   that is set again is announced again.
9. **TRM-10 disabled** " (off)" comes after the name:
   - an action: `[Add comment] (off)`;
   - a field: `Add a comment (off): text`;
   - a toggle: `[ ] api (off)`.
10. **TRM-7 against TRM-A6** TRM-7 puts the terminal cursor at the first cell of the part
    that has focus. TRM-A6 says that the cursor is at the end of the draft when Title.Editing
    starts. These disagree for fields. I follow TRM-7 for the terminal cursor. The insertion
    point of every field is always the end of its text, because no key moves it. So TRM-A6
    holds for the logical caret.
11. **VIS-7 / TRM-A8** The place title gets no reverse video when it has focus, but the
    cursor is at its first cell.
12. **BLK-T1** A "Move selected to" action for a column that is not loaded (Loading or
    Failed) is disabled. Cards cannot be placed in a column whose order is not known yet.
13. **MOV-2** "The same column and position number": the position is the index in the
    column, hidden cards included, that was sent in the request. It is put back with DAT-8.
14. **BLK-T2.1** In "Moved 2 of 3 cards", 3 is the number of cards in the request.
15. **Sidecar matrix note 1** A failed saveDescription, saveLabels or saveAssignee (no fault
    can cause one) keeps the new value, removes the mark "Saving…" and raises no notice. A
    failed label save for the selection raises no BLK-4 notice.
16. **NAV-1** Before the board data comes, a label or person that names nothing stays in the
    address and in the applied filter. When the board data comes, it is dropped from the
    current entry and from "the filter of Board when last shown".
17. **TRM-2**
    - q is percent-decoded after "+" becomes a space. A part with a bad percent code is
      dropped (borrowed from WEB-1).
    - The written form encodes `% & + = # ?` and control characters, so that every text
      reads back the same.
    - `card/` with an empty identifier, a "/" or white space in the identifier is
      Missing.Page.
    - Any other identifier is a card address. A card that does not exist gives Missing.Card
      when loadCard answers null.
18. **TRM-6**
    - The prompt starts empty.
    - Enter, Escape, typing, Backspace and Control+U work in it. Control+B, Control+F and
      Control+R close it and then act. Every other key does nothing.
    - While the prompt is open, a notice moves up one row and the content area is one row
      shorter.
    - Escape gives focus back to the part that had it.
19. **TRM-8, no quit binding** Without `--harness`, Control+Q quits, so that a user can leave.
    With `--harness`, Control+Q has no binding (TRM-8 "does nothing") and only the "quit"
    command ends the build.
20. **CRY-6 against TRM-7** Tab and Shift+Tab still move focus during a carry, and the carry
    stays. The carried card is the focus stop, so Tab comes back to it.
21. **MOV-3 during a carry** If an undo or a retry moves the card that is being carried, the
    carry is cancelled first.
22. **FLT-1, FLT-3** Each time the filter applies, the filter delay timer is cancelled, so a
    commit is not followed by a second apply and announcement.
23. **TTL-3 against TRM-7** leave-title by Tab: focus goes to the next (or previous) stop, as
    Tab does. "Slate shall not move the focus" is read as "Slate adds no focus move of its
    own".
24. **DEL-T1.2** Showing Board in place of the current entry is an arrival of kind "step"
    (NAV-T1.4: top, focus the place title). The replaced entry has no mark.
25. **DAT-8 for a delete from Card** If the column of the card is not loaded yet, its position
    is taken from the column reply when that reply comes. The card is not shown (COL-4). An
    undo puts it at that position.
26. **TRM-13, Card does not scroll** If Card.Ready is taller than the screen, the oldest
    comments are left off the screen until the place fits. The comment count still gives the
    total.
27. **COL-4** A card that the reply puts in a column, while the session already shows it in
    another loaded column, is left where the session has it.
28. **Card mark "Saving…" for labels** A label save for the selection also counts as "a label
    save has no reply" for the Labels group of the Card place of each card in it.
29. **TRM-9** A read that holds more than one key, which TRM-H3 says cannot happen, is split
    into keys. Each key gets its own frame line. Bytes 0x0A and 0x08 are also read as Enter
    and Backspace.
30. **Comment sending** "A comment is sent" is kept for each card. Another card can take a
    comment at the same time.

## Statements that disagree or are unclear

- **TRM-7 and TRM-A6** disagree on where the cursor is in a field (see choice 10).
- **DIS-T1 rows 6 and 7**: while Description.Editing, row 6 wins even with focus in the
  comment field. SCN-DSC-1 confirms this order. The note under DIS-T1 does not say it.
- **TTL-3 and TRM-8**: TTL-3 says the focus is not moved, yet the binding of leave-title is
  Tab, which moves focus (see choice 23).
- **NAV-T1.1 and FOC-1**: after a reload the part that had focus is removed, which would make
  FOC-1 focus the place title. NAV-T1.1 says the focus is not moved. I follow NAV-T1.1 (focus
  none, choice 5).
- **TRM-H5 `cards` and `parts`** both list card items. Only `cards` has `inView`, which
  suggests that cards out of view are listed there (see choice 2).
- I found no disagreement between `fixture/fixture.md` and the JSON files. The fault "f"
  (the second move of SL-108) is `skip: 1, times: 1` in `service.json`.
