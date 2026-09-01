#!/usr/bin/env python3
"""Independently validate V42 qualification custody and gates.

State slice: astral-stage0c-qwen36-causal-target-reliability-v42.
"""

from __future__ import annotations

import argparse
import importlib.metadata
import json
from pathlib import Path
from typing import Any

import protocol_v42 as protocol


def _module_sha(module: Any) -> str:
    source = getattr(module, "__file__", None)
    if not isinstance(source, str):
        raise protocol.ProtocolError("runtime module has no source path")
    return protocol.sha256_file(Path(source).resolve())


def _receipt(errors: list[str], result_digest: str | None) -> dict[str, Any]:
    return {
        "protocol": protocol.PROTOCOL_ID,
        "state_slice": protocol.STATE_SLICE,
        "claim_ceiling": "LocalDevelopmentV42QualificationValidated",
        "classification": "QualificationValidated" if not errors else "QualificationInvalid",
        "valid": not errors,
        "errors": errors,
        "qualification_result_sha256": result_digest,
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
        if not isinstance(runtime, dict) or runtime.get("mlx") != expected_runtime["mlx"] or runtime.get("mlx_lm") != expected_runtime["mlx_lm"] or runtime.get("qwen3_5_source_sha256") != expected_runtime["qwen3_5_source_sha256"] or runtime.get("qwen3_5_moe_source_sha256") != expected_runtime["qwen3_5_moe_source_sha256"]:
            errors.append("runtime_source_binding_mismatch")
        if not isinstance(runtime, dict) or runtime.get("mlx") != "0.31.2" or runtime.get("mlx_lm") != "0.31.3":
            errors.append("runtime_version_mismatch")
        numeric_fields = (
            "native_parity_max_abs_logit_delta",
            "deterministic_repeat_max_abs_logit_delta",
        )
        for field in numeric_fields:
            value = result.get(field)
            if not isinstance(value, (int, float)) or isinstance(value, bool) or value < 0:
                errors.append(f"invalid_numeric_field:{field}")
        for field in ("zero_replacement_max_abs_logit_delta_by_layer", "nonzero_reach_max_abs_logit_delta_by_layer"):
            value = result.get(field)
            if not isinstance(value, dict) or set(value) != {str(layer) for layer in protocol.QUALIFICATION_LAYERS}:
                errors.append(f"invalid_layer_field:{field}")
        if result.get("target_layer") != protocol.TARGET_LAYER or result.get("observed_layer_count") != protocol.EXPECTED_LAYER_COUNT or result.get("observed_hidden_width") != protocol.EXPECTED_HIDDEN_WIDTH:
            errors.append("shape_or_target_binding_mismatch")
        gates = result.get("gates")
        if not isinstance(gates, dict) or set(gates) != {
            "native_parity",
            "deterministic_repeat",
            "zero_replacement",
            "nonzero_reach",
            "capture_shape",
            "replacement_shape",
            "model_architecture",
            "runtime_exact",
            "model_source_custody",
            "no_network_access",
            "no_model_training",
            "no_raw_intermediates_retained",
        } or any(value is not True for value in gates.values()):
            errors.append("qualification_gates_not_all_passed")
        expected_files = {"qualification-result.json"}
        actual_files = {
            candidate.relative_to(qualification_root).as_posix()
            for candidate in qualification_root.rglob("*")
            if candidate.is_file()
        }
        if not actual_files <= expected_files | {"validator-receipt.json"} or not expected_files <= actual_files:
            errors.append("output_census_invalid")
    except (OSError, ImportError, KeyError, TypeError, ValueError, json.JSONDecodeError, protocol.ProtocolError) as exc:
        errors.append(f"validator_error:{type(exc).__name__}:{exc}")
    result_digest = protocol.sha256_file(qualification_root / "qualification-result.json") if (qualification_root / "qualification-result.json").is_file() else None
    return _receipt(errors, result_digest)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("qualification_root", type=Path)
    parser.add_argument("--model", type=Path, default=Path("/Users/shaanp/.lmstudio/models/lmstudio-community/Qwen3.6-35B-A3B-MLX-4bit"))
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
