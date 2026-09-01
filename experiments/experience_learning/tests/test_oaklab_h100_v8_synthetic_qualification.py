"""Hermetic tests for Oak Lab H100 V8 synthetic qualification.

State slice: ``oaklab-experience-learning-h100-replication-v8``.
"""

from experiments.experience_learning.oaklab_h100_v8_synthetic_qualification import (
    FIT_ROWS,
    ROWS,
    STREAMS,
    _run_arm,
    generate,
)


def test_generator_is_deterministic_and_exactly_sized():
    for stream in STREAMS:
        first = generate(stream, 4000)
        second = generate(stream, 4000)
        assert first == second
        assert len(first) == ROWS
        assert all(len(item.features) > 0 and item.row == index for index, item in enumerate(first))


def test_baseline_uses_one_update_per_row_and_tune_half():
    record = _run_arm("sparse_signal_v8", 4000, False)
    assert record["counter"]["rows"] == ROWS
    assert record["updates"] == ROWS
    assert record["gated_rows"] == 0
    assert FIT_ROWS == ROWS // 2
    assert record["mean_loss"] >= 0.0


def test_candidate_counter_is_derived_and_can_skip_without_replay():
    record = _run_arm("pure_noise_v8", 4000, True)
    assert record["counter"]["rows"] == ROWS
    assert record["updates"] + record["gated_rows"] == ROWS
    assert record["apply_rows"] == record["updates"]
    assert record["counter"]["learned_events"] >= 0
