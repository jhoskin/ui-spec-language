"""Rules that the public scenarios do not reach, tested against the logic."""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from driver import Driver, FIXTURE, check_grid  # noqa: E402
import addresses  # noqa: E402
from app import App, cards_word, of_cards, comments_word, fmt_time  # noqa: E402


def run(steps):
    d = Driver()
    d.run(steps)
    return d


class AddressTest(unittest.TestCase):
    """TRM-2, DAT-16."""

    def w(self, s, loaded=True):
        a = addresses.parse(s)
        if loaded:
            return addresses.written(a, ["bug", "ui", "api", "docs", "perf", "blocked"],
                                     ["ana", "ben", "chloe", "dev", "mika"])
        return addresses.written(a)

    def test_forms(self):
        self.assertEqual(self.w(""), "board")
        self.assertEqual(self.w("board"), "board")
        self.assertEqual(self.w("board?q=fix+login"), "board?q=fix+login")
        self.assertEqual(self.w("board?who=none,ana&labels=ui,bug&q=fix+login"),
                         "board?q=fix+login&labels=bug,ui&who=ana,none")
        self.assertEqual(self.w("board?labels=Bug&who=Ana"), "board")
        self.assertEqual(self.w("board?q=a&q=b"), "board?q=b")
        self.assertEqual(self.w("board?x=1&labels=docs"), "board?labels=docs")
        self.assertEqual(self.w("card/sl-114"), "card/SL-114")
        self.assertEqual(self.w("card/SL-114?x=1"), "card/SL-114")
        self.assertEqual(self.w("nowhere"), "nowhere")
        self.assertEqual(addresses.parse("boards").kind, "missing")
        self.assertEqual(addresses.parse("card/").kind, "missing")

    def test_unknown_values_kept_before_board_data(self):
        self.assertEqual(self.w("board?labels=nope,bug", loaded=False), "board?labels=nope,bug")

    def test_text_written_form(self):
        self.assertEqual(addresses.parse("board?q=++fix+++login+").q, "fix login")
        self.assertEqual(self.w("board?q=a%26b"), "board?q=a%26b")
        self.assertEqual(addresses.parse("board?q=a%26b").q, "a&b")
        self.assertEqual(self.w("board?q=%zz&labels=bug"), "board?labels=bug")


class WordsTest(unittest.TestCase):
    def test_words(self):
        self.assertEqual(cards_word(0), "0 cards")
        self.assertEqual(cards_word(1), "1 card")
        self.assertEqual(of_cards(0, 1), "0 of 1 card")
        self.assertEqual(of_cards(4, 27), "4 of 27 cards")
        self.assertEqual(comments_word(1), "1 comment")
        self.assertEqual(fmt_time("2026-11-05T14:39:00Z"), "5 Nov 2026, 14:39")


class ScreenTest(unittest.TestCase):
    def test_small_screen(self):
        """TRM-1."""
        a = App(FIXTURE, "default", "board", 111, 40)
        d = a.dump()
        self.assertEqual([p["name"] for p in d["parts"]], ["Slate needs 112 columns and 30 rows."])
        self.assertEqual("".join(a.layout.chars[0]).strip(), "Slate needs 112 columns and 30 rows.")
        a.resize(112, 30)
        a.advance(2200)
        self.assertEqual(a.dump()["title"], "Board")
        check_grid(a)

    def test_board_tab_order(self):
        """TRM-7: the focus stop comes after "Select all" of its column."""
        a = App(FIXTURE, "default", "board")
        a.advance(2200)
        names = []
        for _ in range(18):
            a.key("tab")
            d = a.dump()
            names.append(d["parts"][d["focus"]]["name"])
        self.assertEqual(names[:3], ["Slate", "Filter cards", "bug"])
        self.assertEqual(names[13], "Unassigned")
        self.assertEqual(names[14:18], ["Select all in Backlog", "SL-101 Export board as CSV",
                                        "Select all in Ready", "Select all in In progress"])
        a.key("shift-tab")
        a.key("shift-tab")
        d = a.dump()
        self.assertEqual(d["parts"][d["focus"]]["name"], "SL-101 Export board as CSV")

    def test_card_tab_order_and_leave_title(self):
        """TRM-7 on Card; TTL-3 by Tab moves on to the next stop."""
        a = App(FIXTURE, "default", "card/SL-104")
        a.advance(700)
        seen = []
        for _ in range(4):
            a.key("tab")
            d = a.dump()
            seen.append(d["parts"][d["focus"]]["name"])
        self.assertEqual(seen, ["Slate", "← Board", "Edit title", "bug"])
        a.key("shift-tab")
        a.key("enter")
        for ch in "New":
            a.key(ch)
        a.key("tab")
        d = a.dump()
        self.assertEqual(d["title"], "Rate limit the search APINew")
        self.assertEqual(d["parts"][d["focus"]]["name"], "bug")


class FlowTest(unittest.TestCase):
    def test_delete_notice_replaced_sends_delete(self):
        """DEL-2, NTC-1: a delete notice ends when another notice is raised."""
        run(["Given start at board.", "After 2200 ms.",
             "Given focus on card SL-101.", "When delete-card.",
             "Then requests deleteCard 0.",
             "Given focus on card SL-119.", "When pick-up.", "When carry left.", "When drop.",
             "Then requests deleteCard 0.",
             "After 400 ms.",
             'Then notice "Moved SL-119 to Ready." with "Undo".',
             "Then requests deleteCard 1."])

    def test_reload_removes_notice_and_sends_nothing(self):
        """MEM-T1 reload: notice removed; session data starts again."""
        d = run(["Given start at board.", "After 2200 ms.",
                 "Given focus on card SL-101.", "When delete-card.",
                 "When reload.", "Then no notice.", "Then focus none.",
                 "After 10000 ms.", "Then requests deleteCard 0.",
                 'Then column "Backlog" starts SL-101.'])
        self.assertEqual(d.d()["requests"][0], {"op": "loadBoard", "at": 0})

    def test_slow_and_loading_count_line(self):
        """COL-1, DAT-2: "Loading cards…" while a column loads."""
        run(["Given start at board.", "After 1399 ms.",
             'Then text "Loading cards…" is shown.', 'Then no text "Still loading…".',
             "After 1 ms.", 'Then text "Still loading…" is shown.',
             "After 799 ms.", 'Then text "Loading cards…" is shown.',
             "After 1 ms.", 'Then text "27 cards" is shown.'])

    def test_card_failed_by_board(self):
        """CRD-T1.2: the board load failed gives Card.Failed; CRD-2 sends it again."""
        run(["Given profile board-down.", "Given start at card SL-114.",
             "After 400 ms.", 'Then place title "SL-114".',
             'Then text "Couldn\'t load this card." is shown.',
             "Then requests loadBoard 1.", "Then requests loadCard 1.",
             "When retry-place.", "After 400 ms.",
             'Then place title "Card title overflows on narrow screens".',
             "Then requests loadBoard 2.", "Then requests loadCard 1."])

    def test_columns_requested_when_board_first_shown(self):
        """A column is requested when Board is first shown, not when Card is shown."""
        run(["Given start at card SL-114.", "After 2000 ms.",
             "Then requests loadColumn 0.", "When go-up.", "Then requests loadColumn 5."])

    def test_undo_of_delete_from_card_gives_card_back(self):
        """DEL-T1.2 then DEL-3 on Board."""
        run(["Given start at card SL-110.", "After 400 ms.", "When delete-card.",
             'Then notice "Deleted SL-110." with "Undo".', "After 2200 ms.",
             'Then column "Backlog" cards SL-101, SL-102, SL-103, SL-104, SL-105, SL-106, SL-107, SL-108, SL-109.',
             "When undo.",
             'Then column "Backlog" cards SL-101, SL-102, SL-103, SL-104, SL-105, SL-106, SL-107, SL-108, SL-109, SL-110.',
             "Then focus card SL-110.", "Then card SL-110 is in view."])

    def test_dismiss_on_filter_field_without_cards(self):
        """DIS-T1.3: no visible card gives the place title."""
        run(["Given start at board.", "After 2200 ms.",
             'When change-filter-text "zzz".', "When commit-filter.",
             'Then text "0 of 27 cards" is shown.', "When dismiss.",
             'Then field "Filter cards" has text "".', "When dismiss.",
             "Then focus card SL-101."])

    def test_carry_ignores_intents(self):
        """CRY-6 and FLT-8: a label filter toggle cancels the carry."""
        run(["Given start at board.", "After 2200 ms.",
             "Given focus on card SL-102.", "When pick-up.", "When carry right.",
             "When toggle-select SL-102.",
             'Then column "Ready" starts SL-111, SL-112, SL-102.',
             "When ask-filter.", "Then focus card SL-102.",
             "When toggle-label-filter bug.",
             'Then column "Backlog" starts SL-102, SL-106.',
             "Then card SL-102 has no mark.", "Then requests moveCards 0."])

    def test_bulk_move_partial_failure_retry_and_comment_elsewhere(self):
        """BLK-T2.1 with two failed cards shows them in board order."""
        run(["Given start at board.", "After 2200 ms.",
             "When toggle-select SL-108.", "When toggle-select SL-107.",
             "When bulk-move Review.", "After 400 ms.",
             'Then notice "Moved 1 of 2 cards to Review. Couldn\'t move SL-107." with "Retry".',
             "When bulk-move Review.", "After 400 ms.",
             'Then notice "Moved 1 card to Review." with "Undo".',
             'Then column "Review" cards SL-108, SL-107.'])

    def test_title_retry_only_ends_notice_while_saving(self):
        """TTL-4: if another title save has no reply, Retry only ends the notice."""
        run(["Given start at card SL-105.", "After 400 ms.",
             "When edit-title.", 'When change-title-text "flaky one".', "When commit-title.",
             "After 400 ms.", 'Then notice "Couldn\'t save the title of SL-105." with "Retry".',
             "When edit-title.", 'When change-title-text "Other".', "When commit-title.",
             "When notice-action.", "Then no notice.", "Then requests saveTitle 2.",
             "After 400 ms.", 'Then place title "Other".', "Then requests saveTitle 2."])

    def test_prompt_escape_changes_nothing(self):
        """TRM-6: Escape closes the prompt; DIS-T1 does not apply."""
        d = Driver()
        d.run(["Given start at board.", "After 2200 ms.", "When toggle-select SL-101."])
        d.key("ctrl-g")
        for ch in "card/SL-1":
            d.key(ch)
        check_grid(d.app)
        d.key("esc")
        d.run(['Then text "1 selected" is shown.', "Then focus card SL-101.", "Then address board."])

    def test_scroll_restored_on_back(self):
        """NAV-T1.3: Back restores the scroll of the entry."""
        run(["Given start at board.", "After 2200 ms.", "Given focus on card SL-110.",
             "Then scroll is not top.", "When open-home.", "Then scroll is top.",
             "When toggle-label-filter docs.", "When open-home.", "When go-back.",
             "Then address board labels docs.", "Then focus place title."])


if __name__ == "__main__":
    unittest.main()
