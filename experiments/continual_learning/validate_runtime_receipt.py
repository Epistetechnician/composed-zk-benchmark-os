#!/usr/bin/env python3
"""Independent readback validator for V22 runtime receipts."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


STATE_SLICE = "continual-learning-runtime-execution-v22"
CLAIM_CEILING = "LocalDevelopmentRuntimeExecution"
LABELS = {"A", "B", "C", "D"}
TOKENIZER_POLICY_VERSION = "mlx-tokenizer-policy-v1"
FIX_MISTRAL_REGEX_MODEL_TYPES = {"nemotron_h"}


def digest(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def sha256_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def validate_model_manifest(manifest: dict[str, Any], model: Path | None = None) -> None:
    manifest_body = manifest.get("manifest")
    if not isinstance(manifest_body, dict) or not isinstance(manifest_body.get("files"), list):
        raise ValueError("model manifest shape is invalid")
    if manifest.get("manifest_sha256") != digest(manifest_body):
        raise ValueError("model manifest digest mismatch")
    if model is None:
        return
    if not model.is_dir():
        raise ValueError(f"model directory does not exist: {model}")
    if manifest_body.get("model_name") != model.name:
        raise ValueError("model name mismatch")
    expected = {}
    for entry in manifest_body["files"]:
        if not isinstance(entry, dict) or not isinstance(entry.get("path"), str):
            raise ValueError("model manifest file entry is invalid")
        relative = Path(entry["path"])
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError("model manifest contains unsafe path")
        target = model / relative
        if not target.is_file() or target.is_symlink():
            raise ValueError(f"model manifest file is missing or unsafe: {relative}")
        actual = {"byte_len": target.stat().st_size, "sha256": sha256_file(target)}
        if actual != {"byte_len": entry.get("byte_len"), "sha256": entry.get("sha256")}:
            raise ValueError(f"model manifest file drift: {relative}")
        expected[relative.as_posix()] = actual
    actual_paths = {
        path.relative_to(model).as_posix()
        for path in model.rglob("*")
        if path.is_file() and not path.is_symlink()
    }
    if set(expected) != actual_paths:
        raise ValueError("model manifest file set drift")


def validate_tokenizer_policy(policy: Any) -> None:
    if not isinstance(policy, dict) or policy.get("policy_version") != TOKENIZER_POLICY_VERSION:
        raise ValueError("tokenizer policy shape is invalid")
    model_type = policy.get("model_type")
    expected_fix = model_type in FIX_MISTRAL_REGEX_MODEL_TYPES
    if not isinstance(model_type, str) or policy.get("fix_mistral_regex") is not expected_fix:
        raise ValueError("tokenizer policy model binding is invalid")


def expected_tokenizer_policy(model: Path) -> dict[str, Any]:
    config_path = model / "config.json"
    if not config_path.is_file() or config_path.is_symlink():
        raise ValueError("model config is missing or unsafe")
    try:
        config = json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError("model config is unreadable") from exc
    model_type = config.get("model_type") if isinstance(config, dict) else None
    if not isinstance(model_type, str) or not model_type:
        raise ValueError("model config has no declared model_type")
    return {
        "policy_version": TOKENIZER_POLICY_VERSION,
        "model_type": model_type,
        "fix_mistral_regex": model_type in FIX_MISTRAL_REGEX_MODEL_TYPES,
    }


def validate(root: Path, model: Path | None = None) -> dict[str, Any]:
    config = json.loads((root / "config.json").read_text(encoding="utf-8"))
    receipt = json.loads((root / "receipt.json").read_text(encoding="utf-8"))
    manifest = json.loads((root / "model-manifest.json").read_text(encoding="utf-8"))
    validate_model_manifest(manifest, model)
    if config.get("state_slice") != STATE_SLICE or receipt.get("state_slice") != STATE_SLICE:
        raise ValueError("state slice mismatch")
    if config.get("claim_ceiling") != CLAIM_CEILING or receipt.get("claim_ceiling") != CLAIM_CEILING:
        raise ValueError("claim ceiling mismatch")
    if config.get("network_access") is not False or config.get("training") is not False:
        raise ValueError("runtime config permits forbidden activity")
    if config.get("offline_environment") != {
        "HF_HUB_OFFLINE": "1",
        "TRANSFORMERS_OFFLINE": "1",
    }:
        raise ValueError("runtime config does not enforce offline model hubs")
    if receipt.get("network_access") is not False or receipt.get("training") is not False:
        raise ValueError("runtime receipt permits forbidden activity")
    if receipt.get("model_loaded") is not True or receipt.get("inference_executed") is not True:
        raise ValueError("runtime execution was not recorded")
    config_policy = config.get("tokenizer_policy")
    receipt_policy = receipt.get("tokenizer_policy")
    if config_policy is None and receipt_policy is None:
        tokenizer_policy = None
    else:
        validate_tokenizer_policy(config_policy)
        if receipt_policy != config_policy:
            raise ValueError("tokenizer policy receipt binding mismatch")
        tokenizer_policy = config_policy
    if model is not None and tokenizer_policy is not None:
        if tokenizer_policy != expected_tokenizer_policy(model):
            raise ValueError("tokenizer policy does not match model config")
    if set(receipt.get("candidate_labels", [])) != LABELS:
        raise ValueError("candidate label panel drift")
    if receipt.get("prediction") not in LABELS:
        raise ValueError("prediction is outside the candidate panel")
    if config.get("model_manifest_sha256") != manifest.get("manifest_sha256"):
        raise ValueError("model manifest binding mismatch")
    if receipt.get("model_manifest_sha256") != manifest.get("manifest_sha256"):
        raise ValueError("receipt manifest binding mismatch")
    unsigned_config = {key: value for key, value in config.items() if key != "config_sha256"}
    if config.get("config_sha256") != digest(unsigned_config):
        raise ValueError("config digest mismatch")
    unsigned_receipt = {key: value for key, value in receipt.items() if key != "receipt_sha256"}
    if receipt.get("receipt_sha256") != digest(unsigned_receipt):
        raise ValueError("receipt digest mismatch")
    if not isinstance(receipt.get("elapsed_ms"), (int, float)) or receipt["elapsed_ms"] < 0:
        raise ValueError("elapsed time is invalid")
    return {
        "valid": True,
        "state_slice": STATE_SLICE,
        "claim_ceiling": CLAIM_CEILING,
        "manifest_sha256": manifest["manifest_sha256"],
        "network_access": False,
        "training": False,
        "tokenizer_policy": tokenizer_policy,
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
