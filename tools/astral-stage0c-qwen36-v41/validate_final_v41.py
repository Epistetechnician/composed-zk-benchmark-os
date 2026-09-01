#!/usr/bin/env python3
"""Independently validate the V41 final narrow classification.

State slice: astral-stage0c-qwen36-directional-block-target-v41.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import finalize_v41 as finalizer
import protocol_v41 as protocol


FORBIDDEN_KEYS = frozenset({"prompts", "tokens", "activations", "logits", "traces", "per_family_effects", "per_family_predictions", "credentials", "pii"})


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


def validate(final_root: Path, assessment_root: Path, assessment_validator_receipt: Path, repository_root: Path) -> dict[str, Any]:
    errors: list[str] = []
    final_root = final_root.resolve()
    assessment_root = assessment_root.resolve()
    assessment_validator_receipt = assessment_validator_receipt.resolve()
    try:
        protocol.assert_external(final_root, repository_root)
        result = _strict_json(final_root / "final-result.json")
        errors.extend(_scan_forbidden(result))
        if result.get("protocol") != protocol.PROTOCOL_ID or result.get("state_slice") != protocol.STATE_SLICE:
            errors.append("protocol_or_state_slice_mismatch")
        if result.get("assessment_effects_present") is not True or result.get("assessment_effects_measured") is not True or result.get("prediction_locked_before_assessment") is not True:
            errors.append("assessment_state_invalid")
        if result.get("aggregate_only") is not True or result.get("raw_intermediates_retained") is not False:
            errors.append("retention_state_invalid")
        if any(result.get(key) is not False for key in ("network_access", "model_training", "stage_0c", "stage_1", "accepted_evidence")):
            errors.append("claim_boundary_invalid")
        receipt = _strict_json(assessment_validator_receipt)
        if receipt.get("valid") is not True or receipt.get("protocol") != protocol.PROTOCOL_ID or receipt.get("state_slice") != protocol.STATE_SLICE:
            errors.append("assessment_validator_receipt_invalid")
        summary = _strict_json(assessment_root / "assessment-summary.json")
        gates = summary.get("gates", {})
        target = summary.get("target_effect", {})
        if result.get("decision_basis", {}).get("gates") != gates or result.get("decision_basis", {}).get("target_std") != float(target.get("std")):
            errors.append("decision_basis_mismatch")
        if float(target.get("std", math.nan)) < protocol.MIN_ASSESSMENT_TARGET_STD:
            expected_classification = finalizer.TARGET_DEGENERATE_CLASSIFICATION
            expected_ceiling = finalizer.NO_CANDIDATE_CLAIM_CEILING
        elif isinstance(gates, dict) and gates and all(gates.values()):
            expected_classification = finalizer.TARGET_VALIDITY_CLASSIFICATION
            expected_ceiling = finalizer.TARGET_VALIDITY_CLAIM_CEILING
        else:
            expected_classification = finalizer.DEVELOPMENT_NO_CANDIDATE_CLASSIFICATION
            expected_ceiling = finalizer.NO_CANDIDATE_CLAIM_CEILING
        if result.get("classification") != expected_classification or result.get("claim_ceiling") != expected_ceiling:
            errors.append("classification_or_ceiling_mismatch")
        expected = {
            "assessment_validator_receipt_sha256": protocol.sha256_file(assessment_validator_receipt),
            "assessment_summary_sha256": protocol.sha256_file(assessment_root / "assessment-summary.json"),
            "assessment_run_manifest_sha256": protocol.sha256_file(assessment_root / "assessment-run-manifest.json"),
            "source_sha256": protocol.sha256_file(Path(finalizer.__file__).resolve()),
        }
        for key, value in expected.items():
            if result.get(key) != value:
                errors.append(f"digest_mismatch:{key}")
        actual_files = {candidate.relative_to(final_root).as_posix() for candidate in final_root.rglob("*") if candidate.is_file()}
        if actual_files != {"final-result.json", "validator-receipt.json"} and actual_files != {"final-result.json"}:
            errors.append("output_census_mismatch")
    except (OSError, json.JSONDecodeError, TypeError, KeyError, AttributeError, protocol.ProtocolError, ValueError) as exc:
        errors.append(f"validator_error:{type(exc).__name__}:{exc}")
    return {
        "protocol": protocol.PROTOCOL_ID,
        "state_slice": protocol.STATE_SLICE,
        "classification": "FinalClassificationValid" if not errors else "FinalClassificationInvalid",
        "valid": not errors,
        "errors": errors,
        "final_result_sha256": protocol.sha256_file(final_root / "final-result.json") if (final_root / "final-result.json").is_file() else None,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("final_root", type=Path)
    parser.add_argument("--assessment-root", type=Path, required=True)
    parser.add_argument("--assessment-validator-receipt", type=Path, required=True)
    parser.add_argument("--repository-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--write-receipt", action="store_true")
    args = parser.parse_args(argv)
    receipt = validate(args.final_root, args.assessment_root, args.assessment_validator_receipt, args.repository_root)
    if args.write_receipt:
        protocol.write_json(args.final_root.resolve() / "validator-receipt.json", receipt)
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0 if receipt["valid"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
