#!/usr/bin/env python3
"""Independent validator for the Qwen recirculation alpha-sweep artifact."""

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
    PARITY_TOLERANCE,
    digest,
)
from experiments.continual_learning.validate_qwen_inference_recirculation_v2 import (
    _validate_corpus_manifest,
)
from experiments.continual_learning.qwen_inference_recirculation_v3 import (
    ALPHAS,
    CLAIM_CEILING,
    STATE_SLICE,
    candidate_configs_v3,
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


def validate(root: Path) -> dict[str, Any]:
    config = _read(root, "config.json")
    corpus = _read(root, "corpus-manifest.json")
    results = _read(root, "results.json")
    manifest = _read(root, "model-manifest.json")
    receipt = _read(root, "receipt.json")
    _require_digest(config, "config_sha256", "config")
    _require_digest(results, "results_sha256", "results")
    _require_digest(receipt, "receipt_sha256", "receipt")
    _validate_corpus_manifest(corpus)
    manifest_body = manifest.get("manifest")
    if not isinstance(manifest_body, dict) or manifest.get("manifest_sha256") != digest(manifest_body):
        raise ValueError("model manifest digest mismatch")
    for value in (config, results, receipt):
        if value.get("state_slice") != STATE_SLICE:
            raise ValueError("state slice mismatch")
        if value.get("claim_ceiling") != CLAIM_CEILING:
            raise ValueError("claim ceiling mismatch")
    if config.get("network_access") is not False or config.get("training") is not False:
        raise ValueError("forbidden activity in config")
    if receipt.get("network_access") is not False or receipt.get("training") is not False:
        raise ValueError("forbidden activity in receipt")
    if config.get("weights_frozen") is not True or receipt.get("weights_frozen") is not True:
        raise ValueError("weights are not frozen")
    if config.get("alpha_grid") != list(ALPHAS):
        raise ValueError("alpha grid mismatch")
    expected_grid = [
        {
            "source_layer": item.source_layer,
            "destination_layer": item.destination_layer,
            "alpha": item.alpha,
            "epsilon": item.epsilon,
        }
        for item in candidate_configs_v3(int(config.get("layer_count", 0)))
    ]
    if config.get("candidate_grid") != expected_grid:
        raise ValueError("candidate grid mismatch")
    corpus_digest = corpus["manifest_sha256"]
    if config.get("corpus_manifest_sha256") != corpus_digest:
        raise ValueError("config corpus binding mismatch")
    if results.get("corpus_manifest_sha256") != corpus_digest:
        raise ValueError("results corpus binding mismatch")
    if receipt.get("corpus_manifest_sha256") != corpus_digest:
        raise ValueError("receipt corpus binding mismatch")
    manifest_digest = manifest["manifest_sha256"]
    if config.get("model_manifest_sha256") != manifest_digest:
        raise ValueError("config model manifest binding mismatch")
    if receipt.get("model_manifest_sha256") != manifest_digest:
        raise ValueError("receipt model manifest binding mismatch")
    if receipt.get("config_sha256") != config.get("config_sha256"):
        raise ValueError("receipt config binding mismatch")
    if receipt.get("results_sha256") != results.get("results_sha256"):
        raise ValueError("receipt results binding mismatch")
    parity = results.get("parity")
    if not isinstance(parity, dict) or parity.get("all_passed") is not True:
        raise ValueError("zero-alpha parity gate did not pass")
    if parity.get("sequence_count") != 24:
        raise ValueError("unexpected parity sequence count")
    if float(parity.get("max_abs_logit_delta", float("inf"))) > PARITY_TOLERANCE:
        raise ValueError("zero-alpha parity exceeds tolerance")
    if receipt.get("zero_alpha_parity_passed") is not True:
        raise ValueError("receipt parity binding mismatch")
    if receipt.get("deterministic_repeat_passed") is not True:
        raise ValueError("assessment repeat is not deterministic")
    if config.get("fit_sequence_count") != 12 or config.get("assessment_sequence_count") != 12:
        raise ValueError("unexpected corpus sequence count")
    return {
        "valid": True,
        "state_slice": STATE_SLICE,
        "claim_ceiling": CLAIM_CEILING,
        "fit_sequence_count": 12,
        "assessment_sequence_count": 12,
        "zero_alpha_parity_passed": True,
        "performance_improved_on_assessment": bool(
            receipt.get("performance_improved_on_assessment")
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(validate(args.root.resolve()), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
