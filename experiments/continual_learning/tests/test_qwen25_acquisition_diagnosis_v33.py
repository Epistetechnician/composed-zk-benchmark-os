from __future__ import annotations

import pytest

from experiments.continual_learning.diagnose_qwen25_acquisition_v33 import (
    MODEL,
    SEEDS,
    STATE_SLICE,
    classify_task,
)


def _task(no_update: float, adapter: float, constant: bool) -> dict:
    return {
        "no_update_train": {"accuracy": no_update},
        "adapter_train": {"accuracy": adapter, "constant_output": constant},
    }


def test_v33_classifies_non_target_tie_or_regression():
    assert classify_task(_task(0.5, 0.5, False)) == "NonTargetAcquisitionTieOrRegression"


def test_v33_classifies_partial_constant_acquisition():
    assert classify_task(_task(0.0, 0.25, True)) == "PartialAcquisitionConstantOutput"


def test_v33_contract_is_bound_to_v32_cases():
    assert STATE_SLICE == "continual-learning-diagnosis-qwen25-acquisition-v33"
    assert SEEDS == (20260853, 20260854, 20260855)
    assert str(MODEL).endswith("Qwen2.5-0.5B-Instruct-4bit")


def test_v33_does_not_accept_unknown_task_shape():
    with pytest.raises(KeyError):
        classify_task({"adapter_train": {"accuracy": 0.5}})
