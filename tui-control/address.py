"""Addresses of the terminal build (TRM-2)."""
import unicodedata
from urllib.parse import quote, unquote


def person_key(name):
    """"Chloé Martin" -> "chloe": first name, lower case, no accent."""
    first = name.split()[0]
    nfkd = unicodedata.normalize("NFKD", first)
    return "".join(ch for ch in nfkd if not unicodedata.combining(ch)).lower()


class Address:
    """kind: "board" | "card" | "missing".  For board: q, labels, who.
    For card: card id (upper case).  text: the canonical address."""

    def __init__(self, kind, text, q="", labels=(), who=(), card=None):
        self.kind = kind
        self.text = text
        self.q = q
        self.labels = list(labels)
        self.who = list(who)
        self.card = card

    def __repr__(self):
        return "Address(%r)" % self.text


def _q_encode(q):
    return "+".join(quote(w, safe=",:;!*'()@$/") for w in q.split(" "))


def board_address(q, labels, who, all_labels, people_keys):
    q = " ".join(q.split())
    parts = []
    if q:
        parts.append("q=" + _q_encode(q))
    ls = [l for l in all_labels if l in labels]
    if ls:
        parts.append("labels=" + ",".join(ls))
    ws = [p for p in list(people_keys) + ["none"] if p in who]
    if ws:
        parts.append("who=" + ",".join(ws))
    return "board" + ("?" + "&".join(parts) if parts else "")


def parse(text, all_labels, people_keys):
    """Parse an address. all_labels and people_keys name what exists."""
    raw = text.strip()
    if raw == "":
        return Address("board", "board")
    if raw.startswith("card/"):
        cid = raw[5:].split("?", 1)[0]
        if cid and "/" not in cid:
            cid = cid.upper()
            return Address("card", "card/" + cid, card=cid)
        return Address("missing", raw)
    path, sep, query = raw.partition("?")
    if path != "board":
        return Address("missing", raw)
    found = {}
    if query:
        for piece in query.split("&"):
            if not piece:
                continue
            name, _, value = piece.partition("=")
            if name in ("q", "labels", "who"):
                found[name] = value
    q = " ".join(unquote(found.get("q", "").replace("+", " ")).split())
    labels = [l for l in found.get("labels", "").split(",") if l in all_labels]
    valid_who = list(people_keys) + ["none"]
    who = [w for w in found.get("who", "").split(",") if w in valid_who]
    canon = board_address(q, labels, who, all_labels, people_keys)
    return Address("board", canon, q=q, labels=labels, who=who)
