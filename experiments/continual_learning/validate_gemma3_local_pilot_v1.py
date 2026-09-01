#!/usr/bin/env python3
"""Independently validate a Gemma3 local-pilot artifact.

State slice: continual-learning-gemma3-local-pilot-v1.

The validator rechecks custody, digest chains, tokenizer window shape, frozen
runtime metadata, parity observations, aggregate metrics, locked selection,
controls, and deterministic repeat. It does not trust runner summaries and
does not write into the artifact root.
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

STATE_SLICE = "continual-learning-gemma3-local-pilot-v1"
CLAIM_CEILING = "LocalDevelopmentGemma3NewsroomRecirculationMechanicsPilot"
CORPUS_SCHEMA = "gemma3-newsroom-recirculation-pilot-corpus-v1"
SOURCE_SCHEMA = "gemma3-newsroom-recirculation-pilot-input-v1"
WINDOW_TOKENS = 256
FIT_WINDOW_COUNT = 2
ASSESSMENT_WINDOW_COUNT = 2
SELECTED_DOCUMENT_COUNT = FIT_WINDOW_COUNT + ASSESSMENT_WINDOW_COUNT
FIT_ALPHA = 0.10
EVALUATION_ALPHA = 0.15
EVALUATION_BETA = 0.85
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


def _read_json(root: Path, name: str) -> dict[str, Any]:
    path = root / name
    if not path.is_file() or path.is_symlink():
        raise FileNotFoundError(f"missing regular artifact file: {path}")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"artifact JSON must be an object: {path}")
    return value


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


def _check_self_digest(value: dict[str, Any], field: str, label: str) -> None:
    declared = value.get(field)
    if not isinstance(declared, str):
        raise ValueError(f"{label} is missing {field}")
    body = dict(value)
    body.pop(field)
    if declared != digest(body):
        raise ValueError(f"{label} digest mismatch")


def _check_nested_manifest_digest(value: dict[str, Any], label: str) -> None:
    declared = value.get("manifest_sha256")
    body = value.get("manifest")
    if not isinstance(declared, str) or not isinstance(body, dict):
        raise ValueError(f"{label} is missing a manifest body or digest")
    if declared != digest(body):
        raise ValueError(f"{label} digest mismatch")


def _load_tokenizer(model_path: Path) -> Any:
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


def _recompute_selection(
    input_path: Path,
    tokenizer: Any,
    selection_offset: int,
) -> list[dict[str, Any]]:
    if selection_offset < 0:
        raise ValueError("selection offset must be non-negative")
    selected: list[dict[str, Any]] = []
    seen_urls: set[str] = set()
    eligible_count = 0
    import gzip

    opener = gzip.open if input_path.suffix == ".gz" else Path.open
    with opener(input_path, "rt", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                raise ValueError(f"blank NEWSROOM JSONL line: {line_number}")
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValueError(f"NEWSROOM record must be an object: line {line_number}")
            text = value.get("text")
            url = value.get("url")
            if not isinstance(text, str) or not text:
                raise ValueError(f"NEWSROOM record has invalid text: line {line_number}")
            if not isinstance(url, str) or not url:
                raise ValueError(f"NEWSROOM record has invalid url: line {line_number}")
            if url in seen_urls:
                raise ValueError(f"duplicate NEWSROOM url before selection: {url}")
            seen_urls.add(url)
            token_count = len(tokenizer.encode(text, add_special_tokens=False))
            if token_count < WINDOW_TOKENS:
                continue
            if eligible_count < selection_offset:
                eligible_count += 1
                continue
            eligible_count += 1
            selected.append(
                {
                    "line_number": line_number,
                    "document_id": f"newsroom-test-line-{line_number:07d}",
                    "url": url,
                    "text_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
                    "token_count": token_count,
                }
            )
            if len(selected) == SELECTED_DOCUMENT_COUNT:
                break
    if len(selected) != SELECTED_DOCUMENT_COUNT:
        raise ValueError("NEWSROOM input did not yield enough selected documents")
    return selected


def _validate_corpus(
    root: Path,
    corpus: dict[str, Any],
    tokenizer: Any,
    *,
    state_slice: str = STATE_SLICE,
    corpus_schema: str = CORPUS_SCHEMA,
    selection_policy: str = "first-four-eligible-newsroom-test-records-v1",
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    _check_nested_manifest_digest(corpus, "corpus manifest")
    body = corpus.get("manifest")
    if not isinstance(body, dict) or body.get("schema") != corpus_schema:
        raise ValueError("corpus schema mismatch")
    if body.get("state_slice") != state_slice:
        raise ValueError("corpus state slice mismatch")
    if body.get("window_token_count") != WINDOW_TOKENS:
        raise ValueError("corpus window token count mismatch")
    if body.get("selection_policy") != selection_policy:
        raise ValueError("corpus selection policy mismatch")
    fit = body.get("fit")
    assessment = body.get("assessment")
    if not isinstance(fit, list) or not isinstance(assessment, list):
        raise ValueError("corpus fit and assessment entries are required")
    if len(fit) != FIT_WINDOW_COUNT or len(assessment) != ASSESSMENT_WINDOW_COUNT:
        raise ValueError("pilot corpus window counts mismatch")
    seen_paths: set[str] = set()
    fit_docs: set[str] = set()
    assessment_docs: set[str] = set()
    for entries, split, documents in (
        (fit, "fit", fit_docs),
        (assessment, "assessment", assessment_docs),
    ):
        for entry in entries:
            if not isinstance(entry, dict):
                raise ValueError(f"{split} corpus entry must be an object")
            relative_path = entry.get("path")
            document_id = entry.get("document_id")
            if not isinstance(relative_path, str) or Path(relative_path).is_absolute():
                raise ValueError(f"invalid {split} corpus path")
            if relative_path in seen_paths:
                raise ValueError("corpus path is reused")
            seen_paths.add(relative_path)
            if not isinstance(document_id, str) or not document_id:
                raise ValueError(f"invalid {split} document id")
            documents.add(document_id)
            path = root / "corpus" / relative_path
            if not path.is_file() or path.is_symlink():
                raise ValueError(f"missing corpus window: {relative_path}")
            raw_bytes = path.read_bytes()
            if len(raw_bytes) != entry.get("byte_len"):
                raise ValueError(f"corpus byte length mismatch: {relative_path}")
            if sha256_file(path) != entry.get("source_sha256"):
                raise ValueError(f"corpus checksum mismatch: {relative_path}")
            if sha256_file(path) != entry.get("text_sha256"):
                raise ValueError(f"corpus text checksum mismatch: {relative_path}")
            text = raw_bytes.decode("utf-8")
            token_count = len(tokenizer.encode(text, add_special_tokens=False))
            if token_count != WINDOW_TOKENS or entry.get("token_count") != WINDOW_TOKENS:
                raise ValueError(f"corpus token count mismatch: {relative_path}")
    if fit_docs & assessment_docs:
        raise ValueError("fit and assessment reuse a document identity")
    return fit, assessment


def _validate_metrics(metrics: Any, label: str) -> None:
    if not isinstance(metrics, dict):
        raise ValueError(f"{label} metrics must be an object")
    rows = metrics.get("rows")
    if not isinstance(rows, list) or not rows:
        raise ValueError(f"{label} metrics need retained rows")
    target_tokens = 0
    total_nll = 0.0
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError(f"{label} metric row must be an object")
        target_count = row.get("target_count")
        nll = row.get("nll")
        if not isinstance(target_count, int) or target_count <= 0:
            raise ValueError(f"{label} metric row has invalid target count")
        if not isinstance(nll, (int, float)) or not math.isfinite(float(nll)):
            raise ValueError(f"{label} metric row has invalid nll")
        target_tokens += target_count
        total_nll += float(nll)
    mean_nll = metrics.get("mean_nll")
    perplexity = metrics.get("perplexity")
    if not isinstance(mean_nll, (int, float)) or not math.isfinite(float(mean_nll)):
        raise ValueError(f"{label} mean nll is invalid")
    if not isinstance(perplexity, (int, float)) or not math.isfinite(float(perplexity)):
        raise ValueError(f"{label} perplexity is invalid")
    if metrics.get("target_tokens") != target_tokens:
        raise ValueError(f"{label} target token total mismatch")
    expected_mean = total_nll / target_tokens
    if not math.isclose(float(mean_nll), round(expected_mean, 9), abs_tol=5e-8):
        raise ValueError(f"{label} mean nll is not recomputed from rows")
    if not math.isclose(float(perplexity), round(math.exp(float(mean_nll)), 9), abs_tol=5e-7):
        raise ValueError(f"{label} perplexity is not derived from mean nll")


def validate(
    root: Path,
    model_path: Path,
    *,
    state_slice: str = STATE_SLICE,
    claim_ceiling: str = CLAIM_CEILING,
    corpus_schema: str = CORPUS_SCHEMA,
    source_schema: str = SOURCE_SCHEMA,
    selection_offset: int = 0,
    selection_policy: str = "first-four-eligible-newsroom-test-records-v1",
) -> dict[str, Any]:
    root = root.resolve()
    model_path = model_path.resolve()
    config = _read_json(root, "config.json")
    results = _read_json(root, "results.json")
    receipt = _read_json(root, "receipt.json")
    input_manifest = _read_json(root, "input-manifest.json")
    corpus = _read_json(root / "corpus", "corpus-manifest.json")
    stored_model_manifest = _read_json(root, "model-manifest.json")
    for value, label in (
        (config, "config"),
        (results, "results"),
        (receipt, "receipt"),
    ):
        if value.get("state_slice") != state_slice:
            raise ValueError(f"{label} state slice mismatch")
        if value.get("claim_ceiling") != claim_ceiling:
            raise ValueError(f"{label} claim ceiling mismatch")
    _check_self_digest(config, "config_sha256", "config")
    _check_self_digest(results, "results_sha256", "results")
    _check_self_digest(receipt, "receipt_sha256", "receipt")
    _check_nested_manifest_digest(input_manifest, "input manifest")
    input_body = input_manifest.get("manifest")
    if (
        not isinstance(input_body, dict)
        or input_body.get("schema") != source_schema
        or input_body.get("state_slice") != state_slice
    ):
        raise ValueError("input manifest state slice mismatch")
    raw_relative_path = input_body.get("raw_path")
    if not isinstance(raw_relative_path, str) or Path(raw_relative_path).is_absolute():
        raise ValueError("raw NEWSROOM input path is invalid")
    raw_path = root / raw_relative_path
    if not raw_path.is_file() or raw_path.is_symlink():
        raise ValueError("raw NEWSROOM input is missing")
    if raw_path.stat().st_size != input_body.get("raw_byte_len"):
        raise ValueError("raw NEWSROOM input byte length mismatch")
    if sha256_file(raw_path) != input_body.get("raw_sha256"):
        raise ValueError("raw NEWSROOM input checksum mismatch")
    if input_body.get("window_token_count") != WINDOW_TOKENS:
        raise ValueError("input window token count mismatch")
    selected_documents = input_body.get("selected_documents")
    if not isinstance(selected_documents, list) or len(selected_documents) != 4:
        raise ValueError("selected NEWSROOM document count mismatch")
    manifest_offset = input_body.get("selection_offset", 0)
    manifest_policy = input_body.get(
        "selection_policy", "first-four-eligible-newsroom-test-records-v1"
    )
    if manifest_offset != selection_offset or manifest_policy != selection_policy:
        raise ValueError("NEWSROOM selection policy mismatch")
    tokenizer = _load_tokenizer(model_path)
    expected_documents = _recompute_selection(raw_path, tokenizer, selection_offset)
    if selected_documents != expected_documents:
        raise ValueError("NEWSROOM selected document manifest is not reproducible")
    fit_entries, assessment_entries = _validate_corpus(
        root,
        corpus,
        tokenizer,
        state_slice=state_slice,
        corpus_schema=corpus_schema,
        selection_policy=selection_policy,
    )
    recomputed_model_manifest = _model_manifest(model_path)
    if stored_model_manifest != recomputed_model_manifest:
        raise ValueError("cached model manifest changed or is incorrect")
    if config.get("model_manifest_sha256") != recomputed_model_manifest["manifest_sha256"]:
        raise ValueError("config model manifest digest mismatch")
    if config.get("input_manifest_sha256") != input_manifest["manifest_sha256"]:
        raise ValueError("config input manifest digest mismatch")
    if config.get("corpus_manifest_sha256") != corpus["manifest_sha256"]:
        raise ValueError("config corpus manifest digest mismatch")
    if results.get("model_manifest_sha256") != recomputed_model_manifest["manifest_sha256"]:
        raise ValueError("results model manifest digest mismatch")
    if results.get("input_manifest_sha256") != input_manifest["manifest_sha256"]:
        raise ValueError("results input manifest digest mismatch")
    if results.get("corpus_manifest_sha256") != corpus["manifest_sha256"]:
        raise ValueError("results corpus manifest digest mismatch")
    if config.get("architecture") != "gemma3_text" or config.get("layer_count") != 26:
        raise ValueError("Gemma3 architecture metadata mismatch")
    if config.get("window_token_count") != WINDOW_TOKENS:
        raise ValueError("config window token count mismatch")
    if config.get("fit_window_count") != FIT_WINDOW_COUNT:
        raise ValueError("config fit count mismatch")
    if config.get("assessment_window_count") != ASSESSMENT_WINDOW_COUNT:
        raise ValueError("config assessment count mismatch")
    if config.get("candidate_pairs") != [list(pair) for pair in PILOT_PAIRS]:
        raise ValueError("candidate pair grid mismatch")
    if config.get("fit_alpha") != FIT_ALPHA:
        raise ValueError("fit alpha mismatch")
    if config.get("evaluation_alpha") != EVALUATION_ALPHA:
        raise ValueError("evaluation alpha mismatch")
    if config.get("evaluation_beta") != EVALUATION_BETA:
        raise ValueError("evaluation beta mismatch")
    if config.get("selection_offset", 0) != selection_offset:
        raise ValueError("config selection offset mismatch")
    if config.get(
        "selection_policy", "first-four-eligible-newsroom-test-records-v1"
    ) != selection_policy:
        raise ValueError("config selection policy mismatch")
    if config.get("network_access") is not False or config.get("training") is not False:
        raise ValueError("pilot must be offline and inference-only")
    if config.get("weights_frozen") is not True:
        raise ValueError("pilot weights must be frozen")
    parity = results.get("parity")
    if not isinstance(parity, dict) or parity.get("all_passed") is not True:
        raise ValueError("zero-alpha parity did not pass")
    if parity.get("sequence_count") != SELECTED_DOCUMENT_COUNT:
        raise ValueError("parity sequence count mismatch")
    if float(parity.get("max_abs_logit_delta", math.inf)) > PARITY_TOLERANCE:
        raise ValueError("parity tolerance exceeded")
    for key in (
        "fit_baseline",
        "assessment_baseline",
        "assessment_selected",
        "assessment_temperature_baseline",
        "assessment_temperature_selected",
        "assessment_repeat",
    ):
        _validate_metrics(results.get(key), key)
    candidates = results.get("fit_candidates")
    if not isinstance(candidates, list) or len(candidates) != len(PILOT_PAIRS):
        raise ValueError("fit candidate count mismatch")
    for candidate in candidates:
        if not isinstance(candidate, dict) or candidate.get("config", {}).get("alpha") != FIT_ALPHA:
            raise ValueError("fit candidate configuration mismatch")
        _validate_metrics(candidate.get("metrics"), "fit candidate")
    selected = results.get("selected_fit_config")
    expected_selected = min(
        candidates,
        key=lambda item: (
            item["metrics"]["mean_nll"],
            item["config"]["source_layer"],
            item["config"]["destination_layer"],
        ),
    )["config"]
    if selected != expected_selected:
        raise ValueError("fit selection is not recomputed from candidates")
    locked = results.get("locked_evaluation_config")
    if not isinstance(locked, dict) or locked.get("alpha") != EVALUATION_ALPHA:
        raise ValueError("locked evaluation alpha mismatch")
    if locked.get("source_layer") != selected.get("source_layer") or locked.get("destination_layer") != selected.get("destination_layer"):
        raise ValueError("locked evaluation pair does not match fit selection")
    baseline = results["assessment_baseline"]
    selected_metrics = results["assessment_selected"]
    delta = round(selected_metrics["mean_nll"] - baseline["mean_nll"], 9)
    if results.get("assessment_nll_delta_selected_minus_baseline") != delta:
        raise ValueError("assessment NLL delta mismatch")
    ppl_delta = round(selected_metrics["perplexity"] - baseline["perplexity"], 9)
    if results.get("assessment_perplexity_delta_selected_minus_baseline") != ppl_delta:
        raise ValueError("assessment perplexity delta mismatch")
    if results.get("assessment_repeat_max_metric_delta", math.inf) > PARITY_TOLERANCE:
        raise ValueError("assessment repeat drift exceeded tolerance")
    if results.get("paper_expected_pair_recovered") is not (
        selected.get("source_layer") == 11 and selected.get("destination_layer") == 4
    ):
        raise ValueError("paper expected pair flag mismatch")
    if receipt.get("config_sha256") != config["config_sha256"]:
        raise ValueError("receipt config digest mismatch")
    if receipt.get("results_sha256") != results["results_sha256"]:
        raise ValueError("receipt results digest mismatch")
    if receipt.get("zero_alpha_parity_passed") is not True:
        raise ValueError("receipt parity flag mismatch")
    if receipt.get("deterministic_repeat_passed") is not True:
        raise ValueError("receipt deterministic-repeat flag mismatch")
    if receipt.get("performance_improved_on_assessment") != (delta < 0):
        raise ValueError("receipt assessment direction mismatch")
    return {
        "valid": True,
        "state_slice": state_slice,
        "claim_ceiling": claim_ceiling,
        "fit_window_count": len(fit_entries),
        "assessment_window_count": len(assessment_entries),
        "selected_fit_config": selected,
        "assessment_nll_delta_selected_minus_baseline": delta,
        "zero_alpha_parity_passed": True,
        "deterministic_repeat_passed": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact-root", type=Path, required=True)
    parser.add_argument("--model", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(validate(args.artifact_root, args.model), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
