import os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "astral-neuron-level-causal-lane-v50", "tests"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "astral-neuron-level-causal-lane-v60", "tests"))
import v61, v50, test_v50, test_v60


class F(test_v60.F):
    def effect(self, units, docs, readout="margin"):
        if docs == ["t"]:
            return {0: 1.0, 1: 0.9, 2: 0.8, 3: 0.7, 200: 0.6, 201: 0.5, 400: 0.4, 401: 0.3}.get(units[0], 0.01)
        return super().effect(units, docs, readout)
    def swap_effect(self, units, docs, means):
        x = 0.5 if set(units) == self.planted_swap else 0.0
        return {"sing": x, "plur": x, "all": x}
    def swap_effect_last(self, units, docs, means): return self.swap_effect(units, docs, means)
    def patch_last(self, units, docs, vals): return self.swap_effect(units, docs, None)


class T(unittest.TestCase):
    def test_e2e_fake(self):
        f = F(); f.planted_swap = {0, 1, 2, 3, 200, 201, 400, 401}
        saved = None
        cfg = dict(test_v50.CFG)
        orig = v50.select_per_layer
        v50.select_per_layer = lambda s, l, t, k: [0, 1, 2, 3, 200, 201, 400, 401, 5, 6, 202, 402]
        try:
            r = v61.run_v61(f, cfg, v54_selected=[0, 1, 2])
        finally:
            v50.select_per_layer = orig
        self.assertEqual(r["swap_units"], [0, 1, 2, 3, 200, 201, 400, 401])
        self.assertTrue(r["headline_reproduced_and_hardened"])
        self.assertEqual(r["overlap_with_v54_selection"], 3)

    def test_quota_is_per_layer(self):
        f = F()
        sel = v50.select_per_layer(f.scores(['f']), f.layers(), [0, 1, 2], v61.FROZEN61['k_per_layer'] * 3)
        self.assertEqual(len(sel), 96)

    def test_frozen(self):
        self.assertEqual(v61.FROZEN61["dtype"], "float32")


if __name__ == "__main__":
    unittest.main()
