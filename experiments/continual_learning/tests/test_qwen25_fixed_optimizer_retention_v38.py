from __future__ import annotations

from experiments.continual_learning.qwen25_fixed_optimizer_retention_v38 import (
    FIXED_OPTIMIZER_SEED,
    REPLAY_CAPACITY,
    TARGET_FLOOR,
    UPDATE_BUDGET,
    case_name,
    replay_counts,
    replay_facts,
)


def test_v38_case_name_binds_task_and_optimizer_seed():
    assert case_name(20260856) == "task-seed-20260856-order-0123-fixed-opt-20260856"


def test_v38_replay_is_bounded_and_deterministically_task_sorted():
    class Fact:
        def __init__(self, task_id, fact_id):
            self.task_id = task_id
            self.fact_id = fact_id

    previous = [Fact(2, "T2-b"), Fact(1, "T1-b"), Fact(1, "T1-a"), Fact(0, "T0-a")]
    selected = replay_facts(previous, [])
    assert [(fact.task_id, fact.fact_id) for fact in selected] == [
        (0, "T0-a"),
        (1, "T1-a"),
        (1, "T1-b"),
        (2, "T2-b"),
    ]
    assert len(selected) <= REPLAY_CAPACITY


def test_v38_replay_counts_are_explicit():
    class Fact:
        def __init__(self, task_id):
            self.task_id = task_id

    assert replay_counts([Fact(0), Fact(0), Fact(2)]) == {"0": 2, "2": 1}


def test_v38_contract_constants_preserve_acquisition_boundary():
    assert FIXED_OPTIMIZER_SEED == 20260856
    assert UPDATE_BUDGET == 32
    assert TARGET_FLOOR == 0.75
