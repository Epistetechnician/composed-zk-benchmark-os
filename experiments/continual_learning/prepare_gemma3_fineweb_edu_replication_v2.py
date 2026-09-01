#!/usr/bin/env python3
"""Pack the fresh FineWeb-Edu rows for Gemma3 replication V2.

State slice: continual-learning-gemma3-fineweb-edu-replication-v2.

This boundary is offline-only. It reads the two already-cached pinned
Parquet shards, selects rows 2048 through 18431 in source order, and writes a
new immutable source root outside the repository. It never downloads, loads a
model, trains, runs a forward pass, mutates the Evidence Ledger, or writes a
scientific result.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Iterator

REPO_ROOT = Path(__file__).resolve().parents[2]
PRIMARY_VOLUME = Path("/Volumes/PrimaryED")
STATE_SLICE = "continual-learning-gemma3-fineweb-edu-replication-v2"
CLAIM_CEILING = "LocalDevelopmentGemma3FineWebEduReplicationV2"
SOURCE_SCHEMA = "gemma3-fineweb-edu-replication-v2-source"
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
FRESH_ROW_START = 2048
FRESH_ROW_COUNT = 16_384
FRESH_ROW_END = FRESH_ROW_START + FRESH_ROW_COUNT
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
SOURCE_FILES = {
    "fit/fineweb_edu": Path("fit/fineweb_edu.jsonl"),
    "assessment/fineweb_edu": Path("assessment/fineweb_edu.jsonl"),
}
VALIDATOR = Path(__file__).with_name("validate_gemma3_fineweb_edu_replication_v2.py")


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
            if FRESH_ROW_START <= global_index < FRESH_ROW_END:
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
            if global_index >= FRESH_ROW_END:
                break
        if global_index >= FRESH_ROW_END:
            break
    if selected != FRESH_ROW_COUNT:
        raise ValueError(f"selected {selected} rows from {path}; expected {FRESH_ROW_COUNT}")


def _write_jsonl(path: Path, rows: Iterator[dict[str, Any]]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    seen: set[str] = set()
    count = 0
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            document_id = row.get("document_id")
            text = row.get("text")
            if not isinstance(document_id, str) or not document_id or document_id in seen:
                raise ValueError(f"invalid or duplicate source document_id: {document_id}")
            if not isinstance(text, str) or not text.strip():
                raise ValueError(f"source record has empty text: {document_id}")
            seen.add(document_id)
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True))
            handle.write("\n")
            count += 1
    if count != FRESH_ROW_COUNT:
        raise ValueError(f"normalized source count {count} != {FRESH_ROW_COUNT}")
    return count


def _raw_artifacts(raw_root: Path) -> list[dict[str, Any]]:
    import pyarrow.parquet as pq

    artifacts = []
    for item in DATASET_FILES:
        path = _regular(raw_root / "dataset" / item["path"], "pinned FineWeb-Edu Parquet shard")
        if path.stat().st_size != item["byte_len"]:
            raise ValueError(f"pinned byte length mismatch: {path}")
        actual_sha = sha256_file(path)
        if actual_sha != item["sha256"]:
            raise ValueError(f"pinned SHA-256 mismatch: {path}")
        row_count = pq.ParquetFile(path).metadata.num_rows
        if row_count < FRESH_ROW_END:
            raise ValueError(f"pinned shard is too short for V2 row range: {path}")
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
    return artifacts


def pack(raw_root: Path, source_root: Path, r1_source_root: Path = R1_SOURCE_ROOT) -> dict[str, Any]:
    raw_root = _primary(raw_root, "raw root")
    source_root = _primary(source_root, "source root")
    r1_source_root = _primary(r1_source_root, "prior pilot source root")
    if not raw_root.is_dir() or raw_root.is_symlink():
        raise FileNotFoundError(f"raw root does not exist as a real directory: {raw_root}")
    if source_root.exists() or source_root.is_symlink():
        raise FileExistsError(f"refusing to overwrite V2 source root: {source_root}")
    if not r1_source_root.is_dir() or r1_source_root.is_symlink():
        raise FileNotFoundError(f"prior pilot source root does not exist: {r1_source_root}")
    staging = Path(tempfile.mkdtemp(prefix=f".{source_root.name}.staging-", dir=source_root.parent))
    try:
        raw_artifacts = _raw_artifacts(raw_root)
        fit_count = _write_jsonl(staging / SOURCE_FILES["fit/fineweb_edu"], _parquet_rows(raw_root / "dataset" / DATASET_FILES[0]["path"], DATASET_FILES[0]))
        assessment_count = _write_jsonl(staging / SOURCE_FILES["assessment/fineweb_edu"], _parquet_rows(raw_root / "dataset" / DATASET_FILES[1]["path"], DATASET_FILES[1]))
        body = {
            "schema": SOURCE_SCHEMA,
            "state_slice": STATE_SLICE,
            "claim_ceiling": CLAIM_CEILING,
            "source_record_schema": "gemma3-source-v1-compatible-with-fineweb-metadata",
            "selection_policy": "rows-2048-through-18431-two-pinned-crawls-v2",
            "dataset": {
                "repo": DATASET_REPO,
                "source": DATASET_SOURCE,
                "revision": DATASET_REVISION,
                "config": DATASET_CONFIG,
                "split": DATASET_SPLIT,
                "selected_file_count": len(DATASET_FILES),
                "selected_crawls": [item["crawl"] for item in DATASET_FILES],
                "parquet_byte_count": DATASET_BYTE_COUNT,
            },
            "raw_root": str(raw_root),
            "raw_artifacts": raw_artifacts,
            "prior_pilot_source_root": str(r1_source_root),
            "prior_pilot_manifest_sha256": R1_SOURCE_MANIFEST_SHA256,
            "prior_pilot_row_range": {"start": 0, "end_exclusive": 2048, "count_per_shard": 2048},
            "fresh_row_range": {"start": FRESH_ROW_START, "end_exclusive": FRESH_ROW_END, "count_per_shard": FRESH_ROW_COUNT},
            "datasets": {
                "fit/fineweb_edu": {
                    "source": DATASET_SOURCE,
                    "revision": DATASET_REVISION,
                    "config": DATASET_CONFIG,
                    "split": DATASET_SPLIT,
                    "crawl": DATASET_FILES[0]["crawl"],
                    "source_path": DATASET_FILES[0]["path"],
                    "row_start": FRESH_ROW_START,
                    "row_count": fit_count,
                    "normalized_path": SOURCE_FILES["fit/fineweb_edu"].as_posix(),
                    "normalized_sha256": sha256_file(staging / SOURCE_FILES["fit/fineweb_edu"]),
                },
                "assessment/fineweb_edu": {
                    "source": DATASET_SOURCE,
                    "revision": DATASET_REVISION,
                    "config": DATASET_CONFIG,
                    "split": DATASET_SPLIT,
                    "crawl": DATASET_FILES[1]["crawl"],
                    "source_path": DATASET_FILES[1]["path"],
                    "row_start": FRESH_ROW_START,
                    "row_count": assessment_count,
                    "normalized_path": SOURCE_FILES["assessment/fineweb_edu"].as_posix(),
                    "normalized_sha256": sha256_file(staging / SOURCE_FILES["assessment/fineweb_edu"]),
                },
            },
            "network_access": False,
            "training": False,
            "scientific_execution": False,
            "evidence_ledger_mutation": False,
            "created_at_utc": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        }
        manifest = {**body, "manifest_sha256": digest(body)}
        (staging / "acquisition-manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        environment = os.environ.copy()
        environment["PYTHONDONTWRITEBYTECODE"] = "1"
        completed = subprocess.run(
            [sys.executable, "-B", str(VALIDATOR), "--source-root", str(staging), "--raw-root", str(raw_root), "--r1-source-root", str(r1_source_root)],
            cwd=REPO_ROOT,
            env=environment,
            capture_output=True,
            text=True,
            check=False,
        )
        if completed.returncode != 0:
            raise RuntimeError(f"V2 source validation failed:\n{completed.stdout}\n{completed.stderr}")
        validation = json.loads(completed.stdout)
        if not isinstance(validation, dict) or validation.get("valid") is not True:
            raise RuntimeError(f"V2 source validator returned invalid output: {validation}")
        os.replace(staging, source_root)
        return {"manifest": manifest, "validation": validation}
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-root", type=Path, required=True)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--r1-source-root", type=Path, default=R1_SOURCE_ROOT)
    args = parser.parse_args()
    print(json.dumps(pack(args.raw_root, args.source_root, args.r1_source_root), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
