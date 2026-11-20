# Scenarios: carry and move

```text
SCN-CRY-1 verifies CRY-1, CRY-2, CRY-T1.3, MOV-1, MOV-3, NTC-5, PRP-4, TSK-2
Given start at board.
After 2200 ms.
Given focus on card SL-103.
When pick-up.
Then card SL-103 has mark "Moving".
When carry right.
Then column "Ready" starts SL-111, SL-112, SL-103, SL-113.
Then column "Backlog" starts SL-101, SL-102, SL-104.
Then requests moveCards 0.
When drop.
Then card SL-103 has mark "Saving…".
Then focus card SL-103.
Then no notice.
Then requests moveCards 1.
After 399 ms.
Then no notice.
After 1 ms.
Then notice "Moved SL-103 to Ready." with "Undo".
Then card SL-103 has no mark.
When undo.
Then column "Backlog" starts SL-101, SL-102, SL-103, SL-104.
Then no notice.
Then focus card SL-103.
After 400 ms.
Then no notice.
Then card SL-103 has no mark.
Then requests moveCards 2.

SCN-CRY-2 verifies CRY-2, CRY-5, CRY-T1.1, DIS-T1.1, CRY-6
Given start at board.
After 2200 ms.
Given focus on card SL-119.
When pick-up.
When carry down.
When carry right.
Then column "Review" cards SL-119.
When carry right.
Then column "Done" starts SL-119, SL-120, SL-121.
When carry right.
Then column "Done" starts SL-119, SL-120, SL-121.
When carry down.
Then column "Done" starts SL-120, SL-119, SL-121.
When delete-card.
Then card SL-119 has mark "Moving".
Then no notice.
When dismiss.
Then column "In progress" cards SL-118, SL-119.
Then requests moveCards 0.
Then no notice.
When pick-up.
When carry up.
When carry down.
When drop.
Then requests moveCards 0.
Then no notice.
Then card SL-119 has no mark.

SCN-CRY-3 [pointer] verifies CRY-3, CRY-T1.3, CRY-5
Given start at board.
After 2200 ms.
When pick-up SL-103 via pointer.
When carry-to Ready 3 via pointer.
Then column "Ready" starts SL-111, SL-112, SL-103.
When drop via pointer.
Then requests moveCards 1.
After 400 ms.
Then notice "Moved SL-103 to Ready." with "Undo".
When pick-up SL-104 via pointer.
When carry-to Done 1 via pointer.
When cancel-carry via pointer.
Then column "Backlog" starts SL-101, SL-102, SL-104.
Then requests moveCards 1.

SCN-CRY-4 verifies DAT-6, CRY-T1.3
Given start at board.
After 2200 ms.
When toggle-label-filter bug.
Then column "Backlog" cards SL-102, SL-106, SL-109.
Given focus on card SL-109.
When pick-up.
When carry up.
When drop.
After 400 ms.
Given focus on card SL-106.
When pick-up.
When carry up.
When carry up.
When drop.
After 400 ms.
When clear-filters.
Then column "Backlog" starts SL-106, SL-101, SL-102, SL-109, SL-103.

SCN-CRY-5 verifies CRY-T1.2, DAT-7, NTC-2
Given start at board.
After 2200 ms.
Given focus on card SL-111.
When pick-up.
When carry right.
When drop.
After 400 ms.
Then column "In progress" cards SL-111, SL-118, SL-119.
Given focus on card SL-112.
When pick-up.
When carry right.
When drop.
Then notice "In progress is full (3 cards)." with no action.
Then column "Ready" starts SL-112.
Then requests moveCards 1.
After 7999 ms.
Then notice "In progress is full (3 cards)." with no action.
After 1 ms.
Then no notice.

SCN-MOV-1 verifies MOV-2, DAT-8, NTC-3, NTC-4, CRY-1, PRP-2
Given start at board.
After 2200 ms.
Given focus on card SL-107.
When pick-up.
When carry right.
When drop.
Then column "Ready" cards SL-111, SL-112, SL-113, SL-114, SL-115, SL-116, SL-107, SL-117.
When pick-up.
Then card SL-107 has mark "Saving…".
After 400 ms.
Then notice "Couldn't move SL-107. It is back in Backlog." with "Retry".
Then column "Backlog" cards SL-101, SL-102, SL-103, SL-104, SL-105, SL-106, SL-107, SL-108, SL-109, SL-110.
After 60000 ms.
Then notice "Couldn't move SL-107. It is back in Backlog." with "Retry".
Then requests moveCards 1.
When notice-action.
Then no notice.
After 400 ms.
Then notice "Moved SL-107 to Ready." with "Undo".
Then requests moveCards 2.

SCN-MOV-2 verifies NTC-6, FOC-1, NTC-1
Given start at board.
After 2200 ms.
Given focus on card SL-107.
When pick-up.
When carry right.
When drop.
After 400 ms.
Then focus card SL-107.
When dismiss-notice.
Then no notice.
Then focus place title.
```

```text
SCN-MOV-3 verifies MOV-4, MOV-3, DAT-8
Given start at board.
After 2200 ms.
Given focus on card SL-108.
When pick-up.
When carry right.
When drop.
After 400 ms.
Then notice "Moved SL-108 to Ready." with "Undo".
When undo.
Then column "Backlog" cards SL-101, SL-102, SL-103, SL-104, SL-105, SL-106, SL-107, SL-108, SL-109, SL-110.
After 400 ms.
Then notice "Couldn't undo the move of SL-108." with "Retry".
Then column "Backlog" cards SL-101, SL-102, SL-103, SL-104, SL-105, SL-106, SL-107, SL-109, SL-110.
Then column "Ready" cards SL-111, SL-112, SL-113, SL-114, SL-115, SL-116, SL-117, SL-108.
When notice-action.
After 400 ms.
Then no notice.
Then column "Backlog" cards SL-101, SL-102, SL-103, SL-104, SL-105, SL-106, SL-107, SL-108, SL-109, SL-110.

SCN-CRY-6 verifies CRY-T1.1, DAT-6
Given start at board.
After 2200 ms.
When toggle-label-filter bug.
Given focus on card SL-102.
When pick-up.
When drop.
When clear-filters.
Then column "Backlog" starts SL-101, SL-102.
Then requests moveCards 0.
Then no notice.
```
