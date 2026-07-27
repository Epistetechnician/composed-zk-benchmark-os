from pathlib import Path
import sys
import unittest

import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import learned_stage0_v5 as v5


class V5Tests(unittest.TestCase):
    def test_clean_parity_and_autograd_capture(self):
        self.assertTrue(v5.clean_parity())
        self.assertTrue(v5.autograd_capture_valid())

    def test_noop_and_fail_closed_overrides(self):
        actor = v5.FrozenScientificTransformer(131)
        tokens = torch.zeros((1, 12), dtype=torch.long)
        clean, heads, _ = actor(tokens)
        self.assertTrue(torch.equal(clean, actor(tokens, {0: heads[:, 0, :]})[0]))
        with self.assertRaises(ValueError):
            actor(tokens, {4: heads[:, 0, :]})
        with self.assertRaises(ValueError):
            actor(tokens, {0: torch.zeros((1, 7))})

    def test_new_seeds_and_holdout_are_disjoint(self):
        self.assertEqual(v5.SCIENTIFIC_SEEDS, (137, 139, 149))
        self.assertFalse(set(v5.SCIENTIFIC_SEEDS) & {109, 113, 127})
        self.assertEqual((min(v5.EVALUATION_FAMILIES), max(v5.EVALUATION_FAMILIES)), (448, 511))
        self.assertEqual(len(v5.examples_for(v5.EVALUATION_FAMILIES)), 1024)

    def test_training_rejects_test_seed(self):
        with self.assertRaises(ValueError):
            v5.train_selected(131)


if __name__ == "__main__":
    unittest.main()
