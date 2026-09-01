"""Hermetic tests for recursive update-policy V2.

State slice: ``continual-learning-recursive-update-policy-v2``.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from experiments.continual_learning import recursive_update_policy_v2 as experiment
from experiments.continual_learning import validate_recursive_update_policy_v2 as validator


def test_memory_contract_and_stable_promotion_pass() -> None:
    assert experiment.memory_probe() == {
        "fresh_accepted": True,
        "stale_rejected": True,
        "contradiction_rejected": True,
        "poison_rejected": True,
        "deletion_rejected": True,
        "procedural_promotion": True,
    }
    case = experiment._run_case(
        experiment.REPLICATE_SEEDS[0],
        experiment.ORDER_SEEDS[0],
        "forward",
        "recursive_policy",
    )
    assert sum(row["memory_promoted"] for row in case["generations"]) > 0


def test_campaign_is_deterministic_and_independently_validated() -> None:
    first = experiment.run_campaign()
    second = experiment.run_campaign()
    assert first == second
    validator.validate_result(json.loads(json.dumps(first)))
    assert len(first["cases"]) == 64
    assert first["execution_authorized"] is False
    assert first["base_state_sha256"] == experiment.BASE_STATE_SHA256


def test_v2_does_not_claim_a_candidate_on_fixed_synthetic_outcome() -> None:
    result = experiment.run_campaign()
    assert result["classification"] == "NoCandidate"
    assert result["campaign_summary"]["selection_advantage_mean"] < experiment.SELECTION_MINIMUM
    assert result["campaign_summary"]["generational_compounding_bootstrap_95"][0] < 0.0


def test_reserve_causally_scales_update_capacity() -> None:
    target = (1.0,) * experiment.DIMENSION
    protected = (0.0,) * experiment.DIMENSION
    low_theta, low_reserve = experiment._apply_update(
        (0.0,) * experiment.DIMENSION,
        0.0,
        target,
        protected,
        experiment._policy("balanced"),
        (0.0,) * experiment.DIMENSION,
    )
    high_theta, high_reserve = experiment._apply_update(
        (0.0,) * experiment.DIMENSION,
        1.0,
        target,
        protected,
        experiment._policy("balanced"),
        (0.0,) * experiment.DIMENSION,
    )
    assert high_theta != low_theta
    assert high_reserve != low_reserve


def test_rollback_restores_a_real_checkpoint() -> None:
    checkpoint = experiment._state(experiment.BASE_THETA, 1.0, experiment.FIXED_POLICY, 0)
    changed = experiment._state((0.4,) * experiment.DIMENSION, 0.2, "plastic", 9)
    restored = experiment._restore_checkpoint(changed, checkpoint)
    assert restored == checkpoint
    assert experiment._state_error(restored, checkpoint) == 0.0
    assert experiment._state_error(changed, checkpoint) > 0.0


def test_sandbox_rejects_immutable_effects_and_bad_digest() -> None:
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
    malformed = {
        "state_slice": experiment.STATE_SLICE,
        "generation": 0,
        "prior_policy": "balanced",
        "proposed_policy": "plastic",
        "candidate_score_digest": "not-a-digest",
        "controller_mode": "recursive_policy",
    }
    with pytest.raises(experiment.ProtocolError, match="sandbox score digest"):
        experiment.validate_sandbox_proposal(malformed)


def test_order_guard_is_present_for_every_case() -> None:
    result = experiment.run_campaign()
    assert all(case["summary"]["order_guard_pass"] for case in result["cases"])
    assert all(case["summary"]["order_pair_delta"] <= experiment.MAX_ORDER_DELTA for case in result["cases"])


def test_independent_validator_rejects_metric_tampering() -> None:
    result = experiment.run_campaign()
    tampered = json.loads(json.dumps(result))
    tampered["cases"][0]["generations"][0]["adaptation_gain"] += 0.1
    tampered["result_sha256"] = experiment._digest({key: value for key, value in tampered.items() if key != "result_sha256"})
    with pytest.raises(validator.ValidationError, match="aggregate does not match"):
        validator.validate_result(tampered)


def test_writer_requires_receipt_and_exact_custody_path(tmp_path: Path) -> None:
    result = experiment.run_campaign()
    with pytest.raises(TypeError):
        experiment.write_result(result, tmp_path / "result.json")  # type: ignore[call-arg]
    with pytest.raises(experiment.ProtocolError, match="review receipt missing"):
        experiment.write_result(result, tmp_path / "result.json", tmp_path / "missing-review.json")
