"""Tests for the fail-closed V26 actor-custody preflight.

State slice: astral-causal-channel-separation-v26-execution-preflight.
"""

from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).parents[1] / "preflight_v26.py"
SPEC = importlib.util.spec_from_file_location("preflight_v26", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

VALIDATOR_PATH = Path(__file__).parents[1] / "validator_v26.py"
VALIDATOR_SPEC = importlib.util.spec_from_file_location("validator_v26", VALIDATOR_PATH)
assert VALIDATOR_SPEC is not None and VALIDATOR_SPEC.loader is not None
VALIDATOR = importlib.util.module_from_spec(VALIDATOR_SPEC)
VALIDATOR_SPEC.loader.exec_module(VALIDATOR)


def write_model(root: Path, name: str, config: dict) -> Path:
    model_dir = root / name
    model_dir.mkdir(parents=True)
    (model_dir / "config.json").write_text(json.dumps(config), encoding="utf-8")
    (model_dir / "model.safetensors").write_bytes(b"synthetic-test-weight")
    return model_dir


class V26PreflightTests(unittest.TestCase):
    def test_reserved_prior_actor_is_not_eligible(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_model(root, "old", {
                "model_type": "qwen2",
                "architectures": ["Qwen2ForCausalLM"],
            })
            result = MODULE.inventory((root,))
            self.assertEqual(result["classification"], MODULE.NO_FRESH_ACTOR)
            self.assertEqual(result["eligible_actor_count"], 0)
            self.assertIn("reserved_signature:V22", result["candidates"][0]["reasons"])

    def test_one_distinct_actor_is_ready_for_instrument_qualification(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_model(root, "fresh", {
                "model_type": "synthetic_causal_decoder",
                "architectures": ["SyntheticCausalDecoderForCausalLM"],
            })
            result = MODULE.inventory((root,))
            self.assertEqual(result["classification"], MODULE.READY)
            self.assertEqual(result["eligible_actor_count"], 1)
            self.assertFalse(result["model_execution"])

    def test_malformed_config_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            model_dir = root / "broken"
            model_dir.mkdir()
            (model_dir / "config.json").write_text("{", encoding="utf-8")
            (model_dir / "model.safetensors").write_bytes(b"synthetic-test-weight")
            result = MODULE.inventory((root,))
            self.assertEqual(result["classification"], MODULE.NO_FRESH_ACTOR)
            self.assertIn("malformed_config:JSONDecodeError", result["candidates"][0]["reasons"])

    def test_multiple_fresh_actors_are_ambiguous(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in ("fresh-a", "fresh-b"):
                write_model(root, name, {
                    "model_type": name,
                    "architectures": ["FreshDecoderForCausalLM"],
                })
            result = MODULE.inventory((root,))
            self.assertEqual(result["classification"], MODULE.NO_FRESH_ACTOR)
            self.assertIn("ambiguous_fresh_actor_inventory", result["reasons"])

    def test_independent_validator_accepts_no_fresh_actor_stop(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            result = MODULE.inventory((Path(directory),))
            self.assertEqual(VALIDATOR.validate(result), [])

    def test_independent_validator_rejects_claim_or_execution_escalation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            result = MODULE.inventory((Path(directory),))
            result["claim_ceiling"] = "Stage0C"
            result["model_execution"] = True
            errors = VALIDATOR.validate(result)
            self.assertIn("claim_ceiling_mismatch", errors)
            self.assertIn("model_execution_mismatch", errors)


if __name__ == "__main__":
    unittest.main()
