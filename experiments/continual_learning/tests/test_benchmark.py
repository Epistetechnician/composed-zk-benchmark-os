import pytest

from experiments.continual_learning.benchmark import (
    STRATEGIES,
    ProtocolConfig,
    make_tasks,
    run_protocol,
    validate_protocol,
)
from experiments.continual_learning.model_benchmark import (
    LABELS,
    choose_balanced_full_replay,
    choose_replay,
    make_tasks as make_model_tasks,
    prompt_for,
    replay_counts_by_task,
    training_example,
)
from experiments.continual_learning.replicate_model_benchmark import campaign_cases, summarize


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


def test_model_task_manifest_is_disjoint_and_four_choice():
    tasks = make_model_tasks(17, task_count=4, facts_per_task=8)
    facts = [fact for task in tasks for fact in task.facts]
    assert len({fact.fact_id for fact in facts}) == 32
    assert {fact.label for fact in facts} == set(LABELS)
    assert {fact.label: sum(item.label == fact.label for item in tasks[0].facts) for fact in tasks[0].facts} == {label: 2 for label in LABELS}


def test_model_prompts_keep_context_explicit_and_training_schema_bounded():
    fact = make_model_tasks(17, task_count=4, facts_per_task=8)[0].facts[0]
    assert fact.fact_id in prompt_for(fact)
    assert "Reference facts" not in prompt_for(fact)
    assert fact.fact_id in prompt_for(fact, context=(fact,))
    assert prompt_for(fact).endswith("\nAnswer:")
    assert training_example(fact)["prompt"] == prompt_for(fact)
    assert training_example(fact)["completion"] == f" {fact.label}"


def test_replay_sample_is_bounded_and_spans_prior_tasks():
    tasks = make_model_tasks(17, task_count=4, facts_per_task=8)
    prior = [fact for task in tasks[:3] for fact in task.facts]
    sample = choose_replay(prior, capacity=16, seed=17, limit=8)
    assert len(sample) == 8
    assert len({fact.task_id for fact in sample}) == 3
    assert len(choose_replay(prior, capacity=16, seed=17)) == 16


def test_replay_counts_are_task_keyed_and_deterministic():
    tasks = make_model_tasks(17, task_count=4, facts_per_task=8)
    facts = [tasks[0].facts[0], tasks[2].facts[0], tasks[2].facts[1]]
    assert replay_counts_by_task(facts) == {"0": 1, "2": 2}


def test_balanced_full_replay_keeps_every_prior_task_complete():
    tasks = make_model_tasks(17, task_count=4, facts_per_task=8)
    prior = [fact for task in tasks[:3] for fact in task.facts]
    sample = choose_balanced_full_replay(prior, capacity=24, limit=24)
    assert len(sample) == 24
    assert replay_counts_by_task(sample) == {"0": 8, "1": 8, "2": 8}


def test_replication_campaign_has_nine_fixed_cases_and_strict_gate():
    cases = campaign_cases()
    assert len(cases) == 9
    rows = [
        {"seed": seed, "order": list(order), "retention_delta": 0.125}
        for seed, order in cases
    ]
    summary = summarize(rows)
    assert summary["all_nine_retention_deltas_positive"] is True
    assert summary["replication_gate_passed"] is True
