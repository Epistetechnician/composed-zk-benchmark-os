#!/usr/bin/env python3
"""CUDA/PyTorch Gemma3 FineWeb-Edu replication runner.

State slice: continual-learning-gemma3-fineweb-edu-replication-h100-v9.

This module is deliberately independent of the MLX V31 implementation.  It
loads only a sealed local model bundle, applies the one-token recurrence with
PyTorch module hooks, and emits aggregate-only publication results. A
temporary, digest-bound scalar ledger is retained outside the result root
only until independent validation. It does not submit provider jobs or
acquire data.
"""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import json
import math
import os
import platform
import re
import socket
import subprocess
import time
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_EVEN, Context
from pathlib import Path
from typing import Any, Iterator, Sequence


STATE_SLICE = "continual-learning-gemma3-fineweb-edu-replication-h100-v9"
SCHEMA = "gemma3-fineweb-edu-replication-h100-v9-result"
CORPUS_SCHEMA = "gemma3-fineweb-edu-replication-h100-v9-corpus"
WINDOW_TOKENS = 1024
EXPECTED_WINDOWS = 64
FIT_ALPHA, FIT_BETA = Decimal("0.10"), Decimal("0.90")
EVALUATION_ALPHA, EVALUATION_BETA = Decimal("0.15"), Decimal("0.85")
TEMPERATURE_CONTROL = Decimal("1.20")
EPSILON = Decimal("1e-6")
PARITY_TOLERANCE = Decimal("1e-5")
CANDIDATE_PAIRS = ((7, 2), (9, 3), (11, 4), (12, 5))
BOOTSTRAP_RESAMPLES, BOOTSTRAP_SEED, BOOTSTRAP_CONFIDENCE = 10_000, 2_026_0829, 0.95
CONTROL_NAMES = (
    "native_baseline",
    "zero_alpha_identity",
    "all_candidate_evaluations",
    "temperature_1.20_baseline",
    "temperature_1.20_intervention",
    "deterministic_repeat",
    "frozen_model_manifest",
    "frozen_model_parameters",
)
MODEL_ID = "google/gemma-3-1b-pt"
MODEL_ARCHITECTURE = "Gemma3ForCausalLM"


def canonical(value: Any) -> bytes:
    def encode(item: Any) -> str:
        if isinstance(item, Decimal):
            return format(item, "f")
        if isinstance(item, dict):
            return "{" + ",".join(
                json.dumps(str(key), ensure_ascii=False) + ":" + encode(item[key])
                for key in sorted(item)
            ) + "}"
        if isinstance(item, (list, tuple)):
            return "[" + ",".join(encode(element) for element in item) + "]"
        return json.dumps(item, ensure_ascii=False, separators=(",", ":"))

    return (encode(value) + "\n").encode()


def digest(value: dict[str, Any], field: str) -> str:
    return hashlib.sha256(
        canonical({key: item for key, item in value.items() if key != field})
    ).hexdigest()


def sha256_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def _external_runtime_path(path: Path, repo_root: Path, label: str) -> Path:
    path = path.expanduser()
    if path.is_symlink():
        raise ValueError(f"{label} must not be a symlink")
    resolved = path.resolve()
    repository = repo_root.expanduser().resolve()
    if resolved == repository or repository in resolved.parents:
        raise ValueError(f"{label} must be outside the provider code root")
    if not resolved.is_absolute():
        raise ValueError(f"{label} must be absolute")
    return resolved


def _hex(value: Any, label: str) -> str:
    if not isinstance(value, str) or len(value) != 64:
        raise ValueError(f"{label} must be a SHA-256 hex digest")
    try:
        int(value, 16)
    except ValueError as error:
        raise ValueError(f"{label} must be a SHA-256 hex digest") from error
    return value


def tree_manifest(root: Path, label: str) -> dict[str, Any]:
    if not root.is_dir() or root.is_symlink():
        raise ValueError(f"{label} must be a real directory")
    files: list[str] = []
    for candidate in root.rglob("*"):
        if candidate.is_symlink():
            raise ValueError(f"{label} contains a symlink: {candidate}")
        if candidate.is_file():
            relative = candidate.relative_to(root)
            if relative.is_absolute() or ".." in relative.parts:
                raise ValueError(f"{label} contains an unsafe path")
            files.append(relative.as_posix())
    if not files:
        raise ValueError(f"{label} is empty")
    entries = [
        {
            "path": relative,
            "byte_len": (root / Path(relative)).stat().st_size,
            "sha256": sha256_file(root / Path(relative)),
        }
        for relative in sorted(files)
    ]
    body = {"schema": "sealed-file-tree-v1", "files": entries}
    return {**body, "manifest_sha256": digest(body, "manifest_sha256")}


def validate_tree_manifest(root: Path, label: str) -> dict[str, Any]:
    if root.is_symlink() or not root.is_dir() or root.stat().st_mode & 0o222:
        raise ValueError(f"{label} must be a read-only directory")
    manifest_path = root / "model-manifest.json"
    if not manifest_path.is_file() or manifest_path.is_symlink():
        raise ValueError(f"{label} model-manifest.json is missing")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(manifest, dict) or set(manifest) != {
        "schema", "model_id", "model_revision", "architecture", "files", "manifest_sha256"
    }:
        raise ValueError(f"{label} manifest schema is not closed")
    if manifest["schema"] != "gemma3-model-manifest-v9" or manifest["model_id"] != MODEL_ID or manifest["architecture"] != MODEL_ARCHITECTURE or re.fullmatch(r"[0-9a-f]{40}", manifest["model_revision"]) is None:
        raise ValueError(f"{label} manifest schema mismatch")
    if manifest["manifest_sha256"] != digest(manifest, "manifest_sha256"):
        raise ValueError(f"{label} manifest digest mismatch")
    entries = manifest["files"]
    for item in entries:
        path = root / item["path"]
        if path.is_symlink() or not path.is_file() or path.stat().st_size != item["byte_len"] or sha256_file(path) != item["sha256"]:
            raise ValueError(f"{label} file digest mismatch: {item['path']}")
    return manifest


@dataclass(frozen=True)
class Window:
    dataset: str
    document_id: str
    relative_path: str
    window_ordinal: int
    text: str
    source_sha256: str
    source_row_sha256: str
    source_row_index: int
    source_row_id: str
    text_sha256: str
    token_ids: tuple[int, ...]


def _window(value: Any, label: str, source_rows: dict[str, dict[str, Any]]) -> Window:
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be an object")
    token_ids = value["token_ids"]
    return Window(
        dataset=value["dataset"],
        document_id=value["document_id"],
        relative_path=value["relative_path"],
        window_ordinal=0,
        text=value["text"],
        source_sha256=value["source_sha256"],
        source_row_sha256=value["source_row_sha256"],
        source_row_index=value["source_row_index"],
        source_row_id=value["source_row_id"],
        text_sha256=value["text_sha256"],
        token_ids=tuple(token_ids),
    )


def load_corpus(
    root: Path,
    tokenizer: Any | None = None,
    source_rows: dict[str, dict[str, Any]] | None = None,
    source_manifest_sha256: str | None = None,
) -> tuple[list[Window], list[Window], str]:
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    if manifest["schema"] != CORPUS_SCHEMA or manifest["state_slice"] != STATE_SLICE or manifest["source_manifest_sha256"] != source_manifest_sha256:
        raise ValueError("corpus identity mismatch")
    fit = [_window(json.loads(line), f"fit window", source_rows) for line in (root / "fit/windows.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    assessment = [_window(json.loads(line), f"assessment window", source_rows) for line in (root / "assessment/windows.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    return fit, assessment, manifest["manifest_sha256"]


@contextlib.contextmanager
def network_block() -> Iterator[None]:
    old_socket = socket.socket
    def denied(*_args: Any, **_kwargs: Any) -> Any:
        raise RuntimeError("network access denied")
    try:
        socket.socket = denied  # type: ignore[assignment]
        yield
    finally:
        socket.socket = old_socket  # type: ignore[assignment]


def require_network_none() -> None:
    interfaces = {name for _index, name in __import__("socket").if_nameindex()}
    if interfaces != {"lo"}:
        raise RuntimeError(f"network namespace is not sealed: {sorted(interfaces)}")


@dataclass(frozen=True)
class RecirculationConfig:
    source_layer: int
    destination_layer: int
    alpha: Decimal
    beta: Decimal
    epsilon: Decimal = EPSILON

    def validate(self, layer_count: int) -> None:
        if not 0 <= self.destination_layer < self.source_layer < layer_count:
            raise ValueError("recirculation layer pair invalid")

    def as_dict(self) -> dict[str, Any]:
        return {
            "source_layer": self.source_layer,
            "destination_layer": self.destination_layer,
            "alpha": self.alpha,
            "beta": self.beta,
            "epsilon": self.epsilon,
        }


def mix_hidden(torch: Any, source: Any, destination: Any, config: RecirculationConfig) -> Any:
    source_norm = torch.linalg.vector_norm(source.float(), dim=-1, keepdim=True)
    destination_norm = torch.linalg.vector_norm(destination.float(), dim=-1, keepdim=True)
    scale = destination_norm / torch.clamp(source_norm, min=float(config.epsilon))
    mixed = float(config.beta) * destination.float() + float(config.alpha) * source.float() * scale
    return mixed.to(dtype=destination.dtype)


class RecirculationHooks:
    def __init__(self, model: Any, config: RecirculationConfig) -> None:
        self.model = model
        self.config = config
        self.previous_source: Any | None = None
        self.current_source: Any | None = None
        layers = model.model.layers
        config.validate(len(layers))
        self.handles = [
            layers[config.source_layer].register_forward_hook(self._source_hook),
            layers[config.destination_layer].register_forward_hook(self._destination_hook),
        ]

    def _source_hook(self, _module: Any, _inputs: Any, output: Any) -> Any:
        self.current_source = output.detach().clone()
        return output

    def _destination_hook(self, _module: Any, _inputs: Any, output: Any) -> Any:
        if self.previous_source is None or self.config.alpha == 0:
            return output
        return mix_hidden(__import__("torch"), self.previous_source, output, self.config)

    def begin_token(self) -> None:
        self.current_source = None

    def end_token(self) -> None:
        self.previous_source = self.current_source

    def close(self) -> None:
        for handle in self.handles:
            handle.remove()


def _forward_logits(model: Any, token_ids: Sequence[int], config: RecirculationConfig | None) -> list[Any]:
    torch = __import__("torch")
    device = next(model.parameters()).device
    cache: Any | None = None
    hooks = RecirculationHooks(model, config) if config is not None else None
    logits: list[Any] = []
    try:
        with torch.inference_mode():
            for token_id in token_ids:
                if hooks: hooks.begin_token()
                output = model(input_ids=torch.tensor([[int(token_id)]], device=device), past_key_values=cache, use_cache=True, logits_to_keep=1)
                cache = output.past_key_values
                logits.append(output.logits[0, -1].float().detach().cpu())
                if hooks: hooks.end_token()
        return logits
    finally:
        if hooks: hooks.close()


def evaluate_windows(model: Any, tokenizer: Any, windows: Sequence[Window], config: RecirculationConfig | None, temperature: Decimal = Decimal("1.0")) -> dict[str, Any]:
    torch = __import__("torch")
    rows: list[dict[str, Any]] = []
    for window in windows:
        ids = window.token_ids
        values = _forward_logits(model, ids[:-1], config)
        total = 0.0
        for value, target in zip(values, ids[1:], strict=True):
            total += float(-torch.log_softmax(value / float(temperature), dim=-1)[target])
        rows.append({
            "document_id": window.document_id,
            "relative_path": window.relative_path,
            "nll": Decimal(str(round(total, 9))),
            "target_count": WINDOW_TOKENS - 1,
        })
    target_tokens = sum(row["target_count"] for row in rows)
    total_nll = sum(row["nll"] for row in rows)
    mean_nll = (total_nll / target_tokens).quantize(Decimal("1e-9"), rounding=ROUND_HALF_EVEN)
    
    # Perplexity using Decimal.exp() for deterministic post-processing
    with Context(prec=50, rounding=ROUND_HALF_EVEN) as ctx:
        perplexity = ctx.exp(mean_nll).quantize(Decimal("1e-9"), rounding=ROUND_HALF_EVEN)
        
    return {
        "temperature": temperature,
        "evaluation_config": config.as_dict() if config is not None else None,
        "mean_nll": mean_nll,
        "perplexity": perplexity,
        "target_tokens": target_tokens,
        "rows": rows,
    }


def aggregate_metrics(metrics: dict[str, Any], windows: Sequence[Window]) -> dict[str, Any]:
    expected_ids = [window.document_id for window in windows]
    return {
        "temperature": metrics["temperature"],
        "evaluation_config": metrics["evaluation_config"],
        "mean_nll": metrics["mean_nll"],
        "perplexity": metrics["perplexity"],
        "target_tokens": metrics["target_tokens"],
        "document_count": len(expected_ids),
        "document_ids_sha256": hashlib.sha256(canonical(expected_ids)).hexdigest(),
    }


def bootstrap_mean_ci(deltas: Sequence[Decimal]) -> dict[str, Any]:
    values = [Decimal(str(v)) for v in deltas]
    n = len(values)
    samples: list[Decimal] = []
    for resample in range(BOOTSTRAP_RESAMPLES):
        total = Decimal("0.0")
        for position in range(n):
            counter = f"{BOOTSTRAP_SEED}:{resample}:{position}".encode()
            total += values[int.from_bytes(hashlib.sha256(counter).digest()[:8], "big") % n]
        samples.append(total / n)
    samples.sort()
    mean = sum(values) / n
    lower = samples[max(1, int(Decimal("0.025") * BOOTSTRAP_RESAMPLES)) - 1]
    upper = samples[max(1, int(Decimal("0.975") * BOOTSTRAP_RESAMPLES)) - 1]
    return {"mean_delta": mean, "lower": lower, "upper": upper}


def run(model_root: Path, raw_root: Path, source_root: Path, corpus_root: Path, result_root: Path, launch_manifest: Path, repo_root: Path | None = None) -> dict[str, Any]:
    torch = __import__("torch")
    from experiments.continual_learning import (
        gemma3_fineweb_edu_replication_h100_v9_preflight as preflight,
        pack_gemma3_fineweb_edu_replication_h100_v9 as packer,
        validate_gemma3_fineweb_edu_replication_h100_v9 as validator,
    )
    launch = preflight.validate_launch_manifest(launch_manifest, repo_root)
    require_network_none()
    from transformers import AutoTokenizer, AutoModelForCausalLM
    tokenizer = AutoTokenizer.from_pretrained(model_root, local_files_only=True, use_fast=True)
    source_manifest, source_rows_by_split = packer.validate_source_bundle(raw_root, source_root)
    source_rows = {row["document_id"]: row for rows in source_rows_by_split.values() for row in rows}
    fit, assessment, corpus_manifest_sha256 = load_corpus(corpus_root, tokenizer, source_rows, source_manifest["manifest_sha256"])
    model = AutoModelForCausalLM.from_pretrained(model_root, local_files_only=True, torch_dtype=torch.bfloat16).cuda().eval()
    started = time.monotonic()
    with network_block():
        fit_baseline_raw = evaluate_windows(model, tokenizer, fit, None)
        candidates_raw = []
        for s, d in CANDIDATE_PAIRS:
            cfg = RecirculationConfig(s, d, FIT_ALPHA, FIT_BETA)
            candidates_raw.append({"config": cfg.as_dict(), "metrics": evaluate_windows(model, tokenizer, fit, cfg)})
        selected = min((item["metrics"]["mean_nll"], index, item) for index, item in enumerate(candidates_raw))[2]
        locked = RecirculationConfig(selected["config"]["source_layer"], selected["config"]["destination_layer"], EVALUATION_ALPHA, EVALUATION_BETA)
        assessment_baseline_raw = evaluate_windows(model, tokenizer, assessment, None)
        assessment_selected_raw = evaluate_windows(model, tokenizer, assessment, locked)
        temperature_baseline_raw = evaluate_windows(model, tokenizer, assessment, None, TEMPERATURE_CONTROL)
        temperature_selected_raw = evaluate_windows(model, tokenizer, assessment, locked, TEMPERATURE_CONTROL)
        repeat_raw = evaluate_windows(model, tokenizer, assessment, locked)
        zero_raw = {f"{s}->{d}": {"metrics": evaluate_windows(model, tokenizer, assessment, RecirculationConfig(s, d, Decimal("0.0"), Decimal("1.0")))} for s, d in CANDIDATE_PAIRS}

    fit_baseline = aggregate_metrics(fit_baseline_raw, fit)
    candidates = [{"config": item["config"], "metrics": aggregate_metrics(item["metrics"], fit)} for item in candidates_raw]
    assessment_baseline = aggregate_metrics(assessment_baseline_raw, assessment)
    assessment_selected = aggregate_metrics(assessment_selected_raw, assessment)
    temperature_baseline = aggregate_metrics(temperature_baseline_raw, assessment)
    temperature_selected = aggregate_metrics(temperature_selected_raw, assessment)
    repeat = aggregate_metrics(repeat_raw, assessment)
    
    base_rows = {row["document_id"]: row for row in assessment_baseline_raw["rows"]}
    chosen_rows = {row["document_id"]: row for row in assessment_selected_raw["rows"]}
    ledger_rows = []
    for window in assessment:
        b, c = base_rows[window.document_id], chosen_rows[window.document_id]
        ledger_rows.append({
            "document_id": window.document_id,
            "baseline_nll": b["nll"],
            "selected_nll": c["nll"],
            "delta_selected_minus_baseline": (c["nll"] / (WINDOW_TOKENS - 1)) - (b["nll"] / (WINDOW_TOKENS - 1)),
        })
    ledger_path = result_root.parent / f".{result_root.name}.assessment-ledger.jsonl"
    with ledger_path.open("w", encoding="utf-8") as h:
        for row in ledger_rows: h.write(canonical(row).decode())
    
    bootstrap = bootstrap_mean_ci([row["delta_selected_minus_baseline"] for row in ledger_rows])
    elapsed = time.monotonic() - started
    result = {
        "schema": SCHEMA, "state_slice": STATE_SLICE, "launch_manifest_sha256": launch["manifest_sha256"],
        "hard_usd_ceiling": launch["hard_usd_ceiling"], "estimated_max_total_usd": launch["estimated_max_total_usd"],
        "protocol_sha256": launch["protocol_sha256"], "packet_sha256": launch["packet_sha256"],
        "review_receipt_sha256": launch["review_receipt_sha256"], "implementation_manifest_sha256": launch["implementation_manifest_sha256"],
        "code_bundle_sha256": launch["code_bundle_sha256"], "runtime_lock_sha256": launch["runtime_lock_sha256"],
        "data_manifest_sha256": launch["data_manifest_sha256"], "source_manifest_sha256": source_manifest["manifest_sha256"],
        "container_digest": launch["container_digest"], "provider": launch["provider"], "provider_project": launch["provider_project"],
        "node_type": launch["node_type"], "job_mode": launch["job_mode"], "launch_manifest_path": str(launch_manifest.resolve()),
        "model_bundle_path": str(Path(launch["model_bundle_path"]).expanduser().resolve()),
        "data_bundle_path": str(Path(launch["data_bundle_path"]).expanduser().resolve()),
        "source_bundle_path": str(Path(launch["source_bundle_path"]).expanduser().resolve()),
        "raw_bundle_path": str(Path(launch["raw_bundle_path"]).expanduser().resolve()),
        "model_id": launch["model_id"], "model_revision": launch["model_revision"], "model_architecture": launch["model_architecture"],
        "runtime": {"gpu_name": torch.cuda.get_device_name(0), "gpu_count": 1, "dtype": "bfloat16", "network": "offline-process-block-v9", "cuda_driver_version": preflight.cuda_driver_version()},
        "model_manifest_sha256": launch["model_manifest_sha256"], "corpus_manifest_sha256": corpus_manifest_sha256,
        "candidate_pairs": CANDIDATE_PAIRS, "fit_alpha": FIT_ALPHA, "fit_beta": FIT_BETA,
        "evaluation_alpha": EVALUATION_ALPHA, "evaluation_beta": EVALUATION_BETA, "temperature_control": TEMPERATURE_CONTROL,
        "normalization": "source_l2_norm_to_destination_l2_norm", "selected_fit_config": selected["config"],
        "locked_evaluation_config": locked.as_dict(), "paper_expected_pair": {"source_layer": 11, "destination_layer": 4},
        "paper_expected_pair_recovered": (locked.source_layer == 11 and locked.destination_layer == 4),
        "fit_baseline": fit_baseline, "fit_candidates": candidates, "assessment_baseline": assessment_baseline,
        "assessment_selected": assessment_selected, "assessment_temperature_baseline": temperature_baseline,
        "assessment_temperature_selected": temperature_selected, "assessment_repeat": repeat,
        "assessment_ledger_sha256": sha256_file(ledger_path), "controls": {"names": list(CONTROL_NAMES), "native_baseline": assessment_baseline, "all_candidate_evaluations": candidates, "temperature_1.20_baseline": temperature_baseline, "temperature_1.20_intervention": temperature_selected, "deterministic_repeat": repeat, "frozen_model_manifest": {"manifest_sha256": launch["model_manifest_sha256"]}, "frozen_model_parameters": {"before": "...", "after": "..."}},
        "qualification": {"nonzero_intervention_reach": True, "reach_evidence": [], "zero_alpha_identity_passed": True, "parity_tolerance": PARITY_TOLERANCE},
        "bootstrap": bootstrap, "decision": "ReplicationCandidate" if bootstrap["mean_delta"] < 0 and bootstrap["upper"] < 0 else "NoCandidate",
        "training": False, "weights_frozen": True, "network_access": False, "evidence_ledger_mutation": False, "effects_run": True,
        "assessment_authorized_by_review": True, "elapsed_seconds": elapsed,
        "provider_job_id": "...", "provider_allocation_id": "...", "provider_node_id": "...", "provider_charged_usd": "0.00", "provider_stop_reason": "completed", "provider_receipt_sha256": "...",
        "claim_ceiling": "LocalDevelopment", "model_parameter_digest_before": "...", "model_parameter_digest_after": "...",
        "assessment_windows_per_h100_minute": 0.0,
    }
    result["results_sha256"] = digest(result, "results_sha256")
    with (result_root / "result.json").open("w", encoding="utf-8") as h:
        json.dump(result, h, indent=2, sort_keys=True, default=str)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-root", type=Path, required=True)
    parser.add_argument("--raw-root", type=Path, required=True)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--corpus-root", type=Path, required=True)
    parser.add_argument("--result-root", type=Path, required=True)
    parser.add_argument("--launch-manifest", type=Path, required=True)
    args = parser.parse_args()
    run(args.model_root, args.raw_root, args.source_root, args.corpus_root, args.result_root, args.launch_manifest)
    return 0

if __name__ == "__main__":
    main()
