# Data rules

Each rule sits on data, not on a control. The example values come from the
fixture.

```text
DAT-1 [must] Card count words: "0 cards", "1 card", "27 cards".
DAT-2 [must] Count line. While a column is in Column.Loading: "Loading cards…". If not:
  Filter.Off: the total, "27 cards". Filter.On: the visible cards and the total,
  "4 of 27 cards", "0 of 1 card". The total counts the cards of the loaded columns. A column
  in Column.Failed counts 0: with Ready failed, "20 cards".
DAT-3 [must] Column count. Filter.Off: "10 cards", "0 cards". Filter.On: "1 of 10 cards".
DAT-4 [must] Filter text, written form: white space removed from the ends; each run of white
  space is one space. "  fix   login " -> "fix login". The field keeps the text as typed.
DAT-5 [must] Filter match. A card matches when all three parts match.
  Text: each word occurs in the title or in the identifier. Letter case is ignored. The
    description is not searched. "fix login" -> SL-102, SL-111. "sl-11" -> SL-110 to SL-119.
  Labels: the card has every label that is on. bug and ui -> SL-106, SL-109, SL-111, SL-114.
  Assignee: the card has one of the assignees that are on. "Unassigned" matches a card with
    no assignee. bug and ui with Ana Ruiz and Unassigned -> SL-109.
DAT-6 [must] Drop position. A carried card has a position among the visible cards of a column.
  At the top of the visible cards, the card goes to the top of the column, above each hidden
  card. At any other position, the card goes directly after the visible card that is above it.
  Backlog with label filter bug shows SL-102, SL-106, SL-109. Drop SL-106 at the top:
  Backlog starts SL-106, SL-101, SL-102.
DAT-7 [must] Limit. A column with a limit is full when its cards, hidden cards included, are as
  many as the limit. Text: "In progress is full (3 cards)."
DAT-8 [must] Return position. A card that goes back to a column goes to the position number it
  had there, counted in the column as it is now, or to the end if the column is shorter.
  Several cards go back in rising order of position.
  Done is SL-120 to SL-127. Delete SL-125 (position 6), then delete SL-124. The delete of
  SL-125 fails: Done is SL-120, SL-121, SL-122, SL-123, SL-126, SL-125, SL-127.
DAT-9 [must] Times are UTC and never relative: "10 Nov 2026, 12:44", "5 Nov 2026, 14:39".
  The day has no leading zero. The hour and the minute have two digits.
DAT-10 [must] Title, written form: white space removed from the ends; each run of white space
  is one space. A good title has 1 to 80 characters. "  A   flaky  title " -> "A flaky title".
DAT-11 [must] The labels of a card show in board order (FIX-3), not in the order added.
  A card has at most 3 labels. Add bug to SL-104 (api, perf): bug, api, perf.
DAT-12 [must] Board order: the columns in order (FIX-1), then the cards from the top.
DAT-13 [must] Count words in notices: "1 card", "2 cards"; "1 of 3 cards", "0 of 1 card".
DAT-14 [must] Comment count: "1 comment", "3 comments". A card item shows no count at 0.
DAT-15 [must] Description, written form: white space removed from the ends. It can be empty.
DAT-16 [must] Address parts. Board: the filter text (DAT-4), the labels that are on in board
  order, the assignees that are on in the order of people and then Unassigned. Card: the
  identifier in upper case. A value that names no label or no person is dropped. The modality
  sheet gives the written form.
DAT-17 [must] A comment has the name of its author. A new comment has the current user (FIX-2)
  and the time of the reply.
```
