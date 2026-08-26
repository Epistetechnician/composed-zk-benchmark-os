import contextlib
import copy
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from experiments.self_model_benchmark.capture_admission import admit
from experiments.self_model_benchmark.capture_handoff import build_handoff
from experiments.self_model_benchmark.capture_quarantine import QuarantineError, build_quarantine_manifest
from experiments.self_model_benchmark.capture_review import (
    CLAIM_CEILING,
    DECISION_OPTIONS,
    ReviewPacketError,
    build_review_packet,
    main as review_main,
    validate_review_packet,
)
from experiments.self_model_benchmark.capture_review_decision import (
    DECISION_CLAIM_CEILING,
    ReviewDecisionError,
    main as decision_main,
    record_review_decision,
    validate_review_decision,
)
from experiments.self_model_benchmark.protocol import digest_json
from experiments.self_model_benchmark.repository_change_capture import write_jsonl
from experiments.self_model_benchmark.tests.test_capture_admission import _receipt
from experiments.self_model_benchmark.tests.test_capture_handoff import _request
from experiments.self_model_benchmark.tests.test_repository_change_capture import (
    _capture_records,
    _live_capture_records,
)


def _packet_for(workflow_id: str) -> dict:
    request = _request()
    request["workflow_id"] = workflow_id
    request["model_digest"] = "b" * 64
    request["runtime_digest"] = "c" * 64
    request["checker_digest"] = "d" * 64
    request["request_digest"] = digest_json({key: value for key, value in request.items() if key != "request_digest"})
    return build_handoff(request)


def _admission(root: Path, live: bool = True) -> dict:
    capture_path = root / "capture.jsonl"
    write_jsonl(capture_path, _live_capture_records() if live else _capture_records("contract_smoke_fixture"))
    packet = _packet_for("repository-change-self-model-test")
    return admit(packet, capture_path, _receipt(packet, capture_path))


def _review_packet(root: Path) -> dict:
    return build_review_packet(build_quarantine_manifest(_admission(root)))


class CaptureReviewTests(unittest.TestCase):
    def test_live_admission_builds_pending_non_promoting_packet(self):
        with tempfile.TemporaryDirectory() as directory:
            report = _admission(Path(directory))
            packet = build_review_packet(build_quarantine_manifest(report))
        validate_review_packet(packet)
        self.assertEqual(packet["review_status"], "pending_manual_review")
        self.assertEqual(packet["decision_options"], DECISION_OPTIONS)
        self.assertTrue(all(packet["checklist"].values()))
        self.assertFalse(packet["accepted"])
        self.assertFalse(packet["conversion_eligible"])
        self.assertFalse(packet["scientific_evidence"])
        self.assertEqual(packet["claim_ceiling"], CLAIM_CEILING)

    def test_rejected_smoke_admission_cannot_enter_review(self):
        with tempfile.TemporaryDirectory() as directory:
            report = _admission(Path(directory), live=False)
            quarantine = build_quarantine_manifest(report)
            with self.assertRaisesRegex(ReviewPacketError, "eligible_for_manual_review"):
                build_review_packet(quarantine)

    def test_report_digest_tampering_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            report = _admission(Path(directory))
            report["report_digest"] = "0" * 64
            with self.assertRaisesRegex(QuarantineError, "admission report invalid: admission report digest mismatch"):
                build_review_packet(build_quarantine_manifest(report))

    def test_packet_self_promotion_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            packet = _review_packet(Path(directory))
            packet["accepted"] = True
            with self.assertRaisesRegex(ReviewPacketError, "accepted must be false"):
                validate_review_packet(packet)

    def test_decision_records_only_digests_and_never_promotes(self):
        with tempfile.TemporaryDirectory() as directory:
            packet = _review_packet(Path(directory))
            decision = record_review_decision(
                packet,
                "not_evidence",
                "operator-reference-42",
                "Reviewed the frozen checklist and retained no raw material.",
            )
        validate_review_decision(decision)
        self.assertEqual(decision["review_status"], "reviewed")
        self.assertEqual(decision["claim_ceiling"], DECISION_CLAIM_CEILING)
        self.assertFalse(decision["accepted"])
        self.assertFalse(decision["conversion_eligible"])
        self.assertFalse(decision["scientific_evidence"])
        self.assertFalse(decision["review_notes_retained"])
        self.assertNotIn("operator-reference-42", json.dumps(decision))
        self.assertNotIn("Reviewed the frozen", json.dumps(decision))

    def test_decision_options_are_explicit_and_invalid_options_fail(self):
        with tempfile.TemporaryDirectory() as directory:
            packet = _review_packet(Path(directory))
            self.assertEqual(
                record_review_decision(packet, "request_recapture", "operator-reference-42", "Re-run required.")["decision"],
                "request_recapture",
            )
            with self.assertRaisesRegex(ReviewDecisionError, "invalid review decision"):
                record_review_decision(packet, "keep_candidate", "operator-reference-42", "No.")

    def test_decision_tampering_and_missing_notes_fail_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            packet = _review_packet(Path(directory))
            decision = record_review_decision(packet, "reject", "operator-reference-42", "Rejected.")
            tampered = copy.deepcopy(decision)
            tampered["accepted"] = True
            with self.assertRaisesRegex(ReviewDecisionError, "accepted must be false"):
                validate_review_decision(tampered)
            with self.assertRaisesRegex(ReviewDecisionError, "review_notes is required"):
                record_review_decision(packet, "reject", "operator-reference-42", " ")

    def test_cli_round_trip_emits_validated_packet_and_decision(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            quarantine = build_quarantine_manifest(_admission(root))
            quarantine_path = root / "quarantine.json"
            packet_path = root / "review-packet.json"
            decision_path = root / "review-decision.json"
            quarantine_path.write_text(json.dumps(quarantine, sort_keys=True), encoding="utf-8")
            with patch.object(
                sys,
                "argv",
                ["capture-review", "--quarantine-manifest", str(quarantine_path), "--output", str(packet_path)],
            ), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(review_main(), 0)
            with patch.object(
                sys,
                "argv",
                [
                    "capture-review-decision",
                    "--review-packet",
                    str(packet_path),
                    "--decision",
                    "not_evidence",
                    "--reviewer-ref",
                    "operator-reference-42",
                    "--notes",
                    "Checklist reviewed.",
                    "--output",
                    str(decision_path),
                ],
            ), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(decision_main(), 0)
            packet = json.loads(packet_path.read_text(encoding="utf-8"))
            decision = json.loads(decision_path.read_text(encoding="utf-8"))
        validate_review_packet(packet)
        validate_review_decision(decision)
        self.assertEqual(decision["source_packet_digest"], packet["packet_digest"])


if __name__ == "__main__":
    unittest.main()
