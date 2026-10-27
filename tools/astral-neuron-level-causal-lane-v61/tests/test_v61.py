import os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "astral-neuron-level-causal-lane-v50", "tests"))
import v61, v60, v50, test_v50


class F(test_v50.Fake):
    def __init__(self, self_ok=True):
        super().__init__()
        self.self_ok = self_ok
    def split(self):
        items, _ = v61.build_minpairs(7, 6)
        return {"fit": ["f"], "tune": ["t"], "assess": ["a"], "minpair": sorted(i["id"] for i in items)}
    def unit_stats(self, units, docs):
        return {u: {"act_sing": 0.0, "act_plur": 1.0, "dla": 0, "dla_sing": 0, "dla_plur": 0} for u in units}
    def capture_last(self, units, docs): return {u: {i: float(n) for n, i in enumerate(docs)} for u in units}
    def patch_last(self, units, docs, vals):
        sw = set(units) == set(v61.FROZEN61["swap_units"])
        # identity donor => same values as capture index of the item itself
        cap = {i: float(n) for n, i in enumerate(docs)}
        selfpatch = all(vals[u][i] == cap[i] for u in units for i in docs)
        x = 0.0 if selfpatch else (0.5 if sw else 0.0)
        if selfpatch and not self.self_ok:
            x = 0.3
        return {"sing": x, "plur": x, "all": x}


class T(unittest.TestCase):
    def test_pairs_minimal(self):
        items, mate = v61.build_minpairs(6161, 400)
        self.assertEqual(len(items), 800)
        by = {i["id"]: i for i in items}
        for a, b in mate.items():
            ta, tb = by[a]["text"].split(), by[b]["text"].split()
            self.assertEqual(len(ta), len(tb))
            self.assertEqual(sum(x != y for x, y in zip(ta, tb)), 1)
            self.assertEqual(by[a]["good"], by[b]["bad"])
            self.assertEqual(mate[b], a)
        self.assertEqual(items, v61.build_minpairs(6161, 400)[0])

    def test_same_number_donor(self):
        items, mate = v61.build_minpairs(1, 20)
        ids = [i["id"] for i in items]
        d = v61.same_number_donors(ids, mate, 3)
        self.assertTrue(all(d[i][-1] == i[-1] and d[i] != i for i in ids))

    def _run(self, f):
        saved = (dict(v61.FROZEN61), v61.FROZEN61_DIGEST)
        v61.FROZEN61["swap_units"] = [0, 1, 2, 200, 201, 400, 401]
        v61.FROZEN61["v58_top_units"] = [0, 1, 2, 3, 200, 201, 400, 401]
        v61.FROZEN61_DIGEST = v50.digest(v61.FROZEN61)
        try:
            sel = v50.select_per_layer(f.scores(["f"]), f.layers(), [0, 1, 2], 32)
            return v61.run_v61(f, dict(test_v50.CFG), {"selected": sel}, {"top_units": [{"unit": u} for u in v61.FROZEN61["v58_top_units"]]})
        finally:
            v61.FROZEN61.clear(); v61.FROZEN61.update(saved[0]); v61.FROZEN61_DIGEST = saved[1]

    def test_e2e_confirmed(self):
        r = self._run(F())
        self.assertTrue(r["self_donor_ok"] and r["minpair_patch"]["supported"] and r["minimal_pair_confirmed"])

    def test_self_donor_failure_voids(self):
        r = self._run(F(self_ok=False))
        self.assertFalse(r["self_donor_ok"]); self.assertFalse(r["minimal_pair_confirmed"])

    def test_guards(self):
        with self.assertRaises(v50.V50Error):
            v61.run_v61(F(), dict(test_v50.CFG), {"selected": []}, {"top_units": [{"unit": 1}]})

    def test_cap(self):
        self.assertLessEqual(v61.FROZEN61["spend_cap_usd"], 1.0)


if __name__ == "__main__":
    unittest.main()
