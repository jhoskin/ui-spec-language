"""TRM-H6 check: what the dump tells is painted inside each rect."""

MARKS = {("toggle", "on"): "[x] ", ("toggle", "off"): "[ ] ", ("toggle", "mixed"): "[-] ",
         ("choice", "chosen"): "(o) ", ("choice", "not chosen"): "( ) "}


def rect_rows(lines, rect):
    r, c, h, w = rect
    return [lines[y - 1][c - 1:c - 1 + w] for y in range(r, r + h)]


def shown(name, painted):
    """True if name is painted whole, or cut as TRM-A4 allows."""
    flat = " ".join(row.rstrip() for row in painted)
    squashed = " ".join(flat.split())
    want = " ".join(name.split())
    if want in squashed:
        return True
    for row in painted:
        if "…" in row:
            head = row.split("…")[0]
            for start in range(len(head)):
                frag = head[start:]
                if frag and len(frag) >= 1 and want.startswith(frag) and (start == 0 or head[start - 1] in "[ :"):
                    return True
    return False


def check_frame(lines, dump, width, height):
    """Return a list of problems (empty if the dump matches the grid)."""
    problems = []
    for i, p in enumerate(dump["parts"]):
        r, c, h, w = p["rect"]
        if r < 1 or c < 1 or h < 1 or w < 1 or r + h - 1 > height or c + w - 1 > width:
            problems.append("part %d %r: rect %r outside the grid" % (i, p["name"], p["rect"]))
            continue
        painted = rect_rows(lines, p["rect"])
        if p["role"] == "card":
            cid = p["name"].split()[0]
            if not any(cid in row for row in painted) and h == 3:
                problems.append("card %s not painted in %r" % (cid, p["rect"]))
            continue
        if p["role"] == "placeholder":
            if not all(set(row) <= {"░"} for row in painted):
                problems.append("placeholder %d not a run of ░: %r" % (i, painted))
            continue
        if p["name"] and not shown(p["name"], painted):
            problems.append("part %d %s %r not painted in %r: %r" % (i, p["role"], p["name"], p["rect"], painted))
        if p["role"] == "field" and p["text"]:
            first = p["text"].split("\n")[0]
            if first and not shown(first, painted):
                problems.append("field %r text %r not painted" % (p["name"], first))
        mark = MARKS.get((p["role"], p["state"]))
        if mark and mark not in painted[0]:
            problems.append("part %r lacks state mark %r: %r" % (p["name"], mark, painted[0]))
        if p["disabled"] and " (off)" not in "".join(painted) and "…" not in "".join(painted):
            problems.append("disabled part %r lacks (off)" % p["name"])
    for card in dump["cards"]:
        mark = "[x] " if card["selected"] else "[ ] "
        painted = rect_rows(lines, card["rect"])
        if card["inView"] and mark + card["id"] not in painted[0]:
            problems.append("card %s selection mark wrong: %r" % (card["id"], painted[0]))
        for m in card["marks"]:
            if card["inView"] and m not in painted[0]:
                problems.append("card %s mark %r not painted" % (card["id"], m))
    n = dump["notice"]
    if n:
        start = "i " if n["kind"] == "info" else "! "
        if not lines[height - 2].startswith(start):
            problems.append("notice row does not start with %r" % start)
    if dump["focus"] is not None and not (0 <= dump["focus"] < len(dump["parts"])):
        problems.append("focus index out of range")
    return problems
