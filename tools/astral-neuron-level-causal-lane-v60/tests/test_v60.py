import os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "astral-neuron-level-causal-lane-v50", "tests"))
import v60, v50, test_v50


class F(test_v50.Fake):
    def split(self): return {"fit": ["f"], "tune": ["t"], "assess": ["a%d" % i for i in range(10)]}
    def unit_stats(self, units, docs):
        return {u: {"act_sing": 0.0, "act_plur": 1.0, "dla": 0, "dla_sing": 0, "dla_plur": 0} for u in units}
    def item_classes(self, docs): return {i: ("sing" if n % 2 == 0 else "plur") for n, i in enumerate(docs)}
    def capture_last(self, units, docs): return {u: {i: float(n) for n, i in enumerate(docs)} for u in units}
    def swap_effect_last(self, units, docs, means):
        x = 0.5 if set(units) == set(v60.FROZEN60["swap_units"]) else 0.0
        return {"sing": x, "plur": x, "all": x}
    def patch_last(self, units, docs, vals):
        x = 0.4 if set(units) == set(v60.FROZEN60["swap_units"]) else 0.0
        return {"sing": x, "plur": x, "all": x}


class T(unittest.TestCase):
    def test_donors_opposite_and_same(self):
        docs = ["a%d" % i for i in range(10)]
        cl = F().item_classes(docs)
        d = v60.donors(cl, docs, 1)
        self.assertTrue(all(cl[d[i]] != cl[i] for i in docs))
        s = v60.donors(cl, docs, 1, same=True)
        self.assertTrue(all(cl[s[i]] == cl[i] and s[i] != i for i in docs))
        self.assertEqual(d, v60.donors(cl, docs, 1))

    def test_frozen_cap(self):
        self.assertLessEqual(v60.FROZEN60["spend_cap_usd"], 1.5)

    def test_e2e_fake(self):
        saved = (dict(v60.FROZEN60), v60.FROZEN60_DIGEST)
        v60.FROZEN60["swap_units"] = [0, 1, 2, 200, 201, 400, 401]
        v60.FROZEN60["v58_top_units"] = [0, 1, 2, 3, 200, 201, 400, 401]
        v60.FROZEN60_DIGEST = v50.digest(v60.FROZEN60)
        try:
            f = F()
            sel = v50.select_per_layer(f.scores(["f"]), f.layers(), [0, 1, 2], 32)
            r = v60.run_v60(f, dict(test_v50.CFG), {"selected": sel}, {"top_units": [{"unit": u} for u in v60.FROZEN60["v58_top_units"]]})
            self.assertTrue(r["last_swap"]["supported"] and r["donor_patch"]["supported"] and r["headline_hardened"])
        finally:
            v60.FROZEN60.clear(); v60.FROZEN60.update(saved[0]); v60.FROZEN60_DIGEST = saved[1]

    def test_top_unit_guard(self):
        with self.assertRaises(v50.V50Error):
            v60.run_v60(F(), dict(test_v50.CFG), {"selected": []}, {"top_units": [{"unit": 1}]})


if __name__ == "__main__":
    unittest.main()
