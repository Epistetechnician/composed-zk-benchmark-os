"""Hermetic V28 contract tests.

State slice: astral-opaque-causal-channel-separation-v28-tests.
"""

from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load(name: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / f"{name}.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class V28Tests(unittest.TestCase):
    def test_aggregate_locks_before_assessment_and_emits_only_aggregate_fields(self) -> None:
        aggregate = load("aggregate_v28")
        rows = []
        for trial in range(16):
            rows.append({
                "trial": trial,
                "split": 0 if trial < 8 else (1 if trial < 12 else 2),
                "target": float(trial + 1),
                "full": [float(trial + offset) for offset in range(16)],
                "opaque": [float(trial + offset) for offset in range(4)],
                "finite": True,
            })
        result = aggregate.aggregate(rows)
        self.assertTrue(result["prediction_locked_before_assessment"])
        self.assertFalse(result["raw_intermediate_retained"])
        self.assertEqual(result["claim_ceiling"], "LocalDevelopmentOpaqueCausalChannelSeparation")

    def test_validator_rejects_claim_escalation(self) -> None:
        validator = load("validator_v28")
        self.assertIn("claim_ceiling_mismatch", validator.validate({"claim_ceiling": "Stage1"}))

    def test_validator_rejects_missing_gate_fields(self) -> None:
        validator = load("validator_v28")
        errors = validator.validate({})
        self.assertIn("protocol_mismatch", errors)
        self.assertIn("utility_gate_missing_or_non_boolean", errors)
        self.assertIn("separation_gate_missing_or_non_boolean", errors)

    def test_preflight_marks_symlink_actor_invalid(self) -> None:
        preflight = load("preflight_v28")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            header = root / "llama.h"
            library = root / "libllama.dylib"
            actor = root / "actor.gguf"
            header.write_text("llama_backend_init llama_model_n_embd", encoding="utf-8")
            library.write_bytes(b"not a library")
            actor.write_bytes(b"actor")
            symlink = root / "actor-link.gguf"
            symlink.symlink_to(actor)
            result = preflight.preflight(header, library, symlink)
            self.assertEqual(result["classification"], "OpaqueCausalChannelSeparationPreflightFailed")
            self.assertIn("actor_not_regular_local_file", result["reasons"])


if __name__ == "__main__":
    unittest.main()
