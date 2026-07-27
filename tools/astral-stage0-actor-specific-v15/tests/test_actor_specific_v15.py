from pathlib import Path
import sys
import unittest

import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import actor_specific_v15 as v15
from run_actor_specific_v15 import classify


class V15Tests(unittest.TestCase):
    def test_boundaries(self):
        self.assertEqual(v15.ACTOR_SEEDS, (263, 269, 271))
        self.assertFalse(set(v15.ACTOR_SEEDS) & set(v15.RESERVED_SEEDS))
        self.assertTrue(v15.authorized_families(v15.FIT_FAMILIES))
        self.assertTrue(v15.authorized_families(v15.ASSESSMENT_FAMILIES))
        self.assertFalse(v15.authorized_families(v15.PRIOR_FAMILIES))

    def test_shuffling_preserves_prefix_and_strata(self):
        rows = []
        for index in range(4):
            rows.append({
                "bits": [0, 0, 0, 0], "clean_logits": [0.0, 0.0], "label": 0,
                "operator": "zero_ablation", "site": "head0.cls",
                "site_attention": 0.0, "site_max_abs": 0.0, "site_mean": 0.0,
                "site_norm": 0.0, "site_vector": [float(index)] * 8,
            })
        original = [v15.features(row, "telemetry") for row in rows]
        shuffled = v15.shuffled_features(rows, 263)
        self.assertTrue(all(left[:16] == right[:16] for left, right in zip(original, shuffled)))
        self.assertEqual(sorted(row[16] for row in original), sorted(row[16] for row in shuffled))

    def test_constant_is_exact_site_operator(self):
        train = [
            {"effect": 1.0, "operator": operator, "site": site}
            for site in v15.SITES for operator in v15.OPERATORS
        ]
        train.append({"effect": 3.0, "operator": "zero_ablation", "site": "head0.cls"})
        test = [{"operator": "zero_ablation", "site": "head0.cls"}]
        self.assertEqual(v15.constant_predictions(train, test), [2.0])

    def test_reserved_seed_rejected(self):
        with self.assertRaises(ValueError):
            v15.train_actor(173)

    def test_gate_boundary(self):
        def cell(mse, correlation=0.7, slope=1.0):
            result = {"pooled": {"mse": mse, "correlation": correlation, "calibration_slope": slope}}
            for seed in v15.ACTOR_SEEDS:
                for operator in v15.OPERATORS:
                    result[f"seed={seed};operator={operator}"] = {"mse": mse}
            return result
        metrics = {method: cell(2.0) for method in v15.METHODS}
        metrics["same_actor_telemetry"] = cell(0.94)
        metrics["same_actor_activation"] = cell(1.0)
        self.assertEqual(classify(metrics), "DevelopmentCandidateEligible")
        metrics["same_actor_telemetry"] = cell(0.951)
        self.assertEqual(classify(metrics), "DevelopmentNoCandidate")


if __name__ == "__main__":
    unittest.main()
