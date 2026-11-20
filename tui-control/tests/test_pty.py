"""The real program through --harness, in a pseudo-terminal of 120 x 40.

A small terminal emulator reads what the build paints. It accepts only the
sequences of TRM-12 and fails on any other control character. Each dump is
checked against the emulated screen (TRM-H6).
"""
import codecs
import fcntl
import json
import os
import pty
import re
import select
import signal
import struct
import sys
import termios
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
TUI = os.path.dirname(HERE)
sys.path.insert(0, HERE)

from checks import check_frame  # noqa: E402

PYTHON = "/opt/homebrew/bin/python3" if os.path.exists("/opt/homebrew/bin/python3") else sys.executable
KEYS = {"Enter": b"\r", "Tab": b"\t", "S-Tab": b"\x1b[Z", "Esc": b"\x1b", "Space": b" ",
        "Backspace": b"\x7f", "Delete": b"\x1b[3~", "Up": b"\x1b[A", "Down": b"\x1b[B",
        "Right": b"\x1b[C", "Left": b"\x1b[D", "Home": b"\x1b[H", "End": b"\x1b[F",
        "C-b": b"\x02", "C-f": b"\x06", "C-g": b"\x07", "C-r": b"\x12", "C-s": b"\x13",
        "C-u": b"\x15", "C-z": b"\x1a"}
SGR_OK = {0, 1, 2, 4, 7, 39, 49} | set(range(30, 38)) | set(range(40, 48)) | set(range(90, 98))


class Screen:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.grid = [[" "] * w for _ in range(h)]
        self.row = self.col = 1
        self.cursor_visible = True
        self.alt = False
        self.buf = ""
        self.decoder = codecs.getincrementaldecoder("utf-8")()
        self.errors = []

    def feed(self, data):
        self.buf += self.decoder.decode(data)
        while self.buf:
            ch = self.buf[0]
            if ch == "\x1b":
                m = re.match(r"\x1b\[([?0-9;]*)([A-Za-z])", self.buf)
                if not m:
                    if len(self.buf) < 16:
                        return  # wait for the rest of the sequence
                    self.errors.append("bad escape %r" % self.buf[:8])
                    self.buf = self.buf[1:]
                    continue
                self.csi(m.group(1), m.group(2))
                self.buf = self.buf[m.end():]
            elif ch == "\r":
                self.col = 1
                self.buf = self.buf[1:]
            elif ch == "\n":
                self.row = min(self.h, self.row + 1)
                self.buf = self.buf[1:]
            elif ord(ch) < 0x20 or ord(ch) == 0x7F:
                self.errors.append("control character %r" % ch)
                self.buf = self.buf[1:]
            else:
                if 1 <= self.row <= self.h and 1 <= self.col <= self.w:
                    self.grid[self.row - 1][self.col - 1] = ch
                self.col += 1
                self.buf = self.buf[1:]

    def csi(self, params, final):
        if final == "H":
            ps = [int(p) if p else 1 for p in params.split(";")] if params else [1, 1]
            self.row, self.col = (ps + [1, 1])[:2]
        elif final == "J" and params == "2":
            self.grid = [[" "] * self.w for _ in range(self.h)]
        elif final == "K" and params in ("", "0"):
            if 1 <= self.row <= self.h:
                for c in range(self.col, self.w + 1):
                    self.grid[self.row - 1][c - 1] = " "
        elif final == "m":
            for p in (params or "0").split(";"):
                if int(p or 0) not in SGR_OK:
                    self.errors.append("SGR %s" % p)
        elif params in ("?25", "?1049") and final in "hl":
            if params == "?25":
                self.cursor_visible = final == "h"
            else:
                self.alt = final == "h"
        else:
            self.errors.append("sequence CSI %s%s" % (params, final))

    def lines(self):
        return ["".join(r) for r in self.grid]


class Build:
    """use_pty: the build runs in a pseudo-terminal. Otherwise its stdin and
    stdout are pipes (the sandbox may refuse pseudo-terminals); the size then
    comes from COLUMNS and LINES."""

    def __init__(self, args, w=120, h=40, use_pty=True):
        self.w, self.h = w, h
        ctrl_r, self.ctrl_w = os.pipe()
        self.reply_r, reply_w = os.pipe()
        argv = [PYTHON, os.path.join(TUI, "slate.py"), "--harness"] + args
        if use_pty:
            pid, master = pty.fork()
            self.key_fd = master
        else:
            in_r, in_w = os.pipe()
            out_r, out_w = os.pipe()
            # keep the child's fds 0 to 4 free of our pipe ends before dup2
            ends = [ctrl_r, reply_w, in_r, out_w]
            pid = os.fork()
            master = out_r
            self.key_fd = in_w
        if pid == 0:
            try:
                if use_pty:
                    fcntl.ioctl(0, termios.TIOCSWINSZ, struct.pack("HHHH", h, w, 0, 0))
                    srcs = [(ctrl_r, 3), (reply_w, 4)]
                else:
                    os.environ["COLUMNS"], os.environ["LINES"] = str(w), str(h)
                    hi = [fcntl.fcntl(fd, fcntl.F_DUPFD, 10) for fd in ends]  # numbers above 4
                    srcs = [(hi[2], 0), (hi[3], 1), (hi[0], 3), (hi[1], 4)]
                for src, dst in srcs:
                    os.dup2(src, dst)
                os.closerange(5, 1024)
                os.execv(PYTHON, argv)
            finally:
                os._exit(127)
        os.close(ctrl_r)
        os.close(reply_w)
        if not use_pty:
            os.close(in_r)
            os.close(out_w)
        self.pid, self.master = pid, master
        self.screen = Screen(w, h)
        self.rbuf = b""
        self.frames = 0

    def pump(self, until_line=True, timeout=10.0):
        """Feed the screen; return the next reply line when until_line."""
        end = time.time() + timeout
        while True:
            if until_line and b"\n" in self.rbuf:
                line, self.rbuf = self.rbuf.split(b"\n", 1)
                self.drain()
                return json.loads(line)
            left = end - time.time()
            if left <= 0:
                raise AssertionError("no reply from the build")
            r, _, _ = select.select([self.master, self.reply_r], [], [], min(left, 0.2))
            if self.master in r:
                try:
                    self.screen.feed(os.read(self.master, 65536))
                except OSError:
                    pass
            if self.reply_r in r:
                chunk = os.read(self.reply_r, 65536)
                if not chunk:
                    raise AssertionError("reply channel closed")
                self.rbuf += chunk

    def drain(self):
        while True:
            r, _, _ = select.select([self.master], [], [], 0.05)
            if not r:
                return
            try:
                data = os.read(self.master, 65536)
            except OSError:
                return
            if not data:
                return
            self.screen.feed(data)

    def frame(self):
        msg = self.pump()
        assert "frame" in msg, msg
        self.frames += 1
        assert msg["frame"] == self.frames, (msg, self.frames)
        return msg

    def command(self, obj):
        os.write(self.ctrl_w, (json.dumps(obj) + "\n").encode())

    def advance(self, ms):
        self.command({"advance": ms})
        return self.frame()

    def key(self, name):
        os.write(self.key_fd, KEYS.get(name, name.encode("utf-8")))
        return self.frame()

    def dump(self):
        self.command({"dump": True})
        return self.pump()

    def quit(self):
        self.command({"quit": True})
        end = time.time() + 5
        while time.time() < end:
            pid, status = os.waitpid(self.pid, os.WNOHANG)
            if pid:
                self.drain_after_exit()
                return status
            self.drain()
        os.kill(self.pid, signal.SIGKILL)
        raise AssertionError("build did not quit")

    def drain_after_exit(self):
        try:
            while True:
                r, _, _ = select.select([self.master], [], [], 0.05)
                if not r:
                    break
                data = os.read(self.master, 65536)
                if not data:
                    break
                self.screen.feed(data)
        except OSError:
            pass

    def close(self):
        for fd in {self.master, self.key_fd, self.ctrl_w, self.reply_r}:
            try:
                os.close(fd)
            except OSError:
                pass


def pty_available():
    try:
        m, s = pty.openpty()
        os.close(m)
        os.close(s)
        return True
    except OSError:
        return False


class HarnessCases:
    use_pty = True

    def setUp(self):
        self.builds = []

    def tearDown(self):
        for b in self.builds:
            try:
                os.kill(b.pid, signal.SIGKILL)
                os.waitpid(b.pid, 0)
            except OSError:
                pass
            b.close()

    def start(self, *args):
        b = Build(list(args), use_pty=self.use_pty)
        self.builds.append(b)
        b.frame()
        return b

    def check(self, b):
        d = b.dump()
        self.assertEqual(b.screen.errors, [])
        self.assertEqual(check_frame(b.screen.lines(), d, b.w, b.h), [])
        if d["focus"] is not None:
            r, c = d["parts"][d["focus"]]["rect"][:2]
            self.assertTrue(b.screen.cursor_visible)
            self.assertEqual((b.screen.row, b.screen.col), (r, c))
        else:
            self.assertFalse(b.screen.cursor_visible)
        return d

    def test_board_session(self):
        b = self.start("--profile", "default", "--address", "board")
        self.assertTrue(b.screen.alt)
        d = self.check(b)
        self.assertEqual(d["title"], "Board")
        self.assertEqual(d["requests"], [{"op": "loadBoard", "at": 0}])
        b.advance(400)
        b.advance(1000)
        self.assertIn("Still loading…", "\n".join(b.screen.lines()))
        b.advance(800)
        d = self.check(b)
        self.assertEqual(d["columns"], ["Backlog", "Ready", "In progress", "Review", "Done"])
        self.assertEqual(len(d["cards"]), 7 + 7 + 2 + 7)
        self.assertTrue(b.screen.lines()[0].endswith("board  1/1"))
        # a key that changes nothing still gives a frame
        b.key("Left")
        b.key("/")
        for ch in "login":
            b.key(ch)
        b.key("Enter")
        d = self.check(b)
        self.assertEqual(d["address"], "board?q=login")
        self.assertEqual(d["parts"][d["focus"]]["name"], "Filter cards")
        b.key("C-u")
        b.key("Enter")
        for _ in range(14):  # 6 label and 6 assignee toggles, "Select all in Backlog", the card
            b.key("Tab")
        d = self.check(b)
        self.assertEqual(d["parts"][d["focus"]]["name"], "SL-101 Export board as CSV")
        b.key("x")
        b.key("Down")
        b.key("Space")
        b.key("Right")
        d = self.check(b)
        moving = [c for c in d["cards"] if c["marks"] == ["Moving"]]
        self.assertEqual([(c["id"], c["column"]) for c in moving], [("SL-102", "Ready")])
        b.key("Space")
        b.advance(400)
        d = self.check(b)
        self.assertEqual(d["notice"], {"kind": "info", "text": "Moved SL-102 to Ready.", "action": "Undo"})
        b.key("End")
        d = self.check(b)
        self.assertFalse(d["scrollTop"])
        b.key("Enter")
        b.advance(300)
        d = self.check(b)
        self.assertEqual(d["title"], "Board loads twice on Back")
        self.assertEqual(d["depth"], 2)
        b.advance(8000)
        d = self.check(b)
        self.assertIsNone(d["notice"])
        b.key("Esc")
        d = self.check(b)
        self.assertEqual(d["address"], "board")
        self.assertFalse(d["scrollTop"])
        b.key("C-r")
        d = self.check(b)
        self.assertEqual(d["requests"], [{"op": "loadBoard", "at": 0}])
        self.assertEqual(d["depth"], 2)
        status = b.quit()
        self.assertEqual(os.WEXITSTATUS(status), 0)
        self.assertFalse(b.screen.alt)
        self.assertEqual(b.screen.errors, [])

    def test_card_editing(self):
        b = self.start("--address", "card/sl-119")
        d = self.check(b)
        self.assertEqual(d["address"], "card/SL-119")
        b.advance(400)
        d = self.check(b)
        self.assertEqual(d["title"], "Fix crash on empty board")
        b.key("Tab")
        b.key("Tab")
        b.key("Tab")  # home, up-link, Edit title
        d = self.check(b)
        self.assertEqual(d["parts"][d["focus"]]["name"], "Edit title")
        b.key("Enter")
        b.key("C-u")
        for ch in "Flaky é":
            b.key(ch)
        b.key("Enter")
        d = self.check(b)
        self.assertIn("Saving…", [p["name"] for p in d["parts"] if p["role"] == "mark"])
        b.advance(400)
        d = self.check(b)
        self.assertIn("Couldn't save the title.", [p["name"] for p in d["parts"] if p["role"] == "alert"])
        self.assertEqual(d["parts"][d["focus"]]["text"], "Flaky é")
        b.key("Enter")
        b.advance(400)
        d = self.check(b)
        self.assertEqual(d["title"], "Flaky é")
        b.key("C-g")
        for ch in "nowhere":
            b.key(ch)
        b.key("Enter")
        d = self.check(b)
        self.assertEqual(d["title"], "Page not found")
        self.assertEqual(d["depth"], 2)
        b.quit()

    def test_small_screen(self):
        b = Build([], w=100, h=30, use_pty=self.use_pty)
        self.builds.append(b)
        b.frame()
        d = b.dump()
        self.assertEqual(b.screen.lines()[0].rstrip(), "Slate needs 112 columns and 30 rows.")
        self.assertEqual(d["parts"][0]["name"], "Slate needs 112 columns and 30 rows.")
        b.quit()


@unittest.skipUnless(pty_available(), "no pseudo-terminal in this sandbox (openpty: out of pty devices)")
class PtyTest(HarnessCases, unittest.TestCase):
    use_pty = True


class PipeHarnessTest(HarnessCases, unittest.TestCase):
    """The same cases with stdin and stdout as pipes."""
    use_pty = False


if __name__ == "__main__":
    unittest.main()
