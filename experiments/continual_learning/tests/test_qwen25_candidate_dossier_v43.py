from __future__ import annotations

import pytest

from experiments.continual_learning import qwen25_candidate_dossier_v43 as v43
from experiments.continual_learning.validate_qwen25_candidate_dossier_v43 import (
    _validate_signed,
)


def _lane(name: str, count: int, *, eligible: bool = True) -> dict:
    return {
        "name": name,
        "case_count": count,
        "valid": True,
        "campaign_eligible": eligible,
    }


def test_v43_freezes_three_local_lanes_and_fifteen_cases():
    assert v43.STATE_SLICE == "continual-learning-qwen25-candidate-dossier-v43"
    assert v43.CLAIM_CEILING == "LocalDevelopmentCandidateSelectionDossier"
    assert [lane["name"] for lane in v43.LANES] == [
        "fresh_acquisition",
        "canonical_retention",
        "order_replication",
    ]
    assert sum(lane["expected_cases"] for lane in v43.LANES) == 15


def test_v43_selection_requires_every_lane_and_exact_case_total():
    lanes = [
        _lane("fresh_acquisition", 3),
        _lane("canonical_retention", 3),
        _lane("order_replication", 9),
    ]
    assert all(v43.selection_gates(lanes).values())
    lanes[2]["campaign_eligible"] = False
    assert v43.selection_gates(lanes)["order_replication_valid_and_eligible"] is False
    lanes[2]["campaign_eligible"] = True
    lanes[2]["case_count"] = 8
    assert v43.selection_gates(lanes)["expected_case_total_15"] is False


def test_v43_output_guard_refuses_repository_or_existing_root(tmp_path):
    with pytest.raises(ValueError, match="outside the repository"):
        v43._ensure_external_new_root(v43.REPO_ROOT / "forbidden")
    existing = tmp_path / "existing"
    existing.mkdir()
    with pytest.raises(FileExistsError, match="refusing overwrite"):
        v43._ensure_external_new_root(existing)


def test_v43_independent_signature_check_rejects_tamper():
    payload = {"value": 1}
    payload["payload_sha256"] = v43.digest(payload)
    _validate_signed(payload, "payload_sha256", "test payload")
    payload["value"] = 2
    with pytest.raises(ValueError, match="digest mismatch"):
        _validate_signed(payload, "payload_sha256", "test payload")
