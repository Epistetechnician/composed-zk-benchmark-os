#!/usr/bin/env python3
"""Qwen recirculation alpha-sweep successor campaign.

V3 changes exactly one experimental factor from V2: it expands the fixed
fit-only alpha grid to the four values used in the source paper. The model,
recirculation implementation, source/destination pairs, corpus, and
assessment lock remain unchanged.
"""

from __future__ import annotations

import argparse
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
    candidate_configs,
    digest,
    evaluate_texts,
    model_manifest,
    package_version,
    parity_check,
)
from experiments.continual_learning.qwen_inference_recirculation_v2 import (
    EXTRACTOR as CORPUS_EXTRACTOR,
    corpus_texts_and_manifest,
)

STATE_SLICE = "continual-learning-qwen-inference-recirculation-v3"
CLAIM_CEILING = "LocalDevelopmentQwenInferenceRecirculationAlphaSweepFeasibility"
ALPHAS = (0.04, 0.07, 0.10, 0.16)


def candidate_configs_v3(layer_count: int) -> tuple[RecirculationConfig, ...]:
    pairs = candidate_configs(layer_count)
    configs = tuple(
        RecirculationConfig(
            source_layer=pair.source_layer,
            destination_layer=pair.destination_layer,
            alpha=alpha,
            epsilon=pair.epsilon,
        )
        for pair in pairs
        for alpha in ALPHAS
    )
    for config in configs:
        config.validate(layer_count)
    return configs


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
    grid = candidate_configs_v3(layer_count)
    parity_checks = [
        parity_check(model, tokenizer, text)
        for text in (*fit_texts, *assessment_texts)
    ]
    if not all(item["passed"] for item in parity_checks):
        raise RuntimeError("zero-alpha parity gate failed")

    fit_baseline = evaluate_texts(model, tokenizer, fit_texts, None)
    fit_candidates = []
    for config in grid:
        fit_candidates.append(
            {
                "config": asdict(config),
                "metrics": evaluate_texts(model, tokenizer, fit_texts, config),
            }
        )
    selected = min(fit_candidates, key=lambda item: item["metrics"]["mean_nll"])
    selected_config = RecirculationConfig(**selected["config"])
    assessment_baseline = evaluate_texts(model, tokenizer, assessment_texts, None)
    assessment_selected = evaluate_texts(
        model, tokenizer, assessment_texts, selected_config
    )
    assessment_repeat = evaluate_texts(
        model, tokenizer, assessment_texts, selected_config
    )
    repeat_delta = max(
        abs(assessment_selected[key] - assessment_repeat[key])
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
        "protocol": "v2-corpus-v3-paper-alpha-sweep",
        "mechanism_source": "arxiv:2608.17981",
        "alpha_semantics": "source_feedback_weight",
        "beta_semantics": "destination_weight_1_minus_alpha",
        "extractor": CORPUS_EXTRACTOR,
        "fit_sequence_count": len(fit_texts),
        "assessment_sequence_count": len(assessment_texts),
        "alpha_grid": list(ALPHAS),
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
        "candidate_grid": [asdict(item) for item in grid],
    }
    config["config_sha256"] = digest(config)
    results = {
        "state_slice": STATE_SLICE,
        "claim_ceiling": CLAIM_CEILING,
        "corpus_manifest_sha256": corpus["manifest_sha256"],
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
        "fit_candidates": fit_candidates,
        "selected_fit_config": asdict(selected_config),
        "assessment_baseline": assessment_baseline,
        "assessment_selected": assessment_selected,
        "assessment_repeat": assessment_repeat,
        "assessment_repeat_max_metric_delta": round(repeat_delta, 12),
        "assessment_nll_delta_selected_minus_baseline": round(
            assessment_selected["mean_nll"] - assessment_baseline["mean_nll"], 9
        ),
        "assessment_perplexity_delta_selected_minus_baseline": round(
            assessment_selected["perplexity"] - assessment_baseline["perplexity"], 9
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
        "zero_alpha_parity_passed": results["parity"]["all_passed"],
        "network_access": False,
        "training": False,
        "weights_frozen": True,
        "deterministic_repeat_passed": repeat_delta <= PARITY_TOLERANCE,
        "performance_improved_on_assessment": (
            assessment_selected["mean_nll"] < assessment_baseline["mean_nll"]
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
