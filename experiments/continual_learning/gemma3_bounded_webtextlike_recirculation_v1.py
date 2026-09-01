#!/usr/bin/env python3
"""Run the bounded Gemma3 WebText-like recirculation mechanics pilot.

State slice: continual-learning-gemma3-paper-recirculation-c4-bounded-v1.

This runner consumes only the independently validated bounded WET acquisition
bundle. It uses the cached Gemma3 1B BF16 MLX checkpoint offline, keeps model
weights frozen, and writes a digest-bound result bundle outside the repository.
It is not a paper replication, full C4 experiment, training run, or production
benchmark.
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
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from experiments.continual_learning import (
    gemma3_paper_recirculation_v1 as engine,
    validate_gemma3_bounded_webtextlike_wet_v1 as source_validator,
)

STATE_SLICE = "continual-learning-gemma3-paper-recirculation-c4-bounded-v1"
CLAIM_CEILING = "LocalDevelopmentGemma3BoundedWebTextLikeRecirculationPilot"
SOURCE_SCHEMA = "gemma3-c4-bounded-wet-acquisition-v1"
CORPUS_SCHEMA = "gemma3-c4-bounded-wet-runtime-corpus-v2"
WINDOW_TOKENS = 256
MAX_RUNTIME_WINDOWS_PER_SPLIT = 4
FIT_ALPHA = 0.10
EVALUATION_ALPHA = 0.15
EVALUATION_BETA = 0.85
TEMPERATURE_CONTROL = 1.2
PILOT_PAIRS = ((7, 2), (9, 3), (11, 4), (12, 5))
DEFAULT_MODEL = Path(
    "/Users/shaanp/.lmstudio/models/mlx-community/gemma-3-1b-pt-bf16"
)
DEFAULT_SOURCE_ROOT = Path(
    "/Volumes/PrimaryED/ResearchArtifacts/composed-zk-benchmark-os/"
    "gemma3-c4-webtextlike-bounded-wet-v1"
)
DEFAULT_OUTPUT_ROOT = Path(
    "/Volumes/PrimaryED/ResearchArtifacts/composed-zk-benchmark-os/"
    "gemma3-c4-bounded-wet-recirculation-v1"
)
PRIMARY_VOLUME = Path("/Volumes/PrimaryED")
VALIDATOR = Path(__file__).with_name(
    "validate_gemma3_bounded_webtextlike_recirculation_v1.py"
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


def _external(path: Path, label: str) -> Path:
    resolved = path.expanduser().resolve()
    if resolved == REPO_ROOT or REPO_ROOT in resolved.parents:
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


def _read_json(path: Path, label: str) -> dict[str, Any]:
    value = json.loads(_regular(path, label).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be a JSON object")
    return value


def _read_jsonl(path: Path, label: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with _regular(path, label).open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                raise ValueError(f"{label} contains a blank line at {line_number}")
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValueError(f"{label} line {line_number} is not an object")
            rows.append(value)
    return rows


def _artifact(path: Path, label: str) -> dict[str, Any]:
    _regular(path, label)
    return {
        "path": str(path.resolve()),
        "byte_len": path.stat().st_size,
        "sha256": sha256_file(path),
    }


def _verify_source_bundle(source_root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    source_root = _primary(source_root, "bounded acquisition root")
    validation = source_validator.validate(source_root)
    manifest = _read_json(source_root / "acquisition-manifest.json", "acquisition manifest")
    if manifest.get("schema") != SOURCE_SCHEMA:
        raise ValueError("bounded acquisition schema mismatch")
    if manifest.get("state_slice") != STATE_SLICE:
        raise ValueError("bounded acquisition state slice mismatch")
    if manifest.get("full_c4_webtextlike") is not False:
        raise ValueError("bounded acquisition must not claim full C4")
    if manifest.get("scientific_execution") is not False:
        raise ValueError("acquisition bundle must not claim scientific execution")
    return manifest, validation


def _runtime_windows(
    source_root: Path,
    manifest: dict[str, Any],
    tokenizer: Any,
) -> tuple[list[engine.CorpusWindow], list[engine.CorpusWindow], dict[str, Any]]:
    windows: dict[str, list[engine.CorpusWindow]] = {"fit": [], "assessment": []}
    entries: dict[str, list[dict[str, Any]]] = {"fit": [], "assessment": []}
    excluded: dict[str, list[dict[str, Any]]] = {"fit": [], "assessment": []}
    deferred: dict[str, list[dict[str, Any]]] = {"fit": [], "assessment": []}
    seen_ids: set[str] = set()
    datasets = manifest.get("datasets")
    if not isinstance(datasets, dict):
        raise ValueError("bounded acquisition datasets are missing")
    for split in ("fit", "assessment"):
        metadata = datasets.get(split)
        if not isinstance(metadata, dict):
            raise ValueError(f"bounded acquisition metadata is missing: {split}")
        path = _regular(
            source_root / str(metadata["relative_path"]),
            f"bounded {split} JSONL",
        )
        if sha256_file(path) != metadata.get("sha256"):
            raise ValueError(f"bounded {split} JSONL checksum mismatch")
        rows = _read_jsonl(path, f"bounded {split} JSONL")
        if len(rows) != metadata.get("record_count"):
            raise ValueError(f"bounded {split} JSONL count mismatch")
        for ordinal, row in enumerate(rows):
            document_id = row.get("document_id")
            text = row.get("text")
            if (
                not isinstance(document_id, str)
                or not document_id
                or document_id in seen_ids
                or not isinstance(text, str)
                or not text.strip()
            ):
                raise ValueError(f"invalid bounded {split} record at {ordinal}")
            seen_ids.add(document_id)
            token_ids = list(tokenizer.encode(text, add_special_tokens=False))
            if len(token_ids) < WINDOW_TOKENS:
                excluded[split].append(
                    {
                        "document_id": document_id,
                        "token_count": len(token_ids),
                        "reason": "shorter_than_fixed_window",
                    }
                )
                continue
            if len(windows[split]) >= MAX_RUNTIME_WINDOWS_PER_SPLIT:
                deferred[split].append(
                    {
                        "document_id": document_id,
                        "token_count": len(token_ids),
                        "reason": "eligible_but_outside_fixed_window_budget",
                    }
                )
                continue
            window_ids = token_ids[:WINDOW_TOKENS]
            window_text = tokenizer.decode(window_ids)
            if list(tokenizer.encode(window_text, add_special_tokens=False)) != window_ids:
                raise ValueError(f"tokenizer round-trip changed bounded window: {document_id}")
            window_bytes = window_text.encode("utf-8")
            full_text_digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
            window = engine.CorpusWindow(
                dataset="bounded_webtextlike",
                document_id=document_id,
                relative_path=f"data/{split}.jsonl#{ordinal}",
                window_ordinal=0,
                text=window_text,
                byte_len=len(window_bytes),
                source_sha256=full_text_digest,
                text_sha256=hashlib.sha256(window_bytes).hexdigest(),
                token_count=WINDOW_TOKENS,
            )
            windows[split].append(window)
            entries[split].append(
                {
                    "dataset": window.dataset,
                    "document_id": document_id,
                    "source_path": path.relative_to(source_root).as_posix(),
                    "source_record_sha256": full_text_digest,
                    "window_text_sha256": window.text_sha256,
                    "window_ordinal": window.window_ordinal,
                    "token_count": window.token_count,
                }
            )
    if len(windows["fit"]) < 4 or len(windows["assessment"]) < 4:
        raise ValueError(
            "bounded panel has too few eligible 256-token windows: "
            f"fit={len(windows['fit'])}, assessment={len(windows['assessment'])}"
        )
    body = {
        "state_slice": STATE_SLICE,
        "schema": CORPUS_SCHEMA,
        "source_manifest_sha256": manifest["manifest_sha256"],
        "window_token_count": WINDOW_TOKENS,
        "selection_policy": "first-four-eligible-256-token-records-per-split-v1",
        "max_windows_per_split": MAX_RUNTIME_WINDOWS_PER_SPLIT,
        "fit": entries["fit"],
        "assessment": entries["assessment"],
        "fit_window_count": len(windows["fit"]),
        "assessment_window_count": len(windows["assessment"]),
        "excluded_short_records": excluded,
        "deferred_eligible_records": deferred,
    }
    return windows["fit"], windows["assessment"], {
        "manifest": body,
        "manifest_sha256": digest(body),
    }


def _pilot_configs(layer_count: int) -> tuple[engine.RecirculationConfig, ...]:
    configs = tuple(
        engine.RecirculationConfig(source, destination, FIT_ALPHA)
        for source, destination in PILOT_PAIRS
    )
    for config in configs:
        config.validate(layer_count)
    return configs


def _write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _run_validator(
    root: Path,
    model_path: Path,
    *,
    reported_root: Path | None = None,
) -> dict[str, Any]:
    completed = subprocess.run(
        [sys.executable, "-B", str(VALIDATOR), str(root), "--model", str(model_path)],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            "independent bounded recirculation validation failed: "
            f"stdout={completed.stdout}\nstderr={completed.stderr}"
        )
    value = json.loads(completed.stdout)
    if not isinstance(value, dict) or value.get("valid") is not True:
        raise RuntimeError(f"independent validator returned invalid result: {value}")
    if reported_root is not None:
        value["result_root"] = str(reported_root)
    return value


def run_campaign(
    source_root: Path = DEFAULT_SOURCE_ROOT,
    output_root: Path = DEFAULT_OUTPUT_ROOT,
    model_path: Path = DEFAULT_MODEL,
) -> dict[str, Any]:
    source_root = _primary(source_root, "bounded acquisition root")
    output_root = _primary(output_root, "bounded result root")
    model_path = _external(model_path, "cached model")
    if output_root.exists() or output_root.is_symlink():
        raise FileExistsError(f"refusing to overwrite bounded result root: {output_root}")
    if not model_path.is_dir():
        raise FileNotFoundError(f"cached Gemma3 model does not exist: {model_path}")

    source_manifest, source_validation = _verify_source_bundle(source_root)
    model_files_before = engine.model_manifest(model_path)
    model, tokenizer, tokenizer_policy = engine._load_runtime(model_path)
    layer_count = len(model.model.layers)
    if getattr(model.args, "model_type", None) != "gemma3_text":
        raise ValueError("loaded checkpoint is not the expected Gemma3 text model")
    if layer_count != 26:
        raise ValueError(f"expected Gemma3 1B PT to have 26 layers, found {layer_count}")
    fit, assessment, corpus = _runtime_windows(source_root, source_manifest, tokenizer)
    parity_checks = [
        engine.parity_check(model, tokenizer, window.text)
        for window in (*fit, *assessment)
    ]
    if not all(check["passed"] for check in parity_checks):
        raise RuntimeError("zero-alpha parity gate failed")

    fit_baseline = engine.evaluate_windows(model, tokenizer, fit, None, include_rows=True)
    fit_candidates = []
    for config in _pilot_configs(layer_count):
        fit_candidates.append(
            {
                "config": asdict(config),
                "metrics": engine.evaluate_windows(
                    model, tokenizer, fit, config, include_rows=True
                ),
            }
        )
    selected = min(
        fit_candidates,
        key=lambda item: (
            item["metrics"]["mean_nll"],
            item["config"]["source_layer"],
            item["config"]["destination_layer"],
        ),
    )
    selected_config = engine.RecirculationConfig(**selected["config"])
    locked_config = engine.RecirculationConfig(
        selected_config.source_layer,
        selected_config.destination_layer,
        EVALUATION_ALPHA,
    )
    assessment_baseline = engine.evaluate_windows(
        model, tokenizer, assessment, None, include_rows=True
    )
    assessment_selected = engine.evaluate_windows(
        model, tokenizer, assessment, locked_config, include_rows=True
    )
    assessment_temperature_baseline = engine.evaluate_windows(
        model,
        tokenizer,
        assessment,
        None,
        temperature=TEMPERATURE_CONTROL,
        include_rows=True,
    )
    assessment_temperature_selected = engine.evaluate_windows(
        model,
        tokenizer,
        assessment,
        locked_config,
        temperature=TEMPERATURE_CONTROL,
        include_rows=True,
    )
    assessment_repeat = engine.evaluate_windows(
        model, tokenizer, assessment, locked_config, include_rows=True
    )
    repeat_delta = max(
        abs(assessment_selected["mean_nll"] - assessment_repeat["mean_nll"]),
        abs(assessment_selected["perplexity"] - assessment_repeat["perplexity"]),
    )
    model_files_after = engine.model_manifest(model_path)
    if model_files_after != model_files_before:
        raise RuntimeError("cached model manifest changed during frozen inference")

    config = {
        "state_slice": STATE_SLICE,
        "claim_ceiling": CLAIM_CEILING,
        "source_schema": SOURCE_SCHEMA,
        "corpus_schema": CORPUS_SCHEMA,
        "source_root": str(source_root),
        "source_manifest_sha256": source_manifest["manifest_sha256"],
        "source_validation": source_validation,
        "model_name": model_path.name,
        "model_path": str(model_path),
        "architecture": "gemma3_text",
        "layer_count": layer_count,
        "protocol": "bounded-webtextlike-256-token-mechanics-v1",
        "mechanism_source": "arxiv:2608.17981",
        "paper_alignment": "mechanism_only_not_paper_replication",
        "window_token_count": WINDOW_TOKENS,
        "runtime_window_selection_policy": "first-four-eligible-256-token-records-per-split-v1",
        "max_windows_per_split": MAX_RUNTIME_WINDOWS_PER_SPLIT,
        "fit_window_count": len(fit),
        "assessment_window_count": len(assessment),
        "candidate_pairs": [list(pair) for pair in PILOT_PAIRS],
        "fit_alpha": FIT_ALPHA,
        "evaluation_alpha": EVALUATION_ALPHA,
        "evaluation_beta": EVALUATION_BETA,
        "temperature_control": TEMPERATURE_CONTROL,
        "normalization": "source_l2_norm_to_destination_l2_norm",
        "selected_fit_config": {
            "source_layer": selected_config.source_layer,
            "destination_layer": selected_config.destination_layer,
        },
        "paper_expected_pair": {"source_layer": 11, "destination_layer": 4},
        "network_access": False,
        "training": False,
        "weights_frozen": True,
        "evidence_ledger_mutation": False,
        "runtime": {
            "python": engine.package_version("pip"),
            "mlx": engine.package_version("mlx"),
            "mlx_lm": engine.package_version("mlx-lm"),
        },
        "tokenizer_policy": tokenizer_policy,
        "model_manifest_sha256": model_files_after["manifest_sha256"],
        "corpus_manifest_sha256": corpus["manifest_sha256"],
    }
    config["config_sha256"] = digest(config)
    results = {
        "state_slice": STATE_SLICE,
        "claim_ceiling": CLAIM_CEILING,
        "source_manifest_sha256": source_manifest["manifest_sha256"],
        "corpus_manifest_sha256": corpus["manifest_sha256"],
        "model_manifest_sha256": model_files_after["manifest_sha256"],
        "parity": {
            "sequence_count": len(parity_checks),
            "max_abs_logit_delta": max(
                check["max_abs_logit_delta"] for check in parity_checks
            ),
            "tolerance": engine.PARITY_TOLERANCE,
            "all_passed": all(check["passed"] for check in parity_checks),
            "checks": parity_checks,
        },
        "fit_baseline": fit_baseline,
        "fit_candidates": fit_candidates,
        "selected_fit_config": asdict(selected_config),
        "locked_evaluation_config": asdict(locked_config),
        "assessment_baseline": assessment_baseline,
        "assessment_selected": assessment_selected,
        "assessment_temperature_baseline": assessment_temperature_baseline,
        "assessment_temperature_selected": assessment_temperature_selected,
        "assessment_repeat": assessment_repeat,
        "assessment_repeat_max_metric_delta": round(repeat_delta, 12),
        "assessment_nll_delta_selected_minus_baseline": round(
            assessment_selected["mean_nll"] - assessment_baseline["mean_nll"], 9
        ),
        "assessment_perplexity_delta_selected_minus_baseline": round(
            assessment_selected["perplexity"] - assessment_baseline["perplexity"], 9
        ),
        "paper_expected_pair_recovered": (
            selected_config.source_layer == 11 and selected_config.destination_layer == 4
        ),
        "performance_result_is_local_bounded_mechanics_pilot_only": True,
    }
    results["results_sha256"] = digest(results)
    selected_delta = assessment_selected["mean_nll"] - assessment_baseline["mean_nll"]
    receipt = {
        "state_slice": STATE_SLICE,
        "claim_ceiling": CLAIM_CEILING,
        "config_sha256": config["config_sha256"],
        "results_sha256": results["results_sha256"],
        "source_manifest_sha256": source_manifest["manifest_sha256"],
        "corpus_manifest_sha256": corpus["manifest_sha256"],
        "model_manifest_sha256": model_files_after["manifest_sha256"],
        "zero_alpha_parity_passed": results["parity"]["all_passed"],
        "network_access": False,
        "training": False,
        "weights_frozen": True,
        "evidence_ledger_mutation": False,
        "deterministic_repeat_passed": repeat_delta <= engine.PARITY_TOLERANCE,
        "assessment_mean_nll_delta_selected_minus_baseline": round(selected_delta, 9),
        "performance_improved_on_assessment": selected_delta < 0,
    }
    receipt["receipt_sha256"] = digest(receipt)

    staging = Path(tempfile.mkdtemp(prefix=f".{output_root.name}.staging-", dir=output_root.parent))
    try:
        _write_json(staging / "config.json", config)
        _write_json(staging / "corpus-manifest.json", corpus)
        _write_json(staging / "results.json", results)
        _write_json(staging / "model-manifest.json", model_files_after)
        _write_json(staging / "receipt.json", receipt)
        validator_receipt = _run_validator(
            staging,
            model_path,
            reported_root=output_root,
        )
        _write_json(staging / "validator-receipt.json", validator_receipt)
        os.replace(staging, output_root)
    finally:
        if staging.exists():
            shutil.rmtree(staging)
    return {
        "state_slice": STATE_SLICE,
        "claim_ceiling": CLAIM_CEILING,
        "output_root": str(output_root),
        "receipt": receipt,
        "validator": validator_receipt,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, default=DEFAULT_SOURCE_ROOT)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--model", type=Path, default=DEFAULT_MODEL)
    args = parser.parse_args()
    print(
        json.dumps(
            run_campaign(args.source_root, args.output_root, args.model),
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
