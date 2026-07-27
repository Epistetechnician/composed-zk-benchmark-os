#!/usr/bin/env python3
"""Canonical data and signature checks for V24 reviewer authorization."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path, PurePosixPath
from typing import Any


SHA256 = re.compile(r"^[0-9a-f]{64}$")
ROLES = ("artifact_reproducibility", "scientific_validity")
REVIEWER_KINDS = ("agent_advisory", "external_human")
ALLOWED_RESULTS = ("Pass", "PassWithFindings", "Fail")
REVIEW_NAMESPACE = "astral-v24-independent-review-v2"
REQUIRED_EVIDENCE = {
    "artifact_reproducibility": {"capsule_run", "reviewer_report"},
    "scientific_validity": {
        "capsule_run",
        "reviewer_report",
        "v24_execution_record",
        "v24_preregistration",
    },
}


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_bytes(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode() + b"\n"


def write_canonical(path: Path, value: object) -> str:
    content = canonical_bytes(value)
    path.write_bytes(content)
    return sha256_bytes(content)


def load_canonical(path: Path) -> tuple[Any, str]:
    value = json.loads(path.read_text())
    content = canonical_bytes(value)
    if path.read_bytes() != content:
        raise ValueError(f"JSON is not canonical: {path.name}")
    return value, sha256_bytes(content)


def parse_time(value: str) -> datetime:
    if not isinstance(value, str) or value == "UNFILLED":
        raise ValueError("timestamp is absent")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("timestamp is not RFC3339-compatible") from exc
    if parsed.tzinfo is None:
        raise ValueError("timestamp must carry a timezone")
    return parsed


def safe_relative(value: str) -> bool:
    path = PurePosixPath(value)
    return (
        value == path.as_posix()
        and value not in ("", ".")
        and not path.is_absolute()
        and ".." not in path.parts
    )


def fingerprint_public_key(public_key: str) -> str:
    if not isinstance(public_key, str) or not public_key.startswith("ssh-ed25519 "):
        raise ValueError("only Ed25519 OpenSSH public keys are accepted")
    with tempfile.TemporaryDirectory() as raw:
        path = Path(raw) / "key.pub"
        path.write_text(public_key.strip() + "\n")
        completed = subprocess.run(
            ["ssh-keygen", "-E", "sha256", "-lf", str(path)],
            check=True,
            capture_output=True,
            text=True,
        )
    fields = completed.stdout.split()
    if len(fields) < 2 or not fields[1].startswith("SHA256:"):
        raise ValueError("could not derive public-key fingerprint")
    return fields[1]


def verify_ssh_signature(
    public_keys: list[str],
    signer_identity: str,
    namespace: str,
    signature: Path,
    message: bytes,
) -> None:
    if signature.is_symlink() or not signature.is_file():
        raise ValueError("signature must be a real file")
    with tempfile.TemporaryDirectory() as raw:
        allowed = Path(raw) / "allowed_signers"
        allowed.write_text(
            "".join(f"{signer_identity} {key.strip()}\n" for key in public_keys)
        )
        completed = subprocess.run(
            [
                "ssh-keygen",
                "-Y",
                "verify",
                "-f",
                str(allowed),
                "-I",
                signer_identity,
                "-n",
                namespace,
                "-s",
                str(signature),
            ],
            input=message,
            capture_output=True,
        )
    if completed.returncode != 0:
        raise ValueError("OpenSSH signature verification failed")


def validate_admin_policy(policy: dict[str, Any]) -> dict[str, Any]:
    required = {
        "admin_id",
        "allowed_public_keys",
        "assignment_capabilities",
        "display_name",
        "namespace",
        "prohibitions",
        "role",
        "schema_version",
    }
    if set(policy) != required or policy["schema_version"] != 2:
        raise ValueError("admin policy shape mismatch")
    if (
        policy["admin_id"] != "shaanp"
        or policy["role"] != "AdminCoordinator"
        or policy["namespace"] != "astral-v24-review-admin-v2"
    ):
        raise ValueError("admin identity or role mismatch")
    keys = policy["allowed_public_keys"]
    if not isinstance(keys, list) or not keys:
        raise ValueError("admin policy has no public keys")
    public_keys, fingerprints = set(), set()
    for row in keys:
        if set(row) != {"fingerprint", "public_key"}:
            raise ValueError("admin public-key row shape mismatch")
        actual = fingerprint_public_key(row["public_key"])
        if actual != row["fingerprint"]:
            raise ValueError("admin public-key fingerprint mismatch")
        public_keys.add(row["public_key"].strip())
        fingerprints.add(actual)
    if len(public_keys) != len(keys) or len(fingerprints) != len(keys):
        raise ValueError("duplicate admin public key")
    return policy


def validate_spec(spec: dict[str, Any]) -> dict[str, Any]:
    required = {
        "admin_policy_sha256",
        "artifact_identity",
        "author_report_sha256",
        "capsule_identity",
        "claim_ceiling",
        "external_states",
        "release_identity",
        "required_roles",
        "required_scientific_sections",
        "review_namespace",
        "schema_version",
        "source_commit",
        "source_tree",
    }
    if set(spec) != required or spec["schema_version"] != 2:
        raise ValueError("review gate specification shape mismatch")
    for field in (
        "admin_policy_sha256",
        "artifact_identity",
        "author_report_sha256",
        "capsule_identity",
        "release_identity",
    ):
        if not SHA256.fullmatch(spec[field]):
            raise ValueError(f"invalid SHA-256 field: {field}")
    if not re.fullmatch(r"[0-9a-f]{40}", spec["source_commit"]):
        raise ValueError("source commit shape mismatch")
    if not re.fullmatch(r"[0-9a-f]{40}", spec["source_tree"]):
        raise ValueError("source tree shape mismatch")
    if (
        spec["claim_ceiling"] != "LocalAuthorDevelopmentPerturbationReadout"
        or spec["required_roles"] != list(ROLES)
        or spec["review_namespace"] != REVIEW_NAMESPACE
        or spec["external_states"].get("independently_verified") != "NotRun"
        or spec["external_states"].get("confirmation") != "NotAuthorized"
        or spec["external_states"].get("stage_0c") != "Blocked"
    ):
        raise ValueError("review gate claim or external-state boundary mismatch")
    return spec


def validate_registry(
    registry: dict[str, Any], policy: dict[str, Any]
) -> dict[str, dict[str, Any]]:
    required = {"admin_id", "purpose", "registered_at", "reviewers", "schema_version"}
    if set(registry) != required or registry["schema_version"] != 2:
        raise ValueError("reviewer registry shape mismatch")
    if registry["admin_id"] != policy["admin_id"] or registry["purpose"] != "astral_v24_review":
        raise ValueError("reviewer registry admin or purpose mismatch")
    parse_time(registry["registered_at"])
    reviewers = registry["reviewers"]
    if not isinstance(reviewers, list) or len(reviewers) != len(ROLES):
        raise ValueError("reviewer registry must contain exactly two roles")
    expected_fields = {
        "affiliation",
        "counts_toward_independent_verification",
        "independence_disclosure",
        "public_key",
        "public_key_fingerprint",
        "reviewer_kind",
        "reviewer_name",
        "role",
        "signer_identity",
    }
    admin_keys = {row["public_key"].strip() for row in policy["allowed_public_keys"]}
    by_role = {}
    signer_ids, reviewer_keys = set(), set()
    for reviewer in reviewers:
        if set(reviewer) != expected_fields:
            raise ValueError("reviewer row shape mismatch")
        role = reviewer["role"]
        kind = reviewer["reviewer_kind"]
        if role not in ROLES or role in by_role or kind not in REVIEWER_KINDS:
            raise ValueError("reviewer role or kind mismatch")
        for field in (
            "affiliation",
            "independence_disclosure",
            "reviewer_name",
            "signer_identity",
        ):
            if not isinstance(reviewer[field], str) or reviewer[field] in ("", "UNFILLED"):
                raise ValueError(f"reviewer field is unfilled: {field}")
        public_key = reviewer["public_key"].strip()
        if public_key in admin_keys or reviewer["signer_identity"] == policy["admin_id"]:
            raise ValueError("admin cannot also be a reviewer")
        actual_fingerprint = fingerprint_public_key(public_key)
        if actual_fingerprint != reviewer["public_key_fingerprint"]:
            raise ValueError("reviewer public-key fingerprint mismatch")
        expected_count = kind == "external_human"
        if reviewer["counts_toward_independent_verification"] is not expected_count:
            raise ValueError("reviewer independence-count flag mismatch")
        if reviewer["signer_identity"] in signer_ids or public_key in reviewer_keys:
            raise ValueError("reviewers must have distinct identities and keys")
        signer_ids.add(reviewer["signer_identity"])
        reviewer_keys.add(public_key)
        by_role[role] = reviewer
    if set(by_role) != set(ROLES):
        raise ValueError("required reviewer role is absent")
    return by_role


def verify_admin_registry_signature(
    policy: dict[str, Any], registry_path: Path, signature: Path
) -> tuple[dict[str, Any], str]:
    validate_admin_policy(policy)
    registry, registry_sha256 = load_canonical(registry_path)
    validate_registry(registry, policy)
    verify_ssh_signature(
        [row["public_key"] for row in policy["allowed_public_keys"]],
        policy["admin_id"],
        policy["namespace"],
        signature,
        registry_path.read_bytes(),
    )
    return registry, registry_sha256


def build_request(
    spec: dict[str, Any],
    reviewer: dict[str, Any],
    registry_sha256: str,
    nonce: str,
    issued_at: str,
    expires_at: str,
) -> dict[str, Any]:
    validate_spec(spec)
    if not SHA256.fullmatch(registry_sha256) or not SHA256.fullmatch(nonce):
        raise ValueError("request registry digest or nonce is invalid")
    if parse_time(issued_at) >= parse_time(expires_at):
        raise ValueError("request expiry must follow issuance")
    return {
        "artifact_identity": spec["artifact_identity"],
        "capsule_identity": spec["capsule_identity"],
        "claim_ceiling": spec["claim_ceiling"],
        "expires_at": expires_at,
        "issued_at": issued_at,
        "nonce": nonce,
        "release_identity": spec["release_identity"],
        "review_namespace": spec["review_namespace"],
        "reviewer_kind": reviewer["reviewer_kind"],
        "reviewer_public_key_fingerprint": reviewer["public_key_fingerprint"],
        "reviewer_registry_sha256": registry_sha256,
        "role": reviewer["role"],
        "schema_version": 2,
        "signer_identity": reviewer["signer_identity"],
        "source_commit": spec["source_commit"],
        "source_tree": spec["source_tree"],
    }


def validate_request(
    request: dict[str, Any],
    spec: dict[str, Any],
    reviewer: dict[str, Any],
    registry_sha256: str,
) -> None:
    expected = build_request(
        spec,
        reviewer,
        registry_sha256,
        request.get("nonce", ""),
        request.get("issued_at", ""),
        request.get("expires_at", ""),
    )
    if request != expected:
        raise ValueError("review request binding mismatch")


def decision_template(request: dict[str, Any], request_sha256: str) -> dict[str, Any]:
    value = {
        "assistance_disclosure": "UNFILLED",
        "evidence": [],
        "findings": [],
        "material_findings_unresolved": True,
        "request_sha256": request_sha256,
        "result": "UNFILLED",
        "reviewed_at": "UNFILLED",
        "reviewer_kind": request["reviewer_kind"],
        "role": request["role"],
        "schema_version": 2,
    }
    if request["role"] == "scientific_validity":
        value["sections"] = {
            section: "UNFILLED"
            for section in (
                "assessment_sealing",
                "claim_ceiling",
                "control_strength",
                "corpus_overlap_and_leakage",
                "preregistration_chronology",
                "statistics_and_uncertainty",
                "stopping_and_selection_rules",
            )
        }
    return value


def validate_decision(
    decision: dict[str, Any],
    request: dict[str, Any],
    request_sha256: str,
    spec: dict[str, Any],
) -> None:
    fields = {
        "assistance_disclosure",
        "evidence",
        "findings",
        "material_findings_unresolved",
        "request_sha256",
        "result",
        "reviewed_at",
        "reviewer_kind",
        "role",
        "schema_version",
    }
    if request["role"] == "scientific_validity":
        fields.add("sections")
    if set(decision) != fields or decision["schema_version"] != 2:
        raise ValueError("review decision shape mismatch")
    if (
        decision["request_sha256"] != request_sha256
        or decision["role"] != request["role"]
        or decision["reviewer_kind"] != request["reviewer_kind"]
        or decision["result"] not in ALLOWED_RESULTS
    ):
        raise ValueError("review decision request or disposition mismatch")
    reviewed_at = parse_time(decision["reviewed_at"])
    if not (parse_time(request["issued_at"]) <= reviewed_at <= parse_time(request["expires_at"])):
        raise ValueError("review decision timestamp is outside request window")
    if decision["assistance_disclosure"] in ("", "UNFILLED"):
        raise ValueError("assistance disclosure is unfilled")
    findings = decision["findings"]
    if not isinstance(findings, list):
        raise ValueError("findings must be a list")
    material_unresolved = False
    for finding in findings:
        if set(finding) != {"resolved", "severity", "text"}:
            raise ValueError("finding shape mismatch")
        if finding["severity"] not in ("info", "minor", "material"):
            raise ValueError("finding severity mismatch")
        if not isinstance(finding["resolved"], bool) or not finding["text"]:
            raise ValueError("finding content mismatch")
        material_unresolved |= finding["severity"] == "material" and not finding["resolved"]
    if decision["material_findings_unresolved"] is not material_unresolved:
        raise ValueError("material-finding summary mismatch")
    if findings and decision["result"] == "Pass":
        raise ValueError("Pass cannot conceal findings")
    if not findings and decision["result"] == "PassWithFindings":
        raise ValueError("PassWithFindings requires findings")
    evidence = decision["evidence"]
    if not isinstance(evidence, list):
        raise ValueError("evidence must be a list")
    labels = set()
    for row in evidence:
        if set(row) != {"label", "path", "sha256"}:
            raise ValueError("evidence row shape mismatch")
        if (
            not row["label"]
            or row["label"] in labels
            or not safe_relative(row["path"])
            or not SHA256.fullmatch(row["sha256"])
        ):
            raise ValueError("evidence row value mismatch")
        labels.add(row["label"])
    if labels != REQUIRED_EVIDENCE[request["role"]]:
        raise ValueError("required evidence labels mismatch")
    if request["role"] == "scientific_validity":
        sections = decision["sections"]
        if set(sections) != set(spec["required_scientific_sections"]):
            raise ValueError("scientific section census mismatch")
        if any(value in ("", "UNFILLED") for value in sections.values()):
            raise ValueError("scientific section is unfilled")


def verify_evidence(evidence_root: Path, evidence: list[dict[str, str]]) -> None:
    if evidence_root.is_symlink() or not evidence_root.is_dir():
        raise ValueError("evidence root must be a real directory")
    for row in evidence:
        path = evidence_root / row["path"]
        current = evidence_root
        for component in PurePosixPath(row["path"]).parts:
            current = current / component
            if current.is_symlink():
                raise ValueError("evidence symlink is forbidden")
        if not path.is_file() or sha256_file(path) != row["sha256"]:
            raise ValueError(f"evidence digest mismatch: {row['label']}")


def gate_classification(reviewers: dict[str, dict[str, Any]]) -> str:
    if all(row["reviewer_kind"] == "external_human" for row in reviewers.values()):
        return "SignedExternalReviewQuorumCandidate"
    return "AuthorizedAgentReviewAdvisoryCandidate"
