# Scenarios: filter

```text
SCN-FLT-1 verifies FLT-1, FLT-2, FLT-8, DAT-4, DAT-5, DAT-3
Given start at board.
After 2200 ms.
Remember history depth as D.
When change-filter-text "  fix   login ".
Then action "Clear filters" is shown.
After 249 ms.
Then address board.
Then text "27 cards" is shown.
After 1 ms.
Then address board text "fix login".
Then history depth is D.
Then text "2 of 27 cards" is shown.
Then announcement "2 of 27 cards".
Then column "Backlog" cards SL-102.
Then column "Ready" cards SL-111.
Then text "1 of 10 cards" is shown.
Then text "No matching cards" is shown.
Then text "No cards" is shown.
Then field "Filter cards" has text "  fix   login ".

SCN-FLT-2 verifies FLT-4, FLT-5, FLT-6, DAT-5, TSK-7
Given start at board.
After 2200 ms.
Remember history depth as D.
When toggle-label-filter ui.
When toggle-label-filter bug.
Then address board labels bug,ui.
Then text "4 of 27 cards" is shown.
When toggle-assignee-filter Unassigned.
When toggle-assignee-filter "Ana Ruiz".
Then address board labels bug,ui assignees "Ana Ruiz",Unassigned.
Then column "Backlog" cards SL-109.
Then toggle "bug" in "Labels" is on.
When clear-filters.
Then address board.
Then text "27 cards" is shown.
Then focus field "Filter cards".
Then history depth is D.
Then toggle "bug" in "Labels" is off.

SCN-FLT-3 verifies DAT-5, FLT-3, FLT-6
Given start at board.
After 2200 ms.
When change-filter-text "SL-11".
When commit-filter.
Then text "10 of 27 cards" is shown.
Then place title "Board".
When change-filter-text "download".
When commit-filter.
Then text "0 of 27 cards" is shown.
Then text "No cards match these filters." is shown.
When clear-filters.
Then text "27 cards" is shown.
Then no text "No cards match these filters.".

SCN-FLT-4 verifies FLT-7, DIS-T1.2, DIS-T1.3, FCS-1
Given start at board.
After 2200 ms.
Given focus on card SL-104.
When ask-filter.
Then focus field "Filter cards".
When change-filter-text "login".
When dismiss.
Then field "Filter cards" has text "".
Then address board.
Then focus field "Filter cards".
When dismiss.
Then focus card SL-104.
```
