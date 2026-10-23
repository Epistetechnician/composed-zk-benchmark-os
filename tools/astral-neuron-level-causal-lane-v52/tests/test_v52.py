import json, os, sys, tempfile, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "astral-neuron-level-causal-lane-v50", "tests"))
import v52, test_v50


class F(test_v50.Fake):
    def flip_scale(self, units, docs):
        return 0.01


class T(unittest.TestCase):
    def test_frozen(self):
        self.assertEqual(v52.FROZEN52["spend_cap_usd"], 10.0)
        self.assertLessEqual(v52.FROZEN52["spend_cap_usd"], v52.v50.FROZEN["spend_cap_usd"])

    def test_incremental_log_and_result(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "x.jsonl")
            rec = v52.Recorder(F(kb=0.01), p)
            r = v52.v51.run_v51(rec, test_v50.CFG)
            lines = [json.loads(l) for l in open(p)]
            self.assertEqual(lines[0]["call"], "start")
            self.assertTrue(any(l["call"] == "flip_scale" for l in lines))
            self.assertTrue(any(l["call"] == "effect" for l in lines))
            self.assertEqual(r["gate"]["gate"], "v3")


if __name__ == "__main__":
    unittest.main()
