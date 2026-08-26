import json
import sys
from pathlib import Path

import pytest

from experiments.continual_learning.mlx_tokenizer_policy import (
    tokenizer_config_from_policy,
    tokenizer_policy_for_model,
)
from experiments.continual_learning.model_benchmark import (
    safe_training_command,
    training_command,
)
from experiments.continual_learning.safe_mlx_lora import require_offline_environment


def model_dir(tmp_path: Path, model_type: str) -> Path:
    model = tmp_path / model_type
    model.mkdir()
    (model / "config.json").write_text(
        json.dumps({"model_type": model_type}), encoding="utf-8"
    )
    return model


def test_nemotron_policy_enables_mistral_regex_fix(tmp_path):
    policy = tokenizer_policy_for_model(model_dir(tmp_path, "nemotron_h"))
    assert policy == {
        "policy_version": "mlx-tokenizer-policy-v1",
        "model_type": "nemotron_h",
        "fix_mistral_regex": True,
    }
    assert tokenizer_config_from_policy(policy) == {"fix_mistral_regex": True}


def test_qwen_policy_preserves_default_tokenizer(tmp_path):
    policy = tokenizer_policy_for_model(model_dir(tmp_path, "qwen2"))
    assert policy["fix_mistral_regex"] is False
    assert tokenizer_config_from_policy(policy) == {}


def test_policy_rejects_missing_or_symlinked_config(tmp_path):
    missing = tmp_path / "missing"
    missing.mkdir()
    with pytest.raises(ValueError, match="missing or unsafe"):
        tokenizer_policy_for_model(missing)

    target = tmp_path / "target.json"
    target.write_text(json.dumps({"model_type": "nemotron_h"}), encoding="utf-8")
    linked = tmp_path / "linked"
    linked.mkdir()
    (linked / "config.json").symlink_to(target)
    with pytest.raises(ValueError, match="missing or unsafe"):
        tokenizer_policy_for_model(linked)


def test_safe_training_command_is_explicit_and_preserves_arguments(tmp_path):
    model = tmp_path / "model"
    dataset = tmp_path / "data"
    adapter = tmp_path / "adapter"
    standard = training_command(model, dataset, adapter, 7, 11, None)
    safe = safe_training_command(model, dataset, adapter, 7, 11, None)
    assert standard[:4] == [sys.executable, "-m", "mlx_lm", "lora"]
    assert safe[:3] == [
        sys.executable,
        "-m",
        "experiments.continual_learning.safe_mlx_lora",
    ]
    assert safe[3:] == standard[4:]


def test_safe_training_requires_both_offline_guards():
    require_offline_environment(
        {"HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1"}
    )
    with pytest.raises(RuntimeError, match="requires offline"):
        require_offline_environment(
            {"HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "0"}
        )
