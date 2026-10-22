import os, random, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import v50

PLANTED = {0, 1, 2, 3, 200, 201, 202, 400, 401, 402, 403}  # 11 of 32 selected  # layers 0,1,2


class Fake:
    """600 units over 3 layers. kb: known-bad effect; direct: planted direct share."""
    def __init__(self, planted=True, kb=0.01, direct_planted=0.3, seed=3):
        self.planted, self.kb, self.dp, self.r = planted, kb, direct_planted, random.Random(seed)
        self.locked, self.calls = None, []
        self._sc = {u: (5.0 if (u in PLANTED and planted) else self.r.random()) for u in range(600)}
    def split(self): return {"fit": ["f"], "tune": ["t"], "assess": ["a"]}
    def scores(self, fit):
        self.calls.append(("scores", tuple(fit))); return dict(self._sc)
    def layers(self): return {u: u // 200 for u in range(600)}
    def magnitude(self): return {u: float(u % 11) for u in range(600)}
    def mark_locked(self, lock): self.locked = lock
    def _eff(self, units, docs):
        if docs != ["f"] and self.locked is None:
            raise AssertionError("effect read before lock")
        self.calls.append(("effect", tuple(docs)))
        return sum(2.0 if (u in PLANTED and self.planted) else 0.002 * (u % 5) for u in units)
    def effect(self, units, docs, readout="margin"):
        e = self._eff(units, docs); return e if readout == "margin" else 0.5 * e
    def control_effect(self, name, units, docs): return 0.0
    def known_bad_effect(self, s, units, docs): return self.kb * (1 + s % 3) / 3
    def activation_values(self): return [-3.0, -0.2, 0.4, 7.0]
    def total_effect(self, units, docs): return self._eff(units, docs)
    def direct_effect(self, units, docs):
        t = self._eff(units, docs)
        return t * (self.dp if sum(u in PLANTED for u in units) * 3 >= len(units) else 0.9)
    def mediators(self, units, docs):
        if sum(u in PLANTED for u in units) * 3 >= len(units): return {"L5H3": 0.6, "L7MLP": 0.3, "x": 0.1}
        return {"c%d" % i: 0.1 for i in range(10)}


CFG = {"seed": 7, "k": 32, "draws": 1000, "alpha": 0.05, "note": "", "target_layers": [0, 1, 2],
       "model_id": "fake", "corpus_digest": "c" * 64, "code_commit": "abc"}


class T(unittest.TestCase):
    def test_frozen(self):
        v50.check_frozen()
        v50.FROZEN["known_bad_max_abs"] = 0.5
        try:
            with self.assertRaises(v50.V50Error): v50.check_frozen()
        finally:
            v50.FROZEN["known_bad_max_abs"] = 0.05
        v50.check_frozen()

    def test_select_quota(self):
        b = Fake(); sel = v50.select_per_layer(b.scores(["f"]), b.layers(), [0, 1, 2], 32)
        self.assertEqual(len(sel), 32)
        lay = b.layers(); self.assertEqual(sorted(sum(lay[u] == l for u in sel) for l in (0, 1, 2)), [10, 11, 11])
        self.assertTrue(PLANTED <= set(sel))
        with self.assertRaises(v50.V50Error): v50.select_per_layer(b.scores(["f"]), b.layers(), [0, 1], 32)

    def test_lock(self):
        a = (list(range(3)), {0: 1, 1: -1, 2: 1}, {"fit": ["f"]}, "m", "c", "x")
        l = v50.make_lock(*a); v50.check_lock(l, *a)
        with self.assertRaises(v50.V50Error): v50.check_lock(l, [0, 1, 4], *a[1:])
        with self.assertRaises(v50.V50Error): v50.make_lock(a[0], {0: 2}, *a[2:])

    def test_candidate_and_order(self):
        b = Fake(); r = v50.run_v50(b, CFG)
        self.assertEqual(r["status"], "Candidate"); self.assertEqual(r["gate"]["status"], "InstrumentValid")
        self.assertTrue(r["path"]["h2"]); self.assertTrue(r["path"]["mechanism_wording_allowed"])
        self.assertEqual(r["ceiling"], v50.CEILING)
        self.assertEqual(b.calls[0], ("scores", ("f",)))  # selection is fit-only, first

    def test_no_signal(self):
        r = v50.run_v50(Fake(planted=False), CFG)
        self.assertIn(r["status"], ("NoCandidate", "InstrumentNotValid"))
        self.assertFalse(r["path"]["mechanism_wording_allowed"])

    def test_known_bad_absolute_rule(self):
        # 0.1 ratio ok but absolute bound 0.05 exceeded -> not valid
        r = v50.run_v50(Fake(kb=0.12), CFG)
        self.assertEqual(r["status"], "InstrumentNotValid"); self.assertIn("known_bad", r["gate"]["fails"])
        # tiny absolute but fails nothing else: valid
        self.assertEqual(v50.run_v50(Fake(kb=0.03), CFG)["gate"]["status"], "InstrumentValid")

    def test_direct_only_blocks_mechanism(self):
        r = v50.run_v50(Fake(direct_planted=0.9), CFG)
        self.assertEqual(r["status"], "Candidate")  # H1 can hold
        self.assertFalse(r["path"]["h2"]); self.assertFalse(r["path"]["mechanism_wording_allowed"])

    def test_gate_bad_activation_and_controls(self):
        b = Fake(); b.activation_values = lambda: [1.0, 2.0]
        self.assertIn("activation_shape", v50.run_v50(b, CFG)["gate"]["fails"])

    def test_rejects(self):
        for bad in ({**CFG, "draws": 100}, {**CFG, "k": 16}, {**CFG, "note": "SOTA"}):
            with self.assertRaises(v50.V50Error): v50.run_v50(Fake(), bad)

    def test_spend(self):
        with self.assertRaises(v50.V50Error): v50.SpendGuard(None).charge(1)
        with self.assertRaises(v50.V50Error): v50.SpendGuard("r", cap=20)
        g = v50.SpendGuard("receipt-1"); g.charge(13.9)
        with self.assertRaises(v50.V50Error): g.charge(0.2)
        self.assertAlmostEqual(g.spent, 13.9)


if __name__ == "__main__":
    unittest.main()
