from experiments.experience_learning.replication_sensitivity_v1 import (
    HYPERPARAMETER_GRID, SURVIVING_ALGORITHMS, run_campaign,
)
from experiments.experience_learning.validate_replication_sensitivity_v1 import validate_result


def test_replication_sensitivity_locks_on_tune_only():
    result = run_campaign(
        ("sparse_noisy", "delayed_reward"), steps=24,
        seed_offsets=(20, 21, 22, 23, 24),
        algorithms=("sgd_b1", "tidbd", "event_driven"),
    )
    assert validate_result(result) == []
    assert "plasticity_guard" not in result["algorithm_names"]
    assert result["closed_arms"]
    for stream in result["streams"].values():
        for algorithm, record in stream["algorithms"].items():
            if record["status"] == "not_applicable":
                assert algorithm == "tidbd"
                continue
            assert len(record["candidates"]) == len(HYPERPARAMETER_GRID[algorithm])
            assert record["selection"]["assessment_selection_used"] is False
            if record["status"] == "executed":
                assert record["assessment"]["mean_loss"]["estimate"]["n"] == 5


def test_grid_is_exactly_the_declared_surviving_set():
    assert set(HYPERPARAMETER_GRID) == set(SURVIVING_ALGORITHMS)
    assert len(SURVIVING_ALGORITHMS) == 12
