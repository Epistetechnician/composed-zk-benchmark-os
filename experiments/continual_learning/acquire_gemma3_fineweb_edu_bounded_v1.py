#!/usr/bin/env python3
"""Acquire a small, metadata-preserving FineWeb-Edu Gemma3 pilot bundle.

State slice: continual-learning-gemma3-fineweb-edu-bounded-v1.

This is the only network-enabled boundary for the FineWeb-Edu bounded pilot.
It downloads two exact upstream Parquet shards outside the repository,
verifies their pinned LFS SHA-256 values, and publishes disjoint normalized
fit/assessment records only after the independent source validator passes.
It never loads a model, trains, or runs the recirculation measurement.
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
from typing import Any, Iterable, Iterator

REPO_ROOT = Path(__file__).resolve().parents[2]
PRIMARY_VOLUME = Path("/Volumes/PrimaryED")
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

STATE_SLICE = "continual-learning-gemma3-fineweb-edu-bounded-v1"
CLAIM_CEILING = "LocalDevelopmentGemma3FineWebEduBoundedPilot"
SOURCE_SCHEMA = "gemma3-fineweb-edu-bounded-acquisition-v1"
DATASET_REPO = "HuggingFaceFW/fineweb-edu"
DATASET_REVISION = "87f09149ef4734204d70ed1d046ddc9ca3f2b8f9"
DATASET_SOURCE = f"https://huggingface.co/datasets/{DATASET_REPO}"
DATASET_FILES = (
    {
        "crawl": "CC-MAIN-2013-20",
        "path": "data/CC-MAIN-2013-20/train-00000-of-00014.parquet",
        "byte_len": 2_369_456_837,
        "sha256": "fb989c566f6fba00ab61decc5f7aa1538a07d9b142e58a52ff790154528ffd03",
        "lfs_sha256": "fb989c566f6fba00ab61decc5f7aa1538a07d9b142e58a52ff790154528ffd03",
    },
    {
        "crawl": "CC-MAIN-2024-10",
        "path": "data/CC-MAIN-2024-10/000_00000.parquet",
        "byte_len": 1_911_528_585,
        "sha256": "89c802096c8adb54cdcfad567c13838814d83dbb4dbcda008a0f740e73f8a484",
        "lfs_sha256": "89c802096c8adb54cdcfad567c13838814d83dbb4dbcda008a0f740e73f8a484",
    },
)
DATASET_BYTE_COUNT = sum(item["byte_len"] for item in DATASET_FILES)
ROWS_PER_PANEL = 2048
FIT_FILE_INDEX = 0
ASSESSMENT_FILE_INDEX = 1
FIT_ROW_START = 0
ASSESSMENT_ROW_START = 0
SOURCE_FILES = {
    "fit/fineweb_edu": Path("fit/fineweb_edu.jsonl"),
    "assessment/fineweb_edu": Path("assessment/fineweb_edu.jsonl"),
}
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
DEFAULT_RAW_ROOT = Path(
    "/Volumes/PrimaryED/ResearchArtifacts/composed-zk-benchmark-os/"
    "gemma3-fineweb-edu-bounded-raw-v1"
)
DEFAULT_SOURCE_ROOT = Path(
    "/Volumes/PrimaryED/ResearchArtifacts/composed-zk-benchmark-os/"
    "gemma3-fineweb-edu-bounded-source-v1"
)
VALIDATOR = Path(__file__).with_name(
    "validate_gemma3_fineweb_edu_bounded_v1.py"
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


def _write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _json_value(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


def _write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    seen: set[str] = set()
    count = 0
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            document_id = row.get("document_id")
            text = row.get("text")
            if not isinstance(document_id, str) or not document_id:
                raise ValueError("normalized record requires document_id")
            if document_id in seen:
                raise ValueError(f"duplicate normalized document_id: {document_id}")
            if not isinstance(text, str) or not text.strip():
                raise ValueError(f"normalized record requires non-empty text: {document_id}")
            seen.add(document_id)
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True))
            handle.write("\n")
            count += 1
    if count != ROWS_PER_PANEL:
        raise ValueError(f"normalized record count {count} != {ROWS_PER_PANEL}")
    return count


def _download_dataset(raw_root: Path, *, resume: bool) -> Path:
    dataset_root = raw_root / "dataset"
    if dataset_root.exists() and not dataset_root.is_dir():
        raise ValueError(f"dataset root is not a directory: {dataset_root}")
    dataset_root.mkdir(parents=True, exist_ok=True)
    from huggingface_hub import snapshot_download

    snapshot_download(
        repo_id=DATASET_REPO,
        repo_type="dataset",
        revision=DATASET_REVISION,
        local_dir=str(dataset_root),
        allow_patterns=[item["path"] for item in DATASET_FILES],
        max_workers=2,
        tqdm_class=None,
    )
    for item in DATASET_FILES:
        path = _regular(dataset_root / item["path"], "FineWeb-Edu Parquet shard")
        if path.stat().st_size != item["byte_len"]:
            raise ValueError(f"pinned byte length mismatch: {path}")
        if sha256_file(path) != item["sha256"]:
            raise ValueError(f"pinned SHA-256 mismatch: {path}")
    if not resume:
        expected = {dataset_root / item["path"] for item in DATASET_FILES}
        actual = {
            path
            for path in dataset_root.rglob("*.parquet")
            if path.is_file() and not path.is_symlink()
        }
        if actual != expected:
            raise ValueError(f"downloaded Parquet set differs from the two-file pin: {sorted(actual)}")
    return dataset_root


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
                text = values["text"][offset]
                if not isinstance(text, str) or not text.strip():
                    raise ValueError(f"FineWeb-Edu row has empty text at {global_index}: {path}")
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
            if global_index >= end:
                break
        if global_index >= end:
            break
    if selected != count:
        raise ValueError(f"selected {selected} rows from {path}:{start}:{end}, expected {count}")


def _raw_artifacts(raw_root: Path, dataset_root: Path) -> list[dict[str, Any]]:
    import pyarrow.parquet as pq

    artifacts = []
    for item in DATASET_FILES:
        path = _regular(dataset_root / item["path"], "FineWeb-Edu Parquet shard")
        artifacts.append(
            {
                "relative_path": path.relative_to(raw_root).as_posix(),
                "source": f"{DATASET_SOURCE}/resolve/{DATASET_REVISION}/{item['path']}",
                "crawl": item["crawl"],
                "byte_len": path.stat().st_size,
                "sha256": sha256_file(path),
                "lfs_sha256": item["lfs_sha256"],
                "row_count": pq.ParquetFile(path).metadata.num_rows,
            }
        )
    return artifacts


def acquire(raw_root: Path, source_root: Path, *, resume: bool = False) -> dict[str, Any]:
    raw_root = _primary(raw_root, "raw root")
    source_root = _primary(source_root, "source root")
    if source_root.exists() or source_root.is_symlink():
        raise FileExistsError(f"refusing to overwrite source root: {source_root}")
    if raw_root.exists():
        if not resume or raw_root.is_symlink() or not raw_root.is_dir():
            raise FileExistsError(f"raw root exists; pass --resume only for a regular directory: {raw_root}")
    else:
        raw_root.mkdir(parents=True)

    dataset_root = _download_dataset(raw_root, resume=resume)
    raw_artifacts = _raw_artifacts(raw_root, dataset_root)
    temporary_source = Path(
        tempfile.mkdtemp(prefix=f".{source_root.name}.staging-", dir=source_root.parent)
    )
    try:
        fit_path = temporary_source / SOURCE_FILES["fit/fineweb_edu"]
        assessment_path = temporary_source / SOURCE_FILES["assessment/fineweb_edu"]
        fit_count = _write_jsonl(
            fit_path,
            _parquet_rows(dataset_root / DATASET_FILES[FIT_FILE_INDEX]["path"], DATASET_FILES[FIT_FILE_INDEX], FIT_ROW_START, ROWS_PER_PANEL),
        )
        assessment_count = _write_jsonl(
            assessment_path,
            _parquet_rows(dataset_root / DATASET_FILES[ASSESSMENT_FILE_INDEX]["path"], DATASET_FILES[ASSESSMENT_FILE_INDEX], ASSESSMENT_ROW_START, ROWS_PER_PANEL),
        )
        body = {
            "schema": SOURCE_SCHEMA,
            "state_slice": STATE_SLICE,
            "claim_ceiling": CLAIM_CEILING,
            "source_record_schema": "gemma3-source-v1-compatible-with-fineweb-metadata",
            "selection_policy": "first-2048-records-from-two-pinned-crawls-document-disjoint-v1",
            "paper_alignment": "mechanism_only_not_c4_webtextlike_replication",
            "dataset": {
                "repo": DATASET_REPO,
                "source": DATASET_SOURCE,
                "revision": DATASET_REVISION,
                "config": "fineweb-edu-crawl-shards",
                "split": "train",
                "selected_file_count": len(DATASET_FILES),
                "selected_crawls": [item["crawl"] for item in DATASET_FILES],
                "parquet_byte_count": DATASET_BYTE_COUNT,
            },
            "raw_root": str(raw_root),
            "raw_artifacts": raw_artifacts,
            "datasets": {
                "fit/fineweb_edu": {
                    "source": DATASET_SOURCE,
                    "revision": DATASET_REVISION,
                    "config": "fineweb-edu-crawl-shards",
                    "split": "train",
                    "crawl": DATASET_FILES[FIT_FILE_INDEX]["crawl"],
                    "source_path": DATASET_FILES[FIT_FILE_INDEX]["path"],
                    "row_start": FIT_ROW_START,
                    "row_count": fit_count,
                    "normalized_path": SOURCE_FILES["fit/fineweb_edu"].as_posix(),
                    "normalized_sha256": sha256_file(fit_path),
                },
                "assessment/fineweb_edu": {
                    "source": DATASET_SOURCE,
                    "revision": DATASET_REVISION,
                    "config": "fineweb-edu-crawl-shards",
                    "split": "train",
                    "crawl": DATASET_FILES[ASSESSMENT_FILE_INDEX]["crawl"],
                    "source_path": DATASET_FILES[ASSESSMENT_FILE_INDEX]["path"],
                    "row_start": ASSESSMENT_ROW_START,
                    "row_count": assessment_count,
                    "normalized_path": SOURCE_FILES["assessment/fineweb_edu"].as_posix(),
                    "normalized_sha256": sha256_file(assessment_path),
                },
            },
            "network_access": True,
            "training": False,
            "scientific_execution": False,
            "evidence_ledger_mutation": False,
            "created_at_utc": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        }
        manifest = {**body, "manifest_sha256": digest(body)}
        _write_json(temporary_source / "acquisition-manifest.json", manifest)
        environment = os.environ.copy()
        environment["PYTHONDONTWRITEBYTECODE"] = "1"
        subprocess.run(
            [sys.executable, "-B", str(VALIDATOR), "--source-root", str(temporary_source)],
            cwd=REPO_ROOT,
            env=environment,
            check=True,
        )
        os.replace(temporary_source, source_root)
        return manifest
    except Exception:
        shutil.rmtree(temporary_source, ignore_errors=True)
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-root", type=Path, default=DEFAULT_RAW_ROOT)
    parser.add_argument("--source-root", type=Path, default=DEFAULT_SOURCE_ROOT)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    print(json.dumps(acquire(args.raw_root, args.source_root, resume=args.resume), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
