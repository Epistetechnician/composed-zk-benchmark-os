#!/usr/bin/env python3
"""Finalize the narrow V40 aggregate disposition.

State slice: astral-stage0c-qwen36-intervention-conditioned-target-v40.

The finalizer consumes only an independently validated post-review aggregate
bundle. It never promotes Stage 0C or Stage 1 and never writes raw data.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import protocol_v40 as protocol
import validate_assessment_v40 as assessment_validator


def _sha256_file(path: Path) -> str:
    return protocol.sha256_file(path)


def _write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def finalize(assessment_root: Path, preassessment_root: Path, panel_root: Path, corpus_root: Path, qualification_root: Path, review_root: Path, model_root: Path, repository_root: Path) -> Path:
    assessment_root = assessment_root.resolve()
    final_path = assessment_root / "final-result.json"
    if final_path.exists():
        raise protocol.ProtocolError(f"refusing to overwrite final result: {final_path}")
    validation = assessment_validator.validate(assessment_root, preassessment_root, panel_root, corpus_root, qualification_root, review_root, model_root, repository_root)
    if not validation["valid"]:
        raise protocol.ProtocolError("assessment bundle is not independently valid: " + "; ".join(validation["errors"]))
    summary = json.loads((assessment_root / "assessment-summary.json").read_text(encoding="utf-8"))
    tune_summary = json.loads((preassessment_root.resolve() / "fit-tune-summary.json").read_text(encoding="utf-8"))
    pair_tune = float(tune_summary["panels"][protocol.PRIMARY_CONTROL]["tune_rmse"])
    constant_tune = float(tune_summary["panels"]["constant"]["tune_rmse"])
    pair_assessment = float(summary["panels"][protocol.PRIMARY_CONTROL]["rmse"])
    constant_assessment = float(summary["panels"]["constant"]["rmse"])
    clean_assessment = float(summary["panels"]["clean_activation_only"]["rmse"])
    shuffled_assessment = float(summary["panels"]["shuffled"]["rmse"])
    text_assessment = float(summary["panels"]["text_only"]["rmse"])
    matched_mean = float(summary["matched_control"]["mean"])
    bootstrap_upper = float(summary["cluster_bootstrap"]["rmse_delta_095_upper"])
    target_std = float(summary["target_effect"]["std"])
    tune_delta = pair_tune - constant_tune
    assessment_delta = pair_assessment - constant_assessment
    gates = {
        "tune_utility": tune_delta <= -protocol.UTILITY_RMSE_MARGIN,
        "assessment_utility": assessment_delta <= -protocol.UTILITY_RMSE_MARGIN,
        "bootstrap_upper": bootstrap_upper < -protocol.BOOTSTRAP_RMSE_MARGIN,
        "clean_control_margin": pair_assessment <= clean_assessment - protocol.CONTROL_RMSE_MARGIN,
        "shuffled_control_margin": pair_assessment <= shuffled_assessment - protocol.CONTROL_RMSE_MARGIN,
        "text_control_not_better": pair_assessment <= text_assessment,
        "matched_control_envelope": abs(matched_mean) <= protocol.MATCHED_CONTROL_MEAN_ABS_MAX,
        "matched_donor_census": summary["matched_control"]["donor_violations"] == 0 and summary["matched_control"]["sequence_length_delta_max"] == 0,
        "target_non_degenerate": target_std >= protocol.MIN_ASSESSMENT_TARGET_STD,
        "assessment_census": summary["assessment_family_count"] == protocol.FAMILIES_PER_SPLIT,
    }
    if not all(math.isfinite(value) for value in (tune_delta, assessment_delta, bootstrap_upper, target_std, matched_mean)):
        raise protocol.ProtocolError("finalization metrics are non-finite")
    candidate = all(gates.values())
    classification = "BoundedTargetValidity" if candidate else "DevelopmentNoCandidate"
    claim_ceiling = "LocalDevelopmentV40BoundedTargetValidity" if candidate else "LocalDevelopmentV40DevelopmentNoCandidate"
    result = {
        "protocol": protocol.PROTOCOL_ID,
        "state_slice": protocol.STATE_SLICE,
        "classification": classification,
        "claim_ceiling": claim_ceiling,
        "assessment_run_manifest_sha256": _sha256_file(assessment_root / "assessment-run-manifest.json"),
        "assessment_summary_sha256": _sha256_file(assessment_root / "assessment-summary.json"),
        "assessment_validator_receipt_sha256": _sha256_file(assessment_root / "validator-receipt.json"),
        "preassessment_prediction_lock_sha256": _sha256_file(preassessment_root.resolve() / "prediction-lock.json"),
        "independent_review_receipt_sha256": _sha256_file(review_root.resolve() / "independent-review-receipt.json"),
        "model_manifest_sha256": summary["model_manifest_sha256"],
        "decision_basis": {
            "primary_metric": "delta_rmse",
            "tune_delta_rmse": tune_delta,
            "assessment_delta_rmse": assessment_delta,
            "assessment_bootstrap_95_upper": bootstrap_upper,
            "gates": gates,
            "candidate_nominated": candidate,
        },
        "assessment_effects_present": True,
        "assessment_effects_measured": True,
        "prediction_locked_before_assessment": True,
        "independent_review_accepted": True,
        "raw_intermediates_retained": False,
        "aggregate_only": True,
        "network_access": False,
        "model_training": False,
        "stage_0c": False,
        "stage_1": False,
        "accepted_evidence": False,
        "source_sha256": _sha256_file(Path(__file__).resolve()),
    }
    _write_json(final_path, result)
    return final_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--assessment-root", type=Path, required=True)
    parser.add_argument("--preassessment-root", type=Path, required=True)
    parser.add_argument("--panel-root", type=Path, required=True)
    parser.add_argument("--corpus-root", type=Path, required=True)
    parser.add_argument("--qualification-root", type=Path, required=True)
    parser.add_argument("--review-root", type=Path, required=True)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--repository-root", type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args(argv)
    try:
        result_path = finalize(args.assessment_root, args.preassessment_root, args.panel_root, args.corpus_root, args.qualification_root, args.review_root, args.model, args.repository_root)
    except (OSError, json.JSONDecodeError, protocol.ProtocolError, ValueError, KeyError) as exc:
        print(json.dumps({"classification": "FinalizationFailed", "reason": f"{type(exc).__name__}:{exc}"}))
        return 2
    print(json.dumps({"final_result": str(result_path), "valid": True}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
