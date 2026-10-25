import os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import v56


class B:
    def __init__(self, sel_total, ctl_total):
        self.s, self.c = sel_total, ctl_total
    def total_effect(self, u, d): return self.s if u == "SEL" else self.c
    def direct_effect(self, u, d): return 0.1
    def mediators(self, u, d): return {"mlp@20": 0.6, "attn@21": 0.2, "mlp@22": 0.2}


class T(unittest.TestCase):
    def test_stats_selected(self):
        s = v56.path_stats_abs(B(1.0, 0.0), "SEL", None)
        self.assertAlmostEqual(s["indirect_abs"], 0.9); self.assertAlmostEqual(s["top2_share"], 0.8)
        self.assertEqual(s["mediators"], ["mlp@20", "attn@21"])

    def test_nonpositive_indirect_is_defined(self):
        s = v56.path_stats_abs(B(1.0, 0.0), "CTL", None)
        self.assertEqual(s["top2_abs"], 0.0); self.assertLess(s["indirect_abs"], 0)

    def test_frozen(self):
        self.assertLessEqual(v56.FROZEN56["spend_cap_usd"], 3.0)


if __name__ == "__main__":
    unittest.main()
