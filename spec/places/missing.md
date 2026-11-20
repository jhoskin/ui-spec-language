# Missing

Missing shows when an address names no place or no card.

```text
Missing  States: Page | Card

Missing.Page face
  1 r1 P place title "Page not found"
  2 r3 Q text "The address may be mistyped or out of date."
  3 r2 N link "Go to the board", the board link

Missing.Card face
  1 r1 P place title "Card not found"
  2 r3 Q text "There is no card SL-999 on this board."
  3 r2 N link "Go to the board", the board link
```

```text
MIS-1 [must] origin: extracted  sets: address
  While Missing.Page, Slate shall keep the address as the user entered it.
```
