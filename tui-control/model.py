"""Slate application logic, with no terminal code.

App holds the history, the session (clock, service double, loaded data) and
the UI state. Intents are methods; handle_key() maps the keys of TRM-8 (as key
names, see keys.py) to intents. semantic() gives the face of the current state
as a list of items in face order; view.py lays them out on a grid.
"""
import datetime

from address import board_address, parse, person_key
from clock import Clock
from service import ServiceDouble, load_fixture

LABEL_LIMIT = 3
NOTICE_MS = 8000
SLOW_MS = 1000
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

FIELD_KEYS = ("filter", "titlefield", "descfield", "commentfield", "prompt")
STOP_ROLES = ("link", "up-link", "action", "toggle", "choice", "field", "card")


def fmt_time(iso):
    d = datetime.datetime.strptime(iso, "%Y-%m-%dT%H:%M:%SZ")
    return "%d %s %d, %02d:%02d" % (d.day, MONTHS[d.month - 1], d.year, d.hour, d.minute)


def plural(n, word):
    return "%d %s%s" % (n, word, "" if n == 1 else "s")


def comment_count(n):
    return plural(n, "comment")


class Entry:
    def __init__(self, address, from_board=False):
        self.address = address
        self.scroll = 0
        self.from_board = from_board


class Item(dict):
    """One part of the face: key, role, name, group, state, disabled, text,
    stop, slot and extra layout data."""
    __getattr__ = dict.get


class App:
    def __init__(self, profile="default", address="board", fixture=None, clock_factory=Clock):
        self.fixture = fixture or load_fixture()
        data, _ = self.fixture
        self.static_labels = list(data["labels"])
        self.static_people = [person_key(p["name"]) for p in data["people"]]
        self.profile = profile
        self.clock_factory = clock_factory
        self.history = [Entry(self.canon(address))]
        self.pos = 0
        self.quit_requested = False
        self.start_session()
        self.enter_place(focus_title=False)

    # ------------------------------------------------------------------ session
    def start_session(self):
        self.clock = self.clock_factory()
        self.service = ServiceDouble(self.clock, self.profile, self.fixture)
        self.announcements = []
        self.meta = None
        self.board_status = "idle"  # idle | loading | failed | ready
        self.columns = {}  # id -> {status, slow, token, cards}
        self.cards = {}  # id -> card data with "column"
        self.saving = {}  # card id -> number of move saves without reply
        self.selection = []
        self.q = ""
        self.flabels = []
        self.fwho = []
        self.draft = ""
        self.carry = None
        self.notice = None
        self.undo_record = None
        self.cv = None
        self.place = None
        self.focus = None
        self.prompt = None
        self.prompt_return = None
        self.last_card = None
        self.left_card = None
        self.visit = 0
        self.focus_title_pending = False
        self._last_order = []

    @property
    def entry(self):
        return self.history[self.pos]

    @property
    def scroll(self):
        return self.entry.scroll

    @scroll.setter
    def scroll(self, v):
        self.entry.scroll = v

    def canon(self, text):
        return parse(text, self.static_labels, self.static_people).text

    def announce(self, text):
        self.announcements.append(text)

    def call(self, op, args, cb):
        self.service.call(op, args, cb)

    # ------------------------------------------------------------- data helpers
    def label_list(self):
        return self.meta["labels"] if self.meta else self.static_labels

    def people(self):
        return self.meta["people"] if self.meta else []

    def person_name(self, pid):
        for p in self.people():
            if p["id"] == pid:
                return p["name"]
        return pid or "Unassigned"

    def column_ids(self):
        return [c["id"] for c in self.meta["columns"]] if self.meta else []

    def column_meta(self, cid):
        for c in self.meta["columns"]:
            if c["id"] == cid:
                return c
        return None

    def column_name(self, cid):
        c = self.column_meta(cid) if self.meta else None
        return c["name"] if c else cid

    def col_cards(self, cid):
        col = self.columns.get(cid)
        return col["cards"] if col else []

    def filter_on(self):
        return bool(self.q or self.flabels or self.fwho)

    def matches(self, cid):
        c = self.cards[cid]
        if self.q:
            hay = (cid + " " + c["title"]).lower()
            if not all(w in hay for w in self.q.lower().split()):
                return False
        if self.flabels and not any(l in c["labels"] for l in self.flabels):
            return False
        if self.fwho:
            who = c["assignee"] or "none"
            if who not in self.fwho:
                return False
        return True

    def visible(self, cid):
        """Visible cards of a ready column, from the top."""
        col = self.columns.get(cid)
        if not col or col["status"] != "ready":
            return []
        return [x for x in col["cards"] if self.matches(x) or (self.carry and self.carry["card"] == x)]

    def board_state(self):
        if self.board_status == "ready":
            return "ready"
        if self.board_status == "failed":
            return "failed"
        return "loading"

    def column_state(self, cid):
        col = self.columns.get(cid)
        if not col or col["status"] == "loading":
            return "loading.slow" if col and col["slow"] else "loading.fresh"
        if col["status"] == "failed":
            return "failed"
        if not col["cards"]:
            return "empty"
        if not self.visible(cid):
            return "nomatch"
        return "cards"

    def all_answered(self):
        ids = self.column_ids()
        return bool(ids) and all(self.columns.get(c, {}).get("status") in ("ready", "failed") for c in ids)

    def loaded_cards(self):
        return [x for c in self.column_ids() for x in self.col_cards(c)
                if self.columns.get(c, {}).get("status") == "ready"]

    def visible_board(self):
        return [x for c in self.column_ids() for x in self.visible(c)]

    def count_line(self):
        total = len(self.loaded_cards())
        if self.filter_on():
            return "Showing %d of %s" % (len(self.visible_board()), plural(total, "card"))
        return plural(total, "card")

    def column_count(self, cid):
        n = len(self.col_cards(cid))
        if self.filter_on():
            return "%d of %d" % (len(self.visible(cid)), n)
        return str(n)

    def focus_stop(self):
        vis = self.visible_board()
        if self.last_card in vis:
            return self.last_card
        return vis[0] if vis else None

    def card_of_focus(self):
        if self.focus and self.focus.startswith("card:"):
            return self.focus[5:]
        return None

    def set_focus(self, key):
        self.focus = key
        if key and key.startswith("card:"):
            self.last_card = key[5:]

    # -------------------------------------------------------------- navigation
    def leave_place(self):
        if self.carry:
            self.cancel_carry(quiet=True)
        self.left_card = self.cv["id"] if (self.place == "card" and self.cv) else None
        self.prompt = None

    def enter_place(self, focus_title=True):
        self.visit += 1
        self.focus = None
        self.cv = None
        addr = parse(self.entry.address, self.static_labels, self.static_people)
        if addr.kind == "board":
            self.place = "board"
            self.q, self.flabels, self.fwho = addr.q, list(addr.labels), list(addr.who)
            self.draft = self.q
            self.selection = [c for c in self.selection if c in self.cards and self.matches(c)]
            if self.board_status in ("idle", "failed"):
                self.load_board()
            elif self.board_status == "ready":
                self.load_missing_columns()
        elif addr.kind == "card":
            self.place = "card"
            self.cv = self.new_card_view(addr.card)
            self.load_card()
        else:
            self.place = "missing_page"
        self.focus_title_pending = focus_title
        if self.place == "board" and self.left_card and self.left_card in self.visible_board():
            self.set_focus("card:" + self.left_card)
            self.focus_title_pending = False
        self.try_focus_title()
        self._last_order = self.keys()

    def try_focus_title(self):
        if self.focus_title_pending and self.focus is None and self.title_text() is not None:
            self.focus = "title"
            self.focus_title_pending = False

    def navigate(self, text, from_board=False):
        canon = self.canon(text)
        self.leave_place()
        if canon == self.entry.address:
            self.entry.from_board = from_board
            self.entry.scroll = 0
        else:
            del self.history[self.pos + 1:]
            self.history.append(Entry(canon, from_board))
            self.pos += 1
        self.enter_place()

    def open_home(self):
        self.navigate("board")

    def open_board_link(self):
        self.navigate("board")

    def go_back(self):
        if self.pos > 0:
            self.leave_place()
            self.pos -= 1
            self.enter_place()

    def go_forward(self):
        if self.pos < len(self.history) - 1:
            self.leave_place()
            self.pos += 1
            self.enter_place()

    def go_up(self):
        if self.place != "card":
            return
        if self.entry.from_board and self.pos > 0 and \
                parse(self.history[self.pos - 1].address, self.static_labels, self.static_people).kind == "board":
            self.go_back()
        else:
            self.navigate("board")

    def open_card(self, cid):
        self.navigate("card/" + cid, from_board=True)

    def reload(self):
        self.start_session()
        self.enter_place(focus_title=False)

    def open_prompt(self):
        if self.prompt is None:
            self.prompt = ""
            self.prompt_return = self.focus
            self.focus = "prompt"

    def close_prompt(self):
        self.prompt = None
        self.focus = self.prompt_return
        self.prompt_return = None

    def commit_prompt(self):
        text = self.prompt
        self.prompt = None
        self.prompt_return = None
        self.navigate(text)

    def retry_place(self):
        if self.place == "board" and self.board_status == "failed":
            self.load_board()
        elif self.place == "card" and self.cv and self.cv["status"] == "failed":
            self.load_card()

    # ------------------------------------------------------------------ board
    def load_board(self):
        self.board_status = "loading"

        def done(reply):
            if reply["ok"]:
                self.meta = reply["data"]
                self.board_status = "ready"
                if self.place == "board":
                    self.load_missing_columns()
                    self.try_focus_title()
                elif self.place == "card":
                    self.card_maybe_ready()
            else:
                self.board_status = "failed"
                if self.place == "board":
                    self.announce("Couldn't load the board.")
                elif self.place == "card" and self.cv and self.cv["status"] == "loading":
                    self.card_failed()
        self.call("loadBoard", {}, done)

    def load_missing_columns(self):
        for cid in self.column_ids():
            if cid not in self.columns:
                self.load_column(cid)

    def load_column(self, cid):
        token = object()
        old = self.columns.get(cid, {}).get("cards", [])
        self.columns[cid] = {"status": "loading", "slow": False, "token": token, "cards": old}

        def slow():
            col = self.columns.get(cid)
            if col and col["token"] is token and col["status"] == "loading":
                col["slow"] = True
        self.clock.schedule(SLOW_MS, slow)

        def done(reply):
            col = self.columns.get(cid)
            if not col or col["token"] is not token:
                return
            if reply["ok"]:
                ids = []
                for c in reply["data"]["cards"]:
                    card = dict(c)
                    card["column"] = cid
                    self.cards[card["id"]] = card
                    ids.append(card["id"])
                col["cards"] = ids
                col["status"] = "ready"
            else:
                col["status"] = "failed"
                if self.place == "board":
                    self.announce("Couldn't load %s." % self.column_name(cid))
        self.call("loadColumn", {"column": cid}, done)

    def retry_column(self, cid):
        if self.columns.get(cid, {}).get("status") == "failed":
            self.load_column(cid)

    # filter -------------------------------------------------------------
    def ask_filter(self):
        if self.place == "board" and self.board_state() == "ready":
            self.set_focus("filter")

    def apply_filter(self, announce=True):
        self.q = " ".join(self.draft.split())
        self.entry.address = board_address(self.q, self.flabels, self.fwho, self.label_list(),
                                           [p["id"] for p in self.people()] or self.static_people)
        self.entry.scroll = 0
        self.selection = [c for c in self.selection if self.matches(c)]
        if announce:
            self.announce(self.count_line())

    def change_filter_text(self, text):
        self.draft = text

    def commit_filter(self):
        self.apply_filter()

    def toggle_label_filter(self, label):
        if label in self.flabels:
            self.flabels.remove(label)
        else:
            self.flabels.append(label)
        self.apply_filter()

    def toggle_assignee_filter(self, who):
        if who in self.fwho:
            self.fwho.remove(who)
        else:
            self.fwho.append(who)
        self.apply_filter()

    def clear_filters(self):
        self.draft = ""
        self.flabels = []
        self.fwho = []
        self.apply_filter()
        if self.focus in ("clear", "showall"):
            self.set_focus("filter")

    # selection ------------------------------------------------------------
    def toggle_select(self, cid):
        if cid in self.selection:
            self.selection.remove(cid)
            self.announce("%s not selected. %d selected." % (cid, len(self.selection)))
        else:
            self.selection.append(cid)
            self.announce("%s selected. %d selected." % (cid, len(self.selection)))

    def select_column(self, col):
        vis = self.visible(col)
        if not vis:
            return
        if all(c in self.selection for c in vis):
            self.selection = [c for c in self.selection if c not in vis]
        else:
            self.selection += [c for c in vis if c not in self.selection]
        self.announce("%d selected." % len(self.selection))

    def clear_selection(self):
        was_bar = self.focus and (self.focus.startswith("sel") and not self.focus.startswith("selectall"))
        self.selection = []
        self.announce("Selection cleared.")
        if was_bar:
            stop = self.focus_stop()
            self.set_focus("card:" + stop if stop else "filter")

    def selected_in_board_order(self):
        return [c for c in self.loaded_cards() if c in self.selection]

    def label_state(self, label):
        sel = [c for c in self.selection if c in self.cards]
        n = sum(1 for c in sel if label in self.cards[c]["labels"])
        if sel and n == len(sel):
            return "on"
        return "mixed" if n else "off"

    # moves ----------------------------------------------------------------
    def position_of(self, cid):
        col = self.cards[cid]["column"]
        return col, self.col_cards(col).index(cid)

    def local_move(self, cid, col, index):
        src = self.cards[cid]["column"]
        if cid in self.col_cards(src):
            self.columns[src]["cards"].remove(cid)
        target = self.columns[col]["cards"]
        target.insert(max(0, min(index, len(target))), cid)
        self.cards[cid]["column"] = col

    def room(self, col, incoming):
        lim = self.column_meta(col)["limit"]
        if lim is None:
            return True
        n = len([c for c in self.col_cards(col)]) + len([c for c in incoming if self.cards[c]["column"] != col])
        return n <= lim

    def refuse_limit(self, col):
        lim = self.column_meta(col)["limit"]
        self.raise_notice("error", "%s has a limit of %d cards." % (self.column_name(col), lim))

    def send_moves(self, moves, kind="move"):
        """moves: list of dict card, col, index, from_col, from_index. The local
        state already shows the moves."""
        for m in moves:
            self.saving[m["card"]] = self.saving.get(m["card"], 0) + 1
        args = {"moves": [{"card": m["card"], "column": m["col"], "index": m["index"]} for m in moves]}

        def done(reply):
            if reply["ok"]:
                results = reply["data"]["results"]
            else:
                results = [{"card": m["card"], "ok": False} for m in moves]
            ok, failed = [], []
            for m, r in zip(moves, results):
                self.saving[m["card"]] -= 1
                if self.saving[m["card"]] <= 0:
                    del self.saving[m["card"]]
                (ok if r["ok"] else failed).append(m)
            for m in reversed(failed):
                c = self.cards.get(m["card"])
                if c and c["column"] == m["col"] and m["from_col"] in self.columns:
                    self.local_move(m["card"], m["from_col"], m["from_index"])
            if ok and kind == "move":
                self.undo_record = {"kind": "move", "moves": ok}
            if failed:
                text = ("Couldn't move %s." % failed[0]["card"]) if len(failed) == 1 \
                    else "Couldn't move %d cards." % len(failed)
                retry = [dict(m) for m in failed]
                self.raise_notice("error", text, "Try again", lambda: self.retry_moves(retry, kind))
            elif kind == "undo":
                text = ("Moved %s back to %s." % (ok[0]["card"], self.column_name(ok[0]["col"]))) \
                    if len(ok) == 1 else "Moved %d cards back." % len(ok)
                self.raise_notice("info", text)
            else:
                cols = {m["col"] for m in ok}
                col = self.column_name(ok[0]["col"])
                if len(ok) == 1:
                    text = "Moved %s to %s." % (ok[0]["card"], col)
                elif len(cols) == 1:
                    text = "Moved %d cards to %s." % (len(ok), col)
                else:
                    text = "Moved %d cards." % len(ok)
                self.raise_notice("info", text, "Undo", self.undo)
        self.call("moveCards", args, done)

    def retry_moves(self, moves, kind):
        todo = []
        for m in moves:
            if m["card"] not in self.cards or m["col"] not in self.columns:
                continue
            fc, fi = self.position_of(m["card"])
            todo.append(dict(m, from_col=fc, from_index=fi))
        if not todo:
            return
        for col in {m["col"] for m in todo}:
            if not self.room(col, [m["card"] for m in todo if m["col"] == col]):
                self.refuse_limit(col)
                return
        for m in todo:
            self.local_move(m["card"], m["col"], m["index"])
        self.send_moves(todo, kind)

    def bulk_move(self, col):
        cards = [c for c in self.selected_in_board_order() if self.cards[c]["column"] != col]
        if not cards:
            return
        if not self.room(col, cards):
            self.refuse_limit(col)
            return
        moves = []
        for c in cards:
            fc, fi = self.position_of(c)
            idx = len(self.col_cards(col))
            moves.append({"card": c, "col": col, "index": idx, "from_col": fc, "from_index": fi})
            self.local_move(c, col, idx)
        was_bar = self.focus and self.focus.startswith("sel") and not self.focus.startswith("selectall")
        self.selection = []
        if was_bar:
            self.set_focus("card:" + cards[0] if cards[0] in self.visible_board() else "filter")
        self.send_moves(moves)

    def bulk_label(self, label):
        sel = [c for c in self.selected_in_board_order()]
        if not sel:
            return
        state = self.label_state(label)
        changes, old, skipped = [], [], 0
        for c in sel:
            labels = list(self.cards[c]["labels"])
            if state == "on":
                new = [l for l in labels if l != label]
            else:
                if label in labels:
                    continue
                if len(labels) >= LABEL_LIMIT:
                    skipped += 1
                    continue
                new = [l for l in self.label_list() if l in labels or l == label]
            changes.append((c, new))
            old.append((c, labels))
        if not changes:
            self.raise_notice("error", "Label limit reached (%d)." % LABEL_LIMIT)
            return
        for c, new in changes:
            self.cards[c]["labels"] = new
        n = len(changes)
        what = changes[0][0] if n == 1 else "%d cards" % n
        text = ("Removed %s from %s." if state == "on" else "Added %s to %s.") % (label, what)
        if skipped:
            text += " %s at the label limit." % ("1 card is" if skipped == 1 else "%d cards are" % skipped)
        self.save_labels(changes, old, text, undoable=True)

    def save_labels(self, changes, old, text, undoable):
        args = {"changes": [{"card": c, "labels": list(l)} for c, l in changes]}

        def done(reply):
            if reply["ok"]:
                if undoable:
                    self.undo_record = {"kind": "labels", "changes": old}
                    self.raise_notice("info", text, "Undo", self.undo)
                elif text:
                    self.raise_notice("info", text)
            else:
                for (c, new), (_, prev) in zip(changes, old):
                    if c in self.cards and self.cards[c]["labels"] == new:
                        self.cards[c]["labels"] = prev
                self.raise_notice("error", "Couldn't save the labels.", "Try again",
                                  lambda: self.retry_labels(changes, old, text, undoable))
        self.call("saveLabels", args, done)

    def retry_labels(self, changes, old, text, undoable):
        for c, new in changes:
            if c in self.cards:
                self.cards[c]["labels"] = list(new)
        self.save_labels(changes, old, text, undoable)

    def undo(self):
        rec = self.undo_record
        if not rec:
            return
        self.undo_record = None
        if self.notice and self.notice.get("action") == "Undo":
            self.drop_notice()
        if rec["kind"] == "move":
            todo = []
            for m in reversed(rec["moves"]):
                if m["card"] in self.cards and m["from_col"] in self.columns:
                    fc, fi = self.position_of(m["card"])
                    todo.append({"card": m["card"], "col": m["from_col"], "index": m["from_index"],
                                 "from_col": fc, "from_index": fi})
            for col in {m["col"] for m in todo}:
                if not self.room(col, [m["card"] for m in todo if m["col"] == col]):
                    self.refuse_limit(col)
                    return
            for m in todo:
                self.local_move(m["card"], m["col"], m["index"])
            if todo:
                self.send_moves(todo, "undo")
        else:
            changes = [(c, l) for c, l in rec["changes"] if c in self.cards]
            cur = [(c, list(self.cards[c]["labels"])) for c, _ in changes]
            for c, l in changes:
                self.cards[c]["labels"] = list(l)
            n = len(changes)
            text = "Restored the labels of %s." % (changes[0][0] if n == 1 else "%d cards" % n)
            self.save_labels(changes, cur, text, undoable=False)

    # carry ----------------------------------------------------------------
    def carry_position_text(self, cid):
        col = self.cards[cid]["column"]
        vis = self.visible(col)
        return "%s, position %d of %d." % (self.column_name(col), vis.index(cid) + 1, len(vis))

    def pick_up(self, cid):
        if self.saving.get(cid):
            self.announce("%s is still saving." % cid)
            return
        fc, fi = self.position_of(cid)
        self.carry = {"card": cid, "from_col": fc, "from_index": fi}
        self.announce("Picked up %s. %s" % (cid, self.carry_position_text(cid)))

    def carry_step(self, direction):
        cid = self.carry["card"]
        col = self.cards[cid]["column"]
        vis = self.visible(col)
        i = vis.index(cid)
        full = self.col_cards(col)
        if direction in ("Up", "Down"):
            j = i - 1 if direction == "Up" else i + 1
            if j < 0 or j >= len(vis):
                self.announce("%s is at the %s of %s." % (cid, "top" if j < 0 else "bottom",
                                                         self.column_name(col)))
                return
            other = vis[j]
            full.remove(cid)
            k = full.index(other)
            full.insert(k if direction == "Up" else k + 1, cid)
        else:
            ids = self.column_ids()
            ci = ids.index(col)
            step = -1 if direction == "Left" else 1
            ci += step
            target = None
            while 0 <= ci < len(ids):
                t = ids[ci]
                if self.columns.get(t, {}).get("status") == "ready" and self.room(t, [cid]):
                    target = t
                    break
                ci += step
            if target is None:
                self.announce("%s can't go further %s." % (cid, "left" if step < 0 else "right"))
                return
            tvis = [x for x in self.visible(target)]
            if i < len(tvis):
                idx = self.col_cards(target).index(tvis[i])
            elif tvis:
                idx = self.col_cards(target).index(tvis[-1]) + 1
            else:
                idx = len(self.col_cards(target))
            self.local_move(cid, target, idx)
        self.announce(self.carry_position_text(cid))

    def drop(self):
        c = self.carry
        self.carry = None
        cid = c["card"]
        col, idx = self.position_of(cid)
        if col == c["from_col"] and idx == c["from_index"]:
            self.announce("%s was not moved." % cid)
            return
        self.announce("Dropped %s. %s" % (cid, self.carry_position_text(cid)))
        self.send_moves([{"card": cid, "col": col, "index": idx,
                          "from_col": c["from_col"], "from_index": c["from_index"]}])

    def cancel_carry(self, quiet=False):
        c = self.carry
        self.carry = None
        if c["card"] in self.cards:
            self.local_move(c["card"], c["from_col"], c["from_index"])
            if not quiet:
                self.announce("Move cancelled. %s is back in %s." % (c["card"], self.column_name(c["from_col"])))

    # focus between cards ----------------------------------------------------
    def move_focus(self, key):
        cid = self.card_of_focus()
        col = self.cards[cid]["column"]
        vis = self.visible(col)
        i = vis.index(cid)
        target = None
        if key == "Up" and i > 0:
            target = vis[i - 1]
        elif key == "Down" and i < len(vis) - 1:
            target = vis[i + 1]
        elif key in ("Left", "Right"):
            ids = self.column_ids()
            ci = ids.index(col)
            step = -1 if key == "Left" else 1
            ci += step
            while 0 <= ci < len(ids):
                tv = self.visible(ids[ci])
                if tv:
                    target = tv[min(i, len(tv) - 1)]
                    break
                ci += step
        elif key in ("Home", "End"):
            allv = self.visible_board()
            target = allv[0] if key == "Home" else allv[-1]
        if target:
            self.set_focus("card:" + target)

    # delete -----------------------------------------------------------------
    def delete_card(self, cid):
        if cid not in self.cards:
            return
        col, idx = self.position_of(cid) if cid in self.col_cards(self.cards[cid]["column"]) else (None, 0)
        snapshot = dict(self.cards[cid])
        if self.focus == "card:" + cid and col:
            vis = self.visible(col)
            i = vis.index(cid)
            rest = vis[i + 1:] + list(reversed(vis[:i]))
            if rest:
                self.set_focus("card:" + rest[0])
            else:
                others = [x for x in self.visible_board() if x != cid]
                self.focus = ("card:" + others[0]) if others else None
        if col:
            self.columns[col]["cards"].remove(cid)
        del self.cards[cid]
        if cid in self.selection:
            self.selection.remove(cid)
        if self.last_card == cid:
            self.last_card = None

        def done(reply):
            if reply["ok"]:
                self.raise_notice("info", "Deleted %s." % cid)
            else:
                self.cards[cid] = snapshot
                if col and col in self.columns:
                    lst = self.columns[col]["cards"]
                    lst.insert(min(idx, len(lst)), cid)
                    snapshot["column"] = col
                self.raise_notice("error", "Couldn't delete %s." % cid, "Try again",
                                  lambda: self.delete_card(cid))
        self.call("deleteCard", {"card": cid}, done)

    def delete_card_place(self):
        cv = self.cv
        cid = cv["id"]
        if cid not in self.cards:
            self.cards[cid] = dict(cv["card"])
        self.delete_card(cid)
        self.leave_place()
        self.left_card = None
        if self.entry.from_board and self.pos > 0 and \
                parse(self.history[self.pos - 1].address, self.static_labels, self.static_people).kind == "board":
            del self.history[self.pos:]
            self.pos -= 1
        else:
            self.entry.address = "board"
            self.entry.from_board = False
            self.entry.scroll = 0
        self.enter_place()

    # ------------------------------------------------------------------ notice
    def raise_notice(self, kind, text, action=None, on_action=None):
        self.drop_notice()
        n = {"kind": kind, "text": text, "action": action, "on_action": on_action, "timer": None}
        if kind == "info":
            def expire():
                if self.notice is n:
                    self.notice = None
            n["timer"] = self.clock.schedule(NOTICE_MS, expire)
        self.notice = n
        self.announce(text)

    def drop_notice(self):
        if self.notice:
            self.clock.cancel(self.notice["timer"])
            self.notice = None

    def notice_action(self):
        n = self.notice
        if n and n["on_action"]:
            self.drop_notice()
            n["on_action"]()

    def dismiss_notice(self):
        self.drop_notice()

    def dismiss(self):
        """DIS-T1 (rows guessed; .1 cancel carry, .6 cancel description, .8 go up)."""
        cv = self.cv
        if self.carry:
            self.cancel_carry()
        elif self.place == "card" and cv and cv["status"] == "ready" and cv["title_editing"]:
            self.cancel_title()
        elif self.place == "card" and cv and cv["status"] == "ready" and cv["desc_editing"]:
            self.cancel_description()
        elif self.place == "board" and self.selection:
            self.clear_selection()
        elif self.notice:
            self.dismiss_notice()
        elif self.place == "card":
            self.go_up()

    # -------------------------------------------------------------------- card
    def new_card_view(self, cid):
        return {"id": cid, "status": "loading", "card": None, "visit": self.visit,
                "title_editing": False, "title_draft": "", "title_msg": None, "title_saving": 0,
                "labels_saving": 0, "assignee_saving": 0,
                "desc_editing": False, "desc_draft": "", "desc_saving": 0,
                "comments_status": "loading", "comments": [], "comment_draft": "",
                "comment_sending": None, "comment_msg": None}

    def load_card(self):
        cv = self.cv
        cv["status"] = "loading"
        cid = cv["id"]

        def card_done(reply):
            if reply["ok"] and reply["data"]["card"] is not None and cid in self.cards:
                fresh = reply["data"]["card"]
                self.cards[cid].update({k: fresh[k] for k in
                                        ("title", "description", "labels", "assignee", "comments")})
            if self.cv is not cv:
                return
            if not reply["ok"]:
                self.card_failed()
            elif reply["data"]["card"] is None:
                self.place = "missing_card"
                self.try_focus_title()
            else:
                cv["card"] = dict(reply["data"]["card"])
                self.card_maybe_ready()
        self.call("loadCard", {"card": cid}, card_done)
        if cv["comments_status"] in ("loading", "failed"):
            self.load_comments()
        if self.meta is None and self.board_status != "loading":
            self.load_board()

    def card_failed(self):
        self.cv["status"] = "failed"
        self.announce("Couldn't load this card.")
        self.try_focus_title()

    def card_maybe_ready(self):
        cv = self.cv
        if cv and cv["card"] is not None and self.meta is not None and cv["status"] != "ready":
            cv["status"] = "ready"
            self.try_focus_title()
            if cv["comments_status"] == "failed":
                self.announce("Couldn't load comments.")
        elif cv and cv["card"] is not None and self.board_status == "failed":
            self.card_failed()

    def load_comments(self):
        cv = self.cv
        cv["comments_status"] = "loading"

        def done(reply):
            if self.cv is not cv:
                return
            if reply["ok"]:
                cv["comments"] = list(reply["data"]["comments"])
                cv["comments_status"] = "some" if cv["comments"] else "none"
            else:
                cv["comments_status"] = "failed"
                if cv["status"] == "ready":
                    self.announce("Couldn't load comments.")
        self.call("loadComments", {"card": cv["id"]}, done)

    def retry_comments(self):
        if self.cv and self.cv["comments_status"] == "failed":
            self.load_comments()

    def update_cache(self, cid, **fields):
        if cid in self.cards:
            self.cards[cid].update(fields)

    def labels_full(self):
        return len(self.cv["card"]["labels"]) >= LABEL_LIMIT

    # title
    def edit_title(self):
        cv = self.cv
        cv["title_editing"] = True
        cv["title_draft"] = cv["card"]["title"]
        cv["title_msg"] = None
        self.set_focus("titlefield")

    def change_title_text(self, text):
        self.cv["title_draft"] = text

    def commit_title(self, move_focus=True):
        cv = self.cv
        t = " ".join(cv["title_draft"].split())
        if not t:
            cv["title_msg"] = "Title can't be empty."
            self.announce(cv["title_msg"])
            return False
        cv["title_editing"] = False
        cv["title_msg"] = None
        if move_focus:
            self.set_focus("edittitle")
        old = cv["card"]["title"]
        if t == old:
            return True
        self.save_title(cv, t, old)
        return True

    def save_title(self, cv, t, old):
        cid = cv["id"]
        cv["card"]["title"] = t
        self.update_cache(cid, title=t)
        cv["title_saving"] += 1

        def done(reply):
            cv["title_saving"] -= 1
            if reply["ok"]:
                return
            if cv["card"]["title"] == t:
                cv["card"]["title"] = old
                self.update_cache(cid, title=old)
            if self.cv is cv:
                cv["title_editing"] = True
                cv["title_draft"] = t
                cv["title_msg"] = "Couldn't save the title."
                self.announce(cv["title_msg"])
                if self.focus in (None, "edittitle", "title"):
                    self.set_focus("titlefield")
        self.call("saveTitle", {"card": cid, "title": t}, done)

    def cancel_title(self):
        cv = self.cv
        cv["title_editing"] = False
        cv["title_msg"] = None
        self.set_focus("edittitle")

    def leave_title(self, backward=False):
        cv = self.cv
        t = " ".join(cv["title_draft"].split())
        if t and t != cv["card"]["title"]:
            self.commit_title(move_focus=False)
        cv["title_editing"] = False
        cv["title_msg"] = None
        self.focus = "edittitle"
        self.tab(backward)

    # labels and assignee
    def toggle_label(self, label):
        cv = self.cv
        labels = list(cv["card"]["labels"])
        if label in labels:
            new = [l for l in labels if l != label]
        elif len(labels) >= LABEL_LIMIT:
            return
        else:
            new = [l for l in self.label_list() if l in labels or l == label]
        self.save_card_labels(cv, new, labels)

    def save_card_labels(self, cv, new, old):
        cid = cv["id"]
        cv["card"]["labels"] = list(new)
        self.update_cache(cid, labels=list(new))
        cv["labels_saving"] += 1

        def done(reply):
            cv["labels_saving"] -= 1
            if reply["ok"]:
                return
            if cv["card"]["labels"] == new:
                cv["card"]["labels"] = list(old)
                self.update_cache(cid, labels=list(old))
            self.raise_notice("error", "Couldn't save the labels.", "Try again",
                              lambda: self.save_card_labels(cv, new, list(cv["card"]["labels"])))
        self.call("saveLabels", {"changes": [{"card": cid, "labels": list(new)}]}, done)

    def choose_assignee(self, pid):
        cv = self.cv
        old = cv["card"]["assignee"]
        if pid == old:
            return
        self.save_assignee(cv, pid, old)

    def save_assignee(self, cv, pid, old):
        cid = cv["id"]
        cv["card"]["assignee"] = pid
        self.update_cache(cid, assignee=pid)
        cv["assignee_saving"] += 1

        def done(reply):
            cv["assignee_saving"] -= 1
            if reply["ok"]:
                return
            if cv["card"]["assignee"] == pid:
                cv["card"]["assignee"] = old
                self.update_cache(cid, assignee=old)
            self.raise_notice("error", "Couldn't save the assignee.", "Try again",
                              lambda: self.save_assignee(cv, pid, cv["card"]["assignee"]))
        self.call("saveAssignee", {"card": cid, "assignee": pid}, done)

    # description
    def edit_description(self):
        cv = self.cv
        cv["desc_editing"] = True
        cv["desc_draft"] = cv["card"]["description"]
        self.set_focus("descfield")

    def change_description_text(self, text):
        self.cv["desc_draft"] = text

    def commit_description(self):
        cv = self.cv
        text = cv["desc_draft"].strip()
        cv["desc_editing"] = False
        self.set_focus("editdesc")
        old = cv["card"]["description"]
        if text != old:
            self.save_description(cv, text, old)

    def save_description(self, cv, text, old):
        cid = cv["id"]
        cv["card"]["description"] = text
        self.update_cache(cid, description=text)
        cv["desc_saving"] += 1

        def done(reply):
            cv["desc_saving"] -= 1
            if reply["ok"]:
                return
            if cv["card"]["description"] == text:
                cv["card"]["description"] = old
                self.update_cache(cid, description=old)
            self.raise_notice("error", "Couldn't save the description.", "Try again",
                              lambda: self.save_description(cv, text, cv["card"]["description"]))
        self.call("saveDescription", {"card": cid, "description": text}, done)

    def cancel_description(self):
        self.cv["desc_editing"] = False
        self.set_focus("editdesc")

    # comments
    def comment_field_disabled(self):
        cv = self.cv
        return cv["comments_status"] in ("loading", "failed") or cv["comment_sending"] is not None

    def add_comment_disabled(self):
        return self.comment_field_disabled() or not self.cv["comment_draft"].strip()

    def change_comment_text(self, text):
        self.cv["comment_draft"] = text
        self.cv["comment_msg"] = None

    def commit_comment(self):
        cv = self.cv
        if self.add_comment_disabled():
            return
        text = cv["comment_draft"].strip()
        cv["comment_sending"] = {"author": self.meta.get("currentUser") if self.meta else None, "text": text}
        cv["comment_msg"] = None
        cid = cv["id"]

        def done(reply):
            cv["comment_sending"] = None
            if reply["ok"]:
                cv["comments"].append(reply["data"]["comment"])
                cv["comments_status"] = "some"
                cv["comment_draft"] = ""
                if cid in self.cards:
                    self.cards[cid]["comments"] = self.cards[cid].get("comments", 0) + 1
                cv["card"]["comments"] = cv["card"].get("comments", 0) + 1
                if self.cv is cv and self.focus == "addcomment":
                    self.set_focus("commentfield")
            else:
                cv["comment_msg"] = "Couldn't add the comment."
                if self.cv is cv:
                    self.announce(cv["comment_msg"])
        self.call("addComment", {"card": cid, "text": text}, done)

    # ------------------------------------------------------------------- face
    def title_text(self):
        if self.place == "board":
            return "Board"
        if self.place == "missing_page":
            return "Page not found"
        if self.place == "missing_card":
            return "Card not found"
        if self.place == "card":
            st = self.cv["status"]
            if st == "failed":
                return self.cv["id"]
            if st == "ready":
                return self.cv["card"]["title"]
        return None

    def semantic(self):
        items = []

        def add(role, name="", key=None, group=None, state=None, disabled=False, text=None,
                stop=None, slot=None, **extra):
            if stop is None:
                stop = key is not None and role in STOP_ROLES and not disabled
            it = Item(role=role, name=name, key=key, group=group, state=state, disabled=disabled,
                      text=text, stop=stop, slot=slot)
            it.update(extra)
            items.append(it)
            return it

        add("link", "Slate", "home", slot="header")
        if self.place == "board":
            self._semantic_board(add)
        elif self.place == "card":
            self._semantic_card(add)
        else:
            add("place title", self.title_text(), "title", stop=False, slot="title")
            if self.place == "missing_page":
                add("text", "The address may be mistyped or out of date.", slot="body", quiet=True)
            else:
                add("text", "There is no card %s on this board." % self.cv["id"], slot="body", quiet=True)
            add("link", "Go to the board", "boardlink", slot="body")
        if self.prompt is not None:
            add("field", "Address", "prompt", text=self.prompt, slot="notice")
        elif self.notice:
            n = self.notice
            add("notice", n["text"], slot="notice", kind=n["kind"])
            if n["action"]:
                add("action", n["action"], "notice:action", slot="notice")
            if n["kind"] == "error":
                add("action", "Dismiss", "notice:dismiss", slot="notice", quiet=True)
        return items

    def _semantic_board(self, add):
        bs = self.board_state()
        add("place title", "Board", "title", stop=False, slot="title")
        if bs == "loading":
            for i in range(3):
                add("placeholder", "", slot="bph", index=i)
            return
        if bs == "failed":
            add("alert", "Couldn't load the board.", slot="body")
            add("action", "Try again", "retryplace", slot="body")
            return
        add("field", "Filter cards", "filter", text=self.draft, slot="f-field")
        for l in self.label_list():
            add("toggle", l, "flabel:" + l, group="Labels", state="on" if l in self.flabels else "off",
                slot="f-labels")
        for p in self.people():
            add("toggle", p["name"], "fwho:" + p["id"], group="Assignee",
                state="on" if p["id"] in self.fwho else "off", slot="f-who")
        add("toggle", "Unassigned", "fwho:none", group="Assignee",
            state="on" if "none" in self.fwho else "off", slot="f-who")
        if self.filter_on() or self.draft:
            add("action", "Clear filters", "clear", slot="f-last")
        line = self.count_line()
        add("status line", line, text=line, slot="f-last", quiet=True)
        if self.selection:
            t = "%d selected" % len(self.selection)
            add("text", t, text=t, slot="s-move")
            for cid in self.column_ids():
                add("action", self.column_name(cid), "selmove:" + cid, group="Move selected to", slot="s-move")
            for l in self.label_list():
                add("toggle", l, "sellabel:" + l, group="Label selected", state=self.label_state(l),
                    slot="s-label")
            add("action", "Clear selection", "selclear", slot="s-label")
        stop = self.focus_stop()
        for ci, cid in enumerate(self.column_ids()):
            meta = self.column_meta(cid)
            name = meta["name"]
            st = self.column_state(cid)
            add("column", name, slot="column", col=cid, index=ci)
            add("heading", name, slot="c-head", col=cid, index=ci)
            if st in ("empty", "nomatch", "cards"):
                cnt = self.column_count(cid)
                add("text", cnt, text=cnt, slot="c-count", col=cid, index=ci, quiet=True)
            if meta["limit"] is not None:
                t = "Limit %d" % meta["limit"]
                add("text", t, text=t, slot="c-limit", col=cid, index=ci, quiet=True)
            if st == "cards":
                add("action", "Select all in " + name, "selectall:" + cid, slot="c-select", col=cid, index=ci)
            if st.startswith("loading"):
                for k in range(3):
                    add("placeholder", "", slot="c-body", col=cid, index=ci, kind="ph")
                if st == "loading.slow":
                    add("text", "Still loading…", text="Still loading…", slot="c-body", col=cid, index=ci,
                        kind="text", quiet=True)
            elif st == "failed":
                t = "Couldn't load %s." % name
                add("alert", t, slot="c-body", col=cid, index=ci, kind="alert")
                add("action", "Retry " + name, "retrycol:" + cid, slot="c-body", col=cid, index=ci, kind="action")
            elif st == "empty":
                add("text", "No cards", text="No cards", slot="c-body", col=cid, index=ci, kind="text", quiet=True)
            elif st == "nomatch":
                add("text", "No matching cards", text="No matching cards", slot="c-body", col=cid, index=ci,
                    kind="text", quiet=True)
            else:
                for x in self.visible(cid):
                    c = self.cards[x]
                    add("card", "%s %s" % (x, c["title"]), "card:" + x, stop=(x == stop), slot="c-body",
                        col=cid, index=ci, kind="card", card=x)
        if self.all_answered():
            if not self.loaded_cards():
                t = "This board has no cards yet."
                add("text", t, text=t, slot="line")
            elif self.filter_on() and not self.visible_board():
                t = "No cards match these filters."
                add("text", t, text=t, slot="line")
                add("action", "Show all cards", "showall", slot="line")

    def card_marks(self, cid):
        marks = []
        if self.carry and self.carry["card"] == cid:
            marks.append("Moving")
        if self.saving.get(cid):
            marks.append("Saving…")
        return marks

    def _semantic_card(self, add):
        cv = self.cv
        st = cv["status"]
        add("up-link", "← Board", "uplink", slot="uplink")
        if st == "loading":
            add("placeholder", "", slot="cph", index=0)
            add("placeholder", "", slot="cph", index=1)
            return
        if st == "failed":
            add("place title", cv["id"], "title", stop=False, slot="title")
            add("alert", "Couldn't load this card.", slot="body")
            add("action", "Try again", "retryplace", slot="body")
            return
        card = cv["card"]
        t = "%s · %s" % (cv["id"], self.column_name(card["column"]))
        add("text", t, text=t, slot="meta", quiet=True)
        if cv["title_editing"]:
            add("field", "Title", "titlefield", text=cv["title_draft"], slot="title-field")
            if cv["title_msg"]:
                add("alert", cv["title_msg"], slot="title-msg")
        else:
            add("place title", card["title"], "title", stop=False, slot="title")
            add("action", "Edit title", "edittitle", slot="title-actions")
            if cv["title_saving"]:
                add("mark", "Saving…", slot="title-actions")
        full = self.labels_full()
        for l in self.label_list():
            on = l in card["labels"]
            add("toggle", l, "label:" + l, group="Labels", state="on" if on else "off",
                disabled=full and not on, slot="labels")
        if cv["labels_saving"]:
            add("mark", "Saving…", group="Labels", slot="labels")
        if full:
            t = "Label limit reached (%d)" % LABEL_LIMIT
            add("text", t, text=t, group="Labels", slot="labels", quiet=True)
        add("choice", "Unassigned", "assignee:", group="Assignee",
            state="chosen" if card["assignee"] is None else "not chosen", slot="assignee")
        for p in self.people():
            add("choice", p["name"], "assignee:" + p["id"], group="Assignee",
                state="chosen" if card["assignee"] == p["id"] else "not chosen", slot="assignee")
        if cv["assignee_saving"]:
            add("mark", "Saving…", group="Assignee", slot="assignee")
        add("heading", "Description", slot="desc-head")
        if cv["desc_editing"]:
            add("field", "Description", "descfield", text=cv["desc_draft"], slot="desc-field", multiline=True)
            add("action", "Save", "descsave", slot="desc-actions")
            add("action", "Cancel", "desccancel", slot="desc-actions")
        else:
            if card["description"]:
                add("text", card["description"], text=card["description"], slot="desc-text", wrap=True)
            else:
                add("text", "No description", text="No description", slot="desc-text", quiet=True)
            add("action", "Edit description", "editdesc", slot="desc-actions")
            if cv["desc_saving"]:
                add("mark", "Saving…", slot="desc-actions")
        add("heading", "Comments", slot="com-head")
        cs = cv["comments_status"]
        if cs == "loading":
            add("placeholder", "", slot="com-ph")
        elif cs == "failed":
            add("alert", "Couldn't load comments.", slot="com-failed")
            add("action", "Retry", "retrycomments", slot="com-retry")
        elif cs == "none" and not cv["comment_sending"]:
            add("text", "No comments yet", text="No comments yet", slot="com-none", quiet=True)
        else:
            n = len(cv["comments"]) + (1 if cv["comment_sending"] else 0)
            t = comment_count(n)
            add("text", t, text=t, slot="com-count", quiet=True)
            for i, c in enumerate(cv["comments"]):
                m = "%s · %s" % (self.person_name(c["author"]), fmt_time(c["at"]))
                add("text", m, text=m, slot="com-meta", quiet=True, row_id=i)
                add("text", c["text"], text=c["text"], slot="com-text", wrap=True, row_id=i)
            s = cv["comment_sending"]
            if s:
                name = self.person_name(s["author"])
                add("text", name, text=name, slot="com-meta", quiet=True, row_id="s", sending=True)
                add("mark", "Sending…", slot="com-meta", row_id="s")
                add("text", s["text"], text=s["text"], slot="com-text", wrap=True, row_id="s")
        fd = self.comment_field_disabled()
        add("field", "Add a comment", "commentfield", text=cv["comment_draft"], disabled=fd,
            slot="com-field", multiline=True)
        add("action", "Add comment", "addcomment", disabled=self.add_comment_disabled(), slot="com-add")
        if cv["comment_msg"]:
            add("alert", cv["comment_msg"], slot="com-msg")
        add("action", "Delete card", "delete", slot="delete")

    # ------------------------------------------------------------------ focus
    def keys(self):
        return [it.key for it in self.semantic() if it.key]

    def stops(self, items=None):
        items = items if items is not None else self.semantic()
        return [it.key for it in items if it.key and it.stop]

    def tab(self, backward=False):
        items = self.semantic()
        stops = self.stops(items)
        if not stops:
            return
        order = [it.key for it in items if it.key]
        if self.focus in order:
            i = order.index(self.focus)
            seq = order[i + 1:] + order[:i] if not backward else list(reversed(order[:i])) + \
                list(reversed(order[i + 1:]))
            for k in seq:
                if k in stops:
                    self.set_focus(k)
                    return
        else:
            self.set_focus(stops[-1] if backward else stops[0])

    def fix_focus(self):
        """Keep focus on a part that exists (after any change of state)."""
        self.try_focus_title()
        order = self.keys()
        if self.focus is not None and self.focus not in order:
            target = None
            if self.focus in self._last_order:
                i = self._last_order.index(self.focus)
                stops = set(self.stops())
                for k in reversed(self._last_order[:i]):
                    if k in stops:
                        target = k
                        break
            self.focus = target
        self._last_order = order

    # ------------------------------------------------------------------- keys
    def handle_key(self, k):
        self._handle_key(k)
        self.fix_focus()

    def _handle_key(self, k):
        if self.prompt is not None:
            if k == "Enter":
                self.commit_prompt()
            elif k == "Esc":
                self.close_prompt()
            elif k == "Backspace":
                self.prompt = self.prompt[:-1]
            elif k == "C-u":
                self.prompt = ""
            elif len(k) == 1 or k == "Space":
                self.prompt += " " if k == "Space" else k
            elif k in ("C-b", "C-f", "C-r"):
                self.close_prompt()
                self._handle_key(k)
            return
        if k == "C-b":
            return self.go_back()
        if k == "C-f":
            return self.go_forward()
        if k == "C-r":
            return self.reload()
        if k == "C-g":
            if self.carry:
                self.cancel_carry()
            return self.open_prompt()
        if k == "Esc":
            return self.dismiss()
        f = self.focus
        if self.carry:
            if k in ("Up", "Down", "Left", "Right"):
                self.carry_step(k)
            elif k in ("Space", "Enter"):
                self.drop()
            return
        if f in FIELD_KEYS:
            return self._field_key(f, k)
        if k in ("Tab", "S-Tab"):
            return self.tab(k == "S-Tab")
        if k == "C-z":
            return self.undo()
        if k == "/":
            return self.ask_filter()
        cid = self.card_of_focus()
        if cid:
            if k in ("Up", "Down", "Left", "Right", "Home", "End"):
                self.move_focus(k)
            elif k == "Enter":
                self.open_card(cid)
            elif k == "x":
                self.toggle_select(cid)
            elif k == "X":
                self.select_column(self.cards[cid]["column"])
            elif k == "Space":
                self.pick_up(cid)
            elif k in ("Delete", "Backspace"):
                self.delete_card(cid)
            return
        if k in ("Enter", "Space") and f:
            self.activate(f)

    def _field_text(self, f):
        if f == "filter":
            return self.draft
        if f == "titlefield":
            return self.cv["title_draft"]
        if f == "descfield":
            return self.cv["desc_draft"]
        return self.cv["comment_draft"]

    def _set_field_text(self, f, text):
        if f == "filter":
            self.change_filter_text(text)
        elif f == "titlefield":
            self.change_title_text(text)
        elif f == "descfield":
            self.change_description_text(text)
        else:
            self.change_comment_text(text)

    def _field_key(self, f, k):
        if f == "commentfield" and self.comment_field_disabled():
            if k in ("Tab", "S-Tab"):
                self.tab(k == "S-Tab")
            return
        if k in ("Tab", "S-Tab"):
            if f == "titlefield":
                return self.leave_title(k == "S-Tab")
            return self.tab(k == "S-Tab")
        text = self._field_text(f)
        multiline = f in ("descfield", "commentfield")
        if k == "Enter":
            if f == "filter":
                return self.commit_filter()
            if f == "titlefield":
                return self.commit_title()
            return self._set_field_text(f, text + "\n")
        if k == "C-s":
            if f == "descfield":
                return self.commit_description()
            if f == "commentfield":
                return self.commit_comment()
            return
        if k == "Backspace":
            return self._set_field_text(f, text[:-1])
        if k == "C-u":
            return self._set_field_text(f, "")
        if k == "Space":
            return self._set_field_text(f, text + " ")
        if len(k) == 1 and (k.isprintable()):
            return self._set_field_text(f, text + k)
        _ = multiline

    def activate(self, key):
        items = {it.key: it for it in self.semantic() if it.key}
        it = items.get(key)
        if it is None or it.disabled:
            return
        kind, _, arg = key.partition(":")
        if key == "home":
            self.open_home()
        elif key == "retryplace":
            self.retry_place()
        elif kind == "flabel":
            self.toggle_label_filter(arg)
        elif kind == "fwho":
            self.toggle_assignee_filter(arg)
        elif key in ("clear", "showall"):
            self.clear_filters()
        elif kind == "selmove":
            self.bulk_move(arg)
        elif kind == "sellabel":
            self.bulk_label(arg)
        elif key == "selclear":
            self.clear_selection()
        elif kind == "selectall":
            self.select_column(arg)
        elif kind == "retrycol":
            self.retry_column(arg)
        elif key == "notice:action":
            self.notice_action()
        elif key == "notice:dismiss":
            self.dismiss_notice()
        elif key == "uplink":
            self.go_up()
        elif key == "edittitle":
            self.edit_title()
        elif kind == "label":
            self.toggle_label(arg)
        elif kind == "assignee":
            self.choose_assignee(arg or None)
        elif key == "editdesc":
            self.edit_description()
        elif key == "descsave":
            self.commit_description()
        elif key == "desccancel":
            self.cancel_description()
        elif key == "retrycomments":
            self.retry_comments()
        elif key == "addcomment":
            self.commit_comment()
        elif key == "delete":
            self.delete_card_place()
        elif key == "boardlink":
            self.open_board_link()

    # ------------------------------------------------------------------ clock
    def advance(self, ms):
        self.clock.advance(ms)
        self.fix_focus()
