#!/usr/bin/env python3
"""Verify admin authorization and two role-separated V24 review decisions."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from review_auth import (
    ROLES,
    canonical_bytes,
    gate_classification,
    load_canonical,
    parse_time,
    sha256_bytes,
    sha256_file,
    validate_decision,
    validate_request,
    validate_spec,
    verify_admin_registry_signature,
    verify_evidence,
    verify_ssh_signature,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", required=True, type=Path)
    parser.add_argument("--admin-policy", required=True, type=Path)
    parser.add_argument("--registry", required=True, type=Path)
    parser.add_argument("--admin-signature", required=True, type=Path)
    parser.add_argument("--requests", required=True, type=Path)
    parser.add_argument("--decisions", required=True, type=Path)
    parser.add_argument("--evidence-root", required=True, type=Path)
    parser.add_argument("--verified-at", required=True)
    parser.add_argument("--report", required=True, type=Path)
    args = parser.parse_args()
    if args.report.exists() or args.report.with_suffix(args.report.suffix + ".sha256").exists():
        raise SystemExit("review-gate report already exists")
    spec = json.loads(args.spec.read_text())
    validate_spec(spec)
    policy = json.loads(args.admin_policy.read_text())
    if sha256_bytes(canonical_bytes(policy)) != spec["admin_policy_sha256"]:
        raise SystemExit("admin policy digest mismatch")
    registry, registry_sha256 = verify_admin_registry_signature(
        policy, args.registry, args.admin_signature
    )
    reviewers = {row["role"]: row for row in registry["reviewers"]}
    verified_at = parse_time(args.verified_at)
    decisions = {}
    rejected = False
    for role in ROLES:
        request_path = args.requests / f"{role}.request.json"
        request, request_sha256 = load_canonical(request_path)
        validate_request(request, spec, reviewers[role], registry_sha256)
        if not (parse_time(request["issued_at"]) <= verified_at <= parse_time(request["expires_at"])):
            raise ValueError("gate verification is outside request window")
        decision_path = args.decisions / f"{role}.decision.json"
        signature_path = args.decisions / f"{role}.decision.json.sig"
        decision, decision_sha256 = load_canonical(decision_path)
        validate_decision(decision, request, request_sha256, spec)
        verify_evidence(args.evidence_root, decision["evidence"])
        verify_ssh_signature(
            [reviewers[role]["public_key"]],
            reviewers[role]["signer_identity"],
            spec["review_namespace"],
            signature_path,
            decision_path.read_bytes(),
        )
        rejected |= (
            decision["result"] == "Fail" or decision["material_findings_unresolved"]
        )
        decisions[role] = {
            "decision_sha256": decision_sha256,
            "reviewer_kind": reviewers[role]["reviewer_kind"],
            "reviewer_public_key_fingerprint": reviewers[role]["public_key_fingerprint"],
            "result": decision["result"],
            "signature_sha256": sha256_file(signature_path),
            "signer_identity": reviewers[role]["signer_identity"],
        }
    status = "SignedReviewGateRejected" if rejected else gate_classification(reviewers)
    report = {
        "admin_authority": "AssignmentOnly",
        "admin_id": policy["admin_id"],
        "admin_signature_sha256": sha256_file(args.admin_signature),
        "artifact_identity": spec["artifact_identity"],
        "capsule_identity": spec["capsule_identity"],
        "claim_ceiling": spec["claim_ceiling"],
        "decisions": decisions,
        "external_states": spec["external_states"],
        "independently_verified": "NotRun",
        "release_identity": spec["release_identity"],
        "reviewer_registry_sha256": registry_sha256,
        "schema_version": 2,
        "source_commit": spec["source_commit"],
        "source_tree": spec["source_tree"],
        "status": status,
        "verified_at": args.verified_at,
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    digest = sha256_file(args.report)
    args.report.with_suffix(args.report.suffix + ".sha256").write_text(
        f"{digest}  {args.report.name}\n"
    )
    print(json.dumps({"report_sha256": digest, "status": status}, sort_keys=True))
    return 1 if rejected else 0


if __name__ == "__main__":
    raise SystemExit(main())
