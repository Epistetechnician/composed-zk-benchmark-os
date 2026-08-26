#!/usr/bin/env python3
"""Independent readback validator for the V22 bounded LoRA smoke."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from experiments.continual_learning.validate_runtime_receipt import (
    digest,
    expected_tokenizer_policy,
    sha256_file,
    validate_tokenizer_policy,
)


STATE_SLICE = "continual-learning-runtime-execution-v22"
CLAIM_CEILING = "LocalDevelopmentRuntimeExecution"
PROTOCOL = "mlx-tokenizer-policy-training-smoke-v1"
LABELS = {"A", "B", "C", "D"}


def validate(root: Path, model: Path | None = None) -> dict[str, Any]:
    config = json.loads((root / "config.json").read_text(encoding="utf-8"))
    receipt = json.loads((root / "receipt.json").read_text(encoding="utf-8"))
    for payload in (config, receipt):
        if payload.get("state_slice") != STATE_SLICE:
            raise ValueError("state slice mismatch")
        if payload.get("claim_ceiling") != CLAIM_CEILING:
            raise ValueError("claim ceiling mismatch")
        if payload.get("protocol") != PROTOCOL:
            raise ValueError("training smoke protocol mismatch")
    if config.get("network_access") is not False or config.get("training") is not True:
        raise ValueError("training smoke config activity boundary drift")
    if config.get("retention_executed") is not False:
        raise ValueError("training smoke config permits retention")
    if config.get("offline_environment") != {
        "HF_HUB_OFFLINE": "1",
        "TRANSFORMERS_OFFLINE": "1",
    }:
        raise ValueError("training smoke does not enforce offline model hubs")
    if config.get("iters") != 2 or config.get("trainable_layers") != 1:
        raise ValueError("training smoke budget drift")
    if config.get("dataset_rows") != 4:
        raise ValueError("training smoke dataset budget drift")
    if config.get("trainer_entrypoint") != "experiments.continual_learning.safe_mlx_lora":
        raise ValueError("unsafe trainer entrypoint")
    validate_tokenizer_policy(config.get("tokenizer_policy"))
    if receipt.get("tokenizer_policy") != config.get("tokenizer_policy"):
        raise ValueError("training tokenizer policy receipt binding mismatch")
    if receipt.get("network_access") is not False or receipt.get("training") is not True:
        raise ValueError("training receipt activity boundary drift")
    if receipt.get("retention_executed") is not False:
        raise ValueError("training receipt permits retention")
    if receipt.get("inference_executed") is not True:
        raise ValueError("adapter readout was not recorded")
    if set(receipt.get("candidate_labels", [])) != LABELS or receipt.get("prediction") not in LABELS:
        raise ValueError("training smoke label panel drift")

    unsigned_config = {key: value for key, value in config.items() if key != "config_sha256"}
    if config.get("config_sha256") != digest(unsigned_config):
        raise ValueError("training config digest mismatch")
    unsigned_receipt = {key: value for key, value in receipt.items() if key != "receipt_sha256"}
    if receipt.get("receipt_sha256") != digest(unsigned_receipt):
        raise ValueError("training receipt digest mismatch")

    adapter = root / "adapter" / "adapters.safetensors"
    log = root / "training.log"
    if not adapter.is_file() or receipt.get("adapter_sha256") != sha256_file(adapter):
        raise ValueError("training adapter digest mismatch")
    if not log.is_file() or receipt.get("training_log_sha256") != sha256_file(log):
        raise ValueError("training log digest mismatch")
    expected_dataset = {
        f"data/{name}": sha256_file(root / "data" / name)
        for name in ("train.jsonl", "valid.jsonl", "test.jsonl")
    }
    if receipt.get("dataset_sha256") != expected_dataset:
        raise ValueError("training dataset digest mismatch")

    if model is not None:
        if not model.is_dir() or model.name != config.get("model_name"):
            raise ValueError("training model binding mismatch")
        if receipt.get("model_name") != model.name:
            raise ValueError("training receipt model binding mismatch")
        model_config_sha256 = sha256_file(model / "config.json")
        if config.get("model_config_sha256") != model_config_sha256:
            raise ValueError("training model config digest mismatch")
        if receipt.get("model_config_sha256") != model_config_sha256:
            raise ValueError("training receipt model config digest mismatch")
        if config.get("tokenizer_policy") != expected_tokenizer_policy(model):
            raise ValueError("training tokenizer policy does not match model config")
    return {
        "valid": True,
        "state_slice": STATE_SLICE,
        "claim_ceiling": CLAIM_CEILING,
        "network_access": False,
        "training": True,
        "retention_executed": False,
        "tokenizer_policy": config["tokenizer_policy"],
        "adapter_sha256": receipt["adapter_sha256"],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("--model", type=Path)
    args = parser.parse_args()
    try:
        model = args.model.resolve() if args.model else None
        print(json.dumps(validate(args.root.resolve(), model), sort_keys=True))
    except Exception as exc:
        print(json.dumps({"valid": False, "reason": str(exc)}, sort_keys=True))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
