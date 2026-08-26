from __future__ import annotations

from experiments.continual_learning.routed_adapter_bank_acquisition_v29 import (
    MODEL_DEFAULT,
    ORDER,
    SEED,
    TARGET_FLOOR,
    eligibility_gates,
)


def _metric(accuracy: float, observed: tuple[str, ...] = ("A", "B")) -> dict:
    return {
        "accuracy": accuracy,
        "n": 8,
        "constant_output": len(set(observed)) == 1,
        "rows": [{"observed": value} for value in observed] + [{"observed": observed[0]}] * (8 - len(observed)),
    }


def test_v29_contract_is_frozen():
    assert SEED == 20260861
    assert ORDER == (0, 1, 2, 3)
    assert TARGET_FLOOR == 0.75
    assert str(MODEL_DEFAULT).endswith("Qwen3.6-35B-A3B-MLX-4bit")


def test_all_four_eligibility_gates_pass_only_for_complete_acquisition():
    results = [
        {
            "task_id": task_id,
            "no_update_train": _metric(0.25),
            "adapter_train": _metric(1.0),
            "adapter_test": _metric(0.75),
        }
        for task_id in range(4)
    ]
    assert eligibility_gates(results) == {
        "all_task_train_above_no_update": True,
        "target_train_floor": True,
        "target_heldout_floor": True,
        "target_not_constant_output": True,
    }


def test_constant_target_output_rejects_eligibility():
    results = [
        {
            "task_id": task_id,
            "no_update_train": _metric(0.25),
            "adapter_train": _metric(1.0),
            "adapter_test": _metric(0.75),
        }
        for task_id in range(4)
    ]
    results[0]["adapter_train"] = _metric(0.75, ("A",))
    assert eligibility_gates(results)["target_not_constant_output"] is False


def test_target_floor_is_independent_of_other_task_acquisition():
    results = [
        {
            "task_id": task_id,
            "no_update_train": _metric(0.25),
            "adapter_train": _metric(1.0 if task_id else 0.75),
            "adapter_test": _metric(0.75),
        }
        for task_id in range(4)
    ]
    results[2]["adapter_train"] = _metric(0.25)
    gates = eligibility_gates(results)
    assert gates["target_train_floor"] is True
    assert gates["all_task_train_above_no_update"] is False
