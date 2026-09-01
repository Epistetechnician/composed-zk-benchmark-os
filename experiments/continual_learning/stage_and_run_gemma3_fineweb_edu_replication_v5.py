#!/usr/bin/env python3
"""Review-gated, self-contained V5 Gemma3 FineWeb-Edu runner.

State slice: continual-learning-gemma3-fineweb-edu-replication-v5.
The V5 runner owns model loading, the reviewed forward seam, controls, metric
construction, custody snapshots, no-overwrite publication, and final validator
execution. It does not import any V1-V4 scientific runner.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Sequence

from experiments.continual_learning import gemma3_fineweb_edu_replication_v5_contract as c
from experiments.continual_learning import validate_gemma3_fineweb_edu_replication_v5 as validator

REPO_ROOT = c.REPO_ROOT
VALIDATOR_MODULE = "experiments.continual_learning.validate_gemma3_fineweb_edu_replication_v5"


def _json(path: Path, label: str) -> dict[str, Any]:
    return validator._json(path, label)


def _write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _enter_native_sandbox() -> None:
    if sys.platform != "darwin" or c.native_network_denied():
        return
    if os.environ.get("V5_SANDBOX_REEXEC_ATTEMPTED") == "1":
        raise RuntimeError("V5 native network sandbox could not be proven")
    sandbox = shutil.which("sandbox-exec")
    if sandbox is None:
        raise RuntimeError("V5 sandbox-exec is unavailable; execution is closed")
    environment = os.environ.copy()
    environment["V5_SANDBOX_REEXEC_ATTEMPTED"] = "1"
    profile = "(version 1) (deny network*) (allow default)"
    os.execvpe(sandbox, [sandbox, "-p", profile, sys.executable, "-B", str(Path(__file__).resolve()), *sys.argv[1:]], environment)


def _require_native_sandbox() -> None:
    c.require_native_network_denial()


def _review_snapshot(review_receipt: Path) -> dict[str, Any]:
    review_path = c.exact_path(review_receipt, c.REVIEW_RECEIPT_PATH, "V5 review receipt")
    c.validate_review_receipt(review_path)
    snapshot = c.snapshot_code_and_review()
    snapshot["review_sha256"] = c.sha256_file(review_path)
    return snapshot


def _assert_review_snapshot(snapshot: dict[str, Any]) -> None:
    c.assert_code_and_review_snapshot(snapshot)


def _expected_corpus_files() -> set[str]:
    return {"manifest.json", *{f"{split}/window-{ordinal:06d}.txt" for split in ("fit", "assessment") for ordinal in range(c.FIT_WINDOW_COUNT)}}


def _input_snapshot(source_root: Path, corpus_root: Path | None, raw_root: Path, prior_root: Path, model_path: Path) -> dict[str, Any]:
    source = c.exact_path(source_root, c.SOURCE_ROOT, "V5 source root")
    raw = c.exact_path(raw_root, c.RAW_ROOT, "V5 raw root")
    prior = c.exact_path(prior_root, c.R1_SOURCE_ROOT, "V5 prior-pilot source root")
    model = c.exact_path(model_path, c.MODEL_PATH, "model path")
    result: dict[str, Any] = {
        "source": c.snapshot_files(source, {"acquisition-manifest.json", "fit/fineweb_edu.jsonl", "assessment/fineweb_edu.jsonl"}, "V5 source root"),
        "raw": c.snapshot_files(raw, {f"dataset/{item['path']}" for item in c.DATASET_FILES}, "V5 raw root", allow_cache=True),
        "prior": c.snapshot_files(prior, {"acquisition-manifest.json", "fit/fineweb_edu.jsonl", "assessment/fineweb_edu.jsonl"}, "V5 prior-pilot source root"),
        "model": c.model_manifest(model),
    }
    if corpus_root is not None:
        corpus = c.exact_path(corpus_root, c.CORPUS_ROOT, "V5 corpus root")
        result["corpus"] = c.snapshot_files(corpus, _expected_corpus_files(), "V5 corpus root")
    return result


def _assert_input_snapshot(snapshot: dict[str, Any], source_root: Path, corpus_root: Path | None, raw_root: Path, prior_root: Path, model_path: Path) -> None:
    observed = _input_snapshot(source_root, corpus_root, raw_root, prior_root, model_path)
    if observed != snapshot:
        raise RuntimeError("V5 reviewed input custody changed after validation")


def _load_tokenizer(model_path: Path) -> Any:
    model_path = c.exact_path(model_path, c.MODEL_PATH, "model path")
    model_files = c.model_manifest(model_path)
    if model_files["manifest_sha256"] != c.EXPECTED_MODEL_MANIFEST_SHA256:
        raise ValueError("V5 model manifest mismatch before tokenizer load")
    if c.runtime_versions() != c.RUNTIME_VERSIONS:
        raise RuntimeError(f"V5 runtime mismatch: {c.runtime_versions()}")
    _require_native_sandbox()
    from mlx_lm.utils import load_tokenizer
    with c.network_block():
        return load_tokenizer(model_path)


def load_runtime(model_path: Path) -> tuple[Any, Any, dict[str, str]]:
    model_path = c.exact_path(model_path, c.MODEL_PATH, "model path")
    model_files = c.model_manifest(model_path)
    if model_files["manifest_sha256"] != c.EXPECTED_MODEL_MANIFEST_SHA256:
        raise ValueError("V5 model manifest mismatch before model load")
    if c.runtime_versions() != c.RUNTIME_VERSIONS:
        raise RuntimeError(f"V5 runtime mismatch: {c.runtime_versions()}")
    _require_native_sandbox()
    from mlx_lm import load
    with c.network_block():
        model, tokenizer = load(str(model_path), tokenizer_config=None)
    return model, tokenizer, dict(c.RUNTIME_VERSIONS)


@dataclass(frozen=True)
class RecirculationConfig:
    source_layer: int
    destination_layer: int
    alpha: float
    beta: float
    epsilon: float = c.EPSILON

    def validate(self, layer_count: int) -> None:
        if not isinstance(self.source_layer, int) or isinstance(self.source_layer, bool) or not isinstance(self.destination_layer, int) or isinstance(self.destination_layer, bool) or not 0 <= self.destination_layer < self.source_layer < layer_count:
            raise ValueError("V5 layer pair is invalid")
        if isinstance(self.alpha, bool) or not isinstance(self.alpha, (int, float)) or isinstance(self.beta, bool) or not isinstance(self.beta, (int, float)) or isinstance(self.epsilon, bool) or not isinstance(self.epsilon, (int, float)) or not math.isfinite(float(self.alpha)) or not math.isfinite(float(self.beta)) or not math.isfinite(float(self.epsilon)) or not 0 <= self.alpha <= 1 or self.beta != 1.0 - self.alpha or self.epsilon <= 0:
            raise ValueError("V5 alpha/beta/epsilon contract is invalid")

    def as_dict(self) -> dict[str, Any]:
        return {"source_layer": self.source_layer, "destination_layer": self.destination_layer, "alpha": self.alpha, "beta": self.beta, "epsilon": self.epsilon}


def mix_residual(mx: Any, source: Any, destination: Any, config: RecirculationConfig) -> Any:
    source_norm = mx.sqrt(mx.sum(mx.square(source), axis=-1, keepdims=True))
    destination_norm = mx.sqrt(mx.sum(mx.square(destination), axis=-1, keepdims=True))
    normalized_source = source * (destination_norm / mx.maximum(source_norm, mx.array(config.epsilon)))
    return config.beta * destination + config.alpha * normalized_source


def _gemma_components(model: Any) -> tuple[Any, Any]:
    inner = getattr(model, "model", None)
    if inner is None or not hasattr(inner, "layers") or not hasattr(inner, "embed_tokens") or not hasattr(model, "lm_head"):
        raise TypeError("loaded model does not expose the Gemma3 text seam")
    return inner, model


def _one_token_native(model: Any, mx: Any, token_id: int, cache_state: list[Any]) -> Any:
    return model(mx.array([[int(token_id)]], dtype=mx.int32), cache=cache_state)


def _one_token_recirculated(model: Any, mx: Any, cache_state: list[Any], token_id: int, config: RecirculationConfig, previous_source: Any | None) -> tuple[Any, Any]:
    from mlx_lm.models.base import create_attention_mask

    inner, text_model = _gemma_components(model)
    hidden = inner.embed_tokens(mx.array([[int(token_id)]], dtype=mx.int32))
    hidden *= mx.array(inner.args.hidden_size**0.5, mx.bfloat16).astype(hidden.dtype)
    global_mask = create_attention_mask(hidden, cache_state[inner.sliding_window_pattern - 1])
    sliding_window_mask = create_attention_mask(hidden, cache_state[0], window_size=inner.window_size)
    current_source = None
    for index, (layer, layer_cache) in enumerate(zip(inner.layers, cache_state, strict=True)):
        is_global = index % inner.sliding_window_pattern == inner.sliding_window_pattern - 1
        hidden = layer(hidden, global_mask if is_global else sliding_window_mask, layer_cache)
        if index == config.destination_layer and previous_source is not None and config.alpha != 0:
            hidden = mix_residual(mx, previous_source, hidden, config)
        if index == config.source_layer:
            current_source = hidden
    if current_source is None:
        raise RuntimeError("V5 source activation was not captured")
    return text_model.lm_head(inner.norm(hidden)), current_source


def logits_for_tokens(model: Any, token_ids: Sequence[int], config: RecirculationConfig | None = None) -> list[Any]:
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
            logits, previous_source = _one_token_recirculated(model, mx, cache_state, int(token_id), config, previous_source)
        mx.eval(logits)
        if previous_source is not None:
            mx.eval(previous_source)
        outputs.append(logits[0, -1, :])
    if outputs:
        mx.eval(*outputs)
    return outputs


def _nll(logits: Sequence[Any], token_ids: Sequence[int], mx: Any, temperature: float) -> tuple[float, int]:
    if isinstance(temperature, bool) or not isinstance(temperature, (int, float)) or not math.isfinite(float(temperature)) or temperature <= 0:
        raise ValueError("V5 temperature must be finite and positive")
    total = 0.0
    for index, target in enumerate(token_ids[1:]):
        scaled = logits[index] / temperature
        total += -float((scaled - mx.logsumexp(scaled))[int(target)])
    if not math.isfinite(total):
        raise ValueError("V5 NLL is nonfinite")
    return total, max(0, len(token_ids) - 1)


def evaluate_windows(model: Any, tokenizer: Any, windows: Iterable[Any], config: RecirculationConfig | None, *, temperature: float = 1.0) -> dict[str, Any]:
    import mlx.core as mx

    if isinstance(temperature, bool) or not isinstance(temperature, (int, float)) or not math.isfinite(float(temperature)) or temperature <= 0:
        raise ValueError("V5 temperature must be finite and positive")
    rows = []
    for window in windows:
        token_ids = list(tokenizer.encode(window.text, add_special_tokens=False))
        if tuple(token_ids) != tuple(window.token_ids) or len(token_ids) != c.WINDOW_TOKENS:
            raise ValueError("V5 tokenizer output changed after corpus validation")
        logits = logits_for_tokens(model, token_ids, config)
        nll, target_count = _nll(logits, token_ids, mx, float(temperature))
        rows.append({"dataset": window.dataset, "document_id": window.document_id, "relative_path": window.relative_path, "window_ordinal": window.window_ordinal, "source_sha256": window.source_sha256, "text_sha256": window.text_sha256, "token_count": len(token_ids), "target_count": target_count, "nll": round(nll, 9)})
    target_tokens = sum(row["target_count"] for row in rows)
    total_nll = sum(row["nll"] for row in rows)
    mean_nll = round(total_nll / target_tokens, 9) if target_tokens else float("nan")
    if not math.isfinite(mean_nll):
        raise ValueError("V5 metric aggregate is nonfinite")
    return {"temperature": float(temperature), "evaluation_config": config.as_dict() if config is not None else None, "mean_nll": mean_nll, "perplexity": round(math.exp(mean_nll), 9), "target_tokens": target_tokens, "rows": rows}


def load_corpus(corpus_root: Path, tokenizer: Any) -> tuple[list[Any], list[Any], dict[str, Any]]:
    root = c.exact_or_staging_path(corpus_root, c.CORPUS_ROOT, "V5 corpus root")
    c.exact_file_set(root, _expected_corpus_files(), "V5 corpus root")
    manifest = _json(root / "manifest.json", "V5 corpus manifest")
    fit = [validator.parse_window(root, item, tokenizer, "fit") for item in manifest["fit_windows"]]
    assessment = [validator.parse_window(root, item, tokenizer, "assessment") for item in manifest["assessment_windows"]]
    if len(fit) != c.FIT_WINDOW_COUNT or len(assessment) != c.ASSESSMENT_WINDOW_COUNT or set(item.document_id for item in fit) & set(item.document_id for item in assessment):
        raise ValueError("V5 corpus window shape or disjointness mismatch")
    return fit, assessment, {"manifest": manifest, "manifest_sha256": manifest["manifest_sha256"]}


def parity(model: Any, windows: Sequence[Any]) -> dict[str, Any]:
    import mlx.core as mx

    checks = []
    for window in windows:
        native = logits_for_tokens(model, window.token_ids, None)
        zero = logits_for_tokens(model, window.token_ids, RecirculationConfig(11, 4, 0.0, 1.0))
        maximum = max((float(mx.max(mx.abs(left - right))) for left, right in zip(native, zero, strict=True)), default=0.0)
        checks.append({"dataset": window.dataset, "document_id": window.document_id, "relative_path": window.relative_path, "source_sha256": window.source_sha256, "text_sha256": window.text_sha256, "token_count": len(window.token_ids), "max_abs_logit_delta": maximum, "tolerance": c.PARITY_TOLERANCE, "passed": maximum <= c.PARITY_TOLERANCE})
    if len(checks) != 128 or not all(item["passed"] is True for item in checks):
        raise RuntimeError("V5 zero-alpha parity gate failed")
    return {"sequence_count": len(checks), "max_abs_logit_delta": max(item["max_abs_logit_delta"] for item in checks), "tolerance": c.PARITY_TOLERANCE, "all_passed": True, "checks": checks}


def _metrics_finite(metrics: dict[str, Any], label: str) -> None:
    for field in ("temperature", "mean_nll", "perplexity"):
        value = metrics.get(field)
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
            raise ValueError(f"{label} {field} is nonfinite or nonnumeric")


def _run_effects(model_path: Path, corpus_root: Path, review_sha: str, source_sha: str, input_snapshot: dict[str, Any], source_root: Path, raw_root: Path, prior_root: Path, review_snapshot: dict[str, Any]) -> dict[str, Any]:
    _require_native_sandbox()
    _assert_review_snapshot(review_snapshot)
    _assert_input_snapshot(input_snapshot, source_root, corpus_root, raw_root, prior_root, model_path)
    with c.network_block():
        model, tokenizer, runtime = load_runtime(model_path)
        if getattr(model.args, "model_type", None) != "gemma3_text" or len(model.model.layers) != 26:
            raise ValueError("V5 model architecture mismatch")
        parameter_before = c.model_parameter_digest(model)
        model_manifest_before = c.model_manifest(model_path)
        fit, assessment, corpus = load_corpus(corpus_root, tokenizer)
        _assert_review_snapshot(review_snapshot)
        _assert_input_snapshot(input_snapshot, source_root, corpus_root, raw_root, prior_root, model_path)
        parity_value = parity(model, [*fit, *assessment])
        fit_baseline = evaluate_windows(model, tokenizer, fit, None)
        fit_candidates = []
        for source_layer, destination_layer in c.CANDIDATE_PAIRS:
            config = RecirculationConfig(source_layer, destination_layer, c.FIT_ALPHA, c.FIT_BETA)
            metrics = evaluate_windows(model, tokenizer, fit, config)
            _metrics_finite(metrics, "V5 fit candidate")
            fit_candidates.append({"config": config.as_dict(), "metrics": metrics})
        selected = min(((item["metrics"]["mean_nll"], pair[0], pair[1], item) for pair, item in zip(c.CANDIDATE_PAIRS, fit_candidates, strict=True)), key=lambda item: (item[0], item[1], item[2]))[3]
        selected_config = selected["config"]
        locked_config = RecirculationConfig(selected_config["source_layer"], selected_config["destination_layer"], c.EVALUATION_ALPHA, c.EVALUATION_BETA)
        assessment_baseline = evaluate_windows(model, tokenizer, assessment, None)
        assessment_selected = evaluate_windows(model, tokenizer, assessment, locked_config)
        temperature_baseline = evaluate_windows(model, tokenizer, assessment, None, temperature=c.TEMPERATURE_CONTROL)
        temperature_selected = evaluate_windows(model, tokenizer, assessment, locked_config, temperature=c.TEMPERATURE_CONTROL)
        repeat = evaluate_windows(model, tokenizer, assessment, locked_config)
        parameter_after = c.model_parameter_digest(model)
        model_manifest_after = c.model_manifest(model_path)
        if model_manifest_before != model_manifest_after or parameter_before != parameter_after:
            raise RuntimeError("V5 frozen model custody changed during inference")
    for label, metrics in (("fit baseline", fit_baseline), ("assessment baseline", assessment_baseline), ("assessment selected", assessment_selected), ("temperature baseline", temperature_baseline), ("temperature selected", temperature_selected), ("repeat", repeat)):
        _metrics_finite(metrics, label)
    baseline_rows = {row["document_id"]: row for row in assessment_baseline["rows"]}
    selected_rows = {row["document_id"]: row for row in assessment_selected["rows"]}
    window_by_id = {window.document_id: window for window in assessment}
    per_document = []
    for document_id in sorted(baseline_rows):
        base = baseline_rows[document_id]
        chosen = selected_rows[document_id]
        window = window_by_id[document_id]
        delta = chosen["nll"] / (c.WINDOW_TOKENS - 1) - base["nll"] / (c.WINDOW_TOKENS - 1)
        per_document.append({"dataset": window.dataset, "document_id": document_id, "relative_path": window.relative_path, "window_ordinal": window.window_ordinal, "source_sha256": window.source_sha256, "text_sha256": window.text_sha256, "token_count": window.token_count, "target_count": c.WINDOW_TOKENS - 1, "baseline_nll": base["nll"], "selected_nll": chosen["nll"], "delta_selected_minus_baseline": delta})
    deltas = [row["delta_selected_minus_baseline"] for row in per_document]
    bootstrap = c.bootstrap_mean_ci(deltas)
    decision = c.decide_replication(bootstrap)
    controls = {"native_baseline": assessment_baseline, "zero_alpha_identity": parity_value, "all_candidate_evaluations": fit_candidates, "temperature_1.20_baseline": temperature_baseline, "temperature_1.20_intervention": temperature_selected, "deterministic_repeat": repeat, "frozen_model_manifest": {"before": model_manifest_before["manifest_sha256"], "after": model_manifest_after["manifest_sha256"]}, "frozen_model_parameters": {"before": parameter_before, "after": parameter_after}}
    expected_pair = {"source_layer": 11, "destination_layer": 4}
    common = {"schema": c.RESULT_SCHEMA, "state_slice": c.STATE_SLICE, "claim_ceiling": c.CLAIM_CEILING, "protocol_sha256": c.PROTOCOL_SHA256, "review_receipt_sha256": review_sha, "source_manifest_sha256": source_sha, "corpus_manifest_sha256": corpus["manifest_sha256"], "model_path": str(c.MODEL_PATH), "model_manifest_sha256": model_manifest_before["manifest_sha256"], "model_parameter_digest_before": parameter_before, "model_parameter_digest_after": parameter_after, "architecture": "gemma3_text", "model_type": "gemma3_text", "layer_count": 26, "runtime": runtime}
    config = {**common, "model_name": model_path.name, "protocol": "paper-aligned-one-additional-iteration-v1", "mechanism_source": "arxiv:2608.17981", "fresh_row_range": {"start": c.FRESH_ROW_START, "end_exclusive": c.FRESH_ROW_END, "count_per_shard": c.FRESH_ROW_COUNT}, "window_token_count": c.WINDOW_TOKENS, "fit_window_count": c.FIT_WINDOW_COUNT, "assessment_window_count": c.ASSESSMENT_WINDOW_COUNT, "candidate_pairs": [list(pair) for pair in c.CANDIDATE_PAIRS], "fit_alpha": c.FIT_ALPHA, "fit_beta": c.FIT_BETA, "evaluation_alpha": c.EVALUATION_ALPHA, "evaluation_beta": c.EVALUATION_BETA, "temperature_control": c.TEMPERATURE_CONTROL, "normalization": "source_l2_norm_to_destination_l2_norm", "selected_fit_config": selected_config, "locked_evaluation_config": locked_config.as_dict(), "paper_expected_pair": expected_pair, "controls": list(c.CONTROL_NAMES), "network_access": False, "training": False, "weights_frozen": True, "evidence_ledger_mutation": False, "assessment_authorized_by_review": True, "selection_policy": "first-64-eligible-1024-token-windows-per-disjoint-v5-source-split"}
    config["config_sha256"] = c.digest(config)
    results = {**common, "network_access": False, "training": False, "weights_frozen": True, "evidence_ledger_mutation": False, "parity": parity_value, "fit_baseline": fit_baseline, "fit_candidates": fit_candidates, "selected_fit_config": selected_config, "locked_evaluation_config": locked_config.as_dict(), "paper_expected_pair": expected_pair, "assessment_baseline": assessment_baseline, "assessment_selected": assessment_selected, "assessment_temperature_baseline": temperature_baseline, "assessment_temperature_selected": temperature_selected, "assessment_repeat": repeat, "deterministic_repeat_passed": repeat == assessment_selected, "qualification": {"nonzero_intervention_reach": any(item["metrics"]["mean_nll"] != fit_baseline["mean_nll"] for item in fit_candidates)}, "controls": controls, "assessment_per_document": per_document, "assessment_nll_delta_selected_minus_baseline": bootstrap["mean_delta"], "bootstrap": bootstrap, "decision": decision, "paper_expected_pair_recovered": (selected_config["source_layer"], selected_config["destination_layer"]) == (11, 4), "local_only": True}
    results["results_sha256"] = c.digest(results)
    receipt = {**common, "config_sha256": config["config_sha256"], "results_sha256": results["results_sha256"], "zero_alpha_parity_passed": True, "nonzero_intervention_reach": results["qualification"]["nonzero_intervention_reach"], "deterministic_repeat_passed": results["deterministic_repeat_passed"], "network_access": False, "training": False, "weights_frozen": True, "evidence_ledger_mutation": False, "bootstrap": bootstrap, "decision": decision}
    receipt["receipt_sha256"] = c.digest(receipt)
    return {"config": config, "results": results, "receipt": receipt, "corpus": corpus["manifest"], "model_manifest": model_manifest_before}


def stage_corpus(source_root: Path, corpus_root: Path, model_path: Path = c.MODEL_PATH, review_receipt: Path = c.REVIEW_RECEIPT_PATH, raw_root: Path = c.RAW_ROOT, prior_root: Path = c.R1_SOURCE_ROOT) -> dict[str, Any]:
    _require_native_sandbox()
    source = c.exact_path(source_root, c.SOURCE_ROOT, "V5 source root")
    final = c.exact_path(corpus_root, c.CORPUS_ROOT, "V5 corpus root")
    model = c.exact_path(model_path, c.MODEL_PATH, "model path")
    raw = c.exact_path(raw_root, c.RAW_ROOT, "V5 raw root")
    prior = c.exact_path(prior_root, c.R1_SOURCE_ROOT, "V5 prior-pilot source root")
    if final.exists() or final.is_symlink():
        raise FileExistsError(f"refusing to overwrite V5 corpus root: {final}")
    review_snapshot = _review_snapshot(review_receipt)
    source_validation = validator.validate_source(source, raw, prior, review_receipt)
    input_snapshot = _input_snapshot(source, None, raw, prior, model)
    _assert_review_snapshot(review_snapshot)
    _assert_input_snapshot(input_snapshot, source, None, raw, prior, model)
    staging = Path(tempfile.mkdtemp(prefix=f".{final.name}.staging-", dir=final.parent))
    try:
        entries: dict[str, list[dict[str, Any]]] = {}
        with c.network_block():
            tokenizer = _load_tokenizer(model)
            for split, count in (("fit", c.FIT_WINDOW_COUNT), ("assessment", c.ASSESSMENT_WINDOW_COUNT)):
                rows = validator._jsonl(source / f"{split}/fineweb_edu.jsonl", f"V5 {split} source")
                split_entries = []
                for row in rows:
                    if len(split_entries) >= count:
                        break
                    token_ids = list(tokenizer.encode(row["text"], add_special_tokens=False))
                    if len(token_ids) < c.WINDOW_TOKENS:
                        continue
                    ids = token_ids[:c.WINDOW_TOKENS]
                    text = tokenizer.decode(ids)
                    if list(tokenizer.encode(text, add_special_tokens=False)) != ids:
                        raise ValueError(f"V5 tokenizer round-trip failed: {row['document_id']}")
                    relative = f"{split}/window-{len(split_entries):06d}.txt"
                    destination = staging / relative
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    encoded = text.encode("utf-8")
                    destination.write_bytes(encoded)
                    split_entries.append({"dataset": "fineweb_edu", "document_id": row["document_id"], "path": relative, "window_ordinal": 0, "byte_len": len(encoded), "source_sha256": hashlib.sha256(row["text"].encode("utf-8")).hexdigest(), "text_sha256": hashlib.sha256(encoded).hexdigest(), "token_count": c.WINDOW_TOKENS, "source_row_index": row["source_row_index"], "source_path": row["source_path"]})
                if len(split_entries) != count:
                    raise ValueError(f"V5 {split} produced {len(split_entries)} windows; expected {count}")
                entries[split] = split_entries
        manifest_body = {"schema": c.CORPUS_SCHEMA, "state_slice": c.STATE_SLICE, "claim_ceiling": c.CLAIM_CEILING, "source_manifest_sha256": source_validation["source_manifest_sha256"], "review_receipt_sha256": review_snapshot["review_sha256"], "model_path": str(c.MODEL_PATH), "model_manifest_sha256": c.model_manifest(model)["manifest_sha256"], "window_token_count": c.WINDOW_TOKENS, "tokenizer": "mlx_lm.utils.load_tokenizer:add_special_tokens=False", "selection_policy": "first-64-eligible-1024-token-windows-per-disjoint-v5-source-split", "fit_window_count": c.FIT_WINDOW_COUNT, "assessment_window_count": c.ASSESSMENT_WINDOW_COUNT, "fit_windows": entries["fit"], "assessment_windows": entries["assessment"], "network_access": False, "training": False, "scientific_execution": False, "evidence_ledger_mutation": False}
        _write_json(staging / "manifest.json", {**manifest_body, "manifest_sha256": c.digest(manifest_body)})
        _assert_review_snapshot(review_snapshot)
        _assert_input_snapshot(input_snapshot, source, None, raw, prior, model)
        c.exact_file_set(staging, _expected_corpus_files(), "V5 staged corpus")
        validation = validator.validate_corpus(staging, source, raw, prior, model, source_validation["source_manifest_sha256"], review_receipt)
        _assert_review_snapshot(review_snapshot)
        _assert_input_snapshot(input_snapshot, source, None, raw, prior, model)
        output_files = _expected_corpus_files()
        output_snapshot = c.snapshot_files(staging, output_files, "V5 staged corpus")
        if c.snapshot_files(staging, output_files, "V5 staged corpus") != output_snapshot:
            raise RuntimeError("V5 staged corpus changed before publication")
        c.publish_no_replace(staging, final, "V5 corpus", output_files)
        return {"manifest": _json(final / "manifest.json", "V5 corpus manifest"), "validation": validation}
    except Exception:
        if staging.exists() and staging.is_dir():
            shutil.rmtree(staging)
        raise


def _write_validator_receipt(staging: Path, results_sha: str, review_sha: str) -> None:
    body = {"schema": "gemma3-fineweb-edu-replication-v5-validator-receipt", "state_slice": c.STATE_SLICE, "result_sha256": results_sha, "review_receipt_sha256": review_sha, "independent_recomputation": True}
    _write_json(staging / "validator-receipt.json", {**body, "receipt_sha256": c.digest(body)})


def run_campaign(result_root: Path, source_root: Path, corpus_root: Path, raw_root: Path = c.RAW_ROOT, prior_root: Path = c.R1_SOURCE_ROOT, model_path: Path = c.MODEL_PATH, review_receipt: Path = c.REVIEW_RECEIPT_PATH) -> dict[str, Any]:
    _require_native_sandbox()
    source = c.exact_path(source_root, c.SOURCE_ROOT, "V5 source root")
    corpus = c.exact_path(corpus_root, c.CORPUS_ROOT, "V5 corpus root")
    raw = c.exact_path(raw_root, c.RAW_ROOT, "V5 raw root")
    prior = c.exact_path(prior_root, c.R1_SOURCE_ROOT, "V5 prior-pilot source root")
    final = c.exact_path(result_root, c.RESULT_ROOT, "V5 result root")
    model = c.exact_path(model_path, c.MODEL_PATH, "model path")
    if final.exists() or final.is_symlink():
        raise FileExistsError(f"refusing to overwrite V5 result root: {final}")
    review_snapshot = _review_snapshot(review_receipt)
    source_validation = validator.validate_source(source, raw, prior, review_receipt)
    corpus_validation = validator.validate_corpus(corpus, source, raw, prior, model, source_validation["source_manifest_sha256"], review_receipt)
    input_snapshot = _input_snapshot(source, corpus, raw, prior, model)
    _assert_review_snapshot(review_snapshot)
    _assert_input_snapshot(input_snapshot, source, corpus, raw, prior, model)
    staging = Path(tempfile.mkdtemp(prefix=f".{final.name}.staging-", dir=final.parent))
    try:
        (staging / "review-receipt.json").write_bytes(review_snapshot["review_bytes"])
        _assert_review_snapshot(review_snapshot)
        _assert_input_snapshot(input_snapshot, source, corpus, raw, prior, model)
        payload = _run_effects(model, corpus, review_snapshot["review_sha256"], source_validation["source_manifest_sha256"], input_snapshot, source, raw, prior, review_snapshot)
        _assert_review_snapshot(review_snapshot)
        _assert_input_snapshot(input_snapshot, source, corpus, raw, prior, model)
        _write_json(staging / "config.json", payload["config"])
        _write_json(staging / "results.json", payload["results"])
        _write_json(staging / "receipt.json", payload["receipt"])
        _write_json(staging / "corpus-manifest.json", payload["corpus"])
        _write_json(staging / "model-manifest.json", payload["model_manifest"])
        _write_validator_receipt(staging, payload["results"]["results_sha256"], review_snapshot["review_sha256"])
        c.exact_file_set(staging, {"config.json", "results.json", "receipt.json", "corpus-manifest.json", "model-manifest.json", "review-receipt.json", "validator-receipt.json"}, "V5 staged result")
        environment = os.environ.copy()
        environment["PYTHONDONTWRITEBYTECODE"] = "1"
        command = [sys.executable, "-B", "-m", VALIDATOR_MODULE, "--mode", "result", "--source-root", str(source), "--raw-root", str(raw), "--prior-root", str(prior), "--corpus-root", str(corpus), "--result-root", str(staging), "--model", str(model), "--review-receipt", str(c.REVIEW_RECEIPT_PATH), "--corpus-manifest-sha256", corpus_validation["corpus_manifest_sha256"]]
        completed = subprocess.run(command, cwd=REPO_ROOT, env=environment, capture_output=True, text=True, check=False)
        if completed.returncode != 0:
            raise RuntimeError(f"V5 result validator failed:\n{completed.stdout}\n{completed.stderr}")
        validation = json.loads(completed.stdout)
        if validation.get("valid") is not True:
            raise RuntimeError(f"V5 result validator returned invalid output: {validation}")
        _assert_review_snapshot(review_snapshot)
        _assert_input_snapshot(input_snapshot, source, corpus, raw, prior, model)
        if c.sha256_file(staging / "results.json") != payload["results"]["results_sha256"]:
            raise RuntimeError("V5 result changed after validation")
        _assert_review_snapshot(review_snapshot)
        _assert_input_snapshot(input_snapshot, source, corpus, raw, prior, model)
        output_files = {"config.json", "results.json", "receipt.json", "corpus-manifest.json", "model-manifest.json", "review-receipt.json", "validator-receipt.json"}
        output_snapshot = c.snapshot_files(staging, output_files, "V5 staged result")
        if c.snapshot_files(staging, output_files, "V5 staged result") != output_snapshot:
            raise RuntimeError("V5 staged result changed before publication")
        c.publish_no_replace(staging, final, "V5 result", output_files)
        return {**payload, "validation": validation}
    except Exception:
        if staging.exists() and staging.is_dir():
            shutil.rmtree(staging)
        raise


def main() -> int:
    _enter_native_sandbox()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--corpus-root", type=Path, required=True)
    parser.add_argument("--result-root", type=Path)
    parser.add_argument("--raw-root", type=Path, default=c.RAW_ROOT)
    parser.add_argument("--prior-root", type=Path, default=c.R1_SOURCE_ROOT)
    parser.add_argument("--model", type=Path, default=c.MODEL_PATH)
    parser.add_argument("--review-receipt", type=Path, default=c.REVIEW_RECEIPT_PATH)
    parser.add_argument("--stage-only", action="store_true")
    args = parser.parse_args()
    if args.stage_only:
        value = stage_corpus(args.source_root, args.corpus_root, args.model, args.review_receipt, args.raw_root, args.prior_root)
    else:
        if args.result_root is None:
            parser.error("execution requires --result-root")
        value = run_campaign(args.result_root, args.source_root, args.corpus_root, args.raw_root, args.prior_root, args.model, args.review_receipt)
    print(json.dumps(value, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
