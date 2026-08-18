"""Hermetic V29 tests. State slice: astral-calibrated-opaque-causal-channel-v29-tests."""
from __future__ import annotations
import importlib.util, tempfile, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
def load(name: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / f"{name}.py"); assert spec and spec.loader
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module); return module

class V29Tests(unittest.TestCase):
    def test_ridge_selection_is_tune_only_and_claim_bounded(self):
        aggregate = load("aggregate_v29")
        rows = [{"trial": i, "split": 0 if i < 16 else (1 if i < 24 else 2), "target": float(i % 5), "full": [float(i), float(i % 3), 1.0, -1.0], "opaque": [float(i), float(i % 3)], "finite": True} for i in range(32)]
        result = aggregate.aggregate(rows)
        self.assertTrue(result["prediction_locked_before_assessment"])
        self.assertFalse(result["raw_intermediate_retained"])
        self.assertEqual(result["claim_ceiling"], "LocalDevelopmentCalibratedOpaqueCausalChannel")

    def test_validator_rejects_stage_language(self):
        validator = load("validator_v29")
        self.assertIn("claim_ceiling_mismatch", validator.validate({"claim_ceiling": "Stage1"}))

    def test_validator_rejects_missing_utility_gate(self):
        validator = load("validator_v29")
        errors = validator.validate({"classification": "CalibratedOpaqueCausalChannelDiagnosticOnly"})
        self.assertIn("utility_gate_missing_or_non_boolean", errors)

    def test_preflight_rejects_symlink_actor(self):
        preflight = load("preflight_v29")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); header = root / "llama.h"; library = root / "libllama.dylib"; actor = root / "actor.gguf"
            header.write_text("llama_backend_init", encoding="utf-8"); library.write_bytes(b"not-a-library"); actor.write_bytes(b"actor")
            link = root / "link.gguf"; link.symlink_to(actor)
            result = preflight.preflight(header, library, link)
            self.assertEqual(result["classification"], "CalibratedOpaqueCausalChannelPreflightFailed")
            self.assertIn("actor_not_regular_local_file", result["reasons"])

if __name__ == "__main__": unittest.main()
