"""Hermetic tests for recursive update-policy V1.

State slice: ``continual-learning-recursive-update-policy-v1``.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from experiments.continual_learning import recursive_update_policy_v1 as experiment
from experiments.continual_learning import validate_recursive_update_policy_v1 as validator


def test_contract_memory_probe_is_complete() -> None:
    assert experiment.memory_probe() == {
        "fresh_accepted": True,
        "stale_rejected": True,
        "contradiction_rejected": True,
        "poison_rejected": True,
        "deletion_rejected": True,
        "procedural_promotion": True,
    }


def test_campaign_is_deterministic_and_independently_validated() -> None:
    first = experiment.run_campaign()
    second = experiment.run_campaign()
    assert first == second
    validator.validate_result(json.loads(json.dumps(first)))
    assert len(first["cases"]) == 64
    assert first["execution_authorized"] is False


def test_fixed_preregistered_synthetic_rule_does_not_claim_rsi() -> None:
    result = experiment.run_campaign()
    assert result["campaign_summary"]["primary_gate_pass"] is False
    assert result["campaign_summary"]["generational_compounding_bootstrap_95"][0] < 0.0


def test_adaptation_retention_and_plasticity_are_separate() -> None:
    case = experiment.run_case(
        experiment.REPLICATE_SEEDS[0],
        experiment.ORDER_SEEDS[0],
        "forward",
        "recursive_policy",
    )
    generation = case["generations"][0]
    assert {
        "adaptation_gain",
        "retention_delta",
        "post_adaptation_plasticity_gain",
    }.issubset(generation)
    assert generation["adaptation_gain"] == pytest.approx(
        generation["base_assessment_loss"] - generation["final_assessment_loss"]
    )
    assert generation["retention_delta"] == pytest.approx(
        generation["final_protected_loss"] - generation["base_protected_loss"]
    )


def test_compute_is_equal_across_arms() -> None:
    result = experiment.run_campaign()
    totals = {
        case["summary"]["total_compute_units"]
        for case in result["cases"]
    }
    assert totals == {experiment.EXPECTED_TOTAL_COMPUTE}
    assert all(
        case["summary"]["update_attempts"] == experiment.GENERATION_COUNT * experiment.FIT_TASK_COUNT
        for case in result["cases"]
    )


def test_sandbox_rejects_immutable_effects() -> None:
    proposal = {
        "state_slice": experiment.STATE_SLICE,
        "generation": 0,
        "prior_policy": "balanced",
        "proposed_policy": "plastic",
        "candidate_score_digest": "0" * 64,
        "controller_mode": "recursive_policy",
        "compute_budget": 999,
    }
    with pytest.raises(experiment.ProtocolError, match="sandbox proposal schema"):
        experiment.validate_sandbox_proposal(proposal)


def test_checkpoint_chain_and_lock_order_are_exact() -> None:
    result = experiment.run_campaign()
    for case in result["cases"]:
        previous = None
        for generation in case["generations"]:
            if previous is not None:
                assert generation["checkpoint_before_sha256"] == previous["checkpoint_after_sha256"]
            assert generation["rollback_max_abs_error"] <= experiment.ROLLBACK_TOLERANCE
            previous = generation
        event_names = [event["event_name"] for event in case["event_log"]]
        assert event_names[0] == "synthetic_initialized"
        for index in range(experiment.GENERATION_COUNT):
            start = 1 + index * 4
            assert event_names[start : start + 4] == [
                "fit_tune_completed",
                "prediction_lock_sealed",
                "assessment_completed",
                "rollback_verified",
            ]
        for event_index, event in enumerate(case["event_log"]):
            assert event["event_index"] == event_index
            assert event["predecessor_event_index"] == (None if event_index == 0 else event_index - 1)


def test_independent_validator_rejects_metric_tampering() -> None:
    result = experiment.run_campaign()
    tampered = json.loads(json.dumps(result))
    tampered["cases"][0]["generations"][0]["adaptation_gain"] += 0.1
    with pytest.raises(validator.ValidationError, match="case recomputation mismatch"):
        validator.validate_result(tampered)


def test_writer_rejects_repository_output(tmp_path: Path) -> None:
    result = experiment.run_campaign()
    with pytest.raises(experiment.ProtocolError, match="outside repository"):
        experiment.write_result(result, Path(__file__).resolve().parents[3] / "recursive-result.json")
