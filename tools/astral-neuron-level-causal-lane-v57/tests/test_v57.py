import os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "astral-neuron-level-causal-lane-v50", "tests"))
import v57, v50, test_v50


class F(test_v50.Fake):
    def __init__(self, *a, **k):
        super().__init__(*a, **k)

    def compute_means(self, fit): pass

    def effect_mean(self, units, docs): return 0.8 * self.effect(units, docs, "margin")


class T(unittest.TestCase):
    def test_frozen(self):
        self.assertLessEqual(v57.FROZEN57["spend_cap_usd"], 2.5)
        self.assertEqual(v57.FROZEN57["ks"], sorted(v57.FROZEN57["ks"]))

    def test_end_to_end_fake(self):
        f = F()
        sel = v50.select_per_layer(f.scores(["f"]), f.layers(), [0, 1, 2], 32)
        r = v57.run_v57(f, dict(test_v50.CFG), {"selected": sel})
        self.assertEqual(set(r["dose_response"]), {"4", "8", "16", "32", "64", "128"})
        self.assertTrue(r["dose_response"]["32"]["beats_all_controls"])
        self.assertTrue(r["mean_ablation"]["supported"])
        self.assertAlmostEqual(r["mean_ablation"]["frac_of_zero"], 0.8)

    def test_reselection_guard(self):
        with self.assertRaises(v50.V50Error):
            v57.run_v57(F(), dict(test_v50.CFG), {"selected": [1, 2, 3]})


if __name__ == "__main__":
    unittest.main()
