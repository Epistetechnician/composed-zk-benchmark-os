from pathlib import Path
import sys
import unittest

import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import learned_stage0_v13 as v13
from run_learned_stage0_v13 import prepare


class V13Tests(unittest.TestCase):
    def test_boundaries_exclude_all_prior_reserves(self):
        self.assertFalse(set(v13.ALL_SEEDS) & set(v13.RESERVED_SEEDS))
        self.assertTrue(v13.authorized_families(v13.FIT_FAMILIES))
        self.assertTrue(v13.authorized_families(v13.ASSESSMENT_FAMILIES))
        self.assertFalse(v13.authorized_families(v13.RESERVED_FAMILIES))
        self.assertFalse(v13.authorized_families(v13.V12_FAMILIES))

    def test_clean_forward_and_identity_override_parity(self):
        actor = v13.CausalTargetActor(131).eval()
        example = v13.examples_for(range(640, 641))[0]
        tokens = torch.tensor([example.tokens])
        self.assertTrue(v13.clean_parity(actor, tokens))
        clean, sites, _ = actor.forward_sites(tokens)
        for site in v13.SITES:
            changed = actor.forward_sites(tokens, (site, sites[site]))[0]
            self.assertTrue(torch.equal(clean, changed))

    def test_cls_effect_sites_are_complete_and_finite(self):
        actor = v13.CausalTargetActor(131).eval()
        example = v13.examples_for(range(640, 641))[0]
        telemetry = v13.telemetry_rows(actor, example)
        effects = v13.effect_rows(actor, example)
        self.assertEqual(len(telemetry), 10)
        self.assertEqual(len(effects), 10)
        self.assertEqual({row["site"] for row in effects}, set(v13.SITES))
        self.assertEqual({row["operator"] for row in effects}, set(v13.OPERATORS))

    def test_override_validation_fails_closed(self):
        actor = v13.CausalTargetActor(131).eval()
        tokens = torch.tensor([v13.examples_for(range(640, 641))[0].tokens])
        with self.assertRaises(ValueError):
            actor.forward_sites(tokens, ("head0.cls", torch.zeros(1, 7)))
        with self.assertRaises(ValueError):
            actor.forward_sites(tokens, ("unknown", torch.zeros(1, 8)))

    def test_feature_panels_have_exactly_48_inputs(self):
        actor = v13.CausalTargetActor(131).eval()
        example = v13.examples_for(range(640, 641))[0]
        for row in v13.telemetry_rows(actor, example):
            for estimator in ("text_io", "activation_only", "telemetry"):
                self.assertEqual(len(v13.features(row, estimator)), 48)

    def test_ridge_is_deterministic(self):
        train_x = [[float(index), float(index % 2)] for index in range(8)]
        train_y = [2 * row[0] - row[1] for row in train_x]
        test_x = [[8.0, 0.0], [9.0, 1.0]]
        self.assertEqual(
            v13.ridge_predict(train_x, train_y, test_x),
            v13.ridge_predict(train_x, train_y, test_x),
        )

    def test_reserved_seed_rejected_without_training(self):
        with self.assertRaises(ValueError):
            v13.train_actor(v13.RESERVED_SEEDS[0])

    def test_output_root_rejects_repo_ancestor(self):
        repo = Path(__file__).resolve().parents[4]
        with self.assertRaises(ValueError):
            prepare(repo.parent, repo)


if __name__ == "__main__":
    unittest.main()
