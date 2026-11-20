# Scenarios: delete

```text
SCN-DEL-1 verifies DEL-1, DEL-2, DEL-3, DEL-5, TSK-6
Given start at board.
After 2200 ms.
Given focus on card SL-101.
When delete-card.
Then column "Backlog" starts SL-102, SL-103.
Then notice "Deleted SL-101." with "Undo".
Then focus card SL-102.
Then text "26 cards" is shown.
Then requests deleteCard 0.
When undo.
Then column "Backlog" starts SL-101, SL-102.
Then focus card SL-101.
Then no notice.
After 20000 ms.
Then requests deleteCard 0.
When delete-card.
After 7999 ms.
Then requests deleteCard 0.
After 1 ms.
Then requests deleteCard 1.
Then no notice.

SCN-DEL-2 verifies DEL-2, DEL-4, DAT-8, NTC-1
Given start at board.
After 2200 ms.
Given focus on card SL-125.
When delete-card.
Then focus card SL-126.
Given focus on card SL-124.
When delete-card.
Then notice "Deleted SL-124." with "Undo".
Then requests deleteCard 1.
After 400 ms.
Then notice "Couldn't delete SL-125. It is back in Done." with "Retry".
Then column "Done" cards SL-120, SL-121, SL-122, SL-123, SL-126, SL-125, SL-127.
Then requests deleteCard 2.
When notice-action.
Then column "Done" cards SL-120, SL-121, SL-122, SL-123, SL-126, SL-127.
Then no notice.
Then requests deleteCard 3.
After 400 ms.
Then no notice.

SCN-DEL-3 verifies DEL-T1.1, DEL-5, NAV-T1.3
Given start at board.
After 2200 ms.
Remember history depth as D.
When open-card SL-110.
When delete-card.
Then place title "Board".
Then history depth is D plus 1.
Then focus place title.
Then notice "Deleted SL-110." with "Undo".
When go-forward.
Then place title "Card not found".
When undo.
Then place title "Archive cards older than a year".

SCN-DEL-4 verifies DEL-T1.2, COL-4
Given start at card SL-110.
After 400 ms.
Remember history depth as D.
When delete-card.
Then place title "Board".
Then address board.
Then history depth is D.
After 2200 ms.
Then column "Backlog" cards SL-101, SL-102, SL-103, SL-104, SL-105, SL-106, SL-107, SL-108, SL-109.
Then text "26 cards" is shown.

SCN-DEL-5 verifies DEL-1
Given start at board.
After 2200 ms.
When toggle-label-filter blocked.
Given focus on card SL-117.
When delete-card.
Then focus place title.
Then text "0 of 26 cards" is shown.
```
