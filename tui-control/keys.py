"""Key bytes (TRM-9) to key names used by model.App.handle_key."""

SEQUENCES = {
    b"\x1b[Z": "S-Tab",
    b"\x1b[3~": "Delete",
    b"\x1b[A": "Up", b"\x1b[B": "Down", b"\x1b[C": "Right", b"\x1b[D": "Left",
    b"\x1b[H": "Home", b"\x1b[F": "End",
    b"\x1bOA": "Up", b"\x1bOB": "Down", b"\x1bOC": "Right", b"\x1bOD": "Left",
    b"\x1bOH": "Home", b"\x1bOF": "End", b"\x1b[1~": "Home", b"\x1b[4~": "End",
}
SINGLE = {
    0x0D: "Enter", 0x0A: "Enter", 0x09: "Tab", 0x1B: "Esc", 0x20: "Space",
    0x7F: "Backspace", 0x08: "Backspace",
    0x02: "C-b", 0x06: "C-f", 0x07: "C-g", 0x12: "C-r", 0x13: "C-s", 0x15: "C-u", 0x1A: "C-z",
    0x11: "C-q",
}


def decode(data, one_key=False):
    """Split bytes into key names. With one_key the whole read is one key
    (TRM-H3: one read from the terminal holds exactly one key)."""
    if one_key and data in SEQUENCES:
        return [SEQUENCES[data]]
    keys = []
    i = 0
    n = len(data)
    while i < n:
        b = data[i]
        if b == 0x1B:
            if i + 1 == n:
                keys.append("Esc")
                i += 1
                continue
            matched = False
            for seq, name in SEQUENCES.items():
                if data.startswith(seq, i):
                    keys.append(name)
                    i += len(seq)
                    matched = True
                    break
            if matched:
                continue
            if data[i + 1:i + 2] in (b"[", b"O"):
                # unknown CSI / SS3 sequence: skip it
                j = i + 2
                while j < n and not (0x40 <= data[j] <= 0x7E):
                    j += 1
                i = j + 1
                continue
            keys.append("Esc")
            i += 1
            continue
        if b in SINGLE:
            keys.append(SINGLE[b])
            i += 1
            continue
        if b < 0x20:
            i += 1
            continue
        # UTF-8 character
        length = 1
        if b >= 0xF0:
            length = 4
        elif b >= 0xE0:
            length = 3
        elif b >= 0xC0:
            length = 2
        ch = data[i:i + length].decode("utf-8", "ignore")
        if ch:
            keys.append(ch)
        i += length
    return keys
