import os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import v55


class T(unittest.TestCase):
    def test_frozen(self):
        self.assertLessEqual(v55.FROZEN55["spend_cap_usd"], 4.0)
        self.assertEqual(v55.FROZEN55["model"], "pythia-1.4b")

    def test_runner_parses(self):
        import ast
        ast.parse(open(os.path.join(os.path.dirname(__file__), "..", "run_v55_node.py")).read())


if __name__ == "__main__":
    unittest.main()
