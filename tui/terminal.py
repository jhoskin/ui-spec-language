"""Terminal: key bytes (TRM-9), paint (TRM-12), raw mode, harness (TRM-H1 to TRM-H6)."""
import json
import os
import select
import signal
import sys
import termios
import time
import tty

from view import BOLD, DIM, REV

CSI = "\x1b["

_CSI_KEYS = {
    "A": "up", "B": "down", "C": "right", "D": "left", "H": "home", "F": "end", "Z": "shift-tab",
    "3~": "delete", "1~": "home", "7~": "home", "4~": "end", "8~": "end",
}
_CTRL = {0x09: "tab", 0x0D: "enter", 0x0A: "enter", 0x20: "space", 0x7F: "backspace", 0x08: "backspace"}


def decode_keys(data):
    """Bytes from the terminal to key names. One read holds one key (TRM-H3); a read
    with several keys gives each of them."""
    keys = []
    i = 0
    n = len(data)
    while i < n:
        b = data[i]
        if b == 0x1B:
            if i + 1 < n and data[i + 1] in (0x5B, 0x4F):        # ESC [ or ESC O
                j = i + 2
                while j < n and not (0x40 <= data[j] <= 0x7E):
                    j += 1
                body = data[i + 2:j + 1].decode("latin-1")
                if data[i + 1] == 0x4F:
                    keys.append({"A": "up", "B": "down", "C": "right", "D": "left",
                                 "H": "home", "F": "end"}.get(body, "unknown"))
                else:
                    keys.append(_CSI_KEYS.get(body, "unknown"))
                i = j + 1
                continue
            keys.append("esc")
            i += 1
            continue
        if b in _CTRL:
            keys.append(_CTRL[b])
            i += 1
            continue
        if b < 0x20:
            keys.append("ctrl-" + chr(b + 0x60))
            i += 1
            continue
        # UTF-8 character
        ln = 1
        if b >= 0xF0:
            ln = 4
        elif b >= 0xE0:
            ln = 3
        elif b >= 0xC0:
            ln = 2
        ch = data[i:i + ln].decode("utf-8", errors="replace")
        keys.append(ch)
        i += ln
    return keys


def _sgr(a):
    codes = ["0"]
    if a & BOLD:
        codes.append("1")
    if a & DIM and not a & BOLD:
        codes.append("2")
    if a & REV:
        codes.append("7")
    return CSI + ";".join(codes) + "m"


def paint(layout, previous=None):
    """The sequences for one frame. Only rows that changed since `previous` are written."""
    out = []
    if previous is None or previous.w != layout.w or previous.h != layout.h:
        out.append(CSI + "0m" + CSI + "2J")
        previous = None
    for r in range(layout.h):
        chars = layout.chars[r]
        attrs = layout.attrs[r]
        if previous is not None and previous.chars[r] == chars and previous.attrs[r] == attrs:
            continue
        last = -1
        for c in range(layout.w - 1, -1, -1):
            if chars[c] != " " or attrs[c] != 0:
                last = c
                break
        out.append("%s%d;1H" % (CSI, r + 1))
        cur = None
        for c in range(last + 1):
            if attrs[c] != cur:
                cur = attrs[c]
                out.append(_sgr(cur))
            out.append(chars[c])
        out.append(CSI + "0m")
        if last < layout.w - 1:
            out.append(CSI + "K")
    if layout.cursor is not None:
        out.append("%s%d;%dH" % (CSI, layout.cursor[0], layout.cursor[1]))
        out.append(CSI + "?25h")
    else:
        out.append(CSI + "?25l")
    return "".join(out)


def terminal_size(fd):
    try:
        sz = os.get_terminal_size(fd)
        return sz.columns, sz.lines
    except OSError:
        return 120, 40


class Runner:
    def __init__(self, app, harness, fd_in=0, fd_out=1, ctl_in=3, ctl_out=4):
        self.app = app
        self.harness = harness
        self.fd_in = fd_in
        self.fd_out = fd_out
        self.ctl_in = ctl_in
        self.ctl_out = ctl_out
        self.frame = 0
        self.painted = None
        self.ctl_buf = b""

    def write(self, s):
        data = s.encode("utf-8")
        while data:
            n = os.write(self.fd_out, data)
            data = data[n:]

    def reply(self, obj):
        data = (json.dumps(obj, ensure_ascii=False) + "\n").encode("utf-8")
        while data:
            n = os.write(self.ctl_out, data)
            data = data[n:]

    def repaint(self):
        L = self.app.layout
        self.write(paint(L, self.painted))
        self.painted = L

    def frame_done(self):
        self.repaint()
        if self.harness:
            self.frame += 1
            self.reply({"frame": self.frame})

    def handle_command(self, line):
        try:
            cmd = json.loads(line)
        except ValueError:
            return True
        if not isinstance(cmd, dict):
            return True
        if cmd.get("quit"):
            return False
        if cmd.get("dump"):
            self.reply(self.app.dump())
            return True
        if "advance" in cmd:
            self.app.advance(int(cmd["advance"]))
        self.frame_done()
        return True

    def run(self):
        old = None
        try:
            old = termios.tcgetattr(self.fd_in)
        except termios.error:
            old = None
        rpipe, wpipe = os.pipe()
        os.set_blocking(wpipe, False)
        os.set_blocking(rpipe, False)
        prev_wakeup = signal.set_wakeup_fd(wpipe)
        signal.signal(signal.SIGWINCH, lambda *a: None)
        try:
            if old is not None:
                tty.setraw(self.fd_in)
            self.write(CSI + "?1049h" + CSI + "2J")
            w, h = terminal_size(self.fd_in)
            self.app.resize(w, h)
            self.frame_done()
            last = time.monotonic()
            running = True
            while running:
                rlist = [self.fd_in, rpipe] + ([self.ctl_in] if self.harness else [])
                timeout = None
                if not self.harness:
                    due = self.app.clock.next_due()
                    if due is not None:
                        timeout = max(0.0, (due - self.app.clock.now) / 1000.0)
                    else:
                        timeout = 1.0
                try:
                    ready, _, _ = select.select(rlist, [], [], timeout)
                except InterruptedError:
                    ready = []
                if not self.harness:
                    now = time.monotonic()
                    ms = int((now - last) * 1000)
                    if ms > 0:
                        last += ms / 1000.0
                        self.app.advance(ms)
                        self.repaint()
                if rpipe in ready:
                    try:
                        os.read(rpipe, 1024)
                    except BlockingIOError:
                        pass
                    w, h = terminal_size(self.fd_in)
                    if (w, h) != (self.app.width, self.app.height):
                        self.app.resize(w, h)
                        self.painted = None
                        self.repaint()
                if self.fd_in in ready:
                    data = os.read(self.fd_in, 1024)
                    if not data:
                        break
                    for k in decode_keys(data):
                        if not self.harness and k == "ctrl-q":
                            running = False
                            break
                        reloaded_clock = self.app.clock
                        self.app.key(k)
                        if self.app.clock is not reloaded_clock:
                            last = time.monotonic()
                        self.frame_done()
                if self.harness and self.ctl_in in ready:
                    data = os.read(self.ctl_in, 65536)
                    if not data:
                        break
                    self.ctl_buf += data
                    while b"\n" in self.ctl_buf:
                        line, self.ctl_buf = self.ctl_buf.split(b"\n", 1)
                        if line.strip() and not self.handle_command(line.decode("utf-8")):
                            running = False
                            break
        finally:
            self.write(CSI + "0m" + CSI + "?25h" + CSI + "?1049l")
            if old is not None:
                termios.tcsetattr(self.fd_in, termios.TCSADRAIN, old)
            signal.set_wakeup_fd(prev_wakeup)
            os.close(rpipe)
            os.close(wpipe)


def main(argv=None):
    import argparse
    here = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, here)
    from app import App
    p = argparse.ArgumentParser(prog="slate.py")
    p.add_argument("--profile", default="default")
    p.add_argument("--address", default="board")
    p.add_argument("--harness", action="store_true")
    args = p.parse_args(argv)
    fixture_dir = os.path.join(os.path.dirname(here), "fixture")
    w, h = terminal_size(0)
    app = App(fixture_dir, args.profile, args.address, w, h)
    Runner(app, args.harness).run()
    return 0
