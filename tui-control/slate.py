#!/usr/bin/env python3
"""Slate, terminal build.

python3 tui/slate.py [--profile NAME] [--address ADDRESS] [--harness]

Paints with raw control sequences (TRM-12). With --harness the clock moves only
by the "advance" command read from file descriptor 3; replies and frame lines
go to file descriptor 4 (TRM-H1 to TRM-H5). Without --harness the build uses
real time; Control+Q quits.
"""
import argparse
import json
import os
import select
import sys
import termios
import traceback
import tty

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from clock import Clock, RealClock  # noqa: E402
from keys import decode  # noqa: E402
from model import App  # noqa: E402
from view import BOLD, DIM, REV, UNDER, render  # noqa: E402

CSI = "\x1b["


def sgr(attr):
    codes = ["0"]
    if attr & BOLD:
        codes.append("1")
    if attr & DIM:
        codes.append("2")
    if attr & UNDER:
        codes.append("4")
    if attr & REV:
        codes.append("7")
    return CSI + ";".join(codes) + "m"


class Terminal:
    def __init__(self, fd_in=0, fd_out=1):
        self.fd_in, self.fd_out = fd_in, fd_out
        self.saved = None
        self.prev = None
        self.prev_size = None

    def start(self):
        if os.isatty(self.fd_in):
            self.saved = termios.tcgetattr(self.fd_in)
            tty.setraw(self.fd_in)
        self.write(CSI + "?1049h" + CSI + "?25l" + CSI + "2J")

    def stop(self):
        self.write(CSI + "0m" + CSI + "2J" + CSI + "?25h" + CSI + "?1049l")
        if self.saved is not None:
            termios.tcsetattr(self.fd_in, termios.TCSADRAIN, self.saved)
            self.saved = None

    def write(self, s):
        data = s.encode("utf-8")
        while data:
            n = os.write(self.fd_out, data)
            data = data[n:]

    def size(self):
        try:
            sz = os.get_terminal_size(self.fd_out)
            return sz.columns, sz.lines
        except OSError:
            # not a terminal (pipes): COLUMNS and LINES, else the check size
            try:
                return int(os.environ.get("COLUMNS", 120)), int(os.environ.get("LINES", 40))
            except ValueError:
                return 120, 40

    def paint(self, frame):
        cv = frame.canvas
        rows = [(tuple(cv.chars[r]), tuple(cv.attrs[r])) for r in range(cv.h)]
        out = [CSI + "?25l"]
        full = self.prev is None or self.prev_size != (cv.w, cv.h)
        if full:
            out.append(CSI + "0m" + CSI + "2J")
        for r, row in enumerate(rows):
            if not full and self.prev[r] == row:
                continue
            chars, attrs = row
            end = len(chars)
            while end > 0 and chars[end - 1] == " " and attrs[end - 1] == 0:
                end -= 1
            seg = [CSI + "%d;1H" % (r + 1), CSI + "0m"]
            cur = 0
            for i in range(end):
                if attrs[i] != cur:
                    seg.append(sgr(attrs[i]))
                    cur = attrs[i]
                seg.append(chars[i])
            seg.append(CSI + "0m" + CSI + "K")
            out.append("".join(seg))
        if frame.cursor:
            out.append(CSI + "%d;%dH" % frame.cursor + CSI + "?25h")
        self.write("".join(out))
        self.prev = rows
        self.prev_size = (cv.w, cv.h)


class Runner:
    def __init__(self, args):
        self.harness = args.harness
        self.app = App(profile=args.profile, address=args.address,
                       clock_factory=Clock if self.harness else RealClock)
        self.term = Terminal()
        self.frame_no = 0
        self.ctrl_buf = b""
        self.ctrl_open = self.harness
        self.done = False
        self.last_size = None

    def reply(self, obj):
        data = (json.dumps(obj, ensure_ascii=True) + "\n").encode("ascii")
        while data:
            n = os.write(4, data)
            data = data[n:]

    def paint(self, frame_line=True):
        w, h = self.term.size()
        self.last_size = (w, h)
        fr = render(self.app, w, h)
        self.term.paint(fr)
        if self.harness and frame_line:
            self.frame_no += 1
            self.reply({"frame": self.frame_no})
        return fr

    def command(self, line):
        try:
            cmd = json.loads(line)
        except ValueError:
            self.reply({"error": "bad json"})
            return
        if not isinstance(cmd, dict):
            self.reply({"error": "bad command"})
        elif "advance" in cmd:
            self.app.advance(int(cmd["advance"]))
            self.paint()
        elif cmd.get("dump"):
            w, h = self.term.size()
            self.reply(render(self.app, w, h).dump)
        elif cmd.get("quit"):
            self.done = True
        else:
            self.reply({"error": "unknown command"})

    def run(self):
        self.term.start()
        try:
            self.paint()
            while not self.done:
                fds = [0] + ([3] if self.ctrl_open else [])
                timeout = 0.25
                if not self.harness:
                    due = self.app.clock.next_due()
                    if due is not None:
                        timeout = max(0.0, min(timeout, (due - self.app.clock.elapsed()) / 1000.0))
                r, _, _ = select.select(fds, [], [], timeout)
                if not self.harness:
                    before = self.app.clock.now
                    self.app.clock.sync()
                    self.app.fix_focus()
                    if not r and self.app.clock.now != before:
                        self.paint(False)
                if 0 in r:
                    data = os.read(0, 4096)
                    if not data:
                        break
                    for k in decode(data, one_key=self.harness):
                        if k == "C-q" and not self.harness:
                            self.done = True
                            break
                        self.app.handle_key(k)
                    if not self.done:
                        self.paint()
                if 3 in r:
                    chunk = os.read(3, 65536)
                    if not chunk:
                        self.ctrl_open = False
                        self.done = True
                    self.ctrl_buf += chunk
                    while b"\n" in self.ctrl_buf and not self.done:
                        line, self.ctrl_buf = self.ctrl_buf.split(b"\n", 1)
                        if line.strip():
                            self.command(line.decode("utf-8"))
                if not r and self.term.size() != self.last_size:
                    self.paint(False)
        finally:
            self.term.stop()


def main(argv=None):
    p = argparse.ArgumentParser(description="Slate terminal build")
    p.add_argument("--profile", default="default")
    p.add_argument("--address", default="board")
    p.add_argument("--harness", action="store_true")
    args = p.parse_args(argv)
    try:
        Runner(args).run()
    except Exception:
        traceback.print_exc()
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
