#!/usr/bin/env python3
"""Prepare the mandatory independent-review packet for V40.

State slice: astral-stage0c-qwen36-intervention-conditioned-target-v40.

This command validates the preassessment chain and publishes a pending packet
to an external root. It does not accept the review, authorize assessment, or
contain prompts, tokens, activations, effects, or predictions.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import tempfile
from pathlib import Path
from typing import Any

import protocol_v40 as protocol
import validate_preassessment_v40 as preassessment_validator


CLAIM_CEILING = "LocalDevelopmentV40PreassessmentPredictionLocked"


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
        raise protocol.ProtocolError(f"refusing to overwrite existing review root: {review_root}")
    receipt = preassessment_validator.validate(
        preassessment_root,
        panel_root,
        corpus_root,
        qualification_root,
        model_root,
        repository_root,
    )
    if not receipt["valid"]:
        raise protocol.ProtocolError("preassessment bundle is not independently valid")
    packet = {
        "protocol": protocol.PROTOCOL_ID,
        "state_slice": protocol.STATE_SLICE,
        "claim_ceiling": CLAIM_CEILING,
        "classification": "IndependentReviewRequired",
        "review_status": "PENDING_INDEPENDENT_REVIEW",
        "reviewer_role": "independent reviewer who did not execute or configure V40",
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
            "corpus_manifest_sha256": _sha256_file(corpus_root / "corpus-manifest.json"),
            "panel_manifest_sha256": _sha256_file(panel_root / "panel-manifest.json"),
            "concept_registry_sha256": _sha256_file(panel_root / "concept-registry.json"),
            "split_manifest_sha256": _sha256_file(panel_root / "split-manifest.json"),
            "panel_validator_receipt_sha256": _sha256_file(panel_root / "validator-receipt.json"),
            "qualification_result_sha256": _sha256_file(qualification_root / "qualification-result.json"),
            "qualification_validator_receipt_sha256": _sha256_file(qualification_root / "validator-receipt.json"),
            "preassessment_run_manifest_sha256": _sha256_file(preassessment_root / "run-manifest.json"),
            "fit_tune_summary_sha256": _sha256_file(preassessment_root / "fit-tune-summary.json"),
            "prediction_lock_sha256": _sha256_file(preassessment_root / "prediction-lock.json"),
            "preassessment_validator_receipt_sha256": _sha256_file(preassessment_root / "validator-receipt.json"),
            "model_manifest_sha256": protocol.model_manifest(model_root)["manifest_sha256"],
        },
        "review_parameters": {
            "fixed_token_length": protocol.FIXED_TOKEN_LENGTH,
            "target_layer": protocol.TARGET_LAYER,
            "feature_width": protocol.FEATURE_WIDTH,
            "controls": list(protocol.CONTROL_NAMES),
            "ridge_alphas": list(protocol.RIDGE_ALPHAS),
            "utility_rmse_margin": protocol.UTILITY_RMSE_MARGIN,
            "bootstrap_rmse_margin": protocol.BOOTSTRAP_RMSE_MARGIN,
            "control_rmse_margin": protocol.CONTROL_RMSE_MARGIN,
            "minimum_assessment_target_std": protocol.MIN_ASSESSMENT_TARGET_STD,
            "matched_control_mean_abs_max": protocol.MATCHED_CONTROL_MEAN_ABS_MAX,
            "bootstrap_seed": protocol.BOOTSTRAP_SEED,
        },
        "review_checklist": [
            {
                "item": "model_runtime_source_custody",
                "status": "PENDING",
                "required_verification": "Recompute model manifest, qualification result, runtime, and installed-source digests.",
            },
            {
                "item": "fresh_data_identity_and_prior_lane_separation",
                "status": "PENDING",
                "required_verification": "Verify the V40 Gutenberg selection, fresh corpus digest, V39 ID exclusion, and no prior scientific artifact reuse.",
            },
            {
                "item": "document_author_disjoint_splits",
                "status": "PENDING",
                "required_verification": "Recompute the 18-document/144-family census, author separation, contained-work exclusion, and cross-split overlap rules.",
            },
            {
                "item": "direct_target_and_controls",
                "status": "PENDING",
                "required_verification": "Verify paired activation, clean activation, text-only, shuffled, constant, and matched controls; matched is excluded from tuning.",
            },
            {
                "item": "fixed_length_and_donor_matching",
                "status": "PENDING",
                "required_verification": "Verify every ordinary/counterfactual prompt has the fixed tokenizer length and every donor is cross-document, exact-length, and norm-matched.",
            },
            {
                "item": "prediction_lock_before_assessment_effects",
                "status": "PENDING",
                "required_verification": "Verify estimator-only fit/tune lock, assessment family order, absence of assessment effects, and no per-family predictions retained.",
            },
            {
                "item": "privacy_and_aggregate_only_retention",
                "status": "PENDING",
                "required_verification": "Verify output census and absence of prompts, tokens, activations, logits, traces, credentials, PII, per-family effects, and per-family predictions.",
            },
            {
                "item": "validator_behavior_and_claim_ceiling",
                "status": "PENDING",
                "required_verification": "Run independent validators and confirm assessment, Stage 0C, Stage 1, accepted-evidence, benchmark, and production claims remain closed.",
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
            f"{packet_digest}  independent-review-packet.json\n", encoding="utf-8"
        )
        if review_root.exists():
            raise protocol.ProtocolError(f"review root appeared during preparation: {review_root}")
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
    parser.add_argument("--repository-root", type=Path, default=Path(__file__).resolve().parents[2])
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
    except (OSError, json.JSONDecodeError, protocol.ProtocolError, ValueError) as exc:
        print(json.dumps({"classification": "IndependentReviewPacketFailed", "reason": str(exc)}))
        return 2
    print(json.dumps({"review_root": str(root), "classification": "IndependentReviewRequired", "valid": True}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
