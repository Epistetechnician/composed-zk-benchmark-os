from pathlib import Path
import sys
import tempfile
import unittest

import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import learned_stage0_v4 as v4
import run_learned_stage0_v4 as runner


class V4Tests(unittest.TestCase):
    def test_frozen_actor_clean_parity(self):
        self.assertTrue(v4.clean_parity())

    def test_override_contract(self):
        actor = v4.FrozenScientificTransformer(131)
        tokens = torch.zeros((1, 12), dtype=torch.long)
        _, heads, _ = actor(tokens)
        clean = actor(tokens)[0]
        noop = actor(tokens, {0: heads[:, 0, :]})[0]
        self.assertTrue(torch.equal(clean, noop))
        with self.assertRaises(ValueError):
            actor(tokens, {4: heads[:, 0, :]})
        with self.assertRaises(ValueError):
            actor(tokens, {0: torch.zeros((1, 7))})
        with self.assertRaises(ValueError):
            actor(tokens, {0: torch.full((1, 8), float("nan"))})

    def test_scientific_seeds_and_holdout_are_exact(self):
        self.assertEqual(v4.SCIENTIFIC_SEEDS, (109, 113, 127))
        self.assertEqual((min(v4.EVALUATION_FAMILIES), max(v4.EVALUATION_FAMILIES)), (384, 447))
        self.assertEqual(len(v4.examples_for(v4.EVALUATION_FAMILIES)), 1024)

    def test_training_rejects_non_scientific_test_seed(self):
        with self.assertRaisesRegex(ValueError, "only frozen scientific seeds"):
            v4.train_selected(131)

    def test_output_boundary(self):
        with self.assertRaisesRegex(ValueError, "repository-external"):
            runner.prepare_output(ROOT / "bad", ROOT.parents[2])
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "target"
            target.mkdir()
            link = Path(directory) / "link"
            link.symlink_to(target, target_is_directory=True)
            with self.assertRaisesRegex(ValueError, "real directory"):
                runner.prepare_output(link, ROOT.parents[2])


if __name__ == "__main__":
    unittest.main()
