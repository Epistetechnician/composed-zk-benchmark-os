from experiments.experience_learning.real_sensitivity_v1 import (
    DATASET_NAMES, FIT_ROWS, REAL_SENSITIVITY_GRID, REQUIRED_ROWS,
    SURVIVING_ALGORITHMS, TUNE_ROWS, _bh_adjust, _split_ranges,
)


def test_real_protocol_has_wider_grid_and_fresh_cohort_splits():
    assert tuple(REAL_SENSITIVITY_GRID) == SURVIVING_ALGORITHMS
    assert all(len(REAL_SENSITIVITY_GRID[name]) == 3 for name in SURVIVING_ALGORITHMS)
    assert _split_ranges(REQUIRED_ROWS) == {
        "fit": (0, FIT_ROWS), "tune": (FIT_ROWS, FIT_ROWS + TUNE_ROWS),
        "assessment": (FIT_ROWS + TUNE_ROWS, REQUIRED_ROWS),
    }
    assert DATASET_NAMES == ("noisy_mnist", "sensor", "long_horizon", "event_camera")


def test_bh_adjustment_is_finite_and_monotone_for_declared_tests():
    adjusted = _bh_adjust([("a", 0.01), ("b", 0.02), ("c", 0.5)])
    assert set(adjusted) == {"a", "b", "c"}
    assert all(0.0 <= value <= 1.0 for value in adjusted.values())
    assert adjusted["a"] <= adjusted["b"] <= adjusted["c"]
