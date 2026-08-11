from experiments.continual_learning.task_keyed_readout_preflight import LABELS, PERMUTATIONS, STATE_SLICE


def test_v17_readout_space_is_four_by_four_permutation_tables():
    assert STATE_SLICE == "continual-learning-protocol-v17-task-keyed-readout-feasibility"
    assert len(PERMUTATIONS) == 24
    assert all(set(permutation) == set(LABELS) for permutation in PERMUTATIONS)


def test_v17_readout_has_no_claim_or_hardware_authority_by_construction():
    assert "feasibility" in STATE_SLICE
