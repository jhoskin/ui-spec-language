"""Walks the public scenarios (scenarios/README.md grammar) against the App.

Each intent is done with the key bindings of TRM-8, as a user of the terminal
does it: Tab to a control and Enter, or a key on the card that has focus.
Every check reads the semantic dump (TRM-H5).
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TUI = os.path.dirname(HERE)
ROOT = os.path.dirname(TUI)
sys.path.insert(0, TUI)

from app import App  # noqa: E402
import addresses  # noqa: E402

FIXTURE = os.path.join(ROOT, "fixture")
SCENARIOS = os.path.join(ROOT, "scenarios")
PEOPLE = {"Ana Ruiz": "ana", "Ben Okafor": "ben", "Chloé Martin": "chloe", "Dev Patel": "dev",
          "Mika Ito": "mika", "Unassigned": "none"}


class StepError(AssertionError):
    pass


def parse_scenarios(path):
    """Returns [(header, [steps])] for each scenario in a file."""
    out = []
    with open(path, encoding="utf-8") as f:
        text = f.read()
    for block in re.findall(r"```text\n(.*?)```", text, re.S):
        cur = None
        for line in block.splitlines():
            line = line.strip()
            if not line:
                continue
            if line.startswith("SCN-"):
                cur = (line, [])
                out.append(cur)
            elif cur is not None:
                cur[1].append(line)
    return out


def all_scenarios():
    out = []
    for name in sorted(os.listdir(SCENARIOS)):
        if name.endswith(".md") and name != "README.md":
            out.extend(parse_scenarios(os.path.join(SCENARIOS, name)))
    return out


def unquote_list(s):
    """'"Ana Ruiz",Unassigned' -> ['Ana Ruiz', 'Unassigned']"""
    return [x.strip().strip('"') for x in re.findall(r'"[^"]*"|[^,]+', s)]


def arg_of(rest):
    rest = rest.strip()
    if rest.startswith('"') and rest.endswith('"'):
        return rest[1:-1]
    return rest


def _painted(rows, s):
    joined = "\n".join(rows)
    if s in joined:
        return True
    first = s.split("\n")[0]
    return any(first[:k] + "…" in joined for k in range(len(first), 0, -1))


def check_grid(app):
    """TRM-H6 on the grid that the app would paint: each name and text of the dump is
    inside its rect (cut as TRM-A4 allows), with the state marks of TRM-10."""
    L = app.layout
    d = app.dump()
    grid = ["".join(r) for r in L.chars]

    def rect_rows(rect):
        r, c, h, w = rect
        if r < 1 or r + h - 1 > L.h or c < 1 or c + w - 1 > L.w:
            raise StepError("rect off the screen: %r" % (rect,))
        return [grid[rr - 1][c - 1:c - 1 + w] for rr in range(r, r + h)]

    for p in d["parts"]:
        rows = rect_rows(p["rect"])
        flat = "".join(rows)
        for label in (p["name"], p["text"]):
            if not label:
                continue
            if p["role"] == "card":
                cid, title = label.split(" ", 1)
                if cid not in rows[0] or not _painted(rows[1:2], title):
                    raise StepError("card %r not painted: %r" % (label, rows))
                continue
            if "\n" in label or (p["role"] == "text" and len(rows) > 1):
                words = label.split()
                if words and words[0] not in "\n".join(rows):
                    raise StepError("%r not painted: %r" % (label, rows))
                continue
            if not _painted(rows, label):
                raise StepError("%s %r not painted in %r: %r" % (p["role"], label, p["rect"], rows))
        mark = {"on": "[x] ", "off": "[ ] ", "mixed": "[-] ", "chosen": "(o) ", "not chosen": "( ) "}.get(p["state"])
        if mark and mark not in flat:
            raise StepError("state mark of %r not painted: %r" % (p, rows))
        if p["disabled"] and "(off)" not in flat:
            raise StepError("(off) of %r not painted" % (p,))
    for c in d["cards"]:
        if c["inView"]:
            rows = rect_rows(c["rect"])
            if c["id"] not in rows[0] or ("[x] " in rows[0]) != c["selected"]:
                raise StepError("card %r not painted: %r" % (c, rows))
            for m in c["marks"]:
                if m not in rows[0]:
                    raise StepError("mark %r of %s not painted" % (m, c["id"]))
    if d["focus"] is not None:
        p = d["parts"][d["focus"]]
        if L.cursor != (p["rect"][0], p["rect"][1]):
            raise StepError("cursor %r is not at %r" % (L.cursor, p))
    elif L.cursor is not None:
        raise StepError("cursor shown with focus none")
    n = d["notice"]
    if n is not None:
        prefix = ("i " if n["kind"] == "info" else "! ")
        if not any(row.startswith(prefix + n["text"][:20]) for row in grid[-3:-1]):
            raise StepError("notice not painted")


class Driver:
    def __init__(self):
        self.profile = "default"
        self.app = None
        self.memory = {}

    # -- dump helpers ---------------------------------------------------
    def d(self):
        return self.app.dump()

    def focused(self):
        d = self.d()
        return d["parts"][d["focus"]] if d["focus"] is not None else None

    def key(self, *keys):
        for k in keys:
            self.app.key(k)

    def type_text(self, text):
        for ch in text:
            self.key("space" if ch == " " else ("enter" if ch == "\n" else ch))

    def tab_to(self, pred, what):
        n = len(self.d()["parts"]) + 3
        for _ in range(n):
            p = self.focused()
            if p is not None and pred(p):
                return True
            self.key("tab")
        p = self.focused()
        if p is not None and pred(p):
            return True
        return False

    def activate(self, role, name, group=None, not_group=None, required=True):
        def pred(p):
            return (p["role"] == role and p["name"] == name and (group is None or p["group"] == group)
                    and (not_group is None or p["group"] != not_group))
        if not self.tab_to(pred, name):
            if required:
                raise StepError("cannot reach %s %r" % (role, name))
            return False
        self.key("enter")
        return True

    def card_pos(self, cid):
        d = self.d()
        cards = d["cards"]
        for c in cards:
            if c["id"] == cid:
                col = c["column"]
                same = [x["id"] for x in cards if x["column"] == col]
                return d["columns"].index(col), same.index(cid)
        raise StepError("card %s is not shown" % cid)

    def focus_card(self, cid):
        p = self.focused()
        if p is None or p["role"] != "card":
            if not self.tab_to(lambda p: p["role"] == "card", "card"):
                raise StepError("no card takes focus")
        target_col, target_pos = self.card_pos(cid)
        for _ in range(10):
            cur = self.focused()["name"].split(" ")[0]
            ccol, _ = self.card_pos(cur)
            if ccol == target_col:
                break
            self.key("right" if ccol < target_col else "left")
        self.key("home")
        for _ in range(target_pos):
            self.key("down")
        if self.focused()["name"].split(" ")[0] != cid:
            raise StepError("could not focus %s" % cid)

    # -- steps ------------------------------------------------------------
    def run(self, steps, grid_check=True):
        for step in steps:
            try:
                self.step(step)
                if grid_check and self.app is not None:
                    check_grid(self.app)
            except StepError as e:
                raise StepError("%s -> %s" % (step, e))

    def step(self, s):
        assert s.endswith("."), s
        s = s[:-1]
        m = re.match(r"Given profile (\S+)$", s)
        if m:
            self.profile = m.group(1)
            return
        m = re.match(r"Given start at board$", s)
        if m:
            self.app = App(FIXTURE, self.profile, "board")
            return
        m = re.match(r"Given start at card (\S+)$", s)
        if m:
            self.app = App(FIXTURE, self.profile, "card/" + m.group(1))
            return
        m = re.match(r'Given start at address "(.*)"$', s)
        if m:
            self.app = App(FIXTURE, self.profile, m.group(1))
            return
        m = re.match(r"Given focus on card (\S+)$", s)
        if m:
            self.focus_card(m.group(1))
            return
        m = re.match(r"After (\d+) ms$", s)
        if m:
            self.app.advance(int(m.group(1)))
            return
        m = re.match(r"Remember history depth as (\S+)$", s)
        if m:
            self.memory[m.group(1)] = self.d()["depth"]
            return
        if s.startswith("When "):
            return self.when(s[5:])
        if s.startswith("Then "):
            return self.then(s[5:])
        raise StepError("unknown step")

    def when(self, s):
        intent, _, rest = s.partition(" ")
        arg = arg_of(rest)
        a = self.app
        if intent == "toggle-select":
            self.focus_card(arg)
            self.key("x")
        elif intent == "open-card":
            self.focus_card(arg)
            self.key("enter")
        elif intent == "pick-up":
            self.key("space")
        elif intent == "carry":
            self.key(arg)
        elif intent == "drop":
            self.key("space")
        elif intent == "cancel-carry":
            self.key("esc")
        elif intent == "move-focus":
            self.key({"first": "home", "last": "end"}.get(arg, arg))
        elif intent == "delete-card":
            p = self.focused()
            if p is not None and p["role"] == "card":
                self.key("delete")
            elif a.place().kind == "card":
                self.activate("action", "Delete card")
            else:
                self.key("delete")
        elif intent == "select-column":
            self.activate("action", "Select all in %s" % arg)
        elif intent == "clear-selection":
            self.activate("action", "Clear selection")
        elif intent == "bulk-move":
            self.activate("action", arg, group="Move selected to")
        elif intent == "bulk-label":
            self.activate("toggle", arg, group="Label selected")
        elif intent == "toggle-label-filter":
            self.activate("toggle", arg, group="Labels")
        elif intent == "toggle-assignee-filter":
            self.activate("toggle", arg, group="Assignee")
        elif intent == "clear-filters":
            if not self.activate("action", "Clear filters", required=False):
                self.activate("action", "Show all cards")
        elif intent == "change-filter-text":
            if not self.tab_to(lambda p: p["role"] == "field" and p["name"] == "Filter cards", "filter"):
                raise StepError("no filter field")
            self.key("ctrl-u")
            self.type_text(arg)
        elif intent == "commit-filter":
            self.key("enter")
        elif intent == "ask-filter":
            self.key("/")
        elif intent == "dismiss":
            self.key("esc")
        elif intent == "undo":
            self.key("ctrl-z")
        elif intent == "notice-action":
            d = self.d()
            self.activate("action", d["notice"]["action"], group="Notice")
        elif intent == "dismiss-notice":
            self.activate("action", "Dismiss", group="Notice")
        elif intent == "retry-place":
            self.activate("action", "Try again")
        elif intent == "retry-column":
            self.activate("action", "Retry %s" % arg)
        elif intent == "retry-comments":
            self.activate("action", "Retry", not_group="Notice")
        elif intent == "go-up":
            self.activate("up-link", "← Board")
        elif intent == "go-back":
            self.key("ctrl-b")
        elif intent == "go-forward":
            self.key("ctrl-f")
        elif intent == "reload":
            self.key("ctrl-r")
        elif intent == "open-home":
            self.activate("link", "Slate")
        elif intent == "open-board-link":
            self.activate("link", "Go to the board")
        elif intent == "enter-address":
            self.key("ctrl-g")
            self.type_text(arg)
            self.key("enter")
        elif intent == "edit-title":
            self.activate("action", "Edit title", required=False)
        elif intent == "change-title-text":
            p = self.focused()
            if p is None or p["name"] != "Title" or p["role"] != "field":
                raise StepError("focus is not in the title field")
            self.key("ctrl-u")
            self.type_text(arg)
        elif intent == "commit-title":
            self.key("enter")
        elif intent == "leave-title":
            self.key("tab")
        elif intent == "toggle-label":
            self.activate("toggle", arg, group="Labels", required=False)
        elif intent == "choose-assignee":
            self.activate("choice", arg, group="Assignee")
        elif intent == "edit-description":
            self.activate("action", "Edit description", required=False)
        elif intent == "change-description-text":
            if not self.tab_to(lambda p: p["role"] == "field" and p["name"] == "Description", "desc"):
                raise StepError("no description field")
            self.key("ctrl-u")
            self.type_text(arg)
        elif intent == "commit-description":
            p = self.focused()
            if p is not None and p["name"] == "Description" and p["role"] == "field":
                self.key("ctrl-s")
            else:
                self.activate("action", "Save")
        elif intent == "cancel-description":
            self.activate("action", "Cancel")
        elif intent == "change-comment-text":
            if not self.tab_to(lambda p: p["role"] == "field" and p["name"] == "Add a comment", "comment"):
                raise StepError("no comment field")
            self.key("ctrl-u")
            self.type_text(arg)
        elif intent == "commit-comment":
            p = self.focused()
            if p is not None and p["name"] == "Add a comment":
                self.key("ctrl-s")
            else:
                self.activate("action", "Add comment")
        else:
            raise StepError("unknown intent %s" % intent)

    # -- checks -----------------------------------------------------------
    def fail(self, msg):
        d = self.d()
        raise StepError("%s\n  focus=%s notice=%s address=%s title=%s" % (
            msg, self.focused(), d["notice"], d["address"], d["title"]))

    def texts(self):
        d = self.d()
        out = []
        for p in d["parts"]:
            if p["text"] is not None:
                out.append(p["text"])
            if p["name"] is not None:
                out.append(p["name"])
        return out

    def column_cards(self, name):
        d = self.d()
        if name not in d["columns"]:
            return []
        return [c["id"] for c in d["cards"] if c["column"] == name]

    def find(self, role, name, group=None):
        for p in self.d()["parts"]:
            if p["role"] == role and p["name"] == name and (group is None or p["group"] == group):
                return p
        return None

    def board_addr(self, rest):
        q, labels, who = "", [], []
        m = re.search(r'text "([^"]*)"', rest)
        if m:
            q = m.group(1)
        m = re.search(r"labels (\S+)", rest)
        if m:
            labels = m.group(1).split(",")
        m = re.search(r"assignees (.+)$", rest)
        if m:
            who = [PEOPLE[x] for x in unquote_list(m.group(1))]
        return addresses.board_written(q, labels, who)

    def then(self, s):
        d = self.d()
        m = re.match(r'place title "(.*)"$', s)
        if m:
            if d["title"] != m.group(1):
                self.fail("place title is %r" % d["title"])
            return
        m = re.match(r"address board(.*)$", s)
        if m:
            want = self.board_addr(m.group(1))
            if d["address"] != want:
                self.fail("address is %r, want %r" % (d["address"], want))
            return
        m = re.match(r"address card (\S+)$", s)
        if m:
            if d["address"] != "card/" + m.group(1):
                self.fail("address is %r" % d["address"])
            return
        m = re.match(r'address is "(.*)"$', s)
        if m:
            if d["address"] != m.group(1):
                self.fail("address is %r" % d["address"])
            return
        m = re.match(r"history depth is (\S+)(?: plus (\d+))?$", s)
        if m:
            want = self.memory[m.group(1)] + int(m.group(2) or 0)
            if d["depth"] != want:
                self.fail("depth is %d, want %d" % (d["depth"], want))
            return
        m = re.match(r"focus (.*)$", s)
        if m:
            return self.check_focus(m.group(1))
        m = re.match(r'column "([^"]*)" (cards|starts) (.*)$', s)
        if m:
            got = self.column_cards(m.group(1))
            want = [] if m.group(3) == "none" else [x.strip() for x in m.group(3).split(",")]
            ok = got == want if m.group(2) == "cards" else got[:len(want)] == want
            if not ok:
                self.fail("column %s has %s" % (m.group(1), got))
            return
        m = re.match(r'text "(.*)" is shown$', s)
        if m:
            if m.group(1) not in self.texts():
                self.fail("text %r is not shown" % m.group(1))
            return
        m = re.match(r'no text "(.*)"$', s)
        if m:
            if m.group(1) in self.texts():
                self.fail("text %r is shown" % m.group(1))
            return
        m = re.match(r'notice "(.*)" with (no action|"(.*)")$', s)
        if m:
            n = d["notice"]
            want_action = None if m.group(2) == "no action" else m.group(3)
            if n is None or n["text"] != m.group(1) or n["action"] != want_action:
                self.fail("notice is %r" % n)
            return
        if s == "no notice":
            if d["notice"] is not None:
                self.fail("notice is %r" % d["notice"])
            return
        m = re.match(r'card (\S+) (has mark "(.*)"|has no mark|is selected|is not selected|is in view)$', s)
        if m:
            card = next((c for c in d["cards"] if c["id"] == m.group(1)), None)
            what = m.group(2)
            if what == "is not selected":
                if card is not None and card["selected"]:
                    self.fail("card is selected")
                return
            if card is None:
                self.fail("card %s is not shown" % m.group(1))
            if what.startswith("has mark"):
                ok = m.group(3) in card["marks"]
            elif what == "has no mark":
                ok = card["marks"] == []
            elif what == "is selected":
                ok = card["selected"]
            else:
                ok = card["inView"]
            if not ok:
                self.fail("card is %r" % card)
            return
        m = re.match(r'(action|toggle|choice|field|link) "([^"]*)"(?: in "([^"]*)")? is (.*)$', s)
        if m:
            role, name, group, state = m.groups()
            p = self.find(role, name, group)
            if state == "absent":
                if p is not None:
                    self.fail("%s %s is shown" % (role, name))
                return
            if p is None:
                self.fail("%s %s is absent" % (role, name))
            if state == "shown":
                return
            if state == "disabled":
                ok = p["disabled"]
            elif state == "enabled":
                ok = not p["disabled"]
            else:
                ok = p["state"] == state
            if not ok:
                self.fail("%s %s is %r" % (role, name, p))
            return
        m = re.match(r'field "([^"]*)" has text "(.*)"$', s)
        if m:
            p = self.find("field", m.group(1))
            if p is None or p["text"] != m.group(2):
                self.fail("field is %r" % p)
            return
        if s in ("scroll is top", "scroll is not top"):
            if d["scrollTop"] != (s == "scroll is top"):
                self.fail("scrollTop is %r" % d["scrollTop"])
            return
        m = re.match(r"requests (\S+) (\d+)$", s)
        if m:
            n = sum(1 for r in d["requests"] if r["op"] == m.group(1))
            if n != int(m.group(2)):
                self.fail("requests %s: %d" % (m.group(1), n))
            return
        m = re.match(r'announcement "(.*)"$', s)
        if m:
            if not d["announcements"] or d["announcements"][-1] != m.group(1):
                self.fail("announcements %r" % d["announcements"][-3:])
            return
        raise StepError("unknown check")

    def check_focus(self, s):
        p = self.focused()
        if s == "none":
            if p is not None:
                self.fail("focus is %r" % p)
            return
        if s == "place title":
            if p is None or p["role"] != "place title":
                self.fail("focus is %r" % p)
            return
        m = re.match(r"card (\S+)$", s)
        if m:
            if p is None or p["role"] != "card" or p["name"].split(" ")[0] != m.group(1):
                self.fail("focus is %r" % p)
            return
        m = re.match(r'(\S+) "(.*)"$', s)
        if m:
            if p is None or p["role"] != m.group(1) or p["name"] != m.group(2):
                self.fail("focus is %r" % p)
            return
        raise StepError("unknown focus check")
