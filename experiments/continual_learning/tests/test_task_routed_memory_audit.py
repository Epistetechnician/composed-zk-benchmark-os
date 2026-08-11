from experiments.continual_learning.task_routed_memory_audit import FIXED_KEYS, STATE_SLICE


def test_v16_audit_is_a_distinct_read_only_state_slice():
    assert STATE_SLICE == "continual-learning-protocol-v16-task-routed-memory-audit"


def test_v16_contract_includes_runtime_and_route_relevant_fields():
    assert "route_policy" in FIXED_KEYS
    assert "iters" in FIXED_KEYS
    assert "prompt_contract" in FIXED_KEYS
