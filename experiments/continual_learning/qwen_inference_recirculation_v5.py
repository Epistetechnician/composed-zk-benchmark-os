#!/usr/bin/env python3
"""Out-of-sample fixed-transfer Qwen recirculation campaign.

V5 changes the evaluation protocol from V4 only by locking the V4 fit-selected
configuration before evaluating a fresh corpus. No configuration search occurs
on the V5 corpus, and the external artifact contains digests rather than raw
corpus text.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from experiments.continual_learning.qwen_inference_recirculation_v1 import (
    DEFAULT_MODEL,
    PARITY_TOLERANCE,
    RecirculationConfig,
    _ensure_external_output,
    _load_runtime,
    digest,
    evaluate_texts,
    model_manifest,
    package_version,
    parity_check,
)
from experiments.continual_learning.qwen_inference_recirculation_v2 import (
    _prose_units,
)

STATE_SLICE = "continual-learning-qwen-inference-recirculation-v5"
CLAIM_CEILING = "LocalDevelopmentQwenInferenceRecirculationFixedTransferFeasibility"
EXTRACTOR = "markdown-prose-first-four-blocks-v1"
MAX_UNITS_PER_FILE = 4
FIT_FILES = (
    "docs/18-phase-h-external-runner-boundary-notes.md",
    "docs/19-phase-i-synthetic-result-import-notes.md",
    "docs/20-phase-j-reviewed-proposal-acceptance-notes.md",
    "docs/21-phase-k-local-soak-runner-telemetry-notes.md",
)
ASSESSMENT_FILES = (
    "docs/22-hyper-sacred-ai-architecture.md",
    "docs/23-claim-envelope-implementation-spec.md",
    "docs/24-hsai-implementation-handoff.md",
    "docs/26-agent-case-evidence-lane-spec.md",
)
TRANSFER_SOURCE = {
    "state_slice": "continual-learning-qwen-inference-recirculation-v4",
    "config_sha256": "5ebd7e72ddf6bff5fff19103172e80f6ac73f3bc7c7da158d1b469c5c2017029",
    "receipt_sha256": "aeec8b111d67e38b25e68b17fda03aae84a37067e4bb3eec1016b272dc4820a9",
}
TRANSFERRED_CONFIG = RecirculationConfig(
    source_layer=12,
    destination_layer=5,
    alpha=0.07,
)


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _source_entry(repo_root: Path, relative_path: str) -> tuple[dict[str, Any], list[str]]:
    path = (repo_root / relative_path).resolve()
    if repo_root.resolve() not in path.parents or not path.is_file() or path.is_symlink():
        raise ValueError(f"invalid corpus source: {relative_path}")
    raw = path.read_bytes()
    units = _prose_units(path)
    if len(units) != MAX_UNITS_PER_FILE:
        raise ValueError(
            f"corpus source has {len(units)} usable units, expected "
            f"{MAX_UNITS_PER_FILE}: {relative_path}"
        )
    return (
        {
            "path": relative_path,
            "byte_len": len(raw),
            "sha256": _sha256_bytes(raw),
            "units": [
                {
                    "ordinal": ordinal,
                    "char_count": len(text),
                    "text_sha256": _sha256_bytes(text.encode("utf-8")),
                }
                for ordinal, text in enumerate(units)
            ],
        },
        units,
    )


def corpus_texts_and_manifest(
    repo_root: Path = REPO_ROOT,
) -> tuple[list[str], list[str], dict[str, Any]]:
    if set(FIT_FILES) & set(ASSESSMENT_FILES):
        raise ValueError("fit and assessment corpus sources overlap")
    fit_entries: list[dict[str, Any]] = []
    fit_texts: list[str] = []
    for relative_path in FIT_FILES:
        entry, units = _source_entry(repo_root, relative_path)
        fit_entries.append(entry)
        fit_texts.extend(units)
    assessment_entries: list[dict[str, Any]] = []
    assessment_texts: list[str] = []
    for relative_path in ASSESSMENT_FILES:
        entry, units = _source_entry(repo_root, relative_path)
        assessment_entries.append(entry)
        assessment_texts.extend(units)
    body = {
        "state_slice": STATE_SLICE,
        "extractor": EXTRACTOR,
        "fit_sources": fit_entries,
        "assessment_sources": assessment_entries,
        "fit_sequence_count": len(fit_texts),
        "assessment_sequence_count": len(assessment_texts),
    }
    return fit_texts, assessment_texts, {
        "manifest": body,
        "manifest_sha256": digest(body),
    }


def _write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def run_campaign(output: Path, model_path: Path = DEFAULT_MODEL) -> dict[str, Any]:
    root = output.resolve()
    model_path = model_path.resolve()
    _ensure_external_output(root)
    if not model_path.is_dir():
        raise FileNotFoundError(f"model path does not exist: {model_path}")

    fit_texts, assessment_texts, corpus = corpus_texts_and_manifest()
    model_files_before = model_manifest(model_path)
    model, tokenizer, tokenizer_policy = _load_runtime(model_path)
    layer_count = len(model.model.layers)
    TRANSFERRED_CONFIG.validate(layer_count)
    parity_checks = [
        parity_check(model, tokenizer, text)
        for text in (*fit_texts, *assessment_texts)
    ]
    if not all(item["passed"] for item in parity_checks):
        raise RuntimeError("zero-alpha parity gate failed")

    fit_baseline = evaluate_texts(model, tokenizer, fit_texts, None)
    fit_transfer = evaluate_texts(model, tokenizer, fit_texts, TRANSFERRED_CONFIG)
    assessment_baseline = evaluate_texts(model, tokenizer, assessment_texts, None)
    assessment_transfer = evaluate_texts(
        model, tokenizer, assessment_texts, TRANSFERRED_CONFIG
    )
    assessment_repeat = evaluate_texts(
        model, tokenizer, assessment_texts, TRANSFERRED_CONFIG
    )
    repeat_delta = max(
        abs(assessment_transfer[key] - assessment_repeat[key])
        for key in ("mean_nll", "perplexity")
    )
    model_files_after = model_manifest(model_path)
    if model_files_after != model_files_before:
        raise RuntimeError("cached model manifest changed during frozen inference")

    config = {
        "state_slice": STATE_SLICE,
        "claim_ceiling": CLAIM_CEILING,
        "model_name": model_path.name,
        "model_path": str(model_path),
        "architecture": "qwen2",
        "layer_count": layer_count,
        "protocol": "v4-fresh-corpus-v5-fixed-transfer",
        "mechanism_source": "arxiv:2608.17981",
        "alpha_semantics": "source_feedback_weight",
        "beta_semantics": "destination_weight_1_minus_alpha",
        "extractor": EXTRACTOR,
        "fit_sequence_count": len(fit_texts),
        "assessment_sequence_count": len(assessment_texts),
        "selection_mode": "locked_transfer_no_v5_search",
        "locked_transfer_config": asdict(TRANSFERRED_CONFIG),
        "transfer_source": TRANSFER_SOURCE,
        "network_access": False,
        "training": False,
        "weights_frozen": True,
        "offline_environment": {
            "HF_HUB_OFFLINE": os.environ.get("HF_HUB_OFFLINE"),
            "TRANSFORMERS_OFFLINE": os.environ.get("TRANSFORMERS_OFFLINE"),
        },
        "runtime": {
            "python": package_version("pip"),
            "mlx": package_version("mlx"),
            "mlx_lm": package_version("mlx-lm"),
        },
        "tokenizer_policy": tokenizer_policy,
        "model_manifest_sha256": model_files_after["manifest_sha256"],
        "corpus_manifest_sha256": corpus["manifest_sha256"],
    }
    config["config_sha256"] = digest(config)
    results = {
        "state_slice": STATE_SLICE,
        "claim_ceiling": CLAIM_CEILING,
        "corpus_manifest_sha256": corpus["manifest_sha256"],
        "locked_transfer_config": asdict(TRANSFERRED_CONFIG),
        "parity": {
            "sequence_count": len(parity_checks),
            "max_abs_logit_delta": max(
                item["max_abs_logit_delta"] for item in parity_checks
            ),
            "tolerance": PARITY_TOLERANCE,
            "all_passed": all(item["passed"] for item in parity_checks),
            "checks": parity_checks,
        },
        "fit_baseline": fit_baseline,
        "fit_transfer_diagnostic": fit_transfer,
        "assessment_baseline": assessment_baseline,
        "assessment_selected": assessment_transfer,
        "assessment_repeat": assessment_repeat,
        "assessment_repeat_max_metric_delta": round(repeat_delta, 12),
        "assessment_nll_delta_selected_minus_baseline": round(
            assessment_transfer["mean_nll"] - assessment_baseline["mean_nll"], 9
        ),
        "assessment_perplexity_delta_selected_minus_baseline": round(
            assessment_transfer["perplexity"] - assessment_baseline["perplexity"], 9
        ),
        "performance_result_is_local_feasibility_only": True,
    }
    results["results_sha256"] = digest(results)
    receipt = {
        "state_slice": STATE_SLICE,
        "claim_ceiling": CLAIM_CEILING,
        "config_sha256": config["config_sha256"],
        "results_sha256": results["results_sha256"],
        "model_manifest_sha256": model_files_after["manifest_sha256"],
        "corpus_manifest_sha256": corpus["manifest_sha256"],
        "transfer_source": TRANSFER_SOURCE,
        "zero_alpha_parity_passed": results["parity"]["all_passed"],
        "network_access": False,
        "training": False,
        "weights_frozen": True,
        "deterministic_repeat_passed": repeat_delta <= PARITY_TOLERANCE,
        "performance_improved_on_assessment": (
            assessment_transfer["mean_nll"] < assessment_baseline["mean_nll"]
        ),
    }
    receipt["receipt_sha256"] = digest(receipt)
    root.mkdir(parents=True)
    _write_json(root / "config.json", config)
    _write_json(root / "corpus-manifest.json", corpus)
    _write_json(root / "results.json", results)
    _write_json(root / "model-manifest.json", model_files_after)
    _write_json(root / "receipt.json", receipt)
    return {"config": config, "corpus": corpus, "results": results, "receipt": receipt}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--model", type=Path, default=DEFAULT_MODEL)
    args = parser.parse_args()
    print(json.dumps(run_campaign(args.output, args.model), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
