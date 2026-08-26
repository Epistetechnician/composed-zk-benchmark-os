from experiments.continual_learning.model_eligibility_preflight_v28 import (
    CLAIM_CEILING,
    STATE_SLICE,
    case_is_eligible,
    eligibility_gates,
)


def _task(task_id, train, heldout, baseline, constant=False):
    metric = lambda accuracy: {"accuracy": accuracy, "constant_output": constant}
    return {
        "task_id": task_id,
        "no_update_train": metric(baseline),
        "adapter_train": metric(train),
        "adapter_test": metric(heldout),
    }


def test_v28_requires_every_task_to_acquire_above_baseline():
    tasks = [_task(task_id, 0.75, 0.75, 0.25) for task_id in range(4)]
    assert all(eligibility_gates(tasks).values())
    tasks[2] = _task(2, 0.25, 0.75, 0.25)
    assert eligibility_gates(tasks)["all_task_train_above_no_update"] is False


def test_v28_target_constant_output_is_rejected_even_at_floor():
    tasks = [_task(task_id, 0.75, 0.75, 0.25) for task_id in range(4)]
    tasks[0] = _task(0, 0.75, 0.75, 0.25, constant=True)
    gates = eligibility_gates(tasks)
    assert gates["target_train_floor"] is True
    assert gates["target_heldout_floor"] is True
    assert gates["target_not_constant_output"] is False


def test_v28_structural_invalidity_is_fail_closed():
    gates = {"gate": True}
    assert case_is_eligible({"valid": True}, gates) is True
    assert case_is_eligible({"valid": False}, gates) is False


def test_v28_state_slice_and_claim_ceiling_are_local_only():
    assert STATE_SLICE == "continual-learning-model-eligibility-preflight-v28"
    assert CLAIM_CEILING == "LocalDevelopmentModelEligibilityPreflight"
