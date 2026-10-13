from experiments.continual_learning import task_stratified_microbatch_protocol as protocol


def test_v28_changes_only_batch_composition_on_the_first_tie_cell():
    plan = protocol.build_plan()
    assert plan["preflight_seed"] == 20260812
    assert plan["preflight_order"] == [0, 2, 3, 1]
    assert plan["changed_protocol_variable"] == "task_stratified_microbatch_schedule_v1"
    assert plan["batch_policy"] == "task_stratified_round_robin_microbatch_v1"
    assert plan["model_training_authorized"] is False


def test_v28_preserves_v26_examples_steps_and_shared_state():
    plan = protocol.build_plan()
    assert plan["total_examples_per_arm"] == 128
    assert plan["total_optimizer_steps_per_arm"] == 640
    assert plan["gates"]["same_selected_fact_ids_as_v26"] is True
    assert plan["gates"]["one_shared_optimizer_state"] is True
    assert plan["h100_authorized"] is False


def test_task_stratified_schedule_is_deterministic():
    assert protocol.task_stratified_batch_task_ids([0, 0, 1, 1]) == [[0, 1], [0, 1]]
    assert protocol.task_stratified_batch_task_ids([0] * 16 + [1] * 8 + [2] * 8)[0] == [0, 1]
