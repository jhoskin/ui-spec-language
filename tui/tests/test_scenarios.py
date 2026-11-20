"""Each public scenario, step by step, against the logic (no terminal).

Scenarios marked [pointer] or [web] are for another modality (TRM-A1, the web
address forms) and are skipped. SCN-NAV-4 has a terminal twin below.
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from driver import Driver, all_scenarios  # noqa: E402


def make_test(header, steps):
    def test(self):
        if "[pointer]" in header or "[web]" in header:
            self.skipTest("not for the terminal: " + header)
        Driver().run(steps)
    return test


class ScenarioTest(unittest.TestCase):
    pass


for header, steps in all_scenarios():
    name = "test_" + header.split()[0].replace("-", "_")
    setattr(ScenarioTest, name, make_test(header, steps))


TERMINAL_TWINS = {
    # SCN-NAV-4 with the address forms of TRM-2.
    "test_NAV_4_terminal": [
        'Given start at address "board?who=none,zed,ana&labels=ui,nope,bug&x=1&q=%20fix%20%20login".',
        "After 2200 ms.",
        'Then address is "board?q=fix+login&labels=bug,ui&who=ana,none".',
        'Given start at address "card/sl-114".',
        'Then address is "card/SL-114".',
        'Given start at address "nowhere".',
        'Then place title "Page not found".',
        'Then text "The address may be mistyped or out of date." is shown.',
        'Then address is "nowhere".',
        "When open-board-link.",
        "Then address board.",
        'Then place title "Board".',
    ],
    # SCN-NAV-1's first part through the address prompt (TRM-6, NAV-3).
    "test_enter_address": [
        "Given start at board.",
        "After 2200 ms.",
        "Remember history depth as D.",
        'When enter-address "card/sl-112".',
        'Then place title "Document the webhook API".',
        "Then history depth is D plus 1.",
        "When go-up.",
        "Then address board.",
        "Then history depth is D plus 2.",
        "Then focus card SL-112.",
    ],
    # Before the board data comes, an unknown label stays in the address (NAV-1).
    "test_unknown_label_dropped_when_board_loads": [
        'Given start at address "board?labels=nope,bug".',
        'Then address is "board?labels=nope,bug".',
        "After 400 ms.",
        'Then address is "board?labels=bug".',
    ],
    # A narrow column of the Card place: Labels.Full disables the toggles that are off.
    "test_card_full_labels": [
        "Given start at card SL-109.",
        "After 400 ms.",
        'Then text "Label limit reached (3)" is shown.',
        'Then toggle "api" in "Labels" is disabled.',
        'Then toggle "bug" in "Labels" is on.',
    ],
}

for tname, tsteps in TERMINAL_TWINS.items():
    setattr(ScenarioTest, tname, make_test("twin", tsteps))


if __name__ == "__main__":
    unittest.main()
