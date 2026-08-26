import json

import pytest

from experiments.continual_learning.validate_runtime_receipt import (
    CLAIM_CEILING,
    STATE_SLICE,
    digest,
    validate,
    validate_model_manifest,
)


def valid_receipt(root):
    manifest_body = {"model_name": "synthetic-model", "files": []}
    manifest = {"manifest": manifest_body, "manifest_sha256": digest(manifest_body)}
    config = {
        "state_slice": STATE_SLICE,
        "claim_ceiling": CLAIM_CEILING,
        "model_name": "synthetic-model",
        "seed": 20260819,
        "probe": "single-token-four-label-logit-selection-v1",
        "network_access": False,
        "training": False,
        "offline_environment": {"HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1"},
        "runtime": {"python": "available", "mlx": "synthetic", "mlx_lm": "synthetic"},
        "tokenizer_policy": {
            "policy_version": "mlx-tokenizer-policy-v1",
            "model_type": "qwen2",
            "fix_mistral_regex": False,
        },
        "model_manifest_sha256": manifest["manifest_sha256"],
    }
    config["config_sha256"] = digest(config)
    receipt = {
        "state_slice": STATE_SLICE,
        "claim_ceiling": CLAIM_CEILING,
        "model_loaded": True,
        "inference_executed": True,
        "training": False,
        "network_access": False,
        "tokenizer_policy": config["tokenizer_policy"],
        "candidate_labels": ["A", "B", "C", "D"],
        "prediction": "A",
        "prompt_sha256": "a" * 64,
        "fact_id": "F00000",
        "elapsed_ms": 1.0,
        "model_manifest_sha256": manifest["manifest_sha256"],
    }
    receipt["receipt_sha256"] = digest(receipt)
    (root / "config.json").write_text(json.dumps(config), encoding="utf-8")
    (root / "receipt.json").write_text(json.dumps(receipt), encoding="utf-8")
    (root / "model-manifest.json").write_text(json.dumps(manifest), encoding="utf-8")


def test_runtime_receipt_is_independently_validated(tmp_path):
    valid_receipt(tmp_path)
    result = validate(tmp_path)
    assert result["valid"] is True
    assert result["network_access"] is False
    assert result["training"] is False
    assert result["tokenizer_policy"]["model_type"] == "qwen2"


@pytest.mark.parametrize("field,value", [("network_access", True), ("training", True)])
def test_runtime_receipt_rejects_forbidden_activity(tmp_path, field, value):
    valid_receipt(tmp_path)
    path = tmp_path / "receipt.json"
    receipt = json.loads(path.read_text(encoding="utf-8"))
    receipt[field] = value
    receipt["receipt_sha256"] = digest({key: item for key, item in receipt.items() if key != "receipt_sha256"})
    path.write_text(json.dumps(receipt), encoding="utf-8")
    with pytest.raises(ValueError, match="forbidden activity"):
        validate(tmp_path)


def test_runtime_receipt_rejects_digest_drift(tmp_path):
    valid_receipt(tmp_path)
    path = tmp_path / "receipt.json"
    receipt = json.loads(path.read_text(encoding="utf-8"))
    receipt["prediction"] = "B"
    path.write_text(json.dumps(receipt), encoding="utf-8")
    with pytest.raises(ValueError, match="receipt digest"):
        validate(tmp_path)


def test_model_manifest_rejects_resealed_digest(tmp_path):
    manifest_body = {"model_name": "synthetic-model", "files": []}
    manifest = {"manifest": manifest_body, "manifest_sha256": "0" * 64}
    with pytest.raises(ValueError, match="model manifest digest"):
        validate_model_manifest(manifest)


def test_model_manifest_rejects_checkpoint_file_drift(tmp_path):
    model = tmp_path / "synthetic-model"
    model.mkdir()
    weight = model / "weights.bin"
    weight.write_bytes(b"original")
    manifest_body = {
        "model_name": model.name,
        "files": [{"path": "weights.bin", "byte_len": 8, "sha256": "0" * 64}],
    }
    manifest = {"manifest": manifest_body, "manifest_sha256": digest(manifest_body)}
    with pytest.raises(ValueError, match="model manifest file drift"):
        validate_model_manifest(manifest, model)


def test_runtime_receipt_rejects_tokenizer_policy_drift(tmp_path):
    valid_receipt(tmp_path)
    path = tmp_path / "receipt.json"
    receipt = json.loads(path.read_text(encoding="utf-8"))
    receipt["tokenizer_policy"]["fix_mistral_regex"] = True
    receipt["receipt_sha256"] = digest(
        {key: item for key, item in receipt.items() if key != "receipt_sha256"}
    )
    path.write_text(json.dumps(receipt), encoding="utf-8")
    with pytest.raises(ValueError, match="tokenizer policy receipt binding"):
        validate(tmp_path)
