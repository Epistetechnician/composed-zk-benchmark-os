import importlib.util
import sys
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("v17", ROOT / "lm_explainer_v17.py")
V17 = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
sys.modules["v17"] = V17
SPEC.loader.exec_module(V17)


class V17UnitTests(unittest.TestCase):
    def test_corpus_is_family_complete_and_split_sealed(self):
        rows = V17.build_corpus()
        self.assertEqual(len(rows), 320)
        self.assertEqual(len({r.example_id for r in rows}), 320)
        self.assertEqual({r.split for r in rows}, {"fit", "tune", "assessment"})
        for family in range(40):
            family_rows = [r for r in rows if r.family == family]
            self.assertEqual(len(family_rows), 8)
            self.assertEqual(
                len(
                    {
                        (r.subject_plural, r.distractor_plural, r.surface)
                        for r in family_rows
                    }
                ),
                8,
            )

    def test_pca_is_deterministic_and_sign_fixed(self):
        x = np.random.default_rng(7).normal(size=(32, 90)).astype(np.float32)
        one = V17.pca_fit(x)
        two = V17.pca_fit(x)
        np.testing.assert_array_equal(one["basis"], two["basis"])
        for row in one["basis"]:
            self.assertGreaterEqual(row[np.argmax(np.abs(row))], 0)
        self.assertEqual(V17.pca_apply(x, one).shape, (32, 64))

    def test_shuffle_stays_inside_fit_family_and_subject(self):
        rows = V17.build_corpus()
        raw = np.arange(len(rows) * 3).reshape(len(rows), 3)
        shuffled = V17.shuffled_fit_telemetry(rows, raw)
        for i, row in enumerate(rows):
            if row.split != "fit":
                np.testing.assert_array_equal(shuffled[i], raw[i])
                continue
            donor = int(shuffled[i, 0] // 3)
            self.assertEqual(rows[donor].family, row.family)
            self.assertEqual(rows[donor].subject_plural, row.subject_plural)
