from experiments.continual_learning.task_routed_replay_protocol import (
    ITERS_PER_UPDATE,
    ORDERS,
    SEEDS,
    SLOT_SEED_BASE,
    STATE_SLICE,
    TASK_COUNT,
    UPDATE_BUDGET,
    build_plan,
    fixed_slot_seed,
    make_schedule,
    validate_plan,
)


def test_v23_is_the_frozen_nine_cell_matrix_without_training_authority():
    plan = build_plan()
    assert STATE_SLICE == "continual-learning-protocol-v23-task-routed-replay-consolidation"
    assert len(SEEDS) * len(ORDERS) == 9
    assert plan["model_training_authorized"] is False
    assert plan["h100_authorized"] is False


def test_v23_replay_rows_route_to_their_fact_task_slot():
    schedule = make_schedule(20260812, (0, 3, 1, 2), True)
    assert schedule[1]["replay_fact_ids"]
    assert all(row["route_key"] == f"T{row['task_id']}" for entry in schedule for row in entry["rows"])
    assert schedule[-1]["dataset_row_count"] == UPDATE_BUDGET


def test_v23_keeps_the_stable_slot_seed_and_budget_contract():
    plan = build_plan()
    assert plan["total_examples_per_cell"] == UPDATE_BUDGET * TASK_COUNT == 128
    assert plan["total_optimizer_steps_per_cell"] == ITERS_PER_UPDATE * TASK_COUNT == 640
    assert [fixed_slot_seed(task_id) for task_id in range(TASK_COUNT)] == [SLOT_SEED_BASE + task_id for task_id in range(TASK_COUNT)]
    assert validate_plan(plan)["valid"] is True
