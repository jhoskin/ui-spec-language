# Appearance

The core holds emphasis ranks (in the faces), token roles, layout intent and
presentation commitments. Token values and sizes are in the modality sheet.

```text
Token roles
  background    behind every place
  surface       cards, fields, controls
  well          columns, the selection bar
  line          borders
  text          main text
  muted         quiet text and marks
  accent        see VIS-1
  on accent     text on accent
  danger        alerts, messages, "Delete card", the stripe of an error notice
  inverse, on inverse   the notice

Layout intent
  Board   the filter bar is pinned at the top. The columns are a row of columns of equal
          width; the row scrolls sideways when it does not fit. A column is a stack of cards.
          The selection bar is between the filter bar and the columns.
  Card    one centered column with a maximum width. The parts are a stack in face order.
  Missing one centered column with a maximum width.
  Notice  pinned at the bottom, at the start side, above the content.
```

```text
VIS-1 [should] [graphic] Accent shows only on: keyboard focus, a toggle that is on, a choice
  that is chosen, the edge of a selected card, the outline of a carried card. Check: token.
VIS-2 [should] [graphic] A selected card has an accent edge and its toggle is on. Check: inspection.
VIS-3 [should] [graphic] A card with mark "Saving…" or "Moving" has a dashed outline. Check: inspection.
VIS-4 [should] [graphic] A toggle that is mixed has a dashed accent outline. Check: inspection.
VIS-5 [should] [graphic] The notice has inverse colours. An error notice adds a danger stripe.
  Check: token.
VIS-6 [should] [graphic] Reduced motion stops the motion of placeholders. Check: inspection.
VIS-7 [should] [graphic] The place title shows no focus mark. Check: inspection.
```
