"""Addresses of the terminal sheet (TRM-2, DAT-16, NAV-1, MIS-1)."""


def norm_ws(s):
    """Written form of a filter text or a title: ends trimmed, runs of white space are one space."""
    return " ".join(s.split())


class Addr:
    __slots__ = ("kind", "q", "labels", "who", "card", "raw")

    def __init__(self, kind, q="", labels=(), who=(), card=None, raw=""):
        self.kind = kind          # "board" | "card" | "missing"
        self.q = q
        self.labels = tuple(labels)
        self.who = tuple(who)
        self.card = card
        self.raw = raw

    def filter(self):
        return (self.q, self.labels, self.who)

    def __repr__(self):
        return "Addr(%r, q=%r, labels=%r, who=%r, card=%r, raw=%r)" % (
            self.kind, self.q, self.labels, self.who, self.card, self.raw)


_HEX = "0123456789abcdefABCDEF"


def _pct_decode(s):
    """Decode "+" and percent codes. A bad percent code raises ValueError."""
    s = s.replace("+", " ")
    out = bytearray()
    i = 0
    while i < len(s):
        ch = s[i]
        if ch == "%":
            h = s[i + 1:i + 3]
            if len(h) != 2 or h[0] not in _HEX or h[1] not in _HEX:
                raise ValueError("bad percent code")
            out.append(int(h, 16))
            i += 3
        else:
            out.extend(ch.encode("utf-8"))
            i += 1
    return out.decode("utf-8")


def _q_encode(s):
    out = []
    for ch in s:
        if ch == " ":
            out.append("+")
        elif ch in "%&+=#?" or ord(ch) < 0x20 or ord(ch) == 0x7F:
            out.append("".join("%%%02X" % b for b in ch.encode("utf-8")))
        else:
            out.append(ch)
    return "".join(out)


def _dedupe(seq):
    seen = []
    for x in seq:
        if x and x not in seen:
            seen.append(x)
    return seen


def parse(s):
    if s == "":
        return Addr("board", raw=s)
    if s == "board" or s.startswith("board?"):
        query = s[len("board?"):] if s.startswith("board?") else ""
        parts = {}
        for piece in query.split("&"):
            if not piece:
                continue
            name, _, val = piece.partition("=")
            try:
                val = _pct_decode(val)
            except (ValueError, UnicodeDecodeError):
                continue
            if name in ("q", "labels", "who"):
                parts[name] = val          # the last one counts
        q = norm_ws(parts.get("q", ""))
        labels = _dedupe(parts.get("labels", "").split(","))
        who = _dedupe(parts.get("who", "").split(","))
        return Addr("board", q, labels, who, raw=s)
    if s.startswith("card/"):
        ident = s[len("card/"):].split("?", 1)[0]
        if ident and "/" not in ident and not any(c.isspace() for c in ident):
            return Addr("card", card=ident.upper(), raw=s)
    return Addr("missing", raw=s)


def board_written(q, labels, who):
    parts = []
    if q:
        parts.append("q=" + _q_encode(q))
    if labels:
        parts.append("labels=" + ",".join(labels))
    if who:
        parts.append("who=" + ",".join(who))
    return "board" + ("?" + "&".join(parts) if parts else "")


def normalize_filter(labels, who, board_labels=None, people_ids=None):
    """DAT-16: labels in board order, people in their order then "none". Values that
    name nothing are dropped, but only when the board data is known (NAV-1)."""
    if board_labels is None:
        return tuple(_dedupe(labels)), tuple(_dedupe(who))
    labels = tuple(l for l in board_labels if l in labels)
    order = list(people_ids) + ["none"]
    who = tuple(p for p in order if p in who)
    return labels, who


def written(addr, board_labels=None, people_ids=None):
    if addr.kind == "board":
        labels, who = normalize_filter(addr.labels, addr.who, board_labels, people_ids)
        return board_written(addr.q, labels, who)
    if addr.kind == "card":
        return "card/" + addr.card
    return addr.raw
