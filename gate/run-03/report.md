# Gate run 03

Set: open. Probes: 39, of which 39 are must-level.

Result: pass.

| Reader | Score, all probes | Score, must-level | Guesses | Ambiguities | Contradictions |
| --- | --- | --- | --- | --- | --- |
| control-haiku | 11 of 39 | 11 of 39 | 36 | 7 | 0 |
| control-opus | 20 of 39 | 20 of 39 | 39 | 7 | 0 |
| control-sonnet | 18 of 39 | 18 of 39 | 39 | 4 | 0 |
| haiku | 39 of 39 | 39 of 39 | 0 | 7 | 4 |
| opus | 39 of 39 | 39 of 39 | 0 | 3 | 0 |
| qwen | 23 of 39 | 23 of 39 | 0 | 0 | 0 |
| sonnet | 39 of 39 | 39 of 39 | 0 | 7 | 0 |

A probe that a control reader answers correctly marks a decision that convention carries.

## Ambiguities and contradictions that the readers listed

- opus, ambiguity: WEB-4 carry-to counts other visible cards "whose middle is above the pointer". It does not say whether the middle is measured before or after the carried card shifts the cards, or how a pointer exactly at a middle counts (PRB-023).
- opus, ambiguity: Whether clicking "Try again" gives it focus is a platform default. FOC-1 then moves focus to the place title only if the button had focus (PRB-004).
- opus, ambiguity: Whether the filter text matches a word as a substring of the title is implied by the example "sl-11" -> SL-110 to SL-119, not stated.
- sonnet, ambiguity: PRB-004: FOC-1 puts focus on the place title after the clicked button disappears. It is not stated whether the place title counts as the 'same part' re-shown, nor whether focus is moved at all.
- sonnet, ambiguity: PRB-013: WEB-6 says the focus stop comes after "Select all" of its column. The next Tab stop after the Backlog focus stop is read as "Select all in Ready".
- sonnet, ambiguity: PRB-023: carry-to counts cards 'whose middle is above the pointer'. It does not say whether a pointer exactly at the middle counts as above, nor how layout shifts during the drag change the counts. Both readings give position 3.
- sonnet, ambiguity: PRB-015: Shift+"x" is read as Shift+X. The text does not say whether the plain "x" first moves the selection for the focused card.
- sonnet, ambiguity: PRB-049: 'history depth after Back' is read as the entry count (unchanged at +1), per SCN-NAV-1.
- sonnet, ambiguity: PRB-005: whether the board data has arrived (400 ms) by the time Retry is clicked is only implied by FIX-11 latency; I read it as arrived, so the card shows Ready.
- sonnet, ambiguity: PRB-009: NAV-1 says dropped filter values are removed when the board data is loaded, but not whether the address is shown in the interim in a different form.
- haiku, ambiguity: PRB-008: FLT-8 says applying the filter "shall not move the focus", but FLT-3 says a commit with one visible card focuses that card. I read FLT-3 as the specific rule for the commit.
- haiku, ambiguity: PRB-025: FOC-1 keeps focus on a card that "came back" in the same change. It is not stated whether a card that moves to another column and then returns counts as the same part. I read it as the same card.
- haiku, ambiguity: PRB-042: the Card.Ready face says an off toggle in Labels.Full is "disabled", while LBL-1 says it "does nothing". I read these as the same behaviour.
- haiku, ambiguity: PRB-023: CRY-3 does not say whether a pointer exactly at a card's middle counts as "above" it. I counted that card as not above.
- haiku, ambiguity: Notice actions: BLK says a notice has at most one action, but Notice.Error always shows "Dismiss" beside its own action. I did not count "Dismiss" as an action for the questions asked.
- haiku, ambiguity: PRB-050: the package does not state the history depth at a start. I took the depth at a direct start to be 1.
- haiku, ambiguity: SCN-DSC-1 sends change-comment-text while focus is in the description field, which the WEB-4 binding does not allow. I treated that step as having no effect.
- haiku, contradiction: SCN-MOV-2 expects focus on place title after dismiss-notice, but NTC-6 names no focus change, the frame rule says a rule changes only what it names, and FOC-1 keeps focus on the card that is still shown (SCN-MOV-2 'Then focus place title' vs NTC-6 and FOC-1).
- haiku, contradiction: FLT-8 says applying the filter "shall not move the focus", while FLT-3 applies the same filter on commit and focuses the one visible card.
- haiku, contradiction: CRD-1 requests comments that were "not loaded in this session", which would include a failed load, but PRP-2 says an arrival does not send a failed request again, and SCN-CRD-3 expects loadComments to stay at 1 after reopening SL-120.
- haiku, contradiction: BLK says "A notice has at most one action", but the Notice.Error face shows "Retry" plus "Dismiss", and SCN-CMT-2 says "with no action" and then "Then action 'Dismiss' is shown".
