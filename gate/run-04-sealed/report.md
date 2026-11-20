# Gate run 04-sealed

Set: sealed. Probes: 13, of which 11 are must-level.

Result: pass.

| Reader | Score, all probes | Score, must-level | Guesses | Ambiguities | Contradictions |
| --- | --- | --- | --- | --- | --- |
| control-haiku | 4 of 13 | 3 of 11 | 13 | 5 | 0 |
| control-opus | 3 of 13 | 2 of 11 | 13 | 5 | 0 |
| control-sonnet | 3 of 13 | 2 of 11 | 13 | 3 | 0 |
| haiku | 13 of 13 | 11 of 11 | 0 | 5 | 1 |
| opus | 13 of 13 | 11 of 11 | 0 | 3 | 0 |
| qwen | 8.5 of 13 | 6.5 of 11 | 0 | 0 | 0 |
| sonnet | 13 of 13 | 11 of 11 | 0 | 4 | 0 |

A probe that a control reader answers correctly marks a decision that convention carries.

The sealed set shows no questions here.

## Ambiguities and contradictions that the readers listed

- opus, ambiguity: WEB-6 lists "the selection bar" as one item in the Tab order. It does not say whether each toggle of the "Label selected" group is its own Tab stop. PRB-018 assumes four Tabs from "Done" go through bug, ui, api to docs.
- opus, ambiguity: The reply time of a comment falls in the middle of a second (65.2 s after 09:00:00). FIX-10 says whole seconds but does not say whether to truncate or round. The shown minute is 09:01 either way.
- opus, ambiguity: BLK-4: the denominator in "2 of 3 cards" can be read as the selected cards or as the selected cards that lack the label. Both give 2 in PRB-018.
- sonnet, ambiguity: PRB-052: NAV-T1.2 says "the card of that place is visible" without defining "that place". I read it as the card place just left, so focus goes to SL-102. Row 4 (place title) is the other reading.
- sonnet, ambiguity: PRB-052: NAV-T1.2 says "scroll ... not changed for a new entry", while NAV-T3.2 says the filter comes from when Board was last shown. Here the board was shown with no filter, so this does not change the answer.
- sonnet, ambiguity: PRB-018: BLK-4 only gives a count example for "X of Y cards" with 3 selected. Here the counts are 1 of 2 by analogy.
- sonnet, ambiguity: PRB-001: the slow mark time depends on reading "1000 ms after its request" as 400+1000, not 1000 from the start. FIX-L2 supports this.
- haiku, ambiguity: PRB-010: the written form when the filter text is empty is not stated. I assumed the empty q part is omitted, as "#/" stands for no filter.
- haiku, ambiguity: PRB-027 and PRB-046: the profile is not named, so I assumed "default", whose faults fail the title and the comment.
- haiku, ambiguity: PRB-036: the notice is raised at 400 ms and its 8 s time ends at 8400 ms. I read the clock as having reached 8400 ms when the answer depends on it.
- haiku, ambiguity: PRB-052: I assumed the page has focus when Escape is pressed, not the address bar.
- haiku, ambiguity: PRB-034: the rules give the focus of the delete through DEL-T1 ("as in DEL-1") and NAV-T1 row 3. Both end at the place title, so I took that as the answer.
- haiku, contradiction: SCN-NAV-9 is tagged [terminal], but the package has no terminal modality sheet. Its addresses ("board?...", "card/sl-114") also disagree with the address forms in WEB-1 ("#/..."). The other questions do not depend on this.
