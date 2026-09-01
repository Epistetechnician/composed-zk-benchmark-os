#!/usr/bin/env python3
"""Independently validate a bounded Gemma3 WebText-like result bundle.

State slice: continual-learning-gemma3-paper-recirculation-c4-bounded-v1.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

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
PARITY_TOLERANCE = 1e-5


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


def _check_self_digest(value: dict[str, Any], field: str, label: str) -> None:
    declared = value.get(field)
    body = dict(value)
    body.pop(field, None)
    if not isinstance(declared, str) or declared != digest(body):
        raise ValueError(f"{label} digest mismatch")


def _model_manifest(model_path: Path) -> dict[str, Any]:
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


def _check_artifact(path: Path, metadata: dict[str, Any], label: str) -> None:
    _regular(path, label)
    if path.stat().st_size != metadata.get("byte_len"):
        raise ValueError(f"{label} byte length mismatch")
    if sha256_file(path) != metadata.get("sha256"):
        raise ValueError(f"{label} checksum mismatch")


def _validate_source_binding(config: dict[str, Any]) -> None:
    source_root = _external(Path(str(config["source_root"])), "bounded acquisition root")
    manifest_path = _regular(source_root / "acquisition-manifest.json", "acquisition manifest")
    manifest = _read_json(manifest_path, "acquisition manifest")
    if manifest.get("schema") != SOURCE_SCHEMA:
        raise ValueError("source schema mismatch")
    if manifest.get("state_slice") != STATE_SLICE:
        raise ValueError("source state slice mismatch")
    if manifest.get("full_c4_webtextlike") is not False:
        raise ValueError("source must not claim full C4")
    if manifest.get("manifest_sha256") != config.get("source_manifest_sha256"):
        raise ValueError("source manifest binding mismatch")
    body = dict(manifest)
    declared = body.pop("manifest_sha256", None)
    if declared != digest(body):
        raise ValueError("source manifest digest mismatch")
    datasets = manifest.get("datasets")
    if not isinstance(datasets, dict) or set(datasets) != {"fit", "assessment"}:
        raise ValueError("source dataset panel mismatch")
    for split, metadata in datasets.items():
        if not isinstance(metadata, dict):
            raise ValueError(f"source metadata is invalid: {split}")
        path = source_root / str(metadata.get("relative_path"))
        _check_artifact(path, metadata, f"source {split} JSONL")
        rows = _read_jsonl(path, f"source {split} JSONL")
        if len(rows) != metadata.get("record_count"):
            raise ValueError(f"source {split} record count mismatch")
        if any(set(row) != {"document_id", "text"} for row in rows):
            raise ValueError(f"source {split} schema mismatch")


def _validate_corpus(corpus: dict[str, Any], config: dict[str, Any]) -> None:
    body = corpus.get("manifest")
    if not isinstance(body, dict) or corpus.get("manifest_sha256") != digest(body):
        raise ValueError("runtime corpus manifest digest mismatch")
    if body.get("schema") != CORPUS_SCHEMA or body.get("state_slice") != STATE_SLICE:
        raise ValueError("runtime corpus identity mismatch")
    if body.get("source_manifest_sha256") != config.get("source_manifest_sha256"):
        raise ValueError("runtime corpus source binding mismatch")
    if body.get("window_token_count") != WINDOW_TOKENS:
        raise ValueError("runtime corpus window size mismatch")
    if body.get("selection_policy") != "first-four-eligible-256-token-records-per-split-v1":
        raise ValueError("runtime corpus selection policy mismatch")
    if body.get("max_windows_per_split") != MAX_RUNTIME_WINDOWS_PER_SPLIT:
        raise ValueError("runtime corpus window budget mismatch")
    for split in ("fit", "assessment"):
        entries = body.get(split)
        if not isinstance(entries, list) or not entries:
            raise ValueError(f"runtime corpus {split} entries are missing")
        ids = [entry.get("document_id") for entry in entries if isinstance(entry, dict)]
        if len(ids) != len(set(ids)) or any(not isinstance(item, str) for item in ids):
            raise ValueError(f"runtime corpus {split} identities are invalid")
        for entry in entries:
            if (
                not isinstance(entry, dict)
                or entry.get("dataset") != "bounded_webtextlike"
                or entry.get("token_count") != WINDOW_TOKENS
                or not isinstance(entry.get("window_text_sha256"), str)
                or len(entry["window_text_sha256"]) != 64
            ):
                raise ValueError(f"runtime corpus {split} entry is invalid")
    excluded = body.get("excluded_short_records")
    if not isinstance(excluded, dict) or set(excluded) != {"fit", "assessment"}:
        raise ValueError("runtime corpus excluded-record contract is missing")
    excluded_ids: set[str] = set()
    for split in ("fit", "assessment"):
        if not isinstance(excluded[split], list):
            raise ValueError(f"runtime corpus excluded records are invalid: {split}")
        for entry in excluded[split]:
            if (
                not isinstance(entry, dict)
                or not isinstance(entry.get("document_id"), str)
                or entry.get("document_id") in excluded_ids
                or not isinstance(entry.get("token_count"), int)
                or entry.get("token_count") >= WINDOW_TOKENS
                or entry.get("reason") != "shorter_than_fixed_window"
            ):
                raise ValueError(f"runtime corpus excluded record is invalid: {split}")
            excluded_ids.add(entry["document_id"])
    deferred = body.get("deferred_eligible_records")
    if not isinstance(deferred, dict) or set(deferred) != {"fit", "assessment"}:
        raise ValueError("runtime corpus deferred-record contract is missing")
    for split in ("fit", "assessment"):
        if not isinstance(deferred[split], list):
            raise ValueError(f"runtime corpus deferred records are invalid: {split}")
        for entry in deferred[split]:
            if (
                not isinstance(entry, dict)
                or not isinstance(entry.get("document_id"), str)
                or entry.get("document_id") in excluded_ids
                or not isinstance(entry.get("token_count"), int)
                or entry.get("token_count") < WINDOW_TOKENS
                or entry.get("reason") != "eligible_but_outside_fixed_window_budget"
            ):
                raise ValueError(f"runtime corpus deferred record is invalid: {split}")
            excluded_ids.add(entry["document_id"])
    fit_ids = {entry["document_id"] for entry in body["fit"]}
    assessment_ids = {entry["document_id"] for entry in body["assessment"]}
    if fit_ids & assessment_ids or (fit_ids | assessment_ids) & excluded_ids:
        raise ValueError("runtime corpus reuses a document across splits")
    if body.get("fit_window_count") != len(body["fit"]):
        raise ValueError("runtime corpus fit count mismatch")
    if body.get("assessment_window_count") != len(body["assessment"]):
        raise ValueError("runtime corpus assessment count mismatch")


def _validate_metrics(metrics: Any, label: str, expected_rows: int) -> None:
    if not isinstance(metrics, dict):
        raise ValueError(f"{label} metrics are not an object")
    rows = metrics.get("rows")
    if not isinstance(rows, list) or len(rows) != expected_rows:
        raise ValueError(f"{label} row count mismatch")
    target_tokens = 0
    total_nll = 0.0
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError(f"{label} metric row is invalid")
        target_count = row.get("target_count")
        nll = row.get("nll")
        if not isinstance(target_count, int) or target_count <= 0:
            raise ValueError(f"{label} target count is invalid")
        if not isinstance(nll, (int, float)) or not math.isfinite(float(nll)):
            raise ValueError(f"{label} NLL is invalid")
        target_tokens += target_count
        total_nll += float(nll)
    mean_nll = metrics.get("mean_nll")
    perplexity = metrics.get("perplexity")
    if (
        not isinstance(mean_nll, (int, float))
        or not math.isfinite(float(mean_nll))
        or not isinstance(perplexity, (int, float))
        or not math.isfinite(float(perplexity))
    ):
        raise ValueError(f"{label} summary metrics are invalid")
    if metrics.get("target_tokens") != target_tokens:
        raise ValueError(f"{label} target token total mismatch")
    if not math.isclose(float(mean_nll), round(total_nll / target_tokens, 9), abs_tol=5e-8):
        raise ValueError(f"{label} mean NLL is not row-derived")
    if not math.isclose(float(perplexity), round(math.exp(float(mean_nll)), 9), abs_tol=5e-7):
        raise ValueError(f"{label} perplexity is not mean-NLL-derived")


def validate(root: Path, model_path: Path) -> dict[str, Any]:
    root = _external(root, "bounded result root")
    model_path = _external(model_path, "cached model")
    if not root.is_dir():
        raise FileNotFoundError(f"bounded result root does not exist: {root}")
    if any(path.is_symlink() for path in root.rglob("*")):
        raise ValueError("bounded result root contains a symlink")
    config = _read_json(root / "config.json", "config")
    corpus = _read_json(root / "corpus-manifest.json", "runtime corpus manifest")
    results = _read_json(root / "results.json", "results")
    receipt = _read_json(root / "receipt.json", "receipt")
    stored_model = _read_json(root / "model-manifest.json", "model manifest")
    for value, label in ((config, "config"), (results, "results"), (receipt, "receipt")):
        if value.get("state_slice") != STATE_SLICE:
            raise ValueError(f"{label} state slice mismatch")
        if value.get("claim_ceiling") != CLAIM_CEILING:
            raise ValueError(f"{label} claim ceiling mismatch")
    _check_self_digest(config, "config_sha256", "config")
    _check_self_digest(results, "results_sha256", "results")
    _check_self_digest(receipt, "receipt_sha256", "receipt")
    for field, expected in {
        "source_schema": SOURCE_SCHEMA,
        "corpus_schema": CORPUS_SCHEMA,
        "window_token_count": WINDOW_TOKENS,
        "fit_alpha": FIT_ALPHA,
        "evaluation_alpha": EVALUATION_ALPHA,
        "evaluation_beta": EVALUATION_BETA,
        "temperature_control": TEMPERATURE_CONTROL,
        "runtime_window_selection_policy": "first-four-eligible-256-token-records-per-split-v1",
        "max_windows_per_split": MAX_RUNTIME_WINDOWS_PER_SPLIT,
        "network_access": False,
        "training": False,
        "weights_frozen": True,
        "evidence_ledger_mutation": False,
    }.items():
        if config.get(field) != expected:
            raise ValueError(f"config field mismatch: {field}")
    if config.get("candidate_pairs") != [list(pair) for pair in PILOT_PAIRS]:
        raise ValueError("candidate pair panel mismatch")
    _validate_source_binding(config)
    _validate_corpus(corpus, config)
    recomputed_model = _model_manifest(model_path)
    if stored_model != recomputed_model:
        raise ValueError("cached model manifest changed or is incorrect")
    if config.get("model_manifest_sha256") != recomputed_model["manifest_sha256"]:
        raise ValueError("config model binding mismatch")
    if results.get("model_manifest_sha256") != recomputed_model["manifest_sha256"]:
        raise ValueError("results model binding mismatch")
    if receipt.get("model_manifest_sha256") != recomputed_model["manifest_sha256"]:
        raise ValueError("receipt model binding mismatch")
    corpus_digest = corpus["manifest_sha256"]
    if config.get("corpus_manifest_sha256") != corpus_digest:
        raise ValueError("config corpus binding mismatch")
    if results.get("corpus_manifest_sha256") != corpus_digest:
        raise ValueError("results corpus binding mismatch")
    if receipt.get("corpus_manifest_sha256") != corpus_digest:
        raise ValueError("receipt corpus binding mismatch")
    fit_count = config["fit_window_count"]
    assessment_count = config["assessment_window_count"]
    _validate_metrics(results.get("fit_baseline"), "fit baseline", fit_count)
    candidates = results.get("fit_candidates")
    if not isinstance(candidates, list) or len(candidates) != len(PILOT_PAIRS):
        raise ValueError("fit candidate count mismatch")
    for candidate in candidates:
        if not isinstance(candidate, dict) or candidate.get("config") not in [
            {"source_layer": pair[0], "destination_layer": pair[1], "alpha": FIT_ALPHA, "epsilon": 1e-6}
            for pair in PILOT_PAIRS
        ]:
            raise ValueError("fit candidate configuration mismatch")
        _validate_metrics(candidate.get("metrics"), "fit candidate", fit_count)
    selected = results.get("selected_fit_config")
    if not isinstance(selected, dict):
        raise ValueError("selected fit configuration is not an object")
    selected_pair = (selected.get("source_layer"), selected.get("destination_layer"))
    if selected_pair not in PILOT_PAIRS:
        raise ValueError("selected fit configuration is not a pilot pair")
    locked = results.get("locked_evaluation_config")
    if locked != {
        "source_layer": selected["source_layer"],
        "destination_layer": selected["destination_layer"],
        "alpha": EVALUATION_ALPHA,
        "epsilon": 1e-6,
    }:
        raise ValueError("locked evaluation configuration mismatch")
    for field in (
        "assessment_baseline",
        "assessment_selected",
        "assessment_temperature_baseline",
        "assessment_temperature_selected",
        "assessment_repeat",
    ):
        _validate_metrics(results.get(field), field, assessment_count)
    if results.get("parity", {}).get("sequence_count") != fit_count + assessment_count:
        raise ValueError("parity sequence count mismatch")
    if results.get("parity", {}).get("all_passed") is not True:
        raise ValueError("parity gate did not pass")
    if results.get("assessment_repeat_max_metric_delta", math.inf) > PARITY_TOLERANCE:
        raise ValueError("deterministic repeat gate did not pass")
    if receipt.get("zero_alpha_parity_passed") is not True:
        raise ValueError("receipt parity gate mismatch")
    if receipt.get("deterministic_repeat_passed") is not True:
        raise ValueError("receipt repeat gate mismatch")
    return {
        "valid": True,
        "state_slice": STATE_SLICE,
        "claim_ceiling": CLAIM_CEILING,
        "result_root": str(root),
        "fit_windows": fit_count,
        "assessment_windows": assessment_count,
        "selected_fit_config": selected,
        "assessment_nll_delta_selected_minus_baseline": results[
            "assessment_nll_delta_selected_minus_baseline"
        ],
        "assessment_perplexity_delta_selected_minus_baseline": results[
            "assessment_perplexity_delta_selected_minus_baseline"
        ],
        "paper_expected_pair_recovered": results["paper_expected_pair_recovered"],
        "source_manifest_sha256": config["source_manifest_sha256"],
        "corpus_manifest_sha256": corpus_digest,
        "model_manifest_sha256": recomputed_model["manifest_sha256"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    parser.add_argument("--model", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(validate(args.root, args.model), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
