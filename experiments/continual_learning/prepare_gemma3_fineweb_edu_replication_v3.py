#!/usr/bin/env python3
"""Create the fresh V3 FineWeb-Edu source bundle.

State slice: continual-learning-gemma3-fineweb-edu-replication-v3.
This offline packer reads only already-cached pinned Parquet files. It never
downloads, loads a model, tokenizes, trains, runs effects, or mutates evidence.
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

from experiments.continual_learning import gemma3_fineweb_edu_replication_v3_contract as c

SOURCE_FILES = {
    "fit/fineweb_edu": Path("fit/fineweb_edu.jsonl"),
    "assessment/fineweb_edu": Path("assessment/fineweb_edu.jsonl"),
}
NORMALIZED_FIELDS = ("id", "url", "date", "dump", "file_path", "language", "language_score", "token_count", "score", "int_score")
VALIDATOR = Path(__file__).with_name("validate_gemma3_fineweb_edu_replication_v3.py")


def _json_value(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


def _parquet_rows(path: Path, item: dict[str, Any]) -> Iterator[dict[str, Any]]:
    import pyarrow.parquet as pq

    parquet = pq.ParquetFile(path)
    available = set(parquet.schema.names)
    if "text" not in available:
        raise ValueError(f"FineWeb-Edu shard has no text column: {path}")
    columns = ["text", *[field for field in NORMALIZED_FIELDS if field in available]]
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
                metadata = {
                    field: _json_value(values[field][offset])
                    for field in NORMALIZED_FIELDS
                    if field in values and values[field][offset] is not None
                }
                yield {
                    "document_id": f"fineweb-edu:{item['crawl']}:{upstream_id}",
                    "text": text,
                    "metadata": metadata,
                    "source_crawl": item["crawl"],
                    "source_path": item["path"],
                    "source_row_index": global_index,
                }
                selected += 1
            global_index += 1
            if global_index >= c.FRESH_ROW_END:
                break
        if global_index >= c.FRESH_ROW_END:
            break
    if selected != c.FRESH_ROW_COUNT:
        raise ValueError(f"selected {selected} rows from {path}; expected {c.FRESH_ROW_COUNT}")


def _write_jsonl(path: Path, rows: Iterator[dict[str, Any]]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    seen: set[str] = set()
    count = 0
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            document_id = row["document_id"]
            if document_id in seen:
                raise ValueError(f"duplicate V3 source document_id: {document_id}")
            if not row["text"].strip():
                raise ValueError(f"empty V3 source text: {document_id}")
            seen.add(document_id)
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
            count += 1
    if count != c.FRESH_ROW_COUNT:
        raise ValueError(f"V3 normalized count {count} != {c.FRESH_ROW_COUNT}")
    return count


def _expected_dataset() -> dict[str, Any]:
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


def _raw_artifacts(raw_root: Path) -> list[dict[str, Any]]:
    import pyarrow.parquet as pq

    artifacts = []
    for item in c.DATASET_FILES:
        path = c.regular(raw_root / "dataset" / item["path"], "pinned V3 Parquet shard")
        if path.stat().st_size != item["byte_len"]:
            raise ValueError(f"pinned byte length mismatch: {path}")
        actual_sha = c.sha256_file(path)
        if actual_sha != item["sha256"]:
            raise ValueError(f"pinned SHA-256 mismatch: {path}")
        row_count = pq.ParquetFile(path).metadata.num_rows
        if row_count < c.FRESH_ROW_END:
            raise ValueError(f"pinned shard too short for V3: {path}")
        artifacts.append({
            "relative_path": path.relative_to(raw_root).as_posix(),
            "source": f"{c.DATASET_SOURCE}/resolve/{c.DATASET_REVISION}/{item['path']}",
            "crawl": item["crawl"],
            "byte_len": path.stat().st_size,
            "sha256": actual_sha,
            "lfs_sha256": item["sha256"],
            "row_count": row_count,
        })
    return artifacts


def pack(raw_root: Path, source_root: Path, r1_source_root: Path = c.R1_SOURCE_ROOT) -> dict[str, Any]:
    raw_root = c.primary(raw_root, "raw root")
    source_root = c.primary(source_root, "V3 source root")
    r1_source_root = c.primary(r1_source_root, "prior pilot source root")
    if not raw_root.is_dir() or raw_root.is_symlink():
        raise FileNotFoundError(f"raw root is not a real directory: {raw_root}")
    if not r1_source_root.is_dir() or r1_source_root.is_symlink():
        raise FileNotFoundError(f"prior pilot source root is not a real directory: {r1_source_root}")
    if source_root.exists() or source_root.is_symlink():
        raise FileExistsError(f"refusing to overwrite V3 source root: {source_root}")
    staging = Path(tempfile.mkdtemp(prefix=f".{source_root.name}.staging-", dir=source_root.parent))
    try:
        raw_artifacts = _raw_artifacts(raw_root)
        fit_path = staging / SOURCE_FILES["fit/fineweb_edu"]
        assessment_path = staging / SOURCE_FILES["assessment/fineweb_edu"]
        fit_count = _write_jsonl(fit_path, _parquet_rows(raw_root / "dataset" / c.DATASET_FILES[0]["path"], c.DATASET_FILES[0]))
        assessment_count = _write_jsonl(assessment_path, _parquet_rows(raw_root / "dataset" / c.DATASET_FILES[1]["path"], c.DATASET_FILES[1]))
        body = {
            "schema": c.SOURCE_SCHEMA,
            "state_slice": c.STATE_SLICE,
            "claim_ceiling": c.CLAIM_CEILING,
            "source_record_schema": "gemma3-source-v1-compatible-with-fineweb-metadata",
            "selection_policy": "rows-2048-through-18431-two-pinned-crawls-v3",
            "dataset": _expected_dataset(),
            "raw_root": str(raw_root),
            "raw_artifacts": raw_artifacts,
            "prior_pilot_source_root": str(r1_source_root),
            "prior_pilot_manifest_sha256": c.R1_SOURCE_MANIFEST_SHA256,
            "prior_pilot_row_range": {"start": 0, "end_exclusive": 2048, "count_per_shard": 2048},
            "fresh_row_range": {"start": c.FRESH_ROW_START, "end_exclusive": c.FRESH_ROW_END, "count_per_shard": c.FRESH_ROW_COUNT},
            "datasets": {
                "fit/fineweb_edu": {
                    "source": c.DATASET_SOURCE, "revision": c.DATASET_REVISION, "config": c.DATASET_CONFIG, "split": c.DATASET_SPLIT,
                    "crawl": c.DATASET_FILES[0]["crawl"], "source_path": c.DATASET_FILES[0]["path"], "row_start": c.FRESH_ROW_START,
                    "row_count": fit_count, "normalized_path": SOURCE_FILES["fit/fineweb_edu"].as_posix(), "normalized_sha256": c.sha256_file(fit_path),
                },
                "assessment/fineweb_edu": {
                    "source": c.DATASET_SOURCE, "revision": c.DATASET_REVISION, "config": c.DATASET_CONFIG, "split": c.DATASET_SPLIT,
                    "crawl": c.DATASET_FILES[1]["crawl"], "source_path": c.DATASET_FILES[1]["path"], "row_start": c.FRESH_ROW_START,
                    "row_count": assessment_count, "normalized_path": SOURCE_FILES["assessment/fineweb_edu"].as_posix(), "normalized_sha256": c.sha256_file(assessment_path),
                },
            },
            "network_access": False,
            "training": False,
            "scientific_execution": False,
            "evidence_ledger_mutation": False,
            "created_at_utc": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        }
        manifest = {**body, "manifest_sha256": c.digest(body)}
        (staging / "acquisition-manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        environment = os.environ.copy()
        environment["PYTHONDONTWRITEBYTECODE"] = "1"
        completed = subprocess.run([sys.executable, "-B", str(VALIDATOR), "--source-root", str(staging), "--raw-root", str(raw_root), "--r1-source-root", str(r1_source_root)], cwd=c.REPO_ROOT, env=environment, capture_output=True, text=True, check=False)
        if completed.returncode != 0:
            raise RuntimeError(f"V3 source validator failed:\n{completed.stdout}\n{completed.stderr}")
        validation = json.loads(completed.stdout)
        if validation.get("valid") is not True:
            raise RuntimeError(f"V3 source validator returned invalid output: {validation}")
        os.replace(staging, source_root)
        return {"manifest": manifest, "validation": validation}
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-root", type=Path, required=True)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--r1-source-root", type=Path, default=c.R1_SOURCE_ROOT)
    args = parser.parse_args()
    print(json.dumps(pack(args.raw_root, args.source_root, args.r1_source_root), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
