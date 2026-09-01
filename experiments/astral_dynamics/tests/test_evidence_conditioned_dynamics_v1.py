from __future__ import annotations

from dataclasses import asdict

import pytest

from experiments.astral_dynamics import evidence_conditioned_dynamics_v1 as dynamics


def test_fixture_shards_and_receipts_are_deterministic_and_digest_bound():
    first = dynamics.make_shards()
    second = dynamics.make_shards()

    assert first == second
    receipt = dynamics.make_receipt(first[2])
    assert receipt.receipt_source == dynamics.RECEIPT_SOURCE
    assert receipt.computation_verified is False
    with pytest.raises(dynamics.ProtocolError, match="receipt digest mismatch"):
        dynamics._validate_receipt(
            dynamics.replace(receipt, receipt_sha256="0" * 64),
            first[2],
        )
    with pytest.raises(dynamics.ProtocolError, match="payload digest mismatch"):
        dynamics._validate_shard(dynamics.replace(first[0], category="novel"))


def test_parallel_wave_multiplier_is_bounded_and_deterministic():
    config = dynamics.ProtocolConfig()
    values = [dynamics.wave_multiplier(step, config) for step in range(32)]

    assert values == [dynamics.wave_multiplier(step, config) for step in range(32)]
    assert min(values) >= config.min_wave_multiplier
    assert max(values) <= config.max_wave_multiplier
    assert len(set(values)) > 4


def test_high_risk_shard_requires_computation_receipt_and_is_quarantined():
    config = dynamics.ProtocolConfig()
    shard = dynamics.make_shards(config)[2]
    state = dynamics.LearnerState()
    result = dynamics.process_shard(
        state,
        shard,
        dynamics.make_receipt(shard),
        dynamics.make_shadow_evaluation(shard),
        step=2,
        mode="adaptive_gate",
        config=config,
    )

    assert result.final_state == "quarantined"
    assert shard.shard_id in result.state.quarantined_shards
    assert result.transitions[-1].reason == "computation_receipt_required"


def test_shadow_precedes_commit_and_rollback_removes_effect():
    config = dynamics.ProtocolConfig()
    shard = dynamics.make_shards(config)[0]
    result = dynamics.process_shard(
        dynamics.LearnerState(),
        shard,
        None,
        dynamics.make_shadow_evaluation(shard),
        step=0,
        mode="fixed_baseline",
        config=config,
    )

    assert result.final_state == "committed"
    actions = [transition.action for transition in result.transitions]
    assert actions.index("shadow") < actions.index("commit")
    rolled_back, event = dynamics.rollback(result.state, shard.shard_id, step=1, config=config)
    assert event.action == "rollback"
    assert shard.shard_id not in rolled_back.committed_shards
    assert rolled_back.fast_value == 0.0
    assert rolled_back.slow_value == 0.0


def test_protocol_is_independent_digest_validated_and_claim_bounded():
    result = dynamics.run_protocol()
    dynamics.validate_result(result)

    assert result["state_slice"] == dynamics.STATE_SLICE
    assert result["claims"] == [
        "contract_mechanics_only",
        "no_model_loaded",
        "no_weights_updated",
        "no_zk_or_pqc_proof_generated",
        "no_astral_scientific_evidence",
    ]
    assert result["results"]["adaptive_gate"]["quarantined_count"] > 0

    tampered = dict(result)
    tampered["results"] = dict(result["results"])
    tampered["results"]["fixed_baseline"] = dict(result["results"]["fixed_baseline"])
    tampered["results"]["fixed_baseline"]["committed_count"] += 1
    with pytest.raises(dynamics.ProtocolError, match="state version mismatch"):
        dynamics.validate_result(tampered)


def test_transition_digest_rejects_untrusted_field_types():
    result = dynamics.run_protocol()
    transition = dict(result["results"]["fixed_baseline"]["transitions"][0])
    transition["step"] = "0"
    with pytest.raises(dynamics.ProtocolError, match="invalid transition step"):
        dynamics._validate_transition(transition)
