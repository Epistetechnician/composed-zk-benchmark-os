import os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import matched_control as m

POOL = list(range(500))
UNITS = [1, 2, 3, 4]
BASE = dict(unit_set=UNITS, layer=7, draws=1000, seed=11, min_effect=0.1, alpha=0.05)


class T(unittest.TestCase):
    def test_not_valid_when_effect_equals_control_mean(self):
        r = m.run(dict(BASE, effect=0.5), POOL)
        self.assertEqual(r["status"], "InstrumentNotValid")

    def test_separates_with_large_effect(self):
        r = m.run(dict(BASE, effect=0.99), POOL)
        self.assertEqual(r["status"], "SeparatesFromControl")

    def test_deterministic(self):
        a = m.run(dict(BASE, effect=0.8), POOL)
        self.assertEqual(a, m.run(dict(BASE, effect=0.8), POOL))

    def test_rejections(self):
        for bad in (dict(BASE, effect=float("nan")), dict(BASE, effect=1, draws=10),
                    dict(BASE, effect=1, extra=1), dict(BASE, effect=1, unit_set=[1, 1]),
                    dict(BASE, effect=1, note="SOTA result")):
            with self.assertRaises(m.ControlError):
                m.validate_request(bad)

    def test_degenerate_shape(self):
        self.assertTrue(m.shape_summary([1, 1, 1])["degenerate"])


if __name__ == "__main__":
    unittest.main()
