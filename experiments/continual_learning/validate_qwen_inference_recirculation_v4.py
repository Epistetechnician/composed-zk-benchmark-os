#!/usr/bin/env python3
"""Independent validator for the fresh-corpus Qwen V4 artifact."""

from __future__ import annotations

import argparse
import hashlib
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
from experiments.continual_learning.qwen_inference_recirculation_v2 import (
    _prose_units,
)
from experiments.continual_learning.qwen_inference_recirculation_v3 import (
    ALPHAS,
    candidate_configs_v3,
)
from experiments.continual_learning.qwen_inference_recirculation_v4 import (
    ASSESSMENT_FILES,
    CLAIM_CEILING,
    EXTRACTOR,
    FIT_FILES,
    MAX_UNITS_PER_FILE,
    STATE_SLICE,
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


def _source_entry(repo_root: Path, relative_path: str) -> tuple[dict[str, Any], list[str]]:
    path = (repo_root / relative_path).resolve()
    if repo_root.resolve() not in path.parents or not path.is_file() or path.is_symlink():
        raise ValueError(f"invalid corpus source: {relative_path}")
    raw = path.read_bytes()
    units = _prose_units(path)
    if len(units) != MAX_UNITS_PER_FILE:
        raise ValueError(f"unexpected usable unit count: {relative_path}")
    return (
        {
            "path": relative_path,
            "byte_len": len(raw),
            "sha256": hashlib.sha256(raw).hexdigest(),
            "units": [
                {
                    "ordinal": ordinal,
                    "char_count": len(text),
                    "text_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
                }
                for ordinal, text in enumerate(units)
            ],
        },
        units,
    )


def _expected_corpus(repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    if set(FIT_FILES) & set(ASSESSMENT_FILES):
        raise ValueError("fit and assessment corpus sources overlap")
    fit_sources = []
    fit_count = 0
    for relative_path in FIT_FILES:
        entry, units = _source_entry(repo_root, relative_path)
        fit_sources.append(entry)
        fit_count += len(units)
    assessment_sources = []
    assessment_count = 0
    for relative_path in ASSESSMENT_FILES:
        entry, units = _source_entry(repo_root, relative_path)
        assessment_sources.append(entry)
        assessment_count += len(units)
    body = {
        "state_slice": STATE_SLICE,
        "extractor": EXTRACTOR,
        "fit_sources": fit_sources,
        "assessment_sources": assessment_sources,
        "fit_sequence_count": fit_count,
        "assessment_sequence_count": assessment_count,
    }
    return {"manifest": body, "manifest_sha256": digest(body)}


def validate(root: Path) -> dict[str, Any]:
    config = _read(root, "config.json")
    corpus = _read(root, "corpus-manifest.json")
    results = _read(root, "results.json")
    manifest = _read(root, "model-manifest.json")
    receipt = _read(root, "receipt.json")
    _require_digest(config, "config_sha256", "config")
    _require_digest(results, "results_sha256", "results")
    _require_digest(receipt, "receipt_sha256", "receipt")
    expected_corpus = _expected_corpus()
    if corpus != expected_corpus:
        raise ValueError("corpus manifest does not match current repository")
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
    if config.get("extractor") != EXTRACTOR or config.get("alpha_grid") != list(ALPHAS):
        raise ValueError("protocol grid mismatch")
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
    for value in (config, results, receipt):
        if value.get("corpus_manifest_sha256") != corpus_digest:
            raise ValueError("corpus binding mismatch")
    manifest_digest = manifest["manifest_sha256"]
    if config.get("model_manifest_sha256") != manifest_digest:
        raise ValueError("config model binding mismatch")
    if receipt.get("model_manifest_sha256") != manifest_digest:
        raise ValueError("receipt model binding mismatch")
    if receipt.get("config_sha256") != config.get("config_sha256"):
        raise ValueError("receipt config binding mismatch")
    if receipt.get("results_sha256") != results.get("results_sha256"):
        raise ValueError("receipt results binding mismatch")
    parity = results.get("parity")
    if not isinstance(parity, dict) or parity.get("all_passed") is not True:
        raise ValueError("zero-alpha parity gate did not pass")
    if parity.get("sequence_count") != 32:
        raise ValueError("unexpected parity sequence count")
    if float(parity.get("max_abs_logit_delta", float("inf"))) > PARITY_TOLERANCE:
        raise ValueError("zero-alpha parity exceeds tolerance")
    if receipt.get("zero_alpha_parity_passed") is not True:
        raise ValueError("receipt parity binding mismatch")
    if receipt.get("deterministic_repeat_passed") is not True:
        raise ValueError("assessment repeat is not deterministic")
    if config.get("fit_sequence_count") != 16 or config.get("assessment_sequence_count") != 16:
        raise ValueError("unexpected corpus sequence count")
    return {
        "valid": True,
        "state_slice": STATE_SLICE,
        "claim_ceiling": CLAIM_CEILING,
        "fit_sequence_count": 16,
        "assessment_sequence_count": 16,
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
