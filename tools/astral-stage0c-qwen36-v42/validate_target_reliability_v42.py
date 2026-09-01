#!/usr/bin/env python3
"""Independently validate the aggregate-only V42 reliability result.

State slice: astral-stage0c-qwen36-causal-target-reliability-v42.

This validator never accepts per-family effects, activations, logits, prompts,
or predictions. It checks custody bindings, lock ordering, aggregate schema,
and the preregistered gate arithmetic.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import protocol_v42 as protocol
import validate_panel_v42 as panel_validator
import validate_qualification_v42 as qualification_validator
import run_target_reliability_v42 as runner


FORBIDDEN_KEYS = frozenset(
    {
        "prompts",
        "source_excerpts",
        "tokens",
        "raw_activations",
        "activations",
        "raw_logits",
        "logits",
        "raw_traces",
        "traces",
        "per_family_effects",
        "per_family_predictions",
        "predictions",
        "credentials",
        "pii",
    }
)


def _strict_json(path: Path) -> Any:
    def reject_constant(value: str) -> Any:
        raise ValueError(f"non-standard JSON constant: {value}")

    def reject_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate JSON key: {key}")
            result[key] = value
        return result

    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=reject_duplicates, parse_constant=reject_constant)


def _scan_forbidden(value: Any, path: str = "$") -> list[str]:
    errors: list[str] = []
    if isinstance(value, dict):
        for key, nested in value.items():
            if key in FORBIDDEN_KEYS:
                errors.append(f"forbidden_key:{path}.{key}")
            errors.extend(_scan_forbidden(nested, f"{path}.{key}"))
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            errors.extend(_scan_forbidden(nested, f"{path}[{index}]"))
    return errors


def _finite(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def _receipt(errors: list[str], result_digest: str | None) -> dict[str, Any]:
    return {
        "protocol": protocol.PROTOCOL_ID,
        "state_slice": protocol.STATE_SLICE,
        "claim_ceiling": "LocalDevelopmentV42ReliabilityValidated",
        "classification": "ReliabilityValidated" if not errors else "ReliabilityInvalid",
        "valid": not errors,
        "errors": errors,
        "reliability_result_sha256": result_digest,
        "independent_validation": True,
    }


def _check_split(split: dict[str, Any], errors: list[str], label: str) -> None:
    if split.get("family_count") != protocol.FAMILIES_PER_SPLIT:
        errors.append(f"family_count_mismatch:{label}")
    if split.get("document_count") != protocol.DOCUMENTS_PER_SPLIT:
        errors.append(f"document_count_mismatch:{label}")
    reliability = split.get("reliability")
    if not isinstance(reliability, dict):
        errors.append(f"reliability_missing:{label}")
        return
    for key in (
        "wrapper_correlation",
        "wrapper_sign_agreement",
        "bootstrap_correlation_lower_95",
        "wrapper_alpha_effect_std",
        "wrapper_beta_effect_std",
        "target_effect_std_min",
    ):
        if not _finite(reliability.get(key)):
            errors.append(f"reliability_nonfinite:{label}:{key}")
    gates = reliability.get("gates")
    if not isinstance(gates, dict) or set(gates) != {
        "target_effect_non_degenerate",
        "wrapper_correlation",
        "wrapper_sign_agreement",
        "bootstrap_correlation",
    } or any(not isinstance(value, bool) for value in gates.values()):
        errors.append(f"reliability_gates_invalid:{label}")
    controls = split.get("controls")
    if not isinstance(controls, dict):
        errors.append(f"controls_missing:{label}")
        return
    for name in protocol.CONTROL_NAMES:
        if name == "activation_only":
            continue
        summary = controls.get(name)
        if not isinstance(summary, dict):
            errors.append(f"control_missing:{label}:{name}")
            continue
        for key in ("count", "mean", "std", "mean_abs", "min", "max"):
            if key != "count" and not _finite(summary.get(key)):
                errors.append(f"control_nonfinite:{label}:{name}:{key}")
    if controls.get("matched_donor_violations") != 0:
        errors.append(f"matched_donor_violation:{label}")
    if not _finite(controls.get("matched_norm_relative_error_max")) or float(controls["matched_norm_relative_error_max"]) > protocol.MATCH_NORM_RELATIVE_TOLERANCE:
        errors.append(f"matched_norm_invalid:{label}")
    if not _finite(controls.get("repeat_max_abs_effect_delta")) or float(controls["repeat_max_abs_effect_delta"]) > protocol.MAX_REPEAT_ABS_EFFECT_DELTA:
        errors.append(f"repeatability_invalid:{label}")


def validate_with_corpus(
    reliability_root: Path,
    panel_root: Path,
    corpus_root: Path,
    qualification_root: Path,
    model_root: Path,
    repository_root: Path,
) -> dict[str, Any]:
    errors: list[str] = []
    reliability_root = reliability_root.resolve()
    try:
        protocol.assert_external(reliability_root, repository_root)
        panel_receipt = panel_validator.validate(panel_root.resolve(), corpus_root.resolve(), model_root.resolve(), repository_root)
        qualification_receipt = qualification_validator.validate(qualification_root.resolve(), model_root.resolve(), repository_root)
        if not panel_receipt["valid"]:
            errors.append("panel_validation_failed")
        if not qualification_receipt["valid"]:
            errors.append("qualification_validation_failed")
        for path, expected in (
            (panel_root.resolve() / "validator-receipt.json", panel_receipt),
            (qualification_root.resolve() / "validator-receipt.json", qualification_receipt),
        ):
            if not path.is_file() or _strict_json(path) != expected:
                errors.append(f"recorded_receipt_mismatch:{path.name}")
        result_path = reliability_root / "reliability-result.json"
        lock_path = reliability_root / "configuration-lock.json"
        result = _strict_json(result_path)
        lock = _strict_json(lock_path)
        if not isinstance(result, dict) or not isinstance(lock, dict):
            raise protocol.ProtocolError("reliability documents must be objects")
        errors.extend(_scan_forbidden(result))
        errors.extend(_scan_forbidden(lock))
        if result.get("protocol") != protocol.PROTOCOL_ID or result.get("state_slice") != protocol.STATE_SLICE:
            errors.append("result_protocol_or_state_slice_mismatch")
        if lock.get("protocol") != protocol.PROTOCOL_ID or lock.get("state_slice") != protocol.STATE_SLICE:
            errors.append("lock_protocol_or_state_slice_mismatch")
        if result.get("aggregate_only_retention") is not True:
            errors.append("result_retention_field_invalid")
        if lock.get("assessment_effects_locked") is not True:
            errors.append("assessment_lock_not_closed")
        if result.get("panel_manifest_sha256") != protocol.sha256_file(panel_root.resolve() / "panel-manifest.json"):
            errors.append("panel_binding_mismatch")
        if result.get("qualification_result_sha256") != protocol.sha256_file(qualification_root.resolve() / "qualification-result.json"):
            errors.append("qualification_binding_mismatch")
        if result.get("model_manifest_sha256") != protocol.model_manifest(model_root.resolve())["manifest_sha256"]:
            errors.append("model_binding_mismatch")
        if lock.get("panel_manifest_sha256") != result.get("panel_manifest_sha256") or lock.get("qualification_result_sha256") != result.get("qualification_result_sha256") or lock.get("model_manifest_sha256") != result.get("model_manifest_sha256"):
            errors.append("lock_custody_binding_mismatch")
        if lock.get("configuration_lock_sha256") != runner._configuration_lock_digest(lock):
            errors.append("configuration_lock_digest_mismatch")
        if lock.get("target_layer") != protocol.TARGET_LAYER or lock.get("wrappers") != list(protocol.WRAPPER_NAMES) or lock.get("controls") != list(protocol.CONTROL_NAMES):
            errors.append("lock_protocol_binding_mismatch")
        if result.get("measured_splits") != ["fit", "tune"]:
            errors.append("assessment_or_split_order_invalid")
        splits = result.get("splits")
        if not isinstance(splits, dict) or set(splits) != {"fit", "tune"}:
            errors.append("split_result_census_invalid")
        else:
            for label in ("fit", "tune"):
                _check_split(splits[label], errors, label)
        tune_gates = result.get("tune_gates")
        if not isinstance(tune_gates, dict) or any(not isinstance(value, bool) for value in tune_gates.values()):
            errors.append("tune_gate_schema_invalid")
        elif result.get("tune_passed") != all(tune_gates.values()):
            errors.append("tune_gate_aggregate_mismatch")
        if result.get("assessment_opened") is not False or result.get("assessment_effects_present") is not False:
            errors.append("assessment_should_be_closed")
        if result.get("classification") != "TargetReliabilityNoCandidate":
            errors.append("unexpected_v42_disposition")
        if result.get("claim_ceiling") != "LocalDevelopmentV42TargetReliabilityNoCandidate":
            errors.append("claim_ceiling_mismatch")
        expected_files = {"configuration-lock.json", "reliability-result.json"}
        actual_files = {candidate.relative_to(reliability_root).as_posix() for candidate in reliability_root.rglob("*") if candidate.is_file()}
        if not actual_files <= expected_files | {"validator-receipt.json"} or not expected_files <= actual_files:
            errors.append("output_census_invalid")
    except (OSError, ImportError, KeyError, TypeError, ValueError, json.JSONDecodeError, protocol.ProtocolError) as exc:
        errors.append(f"validator_error:{type(exc).__name__}:{exc}")
    result_digest = protocol.sha256_file(reliability_root / "reliability-result.json") if (reliability_root / "reliability-result.json").is_file() else None
    return _receipt(errors, result_digest)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("reliability_root", type=Path)
    parser.add_argument("--panel-root", type=Path, required=True)
    parser.add_argument("--corpus-root", type=Path, required=True)
    parser.add_argument("--qualification-root", type=Path, required=True)
    parser.add_argument("--model", type=Path, default=Path("/Users/shaanp/.lmstudio/models/lmstudio-community/Qwen3.6-35B-A3B-MLX-4bit"))
    parser.add_argument("--repository-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--write-receipt", action="store_true")
    args = parser.parse_args(argv)
    receipt = validate_with_corpus(args.reliability_root, args.panel_root, args.corpus_root, args.qualification_root, args.model, args.repository_root.resolve())
    if args.write_receipt:
        protocol.write_json(args.reliability_root.resolve() / "validator-receipt.json", receipt)
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0 if receipt["valid"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
