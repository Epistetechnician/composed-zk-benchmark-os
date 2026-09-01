#!/usr/bin/env python3
"""Finalize the narrow V41 assessment classification.

State slice: astral-stage0c-qwen36-directional-block-target-v41.

Finalization requires an independently valid assessment bundle. It emits only
the bounded V41 classification and digest-bound aggregate gate record; it does
not promote Stage 0C or Stage 1.
"""

from __future__ import annotations

import argparse
import json
import shutil
import tempfile
from pathlib import Path
from typing import Any

import protocol_v41 as protocol
TARGET_VALIDITY_CLASSIFICATION = "BoundedTargetValidity"
DEVELOPMENT_NO_CANDIDATE_CLASSIFICATION = "DevelopmentNoCandidate"
TARGET_DEGENERATE_CLASSIFICATION = "TargetDegenerateNoCandidate"
TARGET_VALIDITY_CLAIM_CEILING = "LocalDevelopmentStage0CQwen36CausalTargetValidity"
NO_CANDIDATE_CLAIM_CEILING = "LocalDevelopmentV41DevelopmentNoCandidate"


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


def _sha256_file(path: Path) -> str:
    return protocol.sha256_file(path)


def finalize(
    assessment_root: Path,
    assessment_validator_receipt: Path,
    output_root: Path,
    repository_root: Path,
) -> Path:
    assessment_root = assessment_root.resolve()
    assessment_validator_receipt = assessment_validator_receipt.resolve()
    output_root = output_root.resolve()
    repository_root = repository_root.resolve()
    protocol.assert_external(output_root, repository_root)
    if output_root.exists():
        raise protocol.ProtocolError(f"refusing to overwrite final root: {output_root}")
    receipt = _strict_json(assessment_validator_receipt)
    if receipt.get("protocol") != protocol.PROTOCOL_ID or receipt.get("state_slice") != protocol.STATE_SLICE:
        raise protocol.ProtocolError("assessment validator receipt protocol mismatch")
    if receipt.get("valid") is not True:
        raise protocol.ProtocolError("assessment validator receipt is not valid")
    summary = _strict_json(assessment_root / "assessment-summary.json")
    gates = summary.get("gates")
    target = summary.get("target_effect")
    if not isinstance(gates, dict) or not isinstance(target, dict):
        raise protocol.ProtocolError("assessment summary lacks finalization fields")
    if float(target["std"]) < protocol.MIN_ASSESSMENT_TARGET_STD:
        classification = TARGET_DEGENERATE_CLASSIFICATION
        claim_ceiling = NO_CANDIDATE_CLAIM_CEILING
    elif all(gates.values()):
        classification = TARGET_VALIDITY_CLASSIFICATION
        claim_ceiling = TARGET_VALIDITY_CLAIM_CEILING
    else:
        classification = DEVELOPMENT_NO_CANDIDATE_CLASSIFICATION
        claim_ceiling = NO_CANDIDATE_CLAIM_CEILING
    result = {
        "protocol": protocol.PROTOCOL_ID,
        "state_slice": protocol.STATE_SLICE,
        "classification": classification,
        "claim_ceiling": claim_ceiling,
        "assessment_validator_receipt_sha256": _sha256_file(assessment_validator_receipt),
        "assessment_summary_sha256": _sha256_file(assessment_root / "assessment-summary.json"),
        "assessment_run_manifest_sha256": _sha256_file(assessment_root / "assessment-run-manifest.json"),
        "decision_basis": {
            "gates": gates,
            "target_std": float(target["std"]),
            "assessment_effects_present": True,
            "assessment_effects_measured": True,
        },
        "assessment_effects_present": True,
        "assessment_effects_measured": True,
        "prediction_locked_before_assessment": True,
        "raw_intermediates_retained": False,
        "aggregate_only": True,
        "network_access": False,
        "model_training": False,
        "stage_0c": False,
        "stage_1": False,
        "accepted_evidence": False,
        "source_sha256": _sha256_file(Path(__file__).resolve()),
    }
    output_root.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(
        tempfile.mkdtemp(prefix=f".{output_root.name}.staging-", dir=str(output_root.parent))
    )
    try:
        _write_json(staging / "final-result.json", result)
        if output_root.exists():
            raise protocol.ProtocolError(f"final root appeared during finalization: {output_root}")
        staging.rename(output_root)
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    return output_root


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--assessment-root", type=Path, required=True)
    parser.add_argument("--assessment-validator-receipt", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--repository-root", type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args(argv)
    try:
        root = finalize(
            args.assessment_root,
            args.assessment_validator_receipt,
            args.output_root,
            args.repository_root,
        )
    except (OSError, json.JSONDecodeError, protocol.ProtocolError, ValueError, TypeError, KeyError) as exc:
        print(json.dumps({"classification": "FinalizationFailed", "reason": f"{type(exc).__name__}:{exc}"}))
        return 2
    result = _strict_json(root / "final-result.json")
    print(json.dumps({"final_root": str(root), "classification": result["classification"], "valid": True}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
