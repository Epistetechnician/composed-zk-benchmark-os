#!/usr/bin/env python3
"""Internal multi-instance Gemma3 recirculation experiment.

State slice: continual-learning-gemma3-paper-recirculation-internal-multimachine-v1.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import platform
import socket
import sys
import time
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from experiments.continual_learning import gemma3_paper_recirculation_v1 as base

STATE_SLICE = "continual-learning-gemma3-paper-recirculation-internal-multimachine-v1"
CLAIM_CEILING = "LocalDevelopmentGemma3InternalMultiInstanceReplication"
PROTOCOL_PATH = REPO_ROOT / "docs/research/continual-learning/297-gemma3-paper-recirculation-internal-multimachine-v1-protocol.md"
MANIFEST_PATH = REPO_ROOT / "docs/research/continual-learning/298-gemma3-paper-recirculation-internal-multimachine-v1-implementation-manifest.json"
WINDOW_TOKENS = 1024
WINDOW_LIMIT = 16
SMOKE_WINDOW_LIMIT = 4
CANDIDATE_PAIRS = ((7, 2), (9, 3), (11, 4), (12, 5))
EVALUATION_ALPHA = 0.15
EVALUATION_BETA = 0.85
PARITY_TOLERANCE = 1e-5
BOOTSTRAP_REPEATS = 2000


def digest(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _read_json(path: Path) -> dict[str, Any]:
    if not path.is_file() or path.is_symlink():
        raise ValueError(f"missing regular JSON file: {path}")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON object required: {path}")
    return value


def _safe_file(root: Path, relative: str) -> Path:
    if not isinstance(relative, str) or not relative or Path(relative).is_absolute():
        raise ValueError("corpus path must be relative")
    raw = root / relative
    resolved = raw.resolve()
    if raw.is_symlink() or resolved == root.resolve() or root.resolve() not in resolved.parents or not resolved.is_file():
        raise ValueError(f"unsafe corpus path: {relative}")
    return resolved


def _model_code_manifest(model_path: Path) -> dict[str, Any]:
    return base.model_manifest(model_path)


def _validate_implementation_manifest() -> str:
    manifest = _read_json(MANIFEST_PATH)
    if manifest.get("schema") != "gemma3-paper-recirculation-internal-multimachine-v1-implementation":
        raise ValueError("implementation manifest schema mismatch")
    if manifest.get("state_slice") != STATE_SLICE:
        raise ValueError("implementation manifest state slice mismatch")
    stored = manifest.get("manifest_sha256")
    body = {key: value for key, value in manifest.items() if key != "manifest_sha256"}
    if not isinstance(stored, str) or digest(body) != stored:
        raise ValueError("implementation manifest digest mismatch")
    files = manifest.get("files")
    if not isinstance(files, list) or not files:
        raise ValueError("implementation manifest file list missing")
    for entry in files:
        if not isinstance(entry, dict) or not isinstance(entry.get("path"), str) or not isinstance(entry.get("sha256"), str):
            raise ValueError("invalid implementation manifest entry")
        path = (REPO_ROOT / entry["path"]).resolve()
        if REPO_ROOT not in path.parents or not path.is_file() or path.is_symlink() or sha256_file(path) != entry["sha256"]:
            raise ValueError(f"implementation digest mismatch: {entry.get('path')}")
    return stored


def _load_windows(corpus_root: Path, tokenizer: Any, split: str, limit: int) -> list[dict[str, Any]]:
    manifest = _read_json(corpus_root / "manifest.json")
    if manifest.get("schema") != "gemma3-paper-recirculation-internal-multimachine-v1-corpus":
        raise ValueError("corpus manifest schema mismatch")
    if manifest.get("window_token_count") != WINDOW_TOKENS:
        raise ValueError("corpus token-count contract mismatch")
    entries = manifest.get(split)
    if not isinstance(entries, list) or len(entries) < limit:
        raise ValueError(f"{split} needs at least {limit} windows")
    windows = []
    seen_paths: set[str] = set()
    seen_docs: set[tuple[str, str]] = set()
    for entry in entries[:limit]:
        if not isinstance(entry, dict):
            raise ValueError(f"invalid {split} manifest entry")
        dataset = entry.get("dataset")
        document_id = entry.get("document_id")
        relative = entry.get("path")
        if not isinstance(dataset, str) or not dataset or not isinstance(document_id, str) or not document_id:
            raise ValueError(f"invalid {split} identity")
        if relative in seen_paths or (dataset, document_id) in seen_docs:
            raise ValueError(f"duplicate {split} identity")
        seen_paths.add(relative)
        seen_docs.add((dataset, document_id))
        path = _safe_file(corpus_root, relative)
        text = path.read_text(encoding="utf-8")
        token_ids = list(tokenizer.encode(text, add_special_tokens=False))
        if entry.get("token_count") != WINDOW_TOKENS or entry.get("text_sha256") != hashlib.sha256(text.encode("utf-8")).hexdigest() or len(token_ids) != WINDOW_TOKENS:
            raise ValueError(f"{split} window is not exactly 1024 tokens: {relative}")
        windows.append({
            "dataset": dataset,
            "document_id": document_id,
            "path": Path(relative).as_posix(),
            "window_ordinal": entry.get("window_ordinal"),
            "text": text,
            "text_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
            "token_ids": token_ids,
        })
    return windows


def _evaluate(model: Any, tokenizer: Any, windows: list[dict[str, Any]], config: Any | None, *, temperature: float = 1.0) -> dict[str, Any]:
    import mlx.core as mx

    rows = []
    total_nll = 0.0
    total_targets = 0
    for window in windows:
        logits = base.logits_for_tokens(model, window["token_ids"], config)
        nll, targets = base._nll(logits, window["token_ids"], mx, temperature)
        if not math.isfinite(nll) or targets <= 0:
            raise ValueError("non-finite or empty metric")
        rows.append({"path": window["path"], "text_sha256": window["text_sha256"], "nll": round(nll, 9), "target_count": targets})
        total_nll += nll
        total_targets += targets
    return {"mean_nll": total_nll / total_targets, "target_tokens": total_targets, "rows": rows}


def _bootstrap_upper(deltas: list[float]) -> float:
    if not deltas:
        raise ValueError("bootstrap requires deltas")
    ordered = sorted(deltas)
    samples = []
    for index in range(BOOTSTRAP_REPEATS):
        sample = [deltas[(index * 7919 + position * 104729) % len(deltas)] for position in range(len(deltas))]
        samples.append(sum(sample) / len(sample))
    samples.sort()
    return samples[min(len(samples) - 1, math.ceil(0.95 * len(samples)) - 1)]


def run_instance(output: Path, corpus_root: Path, model_path: Path, instance_id: str, window_limit: int = WINDOW_LIMIT) -> dict[str, Any]:
    output = output.resolve()
    corpus_root = corpus_root.resolve()
    model_path = model_path.resolve()
    if output.exists() or REPO_ROOT in output.parents or output == REPO_ROOT:
        raise ValueError("output must be a new external root")
    if not corpus_root.is_dir() or not model_path.is_dir():
        raise FileNotFoundError("corpus and model roots must exist")
    if not instance_id or any(character.isspace() for character in instance_id):
        raise ValueError("instance_id must be nonblank and whitespace-free")
    if window_limit not in (SMOKE_WINDOW_LIMIT, WINDOW_LIMIT):
        raise ValueError("window_limit must be 4 for smoke or 16 for replication")
    implementation_manifest_sha256 = _validate_implementation_manifest()
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    model_manifest_before = _model_code_manifest(model_path)
    model, tokenizer, policy = base._load_runtime(model_path)
    if len(model.model.layers) != 26:
        raise ValueError("expected 26 Gemma3 layers")
    fit = _load_windows(corpus_root, tokenizer, "fit", window_limit)
    assessment = _load_windows(corpus_root, tokenizer, "assessment", window_limit)
    if {(item["dataset"], item["document_id"]) for item in fit} & {(item["dataset"], item["document_id"]) for item in assessment}:
        raise ValueError("fit and assessment identities overlap")
    corpus_manifest = _read_json(corpus_root / "manifest.json")
    probe = assessment[0]["text"]
    parity = base.parity_check(model, tokenizer, probe)
    if not parity["passed"]:
        raise ValueError("zero-alpha parity failed")
    baseline_fit = _evaluate(model, tokenizer, fit, None)
    candidates = []
    for pair in CANDIDATE_PAIRS:
        config = base.RecirculationConfig(pair[0], pair[1], EVALUATION_ALPHA)
        metrics = _evaluate(model, tokenizer, fit, config)
        candidates.append({"pair": pair, "mean_nll": metrics["mean_nll"], "delta": metrics["mean_nll"] - baseline_fit["mean_nll"]})
    selected = min(candidates, key=lambda item: (item["delta"], CANDIDATE_PAIRS.index(tuple(item["pair"]))))
    selected_config = base.RecirculationConfig(selected["pair"][0], selected["pair"][1], EVALUATION_ALPHA)
    baseline_assessment = _evaluate(model, tokenizer, assessment, None)
    selected_assessment = _evaluate(model, tokenizer, assessment, selected_config)
    repeat_assessment = _evaluate(model, tokenizer, assessment, selected_config)
    deltas = [row["nll"] - base_row["nll"] for row, base_row in zip(selected_assessment["rows"], baseline_assessment["rows"], strict=True)]
    repeat_deltas = [row["nll"] - repeat_row["nll"] for row, repeat_row in zip(selected_assessment["rows"], repeat_assessment["rows"], strict=True)]
    model_manifest_after = _model_code_manifest(model_path)
    if model_manifest_after != model_manifest_before:
        raise ValueError("model manifest changed during frozen inference")
    result = {
        "schema": "gemma3-paper-recirculation-internal-multimachine-v1-instance",
        "state_slice": STATE_SLICE,
        "claim_ceiling": CLAIM_CEILING,
        "instance_id": instance_id,
        "machine_id": socket.gethostname(),
        "platform_node": platform.node(),
        "pid": os.getpid(),
        "started_at_unix": time.time(),
        "model_path": str(model_path),
        "model_manifest_sha256": model_manifest_after["manifest_sha256"],
        "corpus_manifest_sha256": sha256_file(corpus_root / "manifest.json"),
        "corpus_source_manifest_sha256": corpus_manifest.get("source_manifest_sha256"),
        "prior_source_reused": corpus_manifest.get("prior_source_reused"),
        "runner_sha256": sha256_file(Path(__file__).resolve()),
        "protocol_sha256": sha256_file(PROTOCOL_PATH),
        "implementation_manifest_sha256": implementation_manifest_sha256,
        "tokenizer_policy": policy,
        "fit_window_count": len(fit),
        "assessment_window_count": len(assessment),
        "window_limit": window_limit,
        "execution_mode": "replication" if window_limit == WINDOW_LIMIT else "engineering-smoke",
        "candidate_pairs": [list(pair) for pair in CANDIDATE_PAIRS],
        "selected_pair": list(selected["pair"]),
        "evaluation_alpha": EVALUATION_ALPHA,
        "evaluation_beta": EVALUATION_BETA,
        "zero_alpha_parity": parity,
        "fit_candidates": candidates,
        "assessment_deltas": deltas,
        "assessment_mean_delta": sum(deltas) / len(deltas),
        "assessment_bootstrap_upper_95": _bootstrap_upper(deltas),
        "deterministic_repeat_max_abs_delta": max(abs(value) for value in repeat_deltas),
        "temperature_control": {"temperature": 1.20, "baseline_mean_nll": _evaluate(model, tokenizer, assessment, None, temperature=1.20)["mean_nll"]},
        "training": False,
        "network_access": False,
        "weights_frozen": True,
    }
    result["result_sha256"] = digest(result)
    output.mkdir(parents=True)
    (output / "instance-result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("instance",), default="instance")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--corpus-root", type=Path, required=True)
    parser.add_argument("--model", type=Path, default=base.DEFAULT_MODEL)
    parser.add_argument("--instance-id", required=True)
    parser.add_argument("--window-limit", type=int, choices=(SMOKE_WINDOW_LIMIT, WINDOW_LIMIT), default=WINDOW_LIMIT)
    args = parser.parse_args()
    print(json.dumps(run_instance(args.output, args.corpus_root, args.model, args.instance_id, args.window_limit), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
