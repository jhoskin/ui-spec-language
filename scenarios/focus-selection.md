# Scenarios: focus on cards and selection

```text
SCN-FCS-1 verifies FCS-2, FCS-3, DAT-12
Given start at board.
After 2200 ms.
Given focus on card SL-119.
When move-focus right.
Then focus card SL-121.
When move-focus left.
Then focus card SL-119.
When move-focus down.
Then focus card SL-119.
When move-focus left.
Then focus card SL-112.
When move-focus last.
Then focus card SL-117.
When move-focus right.
Then focus card SL-119.
When move-focus first.
When move-focus up.
Then focus card SL-118.
Given focus on card SL-101.
When move-focus left.
Then focus card SL-101.

SCN-SEL-1 verifies SEL-1, SEL-2, SEL-3, SEL-4, FLT-8
Given start at board.
After 2200 ms.
When toggle-select SL-101.
When toggle-select SL-102.
Then text "2 selected" is shown.
Then card SL-102 is selected.
Then focus card SL-102.
When toggle-label-filter bug.
Then text "1 selected" is shown.
When toggle-label-filter bug.
Then text "1 selected" is shown.
Then card SL-101 is not selected.
When select-column "In progress".
Then text "3 selected" is shown.
When select-column "In progress".
Then text "1 selected" is shown.
When toggle-select SL-102.
Then action "Clear selection" is absent.
When toggle-select SL-102.
When clear-selection.
Then action "Clear selection" is absent.
Then focus place title.

SCN-SEL-2 verifies DIS-T1.4, DIS-T1.9
Given start at board.
After 2200 ms.
When toggle-select SL-103.
When dismiss.
Then action "Clear selection" is absent.
Then focus card SL-103.
When dismiss.
Then focus card SL-103.
Then place title "Board".
```
