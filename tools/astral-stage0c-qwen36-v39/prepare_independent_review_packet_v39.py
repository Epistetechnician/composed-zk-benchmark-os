#!/usr/bin/env python3
"""Prepare the mandatory independent-review packet for V39.

State slice: astral-stage0c-qwen36-layer-effect-v39.

The packet records the sealed external bundles and reviewer checklist. It does
not certify itself, authorize assessment, or contain raw scientific data.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import protocol_v39 as protocol
import validate_preassessment_v39 as preassessment_validator


CLAIM_CEILING = "LocalDevelopmentV39PreassessmentPredictionLocked"


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def prepare(
    preassessment_root: Path,
    panel_root: Path,
    corpus_root: Path,
    qualification_root: Path,
    model_root: Path,
    review_root: Path,
    repository_root: Path,
) -> Path:
    preassessment_root = preassessment_root.resolve()
    panel_root = panel_root.resolve()
    corpus_root = corpus_root.resolve()
    qualification_root = qualification_root.resolve()
    model_root = model_root.resolve()
    review_root = review_root.resolve()
    repository_root = repository_root.resolve()
    protocol.assert_external(review_root, repository_root)
    if review_root.exists():
        raise ValueError(f"refusing to overwrite existing review root: {review_root}")
    preassessment_receipt = preassessment_validator.validate(
        preassessment_root,
        panel_root,
        corpus_root,
        qualification_root,
        model_root,
        repository_root,
    )
    if not preassessment_receipt["valid"]:
        raise ValueError("preassessment bundle is not independently valid")
    run_manifest_path = preassessment_root / "run-manifest.json"
    summary_path = preassessment_root / "fit-tune-summary.json"
    lock_path = preassessment_root / "prediction-lock.json"
    validator_receipt_path = preassessment_root / "validator-receipt.json"
    packet = {
        "protocol": protocol.PROTOCOL_ID,
        "state_slice": protocol.STATE_SLICE,
        "claim_ceiling": CLAIM_CEILING,
        "classification": "IndependentReviewRequired",
        "review_status": "PENDING_INDEPENDENT_REVIEW",
        "reviewer_role": "independent reviewer who did not execute or configure V39",
        "self_review_prohibited": True,
        "assessment_authorization": "CLOSED_PENDING_REVIEW",
        "assessment_effects_present": False,
        "assessment_effects_measured": False,
        "raw_intermediates_retained": False,
        "aggregate_only": True,
        "network_access": False,
        "model_training": False,
        "source_bundles": {
            "corpus_root": str(corpus_root),
            "panel_root": str(panel_root),
            "preassessment_root": str(preassessment_root),
            "qualification_root": str(qualification_root),
            "model_root": str(model_root),
        },
        "digests": {
            "panel_manifest_sha256": _sha256_file(panel_root / "panel-manifest.json"),
            "concept_registry_sha256": _sha256_file(panel_root / "concept-registry.json"),
            "split_manifest_sha256": _sha256_file(panel_root / "split-manifest.json"),
            "panel_validator_receipt_sha256": _sha256_file(panel_root / "validator-receipt.json"),
            "qualification_result_sha256": _sha256_file(qualification_root / "qualification-result.json"),
            "qualification_validator_receipt_sha256": _sha256_file(qualification_root / "validator-receipt.json"),
            "run_manifest_sha256": _sha256_file(run_manifest_path),
            "fit_tune_summary_sha256": _sha256_file(summary_path),
            "prediction_lock_sha256": _sha256_file(lock_path),
            "preassessment_validator_receipt_sha256": _sha256_file(validator_receipt_path),
        },
        "review_checklist": [
            {
                "item": "model_runtime_source_custody",
                "status": "PENDING",
                "required_verification": "Recompute model manifest, qualification result and runtime/source digests from the external roots.",
            },
            {
                "item": "fresh_data_identity_and_prior_lane_separation",
                "status": "PENDING",
                "required_verification": "Verify the Gutenberg selection, corpus identity, V25/V28/V29 exclusions, and no V25/V28/V29 data reuse.",
            },
            {
                "item": "document_disjoint_fit_tune_assessment_splits",
                "status": "PENDING",
                "required_verification": "Recompute family and document census and check that no document crosses fit, tune, and assessment.",
            },
            {
                "item": "direct_target_and_control_definitions",
                "status": "PENDING",
                "required_verification": "Verify activation-only, text-only, shuffled, constant, and matched controls are fixed before assessment and matched is excluded from tuning.",
            },
            {
                "item": "prediction_lock_before_assessment_effects",
                "status": "PENDING",
                "required_verification": "Verify the lock binds all source digests, contains assessment predictions only, and contains no assessment intervention effects.",
            },
            {
                "item": "privacy_and_aggregate_only_retention",
                "status": "PENDING",
                "required_verification": "Verify output census and recursively check that prompts, tokens, activations, logits, traces, credentials, and PII are absent.",
            },
            {
                "item": "validator_behavior",
                "status": "PENDING",
                "required_verification": "Run the independent corpus, panel, qualification, and preassessment validators and inspect fail-closed behavior.",
            },
            {
                "item": "claim_ceiling_and_advancement_gate",
                "status": "PENDING",
                "required_verification": "Confirm the maximum current claim is preassessment prediction locking; assessment and Stage 0C/Stage 1 remain closed.",
            },
        ],
        "independent_reviewer_receipt_present": False,
        "independent_reviewer_identity": None,
        "review_decision": None,
        "review_decision_digest": None,
    }
    review_root.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{review_root.name}.staging-", dir=str(review_root.parent)))
    try:
        packet_path = staging / "independent-review-packet.json"
        _write_json(packet_path, packet)
        packet_digest = _sha256_file(packet_path)
        (staging / "independent-review-packet.sha256").write_text(
            f"{packet_digest}  independent-review-packet.json\n",
            encoding="utf-8",
        )
        if review_root.exists():
            raise ValueError(f"review root appeared during preparation: {review_root}")
        staging.rename(review_root)
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    return review_root


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preassessment-root", type=Path, required=True)
    parser.add_argument("--panel-root", type=Path, required=True)
    parser.add_argument("--corpus-root", type=Path, required=True)
    parser.add_argument("--qualification-root", type=Path, required=True)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--review-root", type=Path, required=True)
    parser.add_argument(
        "--repository-root",
        type=Path,
        default=Path(__file__).resolve().parents[2],
    )
    args = parser.parse_args(argv)
    try:
        root = prepare(
            args.preassessment_root,
            args.panel_root,
            args.corpus_root,
            args.qualification_root,
            args.model,
            args.review_root,
            args.repository_root,
        )
    except (OSError, ValueError) as exc:
        print(json.dumps({"classification": "IndependentReviewPacketFailed", "reason": str(exc)}), file=sys.stderr)
        return 2
    print(root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
