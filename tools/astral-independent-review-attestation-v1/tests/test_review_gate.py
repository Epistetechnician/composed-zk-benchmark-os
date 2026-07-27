from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


TOOL_ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(TOOL_ROOT))
import review_gate as GATE  # noqa: E402


SPEC = json.loads((TOOL_ROOT / "gate-spec.json").read_text())
ISSUED = "2026-07-27T18:00:00Z"
REVIEWED = "2026-07-28T18:00:00Z"
EXPIRES = "2026-08-03T18:00:00Z"


class SignedReviewFixture:
    def __init__(self, root: Path):
        self.root = root
        self.keys = root / "keys"
        self.requests = root / "requests"
        self.decisions = root / "decisions"
        self.evidence = root / "evidence"
        for directory in (self.keys, self.requests, self.decisions, self.evidence):
            directory.mkdir(parents=True)
        self.reviewers = []
        for index, role in enumerate(SPEC["required_roles"], start=1):
            key = self.keys / f"reviewer-{index}"
            subprocess.run(
                [
                    "ssh-keygen",
                    "-q",
                    "-t",
                    "ed25519",
                    "-N",
                    "",
                    "-C",
                    "",
                    "-f",
                    str(key),
                ],
                check=True,
            )
            public_key = " ".join(key.with_suffix(".pub").read_text().split()[:2])
            self.reviewers.append(
                {
                    "affiliation": f"Independent Lab {index}",
                    "independence_disclosure": "No implementation role or author control.",
                    "public_key": public_key,
                    "public_key_fingerprint": GATE.key_fingerprint(public_key),
                    "reviewer_name": f"Protocol Reviewer {index}",
                    "role": role,
                    "signer_identity": f"protocol-reviewer-{index}@example.test",
                }
            )
        self.registry = {
            "coordinator": "Protocol Test Coordinator",
            "purpose": "protocol_test",
            "registered_at": ISSUED,
            "reviewers": self.reviewers,
            "schema_version": 1,
        }
        self.registry_path = root / "reviewer-registry.json"
        self.registry_sha256 = GATE.write_canonical(self.registry_path, self.registry)
        self.request_hashes = {}
        for index, reviewer in enumerate(self.reviewers, start=1):
            request = GATE.build_request(
                SPEC,
                reviewer,
                f"{index:064x}",
                ISSUED,
                EXPIRES,
            )
            path = self.requests / f"{reviewer['role']}.request.json"
            self.request_hashes[reviewer["role"]] = GATE.write_canonical(path, request)
        self._write_evidence()
        self._write_decisions()

    def _write_json_evidence(self, relative: str, value: object) -> dict[str, str]:
        path = self.evidence / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
        return {
            "label": path.stem.replace("-", "_"),
            "path": relative,
            "sha256": GATE.sha256_file(path),
        }

    def _write_evidence(self) -> None:
        capsule_run = {
            "capsule_identity": SPEC["capsule_identity"],
            "claim_ceiling": SPEC["claim_ceiling"],
            "independence_status": "Unasserted",
            "release_commit": SPEC["release_commit"],
            "release_package_identity": SPEC["release_package_identity"],
            "release_tree": SPEC["release_tree"],
            "status": "CapsuleReplayPassed",
        }
        reviewer_report = {
            "claim_ceiling": SPEC["claim_ceiling"],
            "external_gates": GATE.EXPECTED_EXTERNAL_GATES,
            "git_tree": SPEC["release_tree"],
            "package": {"package_identity": SPEC["release_package_identity"]},
            "status": "local_immutable_validation_passed",
        }
        audit = {
            "capsule_identity": SPEC["capsule_identity"],
            "schema_version": 1,
            "sections": {
                section: {"notes": f"Protocol test audit for {section}.", "status": "Pass"}
                for section in SPEC["required_scientific_sections"]
            },
        }
        capsule_item = self._write_json_evidence("artifact/capsule-run.json", capsule_run)
        capsule_item["label"] = "capsule_run"
        report_item = self._write_json_evidence(
            "artifact/reviewer-report.json", reviewer_report
        )
        report_item["label"] = "reviewer_report"
        audit_item = self._write_json_evidence("science/scientific-audit.json", audit)
        audit_item["label"] = "scientific_audit"
        self.evidence_by_role = {
            "artifact_reproducibility": [capsule_item, report_item],
            "scientific_validity": [audit_item],
        }

    def _write_decisions(self) -> None:
        for index, reviewer in enumerate(self.reviewers, start=1):
            role = reviewer["role"]
            request, request_sha256 = GATE.load_canonical(
                self.requests / f"{role}.request.json"
            )
            decision = GATE.decision_template(request, request_sha256)
            decision.update(
                {
                    "author_assistance": "None during protocol rehearsal.",
                    "conflict_disclosure": "No conflict for protocol test.",
                    "evidence": self.evidence_by_role[role],
                    "independence_declaration": {
                        "independent_of_v1_v23_implementation": True,
                        "not_author_controlled": True,
                    },
                    "result": "Pass",
                    "reviewed_at": REVIEWED,
                }
            )
            decision_path = self.decisions / f"{role}.decision.json"
            GATE.write_canonical(decision_path, decision)
            subprocess.run(
                [
                    "ssh-keygen",
                    "-Y",
                    "sign",
                    "-f",
                    str(self.keys / f"reviewer-{index}"),
                    "-n",
                    SPEC["namespace"],
                    str(decision_path),
                ],
                check=True,
                capture_output=True,
                text=True,
            )

    def verify(self):
        return GATE.verify_gate(
            SPEC,
            self.registry_path,
            self.registry_sha256,
            self.requests,
            self.decisions,
            self.evidence,
        )


class ReviewGateTests(unittest.TestCase):
    def test_prepare_and_verify_cli_end_to_end(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            fixture = SignedReviewFixture(root / "fixture")
            prepared = root / "prepared"
            prepare = subprocess.run(
                [
                    sys.executable,
                    str(TOOL_ROOT / "prepare_review.py"),
                    "--registry",
                    str(fixture.registry_path),
                    "--expected-registry-sha256",
                    fixture.registry_sha256,
                    "--issued-at",
                    ISSUED,
                    "--expires-at",
                    EXPIRES,
                    "--output",
                    str(prepared),
                    "--nonce",
                    f"artifact_reproducibility={1:064x}",
                    "--nonce",
                    f"scientific_validity={2:064x}",
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            prepared_state = json.loads(prepare.stdout)
            self.assertTrue((prepared / "REQUEST-MANIFEST.sha256").is_file())
            self.assertEqual(
                fixture.request_hashes, prepared_state["request_sha256"]
            )

            report = root / "gate-report.json"
            verify = subprocess.run(
                [
                    sys.executable,
                    str(TOOL_ROOT / "verify_review_gate.py"),
                    "--registry",
                    str(fixture.registry_path),
                    "--expected-registry-sha256",
                    fixture.registry_sha256,
                    "--requests",
                    str(fixture.requests),
                    "--decisions",
                    str(fixture.decisions),
                    "--evidence-root",
                    str(fixture.evidence),
                    "--report",
                    str(report),
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            verified_state = json.loads(verify.stdout)
            self.assertEqual(
                "SyntheticSignedReviewProtocolPassed", verified_state["status"]
            )
            self.assertTrue(report.with_suffix(".json.sha256").is_file())

    def test_two_distinct_signed_reviews_pass_only_as_synthetic_protocol(self):
        with tempfile.TemporaryDirectory() as raw:
            fixture = SignedReviewFixture(Path(raw))
            report = fixture.verify()
            self.assertEqual("SyntheticSignedReviewProtocolPassed", report["status"])
            self.assertEqual("DeclaredNotVerified", report["independence_status"])
            self.assertEqual(
                {
                    "artifact_reproducibility": "Pass",
                    "scientific_validity": "Pass",
                },
                report["results"],
            )

    def test_external_registry_can_only_reach_quorum_candidate(self):
        with tempfile.TemporaryDirectory() as raw:
            fixture = SignedReviewFixture(Path(raw))
            fixture.registry["purpose"] = "external_review"
            fixture.registry_sha256 = GATE.write_canonical(
                fixture.registry_path, fixture.registry
            )
            report = fixture.verify()
            self.assertEqual("SignedReviewQuorumCandidate", report["status"])
            self.assertEqual("DeclaredNotVerified", report["independence_status"])
            self.assertNotIn("Accepted", report["status"])

    def test_tampered_signed_decision_fails_signature_verification(self):
        with tempfile.TemporaryDirectory() as raw:
            fixture = SignedReviewFixture(Path(raw))
            path = fixture.decisions / "artifact_reproducibility.decision.json"
            decision, _ = GATE.load_canonical(path)
            decision["author_assistance"] = "Tampered after signature."
            GATE.write_canonical(path, decision)
            with self.assertRaisesRegex(ValueError, "signature verification failed"):
                fixture.verify()

    def test_registry_rejects_same_reviewer_for_both_roles(self):
        with tempfile.TemporaryDirectory() as raw:
            fixture = SignedReviewFixture(Path(raw))
            registry = dict(fixture.registry)
            registry["reviewers"] = [dict(item) for item in fixture.reviewers]
            for field in (
                "public_key",
                "public_key_fingerprint",
                "reviewer_name",
                "signer_identity",
            ):
                registry["reviewers"][1][field] = registry["reviewers"][0][field]
            with self.assertRaisesRegex(ValueError, "not distinct"):
                GATE.validate_registry(registry, SPEC)

    def test_open_material_finding_blocks_pass(self):
        with tempfile.TemporaryDirectory() as raw:
            fixture = SignedReviewFixture(Path(raw))
            path = fixture.decisions / "artifact_reproducibility.decision.json"
            decision, _ = GATE.load_canonical(path)
            decision["result"] = "PassWithFindings"
            decision["findings"] = [
                {
                    "code": "TEST-MATERIAL",
                    "severity": "Material",
                    "status": "Open",
                    "summary": "Synthetic material finding.",
                }
            ]
            GATE.write_canonical(path, decision)
            with self.assertRaisesRegex(ValueError, "material finding blocks pass"):
                fixture.verify()


if __name__ == "__main__":
    unittest.main()
