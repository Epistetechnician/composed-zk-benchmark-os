#!/usr/bin/env python3
"""Review-gated, self-contained V4 Gemma3 FineWeb-Edu replication runner.

State slice: continual-learning-gemma3-fineweb-edu-replication-v4.
The reviewed file owns the tokenizer load, Gemma3 forward seam, residual
intervention, metrics, controls, and result binding. V1/V2/V3 runners and
scientific artifacts are not imported or used.
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

from experiments.continual_learning import gemma3_fineweb_edu_replication_v4_contract as c
from experiments.continual_learning import validate_gemma3_fineweb_edu_replication_v4 as validator

REPO_ROOT = c.REPO_ROOT
VALIDATOR_MODULE = "experiments.continual_learning.validate_gemma3_fineweb_edu_replication_v4"


def _json(path: Path, label: str) -> dict[str, Any]:
    return validator._json(path, label)


def _write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _enter_native_sandbox() -> None:
    if sys.platform != "darwin" or c.native_network_denied():
        return
    if os.environ.get("V4_SANDBOX_REEXEC_ATTEMPTED") == "1":
        raise RuntimeError("V4 native network sandbox could not be proven")
    sandbox = shutil.which("sandbox-exec")
    if sandbox is None:
        raise RuntimeError("V4 sandbox-exec is unavailable; execution is closed")
    environment = os.environ.copy()
    environment["V4_SANDBOX_REEXEC_ATTEMPTED"] = "1"
    profile = "(version 1) (deny network*) (allow default)"
    os.execvpe(sandbox, [sandbox, "-p", profile, sys.executable, "-B", str(Path(__file__).resolve()), *sys.argv[1:]], environment)


def _require_native_sandbox() -> None:
    if c.native_network_denied() is not True:
        raise RuntimeError("V4 native network denial is not proven")


def _review_snapshot(path: Path) -> dict[str, Any]:
    path = c.exact_path(path, c.REVIEW_RECEIPT_PATH, "V4 review receipt")
    review_bytes = c.regular(path, "V4 review receipt").read_bytes()
    validator.validate_review_receipt(path)
    return {
        "review_bytes": review_bytes,
        "review_sha256": c.sha256_file(path),
        "protocol_bytes": c.regular(c.PROTOCOL_PATH, "V4 protocol").read_bytes(),
        "packet_bytes": c.regular(c.REVIEW_PACKET_PATH, "V4 review packet").read_bytes(),
        "implementation_manifest_sha256": validator.implementation_manifest()["manifest_sha256"],
    }


def _assert_snapshot(path: Path, snapshot: dict[str, Any]) -> None:
    if c.regular(path, "V4 review receipt").read_bytes() != snapshot["review_bytes"] or c.sha256_file(path) != snapshot["review_sha256"]:
        raise RuntimeError("V4 review receipt snapshot changed")
    if c.regular(c.PROTOCOL_PATH, "V4 protocol").read_bytes() != snapshot["protocol_bytes"] or c.regular(c.REVIEW_PACKET_PATH, "V4 review packet").read_bytes() != snapshot["packet_bytes"]:
        raise RuntimeError("V4 protocol or packet snapshot changed")
    if validator.implementation_manifest()["manifest_sha256"] != snapshot["implementation_manifest_sha256"]:
        raise RuntimeError("V4 implementation snapshot changed")


def _load_tokenizer(model_path: Path) -> Any:
    if c.runtime_versions() != c.RUNTIME_VERSIONS:
        raise RuntimeError(f"V4 runtime mismatch: {c.runtime_versions()}")
    from mlx_lm.utils import load_tokenizer

    return load_tokenizer(model_path)


def load_runtime(model_path: Path) -> tuple[Any, Any, dict[str, str]]:
    if c.runtime_versions() != c.RUNTIME_VERSIONS:
        raise RuntimeError(f"V4 runtime mismatch: {c.runtime_versions()}")
    from mlx_lm import load

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
            raise ValueError("V4 layer pair is invalid")
        if isinstance(self.alpha, bool) or not isinstance(self.alpha, (int, float)) or isinstance(self.beta, bool) or not isinstance(self.beta, (int, float)) or isinstance(self.epsilon, bool) or not isinstance(self.epsilon, (int, float)) or self.alpha < 0 or self.alpha > 1 or not math.isfinite(self.alpha) or not math.isfinite(self.beta) or self.beta != 1.0 - self.alpha or not math.isfinite(self.epsilon) or self.epsilon <= 0:
            raise ValueError("V4 alpha/beta/epsilon contract is invalid")

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
        raise RuntimeError("V4 source activation was not captured")
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
    if not math.isfinite(temperature) or temperature <= 0:
        raise ValueError("V4 temperature must be finite and positive")
    total = 0.0
    for index, target in enumerate(token_ids[1:]):
        scaled = logits[index] / temperature
        total += -float((scaled - mx.logsumexp(scaled))[int(target)])
    return total, max(0, len(token_ids) - 1)


def evaluate_windows(model: Any, tokenizer: Any, windows: Iterable[Any], config: RecirculationConfig | None, *, temperature: float = 1.0) -> dict[str, Any]:
    import mlx.core as mx

    rows = []
    for window in windows:
        token_ids = tokenizer.encode(window.text, add_special_tokens=False)
        logits = logits_for_tokens(model, token_ids, config)
        nll, target_count = _nll(logits, token_ids, mx, temperature)
        rows.append({"dataset": window.dataset, "document_id": window.document_id, "window_ordinal": window.window_ordinal, "text_sha256": window.text_sha256, "token_count": len(token_ids), "target_count": target_count, "nll": round(nll, 9)})
    target_tokens = sum(row["target_count"] for row in rows)
    total_nll = sum(row["nll"] for row in rows)
    mean_nll = round(total_nll / target_tokens, 9) if target_tokens else float("nan")
    return {"temperature": temperature, "evaluation_config": config.as_dict() if config is not None else None, "mean_nll": mean_nll, "perplexity": round(math.exp(mean_nll), 9) if math.isfinite(mean_nll) else None, "target_tokens": target_tokens, "rows": rows}


def load_corpus(corpus_root: Path, tokenizer: Any) -> tuple[list[Any], list[Any], dict[str, Any]]:
    manifest = _json(corpus_root / "manifest.json", "V4 corpus manifest")
    fit = [validator.parse_window(corpus_root, item, tokenizer, "fit") for item in manifest["fit"]]
    assessment = [validator.parse_window(corpus_root, item, tokenizer, "assessment") for item in manifest["assessment"]]
    return fit, assessment, {"manifest": manifest, "manifest_sha256": manifest["manifest_sha256"]}


def parity_check(model: Any, window: Any) -> dict[str, Any]:
    import mlx.core as mx

    token_ids = window.token_ids
    if token_ids is None:
        raise ValueError("V4 parity requires token IDs attached by caller")
    layer_count = len(model.model.layers)
    source, destination = 11, 4
    if not 0 <= destination < source < layer_count:
        raise ValueError("V4 parity target is unavailable")
    native = logits_for_tokens(model, token_ids, None)
    zero = logits_for_tokens(model, token_ids, RecirculationConfig(source, destination, 0.0, 1.0))
    max_delta = max((float(mx.max(mx.abs(left - right))) for left, right in zip(native, zero, strict=True)), default=0.0)
    return {"dataset": window.dataset, "document_id": window.document_id, "text_sha256": window.text_sha256, "token_count": len(token_ids), "max_abs_logit_delta": max_delta, "tolerance": c.PARITY_TOLERANCE, "passed": max_delta <= c.PARITY_TOLERANCE}


def _metrics_finite(metrics: dict[str, Any], label: str) -> None:
    if not math.isfinite(float(metrics["mean_nll"])) or not math.isfinite(float(metrics["perplexity"])):
        raise ValueError(f"{label} metrics are nonfinite")


def _run_effects(model_path: Path, corpus_root: Path, review_sha: str, source_sha: str) -> dict[str, Any]:
    _require_native_sandbox()
    with c.network_block():
        model, tokenizer, runtime = load_runtime(model_path)
        if getattr(model.args, "model_type", None) != "gemma3_text" or len(model.model.layers) != 26:
            raise ValueError("V4 model architecture mismatch")
        parameter_before = c.model_parameter_digest(model)
        model_manifest_before = c.model_manifest(model_path)
        fit, assessment, corpus = load_corpus(corpus_root, tokenizer)
        parity_checks = [parity_check(model, window) for window in (*fit, *assessment)]
        if len(parity_checks) != 128 or not all(item["passed"] is True for item in parity_checks):
            raise RuntimeError("V4 zero-alpha parity gate failed")
        fit_baseline = evaluate_windows(model, tokenizer, fit, None)
        fit_candidates = []
        for source_layer, destination_layer in c.CANDIDATE_PAIRS:
            config = RecirculationConfig(source_layer, destination_layer, c.FIT_ALPHA, c.FIT_BETA)
            metrics = evaluate_windows(model, tokenizer, fit, config)
            _metrics_finite(metrics, "V4 fit candidate")
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
            raise RuntimeError("V4 frozen model custody changed during inference")
    for label, metrics in (("fit baseline", fit_baseline), ("assessment baseline", assessment_baseline), ("assessment selected", assessment_selected), ("temperature baseline", temperature_baseline), ("temperature selected", temperature_selected), ("repeat", repeat)):
        _metrics_finite(metrics, label)
    baseline_rows = {row["document_id"]: row for row in assessment_baseline["rows"]}
    selected_rows = {row["document_id"]: row for row in assessment_selected["rows"]}
    per_document = []
    for document_id in sorted(baseline_rows):
        base = baseline_rows[document_id]
        chosen = selected_rows[document_id]
        delta = chosen["nll"] / (c.WINDOW_TOKENS - 1) - base["nll"] / (c.WINDOW_TOKENS - 1)
        per_document.append({"dataset": "fineweb_edu", "document_id": document_id, "text_sha256": base["text_sha256"], "target_count": c.WINDOW_TOKENS - 1, "baseline_nll": base["nll"], "selected_nll": chosen["nll"], "delta_selected_minus_baseline": delta})
    deltas = [row["delta_selected_minus_baseline"] for row in per_document]
    bootstrap = c.bootstrap_mean_ci(deltas)
    decision = c.decide_replication(bootstrap)
    parity = {"sequence_count": 128, "max_abs_logit_delta": max(item["max_abs_logit_delta"] for item in parity_checks), "tolerance": c.PARITY_TOLERANCE, "all_passed": True, "checks": parity_checks}
    controls = {"native_baseline": assessment_baseline, "zero_alpha_identity": parity, "all_candidate_evaluations": fit_candidates, "temperature_1.20_baseline": temperature_baseline, "temperature_1.20_intervention": temperature_selected, "deterministic_repeat": repeat, "frozen_model_manifest": {"before": model_manifest_before["manifest_sha256"], "after": model_manifest_after["manifest_sha256"]}, "frozen_model_parameters": {"before": parameter_before, "after": parameter_after}}
    expected_pair = {"source_layer": 11, "destination_layer": 4}
    config = {"schema": c.RESULT_SCHEMA, "state_slice": c.STATE_SLICE, "claim_ceiling": c.CLAIM_CEILING, "protocol_sha256": c.PROTOCOL_SHA256, "review_receipt_sha256": review_sha, "source_manifest_sha256": source_sha, "corpus_manifest_sha256": corpus["manifest_sha256"], "model_name": model_path.name, "model_path": str(c.MODEL_PATH), "model_manifest_sha256": model_manifest_before["manifest_sha256"], "model_parameter_digest_before": parameter_before, "model_parameter_digest_after": parameter_after, "architecture": "gemma3_text", "model_type": "gemma3_text", "layer_count": 26, "runtime": runtime, "protocol": "paper-aligned-one-additional-iteration-v1", "mechanism_source": "arxiv:2608.17981", "fresh_row_range": {"start": c.FRESH_ROW_START, "end_exclusive": c.FRESH_ROW_END, "count_per_shard": c.FRESH_ROW_COUNT}, "window_token_count": c.WINDOW_TOKENS, "fit_window_count": c.FIT_WINDOW_COUNT, "assessment_window_count": c.ASSESSMENT_WINDOW_COUNT, "candidate_pairs": [list(pair) for pair in c.CANDIDATE_PAIRS], "fit_alpha": c.FIT_ALPHA, "fit_beta": c.FIT_BETA, "evaluation_alpha": c.EVALUATION_ALPHA, "evaluation_beta": c.EVALUATION_BETA, "temperature_control": c.TEMPERATURE_CONTROL, "normalization": "source_l2_norm_to_destination_l2_norm", "selected_fit_config": selected_config, "locked_evaluation_config": locked_config.as_dict(), "paper_expected_pair": expected_pair, "controls": list(c.CONTROL_NAMES), "network_access": False, "training": False, "weights_frozen": True, "evidence_ledger_mutation": False, "assessment_authorized_by_review": True, "selection_policy": c.SELECTION_POLICY}
    config["config_sha256"] = c.digest(config)
    results = {"schema": c.RESULT_SCHEMA, "state_slice": c.STATE_SLICE, "claim_ceiling": c.CLAIM_CEILING, "protocol_sha256": c.PROTOCOL_SHA256, "review_receipt_sha256": review_sha, "source_manifest_sha256": source_sha, "corpus_manifest_sha256": corpus["manifest_sha256"], "model_path": str(c.MODEL_PATH), "model_manifest_sha256": model_manifest_before["manifest_sha256"], "model_parameter_digest_before": parameter_before, "model_parameter_digest_after": parameter_after, "architecture": "gemma3_text", "model_type": "gemma3_text", "layer_count": 26, "runtime": runtime, "network_access": False, "training": False, "weights_frozen": True, "evidence_ledger_mutation": False, "parity": parity, "fit_baseline": fit_baseline, "fit_candidates": fit_candidates, "selected_fit_config": selected_config, "locked_evaluation_config": locked_config.as_dict(), "paper_expected_pair": expected_pair, "assessment_baseline": assessment_baseline, "assessment_selected": assessment_selected, "assessment_temperature_baseline": temperature_baseline, "assessment_temperature_selected": temperature_selected, "assessment_repeat": repeat, "deterministic_repeat_passed": repeat == assessment_selected, "qualification": {"nonzero_intervention_reach": any(item["metrics"]["mean_nll"] != fit_baseline["mean_nll"] for item in fit_candidates)}, "controls": controls, "assessment_per_document": per_document, "assessment_nll_delta_selected_minus_baseline": sum(deltas) / len(deltas), "bootstrap": bootstrap, "decision": decision, "paper_expected_pair_recovered": (selected_config["source_layer"], selected_config["destination_layer"]) == (11, 4), "local_only": True}
    results["results_sha256"] = c.digest(results)
    receipt = {"schema": c.RESULT_SCHEMA, "state_slice": c.STATE_SLICE, "claim_ceiling": c.CLAIM_CEILING, "protocol_sha256": c.PROTOCOL_SHA256, "review_receipt_sha256": review_sha, "source_manifest_sha256": source_sha, "corpus_manifest_sha256": corpus["manifest_sha256"], "config_sha256": config["config_sha256"], "results_sha256": results["results_sha256"], "model_manifest_sha256": model_manifest_before["manifest_sha256"], "model_parameter_digest_before": parameter_before, "model_parameter_digest_after": parameter_after, "zero_alpha_parity_passed": True, "nonzero_intervention_reach": results["qualification"]["nonzero_intervention_reach"], "deterministic_repeat_passed": results["deterministic_repeat_passed"], "network_access": False, "training": False, "weights_frozen": True, "evidence_ledger_mutation": False, "bootstrap": bootstrap, "decision": decision}
    receipt["receipt_sha256"] = c.digest(receipt)
    return {"config": config, "results": results, "receipt": receipt, "corpus": corpus, "model_manifest": model_manifest_before}


def stage_corpus(source_root: Path, corpus_root: Path, model_path: Path = c.MODEL_PATH, review_receipt: Path = c.REVIEW_RECEIPT_PATH) -> dict[str, Any]:
    _require_native_sandbox()
    snapshot = _review_snapshot(review_receipt)
    source_root = c.exact_path(source_root, c.SOURCE_ROOT, "V4 source root")
    corpus_root = c.exact_path(corpus_root, c.CORPUS_ROOT, "V4 corpus root")
    model_path = c.exact_path(model_path, c.MODEL_PATH, "model path")
    if corpus_root.exists() or corpus_root.is_symlink():
        raise FileExistsError(f"refusing to overwrite V4 corpus root: {corpus_root}")
    source = validator.validate_source(source_root, c.RAW_ROOT, c.R1_SOURCE_ROOT, review_receipt)
    if c.model_manifest(model_path)["manifest_sha256"] != c.EXPECTED_MODEL_MANIFEST_SHA256:
        raise ValueError("V4 model manifest mismatch before tokenizer load")
    staging = Path(tempfile.mkdtemp(prefix=f".{corpus_root.name}.staging-", dir=corpus_root.parent))
    try:
        _assert_snapshot(review_receipt, snapshot)
        with c.network_block():
            tokenizer = _load_tokenizer(model_path)
            fit_rows = validator._jsonl(source_root / "fit/fineweb_edu.jsonl", "V4 fit source")
            assessment_rows = validator._jsonl(source_root / "assessment/fineweb_edu.jsonl", "V4 assessment source")
            entries = {}
            for split, rows, count in (("fit", fit_rows, c.FIT_WINDOW_COUNT), ("assessment", assessment_rows, c.ASSESSMENT_WINDOW_COUNT)):
                split_entries = []
                for row in rows:
                    if len(split_entries) >= count:
                        break
                    token_ids = list(tokenizer.encode(row["text"], add_special_tokens=False))
                    if len(token_ids) < c.WINDOW_TOKENS:
                        continue
                    ids = token_ids[: c.WINDOW_TOKENS]
                    text = tokenizer.decode(ids)
                    if list(tokenizer.encode(text, add_special_tokens=False)) != ids:
                        raise ValueError(f"V4 tokenizer round-trip failed: {row['document_id']}")
                    relative = f"{split}/fineweb_edu/window-{len(split_entries):06d}.txt"
                    destination = staging / relative
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    encoded = text.encode("utf-8")
                    destination.write_bytes(encoded)
                    split_entries.append({"dataset": "fineweb_edu", "document_id": row["document_id"], "path": relative, "window_ordinal": 0, "byte_len": len(encoded), "source_sha256": hashlib.sha256(row["text"].encode("utf-8")).hexdigest(), "text_sha256": hashlib.sha256(encoded).hexdigest(), "token_count": c.WINDOW_TOKENS, "source_row_index": row["source_row_index"], "source_path": row["source_path"]})
                if len(split_entries) != count:
                    raise ValueError(f"V4 {split} produced {len(split_entries)} windows; expected {count}")
                entries[split] = split_entries
        body = {"schema": c.CORPUS_SCHEMA, "state_slice": c.STATE_SLICE, "claim_ceiling": c.CLAIM_CEILING, "source_manifest_sha256": source["source_manifest_sha256"], "review_receipt_sha256": snapshot["review_sha256"], "window_token_count": c.WINDOW_TOKENS, "selection_policy": c.SELECTION_POLICY, "fit_window_count": c.FIT_WINDOW_COUNT, "assessment_window_count": c.ASSESSMENT_WINDOW_COUNT, "fit": entries["fit"], "assessment": entries["assessment"], "network_access": False, "training": False, "scientific_execution": False, "evidence_ledger_mutation": False}
        manifest = {**body, "manifest_sha256": c.digest(body)}
        _write_json(staging / "manifest.json", manifest)
        _assert_snapshot(review_receipt, snapshot)
        validation = validator.validate_corpus(staging, source_root, c.RAW_ROOT, c.R1_SOURCE_ROOT, model_path, source["source_manifest_sha256"], review_receipt)
        os.replace(staging, corpus_root)
        return {"manifest": manifest, "validation": validation}
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise


def run_campaign(result_root: Path, source_root: Path, corpus_root: Path, raw_root: Path = c.RAW_ROOT, r1_source_root: Path = c.R1_SOURCE_ROOT, model_path: Path = c.MODEL_PATH, review_receipt: Path = c.REVIEW_RECEIPT_PATH) -> dict[str, Any]:
    _require_native_sandbox()
    snapshot = _review_snapshot(review_receipt)
    source_root = c.exact_path(source_root, c.SOURCE_ROOT, "V4 source root")
    corpus_root = c.exact_path(corpus_root, c.CORPUS_ROOT, "V4 corpus root")
    raw_root = c.exact_path(raw_root, c.RAW_ROOT, "V4 raw root")
    r1_source_root = c.exact_path(r1_source_root, c.R1_SOURCE_ROOT, "V4 prior-pilot source root")
    result_root = c.exact_path(result_root, c.RESULT_ROOT, "V4 result root")
    model_path = c.exact_path(model_path, c.MODEL_PATH, "model path")
    if result_root.exists() or result_root.is_symlink():
        raise FileExistsError(f"refusing to overwrite V4 result root: {result_root}")
    if c.model_manifest(model_path)["manifest_sha256"] != c.EXPECTED_MODEL_MANIFEST_SHA256:
        raise ValueError("V4 model manifest mismatch before validation/load")
    source = validator.validate_source(source_root, raw_root, r1_source_root, review_receipt)
    corpus_validation = validator.validate_corpus(corpus_root, source_root, raw_root, r1_source_root, model_path, source["source_manifest_sha256"], review_receipt)
    staging = Path(tempfile.mkdtemp(prefix=f".{result_root.name}.staging-", dir=result_root.parent))
    try:
        (staging / "review-receipt.json").write_bytes(snapshot["review_bytes"])
        _assert_snapshot(review_receipt, snapshot)
        payload = _run_effects(model_path, corpus_root, snapshot["review_sha256"], source["source_manifest_sha256"])
        _assert_snapshot(review_receipt, snapshot)
        _write_json(staging / "config.json", payload["config"])
        _write_json(staging / "results.json", payload["results"])
        _write_json(staging / "receipt.json", payload["receipt"])
        _write_json(staging / "corpus-manifest.json", payload["corpus"])
        _write_json(staging / "model-manifest.json", payload["model_manifest"])
        environment = os.environ.copy()
        environment["PYTHONDONTWRITEBYTECODE"] = "1"
        command = [sys.executable, "-B", "-m", VALIDATOR_MODULE, "--mode", "result", "--source-root", str(source_root), "--raw-root", str(raw_root), "--r1-source-root", str(r1_source_root), "--corpus-root", str(corpus_root), "--result-root", str(staging), "--model", str(model_path), "--review-receipt", str(staging / "review-receipt.json"), "--corpus-manifest-sha256", corpus_validation["corpus_manifest_sha256"]]
        completed = subprocess.run(command, cwd=REPO_ROOT, env=environment, capture_output=True, text=True, check=False)
        if completed.returncode != 0:
            raise RuntimeError(f"V4 result validator failed:\n{completed.stdout}\n{completed.stderr}")
        validation = json.loads(completed.stdout)
        if validation.get("valid") is not True:
            raise RuntimeError(f"V4 result validator returned invalid output: {validation}")
        _assert_snapshot(review_receipt, snapshot)
        _write_json(staging / "validator-receipt.json", validation)
        os.replace(staging, result_root)
        return {**payload, "validation": validation}
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise


def main() -> int:
    _enter_native_sandbox()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--corpus-root", type=Path, required=True)
    parser.add_argument("--result-root", type=Path, required=True)
    parser.add_argument("--raw-root", type=Path, default=c.RAW_ROOT)
    parser.add_argument("--r1-source-root", type=Path, default=c.R1_SOURCE_ROOT)
    parser.add_argument("--model", type=Path, default=c.MODEL_PATH)
    parser.add_argument("--review-receipt", type=Path, default=c.REVIEW_RECEIPT_PATH)
    parser.add_argument("--stage-only", action="store_true")
    args = parser.parse_args()
    value = stage_corpus(args.source_root, args.corpus_root, args.model, args.review_receipt) if args.stage_only else run_campaign(args.result_root, args.source_root, args.corpus_root, args.raw_root, args.r1_source_root, args.model, args.review_receipt)
    print(json.dumps(value, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
