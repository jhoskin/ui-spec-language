# Gate run 01

Set: open. Probes: 39, of which 39 are must-level.

Result: blocked by 8 must-level probes.

| Reader | Score, all probes | Score, must-level | Guesses | Ambiguities | Contradictions |
| --- | --- | --- | --- | --- | --- |
| control-haiku | 7 of 39 | 7 of 39 | 39 | 6 | 0 |
| control-opus | 15.5 of 39 | 15.5 of 39 | 39 | 6 | 0 |
| control-sonnet | 18 of 39 | 18 of 39 | 36 | 4 | 0 |
| haiku | 35 of 39 | 35 of 39 | 2 | 6 | 2 |
| opus | 37.5 of 39 | 37.5 of 39 | 2 | 5 | 0 |
| qwen | 0 of 39 | 0 of 39 | 0 | 0 | 0 |
| sonnet | 37 of 39 | 37 of 39 | 1 | 6 | 2 |

A probe that a control reader answers correctly marks a decision that convention carries.

## Wrong and split answers

### PRB-009 (must, filter)

- Open the address #/?labels=perf,nope,bug&q=%20search%20%20results directly with the default data and let the clock run 2200 ms.

Question: What is the address now, did the history grow, and which cards are shown?

- opus, grade 0.5, GUESS, cites NAV-1 DAT-16 WEB-1 DAT-4 DAT-5 FIX-5: The address becomes "#/?q=search+results&labels=bug,perf" and the history did not grow. SL-109 "Search results flicker on slow networks" is shown in Backlog. Any other matching cards cannot be known from the package, which lists only example cards.
- sonnet, grade 1, DERIVED, cites NAV-1 DAT-4 DAT-5 DAT-16 WEB-1 FIX-5: The address is rewritten to "#/?q=search+results&labels=bug,perf", and no history entry is added. "nope" is dropped once the board data is loaded. The one card shown is SL-109 (in Backlog).
- haiku, grade 0.5, GUESS, cites NAV-1 DAT-16 DAT-4 DAT-5 FIX-3 FIX-5: The address is "#/?q=search+results&labels=bug,perf": nope is dropped, the labels are in board order, and the entry is rewritten, so the history did not grow. SL-109 is shown. The package does not give the titles or labels of the other cards, so the rest of the visible set cannot be determined.
- qwen, grade 0, none, cites nothing: (no answer)

### PRB-017 (must, selection and bulk actions)

- Start at the board address #/ with the default data and let the clock run 2200 ms, so that every column has loaded.
- Select SL-106, SL-107 and SL-108 with the x key (focus SL-106, x, ArrowDown, x, ArrowDown, x).
- Click the button "Review" in the "Move selected to" group, then let the clock run 400 ms. The service fails the move of SL-107.

Question: What does the notice say, what is selected, and what is the order of Backlog and Review?

- opus, grade 1, STATED, cites BLK-T2.1 DAT-8 SCN-BLK-2: The notice reads "Moved 2 of 3 cards to Review. Couldn't move SL-107." with "Retry". Only SL-107 is selected ("1 selected"). Backlog is SL-101, SL-102, SL-103, SL-104, SL-105, SL-109, SL-107, SL-110. Review is SL-106, SL-108.
- sonnet, grade 1, DERIVED, cites BLK-T2.1 DAT-8 FIX-14 FIX-9: The notice is "Moved 2 of 3 cards to Review. Couldn't move SL-107." with action "Retry" (no Undo). SL-107 is selected again ("1 selected"). Review is SL-106, SL-108. Backlog is SL-101, SL-102, SL-103, SL-104, SL-105, SL-109, SL-107, SL-110.
- haiku, grade 0.5, DERIVED, cites BLK-T1 BLK-T2 DAT-8 DAT-13 FIX-9 FIX-14: The notice reads "Moved 2 of 3 cards to Review. Couldn't move SL-107." with the action "Retry". Only SL-107 is selected ("1 selected"). Review is SL-106, SL-108. Backlog is SL-101, SL-102, SL-103, SL-104, SL-105, SL-109, SL-107, SL-110.
- qwen, grade 0, none, cites nothing: (no answer)

### PRB-019 (must, selection and bulk actions)

- Start at the board address #/ with the default data and let the clock run 2200 ms, so that every column has loaded.
- Put focus on SL-111 and press Shift+X, so that all 7 cards of Ready are selected.
- Click the label filter button "bug", then click "Clear filters".

Question: How many cards are selected now?

- opus, grade 0.5, GUESS, cites SEL-2 SEL-4 FLT-8 DAT-5: Only the Ready cards with label bug stay selected; they are not selected again after the filters are cleared. The package confirms SL-111 and SL-114 have bug, so likely 2 ("2 selected"). The exact number depends on fixture data not given.
- sonnet, grade 0, GUESS, cites SEL-4 FLT-8 SEL-2 DAT-5: Only the bug-labelled Ready cards that stayed visible remain selected. This is at least SL-111 and SL-114. SEL-4 removed the hidden cards, and clearing the filters does not select them again. The exact count depends on how many Ready cards have bug, which the package does not list.
- haiku, grade 0, GUESS, cites SEL-4 FLT-8 FLT-6 DAT-5 FIX-5: The count cannot be fixed from the package. After Clear filters the selection is the Ready cards that were visible under the bug filter and still have the label bug. SL-111 and SL-114 have bug, so the count is at least 2. The labels of the other Ready cards are not given.
- qwen, grade 0, none, cites nothing: (no answer)

### PRB-025 (must, save failures, rollback and retry)

- Start at the board address #/ with the default data and let the clock run 2200 ms, so that every column has loaded.
- Put focus on SL-107, press Space, ArrowRight, Space. The service fails this move. Let the clock run 400 ms.

Question: Where is SL-107, which part has focus, and what does the notice say?

- opus, grade 1, DERIVED, cites MOV-2 DAT-8 FOC-1 CRY-T1.3 SCN-MOV-1: SL-107 is back in Backlog at position 7, so Backlog is in its original order SL-101 to SL-110. Focus stays on card SL-107. The error notice reads "Couldn't move SL-107. It is back in Backlog." with "Retry" (and "Dismiss").
- sonnet, grade 1, DERIVED, cites MOV-2 DAT-8 FOC-1 FIX-14: SL-107 is back in Backlog at position 7, between SL-106 and SL-108. Focus is on card SL-107. The notice is Error "Couldn't move SL-107. It is back in Backlog." with action "Retry" (and "Dismiss").
- haiku, grade 0.5, DERIVED, cites MOV-2 DAT-8 FOC-1 FIX-14: SL-107 is back in Backlog at position 7, between SL-106 and SL-108. Focus is on card SL-107. The notice reads "Couldn't move SL-107. It is back in Backlog." with the action "Retry".
- qwen, grade 0, none, cites nothing: (no answer)

### PRB-028 (must, save failures, rollback and retry)

- Start at the board address #/ with the default data and let the clock run 2200 ms, so that every column has loaded.
- Put focus on SL-108, press Space, ArrowRight, Space and let the clock run 400 ms (the move succeeds).
- Press Control+Z. The service fails this second move of SL-108. Let the clock run 400 ms.

Question: Where is SL-108, and what does the notice say?

- opus, grade 1, STATED, cites MOV-3 MOV-4 SCN-MOV-3: SL-108 is in Ready, at the end after SL-117. The notice reads "Couldn't undo the move of SL-108." with "Retry".
- sonnet, grade 1, DERIVED, cites MOV-3 MOV-4 FIX-14: SL-108 is in Ready, at the end after SL-117. The notice is Error "Couldn't undo the move of SL-108." with action "Retry".
- haiku, grade 0.5, DERIVED, cites NTC-5 MOV-3 MOV-4 FIX-14 DAT-8: SL-108 is in Ready, at the end (position 8), not in Backlog. The notice reads "Couldn't undo the move of SL-108." with the action "Retry".
- qwen, grade 0, none, cites nothing: (no answer)

### PRB-035 (must, save failures, rollback and retry)

- Start at the board address #/ with the default data and let the clock run 2200 ms, so that every column has loaded.
- Put focus on SL-125 and press Delete. Let the clock run 8000 ms, then 400 ms more. The service fails this delete.

Question: Where is SL-125, and what does the notice say?

- opus, grade 1, DERIVED, cites DEL-2 DEL-4 DAT-8 FIX-14: SL-125 is back in Done at position 6, so Done is SL-120 to SL-127 in its original order. The error notice reads "Couldn't delete SL-125. It is back in Done." with "Retry".
- sonnet, grade 1, DERIVED, cites DEL-2 DEL-4 DAT-8 FIX-14: SL-125 is back in Done at position 6, between SL-124 and SL-126. The notice is Error "Couldn't delete SL-125. It is back in Done." with action "Retry".
- haiku, grade 0.5, DERIVED, cites DEL-4 DAT-8 FIX-14 FIX-11: SL-125 is back in Done at position 6, between SL-124 and SL-126. The notice reads "Couldn't delete SL-125. It is back in Done." with the action "Retry".
- qwen, grade 0, none, cites nothing: (no answer)

### PRB-048 (must, comments)

- Open the address #/card/SL-120 directly and let the clock run 700 ms. The service fails the first comment load of SL-120.
- Click the "Retry" button in the Comments section and let the clock run 300 ms.

Question: What does the Comments section show now?

- opus, grade 0.5, STATED, cites CRD-4 CRD-3 SCN-CRD-3: The count "2 comments" and the two comments of SL-120, oldest first, each with its author and time.
- sonnet, grade 0.5, DERIVED, cites CRD-4 CRD-3 FIX-14 SCN-CRD-3: Comments.Some shows "2 comments", with the two comments oldest first and the comment field enabled.
- haiku, grade 0.5, DERIVED, cites CRD-3 CRD-4 FIX-14 SCN-CRD-3: Comments show as loaded: the count reads "2 comments", with the comments oldest first. The retry succeeded.
- qwen, grade 0, none, cites nothing: (no answer)

### PRB-049 (must, navigation, history, reload and unknown addresses)

- Open the address #/?labels=bug directly with the default data and let the clock run 2200 ms.
- Put focus on SL-114 and press Enter. Let the clock run 300 ms. Press Escape.

Question: What is the address, how did the history change, and which part has focus?

- opus, grade 1, DERIVED, cites DIS-T1.8 NAV-T3.1 NAV-T1.2 PRP-1: The address is "#/?labels=bug". Escape went Back, so the depth is unchanged from the card (still one more than before the card was opened). Focus is on card SL-114, which is in view.
- sonnet, grade 0.5, DERIVED, cites DIS-T1.8 NAV-T3.1 NAV-T1.2 OPN-1: The address is "#/?labels=bug". The history did not grow, because go-up does a Back, so the position moved back one entry. Focus is on card SL-114.
- haiku, grade 1, DERIVED, cites OPN-1 DIS-T1 NAV-T3 NAV-T1 MEM-T1: The address is "#/?labels=bug". Opening the card added one history entry. Back returned to the board entry, and no entry was removed. Focus is on card SL-114, which is visible.
- qwen, grade 0, none, cites nothing: (no answer)

## Ambiguities and contradictions that the readers listed

- opus, ambiguity: WEB-4 carry-to counts the cards 'whose middle is above the pointer'. A pointer exactly at a card's middle is not clearly above or not above, and it is unclear whether the middle is measured before or after the layout shifts for the carried card.
- opus, ambiguity: FOC-1 does not say whether the place title of Board.Loading and Board.Ready is the same part when the 'Try again' button is removed and the board then loads.
- opus, ambiguity: Most card data (labels, comments) is in data.json, which is not part of the package. So the sets of matching cards, such as the Ready cards with bug or the cards matching 'search results', cannot be fully determined.
- opus, ambiguity: DIS-T1.5 needs focus in the title field. Escape while Title.Editing with focus elsewhere falls to row 8 (go up), and it is unclear whether the open title edit is then saved, dropped or committed.
- opus, ambiguity: CRD-T1 row 6 says 'request the board data if not yet requested', while BRD-1 says columns are requested when Board.Ready shows. It is unclear whether a board load that answers while Card is shown counts as Board 'shown' for BRD-1.
- sonnet, ambiguity: PRB-019: the fixture data.json is not in the package, so the exact bug-labelled cards of Ready are not known.
- sonnet, ambiguity: PRB-044: it is not stated how many comments SL-110 has. I assumed none.
- sonnet, ambiguity: PRB-023: whether a pointer exactly on a card's middle counts as the middle being above the pointer. Both readings give position 3 here.
- sonnet, ambiguity: PRB-004: it is not stated whether a pointer click gives focus to the "Try again" button before it is removed. I assumed it does, so FOC-1 moves focus to the place title.
- sonnet, ambiguity: PRB-038: Control+Z in a field has no undo intent in the binding table. I read it as the platform default for text editing.
- sonnet, ambiguity: PRB-041: Tab leaves the title field and Slate does not set where focus goes, so the next focus is the platform default.
- sonnet, contradiction: FIX-5 gives SL-114 the title "Card title overflows on narrow screens", but SCN-CRD-1 expects the title text "A long title pushes the labels out of the card.".
- sonnet, contradiction: SCN-CRD-3 and SCN-CRD-2 name titles and a comment count ("2 comments" for SL-120, "Write onboarding guide" for SL-105) that FIX-5 does not list. They cannot be checked against data.json, which is not in the package.
- haiku, ambiguity: Whether a timer due exactly at the stated clock time has fired. Answers assume that it has, as the scenarios do (all columns load at 2200 ms). This affects PRB-003, PRB-004, PRB-031, PRB-035 and PRB-050.
- haiku, ambiguity: PRB-013: WEB-6 says the focus stop comes after the Select all of its column. The next Tab stop is inferred from that.
- haiku, ambiguity: PRB-025: FOC-1 says focus stays on a part shown again in the same change. Whether a card put back after a failed move counts as the same change is inferred.
- haiku, ambiguity: PRB-009 and PRB-019: the package gives titles and labels for only some cards, so the full visible set cannot be determined.
- haiku, ambiguity: PRB-048: the comment texts and authors of SL-120 are not given. The count of 2 comes only from SCN-CRD-3.
- haiku, ambiguity: PRB-031: whether a notice shown for exactly 8 s has ended at 8000 ms.
- haiku, contradiction: TSK-4 says the mark "Saving…" goes after 400 ms, but TTL-T1 row 4 and TTL-1 put the mark on at commit, and SCN-TTL-1 asserts it at once.
- haiku, contradiction: FIX-5 gives the title of SL-114 as "Card title overflows on narrow screens", but SCN-CRD-1 expects the text "A long title pushes the labels out of the card." to be shown. The package does not say which field holds that text.
