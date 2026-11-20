# Card

The card place shows one card: its title, labels, assignee, description and
comments. It has its own address.

## States

```text
Card         States: Loading | Failed | Ready
Title        States: Shown | Editing
Description  States: Shown | Editing
Labels       States: Open | Full
Comments     States: Loading | Failed | None | Some
```

Title, Description, Labels and Comments exist in Card.Ready only. Labels is
Full when the card has 3 labels.

## Faces

```text
Card.Loading face
  1 r1 N up-link "← Board"
  2 r2 Q two placeholder blocks

Card.Failed face
  1 r2 N up-link "← Board"
  2 r1 P place title: the identifier, "SL-120"
  3 r3 N alert "Couldn't load this card."
  4 r4 N action "Try again"

Card.Ready face
  1 r3 N up-link "← Board"
  2 r6 Q text: the identifier and the column name, "SL-114 · Ready"
  3 r1 P the Title region
  4 r4 N group "Labels": one toggle for each label in board order, on if the card has the label;
         mark "Saving…" while a label save has no reply.
         In Labels.Full: each toggle that is off is disabled, then Q text "Label limit reached (3)"
  5 r5 N group "Assignee": one choice "Unassigned", then one choice for each person in order;
         mark "Saving…" while an assignee save has no reply
  6 r2 N heading "Description", then the Description region
  7 r7 N heading "Comments", then the Comments region, then:
      a field, name "Add a comment"; disabled in Comments.Loading and Comments.Failed and
        while a comment is sent
      b action "Add comment"; disabled while the field is disabled or its text is blank
      c alert: the comment message, if there is one
  8 r8 N action "Delete card"

Title.Shown face
  a place title: the title of the card
  b action "Edit title"
  c mark "Saving…", while a title save has no reply

Title.Editing face
  a field, name "Title", with the draft
  b alert: the title message, if there is one

Description.Shown face
  a the description, or Q text "No description" if it is empty
  b action "Edit description"
  c mark "Saving…", while a description save has no reply

Description.Editing face
  a field of more than one line, name "Description", with the draft
  b action "Save"
  c action "Cancel"

Comments.Loading face: one placeholder block.
Comments.Failed face: alert "Couldn't load comments.", then action "Retry".
Comments.None face: Q text "No comments yet".
Comments.Some face
  a Q the comment count (DAT-14)
  b the comments, oldest first; each has Q text "Dev Patel · 10 Nov 2026, 12:44" (the name of
    the author and the time, DAT-9), then the text of the comment. A comment that is sent
    has mark "Sending…" in the place of the time.
```

The card place has no control that moves the card to another column.

## Which state shows

```text
CRD-T1 [must] decides: Slate arrives in a place  owns: card state
  1 the card has a delete that waits or was sent             Missing.Card
  2 the board load failed, or the card load failed           Card.Failed
  3 the session holds the card and the board data            Card.Ready, with no card request
  4 the session holds the card                               Card.Loading until the board data comes
  5 a card load answered that there is no such card, or
    every column is loaded and none has the card             Missing.Card
  6 otherwise                                                Card.Loading; request the card one time,
                                                             and the board data if not yet requested
```

The session holds a card after a column load or a card load returned it. A
card that the user opens from the board shows at once (row 3). The table
applies again when a reply comes and when the undo of a delete starts: an undo
while Missing.Card shows for that card gives Card.Ready, and CRD-1 applies.

```text
CRD-1 [must] origin: extracted  sets: Comments
  When the card load answers, Slate shall apply CRD-T1 again. When Card.Ready shows a card
  whose comments were not loaded in this session, Slate shall show Comments.Loading and
  request the comments.
CRD-2 [must] origin: extracted  sets: Card
  While Card.Failed, when the user retries the place, Slate shall show Card.Loading and send
  again each request that failed.
CRD-3 [must] origin: extracted  sets: Comments
  When the comments load answers, Slate shall show Comments.Failed if it failed, Comments.None
  if there are no comments, and Comments.Some if there are.
CRD-4 [must] origin: extracted  sets: Comments
  While Comments.Failed, when the user retries the comments, Slate shall show Comments.Loading
  and request the comments again.
```

## Title

```text
TTL-1 [must] origin: extracted  sets: Title, focus
  While Title.Shown, when the user edits the title, Slate shall show Title.Editing with the
  title as the draft and focus the title field. If the title has mark "Saving…", nothing changes.
TTL-2 [must] origin: extracted  sets: Title
  While Title.Editing, when the user changes the title text, Slate shall keep the text as the
  draft. The message does not change.
TTL-3 [must] origin: extracted  sets: Title
  While Title.Editing, when the user moves focus out of the title field, Slate shall show
  Title.Shown. If the draft (DAT-10) is good and is not the title, Slate shall show it as the
  title with mark "Saving…" and request the save. If not, the old title stays and no message
  shows. Slate shall not move the focus.
TTL-4 [must] origin: extracted  sets: Title, Notice
  If a title save fails, then Slate shall show the old title again and raise Error
  "Couldn't save the title of SL-114." with action "Retry". "Retry" shows the new title again
  with mark "Saving…" and requests the save. If another title save of the card has no reply,
  "Retry" only ends the notice.
```

```text
TTL-T1 [must] decides: the user commits the title  owns: -
  The draft is first put in its written form (DAT-10).
  1 the draft has no characters            stay in Title.Editing; message "A title needs at least
                                           1 character."
  2 the draft has more than 80 characters  stay in Title.Editing; message "A title can have at most
                                           80 characters."
  3 the draft is the title                 Title.Shown; focus the place title; no request
  4 otherwise                              Title.Shown with the draft as the title and mark
                                           "Saving…"; focus the place title; request the save
```

## Labels and assignee

```text
LBL-1 [must] origin: extracted  sets: Labels
  While Card.Ready, when the user toggles a label of the card, Slate shall remove the label if
  the card has it, and add it if the card has fewer than 3 labels. Slate shall show the change
  at once with mark "Saving…" and request the save. In Labels.Full, a toggle that is off does
  nothing.
ASG-1 [must] origin: extracted  sets: Card
  While Card.Ready, when the user chooses an assignee, Slate shall show that choice at once
  with mark "Saving…" and request the save. If it is the assignee, nothing changes.
SAV-1 [must] origin: extracted  sets: Card
  When a save succeeds, Slate shall remove the mark "Saving…" of that save and change nothing else.
```

## Description

```text
DSC-1 [must] origin: extracted  sets: Description, focus
  While Description.Shown, when the user edits the description, Slate shall show
  Description.Editing with the description as the draft and focus the description field. If
  the description has mark "Saving…", nothing changes.
DSC-2 [must] origin: extracted  sets: Description, focus
  While Description.Editing, when the user commits the description, Slate shall show
  Description.Shown and focus action "Edit description". If the draft (DAT-15) is not the
  description, Slate shall show it with mark "Saving…" and request the save. An empty
  description is good.
DSC-3 [must] origin: extracted  sets: Description, focus
  While Description.Editing, when the user cancels the description, Slate shall show
  Description.Shown with the old text and focus action "Edit description".
DSC-4 [must] origin: extracted  sets: Description
  While Description.Editing, Slate shall keep the edit open and the draft when focus leaves
  the description field.
  Fail: the description is saved or the edit closes when focus leaves the field.
DSC-5 [must] origin: extracted  sets: Description
  While Description.Editing, when the user changes the description text, Slate shall keep the
  text as the draft.
```

## Comments

```text
CMT-1 [must] origin: extracted  sets: Comments
  While Card.Ready, when the user changes the comment text, Slate shall remove the comment message.
CMT-2 [must] origin: extracted  sets: Comments
  While Comments.None or Comments.Some, when the user commits the comment, Slate shall add the
  text, with white space removed from its ends, as the last comment with mark "Sending…",
  raise the comment count by 1 at once (in Card and on the card item), empty and disable the
  field, set focus to "none", and request the save. If the text is blank or a comment is
  sent, nothing changes.
CMT-3 [must] origin: extracted  sets: Comments
  When a comment save succeeds, Slate shall show the time of the reply in the place of mark
  "Sending…", enable the field and, if Card shows the card of the comment, focus the field.
```

```text
CMT-T1 [must] decides: a comment save fails  owns: -
  1 Card shows the card of the comment   remove the comment and its count; put its text back in the field; enable
                                         and focus the field; message "Couldn't add the comment.
                                         Your text is back in the field."; raise no notice
  2 otherwise                            remove the comment and its count; raise Error "Couldn't add the comment on
                                         SL-114." with no action
```

## Delete

```text
DEL-T1 [must] decides: the user deletes a card  scope: Card.Ready  owns: -
  Slate first removes the card and raises the notice as in DEL-1. It then
  leaves the place:
  1 the entry has the "opened from the board" mark   go Back
  2 otherwise                                        show Board in place of the current history entry,
                                                     with the filter that Board had when last shown
```

There is no confirmation before the delete.
