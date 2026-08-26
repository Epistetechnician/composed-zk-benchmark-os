import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from experiments.self_model_benchmark.capture_admission import (
    CLAIM_CEILING,
    AdmissionError,
    admit,
    main,
    validate_report,
    validate_receipt,
)
from experiments.self_model_benchmark.capture_handoff import build_handoff
from experiments.self_model_benchmark.capture_preflight import preflight_capture
from experiments.self_model_benchmark.protocol import digest_json
from experiments.self_model_benchmark.repository_change_capture import load_capture, write_jsonl
from experiments.self_model_benchmark.tests.test_capture_handoff import _request
from experiments.self_model_benchmark.tests.test_repository_change_capture import (
    _capture_records,
    _live_capture_records,
)


def _packet_for(workflow_id: str):
    request = _request()
    request["workflow_id"] = workflow_id
    request["model_digest"] = "b" * 64
    request["runtime_digest"] = "c" * 64
    request["checker_digest"] = "d" * 64
    request["request_digest"] = digest_json({key: value for key, value in request.items() if key != "request_digest"})
    return build_handoff(request)


def _receipt(packet: dict, capture_path: Path) -> dict:
    manifest, _ = load_capture(capture_path)
    preflight = preflight_capture(capture_path)
    receipt = {
        "record_type": "self_model_capture_validator_receipt",
        "schema_version": "verified-self-model-capture-validator-receipt-v1",
        "state_slice": "verified-self-model-benchmark-capture-admission-v1",
        "workflow_id": manifest["workflow_id"],
        "capture_source_type": manifest["source_type"],
        "handoff_packet_digest": packet["packet_digest"],
        "capture_manifest_digest": digest_json(manifest),
        "preflight_report_digest": preflight["report_digest"],
        "validator_report_digest": manifest["validator_report_digest"],
        "task_spec_digest": packet["task_spec_digest"],
        "corpus_plan_digest": packet["corpus_plan_digest"],
        "runner_identity_digest": packet["runner_identity_digest"],
        "validator_identity_digest": packet["validator_identity_digest"],
        "model_digest": manifest["model_digest"],
        "runtime_digest": manifest["runtime_digest"],
        "checker_digest": manifest["checker_digest"],
        "operator_authorization_reference_digest": "1" * 64,
        "capture_received": True,
        "prediction_lock_verified": True,
        "external_outcomes_verified": True,
        "validator_custody": True,
        "execution_recorded": True,
        "operator_authorization_status": "reference_supplied",
        "raw_reasoning_retained": False,
        "authority_granted": False,
        "network_access": False,
        "non_claims": [
            "not_accepted_evidence",
            "not_scientific_evidence",
            "not_authority_grant",
            "not_independent_custody_proof",
            "not_production_ready",
        ],
    }
    receipt["receipt_digest"] = digest_json(receipt)
    return receipt


class CaptureAdmissionTests(unittest.TestCase):
    def test_live_capture_is_eligible_for_manual_review(self):
        with tempfile.TemporaryDirectory() as directory:
            capture_path = Path(directory) / "capture.jsonl"
            write_jsonl(capture_path, _live_capture_records())
            packet = _packet_for("repository-change-self-model-test")
            report = admit(packet, capture_path, _receipt(packet, capture_path))
        validate_report(report)
        self.assertTrue(report["valid"])
        self.assertEqual(report["admission_status"], "eligible_for_manual_review")
        self.assertEqual(report["claim_ceiling"], CLAIM_CEILING)
        self.assertFalse(report["scientific_evidence"])
        self.assertFalse(report["authority_granted"])

    def test_smoke_capture_is_rejected_by_preflight(self):
        with tempfile.TemporaryDirectory() as directory:
            capture_path = Path(directory) / "capture.jsonl"
            write_jsonl(capture_path, _capture_records("contract_smoke_fixture"))
            packet = _packet_for("repository-change-self-model-test")
            report = admit(packet, capture_path, _receipt(packet, capture_path))
        self.assertFalse(report["valid"])
        self.assertEqual(report["admission_status"], "rejected_preflight")
        self.assertIn("preflight_valid", report["failure_reasons"])

    def test_handoff_digest_binding_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            capture_path = Path(directory) / "capture.jsonl"
            write_jsonl(capture_path, _live_capture_records())
            packet = _packet_for("repository-change-self-model-test")
            receipt = _receipt(packet, capture_path)
            receipt["handoff_packet_digest"] = "2" * 64
            receipt["receipt_digest"] = digest_json({key: value for key, value in receipt.items() if key != "receipt_digest"})
            with self.assertRaisesRegex(AdmissionError, "handoff packet digest"):
                admit(packet, capture_path, receipt)

    def test_capture_manifest_digest_binding_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            capture_path = Path(directory) / "capture.jsonl"
            write_jsonl(capture_path, _live_capture_records())
            packet = _packet_for("repository-change-self-model-test")
            receipt = _receipt(packet, capture_path)
            receipt["capture_manifest_digest"] = "3" * 64
            receipt["receipt_digest"] = digest_json({key: value for key, value in receipt.items() if key != "receipt_digest"})
            with self.assertRaisesRegex(AdmissionError, "capture manifest digest"):
                admit(packet, capture_path, receipt)

    def test_identity_and_safety_drift_fail_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            capture_path = Path(directory) / "capture.jsonl"
            write_jsonl(capture_path, _live_capture_records())
            packet = _packet_for("repository-change-self-model-test")
            receipt = _receipt(packet, capture_path)
            receipt["validator_identity_digest"] = receipt["runner_identity_digest"]
            receipt["receipt_digest"] = digest_json({key: value for key, value in receipt.items() if key != "receipt_digest"})
            with self.assertRaisesRegex(AdmissionError, "identities must differ"):
                admit(packet, capture_path, receipt)
            receipt = _receipt(packet, capture_path)
            receipt["authority_granted"] = True
            receipt["receipt_digest"] = digest_json({key: value for key, value in receipt.items() if key != "receipt_digest"})
            with self.assertRaisesRegex(AdmissionError, "authority_granted"):
                admit(packet, capture_path, receipt)

    def test_receipt_validator_rejects_non_object_cross_record_inputs(self):
        # State slice: verified-self-model-benchmark-capture-admission-v1.
        malformed_values = (None, [], "not-an-object", 1)
        with tempfile.TemporaryDirectory() as directory:
            capture_path = Path(directory) / "capture.jsonl"
            write_jsonl(capture_path, _live_capture_records())
            manifest, _ = load_capture(capture_path)
            packet = _packet_for(manifest["workflow_id"])
            receipt = _receipt(packet, capture_path)
            preflight = preflight_capture(capture_path)
        valid_inputs = {"packet": packet, "manifest": manifest, "preflight_report": preflight}
        expected_messages = {
            "packet": "handoff packet must be an object",
            "manifest": "capture manifest must be an object",
            "preflight_report": "preflight report must be an object",
        }
        for field, message in expected_messages.items():
            for malformed in malformed_values:
                with self.subTest(field=field, value_type=type(malformed).__name__):
                    inputs = dict(valid_inputs)
                    inputs[field] = malformed
                    with self.assertRaisesRegex(AdmissionError, message):
                        validate_receipt(
                            receipt,
                            inputs["packet"],
                            inputs["manifest"],
                            inputs["preflight_report"],
                        )

    def test_cli_emits_validated_manual_review_report(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            capture_path = root / "capture.jsonl"
            handoff_path = root / "handoff.json"
            receipt_path = root / "receipt.json"
            report_path = root / "admission.json"
            write_jsonl(capture_path, _live_capture_records())
            packet = _packet_for("repository-change-self-model-test")
            receipt = _receipt(packet, capture_path)
            handoff_path.write_text(json.dumps(packet, sort_keys=True), encoding="utf-8")
            receipt_path.write_text(json.dumps(receipt, sort_keys=True), encoding="utf-8")
            with patch.object(
                sys,
                "argv",
                [
                    "capture-admission",
                    "--handoff",
                    str(handoff_path),
                    "--capture",
                    str(capture_path),
                    "--receipt",
                    str(receipt_path),
                    "--output",
                    str(report_path),
                ],
            ), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(main(), 0)
            report = json.loads(report_path.read_text(encoding="utf-8"))
        validate_report(report)
        self.assertEqual(report["admission_status"], "eligible_for_manual_review")


if __name__ == "__main__":
    unittest.main()
