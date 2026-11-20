"""Slate application logic. It knows nothing of the terminal.

Input: keys (names from terminal.decode_keys) through App.key(), and clock
advances through App.advance(). Output: App.layout (a view.Layout with the
character grid and the parts) and App.dump() (TRM-H5).
"""
import datetime
import os
from collections import Counter

import addresses
from addresses import norm_ws
from clock import Clock
from service import Service, load_fixture

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
FIELD_KINDS = ("filter", "title-field", "desc-field", "comment-field")
NOTICE_TIME = 8000
FILTER_DELAY = 250
SLOW_AFTER = 1000
MAX_LABELS = 3
MAX_TITLE = 80


# -- text helpers (DAT-1, DAT-9, DAT-13, DAT-14) -----------------------------
def cards_word(n):
    return "%d card" % n if n == 1 else "%d cards" % n


def of_cards(k, n):
    return "%d of %s" % (k, cards_word(n))


def comments_word(n):
    return "%d comment" % n if n == 1 else "%d comments" % n


def fmt_time(iso):
    t = datetime.datetime.strptime(iso, "%Y-%m-%dT%H:%M:%SZ")
    return "%d %s %d, %02d:%02d" % (t.day, MONTHS[t.month - 1], t.year, t.hour, t.minute)


def is_printable(k):
    return len(k) == 1 and k >= " " and k != "\x7f"


class Card:
    __slots__ = ("id", "title", "description", "labels", "assignee", "comments", "column")

    def __init__(self, d, column):
        self.id = d["id"]
        self.title = d.get("title", "")
        self.description = d.get("description", "") or ""
        self.labels = list(d.get("labels", []))
        self.assignee = d.get("assignee")
        self.comments = int(d.get("comments", 0))
        self.column = column


class Entry:
    __slots__ = ("addr", "scroll", "mark")

    def __init__(self, addr, scroll=0, mark=False):
        self.addr = addr
        self.scroll = scroll
        self.mark = mark


class Notice:
    __slots__ = ("kind", "text", "action", "fn", "timer", "delete_card")

    def __init__(self, kind, text, action=None, fn=None, delete_card=None):
        self.kind = kind
        self.text = text
        self.action = action
        self.fn = fn
        self.timer = None
        self.delete_card = delete_card


class App:
    def __init__(self, fixture_dir, profile="default", address="board", width=120, height=40):
        self.fixture_dir = fixture_dir
        self.profile = profile
        self.fixture = load_fixture(fixture_dir)
        self.width = width
        self.height = height
        self.history = [Entry(address)]
        self.pos = 0
        self.layout = None
        self._new_session()
        self._arrive("start", None)
        self._post(False)

    # ======================================================================
    # session
    # ======================================================================
    def _new_session(self):
        self.clock = Clock()
        self.service = Service(self.clock, self.fixture_dir, self.profile, fixture=self.fixture)
        self.announcements = []
        self.board_state = "none"        # none | loading | failed | ok
        self.columns = []
        self.people = []
        self.labels = []
        self.current_user = None
        self.col_state = {}              # none | loading | slow | failed | ok
        self.col_cards = {}
        self.col_timer = {}
        self.cards = {}
        self.card_req = {}               # loading | failed | null | ok
        self.comments = {}               # id -> {"state": loading|failed|ok, "list": [...]}
        self.pending_del = {}            # id -> {"state": waits|sent|done, "col", "idx"}
        self.move_saving = Counter()
        self.title_saving = Counter()
        self.desc_saving = Counter()
        self.labels_saving = Counter()
        self.assignee_saving = Counter()
        self.comment_sending = {}
        self.notice = None
        self.board_last_filter = None
        self.focus_stop = None
        self.focus = None
        self.scroll = 0
        self.selection = []
        self.carry = None
        self.filter_text = ""
        self.filter_timer = None
        self.title_edit = None
        self.desc_edit = None
        self.comment_text = ""
        self.comment_message = None
        self.prompt = None
        self.prompt_prev_focus = None
        self.alert_gen = 0
        self.board_fail_gen = 0
        self.card_fail_gen = 0
        self.col_fail_gen = {}
        self.comments_fail_gen = {}
        self.prev_alerts = set()

    def call(self, op, args, cb):
        self.service.call(op, args, cb)

    def announce(self, text):
        self.announcements.append(text)

    def _gen(self):
        self.alert_gen += 1
        return self.alert_gen

    # ======================================================================
    # derived state
    # ======================================================================
    @property
    def entry(self):
        return self.history[self.pos]

    def place(self):
        return addresses.parse(self.entry.addr)

    def write_addr(self, a):
        if self.board_state == "ok":
            return addresses.written(a, self.labels, [p["id"] for p in self.people])
        return addresses.written(a)

    def column_ids(self):
        return [c["id"] for c in self.columns]

    def column_name(self, cid):
        for c in self.columns:
            if c["id"] == cid:
                return c["name"]
        return cid

    def column_limit(self, cid):
        for c in self.columns:
            if c["id"] == cid:
                return c.get("limit")
        return None

    def person_name(self, pid):
        for p in self.people:
            if p["id"] == pid:
                return p["name"]
        return pid

    def board_ready(self):
        return self.place().kind == "board" and self.board_state == "ok"

    def current_filter(self):
        a = self.place()
        if a.kind != "board":
            return ("", (), ())
        return a.filter()

    def filter_on(self, f=None):
        f = f or self.current_filter()
        return bool(f[0] or f[1] or f[2])

    def matches(self, card, f):
        q, labels, who = f
        if q:
            t = card.title.lower()
            i = card.id.lower()
            for w in q.lower().split(" "):
                if w not in t and w not in i:
                    return False
        for l in labels:
            if l not in card.labels:
                return False
        if who:
            if card.assignee is None:
                if "none" not in who:
                    return False
            elif card.assignee not in who:
                return False
        return True

    def visible(self, col, f=None):
        if self.col_state.get(col) != "ok":
            return []
        f = f or self.current_filter()
        return [x for x in self.col_cards[col] if self.matches(self.cards[x], f)]

    def board_visible(self):
        out = []
        for c in self.column_ids():
            out.extend(self.visible(c))
        return out

    def is_visible(self, cid):
        if cid not in self.cards:
            return False
        col = self.cards[cid].column
        return cid in self.visible(col)

    def board_index(self, cid):
        cols = self.column_ids()
        card = self.cards.get(cid)
        if card is None or card.column not in cols or cid not in self.col_cards.get(card.column, []):
            return (len(cols), 0)
        return (cols.index(card.column), self.col_cards[card.column].index(cid))

    def board_order(self, ids):
        return sorted(ids, key=self.board_index)

    def column_view_state(self, cid):
        st = self.col_state.get(cid, "none")
        if st in ("none", "loading"):
            return "fresh"
        if st in ("slow", "failed"):
            return st
        if not self.col_cards[cid]:
            return "empty"
        return "cards" if self.visible(cid) else "nomatch"

    def any_column_loading(self):
        return any(self.col_state.get(c) in ("none", "loading", "slow") for c in self.column_ids())

    def total_cards(self):
        return sum(len(self.col_cards[c]) for c in self.column_ids() if self.col_state.get(c) == "ok")

    def count_line(self):
        """DAT-2."""
        if self.any_column_loading():
            return "Loading cards…"
        total = self.total_cards()
        if self.filter_on():
            return of_cards(len(self.board_visible()), total)
        return cards_word(total)

    def column_count(self, cid):
        """DAT-3."""
        n = len(self.col_cards[cid])
        if self.filter_on():
            return of_cards(len(self.visible(cid)), n)
        return cards_word(n)

    def effective_stop(self):
        """FCS-1."""
        vis = self.board_visible()
        if self.focus_stop in vis:
            return self.focus_stop
        return vis[0] if vis else None

    def is_full(self, col, exclude=None):
        """DAT-7."""
        lim = self.column_limit(col)
        if lim is None:
            return False
        n = len([x for x in self.col_cards.get(col, []) if x != exclude])
        return n >= lim

    def full_text(self, col):
        return "%s is full (%s)." % (self.column_name(col), cards_word(self.column_limit(col)))

    def card_state(self, cid):
        """CRD-T1, without its requests."""
        if cid in self.pending_del:
            return "missing"
        if self.board_state == "failed" or self.card_req.get(cid) == "failed":
            return "failed"
        held = cid in self.cards
        if held and self.board_state == "ok":
            return "ready"
        if held:
            return "loading"
        if self.card_req.get(cid) == "null":
            return "missing"
        if self.board_state == "ok" and self.columns and all(
                self.col_state.get(c) == "ok" for c in self.column_ids()):
            return "missing"
        return "loading"

    def place_state(self):
        """("board", state) | ("card", state) | ("missing", "page"|"card")."""
        a = self.place()
        if a.kind == "board":
            return ("board", {"none": "loading", "loading": "loading"}.get(self.board_state, self.board_state))
        if a.kind == "card":
            st = self.card_state(a.card)
            if st == "missing":
                return ("missing", "card")
            return ("card", st)
        return ("missing", "page")

    def card_shown(self, cid):
        a = self.place()
        return a.kind == "card" and a.card == cid and self.card_state(cid) == "ready"

    def has_place_title(self):
        kind, st = self.place_state()
        if kind == "card":
            if st == "loading":
                return False
            if st == "ready" and self.title_edit is not None:
                return False
        return True

    def labels_sorted(self, labels):
        order = {l: i for i, l in enumerate(self.labels)}
        return sorted(set(labels), key=lambda l: order.get(l, len(order)))

    # ======================================================================
    # focus
    # ======================================================================
    def set_focus(self, key):
        self.focus = key
        if key is not None and key[0] == "card":
            self.focus_stop = key[1]

    def focus_title(self):
        self.focus = ("title",) if self.has_place_title() else None

    # ======================================================================
    # navigation (NAV-*, TRM-3, MEM-T1, NAV-T1)
    # ======================================================================
    def push(self, addr, mark=False, how="step"):
        prev = self.place()
        del self.history[self.pos + 1:]
        self.history.append(Entry(addr, 0, mark))
        self.pos = len(self.history) - 1
        self._arrive(how, prev)

    def replace(self, addr, how="step"):
        prev = self.place()
        self.history[self.pos] = Entry(addr, 0, False)
        self._arrive(how, prev)

    def go_back(self):
        if self.pos == 0:
            return
        prev = self.place()
        self.pos -= 1
        self._arrive("back", prev)

    def go_forward(self):
        if self.pos >= len(self.history) - 1:
            return
        prev = self.place()
        self.pos += 1
        self._arrive("forward", prev)

    def go_up(self):
        """NAV-T3."""
        if self.entry.mark and self.pos > 0:
            self.go_back()
        else:
            self.push(self.board_last_filter or "board", how="goup")

    def open_home(self):
        """NAV-T2."""
        a = self.place()
        if a.kind == "board" and self.entry.addr == "board":
            self.scroll = 0
            self.entry.scroll = 0
        else:
            self.push("board", how="step")

    def open_board_link(self):
        """NAV-2."""
        self.push("board", how="step")

    def enter_address(self, text):
        """NAV-3."""
        self.push(text, mark=False, how="direct")

    def reload(self):
        """TRM-5."""
        self._new_session()
        self._arrive("start", None)

    def _arrive(self, how, prev):
        # MEM-T1: what an arrival removes
        if self.carry:
            self.cancel_carry()
        self.selection = []
        self.title_edit = None
        self.desc_edit = None
        self.comment_text = ""
        self.comment_message = None
        self.prompt = None
        self._cancel_filter_timer()
        # NAV-1: rewrite the entry to the written form
        a = addresses.parse(self.entry.addr)
        self.entry.addr = self.write_addr(a)
        a = addresses.parse(self.entry.addr)
        if a.kind == "board":
            self.filter_text = a.q
            self.board_last_filter = self.entry.addr
            self._board_loads()
        else:
            self.filter_text = ""
            if a.kind == "card":
                self._card_loads()
        # NAV-T1
        if how == "start":
            self.scroll = 0
            self.focus = None
        else:
            row2 = (a.kind == "board" and prev is not None and prev.kind == "card"
                    and how in ("back", "forward", "goup") and self.is_visible(prev.card))
            if row2:
                self.scroll = self.entry.scroll if how in ("back", "forward") else 0
                self.set_focus(("card", prev.card))
            elif how in ("back", "forward"):
                self.scroll = self.entry.scroll if a.kind == "board" else 0
                self.focus_title()
            else:
                self.scroll = 0
                self.focus_title()
        self.entry.scroll = self.scroll

    # ======================================================================
    # loads (BRD-*, COL-*, CRD-*)
    # ======================================================================
    def _board_loads(self):
        if self.board_state == "none":
            self._request_board()
        elif self.board_state == "ok":
            self._request_columns()

    def _request_board(self):
        self.board_state = "loading"
        self.call("loadBoard", {}, self._on_board)

    def _on_board(self, reply):
        if reply.get("ok"):
            d = reply["data"]
            self.columns = d["columns"]
            self.people = d["people"]
            self.labels = d["labels"]
            self.current_user = d.get("currentUser")
            self.board_state = "ok"
            for c in self.columns:
                self.col_state.setdefault(c["id"], "none")
                self.col_cards.setdefault(c["id"], [])
            a = self.place()
            if self.board_last_filter is not None:
                self.board_last_filter = self.write_addr(addresses.parse(self.board_last_filter))
            if a.kind == "board":
                self.entry.addr = self.write_addr(a)
                self.board_last_filter = self.entry.addr
                self._request_columns()
        else:
            self.board_state = "failed"
            self.board_fail_gen = self._gen()
        self._after_event()

    def _request_columns(self):
        for cid in self.column_ids():
            if self.col_state.get(cid, "none") == "none":
                self._request_column(cid)

    def _request_column(self, cid):
        self.col_state[cid] = "loading"
        old = self.col_timer.get(cid)
        if old:
            old.cancel()

        def slow():
            if self.col_state.get(cid) == "loading":
                self.col_state[cid] = "slow"

        self.col_timer[cid] = self.clock.schedule(SLOW_AFTER, slow)
        self.call("loadColumn", {"column": cid}, lambda r: self._on_column(cid, r))

    def _on_column(self, cid, reply):
        t = self.col_timer.pop(cid, None)
        if t:
            t.cancel()
        if reply.get("ok"):
            placed = set()
            for c in self.column_ids():
                if c != cid and self.col_state.get(c) == "ok":
                    placed.update(self.col_cards[c])
            lst = []
            for i, d in enumerate(reply["data"]["cards"]):
                x = d["id"]
                if x in self.pending_del:
                    pd = self.pending_del[x]
                    if pd["idx"] is None:
                        pd["idx"] = i
                        pd["col"] = cid
                    continue
                if x in placed:
                    continue
                if x in self.cards:
                    self.cards[x].column = cid
                else:
                    self.cards[x] = Card(d, cid)
                lst.append(x)
            self.col_cards[cid] = lst
            self.col_state[cid] = "ok"
            # COL-5
            if self.place().kind == "board" and not self.any_column_loading():
                self.announce(self.count_line())
        else:
            self.col_state[cid] = "failed"
            self.col_fail_gen[cid] = self._gen()
        self._after_event()

    def retry_column(self, cid):
        """COL-3."""
        if self.col_state.get(cid) == "failed":
            self._request_column(cid)

    def retry_place(self):
        kind, st = self.place_state()
        if kind == "board" and st == "failed":
            self._request_board()                       # BRD-3
        elif kind == "card" and st == "failed":         # CRD-2
            cid = self.place().card
            if self.board_state == "failed":
                self._request_board()
            if self.card_req.get(cid) == "failed":
                self._request_card(cid)
            self._card_loads()

    def _after_event(self):
        if self.place().kind == "card":
            self._card_loads()

    def _card_loads(self):
        """The requests of CRD-T1 and CRD-1."""
        cid = self.place().card
        st = self.card_state(cid)
        if st == "loading":
            if cid not in self.cards and cid not in self.card_req:
                self._request_card(cid)
            if self.board_state == "none":
                self._request_board()
        elif st == "ready":
            if cid not in self.comments:
                self._request_comments(cid)

    def _request_card(self, cid):
        self.card_req[cid] = "loading"
        self.call("loadCard", {"card": cid}, lambda r: self._on_card(cid, r))

    def _on_card(self, cid, reply):
        if reply.get("ok"):
            d = reply["data"].get("card")
            if d is None:
                self.card_req[cid] = "null"
            else:
                self.card_req[cid] = "ok"
                if cid not in self.cards:
                    self.cards[cid] = Card(d, d.get("column"))
        else:
            self.card_req[cid] = "failed"
            self.card_fail_gen = self._gen()
        self._after_event()

    def _request_comments(self, cid):
        self.comments[cid] = {"state": "loading", "list": []}
        self.call("loadComments", {"card": cid}, lambda r: self._on_comments(cid, r))

    def _on_comments(self, cid, reply):
        cm = self.comments.setdefault(cid, {"state": "loading", "list": []})
        if reply.get("ok"):
            cm["state"] = "ok"
            cm["list"] = [dict(author=c["author"], at=c["at"], text=c["text"], sending=False)
                          for c in reply["data"]["comments"]]
        else:
            cm["state"] = "failed"
            self.comments_fail_gen[cid] = self._gen()

    def retry_comments(self):
        """CRD-4."""
        cid = self.place().card
        cm = self.comments.get(cid)
        if cm and cm["state"] == "failed":
            self._request_comments(cid)

    # ======================================================================
    # notice (NTC-*)
    # ======================================================================
    def raise_notice(self, kind, text, action=None, fn=None, delete_card=None):
        if self.notice is not None:
            self._end_notice("replaced")
        n = Notice(kind, text, action, fn, delete_card)
        if kind == "info":
            n.timer = self.clock.schedule(NOTICE_TIME, lambda: self._notice_time(n))
        self.notice = n
        self.announce(text)

    def _notice_time(self, n):
        if self.notice is n:
            self._end_notice("time")

    def _end_notice(self, reason):
        n = self.notice
        if n is None:
            return
        self.notice = None
        if n.timer:
            n.timer.cancel()
        if n.delete_card and reason != "undo":
            self._send_delete(n.delete_card)       # DEL-2

    def notice_action(self):
        """NTC-4."""
        n = self.notice
        if n is None or not n.action:
            return
        self._end_notice("undo" if n.action == "Undo" else "action")
        if n.fn:
            n.fn()

    def undo(self):
        """NTC-5."""
        if self.notice is not None and self.notice.action == "Undo":
            self.notice_action()

    def dismiss_notice(self):
        """NTC-6."""
        if self.notice is not None and self.notice.kind == "error":
            self._end_notice("dismiss")

    # ======================================================================
    # filter (FLT-*)
    # ======================================================================
    def _cancel_filter_timer(self):
        if self.filter_timer:
            self.filter_timer.cancel()
        self.filter_timer = None

    def set_filter_text(self, text):
        """FLT-1."""
        if text == self.filter_text:
            return
        self.filter_text = text
        self._cancel_filter_timer()
        if self.board_ready():
            self.filter_timer = self.clock.schedule(FILTER_DELAY, self._filter_delay_end)

    def _filter_delay_end(self):
        """FLT-2."""
        self.filter_timer = None
        if self.board_ready():
            self.apply_filter()

    def apply_filter(self, labels=None, who=None):
        """FLT-8."""
        a = self.place()
        labels = a.labels if labels is None else labels
        who = a.who if who is None else who
        q = norm_ws(self.filter_text)
        self.entry.addr = self.write_addr(addresses.Addr("board", q, labels, who))
        self.board_last_filter = self.entry.addr
        if self.carry:
            self.cancel_carry()
        self.prune_selection()
        self._cancel_filter_timer()
        self.announce(self.count_line())

    def commit_filter(self):
        """FLT-3."""
        self.apply_filter()
        vis = self.board_visible()
        if len(vis) == 1:
            self.set_focus(("card", vis[0]))

    def toggle_label_filter(self, label):
        """FLT-4."""
        labels = list(self.place().labels)
        if label in labels:
            labels.remove(label)
        else:
            labels.append(label)
        self.apply_filter(labels=labels)

    def toggle_assignee_filter(self, pid):
        """FLT-5."""
        who = list(self.place().who)
        if pid in who:
            who.remove(pid)
        else:
            who.append(pid)
        self.apply_filter(who=who)

    def clear_filters(self):
        """FLT-6."""
        self.filter_text = ""
        self.apply_filter(labels=(), who=())
        self.focus = ("filter",)

    def ask_filter(self):
        """FLT-7."""
        if self.board_ready() and not self.carry:
            self.focus = ("filter",)

    # ======================================================================
    # cards on the board: focus, open, selection (FCS-*, OPN-1, SEL-*)
    # ======================================================================
    def move_focus(self, cid, k):
        """FCS-2."""
        col = self.cards[cid].column
        vis = self.visible(col)
        if cid not in vis:
            return
        i = vis.index(cid)
        t = None
        if k == "up":
            t = vis[i - 1] if i > 0 else None
        elif k == "down":
            t = vis[i + 1] if i + 1 < len(vis) else None
        elif k == "home":
            t = vis[0]
        elif k == "end":
            t = vis[-1]
        elif k in ("left", "right"):
            cols = self.column_ids()
            ci = cols.index(col)
            step = -1 if k == "left" else 1
            j = ci + step
            while 0 <= j < len(cols):
                v = self.visible(cols[j])
                if v:
                    t = v[min(i, len(v) - 1)]
                    break
                j += step
        if t is not None:
            self.set_focus(("card", t))

    def open_card(self, cid):
        """OPN-1."""
        if self.carry:
            return
        self.push("card/" + cid, mark=True, how="step")

    def toggle_select(self, cid):
        """SEL-1."""
        if self.carry:
            return
        if cid in self.selection:
            self.selection.remove(cid)
        else:
            self.selection.append(cid)
        self.set_focus(("card", cid))

    def select_column(self, col):
        """SEL-2."""
        if self.carry:
            return
        vis = self.visible(col)
        if not vis:
            return
        if all(x in self.selection for x in vis):
            self.selection = [x for x in self.selection if x not in vis]
        else:
            for x in vis:
                if x not in self.selection:
                    self.selection.append(x)

    def clear_selection(self):
        """SEL-3."""
        if self.selection:
            self.selection = []
            self.focus_title()

    def prune_selection(self):
        """SEL-4."""
        if self.place().kind != "board":
            self.selection = []
            return
        self.selection = [x for x in self.selection if x not in self.pending_del and self.is_visible(x)]

    # ======================================================================
    # column lists
    # ======================================================================
    def position(self, cid):
        card = self.cards[cid]
        lst = self.col_cards.get(card.column, [])
        return card.column, (lst.index(cid) if cid in lst else None)

    def remove_from_col(self, cid):
        card = self.cards[cid]
        lst = self.col_cards.get(card.column, [])
        if cid in lst:
            i = lst.index(cid)
            lst.remove(cid)
            return card.column, i
        return card.column, None

    def insert_at(self, cid, col, idx):
        """DAT-8: the position number, counted in the column as it is now, or the end."""
        lst = self.col_cards.setdefault(col, [])
        if cid in lst:
            lst.remove(cid)
        if idx is None or idx > len(lst):
            idx = len(lst)
        lst.insert(idx, cid)
        self.cards[cid].column = col

    def place_visible(self, cid, col, p):
        """DAT-6: put a card at position p (from 0) among the visible cards of col."""
        self.remove_from_col(cid)
        lst = self.col_cards[col]
        vis = [x for x in self.visible(col) if x != cid]
        if p <= 0 or not vis:
            idx = 0
        else:
            above = vis[min(p, len(vis)) - 1]
            idx = lst.index(above) + 1
        lst.insert(idx, cid)
        self.cards[cid].column = col

    # ======================================================================
    # carry (CRY-*)
    # ======================================================================
    def pick_up(self, cid):
        """CRY-1."""
        if self.carry or self.move_saving[cid]:
            return
        col = self.cards[cid].column
        vis = self.visible(col)
        if cid not in vis:
            return
        self.carry = {"card": cid, "col": col, "idx": self.col_cards[col].index(cid),
                      "vis": vis.index(cid)}
        self.set_focus(("card", cid))

    def carry_step(self, k):
        """CRY-2."""
        cid = self.carry["card"]
        col = self.cards[cid].column
        vis = self.visible(col)
        p = vis.index(cid)
        if k == "up":
            if p > 0:
                self.place_visible(cid, col, p - 1)
        elif k == "down":
            if p + 1 < len(vis):
                self.place_visible(cid, col, p + 1)
        else:
            cols = self.column_ids()
            step = -1 if k == "left" else 1
            j = cols.index(col) + step
            while 0 <= j < len(cols):
                if self.col_state.get(cols[j]) == "ok":
                    tv = self.visible(cols[j])
                    self.place_visible(cid, cols[j], min(p, len(tv)))
                    return
                j += step

    def cancel_carry(self):
        """CRY-5."""
        c = self.carry
        if not c:
            return
        self.carry = None
        if c["card"] in self.cards:
            self.insert_at(c["card"], c["col"], c["idx"])

    def drop(self):
        """CRY-T1."""
        c = self.carry
        cid = c["card"]
        col = self.cards[cid].column
        vis = self.visible(col)
        p = vis.index(cid) if cid in vis else -1
        if col == c["col"] and p == c["vis"]:
            self.cancel_carry()
            return
        if col != c["col"] and self.is_full(col, exclude=cid):
            self.cancel_carry()
            self.raise_notice("info", self.full_text(col))
            return
        self.carry = None
        self.start_move(cid, c["col"], c["idx"], col, self.col_cards[col].index(cid))
        self.set_focus(("card", cid))

    # ======================================================================
    # move saves (MOV-*)
    # ======================================================================
    def start_move(self, cid, from_col, from_idx, to_col, to_idx):
        self.move_saving[cid] += 1
        self.call("moveCards", {"moves": [{"card": cid, "column": to_col, "index": to_idx}]},
                  lambda r: self._on_move(r, cid, from_col, from_idx, to_col, to_idx))

    def _on_move(self, reply, cid, from_col, from_idx, to_col, to_idx):
        self.move_saving[cid] -= 1
        ok = bool(reply.get("ok")) and all(x.get("ok") for x in reply["data"]["results"])
        if ok:                                                    # MOV-1
            self.raise_notice("info", "Moved %s to %s." % (cid, self.column_name(to_col)), "Undo",
                              lambda: self.undo_moves([(cid, from_col, from_idx)]))
        else:                                                     # MOV-2
            if cid in self.cards and cid not in self.pending_del:
                self.remove_from_col(cid)
                self.insert_at(cid, from_col, from_idx)
            self.raise_notice("error", "Couldn't move %s. It is back in %s." % (cid, self.column_name(from_col)),
                              "Retry", lambda: self._retry_move(cid, to_col, to_idx))

    def _retry_move(self, cid, to_col, to_idx):
        if cid not in self.cards or cid in self.pending_del or self.move_saving[cid]:
            return
        if self.carry and self.carry["card"] == cid:
            self.cancel_carry()
        card = self.cards[cid]
        if card.column != to_col and self.is_full(to_col, exclude=cid):
            self.raise_notice("info", self.full_text(to_col))
            return
        fc, fi = self.remove_from_col(cid)
        self.insert_at(cid, to_col, to_idx)
        self.start_move(cid, fc, fi, to_col, self.col_cards[to_col].index(cid))

    def undo_moves(self, moves):
        """MOV-3. moves: [(card, column before the move, position before the move)]."""
        placed = []
        moves = [m for m in moves if m[0] in self.cards and m[0] not in self.pending_del]
        for cid, fc, fi in moves:
            if self.carry and self.carry["card"] == cid:
                self.cancel_carry()
        before = {m[0]: self.position(m[0]) for m in moves}  # where each card is before the undo
        for cid, fc, fi in sorted(moves, key=lambda m: m[2]):
            self.remove_from_col(cid)
            self.insert_at(cid, fc, fi)
            placed.append((cid, fc, fi, before[cid]))
        if not placed:
            return
        req = []
        for cid, fc, fi, pre in placed:
            self.move_saving[cid] += 1
            req.append({"card": cid, "column": fc, "index": self.col_cards[fc].index(cid)})
        first = self.board_order([p[0] for p in placed])[0]
        if self.place().kind == "board" and self.is_visible(first):
            self.set_focus(("card", first))
        self.call("moveCards", {"moves": req}, lambda r: self._on_undo(r, placed))

    def _on_undo(self, reply, placed):
        results = reply["data"]["results"] if reply.get("ok") else [{"card": p[0], "ok": False} for p in placed]
        failed = []
        for (cid, fc, fi, pre), res in zip(placed, results):
            self.move_saving[cid] -= 1
            if not res.get("ok"):
                failed.append((cid, fc, fi, pre))
        if not failed:
            return
        for cid, fc, fi, pre in sorted(failed, key=lambda p: (p[3][1] if p[3][1] is not None else 1 << 30)):
            if cid in self.cards and cid not in self.pending_del:
                self.remove_from_col(cid)
                self.insert_at(cid, pre[0], pre[1])
        if len(failed) == 1:
            text = "Couldn't undo the move of %s." % failed[0][0]
        else:
            text = "Couldn't undo the move of %d cards." % len(failed)
        again = [(cid, fc, fi) for cid, fc, fi, pre in failed]
        self.raise_notice("error", text, "Retry", lambda: self.undo_moves(again))

    # ======================================================================
    # bulk actions (BLK-*)
    # ======================================================================
    def bulk_move(self, target, pool=None):
        """BLK-T1."""
        if self.carry:
            return
        if self.col_state.get(target) != "ok":
            return
        pool = list(self.selection) if pool is None else list(pool)
        cands = [x for x in self.board_order(pool)
                 if x in self.cards and x not in self.pending_del
                 and self.cards[x].column != target and not self.move_saving[x]]
        if not cands:
            return
        lim = self.column_limit(target)
        if lim is not None:
            room = lim - len(self.col_cards[target])
            if room <= 0:
                self.raise_notice("info", self.full_text(target))
                return
            go = cands[:room]
        else:
            go = cands
        moves = []
        before = {cid: self.position(cid) for cid in go}      # DAT-8: the positions before the move
        for cid in go:
            self.remove_from_col(cid)
            self.insert_at(cid, target, None)
            fc, fi = before[cid]
            moves.append((cid, fc, fi))
            if cid in self.selection:
                self.selection.remove(cid)
            self.move_saving[cid] += 1
        req = [{"card": cid, "column": target, "index": self.col_cards[target].index(cid)}
               for cid, fc, fi in moves]
        n_cands = len(cands)
        self.call("moveCards", {"moves": req}, lambda r: self._on_bulk(r, target, moves, n_cands))

    def _on_bulk(self, reply, target, moves, n_cands):
        """BLK-T2."""
        results = reply["data"]["results"] if reply.get("ok") else [{"card": m[0], "ok": False} for m in moves]
        oks, fails = [], []
        for m, res in zip(moves, results):
            self.move_saving[m[0]] -= 1
            (oks if res.get("ok") else fails).append(m)
        tname = self.column_name(target)
        if fails:
            for cid, fc, fi in sorted(fails, key=lambda m: m[2]):
                if cid in self.cards and cid not in self.pending_del:
                    self.remove_from_col(cid)
                    self.insert_at(cid, fc, fi)
                    if self.place().kind == "board" and self.is_visible(cid) and cid not in self.selection:
                        self.selection.append(cid)
            failed_ids = self.board_order([m[0] for m in fails])
            text = "Moved %s to %s. Couldn't move %s." % (of_cards(len(oks), len(moves)), tname, ", ".join(failed_ids))
            self.raise_notice("error", text, "Retry", lambda: self.bulk_move(target, failed_ids))
        elif len(oks) < n_cands:
            text = "Moved %s to %s. %s" % (of_cards(len(oks), n_cands), tname, self.full_text(target))
            self.raise_notice("info", text, "Undo", lambda: self.undo_moves(oks))
        else:
            text = "Moved %s to %s." % (cards_word(len(oks)), tname)
            self.raise_notice("info", text, "Undo", lambda: self.undo_moves(oks))

    def bulk_label(self, label):
        """BLK-T3."""
        if self.carry or not self.selection:
            return
        sel = self.board_order(self.selection)
        if all(label in self.cards[x].labels for x in sel):
            changed = sel
            for x in changed:
                self.cards[x].labels = [l for l in self.cards[x].labels if l != label]
            text = 'Removed "%s" from %s.' % (label, cards_word(len(changed)))
        else:
            lacking = [x for x in sel if label not in self.cards[x].labels]
            changed = [x for x in lacking if len(self.cards[x].labels) < MAX_LABELS]
            if not changed:
                self.raise_notice("info", "A card can have at most 3 labels.")
                return
            for x in changed:
                self.cards[x].labels = self.labels_sorted(self.cards[x].labels + [label])
            if len(changed) == len(lacking):
                text = 'Added "%s" to %s.' % (label, cards_word(len(changed)))
            else:
                text = 'Added "%s" to %s. A card can have at most 3 labels.' % (
                    label, of_cards(len(changed), len(lacking)))
        for x in changed:
            self.labels_saving[x] += 1
        changes = [{"card": x, "labels": list(self.cards[x].labels)} for x in changed]
        self.prune_selection()

        def done(reply):
            for x in changed:
                self.labels_saving[x] -= 1
            if reply.get("ok"):                                   # BLK-4
                self.raise_notice("info", text)

        self.call("saveLabels", {"changes": changes}, done)

    # ======================================================================
    # delete (DEL-*)
    # ======================================================================
    def delete_on_board(self, cid):
        """DEL-1."""
        if self.carry or self.move_saving[cid] or not self.board_ready():
            return
        col = self.cards[cid].column
        vis = self.visible(col)
        target = None
        if cid in vis:
            i = vis.index(cid)
            if i + 1 < len(vis):
                target = vis[i + 1]
            elif i > 0:
                target = vis[i - 1]
        self._delete(cid)
        if target:
            self.set_focus(("card", target))
        else:
            self.focus_title()

    def _delete(self, cid):
        col, idx = self.remove_from_col(cid)
        if self.col_state.get(col) != "ok":
            idx = None
        self.pending_del[cid] = {"state": "waits", "col": col, "idx": idx}
        if cid in self.selection:
            self.selection.remove(cid)
        self.raise_notice("info", "Deleted %s." % cid, "Undo", lambda: self._undo_delete(cid), delete_card=cid)

    def _undo_delete(self, cid):
        """DEL-3."""
        pd = self.pending_del.pop(cid, None)
        if pd is None:
            return
        if self.col_state.get(pd["col"]) == "ok":
            self.insert_at(cid, pd["col"], pd["idx"])
        else:
            self.cards[cid].column = pd["col"]
        if self.place().kind == "board" and self.is_visible(cid):
            self.set_focus(("card", cid))
        self._after_event()

    def _send_delete(self, cid):
        pd = self.pending_del.get(cid)
        if pd is None:
            return
        pd["state"] = "sent"
        self.call("deleteCard", {"card": cid}, lambda r: self._on_delete(cid, r))

    def _on_delete(self, cid, reply):
        pd = self.pending_del.get(cid)
        if reply.get("ok"):
            if pd:
                pd["state"] = "done"
            return
        if pd is None:
            return
        del self.pending_del[cid]                                  # DEL-4
        if self.col_state.get(pd["col"]) == "ok":
            self.insert_at(cid, pd["col"], pd["idx"])
        self.raise_notice("error", "Couldn't delete %s. It is back in %s." % (cid, self.column_name(pd["col"])),
                          "Retry", lambda: self._retry_delete(cid))
        self._after_event()

    def _retry_delete(self, cid):
        if cid in self.pending_del or cid not in self.cards:
            return
        col, idx = self.remove_from_col(cid)
        if self.col_state.get(col) != "ok":
            idx = None
        if cid in self.selection:
            self.selection.remove(cid)
        self.pending_del[cid] = {"state": "waits", "col": col, "idx": idx}
        self._send_delete(cid)

    def delete_on_card(self):
        """DEL-T1."""
        cid = self.place().card
        if self.card_state(cid) != "ready":
            return
        self._delete(cid)
        if self.entry.mark and self.pos > 0:
            self.go_back()
        else:
            self.replace(self.board_last_filter or "board")

    # ======================================================================
    # card place: title, labels, assignee, description, comments
    # ======================================================================
    def _card(self):
        return self.cards[self.place().card]

    def edit_title(self):
        """TTL-1."""
        c = self._card()
        if self.title_saving[c.id] or self.title_edit is not None:
            return
        self.title_edit = {"draft": c.title, "message": None, "gen": 0}
        self.focus = ("title-field",)

    def _title_message(self, text):
        self.title_edit["message"] = text
        self.title_edit["gen"] = self._gen()

    def commit_title(self):
        """TTL-T1."""
        c = self._card()
        d = norm_ws(self.title_edit["draft"])
        if len(d) == 0:
            self._title_message("A title needs at least 1 character.")
        elif len(d) > MAX_TITLE:
            self._title_message("A title can have at most 80 characters.")
        elif d == c.title:
            self.title_edit = None
            self.focus = ("title",)
        else:
            self.title_edit = None
            self.save_title(c.id, d)
            self.focus = ("title",)

    def leave_title(self):
        """TTL-3."""
        c = self._card()
        d = norm_ws(self.title_edit["draft"])
        self.title_edit = None
        if 1 <= len(d) <= MAX_TITLE and d != c.title:
            self.save_title(c.id, d)

    def save_title(self, cid, new):
        old = self.cards[cid].title
        self.cards[cid].title = new
        self.title_saving[cid] += 1

        def done(reply):
            self.title_saving[cid] -= 1
            if not reply.get("ok"):                                 # TTL-4
                if self.cards[cid].title == new:
                    self.cards[cid].title = old

                def retry():
                    if not self.title_saving[cid] and cid in self.cards:
                        self.save_title(cid, new)

                self.raise_notice("error", "Couldn't save the title of %s." % cid, "Retry", retry)

        self.call("saveTitle", {"card": cid, "title": new}, done)

    def toggle_label(self, label):
        """LBL-1."""
        c = self._card()
        if label in c.labels:
            c.labels = [l for l in c.labels if l != label]
        elif len(c.labels) < MAX_LABELS:
            c.labels = self.labels_sorted(c.labels + [label])
        else:
            return
        self.labels_saving[c.id] += 1
        cid = c.id

        def done(reply):
            self.labels_saving[cid] -= 1

        self.call("saveLabels", {"changes": [{"card": cid, "labels": list(c.labels)}]}, done)

    def choose_assignee(self, pid):
        """ASG-1."""
        c = self._card()
        new = None if pid == "none" else pid
        if new == c.assignee:
            return
        c.assignee = new
        self.assignee_saving[c.id] += 1
        cid = c.id

        def done(reply):
            self.assignee_saving[cid] -= 1

        self.call("saveAssignee", {"card": cid, "assignee": new}, done)

    def edit_description(self):
        """DSC-1."""
        c = self._card()
        if self.desc_saving[c.id] or self.desc_edit is not None:
            return
        self.desc_edit = {"draft": c.description}
        self.focus = ("desc-field",)

    def commit_description(self):
        """DSC-2."""
        c = self._card()
        d = self.desc_edit["draft"].strip()
        self.desc_edit = None
        self.focus = ("edit-desc",)
        if d != c.description:
            c.description = d
            self.desc_saving[c.id] += 1
            cid = c.id

            def done(reply):
                self.desc_saving[cid] -= 1

            self.call("saveDescription", {"card": cid, "description": d}, done)

    def cancel_description(self):
        """DSC-3."""
        self.desc_edit = None
        self.focus = ("edit-desc",)

    def comment_enabled(self, cid):
        cm = self.comments.get(cid)
        return bool(cm and cm["state"] == "ok" and cid not in self.comment_sending)

    def commit_comment(self):
        """CMT-2."""
        c = self._card()
        if not self.comment_enabled(c.id):
            return
        t = self.comment_text.strip()
        if not t:
            return
        com = {"author": self.current_user, "at": None, "text": t, "sending": True}
        self.comments[c.id]["list"].append(com)
        c.comments += 1
        self.comment_sending[c.id] = com
        self.comment_text = ""
        self.focus = None
        cid = c.id
        self.call("addComment", {"card": cid, "text": t}, lambda r: self._on_comment(cid, com, r))

    def _on_comment(self, cid, com, reply):
        self.comment_sending.pop(cid, None)
        shown = self.card_shown(cid)
        if reply.get("ok"):                                          # CMT-3
            com["at"] = reply["data"]["comment"]["at"]
            com["sending"] = False
            if shown:
                self.focus = ("comment-field",)
            return
        cm = self.comments.get(cid)                                  # CMT-T1
        if cm and com in cm["list"]:
            cm["list"].remove(com)
        if cid in self.cards:
            self.cards[cid].comments -= 1
        if shown:
            self.comment_text = com["text"]
            self.comment_message = ("Couldn't add the comment. Your text is back in the field.", self._gen())
            self.focus = ("comment-field",)
        else:
            self.raise_notice("error", "Couldn't add the comment on %s." % cid)

    # ======================================================================
    # dismiss (DIS-T1)
    # ======================================================================
    def dismiss(self):
        a = self.place()
        f = self.focus
        if self.carry:
            self.cancel_carry()
            return
        if self.board_ready() and f == ("filter",):
            if self.filter_text:
                self.filter_text = ""
                self.apply_filter()
            else:
                stop = self.effective_stop()
                if stop:
                    self.set_focus(("card", stop))
                else:
                    self.focus_title()
            return
        if self.board_ready() and self.selection:
            self.selection = []
            return
        if a.kind == "card":
            st = self.card_state(a.card)
            if st == "ready":
                if self.title_edit is not None and f == ("title-field",):
                    self.title_edit = None
                    self.focus = ("title",)
                    return
                if self.desc_edit is not None:
                    self.cancel_description()
                    return
                if f == ("comment-field",):
                    return
            if st in ("loading", "failed", "ready"):
                self.go_up()

    # ======================================================================
    # keys (TRM-8)
    # ======================================================================
    def key(self, k):
        self._handle_key(k)
        self._post(True)

    def advance(self, ms):
        self.clock.advance(ms)
        self._post(False)

    def resize(self, width, height):
        self.width, self.height = width, height
        self._post(False)

    def _handle_key(self, k):
        if self.prompt is not None:
            return self._prompt_key(k)
        if k == "ctrl-b":
            return self.go_back()
        if k == "ctrl-f":
            return self.go_forward()
        if k == "ctrl-r":
            return self.reload()
        if k == "ctrl-g":
            self.prompt = ""
            self.prompt_prev_focus = self.focus
            self.focus = ("prompt",)
            return
        if k == "esc":
            return self.dismiss()
        if k in ("tab", "shift-tab"):
            return self.tab(k == "tab")
        f = self.focus
        kind = f[0] if f else None
        if kind in FIELD_KINDS:
            return self._field_key(kind, k)
        if k == "ctrl-z":
            return self.undo()
        if k == "/":
            return self.ask_filter()
        if kind == "card":
            return self._card_key(f[1], k)
        if f is not None and k in ("enter", "space"):
            return self.activate(f)

    def _prompt_key(self, k):
        """TRM-6."""
        if k == "enter":
            text = self.prompt
            self.prompt = None
            self.focus = self.prompt_prev_focus
            self.enter_address(text)
        elif k == "esc":
            self.prompt = None
            self.focus = self.prompt_prev_focus
        elif k == "backspace":
            self.prompt = self.prompt[:-1]
        elif k == "ctrl-u":
            self.prompt = ""
        elif k in ("ctrl-b", "ctrl-f", "ctrl-r"):
            self.prompt = None
            self.focus = self.prompt_prev_focus
            self._handle_key(k)
        elif k == "space":
            self.prompt += " "
        elif is_printable(k):
            self.prompt += k

    def _field_text(self, kind):
        if kind == "filter":
            return self.filter_text
        if kind == "title-field":
            return self.title_edit["draft"]
        if kind == "desc-field":
            return self.desc_edit["draft"]
        return self.comment_text

    def _field_set(self, kind, text):
        if kind == "filter":
            self.set_filter_text(text)
        elif kind == "title-field":
            self.title_edit["draft"] = text                        # TTL-2
        elif kind == "desc-field":
            self.desc_edit["draft"] = text                         # DSC-5
        else:
            if text != self.comment_text:
                self.comment_text = text
                self.comment_message = None                        # CMT-1

    def _field_key(self, kind, k):
        old = self._field_text(kind)
        if is_printable(k):
            self._field_set(kind, old + k)
        elif k == "space":
            self._field_set(kind, old + " ")
        elif k == "backspace":
            if old:
                self._field_set(kind, old[:-1])
        elif k == "ctrl-u":
            if old:
                self._field_set(kind, "")
        elif k == "enter":
            if kind == "filter":
                self.commit_filter()
            elif kind == "title-field":
                self.commit_title()
            else:
                self._field_set(kind, old + "\n")
        elif k == "ctrl-s":
            if kind == "desc-field":
                self.commit_description()
            elif kind == "comment-field":
                self.commit_comment()

    def _card_key(self, cid, k):
        if cid not in self.cards:
            return
        if self.carry:
            if k in ("up", "down", "left", "right"):
                self.carry_step(k)
            elif k in ("space", "enter"):
                self.drop()
            return
        if k in ("up", "down", "left", "right", "home", "end"):
            self.move_focus(cid, k)
        elif k == "enter":
            self.open_card(cid)
        elif k == "space":
            self.pick_up(cid)
        elif k == "x":
            self.toggle_select(cid)
        elif k == "X":
            self.select_column(self.cards[cid].column)
        elif k in ("delete", "backspace"):
            self.delete_on_board(cid)

    def tab(self, forward):
        """TRM-7."""
        order = self.layout.order if self.layout else []
        stops = [k for k, stop in order if stop]
        if not stops:
            return
        keys = [k for k, stop in order]
        cur = self.focus
        if cur in keys:
            i = keys.index(cur)
            n = len(order)
            j = i
            for _ in range(n):
                j = (j + (1 if forward else -1)) % n
                if order[j][1]:
                    break
            target = order[j][0]
        else:
            target = stops[0] if forward else stops[-1]
        if cur == ("title-field",) and self.title_edit is not None:
            self.leave_title()                                     # TTL-3
        self.set_focus(target)

    def activate(self, key):
        kind = key[0]
        arg = key[1] if len(key) > 1 else None
        if kind == "home":
            self.open_home()
        elif kind == "lf":
            self.toggle_label_filter(arg)
        elif kind == "af":
            self.toggle_assignee_filter(arg)
        elif kind in ("clear-filters", "show-all"):
            self.clear_filters()
        elif kind == "mv":
            self.bulk_move(arg)
        elif kind == "ls":
            self.bulk_label(arg)
        elif kind == "clear-sel":
            self.clear_selection()
        elif kind == "selall":
            self.select_column(arg)
        elif kind == "retry-col":
            self.retry_column(arg)
        elif kind == "try-again":
            self.retry_place()
        elif kind == "notice-action":
            self.notice_action()
        elif kind == "notice-dismiss":
            self.dismiss_notice()
        elif kind == "uplink":
            self.go_up()
        elif kind == "edit-title":
            self.edit_title()
        elif kind == "lbl":
            self.toggle_label(arg)
        elif kind == "asg":
            self.choose_assignee(arg)
        elif kind == "edit-desc":
            self.edit_description()
        elif kind == "desc-save":
            if self.desc_edit is not None:
                self.commit_description()
        elif kind == "desc-cancel":
            if self.desc_edit is not None:
                self.cancel_description()
        elif kind == "retry-comments":
            self.retry_comments()
        elif kind == "add-comment":
            self.commit_comment()
        elif kind == "delete-card":
            self.delete_on_card()
        elif kind == "board-link":
            self.open_board_link()

    # ======================================================================
    # after each input
    # ======================================================================
    def _post(self, is_key):
        import view
        if self.place().kind == "board":
            self.prune_selection()
        L = view.build(self)
        # FOC-1: the part that has focus is removed
        if self.focus is not None and self.focus not in L.by_key:
            self.focus = ("title",) if ("title",) in L.by_key else None
            L = view.build(self)
        # keep the part that has focus in view (TRM-A3)
        if self.focus is not None and L.area_h:
            p = L.by_key.get(self.focus)
            if p is not None and p.crow is not None:
                top = self.scroll
                if p.crow < top:
                    self.scroll = p.crow
                elif p.crow + p.rect[2] > top + L.area_h:
                    self.scroll = p.crow + p.rect[2] - L.area_h
                if self.scroll != top:
                    L = view.build(self)
        # alerts are announced each time they show
        cur = L.alerts
        before = len(self.announcements)
        for key, text in cur:
            if key not in self.prev_alerts:
                self.announce(text)
        self.prev_alerts = set(k for k, t in cur)
        if len(self.announcements) != before:
            L = view.build(self)
        if self.place().kind == "board":
            self.entry.scroll = self.scroll
        self.layout = L

    # ======================================================================
    # semantic dump (TRM-H5)
    # ======================================================================
    def dump(self):
        L = self.layout
        n = self.notice
        return {
            "title": L.title,
            "address": self.entry.addr,
            "depth": len(self.history),
            "focus": L.focus_index,
            "scrollTop": self.scroll == 0 or self.place().kind != "board",
            "parts": [p.as_dict() for p in L.shown],
            "columns": list(L.columns),
            "cards": list(L.cards),
            "notice": None if n is None else {"kind": n.kind, "text": n.text, "action": n.action},
            "announcements": list(self.announcements),
            "requests": [dict(r) for r in self.service.log],
        }


def default_fixture_dir():
    return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "fixture")
