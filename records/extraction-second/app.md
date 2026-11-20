# Slate — app level (places, navigation, notice, announcements, focus fallback)

All rules: origin "extracted". Observed on the running build with the driver unless a line says "(code)".
History depth is the driver's number: a fresh start shows 2 (the start entry counts as 2). "+1" means a new entry.

## Inventory

```text
App  States: Board | Card | CardMissing | PageMissing
Notice  States: None | Info | Error
Places: Board (#/ and #/?...), Card (#/card/<ID>), CardMissing ("Card not found"), PageMissing ("Page not found").
Persistent parts: header link "Slate" (always, top, address "#/"), the one Notice (bottom, outside the place).
Closed lists below. A trigger that no rule names keeps the platform default.
```

### Intents and events (closed list)

```text
Navigation intents: start, header-link, open-card (click link, Enter on card), up-link ("← Board"),
  Escape-on-card-place (acts as up-link), go-to-board ("Go to the board"), step-back, step-forward,
  reload, address-entered.
Board intents: filter-text, filter-commit (Enter in filter), filter-clear-field (Escape in filter with text),
  toggle-label-filter, toggle-who-filter, clear-filters ("Clear filters" or "Show all cards"),
  focus-filter ("/"), move-focus, select-toggle ("x" or checkbox), select-column ("X" or "Select all"),
  clear-selection (button or Escape), bulk-move, bulk-label, pick-up (Space or drag past 4 px), carry-step,
  drop, cancel-carry, delete-card (Delete or Backspace), retry-column, retry-board ("Try again").
Card intents: edit-title, title-commit (Enter), title-leave (focus leaves the field), title-cancel (Escape),
  toggle-label, set-assignee, edit-description, description-save (button or Ctrl/Cmd+Enter), description-cancel,
  comment-send (button or Ctrl/Cmd+Enter), retry-comments, retry-card, delete-this-card.
Notice intents: notice-action (button Retry or Undo), undo-key (Ctrl/Cmd+Z), dismiss (button, errors only).
Events: reply-ok, reply-failed, notice-timeout (8000 ms), filter-timer (250 ms), slow-mark (1000 ms).
```

## Document title (the window title)

```text
NAV-1 [must] origin: extracted  sets: App
The window title is: Board "Slate"; Card Ready "<ID> <title> · Slate" (updates at once when the title changes or is rolled back);
Card Loading or Failed "<ID> · Slate"; CardMissing and PageMissing "Not found · Slate".
Example: "SL-114 Card title overflows on narrow screens · Slate"; cold start on #/card/SL-114 shows "SL-114 · Slate" until the card is Ready.
```

## Address grammar (what an address means)

```text
NAV-2 [must] origin: extracted  sets: App
The address is read as follows (after "#"): "", "/" or "#" alone -> Board without filter.
"/?<query>" -> Board with filter. "/card/<ID>" -> Card (one segment only). Anything else -> PageMissing
 ("#/nowhere", "#/card/", "#/card/SL-1/x", "#foo", "/foo" entered, "#/x?q=1").
Query keys: q (text; "+" and %20 are spaces; runs of spaces squashed; surrounding spaces dropped), labels (comma list), who (comma list).
A key that appears twice: the last one wins. Unknown keys are dropped. A value with broken %-coding is ignored (filter field empty).
The card id is read in any letter case and shown upper case: "#/card/sl-114" -> "#/card/SL-114".
Text after "?" on a card address is dropped: "#/card/sl-114?x=1" -> "#/card/SL-114".
A card address with another tail is a card id of its own: "#/card/SL-114#x" -> id "SL-114#X" -> CardMissing "There is no card SL-114#X on this board."
```

```text
NAV-3 [must] origin: extracted  sets: Board filter, address
Once the board data is loaded, a Board address is rewritten in place (no new entry, depth unchanged) to its one written form:
 q squashed; labels only known ids, in board order (bug, ui, api, docs, perf, blocked), no duplicates; who only known ids, in
 order ana, ben, chloe, dev, mika, none, no duplicates; written order q, labels, who; "+" for spaces; empty keys omitted;
 an empty filter is "#/".
Case matters: "labels=Bug" and "who=MIKA" are unknown and dropped.
Example: "#/?labels=Bug,ui,ui&who=MIKA&q=%20Fix&q=a%26b" -> "#/?q=a%26b&labels=ui".
Before the board data is loaded the address is kept (only squashed and de-duplicated) and is rewritten the moment the data is there.
```

## NAV-T1  decides: how a change of place sets focus, scroll, history  owns: App

```text
NAV-T1 [must] decides: arrival at a place
Kind of arrival                                   focus                                   scroll                  history
NAV-T1.1 start / reload                           none (nothing has focus)                top                     start entry (depth 2 at start); reload keeps depth
NAV-T1.2 step-back / step-forward onto Board
         coming from a Card whose card is a
         visible card of the Board                that card (card name "SL-102 <title>")  restored (card in view)  unchanged (moves in the list)
NAV-T1.3 step-back / step-forward onto any
         other place or from a non-Card place     place title (h1: "Board", card title, "Card not found", "Page not found")  restored (see NAV-8)  unchanged
NAV-T1.4 up-link, Escape on Card, with the
         Card's card visible on the Board         that card                               card in view            see NAV-5
NAV-T1.5 open-card, header-link (from other
         place), go-to-board, address-entered,
         up-link with no Board entry before       place title (if the title part exists yet; else none — see NAV-9)   top   +1
NAV-T1.6 otherwise                                place title                             top
```

```text
NAV-4 [must] origin: extracted  sets: App history
While Board, when open-card, Slate shall add one entry with address "#/card/<ID>" and mark it as "came from the board".
The click on the card link keeps the platform default (new tab or window) when Ctrl, Cmd or Shift is held, or the middle button is used.
Open-card does nothing: while a card is being carried, for a hidden card, or while the board data is not Ready.
```

```text
NAV-5 [must] origin: extracted  sets: App history, address
When up-link (or Escape on Card, or a delete from the Card place) and the Card entry was added by open-card, Slate shall go one step back
 (depth unchanged, the address is the board entry as it was: filter included, selection cleared, scroll restored by NAV-8).
When up-link and the Card entry was not added by open-card (cold start, entered address, header link, Forward), Slate shall add one entry
 with the Board address of the last filter that this session wrote on any Board arrival or filter change ("#/" if no Board was shown yet in this session,
 e.g. after a cold start on a card address) and set focus by NAV-T1.4. The Board's columns may not be loaded yet at that moment; then the card cannot take focus and
 focus goes to the place title "Board" (observed: cold "#/card/SL-114" -> "← Board" -> focus on h1 "Board").
Example: start "#/card/SL-114" -> "← Board": address "#/", depth 3.  Board "#/?labels=bug" -> open SL-102 -> "← Board": address "#/?labels=bug", depth 3 (unchanged), focus on SL-102.
```

```text
NAV-6 [must] origin: extracted  sets: App history
When header-link and the place is Board with address exactly "#/", Slate shall scroll to the top and do nothing else (no entry, no focus change, no request).
When header-link otherwise (Board with a filter, Card, missing places), Slate shall add one entry "#/" (filter dropped) and set focus by NAV-T1.5.
When go-to-board ("Go to the board" on CardMissing or PageMissing), Slate shall add one entry "#/".
```

```text
NAV-7 [must] origin: extracted  sets: App history
When address-entered, Slate shall add one entry (the entries after the current one are dropped), read the address by NAV-2, rewrite it by NAV-3, and set focus by NAV-T1.5.
Everything that is not in the address is reset by an arrival (any step, Back, Forward, address): selection cleared, carry cancelled,
 field drafts and open editors (title, description) dropped, comment draft dropped, pending filter timer cancelled.
Data of the session (cards, comments, labels, assignees, deleted cards) stays.
```

```text
NAV-8 [should] origin: extracted  sets: scroll
On step-back or step-forward Slate shall restore the vertical scroll that the entry had when it was left.
On every other arrival Slate shall scroll to the top. Example: Board scrolled 300, open SL-126 (card place at top), Back -> scroll 300 and focus on SL-126.
```

```text
NAV-9 [must] origin: extracted  sets: focus
The focus request of an arrival is made once. If the part to focus does not exist at that moment (the Card place is still Loading, so it has no title yet),
focus stays none and is not set later when the Card becomes Ready.
Example: address "#/card/abc" entered while the card is unknown to the session: focus none.
```

```text
NAV-10 [must] origin: extracted  sets: App
What survives:
 Reload: the address (filter, card id) only. All session data is reloaded from the service; edits made before are gone (the fixture service restarts). Focus none, scroll top, notice gone, selection gone.
 Back / Forward / Up: the data of the session, the notice (see NTC-5), the last written filter. Not: selection, carry, drafts, open editors.
 Address entered while running: data of the session and the notice; drafts and selection reset.
A notice survives every change of place (it is not tied to a place).
```

## Place loading at the app level

```text
NAV-11 [must] origin: extracted  sets: App, Board, Card
Board and Card both need the board data (columns, people, labels, current user). A Card needs the card too.
Cold start on "#/card/<ID>" sends loadBoard and loadCard together at 0. If every column of the Board is already loaded, no loadCard is sent
 (the card is looked up in the loaded columns; if it is not there the Card is CardMissing at once).
Card is Ready when both replies are there (the later one: cold start 400 ms). Comments are requested the moment the Card becomes Ready (see card.md).
loadCard reply "no such card" -> CardMissing at 250 ms, even if the board data is not there yet. A deleted card (this session) is CardMissing.
loadCard failed -> Card.Failed; loadBoard failed -> Card.Failed too ("Couldn't load this card.") and Board.Failed on a Board.
```

## Region Notice

```text
Notice  States: None | Info (Info.Undoable | Info.Plain) | Error (Error.Retry)
```

Notice.Info face (one notice at most, bottom of the page, role status):
```text
1 r1 P  text (exact, see list below)
2 r2 N  action button "Undo" (only Info.Undoable)
```
Notice.Error face (role alert):
```text
1 r1 P  text
2 r2 N  action button "Retry" (all error texts listed except the comment error on another card, which has none)
3 r3 N  button "Dismiss"
```

Texts (exact; N = count; cards by id; column names exact):
```text
Move, one card, ok:       "Moved SL-101 to Ready."                 [Undo]
Move, one card, failed:   "Couldn't move SL-107. It is back in Backlog."     [Retry][Dismiss]   (column = where it was)
Move, several, all ok:    "Moved 3 cards to Ready."                [Undo]   (1 card: "Moved 1 card to Ready.")
Move, several, partly full: "Moved 1 of 3 cards to In progress. In progress is full (3 cards)."  [Undo]
Move, several, some failed: "Moved 2 of 3 cards to Ready. Couldn't move SL-107, SL-108."  [Retry][Dismiss]   (ids joined by ", ")
Column full (drop or retry): "In progress is full (3 cards)."     no action; also used when a bulk move finds no room
Undo of a move failed:    "Couldn't undo the move of SL-101." (one card) or "Couldn't undo the move of 2 cards."  [Retry][Dismiss]
Delete, pending:          "Deleted SL-102."                         [Undo]
Delete, failed:           "Couldn't delete SL-125. It is back in Done."   [Retry][Dismiss]
Bulk label removed:       "Removed "bug" from 2 cards."             (straight double quotes; no action)
Bulk label added:         "Added "bug" to 2 cards."   or when some cards were at the limit  "Added "docs" to 2 of 3 cards. A card can have at most 3 labels."
Bulk label, none can take it: "A card can have at most 3 labels."   (no request)
Title save failed:        "Couldn't save the title of SL-103."      [Retry][Dismiss]
Comment failed while away from the Card: "Couldn't add the comment on SL-110."   [Dismiss] only
```

```text
NTC-1 [must] origin: extracted  sets: Notice
When a notice is raised, Slate shall end the notice that is shown (if any, reason "replaced") and show the new one at once.
Only one notice exists. Raising a notice also gives its text as an announcement (error notices have role alert).
```

```text
NTC-2 [must] origin: extracted  sets: Notice, request
An Info notice ends 8000 ms after it was raised (no pause on hover or focus, no restart by other events). At 7999 ms it is still shown; at 8000 ms it is gone.
An Error notice has no timer. It ends only by Dismiss, by Retry, or by being replaced.
```

```text
NTC-3 [must] origin: extracted  sets: Notice, request
When notice-action on "Undo" or undo-key (Ctrl/Cmd+Z, only when focus is not in a text field and the notice is Info.Undoable), Slate shall end the notice (reason "action") and run the undo.
 Undo of a move: the cards go back to their old column and old position by a new moveCards request (400 ms); no notice on success; focus goes to the first moved card (board order) if it is visible.
 Undo of a delete: the card is back at its old position at once, no request is sent at all; focus goes to that card if visible; no notice.
When undo-key and the notice is Error, plain, absent or has another action, nothing happens (the key is not consumed for text fields).
```

```text
NTC-4 [must] origin: extracted  sets: Notice, request
Delete is sent late: the deleteCard request is sent when the "Deleted" notice ends for any reason except Undo: after 8000 ms, or when another notice replaces it (it has no Dismiss).
Retry after a failed delete is the exception: the card leaves again at once, the request is sent at once (no 8 s wait), a success is silent, a failure raises the error notice again.
Example: delete SL-102 at t, request at t+8000. Delete SL-109, then at t+3000 delete SL-108: the request for SL-109 is sent at t+3000, SL-108 at t+3000+8000.
Reload with the notice shown: the delete is never sent; the card is back after reload (the service restarts).
```

```text
NTC-5 [must] origin: extracted  sets: Notice
Dismiss (button) ends an Error notice (reason "dismissed") and does nothing else; focus then falls to the place title (FOC-1).
Notice-action "Retry" ends the notice first, then repeats the action (see board.md MOV-9, DEL-4 and card.md TIT-8); a Retry whose card is gone or deleted does nothing.
A notice shows in every place and survives navigation; its timer keeps running while the place changes.
```

## Announcements and focus fallback

```text
ANN-1 [must] origin: extracted  sets: announcements
Slate announces (text exactly as shown): every notice text when raised; the count line of the Board when the board becomes settled (all columns replied, ok or failed), after every filter change, and after commit/Escape in filter ("27 cards", "1 of 27 cards");
 the title error ("A title needs at least 1 character." / "A title can have at most 80 characters.") each time it appears; the comment error ("Couldn't add the comment. Your text is back in the field.").
Loading, selection changes, carry steps, focus moves and "Saving…" marks are not announced.
```

```text
FOC-1 [must] origin: extracted  sets: focus
If the part that has focus disappears when the screen changes (a button that is removed, a card that is deleted, a panel that closes), focus goes to the same part if it still exists (matching by its role: the card, the title, the filter field),
 else to the place title (h1: "Board", the card title, "Card not found"). If the place has no title yet (Card Loading), focus is none.
Examples: "Clear selection" pressed -> title "Board". "Dismiss" pressed -> title "Board". Retry on a failed column -> "Board". "Try again" on Board.Failed -> "Board". Retry on Card.Failed -> none (Loading card has no title).
The last selected bulk button ("Move selected to > Done") when the selection panel vanishes -> "Board".
A focused element that stays is never moved: pressing a filter toggle keeps focus on that toggle.
```

## Timers (all)

```text
TIM-1 filter-timer 250 ms after the last keystroke in the filter field: applies the text (see board.md FLT-3). 249 ms: nothing yet, address unchanged. Enter, Escape, toggles, "Clear filters" apply at once and cancel it. Any arrival cancels it.
TIM-2 slow-mark 1000 ms after a column's loadColumn started and still loading: the line "Still loading…" appears in that column (disappears at the reply). Not before (at 999 ms not there).
TIM-3 notice 8000 ms (Info only), see NTC-2.
TIM-4 Service latencies (visible as the time of "Saving…" and loading): loadBoard 400, loadColumn 300 (Done 1800), loadCard 250, loadComments 300, moveCards 400, saveTitle 400, saveDescription 400, saveLabels 300, saveAssignee 300, addComment 500, deleteCard 400.
```

## Data rules (global)

```text
DAT-1 Count words: "0 cards", "1 card", "27 cards", "1 comment", "2 comments"; "N selected" never changes to a word ("1 selected").
DAT-2 Filtered count: "<shown> of <total> cards", for example "1 of 27 cards"; also "1 of 10 cards" per column. Total counts only loaded columns (a failed column counts 0).
DAT-3 Time of a comment: "20 Nov 2026, 09:00" (UTC, day without leading zero: "2 Nov 2026, 08:00", month three letters, 24 h, minutes two digits, no seconds, never relative). Comment being sent: "Sending…".
DAT-4 Card id search and display: ids are "SL-" plus three digits. Person names exact: Ana Ruiz, Ben Okafor, Chloé Martin, Dev Patel, Mika Ito. "Unassigned" for none.
DAT-5 Label order everywhere (filter, card, bulk, address, card chips): bug, ui, api, docs, perf, blocked. A card's label list is always shown in that order, whatever order they were added.
DAT-6 The columns in order: Backlog, Ready, In progress, Review, Done. In progress shows "Limit 3".
```
