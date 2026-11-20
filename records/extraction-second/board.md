# Slate — Board place

Origin of every rule: extracted. "(code)" = read in the source, not seen on the running build. Times are ms from the trigger. Notice texts are in app.md (Region Notice).
Notation: "history depth" is the driver's number (start = 2). Request names as in the fixture.

```text
Board        States: Loading | Failed | Ready
Column       States: Loading (Loading.Fast | Loading.Slow) | Failed | Empty | NoMatch | Cards
Filter       States: Idle | Typing (draft not yet applied) ; Active (a filter applies) | Inactive
Selection    States: None | Some
Carry        States: Idle | Carrying
Card (item)  States: Resting | Selected | Carried | Saving (move pending)
```

## Faces

Board.Loading face
```text
1 r1 P  place title: h1 "Board"
2 r2 Q  three column placeholders (no text; the board is marked busy)
```

Board.Failed face
```text
1 r1 P  h1 "Board"
2 r1 N  alert "Couldn't load the board."
3 r2 N  button "Try again"
```

Board.Ready face (reading order; the filter row and columns are shown as soon as the board data is there, even while the columns still load)
```text
1 r1 P  h1 "Board"
2 r1 N  Filters region
   a  field (searchbox) named "Filter cards", placeholder "Filter cards (press /)"; shows the draft text
   b  group "Labels": six toggles: bug, ui, api, docs, perf, blocked (on = pressed)
   c  group "Assignee": toggles "Ana Ruiz", "Ben Okafor", "Chloé Martin", "Dev Patel", "Mika Ito", "Unassigned"
   d  button "Clear filters" — only while a filter applies OR the field is not empty
   e  status line (count line): "Loading cards…" | "27 cards" | "1 of 27 cards"
3 r2 N  Selection panel — only in Selection.Some (see below)
4 r1 P  five columns left to right: Backlog, Ready, In progress, Review, Done (see Column faces)
5 r2 Q  board line, below the columns — only when settled: "This board has no cards yet." (total 0, filter or not)
        else "No cards match these filters." followed by button "Show all cards" (filter active, 0 visible, total > 0)
```

Selection.Some face (between filters and columns)
```text
1 r1 P  text "N selected"  ("1 selected", "10 selected")
2 r1 N  group "Move selected to": five buttons "Backlog", "Ready", "In progress", "Review", "Done" (all five, also the column of the cards)
3 r2 N  group "Label selected": six toggles bug, ui, api, docs, perf, blocked; pressed = every selected card has it; mixed = some; off = none
4 r2 N  button "Clear selection"
```

Column faces (common head, in order: h2 column name; count text; "Limit 3" (In progress only); button "Select all" [named "Select all in <Column>"] only in Column.Cards; then the body)
```text
Column.Loading face      head without count and without "Select all"; body: three placeholders; Loading.Slow adds line "Still loading…" after them
Column.Failed face       head without count; body: alert "Couldn't load <Column>." ; button "Retry" (named "Retry <Column>")
Column.Empty face        count "0 cards" (with a filter: "0 of 0 cards"); body: "No cards"; no "Select all"
Column.NoMatch face      count "0 of 10 cards"; body: "No matching cards"; no "Select all" (cards exist, filter hides all)
Column.Cards face        count "10 cards" or "1 of 10 cards"; "Limit 3"; "Select all"; list of visible cards in column order
```
Count text per column: no filter "N cards"; filter active "<visible> of <N> cards" (N = all loaded cards of the column, hidden ones included).

Card.Resting face (one list item, name "SL-102 Fix login redirect loop")
```text
1 r1 N  checkbox "Select SL-102" (checked when selected)
2 r2 Q  id text "SL-102"
3 r1 P  title link "Fix login redirect loop" (to #/card/SL-102)
4 r2 N  labels list (aria "Labels") — only if the card has labels; chips in label order, e.g. "bug", "ui", "perf"
5 r3 Q  assignee: person name or "Unassigned"
6 r3 Q  comment count "2 comments" / "1 comment" — only if > 0
7 r1 N  mark "Moving" (Card.Carried) | mark "Saving…" (Card.Saving, a move request is pending)
```
Example SL-102: "SL-102", "Fix login redirect loop", [bug], "Ana Ruiz", "2 comments". SL-101: [api], "Unassigned", no comment text.

## Loading

```text
BRD-1 [must] sets: Board, request
When start or arrival on Board and the board data is not there, Slate shall show Board.Loading at 0 and send loadBoard.
 At 400 ms success -> Board.Ready, filter canonicalised (NAV-3), and five loadColumn requests are sent at once (one per column; all Column.Loading).
 failure -> Board.Failed at 400. "Try again": Board.Loading at 0 (alert and button gone, focus -> "Board" title by FOC-1), loadBoard again; success at +400.
```
```text
BRD-2 [must] sets: Column, Filter
Each column shows Column.Loading from 0 of its request. Success at +300 (Done +1800): Column.Cards or Empty or NoMatch.
 At +1000 still loading: Column.Loading.Slow ("Still loading…"); at +999 not yet. In the fixture only Done reaches it (visible 1400 to 2200 after start).
 Columns appear one by one as they reply; cards of a reply are placed in the column in service order.
If the reply fails: Column.Failed at the reply time (+300 for Ready under profile column-down). "Retry <Column>": Column.Loading at 0 (focus -> "Board" title), same request, a new slow mark.
 Other columns, the filter and the selection are not affected; a failed column cannot be a target of a carry step and it counts 0 in the count line.
```
```text
BRD-3 [must] sets: Filter count line, announcements
While at least one column has not replied (success or failure), the count line is "Loading cards…" (it stays "Loading cards…" for the 2200 ms of the Done column).
When the last column has replied (ok or failed) and the Board is the place shown, the count line shows the count and Slate announces it once ("27 cards", with a failed Ready: "20 cards"). A reply while another place is shown makes no announcement.
Profile empty: "0 cards", every column "0 cards" + "No cards", board line "This board has no cards yet."
```

## Filter

```text
FLT-1 [must] sets: Filter, cards shown
A card is visible when: every word of the text occurs in "<title> <id>" ignoring letter case (substring, not word start; words are split at single spaces after squashing); AND it has every chosen label; AND (no assignee chosen OR its assignee is one of the chosen; "Unassigned" = no assignee).
Examples: "login redirect" matches SL-102 only (1 of 27); "sl-12" matches SL-120..SL-127 (8); "log" matches both "Login…" cards and "Dialog…"; labels bug+ui = SL-106, SL-109, SL-111, SL-114 (cards that have both); Mika Ito + Unassigned = cards of either.
```
```text
FLT-2 [must] sets: Filter, address, history depth
When filter-text, Slate shall show the typed text in the field at once (and "Clear filters") and apply it 250 ms after the last keystroke: at 249 ms the address and cards are unchanged; at 250 ms the cards, the counts, the address (replaced in place, depth unchanged) change and the count line is announced ("1 of 27 cards").
Written address: "#/?q=Login+Redirect" (case kept, spaces squashed, "+" for space). Typing before the board data is there is ignored.
```
```text
FLT-3 [must] sets: Filter, address, Selection, Carry
When toggle-label-filter, toggle-who-filter, clear-filters, filter-commit, filter-clear-field or the filter-timer, Slate shall apply the filter at once, including the text that is in the field now, cancel the filter-timer, replace the address (depth unchanged), cancel a carry, drop selected cards that became hidden, and announce the count line.
Toggles keep focus on themselves. Several chosen labels = all of them; several chosen people = any of them. A hidden selected card is deselected for good (clearing the filter does not select it again).
```
```text
FLT-4 [must] sets: Filter, focus
When filter-commit (Enter in the field) and exactly one card is visible on the whole board, Slate shall move focus to that card (it becomes the focus stop). Otherwise focus stays in the field. The count line is announced again even when nothing changed.
```
```text
FLT-5 [must] sets: Filter, focus
When clear-filters ("Clear filters" or "Show all cards"), Slate shall empty the field, remove all labels and people, and move focus to the filter field. Address "#/". Announces "27 cards".
"Clear filters" exists while a filter applies or the field is not empty (also while the draft is not yet applied); it disappears when both are empty (focus was on it -> the field takes it by this rule).
```
```text
FLT-6 [must] sets: Board face
Board line (face item 5) and the count line follow the filter only when the board is settled; with total 0 the line is "This board has no cards yet." even if a filter is active (no "No cards match these filters.").
```

## DIS-T1  decides: Escape on Board  owns: Carry, Filter, Selection, focus

```text
DIS-T1 [must] decides: Escape pressed on Board
DIS-T1.1  While Carrying, cancel the carry (card back where it was, nothing sent, "Moving" gone). Focus unchanged.
DIS-T1.2  Focus in the filter field and the field is not empty: empty the field and apply the filter at once (announce count). Focus stays in the field. Labels and people stay chosen.
DIS-T1.3  Focus in the filter field and the field is empty: focus moves to the focus stop card (FCS-1); if no card is visible, to the title "Board".
DIS-T1.4  Selection is Some: clear the selection. Focus unchanged.
DIS-T1.5  otherwise: nothing (the key is still consumed).
```
Observed: Escape on a focused card with no selection and no carry does nothing; Escape in the filter with text "card" while columns still load announced "Loading cards…".

## Selection

```text
SEL-1 [must] sets: Selection
When select-toggle ("x" on the focused card, or click on its checkbox), Slate shall add or remove that card. The checkbox click also gives focus to the card. Selection has no limit, spans columns, and ignores keys while Carrying.
When select-column ("Shift+X" on a card, or "Select all in <Column>"): if every visible card of that column is selected, deselect them; else select all visible cards of the column. Hidden cards are never selected.
Panel count: "1 selected", "2 selected", "10 selected" (no plural word).
```
```text
SEL-2 [must] sets: Selection, focus
When clear-selection by the button "Clear selection", Slate shall clear it and move focus to the title "Board" (the button is gone). By Escape (DIS-T1.4) focus stays.
Selection is cleared by every arrival at a place (Back, Forward, open card, reload), and when a selected card is deleted or hidden by a filter.
```
```text
SEL-3 [must] sets: Cards, request, Notice, Selection
When bulk-label on label L with selection S (board order not needed): 
 if every card of S has L: remove L from all of S at once ("Saving…" is not shown on the board; labels change at once), one saveLabels request (300 ms), then at the reply notice "Removed "L" from N cards." (N=|S|, "1 card").
 else the cards that lack L and have fewer than 3 labels get L appended (kept in label order), one saveLabels request, then notice "Added "L" to N cards." or, if some lacked L but were at 3 labels, "Added "L" to N of M cards. A card can have at most 3 labels." (M = cards lacking L).
 If no card can take it: notice "A card can have at most 3 labels." at once, no request.
The selection stays (it is not cleared by bulk-label). The notice comes at the reply (300 ms), not at the click. The toggle state of the panel follows at once (mixed/pressed). Labels removed when "mixed": pressing a mixed toggle ADDS.
```
```text
SEL-4 [must] sets: Cards, request, Notice, Selection
When bulk-move to column T, Slate shall: take the selected cards that are not in T and have no move pending (candidates, M of them), in board order; if there are none, do nothing;
 room = limit - cards in T (all cards, hidden too; no limit = all); if room <= 0 raise "T is full (3 cards)." and move nothing (no request);
 else move the first `room` candidates, in board order, to the end of T in that order, at once ("Saving…" on each), deselect them (the others stay selected), send ONE moveCards request with all moves (400 ms).
 Reply: all ok and none left over -> "Moved 3 cards to Ready." [Undo] ("Moved 1 card to …"); some left over by the limit -> "Moved 1 of 3 cards to In progress. In progress is full (3 cards)." [Undo] (the left-over cards stay selected);
 some failed (the service fails a single card, e.g. SL-107 once) -> the failed cards go back to their old column and place, are selected again, notice (error) "Moved 2 of 3 cards to Ready. Couldn't move SL-107." [Retry][Dismiss] ("of M" counts candidates, not the selection).
 Retry repeats a bulk move of the failed cards to T (the limit is checked again).
Focus stays where it was (on the pressed button); if the panel disappears with the last card focus falls to "Board" (FOC-1).
```
```text
SEL-5 [should] sets: Cards
Undo of a bulk move moves every moved card back to its old column and old position by one moveCards request; no notice when it succeeds; failures -> "Couldn't undo the move of 2 cards." [Retry]. Focus goes to the first moved card in board order.
```

## Focus stop and keys on cards

```text
FCS-1 [must] sets: focus
Exactly one card is in the tab order (the focus stop): the card that last had focus (by key, pointer or Tab) while it is still visible; else the first visible card of the first column that has one. While Carrying it is the carried card.
Other cards take focus only by the arrow keys, Home/End, a click, or the rules above.
```
```text
FCS-2 [must] sets: focus
Keys when focus is on a card (not in a text field, no Ctrl/Cmd/Alt):
 ArrowUp / ArrowDown: previous / next visible card in the same column (nothing at the end; no wrap). Home / End: first / last visible card of the column.
 ArrowLeft / ArrowRight: the nearest column in that direction that has a visible card; target = card at the same index, or the last one if that column has fewer; nothing at the edge; empty and failed columns are skipped.
 Enter: open the card (NAV-4). Space: pick up (MOV-1). "x": select-toggle. "Shift+X": select-column. Delete or Backspace: delete (DEL-1). "/" anywhere on the board (not in a text field): focus the filter field (not while carrying).
 Ctrl/Cmd+Z: undo-key (NTC-3) when focus is not in a text field.
All these keys are consumed (no scroll). While Carrying, arrows and Space/Enter belong to MOV-2/3; every other key is ignored (Home/End then keep their scroll default).
```

## Moving a card (keys and pointer share one state, Carry)

```text
MOV-1 [must] sets: Carry, Card face
When pick-up on a visible card with no move pending (Space on the focused card, or pointer press on the card — not on its checkbox — and a move of 4 px or more), while the Board is Ready and not already Carrying, Slate shall start Carrying: the card shows "Moving", keeps focus, and stays in its place in the list. Nothing is sent. Press and release without 4 px is an ordinary click (the title link opens the card).
Pointer press on the checkbox never starts a drag.
```
```text
MOV-2 [must] sets: Carry
While Carrying, when carry-step by keys: ArrowUp/ArrowDown move the card one place up/down among the OTHER visible cards of its column (clamped: at the top and at the end nothing happens, no wrap).
 ArrowLeft/ArrowRight go to the nearest column on that side that has replied OK (loading and failed columns are skipped; empty columns count), at the same place number or at the end if the column has fewer visible cards; nothing at the edges.
The card is shown at once in its carry position (in the new column too). Counts and "Limit" are not updated during carry. Selection and focus moves are blocked while carrying; opening a card (Enter is drop, link click is ignored) too.
```
```text
MOV-3 [must] sets: Carry, Cards, request, Notice
When drop (Enter or Space, or release of the pointer over a column), Slate shall end Carrying and decide by MOV-T1.
Release of the pointer over no column, pointer cancel, Escape (DIS-T1.1) or a filter change cancel the carry: the card is where it was, nothing is sent.
```
## MOV-T1  decides: drop  owns: Cards, Notice

```text
MOV-T1 [must] decides: drop
MOV-T1.1  Same column and the new absolute place equals the old one: nothing (no request, no notice).
MOV-T1.2  Other column and that column already holds its limit (In progress with 3): card returns, notice "In progress is full (3 cards)." (Info, no action), no request.
MOV-T1.3  otherwise: the card is at the new place at once with "Saving…"; one moveCards request with one move {card, column, index}; at +400:
          ok -> the mark goes; notice "Moved SL-101 to Ready." [Undo] (also for a reorder inside one column: "Moved SL-102 to Backlog."); focus stays on the card.
          failed -> card back in its old column and old place, mark gone, error notice "Couldn't move SL-107. It is back in Backlog." [Retry][Dismiss]. Focus unchanged.
```
```text
MOV-4 [must] sets: Cards
The new absolute place of a card dropped at visible place v (counted among the other visible cards of the target column): at v = 0 it goes to the very top of the column; otherwise directly after the visible card that is above it (hidden cards that follow that card stay below the moved card).
Example (filter bug; Backlog shows SL-102, SL-106, SL-109): carry SL-102 down one place -> after SL-106; with the filter cleared Backlog reads 101 103 104 105 106 102 107 108 109 110.
Example (no filter): SL-101 is at place 1 of Backlog. ArrowRight puts it at place 1 of Ready ("101 111 112 …"); ArrowDown twice -> "111 112 101 113 …"; Enter -> moveCards index 2; notice "Moved SL-101 to Ready.". Carrying SL-107 (place 7) right: place 7 of Ready (before SL-117); ArrowDown once more -> end.
Dropping into an empty or all-hidden column: the card goes to the top. Dropping beyond the end: the end.
```
```text
MOV-5 [must] sets: Carry, Cards (pointer)
While the pointer carries, the place v in the column under the pointer is the number of other cards of that column whose vertical middle is above the pointer. Over a column that has not replied OK, or over no column, the carry position stays as it was. Release over a column drops; release elsewhere cancels. The click that follows a drag never opens a card.
Example: press SL-101 near the top, move into the Ready column over the top half of SL-112 -> SL-101 sits between SL-111 and SL-112; over the lower half of SL-112 -> after SL-112; release -> moveCards at once.
```
```text
MOV-6 [must] sets: Cards
Moves never change a card's labels, people or comment count. The card keeps focus. During a pending move ("Saving…") the card cannot be picked up again or deleted (the key does nothing); other cards can.
Retry (error notice) repeats the same move with the same column and absolute place; if the target column is full now: "In progress is full (3 cards)." instead. Retry of a card that was deleted meanwhile does nothing.
```
```text
MOV-7 [must] sets: Cards, Notice
Undo of a one-card move or of a bulk move (Undo button or Ctrl/Cmd+Z while the "Moved …" notice is shown): the cards go back to old column and old absolute place at once ("Saving…"), one moveCards request (400 ms), no notice on success, error "Couldn't undo the move of SL-101." [Retry] on failure. Focus goes to the first returned card in board order, if visible.
There is no undo once the notice is gone (8000 ms) or replaced.
```

## Limit

```text
LIM-1 [must] sets: Cards, Notice
In progress holds at most 3 cards. At 2 cards, one more may be moved in (3 cards). At 3 cards, a drop or bulk move into it from another column is refused with "In progress is full (3 cards)." and nothing is sent; a drop inside In progress (reorder) is allowed at 3.
A bulk move that exceeds the room moves as many as fit, in board order (selected SL-101, SL-102, SL-103 with 2 cards in In progress: SL-101 moves; notice "Moved 1 of 3 cards to In progress. In progress is full (3 cards)."; SL-102 and SL-103 stay selected).
The limit counts hidden cards too. "Limit 3" is shown under the count of In progress in every state.
LIM-2 Title 80 characters and 3 labels are limits of the Card place (card.md).
```

## Delete (on the Board)

```text
DEL-1 [must] sets: Cards, focus, Notice, request
When delete-card (Delete or Backspace on a focused visible card, no move pending, not carrying), Slate shall take the card out of the list at once (counts, count line and selection follow), move focus to the next visible card of its column, else the previous visible one, else the title "Board", and raise "Deleted SL-102." [Undo]. No request is sent yet.
```
```text
DEL-2 [must] sets: request
The deleteCard request is sent when that notice ends for any reason except Undo: at 8000 ms, or when another notice replaces it (a second delete sends the first request at that moment). It is answered at +400.
 Success: nothing happens. Failure (fixture: SL-125, first time): the card comes back at its old place (clamped), error notice "Couldn't delete SL-125. It is back in Done." [Retry][Dismiss], focus unchanged.
```
```text
DEL-3 [must] sets: Cards, focus
Undo of a delete (button or Ctrl/Cmd+Z within 8000 ms): the card is back at its old place at once, no request was ever sent, no notice; focus goes to that card if it is visible.
```
```text
DEL-4 [must] sets: Cards, request
Retry after a failed delete: the card leaves again at once, deleteCard is sent at once (no 8 s wait, no "Deleted" notice), success is silent.
A deleted card that the service still holds (before the request) is not shown again by a later load of its column: deleted ids are skipped.
```

## Data rules (Board)

```text
BDAT-1 Ordering: columns fixed; cards in a column in service order. Moves put a card at the stated absolute index (clamped to the end). Bulk moves append in board order (column order, then top to bottom).
BDAT-2 Selection set is shown by checked boxes; the "N selected" count counts selected visible cards only.
BDAT-3 The session wins over reloads: a card already known keeps its session state when its column loads later.
BDAT-4 Examples: SL-102 "Fix login redirect loop" [bug] Ana Ruiz 2 comments; SL-110 "Archive cards older than a year" no labels "Unassigned"; filter "login redirect" -> 1 of 27 cards, Backlog "1 of 10 cards", Ready "0 of 7 cards" + "No matching cards", Review "0 of 0 cards" + "No cards".
```
