import os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import v51


class T(unittest.TestCase):
    def test_pass(self):
        self.assertEqual(v51.null_gate([0.01, -0.02, 0.0, 0.015], 0.5, 0.01), [])

    def test_null_inconsistent(self):
        self.assertIn("null_consistency", v51.null_gate([0.2, 0.0], 0.9, 0.01))

    def test_biased_mean(self):
        self.assertIn("null_consistency", v51.null_gate([0.03] * 20, 0.9, 0.01))

    def test_signal_and_min(self):
        f = v51.null_gate([0.0] * 20, 0.3, 0.05)
        self.assertIn("signal_over_noise", f); self.assertIn("min_effect", f)

    def test_bad_scale(self):
        self.assertEqual(v51.null_gate([0.0], 1.0, 0.0), ["null_scale_invalid"])

    def test_frozen_digest(self):
        self.assertEqual(v51.FROZEN51_DIGEST, v51.v50.digest(v51.FROZEN51))
        self.assertEqual(v51.FROZEN51["spend_cap_usd"], 5.50)


if __name__ == "__main__":
    unittest.main()
