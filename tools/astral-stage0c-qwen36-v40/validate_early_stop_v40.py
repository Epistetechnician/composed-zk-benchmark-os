#!/usr/bin/env python3
"""Independently validate the V40 early-stop final disposition.

State slice: astral-stage0c-qwen36-intervention-conditioned-target-v40.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import finalize_early_stop_v40 as finalizer
import protocol_v40 as protocol
import validate_preassessment_v40 as preassessment_validator


def _scan_forbidden(value: Any, path: str = "$") -> list[str]:
    forbidden = {"prompts", "tokens", "activations", "raw_activations", "logits", "raw_logits", "traces", "raw_traces", "per_family_effects", "per_family_predictions", "credentials", "pii"}
    errors: list[str] = []
    if isinstance(value, dict):
        for key, nested in value.items():
            if key in forbidden:
                errors.append(f"forbidden_key:{path}.{key}")
            errors.extend(_scan_forbidden(nested, f"{path}.{key}"))
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            errors.extend(_scan_forbidden(nested, f"{path}[{index}]"))
    return errors


def validate(final_root: Path, preassessment_root: Path, panel_root: Path, corpus_root: Path, qualification_root: Path, model_root: Path, repository_root: Path) -> dict[str, Any]:
    errors: list[str] = []
    final_root = final_root.resolve()
    try:
        protocol.assert_external(final_root, repository_root)
        result = protocol.read_json(final_root / "final-result.json")
        errors.extend(_scan_forbidden(result))
        if result.get("protocol") != protocol.PROTOCOL_ID or result.get("state_slice") != protocol.STATE_SLICE:
            errors.append("protocol_or_state_slice_mismatch")
        if result.get("classification") != finalizer.CLASSIFICATION or result.get("claim_ceiling") != finalizer.CLAIM_CEILING:
            errors.append("classification_or_claim_ceiling_mismatch")
        if result.get("assessment_effects_present") is not False or result.get("assessment_effects_measured") is not False or result.get("prediction_locked_before_assessment") is not True:
            errors.append("assessment_state_invalid")
        if result.get("aggregate_only") is not True or result.get("raw_intermediates_retained") is not False:
            errors.append("retention_state_invalid")
        if any(result.get(key) is not False for key in ("network_access", "model_training", "stage_0c", "stage_1", "accepted_evidence")):
            errors.append("boundary_state_invalid")
        pre_receipt = preassessment_validator.validate(preassessment_root, panel_root, corpus_root, qualification_root, model_root, repository_root)
        if not pre_receipt["valid"]:
            errors.append("preassessment_validation_failed")
        summary = protocol.read_json(preassessment_root / "fit-tune-summary.json")
        pair_tune = float(summary["panels"][protocol.PRIMARY_CONTROL]["tune_rmse"])
        constant_tune = float(summary["panels"]["constant"]["tune_rmse"])
        tune_delta = pair_tune - constant_tune
        if not math.isfinite(tune_delta) or tune_delta <= -protocol.UTILITY_RMSE_MARGIN:
            errors.append("early_stop_tune_gate_not_failed")
        basis = result.get("decision_basis", {})
        if basis.get("tune_delta_rmse") != tune_delta or basis.get("tune_utility_gate_passed") is not False or basis.get("assessment_opened") is not False:
            errors.append("decision_basis_mismatch")
        expected = {
            "preassessment_run_manifest_sha256": protocol.sha256_file(preassessment_root / "run-manifest.json"),
            "preassessment_summary_sha256": protocol.sha256_file(preassessment_root / "fit-tune-summary.json"),
            "preassessment_validator_receipt_sha256": protocol.sha256_file(preassessment_root / "validator-receipt.json"),
            "panel_manifest_sha256": protocol.sha256_file(panel_root / "panel-manifest.json"),
            "corpus_manifest_sha256": protocol.sha256_file(corpus_root / "corpus-manifest.json"),
            "qualification_result_sha256": protocol.sha256_file(qualification_root / "qualification-result.json"),
            "model_manifest_sha256": protocol.model_manifest(model_root)["manifest_sha256"],
        }
        for key, value in expected.items():
            if result.get(key) != value:
                errors.append(f"digest_mismatch:{key}")
        if result.get("source_sha256") != protocol.sha256_file(Path(finalizer.__file__).resolve()):
            errors.append("finalizer_source_mismatch")
        actual_files = {path.relative_to(final_root).as_posix() for path in final_root.rglob("*") if path.is_file()}
        if actual_files - {"final-result.json", "validator-receipt.json"} or "final-result.json" not in actual_files:
            errors.append("output_census_mismatch")
    except (OSError, json.JSONDecodeError, TypeError, KeyError, AttributeError, protocol.ProtocolError, ValueError) as exc:
        errors.append(f"validator_error:{type(exc).__name__}:{exc}")
    return {
        "protocol": protocol.PROTOCOL_ID,
        "state_slice": protocol.STATE_SLICE,
        "claim_ceiling": finalizer.CLAIM_CEILING,
        "classification": finalizer.CLASSIFICATION if not errors else "EarlyStopInvalid",
        "valid": not errors,
        "errors": errors,
        "final_result_sha256": protocol.sha256_file(final_root / "final-result.json") if (final_root / "final-result.json").is_file() else None,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("final_root", type=Path)
    parser.add_argument("--preassessment-root", type=Path, required=True)
    parser.add_argument("--panel-root", type=Path, required=True)
    parser.add_argument("--corpus-root", type=Path, required=True)
    parser.add_argument("--qualification-root", type=Path, required=True)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--repository-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--write-receipt", action="store_true")
    args = parser.parse_args(argv)
    receipt = validate(args.final_root, args.preassessment_root, args.panel_root, args.corpus_root, args.qualification_root, args.model, args.repository_root)
    if args.write_receipt:
        protocol.write_json(args.final_root.resolve() / "validator-receipt.json", receipt)
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0 if receipt["valid"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
