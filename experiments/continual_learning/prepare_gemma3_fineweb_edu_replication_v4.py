#!/usr/bin/env python3
"""Create the reviewed V4 FineWeb-Edu source bundle.

State slice: continual-learning-gemma3-fineweb-edu-replication-v4.
The packer is offline, write-once, exact-root, and review-gated. It never
loads a model or tokenizer and never runs scientific effects.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Iterator

from experiments.continual_learning import gemma3_fineweb_edu_replication_v4_contract as c
from experiments.continual_learning import validate_gemma3_fineweb_edu_replication_v4 as validator

VALIDATOR_MODULE = "experiments.continual_learning.validate_gemma3_fineweb_edu_replication_v4"
NORMALIZED_FIELDS = ("id", "url", "date", "dump", "file_path", "language", "language_score", "token_count", "score", "int_score")


def _json_value(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


def _expected_dataset() -> dict[str, Any]:
    return {"repo": c.DATASET_REPO, "source": c.DATASET_SOURCE, "revision": c.DATASET_REVISION, "config": c.DATASET_CONFIG, "split": c.DATASET_SPLIT, "selected_file_count": 2, "selected_crawls": [item["crawl"] for item in c.DATASET_FILES], "parquet_byte_count": c.DATASET_BYTE_COUNT}


def _parquet_rows(path: Path, item: dict[str, Any]) -> Iterator[dict[str, Any]]:
    import pyarrow.parquet as pq

    parquet = pq.ParquetFile(path)
    columns = ["text", *[field for field in NORMALIZED_FIELDS if field in parquet.schema.names]]
    global_index = 0
    selected = 0
    for batch in parquet.iter_batches(columns=columns, batch_size=256):
        values = {name: batch.column(name).to_pylist() for name in columns}
        for offset in range(batch.num_rows):
            if c.FRESH_ROW_START <= global_index < c.FRESH_ROW_END:
                text = values["text"][offset]
                if not isinstance(text, str) or not text.strip():
                    raise ValueError(f"empty FineWeb-Edu text at row {global_index}: {path}")
                upstream_id = values.get("id", [None] * batch.num_rows)[offset]
                if not isinstance(upstream_id, str) or not upstream_id:
                    upstream_id = f"row-{global_index:08d}"
                metadata = {field: _json_value(values[field][offset]) for field in NORMALIZED_FIELDS if field in values and values[field][offset] is not None}
                yield {"document_id": f"fineweb-edu:{item['crawl']}:{upstream_id}", "text": text, "metadata": metadata, "source_crawl": item["crawl"], "source_path": item["path"], "source_row_index": global_index}
                selected += 1
            global_index += 1
            if global_index >= c.FRESH_ROW_END:
                break
        if global_index >= c.FRESH_ROW_END:
            break
    if selected != c.FRESH_ROW_COUNT:
        raise ValueError(f"selected {selected} rows from {path}; expected {c.FRESH_ROW_COUNT}")


def _raw_artifacts(raw_root: Path) -> list[dict[str, Any]]:
    import pyarrow.parquet as pq

    artifacts = []
    for item in c.DATASET_FILES:
        path = c.regular(raw_root / "dataset" / item["path"], "V4 pinned Parquet shard")
        if path.stat().st_size != item["byte_len"] or c.sha256_file(path) != item["sha256"]:
            raise ValueError(f"V4 raw pin mismatch: {path}")
        row_count = pq.ParquetFile(path).metadata.num_rows
        if row_count < c.FRESH_ROW_END:
            raise ValueError(f"V4 raw shard is too short: {path}")
        artifacts.append({"relative_path": path.relative_to(raw_root).as_posix(), "source": f"{c.DATASET_SOURCE}/resolve/{c.DATASET_REVISION}/{item['path']}", "crawl": item["crawl"], "byte_len": path.stat().st_size, "sha256": c.sha256_file(path), "lfs_sha256": item["sha256"], "row_count": row_count})
    expected = {raw_root / "dataset" / item["path"] for item in c.DATASET_FILES}
    actual = {path for path in (raw_root / "dataset").rglob("*.parquet") if path.is_file() and not path.is_symlink()}
    if actual != expected:
        raise ValueError("V4 raw Parquet set differs from the two pinned files")
    return artifacts


def _write_jsonl(path: Path, rows: Iterator[dict[str, Any]]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    seen: set[str] = set()
    count = 0
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            if row["document_id"] in seen:
                raise ValueError(f"duplicate V4 document_id: {row['document_id']}")
            seen.add(row["document_id"])
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
            count += 1
    if count != c.FRESH_ROW_COUNT:
        raise ValueError(f"V4 normalized count {count} != {c.FRESH_ROW_COUNT}")
    return count


def _review_snapshot(review_receipt: Path) -> tuple[bytes, str]:
    review_receipt = c.exact_path(review_receipt, c.REVIEW_RECEIPT_PATH, "V4 review receipt")
    raw = c.regular(review_receipt, "V4 review receipt").read_bytes()
    validator.validate_review_receipt(review_receipt)
    return raw, c.sha256_file(review_receipt)


def _implementation_snapshot() -> dict[str, Any]:
    return {
        "protocol_bytes": c.regular(c.PROTOCOL_PATH, "V4 protocol").read_bytes(),
        "packet_bytes": c.regular(c.REVIEW_PACKET_PATH, "V4 review packet").read_bytes(),
        "implementation_manifest_sha256": validator.implementation_manifest()["manifest_sha256"],
    }


def _assert_implementation_snapshot(snapshot: dict[str, Any]) -> None:
    if c.regular(c.PROTOCOL_PATH, "V4 protocol").read_bytes() != snapshot["protocol_bytes"] or c.regular(c.REVIEW_PACKET_PATH, "V4 review packet").read_bytes() != snapshot["packet_bytes"] or validator.implementation_manifest()["manifest_sha256"] != snapshot["implementation_manifest_sha256"]:
        raise RuntimeError("V4 implementation snapshot changed during source acquisition")


def pack(raw_root: Path = c.RAW_ROOT, source_root: Path = c.SOURCE_ROOT, review_receipt: Path = c.REVIEW_RECEIPT_PATH) -> dict[str, Any]:
    review_bytes, review_sha = _review_snapshot(review_receipt)
    implementation_snapshot = _implementation_snapshot()
    raw_root = c.exact_path(raw_root, c.RAW_ROOT, "V4 raw root")
    source_root = c.exact_path(source_root, c.SOURCE_ROOT, "V4 source root")
    c.exact_path(c.R1_SOURCE_ROOT, c.R1_SOURCE_ROOT, "V4 prior-pilot source root")
    if c.runtime_versions() != c.RUNTIME_VERSIONS:
        raise RuntimeError(f"V4 runtime mismatch: {c.runtime_versions()}")
    if not raw_root.is_dir() or raw_root.is_symlink() or source_root.exists() or source_root.is_symlink():
        raise FileExistsError("V4 raw root must be a real directory and source root must be absent")
    c.reject_tree_symlinks(raw_root, "V4 raw root")
    staging = Path(tempfile.mkdtemp(prefix=f".{source_root.name}.staging-", dir=source_root.parent))
    try:
        if c.sha256_file(review_receipt) != review_sha or c.regular(review_receipt, "V4 review receipt").read_bytes() != review_bytes:
            raise RuntimeError("V4 review receipt changed before source acquisition")
        _assert_implementation_snapshot(implementation_snapshot)
        raw_artifacts = _raw_artifacts(raw_root)
        fit_count = _write_jsonl(staging / "fit/fineweb_edu.jsonl", _parquet_rows(raw_root / "dataset" / c.DATASET_FILES[0]["path"], c.DATASET_FILES[0]))
        assessment_count = _write_jsonl(staging / "assessment/fineweb_edu.jsonl", _parquet_rows(raw_root / "dataset" / c.DATASET_FILES[1]["path"], c.DATASET_FILES[1]))
        body = {"schema": c.SOURCE_SCHEMA, "state_slice": c.STATE_SLICE, "claim_ceiling": c.CLAIM_CEILING, "source_record_schema": "gemma3-source-v1-compatible-with-fineweb-metadata", "selection_policy": "rows-2048-through-18431-two-pinned-crawls-v4", "dataset": _expected_dataset(), "raw_root": str(raw_root), "raw_artifacts": raw_artifacts, "prior_pilot_source_root": str(c.R1_SOURCE_ROOT), "prior_pilot_manifest_sha256": c.R1_SOURCE_MANIFEST_SHA256, "prior_pilot_row_range": {"start": 0, "end_exclusive": 2048, "count_per_shard": 2048}, "fresh_row_range": {"start": c.FRESH_ROW_START, "end_exclusive": c.FRESH_ROW_END, "count_per_shard": c.FRESH_ROW_COUNT}, "datasets": {"fit/fineweb_edu": {"source": c.DATASET_SOURCE, "revision": c.DATASET_REVISION, "config": c.DATASET_CONFIG, "split": c.DATASET_SPLIT, "crawl": c.DATASET_FILES[0]["crawl"], "source_path": c.DATASET_FILES[0]["path"], "row_start": c.FRESH_ROW_START, "row_count": fit_count, "normalized_path": "fit/fineweb_edu.jsonl", "normalized_sha256": c.sha256_file(staging / "fit/fineweb_edu.jsonl")}, "assessment/fineweb_edu": {"source": c.DATASET_SOURCE, "revision": c.DATASET_REVISION, "config": c.DATASET_CONFIG, "split": c.DATASET_SPLIT, "crawl": c.DATASET_FILES[1]["crawl"], "source_path": c.DATASET_FILES[1]["path"], "row_start": c.FRESH_ROW_START, "row_count": assessment_count, "normalized_path": "assessment/fineweb_edu.jsonl", "normalized_sha256": c.sha256_file(staging / "assessment/fineweb_edu.jsonl")}}, "review_receipt_sha256": review_sha, "network_access": False, "training": False, "scientific_execution": False, "evidence_ledger_mutation": False, "created_at_utc": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()}
        manifest = {**body, "manifest_sha256": c.digest(body)}
        (staging / "acquisition-manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        if c.regular(review_receipt, "V4 review receipt").read_bytes() != review_bytes:
            raise RuntimeError("V4 review receipt changed during source acquisition")
        _assert_implementation_snapshot(implementation_snapshot)
        environment = os.environ.copy()
        environment["PYTHONDONTWRITEBYTECODE"] = "1"
        command = [sys.executable, "-B", "-m", VALIDATOR_MODULE, "--mode", "source", "--source-root", str(staging), "--raw-root", str(raw_root), "--r1-source-root", str(c.R1_SOURCE_ROOT), "--review-receipt", str(review_receipt)]
        completed = subprocess.run(command, cwd=c.REPO_ROOT, env=environment, capture_output=True, text=True, check=False)
        if completed.returncode != 0:
            raise RuntimeError(f"V4 source validator failed:\n{completed.stdout}\n{completed.stderr}")
        validation = json.loads(completed.stdout)
        if validation.get("valid") is not True:
            raise RuntimeError(f"V4 source validator returned invalid output: {validation}")
        os.replace(staging, source_root)
        return {"manifest": manifest, "validation": validation}
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-root", type=Path, default=c.RAW_ROOT)
    parser.add_argument("--source-root", type=Path, default=c.SOURCE_ROOT)
    parser.add_argument("--review-receipt", type=Path, default=c.REVIEW_RECEIPT_PATH)
    args = parser.parse_args()
    print(json.dumps(pack(args.raw_root, args.source_root, args.review_receipt), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
