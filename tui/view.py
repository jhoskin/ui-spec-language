"""Layout: the character grid and the parts (TRM-1, TRM-4, TRM-7, TRM-10, TRM-13,
TRM-14, TRM-A3, TRM-A4, TRM-A8, TRM-H5, TRM-H6).

build(app) gives a Layout. Rows and columns count from 1. A part in the area of
the columns has a virtual rect: its row is where it is painted when that row is
in view, and it can lie outside the screen when the area is scrolled.
"""
from app import comments_word, fmt_time

BOLD, DIM, REV = 1, 2, 4
MIN_W, MIN_H = 112, 30
SMALL_TEXT = "Slate needs 112 columns and 30 rows."
CARD_MAX_W = 80
PLACEHOLDER = "░"


def cut(s, w):
    """TRM-A4."""
    if w <= 0:
        return ""
    if len(s) <= w:
        return s
    return s[:w - 1] + "…"


class Part:
    __slots__ = ("key", "role", "name", "group", "state", "disabled", "text", "rect",
                 "stop", "crow", "clip")

    def __init__(self, key, role, name, group=None, state=None, disabled=False, text=None,
                 rect=(1, 1, 1, 1), stop=False, crow=None, clip=None):
        self.key = key
        self.role = role
        self.name = name
        self.group = group
        self.state = state
        self.disabled = disabled
        self.text = text
        self.rect = rect
        self.stop = stop
        self.crow = crow        # row in the area of the columns, from 0, or None
        self.clip = clip        # (first row, last row) where it can be painted, or None

    def as_dict(self):
        return {"role": self.role, "name": self.name, "group": self.group, "state": self.state,
                "disabled": self.disabled, "text": self.text, "rect": list(self.rect)}


class Layout:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.chars = [[" "] * w for _ in range(h)]
        self.attrs = [[0] * w for _ in range(h)]
        self.parts = []
        self.by_key = {}
        self.cards = []
        self.columns = []
        self.title = None
        self.alerts = []
        self.area_top = None
        self.area_h = 0
        self.cursor = None
        self.focus_index = None
        self.order = []
        self.shown = []
        self._n = 0

    # painting -------------------------------------------------------------
    def put(self, r, c, s, a=0, clip=None):
        if clip is not None and not (clip[0] <= r <= clip[1]):
            return
        if not (1 <= r <= self.h):
            return
        row = self.chars[r - 1]
        arow = self.attrs[r - 1]
        for i, ch in enumerate(s):
            cc = c + i
            if 1 <= cc <= self.w:
                row[cc - 1] = ch
                arow[cc - 1] = a

    def add(self, key, role, name, **kw):
        if key is None:
            self._n += 1
            key = ("_", self._n)
        p = Part(key, role, name, **kw)
        self.parts.append(p)
        self.by_key.setdefault(key, p)
        return p

    def text(self, r, c, s, w, role="text", a=0, key=None, clip=None, crow=None, group=None, name=None):
        """A part whose name and text is s, cut to width w."""
        shown = cut(s, w)
        self.put(r, c, shown, a, clip)
        return self.add(key, role, s if name is None else name, text=s, group=group,
                        rect=(r, c, 1, max(1, len(shown))), clip=clip, crow=crow)


def mark_toggle(state):
    return {"on": "[x] ", "off": "[ ] ", "mixed": "[-] "}[state]


def mark_choice(chosen):
    return "(o) " if chosen else "( ) "


def flow(L, row, x0, maxx, items, indent=None):
    """Put items left to right with two spaces between them; wrap at maxx.
    items: (painted text, attr, kwargs for L.add or None). Returns the last row used."""
    x = x0
    indent = x0 if indent is None else indent
    for text, a, kw in items:
        if x > x0 and x + len(text) - 1 > maxx and x != indent:
            row += 1
            x = indent
        shown = cut(text, maxx - x + 1)
        L.put(row, x, shown, a)
        if kw is not None:
            kw = dict(kw)
            key = kw.pop("key", None)
            role = kw.pop("role")
            name = kw.pop("name")
            L.add(key, role, name, rect=(row, x, 1, len(shown)), **kw)
        x += len(shown) + 2
    return row


# ==========================================================================
def _header(app):
    w, h = app.width, app.height
    L = Layout(w, h)
    # TRM-4 location line
    L.put(1, 1, "[Slate]")
    L.add(("home",), "link", "Slate", rect=(1, 1, 1, 7), stop=True)
    loc = "%s  %d/%d" % (app.entry.addr, app.pos + 1, len(app.history))
    loc = cut(loc, w - 10)
    L.put(1, w - len(loc) + 1, loc, DIM)
    return L


def build(app):
    w, h = app.width, app.height
    if w < MIN_W or h < MIN_H:
        L = Layout(w, h)
        L.put(1, 1, cut(SMALL_TEXT, w))
        L.add(None, "text", SMALL_TEXT, text=SMALL_TEXT, rect=(1, 1, 1, min(w, len(SMALL_TEXT))))
        L.order = []
        L.shown = list(L.parts)
        return L
    kind, st = app.place_state()
    bottom = h - 2          # last row for content
    if app.prompt is not None and app.notice is not None:
        bottom = h - 3      # the notice moves up one row while the prompt is open (TRM-6)
    if kind == "card" and st == "ready":
        # drop the oldest comments from the screen until the place fits
        cid = app.place().card
        ncom = len(app.comments.get(cid, {}).get("list", []))
        skip = 0
        while True:
            L = _header(app)
            last = _card_ready(app, L, cid, min(CARD_MAX_W, w), skip)
            if last <= bottom or skip >= ncom:
                break
            skip += 1
    else:
        L = _header(app)
        if kind == "board":
            _board(app, L, st, bottom)
        elif kind == "card":
            _card(app, L, st, bottom)
        else:
            _missing(app, L, st)
    _notice(app, L)
    # TRM-11 announcement row
    if app.announcements:
        L.put(h, 1, cut(app.announcements[-1], w), DIM)
    _finish(app, L)
    return L


def _finish(app, L):
    # A part of the area of the columns is listed only while all of it is in view (TRM-A3,
    # TRM-H6); the cards list keeps every card with its inView flag.
    shown = []
    for p in L.parts:
        if p.clip is not None:
            r, c, hh, ww = p.rect
            if not (p.clip[0] <= r and r + hh - 1 <= p.clip[1]):
                continue
        shown.append(p)
    L.shown = shown
    order = []
    for p in L.parts:
        if p.stop or p.key == ("title",):
            order.append((p.key, bool(p.stop)))
    L.order = order
    f = app.focus
    if f is not None and f in L.by_key:
        p = L.by_key[f]
        L.focus_index = L.shown.index(p) if p in L.shown else None
        r, c, hh, ww = p.rect
        for rr in range(r, r + hh):
            if p.clip is not None and not (p.clip[0] <= rr <= p.clip[1]):
                continue
            if not (1 <= rr <= L.h):
                continue
            if f == ("title",):
                continue        # VIS-7: the place title shows no focus mark
            for cc in range(c, min(c + ww, L.w + 1)):
                L.attrs[rr - 1][cc - 1] |= REV
        visible = 1 <= r <= L.h and (p.clip is None or p.clip[0] <= r <= p.clip[1])
        L.cursor = (r, c) if visible else None


# ==========================================================================
# Board
# ==========================================================================
def _board(app, L, st, bottom):
    w = L.w
    L.title = "Board"
    L.put(2, 1, "Board", BOLD)
    L.add(("title",), "place title", "Board", rect=(2, 1, 1, 5))
    if st == "loading":
        top = 4
        cw = w // 5 - 1
        for i in range(3):
            x = 1 + i * (w // 5)
            for r in range(top, top + 9):
                L.put(r, x, PLACEHOLDER * cw, DIM)
            L.add(None, "placeholder", None, rect=(top, x, 9, cw))
        return
    if st == "failed":
        L.text(4, 1, "Couldn't load the board.", w, role="alert", a=BOLD)
        L.alerts.append((("board-failed", app.board_fail_gen), "Couldn't load the board."))
        L.put(5, 1, "[Try again]")
        L.add(("try-again",), "action", "Try again", rect=(5, 1, 1, 11), stop=True)
        return
    _filter_bar(app, L)
    row = 6
    if app.selection:
        row = _selection_bar(app, L, row) + 2
    else:
        row = 7
    board_line = _board_line_kind(app)
    area_bottom = bottom - 1 if board_line else bottom
    _columns(app, L, row, area_bottom)
    if board_line:
        r = bottom
        if board_line == "empty":
            L.text(r, 1, "This board has no cards yet.", w)
        else:
            t = "No cards match these filters."
            L.text(r, 1, t, w)
            x = len(t) + 3
            L.put(r, x, "[Show all cards]")
            L.add(("show-all",), "action", "Show all cards", rect=(r, x, 1, 16), stop=True)


def _filter_bar(app, L):
    w = L.w
    fw = min(50, w - 40)
    text = app.filter_text
    shown = cut("Filter cards: " + text.replace("\n", " "), fw)
    L.put(3, 1, shown)
    L.add(("filter",), "field", "Filter cards", text=text, rect=(3, 1, 1, fw), stop=True)
    f = app.current_filter()
    on = app.filter_on(f)
    if on or text:
        x = fw + 3
        L.put(3, x, "[Clear filters]")
        L.add(("clear-filters",), "action", "Clear filters", rect=(3, x, 1, 15), stop=True)
    count = app.count_line()
    L.text(3, w - len(count) + 1, count, len(count), role="status line", a=DIM)
    # labels
    L.put(4, 1, "Labels:")
    items = []
    for l in app.labels:
        s = "on" if l in f[1] else "off"
        items.append((mark_toggle(s) + l, 0, dict(key=("lf", l), role="toggle", name=l, group="Labels",
                                                   state=s, stop=True)))
    flow(L, 4, 10, w, items)
    L.put(5, 1, "Assignee:")
    items = []
    for p in app.people + [{"id": "none", "name": "Unassigned"}]:
        s = "on" if p["id"] in f[2] else "off"
        items.append((mark_toggle(s) + p["name"], 0, dict(key=("af", p["id"]), role="toggle", name=p["name"],
                                                          group="Assignee", state=s, stop=True)))
    flow(L, 5, 11, w, items)


def _selection_bar(app, L, row):
    w = L.w
    n = len(app.selection)
    t = "%d selected" % n
    L.text(row, 1, t, len(t))
    x = len(t) + 3
    L.put(row, x, "Move selected to:")
    x += len("Move selected to:") + 1
    items = []
    for c in app.columns:
        off = app.col_state.get(c["id"]) != "ok"
        s = "[%s]" % c["name"] + (" (off)" if off else "")
        items.append((s, DIM if off else 0, dict(key=("mv", c["id"]), role="action", name=c["name"],
                                                  group="Move selected to", disabled=off, stop=not off)))
    row = flow(L, row, x, w, items)
    row += 1
    L.put(row, 1, "Label selected:")
    sel = app.selection
    items = []
    for l in app.labels:
        k = sum(1 for x_ in sel if l in app.cards[x_].labels)
        s = "on" if k == len(sel) else ("off" if k == 0 else "mixed")
        items.append((mark_toggle(s) + l, 0, dict(key=("ls", l), role="toggle", name=l, group="Label selected",
                                                   state=s, stop=True)))
    items.append(("[Clear selection]", 0, dict(key=("clear-sel",), role="action", name="Clear selection",
                                               stop=True)))
    row = flow(L, row, 17, w, items)
    return row


def _board_line_kind(app):
    if app.any_column_loading():
        return None
    total = app.total_cards()
    if total == 0:
        return "empty"
    if app.filter_on() and not app.board_visible():
        return "nomatch"
    return None


def _column_height(app, cid):
    st = app.column_view_state(cid)
    if st == "fresh":
        return 3 + 12
    if st == "slow":
        return 3 + 13
    if st == "failed":
        return 3 + 2
    if st in ("empty", "nomatch"):
        return 3 + 1
    return 3 + 4 * len(app.visible(cid))


def _columns(app, L, top, bottom):
    w = L.w
    area_h = bottom - top + 1
    content_h = max([_column_height(app, c) for c in app.column_ids()] + [0])
    max_scroll = max(0, content_h - area_h)
    if app.scroll > max_scroll:
        app.scroll = max_scroll
    if app.scroll < 0:
        app.scroll = 0
    L.area_top = top
    L.area_h = area_h
    clip = (top, bottom)
    sc = app.scroll
    base = w // 5
    extra = w % 5
    x = 1
    stop = app.effective_stop()
    carried = app.carry["card"] if app.carry else None
    for i, col in enumerate(app.columns):
        cid = col["id"]
        cwid = base + (1 if i < extra else 0)
        cw = cwid - 1
        name = col["name"]
        L.columns.append(name)
        vr = lambda crow: top + crow - sc  # noqa: E731
        st = app.column_view_state(cid)
        L.put(vr(0), x, cut(name, cw), BOLD, clip)
        L.add(None, "heading", name, rect=(vr(0), x, 1, min(cw, len(name))), clip=clip, crow=0)
        if st in ("empty", "nomatch", "cards"):
            cnt = app.column_count(cid)
            L.text(vr(1), x, cnt, cw, a=DIM, clip=clip, crow=1)
            lim = col.get("limit")
            if lim is not None:
                lt = "Limit %d" % lim
                lx = x + len(cnt) + 2
                L.text(vr(1), lx, lt, max(1, x + cw - lx), a=DIM, clip=clip, crow=1)
        elif col.get("limit") is not None:
            lt = "Limit %d" % col["limit"]
            L.text(vr(1), x, lt, cw, a=DIM, clip=clip, crow=1)
        if st == "cards":
            nm = "Select all in %s" % name
            s = "[" + cut(nm, cw - 2) + "]"
            L.put(vr(2), x, s, 0, clip)
            L.add(("selall", cid), "action", nm, rect=(vr(2), x, 1, len(s)), stop=True, clip=clip, crow=2)
        crow = 3
        if st in ("fresh", "slow"):
            for _ in range(3):
                for k in range(3):
                    L.put(vr(crow + k), x, PLACEHOLDER * cw, DIM, clip)
                L.add(None, "placeholder", None, rect=(vr(crow), x, 3, cw), clip=clip, crow=crow)
                crow += 4
            if st == "slow":
                L.text(vr(crow), x, "Still loading…", cw, a=DIM, clip=clip, crow=crow)
        elif st == "failed":
            t = "Couldn't load %s." % name
            L.text(vr(crow), x, t, cw, role="alert", a=BOLD, clip=clip, crow=crow)
            L.alerts.append((("col-failed", cid, app.col_fail_gen.get(cid)), t))
            nm = "Retry %s" % name
            s = "[" + cut(nm, cw - 2) + "]"
            L.put(vr(crow + 1), x, s, 0, clip)
            L.add(("retry-col", cid), "action", nm, rect=(vr(crow + 1), x, 1, len(s)), stop=True,
                  clip=clip, crow=crow + 1)
        elif st == "empty":
            L.text(vr(crow), x, "No cards", cw, a=DIM, clip=clip, crow=crow)
        elif st == "nomatch":
            L.text(vr(crow), x, "No matching cards", cw, a=DIM, clip=clip, crow=crow)
        else:
            for cardid in app.visible(cid):
                card = app.cards[cardid]
                sel = cardid in app.selection
                marks = []
                if cardid == carried:
                    marks.append("Moving")
                if app.move_saving[cardid] > 0:
                    marks.append("Saving…")
                r0 = vr(crow)
                line1 = ("[x] " if sel else "[ ] ") + cardid + "".join(" " + m for m in marks)
                L.put(r0, x, cut(line1, cw), 0, clip)
                L.put(r0 + 1, x, cut(card.title, cw), 0, clip)
                bits = []
                if card.labels:
                    bits.append(" ".join(card.labels))
                bits.append(app.person_name(card.assignee) if card.assignee else "Unassigned")
                if card.comments > 0:
                    bits.append(comments_word(card.comments))
                L.put(r0 + 2, x, cut(" · ".join(bits), cw), DIM, clip)
                L.add(("card", cardid), "card", "%s %s" % (cardid, card.title), rect=(r0, x, 3, cw),
                      stop=(cardid == stop), clip=clip, crow=crow)
                in_view = r0 >= top and r0 + 2 <= bottom
                L.cards.append({"id": cardid, "column": name, "selected": sel, "marks": marks,
                                "rect": [r0, x, 3, cw], "inView": in_view})
                crow += 4
        x += cwid


# ==========================================================================
# Card
# ==========================================================================
def _card(app, L, st, bottom):
    cid = app.place().card
    cw = min(CARD_MAX_W, L.w)
    L.put(2, 1, "[← Board]")
    L.add(("uplink",), "up-link", "← Board", rect=(2, 1, 1, 9), stop=True)
    if st == "loading":
        for r0 in (4, 7):
            for r in (r0, r0 + 1):
                L.put(r, 1, PLACEHOLDER * min(40, cw), DIM)
            L.add(None, "placeholder", None, rect=(r0, 1, 2, min(40, cw)))
        return
    if st == "failed":
        L.title = cid
        L.put(3, 1, cut(cid, cw), BOLD)
        L.add(("title",), "place title", cid, rect=(3, 1, 1, min(cw, len(cid))))
        t = "Couldn't load this card."
        L.text(4, 1, t, cw, role="alert", a=BOLD)
        L.alerts.append((("card-failed", app.card_fail_gen), t))
        L.put(5, 1, "[Try again]")
        L.add(("try-again",), "action", "Try again", rect=(5, 1, 1, 11), stop=True)
        return


def _wrap(text, width):
    out = []
    for line in text.split("\n"):
        if line == "":
            out.append("")
            continue
        while len(line) > width:
            cutat = line.rfind(" ", 0, width + 1)
            if cutat <= 0:
                cutat = width
            out.append(line[:cutat])
            line = line[cutat:].lstrip(" ")
        out.append(line)
    return out or [""]


def _field_block(L, r, name, text, cw, key, disabled=False, stop=True):
    """A field: name, then ": ", then its text. Lines of the text go on the next rows."""
    label = name + (" (off)" if disabled else "") + ": "
    lines = text.split("\n")
    first = cut(label + lines[0], cw)
    L.put(r, 1, first, DIM if disabled else 0)
    rows = 1
    for extra in lines[1:]:
        L.put(r + rows, 1, cut("  " + extra, cw))
        rows += 1
    L.add(key, "field", name, text=text, disabled=disabled, stop=stop and not disabled,
          rect=(r, 1, rows, cw))
    return rows


def _card_ready(app, L, cid, cw, skip):
    card = app.cards[cid]
    L.put(2, 1, "[← Board]")
    L.add(("uplink",), "up-link", "← Board", rect=(2, 1, 1, 9), stop=True)
    y = 3
    L.text(y, 1, "%s · %s" % (cid, app.column_name(card.column)), cw, a=DIM)
    y += 1
    # Title region
    te = app.title_edit
    if te is None:
        L.title = card.title
        shown = cut(card.title, cw)
        L.put(y, 1, shown, BOLD)
        L.add(("title",), "place title", card.title, rect=(y, 1, 1, len(shown)))
        y += 1
        L.put(y, 1, "[Edit title]")
        L.add(("edit-title",), "action", "Edit title", rect=(y, 1, 1, 12), stop=True)
        if app.title_saving[cid] > 0:
            L.text(y, 15, "Saving…", 7, role="mark", a=DIM)
        y += 1
    else:
        y += _field_block(L, y, "Title", te["draft"], cw, ("title-field",))
        if te["message"]:
            L.text(y, 1, te["message"], cw, role="alert", a=BOLD)
            L.alerts.append((("title-msg", te["gen"]), te["message"]))
        y += 1
    y += 1
    # Labels
    full = len(card.labels) >= 3
    L.put(y, 1, "Labels:")
    items = []
    for l in app.labels:
        on = l in card.labels
        dis = full and not on
        s = mark_toggle("on" if on else "off") + l + (" (off)" if dis else "")
        items.append((s, DIM if dis else 0, dict(key=("lbl", l), role="toggle", name=l, group="Labels",
                                                  state="on" if on else "off", disabled=dis, stop=not dis)))
    if app.labels_saving[cid] > 0:
        items.append(("Saving…", DIM, dict(role="mark", name="Saving…", text="Saving…")))
    y = flow(L, y, 9, cw, items) + 1
    if full:
        L.text(y, 1, "Label limit reached (3)", cw, a=DIM)
        y += 1
    y += 1
    # Assignee
    L.put(y, 1, "Assignee:")
    items = []
    for p in [{"id": "none", "name": "Unassigned"}] + app.people:
        chosen = (card.assignee is None and p["id"] == "none") or card.assignee == p["id"]
        items.append((mark_choice(chosen) + p["name"], 0,
                      dict(key=("asg", p["id"]), role="choice", name=p["name"], group="Assignee",
                           state="chosen" if chosen else "not chosen", stop=True)))
    if app.assignee_saving[cid] > 0:
        items.append(("Saving…", DIM, dict(role="mark", name="Saving…", text="Saving…")))
    y = flow(L, y, 11, cw, items) + 2
    # Description
    L.put(y, 1, "Description", BOLD)
    L.add(None, "heading", "Description", rect=(y, 1, 1, 11))
    y += 1
    de = app.desc_edit
    if de is None:
        if card.description:
            lines = _wrap(card.description, cw)
            for i, line in enumerate(lines):
                L.put(y + i, 1, line)
            L.add(None, "text", card.description, text=card.description,
                  rect=(y, 1, len(lines), max(1, max(len(x) for x in lines))))
            y += len(lines)
        else:
            L.text(y, 1, "No description", cw, a=DIM)
            y += 1
        L.put(y, 1, "[Edit description]")
        L.add(("edit-desc",), "action", "Edit description", rect=(y, 1, 1, 18), stop=True)
        if app.desc_saving[cid] > 0:
            L.text(y, 21, "Saving…", 7, role="mark", a=DIM)
        y += 1
    else:
        y += _field_block(L, y, "Description", de["draft"], cw, ("desc-field",))
        L.put(y, 1, "[Save]")
        L.add(("desc-save",), "action", "Save", rect=(y, 1, 1, 6), stop=True)
        L.put(y, 9, "[Cancel]")
        L.add(("desc-cancel",), "action", "Cancel", rect=(y, 9, 1, 8), stop=True)
        y += 1
    y += 1
    # Comments
    L.put(y, 1, "Comments", BOLD)
    L.add(None, "heading", "Comments", rect=(y, 1, 1, 8))
    y += 1
    cm = app.comments.get(cid)
    state = cm["state"] if cm else "loading"
    if state == "loading":
        L.put(y, 1, PLACEHOLDER * min(40, cw), DIM)
        L.add(None, "placeholder", None, rect=(y, 1, 1, min(40, cw)))
        y += 1
    elif state == "failed":
        t = "Couldn't load comments."
        L.text(y, 1, t, cw, role="alert", a=BOLD)
        L.alerts.append((("comments-failed", cid, app.comments_fail_gen.get(cid)), t))
        y += 1
        L.put(y, 1, "[Retry]")
        L.add(("retry-comments",), "action", "Retry", rect=(y, 1, 1, 7), stop=True)
        y += 1
    elif not cm["list"]:
        L.text(y, 1, "No comments yet", cw, a=DIM)
        y += 1
    else:
        L.text(y, 1, comments_word(card.comments), cw, a=DIM)
        y += 1
        for com in cm["list"][skip:]:
            who = app.person_name(com["author"])
            head = "%s · %s" % (who, "Sending…" if com["sending"] else fmt_time(com["at"]))
            L.text(y, 1, head, cw, a=DIM)
            y += 1
            lines = _wrap(com["text"], cw)
            for i, line in enumerate(lines):
                L.put(y + i, 1, line)
            L.add(None, "text", com["text"], text=com["text"],
                  rect=(y, 1, len(lines), max(1, max(len(x) for x in lines))))
            y += len(lines)
    enabled = app.comment_enabled(cid)
    y += _field_block(L, y, "Add a comment", app.comment_text, cw, ("comment-field",), disabled=not enabled)
    add_ok = enabled and app.comment_text.strip() != ""
    s = "[Add comment]" + ("" if add_ok else " (off)")
    L.put(y, 1, s, 0 if add_ok else DIM)
    L.add(("add-comment",), "action", "Add comment", disabled=not add_ok, stop=add_ok, rect=(y, 1, 1, len(s)))
    y += 1
    if app.comment_message:
        L.text(y, 1, app.comment_message[0], cw, role="alert", a=BOLD)
        L.alerts.append((("comment-msg", app.comment_message[1]), app.comment_message[0]))
        y += 1
    y += 1
    L.put(y, 1, "[Delete card]", BOLD)
    L.add(("delete-card",), "action", "Delete card", rect=(y, 1, 1, 13), stop=True)
    return y


# ==========================================================================
# Missing
# ==========================================================================
def _missing(app, L, st):
    cw = min(CARD_MAX_W, L.w)
    if st == "page":
        title = "Page not found"
        text = "The address may be mistyped or out of date."
    else:
        title = "Card not found"
        text = "There is no card %s on this board." % app.place().card
    L.title = title
    L.put(2, 1, title, BOLD)
    L.add(("title",), "place title", title, rect=(2, 1, 1, len(title)))
    L.text(3, 1, text, cw, a=DIM)
    L.put(4, 1, "[Go to the board]")
    L.add(("board-link",), "link", "Go to the board", rect=(4, 1, 1, 17), stop=True)


# ==========================================================================
# Notice and address prompt
# ==========================================================================
def _notice(app, L):
    w, h = L.w, L.h
    nrow = h - 2 if app.prompt is not None else h - 1
    n = app.notice
    if n is not None:
        _notice_row(L, n, nrow)
    if app.prompt is not None:
        L.put(h - 1, 1, " " * w)
        _field_block_row(L, h - 1, "Address", app.prompt, w)


def _notice_row(L, n, nrow):
    w = L.w
    L.put(nrow, 1, " " * w)
    acts = []
    if n.action:
        acts.append((("notice-action",), n.action))
    if n.kind == "error":
        acts.append((("notice-dismiss",), "Dismiss"))
    room = w - sum(len(a[1]) + 4 for a in acts)
    prefix = "i " if n.kind == "info" else "! "
    shown = cut(prefix + n.text, room)
    L.put(nrow, 1, shown, BOLD if n.kind == "error" else 0)
    L.add(None, "notice", n.text, text=n.text, rect=(nrow, 1, 1, len(shown)))
    x = len(shown) + 3
    for key, name in acts:
        s = "[%s]" % name
        L.put(nrow, x, s)
        L.add(key, "action", name, group="Notice", rect=(nrow, x, 1, len(s)), stop=True)
        x += len(s) + 2


def _field_block_row(L, r, name, text, w):
    s = cut(name + ": " + text, w)
    L.put(r, 1, s)
    L.add(("prompt",), "field", name, text=text, rect=(r, 1, 1, max(len(s), len(name) + 2)))
