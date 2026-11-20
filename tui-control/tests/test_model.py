"""Application logic, tested without a terminal."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from model import App  # noqa: E402
from view import render  # noqa: E402


def dump(app):
    return render(app, 120, 40).dump


def names(app, role=None):
    return [it.name for it in app.semantic() if role is None or it.role == role]


def texts(app):
    return [it.name for it in app.semantic() if it.role in ("text", "alert", "status line", "mark")]


def ready(profile="default", address="board"):
    a = App(profile=profile, address=address)
    a.advance(2200)
    return a


def keys(app, *ks):
    for k in ks:
        app.handle_key(k)


def focus_card(app, cid):
    app.set_focus("card:" + cid)


class BoardLoadTest(unittest.TestCase):
    def test_loading_then_ready(self):
        a = App()
        self.assertEqual(a.board_state(), "loading")
        self.assertEqual(dump(a)["title"], "Board")
        self.assertEqual(names(a, "placeholder"), ["", "", ""])
        a.advance(399)
        self.assertEqual(a.board_state(), "loading")
        a.advance(1)
        self.assertEqual(a.board_state(), "ready")
        self.assertEqual(a.column_state("backlog"), "loading.fresh")
        a.advance(300)
        self.assertEqual(a.column_state("backlog"), "cards")
        self.assertEqual(a.column_state("review"), "empty")
        self.assertEqual(a.column_state("done"), "loading.fresh")
        a.advance(700)  # 1400: Done is slow
        self.assertEqual(a.column_state("done"), "loading.slow")
        self.assertIn("Still loading…", texts(a))
        a.advance(800)  # 2200
        self.assertEqual(a.column_state("done"), "cards")
        self.assertEqual(a.count_line(), "27 cards")
        ops = [(r["op"], r["at"]) for r in dump(a)["requests"]]
        self.assertEqual(ops[0], ("loadBoard", 0))
        self.assertEqual(sorted(o for o, t in ops[1:]), ["loadColumn"] * 5)

    def test_board_down_and_retry(self):
        a = App(profile="board-down")
        a.advance(400)
        self.assertEqual(a.board_state(), "failed")
        self.assertIn("Couldn't load the board.", texts(a))
        self.assertIn("Couldn't load the board.", dump(a)["announcements"])
        a.activate("retryplace")
        self.assertEqual(a.board_state(), "loading")
        a.advance(400)
        self.assertEqual(a.board_state(), "ready")

    def test_column_down_and_retry(self):
        a = ready("column-down")
        self.assertEqual(a.column_state("ready"), "failed")
        self.assertIn("Couldn't load Ready.", texts(a))
        self.assertIn("Retry Ready", names(a, "action"))
        a.activate("retrycol:ready")
        a.advance(300)
        self.assertEqual(a.column_state("ready"), "cards")

    def test_empty_profile(self):
        a = ready("empty")
        self.assertIn("This board has no cards yet.", texts(a))
        self.assertEqual(a.count_line(), "0 cards")


class FilterTest(unittest.TestCase):
    def test_address_filter_and_count(self):
        a = ready(address="board?q=fix+login")
        self.assertTrue(a.filter_on())
        self.assertEqual(a.visible_board(), ["SL-102", "SL-111"])
        self.assertEqual(a.count_line(), "Showing 2 of 27 cards")
        self.assertEqual(a.column_count("backlog"), "1 of 10")
        self.assertEqual(a.column_state("review"), "empty")
        self.assertEqual(a.column_state("done"), "nomatch")

    def test_typing_commits_on_enter(self):
        a = ready()
        keys(a, "/")
        self.assertEqual(a.focus, "filter")
        keys(a, "l", "o", "g", "i", "n")
        self.assertEqual(a.q, "")
        self.assertIn("Clear filters", names(a, "action"))
        keys(a, "Enter")
        self.assertEqual(a.entry.address, "board?q=login")
        self.assertEqual(len(a.history), 1)
        keys(a, "Backspace", "C-u")
        self.assertEqual(a.draft, "")

    def test_toggles_and_clear(self):
        a = ready()
        a.activate("flabel:bug")
        a.activate("fwho:none")
        self.assertEqual(a.entry.address, "board?labels=bug&who=none")
        self.assertEqual(a.visible_board(), [])
        self.assertIn("No cards match these filters.", texts(a))
        a.set_focus("showall")
        a.activate("showall")
        self.assertFalse(a.filter_on())
        self.assertEqual(a.focus, "filter")
        self.assertEqual(a.entry.address, "board")


class SelectionTest(unittest.TestCase):
    def test_select_and_bulk_move(self):
        a = ready()
        focus_card(a, "SL-101")
        keys(a, "x", "Down", "x")
        self.assertEqual(a.selection, ["SL-101", "SL-102"])
        self.assertIn("2 selected", texts(a))
        self.assertEqual(a.label_state("bug"), "mixed")
        self.assertEqual(a.label_state("api"), "mixed")
        a.activate("selmove:review")
        self.assertEqual(a.col_cards("review"), ["SL-101", "SL-102"])
        self.assertEqual(a.card_marks("SL-101"), ["Saving…"])
        self.assertEqual(a.selection, [])
        a.advance(400)
        self.assertEqual(a.card_marks("SL-101"), [])
        self.assertEqual(a.notice["text"], "Moved 2 cards to Review.")
        self.assertEqual(a.notice["action"], "Undo")
        keys(a, "C-z")
        self.assertEqual(a.col_cards("backlog")[:2], ["SL-101", "SL-102"])
        a.advance(400)
        self.assertEqual(a.notice["text"], "Moved 2 cards back.")

    def test_limit_refuses(self):
        a = ready()
        focus_card(a, "SL-101")
        keys(a, "x", "Down", "x")
        a.activate("selmove:progress")
        self.assertEqual(a.notice["kind"], "error")
        self.assertEqual(a.notice["text"], "In progress has a limit of 3 cards.")
        self.assertEqual(a.col_cards("progress"), ["SL-118", "SL-119"])

    def test_select_column_and_bulk_label(self):
        a = ready()
        focus_card(a, "SL-111")
        keys(a, "X")
        self.assertEqual(len(a.selection), 7)
        a.activate("sellabel:docs")
        # SL-112 has docs already; each other card gets docs
        self.assertTrue(all("docs" in a.cards[c]["labels"] for c in a.col_cards("ready")))
        a.advance(300)
        self.assertEqual(a.notice["text"], "Added docs to 6 cards.")
        self.assertEqual(a.label_state("docs"), "on")
        a.activate("sellabel:docs")
        self.assertEqual(a.label_state("docs"), "off")
        keys(a, "Esc")
        self.assertEqual(a.selection, [])

    def test_move_fault_and_retry(self):
        a = ready()
        focus_card(a, "SL-107")
        keys(a, "x")
        a.activate("selmove:review")
        a.advance(400)
        self.assertEqual(a.notice["kind"], "error")
        self.assertEqual(a.notice["text"], "Couldn't move SL-107.")
        self.assertIn("SL-107", a.col_cards("backlog"))
        self.assertEqual(a.col_cards("backlog").index("SL-107"), 6)
        a.notice_action()
        a.advance(400)
        self.assertEqual(a.col_cards("review"), ["SL-107"])
        self.assertEqual(a.notice["text"], "Moved SL-107 to Review.")


class CarryTest(unittest.TestCase):
    def test_carry_and_drop(self):
        a = ready()
        focus_card(a, "SL-103")
        keys(a, "Space")
        self.assertEqual(a.card_marks("SL-103"), ["Moving"])
        keys(a, "Up")
        self.assertEqual(a.col_cards("backlog")[:3], ["SL-101", "SL-103", "SL-102"])
        keys(a, "Right")
        self.assertEqual(a.cards["SL-103"]["column"], "ready")
        self.assertEqual(a.col_cards("ready").index("SL-103"), 1)
        keys(a, "Space")
        self.assertEqual(a.card_marks("SL-103"), ["Saving…"])
        a.advance(400)
        self.assertEqual(a.notice["text"], "Moved SL-103 to Ready.")
        self.assertEqual(a.service.order["ready"][1], "SL-103")

    def test_cancel_carry(self):
        a = ready()
        focus_card(a, "SL-103")
        keys(a, "Space", "Down", "Down", "Right", "Esc")
        self.assertIsNone(a.carry)
        self.assertEqual(a.col_cards("backlog")[2], "SL-103")
        self.assertEqual([r["op"] for r in a.service.log].count("moveCards"), 0)

    def test_carry_skips_full_column(self):
        a = ready()
        focus_card(a, "SL-111")
        keys(a, "Space", "Right")
        self.assertEqual(a.cards["SL-111"]["column"], "progress")  # 2 cards, room for one
        keys(a, "Space")
        a.advance(400)
        focus_card(a, "SL-112")
        keys(a, "Space", "Right")
        self.assertEqual(a.cards["SL-112"]["column"], "review")


class FocusTest(unittest.TestCase):
    def test_tab_order_board(self):
        a = ready()
        stops = a.stops()
        self.assertEqual(stops[:2], ["home", "filter"])
        i = stops.index("selectall:backlog")
        self.assertEqual(stops[i + 1], "card:SL-101")
        self.assertEqual(sum(1 for s in stops if s.startswith("card:")), 1)
        a.focus = None
        keys(a, "Tab")
        self.assertEqual(a.focus, "home")
        keys(a, "S-Tab")
        self.assertEqual(a.focus, stops[-1])

    def test_focus_stop_follows_last_card(self):
        a = ready()
        focus_card(a, "SL-101")
        keys(a, "Right", "Down")
        self.assertEqual(a.focus, "card:SL-112")
        keys(a, "End")
        self.assertEqual(a.focus, "card:SL-127")
        keys(a, "Home")
        self.assertEqual(a.focus, "card:SL-101")
        focus_card(a, "SL-114")
        a.set_focus("filter")
        self.assertIn("card:SL-114", a.stops())

    def test_scroll_keeps_focus_in_view(self):
        a = ready()
        focus_card(a, "SL-110")
        d = dump(a)
        self.assertFalse(d["scrollTop"])
        card = [c for c in d["cards"] if c["id"] == "SL-110"][0]
        self.assertTrue(card["inView"])
        keys(a, "Home")
        self.assertTrue(dump(a)["scrollTop"])


class NavigationTest(unittest.TestCase):
    def test_open_card_and_back(self):
        a = ready()
        focus_card(a, "SL-114")
        keys(a, "Enter")
        self.assertEqual(a.entry.address, "card/SL-114")
        d = dump(a)
        self.assertIsNone(d["title"])
        self.assertEqual(d["depth"], 2)
        a.advance(300)
        d = dump(a)
        self.assertEqual(d["title"], "Card title overflows on narrow screens")
        self.assertEqual(d["parts"][d["focus"]]["role"], "place title")
        self.assertIn("SL-114 · Ready", texts(a))
        self.assertIn("Dev Patel · 10 Nov 2026, 12:44", texts(a))
        keys(a, "Esc")  # go up = back, focus returns to the card
        self.assertEqual(a.entry.address, "board")
        self.assertEqual(a.focus, "card:SL-114")
        self.assertEqual(len(a.history), 2)
        keys(a, "C-f")
        self.assertEqual(a.entry.address, "card/SL-114")
        keys(a, "C-b", "C-b")
        self.assertEqual(a.pos, 0)

    def test_prompt_and_missing(self):
        a = ready()
        keys(a, "C-g")
        self.assertEqual(a.focus, "prompt")
        for ch in "nowhere":
            keys(a, ch)
        keys(a, "Enter")
        self.assertEqual(dump(a)["title"], "Page not found")
        self.assertEqual(a.entry.address, "nowhere")
        keys(a, "C-g", "c", "a", "r", "d", "/", "s", "l", "-", "9", "9", "9", "Enter")
        self.assertEqual(a.entry.address, "card/SL-999")
        a.advance(250)
        self.assertEqual(dump(a)["title"], "Card not found")
        self.assertIn("There is no card SL-999 on this board.", texts(a))
        a.activate("boardlink")
        self.assertEqual(a.entry.address, "board")
        self.assertEqual(len(a.history), 4)
        keys(a, "C-g", "x", "Esc")
        self.assertIsNone(a.prompt)

    def test_reload_keeps_history(self):
        a = ready()
        a.activate("flabel:bug")
        a.advance(5000)
        keys(a, "C-r")
        self.assertEqual(a.clock.now, 0)
        self.assertEqual(dump(a)["requests"], [{"op": "loadBoard", "at": 0}])
        self.assertEqual(a.entry.address, "board?labels=bug")
        a.advance(2200)
        self.assertEqual(a.flabels, ["bug"])

    def test_notice_gone_at_8000(self):
        a = ready()
        focus_card(a, "SL-101")
        keys(a, "x")
        a.activate("selmove:review")
        a.advance(400)
        self.assertIsNotNone(a.notice)
        a.advance(7999)
        self.assertIsNotNone(a.notice)
        a.advance(1)
        self.assertIsNone(a.notice)


class CardTest(unittest.TestCase):
    def open(self, cid, profile="default"):
        a = App(profile=profile, address="card/" + cid)
        a.advance(400)
        return a

    def test_title_flaky_fails_once(self):
        a = self.open("SL-119")
        a.activate("edittitle")
        self.assertEqual(a.focus, "titlefield")
        keys(a, "C-u")
        for ch in "A Flaky title":
            keys(a, ch)
        keys(a, "Enter")
        self.assertIn("Saving…", texts(a))
        a.advance(400)
        self.assertTrue(a.cv["title_editing"])
        self.assertIn("Couldn't save the title.", texts(a))
        keys(a, "Enter")
        a.advance(400)
        self.assertEqual(a.cv["card"]["title"], "A Flaky title")
        self.assertEqual(dump(a)["title"], "A Flaky title")

    def test_blank_title(self):
        a = self.open("SL-119")
        a.activate("edittitle")
        keys(a, "C-u", "Enter")
        self.assertIn("Title can't be empty.", texts(a))
        keys(a, "Esc")
        self.assertFalse(a.cv["title_editing"])
        self.assertEqual(a.focus, "edittitle")

    def test_labels_full(self):
        a = self.open("SL-109")
        self.assertIn("Label limit reached (3)", texts(a))
        dis = [it.name for it in a.semantic() if it.role == "toggle" and it.disabled]
        self.assertEqual(dis, ["api", "docs", "blocked"])
        a.activate("label:perf")
        self.assertNotIn("Label limit reached (3)", texts(a))
        self.assertIn("Saving…", texts(a))

    def test_assignee_and_description(self):
        a = self.open("SL-110")
        self.assertIn("No description", texts(a))
        a.activate("assignee:dev")
        a.advance(300)
        self.assertEqual(a.service.cards["SL-110"]["assignee"], "dev")
        a.activate("editdesc")
        for ch in "Hello":
            keys(a, ch)
        keys(a, "Enter", "x", "C-s")
        self.assertEqual(a.cv["card"]["description"], "Hello\nx")
        a.advance(400)
        self.assertEqual(a.service.cards["SL-110"]["description"], "Hello\nx")

    def test_comment_flaky(self):
        a = self.open("SL-119")
        self.assertIn("No comments yet", texts(a))
        a.set_focus("commentfield")
        for ch in "flaky":
            keys(a, ch)
        keys(a, "C-s")
        self.assertIn("Sending…", texts(a))
        self.assertTrue(a.comment_field_disabled())
        a.advance(500)
        self.assertIn("Couldn't add the comment.", texts(a))
        self.assertEqual(a.cv["comment_draft"], "flaky")
        a.activate("addcomment")
        a.advance(500)
        self.assertIn("1 comment", texts(a))
        self.assertIn("Mika Ito · 20 Nov 2026, 09:00", texts(a))

    def test_comments_fail_once(self):
        a = self.open("SL-120")
        self.assertIn("Couldn't load comments.", texts(a))
        self.assertTrue(a.comment_field_disabled())
        a.activate("retrycomments")
        a.advance(300)
        self.assertIn("2 comments", texts(a))

    def test_card_down(self):
        a = App(profile="card-down", address="card/SL-119")
        a.advance(400)
        d = dump(a)
        self.assertEqual(d["title"], "SL-119")
        self.assertIn("Couldn't load this card.", texts(a))
        a.activate("retryplace")
        a.advance(250)
        self.assertEqual(dump(a)["title"], "Fix crash on empty board")

    def test_delete_fault_and_retry(self):
        a = ready()
        a.navigate("card/SL-125", from_board=True)
        a.advance(300)
        a.activate("delete")
        self.assertEqual(a.entry.address, "board")
        self.assertEqual(len(a.history), 1)
        self.assertNotIn("SL-125", a.col_cards("done"))
        a.advance(400)
        self.assertEqual(a.notice["text"], "Couldn't delete SL-125.")
        self.assertIn("SL-125", a.col_cards("done"))
        a.notice_action()
        a.advance(400)
        self.assertEqual(a.notice["text"], "Deleted SL-125.")
        self.assertNotIn("SL-125", a.service.cards)

    def test_delete_on_board_moves_focus(self):
        a = ready()
        focus_card(a, "SL-101")
        keys(a, "Delete")
        self.assertEqual(a.focus, "card:SL-102")
        a.advance(400)
        self.assertEqual(a.notice["text"], "Deleted SL-101.")


if __name__ == "__main__":
    unittest.main()
