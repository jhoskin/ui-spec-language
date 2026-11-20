"""A very small terminal build that follows the harness of spec/modality/terminal.md.

It is not Slate. It exists to test the terminal adapter: the pseudo-terminal, the frame
lines, the rebuild of the grid and the check of the semantic dump against the grid.
It has a place title, one field, one toggle and a text that changes after 500 ms.
"""
import json
import os
import select
import sys
import termios
import tty

lie = "--lie" in sys.argv
state = {"focus": None, "text": "", "on": False, "clock": 0, "due": None, "late": "waiting", "n": 0}
out = sys.stdout


def parts():
    return [
        {"role": "place title", "name": "Board", "group": None, "state": None, "disabled": False, "rect": [3, 1, 1, 5]},
        {"role": "field", "name": "Filter cards", "group": None, "state": None, "disabled": False, "text": state["text"], "rect": [5, 1, 1, 60]},
        {"role": "toggle", "name": "bug", "group": "Labels", "state": "on" if state["on"] else "off", "disabled": False, "rect": [6, 1, 1, 7]},
        {"role": "text", "name": state["late"], "group": None, "state": None, "disabled": False, "text": state["late"], "rect": [8, 1, 1, 40]},
    ]


def paint():
    w = out.write
    w("\x1b[2J\x1b[1;1H[Slate]")
    w("\x1b[3;1H\x1b[1mBoard\x1b[0m")
    w(f"\x1b[5;1HFilter cards: {state['text']}")
    mark = "[x]" if state["on"] and not lie else "[ ]"
    w(f"\x1b[6;1H{mark} bug")
    w(f"\x1b[8;1H{state['late']}")
    if state["focus"] is None:
        w("\x1b[?25l")
    else:
        r, c, _, _ = parts()[state["focus"]]["rect"]
        w(f"\x1b[{r};{c}H\x1b[?25h")
    out.flush()


def frame():
    state["n"] += 1
    os.write(4, (json.dumps({"frame": state["n"]}) + "\n").encode())


def on_key(data):
    f = state["focus"]
    if data == b"\t":
        state["focus"] = 1 if f in (None, 2) else 2
    elif data == b"\x15" and f == 1:
        state["text"] = ""
    elif data in (b"\r", b" ") and f == 2:
        state["on"] = not state["on"]
        state["due"] = state["clock"] + 500
    elif f == 1 and len(data.decode()) == 1 and data >= b" ":
        state["text"] += data.decode()


def main():
    old = termios.tcgetattr(0)
    tty.setraw(0)
    out.write("\x1b[?1049h")
    paint()
    frame()
    buf = b""
    try:
        while True:
            ready, _, _ = select.select([0, 3], [], [])
            if 0 in ready:
                on_key(os.read(0, 64))
                paint()
                frame()
            if 3 in ready:
                buf += os.read(3, 65536)
                while b"\n" in buf:
                    line, _, buf = buf.partition(b"\n")
                    cmd = json.loads(line)
                    if "advance" in cmd:
                        state["clock"] += cmd["advance"]
                        if state["due"] is not None and state["clock"] >= state["due"]:
                            state["late"] = "done"
                            state["due"] = None
                        paint()
                        frame()
                    elif "dump" in cmd:
                        d = {"title": "Board", "address": "board", "depth": 1, "focus": state["focus"], "scrollTop": True,
                             "parts": parts(), "columns": [], "cards": [], "notice": None, "announcements": [], "requests": []}
                        os.write(4, (json.dumps(d) + "\n").encode())
                    elif "quit" in cmd:
                        return
    finally:
        out.write("\x1b[?1049l\x1b[?25h")
        out.flush()
        termios.tcsetattr(0, termios.TCSADRAIN, old)


main()
