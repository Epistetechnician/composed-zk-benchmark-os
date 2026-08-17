#!/usr/bin/env python3
"""Independent result validator for the v1 metacognitive-control experiment.

Acceptance state slice: ``verified-metacognitive-control-campaign-acceptance-gate-v1``.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .protocol import (
    ProtocolError,
    RESULT_SCHEMA_VERSION,
    STATE_SLICE,
    digest_json,
    evaluate,
    load_input,
)


CAMPAIGN_VERIFICATION_CLAIM_CEILING = "LocalDevelopmentCampaignVerificationOnly"


def _campaign_report_errors(result: dict, report: dict) -> list[str]:
    errors: list[str] = []
    if not isinstance(report, dict):
        return ["campaign verification report must be a JSON object"]
    if report.get("valid") is not True:
        errors.append("campaign verification report is not valid")
    if report.get("claim_ceiling") != CAMPAIGN_VERIFICATION_CLAIM_CEILING:
        errors.append("wrong campaign verification claim ceiling")
    if report.get("result_digest") != result.get("result_digest"):
        errors.append("campaign verification result digest mismatch")
    declared_digest = report.get("report_digest")
    if not isinstance(declared_digest, str) or len(declared_digest) != 64:
        errors.append("campaign verification report digest missing")
    else:
        unsigned = dict(report)
        unsigned.pop("report_digest", None)
        if digest_json(unsigned) != declared_digest:
            errors.append("campaign verification report digest mismatch")
    return errors


def validate(
    result: dict,
    expected: dict | None = None,
    *,
    campaign_verified: bool = False,
    allow_campaign_verification_pending: bool = False,
) -> list[str]:
    errors: list[str] = []
    if not isinstance(result, dict):
        return ["result must be a JSON object"]
    if result.get("record_type") != "result":
        errors.append("wrong record_type")
    if result.get("schema_version") != RESULT_SCHEMA_VERSION:
        errors.append("wrong schema_version")
    if result.get("state_slice") != STATE_SLICE:
        errors.append("wrong state_slice")
    if result.get("decision") == "keep_candidate" and result.get("classification") != "LocalDevelopmentCandidate":
        errors.append("keep_candidate requires LocalDevelopmentCandidate")
    if result.get("source_type") != "live_workflow_capture" and result.get("decision") == "keep_candidate":
        errors.append("non-live result cannot keep candidate")
    if (
        result.get("decision") == "keep_candidate"
        and not campaign_verified
        and not allow_campaign_verification_pending
    ):
        errors.append("keep_candidate requires a valid campaign verification report")
    expected_claim_ceiling = (
        "LocalDevelopmentMetacognitiveControlCandidate"
        if result.get("classification") == "LocalDevelopmentCandidate"
        else "Level0DesignNote"
    )
    if result.get("claim_ceiling") != expected_claim_ceiling:
        errors.append("claim_ceiling does not match classification")
    for field in ("arm_summaries", "coverage", "gates", "thresholds", "non_claims"):
        if field not in result:
            errors.append(f"missing {field}")
    gates = result.get("gates", {})
    if not isinstance(gates, dict):
        errors.append("gates must be a JSON object")
        gates = {}
    if gates.get("no_authority") is not True:
        errors.append("authority gate failed")
    if gates.get("no_raw_reasoning") is not True:
        errors.append("raw-reasoning gate failed")
    if result.get("source_type") == "live_workflow_capture" and gates.get("prediction_lock") is not True:
        errors.append("prediction-lock gate failed")
    if result.get("result_digest"):
        copy = dict(result)
        del copy["result_digest"]
        if digest_json(copy) != result["result_digest"]:
            errors.append("result_digest mismatch")
    if expected is not None and result != expected:
        errors.append("result does not match recomputation from input")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("result")
    parser.add_argument("--input", help="recompute the result from this manifest-plus-trial JSONL")
    parser.add_argument("--campaign-verification", help="campaign verification report required for candidate acceptance")
    args = parser.parse_args()
    if not args.input:
        print(json.dumps({"valid": False, "errors": ["--input is required for independent result validation"]}))
        return 2
    try:
        result = json.loads(Path(args.result).read_text(encoding="utf-8"))
        if not isinstance(result, dict):
            print(json.dumps({"valid": False, "errors": ["result must be a JSON object"]}))
            return 2
        expected = evaluate(load_input(args.input)) if args.input else None
        campaign_errors: list[str] = []
        if args.campaign_verification:
            report = json.loads(Path(args.campaign_verification).read_text(encoding="utf-8"))
            campaign_errors = _campaign_report_errors(result, report)
        errors = validate(result, expected, campaign_verified=bool(args.campaign_verification) and not campaign_errors)
        errors.extend(campaign_errors)
    except (OSError, ProtocolError, json.JSONDecodeError) as exc:
        print(json.dumps({"valid": False, "errors": [str(exc)]}))
        return 2
    print(json.dumps({"valid": not errors, "errors": errors}, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
