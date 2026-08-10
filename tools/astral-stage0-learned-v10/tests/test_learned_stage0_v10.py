from pathlib import Path
import sys
import unittest

import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import learned_stage0_v10 as v10


class V10Tests(unittest.TestCase):
    def test_family_complete_batch_contract(self):
        generator = torch.Generator().manual_seed(7)
        indices = v10.batch_indices(generator)
        self.assertEqual(len(indices), 128)
        for offset in range(0, 128, 16):
            group = indices[offset:offset + 16]
            self.assertEqual((group % 16).tolist(), list(range(16)))

    def test_seed_and_family_boundaries(self):
        self.assertEqual(v10.EXPLORATORY_SEEDS, (157, 163, 167))
        self.assertFalse(set(v10.EXPLORATORY_SEEDS) & set(v10.RESERVED_CONFIRMATION_SEEDS))
        self.assertEqual((min(v10.DEVELOPMENT_FAMILIES), max(v10.DEVELOPMENT_FAMILIES)), (160, 191))

    def test_method_panel_is_frozen_v6(self):
        self.assertEqual(v10.METHODS, (
            "signed_dot_legacy", "absolute_product_l1", "absolute_product_l2",
            "absolute_product_linf", "sign_coherent_mass",
        ))
        self.assertEqual(v10.BASELINES, ("activation_norm", "attention_mass", "gradient_norm"))

    def test_training_rejects_confirmation_seed(self):
        with self.assertRaises(ValueError):
            v10.train_actor(v10.RESERVED_CONFIRMATION_SEEDS[0])


if __name__ == "__main__":
    unittest.main()
