# Modality sheet: web

This sheet binds the core to a web browser with a keyboard and a pointer. It
holds addresses, strings that name keys, bindings, roles, sizes and token
values.

```text
WEB-1 Addresses. Board: "#/", "#/?q=fix+login", "#/?q=fix+login&labels=bug,ui&who=ana,none".
  The parts come in the order q, labels, who. A space in q is "+". A label is its name. A
  person is the first name in lower case with no accent: ana, ben, chloe, dev, mika.
  Unassigned is "none". Card: "#/card/SL-114"; the identifier is read in any letter case.
  An address with no "#" part is Board with no filter. Each other address is Missing.Page.
  A part with another name is dropped. If a part occurs two times, the last one counts. A part
  with a bad percent code is dropped. A label or a person in another letter case names
  nothing ("labels=Bug" is dropped). Text after "?" in a card address is dropped.
WEB-2 Window title. Board: "Slate". Card.Ready: "SL-112 Document the webhook API · Slate".
  Card.Loading and Card.Failed: "SL-112 · Slate". Missing: "Not found · Slate".
WEB-3 Strings. The filter field has the placeholder "Filter cards (press /)". The comment field
  has the placeholder "Add a comment".
WEB-4 Bindings. "Card" means focus is on a card. "Outside text" means focus is not in a field.
  intent                   context         binding
  open-home                any             activate link "Slate"
  go-back                  any             browser Back
  go-forward               any             browser Forward
  reload                   any             browser reload
  enter-address            any             address bar
  dismiss                  any             Escape
  undo                     outside text    Control+Z or Command+Z
  notice-action            any             activate the action of the notice
  dismiss-notice           any             activate "Dismiss"
  retry-place              any             activate "Try again"
  ask-filter               outside text    "/"
  change-filter-text       filter field    type
  commit-filter            filter field    Enter
  toggle-label-filter      any             activate the toggle
  toggle-assignee-filter   any             activate the toggle
  clear-filters            any             activate "Clear filters" or "Show all cards"
  focus-card               any             pointer press on the card, or Tab to the focus stop
  move-focus               card            Up, Down, Left, Right; Home for first; End for last
  open-card                card            Enter
  open-card                any             pointer click on the title of the card
  toggle-select            card            "x"
  toggle-select            any             pointer click on the toggle of the card
  select-column            card            Shift+"x", for the column of the card
  select-column            any             activate "Select all"
  clear-selection          any             activate "Clear selection"
  bulk-move                any             activate the action of the column
  bulk-label               any             activate the toggle of the label
  pick-up                  card            Space
  pick-up                  any             pointer press on a card and a move of 4 px or more
  carry                    card            Up, Down, Left, Right
  carry-to                 any             pointer move while pressed: the column under the pointer;
                                           the position is the number of other visible cards
                                           of the column whose middle is above the pointer, plus 1
  drop                     card            Space or Enter
  drop                     any             pointer release over a column
  cancel-carry             any             pointer release outside every column; a pointer that
                                           the platform cancels; Escape (DIS-T1.1)
  delete-card              card            Delete or Backspace
  delete-card              any             activate "Delete card" (Card place)
  retry-column             any             activate "Retry" of the column
  go-up                    any             activate the up-link; Escape (DIS-T1.8)
  edit-title               any             activate "Edit title"
  change-title-text        title field     type
  commit-title             title field     Enter
  leave-title              title field     Tab, Shift+Tab, or a pointer press outside the field
  toggle-label             any             activate the toggle
  choose-assignee          any             activate the choice
  edit-description         any             activate "Edit description"
  change-description-text  description field  type; Enter makes a new line
  commit-description       description field  Control+Enter or Command+Enter
  commit-description       any             activate "Save"
  cancel-description       any             activate "Cancel"; Escape (DIS-T1.6)
  change-comment-text      comment field   type; Enter makes a new line
  commit-comment           comment field   Control+Enter or Command+Enter
  commit-comment           any             activate "Add comment"
  retry-comments           any             activate "Retry" of the comments
  open-board-link          any             activate "Go to the board"
  "Activate" is a pointer click, or Enter or Space with focus on the control.
WEB-5 Roles. place title: heading of level 1. heading: heading of level 2. up-link, link:
  link. action: button. toggle: button with a pressed state (true, false, mixed); the toggle
  of a card item is a checkbox. choice: radio in a radio group. field: text box; the filter
  field is a search box. column: region with the column name. card: group with the name
  "SL-101 Export board as CSV". notice: status for Info and alert for Error, with the name
  "Notice". alert: alert. status line: status. group: group with its name.
WEB-6 Tab order. Board: home link; filter field; label toggles; assignee toggles; "Clear
  filters"; the selection bar; then for each column "Select all" (or "Retry"); the focus stop
  comes after "Select all" of its column. The controls inside a card item are not Tab stops.
  Card: home link; up-link; "Edit title"; label toggles; assignee choices; "Edit description";
  comment field; "Add comment"; "Delete card".
WEB-7 When Title.Editing starts, all of the draft is selected.
WEB-8 Pointer. A press on a card that does not move 4 px gives focus to the card. A drag
  selects no text. A click on the title of a card with Control, Command or Shift, or with
  the middle button, keeps the platform default (a new tab). A press on the toggle of a card
  starts no carry. The click that ends a drag opens no card.
WEB-9 History. The browser keeps the scroll position and the "opened from the board" mark with
  each history entry, also across a reload. After a reload the scroll is at the top.
WEB-10 Sizes. Column width 260 px. Card and Missing: maximum width 720 px. Notice: 16 px from
  the bottom and from the start side, maximum width 560 px. Focus ring 2 px with 2 px offset.
  Type: place title 22 px, heading 16 px, text 15 px, quiet text 13 px, marks 12 px.
WEB-11 Tokens. background #f4f3ef; surface #ffffff; well #e6e3db; line #d2cfc7; text #1c1d1f;
  muted #5c6168; accent #1f5fbf; on accent #ffffff; danger #b3261e; inverse #1c1d1f;
  on inverse #f4f3ef. There is one theme.
WEB-12 Harness (fixture/harness.md). Before load, the adapter sets
  window.__slateHarness = { clock: "manual", profile: "<name>" }. After load, window.__slate has
  advance(ms), requests() (a list of { op, at }), announcements (a list of texts) and busy()
  (true while a Back that Slate asked for is not done).
WEB-13 Adaptations: none. Every rule applies.
```
