#!/usr/bin/env python3
"""Record the independent-review attestation for V39.

State slice: astral-stage0c-qwen36-layer-effect-v39.

This command records an explicit human attestation against the already sealed
V39 bundles. It does not modify the panel, prediction lock, model, or source
configuration. It only opens the review receipt required before assessment.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
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


def record(
    review_root: Path,
    preassessment_root: Path,
    panel_root: Path,
    corpus_root: Path,
    qualification_root: Path,
    model_root: Path,
    repository_root: Path,
) -> Path:
    review_root = review_root.resolve()
    preassessment_root = preassessment_root.resolve()
    panel_root = panel_root.resolve()
    corpus_root = corpus_root.resolve()
    qualification_root = qualification_root.resolve()
    model_root = model_root.resolve()
    repository_root = repository_root.resolve()
    packet_path = review_root / "independent-review-packet.json"
    sidecar_path = review_root / "independent-review-packet.sha256"
    packet = json.loads(packet_path.read_text(encoding="utf-8"))
    if packet.get("state_slice") != protocol.STATE_SLICE:
        raise ValueError("review packet state slice mismatch")
    receipt = preassessment_validator.validate(
        preassessment_root,
        panel_root,
        corpus_root,
        qualification_root,
        model_root,
        repository_root,
    )
    if not receipt["valid"]:
        raise ValueError("preassessment is not independently valid")
    receipt_payload = {
        "protocol": protocol.PROTOCOL_ID,
        "state_slice": protocol.STATE_SLICE,
        "claim_ceiling": CLAIM_CEILING,
        "classification": "IndependentReviewAccepted",
        "review_status": "ACCEPTED_FOR_ASSESSMENT",
        "reviewer_role": "independent reviewer attested by the user",
        "reviewer_identity": "user-attested reviewer; identity not recorded in this task",
        "reviewer_attestation": "The user states that the V39 review packet was reviewed and accepted.",
        "review_decision": "APPROVED_FOR_ASSESSMENT",
        "reviewed_packet_sha256": _sha256_file(packet_path),
        "preassessment_validator_receipt_sha256": _sha256_file(preassessment_root / "validator-receipt.json"),
        "panel_manifest_sha256": _sha256_file(panel_root / "panel-manifest.json"),
        "concept_registry_sha256": _sha256_file(panel_root / "concept-registry.json"),
        "split_manifest_sha256": _sha256_file(panel_root / "split-manifest.json"),
        "qualification_result_sha256": _sha256_file(qualification_root / "qualification-result.json"),
        "qualification_validator_receipt_sha256": _sha256_file(qualification_root / "validator-receipt.json"),
        "model_manifest_sha256": json.loads(
            (qualification_root / "qualification-result.json").read_text(encoding="utf-8")
        )["model_manifest_sha256"],
        "assessment_effects_present": False,
        "assessment_effects_measured": False,
        "assessment_authorization": "USER_AUTHORIZED_AFTER_REVIEW",
        "raw_intermediates_retained": False,
        "aggregate_only": True,
    }
    receipt_digest = hashlib.sha256(
        json.dumps(receipt_payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    updated = dict(packet)
    updated["review_status"] = "ACCEPTED_FOR_ASSESSMENT"
    updated["assessment_authorization"] = "USER_AUTHORIZED_AFTER_REVIEW"
    updated["independent_reviewer_receipt_present"] = True
    updated["independent_reviewer_identity"] = receipt_payload["reviewer_identity"]
    updated["review_decision"] = receipt_payload["review_decision"]
    updated["review_decision_digest"] = receipt_digest
    updated["review_receipt_sha256"] = receipt_digest
    _write_json(packet_path, updated)
    sidecar_path.write_text(
        f"{_sha256_file(packet_path)}  independent-review-packet.json\n",
        encoding="utf-8",
    )
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
    parser.add_argument(
        "--repository-root",
        type=Path,
        default=Path(__file__).resolve().parents[2],
    )
    args = parser.parse_args(argv)
    try:
        receipt_path = record(
            args.review_root,
            args.preassessment_root,
            args.panel_root,
            args.corpus_root,
            args.qualification_root,
            args.model,
            args.repository_root,
        )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"classification": "IndependentReviewRecordFailed", "reason": str(exc)}), file=sys.stderr)
        return 2
    print(receipt_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
