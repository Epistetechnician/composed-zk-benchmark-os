from pathlib import Path
import sys
import unittest

import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import learned_stage0_v12 as v12
from run_learned_stage0_v12 import prepare
from run_learned_stage0_v12 import top_one_regret


class V12Tests(unittest.TestCase):
    def test_boundaries_exclude_reserves(self):
        self.assertFalse(set(v12.EXPLORATORY_SEEDS) & set(v12.RESERVED_SEEDS))
        self.assertFalse(set(v12.DESIGN_FAMILIES) & set(v12.RESERVED_FAMILIES))
        self.assertFalse(set(v12.ASSESSMENT_FAMILIES) & set(v12.RESERVED_FAMILIES))
        self.assertTrue(v12.authorized_families(v12.DESIGN_FAMILIES))
        self.assertTrue(v12.authorized_families(v12.ASSESSMENT_FAMILIES))
        self.assertFalse(v12.authorized_families(v12.RESERVED_FAMILIES))

    def test_family_complete_batch_contract(self):
        indices = v12.batch_indices(torch.Generator().manual_seed(7))
        self.assertEqual(len(indices), 128)
        for offset in range(0, 128, 16):
            self.assertEqual((indices[offset:offset + 16] % 16).tolist(), list(range(16)))

    def test_feature_panels_are_capacity_matched(self):
        row = {
            "activation_max_abs": 1.0, "activation_mean": .1,
            "activation_norm": 2.0, "attention_causal": .5,
            "bits": [0, 1, 1, 0], "clean_logits": [-.2, .3],
            "clean_margin": .5, "gradient_norm": .4,
            "grad_x_activation": -.7, "head": 2, "label": 1,
            "operator": "matched_patch",
        }
        for estimator in ("input_output_only", "activation_only", "telemetry"):
            self.assertEqual(len(v12.features(row, estimator)), 16)

    def test_ridge_is_deterministic_and_finite(self):
        train_x = [[float(i), float(i % 2)] for i in range(8)]
        train_y = [2.0 * row[0] - row[1] for row in train_x]
        test_x = [[8.0, 0.0], [9.0, 1.0]]
        self.assertEqual(
            v12.ridge_predict(train_x, train_y, test_x),
            v12.ridge_predict(train_x, train_y, test_x),
        )

    def test_top_one_regret_uses_complete_effect_vector(self):
        rows = [
            {
                "actual": value, "predicted": predicted, "head": head,
                "seed": 211, "operator": "zero_ablation", "example_id": "x",
            }
            for head, (value, predicted) in enumerate(
                [(1.0, 0.0), (4.0, 1.0), (2.0, 5.0), (3.0, 2.0)]
            )
        ]
        self.assertEqual(top_one_regret(rows), 0.5)

    def test_reserved_seed_rejected_without_training(self):
        with self.assertRaises(ValueError):
            v12.train_actor(v12.RESERVED_SEEDS[0])

    def test_output_root_rejects_repo_ancestor(self):
        repo = Path(__file__).resolve().parents[4]
        with self.assertRaises(ValueError):
            prepare(repo.parent, repo)


if __name__ == "__main__":
    unittest.main()
