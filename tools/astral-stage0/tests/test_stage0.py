from __future__ import annotations

import importlib.util
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import artifact_validator
import run_stage0
import stage0


class Stage0Tests(unittest.TestCase):
    def test_exhaustive_actor_is_correct_and_deterministic(self):
        rows = stage0.generate_examples()
        self.assertEqual(len(rows), 3 * 64 * 4)
        for row in rows:
            actor = stage0.PlantedTwoHeadActor(row.seed)
            first = actor.forward(row)
            self.assertEqual(first, actor.forward(row))
            self.assertEqual(first.label, row.expected_label)

    def test_split_is_family_disjoint(self):
        rows = stage0.generate_examples()
        dev = {row.family for row in rows if row.split == "development"}
        evaluation = {row.family for row in rows if row.split == "evaluation"}
        self.assertFalse(dev.intersection(evaluation))
        self.assertEqual(len(dev), 16)
        self.assertEqual(len(evaluation), 48)

    def test_hooks_and_interventions_fail_closed(self):
        row = stage0.generate_examples()[0]
        actor = stage0.PlantedTwoHeadActor(row.seed)
        self.assertEqual(set(actor.forward(row).hooks), set(stage0.COMPONENTS))
        with self.assertRaises(ValueError):
            actor.forward(row, {"unknown": 0.0})
        with self.assertRaises(ValueError):
            actor.forward(row, {stage0.COMPONENTS[0]: float("nan")})
        with self.assertRaises(TypeError):
            actor.forward(row, {stage0.COMPONENTS[0]: True})

    def test_signal_positive_and_distractor_negative_controls(self):
        for row in stage0.generate_examples():
            actor = stage0.PlantedTwoHeadActor(row.seed)
            self.assertLess(actor.ablation_effect(row, "layer0.attn.signal"), -2.9)
            self.assertLess(
                abs(actor.ablation_effect(row, "layer0.attn.distractor")), 0.06
            )

    def test_matched_patch_changes_only_signal_path(self):
        rows = stage0.generate_examples()
        row = rows[0]
        donor = stage0.matched_donor(row, rows)
        actor = stage0.PlantedTwoHeadActor(row.seed)
        self.assertEqual(row.family, donor.family)
        self.assertEqual(row.distractor, donor.distractor)
        self.assertNotEqual(row.signal, donor.signal)
        self.assertLess(
            actor.patch_effect(row, donor, "layer0.attn.signal"), -5.9
        )
        self.assertAlmostEqual(
            actor.patch_effect(row, donor, "layer0.attn.distractor"), 0.0
        )

    def test_tracer_and_controls_are_locked(self):
        row = stage0.generate_examples()[0]
        actor = stage0.PlantedTwoHeadActor(row.seed)
        measured = {
            component: actor.ablation_effect(row, component)
            for component in stage0.COMPONENTS
        }
        predictions = stage0.method_predictions(actor, row)
        self.assertEqual(
            stage0.selected_component(predictions["candidate_tracer"]),
            "layer0.attn.signal",
        )
        self.assertEqual(
            stage0.selected_component(predictions["activation_magnitude"]),
            "layer0.attn.distractor",
        )
        self.assertEqual(
            stage0.selection_regret(measured, predictions["candidate_tracer"]),
            0.0,
        )
        self.assertGreater(
            stage0.selection_regret(
                measured, predictions["activation_magnitude"]
            ),
            2.0,
        )

    def test_bundle_is_valid_and_tampering_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "bundle"
            result = run_stage0.run(output, Path.cwd())
            self.assertTrue(result["valid"])
            self.assertEqual(result["summary"]["gate"], "positive_control_pass")
            summary_path = output / "summary.json"
            summary_path.write_bytes(summary_path.read_bytes() + b" ")
            with self.assertRaises(ValueError):
                artifact_validator.validate_bundle(output)

    def test_semantic_tamper_fails_after_digest_rebinding(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "bundle"
            run_stage0.run(output, Path.cwd())
            summary_path = output / "summary.json"
            summary = json.loads(summary_path.read_text())
            summary["mean_baseline_minus_tracer_regret"] = 999.0
            summary_path.write_bytes(stage0.canonical_json_bytes(summary))
            manifest_path = output / "manifest.json"
            manifest = json.loads(manifest_path.read_text())
            for row in manifest["files"]:
                if row["path"] == "summary.json":
                    raw = summary_path.read_bytes()
                    row["bytes"] = len(raw)
                    row["sha256"] = hashlib.sha256(raw).hexdigest()
            manifest_path.write_bytes(stage0.canonical_json_bytes(manifest))
            with self.assertRaisesRegex(ValueError, "primary estimate drift"):
                artifact_validator.validate_bundle(output)

    def test_output_must_be_empty_and_real(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "bundle"
            output.mkdir()
            (output / "existing").write_text("x")
            with self.assertRaises(ValueError):
                run_stage0.run(output, Path.cwd())


if __name__ == "__main__":
    unittest.main()
