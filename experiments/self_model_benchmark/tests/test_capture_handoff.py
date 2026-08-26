import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from experiments.self_model_benchmark.capture_handoff import (
    CLAIM_CEILING,
    HandoffError,
    build_handoff,
    main,
    validate_packet,
)
from experiments.self_model_benchmark.protocol import MIN_LIVE_SPLIT_TRAJECTORIES, VARIANTS, digest_json
from experiments.self_model_benchmark.repository_change_capture import REPOSITORY_CHECK_IDS


def _request() -> dict:
    request = {
        "record_type": "self_model_capture_handoff_request",
        "schema_version": "verified-self-model-capture-handoff-request-v1",
        "state_slice": "verified-self-model-benchmark-capture-handoff-v1",
        "workflow_id": "self-model-repository-change-v1",
        "source_type": "live_workflow_capture",
        "repository_revision": "e298c9b0" * 5,
        "task_spec_digest": "a" * 64,
        "corpus_plan_digest": "b" * 64,
        "runner_identity_digest": "c" * 64,
        "validator_identity_digest": "d" * 64,
        "model_digest": "e" * 64,
        "runtime_digest": "f" * 64,
        "checker_digest": "0" * 64,
        "fixed_budget": True,
        "budget": {"max_latency_ms": 120000, "max_compute_units": 24000, "max_tool_calls": 12, "max_attempts": 2},
        "trajectory_count": 60,
        "task_family_count": 5,
        "split_trajectory_counts": dict(MIN_LIVE_SPLIT_TRAJECTORIES),
        "variants": list(VARIANTS),
        "required_check_ids": list(REPOSITORY_CHECK_IDS),
        "prediction_lock_required": True,
        "external_outcomes_required": True,
        "validator_custody_required": True,
        "operator_authorization_status": "not_authorized",
        "execution_authorized": False,
        "authority_granted": False,
        "network_access": False,
        "raw_reasoning_retained": False,
        "expected_capture_schema_version": "verified-self-model-repository-capture-v1",
        "expected_capture_state_slice": "verified-self-model-benchmark-repository-capture-v1",
        "expected_record_types": ["self_model_capture_manifest", "self_model_repository_observation"],
        "non_claims": [
            "not_agent_execution",
            "not_model_execution",
            "not_validator_custody",
            "not_benchmark_evidence",
            "not_authority_grant",
        ],
    }
    request["request_digest"] = digest_json(request)
    return request


class CaptureHandoffTests(unittest.TestCase):
    def test_valid_request_builds_plan_only_packet(self):
        packet = build_handoff(_request())
        validate_packet(packet)
        self.assertEqual(packet["packet_status"], "ready_for_external_runner")
        self.assertEqual(packet["claim_ceiling"], CLAIM_CEILING)
        self.assertEqual(packet["capture_status"], "not_captured")
        self.assertFalse(packet["execution_authorized"])
        self.assertFalse(packet["scientific_evidence"])

    def test_request_digest_drift_fails_closed(self):
        request = _request()
        request["corpus_plan_digest"] = "1" * 64
        with self.assertRaisesRegex(HandoffError, "request digest mismatch"):
            build_handoff(request)

    def test_runner_and_validator_must_be_separate(self):
        request = _request()
        request["validator_identity_digest"] = request["runner_identity_digest"]
        request["request_digest"] = digest_json({key: value for key, value in request.items() if key != "request_digest"})
        with self.assertRaisesRegex(HandoffError, "identities must differ"):
            build_handoff(request)

    def test_variant_and_check_drift_fail_closed(self):
        request = _request()
        request["variants"] = list(reversed(VARIANTS))
        request["request_digest"] = digest_json({key: value for key, value in request.items() if key != "request_digest"})
        with self.assertRaisesRegex(HandoffError, "variants"):
            build_handoff(request)
        request = _request()
        request["required_check_ids"] = list(reversed(REPOSITORY_CHECK_IDS))
        request["request_digest"] = digest_json({key: value for key, value in request.items() if key != "request_digest"})
        with self.assertRaisesRegex(HandoffError, "checks"):
            build_handoff(request)

    def test_authority_execution_network_or_capture_flags_fail_closed(self):
        for field, value in (
            ("execution_authorized", True),
            ("authority_granted", True),
            ("network_access", True),
            ("raw_reasoning_retained", True),
        ):
            request = _request()
            request[field] = value
            request["request_digest"] = digest_json({key: item for key, item in request.items() if key != "request_digest"})
            with self.subTest(field=field), self.assertRaisesRegex(HandoffError, field):
                build_handoff(request)

    def test_packet_cannot_be_relabelled_as_captured(self):
        packet = build_handoff(_request())
        packet["capture_status"] = "captured"
        packet["packet_digest"] = digest_json({key: value for key, value in packet.items() if key != "packet_digest"})
        with self.assertRaisesRegex(HandoffError, "cannot contain a capture"):
            validate_packet(packet)

    def test_cli_emits_digest_validated_packet(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            request_path = root / "request.json"
            packet_path = root / "packet.json"
            request_path.write_text(json.dumps(_request(), sort_keys=True), encoding="utf-8")
            with patch.object(
                sys,
                "argv",
                ["capture-handoff", "--input", str(request_path), "--output", str(packet_path)],
            ), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(main(), 0)
            packet = json.loads(packet_path.read_text(encoding="utf-8"))
        validate_packet(packet)
        self.assertEqual(packet["packet_status"], "ready_for_external_runner")


if __name__ == "__main__":
    unittest.main()
