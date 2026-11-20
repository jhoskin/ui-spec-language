# Scenarios

Each scenario cites the identifiers that it verifies. It asserts only what a
user perceives, and the requests of the fixture. A scenario never names a state.

## Grammar

One step is one sentence that ends with a full stop.

```text
SCN-<AREA>-<number> verifies <identifier>, <identifier>
Given profile <name>.                      the fixture profile; the default is "default"
Given start at board.                      also with: text "<text>" labels <a>,<b> assignees <a>,<b>
Given start at card <id>.
Given start at address "<written form>".   for one modality only; the header has [web]
Given focus on card <id>.
After <n> ms.                              advance the clock
Remember history depth as <name>.
When <intent> <arguments>.                 an intent of spec/app.md; "via pointer" picks that binding
Then place title "<text>".
Then address board.                        also with text, labels, assignees
Then address card <id>.
Then address is "<written form>".
Then history depth is <name>.              or "<name> plus <n>"
Then focus <role> "<name>".                or "focus card <id>", "focus place title", "focus none"
Then column "<name>" cards <id>, <id>.     the visible cards from the top; "cards none"
Then column "<name>" starts <id>, <id>.
Then text "<text>" is shown.               the whole text of one part; or: Then no text "<text>".
Then notice "<text>" with "<action>".      or "with no action"; or: Then no notice.
Then card <id> has mark "<text>".          or "has no mark", "is selected", "is not selected"
Then <role> "<name>" is <state>.           on, off, mixed, chosen, not chosen, disabled, enabled,
                                           shown, absent; "in "<group>"" picks a group
Then field "<name>" has text "<text>".
Then scroll is top.                        or "scroll is not top"
Then card <id> is in view.
Then requests <operation> <n>.             the number of requests of that operation from the start
Then announcement "<text>".
```

All columns are loaded 2200 ms after a start at the board.
