#!/usr/bin/env python3
"""Fail-closed V5 source, corpus, and result validator.

State slice: continual-learning-gemma3-fineweb-edu-replication-v5.
Result validation independently reruns every reviewed model control after all
structural custody checks and compares retained per-document rows exactly.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator

from experiments.continual_learning import gemma3_fineweb_edu_replication_v5_contract as c


@dataclass(frozen=True)
class CorpusWindow:
    dataset: str
    document_id: str
    relative_path: str
    window_ordinal: int
    text: str
    byte_len: int
    source_sha256: str
    text_sha256: str
    token_count: int
    token_ids: tuple[int, ...]


def _json(path: Path, label: str) -> dict[str, Any]:
    value = json.loads(c.regular(path, label).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be an object")
    return value


def _jsonl(path: Path, label: str) -> list[dict[str, Any]]:
    rows = []
    with c.regular(path, label).open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                raise ValueError(f"{label} has blank line {line_number}")
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValueError(f"{label} line {line_number} is not an object")
            rows.append(value)
    return rows


def _check_self_digest(value: dict[str, Any], field: str, label: str) -> None:
    stored = value.get(field)
    if not isinstance(stored, str) or c.digest({key: item for key, item in value.items() if key != field}) != stored:
        raise ValueError(f"{label} {field} mismatch")


def _expected_dataset() -> dict[str, Any]:
    return {"repo": c.DATASET_REPO, "source": c.DATASET_SOURCE, "revision": c.DATASET_REVISION, "config": c.DATASET_CONFIG, "split": c.DATASET_SPLIT, "selected_file_count": 2, "selected_crawls": [item["crawl"] for item in c.DATASET_FILES], "parquet_byte_count": c.DATASET_BYTE_COUNT}


def _normalized_from_values(values: dict[str, list[Any]], item: dict[str, Any], source_row_index: int, value_index: int) -> dict[str, Any]:
    text = values["text"][value_index]
    if not isinstance(text, str) or not text.strip():
        raise ValueError(f"empty FineWeb-Edu text at {item['path']} row {source_row_index}")
    upstream_id = values.get("id", [None] * len(values["text"]))[value_index]
    if not isinstance(upstream_id, str) or not upstream_id:
        upstream_id = f"row-{source_row_index:08d}"
    fields = ("id", "url", "date", "dump", "file_path", "language", "language_score", "token_count", "score", "int_score")
    metadata = {field: values[field][value_index] for field in fields if field in values and values[field][value_index] is not None}
    normalized_metadata = {field: value.isoformat() if hasattr(value, "isoformat") else value if isinstance(value, (str, int, float, bool)) else str(value) for field, value in metadata.items()}
    return {"document_id": f"fineweb-edu:{item['crawl']}:{upstream_id}", "text": text, "metadata": normalized_metadata, "source_crawl": item["crawl"], "source_path": item["path"], "source_row_index": source_row_index}


def _parquet_rows(path: Path, item: dict[str, Any], start: int, end: int) -> Iterator[dict[str, Any]]:
    import pyarrow.parquet as pq

    parquet = pq.ParquetFile(path)
    if "text" not in parquet.schema.names:
        raise ValueError(f"FineWeb-Edu shard has no text column: {path}")
    fields = ("id", "url", "date", "dump", "file_path", "language", "language_score", "token_count", "score", "int_score")
    columns = ["text", *[field for field in fields if field in parquet.schema.names]]
    global_index = 0
    selected = 0
    for batch in parquet.iter_batches(columns=columns, batch_size=256):
        values = {name: batch.column(name).to_pylist() for name in columns}
        for offset in range(batch.num_rows):
            if start <= global_index < end:
                yield _normalized_from_values(values, item, global_index, offset)
                selected += 1
            global_index += 1
            if global_index >= end:
                break
        if global_index >= end:
            break
    if selected != end - start:
        raise ValueError(f"selected {selected} rows from {path}; expected {end - start}")


def _audit_raw(raw_root: Path) -> list[dict[str, Any]]:
    root = c.exact_path(raw_root, c.RAW_ROOT, "V5 raw root")
    expected = {f"dataset/{item['path']}" for item in c.DATASET_FILES}
    c.exact_file_set(root, expected, "V5 raw root", allow_cache=True)
    artifacts = []
    for item in c.DATASET_FILES:
        path = c.regular(root / "dataset" / item["path"], "V5 pinned Parquet shard")
        if path.stat().st_size != item["byte_len"] or c.sha256_file(path) != item["sha256"]:
            raise ValueError(f"V5 raw pin mismatch: {path}")
        import pyarrow.parquet as pq
        row_count = pq.ParquetFile(path).metadata.num_rows
        if row_count < c.FRESH_ROW_END:
            raise ValueError(f"V5 raw shard is shorter than the locked row range: {path}")
        artifacts.append({"relative_path": path.relative_to(root).as_posix(), "source": f"{c.DATASET_SOURCE}/resolve/{c.DATASET_REVISION}/{item['path']}", "crawl": item["crawl"], "byte_len": path.stat().st_size, "sha256": c.sha256_file(path), "lfs_sha256": item["sha256"], "row_count": row_count})
    return artifacts


def _audit_prior(prior_root: Path, raw_root: Path) -> set[str]:
    root = c.exact_path(prior_root, c.R1_SOURCE_ROOT, "V5 prior-pilot source root")
    c.exact_file_set(root, {"acquisition-manifest.json", "fit/fineweb_edu.jsonl", "assessment/fineweb_edu.jsonl"}, "V5 prior-pilot source root")
    manifest_path = c.regular(root / "acquisition-manifest.json", "prior-pilot source manifest")
    if c.sha256_file(manifest_path) != c.R1_SOURCE_MANIFEST_SHA256:
        raise ValueError("prior-pilot manifest digest mismatch")
    manifest = _json(manifest_path, "prior-pilot source manifest")
    if manifest.get("schema") != "gemma3-fineweb-edu-bounded-acquisition-v1" or manifest.get("dataset") != _expected_dataset() or manifest.get("selection_policy") != "first-2048-records-from-two-pinned-crawls-document-disjoint-v1":
        raise ValueError("prior-pilot source contract mismatch")
    _check_self_digest(manifest, "manifest_sha256", "prior-pilot source manifest")
    datasets = manifest.get("datasets")
    if not isinstance(datasets, dict):
        raise ValueError("prior-pilot dataset entries are missing")
    raw = c.exact_path(raw_root, c.RAW_ROOT, "V5 raw root")
    ids: set[str] = set()
    for split, item in (("fit", c.DATASET_FILES[0]), ("assessment", c.DATASET_FILES[1])):
        metadata = datasets.get(f"{split}/fineweb_edu")
        expected_path = f"{split}/fineweb_edu.jsonl"
        expected = {"row_start": 0, "row_count": 2_048, "normalized_path": expected_path, "crawl": item["crawl"], "source_path": item["path"], "source": c.DATASET_SOURCE, "revision": c.DATASET_REVISION, "config": c.DATASET_CONFIG, "split": c.DATASET_SPLIT}
        if not isinstance(metadata, dict) or any(metadata.get(key) != value for key, value in expected.items()):
            raise ValueError(f"prior-pilot {split} metadata mismatch")
        path = c.safe_relative(root, expected_path, f"prior-pilot {split} JSONL")
        if c.sha256_file(path) != metadata.get("normalized_sha256"):
            raise ValueError(f"prior-pilot {split} normalized digest mismatch")
        rows = _jsonl(path, f"prior-pilot {split} JSONL")
        if len(rows) != 2_048:
            raise ValueError(f"prior-pilot {split} count mismatch")
        for ordinal, (observed, expected_row) in enumerate(zip(rows, _parquet_rows(raw / "dataset" / item["path"], item, 0, 2_048), strict=True)):
            if observed != expected_row:
                raise ValueError(f"prior-pilot {split} content mismatch at {ordinal}")
            document_id = observed.get("document_id")
            if not isinstance(document_id, str) or not document_id or document_id in ids or observed.get("source_row_index") != ordinal or observed.get("source_crawl") != item["crawl"] or observed.get("source_path") != item["path"]:
                raise ValueError(f"prior-pilot {split} identity mismatch at {ordinal}")
            ids.add(document_id)
    return ids


def _audit_source(source_root: Path, raw_root: Path, prior_root: Path, review_sha: str) -> dict[str, Any]:
    root = c.exact_or_staging_path(source_root, c.SOURCE_ROOT, "V5 source root")
    c.exact_file_set(root, {"acquisition-manifest.json", "fit/fineweb_edu.jsonl", "assessment/fineweb_edu.jsonl"}, "V5 source root")
    raw = c.exact_path(raw_root, c.RAW_ROOT, "V5 raw root")
    prior = c.exact_path(prior_root, c.R1_SOURCE_ROOT, "V5 prior-pilot source root")
    manifest = _json(root / "acquisition-manifest.json", "V5 source manifest")
    required = (("schema", c.SOURCE_SCHEMA), ("state_slice", c.STATE_SLICE), ("claim_ceiling", c.CLAIM_CEILING), ("source_record_schema", "gemma3-source-v1-compatible-with-fineweb-metadata"), ("selection_policy", "rows-2048-through-18431-two-pinned-crawls-v5"), ("raw_root", str(c.RAW_ROOT)), ("prior_pilot_source_root", str(c.R1_SOURCE_ROOT)), ("prior_pilot_manifest_sha256", c.R1_SOURCE_MANIFEST_SHA256), ("review_receipt_sha256", review_sha))
    if any(manifest.get(key) != value for key, value in required) or manifest.get("dataset") != _expected_dataset() or manifest.get("fresh_row_range") != {"start": c.FRESH_ROW_START, "end_exclusive": c.FRESH_ROW_END, "count_per_shard": c.FRESH_ROW_COUNT} or manifest.get("prior_pilot_row_range") != {"start": 0, "end_exclusive": 2_048, "count_per_shard": 2_048}:
        raise ValueError("V5 source manifest contract mismatch")
    for field, expected in (("network_access", False), ("training", False), ("scientific_execution", False), ("evidence_ledger_mutation", False)):
        if manifest.get(field) is not expected:
            raise ValueError(f"V5 source flag mismatch: {field}")
    _check_self_digest(manifest, "manifest_sha256", "V5 source manifest")
    raw_artifacts = _audit_raw(raw)
    if manifest.get("raw_artifacts") != raw_artifacts:
        raise ValueError("V5 raw artifact binding mismatch")
    prior_ids = _audit_prior(prior, raw)
    datasets = manifest.get("datasets")
    if not isinstance(datasets, dict):
        raise ValueError("V5 source datasets are missing")
    all_ids: set[str] = set()
    by_split: dict[str, list[dict[str, Any]]] = {}
    for split, item in (("fit", c.DATASET_FILES[0]), ("assessment", c.DATASET_FILES[1])):
        key = f"{split}/fineweb_edu"
        metadata = datasets.get(key)
        expected = {"source": c.DATASET_SOURCE, "revision": c.DATASET_REVISION, "config": c.DATASET_CONFIG, "split": c.DATASET_SPLIT, "crawl": item["crawl"], "source_path": item["path"], "row_start": c.FRESH_ROW_START, "row_count": c.FRESH_ROW_COUNT, "normalized_path": f"{split}/fineweb_edu.jsonl"}
        if not isinstance(metadata, dict) or any(metadata.get(field) != value for field, value in expected.items()):
            raise ValueError(f"V5 {key} metadata mismatch")
        path = c.safe_relative(root, metadata["normalized_path"], f"V5 {key} JSONL")
        if c.sha256_file(path) != metadata.get("normalized_sha256"):
            raise ValueError(f"V5 {key} normalized digest mismatch")
        rows = _jsonl(path, f"V5 {key} JSONL")
        if len(rows) != c.FRESH_ROW_COUNT:
            raise ValueError(f"V5 {key} count mismatch")
        for ordinal, row in enumerate(rows):
            document_id = row.get("document_id")
            if not isinstance(document_id, str) or not document_id.startswith(f"fineweb-edu:{item['crawl']}:") or document_id in all_ids or document_id in prior_ids or row.get("source_row_index") != c.FRESH_ROW_START + ordinal or row.get("source_crawl") != item["crawl"] or row.get("source_path") != item["path"]:
                raise ValueError(f"V5 {key} identity mismatch at {ordinal}")
            all_ids.add(document_id)
        for ordinal, (observed, expected_row) in enumerate(zip(rows, _parquet_rows(raw / "dataset" / item["path"], item, c.FRESH_ROW_START, c.FRESH_ROW_END), strict=True)):
            if observed != expected_row:
                raise ValueError(f"V5 raw lineage mismatch in {key} at {ordinal}")
        by_split[split] = rows
    return {"manifest": manifest, "manifest_sha256": manifest["manifest_sha256"], "prior_ids": prior_ids, "ids": all_ids, "records_by_split": by_split}


def validate_source(source_root: Path, raw_root: Path, prior_root: Path, review_receipt: Path) -> dict[str, Any]:
    review = c.validate_review_receipt(review_receipt)
    review_sha = c.sha256_file(c.exact_path(review_receipt, c.REVIEW_RECEIPT_PATH, "V5 review receipt"))
    audit = _audit_source(source_root, raw_root, prior_root, review_sha)
    return {"valid": True, "state_slice": c.STATE_SLICE, "claim_ceiling": c.CLAIM_CEILING, "reviewer": review["reviewer"], "source_manifest_sha256": audit["manifest_sha256"], "fit_record_count": len(audit["records_by_split"]["fit"]), "assessment_record_count": len(audit["records_by_split"]["assessment"]), "prior_document_count": len(audit["prior_ids"])}


def _load_tokenizer(model_path: Path) -> Any:
    c.exact_path(model_path, c.MODEL_PATH, "model path")
    manifest = c.model_manifest(model_path)
    if manifest["manifest_sha256"] != c.EXPECTED_MODEL_MANIFEST_SHA256:
        raise ValueError("V5 model manifest mismatch before tokenizer load")
    if c.runtime_versions() != c.RUNTIME_VERSIONS:
        raise RuntimeError(f"V5 runtime mismatch: {c.runtime_versions()}")
    c.require_native_network_denial()
    from mlx_lm.utils import load_tokenizer
    with c.network_block():
        return load_tokenizer(model_path)


def parse_window(root: Path, raw: Any, tokenizer: Any, split: str) -> CorpusWindow:
    if not isinstance(raw, dict) or raw.get("dataset") != "fineweb_edu" or not isinstance(raw.get("document_id"), str) or not raw["document_id"] or not isinstance(raw.get("path"), str) or not isinstance(raw.get("window_ordinal"), int) or isinstance(raw["window_ordinal"], bool) or raw["window_ordinal"] != 0:
        raise ValueError(f"V5 {split} corpus identity mismatch")
    path = c.safe_relative(root, raw["path"], f"V5 {split} corpus window")
    data = path.read_bytes()
    text = data.decode("utf-8")
    token_ids = list(tokenizer.encode(text, add_special_tokens=False))
    if len(token_ids) != c.WINDOW_TOKENS or list(tokenizer.encode(tokenizer.decode(token_ids), add_special_tokens=False)) != token_ids:
        raise ValueError(f"V5 {split} tokenizer shape mismatch: {raw['path']}")
    text_sha = hashlib.sha256(data).hexdigest()
    if raw.get("token_count") != c.WINDOW_TOKENS or raw.get("byte_len") != len(data) or raw.get("text_sha256") != text_sha or not isinstance(raw.get("source_sha256"), str) or len(raw["source_sha256"]) != 64:
        raise ValueError(f"V5 {split} window digest/shape mismatch: {raw['path']}")
    return CorpusWindow("fineweb_edu", raw["document_id"], raw["path"], 0, text, len(data), raw["source_sha256"], text_sha, len(token_ids), tuple(token_ids))


def _audit_corpus(corpus_root: Path, source_root: Path, raw_root: Path, prior_root: Path, model_path: Path, source_manifest_sha256: str, review_sha: str) -> dict[str, Any]:
    root = c.exact_or_staging_path(corpus_root, c.CORPUS_ROOT, "V5 corpus root")
    expected_files = {"manifest.json", *{f"{split}/window-{ordinal:06d}.txt" for split in ("fit", "assessment") for ordinal in range(c.FIT_WINDOW_COUNT)}}
    c.exact_file_set(root, expected_files, "V5 corpus root")
    source = _audit_source(source_root, raw_root, prior_root, review_sha)
    if source["manifest_sha256"] != source_manifest_sha256:
        raise ValueError("V5 corpus source binding mismatch")
    model_path = c.exact_path(model_path, c.MODEL_PATH, "model path")
    model_files = c.model_manifest(model_path)
    if model_files["manifest_sha256"] != c.EXPECTED_MODEL_MANIFEST_SHA256:
        raise ValueError("V5 model manifest mismatch before tokenizer load")
    c.require_native_network_denial()
    manifest = _json(root / "manifest.json", "V5 corpus manifest")
    if manifest.get("schema") != c.CORPUS_SCHEMA or manifest.get("state_slice") != c.STATE_SLICE or manifest.get("claim_ceiling") != c.CLAIM_CEILING or manifest.get("source_manifest_sha256") != source_manifest_sha256 or manifest.get("review_receipt_sha256") != review_sha or manifest.get("model_path") != str(c.MODEL_PATH) or manifest.get("model_manifest_sha256") != c.EXPECTED_MODEL_MANIFEST_SHA256 or manifest.get("fit_window_count") != c.FIT_WINDOW_COUNT or manifest.get("assessment_window_count") != c.ASSESSMENT_WINDOW_COUNT or manifest.get("window_token_count") != c.WINDOW_TOKENS or manifest.get("tokenizer") != "mlx_lm.utils.load_tokenizer:add_special_tokens=False" or any(manifest.get(field) is not False for field in ("network_access", "training", "scientific_execution", "evidence_ledger_mutation")):
        raise ValueError("V5 corpus manifest contract mismatch")
    _check_self_digest(manifest, "manifest_sha256", "V5 corpus manifest")
    tokenizer = _load_tokenizer(model_path)
    windows: dict[str, list[CorpusWindow]] = {}
    source_by_id = {row["document_id"]: row for rows in source["records_by_split"].values() for row in rows}
    for split, count in (("fit", c.FIT_WINDOW_COUNT), ("assessment", c.ASSESSMENT_WINDOW_COUNT)):
        rows = manifest.get(f"{split}_windows")
        if not isinstance(rows, list) or len(rows) != count:
            raise ValueError(f"V5 {split} manifest window count mismatch")
        expected_document_ids = []
        for source_row in source["records_by_split"][split]:
            source_ids = list(tokenizer.encode(source_row["text"], add_special_tokens=False))
            if len(source_ids) < c.WINDOW_TOKENS:
                continue
            selected_ids = source_ids[:c.WINDOW_TOKENS]
            if list(tokenizer.encode(tokenizer.decode(selected_ids), add_special_tokens=False)) != selected_ids:
                continue
            expected_document_ids.append(source_row["document_id"])
            if len(expected_document_ids) == count:
                break
        if [item.get("document_id") for item in rows] != expected_document_ids:
            raise ValueError(f"V5 {split} corpus is not the first eligible window sequence")
        seen: set[str] = set()
        parsed = []
        for ordinal, raw in enumerate(rows):
            window = parse_window(root, raw, tokenizer, split)
            if window.window_ordinal != 0 or window.relative_path != f"{split}/window-{ordinal:06d}.txt" or window.document_id in seen or window.document_id not in {item["document_id"] for item in source["records_by_split"][split]}:
                raise ValueError(f"V5 {split} window identity mismatch at {ordinal}")
            source_row = source_by_id[window.document_id]
            if window.source_sha256 != hashlib.sha256(source_row["text"].encode("utf-8")).hexdigest() or raw.get("source_row_index") != source_row["source_row_index"] or raw.get("source_path") != source_row["source_path"]:
                raise ValueError(f"V5 {split} source text binding mismatch at {ordinal}")
            seen.add(window.document_id)
            parsed.append(window)
        windows[split] = parsed
    if set(item.document_id for item in windows["fit"]) & set(item.document_id for item in windows["assessment"]):
        raise ValueError("V5 fit and assessment windows overlap")
    return {"manifest": manifest, "manifest_sha256": manifest["manifest_sha256"], "windows": windows, "fit_ids": {item.document_id for item in windows["fit"]}, "assessment_ids": {item.document_id for item in windows["assessment"]}, "text_sha": {split: {item.document_id: item.text_sha256 for item in values} for split, values in windows.items()}}


def validate_corpus(corpus_root: Path, source_root: Path, raw_root: Path, prior_root: Path, model_path: Path, source_manifest_sha256: str, review_receipt: Path) -> dict[str, Any]:
    review = c.validate_review_receipt(review_receipt)
    review_sha = c.sha256_file(c.exact_path(review_receipt, c.REVIEW_RECEIPT_PATH, "V5 review receipt"))
    audit = _audit_corpus(corpus_root, source_root, raw_root, prior_root, model_path, source_manifest_sha256, review_sha)
    return {"valid": True, "state_slice": c.STATE_SLICE, "claim_ceiling": c.CLAIM_CEILING, "reviewer": review["reviewer"], "corpus_manifest_sha256": audit["manifest_sha256"], "fit_window_count": len(audit["windows"]["fit"]), "assessment_window_count": len(audit["windows"]["assessment"])}


def _finite(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
        raise ValueError(f"{label} must be a finite non-boolean number")
    return float(value)


def _strict_int(value: Any, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{label} must be an integer")
    return value


def _validate_metrics(metrics: Any, windows: list[CorpusWindow], label: str, temperature: float, evaluation_config: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(metrics, dict):
        raise ValueError(f"{label} must be an object")
    if _finite(metrics.get("temperature"), f"{label} temperature") != temperature or metrics.get("evaluation_config") != evaluation_config:
        raise ValueError(f"{label} control identity mismatch")
    rows = metrics.get("rows")
    if not isinstance(rows, list) or len(rows) != len(windows):
        raise ValueError(f"{label} row count mismatch")
    by_id = {window.document_id: window for window in windows}
    seen: set[str] = set()
    total_nll = 0.0
    total_targets = 0
    for row in rows:
        if not isinstance(row, dict) or not isinstance(row.get("document_id"), str) or row["document_id"] not in by_id or row["document_id"] in seen or row.get("dataset") != "fineweb_edu" or _strict_int(row.get("window_ordinal"), f"{label} window_ordinal") != 0 or row.get("relative_path") != by_id[row["document_id"]].relative_path or row.get("source_sha256") != by_id[row["document_id"]].source_sha256 or row.get("text_sha256") != by_id[row["document_id"]].text_sha256 or _strict_int(row.get("token_count"), f"{label} token_count") != c.WINDOW_TOKENS or _strict_int(row.get("target_count"), f"{label} target_count") != c.WINDOW_TOKENS - 1:
            raise ValueError(f"{label} row identity/shape mismatch")
        nll = _finite(row.get("nll"), f"{label} NLL")
        total_nll += nll
        total_targets += c.WINDOW_TOKENS - 1
        seen.add(row["document_id"])
    if seen != set(by_id) or _strict_int(metrics.get("target_tokens"), f"{label} target_tokens") != total_targets:
        raise ValueError(f"{label} target token count mismatch")
    expected_mean = round(total_nll / total_targets, 9)
    expected_perplexity = round(math.exp(expected_mean), 9)
    if _finite(metrics.get("mean_nll"), f"{label} mean_nll") != expected_mean or _finite(metrics.get("perplexity"), f"{label} perplexity") != expected_perplexity:
        raise ValueError(f"{label} aggregate mismatch")
    return metrics


def _validate_parity(parity: Any, windows: list[CorpusWindow]) -> None:
    if not isinstance(parity, dict) or parity.get("sequence_count") != len(windows) or parity.get("all_passed") is not True or parity.get("tolerance") != c.PARITY_TOLERANCE or not isinstance(parity.get("checks"), list) or len(parity["checks"]) != len(windows):
        raise ValueError("V5 parity shape mismatch")
    by_id = {window.document_id: window for window in windows}
    seen: set[str] = set()
    maximum = -math.inf
    for check in parity["checks"]:
        if not isinstance(check, dict) or not isinstance(check.get("document_id"), str) or check["document_id"] not in by_id or check["document_id"] in seen or check.get("dataset") != "fineweb_edu" or _strict_int(check.get("window_ordinal"), "V5 parity window_ordinal") != 0 or check.get("relative_path") != by_id[check["document_id"]].relative_path or check.get("source_sha256") != by_id[check["document_id"]].source_sha256 or check.get("text_sha256") != by_id[check["document_id"]].text_sha256 or _strict_int(check.get("token_count"), "V5 parity token_count") != c.WINDOW_TOKENS or check.get("tolerance") != c.PARITY_TOLERANCE or check.get("passed") is not True:
            raise ValueError("V5 parity identity mismatch")
        maximum = max(maximum, _finite(check.get("max_abs_logit_delta"), "V5 parity delta"))
        seen.add(check["document_id"])
    if seen != set(by_id) or _finite(parity.get("max_abs_logit_delta"), "V5 parity aggregate") != maximum:
        raise ValueError("V5 parity aggregate mismatch")


def _input_snapshot(source_root: Path, corpus_root: Path, raw_root: Path, prior_root: Path, model_path: Path) -> dict[str, Any]:
    source = c.exact_path(source_root, c.SOURCE_ROOT, "V5 source root")
    corpus = c.exact_path(corpus_root, c.CORPUS_ROOT, "V5 corpus root")
    raw = c.exact_path(raw_root, c.RAW_ROOT, "V5 raw root")
    prior = c.exact_path(prior_root, c.R1_SOURCE_ROOT, "V5 prior-pilot source root")
    model = c.exact_path(model_path, c.MODEL_PATH, "model path")
    corpus_files = {"manifest.json", *{f"{split}/window-{ordinal:06d}.txt" for split in ("fit", "assessment") for ordinal in range(c.FIT_WINDOW_COUNT)}}
    return {"source": c.snapshot_files(source, {"acquisition-manifest.json", "fit/fineweb_edu.jsonl", "assessment/fineweb_edu.jsonl"}, "V5 source root"), "corpus": c.snapshot_files(corpus, corpus_files, "V5 corpus root"), "raw": c.snapshot_files(raw, {f"dataset/{item['path']}" for item in c.DATASET_FILES}, "V5 raw root", allow_cache=True), "prior": c.snapshot_files(prior, {"acquisition-manifest.json", "fit/fineweb_edu.jsonl", "assessment/fineweb_edu.jsonl"}, "V5 prior-pilot source root"), "model": c.model_manifest(model)}


def _assert_input_snapshot(snapshot: dict[str, Any], source_root: Path, corpus_root: Path, raw_root: Path, prior_root: Path, model_path: Path) -> None:
    if _input_snapshot(source_root, corpus_root, raw_root, prior_root, model_path) != snapshot:
        raise RuntimeError("V5 independent validator input custody changed")


def _check_common_binding(value: dict[str, Any], label: str, review_sha: str, source_sha: str, corpus_sha: str) -> None:
    if value.get("schema") != c.RESULT_SCHEMA or value.get("state_slice") != c.STATE_SLICE or value.get("claim_ceiling") != c.CLAIM_CEILING or value.get("protocol_sha256") != c.PROTOCOL_SHA256 or value.get("review_receipt_sha256") != review_sha or value.get("source_manifest_sha256") != source_sha or value.get("corpus_manifest_sha256") != corpus_sha or value.get("model_path") != str(c.MODEL_PATH) or value.get("model_manifest_sha256") != c.EXPECTED_MODEL_MANIFEST_SHA256 or value.get("model_type") != "gemma3_text" or value.get("architecture") != "gemma3_text" or value.get("layer_count") != 26 or value.get("runtime") != c.RUNTIME_VERSIONS:
        raise ValueError(f"{label} custody binding mismatch")


def validate_result(result_root: Path, source_root: Path, corpus_root: Path, raw_root: Path, prior_root: Path, model_path: Path, review_receipt: Path, corpus_manifest_sha256: str) -> dict[str, Any]:
    root = c.exact_or_staging_path(result_root, c.RESULT_ROOT, "V5 result root")
    c.exact_file_set(root, {"config.json", "results.json", "receipt.json", "corpus-manifest.json", "model-manifest.json", "review-receipt.json", "validator-receipt.json"}, "V5 result root")
    c.validate_review_receipt(review_receipt)
    reviewed_snapshot = c.snapshot_code_and_review()
    review_path = c.exact_path(review_receipt, c.REVIEW_RECEIPT_PATH, "V5 review receipt")
    review_sha = c.sha256_file(review_path)
    staged_review = c.regular(root / "review-receipt.json", "V5 staged review receipt")
    if staged_review.read_bytes() != review_path.read_bytes():
        raise ValueError("V5 staged review receipt differs from reviewed receipt")
    source = _audit_source(source_root, raw_root, prior_root, review_sha)
    corpus = _audit_corpus(corpus_root, source_root, raw_root, prior_root, model_path, source["manifest_sha256"], review_sha)
    if corpus["manifest_sha256"] != corpus_manifest_sha256 or (root / "corpus-manifest.json").read_bytes() != c.regular(corpus_root / "manifest.json", "V5 corpus manifest").read_bytes():
        raise ValueError("V5 result corpus binding mismatch")
    model_manifest = _json(root / "model-manifest.json", "V5 result model manifest")
    current_model_manifest = c.model_manifest(c.exact_path(model_path, c.MODEL_PATH, "model path"))
    if model_manifest != current_model_manifest or model_manifest["manifest_sha256"] != c.EXPECTED_MODEL_MANIFEST_SHA256:
        raise ValueError("V5 result model manifest mismatch")
    config = _json(root / "config.json", "V5 result config")
    results = _json(root / "results.json", "V5 result body")
    receipt = _json(root / "receipt.json", "V5 result receipt")
    validator_receipt = _json(root / "validator-receipt.json", "V5 validator receipt")
    _check_self_digest(config, "config_sha256", "V5 result config")
    _check_self_digest(results, "results_sha256", "V5 result body")
    _check_self_digest(receipt, "receipt_sha256", "V5 result receipt")
    _check_self_digest(validator_receipt, "receipt_sha256", "V5 validator receipt")
    for value, label in ((config, "V5 config"), (results, "V5 results"), (receipt, "V5 receipt")):
        _check_common_binding(value, label, review_sha, source["manifest_sha256"], corpus_manifest_sha256)
    for field, expected in (("zero_alpha_parity_passed", True), ("nonzero_intervention_reach", results.get("qualification", {}).get("nonzero_intervention_reach")), ("deterministic_repeat_passed", results.get("deterministic_repeat_passed")), ("network_access", False), ("training", False), ("weights_frozen", True), ("evidence_ledger_mutation", False)):
        if receipt.get(field) is not expected:
            raise ValueError(f"V5 result receipt control mismatch: {field}")
    if validator_receipt.get("schema") != "gemma3-fineweb-edu-replication-v5-validator-receipt" or validator_receipt.get("state_slice") != c.STATE_SLICE or validator_receipt.get("result_sha256") != results["results_sha256"] or validator_receipt.get("review_receipt_sha256") != review_sha or validator_receipt.get("independent_recomputation") is not True:
        raise ValueError("V5 validator receipt binding mismatch")
    for value, field, expected in ((config, "network_access", False), (config, "training", False), (config, "weights_frozen", True), (config, "evidence_ledger_mutation", False), (config, "assessment_authorized_by_review", True), (results, "network_access", False), (results, "training", False), (results, "weights_frozen", True), (results, "evidence_ledger_mutation", False), (results, "local_only", True)):
        if value.get(field) is not expected:
            raise ValueError(f"V5 {field} flag mismatch")
    if config.get("candidate_pairs") != [list(pair) for pair in c.CANDIDATE_PAIRS] or config.get("fit_alpha") != c.FIT_ALPHA or config.get("fit_beta") != c.FIT_BETA or config.get("evaluation_alpha") != c.EVALUATION_ALPHA or config.get("evaluation_beta") != c.EVALUATION_BETA or config.get("temperature_control") != c.TEMPERATURE_CONTROL or config.get("normalization") != "source_l2_norm_to_destination_l2_norm" or config.get("controls") != list(c.CONTROL_NAMES):
        raise ValueError("V5 locked configuration mismatch")
    fit_windows = corpus["windows"]["fit"]
    assessment_windows = corpus["windows"]["assessment"]
    candidates = results.get("fit_candidates")
    if not isinstance(candidates, list) or len(candidates) != len(c.CANDIDATE_PAIRS):
        raise ValueError("V5 candidate count mismatch")
    candidate_means = []
    for candidate, pair in zip(candidates, c.CANDIDATE_PAIRS, strict=True):
        expected_cfg = {"source_layer": pair[0], "destination_layer": pair[1], "alpha": c.FIT_ALPHA, "beta": c.FIT_BETA, "epsilon": c.EPSILON}
        if not isinstance(candidate, dict) or candidate.get("config") != expected_cfg:
            raise ValueError("V5 candidate configuration mismatch")
        metrics = _validate_metrics(candidate.get("metrics"), fit_windows, "V5 fit candidate", 1.0, expected_cfg)
        candidate_means.append((metrics["mean_nll"], pair[0], pair[1]))
    fit_baseline = _validate_metrics(results.get("fit_baseline"), fit_windows, "V5 fit baseline", 1.0, None)
    selected_tuple = min(candidate_means)
    selected_cfg = {"source_layer": selected_tuple[1], "destination_layer": selected_tuple[2], "alpha": c.FIT_ALPHA, "beta": c.FIT_BETA, "epsilon": c.EPSILON}
    locked_cfg = {"source_layer": selected_tuple[1], "destination_layer": selected_tuple[2], "alpha": c.EVALUATION_ALPHA, "beta": c.EVALUATION_BETA, "epsilon": c.EPSILON}
    if results.get("selected_fit_config") != selected_cfg or results.get("locked_evaluation_config") != locked_cfg or config.get("selected_fit_config") != selected_cfg or config.get("locked_evaluation_config") != locked_cfg or results.get("paper_expected_pair") != {"source_layer": 11, "destination_layer": 4} or config.get("paper_expected_pair") != {"source_layer": 11, "destination_layer": 4} or results.get("paper_expected_pair_recovered") != ((selected_tuple[1], selected_tuple[2]) == (11, 4)):
        raise ValueError("V5 selected or locked configuration mismatch")
    baseline = _validate_metrics(results.get("assessment_baseline"), assessment_windows, "V5 assessment baseline", 1.0, None)
    selected = _validate_metrics(results.get("assessment_selected"), assessment_windows, "V5 assessment selected", 1.0, locked_cfg)
    temp_baseline = _validate_metrics(results.get("assessment_temperature_baseline"), assessment_windows, "V5 temperature baseline", c.TEMPERATURE_CONTROL, None)
    temp_selected = _validate_metrics(results.get("assessment_temperature_selected"), assessment_windows, "V5 temperature intervention", c.TEMPERATURE_CONTROL, locked_cfg)
    repeat = _validate_metrics(results.get("assessment_repeat"), assessment_windows, "V5 deterministic repeat", 1.0, locked_cfg)
    if repeat != selected:
        raise ValueError("V5 deterministic repeat differs from selected assessment")
    _validate_parity(results.get("parity"), [*fit_windows, *assessment_windows])
    expected_controls = {"native_baseline": baseline, "zero_alpha_identity": results["parity"], "all_candidate_evaluations": candidates, "temperature_1.20_baseline": temp_baseline, "temperature_1.20_intervention": temp_selected, "deterministic_repeat": repeat, "frozen_model_manifest": {"before": c.EXPECTED_MODEL_MANIFEST_SHA256, "after": c.EXPECTED_MODEL_MANIFEST_SHA256}, "frozen_model_parameters": {"before": results.get("model_parameter_digest_before"), "after": results.get("model_parameter_digest_after")}}
    if results.get("controls") != expected_controls or results.get("qualification", {}).get("nonzero_intervention_reach") is not True or results.get("deterministic_repeat_passed") is not True:
        raise ValueError("V5 retained control mismatch")
    baseline_rows = {row["document_id"]: row for row in baseline["rows"]}
    selected_rows = {row["document_id"]: row for row in selected["rows"]}
    per_document = results.get("assessment_per_document")
    if not isinstance(per_document, list) or len(per_document) != len(assessment_windows):
        raise ValueError("V5 per-document count mismatch")
    deltas = []
    seen: set[str] = set()
    by_id = {window.document_id: window for window in assessment_windows}
    for row in per_document:
        document_id = row.get("document_id") if isinstance(row, dict) else None
        if not isinstance(row, dict) or not isinstance(document_id, str) or document_id not in by_id or document_id in seen or row.get("dataset") != "fineweb_edu" or _strict_int(row.get("window_ordinal"), "V5 per-document window_ordinal") != 0 or row.get("relative_path") != by_id[document_id].relative_path or row.get("source_sha256") != by_id[document_id].source_sha256 or row.get("text_sha256") != by_id[document_id].text_sha256 or _strict_int(row.get("token_count"), "V5 per-document token_count") != c.WINDOW_TOKENS or _strict_int(row.get("target_count"), "V5 per-document target_count") != c.WINDOW_TOKENS - 1 or row.get("baseline_nll") != baseline_rows[document_id]["nll"] or row.get("selected_nll") != selected_rows[document_id]["nll"]:
            raise ValueError("V5 per-document binding mismatch")
        delta = _finite(row.get("delta_selected_minus_baseline"), "V5 per-document delta")
        expected_delta = selected_rows[document_id]["nll"] / (c.WINDOW_TOKENS - 1) - baseline_rows[document_id]["nll"] / (c.WINDOW_TOKENS - 1)
        if delta != expected_delta:
            raise ValueError("V5 per-document delta mismatch")
        deltas.append(delta)
        seen.add(document_id)
    if seen != set(by_id):
        raise ValueError("V5 per-document set mismatch")
    bootstrap = c.bootstrap_mean_ci(deltas)
    if results.get("assessment_nll_delta_selected_minus_baseline") != bootstrap["mean_delta"] or results.get("bootstrap") != bootstrap or results.get("decision") != c.decide_replication(bootstrap) or receipt.get("bootstrap") != bootstrap or receipt.get("decision") != results.get("decision"):
        raise ValueError("V5 uncertainty or decision mismatch")
    parameter_before = results.get("model_parameter_digest_before")
    parameter_after = results.get("model_parameter_digest_after")
    if not isinstance(parameter_before, str) or not isinstance(parameter_after, str) or len(parameter_before) != 64 or len(parameter_after) != 64 or parameter_before != parameter_after or config.get("model_parameter_digest_before") != parameter_before or config.get("model_parameter_digest_after") != parameter_after or receipt.get("model_parameter_digest_before") != parameter_before or receipt.get("model_parameter_digest_after") != parameter_after:
        raise ValueError("V5 parameter custody mismatch")
    c.require_native_network_denial()
    input_snapshot = _input_snapshot(source_root, corpus_root, raw_root, prior_root, model_path)
    c.assert_code_and_review_snapshot(reviewed_snapshot)
    from experiments.continual_learning import stage_and_run_gemma3_fineweb_edu_replication_v5 as runner
    pre_effect_manifest = c.model_manifest(c.exact_path(model_path, c.MODEL_PATH, "model path"))
    if pre_effect_manifest["manifest_sha256"] != c.EXPECTED_MODEL_MANIFEST_SHA256:
        raise ValueError("V5 model manifest mismatch before independent recomputation")
    with c.network_block():
        model, tokenizer, _runtime = runner.load_runtime(model_path)
        if getattr(model.args, "model_type", None) != "gemma3_text" or len(model.model.layers) != 26:
            raise ValueError("V5 independent model shape/type mismatch")
        if c.model_parameter_digest(model) != parameter_before:
            raise ValueError("V5 independent before-parameter digest mismatch")
        recompute_fit, recompute_assessment, _ = runner.load_corpus(corpus_root, tokenizer)
        c.assert_code_and_review_snapshot(reviewed_snapshot)
        _assert_input_snapshot(input_snapshot, source_root, corpus_root, raw_root, prior_root, model_path)
        recomputed_parity = runner.parity(model, [*recompute_fit, *recompute_assessment])
        if recomputed_parity != results["parity"]:
            raise ValueError("V5 independent parity mismatch")
        recomputed_fit_baseline = runner.evaluate_windows(model, tokenizer, recompute_fit, None)
        if recomputed_fit_baseline != fit_baseline:
            raise ValueError("V5 independent fit baseline mismatch")
        recomputed_candidates = []
        for pair in c.CANDIDATE_PAIRS:
            cfg = runner.RecirculationConfig(pair[0], pair[1], c.FIT_ALPHA, c.FIT_BETA)
            recomputed_candidates.append({"config": cfg.as_dict(), "metrics": runner.evaluate_windows(model, tokenizer, recompute_fit, cfg)})
        if recomputed_candidates != candidates:
            raise ValueError("V5 independent candidate mismatch")
        recomputed_assessment_baseline = runner.evaluate_windows(model, tokenizer, recompute_assessment, None)
        locked = runner.RecirculationConfig(selected_tuple[1], selected_tuple[2], c.EVALUATION_ALPHA, c.EVALUATION_BETA)
        recomputed_selected = runner.evaluate_windows(model, tokenizer, recompute_assessment, locked)
        recomputed_temp_baseline = runner.evaluate_windows(model, tokenizer, recompute_assessment, None, temperature=c.TEMPERATURE_CONTROL)
        recomputed_temp_selected = runner.evaluate_windows(model, tokenizer, recompute_assessment, locked, temperature=c.TEMPERATURE_CONTROL)
        recomputed_repeat = runner.evaluate_windows(model, tokenizer, recompute_assessment, locked)
        if recomputed_assessment_baseline != baseline or recomputed_selected != selected or recomputed_temp_baseline != temp_baseline or recomputed_temp_selected != temp_selected or recomputed_repeat != repeat:
            raise ValueError("V5 independent assessment/control mismatch")
        if c.model_parameter_digest(model) != parameter_after or c.model_manifest(model_path) != pre_effect_manifest:
            raise ValueError("V5 independent after-custody mismatch")
    c.assert_code_and_review_snapshot(reviewed_snapshot)
    _assert_input_snapshot(input_snapshot, source_root, corpus_root, raw_root, prior_root, model_path)
    return {"valid": True, "state_slice": c.STATE_SLICE, "claim_ceiling": c.CLAIM_CEILING, "result_root": str(root), "decision": results["decision"], "results_sha256": results["results_sha256"], "bootstrap": bootstrap, "review_receipt_sha256": review_sha}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("source", "corpus", "result"), required=True)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--raw-root", type=Path, required=True)
    parser.add_argument("--prior-root", type=Path, required=True)
    parser.add_argument("--corpus-root", type=Path)
    parser.add_argument("--result-root", type=Path)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--review-receipt", type=Path, required=True)
    parser.add_argument("--source-manifest-sha256")
    parser.add_argument("--corpus-manifest-sha256")
    args = parser.parse_args()
    if args.mode == "source":
        value = validate_source(args.source_root, args.raw_root, args.prior_root, args.review_receipt)
    elif args.mode == "corpus":
        if args.corpus_root is None or args.source_manifest_sha256 is None:
            parser.error("corpus mode requires --corpus-root and --source-manifest-sha256")
        value = validate_corpus(args.corpus_root, args.source_root, args.raw_root, args.prior_root, args.model, args.source_manifest_sha256, args.review_receipt)
    else:
        if args.corpus_root is None or args.result_root is None or args.corpus_manifest_sha256 is None:
            parser.error("result mode requires --corpus-root, --result-root, and --corpus-manifest-sha256")
        value = validate_result(args.result_root, args.source_root, args.corpus_root, args.raw_root, args.prior_root, args.model, args.review_receipt, args.corpus_manifest_sha256)
    print(json.dumps(value, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
