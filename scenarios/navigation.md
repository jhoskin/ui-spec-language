# Scenarios: navigation and memory

```text
SCN-NAV-1 verifies OPN-1, NAV-T1.4, NAV-T1.2, NAV-T3.1, PRP-1, FLT-3, FLT-7, TSK-1
Given start at board.
After 2200 ms.
Remember history depth as D.
When ask-filter.
When change-filter-text "webhook".
When commit-filter.
Then focus card SL-112.
When open-card SL-112.
Then place title "Document the webhook API".
Then address card SL-112.
Then history depth is D plus 1.
Then focus place title.
When go-up.
Then address board text "webhook".
Then history depth is D plus 1.
Then focus card SL-112.

SCN-NAV-2 verifies NAV-T3.2, NAV-3, NAV-T1.1, CRD-T1.6, MEM-T1
Given start at card SL-114.
Then focus none.
Remember history depth as D.
After 400 ms.
Then place title "Card title overflows on narrow screens".
When go-up.
Then address board.
Then history depth is D plus 1.
Then focus place title.

SCN-NAV-3 verifies NAV-T2, NAV-2, NAV-T1.3
Given start at board.
After 2200 ms.
Remember history depth as D.
When open-home.
Then history depth is D.
Then address board.
When toggle-label-filter bug.
When open-home.
Then history depth is D plus 1.
Then address board.
Then focus place title.
Then text "27 cards" is shown.
When go-back.
Then address board labels bug.
Then focus place title.
Then text "8 of 27 cards" is shown.

SCN-NAV-4 [web] verifies NAV-1, DAT-16, MIS-1
Given start at address "#/?who=none,zed,ana&labels=ui,nope,bug&x=1&q=%20fix%20%20login".
After 2200 ms.
Then address is "#/?q=fix+login&labels=bug,ui&who=ana,none".
Given start at address "#/card/sl-114".
Then address is "#/card/SL-114".
Given start at address "#/nowhere".
Then place title "Page not found".
Then text "The address may be mistyped or out of date." is shown.
Then address is "#/nowhere".
When open-board-link.
Then address board.
Then place title "Board".

SCN-NAV-5 verifies MEM-T1, SEL-4, NTC-3
Given start at board.
After 2200 ms.
When toggle-select SL-102.
When toggle-select SL-103.
Then text "2 selected" is shown.
Given focus on card SL-101.
When delete-card.
When open-card SL-102.
Then notice "Deleted SL-101." with "Undo".
When go-back.
Then no text "2 selected".
Then notice "Deleted SL-101." with "Undo".
When reload.
After 2200 ms.
Then no notice.
Then column "Backlog" starts SL-101, SL-102.
Then requests deleteCard 0.

SCN-NAV-6 verifies MEM-T1, NAV-T3.1
Given start at board.
After 2200 ms.
When open-card SL-104.
When reload.
After 400 ms.
Remember history depth as D.
When go-up.
Then address board.
Then history depth is D.
Then focus place title.

SCN-NAV-7 verifies CRD-T1.5, MIS-1
Given start at card SL-999.
After 400 ms.
Then place title "Card not found".
Then text "There is no card SL-999 on this board." is shown.
Then address card SL-999.
When dismiss.
Then place title "Card not found".

SCN-NAV-8 verifies NAV-T1.2, NAV-T1.4, NAV-T2.1
Given start at board.
After 2200 ms.
Then scroll is top.
Given focus on card SL-110.
Then card SL-110 is in view.
Then scroll is not top.
When open-card SL-110.
Then scroll is top.
When go-back.
Then focus card SL-110.
Then card SL-110 is in view.
Then scroll is not top.
When open-home.
Then scroll is top.
Then card SL-110 is not selected.
```
