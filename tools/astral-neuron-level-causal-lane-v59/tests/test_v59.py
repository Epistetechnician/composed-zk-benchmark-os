import os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "astral-neuron-level-causal-lane-v50", "tests"))
import v59, v50, test_v50, build_refl_v59 as b


def T_(i, text, tag, dep, head): return {"i": i, "text": text, "tag": tag, "dep": dep, "head": head}


class F(test_v50.Fake):
    def split(self): return {"fit": ["f"], "tune": ["t"], "assess": ["a"], "refl": ["r1", "r2"]}
    def unit_stats(self, units, docs):
        return {u: {"act_sing": 0.0, "act_plur": 1.0, "dla": 0, "dla_sing": 0, "dla_plur": 0} for u in units}
    def swap_effect(self, units, docs, means):
        x = 0.5 if set(units) == set(v59.FROZEN59["swap_units"]) else 0.0
        return {"sing": x, "plur": x, "all": x}
    def refl_class_counts(self, docs): return {"sing": 150, "plur": 150}


class Tt(unittest.TestCase):
    def test_extract_plural(self):
        toks = [T_(0, "The", "DT", "det", 1), T_(1, "boys", "NNS", "nsubj", 2), T_(2, "hurt", "VBD", "ROOT", 2),
                T_(3, "badly", "RB", "advmod", 2), T_(4, "themselves", "PRP", "dobj", 2), T_(5, ".", ".", "punct", 2)]
        it = b.extract_refl("d", 0, toks)
        self.assertEqual(len(it), 1); self.assertEqual(it[0]["good"], " themselves"); self.assertEqual(it[0]["bad"], " itself")

    def test_mismatch_dropped(self):
        toks = [T_(0, "The", "DT", "det", 1), T_(1, "boys", "NNS", "nsubj", 2), T_(2, "hurt", "VBD", "ROOT", 2),
                T_(3, "badly", "RB", "advmod", 2), T_(4, "himself", "PRP", "dobj", 2)]
        self.assertEqual(b.extract_refl("d", 0, toks), [])

    def test_singular(self):
        toks = [T_(0, "The", "DT", "det", 1), T_(1, "old", "JJ", "amod", 2), T_(2, "man", "NN", "nsubj", 3),
                T_(3, "hurt", "VBD", "ROOT", 3), T_(4, "himself", "PRP", "dobj", 3)]
        it = b.extract_refl("d", 0, toks)
        self.assertEqual(it[0]["bad"], " themselves")

    def test_frozen(self):
        self.assertLessEqual(v59.FROZEN59["spend_cap_usd"], 2.5)

    def test_end_to_end_fake(self):
        saved = (dict(v59.FROZEN59), v59.FROZEN59_DIGEST)
        v59.FROZEN59["swap_units"] = [0, 1, 2, 200, 201, 400, 401]
        v59.FROZEN59["ablate_units"] = [0, 1, 2, 3, 200, 201, 400, 401]
        v59.FROZEN59_DIGEST = v50.digest(v59.FROZEN59)
        try:
            self._e2e()
        finally:
            v59.FROZEN59.clear(); v59.FROZEN59.update(saved[0]); v59.FROZEN59_DIGEST = saved[1]

    def _e2e(self):
        f = F()
        sel = v50.select_per_layer(f.scores(["f"]), f.layers(), [0, 1, 2], 32)
        v58 = {"top_units": [{"unit": u} for u in v59.FROZEN59["ablate_units"]]}
        r = v59.run_v59(f, dict(test_v50.CFG), {"selected": sel}, v58)
        self.assertIn("swap", r); self.assertIn("reflexive", r)
        self.assertTrue(r["swap"]["sufficiency_supported"])

    def test_unit_list_guard(self):
        with self.assertRaises(v50.V50Error):
            v59.run_v59(F(), dict(test_v50.CFG), {"selected": []}, {"top_units": [{"unit": 1}]})


if __name__ == "__main__":
    unittest.main()
