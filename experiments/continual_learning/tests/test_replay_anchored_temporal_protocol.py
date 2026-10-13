from experiments.continual_learning import replay_anchored_temporal_protocol as protocol


def test_replay_anchored_schedule_places_oldest_replay_before_current_phase():
    task_ids = [2] * 8 + [0] * 8 + [1] * 8 + [3] * 8
    batches = protocol.replay_anchored_batch_task_ids(task_ids, current_task_id=2)
    assert batches[:4] == [[0, 0], [1, 1], [3, 3], [2, 2]]
    assert batches[4:8] == [[0, 0], [1, 1], [3, 3], [2, 2]]
    assert len(batches) == 16


def test_no_replay_schedule_preserves_current_task_only():
    assert protocol.replay_anchored_batch_task_ids([2] * 32, current_task_id=2) == [[2, 2]] * 16


def test_v29_freezes_the_v28_tie_cell_and_budget():
    plan = protocol.build_plan()
    assert plan["preflight_order"] == [0, 3, 1, 2]
    assert plan["frozen_v28_confirmation_effect"] == 0.0
    assert plan["total_examples_per_arm"] == 128
    assert plan["total_optimizer_steps_per_arm"] == 640
    assert plan["h100_authorized"] is False
