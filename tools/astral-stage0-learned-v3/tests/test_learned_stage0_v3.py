from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import learned_stage0_v3 as v3
import run_learned_stage0_v3 as runner


class V3CapacityTests(unittest.TestCase):
    def test_seed_panels_are_disjoint(self):
        panels = [
            set(v3.SELECTION_SEEDS),
            set(v3.QUALIFICATION_SEEDS),
            {v3.TEST_SEED},
            set(v3.FUTURE_SCIENTIFIC_SEEDS),
        ]
        for index, panel in enumerate(panels):
            for other in panels[index + 1 :]:
                self.assertFalse(panel & other)

    def test_forward_contract_and_architecture_ids(self):
        for config in v3.CONFIGS:
            model = v3.CapacityTransformer(config, v3.TEST_SEED)
            logits, heads, attention = model(torch.zeros((2, 12), dtype=torch.long))
            self.assertEqual(tuple(logits.shape), (2, 2))
            self.assertEqual(tuple(heads.shape), (2, 4, config.width // 4))
            self.assertEqual(tuple(attention.shape), (2, 4, 12))
            self.assertNotEqual(config.architecture_id, "astral.learned-tiny-transformer.v1")

    def test_training_requests_only_development_families(self):
        original = v3.examples_for
        requested = []

        def spy(families):
            values = list(families)
            requested.extend(values)
            return original(range(values[0], values[-1] + 1))

        with patch.object(v3, "examples_for", side_effect=spy):
            _, metrics = v3.train_selected(v3.CONFIGS[0], v3.TEST_SEED, updates=25)
        self.assertTrue(requested)
        self.assertLess(max(requested), 192)
        self.assertEqual(metrics["updates"], 25)

    def test_source_has_no_scientific_execution_imports(self):
        source = (ROOT / "learned_stage0_v3.py").read_text()
        for forbidden in (
            "score_example",
            "intervention_effects",
            "run_learned_stage0_v2",
            "range(192",
            "range(320",
            "range(384",
        ):
            self.assertNotIn(forbidden, source)

    def test_output_rejects_repository_and_symlink_roots(self):
        with self.assertRaisesRegex(ValueError, "repository-external"):
            runner.prepare_output(ROOT / "forbidden-output")
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "target"
            target.mkdir()
            link = Path(directory) / "link"
            link.symlink_to(target, target_is_directory=True)
            with self.assertRaisesRegex(ValueError, "real directory"):
                runner.prepare_output(link)


if __name__ == "__main__":
    unittest.main()
