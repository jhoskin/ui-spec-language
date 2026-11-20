# Extraction probe log

Extraction step 6. The reference build was driven in a browser with a controlled clock and injected faults. Each action is followed by the address, the history depth, the focus, the vertical scroll, the notice and the new announcements. `tools/dev/probe-reference.mjs` writes this log.

```text
== First paint and Tab order on the board
  first paint
      address #/ depth 2 focus none scrollY 0
  advance 400
      address #/ depth 2 focus none scrollY 0
  advance 1800
      address #/ depth 2 focus none scrollY 0 said ["27 cards"]
  Tab 1
      address #/ depth 2 focus a "Slate" scrollY 0
  Tab 2
      address #/ depth 2 focus input "Filter cards" scrollY 0
  Tab 3
      address #/ depth 2 focus button "bug" scrollY 0
  Tab 4
      address #/ depth 2 focus button "ui" scrollY 0
  Tab 5
      address #/ depth 2 focus button "api" scrollY 0
  Tab 6
      address #/ depth 2 focus button "docs" scrollY 0
  Tab 7
      address #/ depth 2 focus button "perf" scrollY 0
  Tab 8
      address #/ depth 2 focus button "blocked" scrollY 0
  Tab 9
      address #/ depth 2 focus button "Ana Ruiz" scrollY 0
  Tab 10
      address #/ depth 2 focus button "Ben Okafor" scrollY 0
  Tab 11
      address #/ depth 2 focus button "Chloé Martin" scrollY 0
  Tab 12
      address #/ depth 2 focus button "Dev Patel" scrollY 0
  Tab 13
      address #/ depth 2 focus button "Mika Ito" scrollY 0
  Tab 14
      address #/ depth 2 focus button "Unassigned" scrollY 0
  Tab 15
      address #/ depth 2 focus button "Select all in Backlog" scrollY 0
  Tab 16
      address #/ depth 2 focus group "SL-101 Export board as CSV" scrollY 0

== Pointer on a card
  click the card body of SL-104
      address #/ depth 2 focus group "SL-104 Rate limit the search API" scrollY 0 said ["27 cards"]
  click the check box of SL-105
      address #/ depth 2 focus group "SL-105 Write onboarding guide" scrollY 0
  key x
      address #/ depth 2 focus group "SL-105 Write onboarding guide" scrollY 0
  Tab
      address #/ depth 2 focus button "Select all in Ready" scrollY 0
  Shift+Tab
      address #/ depth 2 focus group "SL-105 Write onboarding guide" scrollY 0
  click the title of SL-104
      address #/card/SL-104 depth 3 focus h1 "Rate limit the search API" scrollY 0
  browser Back
      address #/ depth 3 focus group "SL-104 Rate limit the search API" scrollY 0
  browser Forward
      address #/card/SL-104 depth 3 focus h1 "Rate limit the search API" scrollY 0
  reload
      address #/card/SL-104 depth 3 focus none scrollY 0
  click up-link
      address #/ depth 3 focus h1 "Board" scrollY 0
  advance 2200
      address #/ depth 3 focus h1 "Board" scrollY 0 said ["27 cards"]

== Drag, Escape during a drag, drop outside
  drag SL-102 over In progress top: SL-102 SL-118 SL-119
      address #/ depth 2 focus group "SL-102 Fix login redirect loop" scrollY 0 said ["27 cards"]
  Escape
      address #/ depth 2 focus group "SL-102 Fix login redirect loop" scrollY 0
  pointer up: Backlog SL-101 SL-102 SL-103 SL-104 SL-105 SL-106 SL-107 SL-108 SL-109 SL-110
      address #/ depth 2 focus group "SL-102 Fix login redirect loop" scrollY 0
  drop on the filter bar: Backlog SL-101 SL-102 SL-103 SL-104 SL-105 SL-106 SL-107 SL-108 SL-109 SL-110
      address #/ depth 2 focus group "SL-102 Fix login redirect loop" scrollY 0

== Scroll and Back, short window
  focus SL-109 by keys
      address #/ depth 2 focus group "SL-109 Search results flicker on slow ne" scrollY 837 said ["27 cards"]
  open (Enter)
      address #/card/SL-109 depth 3 focus h1 "Search results flicker on slow networks" scrollY 0
  go up (Escape)
      address #/ depth 3 focus group "SL-109 Search results flicker on slow ne" scrollY 837
  header link on the unfiltered board
      address #/ depth 3 focus a "Slate" scrollY 0
  type a filter
      address #/?q=api depth 3 focus input "Filter cards" scrollY 0 said ["2 of 27 cards"]
  header link on the filtered board
      address #/ depth 3 focus h1 "Board" scrollY 0
  browser Back
      address #/?q=api depth 3 focus h1 "Board" scrollY 0
  enter address #/card/SL-126
      address #/card/SL-126 depth 3 focus h1 "Card detail page" scrollY 0
  go up (Escape)
      address #/?q=api depth 4 focus h1 "Board" scrollY 0
  enter address #/nowhere
      address #/nowhere depth 5 focus h1 "Page not found" scrollY 0
  browser Back
      address #/?q=api depth 5 focus h1 "Board" scrollY 0

== Notice and focus
  Delete on SL-101
      address #/ depth 2 focus group "SL-102 Fix login redirect loop" scrollY 0 notice [Deleted SL-101. | Undo] said ["27 cards","Deleted SL-101."]
  focus Undo, then advance 8000
      address #/ depth 2 focus h1 "Board" scrollY 0
  advance 400
      address #/ depth 2 focus h1 "Board" scrollY 0
  carry SL-107 right and drop
      address #/ depth 2 focus group "SL-107 Migrate avatars to object storage" scrollY 0
  advance 400 (move fails)
      address #/ depth 2 focus group "SL-107 Migrate avatars to object storage" scrollY 0 notice [Couldn't move SL-107. It is back in Backlog. | Retry | Dismiss] said ["Couldn't move SL-107. It is back in Backlog."]
  click Dismiss
      address #/ depth 2 focus h1 "Board" scrollY 0
  Control+z with no notice
      address #/ depth 2 focus h1 "Board" scrollY 0

== Card place by keys
  first paint
      address #/card/SL-120 depth 2 focus none scrollY 0
  advance 400
      address #/card/SL-120 depth 2 focus none scrollY 0
  advance 300 (comments fail)
      address #/card/SL-120 depth 2 focus none scrollY 0
  Tab 1
      address #/card/SL-120 depth 2 focus a "Slate" scrollY 0
  Tab 2
      address #/card/SL-120 depth 2 focus a "← Board" scrollY 0
  Tab 3
      address #/card/SL-120 depth 2 focus button "Edit title" scrollY 0
  Tab 4
      address #/card/SL-120 depth 2 focus button "bug" scrollY 0
  Tab 5
      address #/card/SL-120 depth 2 focus button "ui" scrollY 0
  Tab 6
      address #/card/SL-120 depth 2 focus button "api" scrollY 0
  click Edit title, then Escape
      address #/card/SL-120 depth 2 focus h1 "Set up CI pipeline" scrollY 0
  click Edit description, type, click the heading
      address #/card/SL-120 depth 2 focus none scrollY 0
  Escape with focus on the body
      address #/card/SL-120 depth 2 focus button "Edit description" scrollY 0
```
