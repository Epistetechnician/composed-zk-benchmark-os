import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from experiments.self_model_benchmark.capture_admission import admit
from experiments.self_model_benchmark.capture_handoff import build_handoff
from experiments.self_model_benchmark.capture_quarantine import (
    CLAIM_CEILING,
    QuarantineError,
    build_quarantine_manifest,
    main,
    validate_quarantine_manifest,
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


class CaptureQuarantineTests(unittest.TestCase):
    def test_eligible_admission_becomes_held_pending_quarantine(self):
        with tempfile.TemporaryDirectory() as directory:
            manifest = build_quarantine_manifest(_admission(Path(directory)))
        validate_quarantine_manifest(manifest)
        self.assertEqual(manifest["quarantine_status"], "pending_manual_review")
        self.assertEqual(manifest["release_status"], "held")
        self.assertFalse(manifest["conversion_eligible"])
        self.assertFalse(manifest["accepted"])
        self.assertFalse(manifest["scientific_evidence"])
        self.assertEqual(manifest["claim_ceiling"], CLAIM_CEILING)

    def test_rejected_admission_is_quarantined_without_review_release(self):
        with tempfile.TemporaryDirectory() as directory:
            manifest = build_quarantine_manifest(_admission(Path(directory), live=False))
        validate_quarantine_manifest(manifest)
        self.assertEqual(manifest["quarantine_status"], "rejected_preflight")
        self.assertEqual(manifest["reason"], "preflight_rejected")
        self.assertEqual(manifest["release_status"], "held")

    def test_admission_digest_tampering_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            report = _admission(Path(directory))
            report["report_digest"] = "0" * 64
            with self.assertRaisesRegex(QuarantineError, "admission report invalid"):
                build_quarantine_manifest(report)

    def test_release_or_promotion_tampering_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            manifest = build_quarantine_manifest(_admission(Path(directory)))
            manifest["release_status"] = "released"
            with self.assertRaisesRegex(QuarantineError, "release status must remain held"):
                validate_quarantine_manifest(manifest)
            manifest = build_quarantine_manifest(_admission(Path(directory)))
            manifest["conversion_eligible"] = True
            with self.assertRaisesRegex(QuarantineError, "conversion_eligible must be false"):
                validate_quarantine_manifest(manifest)

    def test_cli_round_trip_emits_held_manifest(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            report_path = root / "admission.json"
            manifest_path = root / "quarantine.json"
            report_path.write_text(json.dumps(_admission(root), sort_keys=True), encoding="utf-8")
            with patch.object(
                sys,
                "argv",
                ["capture-quarantine", "--admission-report", str(report_path), "--output", str(manifest_path)],
            ), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(main(), 0)
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        validate_quarantine_manifest(manifest)
        self.assertEqual(manifest["release_status"], "held")


if __name__ == "__main__":
    unittest.main()
