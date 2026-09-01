#!/usr/bin/env python3
"""Independent strict validator for Gemma3 FineWeb-Edu replication V4.

State slice: continual-learning-gemma3-fineweb-edu-replication-v4.
Every validator mode is read-only. Result validation re-runs the reviewed V4
inference seam after structural custody checks and compares every retained
control and metric, rather than trusting self-reported aggregates.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator

from experiments.continual_learning import gemma3_fineweb_edu_replication_v4_contract as c


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
    token_ids: tuple[int, ...] | None = None


def _json(path: Path, label: str) -> dict[str, Any]:
    value = json.loads(c.regular(path, label).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be a JSON object")
    return value


def _jsonl(path: Path, label: str) -> list[dict[str, Any]]:
    rows = []
    with c.regular(path, label).open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                raise ValueError(f"{label} has a blank line at {line_number}")
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
        raise ValueError(f"empty FineWeb-Edu text at row {source_row_index}: {item['path']}")
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
    raw_root = c.exact_path(raw_root, c.RAW_ROOT, "V4 raw root")
    if not raw_root.is_dir():
        raise FileNotFoundError(f"V4 raw root is not a directory: {raw_root}")
    c.reject_tree_symlinks(raw_root, "V4 raw root")
    artifacts = []
    expected_paths = set()
    for item in c.DATASET_FILES:
        path = c.regular(raw_root / "dataset" / item["path"], "V4 pinned Parquet shard")
        expected_paths.add(path)
        if path.stat().st_size != item["byte_len"] or c.sha256_file(path) != item["sha256"]:
            raise ValueError(f"V4 raw pin mismatch: {path}")
        import pyarrow.parquet as pq

        row_count = pq.ParquetFile(path).metadata.num_rows
        if row_count < c.FRESH_ROW_END:
            raise ValueError(f"V4 raw shard is too short: {path}")
        artifacts.append({"relative_path": path.relative_to(raw_root).as_posix(), "source": f"{c.DATASET_SOURCE}/resolve/{c.DATASET_REVISION}/{item['path']}", "crawl": item["crawl"], "byte_len": path.stat().st_size, "sha256": c.sha256_file(path), "lfs_sha256": item["sha256"], "row_count": row_count})
    actual_paths = {path for path in (raw_root / "dataset").rglob("*.parquet") if path.is_file() and not path.is_symlink()}
    if actual_paths != expected_paths:
        raise ValueError("V4 raw Parquet set differs from pinned two-file set")
    return artifacts


def _audit_prior(r1_source_root: Path, raw_root: Path) -> set[str]:
    root = c.exact_path(r1_source_root, c.R1_SOURCE_ROOT, "V4 prior-pilot source root")
    manifest_path = c.regular(root / "acquisition-manifest.json", "prior-pilot source manifest")
    if c.sha256_file(manifest_path) != c.R1_SOURCE_MANIFEST_SHA256:
        raise ValueError("prior-pilot manifest digest mismatch")
    manifest = _json(manifest_path, "prior-pilot source manifest")
    if manifest.get("schema") != "gemma3-fineweb-edu-bounded-acquisition-v1" or manifest.get("dataset") != _expected_dataset() or manifest.get("selection_policy") != "first-2048-records-from-two-pinned-crawls-document-disjoint-v1":
        raise ValueError("prior-pilot source contract mismatch")
    _check_self_digest(manifest, "manifest_sha256", "prior-pilot source manifest")
    datasets = manifest.get("datasets")
    if not isinstance(datasets, dict):
        raise ValueError("prior-pilot dataset entries missing")
    ids: set[str] = set()
    raw_root = c.exact_path(raw_root, c.RAW_ROOT, "V4 raw root")
    for split, item in (("fit", c.DATASET_FILES[0]), ("assessment", c.DATASET_FILES[1])):
        metadata = datasets.get(f"{split}/fineweb_edu")
        expected_path = f"{split}/fineweb_edu.jsonl"
        if not isinstance(metadata, dict) or metadata.get("row_start") != 0 or metadata.get("row_count") != 2048 or metadata.get("normalized_path") != expected_path or metadata.get("crawl") != item["crawl"] or metadata.get("source_path") != item["path"] or metadata.get("source") != c.DATASET_SOURCE or metadata.get("revision") != c.DATASET_REVISION or metadata.get("config") != c.DATASET_CONFIG or metadata.get("split") != c.DATASET_SPLIT:
            raise ValueError(f"prior-pilot {split} metadata mismatch")
        path = c.safe_relative(root, expected_path, f"prior-pilot {split} JSONL")
        if c.sha256_file(path) != metadata.get("normalized_sha256"):
            raise ValueError(f"prior-pilot {split} normalized digest mismatch")
        rows = _jsonl(path, f"prior-pilot {split} JSONL")
        if len(rows) != 2048:
            raise ValueError(f"prior-pilot {split} count mismatch")
        expected_rows = _parquet_rows(raw_root / "dataset" / item["path"], item, 0, 2048)
        for ordinal, (row, expected) in enumerate(zip(rows, expected_rows, strict=True)):
            if row != expected:
                raise ValueError(f"prior-pilot {split} content mismatch at {ordinal}")
            document_id = row.get("document_id")
            if not isinstance(document_id, str) or not document_id or document_id in ids or row.get("source_row_index") != ordinal or row.get("source_crawl") != item["crawl"] or row.get("source_path") != item["path"]:
                raise ValueError(f"prior-pilot {split} identity mismatch at {ordinal}")
            ids.add(document_id)
    return ids


def _audit_source(source_root: Path, raw_root: Path, r1_source_root: Path, review_sha: str | None = None) -> dict[str, Any]:
    root = c.exact_or_staging_path(source_root, c.SOURCE_ROOT, "V4 source root")
    raw_root = c.exact_path(raw_root, c.RAW_ROOT, "V4 raw root")
    r1_source_root = c.exact_path(r1_source_root, c.R1_SOURCE_ROOT, "V4 prior-pilot source root")
    c.reject_tree_symlinks(root, "V4 source root")
    c.reject_tree_symlinks(r1_source_root, "V4 prior-pilot source root")
    manifest = _json(root / "acquisition-manifest.json", "V4 source manifest")
    required = (("schema", c.SOURCE_SCHEMA), ("state_slice", c.STATE_SLICE), ("claim_ceiling", c.CLAIM_CEILING), ("source_record_schema", "gemma3-source-v1-compatible-with-fineweb-metadata"), ("selection_policy", "rows-2048-through-18431-two-pinned-crawls-v4"), ("raw_root", str(c.RAW_ROOT)), ("prior_pilot_source_root", str(c.R1_SOURCE_ROOT)), ("prior_pilot_manifest_sha256", c.R1_SOURCE_MANIFEST_SHA256))
    if any(manifest.get(key) != value for key, value in required) or manifest.get("dataset") != _expected_dataset() or manifest.get("fresh_row_range") != {"start": c.FRESH_ROW_START, "end_exclusive": c.FRESH_ROW_END, "count_per_shard": c.FRESH_ROW_COUNT}:
        raise ValueError("V4 source manifest contract mismatch")
    if manifest.get("prior_pilot_row_range") != {"start": 0, "end_exclusive": 2048, "count_per_shard": 2048}:
        raise ValueError("V4 prior-pilot row range mismatch")
    if review_sha is not None and manifest.get("review_receipt_sha256") != review_sha:
        raise ValueError("V4 source review binding mismatch")
    for key in ("network_access", "training", "scientific_execution", "evidence_ledger_mutation"):
        if manifest.get(key) is not False:
            raise ValueError(f"V4 source flag mismatch: {key}")
    _check_self_digest(manifest, "manifest_sha256", "V4 source manifest")
    raw_artifacts = _audit_raw(raw_root)
    if manifest.get("raw_artifacts") != raw_artifacts:
        raise ValueError("V4 raw artifact binding mismatch")
    prior_ids = _audit_prior(r1_source_root, raw_root)
    datasets = manifest.get("datasets")
    if not isinstance(datasets, dict):
        raise ValueError("V4 source datasets missing")
    records_by_split: dict[str, list[dict[str, Any]]] = {}
    all_ids: set[str] = set()
    for split, item in (("fit", c.DATASET_FILES[0]), ("assessment", c.DATASET_FILES[1])):
        key = f"{split}/fineweb_edu"
        metadata = datasets.get(key)
        expected = {"source": c.DATASET_SOURCE, "revision": c.DATASET_REVISION, "config": c.DATASET_CONFIG, "split": c.DATASET_SPLIT, "crawl": item["crawl"], "source_path": item["path"], "row_start": c.FRESH_ROW_START, "row_count": c.FRESH_ROW_COUNT, "normalized_path": f"{split}/fineweb_edu.jsonl"}
        if not isinstance(metadata, dict) or any(metadata.get(field) != value for field, value in expected.items()):
            raise ValueError(f"V4 {key} metadata mismatch")
        path = c.safe_relative(root, metadata["normalized_path"], f"V4 {key} JSONL")
        if c.sha256_file(path) != metadata.get("normalized_sha256"):
            raise ValueError(f"V4 {key} normalized digest mismatch")
        rows = _jsonl(path, f"V4 {key} JSONL")
        if len(rows) != c.FRESH_ROW_COUNT:
            raise ValueError(f"V4 {key} count mismatch")
        for ordinal, row in enumerate(rows):
            document_id = row.get("document_id")
            if not isinstance(document_id, str) or not document_id.startswith(f"fineweb-edu:{item['crawl']}:") or document_id in all_ids or document_id in prior_ids or row.get("source_row_index") != c.FRESH_ROW_START + ordinal or row.get("source_crawl") != item["crawl"] or row.get("source_path") != item["path"]:
                raise ValueError(f"V4 {key} identity mismatch at {ordinal}")
            all_ids.add(document_id)
        for ordinal, (observed, expected_row) in enumerate(zip(rows, _parquet_rows(raw_root / "dataset" / item["path"], item, c.FRESH_ROW_START, c.FRESH_ROW_END), strict=True)):
            if observed != expected_row:
                raise ValueError(f"V4 raw lineage mismatch in {key} at {ordinal}")
        records_by_split[split] = rows
    return {"manifest": manifest, "manifest_sha256": manifest["manifest_sha256"], "prior_ids": prior_ids, "ids": all_ids, "records_by_split": records_by_split}


def validate_source(source_root: Path, raw_root: Path = c.RAW_ROOT, r1_source_root: Path = c.R1_SOURCE_ROOT, review_receipt: Path | None = None) -> dict[str, Any]:
    if review_receipt is not None:
        validate_review_receipt(review_receipt)
    review_sha = c.sha256_file(review_receipt) if review_receipt is not None else None
    audit = _audit_source(source_root, raw_root, r1_source_root, review_sha)
    return {"valid": True, "state_slice": c.STATE_SLICE, "claim_ceiling": c.CLAIM_CEILING, "source_manifest_sha256": audit["manifest_sha256"], "fit_record_count": len(audit["records_by_split"]["fit"]), "assessment_record_count": len(audit["records_by_split"]["assessment"]), "prior_document_count": len(audit["prior_ids"])}


def _load_tokenizer(model_path: Path) -> Any:
    if c.runtime_versions() != c.RUNTIME_VERSIONS:
        raise RuntimeError(f"V4 runtime mismatch: {c.runtime_versions()}")
    from mlx_lm.utils import load_tokenizer

    return load_tokenizer(model_path)


def parse_window(root: Path, raw: Any, tokenizer: Any, split: str) -> CorpusWindow:
    if not isinstance(raw, dict):
        raise ValueError(f"V4 {split} corpus entry must be an object")
    dataset = raw.get("dataset")
    document_id = raw.get("document_id")
    relative_path = raw.get("path")
    ordinal = raw.get("window_ordinal")
    if not isinstance(dataset, str) or dataset != "fineweb_edu" or not isinstance(document_id, str) or not document_id or not isinstance(relative_path, str) or not isinstance(ordinal, int) or isinstance(ordinal, bool) or ordinal != 0:
        raise ValueError(f"V4 {split} corpus identity mismatch")
    path = c.safe_relative(root, relative_path, f"V4 {split} corpus window")
    raw_bytes = path.read_bytes()
    text = raw_bytes.decode("utf-8")
    token_ids = list(tokenizer.encode(text, add_special_tokens=False))
    if len(token_ids) != c.WINDOW_TOKENS or list(tokenizer.encode(tokenizer.decode(token_ids), add_special_tokens=False)) != token_ids:
        raise ValueError(f"V4 {split} corpus tokenizer shape mismatch: {relative_path}")
    if raw.get("token_count") != c.WINDOW_TOKENS or raw.get("byte_len") != len(raw_bytes) or raw.get("text_sha256") != hashlib.sha256(raw_bytes).hexdigest():
        raise ValueError(f"V4 {split} corpus digest/shape mismatch: {relative_path}")
    return CorpusWindow(dataset, document_id, relative_path, ordinal, text, len(raw_bytes), str(raw.get("source_sha256")), str(raw.get("text_sha256")), len(token_ids), tuple(token_ids))


def _audit_corpus(corpus_root: Path, source_root: Path, raw_root: Path, r1_source_root: Path, model_path: Path, source_manifest_sha256: str, review_sha: str) -> dict[str, Any]:
    root = c.exact_or_staging_path(corpus_root, c.CORPUS_ROOT, "V4 corpus root")
    source = _audit_source(source_root, raw_root, r1_source_root, review_sha)
    if source["manifest_sha256"] != source_manifest_sha256:
        raise ValueError("V4 corpus source binding mismatch")
    model_path = c.exact_path(model_path, c.MODEL_PATH, "model path")
    model_files = c.model_manifest(model_path)
    manifest = _json(root / "manifest.json", "V4 corpus manifest")
    if manifest.get("schema") != c.CORPUS_SCHEMA or manifest.get("state_slice") != c.STATE_SLICE or manifest.get("claim_ceiling") != c.CLAIM_CEILING or manifest.get("source_manifest_sha256") != source_manifest_sha256 or manifest.get("window_token_count") != c.WINDOW_TOKENS or manifest.get("selection_policy") != c.SELECTION_POLICY or manifest.get("fit_window_count") != c.FIT_WINDOW_COUNT or manifest.get("assessment_window_count") != c.ASSESSMENT_WINDOW_COUNT or manifest.get("review_receipt_sha256") != review_sha:
        raise ValueError("V4 corpus manifest contract mismatch")
    for key in ("network_access", "training", "scientific_execution", "evidence_ledger_mutation"):
        if manifest.get(key) is not False:
            raise ValueError(f"V4 corpus flag mismatch: {key}")
    _check_self_digest(manifest, "manifest_sha256", "V4 corpus manifest")
    expected_paths = {f"{split}/fineweb_edu/window-{ordinal:06d}.txt" for split, count in (("fit", c.FIT_WINDOW_COUNT), ("assessment", c.ASSESSMENT_WINDOW_COUNT)) for ordinal in range(count)}
    actual_paths = set()
    for candidate in root.rglob("*"):
        if candidate.is_symlink():
            raise ValueError(f"V4 corpus contains a symlink: {candidate}")
        if candidate.is_file() and candidate.suffix == ".txt":
            actual_paths.add(candidate.relative_to(root).as_posix())
    if actual_paths != expected_paths:
        raise ValueError("V4 corpus text file set mismatch")
    source_maps = {split: {row["document_id"]: row for row in source["records_by_split"][split]} for split in ("fit", "assessment")}
    split_ids: dict[str, set[str]] = {}
    text_sha: dict[str, dict[str, str]] = {}
    tokenizer = None
    if c.native_network_denied() is not True:
        raise RuntimeError("V4 native network denial is not proven")
    with c.network_block():
        tokenizer = _load_tokenizer(model_path)
    for split, count in (("fit", c.FIT_WINDOW_COUNT), ("assessment", c.ASSESSMENT_WINDOW_COUNT)):
        entries = manifest.get(split)
        if not isinstance(entries, list) or len(entries) != count:
            raise ValueError(f"V4 corpus {split} entry count mismatch")
        ids: set[str] = set()
        shas: dict[str, str] = {}
        for ordinal, entry in enumerate(entries):
            if not isinstance(entry, dict) or entry.get("path") != f"{split}/fineweb_edu/window-{ordinal:06d}.txt":
                raise ValueError(f"V4 corpus {split} path mismatch")
            window = parse_window(root, entry, tokenizer, split)
            if window.document_id in ids or window.document_id not in source_maps[split]:
                raise ValueError(f"V4 corpus {split} document/split mismatch")
            source_row = source_maps[split][window.document_id]
            if entry.get("source_row_index") != source_row["source_row_index"] or entry.get("source_path") != source_row["source_path"] or entry.get("source_sha256") != hashlib.sha256(source_row["text"].encode("utf-8")).hexdigest():
                raise ValueError(f"V4 corpus {split} source binding mismatch")
            ids.add(window.document_id)
            shas[window.document_id] = window.text_sha256
        split_ids[split] = ids
        text_sha[split] = shas
    if split_ids["fit"] & split_ids["assessment"]:
        raise ValueError("V4 corpus fit/assessment overlap")
    return {"manifest": manifest, "manifest_sha256": manifest["manifest_sha256"], "source": source, "model_manifest": model_files, "fit_ids": split_ids["fit"], "assessment_ids": split_ids["assessment"], "text_sha": text_sha}


def validate_corpus(corpus_root: Path, source_root: Path, raw_root: Path, r1_source_root: Path, model_path: Path, source_manifest_sha256: str, review_receipt: Path) -> dict[str, Any]:
    validate_review_receipt(review_receipt)
    audit = _audit_corpus(corpus_root, source_root, raw_root, r1_source_root, model_path, source_manifest_sha256, c.sha256_file(review_receipt))
    return {"valid": True, "state_slice": c.STATE_SLICE, "claim_ceiling": c.CLAIM_CEILING, "corpus_manifest_sha256": audit["manifest_sha256"], "fit_window_count": len(audit["fit_ids"]), "assessment_window_count": len(audit["assessment_ids"])}


def implementation_manifest() -> dict[str, Any]:
    files = []
    for path in c.IMPLEMENTATION_FILES:
        path = c.regular(path, "V4 reviewed file")
        files.append({"path": path.relative_to(c.REPO_ROOT).as_posix(), "byte_len": path.stat().st_size, "sha256": c.sha256_file(path)})
    body = {"state_slice": c.STATE_SLICE, "files": files}
    return {"manifest": body, "manifest_sha256": c.digest(body)}


def _reviewed_relative_files() -> list[str]:
    return [path.relative_to(c.REPO_ROOT).as_posix() for path in c.IMPLEMENTATION_FILES]


def validate_review_receipt(path: Path) -> dict[str, Any]:
    receipt = _json(path, "V4 independent review receipt")
    if receipt.get("schema") != c.REVIEW_SCHEMA or receipt.get("state_slice") != c.STATE_SLICE or receipt.get("claim_ceiling") != c.CLAIM_CEILING or receipt.get("protocol_sha256") != c.sha256_file(c.PROTOCOL_PATH) or receipt.get("protocol_sha256") != c.PROTOCOL_SHA256 or receipt.get("review_packet_sha256") != c.sha256_file(c.REVIEW_PACKET_PATH) or receipt.get("implementation_manifest_sha256") != implementation_manifest()["manifest_sha256"]:
        raise ValueError("V4 review binding mismatch")
    if receipt.get("review_status") != "ACCEPT" or receipt.get("effects_run") is not False or receipt.get("reviewed_files") != _reviewed_relative_files() or not isinstance(receipt.get("reviewer"), str) or not receipt["reviewer"]:
        raise ValueError("V4 review identity/status mismatch")
    timestamp = receipt.get("reviewed_at_utc")
    if not isinstance(timestamp, str) or not timestamp.endswith("Z"):
        raise ValueError("V4 review timestamp is not canonical UTC")
    try:
        parsed = dt.datetime.fromisoformat(timestamp[:-1] + "+00:00")
    except ValueError as exc:
        raise ValueError("V4 review timestamp is invalid") from exc
    if parsed.tzinfo != dt.timezone.utc or parsed.isoformat().replace("+00:00", "Z") != timestamp:
        raise ValueError("V4 review timestamp is not canonical UTC")
    findings = receipt.get("findings")
    if not isinstance(findings, dict) or set(findings) != set(c.REVIEW_FINDINGS) or any(findings[key] is not True for key in c.REVIEW_FINDINGS):
        raise ValueError("V4 review findings are incomplete")
    _check_self_digest(receipt, "receipt_digest_sha256", "V4 independent review receipt")
    return receipt


def _finite(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
        raise ValueError(f"{label} must be finite")
    return float(value)


def _validate_metrics(metrics: Any, ids: set[str], text_sha: dict[str, str], label: str, temperature: float, evaluation_config: dict[str, Any] | None) -> dict[str, Any]:
    observed_temperature = metrics.get("temperature") if isinstance(metrics, dict) else None
    if not isinstance(metrics, dict) or isinstance(observed_temperature, bool) or not isinstance(observed_temperature, (int, float)) or observed_temperature != temperature or metrics.get("evaluation_config") != evaluation_config:
        raise ValueError(f"{label} control identity mismatch")
    rows = metrics.get("rows")
    if not isinstance(rows, list) or len(rows) != len(ids):
        raise ValueError(f"{label} row count mismatch")
    seen: set[str] = set()
    total_nll = 0.0
    total_targets = 0
    for row in rows:
        if not isinstance(row, dict) or not isinstance(row.get("document_id"), str) or row["document_id"] not in ids or row["document_id"] in seen or row.get("dataset") != "fineweb_edu" or row.get("window_ordinal") != 0 or row.get("token_count") != c.WINDOW_TOKENS or row.get("target_count") != c.WINDOW_TOKENS - 1 or row.get("text_sha256") != text_sha[row["document_id"]]:
            raise ValueError(f"{label} row identity/shape mismatch")
        nll = _finite(row.get("nll"), f"{label} NLL")
        total_nll += nll
        total_targets += row["target_count"]
        seen.add(row["document_id"])
    if seen != ids or not isinstance(metrics.get("target_tokens"), int) or isinstance(metrics["target_tokens"], bool) or metrics["target_tokens"] != total_targets:
        raise ValueError(f"{label} target token count mismatch")
    expected_mean = round(total_nll / total_targets, 9) if total_targets else float("nan")
    expected_perplexity = round(math.exp(expected_mean), 9) if math.isfinite(expected_mean) else None
    if metrics.get("mean_nll") != expected_mean or metrics.get("perplexity") != expected_perplexity:
        raise ValueError(f"{label} aggregate mismatch")
    return metrics


def _parity_shape(parity: Any, expected_text_sha: dict[str, str]) -> None:
    expected_ids = set(expected_text_sha)
    if not isinstance(parity, dict) or parity.get("sequence_count") != 128 or parity.get("all_passed") is not True or not isinstance(parity.get("checks"), list) or len(parity["checks"]) != 128:
        raise ValueError("V4 parity control shape mismatch")
    seen: set[str] = set()
    maximum = -math.inf
    for check in parity["checks"]:
        if not isinstance(check, dict) or check.get("dataset") != "fineweb_edu" or not isinstance(check.get("document_id"), str) or check["document_id"] not in expected_ids or check["document_id"] in seen or check.get("text_sha256") != expected_text_sha[check["document_id"]] or check.get("token_count") != c.WINDOW_TOKENS or check.get("tolerance") != c.PARITY_TOLERANCE or check.get("passed") is not True:
            raise ValueError("V4 parity check identity mismatch")
        maximum = max(maximum, _finite(check.get("max_abs_logit_delta"), "V4 parity delta"))
        seen.add(check["document_id"])
    if seen != expected_ids or parity.get("max_abs_logit_delta") != maximum:
        raise ValueError("V4 parity aggregate mismatch")


def validate_result(result_root: Path, source_root: Path, corpus_root: Path, raw_root: Path, r1_source_root: Path, model_path: Path, review_receipt: Path, corpus_manifest_sha256: str) -> dict[str, Any]:
    root = c.exact_or_staging_path(result_root, c.RESULT_ROOT, "V4 result root")
    c.reject_tree_symlinks(root, "V4 result root")
    validate_review_receipt(review_receipt)
    review_sha = c.sha256_file(review_receipt)
    source = _audit_source(source_root, raw_root, r1_source_root, review_sha)
    corpus = _audit_corpus(corpus_root, source_root, raw_root, r1_source_root, model_path, source["manifest_sha256"], review_sha)
    if corpus["manifest_sha256"] != corpus_manifest_sha256:
        raise ValueError("V4 result corpus binding mismatch")
    config = _json(root / "config.json", "V4 result config")
    results = _json(root / "results.json", "V4 result body")
    receipt = _json(root / "receipt.json", "V4 result receipt")
    for value, label in ((config, "V4 result config"), (results, "V4 result body"), (receipt, "V4 result receipt")):
        if value.get("schema") != c.RESULT_SCHEMA or value.get("state_slice") != c.STATE_SLICE or value.get("claim_ceiling") != c.CLAIM_CEILING:
            raise ValueError(f"{label} contract mismatch")
    _check_self_digest(config, "config_sha256", "V4 result config")
    _check_self_digest(results, "results_sha256", "V4 result body")
    _check_self_digest(receipt, "receipt_sha256", "V4 result receipt")
    for value, label in ((config, "V4 config"), (results, "V4 results")):
        if value.get("protocol_sha256") != c.PROTOCOL_SHA256 or value.get("review_receipt_sha256") != review_sha or value.get("source_manifest_sha256") != source["manifest_sha256"] or value.get("corpus_manifest_sha256") != corpus_manifest_sha256 or value.get("model_path") != str(c.MODEL_PATH) or value.get("model_manifest_sha256") != c.EXPECTED_MODEL_MANIFEST_SHA256 or value.get("model_type") != "gemma3_text" or value.get("architecture") != "gemma3_text" or value.get("layer_count") != 26 or value.get("runtime") != c.RUNTIME_VERSIONS:
            raise ValueError(f"{label} custody binding mismatch")
    if receipt.get("protocol_sha256") != c.PROTOCOL_SHA256 or receipt.get("review_receipt_sha256") != review_sha or receipt.get("source_manifest_sha256") != source["manifest_sha256"] or receipt.get("corpus_manifest_sha256") != corpus_manifest_sha256 or receipt.get("model_manifest_sha256") != c.EXPECTED_MODEL_MANIFEST_SHA256:
        raise ValueError("V4 receipt custody binding mismatch")
    if receipt.get("config_sha256") != config.get("config_sha256") or receipt.get("results_sha256") != results.get("results_sha256") or receipt.get("zero_alpha_parity_passed") is not True or receipt.get("nonzero_intervention_reach") is not results.get("qualification", {}).get("nonzero_intervention_reach") or receipt.get("deterministic_repeat_passed") is not results.get("deterministic_repeat_passed") or receipt.get("network_access") is not False or receipt.get("training") is not False or receipt.get("weights_frozen") is not True or receipt.get("evidence_ledger_mutation") is not False:
        raise ValueError("V4 result receipt control binding mismatch")
    for value, field, expected in ((config, "network_access", False), (config, "training", False), (config, "weights_frozen", True), (config, "evidence_ledger_mutation", False), (config, "assessment_authorized_by_review", True), (results, "network_access", False), (results, "training", False), (results, "weights_frozen", True), (results, "evidence_ledger_mutation", False), (results, "local_only", True)):
        if value.get(field) is not expected:
            raise ValueError(f"V4 {field} flag mismatch")
    if config.get("candidate_pairs") != [list(pair) for pair in c.CANDIDATE_PAIRS] or config.get("fit_alpha") != c.FIT_ALPHA or config.get("fit_beta") != c.FIT_BETA or config.get("evaluation_alpha") != c.EVALUATION_ALPHA or config.get("evaluation_beta") != c.EVALUATION_BETA or config.get("temperature_control") != c.TEMPERATURE_CONTROL or config.get("normalization") != "source_l2_norm_to_destination_l2_norm" or config.get("controls") != list(c.CONTROL_NAMES):
        raise ValueError("V4 locked configuration mismatch")
    fit_ids = corpus["fit_ids"]
    assessment_ids = corpus["assessment_ids"]
    fit_sha = corpus["text_sha"]["fit"]
    assessment_sha = corpus["text_sha"]["assessment"]
    candidates = results.get("fit_candidates")
    if not isinstance(candidates, list) or len(candidates) != len(c.CANDIDATE_PAIRS):
        raise ValueError("V4 fit candidate count mismatch")
    candidate_means = []
    for candidate, pair in zip(candidates, c.CANDIDATE_PAIRS, strict=True):
        expected_config = {"source_layer": pair[0], "destination_layer": pair[1], "alpha": c.FIT_ALPHA, "beta": c.FIT_BETA, "epsilon": c.EPSILON}
        if not isinstance(candidate, dict) or candidate.get("config") != expected_config:
            raise ValueError("V4 candidate configuration mismatch")
        metrics = _validate_metrics(candidate.get("metrics"), fit_ids, fit_sha, "V4 fit candidate", 1.0, expected_config)
        candidate_means.append((metrics["mean_nll"], pair[0], pair[1]))
    fit_baseline_config = None
    _validate_metrics(results.get("fit_baseline"), fit_ids, fit_sha, "V4 fit baseline", 1.0, fit_baseline_config)
    expected_pair = min(candidate_means)
    selected_config = results.get("selected_fit_config")
    locked_config = results.get("locked_evaluation_config")
    expected_selected = {"source_layer": expected_pair[1], "destination_layer": expected_pair[2], "alpha": c.FIT_ALPHA, "beta": c.FIT_BETA, "epsilon": c.EPSILON}
    expected_locked = {"source_layer": expected_pair[1], "destination_layer": expected_pair[2], "alpha": c.EVALUATION_ALPHA, "beta": c.EVALUATION_BETA, "epsilon": c.EPSILON}
    if selected_config != expected_selected or locked_config != expected_locked or config.get("selected_fit_config") != selected_config or config.get("locked_evaluation_config") != locked_config or results.get("paper_expected_pair") != {"source_layer": 11, "destination_layer": 4} or config.get("paper_expected_pair") != {"source_layer": 11, "destination_layer": 4} or results.get("paper_expected_pair_recovered") != ((selected_config["source_layer"], selected_config["destination_layer"]) == (11, 4)):
        raise ValueError("V4 selected/locked configuration mismatch")
    baseline = _validate_metrics(results.get("assessment_baseline"), assessment_ids, assessment_sha, "V4 assessment baseline", 1.0, None)
    selected = _validate_metrics(results.get("assessment_selected"), assessment_ids, assessment_sha, "V4 assessment selected", 1.0, expected_locked)
    temp_baseline = _validate_metrics(results.get("assessment_temperature_baseline"), assessment_ids, assessment_sha, "V4 temperature baseline", c.TEMPERATURE_CONTROL, None)
    temp_selected = _validate_metrics(results.get("assessment_temperature_selected"), assessment_ids, assessment_sha, "V4 temperature intervention", c.TEMPERATURE_CONTROL, expected_locked)
    repeat = _validate_metrics(results.get("assessment_repeat"), assessment_ids, assessment_sha, "V4 deterministic repeat", 1.0, expected_locked)
    if repeat != selected:
        raise ValueError("V4 deterministic repeat differs from selected assessment")
    _parity_shape(results.get("parity"), {**fit_sha, **assessment_sha})
    if results.get("controls") != {"native_baseline": baseline, "zero_alpha_identity": results.get("parity"), "all_candidate_evaluations": candidates, "temperature_1.20_baseline": temp_baseline, "temperature_1.20_intervention": temp_selected, "deterministic_repeat": repeat, "frozen_model_manifest": {"before": c.EXPECTED_MODEL_MANIFEST_SHA256, "after": c.EXPECTED_MODEL_MANIFEST_SHA256}, "frozen_model_parameters": {"before": results.get("model_parameter_digest_before"), "after": results.get("model_parameter_digest_after")}}:
        raise ValueError("V4 retained control mismatch")
    if not any(candidate["metrics"]["mean_nll"] != results["fit_baseline"]["mean_nll"] for candidate in candidates) or results.get("qualification", {}).get("nonzero_intervention_reach") is not True or results.get("deterministic_repeat_passed") is not True:
        raise ValueError("V4 qualification control mismatch")
    per_document = results.get("assessment_per_document")
    baseline_rows = {row["document_id"]: row for row in baseline["rows"]}
    selected_rows = {row["document_id"]: row for row in selected["rows"]}
    if not isinstance(per_document, list) or len(per_document) != len(assessment_ids):
        raise ValueError("V4 per-document count mismatch")
    deltas = []
    seen: set[str] = set()
    for row in per_document:
        document_id = row.get("document_id")
        if not isinstance(row, dict) or not isinstance(document_id, str) or document_id not in assessment_ids or document_id in seen or row.get("dataset") != "fineweb_edu" or row.get("text_sha256") != assessment_sha[document_id] or row.get("target_count") != c.WINDOW_TOKENS - 1 or row.get("baseline_nll") != baseline_rows[document_id]["nll"] or row.get("selected_nll") != selected_rows[document_id]["nll"]:
            raise ValueError("V4 per-document binding mismatch")
        delta = _finite(row.get("delta_selected_minus_baseline"), "V4 per-document delta")
        expected_delta = baseline_rows[document_id]["nll"] * 0.0 + selected_rows[document_id]["nll"] / (c.WINDOW_TOKENS - 1) - baseline_rows[document_id]["nll"] / (c.WINDOW_TOKENS - 1)
        if delta != expected_delta:
            raise ValueError("V4 per-document delta mismatch")
        deltas.append(delta)
        seen.add(document_id)
    if seen != assessment_ids:
        raise ValueError("V4 per-document set mismatch")
    mean_delta = sum(deltas) / len(deltas)
    bootstrap = c.bootstrap_mean_ci(deltas)
    if results.get("assessment_nll_delta_selected_minus_baseline") != mean_delta or results.get("bootstrap") != bootstrap or results.get("decision") != c.decide_replication(bootstrap) or receipt.get("bootstrap") != bootstrap or receipt.get("decision") != results.get("decision"):
        raise ValueError("V4 uncertainty or decision mismatch")
    for value in (config.get("model_parameter_digest_before"), config.get("model_parameter_digest_after"), results.get("model_parameter_digest_before"), results.get("model_parameter_digest_after"), receipt.get("model_parameter_digest_before"), receipt.get("model_parameter_digest_after")):
        if not isinstance(value, str) or len(value) != 64:
            raise ValueError("V4 parameter digest is missing")
    if config.get("model_parameter_digest_before") != config.get("model_parameter_digest_after") or results.get("model_parameter_digest_before") != results.get("model_parameter_digest_after") or config.get("model_parameter_digest_before") != results.get("model_parameter_digest_before") or receipt.get("model_parameter_digest_before") != results.get("model_parameter_digest_before") or receipt.get("model_parameter_digest_after") != results.get("model_parameter_digest_after"):
        raise ValueError("V4 model parameter custody mismatch")
    current_manifest = c.model_manifest(model_path)
    if current_manifest["manifest_sha256"] != c.EXPECTED_MODEL_MANIFEST_SHA256:
        raise ValueError("V4 model manifest mismatch before independent recomputation")
    if c.native_network_denied() is not True:
        raise RuntimeError("V4 native network denial is not proven")
    from experiments.continual_learning import stage_and_run_gemma3_fineweb_edu_replication_v4 as runner

    with c.network_block():
        model, tokenizer, _runtime = runner.load_runtime(model_path)
        if getattr(model.args, "model_type", None) != "gemma3_text" or len(model.model.layers) != 26:
            raise ValueError("V4 independently loaded model shape/type mismatch")
        if c.model_parameter_digest(model) != results["model_parameter_digest_before"]:
            raise ValueError("V4 independent before-parameter digest mismatch")
        fit_windows, assessment_windows, _ = runner.load_corpus(corpus_root, tokenizer)
        parity = {"sequence_count": 128, "max_abs_logit_delta": 0.0, "tolerance": c.PARITY_TOLERANCE, "all_passed": True, "checks": [runner.parity_check(model, window) for window in (*fit_windows, *assessment_windows)]}
        parity["max_abs_logit_delta"] = max(item["max_abs_logit_delta"] for item in parity["checks"])
        if parity != results["parity"]:
            raise ValueError("V4 independent parity recomputation mismatch")
        recomputed_baseline = runner.evaluate_windows(model, tokenizer, fit_windows, None)
        if recomputed_baseline != results["fit_baseline"]:
            raise ValueError("V4 independent fit baseline mismatch")
        recomputed_candidates = []
        for pair in c.CANDIDATE_PAIRS:
            cfg = runner.RecirculationConfig(pair[0], pair[1], c.FIT_ALPHA, c.FIT_BETA)
            recomputed_candidates.append({"config": cfg.as_dict(), "metrics": runner.evaluate_windows(model, tokenizer, fit_windows, cfg)})
        if recomputed_candidates != candidates:
            raise ValueError("V4 independent fit candidate mismatch")
        recomputed_assessment_baseline = runner.evaluate_windows(model, tokenizer, assessment_windows, None)
        locked = runner.RecirculationConfig(expected_pair[1], expected_pair[2], c.EVALUATION_ALPHA, c.EVALUATION_BETA)
        recomputed_selected = runner.evaluate_windows(model, tokenizer, assessment_windows, locked)
        recomputed_temp_baseline = runner.evaluate_windows(model, tokenizer, assessment_windows, None, temperature=c.TEMPERATURE_CONTROL)
        recomputed_temp_selected = runner.evaluate_windows(model, tokenizer, assessment_windows, locked, temperature=c.TEMPERATURE_CONTROL)
        recomputed_repeat = runner.evaluate_windows(model, tokenizer, assessment_windows, locked)
        if recomputed_assessment_baseline != baseline or recomputed_selected != selected or recomputed_temp_baseline != temp_baseline or recomputed_temp_selected != temp_selected or recomputed_repeat != repeat:
            raise ValueError("V4 independent assessment/control mismatch")
        if c.model_parameter_digest(model) != results["model_parameter_digest_after"] or c.model_manifest(model_path) != current_manifest:
            raise ValueError("V4 independent after-parameter digest mismatch")
    return {"valid": True, "state_slice": c.STATE_SLICE, "claim_ceiling": c.CLAIM_CEILING, "result_root": str(root), "decision": results["decision"], "results_sha256": results["results_sha256"], "bootstrap": bootstrap, "review_receipt_sha256": review_sha}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("source", "corpus", "result"), required=True)
    parser.add_argument("--source-root", type=Path)
    parser.add_argument("--raw-root", type=Path, default=c.RAW_ROOT)
    parser.add_argument("--r1-source-root", type=Path, default=c.R1_SOURCE_ROOT)
    parser.add_argument("--corpus-root", type=Path)
    parser.add_argument("--result-root", type=Path)
    parser.add_argument("--model", type=Path, default=c.MODEL_PATH)
    parser.add_argument("--review-receipt", type=Path)
    parser.add_argument("--source-manifest-sha256")
    parser.add_argument("--corpus-manifest-sha256")
    args = parser.parse_args()
    if args.review_receipt is None:
        parser.error("--review-receipt is required for every V4 validation mode")
    if args.mode == "source":
        if args.source_root is None:
            parser.error("source mode requires --source-root")
        value = validate_source(args.source_root, args.raw_root, args.r1_source_root, args.review_receipt)
    elif args.mode == "corpus":
        if args.source_root is None or args.corpus_root is None or args.source_manifest_sha256 is None:
            parser.error("corpus mode requires source, corpus, and source-manifest bindings")
        value = validate_corpus(args.corpus_root, args.source_root, args.raw_root, args.r1_source_root, args.model, args.source_manifest_sha256, args.review_receipt)
    else:
        if args.source_root is None or args.corpus_root is None or args.result_root is None or args.corpus_manifest_sha256 is None:
            parser.error("result mode requires source, corpus, result, and corpus-manifest bindings")
        value = validate_result(args.result_root, args.source_root, args.corpus_root, args.raw_root, args.r1_source_root, args.model, args.review_receipt, args.corpus_manifest_sha256)
    print(json.dumps(value, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
