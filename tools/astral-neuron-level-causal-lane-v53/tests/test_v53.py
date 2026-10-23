import os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "astral-neuron-level-causal-lane-v50", "tests"))
import v53, test_v50


class T(unittest.TestCase):
    def test_specific_pass(self):
        r = [1.0 + 0.1 * (i % 3) for i in range(100)]; c = [0.05] * 100
        s = v53.specificity(r, c); self.assertTrue(s["pass"])

    def test_generic_bias_fails(self):
        r = [0.8 + 0.01 * (i % 3) for i in range(100)]; c = [0.7] * 100
        self.assertFalse(v53.specificity(r, c)["pass"])

    def test_const_over_abs_fails(self):
        r = [2.0 + 0.01 * (i % 5) for i in range(100)]; c = [0.6] * 100
        self.assertFalse(v53.specificity(r, c)["pass"])

    def test_noisy_gap_fails(self):
        r = [0.6 + (-1) ** i * 3 for i in range(100)]; c = [0.0] * 100
        self.assertFalse(v53.specificity(r, c)["pass"])

    def test_end_to_end_fake(self):
        class F(test_v50.Fake):
            spec_stats = None
            def flip_scale(self, u, d): return 0.01
            def control_effect(self, name, u, d):
                if name == "constant":
                    self.spec_stats = v53.specificity([1.0 + 0.1 * (i % 3) for i in range(50)], [0.05] * 50)
                    return self.spec_stats["const_mean"]
                return 0.0
        r = v53.run_v53(F(kb=0.01), test_v50.CFG)
        self.assertTrue(r["specificity"]["pass"]); self.assertEqual(r["gate"]["gate"], "v3")

    def test_frozen(self):
        self.assertLessEqual(v53.FROZEN53["spend_cap_usd"], 6.0)


if __name__ == "__main__":
    unittest.main()
