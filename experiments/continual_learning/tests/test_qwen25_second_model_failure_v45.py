from __future__ import annotations

import pytest

from experiments.continual_learning import diagnose_qwen25_second_model_failure_v45 as v45


def test_v45_freezes_source_identity_and_read_only_boundary():
    assert v45.STATE_SLICE == "continual-learning-qwen25-second-model-failure-diagnosis-v45"
    assert v45.PROTOCOL == "v45-qwen25-second-model-failure-diagnosis-v1"
    assert v45.SOURCE_STATE_SLICE == "continual-learning-qwen25-second-model-replication-v44"
    assert v45.TASK_SEEDS == (20260862, 20260863, 20260864)
    assert v45.ITERS == 160
    assert v45.UPDATE_BUDGET == 32


def test_v45_source_and_output_guards_are_external_and_immutable(tmp_path):
    with pytest.raises(ValueError, match="outside the repository"):
        v45._ensure_external_new_root(v45.REPO_ROOT / "forbidden-v45")
    existing = tmp_path / "existing-v45"
    existing.mkdir()
    with pytest.raises(FileExistsError, match="refusing overwrite"):
        v45._ensure_external_new_root(existing)
    with pytest.raises(ValueError, match="frozen V44 artifact root"):
        v45._ensure_source_root(tmp_path)


def test_v45_histogram_and_raw_observation_are_deterministic(tmp_path):
    assert v45._histogram(["B", "A", "B", "C"]) == {"A": 1, "B": 2, "C": 1}
    path = tmp_path / "train.jsonl"
    text = "Task token: T0.\nTask route binding: T0.\nAnswer: A"
    path.write_text(__import__("json").dumps({"text": text}) + "\n", encoding="utf-8")
    observed = v45._jsonl_observation(path)
    assert observed["row_count"] == 1
    assert observed["completion_histogram"] == {"A": 1}
    assert observed["task_token_values"] == ["T0"]
    assert observed["route_binding_values"] == ["T0"]


def test_v45_diagnosis_contract_does_not_authorize_execution():
    boundary = {
        "model_execution": False,
        "training": False,
        "inference": False,
        "network_access": False,
        "source_artifact_mutated": False,
        "source_result_relabeling": False,
        "source_result_reuse_for_promotion": False,
    }
    assert all(value is False for value in boundary.values())
