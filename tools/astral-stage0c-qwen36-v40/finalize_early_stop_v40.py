#!/usr/bin/env python3
"""Seal an early V40 no-candidate disposition after a failed tune gate.

State slice: astral-stage0c-qwen36-intervention-conditioned-target-v40.

V40 stops before review and assessment when the locked tune utility gate fails.
This finalizer retains only the validated preassessment aggregates and custody
digests; it never measures assessment effects.
"""

from __future__ import annotations

import argparse
import json
import shutil
import tempfile
from pathlib import Path
from typing import Any

import protocol_v40 as protocol
import validate_preassessment_v40 as preassessment_validator


CLASSIFICATION = "DevelopmentNoCandidate"
CLAIM_CEILING = "LocalDevelopmentV40DevelopmentNoCandidate"


def _write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def finalize(preassessment_root: Path, panel_root: Path, corpus_root: Path, qualification_root: Path, model_root: Path, output_root: Path, repository_root: Path) -> Path:
    preassessment_root = preassessment_root.resolve()
    panel_root = panel_root.resolve()
    corpus_root = corpus_root.resolve()
    qualification_root = qualification_root.resolve()
    model_root = model_root.resolve()
    output_root = output_root.resolve()
    repository_root = repository_root.resolve()
    protocol.assert_external(output_root, repository_root)
    if output_root.exists():
        raise protocol.ProtocolError(f"refusing to overwrite final root: {output_root}")
    validation = preassessment_validator.validate(preassessment_root, panel_root, corpus_root, qualification_root, model_root, repository_root)
    if not validation["valid"]:
        raise protocol.ProtocolError("preassessment is not independently valid: " + "; ".join(validation["errors"]))
    summary = protocol.read_json(preassessment_root / "fit-tune-summary.json")
    pair_tune = float(summary["panels"][protocol.PRIMARY_CONTROL]["tune_rmse"])
    constant_tune = float(summary["panels"]["constant"]["tune_rmse"])
    tune_delta = pair_tune - constant_tune
    if tune_delta <= -protocol.UTILITY_RMSE_MARGIN:
        raise protocol.ProtocolError("tune utility gate passed; early-stop finalization is not applicable")
    result = {
        "protocol": protocol.PROTOCOL_ID,
        "state_slice": protocol.STATE_SLICE,
        "classification": CLASSIFICATION,
        "claim_ceiling": CLAIM_CEILING,
        "preassessment_run_manifest_sha256": protocol.sha256_file(preassessment_root / "run-manifest.json"),
        "preassessment_summary_sha256": protocol.sha256_file(preassessment_root / "fit-tune-summary.json"),
        "preassessment_validator_receipt_sha256": protocol.sha256_file(preassessment_root / "validator-receipt.json"),
        "panel_manifest_sha256": protocol.sha256_file(panel_root / "panel-manifest.json"),
        "corpus_manifest_sha256": protocol.sha256_file(corpus_root / "corpus-manifest.json"),
        "qualification_result_sha256": protocol.sha256_file(qualification_root / "qualification-result.json"),
        "model_manifest_sha256": protocol.model_manifest(model_root)["manifest_sha256"],
        "decision_basis": {
            "primary_metric": "delta_rmse",
            "tune_pair_rmse": pair_tune,
            "tune_constant_rmse": constant_tune,
            "tune_delta_rmse": tune_delta,
            "required_delta_rmse": -protocol.UTILITY_RMSE_MARGIN,
            "tune_utility_gate_passed": False,
            "assessment_opened": False,
            "assessment_not_run_reason": "V40 stops immediately after failed locked tune utility gate",
            "candidate_nominated": False,
        },
        "assessment_effects_present": False,
        "assessment_effects_measured": False,
        "prediction_locked_before_assessment": True,
        "independent_review_required_before_assessment": True,
        "raw_intermediates_retained": False,
        "aggregate_only": True,
        "network_access": False,
        "model_training": False,
        "stage_0c": False,
        "stage_1": False,
        "accepted_evidence": False,
        "source_sha256": protocol.sha256_file(Path(__file__).resolve()),
    }
    output_root.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{output_root.name}.staging-", dir=str(output_root.parent)))
    try:
        _write_json(staging / "final-result.json", result)
        if output_root.exists():
            raise protocol.ProtocolError(f"final root appeared during publication: {output_root}")
        staging.rename(output_root)
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    return output_root


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preassessment-root", type=Path, required=True)
    parser.add_argument("--panel-root", type=Path, required=True)
    parser.add_argument("--corpus-root", type=Path, required=True)
    parser.add_argument("--qualification-root", type=Path, required=True)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--repository-root", type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args(argv)
    try:
        root = finalize(args.preassessment_root, args.panel_root, args.corpus_root, args.qualification_root, args.model, args.output_root, args.repository_root)
    except (OSError, json.JSONDecodeError, protocol.ProtocolError, ValueError, KeyError) as exc:
        print(json.dumps({"classification": "FinalizationFailed", "reason": f"{type(exc).__name__}:{exc}"}))
        return 2
    print(json.dumps({"final_root": str(root), "classification": CLASSIFICATION, "valid": True}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
