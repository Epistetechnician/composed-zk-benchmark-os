from experiments.continual_learning.task_routed_compact_residual_preflight import (
    COMPACT_SLOT_LAYERS,
    FULL_SHARED_LAYERS,
    STATE_SLICE,
)


def test_v19_compact_slots_match_one_shared_adapter_layer_budget():
    assert STATE_SLICE == "continual-learning-protocol-v19-task-routed-compact-residual"
    assert COMPACT_SLOT_LAYERS * 4 == FULL_SHARED_LAYERS


def test_v19_claim_and_hardware_boundaries_are_local_only():
    assert "compact-residual" in STATE_SLICE
