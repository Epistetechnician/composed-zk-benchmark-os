#!/usr/bin/env python3
"""Offline Gemma3 1B paper-aligned recirculation campaign.

State slice: continual-learning-gemma3-paper-recirculation-v1.

This runner requires an operator-supplied external corpus root. It never
downloads model or corpus data, never trains, and never writes an output root
inside the repository. The controlled forward path mirrors the installed
MLX-Gemma3 text model, including its global and sliding-window KV caches.
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

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

STATE_SLICE = "continual-learning-gemma3-paper-recirculation-v1"
CLAIM_CEILING = "LocalDevelopmentGemma3PaperAlignedRecirculationReplication"
DEFAULT_MODEL = Path("/Users/shaanp/.lmstudio/models/mlx-community/gemma-3-1b-pt-bf16")
PARITY_TOLERANCE = 1e-5
EPSILON = 1e-6
WINDOW_TOKENS = 1024
MAX_LAYER_DISTANCE = 12
ALPHAS = (0.04, 0.07, 0.10, 0.16)
PAIR_SELECTION_ALPHA = 0.10
EVALUATION_ALPHA = 0.15
EVALUATION_BETA = 0.85
FIT_DATASETS = ("arxiv", "c4", "pg19")
ASSESSMENT_DATASETS = (
    "arxiv",
    "big_patent",
    "billsum",
    "booksum/book",
    "c4/webtextlike",
    "gov_report",
    "lambada",
    "newsroom",
    "pg19",
    "pubmed",
)
PARTIAL_ASSESSMENT_DATASETS = frozenset(("c4/webtextlike", "lambada", "newsroom"))
CORPUS_SCHEMA = "gemma3-paper-recirculation-corpus-v1"


def digest(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def package_version(name: str) -> str:
    try:
        return version(name)
    except PackageNotFoundError:
        return "unavailable"


def model_manifest(model_path: Path) -> dict[str, Any]:
    """Bind stable model files while excluding Hugging Face download state."""

    files = []
    for path in sorted(
        candidate
        for candidate in model_path.rglob("*")
        if candidate.is_file()
        and not candidate.is_symlink()
        and ".cache" not in candidate.relative_to(model_path).parts
    ):
        files.append(
            {
                "path": path.relative_to(model_path).as_posix(),
                "byte_len": path.stat().st_size,
                "sha256": sha256_file(path),
            }
        )
    if not files:
        raise ValueError(f"cached model directory has no stable files: {model_path}")
    body = {"model_name": model_path.name, "files": files}
    return {"manifest": body, "manifest_sha256": digest(body)}


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
        if self.source_layer - self.destination_layer > MAX_LAYER_DISTANCE:
            raise ValueError("source/destination distance exceeds paper bound")
        if not math.isfinite(self.alpha) or not 0 <= self.alpha <= 1:
            raise ValueError("alpha must be finite and within [0, 1]")
        if not math.isfinite(self.epsilon) or self.epsilon <= 0:
            raise ValueError("epsilon must be finite and positive")


@dataclass(frozen=True)
class CorpusWindow:
    dataset: str
    document_id: str
    relative_path: str
    window_ordinal: int
    text: str
    byte_len: int
    source_sha256: str
    text_sha256: str
    token_count: int | None


def candidate_pairs(layer_count: int) -> tuple[tuple[int, int], ...]:
    pairs = tuple(
        (source, destination)
        for source in range(layer_count)
        for destination in range(source)
        if source - destination <= MAX_LAYER_DISTANCE
    )
    if not pairs:
        raise ValueError(f"no paper-bounded layer pairs for {layer_count} layers")
    return pairs


def candidate_configs(layer_count: int, alpha: float) -> tuple[RecirculationConfig, ...]:
    configs = tuple(
        RecirculationConfig(source_layer=source, destination_layer=destination, alpha=alpha)
        for source, destination in candidate_pairs(layer_count)
    )
    for config in configs:
        config.validate(layer_count)
    return configs


def mix_residual(mx: Any, source: Any, destination: Any, alpha: float, epsilon: float) -> Any:
    source_norm = mx.sqrt(mx.sum(mx.square(source), axis=-1, keepdims=True))
    destination_norm = mx.sqrt(mx.sum(mx.square(destination), axis=-1, keepdims=True))
    scale = destination_norm / mx.maximum(source_norm, mx.array(epsilon))
    normalized_source = source * scale
    return (1.0 - alpha) * destination + alpha * normalized_source


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


def _gemma_components(model: Any) -> tuple[Any, Any]:
    inner = getattr(model, "model", None)
    if inner is None or not hasattr(inner, "layers") or not hasattr(inner, "embed_tokens"):
        raise TypeError("loaded model does not expose the Gemma3 text model seam")
    if not hasattr(model, "lm_head"):
        raise TypeError("loaded model does not expose a Gemma3 lm_head")
    return inner, model


def _one_token_native(model: Any, mx: Any, token_id: int, cache_state: list[Any]) -> Any:
    return model(mx.array([[int(token_id)]], dtype=mx.int32), cache=cache_state)


def _one_token_recirculated(
    model: Any,
    mx: Any,
    cache_state: list[Any],
    token_id: int,
    config: RecirculationConfig,
    previous_source: Any | None,
) -> tuple[Any, Any]:
    from mlx_lm.models.base import create_attention_mask

    inner, text_model = _gemma_components(model)
    hidden = inner.embed_tokens(mx.array([[int(token_id)]], dtype=mx.int32))
    hidden *= mx.array(inner.args.hidden_size**0.5, mx.bfloat16).astype(hidden.dtype)
    global_mask = create_attention_mask(
        hidden, cache_state[inner.sliding_window_pattern - 1]
    )
    sliding_window_mask = create_attention_mask(
        hidden,
        cache_state[0],
        window_size=inner.window_size,
    )
    current_source = None
    for index, (layer, layer_cache) in enumerate(zip(inner.layers, cache_state)):
        is_global = (
            index % inner.sliding_window_pattern
            == inner.sliding_window_pattern - 1
        )
        hidden = layer(
            hidden,
            global_mask if is_global else sliding_window_mask,
            layer_cache,
        )
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
    logits = text_model.lm_head(inner.norm(hidden))
    return logits, current_source


def logits_for_tokens(
    model: Any,
    token_ids: Sequence[int],
    config: RecirculationConfig | None = None,
) -> list[Any]:
    """Compute teacher-forced logits using a fresh Gemma3 KV-cache set."""

    import mlx.core as mx

    _gemma_components(model)
    layer_count = len(model.model.layers)
    if config is not None:
        config.validate(layer_count)
    cache_state = model.make_cache()
    outputs = []
    previous_source = None
    for token_id in token_ids:
        if config is None:
            logits = _one_token_native(model, mx, int(token_id), cache_state)
        else:
            logits, previous_source = _one_token_recirculated(
                model,
                mx,
                cache_state,
                int(token_id),
                config,
                previous_source,
            )
        mx.eval(logits)
        if previous_source is not None:
            mx.eval(previous_source)
        outputs.append(logits[0, -1, :])
    if outputs:
        mx.eval(*outputs)
    return outputs


def _nll(
    logits: Sequence[Any],
    token_ids: Sequence[int],
    mx: Any,
    temperature: float,
) -> tuple[float, int]:
    if not math.isfinite(temperature) or temperature <= 0:
        raise ValueError("temperature must be finite and positive")
    if len(token_ids) < 2:
        return 0.0, 0
    total = 0.0
    count = 0
    for index, target in enumerate(token_ids[1:]):
        scaled = logits[index] / temperature
        log_probs = scaled - mx.logsumexp(scaled)
        total += -float(log_probs[int(target)])
        count += 1
    return total, count


def evaluate_windows(
    model: Any,
    tokenizer: Any,
    windows: Iterable[CorpusWindow],
    config: RecirculationConfig | None,
    *,
    temperature: float = 1.0,
    include_rows: bool = True,
) -> dict[str, Any]:
    import mlx.core as mx

    total_nll = 0.0
    total_tokens = 0
    rows = []
    for window in windows:
        token_ids = tokenizer.encode(window.text, add_special_tokens=False)
        logits = logits_for_tokens(model, token_ids, config)
        nll, target_count = _nll(logits, token_ids, mx, temperature)
        total_nll += nll
        total_tokens += target_count
        if include_rows:
            rows.append(
                {
                    "dataset": window.dataset,
                    "document_id": window.document_id,
                    "window_ordinal": window.window_ordinal,
                    "text_sha256": window.text_sha256,
                    "token_count": len(token_ids),
                    "target_count": target_count,
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


def evaluate_by_dataset(
    model: Any,
    tokenizer: Any,
    windows: Sequence[CorpusWindow],
    config: RecirculationConfig | None,
    *,
    temperature: float = 1.0,
    include_rows: bool = False,
) -> dict[str, dict[str, Any]]:
    datasets = sorted({window.dataset for window in windows})
    return {
        dataset: evaluate_windows(
            model,
            tokenizer,
            [window for window in windows if window.dataset == dataset],
            config,
            temperature=temperature,
            include_rows=include_rows,
        )
        for dataset in datasets
    }


def parity_check(model: Any, tokenizer: Any, text: str) -> dict[str, Any]:
    import mlx.core as mx

    token_ids = tokenizer.encode(text, add_special_tokens=False)
    layer_count = len(model.model.layers)
    source, destination = min(11, layer_count - 1), min(4, layer_count - 2)
    if destination >= source:
        destination = source - 1
    native = logits_for_tokens(model, token_ids, None)
    zero_alpha = logits_for_tokens(
        model,
        token_ids,
        RecirculationConfig(source, destination, 0.0),
    )
    deltas = [float(mx.max(mx.abs(a - b))) for a, b in zip(native, zero_alpha)]
    max_delta = max(deltas, default=0.0)
    return {
        "token_count": len(token_ids),
        "max_abs_logit_delta": max_delta,
        "tolerance": PARITY_TOLERANCE,
        "passed": max_delta <= PARITY_TOLERANCE,
    }


def _safe_source(root: Path, relative_path: str) -> Path:
    if not isinstance(relative_path, str) or not relative_path:
        raise ValueError("corpus path must be a non-empty relative string")
    raw_path = root / relative_path
    if raw_path.is_symlink():
        raise ValueError(f"invalid external corpus path: {relative_path}")
    candidate = raw_path.resolve()
    resolved_root = root.resolve()
    if (
        candidate == resolved_root
        or resolved_root not in candidate.parents
        or Path(relative_path).is_absolute()
        or candidate.is_symlink()
        or not candidate.is_file()
    ):
        raise ValueError(f"invalid external corpus path: {relative_path}")
    return candidate


def _parse_window(
    root: Path,
    raw: Any,
    tokenizer: Any | None,
    split: str,
) -> CorpusWindow:
    if not isinstance(raw, dict):
        raise ValueError(f"{split} corpus entry must be an object")
    dataset = raw.get("dataset")
    document_id = raw.get("document_id")
    relative_path = raw.get("path")
    ordinal = raw.get("window_ordinal")
    if not isinstance(dataset, str) or not dataset:
        raise ValueError(f"{split} corpus entry has invalid dataset")
    if not isinstance(document_id, str) or not document_id:
        raise ValueError(f"{split} corpus entry has invalid document_id")
    if not isinstance(ordinal, int) or ordinal < 0:
        raise ValueError(f"{split} corpus entry has invalid window_ordinal")
    path = _safe_source(root, relative_path)
    raw_bytes = path.read_bytes()
    text = raw_bytes.decode("utf-8")
    token_count = None
    if tokenizer is not None:
        token_count = len(tokenizer.encode(text, add_special_tokens=False))
    declared_count = raw.get("token_count")
    if declared_count is not None and declared_count != token_count:
        raise ValueError(f"token count mismatch: {relative_path}")
    if token_count is not None:
        full_window = token_count == WINDOW_TOKENS
        partial_allowed = split == "assessment" and dataset in PARTIAL_ASSESSMENT_DATASETS
        if not full_window and not (partial_allowed and 1 < token_count < WINDOW_TOKENS):
            raise ValueError(f"window is not a permitted full window: {relative_path}")
    return CorpusWindow(
        dataset=dataset,
        document_id=document_id,
        relative_path=Path(relative_path).as_posix(),
        window_ordinal=ordinal,
        text=text,
        byte_len=len(raw_bytes),
        source_sha256=sha256_bytes(raw_bytes),
        text_sha256=sha256_bytes(text.encode("utf-8")),
        token_count=token_count,
    )


def _check_corpus_root_manifest(corpus_root: Path) -> None:
    root = corpus_root.resolve()
    manifest_path = root / "manifest.json"
    if not root.is_dir() or not manifest_path.is_file() or manifest_path.is_symlink():
        raise FileNotFoundError(
            "external corpus root must contain a regular manifest.json: "
            f"{root}"
        )
    try:
        raw_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError("external corpus manifest is not valid JSON") from exc
    if not isinstance(raw_manifest, dict):
        raise ValueError("external corpus manifest must be an object")
    if raw_manifest.get("schema") != CORPUS_SCHEMA:
        raise ValueError("external corpus schema mismatch")
    if raw_manifest.get("window_token_count") != WINDOW_TOKENS:
        raise ValueError("external corpus window_token_count must be 1024")
    if not isinstance(raw_manifest.get("fit"), list) or not isinstance(
        raw_manifest.get("assessment"), list
    ):
        raise ValueError("external corpus must contain fit and assessment lists")


def _window_manifest(window: CorpusWindow) -> dict[str, Any]:
    result = {
        "dataset": window.dataset,
        "document_id": window.document_id,
        "path": window.relative_path,
        "window_ordinal": window.window_ordinal,
        "byte_len": window.byte_len,
        "source_sha256": window.source_sha256,
        "text_sha256": window.text_sha256,
    }
    if window.token_count is not None:
        result["token_count"] = window.token_count
    return result


def load_corpus(
    corpus_root: Path,
    tokenizer: Any | None,
    *,
    strict_shape: bool = True,
) -> tuple[list[CorpusWindow], list[CorpusWindow], dict[str, Any]]:
    root = corpus_root.resolve()
    manifest_path = root / "manifest.json"
    if not root.is_dir() or not manifest_path.is_file() or manifest_path.is_symlink():
        raise FileNotFoundError(
            "external corpus root must contain a regular manifest.json: "
            f"{root}"
        )
    try:
        raw_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError("external corpus manifest is not valid JSON") from exc
    if not isinstance(raw_manifest, dict):
        raise ValueError("external corpus manifest must be an object")
    if raw_manifest.get("schema") != CORPUS_SCHEMA:
        raise ValueError("external corpus schema mismatch")
    if raw_manifest.get("window_token_count") != WINDOW_TOKENS:
        raise ValueError("external corpus window_token_count must be 1024")
    fit_raw = raw_manifest.get("fit")
    assessment_raw = raw_manifest.get("assessment")
    if not isinstance(fit_raw, list) or not isinstance(assessment_raw, list):
        raise ValueError("external corpus must contain fit and assessment lists")
    fit = [_parse_window(root, item, tokenizer, "fit") for item in fit_raw]
    assessment = [
        _parse_window(root, item, tokenizer, "assessment") for item in assessment_raw
    ]
    all_windows = fit + assessment
    paths = [window.relative_path for window in all_windows]
    if len(paths) != len(set(paths)):
        raise ValueError("external corpus reuses a source path")
    fit_keys = [(window.dataset, window.document_id) for window in fit]
    assessment_keys = [(window.dataset, window.document_id) for window in assessment]
    if set(fit_keys) & set(assessment_keys):
        raise ValueError("fit and assessment reuse a document identity")
    if any(fit_keys.count(key) > 2 for key in set(fit_keys)):
        raise ValueError("fit uses more than two windows from one document")
    if strict_shape:
        if {window.dataset for window in fit} != set(FIT_DATASETS):
            raise ValueError("fit datasets do not match the paper training panel")
        if {window.dataset for window in assessment} != set(ASSESSMENT_DATASETS):
            raise ValueError("assessment datasets do not match the paper panel")
    body = {
        "state_slice": STATE_SLICE,
        "schema": CORPUS_SCHEMA,
        "window_token_count": WINDOW_TOKENS,
        "source_manifest_sha256": sha256_file(manifest_path),
        "fit": [_window_manifest(window) for window in fit],
        "assessment": [_window_manifest(window) for window in assessment],
        "fit_window_count": len(fit),
        "assessment_window_count": len(assessment),
    }
    return fit, assessment, {"manifest": body, "manifest_sha256": digest(body)}


def _write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _ensure_external_output(root: Path) -> None:
    if root == REPO_ROOT or REPO_ROOT in root.parents:
        raise ValueError("recirculation output must be outside the repository")
    if root.exists():
        raise FileExistsError(f"refusing overwrite of immutable output: {root}")


def _fit_pair_score(
    baseline: dict[str, dict[str, Any]],
    candidate: dict[str, dict[str, Any]],
) -> float:
    reductions = []
    for dataset in FIT_DATASETS:
        base_ppl = baseline[dataset]["perplexity"]
        candidate_ppl = candidate[dataset]["perplexity"]
        if base_ppl is None or candidate_ppl is None or base_ppl <= 0:
            raise ValueError(f"missing finite perplexity for fit dataset {dataset}")
        reductions.append((base_ppl - candidate_ppl) / base_ppl)
    return sum(reductions) / len(reductions)


def _weighted_mean(metrics: dict[str, dict[str, Any]]) -> float:
    total_nll = sum(
        value["mean_nll"] * value["target_tokens"] for value in metrics.values()
    )
    total_targets = sum(value["target_tokens"] for value in metrics.values())
    if total_targets <= 0:
        raise ValueError("assessment has no target tokens")
    return total_nll / total_targets


def run_campaign(
    output: Path,
    corpus_root: Path,
    model_path: Path = DEFAULT_MODEL,
) -> dict[str, Any]:
    root = output.resolve()
    corpus_root = corpus_root.resolve()
    model_path = model_path.resolve()
    _ensure_external_output(root)
    if not model_path.is_dir():
        raise FileNotFoundError(f"model path does not exist: {model_path}")

    _check_corpus_root_manifest(corpus_root)
    model_files_before = model_manifest(model_path)
    model, tokenizer, tokenizer_policy = _load_runtime(model_path)
    layer_count = len(model.model.layers)
    if getattr(model.args, "model_type", None) != "gemma3_text":
        raise ValueError("loaded checkpoint is not the expected Gemma3 text model")
    if layer_count != 26:
        raise ValueError(f"expected Gemma3 1B PT to have 26 layers, found {layer_count}")
    fit, assessment, corpus = load_corpus(corpus_root, tokenizer, strict_shape=True)
    parity_checks = [
        parity_check(model, tokenizer, window.text)
        for window in (*fit, *assessment)
    ]
    if not all(item["passed"] for item in parity_checks):
        raise RuntimeError("zero-alpha parity gate failed")

    fit_baseline = evaluate_by_dataset(model, tokenizer, fit, None)
    pair_configs = candidate_configs(layer_count, PAIR_SELECTION_ALPHA)
    fit_pair_candidates = []
    for config in pair_configs:
        candidate = evaluate_by_dataset(model, tokenizer, fit, config)
        fit_pair_candidates.append(
            {
                "config": asdict(config),
                "mean_percentage_perplexity_reduction": _fit_pair_score(
                    fit_baseline, candidate
                ),
                "metrics_by_dataset": candidate,
            }
        )
    selected_pair = max(
        fit_pair_candidates,
        key=lambda item: item["mean_percentage_perplexity_reduction"],
    )
    selected_pair_config = RecirculationConfig(**selected_pair["config"])

    arxiv_fit = [window for window in fit if window.dataset == "arxiv"]
    fit_alpha_sweep = []
    for alpha in ALPHAS:
        for source, destination in candidate_pairs(layer_count):
            config = RecirculationConfig(source, destination, alpha)
            fit_alpha_sweep.append(
                {
                    "config": asdict(config),
                    "metrics": evaluate_windows(
                        model,
                        tokenizer,
                        arxiv_fit,
                        config,
                        include_rows=False,
                    ),
                }
            )

    locked_config = RecirculationConfig(
        selected_pair_config.source_layer,
        selected_pair_config.destination_layer,
        EVALUATION_ALPHA,
    )
    assessment_baseline = evaluate_by_dataset(
        model, tokenizer, assessment, None, include_rows=True
    )
    assessment_selected = evaluate_by_dataset(
        model, tokenizer, assessment, locked_config, include_rows=True
    )
    assessment_temperature_baseline = evaluate_by_dataset(
        model, tokenizer, assessment, None, temperature=1.2
    )
    assessment_temperature_selected = evaluate_by_dataset(
        model,
        tokenizer,
        assessment,
        locked_config,
        temperature=1.2,
    )
    assessment_repeat = evaluate_by_dataset(
        model, tokenizer, assessment, locked_config, include_rows=False
    )
    repeat_delta = max(
        abs(
            assessment_selected[dataset]["mean_nll"]
            - assessment_repeat[dataset]["mean_nll"]
        )
        for dataset in ASSESSMENT_DATASETS
    )
    model_files_after = model_manifest(model_path)
    if model_files_after != model_files_before:
        raise RuntimeError("cached model manifest changed during frozen inference")

    config = {
        "state_slice": STATE_SLICE,
        "claim_ceiling": CLAIM_CEILING,
        "model_name": model_path.name,
        "model_path": str(model_path),
        "architecture": "gemma3_text",
        "layer_count": layer_count,
        "protocol": "paper-aligned-one-additional-iteration-v1",
        "mechanism_source": "arxiv:2608.17981",
        "alpha_semantics": "source_feedback_weight",
        "beta_semantics": "destination_weight_1_minus_alpha",
        "normalization": "source_l2_norm_to_destination_l2_norm",
        "window_token_count": WINDOW_TOKENS,
        "fit_datasets": list(FIT_DATASETS),
        "assessment_datasets": list(ASSESSMENT_DATASETS),
        "alpha_grid": list(ALPHAS),
        "pair_selection_alpha": PAIR_SELECTION_ALPHA,
        "evaluation_alpha": EVALUATION_ALPHA,
        "evaluation_beta": EVALUATION_BETA,
        "selected_fit_pair": {
            "source_layer": selected_pair_config.source_layer,
            "destination_layer": selected_pair_config.destination_layer,
        },
        "paper_expected_pair": {"source_layer": 11, "destination_layer": 4},
        "network_access": False,
        "training": False,
        "weights_frozen": True,
        "looping_control": "deferred_separate_runtime_surface",
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
        "fit_window_count": len(fit),
        "assessment_window_count": len(assessment),
        "pair_candidate_count": len(pair_configs),
        "alpha_sweep_candidate_count": len(fit_alpha_sweep),
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
        "fit_baseline_by_dataset": fit_baseline,
        "fit_pair_candidates": fit_pair_candidates,
        "fit_alpha_sweep_arxiv": fit_alpha_sweep,
        "selected_fit_pair": asdict(selected_pair_config),
        "paper_expected_pair_recovered": (
            selected_pair_config.source_layer == 11
            and selected_pair_config.destination_layer == 4
        ),
        "locked_evaluation_config": asdict(locked_config),
        "assessment_baseline_by_dataset": assessment_baseline,
        "assessment_selected_by_dataset": assessment_selected,
        "assessment_temperature_baseline_by_dataset": assessment_temperature_baseline,
        "assessment_temperature_selected_by_dataset": assessment_temperature_selected,
        "assessment_repeat_by_dataset": assessment_repeat,
        "assessment_repeat_max_mean_nll_delta": round(repeat_delta, 12),
        "looping_control": {
            "status": "deferred_separate_runtime_surface",
            "included_in_primary_endpoint": False,
        },
        "performance_result_is_local_paper_aligned_replication_only": True,
    }
    results["results_sha256"] = digest(results)
    selected_mean_baseline = _weighted_mean(assessment_baseline)
    selected_mean_recirculation = _weighted_mean(assessment_selected)
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
        "paper_expected_pair_recovered": results["paper_expected_pair_recovered"],
        "assessment_mean_nll_delta_selected_minus_baseline": round(
            selected_mean_recirculation - selected_mean_baseline, 9
        ),
        "performance_improved_on_assessment": (
            selected_mean_recirculation < selected_mean_baseline
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
    parser.add_argument("--corpus-root", type=Path, required=True)
    parser.add_argument("--model", type=Path, default=DEFAULT_MODEL)
    args = parser.parse_args()
    print(
        json.dumps(
            run_campaign(args.output, args.corpus_root, args.model),
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
