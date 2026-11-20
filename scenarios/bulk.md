# Scenarios: bulk actions

```text
SCN-BLK-1 verifies BLK-T1, BLK-T2.2, BLK-T2.3, MOV-3, DAT-13, DAT-7
Given start at board.
After 2200 ms.
When toggle-select SL-112.
When toggle-select SL-102.
When toggle-select SL-101.
When bulk-move "In progress".
Then column "In progress" cards SL-118, SL-119, SL-101.
Then card SL-101 has mark "Saving…".
Then text "2 selected" is shown.
Then no notice.
Then requests moveCards 1.
After 400 ms.
Then notice "Moved 1 of 3 cards to In progress. In progress is full (3 cards)." with "Undo".
When bulk-move "In progress".
Then notice "In progress is full (3 cards)." with no action.
Then requests moveCards 1.
When bulk-move Review.
After 400 ms.
Then notice "Moved 2 cards to Review." with "Undo".
Then column "Review" cards SL-102, SL-112.
Then action "Clear selection" is absent.
When notice-action.
Then column "Backlog" starts SL-102, SL-103.
Then column "Ready" starts SL-111, SL-112.
Then action "Clear selection" is absent.
Then focus card SL-102.
After 400 ms.
Then no notice.

SCN-BLK-2 verifies BLK-T2.1, DAT-8, DAT-13, TSK-3
Given start at board.
After 2200 ms.
When toggle-select SL-106.
When toggle-select SL-107.
When toggle-select SL-108.
When bulk-move Review.
Then action "Clear selection" is absent.
After 400 ms.
Then notice "Moved 2 of 3 cards to Review. Couldn't move SL-107." with "Retry".
Then column "Review" cards SL-106, SL-108.
Then column "Backlog" cards SL-101, SL-102, SL-103, SL-104, SL-105, SL-109, SL-107, SL-110.
Then text "1 selected" is shown.
Then card SL-107 is selected.
When notice-action.
After 400 ms.
Then notice "Moved 1 card to Review." with "Undo".
Then column "Review" cards SL-106, SL-108, SL-107.

SCN-BLK-3 verifies BLK-T3, BLK-4, DAT-11, DAT-13
Given start at board.
After 2200 ms.
When toggle-select SL-109.
When toggle-select SL-110.
When toggle-select SL-104.
Then toggle "perf" in "Label selected" is mixed.
Then toggle "docs" in "Label selected" is off.
When bulk-label docs.
Then no notice.
Then requests saveLabels 1.
After 300 ms.
Then notice "Added "docs" to 2 of 3 cards. A card can have at most 3 labels." with no action.
Then text "3 selected" is shown.
When toggle-select SL-109.
Then toggle "docs" in "Label selected" is on.
When bulk-label docs.
After 300 ms.
Then notice "Removed "docs" from 2 cards." with no action.
When toggle-select SL-104.
When toggle-select SL-110.
When toggle-select SL-109.
When bulk-label blocked.
Then notice "A card can have at most 3 labels." with no action.
Then requests saveLabels 2.

SCN-BLK-4 verifies BLK-T1.1, SEL-4
Given start at board.
After 2200 ms.
When toggle-select SL-118.
When bulk-move "In progress".
Then no notice.
Then requests moveCards 0.
Then text "1 selected" is shown.
When toggle-label-filter ui.
When bulk-label ui.
Then action "Clear selection" is absent.
Then column "In progress" cards none.
```
