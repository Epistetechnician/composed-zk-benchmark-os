from experiments.continual_learning.shared_adapter_task_keyed_optimizer_state_protocol import (
    ITERS_PER_UPDATE,
    ORDERS,
    SEEDS,
    SHARED_ADAPTER_ID,
    SHARED_ADAPTER_LAYERS,
    STATE_SLICE,
    TASK_COUNT,
    UPDATE_BUDGET,
    build_plan,
    make_schedule,
    validate_plan,
)


def test_v24_is_a_frozen_nine_cell_protocol_without_training_authority():
    plan = build_plan()
    assert STATE_SLICE == "continual-learning-protocol-v24-shared-adapter-task-keyed-optimizer-state"
    assert len(SEEDS) * len(ORDERS) == 9
    assert plan["model_training_authorized"] is False
    assert plan["h100_authorized"] is False
    assert validate_plan(plan)["valid"] is True


def test_v24_replay_rows_use_their_task_keyed_optimizer_state():
    schedule = make_schedule(20260812, (0, 1, 2, 3), True)
    assert schedule[-1]["replay_fact_ids"]
    assert schedule[-1]["route_counts_by_task"] == {"0": 8, "1": 8, "2": 8, "3": 8}
    assert schedule[-1]["optimizer_iterations_by_task"] == {"0": 40, "1": 40, "2": 40, "3": 40}
    assert all(row["route_key"] == f"T{row['task_id']}" for entry in schedule for row in entry["rows"])


def test_v24_keeps_shared_adapter_and_exact_budgets():
    plan = build_plan()
    assert plan["total_examples_per_cell"] == UPDATE_BUDGET * TASK_COUNT == 128
    assert plan["total_optimizer_steps_per_cell"] == ITERS_PER_UPDATE * TASK_COUNT == 640
    assert all(
        entry["shared_adapter_id"] == SHARED_ADAPTER_ID
        and entry["shared_adapter_layers"] == SHARED_ADAPTER_LAYERS
        for cell in plan["cells"] for entry in cell["shared_replay_schedule"]
    )
