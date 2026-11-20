"""Seeded random keys and clock steps: no exception, and the dump always matches the grid."""
import os
import random
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, HERE)

from checks import check_frame  # noqa: E402
from model import App  # noqa: E402
from view import render  # noqa: E402

KEYS = ["Tab"] * 4 + ["S-Tab", "Enter", "Space", "Space", "Esc", "Up", "Down", "Left", "Right", "Right",
                      "Home", "End", "x", "X", "/", "a", "f", "Backspace", "Delete", "C-z", "C-s", "C-u",
                      "C-b", "C-f", "C-r"]


def step(app, rnd):
    r = rnd.random()
    if r < 0.2:
        app.advance(rnd.choice([100, 300, 400, 1000, 2500, 8000]))
    elif r < 0.3 and app.place == "board" and app.visible_board():
        app.set_focus("card:" + rnd.choice(app.visible_board()))
        app.fix_focus()
    elif r < 0.4:
        stops = app.stops()
        if stops:
            app.set_focus(rnd.choice(stops))
            app.handle_key(rnd.choice(["Enter", "Space"]))
    elif r < 0.41:
        app.handle_key("C-g")
        for ch in rnd.choice(["card/sl-119", "board?labels=perf", "card/SL-125", "zzz"]):
            app.handle_key(ch)
        app.handle_key("Enter")
    else:
        k = rnd.choice(KEYS)
        if k == "C-r" and rnd.random() < 0.8:
            k = "Tab"
        app.handle_key(k)
STARTS = [("default", "board"), ("default", "card/SL-114"), ("column-down", "board"),
          ("board-down", "board"), ("card-down", "card/SL-120"), ("empty", "board"),
          ("default", "board?labels=bug&who=ana,none"), ("default", "nowhere")]


class FuzzTest(unittest.TestCase):
    def test_random_sessions(self):
        for seed in range(24):
            rnd = random.Random(seed)
            profile, address = STARTS[seed % len(STARTS)]
            app = App(profile=profile, address=address)
            for n in range(300):
                step(app, rnd)
                w, h = rnd.choice([(120, 40), (112, 30)])
                fr = render(app, w, h)
                problems = check_frame(fr.canvas.lines(), fr.dump, w, h)
                if problems:
                    self.fail("seed %d step %d: %s" % (seed, n, problems[:3]))


if __name__ == "__main__":
    unittest.main()
