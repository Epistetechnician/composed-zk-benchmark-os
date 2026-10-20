import os, random, sys, unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import v49


class Fake:
    """Planted-signal backend: units 0-3 truly matter; others noise."""
    def __init__(self, planted=True, seed=3):
        self.planted, self.r = planted, random.Random(seed)
    def docs(self): return ["d%d" % i for i in range(30)]
    def scores(self, fit): return {u: (5.0 if (u < 4 and self.planted) else self.r.random()) for u in range(60)}
    def magnitude(self): return {u: float(u % 7) for u in range(60)}
    def layers(self): return {u: u // 20 for u in range(60)}
    def effect(self, units, docs): return sum(2.0 if (u < 4 and self.planted) else 0.01 * (u % 5) for u in units)
    def control_effect(self, name, units, docs): return 0.0


CFG = {"seed": 7, "k": 4, "draws": 1000, "min_effect": 0.5, "alpha": 0.05, "note": ""}


class T(unittest.TestCase):
    def test_planted_candidate(self):
        r = v49.run_v49(Fake(True), CFG)
        self.assertEqual(r["status"], "Candidate"); self.assertEqual(r["ceiling"], v49.CEILING)
    def test_null_no_candidate(self):
        self.assertEqual(v49.run_v49(Fake(False), CFG)["status"], "NoCandidate")
    def test_deterministic_lock(self):
        self.assertEqual(v49.run_v49(Fake(), CFG)["lock"], v49.run_v49(Fake(), CFG)["lock"])
    def test_rejects(self):
        for bad in ({**CFG, "draws": 10}, {**CFG, "note": "SOTA result"}):
            with self.assertRaises(v49.V49Error): v49.run_v49(Fake(), bad)
        with self.assertRaises(v49.V49Error): v49.split_docs(["a", "a", "b", "c", "d", "e"], 1)
    def test_holm(self):
        self.assertEqual(v49.holm([0.01, 0.04], 0.05), [True, True])
        self.assertEqual(v49.holm([0.04, 0.03], 0.05), [False, False])
    def test_lane_b(self):
        ok = dict(values=[-2, -1, 0.5, 3], lens_tol=0.1, positive_control=True, near_miss_rejected=True, known_bad_fails=True)
        lens = {"mean": lambda v: 1.0, "med": lambda v: 1.05}
        self.assertEqual(v49.instrument_validity_gate(lens, ok)["status"], "InstrumentValid")
        for k, v in (("known_bad_fails", False), ("values", [1, 2, 3]), ("values", [1, 1])):
            self.assertEqual(v49.instrument_validity_gate(lens, {**ok, k: v})["status"], "InstrumentNotValid")
        self.assertEqual(v49.instrument_validity_gate({"a": lens["mean"]}, ok)["status"], "InstrumentNotValid")
    def test_lane_c_not_gate(self):
        r = v49.lane_c_report({"g": True}, 1.0, [0.2, 0.4])
        self.assertTrue(r["descriptive_only"]); self.assertFalse(r["is_gate"] or r["is_score"])
    def test_lane_d(self):
        r = v49.lane_d_diagnostic([{"a": 1, "b": 1}, {"a": 3, "b": 1}], {"a"})
        self.assertTrue(r["grows_local"]); self.assertFalse(r["claims_retention_or_improvement"])


if __name__ == "__main__":
    unittest.main()
