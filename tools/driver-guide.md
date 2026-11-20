# Raw driver for the reference build

You cannot run a browser. A helper outside your directory runs one for you.

Write a request file `requests/<name>.json` in your work directory. Wait for
`results/<name>.json`. Each request starts a fresh browser and a fresh fixture.

```sh
until [ -f results/a1.json ]; do sleep 0.3; done; cat results/a1.json
```

## Request

```json
{
  "profile": "default",
  "start": "#/",
  "steps": [
    { "advance": 2200 },
    { "focus": { "card": "SL-101" } },
    { "key": "ArrowDown" },
    { "click": { "role": "button", "name": "Clear filters" } }
  ]
}
```

- `profile`: a profile of `fixture/service.json`. The default is `default`.
- `start`: the address part after the page, for example `#/` or `#/card/SL-114`.
- `viewport`: optional, `{ "width": 1500, "height": 900 }`.

## Steps

The clock moves only on an `advance` step.

| Step | Effect |
| --- | --- |
| `{ "advance": 400 }` | Move the clock by that number of ms |
| `{ "key": "Enter" }` | Press a key or a chord (`"Shift+x"`, `"Control+z"`, `"Tab"`, `"Escape"`, `"Space"`) |
| `{ "type": "text" }` | Type text into the part that has focus |
| `{ "fill": target, "value": "text" }` | Replace the text of a field |
| `{ "click": target }` | Pointer click; `"modifiers": ["Meta"]` is optional |
| `{ "focus": target }` | Put focus on a part |
| `{ "pointer": "down", "on": target, "at": "middle" }` | Press the pointer on a part (`top`, `middle`, `bottom`) |
| `{ "pointer": "move", "on": target, "at": "top" }` | Move the pressed pointer to a part; `"x"` and `"y"` also work |
| `{ "pointer": "up" }` | Release the pointer |
| `{ "back": true }`, `{ "forward": true }`, `{ "reload": true }` | Browser history and reload |
| `{ "address": "#/card/SL-101" }` | Enter an address while the app runs |
| `{ "scrollTo": 300 }` | Scroll the window |

A target is `{ "card": "SL-101" }`, `{ "role": "button", "name": "Undo" }` or
`{ "text": "Still loading…" }`.

## Result

A list with one entry for the start and one for each step. Each entry has the
address, the history length, the window title, the focus, the vertical
scroll, the new announcements, the request log, and `screen`: the
accessibility tree of the page as text.
