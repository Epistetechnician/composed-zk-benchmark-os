#!/usr/bin/env python3
"""Independent fail-closed V10 validator.

State slice: continual-learning-gemma3-fineweb-edu-replication-v10.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator

from experiments.continual_learning import (
    gemma3_fineweb_edu_replication_v10_contract as c,
)


@dataclass(frozen=True)
class Window:
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


def obj(path: Path, label: str) -> dict[str, Any]:
    value = json.loads(c.regular(path, label).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be an object")
    return value


def jsonl(path: Path, label: str) -> list[dict[str, Any]]:
    rows = []
    with c.regular(path, label).open(encoding="utf-8") as handle:
        for number, line in enumerate(handle, 1):
            if not line.strip():
                raise ValueError(f"{label} blank line {number}")
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValueError(f"{label} line {number} is not an object")
            rows.append(value)
    return rows


def self_digest(value: dict[str, Any], field: str, label: str) -> None:
    if (
        not isinstance(value.get(field), str)
        or c.digest({key: item for key, item in value.items() if key != field})
        != value[field]
    ):
        raise ValueError(f"{label} digest mismatch")


def pinned_manifest(path: Path, expected_sha256: str, label: str) -> dict[str, Any]:
    manifest = obj(path, label)
    self_digest(manifest, "manifest_sha256", label)
    if manifest.get("manifest_sha256") != expected_sha256:
        raise ValueError(f"{label} pin mismatch")
    return manifest


def expected_dataset() -> dict[str, Any]:
    return {
        "repo": c.DATASET_REPO,
        "source": c.DATASET_SOURCE,
        "revision": c.DATASET_REVISION,
        "config": c.DATASET_CONFIG,
        "split": c.DATASET_SPLIT,
        "selected_file_count": 2,
        "selected_crawls": [item["crawl"] for item in c.DATASET_FILES],
        "parquet_byte_count": c.DATASET_BYTE_COUNT,
    }


def normalized(
    values: dict[str, list[Any]], item: dict[str, Any], row_index: int, index: int
) -> dict[str, Any]:
    text = values["text"][index]
    if not isinstance(text, str) or not text.strip():
        raise ValueError("FineWeb-Edu text is empty")
    upstream = values.get("id", [None] * len(values["text"]))[index]
    if not isinstance(upstream, str) or not upstream:
        upstream = f"row-{row_index:08d}"
    fields = (
        "id",
        "url",
        "date",
        "dump",
        "file_path",
        "language",
        "language_score",
        "token_count",
        "score",
        "int_score",
    )
    metadata = {
        field: values[field][index]
        for field in fields
        if field in values and values[field][index] is not None
    }
    metadata = {
        field: (
            value.isoformat()
            if hasattr(value, "isoformat")
            else value
            if isinstance(value, (str, int, float, bool))
            else str(value)
        )
        for field, value in metadata.items()
    }
    return {
        "document_id": f"fineweb-edu:{item['crawl']}:{upstream}",
        "text": text,
        "metadata": metadata,
        "source_crawl": item["crawl"],
        "source_path": item["path"],
        "source_row_index": row_index,
    }


def parquet_rows(
    path: Path, item: dict[str, Any], start: int, end: int
) -> Iterator[dict[str, Any]]:
    import pyarrow.parquet as pq

    parquet = pq.ParquetFile(path)
    if "text" not in parquet.schema.names:
        raise ValueError("pinned shard has no text column")
    fields = (
        "id",
        "url",
        "date",
        "dump",
        "file_path",
        "language",
        "language_score",
        "token_count",
        "score",
        "int_score",
    )
    columns = ["text", *[field for field in fields if field in parquet.schema.names]]
    position = selected = 0
    for batch in parquet.iter_batches(columns=columns, batch_size=256):
        values = {name: batch.column(name).to_pylist() for name in columns}
        for offset in range(batch.num_rows):
            if start <= position < end:
                yield normalized(values, item, position, offset)
                selected += 1
            position += 1
            if position >= end:
                break
        if position >= end:
            break
    if selected != end - start:
        raise ValueError(f"expected {end - start} rows, observed {selected}")


def first_eligible_rows(
    rows: list[dict[str, Any]], tokenizer: Any
) -> list[dict[str, Any]]:
    selected = []
    for row in rows:
        token_ids = tokenizer.encode(row["text"], add_special_tokens=False)
        if len(token_ids) >= c.WINDOW_TOKENS:
            selected.append(row)
            if len(selected) == 64:
                return selected
    raise ValueError("source split has fewer than 64 eligible windows")


def audit_raw(root: Path) -> list[dict[str, Any]]:
    root = c.exact_path(root, c.RAW_ROOT, "V10 raw")
    c.exact_file_set(
        root, {f"dataset/{item['path']}" for item in c.DATASET_FILES}, "V10 raw"
    )
    artifacts = []
    import pyarrow.parquet as pq

    for item in c.DATASET_FILES:
        path = c.regular(root / "dataset" / item["path"], "V10 Parquet")
        if (
            path.stat().st_size != item["byte_len"]
            or c.sha256_file(path) != item["sha256"]
        ):
            raise ValueError("V10 raw pin mismatch")
        count = pq.ParquetFile(path).metadata.num_rows
        if count < c.FRESH_ROW_END:
            raise ValueError("V10 raw shard is too short")
        artifacts.append(
            {
                "relative_path": path.relative_to(root).as_posix(),
                "source": f"{c.DATASET_SOURCE}/resolve/{c.DATASET_REVISION}/{item['path']}",
                "crawl": item["crawl"],
                "byte_len": path.stat().st_size,
                "sha256": c.sha256_file(path),
                "row_count": count,
            }
        )
    return artifacts


def audit_prior(root: Path, raw_root: Path) -> set[str]:
    root = c.exact_path(root, c.PRIOR_ROOT, "V10 prior")
    c.exact_file_set(
        root,
        {
            "acquisition-manifest.json",
            "fit/fineweb_edu.jsonl",
            "assessment/fineweb_edu.jsonl",
        },
        "V10 prior",
    )
    manifest_path = root / "acquisition-manifest.json"
    manifest = pinned_manifest(
        manifest_path, c.PRIOR_MANIFEST_SHA256, "prior manifest"
    )
    if (
        manifest.get("schema") != "gemma3-fineweb-edu-bounded-acquisition-v1"
        or manifest.get("dataset") != expected_dataset()
        or manifest.get("selection_policy")
        != "first-2048-records-from-two-pinned-crawls-document-disjoint-v1"
    ):
        raise ValueError("prior contract mismatch")
    datasets, ids = manifest.get("datasets"), set()
    if not isinstance(datasets, dict):
        raise ValueError("prior datasets missing")
    raw = c.exact_path(raw_root, c.RAW_ROOT, "V10 raw")
    for split, item in (
        ("fit", c.DATASET_FILES[0]),
        ("assessment", c.DATASET_FILES[1]),
    ):
        metadata = datasets.get(f"{split}/fineweb_edu")
        expected = {
            "row_start": 0,
            "row_count": 2_048,
            "normalized_path": f"{split}/fineweb_edu.jsonl",
            "crawl": item["crawl"],
            "source_path": item["path"],
            "source": c.DATASET_SOURCE,
            "revision": c.DATASET_REVISION,
            "config": c.DATASET_CONFIG,
            "split": c.DATASET_SPLIT,
        }
        if not isinstance(metadata, dict) or any(
            metadata.get(key) != value for key, value in expected.items()
        ):
            raise ValueError("prior metadata mismatch")
        path = c.safe_relative(root, expected["normalized_path"], "prior JSONL")
        if c.sha256_file(path) != metadata.get("normalized_sha256"):
            raise ValueError("prior JSONL digest mismatch")
        rows = jsonl(path, "prior JSONL")
        if len(rows) != 2_048:
            raise ValueError("prior row count mismatch")
        for ordinal, (observed, recomputed) in enumerate(
            zip(
                rows,
                parquet_rows(raw / "dataset" / item["path"], item, 0, 2_048),
                strict=True,
            )
        ):
            if (
                observed != recomputed
                or not isinstance(observed.get("document_id"), str)
                or observed["document_id"] in ids
                or strict_int(observed.get("source_row_index"), "V10 prior source row")
                != ordinal
            ):
                raise ValueError("prior row identity mismatch")
            ids.add(observed["document_id"])
    return ids


def audit_source(
    root: Path, raw_root: Path, prior_root: Path, review_sha: str
) -> dict[str, Any]:
    root = c.exact_or_staging(root, c.SOURCE_ROOT, "V10 source")
    c.exact_file_set(
        root,
        {
            "acquisition-manifest.json",
            "fit/fineweb_edu.jsonl",
            "assessment/fineweb_edu.jsonl",
        },
        "V10 source",
    )
    manifest = obj(root / "acquisition-manifest.json", "V10 source manifest")
    required = {
        "schema": c.SOURCE_SCHEMA,
        "state_slice": c.STATE_SLICE,
        "claim_ceiling": c.CLAIM_CEILING,
        "source_record_schema": "gemma3-source-v1-compatible-with-fineweb-metadata",
        "selection_policy": "rows-2048-through-18431-two-pinned-crawls-v10",
        "raw_root": str(c.RAW_ROOT),
        "prior_root": str(c.PRIOR_ROOT),
        "prior_manifest_sha256": c.PRIOR_MANIFEST_SHA256,
        "review_receipt_sha256": review_sha,
        "dataset": expected_dataset(),
        "fresh_row_range": {
            "start": c.FRESH_ROW_START,
            "end_exclusive": c.FRESH_ROW_END,
            "count_per_shard": c.FRESH_ROW_COUNT,
        },
        "prior_row_range": {
            "start": 0,
            "end_exclusive": 2_048,
            "count_per_shard": 2_048,
        },
    }
    if any(manifest.get(key) != value for key, value in required.items()) or any(
        manifest.get(key) is not False
        for key in (
            "network_access",
            "training",
            "scientific_execution",
            "evidence_ledger_mutation",
        )
    ):
        raise ValueError("V10 source contract mismatch")
    self_digest(manifest, "manifest_sha256", "V10 source manifest")
    raw = c.exact_path(raw_root, c.RAW_ROOT, "V10 raw")
    prior_ids = audit_prior(prior_root, raw)
    raw_artifacts = audit_raw(raw)
    if (
        manifest.get("raw_artifacts") != raw_artifacts
        or manifest.get("prior_history") != c.validate_prior_history()
    ):
        raise ValueError("V10 source custody mismatch")
    ids, split_rows = set(), {}
    datasets = manifest.get("datasets")
    if not isinstance(datasets, dict):
        raise ValueError("V10 source datasets missing")
    for split, item in (
        ("fit", c.DATASET_FILES[0]),
        ("assessment", c.DATASET_FILES[1]),
    ):
        metadata = datasets.get(f"{split}/fineweb_edu")
        expected = {
            "source": c.DATASET_SOURCE,
            "revision": c.DATASET_REVISION,
            "config": c.DATASET_CONFIG,
            "split": c.DATASET_SPLIT,
            "crawl": item["crawl"],
            "source_path": item["path"],
            "row_start": c.FRESH_ROW_START,
            "row_count": c.FRESH_ROW_COUNT,
            "normalized_path": f"{split}/fineweb_edu.jsonl",
        }
        if not isinstance(metadata, dict) or any(
            metadata.get(key) != value for key, value in expected.items()
        ):
            raise ValueError("V10 source dataset metadata mismatch")
        path = c.safe_relative(root, expected["normalized_path"], "V10 source JSONL")
        if c.sha256_file(path) != metadata.get(
            "normalized_sha256"
        ) or path.stat().st_size != metadata.get("normalized_byte_len"):
            raise ValueError("V10 source JSONL digest mismatch")
        rows = jsonl(path, "V10 source JSONL")
        if len(rows) != c.FRESH_ROW_COUNT:
            raise ValueError("V10 source row count mismatch")
        recomputed_rows = parquet_rows(
            raw / "dataset" / item["path"], item, c.FRESH_ROW_START, c.FRESH_ROW_END
        )
        for ordinal, (row, recomputed) in enumerate(
            zip(rows, recomputed_rows, strict=True)
        ):
            if (
                row != recomputed
                or not isinstance(row.get("document_id"), str)
                or row["document_id"] in ids
                or row["document_id"] in prior_ids
                or strict_int(row.get("source_row_index"), "V10 fresh source row")
                != c.FRESH_ROW_START + ordinal
                or row.get("source_crawl") != item["crawl"]
                or row.get("source_path") != item["path"]
            ):
                raise ValueError("V10 source identity mismatch")
            ids.add(row["document_id"])
        split_rows[split] = rows
    return {
        "manifest": manifest,
        "manifest_sha256": manifest["manifest_sha256"],
        "rows": split_rows,
    }


def parse_window(
    root: Path, entry: dict[str, Any], tokenizer: Any, split: str
) -> Window:
    if (
        entry.get("dataset") != "fineweb_edu"
        or not isinstance(entry.get("document_id"), str)
        or strict_int(entry.get("window_ordinal"), "V10 window ordinal") != 0
        or strict_int(entry.get("token_count"), "V10 window token count")
        != c.WINDOW_TOKENS
    ):
        raise ValueError("V10 window metadata mismatch")
    path = c.safe_relative(root, entry.get("path"), "V10 window")
    raw = path.read_bytes()
    text = raw.decode("utf-8")
    if len(raw) != strict_int(
        entry.get("byte_len"), "V10 window byte length"
    ) or hashlib.sha256(raw).hexdigest() != entry.get("text_sha256"):
        raise ValueError("V10 window bytes mismatch")
    token_ids = tuple(
        int(value) for value in tokenizer.encode(text, add_special_tokens=False)
    )
    if len(token_ids) != c.WINDOW_TOKENS or tokenizer.decode(list(token_ids)) != text:
        raise ValueError("V10 tokenizer window mismatch")
    return Window(
        "fineweb_edu",
        entry["document_id"],
        entry["path"],
        0,
        text,
        len(raw),
        entry["source_sha256"],
        entry["text_sha256"],
        len(token_ids),
        token_ids,
    )


def audit_corpus(
    root: Path,
    source_root: Path,
    raw_root: Path,
    prior_root: Path,
    model_path: Path,
    source_sha: str,
    review_sha: str,
    tokenizer: Any,
) -> dict[str, Any]:
    root = c.exact_or_staging(root, c.CORPUS_ROOT, "V10 corpus")
    expected = {
        "manifest.json",
        *{
            f"{split}/window-{i:06d}.txt"
            for split in ("fit", "assessment")
            for i in range(64)
        },
    }
    c.exact_file_set(root, expected, "V10 corpus")
    source = audit_source(source_root, raw_root, prior_root, review_sha)
    manifest = obj(root / "manifest.json", "V10 corpus manifest")
    required = {
        "schema": c.CORPUS_SCHEMA,
        "state_slice": c.STATE_SLICE,
        "claim_ceiling": c.CLAIM_CEILING,
        "source_manifest_sha256": source_sha,
        "review_receipt_sha256": review_sha,
        "model_path": str(c.MODEL_PATH),
        "model_manifest_sha256": c.MODEL_STABLE_MANIFEST_SHA256,
        "model_cache_manifest_sha256": c.MODEL_CACHE_MANIFEST_SHA256,
        "window_token_count": c.WINDOW_TOKENS,
        "fit_window_count": 64,
        "assessment_window_count": 64,
    }
    if any(manifest.get(key) != value for key, value in required.items()) or any(
        manifest.get(key) is not False
        for key in (
            "network_access",
            "training",
            "scientific_execution",
            "evidence_ledger_mutation",
        )
    ):
        raise ValueError("V10 corpus contract mismatch")
    self_digest(manifest, "manifest_sha256", "V10 corpus manifest")
    model = c.model_manifest(model_path)
    if (
        model["manifest_sha256"] != c.MODEL_STABLE_MANIFEST_SHA256
        or model["cache_manifest_sha256"] != c.MODEL_CACHE_MANIFEST_SHA256
    ):
        raise ValueError("V10 model pin mismatch")
    by_id = {
        row["document_id"]: row for rows in source["rows"].values() for row in rows
    }
    windows = {}
    for split in ("fit", "assessment"):
        entries = manifest.get(f"{split}_windows")
        if not isinstance(entries, list) or len(entries) != 64:
            raise ValueError("V10 corpus window count mismatch")
        expected_rows = first_eligible_rows(source["rows"][split], tokenizer)
        if [entry.get("document_id") for entry in entries] != [
            row["document_id"] for row in expected_rows
        ] or [
            strict_int(entry.get("source_row_index"), "V10 corpus source row")
            for entry in entries
        ] != [
            strict_int(row.get("source_row_index"), "V10 source row")
            for row in expected_rows
        ]:
            raise ValueError("V10 corpus is not the first eligible source sequence")
        parsed = []
        for entry in entries:
            window = parse_window(root, entry, tokenizer, split)
            source_row = by_id.get(window.document_id)
            if (
                source_row is None
                or hashlib.sha256(source_row["text"].encode()).hexdigest()
                != window.source_sha256
                or strict_int(entry.get("source_row_index"), "V10 corpus source row")
                != strict_int(source_row["source_row_index"], "V10 source row")
            ):
                raise ValueError("V10 corpus source binding mismatch")
            parsed.append(window)
        windows[split] = parsed
    if set(w.document_id for w in windows["fit"]) & set(
        w.document_id for w in windows["assessment"]
    ):
        raise ValueError("V10 fit/assessment overlap")
    return {
        "manifest": manifest,
        "manifest_sha256": manifest["manifest_sha256"],
        "windows": windows,
    }


def finite(value: Any, label: str) -> float:
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(float(value))
    ):
        raise ValueError(f"{label} must be finite number")
    return float(value)


def strict_int(value: Any, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{label} must be integer")
    return value


def metrics(
    value: Any,
    windows: list[Window],
    label: str,
    temperature: float,
    config: dict[str, Any] | None,
) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{label} configuration mismatch")
    if (
        finite(value.get("temperature"), f"{label} temperature") != float(temperature)
        or value.get("evaluation_config") != config
    ):
        raise ValueError(f"{label} configuration mismatch")
    rows = value.get("rows")
    if not isinstance(rows, list) or len(rows) != len(windows):
        raise ValueError(f"{label} rows mismatch")
    expected_ids = {window.document_id for window in windows}
    seen = set()
    by_id = {window.document_id: window for window in windows}
    for row in rows:
        if (
            not isinstance(row, dict)
            or row.get("document_id") not in expected_ids
            or row["document_id"] in seen
            or row.get("dataset") != "fineweb_edu"
            or strict_int(row.get("window_ordinal"), f"{label} ordinal") != 0
            or strict_int(row.get("token_count"), f"{label} tokens") != c.WINDOW_TOKENS
            or strict_int(row.get("target_count"), f"{label} targets")
            != c.WINDOW_TOKENS - 1
        ):
            raise ValueError(f"{label} row identity mismatch")
        window = by_id[row["document_id"]]
        if (
            row.get("relative_path") != window.relative_path
            or row.get("source_sha256") != window.source_sha256
            or row.get("text_sha256") != window.text_sha256
        ):
            raise ValueError(f"{label} provenance mismatch")
        finite(row.get("nll"), f"{label} nll")
        seen.add(row["document_id"])
    if seen != expected_ids or strict_int(
        value.get("target_tokens"), f"{label} target tokens"
    ) != len(windows) * (c.WINDOW_TOKENS - 1):
        raise ValueError(f"{label} row set mismatch")
    finite(value.get("mean_nll"), f"{label} mean")
    finite(value.get("perplexity"), f"{label} perplexity")
    if value["mean_nll"] != round(
        sum(row["nll"] for row in rows) / value["target_tokens"], 9
    ) or value["perplexity"] != round(math.exp(value["mean_nll"]), 9):
        raise ValueError(f"{label} aggregate mismatch")
    return value


def parity(value: Any, windows: list[Window]) -> dict[str, Any]:
    if (
        not isinstance(value, dict)
        or value.get("sequence_count") != len(windows)
        or value.get("tolerance") != c.PARITY_TOLERANCE
        or value.get("all_passed") is not True
    ):
        raise ValueError("V10 parity summary mismatch")
    checks, seen = value.get("checks"), set()
    if not isinstance(checks, list) or len(checks) != len(windows):
        raise ValueError("V10 parity checks mismatch")
    by_id = {window.document_id: window for window in windows}
    for check in checks:
        if (
            not isinstance(check, dict)
            or check.get("document_id") not in by_id
            or check["document_id"] in seen
            or check.get("dataset") != "fineweb_edu"
            or check.get("relative_path") != by_id[check["document_id"]].relative_path
            or check.get("source_sha256") != by_id[check["document_id"]].source_sha256
            or check.get("text_sha256") != by_id[check["document_id"]].text_sha256
            or check.get("passed") is not True
            or strict_int(check.get("token_count"), "V10 parity tokens")
            != c.WINDOW_TOKENS
            or check.get("tolerance") != c.PARITY_TOLERANCE
        ):
            raise ValueError("V10 parity identity mismatch")
        finite(check.get("max_abs_logit_delta"), "V10 parity delta")
        seen.add(check["document_id"])
    if seen != set(by_id) or finite(
        value.get("max_abs_logit_delta"), "V10 parity maximum"
    ) != max(check["max_abs_logit_delta"] for check in checks):
        raise ValueError("V10 parity aggregate mismatch")
    return value


def input_snapshot(
    source: Path, corpus: Path | None, raw: Path, prior: Path, model: Path
) -> dict[str, Any]:
    result = {
        "source": c.snapshot_files(
            c.exact_path(source, c.SOURCE_ROOT, "V10 source"),
            {
                "acquisition-manifest.json",
                "fit/fineweb_edu.jsonl",
                "assessment/fineweb_edu.jsonl",
            },
            "V10 source",
        ),
        "raw": c.snapshot_files(
            c.exact_path(raw, c.RAW_ROOT, "V10 raw"),
            {f"dataset/{item['path']}" for item in c.DATASET_FILES},
            "V10 raw",
        ),
        "prior": c.snapshot_files(
            c.exact_path(prior, c.PRIOR_ROOT, "V10 prior"),
            {
                "acquisition-manifest.json",
                "fit/fineweb_edu.jsonl",
                "assessment/fineweb_edu.jsonl",
            },
            "V10 prior",
        ),
        "model": c.model_manifest(c.exact_path(model, c.MODEL_PATH, "model path")),
    }
    if corpus is not None:
        result["corpus"] = c.snapshot_files(
            c.exact_path(corpus, c.CORPUS_ROOT, "V10 corpus"),
            {
                "manifest.json",
                *{
                    f"{split}/window-{i:06d}.txt"
                    for split in ("fit", "assessment")
                    for i in range(64)
                },
            },
            "V10 corpus",
        )
    return result


def validate_source(
    source_root: Path, raw_root: Path, prior_root: Path, receipt: Path
) -> dict[str, Any]:
    review = c.validate_review_receipt(receipt)
    return audit_source(
        source_root,
        raw_root,
        prior_root,
        c.sha256_file(c.exact_path(receipt, c.RECEIPT_PATH, "V10 receipt")),
    ) | {
        "review_receipt_sha256": c.sha256_file(
            c.exact_path(receipt, c.RECEIPT_PATH, "V10 receipt")
        ),
        "reviewer": review["reviewer"],
    }


def validate_corpus(
    corpus_root: Path,
    source_root: Path,
    raw_root: Path,
    prior_root: Path,
    model_path: Path,
    source_sha: str,
    receipt: Path,
    tokenizer: Any,
) -> dict[str, Any]:
    c.validate_review_receipt(receipt)
    return audit_corpus(
        corpus_root,
        source_root,
        raw_root,
        prior_root,
        model_path,
        source_sha,
        c.sha256_file(c.exact_path(receipt, c.RECEIPT_PATH, "V10 receipt")),
        tokenizer,
    )


def common(
    value: dict[str, Any], label: str, review_sha: str, source_sha: str, corpus_sha: str
) -> None:
    expected = {
        "schema": c.RESULT_SCHEMA,
        "state_slice": c.STATE_SLICE,
        "claim_ceiling": c.CLAIM_CEILING,
        "protocol_sha256": c.PROTOCOL_SHA256,
        "review_receipt_sha256": review_sha,
        "source_manifest_sha256": source_sha,
        "corpus_manifest_sha256": corpus_sha,
        "model_path": str(c.MODEL_PATH),
        "model_manifest_sha256": c.MODEL_STABLE_MANIFEST_SHA256,
        "model_cache_manifest_sha256": c.MODEL_CACHE_MANIFEST_SHA256,
        "model_type": "gemma3_text",
        "architecture": "gemma3_text",
        "layer_count": 26,
        "runtime": c.RUNTIME_VERSIONS,
    }
    if any(
        value.get(key) != expected_value for key, expected_value in expected.items()
    ):
        raise ValueError(f"{label} common binding mismatch")


def validate_result(
    result_root: Path,
    source_root: Path,
    corpus_root: Path,
    raw_root: Path,
    prior_root: Path,
    model_path: Path,
    receipt: Path,
    corpus_sha: str,
    invocation_snapshot_sha: str,
) -> dict[str, Any]:
    root = c.exact_or_staging(result_root, c.RESULT_ROOT, "V10 result")
    expected_files = {
        "config.json",
        "results.json",
        "receipt.json",
        "corpus-manifest.json",
        "model-manifest.json",
        "review-receipt.json",
        "validator-receipt.json",
    }
    c.exact_file_set(root, expected_files, "V10 result")
    review = c.validate_review_receipt(receipt)
    review_path = c.exact_path(receipt, c.RECEIPT_PATH, "V10 receipt")
    review_sha = c.sha256_file(review_path)
    code_snapshot = c.snapshot_code()
    current_input = input_snapshot(
        source_root, corpus_root, raw_root, prior_root, model_path
    )
    if c.digest(current_input) != invocation_snapshot_sha:
        raise ValueError("V10 invocation input snapshot mismatch")
    staged = c.regular(root / "review-receipt.json", "V10 staged receipt")
    if staged.read_bytes() != review_path.read_bytes():
        raise ValueError("V10 staged review receipt mismatch")
    source = audit_source(source_root, raw_root, prior_root, review_sha)
    corpus = audit_corpus(
        corpus_root,
        source_root,
        raw_root,
        prior_root,
        model_path,
        source["manifest_sha256"],
        review_sha,
        _tokenizer_for_validation(model_path),
    )
    if (
        corpus["manifest_sha256"] != corpus_sha
        or (root / "corpus-manifest.json").read_bytes()
        != (corpus_root / "manifest.json").read_bytes()
    ):
        raise ValueError("V10 corpus result binding mismatch")
    model = obj(root / "model-manifest.json", "V10 result model manifest")
    current_model = c.model_manifest(model_path)
    if (
        model != current_model
        or model["manifest_sha256"] != c.MODEL_STABLE_MANIFEST_SHA256
        or model["cache_manifest_sha256"] != c.MODEL_CACHE_MANIFEST_SHA256
    ):
        raise ValueError("V10 model result binding mismatch")
    config, results, result_receipt, validator_receipt = (
        obj(root / name, f"V10 {name}")
        for name in (
            "config.json",
            "results.json",
            "receipt.json",
            "validator-receipt.json",
        )
    )
    for value, field, label in (
        (config, "config_sha256", "V10 config"),
        (results, "results_sha256", "V10 results"),
        (result_receipt, "receipt_sha256", "V10 result receipt"),
        (validator_receipt, "receipt_sha256", "V10 validator receipt"),
    ):
        self_digest(value, field, label)
    for value, label in (
        (config, "V10 config"),
        (results, "V10 results"),
        (result_receipt, "V10 result receipt"),
    ):
        common(value, label, review_sha, source["manifest_sha256"], corpus_sha)
    if (
        validator_receipt.get("schema")
        != "gemma3-fineweb-edu-replication-v10-validator-receipt"
        or validator_receipt.get("state_slice") != c.STATE_SLICE
        or validator_receipt.get("result_sha256") != results["results_sha256"]
        or validator_receipt.get("review_receipt_sha256") != review_sha
        or validator_receipt.get("independent_recomputation") is not True
    ):
        raise ValueError("V10 validator receipt mismatch")
    if (
        result_receipt.get("config_sha256") != config["config_sha256"]
        or result_receipt.get("results_sha256") != results["results_sha256"]
        or result_receipt.get("deterministic_repeat_passed") is not True
    ):
        raise ValueError("V10 result receipt cross-binding mismatch")
    if any(
        value.get(field) is not expected
        for value, field, expected in (
            (config, "network_access", False),
            (config, "training", False),
            (config, "weights_frozen", True),
            (config, "assessment_authorized_by_review", True),
            (results, "network_access", False),
            (results, "training", False),
            (results, "evidence_ledger_mutation", False),
            (results, "weights_frozen", True),
            (results, "local_only", True),
            (result_receipt, "zero_alpha_parity_passed", True),
            (result_receipt, "network_access", False),
            (result_receipt, "training", False),
            (result_receipt, "evidence_ledger_mutation", False),
            (result_receipt, "weights_frozen", True),
        )
    ):
        raise ValueError("V10 result flags mismatch")
    locked_constants = {
        "candidate_pairs": [list(pair) for pair in c.CANDIDATE_PAIRS],
        "fit_alpha": c.FIT_ALPHA,
        "fit_beta": c.FIT_BETA,
        "evaluation_alpha": c.EVALUATION_ALPHA,
        "evaluation_beta": c.EVALUATION_BETA,
        "temperature_control": c.TEMPERATURE_CONTROL,
        "controls": list(c.CONTROL_NAMES),
    }
    if any(
        config.get(key) != value for key, value in locked_constants.items()
    ) or config.get("paper_expected_pair") != {
        "source_layer": 11,
        "destination_layer": 4,
    }:
        raise ValueError("V10 locked configuration mismatch")
    windows = corpus["windows"]
    fit_base = metrics(
        results.get("fit_baseline"), windows["fit"], "V10 fit baseline", 1.0, None
    )
    candidates = results.get("fit_candidates")
    if not isinstance(candidates, list) or len(candidates) != len(c.CANDIDATE_PAIRS):
        raise ValueError("V10 candidate set mismatch")
    candidate_means = []
    for candidate, pair in zip(candidates, c.CANDIDATE_PAIRS, strict=True):
        cfg = {
            "source_layer": pair[0],
            "destination_layer": pair[1],
            "alpha": c.FIT_ALPHA,
            "beta": c.FIT_BETA,
            "epsilon": c.EPSILON,
        }
        if not isinstance(candidate, dict) or candidate.get("config") != cfg:
            raise ValueError("V10 candidate config mismatch")
        candidate_means.append(
            (
                metrics(
                    candidate.get("metrics"), windows["fit"], "V10 candidate", 1.0, cfg
                )["mean_nll"],
                pair[0],
                pair[1],
            )
        )
    selected_tuple = min(candidate_means)
    selected_fit = {
        "source_layer": selected_tuple[1],
        "destination_layer": selected_tuple[2],
        "alpha": c.FIT_ALPHA,
        "beta": c.FIT_BETA,
        "epsilon": c.EPSILON,
    }
    locked = {**selected_fit, "alpha": c.EVALUATION_ALPHA, "beta": c.EVALUATION_BETA}
    if (
        results.get("selected_fit_config") != selected_fit
        or results.get("locked_evaluation_config") != locked
        or config.get("selected_fit_config") != selected_fit
        or config.get("locked_evaluation_config") != locked
        or results.get("paper_expected_pair")
        != {"source_layer": 11, "destination_layer": 4}
        or results.get("paper_expected_pair_recovered")
        != (
            (selected_fit["source_layer"], selected_fit["destination_layer"]) == (11, 4)
        )
        or config.get("paper_expected_pair_recovered")
        != (
            (selected_fit["source_layer"], selected_fit["destination_layer"]) == (11, 4)
        )
    ):
        raise ValueError("V10 selection mismatch")
    assessment_base = metrics(
        results.get("assessment_baseline"),
        windows["assessment"],
        "V10 assessment baseline",
        1.0,
        None,
    )
    selected = metrics(
        results.get("assessment_selected"),
        windows["assessment"],
        "V10 assessment selected",
        1.0,
        locked,
    )
    temp_base = metrics(
        results.get("assessment_temperature_baseline"),
        windows["assessment"],
        "V10 temperature baseline",
        c.TEMPERATURE_CONTROL,
        None,
    )
    temp_selected = metrics(
        results.get("assessment_temperature_selected"),
        windows["assessment"],
        "V10 temperature selected",
        c.TEMPERATURE_CONTROL,
        locked,
    )
    repeat = metrics(
        results.get("assessment_repeat"),
        windows["assessment"],
        "V10 repeat",
        1.0,
        locked,
    )
    if repeat != selected or results.get("deterministic_repeat_passed") is not True:
        raise ValueError("V10 repeat mismatch")
    parity_value = parity(
        results.get("parity"), [*windows["fit"], *windows["assessment"]]
    )
    baseline_rows = {row["document_id"]: row for row in assessment_base["rows"]}
    selected_rows = {row["document_id"]: row for row in selected["rows"]}
    per_document = results.get("assessment_per_document")
    if not isinstance(per_document, list) or len(per_document) != len(
        windows["assessment"]
    ):
        raise ValueError("V10 per-document count mismatch")
    deltas, seen = [], set()
    by_id = {window.document_id: window for window in windows["assessment"]}
    for row in per_document:
        if (
            not isinstance(row, dict)
            or row.get("document_id") not in by_id
            or row["document_id"] in seen
            or row.get("dataset") != "assessment"
            or row.get("relative_path") != by_id[row["document_id"]].relative_path
            or row.get("source_sha256") != by_id[row["document_id"]].source_sha256
            or row.get("text_sha256") != by_id[row["document_id"]].text_sha256
            or strict_int(row.get("window_ordinal"), "V10 retained window ordinal") != 0
            or strict_int(row.get("token_count"), "V10 retained token count")
            != c.WINDOW_TOKENS
            or strict_int(row.get("target_count"), "V10 retained targets")
            != c.WINDOW_TOKENS - 1
        ):
            raise ValueError("V10 per-document identity mismatch")
        document_id = row["document_id"]
        expected_delta = selected_rows[document_id]["nll"] / (
            c.WINDOW_TOKENS - 1
        ) - baseline_rows[document_id]["nll"] / (c.WINDOW_TOKENS - 1)
        if (
            row.get("baseline_nll") != baseline_rows[document_id]["nll"]
            or row.get("selected_nll") != selected_rows[document_id]["nll"]
            or row.get("delta_selected_minus_baseline") != expected_delta
        ):
            raise ValueError("V10 per-document metric mismatch")
        finite(row.get("baseline_nll"), "V10 retained baseline NLL")
        finite(row.get("selected_nll"), "V10 retained selected NLL")
        finite(row["delta_selected_minus_baseline"], "V10 delta")
        deltas.append(row["delta_selected_minus_baseline"])
        seen.add(document_id)
    if seen != set(by_id):
        raise ValueError("V10 per-document set mismatch")
    bootstrap = c.bootstrap_mean_ci(deltas)
    decision = c.decide_replication(bootstrap)
    if (
        results.get("bootstrap") != bootstrap
        or results.get("assessment_nll_delta_selected_minus_baseline")
        != bootstrap["mean_delta"]
        or results.get("decision") != decision
        or result_receipt.get("bootstrap") != bootstrap
        or result_receipt.get("decision") != decision
    ):
        raise ValueError("V10 uncertainty mismatch")
    reach_evidence = []
    base_by_id = {row["document_id"]: row for row in fit_base["rows"]}
    for candidate, pair in zip(candidates, c.CANDIDATE_PAIRS, strict=True):
        candidate_rows = {
            row["document_id"]: row for row in candidate["metrics"]["rows"]
        }
        maximum = max(
            abs(candidate_rows[key]["nll"] - base_by_id[key]["nll"])
            for key in base_by_id
        )
        reach_evidence.append(
            {
                "source_layer": pair[0],
                "destination_layer": pair[1],
                "max_abs_fit_nll_delta": maximum,
                "reached": maximum != 0.0,
            }
        )
    reached = any(item["reached"] for item in reach_evidence)
    if (
        results.get("qualification")
        != {"nonzero_intervention_reach": reached, "reach_evidence": reach_evidence}
        or result_receipt.get("nonzero_intervention_reach") is not reached
    ):
        raise ValueError("V10 reach was not independently derived")
    if results.get("controls") != {
        "native_baseline": assessment_base,
        "zero_alpha_identity": parity_value,
        "all_candidate_evaluations": candidates,
        "temperature_1.20_baseline": temp_base,
        "temperature_1.20_intervention": temp_selected,
        "deterministic_repeat": repeat,
        "frozen_model_manifest": {
            "before": c.MODEL_STABLE_MANIFEST_SHA256,
            "after": c.MODEL_STABLE_MANIFEST_SHA256,
        },
        "frozen_model_parameters": {
            "before": results.get("model_parameter_digest_before"),
            "after": results.get("model_parameter_digest_after"),
        },
    }:
        raise ValueError("V10 controls mismatch")
    for field in ("model_parameter_digest_before", "model_parameter_digest_after"):
        if (
            not isinstance(results.get(field), str)
            or len(results[field]) != 64
            or config.get(field) != results[field]
            or result_receipt.get(field) != results[field]
        ):
            raise ValueError("V10 parameter binding mismatch")
    if (
        results["model_parameter_digest_before"]
        != results["model_parameter_digest_after"]
    ):
        raise ValueError("V10 model parameters changed")
    c.require_native_network_denial()
    from experiments.continual_learning import (
        stage_and_run_gemma3_fineweb_edu_replication_v10 as runner,
    )

    if c.model_manifest(model_path) != current_model:
        raise ValueError("V10 model changed before independent recomputation")
    with c.network_block():
        model_value, tokenizer_value, runtime_value = runner.load_runtime(model_path)
        if (
            getattr(model_value.args, "model_type", None) != "gemma3_text"
            or len(model_value.model.layers) != 26
            or runtime_value != c.RUNTIME_VERSIONS
        ):
            raise ValueError("V10 independent model shape/runtime mismatch")
        if (
            c.model_parameter_digest(model_value)
            != results["model_parameter_digest_before"]
        ):
            raise ValueError("V10 independent parameter-before mismatch")
        recomputed_corpus = audit_corpus(
            corpus_root,
            source_root,
            raw_root,
            prior_root,
            model_path,
            source["manifest_sha256"],
            review_sha,
            tokenizer_value,
        )
        fit_windows = recomputed_corpus["windows"]["fit"]
        assessment_windows = recomputed_corpus["windows"]["assessment"]
        if (
            runner.parity(model_value, [*fit_windows, *assessment_windows])
            != parity_value
        ):
            raise ValueError("V10 independent parity mismatch")
        if (
            runner.evaluate_windows(model_value, tokenizer_value, fit_windows, None)
            != fit_base
        ):
            raise ValueError("V10 independent fit baseline mismatch")
        recomputed_candidates = []
        for source_layer, destination_layer in c.CANDIDATE_PAIRS:
            candidate_config = runner.RecirculationConfig(
                source_layer, destination_layer, c.FIT_ALPHA, c.FIT_BETA
            )
            recomputed_candidates.append(
                {
                    "config": candidate_config.as_dict(),
                    "metrics": runner.evaluate_windows(
                        model_value, tokenizer_value, fit_windows, candidate_config
                    ),
                }
            )
        if recomputed_candidates != candidates:
            raise ValueError("V10 independent candidate mismatch")
        recomputed_base = runner.evaluate_windows(
            model_value, tokenizer_value, assessment_windows, None
        )
        locked_runner = runner.RecirculationConfig(
            selected_fit["source_layer"],
            selected_fit["destination_layer"],
            c.EVALUATION_ALPHA,
            c.EVALUATION_BETA,
        )
        recomputed_selected = runner.evaluate_windows(
            model_value, tokenizer_value, assessment_windows, locked_runner
        )
        recomputed_temp_base = runner.evaluate_windows(
            model_value,
            tokenizer_value,
            assessment_windows,
            None,
            c.TEMPERATURE_CONTROL,
        )
        recomputed_temp_selected = runner.evaluate_windows(
            model_value,
            tokenizer_value,
            assessment_windows,
            locked_runner,
            c.TEMPERATURE_CONTROL,
        )
        recomputed_repeat = runner.evaluate_windows(
            model_value, tokenizer_value, assessment_windows, locked_runner
        )
        if (
            recomputed_base != assessment_base
            or recomputed_selected != selected
            or recomputed_temp_base != temp_base
            or recomputed_temp_selected != temp_selected
            or recomputed_repeat != repeat
        ):
            raise ValueError("V10 independent assessment/control mismatch")
        if (
            c.model_parameter_digest(model_value)
            != results["model_parameter_digest_after"]
            or c.model_manifest(model_path) != current_model
        ):
            raise ValueError("V10 independent model custody-after mismatch")
    if (
        input_snapshot(source_root, corpus_root, raw_root, prior_root, model_path)
        != current_input
    ):
        raise ValueError("V10 inputs changed during independent recomputation")
    c.assert_code_snapshot(code_snapshot)
    return {
        "valid": True,
        "state_slice": c.STATE_SLICE,
        "claim_ceiling": c.CLAIM_CEILING,
        "result_root": str(root),
        "decision": decision,
        "results_sha256": results["results_sha256"],
        "bootstrap": bootstrap,
        "review_receipt_sha256": review_sha,
        "reviewer": review["reviewer"],
    }


def _tokenizer_for_validation(model_path: Path) -> Any:
    c.require_native_network_denial()
    model = c.exact_path(model_path, c.MODEL_PATH, "model path")
    manifest = c.model_manifest(model)
    if (
        manifest["manifest_sha256"] != c.MODEL_STABLE_MANIFEST_SHA256
        or manifest["cache_manifest_sha256"] != c.MODEL_CACHE_MANIFEST_SHA256
        or c.runtime_versions() != c.RUNTIME_VERSIONS
    ):
        raise RuntimeError("V10 tokenizer custody/runtime mismatch")
    from mlx_lm.utils import load_tokenizer

    with c.network_block():
        return load_tokenizer(str(model))


def main() -> int:
    c.require_native_network_denial()
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
    parser.add_argument("--invocation-snapshot-sha256")
    args = parser.parse_args()
    if args.mode == "source":
        value = validate_source(
            args.source_root, args.raw_root, args.prior_root, args.review_receipt
        )
    elif args.mode == "corpus":
        value = validate_corpus(
            args.corpus_root,
            args.source_root,
            args.raw_root,
            args.prior_root,
            args.model,
            args.source_manifest_sha256,
            args.review_receipt,
            _tokenizer_for_validation(args.model),
        )
    else:
        value = validate_result(
            args.result_root,
            args.source_root,
            args.corpus_root,
            args.raw_root,
            args.prior_root,
            args.model,
            args.review_receipt,
            args.corpus_manifest_sha256,
            args.invocation_snapshot_sha256,
        )
    print(json.dumps(value, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
