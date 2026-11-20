# Scenarios: card place

```text
SCN-CRD-1 verifies CRD-T1.3, CRD-1, CRD-3, DAT-9, DAT-14, DAT-17
Given start at board.
After 2200 ms.
When open-card SL-114.
Then text "SL-114 · Ready" is shown.
Then toggle "bug" in "Labels" is on.
Then toggle "api" in "Labels" is off.
Then choice "Mika Ito" is chosen.
Then text "A long title pushes the labels out of the card." is shown.
Then field "Add a comment" is disabled.
Then requests loadCard 0.
After 300 ms.
Then text "2 comments" is shown.
Then text "Dev Patel · 10 Nov 2026, 12:44" is shown.
Then text "I can reproduce this." is shown.
Then field "Add a comment" is enabled.
Then action "Add comment" is disabled.

SCN-CRD-2 verifies CRD-T1.2, CRD-2
Given profile card-down.
Given start at card SL-105.
After 400 ms.
Then place title "SL-105".
Then text "Couldn't load this card." is shown.
When retry-place.
After 250 ms.
Then place title "Write onboarding guide".
Then text "No description" is shown.

SCN-CRD-3 verifies CRD-3, CRD-4, PRP-2
Given start at board.
After 2200 ms.
When open-card SL-120.
After 300 ms.
Then text "Couldn't load comments." is shown.
Then field "Add a comment" is disabled.
When go-up.
When open-card SL-120.
After 300 ms.
Then text "Couldn't load comments." is shown.
Then requests loadComments 1.
When retry-comments.
After 300 ms.
Then text "2 comments" is shown.

SCN-TTL-1 verifies TTL-1, TTL-2, TTL-T1, DAT-10, SAV-1, TSK-4
Given start at card SL-105.
After 400 ms.
When edit-title.
Then focus field "Title".
Then field "Title" has text "Write onboarding guide".
When change-title-text "   ".
When commit-title.
Then text "A title needs at least 1 character." is shown.
When change-title-text "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx".
When commit-title.
Then text "A title can have at most 80 characters." is shown.
When change-title-text " Write onboarding  guide ".
When commit-title.
Then focus place title.
Then requests saveTitle 0.
When edit-title.
When change-title-text "Write the onboarding guide".
When commit-title.
Then place title "Write the onboarding guide".
Then text "Saving…" is shown.
Then focus place title.
When edit-title.
Then field "Title" is absent.
After 400 ms.
Then no text "Saving…".
Then requests saveTitle 1.

SCN-TTL-2 verifies TTL-3, TTL-4, DIS-T1.5
Given start at card SL-105.
After 400 ms.
When edit-title.
When change-title-text "A flaky title".
When leave-title.
Then place title "A flaky title".
After 400 ms.
Then place title "Write onboarding guide".
Then notice "Couldn't save the title of SL-105." with "Retry".
When notice-action.
After 400 ms.
Then place title "A flaky title".
Then no notice.
When edit-title.
When change-title-text "".
When leave-title.
Then place title "A flaky title".
Then no text "A title needs at least 1 character.".
When edit-title.
When change-title-text "Dropped".
When dismiss.
Then place title "A flaky title".
Then focus place title.
Then requests saveTitle 2.

SCN-LBL-1 verifies LBL-1, ASG-1, DAT-11, SAV-1
Given start at card SL-104.
After 400 ms.
When toggle-label bug.
Then toggle "bug" in "Labels" is on.
Then text "Label limit reached (3)" is shown.
Then toggle "ui" in "Labels" is disabled.
Then text "Saving…" is shown.
After 300 ms.
Then no text "Saving…".
When toggle-label ui.
Then requests saveLabels 1.
When toggle-label api.
Then no text "Label limit reached (3)".
When choose-assignee Unassigned.
Then choice "Unassigned" is chosen.
When choose-assignee Unassigned.
Then requests saveAssignee 1.
When go-up.
After 2200 ms.
Then text "Unassigned" is shown.

SCN-DSC-1 verifies DSC-1, DSC-2, DSC-3, DSC-4, DSC-5, DIS-T1.6, DIS-T1.8, DAT-15
Given start at card SL-110.
After 700 ms.
Then text "No description" is shown.
When edit-description.
Then focus field "Description".
When change-description-text "  First line  ".
When cancel-description.
Then text "No description" is shown.
Then focus action "Edit description".
When edit-description.
When change-description-text "Kept draft".
When change-comment-text "x".
Then field "Description" has text "Kept draft".
When dismiss.
Then text "No description" is shown.
Then place title "Archive cards older than a year".
When edit-description.
When change-description-text "  First line  ".
When commit-description.
Then text "First line" is shown.
Then focus action "Edit description".
Then requests saveDescription 1.
When dismiss.
Then place title "Board".
```
