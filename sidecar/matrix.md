# State-by-event matrix

This file is not normative. It is the worksheet of extraction step 4. Each
cell is a rule or table, "nothing", "default" (the platform default) or "-"
(cannot occur). An empty cell is an open question; there is none.

## Carry and the board intents

```text
state \ intent    pick-up   carry    carry-to  drop     cancel-carry  dismiss   open-card  move-focus  toggle-select  delete-card  bulk-move  bulk-label
Carry.Idle        CRY-1     nothing  nothing   nothing  nothing       DIS-T1    OPN-1      FCS-2       SEL-1          DEL-1        BLK-T1     BLK-T3
Carry.Carrying    CRY-6     CRY-2    CRY-3     CRY-T1   CRY-5         DIS-T1.1  CRY-6      CRY-6       CRY-6          DEL-1        BLK-T1.1   BLK-T3.1
```

## A card on the board

```text
state \ intent or event   pick-up  delete-card  open-card  toggle-select  bulk-move      move save succeeds  move save fails
no mark                   CRY-1    DEL-1        OPN-1      SEL-1          BLK-T1         -                   -
mark "Saving…"            nothing  nothing      OPN-1      SEL-1          not a candidate  MOV-1, BLK-T2     MOV-2, BLK-T2.1, MOV-4
mark "Moving"             CRY-6    nothing      CRY-6      CRY-6          BLK-T1.1       -                   -
```

## Board and columns

```text
state \ event      load succeeds  load fails  load is slow  retry-place  retry-column  filter intents
Board.Loading      BRD-1          BRD-2       -             nothing      -             -
Board.Failed       -              -           -             BRD-3        -             -
Board.Ready        -              -           -             nothing      see Column    FLT-1 to FLT-8
Column.Loading.Fresh  COL-4       COL-2       COL-1         -            nothing       -
Column.Loading.Slow   COL-4       COL-2       -             -            nothing       -
Column.Failed      -              -           -             -            COL-3         -
Column.Empty, NoMatch, Cards   -  -           -             -            nothing       -
```

## Notice

```text
state \ event   a notice is raised  notice time ends  notice-action  undo                 dismiss-notice  dismiss  place changes  reload
Notice.None     NTC-1               -                 nothing        nothing              nothing         DIS-T1   -              -
Notice.Info     NTC-1 (DEL-2)       NTC-2 (DEL-2)     NTC-4          NTC-5                nothing         DIS-T1   kept (MEM-T1)  removed
Notice.Error    NTC-1               -                 NTC-4          NTC-5                NTC-6           DIS-T1   kept (MEM-T1)  removed
```

## Selection

```text
state \ intent or event  toggle-select  select-column  clear-selection  bulk-move  bulk-label  dismiss    a card is hidden or deleted  place changes
Selection.None           SEL-1          SEL-2          nothing          nothing    nothing     DIS-T1     -                            -
Selection.Some           SEL-1          SEL-2          SEL-3            BLK-T1     BLK-T3      DIS-T1.4   SEL-4                        cleared (MEM-T1)
```

## Card place

```text
state \ intent or event  edit-title  commit-title  leave-title  dismiss    title save fails  retry-place  go-up
Card.Loading             -           -             -            DIS-T1.8   TTL-4             nothing      NAV-T3
Card.Failed              -           -             -            DIS-T1.8   TTL-4             CRD-2        NAV-T3
Title.Shown              TTL-1       -             -            DIS-T1.8   TTL-4             nothing      NAV-T3
Title.Shown, "Saving…"   nothing     -             -            DIS-T1.8   TTL-4             nothing      NAV-T3
Title.Editing            -           TTL-T1        TTL-3        DIS-T1.5   TTL-4             nothing      NAV-T3

state \ intent           edit-description  commit-description  cancel-description  focus leaves the field  dismiss
Description.Shown        DSC-1             nothing             nothing             -                       DIS-T1.8
Description.Editing      nothing           DSC-2               DSC-3               DSC-4                   DIS-T1.6

state \ intent or event  commit-comment  change-comment-text  comment save succeeds  comment save fails  retry-comments  comments load answers
Comments.Loading         nothing         CMT-1                -                      -                   nothing         CRD-3
Comments.Failed          nothing         CMT-1                -                      -                   CRD-4           -
Comments.None, Some      CMT-2           CMT-1                CMT-3                  CMT-T1              nothing         -
a comment is sent        nothing         field is disabled    CMT-3                  CMT-T1              nothing         -
```

## Open questions that the matrix found

```text
1 The fixture has no fault for saveDescription, saveLabels or saveAssignee. The reference
  build keeps the new value if such a save fails. No check can decide this, so the
  specification has no rule for it.
2 A reload while a save has no reply: the request is lost with the session. MEM-T1 covers it
  ("session data: start again").
3 Two undo notices in a row: only the last notice can be undone (NTC-1).
```
