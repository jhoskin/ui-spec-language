"""Layout of the face on a grid of characters (TRM-1, TRM-4, TRM-10 to TRM-14).

render(app, width, height) returns a Frame: the grid (characters and
attributes), the parts with their rects, the card items, the cursor and the
semantic dump (TRM-H5). It has no terminal code; slate.py paints the grid.
"""
import textwrap

BOLD, DIM, UNDER, REV = 1, 2, 4, 8
MIN_W, MIN_H = 112, 30
TOO_SMALL = "Slate needs 112 columns and 30 rows."
CARD_MAX_W = 80


def cut(s, w):
    """TRM-A4: a text that does not fit is cut; its last shown character is "…"."""
    s = s.replace("\n", " ")
    if w <= 0:
        return ""
    if len(s) <= w:
        return s
    return s[:w - 1] + "…"


def wrap(s, w):
    lines = []
    for para in s.split("\n"):
        lines += textwrap.wrap(para, w) or [""]
    return lines or [""]


def label(it):
    role = it.role
    if role == "toggle":
        s = {"on": "[x] ", "mixed": "[-] "}.get(it.state, "[ ] ") + it.name
    elif role == "choice":
        s = ("(o) " if it.state == "chosen" else "( ) ") + it.name
    elif role in ("action", "link", "up-link"):
        s = "[" + it.name + "]"
    elif role == "field":
        s = it.name
    else:
        s = it.name
    if it.disabled:
        s += " (off)"
    if role == "field":
        s += ": " + (it.text or "")
    return s


def attr_of(it):
    a = 0
    if it.role in ("place title", "heading", "alert"):
        a |= BOLD
    if it.quiet or it.role in ("placeholder", "mark") or it.disabled:
        a |= DIM
    return a


class Canvas:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.chars = [[" "] * w for _ in range(h)]
        self.attrs = [[0] * w for _ in range(h)]

    def put(self, row, col, s, attr=0):
        if row < 1 or row > self.h:
            return
        for i, ch in enumerate(s):
            c = col + i
            if 1 <= c <= self.w:
                self.chars[row - 1][c - 1] = ch
                self.attrs[row - 1][c - 1] = attr

    def add_attr(self, rect, attr):
        r, c, h, w = rect
        for y in range(r, r + h):
            for x in range(c, c + w):
                if 1 <= y <= self.h and 1 <= x <= self.w:
                    self.attrs[y - 1][x - 1] |= attr

    def lines(self):
        return ["".join(r) for r in self.chars]


class Frame:
    def __init__(self, canvas):
        self.canvas = canvas
        self.parts = []
        self.cards = []
        self.cursor = None
        self.focus_index = None
        self.dump = None

    def text(self):
        return "\n".join(self.canvas.lines())


class Renderer:
    def __init__(self, app, w, h):
        self.app = app
        self.w, self.h = w, h
        self.cv = Canvas(w, h)
        self.frame = Frame(self.cv)
        self.items = app.semantic()
        self.limit_row = h - 2  # last row a place can use

    # ---- painting helpers --------------------------------------------------
    def part(self, it, rect, painted=None, attr=None, paint=True):
        r, c, hh, ww = rect
        if paint and painted is not None:
            self.cv.put(r, c, painted, attr_of(it) if attr is None else attr)
        p = {"role": it.role, "name": it.name, "group": it.group, "state": it.state,
             "disabled": bool(it.disabled),
             "text": it.text if it.role in ("field", "text", "status line") else None,
             "rect": [r, c, hh, ww], "key": it.key}
        self.frame.parts.append(p)
        return p

    def single(self, it, row, col, width, fixed_width=False):
        s = cut(label(it), width)
        w = width if fixed_width else len(s)
        if row > self.limit_row and it.slot != "notice":
            return row + 1
        self.part(it, [row, col, 1, max(1, w)], s)
        return row + 1

    def flow(self, row, col, width, seq, gap=1):
        """Lay out items left to right; wrap to a new row when one does not fit.
        seq holds Items, ("deco", text) and ("gap", n)."""
        x = col
        maxx = col + width - 1
        extra = 0
        for el in seq:
            if isinstance(el, tuple) and el[0] == "gap":
                extra = el[1]
                continue
            s = el[1] if isinstance(el, tuple) else label(el)
            g = (gap + extra) if x > col else 0
            extra = 0
            if x > col and x + g + len(s) - 1 > maxx:
                row += 1
                x = col
                g = 0
            x += g
            s2 = cut(s, maxx - x + 1)
            if isinstance(el, tuple):
                if row <= self.limit_row:
                    self.cv.put(row, x, s2, DIM)
            elif row <= self.limit_row or el.slot in ("notice", "line"):
                self.part(el, [row, x, 1, max(1, len(s2))], s2)
            x += len(s2)
        return row + 1

    def multiline(self, it, row, col, width):
        prefix = label(it)[:-len(it.text or "")] if it.text else label(it)
        lines = (prefix + (it.text or "")).split("\n")
        shown = []
        for i, ln in enumerate(lines):
            if row + i > self.limit_row:
                break
            s = cut(ln if i == 0 else " " * len(prefix) + ln, width)
            self.cv.put(row + i, col, s, attr_of(it))
            shown.append(s)
        if shown:
            self.part(it, [row, col, len(shown), width], paint=False)
        return row + max(1, len(lines))

    def wrapped(self, it, row, col, width):
        lines = wrap(it.name, width)
        n = 0
        for i, ln in enumerate(lines):
            if row + i > self.limit_row:
                break
            self.cv.put(row + i, col, ln, attr_of(it))
            n += 1
        if n:
            self.part(it, [row, col, n, max(len(l) for l in lines[:n]) or 1], paint=False)
        return row + len(lines)

    def by_slot(self, *slots):
        return [it for it in self.items if it.slot in slots]

    def one(self, slot):
        xs = self.by_slot(slot)
        return xs[0] if xs else None

    # ---- frame ---------------------------------------------------------------
    def render(self):
        app = self.app
        self.location_line()
        if app.place == "board":
            self.board()
        elif app.place == "card":
            self.card()
        else:
            self.missing()
        self.notice_row()
        if app.announcements:
            self.cv.put(self.h, 1, cut(app.announcements[-1], self.w), DIM)
        self.apply_focus()
        return self.frame

    def location_line(self):
        app = self.app
        self.single(self.items[0], 1, 1, 7)
        right = "%s  %d/%d" % (app.entry.address, app.pos + 1, len(app.history))
        right = cut(right, self.w - 9)
        self.cv.put(1, self.w - len(right) + 1, right, DIM)

    def notice_row(self):
        row = self.h - 1
        items = self.by_slot("notice")
        if not items:
            return
        if items[0].role == "field":
            self.single(items[0], row, 1, self.w, fixed_width=True)
            return
        n = items[0]
        s = cut(("i " if n.kind == "info" else "! ") + n.name, self.w - 30)
        self.part(n, [row, 1, 1, len(s)], s, attr=BOLD if n.kind == "error" else 0)
        x = len(s) + 3
        for a in items[1:]:
            t = label(a)
            self.part(a, [row, x, 1, len(t)], t)
            x += len(t) + 2

    def apply_focus(self):
        app = self.app
        if app.focus is None:
            return
        for i, p in enumerate(self.frame.parts):
            if p["key"] == app.focus:
                self.frame.focus_index = i
                self.cv.add_attr(p["rect"], REV)
                self.frame.cursor = (p["rect"][0], p["rect"][1])
                return

    # ---- board -----------------------------------------------------------------
    def col_geom(self, i):
        cw = self.w // 5
        x = 1 + i * cw
        iw = cw - 1 if i < 4 else self.w - x
        return x, iw

    def board(self):
        app = self.app
        self.single(self.one("title"), 2, 1, self.w)
        state = app.board_state()
        if state == "loading":
            for it in self.by_slot("bph"):
                x, iw = self.col_geom(it.index)
                for y in range(4, 13):
                    self.cv.put(y, x, "░" * iw, DIM)
                self.part(it, [4, x, 9, iw], paint=False)
            return
        if state == "failed":
            row = 4
            for it in self.by_slot("body"):
                row = self.single(it, row, 1, self.w)
            return
        field = self.one("f-field")
        self.single(field, 3, 1, min(60, self.w), fixed_width=True)
        row = self.flow(4, 1, self.w, [("deco", "Labels:")] + self.by_slot("f-labels"))
        row = self.flow(row, 1, self.w, [("deco", "Assignee:")] + self.by_slot("f-who"))
        row = self.flow(row, 1, self.w, self.by_slot("f-last"), gap=2)
        if app.selection:
            sm = self.by_slot("s-move")
            row = self.flow(row, 1, self.w, [sm[0], ("gap", 2), ("deco", "Move selected to:")] + sm[1:])
            sl = self.by_slot("s-label")
            row = self.flow(row, 1, self.w, [("deco", "Label selected:")] + sl[:-1] + [("gap", 2), sl[-1]])
        row += 1
        self.columns(row)
        line = self.by_slot("line")
        if line:
            self.flow(self.h - 2, 1, self.w, line, gap=2)

    def column_blocks(self, cid, iw):
        blocks = []  # (y, h, item, lines)
        y = 0
        for it in self.items:
            if it.slot != "c-body" or it.col != cid:
                continue
            k = it.kind
            if k == "ph":
                blocks.append((y, 3, it, ["░" * iw] * 3))
                y += 4
            elif k == "card":
                blocks.append((y, 3, it, self.card_lines(it.card, iw)))
                y += 4
            elif k == "alert":
                lines = wrap(it.name, iw)
                blocks.append((y, len(lines), it, lines))
                y += len(lines)
            else:
                s = cut(label(it), iw)
                blocks.append((y, 1, it, [s]))
                y += 1
        return blocks

    def card_lines(self, cid, iw):
        app = self.app
        c = app.cards[cid]
        sel = "[x] " if cid in app.selection else "[ ] "
        left = sel + cid
        marks = " ".join(app.card_marks(cid))
        if marks:
            pad = iw - len(left) - len(marks)
            l1 = left + " " * max(1, pad) + marks
        else:
            l1 = left
        meta = []
        if c["labels"]:
            meta.append(" ".join(c["labels"]))
        meta.append(app.person_name(c["assignee"]) if c["assignee"] else "Unassigned")
        if c.get("comments"):
            from model import comment_count
            meta.append(comment_count(c["comments"]))
        return [cut(l1, iw), cut(c["title"], iw), cut(" · ".join(meta), iw)]

    def columns(self, top):
        app = self.app
        body_top = top + 3
        body_h = max(1, self.h - 2 - body_top)
        ids = app.column_ids()
        blocks = {}
        content_h = 0
        for i, cid in enumerate(ids):
            x, iw = self.col_geom(i)
            blocks[cid] = self.column_blocks(cid, iw)
            if blocks[cid]:
                b = blocks[cid][-1]
                content_h = max(content_h, b[0] + b[1])
        # scroll: keep the focused body part in view, clamp to the content
        s = app.scroll
        for cid in ids:
            for (y, hh, it, _) in blocks[cid]:
                if it.key and it.key == app.focus:
                    if y < s:
                        s = y
                    elif y + hh > s + body_h:
                        s = y + hh - body_h
        s = max(0, min(s, max(0, content_h - body_h)))
        app.scroll = s
        self.body = (body_top, body_h)
        for i, cid in enumerate(ids):
            x, iw = self.col_geom(i)
            col_items = [it for it in self.items if it.col == cid and it.slot != "c-body"]
            for it in col_items:
                if it.slot == "column":
                    self.part(it, [top, x, 3 + body_h, iw], paint=False)
                elif it.slot == "c-head":
                    cnt = next((c for c in col_items if c.slot == "c-count"), None)
                    room = iw - (len(cnt.name) + 1 if cnt else 0)
                    self.single(it, top, x, room)
                elif it.slot == "c-count":
                    self.part(it, [top, x + iw - len(it.name), 1, len(it.name)], it.name)
                elif it.slot == "c-limit":
                    self.single(it, top + 1, x, iw)
                elif it.slot == "c-select":
                    self.single(it, top + 2, x, iw)
            for (y, hh, it, lines) in blocks[cid]:
                first = max(y, s)
                last = min(y + hh, s + body_h)
                if first >= last:
                    continue
                for cy in range(first, last):
                    row = body_top + cy - s
                    a = attr_of(it)
                    if it.kind == "card":
                        a = DIM if cy - y in (0, 2) else 0
                    self.cv.put(row, x, lines[cy - y], a)
                rect = [body_top + first - s, x, last - first, iw if it.kind in ("card", "ph") else
                        max(len(l) for l in lines[first - y:last - y]) or 1]
                self.part(it, rect, paint=False)
                if it.kind == "card":
                    self.frame.cards.append({
                        "id": it.card, "column": app.column_name(cid),
                        "selected": it.card in app.selection, "marks": app.card_marks(it.card),
                        "rect": rect, "inView": last - first == 3})

    # ---- card ------------------------------------------------------------------
    def card(self):
        app = self.app
        cw = min(CARD_MAX_W, self.w)
        st = app.cv["status"]
        self.single(self.one("uplink"), 2, 1, cw)
        if st == "loading":
            for it in self.by_slot("cph"):
                r = 4 + 4 * it.index
                pw = min(60, cw)
                for y in range(r, r + 3):
                    self.cv.put(y, 1, "░" * pw, DIM)
                self.part(it, [r, 1, 3, pw], paint=False)
            return
        if st == "failed":
            self.single(self.one("title"), 3, 1, cw)
            row = 5
            for it in self.by_slot("body"):
                row = self.single(it, row, 1, cw)
            return
        self.single(self.one("meta"), 3, 1, cw)
        if self.one("title-field"):
            self.single(self.one("title-field"), 4, 1, cw, fixed_width=True)
            if self.one("title-msg"):
                self.single(self.one("title-msg"), 5, 1, cw)
        else:
            self.single(self.one("title"), 4, 1, cw)
            self.flow(5, 1, cw, self.by_slot("title-actions"), gap=2)
        row = 7
        row = self.flow(row, 1, cw, [("deco", "Labels:")] + self.by_slot("labels")) + 1
        row = self.flow(row, 1, cw, [("deco", "Assignee:")] + self.by_slot("assignee")) + 1
        row = self.single(self.one("desc-head"), row, 1, cw)
        if self.one("desc-field"):
            row = self.multiline(self.one("desc-field"), row, 1, cw)
        else:
            it = self.one("desc-text")
            row = self.wrapped(it, row, 1, cw) if it.wrap else self.single(it, row, 1, cw)
        row = self.flow(row, 1, cw, self.by_slot("desc-actions"), gap=2) + 1
        row = self.single(self.one("com-head"), row, 1, cw)
        ph = self.one("com-ph")
        if ph:
            if row <= self.limit_row:
                self.cv.put(row, 1, "░" * min(40, cw), DIM)
                self.part(ph, [row, 1, 1, min(40, cw)], paint=False)
            row += 1
        for slot in ("com-failed", "com-retry", "com-none", "com-count"):
            if self.one(slot):
                row = self.single(self.one(slot), row, 1, cw)
        metas = self.by_slot("com-meta")
        texts = self.by_slot("com-text")
        for t in texts:
            seq = []
            for m in metas:
                if m.row_id == t.row_id:
                    if seq:
                        seq.append(("deco", "·"))
                    seq.append(m)
            row = self.flow(row, 1, cw, seq)
            row = self.wrapped(t, row, 1, cw)
        row = self.multiline(self.one("com-field"), row, 1, cw)
        row = self.single(self.one("com-add"), row, 1, cw)
        if self.one("com-msg"):
            row = self.single(self.one("com-msg"), row, 1, cw)
        row += 1
        self.single(self.one("delete"), row, 1, cw)

    # ---- missing ---------------------------------------------------------------
    def missing(self):
        cw = min(CARD_MAX_W, self.w)
        self.single(self.one("title"), 2, 1, cw)
        row = 3
        for it in self.by_slot("body"):
            row = self.single(it, row, 1, cw)


def render(app, w, h):
    if w < MIN_W or h < MIN_H:
        cv = Canvas(w, h)
        cv.put(1, 1, TOO_SMALL)
        fr = Frame(cv)
        fr.parts.append({"role": "text", "name": TOO_SMALL, "group": None, "state": None, "disabled": False,
                         "text": TOO_SMALL, "rect": [1, 1, 1, min(w, len(TOO_SMALL))], "key": None})
        fr.dump = make_dump(app, fr, too_small=True)
        return fr
    fr = Renderer(app, w, h).render()
    fr.dump = make_dump(app, fr)
    return fr


def make_dump(app, fr, too_small=False):
    notice = None
    if app.notice and app.prompt is None and not too_small:
        notice = {"kind": app.notice["kind"], "text": app.notice["text"], "action": app.notice["action"]}
    return {
        "title": None if too_small else app.title_text(),
        "address": app.entry.address,
        "depth": len(app.history),
        "focus": fr.focus_index,
        "scrollTop": app.scroll == 0 if app.place == "board" else True,
        "parts": [{k: v for k, v in p.items() if k != "key"} for p in fr.parts],
        "columns": [] if too_small or app.place != "board" or app.board_state() != "ready"
        else [app.column_name(c) for c in app.column_ids()],
        "cards": fr.cards,
        "notice": notice,
        "announcements": list(app.announcements),
        "requests": [dict(r) for r in app.service.log],
    }
