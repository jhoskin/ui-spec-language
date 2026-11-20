"""The service double gives the reply of every vector in fixture/vectors.json."""
import json
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

from clock import Clock  # noqa: E402
from service import FIXTURE_DIR, ServiceDouble, load_fixture  # noqa: E402


def run_vector(vector, fixture):
    clock = Clock()
    double = ServiceDouble(clock, vector["profile"], fixture)
    got = []
    for i, call in enumerate(vector["calls"]):
        clock.advance_to(call["at"])
        double.call(call["op"], call["args"],
                    lambda reply, i=i: got.append({"at": clock.now, "call": i, "reply": reply}))
    clock.advance(10 ** 7)
    return got, double


class VectorTest(unittest.TestCase):
    def test_every_vector(self):
        with open(os.path.join(FIXTURE_DIR, "vectors.json"), encoding="utf-8") as f:
            vectors = json.load(f)["vectors"]
        fixture = load_fixture()
        passed = 0
        for v in vectors:
            with self.subTest(vector=v["name"]):
                got, double = run_vector(v, fixture)
                self.assertEqual(got, v["replies"])
                self.assertEqual([e["at"] for e in double.log], [c["at"] for c in v["calls"]])
                passed += 1
        sys.stderr.write("\nvectors passed: %d of %d\n" % (passed, len(vectors)))
        self.assertEqual(passed, len(vectors))


if __name__ == "__main__":
    unittest.main()
