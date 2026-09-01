#!/usr/bin/env python3
"""Independently validate V45 qualification custody and gates.

State slice: astral-stage0c-qwen36-response-anchored-causal-target-v45.
"""

from __future__ import annotations

import argparse
import importlib.metadata
import json
import math
from pathlib import Path
from typing import Any

import protocol_v45 as protocol


def _module_sha(module: Any) -> str:
    source = getattr(module, "__file__", None)
    if not isinstance(source, str):
        raise protocol.ProtocolError("runtime module has no source path")
    return protocol.sha256_file(Path(source).resolve())


def _receipt(errors: list[str], digest: str | None) -> dict[str, Any]:
    return {
        "protocol": protocol.PROTOCOL_ID,
        "state_slice": protocol.STATE_SLICE,
        "claim_ceiling": "LocalDevelopmentV45QualificationValidated",
        "classification": "QualificationValidated" if not errors else "QualificationInvalid",
        "valid": not errors,
        "errors": errors,
        "qualification_result_sha256": digest,
        "independent_validation": True,
    }


def validate(qualification_root: Path, model_root: Path, repository_root: Path) -> dict[str, Any]:
    errors: list[str] = []
    qualification_root = qualification_root.resolve()
    model_root = model_root.resolve()
    try:
        protocol.assert_external(qualification_root, repository_root)
        protocol.assert_external(model_root, repository_root)
        result_path = qualification_root / "qualification-result.json"
        result = protocol.read_json(result_path)
        if not isinstance(result, dict):
            raise protocol.ProtocolError("qualification result must be an object")
        if result.get("protocol") != protocol.PROTOCOL_ID or result.get("state_slice") != protocol.STATE_SLICE:
            errors.append("protocol_or_state_slice_mismatch")
        if result.get("qualification_id") != protocol.QUALIFICATION_ID:
            errors.append("qualification_id_mismatch")
        manifest = protocol.model_manifest(model_root)
        if result.get("model_manifest_sha256") != manifest.get("manifest_sha256"):
            errors.append("model_manifest_binding_mismatch")
        if result.get("protocol_source_sha256") != protocol.sha256_file(Path(protocol.__file__).resolve()):
            errors.append("protocol_source_digest_mismatch")
        if result.get("model_root_basename") != protocol.MODEL_BASENAME:
            errors.append("model_basename_mismatch")
        if result.get("config_sha256") != protocol.sha256_file(model_root / "config.json"):
            errors.append("config_digest_mismatch")
        config = protocol.read_json(model_root / "config.json")
        if config.get("architectures") != [protocol.MODEL_ARCHITECTURE]:
            errors.append("model_architecture_mismatch")
        import mlx_lm.models.qwen3_5 as qwen3_5
        import mlx_lm.models.qwen3_5_moe as qwen3_5_moe

        runtime = result.get("runtime")
        expected_runtime = {
            "python": runtime.get("python") if isinstance(runtime, dict) else None,
            "mlx": importlib.metadata.version("mlx"),
            "mlx_lm": importlib.metadata.version("mlx-lm"),
            "qwen3_5_source_sha256": _module_sha(qwen3_5),
            "qwen3_5_moe_source_sha256": _module_sha(qwen3_5_moe),
        }
        if not isinstance(runtime, dict) or any(runtime.get(key) != value for key, value in expected_runtime.items()):
            errors.append("runtime_source_binding_mismatch")
        if not isinstance(runtime, dict) or runtime.get("mlx") != "0.31.2" or runtime.get("mlx_lm") != "0.31.3":
            errors.append("runtime_version_mismatch")
        for field in ("native_parity_max_abs_logit_delta", "deterministic_repeat_max_abs_logit_delta", "noop_replacement_max_abs_logit_delta"):
            value = result.get(field)
            if not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(float(value)) or value < 0:
                errors.append(f"invalid_numeric_field:{field}")
        expected_layers = {str(layer) for layer in protocol.CANDIDATE_LAYERS}
        for field in ("zero_replacement_max_abs_logit_delta_by_layer", "nonzero_reach_max_abs_logit_delta_by_layer"):
            value = result.get(field)
            if not isinstance(value, dict) or set(value) != expected_layers or any(not isinstance(item, (int, float)) or isinstance(item, bool) or not math.isfinite(float(item)) or item < 0 for item in value.values()):
                errors.append(f"invalid_layer_field:{field}")
        if result.get("candidate_layers") != list(protocol.CANDIDATE_LAYERS) or result.get("position_name") != protocol.POSITION_NAME or result.get("content_anchor_offset") != protocol.CONTENT_ANCHOR_OFFSET or result.get("position_rule") != protocol.POSITION_RULE:
            errors.append("target_binding_mismatch")
        if result.get("observed_layer_count") != protocol.EXPECTED_LAYER_COUNT or result.get("observed_hidden_width") != protocol.EXPECTED_HIDDEN_WIDTH:
            errors.append("shape_binding_mismatch")
        gates = result.get("gates")
        expected_gates = {
            "native_parity", "deterministic_repeat", "noop_replacement", "zero_replacement_reached",
            "nonzero_reach", "capture_shape", "replacement_shape", "model_architecture", "runtime_exact",
            "model_source_custody", "no_network_access", "no_model_training", "no_raw_intermediates_retained",
        }
        if not isinstance(gates, dict) or set(gates) != expected_gates or any(value is not True for value in gates.values()):
            errors.append("qualification_gates_not_all_passed")
        if result.get("classification") != "InstrumentFeasibility":
            errors.append("qualification_classification_not_feasible")
        if result.get("assessment_opened") is not False:
            errors.append("assessment_opened")
        expected_files = {"qualification-result.json"}
        actual_files = {candidate.relative_to(qualification_root).as_posix() for candidate in qualification_root.rglob("*") if candidate.is_file()}
        if actual_files not in (expected_files, expected_files | {"validator-receipt.json"}):
            errors.append("output_census_invalid")
    except (OSError, ImportError, KeyError, TypeError, ValueError, json.JSONDecodeError, protocol.ProtocolError) as exc:
        errors.append(f"validator_error:{type(exc).__name__}:{exc}")
    digest = protocol.sha256_file(qualification_root / "qualification-result.json") if (qualification_root / "qualification-result.json").is_file() else None
    return _receipt(errors, digest)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("qualification_root", type=Path)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--repository-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--write-receipt", action="store_true")
    args = parser.parse_args(argv)
    receipt = validate(args.qualification_root, args.model, args.repository_root.resolve())
    if args.write_receipt:
        protocol.write_json(args.qualification_root.resolve() / "validator-receipt.json", receipt)
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0 if receipt["valid"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
