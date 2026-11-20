# Fixture

The fixture is a fixed data set, a service double and a controlled clock. A
build that runs on the fixture gives the same result on each run.

The files of the fixture are:

- `data.json`: the data set.
- `service.json`: the latency of each operation, the faults and the profiles.
- `vectors.json`: timed calls and the replies that a correct service double gives.
- `harness.md`: the controls that a build gives to an adapter.

Where this file and a JSON file disagree, the JSON file is correct.

## Data set

```text
FIX-1 Board "Slate". Columns in order: Backlog, Ready, In progress, Review, Done.
  In progress has a limit of 3 cards. The other columns have no limit.
FIX-2 People in order: Ana Ruiz, Ben Okafor, Chloé Martin, Dev Patel, Mika Ito.
  The current user is Mika Ito.
FIX-3 Labels in order: bug, ui, api, docs, perf, blocked.
FIX-4 27 cards, SL-101 to SL-127, in this order:
  Backlog 10: SL-101 to SL-110.   Ready 7: SL-111 to SL-117.
  In progress 2: SL-118, SL-119.  Review 0.   Done 8: SL-120 to SL-127.
FIX-5 Example cards:
  SL-101 "Export board as CSV", label api, no assignee, no comments.
  SL-102 "Fix login redirect loop", label bug, Ana Ruiz, 2 comments.
  SL-109 "Search results flicker on slow networks", labels bug, ui, perf, Ana Ruiz, 1 comment.
  SL-110 "Archive cards older than a year", no labels, no assignee, no description.
  SL-114 "Card title overflows on narrow screens", labels bug, ui, Mika Ito, 2 comments.
    Its first comment: Dev Patel, 2026-11-10T12:44:00Z, "I can reproduce this."
FIX-6 The clock starts at 2026-11-20T09:00:00Z.
```

## Service double

The service double holds the session data. A save that succeeds changes the
data that a later load returns. The double starts from the data set at each
start and at each reload.

```text
FIX-7 Operations, with the reply data of each:
  loadBoard {}                      columns (id, name, limit), people (id, name), labels, currentUser
  loadColumn {column}               cards in order: id, title, description, labels, assignee, comments (a count)
  loadCard {card}                   card (as above, with its column), or card null if there is no such card
  loadComments {card}               comments in order: author, at, text
  moveCards {moves: [{card, column, index}]}   results: [{card, ok}], one for each move
  saveTitle {card, title}           nothing
  saveDescription {card, description}   nothing
  saveLabels {changes: [{card, labels}]}   nothing
  saveAssignee {card, assignee}     nothing (assignee null means no assignee)
  addComment {card, text}           comment: author (the current user), at (the time of the reply), text
  deleteCard {card}                 nothing
FIX-8 A reply is {ok: true, data} or {ok: false}. A failed call changes no data.
FIX-9 moveCards applies its moves in order. For each move, the double takes the card out of its
  column and puts it in the target column at "index", or at the end if the index is too large.
  A fault fails one move only. The other moves of the call are saved.
FIX-10 Times are UTC with whole seconds: "2026-11-20T09:01:00Z".
FIX-11 Latency in ms: loadBoard 400; loadColumn 300; loadCard 250; loadComments 300;
  moveCards 400; saveTitle 400; saveDescription 400; saveLabels 300; saveAssignee 300;
  addComment 500; deleteCard 400.
FIX-12 Slow: loadColumn of Done takes 1800 ms.
FIX-13 Two calls with replies at the same time get their replies in the order of the calls.
```

## Faults

A fault makes one reply fail. Each fault is used one time for each start. A
fault is used when the reply is made.

```text
FIX-14 Faults of profile "default":
  a  a move of SL-107 (in moveCards, that move only)
  b  saveTitle with a title that contains "flaky", in any letter case
  c  addComment with a text that contains "flaky", in any letter case
  d  deleteCard of SL-125
  e  loadComments of SL-120
FIX-15 Profile "column-down": the faults of "default", and loadColumn of Ready.
FIX-16 Profile "board-down": the faults of "default", and loadBoard.
FIX-17 Profile "card-down": the faults of "default", and loadCard of any card.
FIX-18 Profile "empty": the board has its 5 columns and no cards. There are no faults.
FIX-19 No request is abandoned. A reply that comes when its place is not shown changes the data.
```

## Timelines

Each line gives the marks of one request on the clock. `@0` is the time of the
request.

```text
FIX-L1 board     @0 Board.Loading | @400 success: Board.Ready, and the 5 column requests start
                 failure: Board.Failed | retry: Board.Loading @0
FIX-L2 column    @0 Column.Loading | @1000 slow: line "Still loading…" | @300 success (Done: @1800)
                 failure: Column.Failed | retry: Column.Loading @0
FIX-L3 card      @0 Card.Loading | @250 success: Card.Ready when the board data is also there
                 failure: Card.Failed | retry: Card.Loading @0
FIX-L4 comments  @0 Comments.Loading | @300 success: Comments.None or Comments.Some
                 failure: Comments.Failed | retry: Comments.Loading @0
FIX-L5 move      @0 card at the new position, "Saving…" | @400 success: notice | failure: card back, error notice
FIX-L6 title, description   @0 new text, "Saving…" | @400 success: mark removed | failure (title): old text, error notice
FIX-L7 labels, assignee     @0 new value, "Saving…" | @300 success: mark removed
FIX-L8 comment   @0 comment at the end, "Sending…", field off | @500 success: time shown, field on
                 failure: comment removed, text back in the field
FIX-L9 delete    @0 card removed, notice | notice ends: request | @400 after that: success: nothing
                 failure: card back, error notice
```
