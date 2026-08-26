from __future__ import annotations

import pytest

from experiments.continual_learning import nemotron_target_acquisition_recovery_v42 as v42
from experiments.continual_learning.validate_nemotron_target_acquisition_recovery_v42 import (
    _validate_metric,
)


def _metric(accuracy: float, *, constant: bool = False) -> dict:
    return {"accuracy": accuracy, "constant_output": constant}


def test_v42_contract_is_target_only_and_retention_closed():
    assert v42.SEED == 20260825
    assert v42.ITERS == 160
    assert v42.NUM_LAYERS == 8
    assert v42.UPDATE_BUDGET == 32
    assert v42.TARGET_TASK_ID == 0
    assert v42.TARGET_FLOOR == 0.75
    assert v42.TOKENIZER_POLICY["fix_mistral_regex"] is True
    assert '"event": "mlx_tokenizer_policy"' not in "Starting training..., iters: 160"


def test_v42_eligibility_requires_all_four_frozen_gates():
    gates = v42.eligibility_gates(_metric(0.25, constant=True), _metric(0.875), _metric(0.75))
    assert gates == {
        "target_train_above_no_update": True,
        "target_train_floor": True,
        "target_heldout_floor": True,
        "target_not_constant_output": True,
    }
    assert all(gates.values())
    failed = v42.eligibility_gates(_metric(0.25, constant=True), _metric(0.25, constant=True), _metric(0.25, constant=True))
    assert not all(failed.values())


def test_v42_prompt_matches_frozen_route_boundary():
    prompt = v42.expected_prompt({"task_token": "T0", "residue": 3})
    assert prompt == (
        "Answer with exactly one letter: A, B, C, or D.\n"
        "Task token: T0.\n"
        "Derived residue: 3.\n"
        "Use the task's residue-to-option codebook and return only the option letter.\n"
        "Task route binding: T0.\nAnswer:"
    )


def test_v42_recovery_refuses_repository_or_existing_output(tmp_path):
    with pytest.raises(ValueError, match="outside the repository"):
        v42._ensure_external_new_root(v42.REPO_ROOT / "forbidden")
    existing = tmp_path / "existing"
    existing.mkdir()
    with pytest.raises(FileExistsError, match="refusing overwrite"):
        v42._ensure_external_new_root(existing)


def test_v42_independent_metric_validator_rejects_score_tamper():
    facts = [{"fact_id": "F0", "label": "A"}, {"fact_id": "F1", "label": "B"}]
    metric = {
        "correct": 1,
        "n": 2,
        "accuracy": 0.75,
        "constant_output": False,
        "tokenizer_policy": v42.TOKENIZER_POLICY,
        "rows": [
            {"fact_id": "F0", "expected": "A", "observed": "A", "correct": True},
            {"fact_id": "F1", "expected": "B", "observed": "A", "correct": False},
        ],
    }
    with pytest.raises(ValueError, match="score drift"):
        _validate_metric(metric, facts)
