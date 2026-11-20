# Gate run 02

Set: open. Probes: 39, of which 39 are must-level.

Result: blocked by 2 must-level probes.

| Reader | Score, all probes | Score, must-level | Guesses | Ambiguities | Contradictions |
| --- | --- | --- | --- | --- | --- |
| control-haiku | 10.5 of 39 | 10.5 of 39 | 38 | 12 | 0 |
| control-opus | 18 of 39 | 18 of 39 | 39 | 6 | 0 |
| control-sonnet | 18 of 39 | 18 of 39 | 39 | 5 | 0 |
| haiku | 39 of 39 | 39 of 39 | 0 | 6 | 2 |
| opus | 38 of 39 | 38 of 39 | 0 | 4 | 1 |
| qwen | 26.5 of 39 | 26.5 of 39 | 0 | 0 | 0 |
| sonnet | 38 of 39 | 38 of 39 | 0 | 5 | 0 |

A probe that a control reader answers correctly marks a decision that convention carries.

## Wrong and split answers

### PRB-025 (must, save failures, rollback and retry)

- Start at the board address #/ with the default data and let the clock run 2200 ms, so that every column has loaded.
- Put focus on SL-107, press Space, ArrowRight, Space. The service fails this move. Let the clock run 400 ms.

Question: Where is SL-107, which part has focus, and what does the notice say?

- opus, grade 1, DERIVED, cites MOV-2 DAT-8 FOC-1 SCN-MOV-1 SCN-MOV-2: SL-107 is back in Backlog at position 7 (between SL-106 and SL-108). Card SL-107 has focus. The notice is "Couldn't move SL-107. It is back in Backlog." with the actions "Retry" and "Dismiss".
- sonnet, grade 0, DERIVED, cites MOV-2 DAT-8 FOC-1 NTC-3 SCN-MOV-1: SL-107 is back in Backlog at position 7 (between SL-109 and SL-110, with SL-110 last). Focus is on card SL-107. The notice reads "Couldn't move SL-107. It is back in Backlog." with the action "Retry" (plus "Dismiss").
- haiku, grade 1, DERIVED, cites MOV-2 DAT-8 FOC-1 CRY-T1.3: SL-107 is back in Backlog at position 7, between SL-106 and SL-108. Focus is on card SL-107 (“SL-107 Migrate avatars to object storage”). The notice reads “Couldn't move SL-107. It is back in Backlog.” with the action “Retry”.
- qwen, grade 1, DERIVED, cites MOV-2 CRY-T1: SL-107 is in Backlog. Focus is on SL-107. Notice says "Couldn't move SL-107. It is back in Backlog." with action "Retry".

### PRB-048 (must, comments)

- Open the address #/card/SL-120 directly and let the clock run 700 ms. The service fails the first comment load of SL-120.
- Click the "Retry" button in the Comments section and let the clock run 300 ms.

Question: What does the Comments section show now?

- opus, grade 0, none, cites nothing: (no answer)
- sonnet, grade 1, DERIVED, cites CRD-3 CRD-4 FIX-14 DAT-9 DAT-14: The Comments section shows "2 comments". The first is "Ana Ruiz · 17 Nov 2026, 11:15" "See the linked report.". The second is "Ben Okafor · 18 Nov 2026, 16:28" "I can reproduce this.". The comment field is enabled.
- haiku, grade 1, DERIVED, cites CRD-4 CRD-3 DAT-9 DAT-14 FIX-L4 FIX-14: The Comments section shows “2 comments”, then “Ana Ruiz · 17 Nov 2026, 11:15” with “See the linked report.”, then “Ben Okafor · 18 Nov 2026, 16:28” with “I can reproduce this.”. The field “Add a comment” is enabled.
- qwen, grade 0.5, DERIVED, cites CRD-4 FIX-5: Shows "2 comments" and the two comment texts/author/time.

## Ambiguities and contradictions that the readers listed

- opus, ambiguity: PRB-004: whether a pointer click on "Try again" gives the button focus is a platform matter. If it does not, focus could stay "none" instead of moving to the place title by FOC-1.
- opus, ambiguity: CRY-3/WEB-4 carry-to: it is not stated whether a card whose middle is exactly at the pointer counts as "above", or whether the positions use the layout after the carried card is shown.
- opus, ambiguity: MOV-2 "same position number": it is not stated whether this is the position among the visible cards or in the whole column.
- opus, ambiguity: History depth after Back: the spec counts entries but does not say how a Back changes the reported depth.
- opus, contradiction: Notice.Error face has a second action "Dismiss", but the note under BLK-4 says "A notice has at most one action."
- sonnet, ambiguity: PRB-004: it is not stated whether focus stays on the place title after Board.Loading turns into Board.Ready, or whether the retry button's focus is kept at all (FOC-1 with a pointer click).
- sonnet, ambiguity: PRB-013: WEB-6 says the focus stop comes after "Select all" of its column, but does not say outright that Tab from the focus stop goes to the next column's "Select all".
- sonnet, ambiguity: PRB-023: whether a pointer exactly at the middle of a card counts as "above" for carry-to, and whether the layout shift of the carried card changes where SL-113 is.
- sonnet, ambiguity: PRB-049/050: "history depth" after Back is read as the total entries (Back removes none), as in SCN-NAV-1.
- sonnet, ambiguity: Error notices have the extra action "Dismiss", but the notice text of some rules lists only the named action.
- haiku, ambiguity: PRB-013: WEB-6 says the focus stop comes after the Select all of its column, but it does not say which Tab stop follows the focus stop; I took the next column's Select all.
- haiku, ambiguity: PRB-017, PRB-026: DAT-8 says a card goes to its old position number, or to the end if the column is shorter. When the position equals the current length, the text does not say whether it is inserted there or appended; I inserted it at that position.
- haiku, ambiguity: PRB-023: CRY-3 counts cards whose middle is above the pointer. The text does not say what happens when the pointer is exactly at a middle; I did not count the card whose middle the pointer is on.
- haiku, ambiguity: PRB-004: the rules give no focus target when the 'Try again' button leaves the page; I used FOC-1 and took the place title.
- haiku, ambiguity: PRB-022: the 'full' check in DAT-7 counts cards still marked 'Saving…'; I counted them.
- haiku, ambiguity: NAV-T1 row 1 says focus is not moved on a reload, while MEM-T1 keeps a focus stop that is 'first visible' on reload. The text does not say whether the focus stop has focus after a reload.
- haiku, contradiction: FCS-2 and CRY-2 both say 'the nearest column on that side' but differ. FCS-2 requires a column with a visible card, so from In progress it skips the empty Review and goes to Done. CRY-2 requires a loaded column, and Empty counts as loaded, so it goes to Review. (PRB-011 uses FCS-2; PRB-021 uses CRY-2.)
- haiku, contradiction: MIS-1 says that while Missing.Page shows, Slate keeps the address as the user entered it. NAV-1 says that when Slate shows an address, it rewrites the current entry to the written form. For an unknown address such as #/nowhere, the written form is not defined, so the two rules disagree on what the address becomes.
