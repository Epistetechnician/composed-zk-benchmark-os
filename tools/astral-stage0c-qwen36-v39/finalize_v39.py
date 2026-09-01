#!/usr/bin/env python3
"""Seal the narrow V39 development disposition.

State slice: astral-stage0c-qwen36-layer-effect-v39.

The finalizer consumes only the independently validated aggregate assessment.
It nominates no Stage 0C candidate when the locked activation-only estimator
does not beat the fit/tune-selected constant baseline on tune and assessment.
It writes no raw or per-family effects.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import protocol_v39 as protocol
import validate_assessment_v39 as assessment_validator


CLASSIFICATION = "DevelopmentNoCandidate"
CLAIM_CEILING = "LocalDevelopmentV39DevelopmentNoCandidate"


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _canonical_digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def _write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def finalize(
    assessment_root: Path,
    preassessment_root: Path,
    panel_root: Path,
    corpus_root: Path,
    qualification_root: Path,
    review_root: Path,
    model_root: Path,
    repository_root: Path,
) -> Path:
    assessment_root = assessment_root.resolve()
    preassessment_root = preassessment_root.resolve()
    panel_root = panel_root.resolve()
    corpus_root = corpus_root.resolve()
    qualification_root = qualification_root.resolve()
    review_root = review_root.resolve()
    model_root = model_root.resolve()
    repository_root = repository_root.resolve()
    final_path = assessment_root / "final-result.json"
    if final_path.exists():
        raise ValueError(f"refusing to overwrite existing final result: {final_path}")
    validation = assessment_validator.validate(
        assessment_root,
        preassessment_root,
        panel_root,
        corpus_root,
        qualification_root,
        review_root,
        model_root,
        repository_root,
    )
    if not validation["valid"]:
        raise ValueError("assessment bundle is not independently valid: " + "; ".join(validation["errors"]))
    summary_path = assessment_root / "assessment-summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    panels = summary["panels"]
    candidate = panels["activation_only"]
    baseline = panels["constant"]
    tune_summary = json.loads(
        (preassessment_root / "fit-tune-summary.json").read_text(encoding="utf-8")
    )
    candidate_tune_rmse = float(tune_summary["panels"]["activation_only"]["tune_rmse"])
    baseline_tune_rmse = float(tune_summary["panels"]["constant"]["tune_rmse"])
    candidate_assessment_rmse = float(candidate["rmse"])
    baseline_assessment_rmse = float(baseline["rmse"])
    if not all(
        math.isfinite(value)
        for value in (
            candidate_tune_rmse,
            baseline_tune_rmse,
            candidate_assessment_rmse,
            baseline_assessment_rmse,
        )
    ):
        raise ValueError("classification metrics are not finite")
    if candidate_tune_rmse < baseline_tune_rmse or candidate_assessment_rmse < baseline_assessment_rmse:
        raise ValueError("activation-only estimator beat the constant baseline; no-candidate disposition is invalid")

    result = {
        "protocol": protocol.PROTOCOL_ID,
        "state_slice": protocol.STATE_SLICE,
        "claim_ceiling": CLAIM_CEILING,
        "classification": CLASSIFICATION,
        "assessment_run_manifest_sha256": _sha256_file(assessment_root / "assessment-run-manifest.json"),
        "assessment_summary_sha256": _sha256_file(summary_path),
        "assessment_validator_receipt_sha256": _sha256_file(assessment_root / "validator-receipt.json"),
        "preassessment_prediction_lock_sha256": _sha256_file(preassessment_root / "prediction-lock.json"),
        "independent_review_receipt_sha256": _sha256_file(review_root / "independent-review-receipt.json"),
        "model_manifest_sha256": summary["model_manifest_sha256"],
        "assessment_family_count": summary["assessment_family_count"],
        "decision_basis": {
            "candidate_panel": "activation_only",
            "utility_gate": "activation_only_rmse_must_be_strictly_lower_than_constant_on_tune_and_assessment",
            "candidate_tune_rmse": candidate_tune_rmse,
            "constant_tune_rmse": baseline_tune_rmse,
            "candidate_assessment_rmse": candidate_assessment_rmse,
            "constant_assessment_rmse": baseline_assessment_rmse,
            "tune_utility_gate_passed": candidate_tune_rmse < baseline_tune_rmse,
            "assessment_utility_gate_passed": candidate_assessment_rmse < baseline_assessment_rmse,
            "candidate_nominated": False,
        },
        "assessment_effects_measured": True,
        "assessment_effects_present": True,
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
    parser.add_argument(
        "--repository-root",
        type=Path,
        default=Path(__file__).resolve().parents[2],
    )
    args = parser.parse_args(argv)
    try:
        result_path = finalize(
            args.assessment_root,
            args.preassessment_root,
            args.panel_root,
            args.corpus_root,
            args.qualification_root,
            args.review_root,
            args.model,
            args.repository_root,
        )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"classification": "FinalizationFailed", "reason": str(exc)}), file=sys.stderr)
        return 2
    print(result_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
