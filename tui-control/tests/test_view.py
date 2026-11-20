"""Layout and semantic dump, tested without a terminal."""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, HERE)

from checks import check_frame  # noqa: E402
from model import App  # noqa: E402
from view import render  # noqa: E402

W, H = 120, 40


def frame(app, w=W, h=H):
    fr = render(app, w, h)
    return fr, fr.canvas.lines()


def scenarios():
    """(label, app) pairs that cover the places, states and faces."""
    out = []
    a = App()
    out.append(("board loading", a))
    a = App(); a.advance(1400)
    out.append(("columns loading slow", a))
    a = App(); a.advance(2200)
    out.append(("board ready", a))
    a = App(profile="board-down"); a.advance(400)
    out.append(("board failed", a))
    a = App(profile="column-down"); a.advance(2200)
    out.append(("column failed", a))
    a = App(profile="empty"); a.advance(2200)
    out.append(("empty board", a))
    a = App(address="board?q=zzz"); a.advance(2200)
    out.append(("no match", a))
    a = App(address="board?labels=perf&who=ana,none"); a.advance(2200)
    a.set_focus("card:SL-127"); a.selection = ["SL-109", "SL-127"]
    out.append(("filter and selection", a))
    a = App(); a.advance(2200); a.set_focus("card:SL-110")
    out.append(("scrolled", a))
    a = App(); a.advance(2200); a.set_focus("card:SL-103"); a.handle_key("Space"); a.handle_key("Right")
    out.append(("carrying", a))
    a = App(); a.advance(2200); a.set_focus("card:SL-103"); a.handle_key("Space"); a.handle_key("Space")
    out.append(("saving move", a))
    a = App(); a.advance(2200); a.set_focus("card:SL-107"); a.handle_key("Delete"); a.advance(400)
    out.append(("info notice", a))
    a = App(); a.advance(2200); a.selection = ["SL-107"]; a.activate("selmove:review"); a.advance(400)
    a.set_focus("notice:action")
    out.append(("error notice", a))
    a = App(); a.advance(2200); a.handle_key("C-g"); a.handle_key("c")
    out.append(("address prompt", a))
    a = App(address="card/SL-114")
    out.append(("card loading", a))
    a = App(address="card/SL-114"); a.advance(400)
    out.append(("card ready", a))
    a = App(address="card/SL-126"); a.advance(400)
    out.append(("card many comments", a))
    a = App(address="card/SL-109"); a.advance(400)
    out.append(("card labels full", a))
    a = App(address="card/SL-120"); a.advance(400)
    out.append(("card comments failed", a))
    a = App(profile="card-down", address="card/SL-120"); a.advance(400)
    out.append(("card failed", a))
    a = App(address="card/SL-119"); a.advance(400); a.activate("edittitle"); a.handle_key("C-u")
    a.handle_key("Enter")
    out.append(("title editing with message", a))
    a = App(address="card/SL-119"); a.advance(400); a.activate("editdesc"); a.handle_key("Enter")
    a.handle_key("z")
    out.append(("description editing", a))
    a = App(address="card/SL-119"); a.advance(400); a.set_focus("commentfield")
    for ch in "hi there":
        a.handle_key(ch)
    a.handle_key("C-s")
    out.append(("comment sending", a))
    a = App(address="nowhere")
    out.append(("missing page", a))
    a = App(address="card/SL-999"); a.advance(400)
    out.append(("missing card", a))
    return out


class ViewTest(unittest.TestCase):
    def test_dump_matches_grid(self):
        for label, app in scenarios():
            for (w, h) in ((W, H), (112, 30)):
                with self.subTest(scenario=label, size=(w, h)):
                    fr, lines = frame(app, w, h)
                    self.assertEqual(check_frame(lines, fr.dump, w, h), [])

    def test_location_line(self):
        a = App(address="board?q=fix+login")
        a.navigate("card/SL-101")
        a.go_back()
        _, lines = frame(a)
        self.assertTrue(lines[0].startswith("[Slate]"))
        self.assertTrue(lines[0].endswith("board?q=fix+login  1/2"))

    def test_too_small(self):
        a = App()
        fr, lines = frame(a, 111, 40)
        self.assertEqual(lines[0].rstrip(), "Slate needs 112 columns and 30 rows.")
        self.assertTrue(all(not l.strip() for l in lines[1:]))
        fr, lines = frame(a, 120, 29)
        self.assertEqual(lines[0].rstrip(), "Slate needs 112 columns and 30 rows.")

    def test_marks_and_layout(self):
        a = App(); a.advance(2200)
        a.selection = ["SL-101"]
        fr, lines = frame(a)
        d = fr.dump
        self.assertEqual(d["columns"], ["Backlog", "Ready", "In progress", "Review", "Done"])
        c = [c for c in d["cards"] if c["id"] == "SL-101"][0]
        self.assertTrue(c["selected"])
        self.assertTrue(lines[c["rect"][0] - 1].startswith("[x] SL-101"))
        # three rows and a blank row for each card
        self.assertEqual(c["rect"][2], 3)
        second = [c for c in d["cards"] if c["id"] == "SL-102"][0]
        self.assertEqual(second["rect"][0], c["rect"][0] + 4)
        # columns of equal width side by side
        xs = sorted({cc["rect"][1] for cc in d["cards"]})
        self.assertEqual(xs, [1, 25, 49, 97])
        roles = [p["role"] for p in d["parts"]]
        self.assertEqual(roles[:3], ["link", "place title", "field"])
        self.assertIn("status line", roles)

    def test_focus_cursor_and_reverse(self):
        a = App(); a.advance(2200)
        a.set_focus("filter")
        fr, lines = frame(a)
        p = fr.dump["parts"][fr.dump["focus"]]
        self.assertEqual(p["name"], "Filter cards")
        self.assertEqual(fr.cursor, (p["rect"][0], p["rect"][1]))
        self.assertTrue(fr.canvas.attrs[p["rect"][0] - 1][0] & 8)
        a.focus = None
        fr, _ = frame(a)
        self.assertIsNone(fr.cursor)
        self.assertIsNone(fr.dump["focus"])

    def test_notice_row_and_announcement(self):
        a = App(); a.advance(2200)
        a.set_focus("card:SL-101"); a.handle_key("Delete"); a.advance(400)
        _, lines = frame(a)
        self.assertTrue(lines[H - 2].startswith("i Deleted SL-101."))
        self.assertEqual(lines[H - 1].rstrip(), "Deleted SL-101.")


if __name__ == "__main__":
    unittest.main()
