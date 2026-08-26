#!/usr/bin/env python3
"""Independent validator for the external Qwen recirculation receipt."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from experiments.continual_learning.qwen_inference_recirculation_v1 import (
    CLAIM_CEILING,
    PARITY_TOLERANCE,
    STATE_SLICE,
    digest,
    model_manifest,
)


def _read(root: Path, name: str) -> dict[str, Any]:
    path = root / name
    if not path.is_file():
        raise ValueError(f"missing artifact: {name}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON: {name}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"artifact must be an object: {name}")
    return value


def _require_digest(value: dict[str, Any], field: str, label: str) -> None:
    actual = value.get(field)
    if not isinstance(actual, str):
        raise ValueError(f"missing {label} digest")
    body = {key: item for key, item in value.items() if key != field}
    if digest(body) != actual:
        raise ValueError(f"{label} digest mismatch")


def validate_model_manifest(value: dict[str, Any], model_path: Path | None = None) -> None:
    manifest = value.get("manifest")
    if not isinstance(manifest, dict) or not isinstance(manifest.get("files"), list):
        raise ValueError("invalid model manifest body")
    if value.get("manifest_sha256") != digest(manifest):
        raise ValueError("model manifest digest mismatch")
    for row in manifest["files"]:
        if not isinstance(row, dict) or not isinstance(row.get("path"), str):
            raise ValueError("invalid model manifest file row")
    if model_path is not None:
        if model_manifest(model_path) != value:
            raise ValueError("model manifest file drift")


def validate(root: Path) -> dict[str, Any]:
    config = _read(root, "config.json")
    results = _read(root, "results.json")
    manifest = _read(root, "model-manifest.json")
    receipt = _read(root, "receipt.json")
    for value, label in (
        (config, "config"),
        (results, "results"),
        (receipt, "receipt"),
    ):
        _require_digest(value, f"{label}_sha256" if label != "receipt" else "receipt_sha256", label)
    for value in (config, results, receipt):
        if value.get("state_slice") != STATE_SLICE:
            raise ValueError("state slice mismatch")
        if value.get("claim_ceiling") != CLAIM_CEILING:
            raise ValueError("claim ceiling mismatch")
    validate_model_manifest(manifest)
    if config.get("network_access") is not False or config.get("training") is not False:
        raise ValueError("forbidden activity in config")
    if receipt.get("network_access") is not False or receipt.get("training") is not False:
        raise ValueError("forbidden activity in receipt")
    if config.get("weights_frozen") is not True or receipt.get("weights_frozen") is not True:
        raise ValueError("weights are not frozen")
    if config.get("model_manifest_sha256") != manifest.get("manifest_sha256"):
        raise ValueError("config model manifest binding mismatch")
    if receipt.get("model_manifest_sha256") != manifest.get("manifest_sha256"):
        raise ValueError("receipt model manifest binding mismatch")
    if receipt.get("config_sha256") != config.get("config_sha256"):
        raise ValueError("receipt config binding mismatch")
    if receipt.get("results_sha256") != results.get("results_sha256"):
        raise ValueError("receipt results binding mismatch")
    parity = results.get("parity")
    if not isinstance(parity, dict) or parity.get("passed") is not True:
        raise ValueError("zero-alpha parity gate did not pass")
    if float(parity.get("max_abs_logit_delta", float("inf"))) > PARITY_TOLERANCE:
        raise ValueError("zero-alpha parity exceeds tolerance")
    if receipt.get("zero_alpha_parity_passed") is not True:
        raise ValueError("receipt parity binding mismatch")
    if receipt.get("deterministic_repeat_passed") is not True:
        raise ValueError("assessment repeat is not deterministic")
    return {
        "valid": True,
        "state_slice": STATE_SLICE,
        "claim_ceiling": CLAIM_CEILING,
        "zero_alpha_parity_passed": True,
        "performance_improved_on_assessment": bool(
            receipt.get("performance_improved_on_assessment")
        ),
        "performance_claim_ceiling": CLAIM_CEILING,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(validate(args.root.resolve()), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
