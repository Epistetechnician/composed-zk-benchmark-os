from pathlib import Path
import sys
import unittest

import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import learned_stage0_v6 as v6
from learned_stage0_v5 import FrozenScientificTransformer


class V6Tests(unittest.TestCase):
    def test_boundaries_and_seed_disjointness(self):
        self.assertEqual((min(v6.DEVELOPMENT_FAMILIES), max(v6.DEVELOPMENT_FAMILIES)), (160, 191))
        self.assertFalse(set(v6.EXPLORATORY_SEEDS) & set(v6.FUTURE_SEEDS))
        self.assertNotIn(v6.TEST_SEED, v6.EXPLORATORY_SEEDS)

    def test_method_formulas_are_finite_and_distinct(self):
        actor = FrozenScientificTransformer(v6.TEST_SEED)
        example = v6.examples_for(range(160, 161))[0]
        scores = v6.score_example(actor, example)
        expected = set(v6.METHODS) | set(v6.BASELINES) | {
            f"permuted_{method}" for method in v6.NEW_METHODS
        }
        self.assertEqual(set(scores), expected)
        self.assertTrue(all(len(values) == 4 for values in scores.values()))

    def test_training_rejects_test_and_future_seeds(self):
        for seed in (v6.TEST_SEED, *v6.FUTURE_SEEDS):
            with self.assertRaises(ValueError):
                v6.train_actor(seed)

    def test_method_transforms_remove_signed_cancellation(self):
        actor = FrozenScientificTransformer(v6.TEST_SEED)
        example = v6.examples_for(range(160, 161))[1]
        scores = v6.score_example(actor, example)
        self.assertTrue(all(value >= 0 for value in scores["absolute_product_l1"]))
        self.assertTrue(all(value >= 0 for value in scores["absolute_product_l2"]))
        self.assertTrue(all(value >= 0 for value in scores["absolute_product_linf"]))


if __name__ == "__main__":
    unittest.main()
