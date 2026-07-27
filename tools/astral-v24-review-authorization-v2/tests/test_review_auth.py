from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("astral_v24_review_auth", ROOT / "review_auth.py")
AUTH = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = AUTH
assert SPEC.loader
SPEC.loader.exec_module(AUTH)

sys.path.insert(0, str(ROOT))
KIT_SPEC = importlib.util.spec_from_file_location(
    "astral_v24_review_kit", ROOT / "verify_kit.py"
)
KIT = importlib.util.module_from_spec(KIT_SPEC)
sys.modules[KIT_SPEC.name] = KIT
assert KIT_SPEC.loader
KIT_SPEC.loader.exec_module(KIT)


def generate_key(root: Path, name: str) -> tuple[Path, str, str]:
    private = root / name
    subprocess.run(
        ["ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-f", str(private)],
        check=True,
    )
    public_key = private.with_suffix(".pub").read_text().strip()
    return private, public_key, AUTH.fingerprint_public_key(public_key)


def sign(private: Path, namespace: str, path: Path) -> Path:
    subprocess.run(
        ["ssh-keygen", "-Y", "sign", "-f", str(private), "-n", namespace, str(path)],
        check=True,
        capture_output=True,
    )
    return Path(str(path) + ".sig")


def policy_for(admin_public: str, fingerprint: str) -> dict:
    return {
        "admin_id": "shaanp",
        "allowed_public_keys": [
            {"fingerprint": fingerprint, "public_key": admin_public}
        ],
        "assignment_capabilities": ["register_distinct_reviewer_identities"],
        "display_name": "Epistetechnic",
        "namespace": "astral-v24-review-admin-v2",
        "prohibitions": ["set_independently_verified"],
        "role": "AdminCoordinator",
        "schema_version": 2,
    }


def reviewer(role: str, public_key: str, fingerprint: str, index: int) -> dict:
    return {
        "affiliation": "local advisory harness",
        "counts_toward_independent_verification": False,
        "independence_disclosure": "author-environment advisory agent",
        "public_key": public_key,
        "public_key_fingerprint": fingerprint,
        "reviewer_kind": "agent_advisory",
        "reviewer_name": f"agent-{index}",
        "role": role,
        "signer_identity": f"agent-{index}",
    }


def test_committed_admin_policy_pins_shaanp_without_promotion_power():
    policy = AUTH.validate_admin_policy(json.loads((ROOT / "admin-policy.json").read_text()))
    assert policy["admin_id"] == "shaanp"
    assert policy["role"] == "AdminCoordinator"
    assert len(policy["allowed_public_keys"]) == 2
    assert "set_independently_verified" in policy["prohibitions"]


def test_admin_signed_registry_authorizes_two_distinct_advisory_agents(tmp_path):
    admin_private, admin_public, admin_fingerprint = generate_key(tmp_path, "admin")
    _, first_public, first_fingerprint = generate_key(tmp_path, "first")
    _, second_public, second_fingerprint = generate_key(tmp_path, "second")
    policy = policy_for(admin_public, admin_fingerprint)
    registry = {
        "admin_id": "shaanp",
        "purpose": "astral_v24_review",
        "registered_at": "2026-07-27T18:00:00Z",
        "reviewers": [
            reviewer("artifact_reproducibility", first_public, first_fingerprint, 1),
            reviewer("scientific_validity", second_public, second_fingerprint, 2),
        ],
        "schema_version": 2,
    }
    registry_path = tmp_path / "registry.json"
    AUTH.write_canonical(registry_path, registry)
    signature = sign(admin_private, policy["namespace"], registry_path)
    retained, digest = AUTH.verify_admin_registry_signature(
        policy, registry_path, signature
    )
    reviewers = AUTH.validate_registry(retained, policy)
    assert AUTH.SHA256.fullmatch(digest)
    assert AUTH.gate_classification(reviewers) == "AuthorizedAgentReviewAdvisoryCandidate"


def test_registry_rejects_admin_as_reviewer_and_reused_reviewer_key(tmp_path):
    _, admin_public, admin_fingerprint = generate_key(tmp_path, "admin")
    _, reviewer_public, reviewer_fingerprint = generate_key(tmp_path, "reviewer")
    policy = policy_for(admin_public, admin_fingerprint)
    registry = {
        "admin_id": "shaanp",
        "purpose": "astral_v24_review",
        "registered_at": "2026-07-27T18:00:00Z",
        "reviewers": [
            reviewer("artifact_reproducibility", admin_public, admin_fingerprint, 1),
            reviewer("scientific_validity", reviewer_public, reviewer_fingerprint, 2),
        ],
        "schema_version": 2,
    }
    with pytest.raises(ValueError, match="admin cannot also be a reviewer"):
        AUTH.validate_registry(registry, policy)
    registry["reviewers"][0] = reviewer(
        "artifact_reproducibility", reviewer_public, reviewer_fingerprint, 1
    )
    with pytest.raises(ValueError, match="distinct identities and keys"):
        AUTH.validate_registry(registry, policy)


def test_external_human_candidate_still_does_not_set_verified(tmp_path):
    _, admin_public, admin_fingerprint = generate_key(tmp_path, "admin")
    _, first_public, first_fingerprint = generate_key(tmp_path, "first")
    _, second_public, second_fingerprint = generate_key(tmp_path, "second")
    policy = policy_for(admin_public, admin_fingerprint)
    rows = [
        reviewer("artifact_reproducibility", first_public, first_fingerprint, 1),
        reviewer("scientific_validity", second_public, second_fingerprint, 2),
    ]
    for row in rows:
        row["reviewer_kind"] = "external_human"
        row["counts_toward_independent_verification"] = True
    registry = {
        "admin_id": "shaanp",
        "purpose": "astral_v24_review",
        "registered_at": "2026-07-27T18:00:00Z",
        "reviewers": rows,
        "schema_version": 2,
    }
    reviewers = AUTH.validate_registry(registry, policy)
    assert AUTH.gate_classification(reviewers) == "SignedExternalReviewQuorumCandidate"
    assert "Verified" not in AUTH.gate_classification(reviewers)


def test_advisory_decisions_are_role_bound_signed_and_evidence_complete(tmp_path):
    admin_private, admin_public, admin_fingerprint = generate_key(tmp_path, "admin")
    first_private, first_public, first_fingerprint = generate_key(tmp_path, "first")
    second_private, second_public, second_fingerprint = generate_key(tmp_path, "second")
    policy = policy_for(admin_public, admin_fingerprint)
    registry = {
        "admin_id": "shaanp",
        "purpose": "astral_v24_review",
        "registered_at": "2026-07-27T18:00:00Z",
        "reviewers": [
            reviewer("artifact_reproducibility", first_public, first_fingerprint, 1),
            reviewer("scientific_validity", second_public, second_fingerprint, 2),
        ],
        "schema_version": 2,
    }
    registry_path = tmp_path / "registry.json"
    registry_digest = AUTH.write_canonical(registry_path, registry)
    admin_signature = sign(admin_private, policy["namespace"], registry_path)
    AUTH.verify_admin_registry_signature(policy, registry_path, admin_signature)
    policy_digest = AUTH.sha256_bytes(AUTH.canonical_bytes(policy))
    spec = {
        "admin_policy_sha256": policy_digest,
        "artifact_identity": "a" * 64,
        "author_report_sha256": "b" * 64,
        "capsule_identity": "c" * 64,
        "claim_ceiling": "LocalAuthorDevelopmentPerturbationReadout",
        "external_states": {
            "confirmation": "NotAuthorized",
            "independently_verified": "NotRun",
            "stage_0c": "Blocked",
        },
        "release_identity": "d" * 64,
        "required_roles": list(AUTH.ROLES),
        "required_scientific_sections": [
            "assessment_sealing",
            "claim_ceiling",
            "control_strength",
            "corpus_overlap_and_leakage",
            "preregistration_chronology",
            "statistics_and_uncertainty",
            "stopping_and_selection_rules",
        ],
        "review_namespace": AUTH.REVIEW_NAMESPACE,
        "schema_version": 2,
        "source_commit": "e" * 40,
        "source_tree": "f" * 40,
    }
    AUTH.validate_spec(spec)
    evidence_root = tmp_path / "evidence"
    evidence_root.mkdir()
    by_role = AUTH.validate_registry(registry, policy)
    private_by_role = {
        "artifact_reproducibility": first_private,
        "scientific_validity": second_private,
    }
    for role in AUTH.ROLES:
        request = AUTH.build_request(
            spec,
            by_role[role],
            registry_digest,
            ("1" if role == "artifact_reproducibility" else "2") * 64,
            "2026-07-27T18:00:00Z",
            "2026-07-28T18:00:00Z",
        )
        request_path = tmp_path / f"{role}.request.json"
        request_digest = AUTH.write_canonical(request_path, request)
        decision = AUTH.decision_template(request, request_digest)
        decision["assistance_disclosure"] = "No assistance beyond supplied capsule."
        decision["material_findings_unresolved"] = False
        decision["result"] = "Pass"
        decision["reviewed_at"] = "2026-07-27T19:00:00Z"
        evidence = []
        for label in sorted(AUTH.REQUIRED_EVIDENCE[role]):
            path = evidence_root / f"{role}-{label}.json"
            path.write_text(f'{{"label":"{label}"}}\n')
            evidence.append(
                {
                    "label": label,
                    "path": path.relative_to(evidence_root).as_posix(),
                    "sha256": AUTH.sha256_file(path),
                }
            )
        decision["evidence"] = evidence
        if role == "scientific_validity":
            decision["sections"] = {
                section: "Reviewed; no material finding in advisory rehearsal."
                for section in spec["required_scientific_sections"]
            }
        decision_path = tmp_path / f"{role}.decision.json"
        AUTH.write_canonical(decision_path, decision)
        signature = sign(private_by_role[role], AUTH.REVIEW_NAMESPACE, decision_path)
        AUTH.validate_decision(decision, request, request_digest, spec)
        AUTH.verify_evidence(evidence_root, evidence)
        AUTH.verify_ssh_signature(
            [by_role[role]["public_key"]],
            by_role[role]["signer_identity"],
            AUTH.REVIEW_NAMESPACE,
            signature,
            decision_path.read_bytes(),
        )


def test_kit_verifier_rejects_extra_file(tmp_path):
    root = tmp_path / "staging"
    (root / "metadata").mkdir(parents=True)
    policy = json.loads((ROOT / "admin-policy.json").read_text())
    policy_digest = AUTH.sha256_bytes(AUTH.canonical_bytes(policy))
    spec = {
        "admin_policy_sha256": policy_digest,
        "artifact_identity": "a" * 64,
        "author_report_sha256": "b" * 64,
        "capsule_identity": "c" * 64,
        "claim_ceiling": "LocalAuthorDevelopmentPerturbationReadout",
        "external_states": {
            "confirmation": "NotAuthorized",
            "independently_verified": "NotRun",
            "stage_0c": "Blocked",
        },
        "release_identity": "d" * 64,
        "required_roles": list(AUTH.ROLES),
        "required_scientific_sections": [
            "assessment_sealing",
            "claim_ceiling",
            "control_strength",
            "corpus_overlap_and_leakage",
            "preregistration_chronology",
            "statistics_and_uncertainty",
            "stopping_and_selection_rules",
        ],
        "review_namespace": AUTH.REVIEW_NAMESPACE,
        "schema_version": 2,
        "source_commit": "e" * 40,
        "source_tree": "f" * 40,
    }
    AUTH.write_canonical(root / "metadata/admin-policy.json", policy)
    AUTH.write_canonical(root / "metadata/gate-spec.json", spec)
    rows = []
    for path in sorted(candidate for candidate in root.rglob("*") if candidate.is_file()):
        rows.append(f"{AUTH.sha256_file(path)}  {path.relative_to(root).as_posix()}")
    manifest = "\n".join(rows) + "\n"
    (root / KIT.MANIFEST_NAME).write_text(manifest)
    identity = AUTH.sha256_bytes(manifest.encode())
    destination = tmp_path / f"{KIT.KIT_ID}-{identity}"
    root.rename(destination)
    assert KIT.verify_kit(destination)["status"] == "V24ReviewAuthorizationKitValid"
    (destination / "extra.txt").write_text("extra\n")
    with pytest.raises(ValueError, match="census mismatch"):
        KIT.verify_kit(destination)
