from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import learned_stage0 as stage0


class LearnedStage0Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        stage0.configure_runtime()

    def test_family_splits_and_census_are_disjoint(self):
        train = stage0.examples_for(range(160))
        dev = stage0.examples_for(range(160, 192))
        evaluation = stage0.examples_for(range(256, 320))
        self.assertEqual((len(train), len(dev), len(evaluation)), (2560, 512, 1024))
        self.assertFalse(
            {row.family for row in train}
            & {row.family for row in dev + evaluation}
        )

    def test_task_labels_match_frozen_formula(self):
        for row in stage0.examples_for(range(256)):
            a, b, c, d = row.bits
            self.assertEqual(row.label, (a ^ b) ^ (c & d))

    def test_training_is_deterministic_and_eligible(self):
        first, first_metrics = stage0.train_actor(11)
        second, second_metrics = stage0.train_actor(11)
        self.assertEqual(first_metrics, second_metrics)
        self.assertGreaterEqual(first_metrics["train_accuracy"], 0.95)
        self.assertGreaterEqual(first_metrics["dev_accuracy"], 0.95)
        self.assertEqual(
            stage0.checkpoint_digest(first), stage0.checkpoint_digest(second)
        )

    def test_scores_are_computed_without_interventions(self):
        model, _ = stage0.train_actor(11)
        row = stage0.examples_for(range(160, 161))[0]
        scores, margin, capture = stage0.score_example(model, row)
        self.assertEqual(set(scores), set(stage0.METHODS))
        self.assertEqual(len(capture), 32)
        self.assertTrue(all(len(values) == 4 for values in scores.values()))
        effects, patches = stage0.intervention_effects(model, row)
        self.assertEqual(len(effects), 4)
        self.assertEqual(len(patches), 4)
        self.assertTrue(any(abs(value) > 1e-6 for value in effects))
        self.assertIsInstance(margin, float)

    def test_unknown_and_nonfinite_overrides_fail_closed(self):
        model, _ = stage0.train_actor(11)
        row = stage0.examples_for(range(160, 161))[0]
        tokens, _ = stage0.tensors([row])
        import torch
        with self.assertRaises(ValueError):
            model(tokens, {4: torch.zeros((1, 8))})
        with self.assertRaises(ValueError):
            model(tokens, {0: torch.full((1, 8), float("nan"))})

    def test_candidate_is_not_algebraically_identical_to_ablation(self):
        model, _ = stage0.train_actor(11)
        differences = []
        for row in stage0.examples_for(range(160, 162)):
            scores, _, _ = stage0.score_example(model, row)
            effects, _ = stage0.intervention_effects(model, row)
            differences.extend(
                abs(scores["candidate_grad_x_activation"][index] - effects[index])
                for index in range(4)
            )
        self.assertTrue(any(value > 1e-3 for value in differences))

    def test_causal_positions_vary_across_non_cls_slots(self):
        position_sets = {
            row.causal_positions
            for row in stage0.examples_for(range(160, 192))
        }
        self.assertGreater(len(position_sets), 8)
        self.assertTrue(any(max(positions) > 4 for positions in position_sets))


if __name__ == "__main__":
    unittest.main()
