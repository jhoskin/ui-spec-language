# Tessera: a worked example of the consensus specification format

This file is the specification package of Tessera, a small image browser, in the consensus format. Each second-level section is one package file.

## spec/conventions.md

```text
Levels: must (absence can block or mislead a user), should. Outcomes: passed, failed, inapplicable.
Observations: place, text, role, name, state, focus, announcement, address, history depth,
  scroll. A rule changes only what it names. An unlisted trigger keeps the platform default.
The inventory is closed. Quoted text is exact.
Face line: number, rank rN (drop the highest first), emphasis P|N|Q (primary, normal, quiet), item.
Every rule is extracted from the reference. "Fail:" lines are unconfirmed.
Up-link: link to the parent place. Placeholder: a shimmer block of the size of its content.
```

## spec/app.md

```text
Chart
  Catalog --open row--> Category --open tile--> Image --step--> Image
  Category --up-link--> Catalog      Image --up-link--> Category
  unknown address --> Missing

Regions: Place | Header | Theme (Dark | Light) | DemoNotes (Closed | Open) | Toast (None | Notice | Error)

Header face (not pinned)
  1 r1 P link "Tessera" to the unfiltered catalog
  2 r3 Q button "Demo notes"
  3 r2 Q button "Theme: Dark" | "Theme: Light"

DemoNotes.Open face
  1 "All data is generated in the page. Tag edits last until you reload."
  2 "Long Exposures loads slowly."
  3 "Film Scans fails on its first load."
  4 "In every category, the third batch of images fails once."
  5 "Saving the tag "flaky" fails once per image."

Missing  States: PageMissing | CategoryMissing | ImageMissing
  1 r1 P title "Page not found" | "Category not found" | "Image not found"
  2 r3 Q "The address may be mistyped or out of date." | "There is no image with that ID in Coastlines."
  3 r2 N link "Go to the catalog" | "Go to Coastlines"

Toast  States: None | Notice | Error
  1 r1 N text  2 r2 N action button  3 r3 Q Error only: button "×", name "Dismiss"
```

```text
APP-1 [must] While Dark or Light, when the user activates the theme button, Tessera shall switch
  the theme. Dark is the default; the platform preference is ignored.
APP-2 [should] While Open, when the user activates outside or dismisses, Tessera shall close
  the notes.
APP-3 [must] While Missing, the address shall stay as entered.
NAV-1 [must] When the user opens a link, Tessera shall add a history entry. If the target is the
  current address, Tessera shall only scroll to the top.
NAV-2 [must] When the filter applies, the order changes or the user steps, Tessera shall rewrite
  the current entry.
NAV-3 [must] overrides NAV-1. When the user follows an up-link and the current entry was opened
  from that parent, Tessera shall go Back. "Catalog" carries the last applied filter.
NAV-4 [must] When a place waits for data, Tessera shall keep the previous face until "slow".
NAV-5 [must] When the place, order or image changes, Tessera shall remove the toast.
TST-1 [must] When a toast is raised, Tessera shall replace any old toast and its action.
TST-2 [must] While Notice, Tessera shall remove the toast after 6 s. Pointer or focus on it
  stops the countdown, which then restarts.
TST-3 [must] While Error, Tessera shall keep the toast until answered. "×" focuses the tag field.
```

```text
NAV-T1 Arrival in a place. First matching row wins.
  1 first paint after start or reload     top; focus not moved
  2 Category, from one of its images      scroll as rows 6 and 7; GRD-7; center that image's
                                          tile if hidden; focus it
  3 Category, after an order change       top; focus stays on the chosen option
  4 Image, after a step                   scroll kept; focus stays on the step button used (now
                                          off: the other); else the title
  5 Catalog, by Back or Forward           restore scroll; focus the last visited row, else title
  6 any other Back or Forward             restore scroll; focus the title
  7 otherwise                             top; focus the title
The title shows no focus mark.
```

```text
NAV-T2 Memory. Direct: an address entered while running.
  region                      step        Back/Forward  reload         direct
  scroll                      NAV-T1      restored      top            top
  filter, order shown         address     address       address        address
  session order (rows)        last shown  last shown    Newest, until  last shown
                                                        a category
  batches, tag edits, faults,
  latency spent               kept        kept          cleared        kept
  opened-from-parent          kept        kept          kept           none
  toast, tag field text       removed     removed       removed        removed
  theme                       kept        kept          kept           kept
```

```text
PRP-1 Always, under all faults: after a tile is opened and any steps, one Back shows the
  category.
PRP-2 Always: only "Try again" or "Retry" requests a failed batch again.
```

## spec/places/catalog.md

```text
Catalog  States: Loading | Ready (All | Some | None)

Catalog.Loading face: 1 r1 P title "Catalog"  2 r2 N field, off  3 r3 Q eight placeholder rows

Catalog.Ready face
  1 r2 N title "Catalog"
  2 r3 N search field, name "Filter categories", placeholder WEB-3
  3 r5 N button "Clear", while the field has text
  4 r4 Q count line, announced politely (DAT-5)
  5 r1 P rows (DAT-7), each one link to the category in the session order:
         a r4 Q swatches: hues of the three newest images, or a dashed box
         b r1 P name "Monochrome"
         c r2 N "1,204 images" | "1 image" | "Empty" (Q)
         d r3 Q "Updated 17 Jun 2025"
Catalog.None: item 5 is `No categories match "xyz"`, button "Clear filter".
```

```text
CAT-1 [must] While Ready, when the filter text changes, Tessera shall update "Clear" at once,
  and apply it 300 ms after the last change.
CAT-2 [must] While Ready, when the user commits the filter, Tessera shall apply it at once and,
  if exactly one row remains, open it.
CAT-3 [must] While Ready, when the user dismisses the filter, Tessera shall clear and apply;
  if it was empty, focus goes to none.
CAT-4 [must] While Ready, when "Clear" or "Clear filter" is activated, Tessera shall clear,
  apply and focus the field.
CAT-5 [should] While Ready, when the user asks for the filter, Tessera shall focus the field.
  It never takes focus unasked.
CAT-6 [should] While Ready, when the user moves down from the field, Tessera shall focus the
  first row; up from it returns.
```

## spec/places/category.md

```text
Category  States: Empty | FirstLoading | FirstFailed | Grid (Idle | More | MoreFailed | Complete)

Toolbar, pinned (Empty: items 1 and 2 only)
  1 r3 N up-link "Catalog", then "/"
  2 r1 P title "Coastlines"
  3 r4 Q "310 images"
  4 r2 N exclusive choice "Sort images", far end: "Newest" "Captured" "Name" "Size"

Category.Grid face
  5 r1 P tiles: one link per loaded image, name and tooltip the file name; caption DAT-6
  6 r2 Q More: one placeholder tile per image due
         MoreFailed: alert "Couldn't load more images." and button "Retry"
         Complete: "All 310 images shown", if above one batch
FirstLoading: placeholder tiles, one per image due, at most one batch.
FirstFailed: alert "Couldn't load images", "Nothing was loaded. Check your connection and
  try again.", button "Try again".
Empty: "No images in this category yet", "Images added to Infrared will appear here."
```

```text
GRD-1 [must] While Grid, when the grid end comes near the window bottom (WEB-5), Tessera shall
  request the next batch (FIX-4).
GRD-2 [must] If the first batch fails, then Tessera shall show FirstFailed.
GRD-3 [must] If a later batch fails, then Tessera shall keep the tiles and show MoreFailed.
  Fail: scrolling retries.
GRD-4 [must] While FirstFailed or MoreFailed, when "Try again" or "Retry" is activated, Tessera
  shall show placeholders at once and, on success, focus the first new tile.
GRD-5 [must] While Grid, when the user picks another order, Tessera shall show it and make it
  the session order. The active option does nothing.
GRD-6 [must] While Grid, the tiles shall be one focus stop, the tile focused last. Moving goes
  by tile, by row (down with no tile below: the last), or to an end. No wrap.
GRD-7 [must] When the user arrives from an image of this category, Tessera shall show tiles
  through that image's batch: at once if a batch of this order is loaded, else in one request.
GRD-8 [must] When the user returns, Tessera shall show the batches loaded for this category
  and order at once. A failed batch stays failed.
```

## spec/places/image.md

```text
Image  States: Loading | Ready.   Tags  States: None | Some | Full

Image.Loading face: 1 r1 P up-link "← Monochrome"  2 r2 Q placeholder image  3 r3 Q six placeholder lines

Image.Ready face
  1  r2 N up-link "← Monochrome"
  2  r6 Q "1 of 1,204"
  3  r4 N button "Previous", off at the first
  4  r5 N button "Next", off at the last
  5  r1 P the whole image
  side panel:
  6  r3 P title "broken-dune-1.jpg"
  7  r7 Q heading "Tags", "2 of 12"
  8  r8 N chips in the order added: tag and remove control "×", name "Remove tag landscape"; None: "No tags yet"
  9  r9 N field, name "Add a tag", placeholder WEB-3; Full: off, "Tag limit reached (12)"
  10 r10 Q message line, announced politely
  11 r11 Q heading "Details"; Captured "12 Jun 2024, 08:48"; Added "17 Jun 2025";
          Dimensions "3000 × 3000 (9.0 MP)"; File size "2.5 MB (2,501,130 bytes)"; ID "2973"
  12 r12 Q hint WEB-3
No download, delete, share or zoom.
```

```text
IMG-1 [must] While Ready, when the user steps, Tessera shall show the next or previous image of
  the whole category in this order, loaded or not. No wrap.
IMG-2 [must] While Ready or Loading, when the user goes up, Tessera shall follow the up-link.
  While Loading, nothing else works.
IMG-3 [must] While focus is in Tags or a toast, Tessera shall ignore step, go up and add tag.
IMG-4 [should] While None or Some, when the user asks to add a tag, Tessera shall focus the field.
TAG-1 [must] While None or Some, when the user commits the field, Tessera shall split the text at
  commas, skip blanks, normalize each part (DAT-4), and take the first match:
  a length not 2 to 24: refuse; "Tags need 2 to 24 letters, digits or hyphens."
  b already on the image: its chip pulses for 1.2 s; no message
  c 12 tags: refuse; "An image can have at most 12 tags."
  d otherwise: add at the end, pending (dimmed, dashed), and save.
  The field keeps the refused parts, joined by ", ". The message line shows only this commit.
TAG-2 [must] overrides TAG-1. When a commit reaches 12 tags, Tessera shall focus the last remove control.
TAG-3 [must] If a save fails, then Tessera shall remove the chip and raise, in any place, error
  `Couldn't save tag "flaky" on broken-dune-1.jpg.` with "Retry" (add, save, focus the field).
TAG-4 [must] While Some or Full, when the user removes a tag, Tessera shall remove it at once,
  focus the next remove control, else the previous, else the field, and raise notice
  `Removed tag "landscape".` with "Undo".
TAG-5 [must] While Notice, when the user undoes, Tessera shall restore the tag at its old
  position and focus its remove control. At 12 tags, error
  `Can't restore "landscape": the image already has 12 tags.`
TAG-6 [should] While Some, when the user selects the last tag from the empty field, Tessera shall
  focus the last remove control and remove nothing.
TAG-7 [should] While Ready, when the user dismisses the field, Tessera shall clear text
  and message; if it was empty, focus goes to none.
```

## spec/data.md

```text
DAT-1 Dates: UTC, never relative: "3 Mar 2024", "12 Jun 2024, 08:48".
DAT-2 Counts: "1 image", "1,204 images".
DAT-3 Size, decimal: from 999,500 bytes one-decimal MB, else whole kB.
      2,501,130 -> "2.5 MB"; 999,500 -> "1.0 MB"
DAT-4 Normalize a tag: trim; lower case; spaces and underscores to one hyphen; drop all but a-z,
      0-9, hyphen; no double or end hyphens.   "Golden Hour" -> "golden-hour"
DAT-5 Count line: "24 categories"; filtered "0 of 24 categories"; one match adds WEB-3.
DAT-6 Orders; ties by name, then ID. Newest: Added, latest first. Captured: latest first.
      Name: natural, case ignored, "-9" before "-10". Size: largest first.
      Caption: Added date | Captured date | file name without ".jpg", monospace | size.
DAT-7 Catalog order: Updated latest first, then name. Updated = newest Added of its images;
      if none, a stored date.
DAT-8 Filter: every word of the trimmed text occurs in the name, any order, case ignored.
      "ni" -> Night Markets, Night Sky, Botanical
```

## spec/tasks.md

```text
TSK-1 Find a category. Start: Catalog.Ready.
  Steps: ask for the filter; enter "film"; commit.  Count: 3
  Outcome: Film Scans, new entry; first visit FirstFailed (FIX-6).
TSK-2 Add tags. Start: Image.Ready, "broken-dune-1.jpg".
  Steps: ask to add a tag; enter "Golden Hour, bw"; commit.  Count: 3
  Outcome: "golden-hour", "bw" added; "4 of 12".
TSK-3 Browse and return. Start: Coastlines Grid.
  Steps: open tile 2; step next; step next; go Back.  Count: 4
  Outcome: Coastlines; "pale-summit-4.jpg" focused; history depth unchanged.
TSK-4 Keep an order. Start: Coastlines Grid, from the catalog.
  Steps: pick "Size"; go up; open Alpine.  Count: 3
  Outcome: Alpine by Size.
```

## spec/appearance.md

```text
Token roles: background; surface; raised (hover); line; text; muted (meta); accent; on accent;
  danger (tag message, error stripe); well (behind images).
Layout intent: Catalog: centered column with a maximum width. Category: pinned toolbar; grid
  with a minimum tile width. Image: side panel with a fixed width and a collapse threshold.
  Toast: pinned, bottom center.
VIS-1 [should] [graphic] Accent only on keyboard focus, the active order, the duplicate pulse. Check: token.
VIS-2 [should] [graphic] A tile is a square well with the whole image, never cropped; hover and
  focus outline it, never enlarge it. Check: inspection.
VIS-3 [should] [graphic] Remove controls are neutral: removal can be undone. Check: token.
VIS-4 [should] [graphic] Toast inverted; an error toast adds a danger stripe. Check: token.
VIS-5 [should] [graphic] Reduced motion stops motion; the pulse becomes an outline. Check: inspection.
```

## spec/modality/web.md

```text
WEB-1 Addresses: "#/", "#/?q=night", "#/c/coastlines?sort=name", "#/c/coastlines/i/1227".
  Slug: lower case, spaces to hyphens. Newest is not written; an unknown sort means Newest.
WEB-2 Window title: "pale-summit-2.jpg · Coastlines · Tessera".
WEB-3 Strings: "Filter categories (press /)"; suffix " · Enter to open"; "Add a tag, then press
  Enter"; hint "Left and Right arrows step through images. Esc returns to the grid. T adds a tag."
WEB-4 Bindings:
  open: click or Enter; modified click: new tab
  ask for the filter: "/" outside a text field     commit filter or tags: Enter
  dismiss filter, tag field, notes: Escape          go up: Escape
  move in rows: Down, Up                            move in grid: arrows, Home, End
  step: Left, Right                                 ask to add a tag: T
  commit tags also: "," at once
  select last tag: Backspace in the empty field     remove: Backspace or Delete on "×"
  undo: Ctrl/Cmd+Z outside a text field
WEB-5 Load margin 400 px. Tile at least 140 px, stretched. Catalog column 880 px. Panel 320 px,
  under the image below 800 px. Adaptation: below 560 px a row drops swatches; the date goes
  under the name. Type 22, 18, 15, 14, 12 px from the catalog title to meta. Focus ring 2 px.
WEB-6 Tokens, dark/light: background #111315/#f5f4f0; surface #191c20/#ffffff; raised
  #23272c/#eae8e2; line #30353b/#d3d0c8; text #e9ebee/#1b1c1e; muted #9ca3ad/#5d6269;
  accent #f2b544/#8a5200; on accent #1b1403/#ffffff; danger #ff9383/#b3261e; well
  #0a0b0d/#dedbd3.
```

## fixture/

```text
FIX-1 Catalog order, image counts: Monochrome 1204, Coastlines 310,
  Wildlife 262, Architecture 187, Long Exposures 90, Desert Roads 67, Night Markets 149,
  Workshops 133, Abandoned Places 177, Night Sky 84, Aerial 121, Alpine 208, Rail Yards 55,
  Festivals 91, Film Scans 40, Reflections 36, Macro 58, Street Portraits 73, Still Life 12,
  Botanical 24, Infrared 0, Storm Fronts 5, Harbors 1, Underwater 0.
FIX-2 3,387 fixed images from ID 1001. A series of 3 to 14 shares a base name and an Added
  date. 0 to 5 tags. The picture: a gradient, ID centered.
FIX-3 Monochrome, Newest, first: 2973 "broken-dune-1.jpg", tags landscape, needs-review.
  Coastlines, Newest: 1226 to 1229, "pale-summit-1.jpg" to "pale-summit-4.jpg".
FIX-4 Batch: 24 images.
FIX-5 Latency: catalog 700 ms, first time only. Batch 600 ms. Image 150 ms, first
  open only. Long Exposures: batch and image 2500 ms. Tag save 500 ms.
FIX-6 Faults, once per session: first batch of Film Scans; third batch of every category,
  once per category, not per order; save of "flaky", once per image. An abandoned request
  uses no fault.

Timelines
  catalog  @250 slow: Loading, top | @700 success: Ready | abandoned: discarded
  batch    @250 slow: placeholders | @600 success: tiles | failure: GRD-2, GRD-3
           retry: placeholders @0 | abandoned: discarded
  image    @150 success | @250 slow (Long Exposures only): Loading, top unless a step
  tag save @0 pending chip | @500 success: plain chip | failure: TAG-3 | retry: new save
           abandoned: never
```

## scenarios/

```text
SCN-GRD-3a verifies GRD-3, GRD-4, PRP-2, FIX-6
Given Coastlines, first visit. When scroll to the end, repeatedly.
Then 48 tiles, alert "Couldn't load more images.", "Retry"; no more requests.
When activate "Retry". Then placeholders at once; after 600 ms 72 tiles, focus on tile 49.

SCN-CAT-2a verifies CAT-1, CAT-2, NAV-1
Given Catalog. When enter "film". After 300 ms one row, "1 of 24 categories · Enter to open".
When commit. Then title "Film Scans"; history depth plus 1.

SCN-TAG-1a verifies TAG-1, DAT-4
Given "broken-dune-1.jpg". When commit "Landscape, x, Golden Hour".
Then "landscape" pulses; "golden-hour" pending; field "x";
"Tags need 2 to 24 letters, digits or hyphens."

SCN-TAG-3a verifies TAG-3, FIX-6
Given "broken-dune-1.jpg". When commit "flaky". After 500 ms no chip "flaky";
alert `Couldn't save tag "flaky" on broken-dune-1.jpg.`
When activate "Retry". After 500 ms chip "flaky", saved.

SCN-NAV-T1a verifies NAV-T1.2, PRP-1, IMG-1
Given Coastlines. When open tile 2; step next twice; go Back.
Then focus on tile "pale-summit-4.jpg".

SCN-APP-3a verifies APP-3, WEB-1
Given address "#/c/coastlines/i/2973". Then "Image not found", "Go to Coastlines";
address unchanged.
```

## sidecar/matrix.md

```text
Category grid, excerpt. "-": cannot occur.
  state \ event  near end   batch ok        batch fails   Retry          order change
  Idle           More       -               -             -              GRD-5
  More           nothing    Idle, Complete  MoreFailed    -              GRD-5, discarded
  MoreFailed     nothing    -               -             More (GRD-4)   GRD-5
  Complete       nothing    -               -             -              GRD-5
```
