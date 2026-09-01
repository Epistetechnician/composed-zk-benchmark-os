#!/usr/bin/env python3
"""Stage and execute the reviewed V3 FineWeb-Edu replication.

State slice: continual-learning-gemma3-fineweb-edu-replication-v3.
This entrypoint is review-gated, model-frozen, and offline-only. It does not
repair or reuse V1/V2 protocols, corpora, or results as scientific inputs.
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
from dataclasses import asdict
from pathlib import Path
from typing import Any, Iterable

from experiments.continual_learning import gemma3_fineweb_edu_replication_v3_contract as c
from experiments.continual_learning import validate_gemma3_fineweb_edu_replication_v3 as validator

REPO_ROOT = c.REPO_ROOT
VALIDATOR = Path(__file__).with_name("validate_gemma3_fineweb_edu_replication_v3.py")
REVIEW_RECEIPT = REPO_ROOT / "docs/research/continual-learning/150-gemma3-fineweb-edu-replication-v3-independent-review-2026-08-30.json"
RAW_ROOT = Path("/Volumes/PrimaryED/ResearchArtifacts/composed-zk-benchmark-os/gemma3-fineweb-edu-bounded-raw-v1")
V3_SOURCE_ROOT = Path("/Volumes/PrimaryED/ResearchArtifacts/composed-zk-benchmark-os/gemma3-fineweb-edu-replication-v3-source")
V3_CORPUS_ROOT = Path("/Volumes/PrimaryED/ResearchArtifacts/composed-zk-benchmark-os/gemma3-fineweb-edu-replication-v3-corpus")
V3_RESULT_ROOT = Path("/Volumes/PrimaryED/ResearchArtifacts/composed-zk-benchmark-os/gemma3-fineweb-edu-replication-v3-result")
R1_SOURCE_ROOT = c.R1_SOURCE_ROOT


def _json(path: Path, label: str) -> dict[str, Any]:
    return validator._json(path, label)


def _write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _require_native_sandbox() -> None:
    if sys.platform == "darwin" and os.environ.get("V3_NATIVE_SANDBOX_ACTIVE") != "1":
        raise RuntimeError("V3 execution requires the native macOS network sandbox")


def _enter_native_sandbox() -> None:
    if sys.platform != "darwin" or os.environ.get("V3_NATIVE_SANDBOX_ACTIVE") == "1":
        return
    sandbox = shutil.which("sandbox-exec")
    if sandbox is None:
        raise RuntimeError("sandbox-exec is unavailable; V3 fails closed")
    environment = os.environ.copy()
    environment["V3_NATIVE_SANDBOX_ACTIVE"] = "1"
    profile = "(version 1) (deny network*) (allow default)"
    os.execvpe(
        sandbox,
        [sandbox, "-p", profile, sys.executable, "-B", str(Path(__file__).resolve()), *sys.argv[1:]],
        environment,
    )


def _review_snapshot(path: Path) -> tuple[dict[str, Any], bytes, str]:
    raw = c.regular(path, "V3 review receipt").read_bytes()
    receipt = validator.validate_review_receipt(path)
    return receipt, raw, c.sha256_file(path)


def _assert_review_snapshot(path: Path, raw: bytes, digest: str) -> None:
    current = c.regular(path, "V3 review receipt").read_bytes()
    if current != raw or c.sha256_file(path) != digest:
        raise RuntimeError("V3 accepted review receipt changed after snapshot")


def _require_review(path: Path = REVIEW_RECEIPT) -> tuple[dict[str, Any], bytes, str]:
    if path.resolve() != REVIEW_RECEIPT.resolve():
        raise ValueError(f"V3 review receipt must be the sealed path: {REVIEW_RECEIPT}")
    return _review_snapshot(path)


def _source_rows(path: Path, label: str) -> list[dict[str, Any]]:
    return validator._jsonl(path, label)


def _stage_windows(
    staging: Path,
    split: str,
    rows: Iterable[dict[str, Any]],
    tokenizer: Any,
    count: int,
) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for row in rows:
        if len(entries) >= count:
            break
        text = row.get("text")
        document_id = row.get("document_id")
        if not isinstance(text, str) or not text.strip() or not isinstance(document_id, str) or not document_id:
            raise ValueError(f"V3 {split} source row has invalid text or document_id")
        token_ids = list(tokenizer.encode(text, add_special_tokens=False))
        if len(token_ids) < c.WINDOW_TOKENS:
            continue
        window_ids = token_ids[: c.WINDOW_TOKENS]
        window_text = tokenizer.decode(window_ids)
        if list(tokenizer.encode(window_text, add_special_tokens=False)) != window_ids:
            raise ValueError(f"V3 {split} tokenizer round-trip failed for {document_id}")
        ordinal = len(entries)
        relative_path = f"{split}/fineweb_edu/window-{ordinal:06d}.txt"
        destination = staging / relative_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        encoded = window_text.encode("utf-8")
        destination.write_bytes(encoded)
        entries.append(
            {
                "dataset": "fineweb_edu",
                "document_id": document_id,
                "path": relative_path,
                "window_ordinal": 0,
                "byte_len": len(encoded),
                "source_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
                "text_sha256": hashlib.sha256(encoded).hexdigest(),
                "token_count": c.WINDOW_TOKENS,
                "source_row_index": row["source_row_index"],
                "source_path": row["source_path"],
            }
        )
    if len(entries) != count:
        raise ValueError(f"V3 {split} produced {len(entries)} windows; expected {count}")
    return entries


def stage_corpus(
    source_root: Path,
    corpus_root: Path,
    model_path: Path = c.MODEL_PATH,
    review_receipt: Path = REVIEW_RECEIPT,
) -> dict[str, Any]:
    """Create the V3 tokenizer-locked corpus only after review acceptance."""

    _require_native_sandbox()
    _review, review_bytes, review_sha = _require_review(review_receipt)
    source_root = c.primary(source_root, "V3 source root")
    corpus_root = c.primary(corpus_root, "V3 corpus root")
    model_path = model_path.expanduser().absolute()
    if model_path != c.MODEL_PATH or model_path.is_symlink():
        raise ValueError(f"V3 exact model path required: {c.MODEL_PATH}")
    if corpus_root.exists() or corpus_root.is_symlink():
        raise FileExistsError(f"refusing to overwrite V3 corpus root: {corpus_root}")
    source_audit = validator.validate_source(source_root, RAW_ROOT, R1_SOURCE_ROOT)
    staging = Path(tempfile.mkdtemp(prefix=f".{corpus_root.name}.staging-", dir=corpus_root.parent))
    try:
        _assert_review_snapshot(review_receipt, review_bytes, review_sha)
        with c.network_block():
            tokenizer = validator._load_tokenizer(model_path)
            fit_rows = _source_rows(source_root / "fit/fineweb_edu.jsonl", "V3 fit source")
            assessment_rows = _source_rows(source_root / "assessment/fineweb_edu.jsonl", "V3 assessment source")
            fit_entries = _stage_windows(staging, "fit", fit_rows, tokenizer, c.FIT_WINDOW_COUNT)
            assessment_entries = _stage_windows(staging, "assessment", assessment_rows, tokenizer, c.ASSESSMENT_WINDOW_COUNT)
        body = {
            "schema": c.CORPUS_SCHEMA,
            "state_slice": c.STATE_SLICE,
            "claim_ceiling": c.CLAIM_CEILING,
            "source_manifest_sha256": source_audit["source_manifest_sha256"],
            "window_token_count": c.WINDOW_TOKENS,
            "selection_policy": c.SELECTION_POLICY,
            "fit_window_count": len(fit_entries),
            "assessment_window_count": len(assessment_entries),
            "fit": fit_entries,
            "assessment": assessment_entries,
            "network_access": False,
            "training": False,
            "scientific_execution": False,
            "evidence_ledger_mutation": False,
            "review_receipt_sha256": review_sha,
        }
        manifest = {**body, "manifest_sha256": c.digest(body)}
        _write_json(staging / "manifest.json", manifest)
        _assert_review_snapshot(review_receipt, review_bytes, review_sha)
        validation = validator.validate_corpus(staging, source_root, RAW_ROOT, R1_SOURCE_ROOT, model_path, source_audit["source_manifest_sha256"])
        os.replace(staging, corpus_root)
        return {"manifest": manifest, "validation": validation}
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise


def _metrics_finite(metrics: dict[str, Any], label: str) -> None:
    for field in ("mean_nll", "perplexity"):
        value = metrics.get(field)
        if value is None or isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
            raise ValueError(f"{label} {field} is not finite")


def _load_windows(corpus_root: Path, tokenizer: Any) -> tuple[list[Any], list[Any], dict[str, Any]]:
    fit_raw = _json(corpus_root / "manifest.json", "V3 corpus manifest")["fit"]
    assessment_raw = _json(corpus_root / "manifest.json", "V3 corpus manifest")["assessment"]
    fit = [validator._parse_window(corpus_root, item, tokenizer, "fit") for item in fit_raw]
    assessment = [validator._parse_window(corpus_root, item, tokenizer, "assessment") for item in assessment_raw]
    manifest = _json(corpus_root / "manifest.json", "V3 corpus manifest")
    return fit, assessment, {"manifest": manifest, "manifest_sha256": manifest["manifest_sha256"]}


def _run_effects(model_path: Path, corpus_root: Path, review_sha: str, source_sha: str) -> dict[str, Any]:
    from experiments.continual_learning import gemma3_paper_recirculation_v1 as engine

    with c.network_block():
        model, tokenizer, tokenizer_policy = engine._load_runtime(model_path)
        model_type = getattr(model.args, "model_type", None)
        layer_count = len(model.model.layers)
        if model_type != "gemma3_text" or layer_count != 26:
            raise ValueError(f"unexpected Gemma3 runtime shape/type: {model_type}, {layer_count}")
        parameter_before = c.model_parameter_digest(model)
        model_manifest_before = c.model_manifest(model_path)
        fit, assessment, corpus = _load_windows(corpus_root, tokenizer)
        parity_checks = [engine.parity_check(model, tokenizer, window.text) for window in (*fit, *assessment)]
        if len(parity_checks) != 128 or not all(item.get("passed") is True for item in parity_checks):
            raise RuntimeError("V3 zero-alpha parity gate failed")
        fit_baseline = engine.evaluate_windows(model, tokenizer, fit, None, include_rows=True)
        fit_candidates = []
        for source_layer, destination_layer in c.CANDIDATE_PAIRS:
            config = engine.RecirculationConfig(source_layer, destination_layer, c.FIT_ALPHA)
            metrics = engine.evaluate_windows(model, tokenizer, fit, config, include_rows=True)
            _metrics_finite(metrics, "V3 fit candidate")
            fit_candidates.append({"config": asdict(config), "metrics": metrics})
        candidate_keyed = [
            (candidate["metrics"]["mean_nll"], pair[0], pair[1], candidate)
            for pair, candidate in zip(c.CANDIDATE_PAIRS, fit_candidates, strict=True)
        ]
        selected = min(candidate_keyed, key=lambda item: (item[0], item[1], item[2]))[3]
        selected_config = dict(selected["config"])
        locked_config = asdict(engine.RecirculationConfig(selected_config["source_layer"], selected_config["destination_layer"], c.EVALUATION_ALPHA))
        assessment_baseline = engine.evaluate_windows(model, tokenizer, assessment, None, include_rows=True)
        assessment_selected = engine.evaluate_windows(model, tokenizer, assessment, engine.RecirculationConfig(**locked_config), include_rows=True)
        assessment_temperature_baseline = engine.evaluate_windows(model, tokenizer, assessment, None, temperature=c.TEMPERATURE_CONTROL, include_rows=True)
        assessment_temperature_selected = engine.evaluate_windows(model, tokenizer, assessment, engine.RecirculationConfig(**locked_config), temperature=c.TEMPERATURE_CONTROL, include_rows=True)
        assessment_repeat = engine.evaluate_windows(model, tokenizer, assessment, engine.RecirculationConfig(**locked_config), include_rows=True)
        parameter_after = c.model_parameter_digest(model)
        model_manifest_after = c.model_manifest(model_path)
        if model_manifest_after != model_manifest_before or parameter_after != parameter_before:
            raise RuntimeError("V3 frozen model custody changed during inference")
    repeat_delta = max(abs(a["nll"] - b["nll"]) for a, b in zip(assessment_selected["rows"], assessment_repeat["rows"], strict=True))
    for label, metrics in (("V3 fit baseline", fit_baseline), ("V3 assessment baseline", assessment_baseline), ("V3 assessment selected", assessment_selected), ("V3 temperature baseline", assessment_temperature_baseline), ("V3 temperature selected", assessment_temperature_selected), ("V3 repeat", assessment_repeat)):
        _metrics_finite(metrics, label)
    baseline_by_id = {row["document_id"]: row for row in assessment_baseline["rows"]}
    selected_by_id = {row["document_id"]: row for row in assessment_selected["rows"]}
    per_document = []
    for document_id in sorted(baseline_by_id):
        baseline_row = baseline_by_id[document_id]
        selected_row = selected_by_id[document_id]
        target_count = baseline_row["target_count"]
        delta = selected_row["nll"] / target_count - baseline_row["nll"] / target_count
        per_document.append({
            "dataset": "fineweb_edu",
            "document_id": document_id,
            "text_sha256": baseline_row["text_sha256"],
            "target_count": target_count,
            "baseline_nll": baseline_row["nll"],
            "selected_nll": selected_row["nll"],
            "delta_selected_minus_baseline": delta,
        })
    deltas = [row["delta_selected_minus_baseline"] for row in per_document]
    bootstrap = c.bootstrap_mean_ci(deltas)
    decision = c.decide_replication(bootstrap)
    parity = {
        "sequence_count": len(parity_checks),
        "max_abs_logit_delta": max(float(item["max_abs_logit_delta"]) for item in parity_checks),
        "tolerance": c.PARITY_TOLERANCE,
        "all_passed": all(item["passed"] for item in parity_checks),
        "checks": parity_checks,
    }
    controls = {
        "native_baseline": assessment_baseline,
        "zero_alpha_identity": parity,
        "all_candidate_evaluations": fit_candidates,
        "temperature_1.20_baseline": assessment_temperature_baseline,
        "temperature_1.20_intervention": assessment_temperature_selected,
        "deterministic_repeat": assessment_repeat,
        "frozen_model_manifest": {"before": model_manifest_before["manifest_sha256"], "after": model_manifest_after["manifest_sha256"]},
        "frozen_model_parameters": {"before": parameter_before, "after": parameter_after},
    }
    config = {
        "schema": c.RESULT_SCHEMA,
        "state_slice": c.STATE_SLICE,
        "claim_ceiling": c.CLAIM_CEILING,
        "protocol_sha256": c.PROTOCOL_SHA256,
        "review_receipt_sha256": review_sha,
        "source_manifest_sha256": source_sha,
        "corpus_manifest_sha256": corpus["manifest_sha256"],
        "model_name": model_path.name,
        "model_path": str(c.MODEL_PATH),
        "model_manifest_sha256": model_manifest_before["manifest_sha256"],
        "model_parameter_digest_before": parameter_before,
        "model_parameter_digest_after": parameter_after,
        "architecture": "gemma3_text",
        "model_type": model_type,
        "layer_count": layer_count,
        "protocol": "paper-aligned-one-additional-iteration-v1",
        "mechanism_source": "arxiv:2608.17981",
        "fresh_row_range": {"start": c.FRESH_ROW_START, "end_exclusive": c.FRESH_ROW_END, "count_per_shard": c.FRESH_ROW_COUNT},
        "window_token_count": c.WINDOW_TOKENS,
        "fit_window_count": c.FIT_WINDOW_COUNT,
        "assessment_window_count": c.ASSESSMENT_WINDOW_COUNT,
        "candidate_pairs": [list(pair) for pair in c.CANDIDATE_PAIRS],
        "fit_alpha": c.FIT_ALPHA,
        "evaluation_alpha": c.EVALUATION_ALPHA,
        "evaluation_beta": c.EVALUATION_BETA,
        "temperature_control": c.TEMPERATURE_CONTROL,
        "normalization": "source_l2_norm_to_destination_l2_norm",
        "selected_fit_config": selected_config,
        "locked_evaluation_config": locked_config,
        "paper_expected_pair": {"source_layer": 11, "destination_layer": 4},
        "controls": list(c.CONTROL_NAMES),
        "network_access": False,
        "training": False,
        "weights_frozen": True,
        "evidence_ledger_mutation": False,
        "assessment_authorized_by_review": True,
        "tokenizer_policy": tokenizer_policy,
        "runtime": {"python": sys.version.split()[0], "mlx": _package_version("mlx"), "mlx_lm": _package_version("mlx-lm")},
        "selection_policy": c.SELECTION_POLICY,
    }
    config["config_sha256"] = c.digest(config)
    results = {
        "schema": c.RESULT_SCHEMA,
        "state_slice": c.STATE_SLICE,
        "claim_ceiling": c.CLAIM_CEILING,
        "protocol_sha256": c.PROTOCOL_SHA256,
        "review_receipt_sha256": review_sha,
        "source_manifest_sha256": source_sha,
        "corpus_manifest_sha256": corpus["manifest_sha256"],
        "model_path": str(c.MODEL_PATH),
        "model_manifest_sha256": model_manifest_before["manifest_sha256"],
        "model_parameter_digest_before": parameter_before,
        "model_parameter_digest_after": parameter_after,
        "architecture": "gemma3_text",
        "model_type": model_type,
        "layer_count": layer_count,
        "network_access": False,
        "training": False,
        "weights_frozen": True,
        "evidence_ledger_mutation": False,
        "parity": parity,
        "fit_baseline": fit_baseline,
        "fit_candidates": fit_candidates,
        "selected_fit_config": selected_config,
        "locked_evaluation_config": locked_config,
        "paper_expected_pair": {"source_layer": 11, "destination_layer": 4},
        "assessment_baseline": assessment_baseline,
        "assessment_selected": assessment_selected,
        "assessment_temperature_baseline": assessment_temperature_baseline,
        "assessment_temperature_selected": assessment_temperature_selected,
        "assessment_repeat": assessment_repeat,
        "deterministic_repeat_passed": repeat_delta <= c.PARITY_TOLERANCE,
        "assessment_repeat_max_nll_delta": repeat_delta,
        "qualification": {"nonzero_intervention_reach": any(candidate["metrics"]["mean_nll"] != fit_baseline["mean_nll"] for candidate in fit_candidates)},
        "controls": controls,
        "assessment_per_document": per_document,
        "assessment_nll_delta_selected_minus_baseline": assessment_selected["mean_nll"] - assessment_baseline["mean_nll"],
        "bootstrap": bootstrap,
        "decision": decision,
        "paper_expected_pair_recovered": (selected_config["source_layer"], selected_config["destination_layer"]) == (11, 4),
        "local_only": True,
    }
    results["results_sha256"] = c.digest(results)
    receipt = {
        "schema": c.RESULT_SCHEMA,
        "state_slice": c.STATE_SLICE,
        "claim_ceiling": c.CLAIM_CEILING,
        "protocol_sha256": c.PROTOCOL_SHA256,
        "review_receipt_sha256": review_sha,
        "source_manifest_sha256": source_sha,
        "corpus_manifest_sha256": corpus["manifest_sha256"],
        "config_sha256": config["config_sha256"],
        "results_sha256": results["results_sha256"],
        "model_manifest_sha256": model_manifest_before["manifest_sha256"],
        "model_parameter_digest_before": parameter_before,
        "model_parameter_digest_after": parameter_after,
        "zero_alpha_parity_passed": parity["all_passed"],
        "nonzero_intervention_reach": results["qualification"]["nonzero_intervention_reach"],
        "deterministic_repeat_passed": results["deterministic_repeat_passed"],
        "network_access": False,
        "training": False,
        "weights_frozen": True,
        "evidence_ledger_mutation": False,
        "bootstrap": bootstrap,
        "decision": decision,
    }
    receipt["receipt_sha256"] = c.digest(receipt)
    return {"config": config, "results": results, "receipt": receipt, "corpus": corpus, "model_manifest": model_manifest_before}


def _package_version(name: str) -> str:
    try:
        from importlib.metadata import version
        return version(name)
    except Exception:
        return "unavailable"


def run_campaign(
    result_root: Path,
    source_root: Path,
    corpus_root: Path,
    raw_root: Path = RAW_ROOT,
    r1_source_root: Path = R1_SOURCE_ROOT,
    model_path: Path = c.MODEL_PATH,
    review_receipt: Path = REVIEW_RECEIPT,
) -> dict[str, Any]:
    _require_native_sandbox()
    _review, review_bytes, review_sha = _require_review(review_receipt)
    source_root = c.primary(source_root, "V3 source root")
    corpus_root = c.primary(corpus_root, "V3 corpus root")
    raw_root = c.primary(raw_root, "raw root")
    r1_source_root = c.primary(r1_source_root, "prior pilot source root")
    result_root = c.primary(result_root, "V3 result root")
    model_path = model_path.expanduser().absolute()
    if model_path != c.MODEL_PATH or model_path.is_symlink():
        raise ValueError(f"V3 exact model path required: {c.MODEL_PATH}")
    if result_root.exists() or result_root.is_symlink():
        raise FileExistsError(f"refusing to overwrite V3 result root: {result_root}")
    source_validation = validator.validate_source(source_root, raw_root, r1_source_root)
    corpus_validation = validator.validate_corpus(corpus_root, source_root, raw_root, r1_source_root, model_path, source_validation["source_manifest_sha256"])
    staging = Path(tempfile.mkdtemp(prefix=f".{result_root.name}.staging-", dir=result_root.parent))
    try:
        (staging / "review-receipt.json").write_bytes(review_bytes)
        _assert_review_snapshot(review_receipt, review_bytes, review_sha)
        payload = _run_effects(model_path, corpus_root, review_sha, source_validation["source_manifest_sha256"])
        _assert_review_snapshot(review_receipt, review_bytes, review_sha)
        _write_json(staging / "config.json", payload["config"])
        _write_json(staging / "results.json", payload["results"])
        _write_json(staging / "receipt.json", payload["receipt"])
        _write_json(staging / "corpus-manifest.json", payload["corpus"])
        _write_json(staging / "model-manifest.json", payload["model_manifest"])
        environment = os.environ.copy()
        environment["PYTHONDONTWRITEBYTECODE"] = "1"
        command = [
            sys.executable, "-B", str(VALIDATOR),
            "--result-root", str(staging), "--source-root", str(source_root),
            "--raw-root", str(raw_root), "--r1-source-root", str(r1_source_root),
            "--corpus-root", str(corpus_root), "--model", str(model_path),
            "--review-receipt", str(staging / "review-receipt.json"),
            "--corpus-manifest-sha256", corpus_validation["corpus_manifest_sha256"],
        ]
        completed = subprocess.run(command, cwd=REPO_ROOT, env=environment, capture_output=True, text=True, check=False)
        if completed.returncode != 0:
            raise RuntimeError(f"V3 result validator failed:\n{completed.stdout}\n{completed.stderr}")
        validation = json.loads(completed.stdout)
        if validation.get("valid") is not True:
            raise RuntimeError(f"V3 result validator returned invalid output: {validation}")
        _assert_review_snapshot(review_receipt, review_bytes, review_sha)
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
    parser.add_argument("--raw-root", type=Path, default=RAW_ROOT)
    parser.add_argument("--r1-source-root", type=Path, default=R1_SOURCE_ROOT)
    parser.add_argument("--model", type=Path, default=c.MODEL_PATH)
    parser.add_argument("--review-receipt", type=Path, default=REVIEW_RECEIPT)
    parser.add_argument("--stage-only", action="store_true")
    args = parser.parse_args()
    if args.stage_only:
        value = stage_corpus(args.source_root, args.corpus_root, args.model, args.review_receipt)
    else:
        value = run_campaign(args.result_root, args.source_root, args.corpus_root, args.raw_root, args.r1_source_root, args.model, args.review_receipt)
    print(json.dumps(value, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
