import importlib.util
import sys
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("v20", ROOT / "v20.py")
V20 = importlib.util.module_from_spec(SPEC)
sys.modules["v20"] = V20
assert SPEC.loader
SPEC.loader.exec_module(V20)


class V20Tests(unittest.TestCase):
    def test_corpus_is_new_deterministic_and_complete(self):
        rows = V20.build_corpus()
        self.assertEqual(rows, V20.build_corpus())
        self.assertEqual(len(rows), 400)
        self.assertEqual(len({x.family_id for x in rows}), 400)
        self.assertTrue(all(x.family_id.startswith("v20-") for x in rows))
        self.assertEqual(sum(x.split == "assessment" for x in rows), 50)

    def test_bins_are_fit_only_ordered_and_complete(self):
        values = list(np.linspace(-10, 10, 100))
        boundaries, centroids, indices = V20.fit_bins(values)
        self.assertEqual(len(boundaries), 4)
        self.assertEqual(len(centroids), 5)
        self.assertEqual(sorted(set(indices)), [0, 1, 2, 3, 4])
        self.assertEqual([indices.count(x) for x in range(5)], [20] * 5)
        self.assertEqual(centroids, sorted(centroids))

    def test_effect_is_ablated_minus_hinted_margin(self):
        hinted = {"a_logit": 3.0, "b_logit": 1.0}
        ablated = {"a_logit": 1.5, "b_logit": 2.0}
        self.assertEqual(V20.effect(hinted, ablated), -2.5)


if __name__ == "__main__":
    unittest.main()
