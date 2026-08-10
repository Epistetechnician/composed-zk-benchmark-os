import pytest

from experiments.continual_learning.benchmark import (
    STRATEGIES,
    ProtocolConfig,
    make_tasks,
    run_protocol,
    validate_protocol,
)


def test_task_generation_and_protocol_are_deterministic():
    config = ProtocolConfig(seed=17, facts_per_task=8, replay_capacity=12)
    assert make_tasks(config) == make_tasks(config)
    first = run_protocol(config)
    second = run_protocol(config)
    assert first == second
    validate_protocol(first)


def test_source_context_control_exposes_leakage_boundary():
    result = run_protocol(ProtocolConfig(facts_per_task=8, replay_capacity=12))
    assert result["results"]["context_only"]["acquisition"]["accuracy"] == 0
    assert result["results"]["context_only"]["acquisition_with_context"]["accuracy"] == 1
    assert result["results"]["context_only"]["retention_after_interference"]["accuracy"] == 0


def test_naive_sequential_forgets_and_reacquisition_recovers():
    result = run_protocol(ProtocolConfig(facts_per_task=8, replay_capacity=12))
    metrics = result["results"]["naive_sequential"]
    assert metrics["acquisition"]["accuracy"] == 1
    assert metrics["retention_after_interference"]["accuracy"] == 0
    assert metrics["recovery_after_reacquisition"]["accuracy"] == 1


def test_retrieval_is_an_upper_control_and_replay_is_capacity_bounded():
    result = run_protocol(ProtocolConfig(facts_per_task=8, replay_capacity=12))
    assert result["results"]["retrieval"]["retention_after_interference"]["accuracy"] == 1
    assert result["results"]["replay"]["memory_size_after_interference"] <= 12


def test_protocol_rejects_strategy_panel_drift():
    result = run_protocol(ProtocolConfig(facts_per_task=4, replay_capacity=6))
    result["strategies"] = list(reversed(STRATEGIES))
    with pytest.raises(ValueError, match="strategy panel"):
        validate_protocol(result)


def test_protocol_rejects_digest_drift():
    result = run_protocol(ProtocolConfig(facts_per_task=4, replay_capacity=6))
    result["results"]["replay"]["retention_after_interference"]["correct"] = 0
    with pytest.raises(ValueError, match="digest"):
        validate_protocol(result)
