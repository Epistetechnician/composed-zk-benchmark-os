#!/usr/bin/env python3
"""Independent validator for the Gemma3 Phase 815 artifact."""

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

STATE_SLICE = "continual-learning-gemma3-paper-recirculation-v1"
CLAIM_CEILING = "LocalDevelopmentGemma3PaperAlignedRecirculationReplication"
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
PARITY_TOLERANCE = 1e-5


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


def _read(root: Path, name: str) -> dict[str, Any]:
    path = root / name
    if not path.is_file() or path.is_symlink():
        raise ValueError(f"missing artifact: {name}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON: {name}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"artifact must be an object: {name}")
    return value


def _require_digest(value: dict[str, Any], field: str, label: str) -> None:
    actual = value.get(field)
    if not isinstance(actual, str):
        raise ValueError(f"missing {label} digest")
    body = {key: item for key, item in value.items() if key != field}
    if digest(body) != actual:
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
        raise ValueError("model directory has no stable files")
    body = {"model_name": model_path.name, "files": files}
    return {"manifest": body, "manifest_sha256": digest(body)}


def _safe_source(root: Path, relative_path: str) -> Path:
    if not isinstance(relative_path, str) or not relative_path:
        raise ValueError("corpus path must be non-empty")
    raw_path = root / relative_path
    if Path(relative_path).is_absolute() or raw_path.is_symlink():
        raise ValueError(f"unsafe corpus path: {relative_path}")
    candidate = raw_path.resolve()
    resolved_root = root.resolve()
    if (
        candidate == resolved_root
        or resolved_root not in candidate.parents
        or not candidate.is_file()
    ):
        raise ValueError(f"invalid corpus path: {relative_path}")
    return candidate


def _tokenizer(model_path: Path) -> Any:
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
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


def _corpus_manifest(corpus_root: Path, tokenizer: Any) -> dict[str, Any]:
    root = corpus_root.resolve()
    path = root / "manifest.json"
    if not root.is_dir() or not path.is_file() or path.is_symlink():
        raise ValueError("external corpus root is missing manifest.json")
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict) or raw.get("schema") != CORPUS_SCHEMA:
        raise ValueError("external corpus schema mismatch")
    if raw.get("window_token_count") != WINDOW_TOKENS:
        raise ValueError("external corpus window size mismatch")
    fit = raw.get("fit")
    assessment = raw.get("assessment")
    if not isinstance(fit, list) or not isinstance(assessment, list):
        raise ValueError("external corpus split lists are missing")
    seen_paths: set[str] = set()
    seen_fit_docs: list[tuple[str, str]] = []
    seen_assessment_docs: list[tuple[str, str]] = []

    def parse(entries: list[Any], split: str) -> list[dict[str, Any]]:
        parsed = []
        for raw_entry in entries:
            if not isinstance(raw_entry, dict):
                raise ValueError(f"{split} corpus entry must be an object")
            dataset = raw_entry.get("dataset")
            document_id = raw_entry.get("document_id")
            relative_path = raw_entry.get("path")
            ordinal = raw_entry.get("window_ordinal")
            if (
                not isinstance(dataset, str)
                or not dataset
                or not isinstance(document_id, str)
                or not document_id
                or not isinstance(ordinal, int)
                or ordinal < 0
            ):
                raise ValueError(f"invalid {split} corpus identity")
            if relative_path in seen_paths:
                raise ValueError("external corpus reuses a source path")
            seen_paths.add(relative_path)
            source = _safe_source(root, relative_path)
            raw_bytes = source.read_bytes()
            text = raw_bytes.decode("utf-8")
            token_count = len(tokenizer.encode(text, add_special_tokens=False))
            full_window = token_count == WINDOW_TOKENS
            partial_allowed = split == "assessment" and dataset in PARTIAL_ASSESSMENT_DATASETS
            if not full_window and not (partial_allowed and 1 < token_count < WINDOW_TOKENS):
                raise ValueError(f"invalid token window: {relative_path}")
            if raw_entry.get("token_count") not in (None, token_count):
                raise ValueError(f"declared token count mismatch: {relative_path}")
            parsed.append(
                {
                    "dataset": dataset,
                    "document_id": document_id,
                    "path": Path(relative_path).as_posix(),
                    "window_ordinal": ordinal,
                    "byte_len": len(raw_bytes),
                    "source_sha256": sha256_bytes(raw_bytes),
                    "text_sha256": sha256_bytes(text.encode("utf-8")),
                    "token_count": token_count,
                }
            )
            (seen_fit_docs if split == "fit" else seen_assessment_docs).append(
                (dataset, document_id)
            )
        return parsed

    fit_entries = parse(fit, "fit")
    assessment_entries = parse(assessment, "assessment")
    if set(seen_fit_docs) & set(seen_assessment_docs):
        raise ValueError("fit and assessment reuse a document identity")
    if any(seen_fit_docs.count(key) > 2 for key in set(seen_fit_docs)):
        raise ValueError("fit uses more than two windows from a document")
    if {entry["dataset"] for entry in fit_entries} != set(FIT_DATASETS):
        raise ValueError("fit dataset panel mismatch")
    if {entry["dataset"] for entry in assessment_entries} != set(ASSESSMENT_DATASETS):
        raise ValueError("assessment dataset panel mismatch")
    body = {
        "state_slice": STATE_SLICE,
        "schema": CORPUS_SCHEMA,
        "window_token_count": WINDOW_TOKENS,
        "source_manifest_sha256": sha256_file(path),
        "fit": fit_entries,
        "assessment": assessment_entries,
        "fit_window_count": len(fit_entries),
        "assessment_window_count": len(assessment_entries),
    }
    return {"manifest": body, "manifest_sha256": digest(body)}


def _validate_metric_rows(
    metrics: dict[str, Any],
    expected_dataset: str,
    expected_hashes: set[str],
) -> None:
    rows = metrics.get("rows")
    if not isinstance(rows, list) or not rows:
        raise ValueError(f"missing retained metric rows for {expected_dataset}")
    total_nll = 0.0
    total_targets = 0
    for row in rows:
        if row.get("dataset") != expected_dataset:
            raise ValueError("metric dataset mismatch")
        if row.get("text_sha256") not in expected_hashes:
            raise ValueError("metric text binding mismatch")
        nll = row.get("nll")
        target_count = row.get("target_count")
        if not isinstance(nll, (int, float)) or not math.isfinite(float(nll)):
            raise ValueError("metric row has invalid nll")
        if not isinstance(target_count, int) or target_count < 1:
            raise ValueError("metric row has invalid target count")
        total_nll += float(nll)
        total_targets += target_count
    if metrics.get("target_tokens") != total_targets:
        raise ValueError("metric target-token total mismatch")
    recomputed = round(total_nll / total_targets, 9)
    if not math.isclose(float(metrics.get("mean_nll")), recomputed, abs_tol=1e-8):
        raise ValueError("metric mean NLL is not recomputed from rows")
    if not math.isclose(
        float(metrics.get("perplexity")), round(math.exp(recomputed), 9), abs_tol=1e-8
    ):
        raise ValueError("metric perplexity is not bound to mean NLL")


def _weighted_mean(metrics: dict[str, dict[str, Any]]) -> float:
    total_nll = sum(
        value["mean_nll"] * value["target_tokens"] for value in metrics.values()
    )
    total_targets = sum(value["target_tokens"] for value in metrics.values())
    return total_nll / total_targets


def validate(root: Path, corpus_root: Path, model_path: Path) -> dict[str, Any]:
    root = root.resolve()
    corpus_root = corpus_root.resolve()
    model_path = model_path.resolve()
    if root == REPO_ROOT or REPO_ROOT in root.parents:
        raise ValueError("artifact root must be outside the repository")
    config = _read(root, "config.json")
    corpus = _read(root, "corpus-manifest.json")
    results = _read(root, "results.json")
    manifest = _read(root, "model-manifest.json")
    receipt = _read(root, "receipt.json")
    _require_digest(config, "config_sha256", "config")
    _require_digest(results, "results_sha256", "results")
    _require_digest(receipt, "receipt_sha256", "receipt")
    tokenizer = _tokenizer(model_path)
    expected_corpus = _corpus_manifest(corpus_root, tokenizer)
    if corpus != expected_corpus:
        raise ValueError("corpus manifest does not match external source bytes")
    expected_model = _model_manifest(model_path)
    if manifest != expected_model:
        raise ValueError("model manifest does not match stable model files")
    for value in (config, results, receipt):
        if value.get("state_slice") != STATE_SLICE:
            raise ValueError("state slice mismatch")
        if value.get("claim_ceiling") != CLAIM_CEILING:
            raise ValueError("claim ceiling mismatch")
    if config.get("architecture") != "gemma3_text" or config.get("layer_count") != 26:
        raise ValueError("Gemma3 architecture binding mismatch")
    if config.get("network_access") is not False or config.get("training") is not False:
        raise ValueError("forbidden activity in config")
    if receipt.get("network_access") is not False or receipt.get("training") is not False:
        raise ValueError("forbidden activity in receipt")
    if config.get("weights_frozen") is not True or receipt.get("weights_frozen") is not True:
        raise ValueError("weights are not frozen")
    if config.get("alpha_grid") != list(ALPHAS):
        raise ValueError("alpha grid mismatch")
    if config.get("pair_selection_alpha") != PAIR_SELECTION_ALPHA:
        raise ValueError("pair-selection alpha mismatch")
    if config.get("evaluation_alpha") != EVALUATION_ALPHA or config.get("evaluation_beta") != EVALUATION_BETA:
        raise ValueError("evaluation coefficients mismatch")
    pairs = [
        {
            "source_layer": source,
            "destination_layer": destination,
            "alpha": PAIR_SELECTION_ALPHA,
            "epsilon": 1e-6,
        }
        for source in range(26)
        for destination in range(source)
        if source - destination <= MAX_LAYER_DISTANCE
    ]
    if config.get("pair_candidate_count") != len(pairs):
        raise ValueError("pair candidate count mismatch")
    if config.get("alpha_sweep_candidate_count") != len(pairs) * len(ALPHAS):
        raise ValueError("alpha sweep count mismatch")
    if config.get("corpus_manifest_sha256") != corpus["manifest_sha256"]:
        raise ValueError("config corpus binding mismatch")
    if results.get("corpus_manifest_sha256") != corpus["manifest_sha256"]:
        raise ValueError("results corpus binding mismatch")
    if receipt.get("corpus_manifest_sha256") != corpus["manifest_sha256"]:
        raise ValueError("receipt corpus binding mismatch")
    if config.get("model_manifest_sha256") != manifest["manifest_sha256"]:
        raise ValueError("config model binding mismatch")
    if receipt.get("model_manifest_sha256") != manifest["manifest_sha256"]:
        raise ValueError("receipt model binding mismatch")
    if receipt.get("config_sha256") != config["config_sha256"]:
        raise ValueError("receipt config binding mismatch")
    if receipt.get("results_sha256") != results["results_sha256"]:
        raise ValueError("receipt results binding mismatch")
    if config.get("fit_window_count") != corpus["manifest"]["fit_window_count"]:
        raise ValueError("fit window count mismatch")
    if config.get("assessment_window_count") != corpus["manifest"]["assessment_window_count"]:
        raise ValueError("assessment window count mismatch")
    parity = results.get("parity")
    if not isinstance(parity, dict) or parity.get("all_passed") is not True:
        raise ValueError("zero-alpha parity gate did not pass")
    expected_count = config["fit_window_count"] + config["assessment_window_count"]
    if parity.get("sequence_count") != expected_count:
        raise ValueError("parity sequence count mismatch")
    if float(parity.get("max_abs_logit_delta", float("inf"))) > PARITY_TOLERANCE:
        raise ValueError("zero-alpha parity exceeds tolerance")
    if receipt.get("zero_alpha_parity_passed") is not True:
        raise ValueError("receipt parity binding mismatch")
    if receipt.get("deterministic_repeat_passed") is not True:
        raise ValueError("assessment repeat is not deterministic")
    assessment_manifest = {
        (row["dataset"], row["text_sha256"])
        for row in corpus["manifest"]["assessment"]
    }
    selected = results.get("assessment_selected_by_dataset")
    baseline = results.get("assessment_baseline_by_dataset")
    repeat = results.get("assessment_repeat_by_dataset")
    if not isinstance(selected, dict) or not isinstance(baseline, dict) or not isinstance(repeat, dict):
        raise ValueError("assessment metrics are missing")
    if set(selected) != set(ASSESSMENT_DATASETS) or set(baseline) != set(ASSESSMENT_DATASETS):
        raise ValueError("assessment dataset metrics mismatch")
    for dataset in ASSESSMENT_DATASETS:
        hashes = {text_hash for current_dataset, text_hash in assessment_manifest if current_dataset == dataset}
        _validate_metric_rows(baseline[dataset], dataset, hashes)
        _validate_metric_rows(selected[dataset], dataset, hashes)
        for key in ("mean_nll", "perplexity", "target_tokens"):
            if selected[dataset].get(key) != repeat[dataset].get(key):
                raise ValueError("assessment repeat drift")
    delta = _weighted_mean(selected) - _weighted_mean(baseline)
    if receipt.get("assessment_mean_nll_delta_selected_minus_baseline") != round(delta, 9):
        raise ValueError("assessment delta is not recomputed")
    if receipt.get("performance_improved_on_assessment") != (delta < 0):
        raise ValueError("assessment direction mismatch")
    return {
        "valid": True,
        "state_slice": STATE_SLICE,
        "claim_ceiling": CLAIM_CEILING,
        "fit_window_count": config["fit_window_count"],
        "assessment_window_count": config["assessment_window_count"],
        "zero_alpha_parity_passed": True,
        "deterministic_repeat_passed": True,
        "paper_expected_pair_recovered": bool(
            results.get("paper_expected_pair_recovered")
        ),
        "performance_improved_on_assessment": bool(
            receipt.get("performance_improved_on_assessment")
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--corpus-root", type=Path, required=True)
    parser.add_argument("--model", type=Path, required=True)
    args = parser.parse_args()
    print(
        json.dumps(
            validate(args.root, args.corpus_root, args.model),
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
