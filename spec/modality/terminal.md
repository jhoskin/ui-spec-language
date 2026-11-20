# Modality sheet: terminal

This sheet binds the core to a character terminal with a keyboard and no
pointer. It holds the address forms, the key bindings, the marks that show
state in characters, the permitted adaptations and the harness binding.

```text
TRM-1 Screen. The build paints a grid of characters. It needs 112 columns and 30 rows or more.
  On a smaller screen it shows only the text "Slate needs 112 columns and 30 rows." The checks
  use 120 columns and 40 rows.
TRM-2 Addresses. Board: "board", "board?q=fix+login", "board?q=fix+login&labels=bug,ui&who=ana,none".
  The parts come in the order q, labels, who. A space in q is "+". A label is its name. A person
  is the first name in lower case with no accent: ana, ben, chloe, dev, mika. Unassigned is
  "none". Card: "card/SL-114"; the identifier is read in any letter case. An empty address is
  Board with no filter. Each other address is Missing.Page. A part with another name is
  dropped. If a part occurs two times, the last one counts. A label or a person in another
  letter case names nothing. Text after "?" in a card address is dropped.
TRM-3 History. The terminal has no history of its own. The build keeps a list of history
  entries and a position in it, with the same rules as the core: a new entry is put after the
  current entry and removes the entries after it; a rewrite changes the current entry; Back
  and Forward move the position. Each entry keeps its address, its scroll and its
  "opened from the board" mark. Back at the first entry and Forward at the last entry do nothing.
TRM-4 Location line. The first row shows the home link "Slate" at the start side. At the far
  end it shows the address of the current entry, then the position and the number of entries,
  for example "board?q=fix+login  2/3".
TRM-5 Reload. A reload starts the session again at the current address: the service double,
  the clock and all session data start again. The history list, the position and the marks of
  the entries are kept.
TRM-6 Address prompt. The enter-address intent opens a field with the name "Address" on the
  row of the notice. Enter commits the text as an address (NAV-3). Escape closes the prompt
  and changes nothing else; DIS-T1 does not apply while the prompt is open.
TRM-7 Focus. Exactly one part has focus, or none. Tab moves focus to the next part that can
  take focus, in face order; Shift+Tab moves it back. Both wrap. The order on Board: home link;
  filter field; label toggles; assignee toggles; "Clear filters"; the parts of the selection
  bar; then for each column "Select all" (or "Retry"); the focus stop comes after "Select all"
  of its column; then "Show all cards"; then the parts of the notice. The parts inside a card
  item are not stops. The order on Card: home link; up-link; "Edit title" (or the title
  field); label toggles; assignee choices; "Edit description" (or the description field,
  "Save", "Cancel"); "Retry" of the comments; comment field; "Add comment"; "Delete card";
  then the parts of the notice. A disabled part is not a stop. The terminal cursor is shown
  at the first cell of the part that has focus. With focus "none" the cursor is hidden.
  The place title can have focus (by a rule); Tab does not stop on it.
TRM-8 Bindings. "Card" means focus is on a card. "Outside text" means focus is not in a field.
  intent                   context            binding
  open-home                any                activate link "Slate"
  go-back                  any                Control+B
  go-forward               any                Control+F
  reload                   any                Control+R
  enter-address            any                Control+G, then type, then Enter (TRM-6)
  dismiss                  any                Escape
  undo                     outside text       Control+Z
  notice-action            any                activate the action of the notice
  dismiss-notice           any                activate "Dismiss"
  retry-place              any                activate "Try again"
  ask-filter               outside text       "/"
  change-filter-text       filter field       type; Backspace removes one character; Control+U empties the field
  commit-filter            filter field       Enter
  toggle-label-filter      any                activate the toggle
  toggle-assignee-filter   any                activate the toggle
  clear-filters            any                activate "Clear filters" or "Show all cards"
  focus-card               any                Tab to the focus stop
  move-focus               card               Up, Down, Left, Right; Home for first; End for last
  open-card                card               Enter
  toggle-select            card               "x"
  select-column            card               Shift+"x", for the column of the card
  select-column            any                activate "Select all"
  clear-selection          any                activate "Clear selection"
  bulk-move                any                activate the action of the column
  bulk-label               any                activate the toggle of the label
  pick-up                  card               Space
  carry                    card               Up, Down, Left, Right
  drop                     card               Space or Enter
  cancel-carry             any                Escape (DIS-T1.1)
  delete-card              card               Delete or Backspace
  delete-card              any                activate "Delete card" (Card place)
  retry-column             any                activate "Retry" of the column
  go-up                    any                activate the up-link; Escape (DIS-T1.8)
  edit-title               any                activate "Edit title"
  change-title-text        title field        type; Backspace; Control+U empties the field
  commit-title             title field        Enter
  leave-title              title field        Tab or Shift+Tab
  toggle-label             any                activate the toggle
  choose-assignee          any                activate the choice
  edit-description         any                activate "Edit description"
  change-description-text  description field  type; Enter makes a new line; Backspace; Control+U empties the field
  commit-description       description field  Control+S
  commit-description       any                activate "Save"
  cancel-description       any                activate "Cancel"; Escape (DIS-T1.6)
  change-comment-text      comment field      type; Enter makes a new line; Backspace; Control+U empties the field
  commit-comment           comment field      Control+S
  commit-comment           any                activate "Add comment"
  retry-comments           any                activate "Retry" of the comments
  open-board-link          any                activate "Go to the board"
  "Activate" is Enter or Space with focus on the control.
  A key with no binding in its context does nothing.
TRM-9 Key bytes. Enter 0x0D. Tab 0x09. Shift+Tab ESC [ Z. Escape 0x1B alone. Space 0x20.
  Backspace 0x7F. Delete ESC [ 3 ~. Up ESC [ A. Down ESC [ B. Right ESC [ C. Left ESC [ D.
  Home ESC [ H. End ESC [ F. Control+B 0x02. Control+F 0x06. Control+G 0x07. Control+R 0x12.
  Control+S 0x13. Control+U 0x15. Control+Z 0x1A. Shift+"x" is "X". The build puts the
  terminal in raw mode, so that no key makes a signal.
TRM-10 State in characters. A toggle shows "[x] " before its name when on, "[ ] " when off and
  "[-] " when mixed. A choice shows "(o) " when chosen and "( ) " when not. A card item shows
  "[x] " before its identifier when selected and "[ ] " when not. An action and a link show
  their name in square brackets: "[Clear filters]". A disabled part shows " (off)" after its
  name. A field shows its name, then ": ", then its text. A placeholder is a run of "░".
  An info notice starts with "i "; an error notice starts with "! ".
TRM-11 Announcements. The last row shows the text of the last announcement. It stays until
  the next announcement.
TRM-12 Paint. The build paints with these sequences only: cursor position (CSI row ; col H),
  erase display (CSI 2 J), erase to end of line (CSI K), character attributes (CSI ... m with
  0, 1, 2, 4, 7, 30 to 37, 39, 40 to 47, 49, 90 to 97), show and hide cursor (CSI ? 25 h and
  CSI ? 25 l), and the alternate screen (CSI ? 1049 h and CSI ? 1049 l). Each character takes
  one cell. The build uses no other control characters than CR and LF.
TRM-13 Layout. Row 1: location line. Then the place. The notice is pinned on the row above
  the last row, at the start side. Board: the filter bar is pinned under the place title; the
  selection bar is under it; the five columns stand side by side with equal width and fill
  the width. The area of the columns scrolls up and down as one part when a column is longer
  than the area; the filter bar, the notice and the last row do not scroll. Card and Missing:
  one column of text with a maximum width of 80 cells, at the start side.
TRM-14 Card item. A card item has three rows: the selection mark, the identifier and the marks
  ("Moving", "Saving…"); the title; the labels, the assignee and the comment count. A blank
  row follows each card.
```

## Adaptations

Each entry names the rule that it adapts and how the intent of the rule stays.

```text
TRM-A1 CRY-3 and the intent carry-to are inapplicable: there is no pointer. The carry by keys
  (CRY-2) reaches each position that CRY-3 reaches.
TRM-A2 open-card, toggle-select, pick-up, drop and cancel-carry have no pointer binding. The
  key bindings of TRM-8 keep each intent.
TRM-A3 "Scroll" is the first row of the area of the columns that is shown. "Top" is row 1 of
  that area. "In view" means that all three rows of the card are shown. Card and Missing do
  not scroll.
TRM-A4 A title or a text that does not fit its width is cut, and its last shown character is
  "…". The semantic dump (TRM-H4) has the whole text.
TRM-A5 commit-description and commit-comment use Control+S. A terminal cannot tell Enter from
  Control+Enter.
TRM-A6 WEB-2 (window title), WEB-7 (the draft is selected), WEB-8 and the VIS commitments
  with [graphic] are inapplicable. When Title.Editing starts, the cursor is at the end of the
  draft, and Control+U empties the field.
TRM-A7 Layout intent words that this sheet replaces: "centered column with a maximum width"
  becomes "one column at the start side with a maximum width" (TRM-13); "the row scrolls
  sideways" is replaced by the minimum width of TRM-1.
TRM-A8 Token roles map to character attributes: accent is reverse video on the part that has
  focus; muted is dim; danger is bold. No other colour is required.
```

## Harness

The harness binds `fixture/harness.md` for a terminal build. The build is one
command that runs in a terminal.

```text
TRM-H1 Start. "python3 tui/slate.py --profile <name> --address <address> --harness". Without
  --harness the build uses real time and has no control channel. Without --address it starts
  at "board". The fixture files are read from the directory "fixture" next to "tui".
TRM-H2 Control channel. With --harness the build reads control commands from file descriptor
  3 and writes replies to file descriptor 4, one JSON object on each line. The clock moves
  only by the "advance" command.
TRM-H3 Frames. After the build handles one input and has painted, it writes {"frame": n} on
  descriptor 4, with n one more than the last. An input is one key from the terminal, or one
  control command. One read from the terminal holds exactly one key (TRM-9). The first frame
  line comes when the first paint is done. A key that changes nothing still gives a frame line.
TRM-H4 Commands. {"advance": ms}: move the clock, run each timer that is due in order of due
  time, paint, write a frame line. {"dump": true}: write the semantic dump (TRM-H5) as one
  line; it changes nothing and gives no frame line. {"quit": true}: restore the terminal and exit.
TRM-H5 Semantic dump. One JSON object:
  title          the text of the place title, or null
  address        the address of the current entry (TRM-2)
  depth          the number of history entries
  focus          the index in "parts" of the part that has focus, or null
  scrollTop      true if the scroll is at the top (TRM-A3)
  parts          a flat list in reading order of every part that is shown. A card item is one
                 part with the role "card"; the parts inside a card item are not listed. Each:
                 role (a role concept of spec/conventions.md), name, group (the name of the group
                 that holds it, or null), state ("on", "off", "mixed", "chosen", "not chosen" or
                 null), disabled (true or false), text (the text of a field; for role "text" the
                 whole text), rect ([row, column, height, width], counted from 1)
  columns        the names of the columns that are shown, in order
  cards          every card item that is shown, in reading order: id, column (the column name),
                 selected, marks (a list of the mark texts), rect, inView
  notice         null, or kind ("info" or "error"), text, action (the name, or null)
  announcements  every announcement from the start or the last reload, in order
  requests       every request from the start or the last reload: op, at (ms from the start)
  A part with role "text" is a text that is not the name of another part: a count, a line, a
  message, a comment. The name of a part is what the face gives: "Clear filters", "bug",
  "Filter cards", "SL-101 Export board as CSV" is the name of a card. The up-link has the role
  "up-link" and the name "← Board". The place title has the role "place title".
TRM-H6 The dump tells what is painted. Each name and each text of the dump is painted inside
  its rect, cut as TRM-A4 allows. The state marks of TRM-10 are painted inside the rect.
```
