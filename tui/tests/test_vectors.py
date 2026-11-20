"""The service double gives the reply of every vector in fixture/vectors.json."""
import json
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
TUI = os.path.dirname(HERE)
sys.path.insert(0, TUI)

from clock import Clock  # noqa: E402
from service import Service  # noqa: E402

FIXTURE = os.path.join(os.path.dirname(TUI), "fixture")


def run_vector(vec):
    clock = Clock()
    svc = Service(clock, FIXTURE, vec["profile"])
    got = []
    for i, call in enumerate(vec["calls"]):
        clock.advance(call["at"] - clock.now)

        def cb(reply, i=i):
            got.append({"at": clock.now, "call": i, "reply": reply})

        svc.call(call["op"], call["args"], cb)
    clock.advance(10 ** 7)
    return got, svc


def load_vectors():
    with open(os.path.join(FIXTURE, "vectors.json"), encoding="utf-8") as f:
        return json.load(f)["vectors"]


class VectorTest(unittest.TestCase):
    def test_every_vector(self):
        vectors = load_vectors()
        passed = 0
        for vec in vectors:
            with self.subTest(vector=vec["name"]):
                got, svc = run_vector(vec)
                self.assertEqual(got, vec["replies"])
                self.assertEqual([e["op"] for e in svc.log], [c["op"] for c in vec["calls"]])
                self.assertEqual([e["at"] for e in svc.log], [c["at"] for c in vec["calls"]])
                passed += 1
        print("\nvectors passed: %d of %d" % (passed, len(vectors)), file=sys.stderr)


if __name__ == "__main__":
    unittest.main()
