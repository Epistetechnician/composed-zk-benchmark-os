"""Hermetic contract tests for the CL-Bench task-level alignment design.

State slice: ``aligned-holistic-continual-learning-interpretability-monorepo-v1``.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from experiments.continual_learning import clbench_task_level_alignment_v1 as protocol


def test_manifest_is_valid_and_execution_remains_closed() -> None:
    result = protocol.validate_manifest_file()
    assert result["valid"] is True
    assert result["status"] == protocol.STATUS
    assert result["execution_authorized"] is False
    assert result["review_transport_protocol"] == protocol.REVIEW_TRANSPORT_PROTOCOL
    assert result["mailbox_packet_digest"] == f"sha256:{result['protocol_digest']}"

    manifest = protocol.load_json(protocol.MANIFEST_PATH)
    gate = protocol.execution_gate(manifest)
    assert gate["allowed"] is False
    assert "independent_packet_bound_accept_missing" in gate["reasons"]
    assert "explicit_execution_authorization_missing" in gate["reasons"]


def test_protocol_contains_requested_controls_and_exact_task_roster() -> None:
    manifest = protocol.load_json(protocol.MANIFEST_PATH)
    assert tuple(item["id"] for item in manifest["arms"]) == protocol.ARMS
    assert tuple(manifest["benchmark"]["task_ids"]) == protocol.TASK_IDS
    assert manifest["splits"]["names"] == list(protocol.SPLITS)
    assert manifest["splits"]["assessment_is_unseen_at_lock"] is True
    assert manifest["prediction_lock"]["assessment_labels_available_at_lock"] is False
    assert manifest["replication"]["independent_recomputation_required"] is True


def test_tampered_review_packet_digest_is_rejected() -> None:
    manifest = protocol.load_json(protocol.MANIFEST_PATH)
    manifest["review_packet_sha256"] = "0" * 64
    with pytest.raises(protocol.ProtocolError, match="review packet digest"):
        protocol.validate_manifest(manifest)


def test_execution_gate_rejects_any_attempt_to_open_authority() -> None:
    manifest = protocol.load_json(protocol.MANIFEST_PATH)
    tampered = json.loads(json.dumps(manifest))
    tampered["execution_gates"]["model_execution_authorized"] = True
    with pytest.raises(protocol.ProtocolError, match="model_execution_authorized"):
        protocol.execution_gate(tampered)


def test_custody_root_must_be_external_and_not_repo_relative() -> None:
    manifest = protocol.load_json(protocol.MANIFEST_PATH)
    tampered = json.loads(json.dumps(manifest))
    tampered["custody"]["raw_trace_root"] = str(Path.cwd() / "raw")
    with pytest.raises(protocol.ProtocolError, match="outside the repository"):
        protocol.validate_manifest(tampered)


def test_life_is_explicitly_excluded_from_update_arms() -> None:
    manifest = protocol.load_json(protocol.MANIFEST_PATH)
    exclusion = manifest["excluded_benchmark"]
    assert exclusion["name"] == "CL-bench Life"
    assert "parameter_updates" in exclusion["reason"]
    assert exclusion["future_use"] == "separate_inference_only_protocol_after_license_review"
