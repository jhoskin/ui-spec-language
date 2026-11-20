# Scenarios: comments

```text
SCN-CMT-1 verifies CMT-1, CMT-2, CMT-3, CMT-T1.1, DAT-9, DAT-14, DAT-17, DIS-T1.7, TSK-5
Given start at board.
After 2200 ms.
When open-card SL-101.
After 300 ms.
Then text "No comments yet" is shown.
When change-comment-text "  a flaky one ".
When commit-comment.
Then text "1 comment" is shown.
Then text "Mika Ito · Sending…" is shown.
Then field "Add a comment" is disabled.
Then focus none.
After 500 ms.
Then text "No comments yet" is shown.
Then text "Couldn't add the comment. Your text is back in the field." is shown.
Then field "Add a comment" has text "a flaky one".
Then focus field "Add a comment".
Then no notice.
When dismiss.
Then place title "Export board as CSV".
When change-comment-text "Looks fine.".
Then no text "Couldn't add the comment. Your text is back in the field.".
When commit-comment.
After 500 ms.
Then text "1 comment" is shown.
Then text "Mika Ito · 20 Nov 2026, 09:00" is shown.
Then field "Add a comment" is enabled.
Then focus field "Add a comment".

SCN-CMT-2 verifies CMT-T1.2, FIX-19
Given start at board.
After 2200 ms.
When open-card SL-101.
After 300 ms.
When change-comment-text "flaky".
When commit-comment.
When go-up.
After 500 ms.
Then notice "Couldn't add the comment on SL-101." with no action.
Then action "Dismiss" is shown.
```
