import os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "astral-neuron-level-causal-lane-v50", "tests"))
import v58, v50, test_v50


class F(test_v50.Fake):
    def unit_stats(self, units, docs):
        return {u: {"dla_sing": 0.1 if u in test_v50.PLANTED else 0.0, "dla_plur": 0.1 if u in test_v50.PLANTED else 0.0,
                    "dla": 0.2 if u in test_v50.PLANTED else 0.0001 * (u % 7), "act_sing": 1.0, "act_plur": -1.0} for u in units}


class T(unittest.TestCase):
    def test_spearman(self):
        self.assertAlmostEqual(v58.spearman([1, 2, 3, 4], [10, 20, 30, 40]), 1.0)
        self.assertAlmostEqual(v58.spearman([1, 2, 3, 4], [4, 3, 2, 1]), -1.0)
        self.assertEqual(v58.spearman([1, 1, 1], [1, 2, 3]), 0.0)

    def test_frozen(self):
        self.assertLessEqual(v58.FROZEN58["spend_cap_usd"], 2.5)

    def test_end_to_end_fake(self):
        f = F()
        sel = v50.select_per_layer(f.scores(["f"]), f.layers(), [0, 1, 2], 32)
        r = v58.run_v58(f, dict(test_v50.CFG), {"selected": sel})
        self.assertEqual(len(r["top_units"]), 8)
        self.assertTrue(r["h_direct_path"] or r["spearman_single_vs_dla_selected128"] <= 1.0)
        self.assertGreaterEqual(r["n_top8_agreement_selective"], 0)

    def test_reselection_guard(self):
        with self.assertRaises(v50.V50Error):
            v58.run_v58(F(), dict(test_v50.CFG), {"selected": [1, 2, 3]})


if __name__ == "__main__":
    unittest.main()
