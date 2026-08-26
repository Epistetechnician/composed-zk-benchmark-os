from __future__ import annotations

from argparse import Namespace

import pytest

from experiments.continual_learning import qwen25_raw_text_acquisition_v34 as v34
from experiments.continual_learning.validate_qwen25_raw_text_acquisition_v34 import expected_prompt


def test_v34_contract_uses_fresh_fixed_seeds_and_raw_text_boundary():
    assert v34.ORDER == (0, 1, 2, 3)
    assert v34.SEEDS == (20260856, 20260857, 20260858)
    assert v34.ITERS == 160
    assert v34.UPDATE_BUDGET == 32
    assert str(v34.MODEL_DEFAULT).endswith("Qwen2.5-0.5B-Instruct-4bit")
    assert "--mask-prompt" not in v34.raw_text_training_command(v34.MODEL_DEFAULT, v34.MODEL_DEFAULT, v34.MODEL_DEFAULT, 1, 1, None)


def test_v34_raw_text_row_preserves_exact_route_bound_prompt():
    fact = Namespace(task_token="T2", residue=3, label="A")
    row = v34.raw_text_training_example(fact)
    assert set(row) == {"text"}
    assert row["text"] == expected_prompt({"task_token": "T2", "residue": 3}) + " A"
    assert "Compose " not in row["text"]


def test_v34_case_mode_rejects_model_drift_without_mutation(tmp_path):
    with pytest.raises(ValueError, match="model drift"):
        v34.run_case(tmp_path / "case", tmp_path / "wrong-model", v34.SEEDS[0])
    assert not (tmp_path / "case").exists()


def test_v34_campaign_rejects_existing_immutable_root(tmp_path):
    root = tmp_path / "campaign"
    root.mkdir()
    with pytest.raises(RuntimeError, match="refusing overwrite"):
        v34.run_campaign(root, v34.MODEL_DEFAULT)
