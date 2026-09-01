"""Hermetic V39 protocol and validator-envelope tests.

State slice: astral-stage0c-qwen36-layer-effect-v39.
"""

from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parents[1]


def load_module(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, HERE / filename)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


PROTOCOL = load_module("astral_stage0c_qwen36_protocol_v39", "protocol_v39.py")
VALIDATOR = load_module("astral_stage0c_qwen36_validator_v39", "validator_v39.py")


def result_template() -> dict:
    return {
        "protocol": PROTOCOL.PROTOCOL_ID,
        "state_slice": PROTOCOL.STATE_SLICE,
        "claim_ceiling": PROTOCOL.QUALIFICATION_CLAIM_CEILING,
        "classification": "InstrumentQualificationPassed",
        "model_id": PROTOCOL.MODEL_ID,
        "model_architecture": PROTOCOL.MODEL_ARCHITECTURE,
        "model_root": "/external/model",
        "model_manifest_sha256": "a" * 64,
        "model_file_count": 4,
        "runtime": {
            "python": "3.14.5",
            "mlx": PROTOCOL.EXPECTED_MLX,
            "mlx_lm": PROTOCOL.EXPECTED_MLX_LM,
            "qwen3_5_source_sha256": "b" * 64,
            "qwen3_5_moe_source_sha256": "c" * 64,
        },
        "source": {"runner_sha256": "d" * 64, "protocol_sha256": "e" * 64},
        "prompt_count": len(PROTOCOL.QUALIFICATION_PROMPTS),
        "prompt_registry_sha256": PROTOCOL.QUALIFICATION_PROMPT_DIGEST,
        "layer_count": PROTOCOL.EXPECTED_LAYER_COUNT,
        "hidden_width_observed": PROTOCOL.EXPECTED_HIDDEN_WIDTH,
        "target_layer": PROTOCOL.TARGET_LAYER,
        "capture_shape_ok": True,
        "replacement_shape_ok": True,
        "native_parity_max_abs_logit_delta": 0.0,
        "baseline_repeat_max_abs_logit_delta": 0.0,
        "zero_replacement_max_abs_logit_delta": 0.0,
        "nonzero_replacement_max_abs_logit_delta": 0.5,
        "assessment_opened": False,
        "prediction_locked_before_assessment": False,
        "scientific_assessment": False,
        "model_loaded": True,
        "model_training": False,
        "network_access": False,
        "raw_intermediates_retained": False,
        "aggregate_only": True,
        "stage_0c": False,
        "stage_1": False,
        "accepted_evidence": False,
        "reasons": [],
    }


class ProtocolV39Tests(unittest.TestCase):
    def test_passed_result_has_no_gate_errors(self) -> None:
        self.assertEqual(PROTOCOL.qualification_gate_errors(result_template()), [])

    def test_each_measurement_gate_stops_without_opening_assessment(self) -> None:
        for field, error in (
            ("native_parity_max_abs_logit_delta", "native_parity_gate_failed"),
            ("baseline_repeat_max_abs_logit_delta", "repeatability_gate_failed"),
            ("zero_replacement_max_abs_logit_delta", "zero_replacement_gate_failed"),
            ("nonzero_replacement_max_abs_logit_delta", "nonzero_logit_reach_gate_failed"),
        ):
            result = result_template()
            result["classification"] = "InstrumentQualificationFailed"
            result[field] = 1.0 if field != "nonzero_replacement_max_abs_logit_delta" else 0.0
            result["reasons"] = PROTOCOL.qualification_gate_errors(result)
            errors = PROTOCOL.qualification_gate_errors(result)
            self.assertIn(error, errors)
            self.assertFalse(result["assessment_opened"])

    def test_forbidden_raw_field_is_rejected(self) -> None:
        result = result_template()
        result["raw_logits"] = ["not retained"]
        self.assertIn(
            "forbidden_raw_or_sensitive_field",
            PROTOCOL.qualification_gate_errors(result),
        )

    def test_validator_strict_json_rejects_duplicate_keys(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "result.json"
            path.write_text('{"protocol":"x","protocol":"y"}', encoding="utf-8")
            with self.assertRaises(ValueError):
                VALIDATOR._strict_json(path)

    def test_result_keys_are_explicit(self) -> None:
        self.assertEqual(set(result_template()), PROTOCOL.RESULT_KEYS)


if __name__ == "__main__":
    unittest.main()
