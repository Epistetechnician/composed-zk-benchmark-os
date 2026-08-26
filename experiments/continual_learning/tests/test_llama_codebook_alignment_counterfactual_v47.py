from __future__ import annotations

import pytest

from experiments.continual_learning import llama_codebook_alignment_counterfactual_v47 as v47


def test_v47_freezes_paired_counterfactual_contract():
    assert v47.STATE_SLICE == "continual-learning-llama-codebook-alignment-counterfactual-execution-v47"
    assert v47.TASK_SEEDS == (20260865, 20260866, 20260867)
    assert v47.TARGET_SHIFTS == (0, 1)
    assert v47.FIXED_OPTIMIZER_SEED == 20260856
    assert v47.ORDER == (0, 1, 2, 3)
    assert v47.ITERS == 160
    assert v47.UPDATE_BUDGET == 32


def test_v47_counterfactual_changes_only_target_mapping():
    identity = v47._counterfactual_tasks(20260865, 4, 0)
    shifted = v47._counterfactual_tasks(20260865, 4, 1)
    assert v47._underlying_fact_digest([
        {
            "task_id": task.task_id,
            "task_token": task.task_token,
            "train_facts": [fact.__dict__ for fact in task.train_facts],
            "test_facts": [fact.__dict__ for fact in task.test_facts],
        }
        for task in identity
    ]) == v47._underlying_fact_digest([
        {
            "task_id": task.task_id,
            "task_token": task.task_token,
            "train_facts": [fact.__dict__ for fact in task.train_facts],
            "test_facts": [fact.__dict__ for fact in task.test_facts],
        }
        for task in shifted
    ])
    assert identity[0].mapping != shifted[0].mapping
    assert identity[1:] == shifted[1:]
    assert [fact.label for fact in identity[0].train_facts] != [fact.label for fact in shifted[0].train_facts]


def test_v47_rejects_repository_or_existing_artifact_roots(tmp_path):
    with pytest.raises(ValueError, match="outside the repository"):
        v47._ensure_external_new_root(v47.REPO_ROOT / "forbidden-v47")
    existing = tmp_path / "existing-v47"
    existing.mkdir()
    with pytest.raises(FileExistsError, match="refusing overwrite"):
        v47._ensure_external_new_root(existing)

