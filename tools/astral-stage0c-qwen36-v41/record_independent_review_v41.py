#!/usr/bin/env python3
"""Record an explicit independent-review attestation for V41.

State slice: astral-stage0c-qwen36-directional-block-target-v41.

The reviewer identity and attestation are mandatory. This command only opens
the assessment authorization state; it does not execute assessment.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import protocol_v41 as protocol
import validate_preassessment_v41 as preassessment_validator


CLAIM_CEILING = "LocalDevelopmentV41PreassessmentPredictionLocked"


def _sha256_file(path: Path) -> str:
    return protocol.sha256_file(path)


def _canonical_digest(value: Any) -> str:
    return protocol.canonical_digest(value)


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

    return json.loads(
        path.read_text(encoding="utf-8"),
        object_pairs_hook=reject_duplicates,
        parse_constant=reject_constant,
    )


def _write_json(path: Path, value: Any) -> None:
    protocol.write_json(path, value)


def record(
    review_root: Path,
    preassessment_root: Path,
    panel_root: Path,
    corpus_root: Path,
    qualification_root: Path,
    model_root: Path,
    reviewer_identity: str,
    attestation: str,
    repository_root: Path,
) -> Path:
    if not reviewer_identity.strip() or not attestation.strip():
        raise protocol.ProtocolError("reviewer identity and attestation are required")
    review_root = review_root.resolve()
    preassessment_root = preassessment_root.resolve()
    panel_root = panel_root.resolve()
    corpus_root = corpus_root.resolve()
    qualification_root = qualification_root.resolve()
    model_root = model_root.resolve()
    repository_root = repository_root.resolve()
    protocol.assert_external(review_root, repository_root)
    packet_path = review_root / "independent-review-packet.json"
    sidecar_path = review_root / "independent-review-packet.sha256"
    packet = _strict_json(packet_path)
    if packet.get("protocol") != protocol.PROTOCOL_ID or packet.get("state_slice") != protocol.STATE_SLICE:
        raise protocol.ProtocolError("review packet protocol or state slice mismatch")
    if packet.get("review_status") != "PENDING_INDEPENDENT_REVIEW" or packet.get("assessment_authorization") != "CLOSED_PENDING_REVIEW":
        raise protocol.ProtocolError("review packet is not pending acceptance")
    if sidecar_path.read_text(encoding="utf-8") != f"{_sha256_file(packet_path)}  independent-review-packet.json\n":
        raise protocol.ProtocolError("review packet sidecar mismatch")
    pending_packet_sha256 = _sha256_file(packet_path)
    expected_sources = {
        "corpus_root": str(corpus_root),
        "panel_root": str(panel_root),
        "preassessment_root": str(preassessment_root),
        "qualification_root": str(qualification_root),
        "model_root": str(model_root),
    }
    if packet.get("source_bundles") != expected_sources:
        raise protocol.ProtocolError("review packet source bundle mismatch")
    validation = preassessment_validator.validate(
        preassessment_root,
        panel_root,
        corpus_root,
        qualification_root,
        model_root,
        repository_root,
    )
    if not validation["valid"]:
        raise protocol.ProtocolError("preassessment bundle is not independently valid")
    expected_packet_digests = {
        "corpus_manifest_sha256": _sha256_file(corpus_root / "corpus-manifest.json"),
        "corpus_validator_receipt_sha256": _sha256_file(corpus_root / "validator-receipt.json"),
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
    }
    if packet.get("digests") != expected_packet_digests:
        raise protocol.ProtocolError("review packet digest map mismatch")
    receipt_payload = {
        "protocol": protocol.PROTOCOL_ID,
        "state_slice": protocol.STATE_SLICE,
        "claim_ceiling": CLAIM_CEILING,
        "classification": "IndependentReviewAccepted",
        "review_status": "ACCEPTED_FOR_ASSESSMENT",
        "reviewer_role": "independent reviewer who did not execute or configure V41",
        "reviewer_identity": reviewer_identity.strip(),
        "reviewer_attestation": attestation.strip(),
        "review_decision": "APPROVED_FOR_ASSESSMENT",
        "reviewed_pending_packet_sha256": pending_packet_sha256,
        **expected_packet_digests,
        "assessment_effects_present": False,
        "assessment_effects_measured": False,
        "assessment_authorization": "USER_AUTHORIZED_AFTER_REVIEW",
        "raw_intermediates_retained": False,
        "aggregate_only": True,
    }
    receipt_digest = _canonical_digest(receipt_payload)
    updated = dict(packet)
    updated.update(
        {
            "review_status": "ACCEPTED_FOR_ASSESSMENT",
            "assessment_authorization": "USER_AUTHORIZED_AFTER_REVIEW",
            "independent_reviewer_receipt_present": True,
            "independent_reviewer_identity": reviewer_identity.strip(),
            "review_decision": "APPROVED_FOR_ASSESSMENT",
            "review_decision_digest": receipt_digest,
            "review_receipt_sha256": receipt_digest,
        }
    )
    _write_json(packet_path, updated)
    sidecar_path.write_text(f"{_sha256_file(packet_path)}  independent-review-packet.json\n", encoding="utf-8")
    receipt_path = review_root / "independent-review-receipt.json"
    _write_json(receipt_path, receipt_payload)
    return receipt_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--review-root", type=Path, required=True)
    parser.add_argument("--preassessment-root", type=Path, required=True)
    parser.add_argument("--panel-root", type=Path, required=True)
    parser.add_argument("--corpus-root", type=Path, required=True)
    parser.add_argument("--qualification-root", type=Path, required=True)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--reviewer-identity", required=True)
    parser.add_argument("--attestation", required=True)
    parser.add_argument("--repository-root", type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args(argv)
    try:
        receipt_path = record(
            args.review_root,
            args.preassessment_root,
            args.panel_root,
            args.corpus_root,
            args.qualification_root,
            args.model,
            args.reviewer_identity,
            args.attestation,
            args.repository_root,
        )
    except (OSError, json.JSONDecodeError, protocol.ProtocolError, ValueError) as exc:
        print(json.dumps({"classification": "IndependentReviewRecordFailed", "reason": str(exc)}))
        return 2
    print(json.dumps({"receipt": str(receipt_path), "classification": "IndependentReviewAccepted", "valid": True}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
