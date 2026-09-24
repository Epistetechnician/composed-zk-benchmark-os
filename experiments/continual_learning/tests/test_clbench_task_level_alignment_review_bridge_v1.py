"""Hermetic tests for the external CL-Bench review bridge.

State slice: ``aligned-holistic-continual-learning-interpretability-monorepo-v1``.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from experiments.continual_learning import clbench_task_level_alignment_review_bridge_v1 as bridge


def test_binding_is_portable_and_non_authorizing() -> None:
    binding = bridge.review_binding()
    assert binding["protocol_id"] == bridge.PROTOCOL_ID
    assert binding["state_slice"] == bridge.STATE_SLICE
    assert binding["mailbox_packet_digest"] == f"sha256:{binding['protocol_digest']}"
    assert binding["manifest_sha256"]
    assert binding["packet_sha256"]
    assert binding["review_bundle_sha256"]
    assert binding["required_checks"] == list(bridge.REQUIRED_CHECKS)
    assert binding["execution_authorized"] is False
    assert not hasattr(bridge, "sign_receipt")


def test_receipt_schema_is_checked_before_external_registry_access(tmp_path: Path) -> None:
    receipt = tmp_path / "receipt.json"
    receipt.write_text(json.dumps({"decision": "ACCEPT"}), encoding="utf-8")
    with pytest.raises(bridge.ReviewBridgeError, match="review receipt schema"):
        bridge.verify_receipt(receipt, tmp_path / "registry.json", tmp_path / "owner.key")


def test_registry_and_receipt_paths_must_be_external(tmp_path: Path) -> None:
    with pytest.raises(bridge.ReviewBridgeError, match="must be absolute"):
        bridge.verify_receipt(Path("receipt.json"), tmp_path / "registry.json", tmp_path / "owner.key")
