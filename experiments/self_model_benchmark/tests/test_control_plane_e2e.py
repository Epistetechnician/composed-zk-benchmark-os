import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from experiments.self_model_benchmark.capture_admission import AdmissionError, admit, validate_report
from experiments.self_model_benchmark.capture_handoff import HandoffError, build_handoff, validate_packet
from experiments.self_model_benchmark.capture_quarantine import (
    QuarantineError,
    build_quarantine_manifest,
    validate_quarantine_manifest,
)
from experiments.self_model_benchmark.capture_review import ReviewPacketError, build_review_packet, validate_review_packet
from experiments.self_model_benchmark.capture_review_decision import (
    ReviewDecisionError,
    record_review_decision,
    validate_review_decision,
)
from experiments.self_model_benchmark.protocol import digest_json
from experiments.self_model_benchmark.repository_change_capture import CaptureError, convert, write_jsonl
from experiments.self_model_benchmark.tests.test_capture_admission import _receipt
from experiments.self_model_benchmark.tests.test_capture_handoff import _request
from experiments.self_model_benchmark.tests.test_repository_change_capture import _live_capture_records


def _handoff_request() -> dict:
    request = _request()
    request["workflow_id"] = "repository-change-self-model-test"
    request["model_digest"] = "b" * 64
    request["runtime_digest"] = "c" * 64
    request["checker_digest"] = "d" * 64
    request["request_digest"] = digest_json({key: value for key, value in request.items() if key != "request_digest"})
    return request


def _run_cli(module: str, *arguments: Path | str) -> subprocess.CompletedProcess[str]:
    repository_root = Path(__file__).resolve().parents[3]
    environment = dict(os.environ)
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    return subprocess.run(
        [sys.executable, "-m", module, *(str(argument) for argument in arguments)],
        cwd=repository_root,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )


def _build_live_chain(root: Path) -> dict[str, dict]:
    capture_path = root / "capture.jsonl"
    write_jsonl(capture_path, _live_capture_records())
    handoff = build_handoff(_handoff_request())
    receipt = _receipt(handoff, capture_path)
    admission = admit(handoff, capture_path, receipt)
    quarantine = build_quarantine_manifest(admission)
    review_packet = build_review_packet(quarantine)
    decision = record_review_decision(
        review_packet,
        "not_evidence",
        "operator-reference-e2e",
        "E2E contract review; retain no raw material.",
    )
    return {
        "handoff": handoff,
        "admission": admission,
        "quarantine": quarantine,
        "review_packet": review_packet,
        "decision": decision,
    }


class ControlPlaneE2ETests(unittest.TestCase):
    def test_live_capture_chain_reaches_reviewed_but_never_promotes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            capture_path = root / "capture.jsonl"
            chain = _build_live_chain(root)
            handoff = chain["handoff"]
            admission = chain["admission"]
            quarantine = chain["quarantine"]
            review_packet = chain["review_packet"]
            decision = chain["decision"]
            with self.assertRaisesRegex(CaptureError, "separately authorized release"):
                convert(capture_path)

        validate_report(admission)
        validate_quarantine_manifest(quarantine)
        validate_review_packet(review_packet)
        validate_review_decision(decision)
        self.assertEqual(handoff["packet_status"], "ready_for_external_runner")
        self.assertEqual(admission["admission_status"], "eligible_for_manual_review")
        self.assertEqual(quarantine["quarantine_status"], "pending_manual_review")
        self.assertEqual(review_packet["review_status"], "pending_manual_review")
        self.assertEqual(decision["review_status"], "reviewed")
        self.assertEqual(decision["decision"], "not_evidence")
        self.assertEqual(decision["quarantine_manifest_digest"], quarantine["quarantine_digest"])
        self.assertEqual(decision["source_packet_digest"], review_packet["packet_digest"])
        for artifact in (quarantine, review_packet, decision):
            self.assertEqual(artifact["release_status"], "held")
            self.assertFalse(artifact["accepted"])
            self.assertFalse(artifact["conversion_eligible"])
            self.assertFalse(artifact["scientific_evidence"])
            self.assertFalse(artifact["authority_granted"])
            self.assertFalse(artifact["network_access"])

    def test_cli_chain_round_trips_and_keeps_live_conversion_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            capture_path = root / "capture.jsonl"
            request_path = root / "handoff-request.json"
            handoff_path = root / "handoff.json"
            receipt_path = root / "receipt.json"
            admission_path = root / "admission.json"
            quarantine_path = root / "quarantine.json"
            review_path = root / "review.json"
            decision_path = root / "decision.json"
            converted_path = root / "converted-input.jsonl"
            write_jsonl(capture_path, _live_capture_records())
            request_path.write_text(json.dumps(_handoff_request(), sort_keys=True) + "\n", encoding="utf-8")

            command = _run_cli(
                "experiments.self_model_benchmark.capture_handoff",
                "--input",
                request_path,
                "--output",
                handoff_path,
            )
            self.assertEqual(command.returncode, 0, command.stderr)
            handoff = json.loads(handoff_path.read_text(encoding="utf-8"))
            receipt_path.write_text(json.dumps(_receipt(handoff, capture_path), sort_keys=True) + "\n", encoding="utf-8")

            command = _run_cli(
                "experiments.self_model_benchmark.capture_admission",
                "--handoff",
                handoff_path,
                "--capture",
                capture_path,
                "--receipt",
                receipt_path,
                "--output",
                admission_path,
            )
            self.assertEqual(command.returncode, 0, command.stderr)
            command = _run_cli(
                "experiments.self_model_benchmark.capture_quarantine",
                "--admission-report",
                admission_path,
                "--output",
                quarantine_path,
            )
            self.assertEqual(command.returncode, 0, command.stderr)
            command = _run_cli(
                "experiments.self_model_benchmark.capture_review",
                "--quarantine-manifest",
                quarantine_path,
                "--output",
                review_path,
            )
            self.assertEqual(command.returncode, 0, command.stderr)
            command = _run_cli(
                "experiments.self_model_benchmark.capture_review_decision",
                "--review-packet",
                review_path,
                "--decision",
                "not_evidence",
                "--reviewer-ref",
                "operator-reference-cli-e2e",
                "--notes",
                "CLI composition contract review; retain no raw material.",
                "--output",
                decision_path,
            )
            self.assertEqual(command.returncode, 0, command.stderr)

            decision = json.loads(decision_path.read_text(encoding="utf-8"))
            self.assertEqual(decision["review_status"], "reviewed")
            self.assertEqual(decision["decision"], "not_evidence")
            self.assertEqual(decision["release_status"], "held")
            self.assertFalse(decision["accepted"])
            self.assertFalse(decision["conversion_eligible"])
            self.assertFalse(decision["scientific_evidence"])
            self.assertFalse(decision["authority_granted"])
            self.assertFalse(decision["network_access"])

            command = _run_cli(
                "experiments.self_model_benchmark.repository_change_capture",
                "--input",
                capture_path,
                "--output",
                converted_path,
            )
            self.assertEqual(command.returncode, 2)
            self.assertIn("separately authorized release", command.stderr)
            self.assertFalse(converted_path.exists())

    def test_semantic_tamper_matrix_fails_closed_after_digest_rewrite(self):
        with tempfile.TemporaryDirectory() as directory:
            chain = _build_live_chain(Path(directory))

        tamper_cases = (
            (
                "handoff authorization",
                chain["handoff"],
                "operator_authorization_status",
                "authorized",
                "packet_digest",
                validate_packet,
                HandoffError,
            ),
            (
                "admission status",
                chain["admission"],
                "admission_status",
                "accepted",
                "report_digest",
                validate_report,
                AdmissionError,
            ),
            (
                "quarantine release",
                chain["quarantine"],
                "release_status",
                "released",
                "quarantine_digest",
                validate_quarantine_manifest,
                QuarantineError,
            ),
            (
                "review conversion",
                chain["review_packet"],
                "conversion_eligible",
                True,
                "packet_digest",
                validate_review_packet,
                ReviewPacketError,
            ),
            (
                "review acceptance",
                chain["decision"],
                "accepted",
                True,
                "decision_digest",
                validate_review_decision,
                ReviewDecisionError,
            ),
        )

        for label, artifact, field, value, digest_field, validator, error_type in tamper_cases:
            with self.subTest(label=label):
                tampered = dict(artifact)
                tampered[field] = value
                tampered[digest_field] = digest_json(
                    {key: item for key, item in tampered.items() if key != digest_field}
                )
                with self.assertRaises(error_type):
                    validator(tampered)

if __name__ == "__main__":
    unittest.main()
