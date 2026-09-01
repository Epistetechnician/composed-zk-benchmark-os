"""Hermetic tests for the functional-plasticity frontier slice.

State slice: ``continual-learning-functional-plasticity-frontier-v1``.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from experiments.continual_learning import functional_plasticity_frontier_v1 as experiment
from experiments.continual_learning import validate_functional_plasticity_frontier_v1 as validator


def test_contract_check_and_receipt_binding() -> None:
    assert experiment.contract_check() == {
        "contract_check": "PASS",
        "state_slice": experiment.STATE_SLICE,
    }
    assert experiment._validate_review_receipt(experiment.REVIEW_RECEIPT_PATH)


def test_campaign_is_deterministic_and_independently_validated() -> None:
    first = experiment.run_campaign()
    second = experiment.run_campaign()
    assert first == second
    validator.validate_result(json.loads(json.dumps(first)))
    assert first["case_group_count"] == 32
    assert first["case_count"] == 96
    assert first["execution_authorized"] is False
    assert first["base_state_sha256"] == experiment.BASE_STATE_SHA256


def test_projection_removes_protected_function_component() -> None:
    protected = experiment._shards(experiment.REPLICATE_SEEDS[0], "protected")
    basis = experiment._gram_schmidt(tuple(shard[0] for shard in protected))
    raw = (1.0,) * experiment.DIMENSION
    projected = experiment._project(raw, basis)
    assert max(abs(experiment._dot(shard[0], projected)) for shard in protected) < 1e-10


def test_untouched_and_fixed_have_equal_candidate_compute() -> None:
    untouched = experiment._build_case(0, 5101, 6101, "forward", "untouched_base")
    fixed = experiment._build_case(1, 5101, 6101, "forward", "fixed_adapter")
    assert {
        key: value
        for key, value in untouched["compute_counts"].items()
        if key != "committed_updates"
    } == {
        key: value
        for key, value in fixed["compute_counts"].items()
        if key != "committed_updates"
    }
    assert untouched["compute_counts"]["candidate_states"] == 24
    assert untouched["compute_counts"]["candidate_fit_evaluations"] == 24
    assert untouched["compute_counts"]["candidate_protected_evaluations"] == 24
    assert untouched["compute_counts"]["committed_updates"] == 0
    assert fixed["compute_counts"]["committed_updates"] == 12


def test_rollback_restores_a_real_checkpoint() -> None:
    checkpoint = (0.0,) * experiment.DIMENSION
    changed = (0.4,) * experiment.DIMENSION
    restored = experiment._restore_checkpoint(changed, checkpoint)
    assert restored == checkpoint
    assert experiment._state_error(restored, checkpoint) == 0.0
    assert experiment._state_error(changed, checkpoint) > 0.0


def test_lock_precedes_assessment_and_probe_events() -> None:
    result = experiment.run_campaign()
    case = result["cases"][2]
    names = [event["event_name"] for event in case["event_log"]]
    assert names == list(experiment.EVENT_NAMES)
    assert names.index("prediction_lock_sealed") < names.index("assessment_completed")
    assert names.index("prediction_lock_sealed") < names.index("probe_completed")


def test_validator_rejects_metric_tampering() -> None:
    result = experiment.run_campaign()
    tampered = json.loads(json.dumps(result))
    tampered["cases"][0]["probe_gain"] += 0.01
    with pytest.raises(validator.ValidationError):
        validator.validate_result(tampered)


def test_writer_requires_receipt_and_exact_custody_path(tmp_path: Path) -> None:
    result = experiment.run_campaign()
    with pytest.raises(experiment.ProtocolError, match="review receipt"):
        experiment.write_result(result, tmp_path / "result.json", tmp_path / "missing.json")
    with pytest.raises(experiment.ProtocolError, match="declared custody path"):
        experiment.write_result(result, tmp_path / "result.json", experiment.REVIEW_RECEIPT_PATH)
