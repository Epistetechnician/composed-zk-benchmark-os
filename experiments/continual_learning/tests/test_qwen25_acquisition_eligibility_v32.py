from __future__ import annotations

from argparse import Namespace

import pytest

from experiments.continual_learning import qwen25_acquisition_eligibility_v32 as v32
from experiments.continual_learning.validate_qwen25_acquisition_eligibility_v32 import expected_prompt


def test_v32_contract_uses_disjoint_fixed_seeds_and_route_order():
    assert v32.ORDER == (0, 1, 2, 3)
    assert v32.SEEDS == (20260853, 20260854, 20260855)
    assert v32.ITERS == 160
    assert v32.UPDATE_BUDGET == 32
    assert str(v32.MODEL_DEFAULT).endswith("Qwen2.5-0.5B-Instruct-4bit")


def test_v32_prompt_is_exact_route_bound_prompt():
    fact = {"task_token": "T2", "residue": 3}
    prompt = expected_prompt({**fact, "label": "A"})
    assert prompt.endswith("Task route binding: T2.\nAnswer:")
    assert "Compose " not in prompt


def test_v32_case_mode_rejects_model_drift_without_mutation(tmp_path):
    with pytest.raises(ValueError, match="model drift"):
        v32.run_case(tmp_path / "case", tmp_path / "wrong-model", v32.SEEDS[0])
    assert not (tmp_path / "case").exists()


def test_v32_campaign_rejects_existing_immutable_root(tmp_path):
    root = tmp_path / "campaign"
    root.mkdir()
    args = Namespace(artifact_root=root, model=v32.MODEL_DEFAULT)
    with pytest.raises(RuntimeError, match="refusing overwrite"):
        v32.run_campaign(args)
