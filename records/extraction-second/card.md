# Slate — Card place (and the two "not found" places)

Origin of every rule: extracted. "(code)" = read in the source, not seen on the running build. Times in ms from the trigger. Notice texts: app.md.

```text
Card          States: Loading | Ready | Failed | Missing (CardMissing)
Title         States: Shown | Editing (Editing.Valid | Editing.Invalid) ; Saving (mark) on/off
Labels        States: Free | AtLimit ; Saving on/off
Assignee      States: Shown ; Saving on/off
Description   States: Shown | Empty | Editing ; Saving on/off
Comments      States: Loading | Failed | None | Some
CommentField  States: Off (Comments not Ready, or Sending) | Idle | Filled
PageMissing   States: Shown
```

## Faces

Card.Loading face
```text
1 r1 N  up-link "← Board"
2 r2 Q  two block placeholders (no text; the first is marked busy). No title yet: the window title is "<ID> · Slate".
```

Card.Failed face
```text
1 r1 N  up-link "← Board"
2 r1 P  h1 "<ID>" (for example "SL-114")
3 r1 N  alert "Couldn't load this card."
4 r2 N  button "Try again"
```

Card.Ready face (reading order)
```text
1 r1 N  up-link "← Board"
2 r2 Q  line "<ID> · <current column name>"   e.g. "SL-114 · Ready" (follows moves of this session)
3 r1 P  title row
   a  h1 title (Title.Shown)   |  field "Title" with the draft (Title.Editing) and, under it, an alert with the message (Editing.Invalid)
   b  button "Edit title" (Shown only)
   c  mark "Saving…" (while a title save is pending)
4 r1 N  group "Labels": toggles bug, ui, api, docs, perf, blocked (pressed = on; disabled = off while 3 are on); mark "Saving…" after them
5 r3 Q  line "Label limit reached (3)" — only in Labels.AtLimit
6 r1 N  radio group "Assignee": "Unassigned", "Ana Ruiz", "Ben Okafor", "Chloé Martin", "Dev Patel", "Mika Ito" (exactly one checked); mark "Saving…"
7 r2 P  h2 "Description", then
   a  text, or "No description" (Description.Empty, quiet)   |  textarea "Description" (5 lines) + buttons "Save", "Cancel" (Editing)
   b  button "Edit description" (not in Editing); mark "Saving…" after it
8 r2 P  h2 "Comments", then one of
   Loading: a placeholder (no text)
   Failed: alert "Couldn't load comments." + button "Retry"
   None: "No comments yet"
   Some: count text "2 comments" / "1 comment", then ordered list; each item: "<Author> · <time>" then the text
9 r1 N  textarea "Add a comment" (placeholder "Add a comment"); button "Add comment"; alert (comment error) after the button when present
10 r3 N  separator, button "Delete card"
```
Example SL-114 (Ready, cold): "SL-114 · Ready"; "Card title overflows on narrow screens"; labels bug, ui pressed; assignee Mika Ito checked; description "A long title pushes the labels out of the card."; "2 comments": "Dev Patel · 10 Nov 2026, 12:44" "I can reproduce this."; "Mika Ito · 11 Nov 2026, 08:57" "Is this still needed?".

CardMissing face (place Missing; no up-link)
```text
1 r1 P  h1 "Card not found"
2 r1 N  text "There is no card SL-999 on this board."   (id in upper case as read from the address)
3 r2 N  link "Go to the board" (-> "#/", NAV-6)
```
PageMissing face
```text
1 r1 P  h1 "Page not found"
2 r1 N  text "The address may be mistyped or out of date."
3 r2 N  link "Go to the board"
```
Both keep the entered address (not rewritten) and take focus on the h1 on arrival (NAV-T1). Window title "Not found · Slate".

## Loading

```text
CRD-1 [must] sets: Card, request
Cold start or address entered for a card that the session does not hold: Card.Loading at 0; loadBoard and loadCard are sent together (loadCard only if some column is still unloaded; else the card is read from the loaded columns).
 At +250 loadCard replies; Card is Ready when the board data AND the card are there (cold start: 400). If loadCard replies "no card": CardMissing at +250, even before the board data arrived.
 loadCard failed (profile card-down, once): Card.Failed at +250. "Try again": Card.Loading at 0, loadCard again; success -> Ready at +250; focus none (the Loading card has no title; NAV-9). loadBoard failed: Card.Failed too.
Opened from the Board (card already known): Card.Ready at once, no card request.
```
```text
CRD-2 [must] sets: Comments, request
At the moment Card is Ready Slate shall request the comments (loadComments, +300). Until the reply: Comments.Loading, textarea and "Add comment" disabled. Success -> None or Some, field enabled. Failure (fixture: SL-120, first time) -> Comments.Failed ("Couldn't load comments." + "Retry").
Retry: Comments.Loading at 0 (focus falls to the h1 title), loadComments again; a second reply ok -> Some.
Comments of a card are loaded once per session: coming back to the card shows them at once with no request (also after Back and Forward).
```

## Title

```text
TIT-1 [must] sets: Title, focus
When edit-title ("Edit title"), Slate shall replace h1 and button by the field "Title" with the current title, focus in the field with all text selected. Nothing is sent. While a title save is pending the button does nothing.
```
```text
TIT-2 [must] sets: Title, announcements
When title-commit (Enter in the field), Slate shall squash the draft (runs of white space become one space; ends trimmed) and check it:
 0 characters -> stays Editing.Invalid, alert "A title needs at least 1 character." (announced), focus stays in the field.
 more than 80 characters -> stays Editing.Invalid, alert "A title can have at most 80 characters.". 80 characters is accepted, 81 is not.
 The message stays until the next accepted commit (typing does not remove it).
```
```text
TIT-3 [must] sets: Title, focus, request, window title
When title-commit with a valid title: the field closes and focus goes to the h1 title. If the squashed title equals the current one: nothing else (no request, no mark).
 Otherwise the new title shows at once (also in the window title and on the Board) with the mark "Saving…", saveTitle is sent at 0 and answers at +400; success: the mark goes.
Example: "  Big   FLAKY  title " is saved as "Big FLAKY title".
```
```text
TIT-4 [must] sets: Title, Notice
If saveTitle fails (fixture: a title containing "flaky" in any letter case, first time), then Slate shall at +400 put the old title back (only if the title is still the one that was saved), remove the mark and raise the error notice "Couldn't save the title of SL-103." [Retry][Dismiss].
 Retry saves the same new title again at once (new title and "Saving…" shown, +400); it does nothing if a title save is pending or the card is deleted. The second reply is ok.
```
```text
TIT-5 [must] sets: Title, focus
When title-cancel (Escape in the field): the field closes, old title, no request, focus goes to the h1. (Escape does not leave the place; see DIS-T2.)
```
```text
TIT-6 [must] sets: Title, request, focus
When title-leave (focus leaves the field by Tab or a click elsewhere): a valid changed draft is saved like TIT-3 and focus is NOT forced to the title (it stays with what the user chose; observed after Tab: on "Edit title"); an invalid draft (empty or over 80) is dropped silently: old title, no message, no request; an unchanged draft just closes.
```

## Labels and assignee

```text
LAB-1 [must] sets: Labels, request
When toggle-label on a card with fewer than 3 labels, or on a label that is on: the toggle flips at once, the list is kept in label order (bug, ui, api, docs, perf, blocked), the mark "Saving…" shows, saveLabels is sent at 0 (+300).
 Each click is its own request; the mark stays until every request has replied. No failure path is defined (a failure would not undo the change).
 Example: SL-110 (no labels): perf, then bug -> request 1 [perf], request 2 [bug, perf]; shown as bug, perf.
```
```text
LIM-3 [must] sets: Labels
A card has at most 3 labels. With 2 labels a third can be added. With 3 labels the three off toggles are disabled (cannot be pressed, no request) and the line "Label limit reached (3)" shows; switching one off removes the line and enables them at once.
Bulk labels follow the same limit (board.md SEL-3).
```
```text
ASG-1 [must] sets: Assignee, request
When set-assignee on another person (or "Unassigned"): the radio changes at once, mark "Saving…", saveAssignee at 0 (+300). Choosing the person that is already checked does nothing (no request, no mark). Clicks do not move focus away from the pressed radio. No failure path.
The Board card shows the new name (or "Unassigned") and the filter "who" uses it at once.
```

## Description

```text
DSC-1 [must] sets: Description, focus
When edit-description, Slate shall replace text and button by a textarea "Description" with the current text and buttons "Save" and "Cancel"; focus in the textarea. While a description save is pending the button does nothing.
Leaving the textarea by Tab or click does not close it (the draft stays); Enter inserts a new line.
```
```text
DSC-2 [must] sets: Description, request, focus
When description-save ("Save", or Ctrl/Cmd+Enter in the textarea): trim the ends (inside is kept), close the editor, focus goes to "Edit description". If the text equals the current description (including whitespace-only on an empty description): nothing more.
 Otherwise the text shows at once (empty -> "No description"), mark "Saving…", saveDescription at 0 (+400), mark off on reply. No failure path.
```
```text
DSC-3 [must] sets: Description, focus
When description-cancel ("Cancel" or Escape anywhere on the place while the editor is open): the editor closes, old text, no request, focus goes to "Edit description".
```

## Comments

```text
COM-1 [must] sets: CommentField
"Add comment" is disabled while comments are not loaded, while a comment is being sent, and while the text is empty after trimming (spaces only = disabled). The textarea is disabled while comments are not loaded and while sending.
Typing clears the comment error message.
```
```text
COM-2 [must] sets: Comments, request, CommentField
When comment-send (button, or Ctrl/Cmd+Enter in the textarea; Enter alone is a new line): Slate shall trim the text and, if it is not empty, at 0:
 put the comment last in the list as "<current user, Mika Ito> · Sending…" with its text; the count line shows N+1 ("1 comment" replaces "No comments yet"); the textarea empties and is disabled; "Add comment" is disabled; the Board card count rises too; send addComment (+500).
 At +500 ok: "Sending…" becomes the time of the reply "20 Nov 2026, 09:00" (UTC; the clock started 09:00), field and button enabled; focus stays where it was.
 Example: SL-110 "  hello  " -> "Mika Ito · Sending…" / "hello" -> "Mika Ito · 20 Nov 2026, 09:00" at +500; at +499 still "Sending…".
```
```text
COM-3 [must] sets: Comments, CommentField, announcements, focus
If addComment fails (fixture: text containing "flaky" in any case, first time), then at +500 Slate shall remove the comment, restore the count, put the text back in the field (as typed after trimming), enable the field, show the alert "Couldn't add the comment. Your text is back in the field." (announced) and move focus to the field.
 If the user has left the Card place meanwhile, the text is lost and the error notice "Couldn't add the comment on SL-110." [Dismiss] is raised instead.
 Escape in the comment field does nothing (DIS-T2.3).
```
```text
COM-4 Order and format: comments oldest first in service order, a new one last. Heading text "N comments"/"1 comment" only in Some. Author is the person's name; unknown author shows "Unassigned". Time "2 Nov 2026, 08:00" (DAT-3).
Example: SL-102 "2 comments": "Ana Ruiz · 2 Nov 2026, 08:00 / I can reproduce this.", "Ben Okafor · 3 Nov 2026, 13:13 / Is this still needed?".
```

## DIS-T2  decides: Escape on the Card place  owns: Title, Description, App history

```text
DIS-T2 [must] decides: Escape pressed on Card (Loading, Ready or Failed)
DIS-T2.1  Focus in the title field: title-cancel (TIT-5).
DIS-T2.2  The description editor is open (focus anywhere, also in the comment field): description-cancel (DSC-3).
DIS-T2.3  Focus in the comment field: nothing.
DIS-T2.4  otherwise: up-link (NAV-5): from a card opened from the Board it is one step back (depth unchanged), else a new Board entry (depth + 1).
DIS-T2.5  On CardMissing and PageMissing: nothing.
```
Escape is consumed in every case. The title field wins over the description editor because focus is where the key goes.

## Delete (on the Card place)

```text
CDL-1 [must] sets: App history, Cards, Notice, focus
When delete-this-card ("Delete card"; there is no confirmation): the card is removed from the session at once, "Deleted SL-103." [Undo] is raised, and the user leaves the place:
 if this Card entry was added by open-card: one step back (depth unchanged, board address and scroll restored, focus on the title "Board" because the card is gone);
 else (cold start, entered address): this entry is replaced by the Board address (depth unchanged: cold start depth 2 stays 2), loadColumn x5 are sent if the columns are not loaded, focus on the title "Board".
No deleteCard request yet: it follows the rules of board.md DEL-2 (8000 ms, or when another notice replaces it; failure brings the card back with the error notice).
```
```text
CDL-2 [must] sets: Card, history
A card deleted in this session is CardMissing at its address ("Card not found", "There is no card SL-103 on this board.", title "Not found · Slate"). Undo (button or Ctrl/Cmd+Z) while that is shown brings the card back and the place becomes Card.Ready (focus on the h1 title, no history change).
After the delete request succeeded the card is gone for good (also for the cold start of its address: loadCard replies "no card").
```

## What survives on the Card place

```text
CST-1 [must] sets: Card
Back, Forward, Up, address entered, reload: open editors (title, description) close and their drafts are lost; the comment draft is lost; the comment error is cleared.
Session data survives except across reload: saved title, labels, assignee, description, comments, sent comments. After reload everything is back to the fixture (the service restarts).
A pending save keeps going when the place changes; its reply changes the data (e.g. a title that fails rolls back although the Card is not shown) and the notice is raised in the new place.
```

## Data rules (Card)

```text
CDAT-1 Title: squash then 1 to 80 characters; shown as saved (case kept). "Fix   login" -> "Fix login".
CDAT-2 Description: trimmed at the ends; empty shows "No description"; SL-110 has none, SL-103 has none, SL-102 "After a failed sign-in the page redirects to itself."
CDAT-3 Labels: at most 3, always in label order; SL-109 "bug, ui, perf" is at the limit (all other toggles disabled).
CDAT-4 Comment count words and time: see DAT-1 and DAT-3.
CDAT-5 Failure triggers of the fixture, each once per start: title containing "flaky" (any case); comment containing "flaky" (any case); loadComments of SL-120; deleteCard of SL-125; loadCard (profile card-down).
```
