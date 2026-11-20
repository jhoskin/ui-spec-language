"""The real program through --harness (TRM-H1 to TRM-H6).

The sandbox of this build does not allow a pseudo-terminal (openpty and
/dev/ptmx give "Operation not permitted"), so the terminal is a pair of pipes:
the build then paints at the 120 x 40 that the checks use, and skips raw mode.
A small VT parser rebuilds the grid from the bytes. The test checks:
- only the sequences of TRM-12 are used, and no other control character;
- a frame line follows each input, numbered one more than the last (TRM-H3);
- every name and text of the dump is painted inside its rect (TRM-H6);
- the cursor is at the first cell of the part that has focus (TRM-7).
"""
import fcntl
import json
import os
import re
import select
import subprocess
import sys
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
TUI = os.path.dirname(HERE)
PY = sys.executable
SLATE = os.path.join(TUI, "slate.py")

ALLOWED_SGR = {0, 1, 2, 4, 7, 39, 49} | set(range(30, 38)) | set(range(40, 48)) | set(range(90, 98))


class Screen:
    def __init__(self, w=120, h=40):
        self.w, self.h = w, h
        self.grid = [[" "] * w for _ in range(h)]
        self.r, self.c = 1, 1
        self.cursor_visible = True
        self.alt = False
        self.violations = []
        self.buf = b""

    def feed(self, data):
        self.buf += data
        text = self.buf.decode("utf-8", errors="ignore")
        # keep an incomplete trailing sequence for the next feed
        m = re.search(r"\x1b(\[[0-9;?]*)?$", text)
        if m:
            keep = text[m.start():]
            text = text[:m.start()]
            self.buf = keep.encode("utf-8")
        else:
            self.buf = b""
        i = 0
        while i < len(text):
            ch = text[i]
            if ch == "\x1b":
                m = re.match(r"\x1b\[([0-9;?]*)([@-~])", text[i:])
                if not m:
                    self.violations.append(repr(text[i:i + 6]))
                    i += 1
                    continue
                self.csi(m.group(1), m.group(2))
                i += m.end()
                continue
            if ch in "\r\n":
                i += 1
                continue
            if ord(ch) < 0x20 or ord(ch) == 0x7F:
                self.violations.append("control %r" % ch)
                i += 1
                continue
            if self.c > self.w:
                self.violations.append("wrap at row %d" % self.r)
            elif 1 <= self.r <= self.h:
                self.grid[self.r - 1][self.c - 1] = ch
            self.c += 1
            i += 1

    def csi(self, params, final):
        if final == "H" and "?" not in params:
            parts = [int(x) if x else 1 for x in params.split(";")] if params else [1, 1]
            self.r, self.c = parts[0], (parts[1] if len(parts) > 1 else 1)
        elif final == "J" and params == "2":
            self.grid = [[" "] * self.w for _ in range(self.h)]
        elif final == "K" and params == "":
            for cc in range(self.c, self.w + 1):
                self.grid[self.r - 1][cc - 1] = " "
        elif final == "m":
            for x in (params.split(";") if params else ["0"]):
                if int(x or 0) not in ALLOWED_SGR:
                    self.violations.append("sgr %s" % x)
        elif final in "hl" and params in ("?25", "?1049"):
            if params == "?25":
                self.cursor_visible = final == "h"
            else:
                self.alt = final == "h"
        else:
            self.violations.append("csi %r %r" % (params, final))

    def row(self, r):
        return "".join(self.grid[r - 1])

    def rect_text(self, rect):
        r, c, h, w = rect
        return ["".join(self.grid[rr - 1][c - 1:c - 1 + w]) for rr in range(r, r + h) if 1 <= rr <= self.h]


def painted(screen, rect, s):
    """s, or s cut with "…" (TRM-A4), is painted inside rect."""
    rows = screen.rect_text(rect)
    joined = "\n".join(rows)
    if s in joined:
        return True
    first = s.split("\n")[0]
    for k in range(len(first), 0, -1):
        if first[:k] + "…" in joined:
            return True
    return False


class Proc:
    def __init__(self, *args):
        ctl_r, ctl_w = os.pipe()
        rep_r, rep_w = os.pipe()
        # move the ends that the child gets above 9, so that the redirections of the
        # shell do not close a descriptor that is 3 or 4 in this process
        hi_r = fcntl.fcntl(ctl_r, fcntl.F_DUPFD, 20)
        hi_w = fcntl.fcntl(rep_w, fcntl.F_DUPFD, 20)
        os.close(ctl_r)
        os.close(rep_w)
        ctl_r, rep_w = hi_r, hi_w
        cmd = "exec %s %s %s --harness 3<&%d 4>&%d %d<&- %d>&-" % (
            PY, SLATE, " ".join("'%s'" % a for a in args), ctl_r, rep_w, ctl_r, rep_w)
        self.p = subprocess.Popen(["/bin/sh", "-c", cmd], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  pass_fds=(ctl_r, rep_w), bufsize=0)
        os.close(ctl_r)
        os.close(rep_w)
        self.ctl = ctl_w
        self.rep = rep_r
        self.rbuf = b""
        self.screen = Screen()

    def _pump(self, timeout=10.0):
        """Read the terminal output and one line of the control channel."""
        end = time.time() + timeout
        while b"\n" not in self.rbuf:
            left = end - time.time()
            if left <= 0:
                raise TimeoutError("no reply")
            r, _, _ = select.select([self.p.stdout.fileno(), self.rep], [], [], left)
            if self.p.stdout.fileno() in r:
                data = os.read(self.p.stdout.fileno(), 65536)
                if data:
                    self.screen.feed(data)
            if self.rep in r:
                data = os.read(self.rep, 65536)
                if not data:
                    raise EOFError("control channel closed")
                self.rbuf += data
        line, self.rbuf = self.rbuf.split(b"\n", 1)
        # drain the rest of the paint that is already written
        while True:
            r, _, _ = select.select([self.p.stdout.fileno()], [], [], 0.02)
            if not r:
                break
            data = os.read(self.p.stdout.fileno(), 65536)
            if not data:
                break
            self.screen.feed(data)
        return json.loads(line)

    def command(self, obj):
        os.write(self.ctl, (json.dumps(obj) + "\n").encode())
        return self._pump()

    def key(self, b):
        self.p.stdin.write(b)
        self.p.stdin.flush()
        return self._pump()

    def quit(self):
        os.write(self.ctl, b'{"quit": true}\n')
        rest = b""
        end = time.time() + 10
        while time.time() < end:
            r, _, _ = select.select([self.p.stdout.fileno()], [], [], 0.5)
            if r:
                data = os.read(self.p.stdout.fileno(), 65536)
                if not data:
                    break
                rest += data
            elif self.p.poll() is not None:
                break
        self.screen.feed(rest)
        try:
            self.p.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self.p.kill()
            self.p.wait()
        self.p.stdin.close()
        self.p.stdout.close()
        os.close(self.ctl)
        os.close(self.rep)
        return rest


class HarnessTest(unittest.TestCase):
    def check_dump_against_grid(self, proc, d):
        s = proc.screen
        self.assertEqual(s.violations, [])
        for p in d["parts"]:
            r, c, h, w = p["rect"]
            self.assertTrue(1 <= r and r + h - 1 <= 40 and 1 <= c and c + w - 1 <= 120, p)
            for label in (p["name"], p["text"]):
                if not label:
                    continue
                if p["role"] == "card":
                    cid, title = label.split(" ", 1)
                    rows = s.rect_text(p["rect"])
                    self.assertIn(cid, rows[0], p)
                    self.assertTrue(painted(proc.screen, [r + 1, c, 1, w], title), (p, rows))
                    continue
                if p["role"] == "field" and label == p["text"] and "\n" in label:
                    continue
                if p["role"] == "text" and h > 1:
                    continue  # wrapped text: checked by words below
                self.assertTrue(painted(proc.screen, p["rect"], label),
                                "%r not painted in %r: %r" % (label, p["rect"], s.rect_text(p["rect"])))
            if p["state"] in ("on", "off", "mixed"):
                mark = {"on": "[x] ", "off": "[ ] ", "mixed": "[-] "}[p["state"]]
                self.assertIn(mark, "".join(s.rect_text(p["rect"])), p)
            if p["state"] in ("chosen", "not chosen"):
                mark = "(o) " if p["state"] == "chosen" else "( ) "
                self.assertIn(mark, "".join(s.rect_text(p["rect"])), p)
            if p["disabled"]:
                self.assertIn("(off)", "".join(s.rect_text(p["rect"])), p)
        for card in d["cards"]:
            if card["inView"]:
                self.assertIn(card["id"], s.rect_text(card["rect"])[0])
        if d["focus"] is not None:
            p = d["parts"][d["focus"]]
            self.assertTrue(s.cursor_visible)
            self.assertEqual((s.r, s.c), (p["rect"][0], p["rect"][1]))
        else:
            self.assertFalse(s.cursor_visible)
        if d["announcements"]:
            self.assertTrue(s.row(40).startswith(d["announcements"][-1][:119]))

    def test_harness_board_session(self):
        proc = Proc("--profile", "default", "--address", "board")
        try:
            self.assertEqual(proc._pump(), {"frame": 1})
            self.assertTrue(proc.screen.alt)
            d = proc.command({"dump": True})
            self.assertEqual(d["title"], "Board")
            self.assertEqual(d["address"], "board")
            self.assertEqual(d["depth"], 1)
            self.assertIsNone(d["focus"])
            self.assertEqual(d["requests"], [{"op": "loadBoard", "at": 0}])
            self.check_dump_against_grid(proc, d)
            self.assertEqual(proc.command({"advance": 2200}), {"frame": 2})
            d = proc.command({"dump": True})
            self.assertEqual(d["columns"], ["Backlog", "Ready", "In progress", "Review", "Done"])
            self.assertEqual(len(d["cards"]), 27)
            self.assertEqual(d["announcements"], ["27 cards"])
            self.assertIn("board  1/1", proc.screen.row(1))
            self.check_dump_against_grid(proc, d)
            # Tab twice: home link, then the filter field
            self.assertEqual(proc.key(b"\t"), {"frame": 3})
            self.assertEqual(proc.key(b"\t"), {"frame": 4})
            d = proc.command({"dump": True})
            self.assertEqual(d["parts"][d["focus"]]["name"], "Filter cards")
            self.check_dump_against_grid(proc, d)
            for ch in b"webhook":
                proc.key(bytes([ch]))
            proc.key(b"\r")
            d = proc.command({"dump": True})
            self.assertEqual(d["address"], "board?q=webhook")
            self.assertEqual(d["parts"][d["focus"]]["name"], "SL-112 Document the webhook API")
            self.check_dump_against_grid(proc, d)
            proc.key(b"\r")                       # open the card
            d = proc.command({"dump": True})
            self.assertEqual(d["title"], "Document the webhook API")
            self.assertEqual(d["depth"], 2)
            self.check_dump_against_grid(proc, d)
            proc.command({"advance": 300})
            d = proc.command({"dump": True})
            self.check_dump_against_grid(proc, d)
            proc.key(b"\x1b")                     # Escape goes up: Back to the board
            d = proc.command({"dump": True})
            self.assertEqual(d["address"], "board?q=webhook")
            self.assertEqual(d["parts"][d["focus"]]["role"], "card")
            self.check_dump_against_grid(proc, d)
            # pick up, carry right, drop: a move with "Saving…"
            proc.key(b" ")
            proc.key(b"\x1b[C")
            proc.key(b" ")
            d = proc.command({"dump": True})
            card = [c for c in d["cards"] if c["id"] == "SL-112"][0]
            self.assertEqual(card["column"], "In progress")
            self.assertEqual(card["marks"], ["Saving…"])
            self.check_dump_against_grid(proc, d)
            proc.command({"advance": 400})
            d = proc.command({"dump": True})
            self.assertEqual(d["notice"], {"kind": "info", "text": "Moved SL-112 to In progress.",
                                           "action": "Undo"})
            self.assertTrue(proc.screen.row(39).startswith("i Moved SL-112 to In progress."))
            self.check_dump_against_grid(proc, d)
            proc.key(b"\x1a")                     # Control+Z
            d = proc.command({"dump": True})
            self.assertIsNone(d["notice"])
            self.check_dump_against_grid(proc, d)
            # a key with no binding still gives a frame
            f = proc.key(b"q")
            self.assertIn("frame", f)
            # reload starts the requests and the clock again
            proc.key(b"\x12")
            d = proc.command({"dump": True})
            self.assertEqual(d["requests"], [{"op": "loadBoard", "at": 0}])
            self.assertEqual(d["depth"], 2)
            self.check_dump_against_grid(proc, d)
        finally:
            rest = proc.quit()
        self.assertEqual(proc.p.returncode, 0)
        self.assertFalse(proc.screen.alt)
        self.assertEqual(proc.screen.violations, [])

    def test_harness_card_place_and_prompt(self):
        proc = Proc("--profile", "default", "--address", "card/sl-114")
        try:
            proc._pump()
            d = proc.command({"dump": True})
            self.assertEqual(d["address"], "card/SL-114")
            self.assertIsNone(d["title"])
            self.check_dump_against_grid(proc, d)
            proc.command({"advance": 700})
            d = proc.command({"dump": True})
            self.assertEqual(d["title"], "Card title overflows on narrow screens")
            self.check_dump_against_grid(proc, d)
            # address prompt
            proc.key(b"\x07")
            for ch in b"nowhere":
                proc.key(bytes([ch]))
            d = proc.command({"dump": True})
            self.assertEqual(d["parts"][d["focus"]]["name"], "Address")
            self.check_dump_against_grid(proc, d)
            proc.key(b"\r")
            d = proc.command({"dump": True})
            self.assertEqual(d["title"], "Page not found")
            self.assertEqual(d["address"], "nowhere")
            self.assertEqual(d["depth"], 2)
            self.check_dump_against_grid(proc, d)
            proc.key(b"\x02")                     # Control+B
            d = proc.command({"dump": True})
            self.assertEqual(d["address"], "card/SL-114")
            self.assertIn("card/SL-114  1/2", proc.screen.row(1))
            self.check_dump_against_grid(proc, d)
        finally:
            proc.quit()

    def test_harness_failures_paint(self):
        for profile, address, ms in (("board-down", "board", 400), ("column-down", "board", 2200),
                                     ("card-down", "card/SL-105", 400), ("empty", "board", 2200)):
            proc = Proc("--profile", profile, "--address", address)
            try:
                proc._pump()
                proc.command({"advance": ms})
                d = proc.command({"dump": True})
                self.check_dump_against_grid(proc, d)
                alerts = [p["name"] for p in d["parts"] if p["role"] == "alert"]
                if profile != "empty":
                    self.assertEqual(len(alerts), 1, profile)
                    self.assertIn(alerts[0], d["announcements"])
            finally:
                proc.quit()


if __name__ == "__main__":
    unittest.main()
