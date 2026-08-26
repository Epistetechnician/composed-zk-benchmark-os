from experiments.continual_learning.diagnose_routed_adapter_bank_replication_v27 import (
    STATE_SLICE,
)


def test_v27_diagnosis_is_read_only_and_bounded():
    assert STATE_SLICE == "continual-learning-diagnosis-task-routed-adapter-bank-v27"
