#!/usr/bin/env python3
"""Independently validate an aggregate-only V39 qualification result.

State slice: astral-stage0c-qwen36-layer-effect-v39.

This validator does not rerun the model.  It independently rechecks the
result envelope, external model manifest, runtime versions/source digests,
runner/protocol source digests, qualification gates, and output census.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib
import importlib.metadata
import json
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import protocol_v39 as protocol


STRUCTURAL_ERROR_PREFIXES = (
    "unknown_result_fields:",
    "missing_result_fields:",
    "forbidden_raw_or_sensitive_field",
    "protocol_mismatch",
    "state_slice_mismatch",
    "claim_ceiling_mismatch",
    "model_id_mismatch",
    "prompt_count_mismatch",
    "prompt_registry_sha256_mismatch",
    "layer_count_mismatch",
    "hidden_width_observed_mismatch",
    "target_layer_mismatch",
    "model_manifest_sha256_invalid",
    "model_root_invalid",
    "model_file_count_invalid",
    "runtime_shape_invalid",
    "source_shape_invalid",
    "source_digest_invalid",
    "capture_shape_ok_failed",
    "replacement_shape_ok_failed",
    "native_parity_max_abs_logit_delta_invalid",
    "baseline_repeat_max_abs_logit_delta_invalid",
    "zero_replacement_max_abs_logit_delta_invalid",
    "nonzero_replacement_max_abs_logit_delta_invalid",
    "assessment_opened_failed",
    "prediction_locked_before_assessment_failed",
    "scientific_assessment_failed",
    "model_training_failed",
    "network_access_failed",
    "raw_intermediates_retained_failed",
    "aggregate_only_failed",
    "stage_0c_failed",
    "stage_1_failed",
    "accepted_evidence_failed",
    "model_loaded_failed",
    "reasons_invalid",
    "classification_invalid",
)


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _strict_json(path: Path) -> Any:
    def reject_constant(value: str) -> Any:
        raise ValueError(f"non-standard JSON constant: {value}")

    def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        value: dict[str, Any] = {}
        for key, item in pairs:
            if key in value:
                raise ValueError(f"duplicate JSON key: {key}")
            value[key] = item
        return value

    return json.loads(
        path.read_text(encoding="utf-8"),
        object_pairs_hook=reject_duplicate_keys,
        parse_constant=reject_constant,
    )


def _runtime_source_digests() -> dict[str, str]:
    modules = {
        "qwen3_5_source_sha256": importlib.import_module("mlx_lm.models.qwen3_5"),
        "qwen3_5_moe_source_sha256": importlib.import_module("mlx_lm.models.qwen3_5_moe"),
    }
    return {
        key: protocol.sha256_file(Path(module.__file__).resolve())
        for key, module in modules.items()
    }


def _validate_output_census(root: Path) -> list[str]:
    allowed = {"qualification-result.json", "validator-receipt.json"}
    actual = {
        path.name
        for path in root.iterdir()
        if path.is_file() and not path.is_symlink()
    }
    return [f"unexpected_output_files:{','.join(sorted(actual - allowed))}"] if actual - allowed else []


def validate(result: object, result_path: Path, model_root: Path, repository_root: Path) -> dict[str, Any]:
    errors: list[str] = []
    if result_path.name != "qualification-result.json":
        errors.append("result_filename_invalid")
    errors.extend(_validate_output_census(result_path.parent))
    gate_errors = protocol.qualification_gate_errors(result)
    if isinstance(result, dict) and result.get("classification") == "InstrumentQualificationFailed":
        structural = [
            error for error in gate_errors
            if any(error == prefix or error.startswith(prefix) for prefix in STRUCTURAL_ERROR_PREFIXES)
        ]
        if structural:
            errors.extend(structural)
        if not result.get("reasons"):
            errors.append("failed_classification_without_reason")
        if not all(reason in gate_errors for reason in result.get("reasons", [])):
            errors.append("failure_reasons_not_recomputed")
    else:
        errors.extend(gate_errors)

    model_root = model_root.resolve()
    try:
        protocol.assert_external(model_root, repository_root)
    except ValueError as exc:
        errors.append(str(exc))
    if isinstance(result, dict) and result.get("model_root") != str(model_root):
        errors.append("model_root_binding_mismatch")
    try:
        manifest = protocol.model_manifest(model_root)
    except (OSError, ValueError) as exc:
        errors.append(f"model_manifest_unreadable:{type(exc).__name__}")
        manifest = None
    if isinstance(result, dict) and manifest is not None:
        if result.get("model_manifest_sha256") != manifest["manifest_sha256"]:
            errors.append("model_manifest_digest_mismatch")
        if result.get("model_file_count") != manifest["file_count"]:
            errors.append("model_file_count_mismatch")
        try:
            config = _strict_json(model_root / "config.json")
        except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
            errors.append(f"model_config_unreadable:{type(exc).__name__}")
        else:
            if not isinstance(config, dict) or config.get("architectures") != [protocol.MODEL_ARCHITECTURE]:
                errors.append("model_architecture_binding_mismatch")

    if isinstance(result, dict):
        source = result.get("source")
        if isinstance(source, dict):
            expected_sources = {
                "runner_sha256": protocol.sha256_file(HERE / "qualify_v39.py"),
                "protocol_sha256": protocol.sha256_file(HERE / "protocol_v39.py"),
            }
            for key, expected in expected_sources.items():
                if source.get(key) != expected:
                    errors.append(f"{key}_mismatch")
        runtime = result.get("runtime")
        if isinstance(runtime, dict):
            if runtime.get("mlx") != importlib.metadata.version("mlx"):
                errors.append("mlx_runtime_binding_mismatch")
            if runtime.get("mlx_lm") != importlib.metadata.version("mlx-lm"):
                errors.append("mlx_lm_runtime_binding_mismatch")
            try:
                expected_runtime_sources = _runtime_source_digests()
            except (ImportError, OSError, ValueError) as exc:
                errors.append(f"runtime_source_unreadable:{type(exc).__name__}")
            else:
                for key, expected in expected_runtime_sources.items():
                    if runtime.get(key) != expected:
                        errors.append(f"{key}_mismatch")

    receipt = {
        "protocol": protocol.PROTOCOL_ID,
        "state_slice": protocol.STATE_SLICE,
        "claim_ceiling": protocol.QUALIFICATION_CLAIM_CEILING,
        "valid": not errors,
        "classification": result.get("classification") if isinstance(result, dict) else None,
        "result_sha256": _sha256_bytes(result_path.read_bytes()),
        "model_manifest_sha256": manifest["manifest_sha256"] if manifest is not None else None,
        "errors": errors,
    }
    return receipt


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("result", type=Path)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument(
        "--repository-root",
        type=Path,
        default=Path(__file__).resolve().parents[2],
    )
    parser.add_argument("--write-receipt", action="store_true")
    args = parser.parse_args(argv)
    try:
        result = _strict_json(args.result)
        receipt = validate(
            result,
            args.result.resolve(),
            args.model,
            args.repository_root,
        )
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        receipt = {
            "protocol": protocol.PROTOCOL_ID,
            "state_slice": protocol.STATE_SLICE,
            "claim_ceiling": protocol.QUALIFICATION_CLAIM_CEILING,
            "valid": False,
            "errors": [f"validator_error:{type(exc).__name__}:{exc}"],
        }
    if args.write_receipt:
        receipt_path = args.result.resolve().parent / "validator-receipt.json"
        receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0 if receipt["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
