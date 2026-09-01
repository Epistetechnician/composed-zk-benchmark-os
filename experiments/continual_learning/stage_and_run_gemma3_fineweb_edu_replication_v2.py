#!/usr/bin/env python3
"""Stage and execute the Gemma3 FineWeb-Edu replication V2 campaign.

State slice: continual-learning-gemma3-fineweb-edu-replication-v2.

The runner is review-gated and offline-only. It imports only the low-level
Gemma3 forward/evaluation seam from the older engine; no V1 protocol,
configuration, corpus, result, or review is used as an approved input. A
fresh accepted V2 review is required before tokenizer/model loading or any
assessment-related work.
"""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import json
import math
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import urllib.request
from dataclasses import asdict
from pathlib import Path
from typing import Any, Iterator

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from experiments.continual_learning import gemma3_paper_recirculation_v1 as engine
from experiments.continual_learning import validate_gemma3_fineweb_edu_replication_v2 as validator

STATE_SLICE = "continual-learning-gemma3-fineweb-edu-replication-v2"
CLAIM_CEILING = "LocalDevelopmentGemma3FineWebEduReplicationV2"
CORPUS_SCHEMA = "gemma3-fineweb-edu-replication-v2-corpus"
RESULT_SCHEMA = "gemma3-fineweb-edu-replication-v2-result"
PRIMARY_VOLUME = Path("/Volumes/PrimaryED")
DEFAULT_MODEL = Path("/Users/shaanp/.lmstudio/models/mlx-community/gemma-3-1b-pt-bf16")
DEFAULT_RAW_ROOT = Path("/Volumes/PrimaryED/ResearchArtifacts/composed-zk-benchmark-os/gemma3-fineweb-edu-bounded-raw-v1")
DEFAULT_R1_SOURCE_ROOT = Path("/Volumes/PrimaryED/ResearchArtifacts/composed-zk-benchmark-os/gemma3-fineweb-edu-bounded-source-v1")
DEFAULT_SOURCE_ROOT = Path("/Volumes/PrimaryED/ResearchArtifacts/composed-zk-benchmark-os/gemma3-fineweb-edu-replication-v2-source")
DEFAULT_CORPUS_ROOT = Path("/Volumes/PrimaryED/ResearchArtifacts/composed-zk-benchmark-os/gemma3-fineweb-edu-replication-v2-corpus")
DEFAULT_OUTPUT_ROOT = Path("/Volumes/PrimaryED/ResearchArtifacts/composed-zk-benchmark-os/gemma3-fineweb-edu-replication-v2-result")
WINDOW_TOKENS = validator.WINDOW_TOKENS
FIT_WINDOW_COUNT = validator.FIT_WINDOW_COUNT
ASSESSMENT_WINDOW_COUNT = validator.ASSESSMENT_WINDOW_COUNT
FIT_ALPHA = validator.FIT_ALPHA
EVALUATION_ALPHA = validator.EVALUATION_ALPHA
EVALUATION_BETA = validator.EVALUATION_BETA
TEMPERATURE_CONTROL = validator.TEMPERATURE_CONTROL
CANDIDATE_PAIRS = validator.CANDIDATE_PAIRS
PARITY_TOLERANCE = validator.PARITY_TOLERANCE
EXPECTED_MODEL_MANIFEST_SHA256 = validator.EXPECTED_MODEL_MANIFEST_SHA256
SELECTION_POLICY = "first-64-eligible-1024-token-windows-per-disjoint-v2-source-split"


def digest(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _external(path: Path, label: str) -> Path:
    resolved = path.expanduser().resolve()
    repository = REPO_ROOT.resolve()
    if resolved == repository or repository in resolved.parents:
        raise ValueError(f"{label} must be outside the repository: {resolved}")
    return resolved


def _primary(path: Path, label: str) -> Path:
    resolved = _external(path, label)
    volume = PRIMARY_VOLUME.resolve()
    if not volume.is_dir():
        raise FileNotFoundError(f"required external volume is not mounted: {volume}")
    if resolved != volume and volume not in resolved.parents:
        raise ValueError(f"{label} must be under {volume}: {resolved}")
    return resolved


def _regular(path: Path, label: str) -> Path:
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"{label} must be a regular file: {path}")
    return path


def _json(path: Path, label: str) -> dict[str, Any]:
    value = json.loads(_regular(path, label).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be a JSON object")
    return value


def _jsonl(path: Path, label: str) -> list[dict[str, Any]]:
    rows = []
    with _regular(path, label).open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                raise ValueError(f"{label} has a blank line at {line_number}")
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValueError(f"{label} line {line_number} is not an object")
            rows.append(value)
    return rows


@contextlib.contextmanager
def network_block() -> Iterator[None]:
    """Install a process-local hard network denial for model execution."""

    old_env = {key: os.environ.get(key) for key in ("HF_HUB_OFFLINE", "TRANSFORMERS_OFFLINE", "HF_DATASETS_OFFLINE")}
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    os.environ["HF_DATASETS_OFFLINE"] = "1"

    def forbidden(*_args: Any, **_kwargs: Any) -> Any:
        raise RuntimeError("network access is disabled for V2 offline execution")

    original_socket = socket.socket
    original_create_connection = socket.create_connection
    original_getaddrinfo = socket.getaddrinfo
    original_urlopen = urllib.request.urlopen

    class OfflineSocket(original_socket):
        def connect(self, *_args: Any, **_kwargs: Any) -> None:
            raise RuntimeError("network access is disabled for V2 offline execution")

        def connect_ex(self, *_args: Any, **_kwargs: Any) -> int:
            raise RuntimeError("network access is disabled for V2 offline execution")

    socket.socket = OfflineSocket
    socket.create_connection = forbidden
    socket.getaddrinfo = forbidden
    urllib.request.urlopen = forbidden
    try:
        yield
    finally:
        socket.socket = original_socket
        socket.create_connection = original_create_connection
        socket.getaddrinfo = original_getaddrinfo
        urllib.request.urlopen = original_urlopen
        for key, value in old_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def _load_tokenizer_offline(model_path: Path) -> Any:
    from mlx_lm.utils import load_tokenizer

    from experiments.continual_learning.mlx_tokenizer_policy import (
        tokenizer_config_from_policy,
        tokenizer_policy_for_model,
    )

    policy = tokenizer_policy_for_model(model_path)
    return load_tokenizer(
        model_path,
        tokenizer_config_extra=tokenizer_config_from_policy(policy) or None,
    )


def _window_from_row(tokenizer: Any, row: dict[str, Any], relative_path: Path) -> engine.CorpusWindow | None:
    document_id = row.get("document_id")
    text = row.get("text")
    if not isinstance(document_id, str) or not document_id:
        raise ValueError("source record has invalid document_id")
    if not isinstance(text, str) or not text.strip():
        raise ValueError(f"source record has empty text: {document_id}")
    token_ids = list(tokenizer.encode(text, add_special_tokens=False))
    if len(token_ids) < WINDOW_TOKENS:
        return None
    selected_ids = token_ids[:WINDOW_TOKENS]
    window_text = tokenizer.decode(selected_ids)
    if list(tokenizer.encode(window_text, add_special_tokens=False)) != selected_ids:
        raise ValueError(f"tokenizer round-trip changed source record: {document_id}")
    window_bytes = window_text.encode("utf-8")
    return engine.CorpusWindow(
        dataset="fineweb_edu",
        document_id=document_id,
        relative_path=relative_path.as_posix(),
        window_ordinal=0,
        text=window_text,
        byte_len=len(window_bytes),
        source_sha256=sha256_bytes(text.encode("utf-8")),
        text_sha256=sha256_bytes(window_bytes),
        token_count=WINDOW_TOKENS,
    )


def _require_review(review_receipt: Path) -> dict[str, Any]:
    return validator.validate_review_receipt(review_receipt, validator.PROTOCOL_SHA256)


def stage_corpus(source_root: Path, corpus_root: Path, model_path: Path, raw_root: Path, r1_source_root: Path, review_receipt: Path) -> dict[str, Any]:
    source_root = _primary(source_root, "source root")
    corpus_root = _primary(corpus_root, "corpus root")
    model_path = _external(model_path, "model path")
    raw_root = _primary(raw_root, "raw root")
    r1_source_root = _primary(r1_source_root, "prior pilot source root")
    if corpus_root.exists() or corpus_root.is_symlink():
        raise FileExistsError(f"refusing to overwrite V2 corpus root: {corpus_root}")
    review = _require_review(review_receipt)
    source_validation = validator.validate_source(source_root, raw_root, r1_source_root)
    model_manifest = validator._model_manifest(model_path)
    if model_manifest["manifest_sha256"] != EXPECTED_MODEL_MANIFEST_SHA256:
        raise ValueError("cached model manifest does not match frozen V2 model custody")
    source_manifest = _json(source_root / "acquisition-manifest.json", "V2 source manifest")
    tokenizer = None
    with network_block():
        tokenizer = _load_tokenizer_offline(model_path)
    staging = Path(tempfile.mkdtemp(prefix=f".{corpus_root.name}.staging-", dir=corpus_root.parent))
    try:
        windows: dict[str, list[engine.CorpusWindow]] = {"fit": [], "assessment": []}
        entries: dict[str, list[dict[str, Any]]] = {"fit": [], "assessment": []}
        excluded: dict[str, list[dict[str, Any]]] = {"fit": [], "assessment": []}
        source_keys = (("fit", "fit/fineweb_edu", FIT_WINDOW_COUNT), ("assessment", "assessment/fineweb_edu", ASSESSMENT_WINDOW_COUNT))
        for split, key, target in source_keys:
            metadata = source_manifest["datasets"][key]
            rows = _jsonl(source_root / metadata["normalized_path"], f"V2 source {key}")
            for ordinal, row in enumerate(rows):
                if len(windows[split]) >= target:
                    break
                relative = Path(split) / "fineweb_edu" / f"window-{len(windows[split]):06d}.txt"
                window = _window_from_row(tokenizer, row, relative)
                if window is None:
                    excluded[split].append({"document_id": row.get("document_id"), "source_row_index": row.get("source_row_index"), "reason": "shorter_than_fixed_1024_token_window"})
                    continue
                output_path = staging / relative
                output_path.parent.mkdir(parents=True, exist_ok=True)
                output_path.write_text(window.text, encoding="utf-8")
                windows[split].append(window)
                entries[split].append({
                    "dataset": window.dataset,
                    "document_id": window.document_id,
                    "path": window.relative_path,
                    "window_ordinal": window.window_ordinal,
                    "byte_len": window.byte_len,
                    "source_sha256": window.source_sha256,
                    "text_sha256": window.text_sha256,
                    "token_count": window.token_count,
                    "source_row_index": row["source_row_index"],
                    "source_path": row["source_path"],
                })
            if len(windows[split]) != target:
                raise ValueError(f"{split} has only {len(windows[split])} eligible V2 windows; expected {target}")
        body = {
            "schema": CORPUS_SCHEMA,
            "state_slice": STATE_SLICE,
            "claim_ceiling": CLAIM_CEILING,
            "window_token_count": WINDOW_TOKENS,
            "source_manifest_sha256": source_manifest["manifest_sha256"],
            "source_root": str(source_root),
            "selection_policy": SELECTION_POLICY,
            "fit": entries["fit"],
            "assessment": entries["assessment"],
            "fit_window_count": len(windows["fit"]),
            "assessment_window_count": len(windows["assessment"]),
            "excluded_short_records": excluded,
            "network_access": False,
            "training": False,
            "scientific_execution": False,
            "evidence_ledger_mutation": False,
        }
        manifest = {**body, "manifest_sha256": digest(body)}
        (staging / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        validation = validator.validate_corpus(staging, source_root, raw_root, r1_source_root, source_manifest["manifest_sha256"])
        os.replace(staging, corpus_root)
        return {"review_receipt_sha256": sha256_bytes(review_receipt.read_bytes()), "source_validation": source_validation, "corpus_manifest": manifest, "validation": validation}
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise


def _load_windows(corpus_root: Path, manifest: dict[str, Any], split: str) -> list[engine.CorpusWindow]:
    windows = []
    for entry in manifest[split]:
        path = _regular(corpus_root / entry["path"], f"V2 {split} window")
        text = path.read_text(encoding="utf-8")
        windows.append(engine.CorpusWindow(
            dataset="fineweb_edu",
            document_id=entry["document_id"],
            relative_path=entry["path"],
            window_ordinal=entry["window_ordinal"],
            text=text,
            byte_len=entry["byte_len"],
            source_sha256=entry["source_sha256"],
            text_sha256=entry["text_sha256"],
            token_count=entry["token_count"],
        ))
    return windows


def _run_validator(result_root: Path, corpus_root: Path, source_root: Path, raw_root: Path, r1_source_root: Path, model_path: Path, review_receipt: Path, corpus_manifest_sha256: str) -> dict[str, Any]:
    environment = os.environ.copy()
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    environment["PYTHONPATH"] = os.pathsep.join(value for value in (str(REPO_ROOT), environment.get("PYTHONPATH")) if value)
    completed = subprocess.run([
        sys.executable, "-B", str(validator.__file__),
        "--result-root", str(result_root),
        "--corpus-root", str(corpus_root),
        "--source-root", str(source_root),
        "--raw-root", str(raw_root),
        "--r1-source-root", str(r1_source_root),
        "--model", str(model_path),
        "--review-receipt", str(review_receipt),
        "--corpus-manifest-sha256", corpus_manifest_sha256,
    ], cwd=REPO_ROOT, env=environment, capture_output=True, text=True, check=False)
    if completed.returncode != 0:
        raise RuntimeError(f"independent V2 result validation failed:\n{completed.stdout}\n{completed.stderr}")
    value = json.loads(completed.stdout)
    if not isinstance(value, dict) or value.get("valid") is not True:
        raise RuntimeError(f"independent V2 validator returned invalid output: {value}")
    return value


def _per_document(assessment_baseline: dict[str, Any], assessment_selected: dict[str, Any]) -> list[dict[str, Any]]:
    baseline_rows = {row["document_id"]: row for row in assessment_baseline["rows"]}
    selected_rows = {row["document_id"]: row for row in assessment_selected["rows"]}
    if set(baseline_rows) != set(selected_rows):
        raise ValueError("baseline and selected assessment document sets differ")
    rows = []
    for document_id in sorted(baseline_rows):
        baseline = baseline_rows[document_id]
        selected = selected_rows[document_id]
        if baseline["target_count"] != selected["target_count"]:
            raise ValueError("baseline and selected target counts differ")
        target_count = int(baseline["target_count"])
        baseline_nll = float(baseline["nll"])
        selected_nll = float(selected["nll"])
        delta = selected_nll / target_count - baseline_nll / target_count
        if not all(math.isfinite(value) for value in (baseline_nll, selected_nll, delta)):
            raise ValueError("nonfinite assessment per-document metric")
        rows.append({
            "dataset": "fineweb_edu",
            "document_id": document_id,
            "text_sha256": selected["text_sha256"],
            "target_count": target_count,
            "baseline_nll": baseline_nll,
            "selected_nll": selected_nll,
            "delta_selected_minus_baseline": delta,
        })
    return rows


def run_campaign(source_root: Path, corpus_root: Path, output_root: Path, model_path: Path, raw_root: Path, r1_source_root: Path, review_receipt: Path) -> dict[str, Any]:
    source_root = _primary(source_root, "source root")
    corpus_root = _primary(corpus_root, "corpus root")
    output_root = _primary(output_root, "output root")
    model_path = _external(model_path, "model path")
    raw_root = _primary(raw_root, "raw root")
    r1_source_root = _primary(r1_source_root, "prior pilot source root")
    if output_root.exists() or output_root.is_symlink():
        raise FileExistsError(f"refusing to overwrite V2 result root: {output_root}")
    review = _require_review(review_receipt)
    source_validation = validator.validate_source(source_root, raw_root, r1_source_root)
    corpus_validation = validator.validate_corpus(corpus_root, source_root, raw_root, r1_source_root, source_validation["source_manifest_sha256"])
    corpus_manifest = _json(corpus_root / "manifest.json", "V2 corpus manifest")
    model_files_before = validator._model_manifest(model_path)
    if model_files_before["manifest_sha256"] != EXPECTED_MODEL_MANIFEST_SHA256:
        raise ValueError("cached model manifest does not match frozen V2 model custody")
    if EVALUATION_BETA != 1.0 - EVALUATION_ALPHA:
        raise ValueError("V2 beta must equal the fixed destination coefficient 1-alpha")
    fit = _load_windows(corpus_root, corpus_manifest, "fit")
    assessment = _load_windows(corpus_root, corpus_manifest, "assessment")
    all_windows = (*fit, *assessment)
    with network_block():
        model, tokenizer, tokenizer_policy = engine._load_runtime(model_path)
        layer_count = len(model.model.layers)
        if getattr(model.args, "model_type", None) != "gemma3_text" or layer_count != 26:
            raise ValueError(f"expected cached Gemma3 1B PT text model with 26 layers, found {layer_count}")
        parity_checks = [engine.parity_check(model, tokenizer, window.text) for window in all_windows]
        if not all(check["passed"] for check in parity_checks):
            raise RuntimeError("V2 zero-alpha native parity gate failed")
        fit_baseline = engine.evaluate_windows(model, tokenizer, fit, None, include_rows=True)
        fit_candidates = []
        for source, destination in CANDIDATE_PAIRS:
            config = engine.RecirculationConfig(source, destination, FIT_ALPHA)
            metrics = engine.evaluate_windows(model, tokenizer, fit, config, include_rows=True)
            fit_candidates.append({"config": asdict(config), "metrics": metrics})
        selected = min(fit_candidates, key=lambda item: (item["metrics"]["mean_nll"], item["config"]["source_layer"], item["config"]["destination_layer"]))
        selected_config = engine.RecirculationConfig(**selected["config"])
        locked_config = engine.RecirculationConfig(selected_config.source_layer, selected_config.destination_layer, EVALUATION_ALPHA)
        assessment_baseline = engine.evaluate_windows(model, tokenizer, assessment, None, include_rows=True)
        assessment_selected = engine.evaluate_windows(model, tokenizer, assessment, locked_config, include_rows=True)
        assessment_temperature_baseline = engine.evaluate_windows(model, tokenizer, assessment, None, temperature=TEMPERATURE_CONTROL, include_rows=True)
        assessment_temperature_selected = engine.evaluate_windows(model, tokenizer, assessment, locked_config, temperature=TEMPERATURE_CONTROL, include_rows=True)
        assessment_repeat = engine.evaluate_windows(model, tokenizer, assessment, locked_config, include_rows=True)
        model_files_after = validator._model_manifest(model_path)
    if model_files_after != model_files_before:
        raise RuntimeError("cached model manifest changed during frozen V2 inference")
    intervention_reach = any(abs(item["metrics"]["mean_nll"] - fit_baseline["mean_nll"]) > 0.0 for item in fit_candidates)
    if not intervention_reach:
        raise RuntimeError("V2 nonzero intervention reach gate failed")
    repeat_delta = max(abs(assessment_selected["mean_nll"] - assessment_repeat["mean_nll"]), abs(assessment_selected["perplexity"] - assessment_repeat["perplexity"]))
    if repeat_delta > PARITY_TOLERANCE:
        raise RuntimeError(f"V2 deterministic repeat gate failed: {repeat_delta}")
    assessment_rows = _per_document(assessment_baseline, assessment_selected)
    bootstrap = validator.bootstrap_mean_ci(row["delta_selected_minus_baseline"] for row in assessment_rows)
    decision = validator.decide_replication(bootstrap)
    review_sha = sha256_bytes(review_receipt.read_bytes())
    config = {
        "schema": RESULT_SCHEMA,
        "state_slice": STATE_SLICE,
        "claim_ceiling": CLAIM_CEILING,
        "protocol_sha256": validator.PROTOCOL_SHA256,
        "review_receipt_sha256": review_sha,
        "source_schema": validator.SOURCE_SCHEMA,
        "corpus_schema": CORPUS_SCHEMA,
        "source_manifest_sha256": source_validation["source_manifest_sha256"],
        "corpus_manifest_sha256": corpus_validation["corpus_manifest_sha256"],
        "model_name": model_path.name,
        "model_path": str(model_path),
        "model_manifest_sha256": model_files_after["manifest_sha256"],
        "dataset": "fineweb_edu",
        "architecture": "gemma3_text",
        "layer_count": layer_count,
        "protocol": "fineweb-edu-fresh-disjoint-1024-token-replication-v2",
        "mechanism_source": "arxiv:2608.17981",
        "fresh_row_range": {"start": validator.FRESH_ROW_START, "end_exclusive": validator.FRESH_ROW_END, "count_per_shard": validator.FRESH_ROW_COUNT},
        "window_token_count": WINDOW_TOKENS,
        "fit_window_count": len(fit),
        "assessment_window_count": len(assessment),
        "candidate_pairs": [list(pair) for pair in CANDIDATE_PAIRS],
        "fit_alpha": FIT_ALPHA,
        "evaluation_alpha": EVALUATION_ALPHA,
        "evaluation_beta": EVALUATION_BETA,
        "temperature_control": TEMPERATURE_CONTROL,
        "normalization": "source_l2_norm_to_destination_l2_norm",
        "selected_fit_config": asdict(selected_config),
        "locked_evaluation_config": asdict(locked_config),
        "paper_expected_pair": {"source_layer": 11, "destination_layer": 4},
        "controls": ["native_baseline", "zero_alpha_identity", "temperature_1.20", "deterministic_repeat", "frozen_model_manifest"],
        "qualification": {"parity_all_passed": True, "nonzero_intervention_reach": intervention_reach, "deterministic_repeat_max_metric_delta": repeat_delta, "model_layer_count": layer_count},
        "assessment_authorized_by_review": review["review_status"] == "ACCEPT",
        "network_access": False,
        "training": False,
        "weights_frozen": True,
        "evidence_ledger_mutation": False,
        "tokenizer_policy": tokenizer_policy,
        "runtime": {"python": engine.package_version("pip"), "mlx": engine.package_version("mlx"), "mlx_lm": engine.package_version("mlx-lm")},
        "selection_policy": SELECTION_POLICY,
    }
    config["config_sha256"] = digest(config)
    results = {
        "schema": RESULT_SCHEMA,
        "state_slice": STATE_SLICE,
        "claim_ceiling": CLAIM_CEILING,
        "protocol_sha256": validator.PROTOCOL_SHA256,
        "source_manifest_sha256": source_validation["source_manifest_sha256"],
        "corpus_manifest_sha256": corpus_validation["corpus_manifest_sha256"],
        "model_manifest_sha256": model_files_after["manifest_sha256"],
        "review_receipt_sha256": review_sha,
        "parity": {"sequence_count": len(parity_checks), "max_abs_logit_delta": max(check["max_abs_logit_delta"] for check in parity_checks), "tolerance": PARITY_TOLERANCE, "all_passed": all(check["passed"] for check in parity_checks)},
        "fit_baseline": fit_baseline,
        "fit_candidates": fit_candidates,
        "selected_fit_config": asdict(selected_config),
        "locked_evaluation_config": asdict(locked_config),
        "assessment_baseline": assessment_baseline,
        "assessment_selected": assessment_selected,
        "assessment_temperature_baseline": assessment_temperature_baseline,
        "assessment_temperature_selected": assessment_temperature_selected,
        "assessment_repeat": assessment_repeat,
        "deterministic_repeat_passed": repeat_delta <= PARITY_TOLERANCE,
        "assessment_repeat_max_metric_delta": repeat_delta,
        "assessment_per_document": assessment_rows,
        "bootstrap": bootstrap,
        "decision": decision,
        "paper_expected_pair_recovered": selected_config.source_layer == 11 and selected_config.destination_layer == 4,
        "performance_result_is_local_fineweb_edu_replication_v2_only": True,
    }
    results["results_sha256"] = digest(results)
    receipt = {
        "schema": RESULT_SCHEMA,
        "state_slice": STATE_SLICE,
        "claim_ceiling": CLAIM_CEILING,
        "protocol_sha256": validator.PROTOCOL_SHA256,
        "review_receipt_sha256": review_sha,
        "config_sha256": config["config_sha256"],
        "results_sha256": results["results_sha256"],
        "source_manifest_sha256": source_validation["source_manifest_sha256"],
        "corpus_manifest_sha256": corpus_validation["corpus_manifest_sha256"],
        "model_manifest_sha256": model_files_after["manifest_sha256"],
        "zero_alpha_parity_passed": results["parity"]["all_passed"],
        "nonzero_intervention_reach_passed": intervention_reach,
        "deterministic_repeat_passed": results["deterministic_repeat_passed"],
        "assessment_authorized_by_review": True,
        "network_access": False,
        "training": False,
        "weights_frozen": True,
        "evidence_ledger_mutation": False,
        "bootstrap": bootstrap,
        "decision": decision,
    }
    receipt["receipt_sha256"] = digest(receipt)
    output_root.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{output_root.name}.staging-", dir=output_root.parent))
    try:
        for name, value in (("config.json", config), ("results.json", results), ("receipt.json", receipt), ("model-manifest.json", model_files_after)):
            (staging / name).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        validation = _run_validator(staging, corpus_root, source_root, raw_root, r1_source_root, model_path, review_receipt, corpus_validation["corpus_manifest_sha256"])
        (staging / "validator-receipt.json").write_text(json.dumps(validation, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        os.replace(staging, output_root)
    finally:
        if staging.exists():
            shutil.rmtree(staging, ignore_errors=True)
    return {"state_slice": STATE_SLICE, "claim_ceiling": CLAIM_CEILING, "output_root": str(output_root), "decision": decision, "review_receipt_sha256": review_sha, "results_sha256": results["results_sha256"], "bootstrap": bootstrap, "validator": validation}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-root", type=Path, default=DEFAULT_RAW_ROOT)
    parser.add_argument("--r1-source-root", type=Path, default=DEFAULT_R1_SOURCE_ROOT)
    parser.add_argument("--source-root", type=Path, default=DEFAULT_SOURCE_ROOT)
    parser.add_argument("--corpus-root", type=Path, default=DEFAULT_CORPUS_ROOT)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--model", type=Path, default=DEFAULT_MODEL)
    parser.add_argument("--review-receipt", type=Path, required=True)
    parser.add_argument("--pack-only", action="store_true")
    args = parser.parse_args()
    if args.pack_only:
        value = stage_corpus(args.source_root, args.corpus_root, args.model, args.raw_root, args.r1_source_root, args.review_receipt)
    else:
        value = run_campaign(args.source_root, args.corpus_root, args.output_root, args.model, args.raw_root, args.r1_source_root, args.review_receipt)
    print(json.dumps(value, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
