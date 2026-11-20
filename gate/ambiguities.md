# Ambiguities and contradictions from gate run 03

Each item that a gating reader listed in the last run has an identifier and a
decision. "Logged" items stay open in the accepted version. The specification
author owns each of them.

| Item | Source | What the reader named | Decision |
| --- | --- | --- | --- |
| AMB-1 | Opus, Sonnet, Haiku | WEB-4 carry-to: a pointer exactly at the middle of a card, and whether the middle is measured before or after the carried card moves the others | Logged. Continuous pointer geometry is a stated limit of the format. The build counts a card only if its middle is above the pointer, measured in the layout as it is shown |
| AMB-2 | Opus, Sonnet | Whether a pointer click gives focus to "Try again" or "Dismiss" before the part is removed (FOC-1 then applies) | Logged. It is a platform default of the web. The web sheet should say it |
| AMB-3 | Opus | DAT-5 does not say in words that a filter word can match a part of a word | Logged. The example "sl-11" shows it. "Occurs in" should say "as a part of the text" |
| AMB-4 | Sonnet | WEB-6: which part is the next Tab stop after the focus stop | Logged. WEB-6 gives the order; the reader read it correctly |
| AMB-5 | Sonnet | NAV-1: how the address looks between the start and the load of the board data | Logged. NAV-1 says when a value is dropped; it should give the form in between |
| AMB-6 | Haiku | FLT-8 "shall not move the focus" against FLT-3, which focuses the one visible card | Logged as a real conflict of wording. FLT-3 should carry "overrides FLT-8" for the focus. The lint did not find it, because the two rules have different triggers |
| AMB-7 | Haiku | Labels.Full: a toggle that is "disabled" (face) against "does nothing" (LBL-1) | Logged. Both are true; one statement is enough |
| AMB-8 | Haiku | "A notice has at most one action" against "Dismiss" on an error notice | Logged as a real conflict of wording. "Dismiss" is an action role in the face. The note should say "one action besides Dismiss" |
| AMB-9 | Haiku | The history depth at a start is not stated | Logged. Scenarios use a remembered depth, so no check needs it |
| AMB-10 | Haiku | SCN-DSC-1 changes the comment text while focus is in the description field | Logged. The intent moves focus to the comment field; the scenario grammar does not say that an intent on a field first puts focus there |
| AMB-11 | Haiku | SCN-MOV-2 expects focus on the place title after dismiss-notice; NTC-6 names no focus | Logged with AMB-2. The result depends on whether the "Dismiss" control had focus |
| AMB-12 | Haiku | CRD-1 "not loaded in this session" against PRP-2 for a failed comments load | Logged as a real conflict of wording. CRD-1 should say "not requested in this session" |
| AMB-13 | Haiku | FOC-1: is a card that moved to another column and came back "the same part" | Logged. The reader chose the intended reading |
