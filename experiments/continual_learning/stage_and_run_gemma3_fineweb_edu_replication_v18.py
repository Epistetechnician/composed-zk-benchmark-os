#!/usr/bin/env python3
"""Review-gated V18 corpus stage and offline Gemma3 runner.

State slice: continual-learning-gemma3-fineweb-edu-replication-v18.
No model or scientific effect is reachable until the V18 receipt validates.
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

from experiments.continual_learning import (
    gemma3_fineweb_edu_replication_v18_contract as c,
)
from experiments.continual_learning import (
    validate_gemma3_fineweb_edu_replication_v18 as v,
)

VALIDATOR = "experiments.continual_learning.validate_gemma3_fineweb_edu_replication_v18"


def _json(path: Path, label: str) -> dict[str, Any]:
    return v.obj(path, label)


def _write(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def _sandbox() -> None:
    if sys.platform != "darwin" or c.native_network_denied():
        return
    if os.environ.get("V18_RUN_REEXEC") == "1":
        raise RuntimeError("V18 native network denial could not be established")
    executable = shutil.which("sandbox-exec")
    if executable is None:
        raise RuntimeError("sandbox-exec is unavailable")
    env = os.environ.copy()
    env["V18_RUN_REEXEC"] = "1"
    os.execvpe(
        executable,
        [
            executable,
            "-p",
            "(version 1) (deny network*) (allow default)",
            sys.executable,
            "-B",
            str(Path(__file__).resolve()),
            *sys.argv[1:],
        ],
        env,
    )


def _review(receipt: Path) -> dict[str, Any]:
    value = c.validate_review_receipt(receipt)
    snapshot = c.snapshot_code()
    snapshot["review_sha256"] = c.sha256_file(
        c.exact_path(receipt, c.RECEIPT_PATH, "V18 receipt")
    )
    return snapshot | {"review": value}


def _assert_review(snapshot: dict[str, Any]) -> None:
    c.assert_code_snapshot(
        {key: snapshot[key] for key in ("protocol", "packet", "receipt", "implementation", "history")}
    )


def _expected_corpus_files() -> set[str]:
    return {
        "manifest.json",
        *{
            f"{split}/window-{i:06d}.txt"
            for split in ("fit", "assessment")
            for i in range(64)
        },
    }


@dataclass(frozen=True)
class RecirculationConfig:
    source_layer: int
    destination_layer: int
    alpha: float
    beta: float
    epsilon: float = c.EPSILON

    def validate(self, layer_count: int) -> None:
        if (
            isinstance(self.source_layer, bool)
            or not isinstance(self.source_layer, int)
            or isinstance(self.destination_layer, bool)
            or not isinstance(self.destination_layer, int)
            or not 0 <= self.destination_layer < self.source_layer < layer_count
        ):
            raise ValueError("V18 layer pair invalid")
        if (
            any(
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not math.isfinite(float(value))
                for value in (self.alpha, self.beta, self.epsilon)
            )
            or not 0 <= self.alpha <= 1
            or self.beta != 1 - self.alpha
            or self.epsilon <= 0
        ):
            raise ValueError("V18 recirculation parameters invalid")

    def as_dict(self) -> dict[str, Any]:
        return {
            "source_layer": self.source_layer,
            "destination_layer": self.destination_layer,
            "alpha": self.alpha,
            "beta": self.beta,
            "epsilon": self.epsilon,
        }


def load_tokenizer(model_path: Path) -> Any:
    model_path = c.exact_path(model_path, c.MODEL_PATH, "model path")
    manifest = c.model_manifest(model_path)
    if (
        manifest["manifest_sha256"] != c.MODEL_STABLE_MANIFEST_SHA256
        or manifest["cache_manifest_sha256"] != c.MODEL_CACHE_MANIFEST_SHA256
        or c.runtime_versions() != c.RUNTIME_VERSIONS
    ):
        raise RuntimeError("V18 tokenizer custody/runtime mismatch")
    c.require_native_network_denial()
    from mlx_lm.utils import load_tokenizer

    with c.network_block():
        return load_tokenizer(str(model_path))


def load_runtime(model_path: Path) -> tuple[Any, Any, dict[str, str]]:
    model_path = c.exact_path(model_path, c.MODEL_PATH, "model path")
    manifest = c.model_manifest(model_path)
    if (
        manifest["manifest_sha256"] != c.MODEL_STABLE_MANIFEST_SHA256
        or manifest["cache_manifest_sha256"] != c.MODEL_CACHE_MANIFEST_SHA256
        or c.runtime_versions() != c.RUNTIME_VERSIONS
    ):
        raise RuntimeError("V18 model custody/runtime mismatch")
    c.require_native_network_denial()
    from mlx_lm import load

    with c.network_block():
        model, tokenizer = load(str(model_path), tokenizer_config=None)
    return model, tokenizer, dict(c.RUNTIME_VERSIONS)


def _components(model: Any) -> tuple[Any, Any]:
    inner = getattr(model, "model", None)
    if (
        inner is None
        or not hasattr(inner, "layers")
        or not hasattr(inner, "embed_tokens")
        or not hasattr(model, "lm_head")
    ):
        raise TypeError("Gemma3 text seam unavailable")
    return inner, model


def _mix(mx: Any, source: Any, destination: Any, config: RecirculationConfig) -> Any:
    source_norm = mx.sqrt(mx.sum(mx.square(source), axis=-1, keepdims=True))
    destination_norm = mx.sqrt(mx.sum(mx.square(destination), axis=-1, keepdims=True))
    return config.beta * destination + config.alpha * source * (
        destination_norm / mx.maximum(source_norm, mx.array(config.epsilon))
    )


def logits_for_tokens(
    model: Any, token_ids: Sequence[int], config: RecirculationConfig | None = None
) -> list[Any]:
    import mlx.core as mx

    inner, text_model = _components(model)
    layer_count = len(inner.layers)
    if config is not None:
        config.validate(layer_count)
    cache = model.make_cache()
    outputs = []
    previous = None
    for token_id in token_ids:
        if config is None:
            logits = model(mx.array([[int(token_id)]], dtype=mx.int32), cache=cache)
        else:
            from mlx_lm.models.base import create_attention_mask

            hidden = inner.embed_tokens(mx.array([[int(token_id)]], dtype=mx.int32))
            hidden *= mx.array(inner.args.hidden_size**0.5, mx.bfloat16).astype(
                hidden.dtype
            )
            global_mask = create_attention_mask(
                hidden, cache[inner.sliding_window_pattern - 1]
            )
            sliding_mask = create_attention_mask(
                hidden, cache[0], window_size=inner.window_size
            )
            current = None
            for index, (layer, layer_cache) in enumerate(
                zip(inner.layers, cache, strict=True)
            ):
                hidden = layer(
                    hidden,
                    global_mask
                    if index % inner.sliding_window_pattern
                    == inner.sliding_window_pattern - 1
                    else sliding_mask,
                    layer_cache,
                )
                if (
                    index == config.destination_layer
                    and previous is not None
                    and config.alpha != 0
                ):
                    hidden = _mix(mx, previous, hidden, config)
                if index == config.source_layer:
                    current = hidden
            if current is None:
                raise RuntimeError("V18 source activation not captured")
            logits, previous = text_model.lm_head(inner.norm(hidden)), current
        mx.eval(logits)
        outputs.append(logits[0, -1, :])
        if previous is not None:
            mx.eval(previous)
    if outputs:
        mx.eval(*outputs)
    return outputs


def evaluate_windows(
    model: Any,
    tokenizer: Any,
    windows: Iterable[v.Window],
    config: RecirculationConfig | None,
    temperature: float = 1.0,
) -> dict[str, Any]:
    import mlx.core as mx

    if (
        isinstance(temperature, bool)
        or not isinstance(temperature, (int, float))
        or not math.isfinite(float(temperature))
        or temperature <= 0
    ):
        raise ValueError("V18 temperature invalid")
    rows = []
    for window in windows:
        ids = list(tokenizer.encode(window.text, add_special_tokens=False))
        if tuple(ids) != window.token_ids or len(ids) != c.WINDOW_TOKENS:
            raise ValueError("V18 tokenizer changed")
        logits = logits_for_tokens(model, ids, config)
        total = 0.0
        for index, target in enumerate(ids[1:]):
            scaled = logits[index] / temperature
            total += -float((scaled - mx.logsumexp(scaled))[int(target)])
        if not math.isfinite(total):
            raise ValueError("V18 NLL invalid")
        rows.append(
            {
                "dataset": window.dataset,
                "document_id": window.document_id,
                "relative_path": window.relative_path,
                "window_ordinal": 0,
                "source_sha256": window.source_sha256,
                "text_sha256": window.text_sha256,
                "token_count": len(ids),
                "target_count": len(ids) - 1,
                "nll": round(total, 9),
            }
        )
    targets = sum(row["target_count"] for row in rows)
    mean = round(sum(row["nll"] for row in rows) / targets, 9)
    return {
        "temperature": float(temperature),
        "evaluation_config": config.as_dict() if config else None,
        "mean_nll": mean,
        "perplexity": round(math.exp(mean), 9),
        "target_tokens": targets,
        "rows": rows,
    }


def parity(model: Any, windows: Sequence[v.Window]) -> dict[str, Any]:
    import mlx.core as mx

    checks = []
    for window in windows:
        native, zero = (
            logits_for_tokens(model, window.token_ids),
            logits_for_tokens(
                model, window.token_ids, RecirculationConfig(11, 4, 0.0, 1.0)
            ),
        )
        maximum = max(
            (
                float(mx.max(mx.abs(left - right)))
                for left, right in zip(native, zero, strict=True)
            ),
            default=0.0,
        )
        checks.append(
            {
                "dataset": window.dataset,
                "document_id": window.document_id,
                "relative_path": window.relative_path,
                "source_sha256": window.source_sha256,
                "text_sha256": window.text_sha256,
                "token_count": len(window.token_ids),
                "max_abs_logit_delta": maximum,
                "tolerance": c.PARITY_TOLERANCE,
                "passed": maximum <= c.PARITY_TOLERANCE,
            }
        )
    if len(checks) != 128 or not all(item["passed"] is True for item in checks):
        raise RuntimeError("V18 zero-alpha parity failed")
    return {
        "sequence_count": len(checks),
        "max_abs_logit_delta": max(item["max_abs_logit_delta"] for item in checks),
        "tolerance": c.PARITY_TOLERANCE,
        "all_passed": True,
        "checks": checks,
    }


def _reviewed_input(
    source: Path, corpus: Path | None, raw: Path, prior: Path, model: Path
) -> dict[str, Any]:
    return v.input_snapshot(source, corpus, raw, prior, model)


def _run_effects(
    model_path: Path,
    source_root: Path,
    corpus_root: Path,
    raw_root: Path,
    prior_root: Path,
    review_snapshot: dict[str, Any],
    input_snapshot: dict[str, Any],
    source_sha: str,
) -> dict[str, Any]:
    c.require_native_network_denial()
    _assert_review(review_snapshot)
    if (
        _reviewed_input(source_root, corpus_root, raw_root, prior_root, model_path)
        != input_snapshot
    ):
        raise RuntimeError("V18 input changed before effects")
    with c.network_block():
        model, tokenizer, runtime = load_runtime(model_path)
        if (
            getattr(model.args, "model_type", None) != "gemma3_text"
            or len(model.model.layers) != 26
        ):
            raise ValueError("V18 architecture mismatch")
        before_parameters, before_model = (
            c.model_parameter_digest(model),
            c.model_manifest(model_path),
        )
        audited = v.audit_corpus(
            corpus_root,
            source_root,
            raw_root,
            prior_root,
            model_path,
            source_sha,
            review_snapshot["review_sha256"],
            tokenizer,
        )
        fit, assessment, corpus = (
            audited["windows"]["fit"],
            audited["windows"]["assessment"],
            audited["manifest"],
        )
        _assert_review(review_snapshot)
        if (
            _reviewed_input(source_root, corpus_root, raw_root, prior_root, model_path)
            != input_snapshot
        ):
            raise RuntimeError("V18 input changed during effects")
        parity_value = parity(model, [*fit, *assessment])
        fit_baseline = evaluate_windows(model, tokenizer, fit, None)
        candidates = []
        for source_layer, destination_layer in c.CANDIDATE_PAIRS:
            config = RecirculationConfig(
                source_layer, destination_layer, c.FIT_ALPHA, c.FIT_BETA
            )
            candidates.append(
                {
                    "config": config.as_dict(),
                    "metrics": evaluate_windows(model, tokenizer, fit, config),
                }
            )
        selected = min(
            (item["metrics"]["mean_nll"], pair[0], pair[1], item)
            for pair, item in zip(c.CANDIDATE_PAIRS, candidates, strict=True)
        )[3]
        selected_fit = selected["config"]
        locked = RecirculationConfig(
            selected_fit["source_layer"],
            selected_fit["destination_layer"],
            c.EVALUATION_ALPHA,
            c.EVALUATION_BETA,
        )
        assessment_base, assessment_selected = (
            evaluate_windows(model, tokenizer, assessment, None),
            evaluate_windows(model, tokenizer, assessment, locked),
        )
        temp_base, temp_selected = (
            evaluate_windows(model, tokenizer, assessment, None, c.TEMPERATURE_CONTROL),
            evaluate_windows(
                model, tokenizer, assessment, locked, c.TEMPERATURE_CONTROL
            ),
        )
        repeat = evaluate_windows(model, tokenizer, assessment, locked)
        after_parameters, after_model = (
            c.model_parameter_digest(model),
            c.model_manifest(model_path),
        )
        if before_parameters != after_parameters or before_model != after_model:
            raise RuntimeError("V18 model custody changed")
    base_rows, selected_rows = (
        {row["document_id"]: row for row in assessment_base["rows"]},
        {row["document_id"]: row for row in assessment_selected["rows"]},
    )
    per_document = []
    for window in assessment:
        document_id = window.document_id
        base, chosen = base_rows[document_id], selected_rows[document_id]
        delta = chosen["nll"] / 1023 - base["nll"] / 1023
        per_document.append(
            {
                "dataset": "assessment",
                "document_id": document_id,
                "relative_path": window.relative_path,
                "window_ordinal": 0,
                "source_sha256": window.source_sha256,
                "text_sha256": window.text_sha256,
                "token_count": window.token_count,
                "target_count": 1023,
                "baseline_nll": base["nll"],
                "selected_nll": chosen["nll"],
                "delta_selected_minus_baseline": delta,
            }
        )
    bootstrap = c.bootstrap_mean_ci(
        [row["delta_selected_minus_baseline"] for row in per_document]
    )
    reach = []
    fit_base_rows = {row["document_id"]: row for row in fit_baseline["rows"]}
    for candidate, pair in zip(candidates, c.CANDIDATE_PAIRS, strict=True):
        candidate_rows = {
            row["document_id"]: row for row in candidate["metrics"]["rows"]
        }
        maximum = max(
            abs(candidate_rows[key]["nll"] - fit_base_rows[key]["nll"])
            for key in fit_base_rows
        )
        reach.append(
            {
                "source_layer": pair[0],
                "destination_layer": pair[1],
                "max_abs_fit_nll_delta": maximum,
                "reached": maximum != 0.0,
            }
        )
    if not any(item["reached"] for item in reach):
        raise RuntimeError("V18 nonzero intervention reach failed")
    common = {
        "schema": c.RESULT_SCHEMA,
        "state_slice": c.STATE_SLICE,
        "claim_ceiling": c.CLAIM_CEILING,
        "protocol_sha256": c.PROTOCOL_SHA256,
        "review_receipt_sha256": review_snapshot["review_sha256"],
        "source_manifest_sha256": source_sha,
        "corpus_manifest_sha256": corpus["manifest_sha256"],
        "model_path": str(c.MODEL_PATH),
        "model_manifest_sha256": before_model["manifest_sha256"],
        "model_cache_manifest_sha256": before_model["cache_manifest_sha256"],
        "model_parameter_digest_before": before_parameters,
        "model_parameter_digest_after": after_parameters,
        "architecture": "gemma3_text",
        "model_type": "gemma3_text",
        "layer_count": 26,
        "runtime": runtime,
    }
    expected_pair = {"source_layer": 11, "destination_layer": 4}
    decision = c.decide_replication(bootstrap)
    locked_dict = locked.as_dict()
    config = {
        **common,
        "model_name": model_path.name,
        "protocol": "paper-aligned-one-additional-iteration-v1",
        "mechanism_source": "arxiv:2608.17981",
        "fresh_row_range": {
            "start": c.FRESH_ROW_START,
            "end_exclusive": c.FRESH_ROW_END,
            "count_per_shard": c.FRESH_ROW_COUNT,
        },
        "window_token_count": c.WINDOW_TOKENS,
        "fit_window_count": 64,
        "assessment_window_count": 64,
        "candidate_pairs": [list(pair) for pair in c.CANDIDATE_PAIRS],
        "fit_alpha": c.FIT_ALPHA,
        "fit_beta": c.FIT_BETA,
        "evaluation_alpha": c.EVALUATION_ALPHA,
        "evaluation_beta": c.EVALUATION_BETA,
        "temperature_control": c.TEMPERATURE_CONTROL,
        "normalization": "source_l2_norm_to_destination_l2_norm",
        "selected_fit_config": selected_fit,
        "locked_evaluation_config": locked_dict,
        "paper_expected_pair": expected_pair,
        "paper_expected_pair_recovered": (
            selected_fit["source_layer"],
            selected_fit["destination_layer"],
        )
        == (11, 4),
        "controls": list(c.CONTROL_NAMES),
        "network_access": False,
        "training": False,
        "weights_frozen": True,
        "evidence_ledger_mutation": False,
        "assessment_authorized_by_review": True,
        "selection_policy": "first-64-eligible-1024-token-windows-per-disjoint-v18-source-split",
    }
    config["config_sha256"] = c.digest(config)
    qualification = {
        "nonzero_intervention_reach": any(item["reached"] for item in reach),
        "reach_evidence": reach,
    }
    controls = {
        "native_baseline": assessment_base,
        "zero_alpha_identity": parity_value,
        "all_candidate_evaluations": candidates,
        "temperature_1.20_baseline": temp_base,
        "temperature_1.20_intervention": temp_selected,
        "deterministic_repeat": repeat,
        "frozen_model_manifest": {
            "before": before_model["manifest_sha256"],
            "after": after_model["manifest_sha256"],
        },
        "frozen_model_parameters": {
            "before": before_parameters,
            "after": after_parameters,
        },
    }
    results = {
        **common,
        "network_access": False,
        "training": False,
        "weights_frozen": True,
        "evidence_ledger_mutation": False,
        "local_only": True,
        "parity": parity_value,
        "fit_baseline": fit_baseline,
        "fit_candidates": candidates,
        "selected_fit_config": selected_fit,
        "locked_evaluation_config": locked_dict,
        "paper_expected_pair": expected_pair,
        "paper_expected_pair_recovered": (
            selected_fit["source_layer"],
            selected_fit["destination_layer"],
        )
        == (11, 4),
        "assessment_baseline": assessment_base,
        "assessment_selected": assessment_selected,
        "assessment_temperature_baseline": temp_base,
        "assessment_temperature_selected": temp_selected,
        "assessment_repeat": repeat,
        "deterministic_repeat_passed": repeat == assessment_selected,
        "qualification": qualification,
        "controls": controls,
        "assessment_per_document": per_document,
        "assessment_nll_delta_selected_minus_baseline": bootstrap["mean_delta"],
        "bootstrap": bootstrap,
        "decision": decision,
    }
    results["results_sha256"] = c.digest(results)
    receipt = {
        **common,
        "config_sha256": config["config_sha256"],
        "results_sha256": results["results_sha256"],
        "zero_alpha_parity_passed": True,
        "nonzero_intervention_reach": qualification["nonzero_intervention_reach"],
        "deterministic_repeat_passed": True,
        "network_access": False,
        "training": False,
        "weights_frozen": True,
        "evidence_ledger_mutation": False,
        "bootstrap": bootstrap,
        "decision": decision,
    }
    receipt["receipt_sha256"] = c.digest(receipt)
    return {
        "config": config,
        "results": results,
        "receipt": receipt,
        "corpus": corpus,
        "model_manifest": before_model,
    }


def stage_corpus(
    source_root: Path,
    corpus_root: Path,
    model_path: Path = c.MODEL_PATH,
    receipt: Path = c.RECEIPT_PATH,
    raw_root: Path = c.RAW_ROOT,
    prior_root: Path = c.PRIOR_ROOT,
) -> dict[str, Any]:
    source, final, model = (
        c.exact_path(source_root, c.SOURCE_ROOT, "V18 source"),
        c.exact_path(corpus_root, c.CORPUS_ROOT, "V18 corpus"),
        c.exact_path(model_path, c.MODEL_PATH, "model path"),
    )
    if final.exists():
        raise FileExistsError(f"V18 corpus exists: {final}")
    review_snapshot = _review(receipt)
    source_validation = v.validate_source(source, raw_root, prior_root, receipt)
    input_snapshot = _reviewed_input(source, None, raw_root, prior_root, model)
    _assert_review(review_snapshot)
    if _reviewed_input(source, None, raw_root, prior_root, model) != input_snapshot:
        raise RuntimeError("V18 inputs changed before tokenizer")
    staging = Path(tempfile.mkdtemp(prefix=f".{final.name}.staging-", dir=final.parent))
    try:
        with c.network_block():
            tokenizer = load_tokenizer(model)
            entries = {}
        for split, count in (("fit", 64), ("assessment", 64)):
            selected = []
            for row in v.jsonl(source / f"{split}/fineweb_edu.jsonl", f"V18 {split}"):
                if len(selected) >= count:
                    break
                ids = list(tokenizer.encode(row["text"], add_special_tokens=False))
                if len(ids) < c.WINDOW_TOKENS:
                    continue
                text = tokenizer.decode(ids[: c.WINDOW_TOKENS])
                encoded = text.encode("utf-8")
                if (
                    list(tokenizer.encode(text, add_special_tokens=False))
                    != ids[: c.WINDOW_TOKENS]
                ):
                    raise ValueError("V18 tokenizer round trip failed")
                relative = f"{split}/window-{len(selected):06d}.txt"
                path = staging / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(encoded)
                selected.append(
                    {
                        "dataset": "fineweb_edu",
                        "document_id": row["document_id"],
                        "path": relative,
                        "window_ordinal": 0,
                        "byte_len": len(encoded),
                        "source_sha256": hashlib.sha256(
                            row["text"].encode()
                        ).hexdigest(),
                        "text_sha256": hashlib.sha256(encoded).hexdigest(),
                        "token_count": c.WINDOW_TOKENS,
                        "source_row_index": row["source_row_index"],
                    }
                )
            if len(selected) != count:
                raise ValueError(f"V18 {split} has {len(selected)} eligible windows")
            entries[split] = selected
        model_manifest = c.model_manifest(model)
        body = {
            "schema": c.CORPUS_SCHEMA,
            "state_slice": c.STATE_SLICE,
            "claim_ceiling": c.CLAIM_CEILING,
            "source_manifest_sha256": source_validation["manifest_sha256"],
            "review_receipt_sha256": review_snapshot["review_sha256"],
            "model_path": str(c.MODEL_PATH),
            "model_manifest_sha256": model_manifest["manifest_sha256"],
            "model_cache_manifest_sha256": model_manifest["cache_manifest_sha256"],
            "window_token_count": c.WINDOW_TOKENS,
            "fit_window_count": 64,
            "assessment_window_count": 64,
            "fit_windows": entries["fit"],
            "assessment_windows": entries["assessment"],
            "network_access": False,
            "training": False,
            "scientific_execution": False,
            "evidence_ledger_mutation": False,
        }
        _write(staging / "manifest.json", {**body, "manifest_sha256": c.digest(body)})
        _assert_review(review_snapshot)
        c.exact_file_set(staging, _expected_corpus_files(), "V18 corpus staging")
        with c.network_block():
            v.audit_corpus(
                staging,
                source,
                raw_root,
                prior_root,
                model,
                source_validation["manifest_sha256"],
                review_snapshot["review_sha256"],
                tokenizer,
            )
        _assert_review(review_snapshot)
        output = c.snapshot_files(
            staging, _expected_corpus_files(), "V18 corpus staging"
        )
        c.publish_no_replace(
            staging,
            final,
            _expected_corpus_files(),
            "V18 corpus",
            lambda: (
                _assert_review(review_snapshot),
                None
                if _reviewed_input(source, None, raw_root, prior_root, model) == input_snapshot
                else (_ for _ in ()).throw(
                    RuntimeError("V18 corpus inputs changed after publication")
                ),
            ),
        )
        return {
            "manifest": _json(final / "manifest.json", "V18 corpus manifest"),
            "snapshot": output,
        }
    except Exception:
        if staging.exists():
            shutil.rmtree(staging)
        raise


def _validator_receipt(staging: Path, validation: dict[str, Any]) -> None:
    body = {
        "schema": "gemma3-fineweb-edu-replication-v18-validator-receipt",
        "state_slice": c.STATE_SLICE,
        "result_sha256": validation["results_sha256"],
        "review_receipt_sha256": validation["review_receipt_sha256"],
        "independent_recomputation": validation["valid"] is True,
        "validator_return_sha256": c.digest(validation),
        "validator_valid": validation["valid"],
        "validator_decision": validation["decision"],
        "validator_bootstrap": validation["bootstrap"],
        "validator_input_snapshot_sha256": validation["input_snapshot_sha256"],
        "validator_code_snapshot_sha256": validation["code_snapshot_sha256"],
        "custody_recomputed": validation["custody_recomputed"],
    }
    _write(staging / "validator-receipt.json", {**body, "receipt_sha256": c.digest(body)})

def run_campaign(
    result_root: Path,
    source_root: Path,
    corpus_root: Path,
    raw_root: Path = c.RAW_ROOT,
    prior_root: Path = c.PRIOR_ROOT,
    model_path: Path = c.MODEL_PATH,
    receipt: Path = c.RECEIPT_PATH,
) -> dict[str, Any]:
    final, source, corpus, raw, prior, model = (
        c.exact_path(result_root, c.RESULT_ROOT, "V18 result"),
        c.exact_path(source_root, c.SOURCE_ROOT, "V18 source"),
        c.exact_path(corpus_root, c.CORPUS_ROOT, "V18 corpus"),
        c.exact_path(raw_root, c.RAW_ROOT, "V18 raw"),
        c.exact_path(prior_root, c.PRIOR_ROOT, "V18 prior"),
        c.exact_path(model_path, c.MODEL_PATH, "model path"),
    )
    if final.exists():
        raise FileExistsError(f"V18 result exists: {final}")
    review_snapshot = _review(receipt)
    source_validation = v.validate_source(source, raw, prior, receipt)
    input_snapshot = _reviewed_input(source, corpus, raw, prior, model)
    _assert_review(review_snapshot)
    if _reviewed_input(source, corpus, raw, prior, model) != input_snapshot:
        raise RuntimeError("V18 inputs changed before tokenizer")
    tokenizer = load_tokenizer(model)
    _assert_review(review_snapshot)
    if _reviewed_input(source, corpus, raw, prior, model) != input_snapshot:
        raise RuntimeError("V18 inputs changed during tokenizer load")
    corpus_validation = v.validate_corpus(
        corpus,
        source,
        raw,
        prior,
        model,
        source_validation["manifest_sha256"],
        receipt,
        tokenizer,
    )
    _assert_review(review_snapshot)
    if _reviewed_input(source, corpus, raw, prior, model) != input_snapshot:
        raise RuntimeError("V18 inputs changed before effects")
    staging = Path(tempfile.mkdtemp(prefix=f".{final.name}.staging-", dir=final.parent))
    try:
        (staging / "review-receipt.json").write_bytes(review_snapshot["receipt"])
        _assert_review(review_snapshot)
        payload = _run_effects(
            model,
            source,
            corpus,
            raw,
            prior,
            review_snapshot,
            input_snapshot,
            source_validation["manifest_sha256"],
        )
        _assert_review(review_snapshot)
        for name, value in (
            ("config.json", payload["config"]),
            ("results.json", payload["results"]),
            ("receipt.json", payload["receipt"]),
            ("corpus-manifest.json", payload["corpus"]),
            ("model-manifest.json", payload["model_manifest"]),
        ):
            _write(staging / name, value)
        expected = {
            "config.json",
            "results.json",
            "receipt.json",
            "corpus-manifest.json",
            "model-manifest.json",
            "review-receipt.json",
        }
        c.exact_file_set(staging, expected, "V18 result staging")
        _assert_review(review_snapshot)
        current = _reviewed_input(source, corpus, raw, prior, model)
        if current != input_snapshot:
            raise RuntimeError("V18 inputs changed immediately before validator")
        invocation_sha = c.digest(current)
        command = [
            sys.executable,
            "-B",
            "-m",
            VALIDATOR,
            "--mode",
            "result",
            "--source-root",
            str(source),
            "--raw-root",
            str(raw),
            "--prior-root",
            str(prior),
            "--corpus-root",
            str(corpus),
            "--result-root",
            str(staging),
            "--model",
            str(model),
            "--review-receipt",
            str(c.RECEIPT_PATH),
            "--corpus-manifest-sha256",
            corpus_validation["manifest_sha256"],
            "--invocation-snapshot-sha256",
            invocation_sha,
            "--allow-missing-validator-receipt",
        ]
        env = os.environ.copy()
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        completed = subprocess.run(
            command,
            cwd=c.REPO_ROOT,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        if completed.returncode != 0:
            raise RuntimeError(
                f"V18 independent validator failed:\n{completed.stdout}\n{completed.stderr}"
            )
        validation = json.loads(completed.stdout)
        _assert_review(review_snapshot)
        current_after_validation = _reviewed_input(source, corpus, raw, prior, model)
        if (
            current_after_validation != input_snapshot
            or validation.get("valid") is not True
            or validation.get("custody_recomputed") is not True
            or validation.get("input_snapshot_sha256") != c.digest(input_snapshot)
            or validation.get("code_snapshot_sha256") != c.code_snapshot_digest()
        ):
            raise RuntimeError("V18 post-validator custody check failed")
        _validator_receipt(staging, validation)
        v.validate_validator_receipt(staging / "validator-receipt.json", validation)
        expected_with_validator = set(expected) | {"validator-receipt.json"}
        c.exact_file_set(staging, expected_with_validator, "V18 result staging")
        c.publish_no_replace(
            staging,
            final,
            expected_with_validator,
            "V18 result",
            lambda: (
                _assert_review(review_snapshot),
                None
                if _reviewed_input(source, corpus, raw, prior, model) == input_snapshot
                else (_ for _ in ()).throw(
                    RuntimeError("V18 result inputs changed after publication")
                ),
            ),
        )
        return {**payload, "validation": validation}
    except Exception:
        if staging.exists():
            shutil.rmtree(staging)
        raise


def main() -> int:
    _sandbox()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--corpus-root", type=Path, required=True)
    parser.add_argument("--result-root", type=Path)
    parser.add_argument("--raw-root", type=Path, default=c.RAW_ROOT)
    parser.add_argument("--prior-root", type=Path, default=c.PRIOR_ROOT)
    parser.add_argument("--model", type=Path, default=c.MODEL_PATH)
    parser.add_argument("--review-receipt", type=Path, default=c.RECEIPT_PATH)
    parser.add_argument("--stage-only", action="store_true")
    args = parser.parse_args()
    value = (
        stage_corpus(
            args.source_root,
            args.corpus_root,
            args.model,
            args.review_receipt,
            args.raw_root,
            args.prior_root,
        )
        if args.stage_only
        else run_campaign(
            args.result_root,
            args.source_root,
            args.corpus_root,
            args.raw_root,
            args.prior_root,
            args.model,
            args.review_receipt,
        )
    )
    print(json.dumps(value, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())



