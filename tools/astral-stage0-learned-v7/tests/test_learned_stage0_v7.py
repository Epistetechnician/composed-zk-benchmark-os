from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import learned_stage0_v7 as v7


class V7Tests(unittest.TestCase):
    def test_family_complete_batch_has_complete_truth_tables(self):
        import torch
        generator = torch.Generator().manual_seed(7)
        recipe = v7.RECIPES[1]
        indices = v7.batch_indices(recipe, generator)
        self.assertEqual(len(indices), 128)
        for offset in range(0, 128, 16):
            group = indices[offset:offset + 16]
            self.assertEqual((group % 16).tolist(), list(range(16)))
            self.assertEqual(len(set((group // 16).tolist())), 1)

    def test_batch_plan_is_deterministic(self):
        import torch
        left = torch.Generator().manual_seed(9)
        right = torch.Generator().manual_seed(9)
        self.assertTrue(torch.equal(
            v7.batch_indices(v7.RECIPES[1], left),
            v7.batch_indices(v7.RECIPES[1], right),
        ))

    def test_seed_roles_are_disjoint(self):
        self.assertFalse(set(v7.SELECTION_SEEDS) & set(v7.QUALIFICATION_SEEDS))
        self.assertFalse(set(v7.RESERVED_SEEDS) & (
            set(v7.SELECTION_SEEDS) | set(v7.QUALIFICATION_SEEDS) | {v7.TEST_SEED}
        ))

    def test_small_training_is_reproducible_and_development_only(self):
        _, first = v7.train_recipe(v7.RECIPES[1], v7.TEST_SEED, updates_override=25)
        _, second = v7.train_recipe(v7.RECIPES[1], v7.TEST_SEED, updates_override=25)
        self.assertEqual(first["batch_plan_sha256"], second["batch_plan_sha256"])
        self.assertEqual(first["checkpoint_sha256"], second["checkpoint_sha256"])


if __name__ == "__main__":
    unittest.main()
