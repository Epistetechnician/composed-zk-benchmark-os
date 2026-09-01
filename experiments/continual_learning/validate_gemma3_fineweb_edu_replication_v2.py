#!/usr/bin/env python3
"""Independent validator for Gemma3 FineWeb-Edu replication V2.

State slice: continual-learning-gemma3-fineweb-edu-replication-v2.

This validator is read-only. It never downloads, loads a model, performs a
forward pass, trains, mutates the Evidence Ledger, or publishes a result.
The V2 source validator re-derives normalized records from the pinned raw
Parquet rows, and the result validator re-derives the exact counter-hash
bootstrap interval.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path
from typing import Any, Iterable, Iterator

REPO_ROOT = Path(__file__).resolve().parents[2]
PRIMARY_VOLUME = Path("/Volumes/PrimaryED")
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

STATE_SLICE = "continual-learning-gemma3-fineweb-edu-replication-v2"
CLAIM_CEILING = "LocalDevelopmentGemma3FineWebEduReplicationV2"
SOURCE_SCHEMA = "gemma3-fineweb-edu-replication-v2-source"
CORPUS_SCHEMA = "gemma3-fineweb-edu-replication-v2-corpus"
RESULT_SCHEMA = "gemma3-fineweb-edu-replication-v2-result"
REVIEW_SCHEMA = "gemma3-fineweb-edu-replication-v2-independent-review"
PROTOCOL_SHA256 = "580d3890668303e870184e910e0c0cd2098ddb6064b89da565385489e7e71564"
REVIEW_PACKET_PATH = REPO_ROOT / "docs/research/continual-learning/147-gemma3-fineweb-edu-replication-v2-review-packet.md"
PROTOCOL_PATH = REPO_ROOT / "docs/research/continual-learning/146-gemma3-fineweb-edu-replication-v2-protocol.md"
DATASET_REPO = "HuggingFaceFW/fineweb-edu"
DATASET_REVISION = "87f09149ef4734204d70ed1d046ddc9ca3f2b8f9"
DATASET_SOURCE = f"https://huggingface.co/datasets/{DATASET_REPO}"
DATASET_CONFIG = "fineweb-edu-crawl-shards"
DATASET_SPLIT = "train"
DATASET_FILES = (
    {
        "crawl": "CC-MAIN-2013-20",
        "path": "data/CC-MAIN-2013-20/train-00000-of-00014.parquet",
        "byte_len": 2_369_456_837,
        "sha256": "fb989c566f6fba00ab61decc5f7aa1538a07d9b142e58a52ff790154528ffd03",
    },
    {
        "crawl": "CC-MAIN-2024-10",
        "path": "data/CC-MAIN-2024-10/000_00000.parquet",
        "byte_len": 1_911_528_585,
        "sha256": "89c802096c8adb54cdcfad567c13838814d83dbb4dbcda008a0f740e73f8a484",
    },
)
DATASET_BYTE_COUNT = sum(item["byte_len"] for item in DATASET_FILES)
R1_SOURCE_ROOT = Path("/Volumes/PrimaryED/ResearchArtifacts/composed-zk-benchmark-os/gemma3-fineweb-edu-bounded-source-v1")
R1_SOURCE_MANIFEST_SHA256 = "9e6311b8a88b879c2b8d102cc1b1d4093312c796633571d00c928738327b33d3"
R1_ROW_START = 0
R1_ROW_COUNT = 2048
FRESH_ROW_START = 2048
FRESH_ROW_COUNT = 16_384
FRESH_ROW_END = FRESH_ROW_START + FRESH_ROW_COUNT
WINDOW_TOKENS = 1024
FIT_WINDOW_COUNT = 64
ASSESSMENT_WINDOW_COUNT = 64
FIT_ALPHA = 0.10
EVALUATION_ALPHA = 0.15
EVALUATION_BETA = 0.85
TEMPERATURE_CONTROL = 1.20
CANDIDATE_PAIRS = ((7, 2), (9, 3), (11, 4), (12, 5))
EXPECTED_MODEL_MANIFEST_SHA256 = "69f078b42d4521d3e53f0c388a20fa6cf32b4df7ea6535b0eb9da6ccef75c256"
PARITY_TOLERANCE = 1e-5
BOOTSTRAP_RESAMPLES = 10_000
BOOTSTRAP_SEED = 20260829
BOOTSTRAP_CONFIDENCE = 0.95
BOOTSTRAP_PRNG = "sha256-counter-v1"
BOOTSTRAP_STATISTIC = "mean paired per-document NLL delta selected_minus_baseline"
BOOTSTRAP_PERCENTILE = "nearest-rank-1-indexed"
BOOTSTRAP_NONFINITE = "reject"
IMPLEMENTATION_FILES = (
    PROTOCOL_PATH,
    REVIEW_PACKET_PATH,
    REPO_ROOT / "experiments/continual_learning/prepare_gemma3_fineweb_edu_replication_v2.py",
    REPO_ROOT / "experiments/continual_learning/validate_gemma3_fineweb_edu_replication_v2.py",
    REPO_ROOT / "experiments/continual_learning/stage_and_run_gemma3_fineweb_edu_replication_v2.py",
    REPO_ROOT / "experiments/continual_learning/tests/test_gemma3_fineweb_edu_replication_v2.py",
)
REVIEW_FINDINGS = (
    "custody_exact_pinned_data_identity",
    "fit_assessment_prior_pilot_disjointness",
    "locked_configuration_and_paper_target_treatment",
    "controls_and_frozen_weight_behavior",
    "exact_bootstrap_and_uncertainty_rule",
    "aggregate_per_document_retention_and_validator_behavior",
    "v1_rejection_preserved_and_prohibited_actions_enforced",
)
NORMALIZED_FIELDS = (
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


def _check_self_digest(value: dict[str, Any], field: str, label: str) -> None:
    stored = value.get(field)
    if not isinstance(stored, str) or not stored:
        raise ValueError(f"{label} is missing {field}")
    body = {key: item for key, item in value.items() if key != field}
    if digest(body) != stored:
        raise ValueError(f"{label} {field} mismatch")


def _safe_relative(root: Path, relative: Any, label: str) -> Path:
    if not isinstance(relative, str) or not relative or Path(relative).is_absolute():
        raise ValueError(f"{label} must be a relative path")
    candidate = (root / relative).resolve()
    resolved_root = root.resolve()
    if candidate == resolved_root or resolved_root not in candidate.parents:
        raise ValueError(f"{label} escapes its root: {relative}")
    return _regular(candidate, label)


def _json_value(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


def _normalized_from_values(values: dict[str, list[Any]], item: dict[str, Any], source_row_index: int, value_index: int) -> dict[str, Any]:
    text = values["text"][value_index]
    if not isinstance(text, str) or not text.strip():
        raise ValueError(f"empty FineWeb-Edu text at row {source_row_index}: {item['path']}")
    upstream_id = values.get("id", [None] * len(values["text"]))[value_index]
    if not isinstance(upstream_id, str) or not upstream_id:
        upstream_id = f"row-{source_row_index:08d}"
    metadata = {
        field: _json_value(values[field][value_index])
        for field in NORMALIZED_FIELDS
        if field in values and values[field][value_index] is not None
    }
    return {
        "document_id": f"fineweb-edu:{item['crawl']}:{upstream_id}",
        "text": text,
        "metadata": metadata,
        "source_crawl": item["crawl"],
        "source_path": item["path"],
        "source_row_index": source_row_index,
    }


def _parquet_rows(path: Path, item: dict[str, Any], start: int, count: int) -> Iterator[dict[str, Any]]:
    import pyarrow.parquet as pq

    parquet = pq.ParquetFile(path)
    available = set(parquet.schema.names)
    if "text" not in available:
        raise ValueError(f"FineWeb-Edu shard has no text column: {path}")
    columns = ["text", *[field for field in NORMALIZED_FIELDS if field in available]]
    end = start + count
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
    if selected != count:
        raise ValueError(f"selected {selected} rows from {path}:{start}:{end}, expected {count}")


def _expected_dataset_manifest() -> dict[str, Any]:
    return {
        "repo": DATASET_REPO,
        "source": DATASET_SOURCE,
        "revision": DATASET_REVISION,
        "config": DATASET_CONFIG,
        "split": DATASET_SPLIT,
        "selected_file_count": 2,
        "selected_crawls": [item["crawl"] for item in DATASET_FILES],
        "parquet_byte_count": DATASET_BYTE_COUNT,
    }


def _audit_raw(raw_root: Path) -> dict[str, Any]:
    raw_root = _primary(raw_root, "raw root")
    dataset_root = raw_root / "dataset"
    artifacts = []
    expected_paths = set()
    for item in DATASET_FILES:
        path = _regular(dataset_root / item["path"], "pinned FineWeb-Edu Parquet shard")
        expected_paths.add(path)
        if path.stat().st_size != item["byte_len"]:
            raise ValueError(f"pinned byte length mismatch: {path}")
        actual_sha = sha256_file(path)
        if actual_sha != item["sha256"]:
            raise ValueError(f"pinned SHA-256 mismatch: {path}")
        import pyarrow.parquet as pq

        row_count = pq.ParquetFile(path).metadata.num_rows
        if row_count < FRESH_ROW_END:
            raise ValueError(f"pinned shard is too short for V2 rows: {path}")
        artifacts.append(
            {
                "relative_path": path.relative_to(raw_root).as_posix(),
                "source": f"{DATASET_SOURCE}/resolve/{DATASET_REVISION}/{item['path']}",
                "crawl": item["crawl"],
                "byte_len": path.stat().st_size,
                "sha256": actual_sha,
                "lfs_sha256": item["sha256"],
                "row_count": row_count,
            }
        )
    actual_paths = {
        path
        for path in dataset_root.rglob("*.parquet")
        if path.is_file() and not path.is_symlink()
    }
    if actual_paths != expected_paths:
        raise ValueError(f"raw Parquet set differs from the two-file pin: {sorted(actual_paths)}")
    return {"root": raw_root, "artifacts": artifacts}


def _audit_prior_source(r1_source_root: Path) -> set[str]:
    r1_source_root = _primary(r1_source_root, "prior pilot source root")
    manifest_path = r1_source_root / "acquisition-manifest.json"
    manifest = _json(manifest_path, "prior pilot source manifest")
    if sha256_file(manifest_path) != R1_SOURCE_MANIFEST_SHA256:
        raise ValueError("prior pilot source manifest SHA-256 mismatch")
    if manifest.get("schema") != "gemma3-fineweb-edu-bounded-acquisition-v1":
        raise ValueError("prior pilot source schema mismatch")
    if manifest.get("selection_policy") != "first-2048-records-from-two-pinned-crawls-document-disjoint-v1":
        raise ValueError("prior pilot source selection policy mismatch")
    if manifest.get("dataset") != _expected_dataset_manifest():
        raise ValueError("prior pilot dataset pin mismatch")
    _check_self_digest(manifest, "manifest_sha256", "prior pilot source manifest")
    document_ids: set[str] = set()
    datasets = manifest.get("datasets")
    if not isinstance(datasets, dict):
        raise ValueError("prior pilot source datasets missing")
    for split, item in (("fit", DATASET_FILES[0]), ("assessment", DATASET_FILES[1])):
        key = f"{split}/fineweb_edu"
        metadata = datasets.get(key)
        if not isinstance(metadata, dict) or metadata.get("row_start") != R1_ROW_START or metadata.get("row_count") != R1_ROW_COUNT:
            raise ValueError(f"prior pilot {key} row binding mismatch")
        if metadata.get("crawl") != item["crawl"] or metadata.get("source_path") != item["path"]:
            raise ValueError(f"prior pilot {key} shard binding mismatch")
        rows = _jsonl(r1_source_root / metadata["normalized_path"], f"prior pilot {key}")
        if len(rows) != R1_ROW_COUNT:
            raise ValueError(f"prior pilot {key} count mismatch")
        for ordinal, row in enumerate(rows):
            document_id = row.get("document_id")
            if not isinstance(document_id, str) or not document_id:
                raise ValueError(f"prior pilot {key} has invalid document ID")
            if row.get("source_crawl") != item["crawl"] or row.get("source_path") != item["path"] or row.get("source_row_index") != ordinal:
                raise ValueError(f"prior pilot {key} row identity mismatch at {ordinal}")
            if document_id in document_ids:
                raise ValueError(f"prior pilot document overlap: {document_id}")
            document_ids.add(document_id)
    return document_ids


def _audit_source(source_root: Path, raw_root: Path, r1_source_root: Path) -> dict[str, Any]:
    source_root = _primary(source_root, "source root")
    raw_root = _primary(raw_root, "raw root")
    r1_source_root = _primary(r1_source_root, "prior pilot source root")
    manifest = _json(source_root / "acquisition-manifest.json", "V2 source manifest")
    if manifest.get("schema") != SOURCE_SCHEMA or manifest.get("state_slice") != STATE_SLICE:
        raise ValueError("V2 source schema or state slice mismatch")
    if manifest.get("claim_ceiling") != CLAIM_CEILING:
        raise ValueError("V2 source claim ceiling mismatch")
    if manifest.get("source_record_schema") != "gemma3-source-v1-compatible-with-fineweb-metadata":
        raise ValueError("V2 source record schema mismatch")
    if manifest.get("selection_policy") != "rows-2048-through-18431-two-pinned-crawls-v2":
        raise ValueError("V2 source selection policy mismatch")
    if manifest.get("dataset") != _expected_dataset_manifest():
        raise ValueError("V2 source dataset pin mismatch")
    if manifest.get("raw_root") != str(raw_root):
        raise ValueError("V2 source raw-root binding mismatch")
    if manifest.get("prior_pilot_source_root") != str(r1_source_root):
        raise ValueError("V2 source prior-pilot root binding mismatch")
    if manifest.get("prior_pilot_manifest_sha256") != R1_SOURCE_MANIFEST_SHA256:
        raise ValueError("V2 source prior-pilot manifest binding mismatch")
    if manifest.get("fresh_row_range") != {"start": FRESH_ROW_START, "end_exclusive": FRESH_ROW_END, "count_per_shard": FRESH_ROW_COUNT}:
        raise ValueError("V2 fresh row range mismatch")
    for field, expected in (("network_access", False), ("training", False), ("scientific_execution", False), ("evidence_ledger_mutation", False)):
        if manifest.get(field) is not expected:
            raise ValueError(f"V2 source {field} flag mismatch")
    _check_self_digest(manifest, "manifest_sha256", "V2 source manifest")
    raw_audit = _audit_raw(raw_root)
    if manifest.get("raw_artifacts") != raw_audit["artifacts"]:
        raise ValueError("V2 source raw-artifact binding mismatch")
    prior_ids = _audit_prior_source(r1_source_root)
    datasets = manifest.get("datasets")
    if not isinstance(datasets, dict):
        raise ValueError("V2 source datasets missing")
    records_by_split: dict[str, list[dict[str, Any]]] = {}
    all_ids: set[str] = set()
    for split, item in (("fit", DATASET_FILES[0]), ("assessment", DATASET_FILES[1])):
        key = f"{split}/fineweb_edu"
        metadata = datasets.get(key)
        expected_metadata = {
            "source": DATASET_SOURCE,
            "revision": DATASET_REVISION,
            "config": DATASET_CONFIG,
            "split": DATASET_SPLIT,
            "crawl": item["crawl"],
            "source_path": item["path"],
            "row_start": FRESH_ROW_START,
            "row_count": FRESH_ROW_COUNT,
            "normalized_path": f"{split}/fineweb_edu.jsonl",
        }
        if not isinstance(metadata, dict) or any(metadata.get(k) != v for k, v in expected_metadata.items()):
            raise ValueError(f"V2 {key} metadata mismatch")
        path = _safe_relative(source_root, metadata["normalized_path"], f"V2 {key} JSONL")
        if sha256_file(path) != metadata.get("normalized_sha256"):
            raise ValueError(f"V2 {key} normalized SHA-256 mismatch")
        rows = _jsonl(path, f"V2 {key}")
        if len(rows) != FRESH_ROW_COUNT:
            raise ValueError(f"V2 {key} count mismatch")
        for ordinal, row in enumerate(rows):
            document_id = row.get("document_id")
            text = row.get("text")
            if not isinstance(document_id, str) or not document_id:
                raise ValueError(f"V2 {key} invalid document_id at {ordinal}")
            if not isinstance(text, str) or not text.strip():
                raise ValueError(f"V2 {key} empty text at {ordinal}")
            if row.get("source_crawl") != item["crawl"] or row.get("source_path") != item["path"]:
                raise ValueError(f"V2 {key} shard identity mismatch at {ordinal}")
            source_index = row.get("source_row_index")
            if source_index != FRESH_ROW_START + ordinal or not FRESH_ROW_START <= source_index < FRESH_ROW_END:
                raise ValueError(f"V2 {key} source row mismatch at {ordinal}")
            if not document_id.startswith(f"fineweb-edu:{item['crawl']}:"):
                raise ValueError(f"V2 {key} document ID prefix mismatch at {ordinal}")
            if document_id in all_ids or document_id in prior_ids:
                raise ValueError(f"V2 document overlap: {document_id}")
            all_ids.add(document_id)
        expected_rows = _parquet_rows(raw_root / "dataset" / item["path"], item, FRESH_ROW_START, FRESH_ROW_COUNT)
        for ordinal, (observed, expected) in enumerate(zip(rows, expected_rows, strict=True)):
            if observed != expected:
                raise ValueError(f"V2 raw-row lineage mismatch in {key} at {ordinal}")
        records_by_split[split] = rows
    return {
        "manifest": manifest,
        "manifest_sha256": manifest["manifest_sha256"],
        "raw_audit": raw_audit,
        "prior_document_ids": prior_ids,
        "document_ids": all_ids,
        "records_by_split": records_by_split,
    }


def validate_source(source_root: Path, raw_root: Path = Path("/Volumes/PrimaryED/ResearchArtifacts/composed-zk-benchmark-os/gemma3-fineweb-edu-bounded-raw-v1"), r1_source_root: Path = R1_SOURCE_ROOT) -> dict[str, Any]:
    audit = _audit_source(source_root, raw_root, r1_source_root)
    return {
        "valid": True,
        "state_slice": STATE_SLICE,
        "claim_ceiling": CLAIM_CEILING,
        "source_manifest_sha256": audit["manifest_sha256"],
        "fit_record_count": len(audit["records_by_split"]["fit"]),
        "assessment_record_count": len(audit["records_by_split"]["assessment"]),
        "prior_document_count": len(audit["prior_document_ids"]),
        "raw_artifact_count": len(audit["raw_audit"]["artifacts"]),
    }


def _audit_corpus(corpus_root: Path, source_root: Path, raw_root: Path, r1_source_root: Path, source_manifest_sha256: str) -> dict[str, Any]:
    corpus_root = _primary(corpus_root, "corpus root")
    source_audit = _audit_source(source_root, raw_root, r1_source_root)
    if source_audit["manifest_sha256"] != source_manifest_sha256:
        raise ValueError("corpus source manifest binding mismatch")
    manifest = _json(corpus_root / "manifest.json", "V2 corpus manifest")
    if manifest.get("schema") != CORPUS_SCHEMA or manifest.get("state_slice") != STATE_SLICE:
        raise ValueError("V2 corpus schema or state slice mismatch")
    if manifest.get("claim_ceiling") != CLAIM_CEILING or manifest.get("window_token_count") != WINDOW_TOKENS:
        raise ValueError("V2 corpus claim ceiling or window size mismatch")
    if manifest.get("source_manifest_sha256") != source_manifest_sha256:
        raise ValueError("V2 corpus source binding mismatch")
    if manifest.get("selection_policy") != "first-64-eligible-1024-token-windows-per-disjoint-v2-source-split":
        raise ValueError("V2 corpus selection policy mismatch")
    if manifest.get("fit_window_count") != FIT_WINDOW_COUNT or manifest.get("assessment_window_count") != ASSESSMENT_WINDOW_COUNT:
        raise ValueError("V2 corpus window counts mismatch")
    for field, expected in (("network_access", False), ("training", False)):
        if manifest.get(field) is not expected:
            raise ValueError(f"V2 corpus {field} flag mismatch")
    _check_self_digest(manifest, "manifest_sha256", "V2 corpus manifest")
    prior_ids = source_audit["prior_document_ids"]
    source_records = {
        row["document_id"]: row
        for rows in source_audit["records_by_split"].values()
        for row in rows
    }
    split_ids: dict[str, set[str]] = {}
    for split, expected_count in (("fit", FIT_WINDOW_COUNT), ("assessment", ASSESSMENT_WINDOW_COUNT)):
        entries = manifest.get(split)
        if not isinstance(entries, list) or len(entries) != expected_count:
            raise ValueError(f"V2 corpus {split} entry count mismatch")
        seen: set[str] = set()
        for entry in entries:
            if not isinstance(entry, dict):
                raise ValueError(f"V2 corpus {split} entry is not an object")
            document_id = entry.get("document_id")
            if not isinstance(document_id, str) or document_id in seen or document_id in prior_ids:
                raise ValueError(f"V2 corpus {split} document overlap or invalid ID")
            if document_id not in source_audit["document_ids"]:
                raise ValueError(f"V2 corpus {split} document is not in fresh source")
            if entry.get("dataset") != "fineweb_edu" or entry.get("window_ordinal") != 0 or entry.get("token_count") != WINDOW_TOKENS:
                raise ValueError(f"V2 corpus {split} fixed window contract mismatch")
            source_record = source_records[document_id]
            if entry.get("source_row_index") != source_record["source_row_index"] or entry.get("source_path") != source_record["source_path"]:
                raise ValueError(f"V2 corpus {split} source-row binding mismatch")
            if entry.get("source_sha256") != hashlib.sha256(source_record["text"].encode("utf-8")).hexdigest():
                raise ValueError(f"V2 corpus {split} source-text binding mismatch")
            path = _safe_relative(corpus_root, entry.get("path"), f"V2 corpus {split} window")
            if len(path.read_bytes()) != entry.get("byte_len"):
                raise ValueError(f"V2 corpus {split} byte length mismatch")
            if sha256_file(path) != entry.get("text_sha256"):
                raise ValueError(f"V2 corpus {split} text SHA-256 mismatch")
            if not isinstance(entry.get("source_sha256"), str) or len(entry["source_sha256"]) != 64:
                raise ValueError(f"V2 corpus {split} source SHA-256 missing")
            seen.add(document_id)
        split_ids[split] = seen
    if split_ids["fit"] & split_ids["assessment"]:
        raise ValueError("V2 corpus fit/assessment document overlap")
    return {
        "manifest": manifest,
        "manifest_sha256": manifest["manifest_sha256"],
        "source_audit": source_audit,
        "fit_ids": split_ids["fit"],
        "assessment_ids": split_ids["assessment"],
    }


def validate_corpus(corpus_root: Path, source_root: Path, raw_root: Path, r1_source_root: Path, source_manifest_sha256: str) -> dict[str, Any]:
    audit = _audit_corpus(corpus_root, source_root, raw_root, r1_source_root, source_manifest_sha256)
    return {
        "valid": True,
        "state_slice": STATE_SLICE,
        "claim_ceiling": CLAIM_CEILING,
        "corpus_manifest_sha256": audit["manifest_sha256"],
        "source_manifest_sha256": source_manifest_sha256,
        "fit_window_count": len(audit["fit_ids"]),
        "assessment_window_count": len(audit["assessment_ids"]),
    }


def implementation_manifest() -> dict[str, Any]:
    files = []
    for path in IMPLEMENTATION_FILES:
        path = _regular(path, "reviewed V2 implementation file")
        files.append({"path": path.relative_to(REPO_ROOT).as_posix(), "byte_len": path.stat().st_size, "sha256": sha256_file(path)})
    body = {"state_slice": STATE_SLICE, "files": files}
    return {"manifest": body, "manifest_sha256": digest(body)}


def validate_review_receipt(path: Path, protocol_sha256: str = PROTOCOL_SHA256) -> dict[str, Any]:
    receipt = _json(path, "independent V2 review receipt")
    if receipt.get("schema") != REVIEW_SCHEMA or receipt.get("state_slice") != STATE_SLICE:
        raise ValueError("V2 review receipt schema or state slice mismatch")
    if receipt.get("claim_ceiling") != CLAIM_CEILING or receipt.get("protocol_sha256") != protocol_sha256:
        raise ValueError("V2 review receipt protocol or claim binding mismatch")
    if receipt.get("review_status") != "ACCEPT" or receipt.get("effects_run") is not False:
        raise ValueError("V2 requires an independent ACCEPT receipt with effects_run=false")
    findings = receipt.get("findings")
    if not isinstance(findings, dict) or any(findings.get(key) is not True for key in REVIEW_FINDINGS):
        raise ValueError("V2 independent review findings are incomplete")
    if receipt.get("review_packet_sha256") != sha256_file(REVIEW_PACKET_PATH):
        raise ValueError("V2 review packet binding mismatch")
    if receipt.get("implementation_manifest_sha256") != implementation_manifest()["manifest_sha256"]:
        raise ValueError("V2 implementation manifest binding mismatch")
    _check_self_digest(receipt, "receipt_digest_sha256", "V2 independent review receipt")
    return receipt


def _model_manifest(model_path: Path) -> dict[str, Any]:
    model_path = _external(model_path, "model path")
    if not model_path.is_dir() or model_path.is_symlink():
        raise ValueError(f"model path must be a real directory: {model_path}")
    files = []
    for path in sorted(candidate for candidate in model_path.rglob("*") if candidate.is_file() and not candidate.is_symlink() and ".cache" not in candidate.relative_to(model_path).parts):
        files.append({"path": path.relative_to(model_path).as_posix(), "byte_len": path.stat().st_size, "sha256": sha256_file(path)})
    if not files:
        raise ValueError("cached model directory has no stable files")
    body = {"model_name": model_path.name, "files": files}
    return {"manifest": body, "manifest_sha256": digest(body)}


def _require_finite(value: Any, label: str) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(float(value)):
        raise ValueError(f"{label} must be finite")
    return float(value)


def bootstrap_mean_ci(deltas: Iterable[float], *, resamples: int = BOOTSTRAP_RESAMPLES, seed: int = BOOTSTRAP_SEED) -> dict[str, Any]:
    values = [_require_finite(value, "paired delta") for value in deltas]
    if not values:
        raise ValueError("bootstrap requires at least one paired delta")
    if resamples <= 0:
        raise ValueError("bootstrap resamples must be positive")
    bootstrap_values = []
    n = len(values)
    for resample in range(resamples):
        total = 0.0
        for position in range(n):
            counter = f"{seed}:{resample}:{position}".encode("utf-8")
            index = int.from_bytes(hashlib.sha256(counter).digest()[:8], "big") % n
            total += values[index]
        sample_mean = total / n
        if not math.isfinite(sample_mean):
            raise ValueError("bootstrap produced a nonfinite sample mean")
        bootstrap_values.append(sample_mean)
    bootstrap_values.sort()

    def nearest_rank(q: float) -> float:
        rank = max(1, math.ceil(q * resamples))
        return bootstrap_values[rank - 1]

    mean_delta = sum(values) / n
    return {
        "mean_delta": mean_delta,
        "lower": nearest_rank(0.025),
        "upper": nearest_rank(0.975),
        "resamples": resamples,
        "seed": seed,
        "confidence": BOOTSTRAP_CONFIDENCE,
        "prng": BOOTSTRAP_PRNG,
        "statistic": BOOTSTRAP_STATISTIC,
        "percentile": BOOTSTRAP_PERCENTILE,
        "nonfinite": BOOTSTRAP_NONFINITE,
    }


def decide_replication(bootstrap: dict[str, Any]) -> str:
    mean_delta = _require_finite(bootstrap.get("mean_delta"), "bootstrap mean_delta")
    upper = _require_finite(bootstrap.get("upper"), "bootstrap upper")
    return "ReplicationCandidate" if mean_delta < 0 and upper < 0 else "NoCandidate"


def _validate_result_rows(results: dict[str, Any], assessment_ids: set[str], prior_ids: set[str]) -> list[float]:
    rows = results.get("assessment_per_document")
    if not isinstance(rows, list) or len(rows) != ASSESSMENT_WINDOW_COUNT:
        raise ValueError("assessment_per_document count mismatch")
    seen: set[str] = set()
    deltas = []
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("assessment per-document row is not an object")
        document_id = row.get("document_id")
        if not isinstance(document_id, str) or document_id not in assessment_ids or document_id in prior_ids or document_id in seen:
            raise ValueError("assessment per-document identity mismatch")
        target_count = row.get("target_count")
        if not isinstance(target_count, int) or target_count <= 0:
            raise ValueError("assessment target_count mismatch")
        baseline_nll = _require_finite(row.get("baseline_nll"), "baseline NLL")
        selected_nll = _require_finite(row.get("selected_nll"), "selected NLL")
        delta = _require_finite(row.get("delta_selected_minus_baseline"), "assessment delta")
        expected = selected_nll / target_count - baseline_nll / target_count
        if not math.isclose(delta, expected, rel_tol=0.0, abs_tol=1e-12):
            raise ValueError("assessment paired delta mismatch")
        seen.add(document_id)
        deltas.append(delta)
    if seen != assessment_ids:
        raise ValueError("assessment per-document set mismatch")
    return deltas


def validate_result(result_root: Path, corpus_root: Path, source_root: Path, raw_root: Path, r1_source_root: Path, model_path: Path, review_receipt: Path, corpus_manifest_sha256: str) -> dict[str, Any]:
    result_root = _primary(result_root, "result root")
    review = validate_review_receipt(review_receipt)
    source_audit = _audit_source(source_root, raw_root, r1_source_root)
    corpus = _audit_corpus(corpus_root, source_root, raw_root, r1_source_root, source_audit["manifest_sha256"])
    if corpus["manifest_sha256"] != corpus_manifest_sha256:
        raise ValueError("result corpus manifest binding mismatch")
    config = _json(result_root / "config.json", "V2 result config")
    results = _json(result_root / "results.json", "V2 result body")
    receipt = _json(result_root / "receipt.json", "V2 result receipt")
    for value, label in ((config, "V2 result config"), (results, "V2 result body"), (receipt, "V2 result receipt")):
        if value.get("state_slice") != STATE_SLICE or value.get("claim_ceiling") != CLAIM_CEILING:
            raise ValueError(f"{label} state or claim binding mismatch")
    if config.get("schema") != RESULT_SCHEMA or results.get("schema") != RESULT_SCHEMA or receipt.get("schema") != RESULT_SCHEMA:
        raise ValueError("V2 result schema mismatch")
    _check_self_digest(config, "config_sha256", "V2 result config")
    _check_self_digest(results, "results_sha256", "V2 result body")
    _check_self_digest(receipt, "receipt_sha256", "V2 result receipt")
    source_manifest_sha256 = corpus["source_audit"]["manifest_sha256"]
    if config.get("protocol_sha256") != PROTOCOL_SHA256 or config.get("source_manifest_sha256") != source_manifest_sha256 or config.get("corpus_manifest_sha256") != corpus_manifest_sha256:
        raise ValueError("V2 result config binding mismatch")
    if results.get("source_manifest_sha256") != source_manifest_sha256 or results.get("corpus_manifest_sha256") != corpus_manifest_sha256:
        raise ValueError("V2 result body corpus binding mismatch")
    if config.get("review_receipt_sha256") != sha256_file(review_receipt):
        raise ValueError("V2 result review receipt binding mismatch")
    model_manifest = _model_manifest(model_path)
    if model_manifest["manifest_sha256"] != EXPECTED_MODEL_MANIFEST_SHA256 or config.get("model_manifest_sha256") != model_manifest["manifest_sha256"]:
        raise ValueError("V2 model manifest mismatch")
    if config.get("candidate_pairs") != [list(pair) for pair in CANDIDATE_PAIRS] or config.get("fit_alpha") != FIT_ALPHA or config.get("evaluation_alpha") != EVALUATION_ALPHA or config.get("evaluation_beta") != EVALUATION_BETA or config.get("temperature_control") != TEMPERATURE_CONTROL:
        raise ValueError("V2 locked intervention configuration mismatch")
    if config.get("selected_fit_config", {}).get("alpha") != FIT_ALPHA or config.get("locked_evaluation_config", {}).get("alpha") != EVALUATION_ALPHA:
        raise ValueError("V2 selected/locked alpha mismatch")
    if config.get("paper_expected_pair") != {"source_layer": 11, "destination_layer": 4}:
        raise ValueError("V2 paper expected pair binding mismatch")
    for field, expected in (("network_access", False), ("training", False), ("weights_frozen", True), ("evidence_ledger_mutation", False), ("assessment_authorized_by_review", True)):
        if config.get(field) is not expected:
            raise ValueError(f"V2 result config {field} flag mismatch")
    if results.get("parity", {}).get("all_passed") is not True or results.get("deterministic_repeat_passed") is not True:
        raise ValueError("V2 qualification controls did not pass")
    deltas = _validate_result_rows(results, corpus["assessment_ids"], corpus["source_audit"]["prior_document_ids"])
    bootstrap = results.get("bootstrap")
    if not isinstance(bootstrap, dict):
        raise ValueError("V2 bootstrap result missing")
    expected_bootstrap = bootstrap_mean_ci(deltas)
    for key in expected_bootstrap:
        if bootstrap.get(key) != expected_bootstrap[key]:
            raise ValueError(f"V2 bootstrap field mismatch: {key}")
    expected_decision = decide_replication(expected_bootstrap)
    if results.get("decision") != expected_decision or receipt.get("decision") != expected_decision:
        raise ValueError("V2 decision mismatch")
    if receipt.get("review_receipt_sha256") != sha256_file(review_receipt) or receipt.get("bootstrap") != bootstrap:
        raise ValueError("V2 receipt binding mismatch")
    return {
        "valid": True,
        "state_slice": STATE_SLICE,
        "claim_ceiling": CLAIM_CEILING,
        "result_root": str(result_root),
        "decision": expected_decision,
        "assessment_document_count": len(deltas),
        "bootstrap": bootstrap,
        "review_receipt_sha256": sha256_file(review_receipt),
        "results_sha256": results["results_sha256"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path)
    parser.add_argument("--raw-root", type=Path, default=Path("/Volumes/PrimaryED/ResearchArtifacts/composed-zk-benchmark-os/gemma3-fineweb-edu-bounded-raw-v1"))
    parser.add_argument("--r1-source-root", type=Path, default=R1_SOURCE_ROOT)
    parser.add_argument("--corpus-root", type=Path)
    parser.add_argument("--source-manifest-sha256")
    parser.add_argument("--result-root", type=Path)
    parser.add_argument("--model", type=Path)
    parser.add_argument("--review-receipt", type=Path)
    parser.add_argument("--corpus-manifest-sha256")
    args = parser.parse_args()
    modes = sum(value is not None for value in (args.source_root, args.corpus_root, args.result_root))
    if modes != 1:
        parser.error("choose exactly one of --source-root, --corpus-root, or --result-root")
    if args.source_root is not None:
        value = validate_source(args.source_root, args.raw_root, args.r1_source_root)
    elif args.corpus_root is not None:
        if not args.source_root or not args.source_manifest_sha256:
            parser.error("--corpus-root requires --source-root and --source-manifest-sha256")
        value = validate_corpus(args.corpus_root, args.source_root, args.raw_root, args.r1_source_root, args.source_manifest_sha256)
    else:
        required = (args.source_root, args.corpus_root, args.model, args.review_receipt, args.corpus_manifest_sha256)
        if any(value is None for value in required):
            parser.error("--result-root requires --source-root, --corpus-root, --model, --review-receipt, and --corpus-manifest-sha256")
        value = validate_result(args.result_root, args.corpus_root, args.source_root, args.raw_root, args.r1_source_root, args.model, args.review_receipt, args.corpus_manifest_sha256)
    print(json.dumps(value, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
