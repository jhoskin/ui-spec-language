"""Runs a terminal build on a pseudo-terminal for the terminal adapter.

It reads one JSON command for each line on standard input and writes one JSON reply
for each line on standard output:

  {"spawn": [argv], "cols": 120, "rows": 40, "cwd": "."}  start the build; waits for the first frame
  {"keys": "<base64>"}                                    write key bytes to the terminal; waits for a frame
  {"control": {...}, "frame": true}                       write a control command; waits for a frame
  {"control": {"dump": true}}                             write a control command; returns the reply line
  {"close": true}                                         end the build

Each reply has "output": the bytes that the build painted since the last reply, in base64.
The build gets the control channel on file descriptors 3 (commands) and 4 (replies).
"""
import base64
import fcntl
import json
import os
import pty
import select
import signal
import struct
import sys
import termios
import time

TIMEOUT = 10.0
state = {"pid": None, "master": None, "ctl_in": None, "ctl_out": None, "buf": b"", "ctl_buf": b""}


def spawn(argv, cols, rows, cwd):
    to_child_r, to_child_w = os.pipe()
    from_child_r, from_child_w = os.pipe()
    pid, master = pty.fork()
    if pid == 0:
        os.chdir(cwd)
        os.dup2(to_child_r, 3)
        os.dup2(from_child_w, 4)
        for fd in (to_child_r, to_child_w, from_child_r, from_child_w):
            if fd > 4:
                os.close(fd)
        os.set_inheritable(3, True)
        os.set_inheritable(4, True)
        os.environ["TERM"] = "xterm-256color"
        os.execvp(argv[0], argv)
    os.close(to_child_r)
    os.close(from_child_w)
    fcntl.ioctl(master, termios.TIOCSWINSZ, struct.pack("HHHH", rows, cols, 0, 0))
    state.update(pid=pid, master=master, ctl_in=to_child_w, ctl_out=from_child_r)


def pump(want_line):
    """Read terminal output and control lines until one control line comes (if wanted)."""
    end = time.time() + TIMEOUT
    line = None
    while True:
        if want_line and b"\n" in state["ctl_buf"]:
            line, _, state["ctl_buf"] = state["ctl_buf"].partition(b"\n")
            want_line = False
        wait = 0.02 if not want_line else max(0.0, end - time.time())
        ready, _, _ = select.select([state["master"], state["ctl_out"]], [], [], wait)
        if not ready:
            if not want_line:
                return line
            if time.time() >= end:
                return None
            continue
        for fd in ready:
            try:
                data = os.read(fd, 65536)
            except OSError:
                data = b""
            if not data:
                if want_line:
                    return None
                return line
            if fd == state["master"]:
                state["buf"] += data
            else:
                state["ctl_buf"] += data


def reply(extra):
    out, state["buf"] = state["buf"], b""
    extra["output"] = base64.b64encode(out).decode()
    sys.stdout.write(json.dumps(extra) + "\n")
    sys.stdout.flush()


def main():
    for raw in sys.stdin:
        cmd = json.loads(raw)
        if "spawn" in cmd:
            if state["pid"]:
                close()
            spawn(cmd["spawn"], cmd.get("cols", 120), cmd.get("rows", 40), cmd.get("cwd", "."))
            line = pump(True)
            reply({"line": line.decode() if line else None})
        elif "keys" in cmd:
            os.write(state["master"], base64.b64decode(cmd["keys"]))
            line = pump(True)
            reply({"line": line.decode() if line else None})
        elif "control" in cmd:
            os.write(state["ctl_in"], (json.dumps(cmd["control"]) + "\n").encode())
            line = pump(True)
            reply({"line": line.decode() if line else None})
        elif "close" in cmd:
            close()
            reply({"closed": True})


def close():
    if not state["pid"]:
        return
    try:
        os.write(state["ctl_in"], b'{"quit": true}\n')
        time.sleep(0.05)
        os.kill(state["pid"], signal.SIGTERM)
    except OSError:
        pass
    try:
        os.waitpid(state["pid"], 0)
    except OSError:
        pass
    for key in ("master", "ctl_in", "ctl_out"):
        try:
            os.close(state[key])
        except OSError:
            pass
    state.update(pid=None, buf=b"", ctl_buf=b"")


if __name__ == "__main__":
    main()
