#!/usr/bin/env python3
"""Bounded, offline Qwen inference-time recirculation feasibility campaign.

This module implements the one-additional-iteration mechanism described by
arXiv:2608.17981: after a token is processed through a deep source layer, its
residual stream is normalized and mixed into a shallower destination layer on
the next token step. The checkpoint remains frozen.

The implementation deliberately exposes a small, testable seam. It does not
claim a paper replication: the cached model is Qwen2.5-0.5B-Instruct, while
the paper reports Gemma3 results and uses larger external corpora.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import sys
from dataclasses import asdict, dataclass
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any, Iterable, Sequence

STATE_SLICE = "continual-learning-qwen-inference-recirculation-v1"
CLAIM_CEILING = "LocalDevelopmentQwenInferenceRecirculationFeasibility"
DEFAULT_MODEL = Path(
    "/Users/shaanp/.lmstudio/models/mlx-community/Qwen2.5-0.5B-Instruct-4bit"
)
REPO_ROOT = Path(__file__).resolve().parents[2]
PARITY_TOLERANCE = 1e-5
EPSILON = 1e-6
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# Repository-owned, fixed text only. These are used to exercise the sequential
# teacher-forcing seam; they are not a benchmark corpus or accepted evidence.
FIT_TEXTS = (
    "A state tracker updates a belief after each observation. The next decision uses the updated belief rather than the stale one.",
    "A transformer processes a sequence with attention and residual streams. A recurrent update adds a second path for information across input steps.",
    "When a river bank is discussed, the surrounding words disambiguate the meaning of bank. Later predictions should preserve that context.",
    "A frozen checkpoint can be evaluated with a changed inference schedule. Any improvement must be measured on text held out before the schedule is selected.",
)
ASSESSMENT_TEXTS = (
    "The memory state is revised when a new fact arrives, and the revised state controls the following prediction.",
    "Deep residual features can be made available to a shallow layer by a small normalized mixture on the next token step.",
    "The financial bank differs from the river bank, so a language model must use the local context to resolve the ambiguous word.",
    "An inference-only architectural change leaves learned weights untouched, but it may still change logits and perplexity.",
)


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


def model_manifest(model_path: Path) -> dict[str, Any]:
    files = []
    for path in sorted(
        path for path in model_path.rglob("*") if path.is_file() and not path.is_symlink()
    ):
        files.append(
            {
                "path": path.relative_to(model_path).as_posix(),
                "byte_len": path.stat().st_size,
                "sha256": sha256_file(path),
            }
        )
    if not files:
        raise ValueError(f"cached model directory has no regular files: {model_path}")
    body = {"model_name": model_path.name, "files": files}
    return {"manifest": body, "manifest_sha256": digest(body)}


def package_version(name: str) -> str:
    try:
        return version(name)
    except PackageNotFoundError:
        return "unavailable"


@dataclass(frozen=True)
class RecirculationConfig:
    source_layer: int
    destination_layer: int
    alpha: float
    epsilon: float = EPSILON

    def validate(self, layer_count: int) -> None:
        if layer_count < 2:
            raise ValueError("recirculation requires at least two layers")
        if not 0 <= self.destination_layer < self.source_layer < layer_count:
            raise ValueError(
                "recirculation requires 0 <= destination < source < layer_count"
            )
        if not math.isfinite(self.alpha) or not 0 <= self.alpha <= 1:
            raise ValueError("alpha must be finite and within [0, 1]")
        if not math.isfinite(self.epsilon) or self.epsilon <= 0:
            raise ValueError("epsilon must be finite and positive")


def _normalized_source(mx: Any, source: Any, destination: Any, epsilon: float) -> Any:
    source_norm = mx.sqrt(mx.sum(mx.square(source), axis=-1, keepdims=True))
    destination_norm = mx.sqrt(mx.sum(mx.square(destination), axis=-1, keepdims=True))
    scale = destination_norm / mx.maximum(source_norm, mx.array(epsilon))
    return source * scale


def mix_residual(mx: Any, source: Any, destination: Any, alpha: float, epsilon: float) -> Any:
    """Return beta*destination + alpha*normalized(source), beta=1-alpha."""

    return (1.0 - alpha) * destination + alpha * _normalized_source(
        mx, source, destination, epsilon
    )


def candidate_configs(layer_count: int) -> tuple[RecirculationConfig, ...]:
    """Return a frozen, small Qwen-local fit grid with deep-to-shallow pairs."""

    pairs = ((7, 2), (9, 3), (11, 4), (12, 5))
    configs = tuple(
        RecirculationConfig(source_layer=source, destination_layer=destination, alpha=0.10)
        for source, destination in pairs
        if source < layer_count
    )
    if not configs:
        raise ValueError(f"no candidate source/destination pair for {layer_count} layers")
    for config in configs:
        config.validate(layer_count)
    return configs


def _load_runtime(model_path: Path) -> tuple[Any, Any, dict[str, Any]]:
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    from mlx_lm import load

    from experiments.continual_learning.mlx_tokenizer_policy import (
        tokenizer_config_from_policy,
        tokenizer_policy_for_model,
    )

    policy = tokenizer_policy_for_model(model_path)
    model, tokenizer = load(
        str(model_path),
        tokenizer_config=tokenizer_config_from_policy(policy) or None,
    )
    return model, tokenizer, policy


def _one_token_native(model: Any, mx: Any, token_id: int, cache_state: list[Any]) -> Any:
    return model(mx.array([[int(token_id)]], dtype=mx.int32), cache=cache_state)


def _one_token_recirculated(
    model: Any,
    mx: Any,
    qwen2: Any,
    cache_state: list[Any],
    token_id: int,
    config: RecirculationConfig,
    previous_source: Any | None,
) -> tuple[Any, Any]:
    inner = model.model
    hidden = inner.embed_tokens(mx.array([[int(token_id)]], dtype=mx.int32))
    mask = qwen2.create_attention_mask(hidden, cache_state[0])
    current_source = None
    for index, (layer, layer_cache) in enumerate(zip(inner.layers, cache_state)):
        hidden = layer(hidden, mask, layer_cache)
        if (
            index == config.destination_layer
            and previous_source is not None
            and config.alpha != 0
        ):
            hidden = mix_residual(
                mx,
                previous_source,
                hidden,
                config.alpha,
                config.epsilon,
            )
        if index == config.source_layer:
            current_source = hidden
    if current_source is None:
        raise RuntimeError("source activation was not captured")
    hidden = inner.norm(hidden)
    if model.args.tie_word_embeddings:
        logits = inner.embed_tokens.as_linear(hidden)
    else:
        logits = model.lm_head(hidden)
    return logits, current_source


def logits_for_tokens(
    model: Any,
    token_ids: Sequence[int],
    config: RecirculationConfig | None = None,
) -> list[Any]:
    """Compute one logit vector per input token using a fresh KV cache."""

    import importlib

    import mlx.core as mx

    cache_module = importlib.import_module("mlx_lm.models.cache")
    qwen2 = importlib.import_module("mlx_lm.models.qwen2")
    inner = model.model
    layer_count = len(inner.layers)
    if config is not None:
        config.validate(layer_count)
    cache_state = cache_module.make_prompt_cache(inner)
    outputs = []
    previous_source = None
    for token_id in token_ids:
        if config is None:
            logits = _one_token_native(model, mx, int(token_id), cache_state)
        else:
            logits, previous_source = _one_token_recirculated(
                model,
                mx,
                qwen2,
                cache_state,
                int(token_id),
                config,
                previous_source,
            )
        mx.eval(logits)
        outputs.append(logits[0, -1, :])
        if config is None:
            previous_source = None
    mx.eval(*outputs)
    return outputs


def _nll(logits: Sequence[Any], token_ids: Sequence[int], mx: Any) -> tuple[float, int]:
    if len(token_ids) < 2:
        return 0.0, 0
    total = 0.0
    count = 0
    for index, target in enumerate(token_ids[1:]):
        row = logits[index]
        log_probs = row - mx.logsumexp(row)
        total += -float(log_probs[int(target)])
        count += 1
    return total, count


def evaluate_texts(
    model: Any,
    tokenizer: Any,
    texts: Iterable[str],
    config: RecirculationConfig | None,
) -> dict[str, Any]:
    import mlx.core as mx

    total_nll = 0.0
    total_tokens = 0
    rows = []
    for text in texts:
        token_ids = tokenizer.encode(text, add_special_tokens=False)
        logits = logits_for_tokens(model, token_ids, config)
        nll, token_count = _nll(logits, token_ids, mx)
        total_nll += nll
        total_tokens += token_count
        rows.append(
            {
                "text_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
                "token_count": len(token_ids),
                "target_count": token_count,
                "nll": round(nll, 9),
            }
        )
    mean_nll = total_nll / total_tokens if total_tokens else float("nan")
    return {
        "mean_nll": round(mean_nll, 9),
        "perplexity": round(math.exp(mean_nll), 9) if math.isfinite(mean_nll) else None,
        "target_tokens": total_tokens,
        "rows": rows,
    }


def parity_check(model: Any, tokenizer: Any, text: str) -> dict[str, Any]:
    import mlx.core as mx

    token_ids = tokenizer.encode(text, add_special_tokens=False)
    native = logits_for_tokens(model, token_ids, None)
    zero_alpha = logits_for_tokens(
        model,
        token_ids,
        RecirculationConfig(source_layer=7, destination_layer=2, alpha=0.0),
    )
    deltas = [float(mx.max(mx.abs(a - b))) for a, b in zip(native, zero_alpha)]
    max_delta = max(deltas, default=0.0)
    return {
        "token_count": len(token_ids),
        "max_abs_logit_delta": max_delta,
        "tolerance": PARITY_TOLERANCE,
        "passed": max_delta <= PARITY_TOLERANCE,
    }


def _write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _ensure_external_output(root: Path) -> None:
    if root == REPO_ROOT or REPO_ROOT in root.parents:
        raise ValueError("recirculation output must be outside the repository")
    if root.exists():
        raise FileExistsError(f"refusing overwrite of immutable output: {root}")


def run_campaign(output: Path, model_path: Path = DEFAULT_MODEL) -> dict[str, Any]:
    root = output.resolve()
    model_path = model_path.resolve()
    _ensure_external_output(root)
    if not model_path.is_dir():
        raise FileNotFoundError(f"model path does not exist: {model_path}")

    model_files_before = model_manifest(model_path)
    model, tokenizer, tokenizer_policy = _load_runtime(model_path)
    layer_count = len(model.model.layers)
    grid = candidate_configs(layer_count)
    parity = parity_check(model, tokenizer, FIT_TEXTS[0])
    if not parity["passed"]:
        raise RuntimeError(f"zero-alpha parity gate failed: {parity}")

    fit_baseline = evaluate_texts(model, tokenizer, FIT_TEXTS, None)
    fit_candidates = []
    for config in grid:
        metrics = evaluate_texts(model, tokenizer, FIT_TEXTS, config)
        fit_candidates.append({"config": asdict(config), "metrics": metrics})
    selected = min(fit_candidates, key=lambda item: item["metrics"]["mean_nll"])
    selected_config = RecirculationConfig(**selected["config"])
    assessment_baseline = evaluate_texts(model, tokenizer, ASSESSMENT_TEXTS, None)
    assessment_selected = evaluate_texts(
        model, tokenizer, ASSESSMENT_TEXTS, selected_config
    )
    assessment_repeat = evaluate_texts(
        model, tokenizer, ASSESSMENT_TEXTS, selected_config
    )
    repeat_delta = max(
        abs(assessment_selected[key] - assessment_repeat[key])
        for key in ("mean_nll", "perplexity")
        if assessment_selected[key] is not None and assessment_repeat[key] is not None
    )
    model_files_after = model_manifest(model_path)
    if model_files_after != model_files_before:
        raise RuntimeError("cached model manifest changed during frozen inference")
    model_files = model_files_after
    config = {
        "state_slice": STATE_SLICE,
        "claim_ceiling": CLAIM_CEILING,
        "model_name": model_path.name,
        "model_path": str(model_path),
        "architecture": "qwen2",
        "layer_count": layer_count,
        "protocol": "one-additional-iteration-deep-to-shallow-residual-recirculation-v1",
        "alpha_semantics": "source_feedback_weight",
        "beta_semantics": "destination_weight_1_minus_alpha",
        "fit_text_count": len(FIT_TEXTS),
        "assessment_text_count": len(ASSESSMENT_TEXTS),
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
        "model_manifest_sha256": model_files["manifest_sha256"],
        "candidate_grid": [asdict(item) for item in grid],
    }
    config["config_sha256"] = digest(config)
    results = {
        "state_slice": STATE_SLICE,
        "claim_ceiling": CLAIM_CEILING,
        "parity": parity,
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
        "model_manifest_sha256": model_files["manifest_sha256"],
        "zero_alpha_parity_passed": parity["passed"],
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
    _write_json(root / "results.json", results)
    _write_json(root / "model-manifest.json", model_files)
    _write_json(root / "receipt.json", receipt)
    return {"config": config, "results": results, "receipt": receipt}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--model", type=Path, default=DEFAULT_MODEL)
    args = parser.parse_args()
    print(json.dumps(run_campaign(args.output, args.model), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
