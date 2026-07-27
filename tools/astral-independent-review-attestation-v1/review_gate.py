#!/usr/bin/env python3
"""Fail-closed signed-review primitives for the Astral review gate."""

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
GIT_OBJECT_ID = re.compile(r"^[0-9a-f]{40}$")
SIGNER_IDENTITY = re.compile(r"^[A-Za-z0-9._@+-]{3,128}$")
PASS_RESULTS = {"Pass", "PassWithFindings"}
SEVERITIES = {"Informational", "Minor", "Material", "Critical"}
FINDING_STATUSES = {"Open", "Resolved"}
AUDIT_STATUSES = {"Pass", "Concern", "Fail"}
EXPECTED_EXTERNAL_GATES = {
    "independent_implementation_replication": "NotRun",
    "reproducibility_reviewer": "NotRun",
    "scientific_reviewer": "NotRun",
    "stage_0c_confirmation": "Blocked",
    "stage_1": "BlockedByStage0C",
}


def canonical_bytes(value: object) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
        + "\n"
    ).encode()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def write_canonical(path: Path, value: object) -> str:
    data = canonical_bytes(value)
    path.write_bytes(data)
    return sha256_bytes(data)


def load_canonical(path: Path) -> tuple[Any, str]:
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"required real JSON file absent: {path}")
    raw = path.read_bytes()
    value = json.loads(raw)
    if raw != canonical_bytes(value):
        raise ValueError(f"JSON is not canonical: {path.name}")
    return value, sha256_bytes(raw)


def parse_utc(value: str) -> datetime:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise ValueError("timestamp must use UTC Z form")
    parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    if parsed.isoformat().replace("+00:00", "Z") != value:
        raise ValueError("timestamp must be canonical RFC3339")
    return parsed


def safe_relative(value: str) -> bool:
    if not isinstance(value, str):
        return False
    path = PurePosixPath(value)
    return (
        value == path.as_posix()
        and value not in ("", ".")
        and not path.is_absolute()
        and ".." not in path.parts
    )


def key_fingerprint(public_key: str) -> str:
    parts = public_key.split()
    if len(parts) != 2 or parts[0] != "ssh-ed25519":
        raise ValueError("reviewer key must be comment-free ssh-ed25519")
    with tempfile.TemporaryDirectory(prefix="astral-review-key-") as raw:
        key_path = Path(raw) / "reviewer.pub"
        key_path.write_text(public_key + "\n")
        completed = subprocess.run(
            ["ssh-keygen", "-lf", str(key_path), "-E", "sha256"],
            check=True,
            capture_output=True,
            text=True,
        )
    fields = completed.stdout.split()
    if len(fields) < 2 or not fields[1].startswith("SHA256:"):
        raise ValueError("unable to derive reviewer key fingerprint")
    return fields[1]


def validate_spec(spec: dict[str, Any]) -> None:
    if spec.get("schema_version") != 1:
        raise ValueError("unsupported gate specification")
    for field in (
        "author_report_sha256",
        "capsule_identity",
        "release_package_identity",
    ):
        if not SHA256.fullmatch(spec.get(field, "")):
            raise ValueError(f"invalid specification digest: {field}")
    for field in ("release_commit", "release_tree"):
        if not GIT_OBJECT_ID.fullmatch(spec.get(field, "")):
            raise ValueError(f"invalid Git object identity: {field}")
    roles = spec.get("required_roles")
    if roles != ["artifact_reproducibility", "scientific_validity"]:
        raise ValueError("unexpected review role contract")
    if spec.get("allowed_results") != ["Pass", "PassWithFindings", "Fail"]:
        raise ValueError("unexpected result contract")


def validate_registry(registry: dict[str, Any], spec: dict[str, Any]) -> dict[str, dict[str, Any]]:
    if registry.get("schema_version") != 1:
        raise ValueError("unsupported registry schema")
    if registry.get("purpose") not in ("external_review", "protocol_test"):
        raise ValueError("invalid registry purpose")
    if not isinstance(registry.get("coordinator"), str) or not registry["coordinator"].strip():
        raise ValueError("registry coordinator is required")
    parse_utc(registry.get("registered_at", ""))
    reviewers = registry.get("reviewers")
    if not isinstance(reviewers, list) or len(reviewers) != len(spec["required_roles"]):
        raise ValueError("registry reviewer census mismatch")
    by_role = {}
    for reviewer in reviewers:
        if set(reviewer) != {
            "affiliation",
            "independence_disclosure",
            "public_key",
            "public_key_fingerprint",
            "reviewer_name",
            "role",
            "signer_identity",
        }:
            raise ValueError("registry reviewer fields mismatch")
        role = reviewer["role"]
        if role not in spec["required_roles"] or role in by_role:
            raise ValueError("registry role mismatch")
        for field in ("affiliation", "independence_disclosure", "reviewer_name"):
            if not isinstance(reviewer[field], str) or not reviewer[field].strip():
                raise ValueError(f"registry reviewer field required: {field}")
        if not SIGNER_IDENTITY.fullmatch(reviewer["signer_identity"]):
            raise ValueError("invalid signer identity")
        derived = key_fingerprint(reviewer["public_key"])
        if reviewer["public_key_fingerprint"] != derived:
            raise ValueError("reviewer key fingerprint mismatch")
        by_role[role] = reviewer
    if set(by_role) != set(spec["required_roles"]):
        raise ValueError("required reviewer role absent")
    for field in ("signer_identity", "reviewer_name", "public_key", "public_key_fingerprint"):
        if len({reviewer[field] for reviewer in reviewers}) != len(reviewers):
            raise ValueError(f"reviewers are not distinct by {field}")
    return by_role


def build_request(
    spec: dict[str, Any],
    reviewer: dict[str, Any],
    nonce: str,
    issued_at: str,
    expires_at: str,
) -> dict[str, Any]:
    if not SHA256.fullmatch(nonce):
        raise ValueError("review request nonce must be 32-byte lowercase hex")
    if parse_utc(issued_at) >= parse_utc(expires_at):
        raise ValueError("review request expiry must follow issuance")
    return {
        "affiliation": reviewer["affiliation"],
        "author_report_sha256": spec["author_report_sha256"],
        "capsule_identity": spec["capsule_identity"],
        "claim_ceiling": spec["claim_ceiling"],
        "expires_at": expires_at,
        "issued_at": issued_at,
        "namespace": spec["namespace"],
        "nonce": nonce,
        "public_key_fingerprint": reviewer["public_key_fingerprint"],
        "release_commit": spec["release_commit"],
        "release_package_identity": spec["release_package_identity"],
        "release_tree": spec["release_tree"],
        "reviewer_name": reviewer["reviewer_name"],
        "role": reviewer["role"],
        "schema_version": 1,
        "signer_identity": reviewer["signer_identity"],
    }


def decision_template(
    request: dict[str, Any], request_sha256: str
) -> dict[str, Any]:
    return {
        "affiliation": request["affiliation"],
        "author_assistance": "",
        "author_report_sha256": request["author_report_sha256"],
        "capsule_identity": request["capsule_identity"],
        "claim_corrections": [],
        "claim_ceiling": request["claim_ceiling"],
        "conflict_disclosure": "",
        "environment_differences": [],
        "evidence": [],
        "findings": [],
        "independence_declaration": {
            "independent_of_v1_v23_implementation": False,
            "not_author_controlled": False,
        },
        "release_commit": request["release_commit"],
        "release_package_identity": request["release_package_identity"],
        "release_tree": request["release_tree"],
        "request_sha256": request_sha256,
        "result": "NotRun",
        "reviewed_at": "",
        "reviewer_name": request["reviewer_name"],
        "role": request["role"],
        "schema_version": 1,
        "signer_identity": request["signer_identity"],
    }


def validate_request(
    request: dict[str, Any],
    spec: dict[str, Any],
    reviewer: dict[str, Any],
) -> None:
    expected_fields = set(
        build_request(
            spec,
            reviewer,
            "0" * 64,
            "2000-01-01T00:00:00Z",
            "2000-01-02T00:00:00Z",
        )
    )
    if set(request) != expected_fields:
        raise ValueError("request fields mismatch")
    for field in (
        "affiliation",
        "public_key_fingerprint",
        "reviewer_name",
        "role",
        "signer_identity",
    ):
        if request.get(field) != reviewer[field]:
            raise ValueError(f"request reviewer binding mismatch: {field}")
    for field in (
        "author_report_sha256",
        "capsule_identity",
        "claim_ceiling",
        "namespace",
        "release_commit",
        "release_package_identity",
        "release_tree",
    ):
        if request.get(field) != spec[field]:
            raise ValueError(f"request artifact binding mismatch: {field}")
    if not SHA256.fullmatch(request.get("nonce", "")):
        raise ValueError("request nonce invalid")
    if parse_utc(request["issued_at"]) >= parse_utc(request["expires_at"]):
        raise ValueError("request time window invalid")


def validate_findings(findings: Any, result: str) -> None:
    if not isinstance(findings, list):
        raise ValueError("findings must be a list")
    for finding in findings:
        if set(finding) != {"code", "severity", "status", "summary"}:
            raise ValueError("finding fields mismatch")
        if (
            finding["severity"] not in SEVERITIES
            or finding["status"] not in FINDING_STATUSES
            or not isinstance(finding["code"], str)
            or not finding["code"].strip()
            or not isinstance(finding["summary"], str)
            or not finding["summary"].strip()
        ):
            raise ValueError("invalid finding")
    if result == "Pass" and findings:
        raise ValueError("Pass cannot carry findings")
    if result == "PassWithFindings" and not findings:
        raise ValueError("PassWithFindings requires findings")
    if result in PASS_RESULTS and any(
        finding["status"] == "Open"
        and finding["severity"] in {"Material", "Critical"}
        for finding in findings
    ):
        raise ValueError("unresolved material finding blocks pass")


def _evidence_files(
    evidence: Any, evidence_root: Path
) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    if not isinstance(evidence, list):
        raise ValueError("evidence must be a list")
    by_label = {}
    parsed = {}
    for item in evidence:
        if set(item) != {"label", "path", "sha256"}:
            raise ValueError("evidence fields mismatch")
        if (
            not isinstance(item["label"], str)
            or not item["label"]
            or item["label"] in by_label
            or not safe_relative(item["path"])
            or not SHA256.fullmatch(item["sha256"])
        ):
            raise ValueError("invalid evidence entry")
        path = evidence_root / item["path"]
        if path.is_symlink() or not path.is_file() or sha256_file(path) != item["sha256"]:
            raise ValueError(f"evidence bytes mismatch: {item['label']}")
        by_label[item["label"]] = item
        if path.suffix == ".json":
            parsed[item["label"]] = json.loads(path.read_text())
    return by_label, parsed


def validate_role_evidence(
    role: str,
    evidence: Any,
    evidence_root: Path,
    spec: dict[str, Any],
    result: str,
) -> None:
    by_label, parsed = _evidence_files(evidence, evidence_root)
    if role == "artifact_reproducibility":
        if set(by_label) != {"capsule_run", "reviewer_report"}:
            raise ValueError("artifact-review evidence census mismatch")
        capsule_run = parsed.get("capsule_run", {})
        reviewer_report = parsed.get("reviewer_report", {})
        if (
            capsule_run.get("status") != "CapsuleReplayPassed"
            or capsule_run.get("capsule_identity") != spec["capsule_identity"]
            or capsule_run.get("release_commit") != spec["release_commit"]
            or capsule_run.get("release_tree") != spec["release_tree"]
            or capsule_run.get("release_package_identity")
            != spec["release_package_identity"]
            or capsule_run.get("claim_ceiling") != spec["claim_ceiling"]
            or capsule_run.get("independence_status") != "Unasserted"
        ):
            raise ValueError("capsule-run evidence binding mismatch")
        if (
            reviewer_report.get("status") != "local_immutable_validation_passed"
            or reviewer_report.get("git_tree") != spec["release_tree"]
            or reviewer_report.get("package", {}).get("package_identity")
            != spec["release_package_identity"]
            or reviewer_report.get("claim_ceiling") != spec["claim_ceiling"]
            or reviewer_report.get("external_gates") != EXPECTED_EXTERNAL_GATES
        ):
            raise ValueError("reviewer-report evidence binding mismatch")
    elif role == "scientific_validity":
        if set(by_label) != {"scientific_audit"}:
            raise ValueError("scientific-review evidence census mismatch")
        audit = parsed.get("scientific_audit", {})
        sections = audit.get("sections")
        if (
            audit.get("schema_version") != 1
            or audit.get("capsule_identity") != spec["capsule_identity"]
            or not isinstance(sections, dict)
            or set(sections) != set(spec["required_scientific_sections"])
        ):
            raise ValueError("scientific audit binding mismatch")
        for name, section in sections.items():
            if (
                set(section) != {"notes", "status"}
                or section["status"] not in AUDIT_STATUSES
                or not isinstance(section["notes"], str)
                or not section["notes"].strip()
            ):
                raise ValueError(f"invalid scientific audit section: {name}")
        statuses = {section["status"] for section in sections.values()}
        if result in PASS_RESULTS and "Fail" in statuses:
            raise ValueError("failed scientific audit section blocks pass")
        if result == "Pass" and statuses != {"Pass"}:
            raise ValueError("scientific Pass requires all sections to pass")
        if result == "PassWithFindings" and "Concern" not in statuses:
            raise ValueError("scientific PassWithFindings requires a concern")
    else:
        raise ValueError("unknown review role")


def verify_signature(
    decision_path: Path,
    signature_path: Path,
    reviewer: dict[str, Any],
    namespace: str,
) -> None:
    if signature_path.is_symlink() or not signature_path.is_file():
        raise ValueError("review signature missing")
    with tempfile.TemporaryDirectory(prefix="astral-allowed-signers-") as raw:
        allowed = Path(raw) / "allowed_signers"
        allowed.write_text(
            f"{reviewer['signer_identity']} {reviewer['public_key']}\n"
        )
        completed = subprocess.run(
            [
                "ssh-keygen",
                "-Y",
                "verify",
                "-f",
                str(allowed),
                "-I",
                reviewer["signer_identity"],
                "-n",
                namespace,
                "-s",
                str(signature_path),
            ],
            input=decision_path.read_bytes(),
            capture_output=True,
        )
    if completed.returncode != 0:
        raise ValueError("review signature verification failed")


def validate_decision(
    decision_path: Path,
    signature_path: Path,
    request: dict[str, Any],
    request_sha256: str,
    reviewer: dict[str, Any],
    spec: dict[str, Any],
    evidence_root: Path,
) -> tuple[dict[str, Any], str]:
    decision, decision_sha256 = load_canonical(decision_path)
    if set(decision) != set(decision_template(request, request_sha256)):
        raise ValueError("decision fields mismatch")
    for field in (
        "affiliation",
        "reviewer_name",
        "role",
        "signer_identity",
    ):
        if decision.get(field) != reviewer[field]:
            raise ValueError(f"decision reviewer binding mismatch: {field}")
    for field in (
        "author_report_sha256",
        "capsule_identity",
        "claim_ceiling",
        "release_commit",
        "release_package_identity",
        "release_tree",
    ):
        if decision.get(field) != spec[field]:
            raise ValueError(f"decision artifact binding mismatch: {field}")
    if decision.get("request_sha256") != request_sha256:
        raise ValueError("decision request binding mismatch")
    reviewed_at = parse_utc(decision.get("reviewed_at", ""))
    if not (parse_utc(request["issued_at"]) <= reviewed_at <= parse_utc(request["expires_at"])):
        raise ValueError("decision outside request validity window")
    if (
        decision.get("result") not in spec["allowed_results"]
        or not isinstance(decision.get("conflict_disclosure"), str)
        or not decision["conflict_disclosure"].strip()
        or decision.get("independence_declaration")
        != {
            "independent_of_v1_v23_implementation": True,
            "not_author_controlled": True,
        }
        or not isinstance(decision.get("author_assistance"), str)
        or not isinstance(decision.get("environment_differences"), list)
        or not isinstance(decision.get("claim_corrections"), list)
    ):
        raise ValueError("decision disclosure or result invalid")
    validate_findings(decision["findings"], decision["result"])
    validate_role_evidence(
        decision["role"],
        decision["evidence"],
        evidence_root,
        spec,
        decision["result"],
    )
    verify_signature(
        decision_path,
        signature_path,
        reviewer,
        spec["namespace"],
    )
    return decision, decision_sha256


def verify_gate(
    spec: dict[str, Any],
    registry_path: Path,
    expected_registry_sha256: str,
    requests_dir: Path,
    decisions_dir: Path,
    evidence_root: Path,
) -> dict[str, Any]:
    validate_spec(spec)
    if not SHA256.fullmatch(expected_registry_sha256):
        raise ValueError("expected registry digest invalid")
    registry, registry_sha256 = load_canonical(registry_path)
    if registry_sha256 != expected_registry_sha256:
        raise ValueError("reviewer registry digest mismatch")
    reviewers = validate_registry(registry, spec)
    request_hashes = {}
    decisions = {}
    decision_hashes = {}
    signature_hashes = {}
    nonces = set()
    for role in spec["required_roles"]:
        request_path = requests_dir / f"{role}.request.json"
        request, request_sha256 = load_canonical(request_path)
        validate_request(request, spec, reviewers[role])
        if request["nonce"] in nonces:
            raise ValueError("review request nonce reused")
        nonces.add(request["nonce"])
        decision_path = decisions_dir / f"{role}.decision.json"
        signature_path = decision_path.with_suffix(decision_path.suffix + ".sig")
        decision, decision_sha256 = validate_decision(
            decision_path,
            signature_path,
            request,
            request_sha256,
            reviewers[role],
            spec,
            evidence_root,
        )
        request_hashes[role] = request_sha256
        decisions[role] = decision
        decision_hashes[role] = decision_sha256
        signature_hashes[role] = sha256_file(signature_path)
    if any(decision["result"] == "Fail" for decision in decisions.values()):
        status = "SignedReviewGateRejected"
    elif registry["purpose"] == "protocol_test":
        status = "SyntheticSignedReviewProtocolPassed"
    else:
        status = "SignedReviewQuorumCandidate"
    return {
        "status": status,
        "claim_ceiling": spec["claim_ceiling"],
        "independence_status": "DeclaredNotVerified",
        "registry_purpose": registry["purpose"],
        "reviewer_registry_sha256": registry_sha256,
        "capsule_identity": spec["capsule_identity"],
        "release_commit": spec["release_commit"],
        "release_tree": spec["release_tree"],
        "release_package_identity": spec["release_package_identity"],
        "request_sha256": request_hashes,
        "decision_sha256": decision_hashes,
        "signature_sha256": signature_hashes,
        "results": {
            role: decisions[role]["result"] for role in spec["required_roles"]
        },
        "external_gates": {
            "human_identity_and_conflict_verification": "Required",
            "independent_implementation_replication": "NotRun",
            "stage_0c_confirmation": "Blocked",
            "stage_1": "BlockedByStage0C",
        },
    }
