import json

import pytest

from experiments.continual_learning.validate_runtime_receipt import digest, sha256_file
from experiments.continual_learning.validate_training_seam_receipt import validate


def valid_training_receipt(root):
    (root / "adapter").mkdir()
    (root / "data").mkdir()
    adapter = root / "adapter" / "adapters.safetensors"
    adapter.write_bytes(b"synthetic-adapter")
    log = root / "training.log"
    log.write_text("synthetic training log\n", encoding="utf-8")
    for name in ("train.jsonl", "valid.jsonl", "test.jsonl"):
        (root / "data" / name).write_text('{"prompt":"p","completion":" A"}\n', encoding="utf-8")
    policy = {
        "policy_version": "mlx-tokenizer-policy-v1",
        "model_type": "nemotron_h",
        "fix_mistral_regex": True,
    }
    config = {
        "state_slice": "continual-learning-runtime-execution-v22",
        "claim_ceiling": "LocalDevelopmentRuntimeExecution",
        "protocol": "mlx-tokenizer-policy-training-smoke-v1",
        "model_name": "synthetic-model",
        "model_config_sha256": "a" * 64,
        "seed": 20260825,
        "iters": 2,
        "trainable_layers": 1,
        "dataset_rows": 4,
        "network_access": False,
        "training": True,
        "retention_executed": False,
        "offline_environment": {"HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1"},
        "tokenizer_policy": policy,
        "trainer_entrypoint": "experiments.continual_learning.safe_mlx_lora",
    }
    config["config_sha256"] = digest(config)
    receipt = {
        "state_slice": config["state_slice"],
        "claim_ceiling": config["claim_ceiling"],
        "protocol": config["protocol"],
        "model_name": config["model_name"],
        "model_config_sha256": config["model_config_sha256"],
        "training": True,
        "inference_executed": True,
        "network_access": False,
        "retention_executed": False,
        "tokenizer_policy": policy,
        "candidate_labels": ["A", "B", "C", "D"],
        "prediction": "A",
        "adapter_sha256": sha256_file(adapter),
        "training_log_sha256": sha256_file(log),
        "dataset_sha256": {
            f"data/{name}": sha256_file(root / "data" / name)
            for name in ("train.jsonl", "valid.jsonl", "test.jsonl")
        },
        "command_sha256": "b" * 64,
    }
    receipt["receipt_sha256"] = digest(receipt)
    (root / "config.json").write_text(json.dumps(config), encoding="utf-8")
    (root / "receipt.json").write_text(json.dumps(receipt), encoding="utf-8")


def test_training_receipt_is_independently_validated(tmp_path):
    valid_training_receipt(tmp_path)
    result = validate(tmp_path)
    assert result["valid"] is True
    assert result["network_access"] is False
    assert result["retention_executed"] is False
    assert result["tokenizer_policy"]["fix_mistral_regex"] is True


def test_training_receipt_rejects_adapter_drift(tmp_path):
    valid_training_receipt(tmp_path)
    (tmp_path / "adapter" / "adapters.safetensors").write_bytes(b"drift")
    with pytest.raises(ValueError, match="adapter digest"):
        validate(tmp_path)


def test_training_receipt_rejects_policy_drift(tmp_path):
    valid_training_receipt(tmp_path)
    config_path = tmp_path / "config.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    config["tokenizer_policy"]["fix_mistral_regex"] = False
    config["config_sha256"] = digest(
        {key: value for key, value in config.items() if key != "config_sha256"}
    )
    config_path.write_text(json.dumps(config), encoding="utf-8")
    with pytest.raises(ValueError, match="tokenizer policy"):
        validate(tmp_path)
