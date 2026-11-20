import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from address import parse, person_key  # noqa: E402

LABELS = ["bug", "ui", "api", "docs", "perf", "blocked"]
PEOPLE = ["ana", "ben", "chloe", "dev", "mika"]


def p(text):
    return parse(text, LABELS, PEOPLE)


class AddressTest(unittest.TestCase):
    def test_person_key(self):
        self.assertEqual(person_key("Chloé Martin"), "chloe")
        self.assertEqual(person_key("Ana Ruiz"), "ana")

    def test_board_forms(self):
        self.assertEqual(p("board").text, "board")
        self.assertEqual(p("").text, "board")
        a = p("board?q=fix+login")
        self.assertEqual((a.kind, a.q, a.text), ("board", "fix login", "board?q=fix+login"))
        a = p("board?q=fix+login&labels=bug,ui&who=ana,none")
        self.assertEqual(a.labels, ["bug", "ui"])
        self.assertEqual(a.who, ["ana", "none"])
        self.assertEqual(a.text, "board?q=fix+login&labels=bug,ui&who=ana,none")

    def test_order_and_duplicates(self):
        self.assertEqual(p("board?who=ana&q=x&labels=ui").text, "board?q=x&labels=ui&who=ana")
        self.assertEqual(p("board?q=a&q=b").q, "b")
        self.assertEqual(p("board?zzz=1&q=a").text, "board?q=a")

    def test_case_names_nothing(self):
        a = p("board?labels=Bug,ui&who=Ana,ben")
        self.assertEqual(a.labels, ["ui"])
        self.assertEqual(a.who, ["ben"])

    def test_card(self):
        a = p("card/sl-114")
        self.assertEqual((a.kind, a.card, a.text), ("card", "SL-114", "card/SL-114"))
        self.assertEqual(p("card/SL-114?x=1").text, "card/SL-114")

    def test_missing(self):
        for t in ("boards", "Board", "card/", "foo/bar", "card/a/b"):
            self.assertEqual(p(t).kind, "missing", t)
        self.assertEqual(p("nowhere").text, "nowhere")


if __name__ == "__main__":
    unittest.main()
