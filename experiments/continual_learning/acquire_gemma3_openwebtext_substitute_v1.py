#!/usr/bin/env python3
"""Acquire a pinned OpenWebText substitute for bounded Gemma3 recirculation.

State slice: continual-learning-gemma3-paper-recirculation-openwebtext-substitute-v1.

This is the network-enabled acquisition boundary for the OpenWebText
substitute lane. It downloads the pinned Parquet release outside the
repository, records file checksums and the upstream revision, and publishes a
small document-disjoint normalized source panel only after independent
readback validation. It never loads the model, trains, or runs recirculation.
The resulting source is not TFDS ``c4/webtextlike``.
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

STATE_SLICE = (
    "continual-learning-gemma3-paper-recirculation-"
    "openwebtext-substitute-v1"
)
CLAIM_CEILING = "LocalDevelopmentGemma3OpenWebTextSubstitutePilot"
SOURCE_SCHEMA = "gemma3-openwebtext-substitute-acquisition-v1"
DATASET_REPO = "Skylion007/openwebtext"
DATASET_REVISION = "79d93d786212f7344586290adb811d4ae6a1762c"
DATASET_CONFIG = "plain_text"
DATASET_SPLIT = "train"
DATASET_FILE_COUNT = 80
DATASET_ROW_COUNT = 8_013_769
# This is the aggregate size of the pinned Parquet download. The dataset card
# separately reports 39,769,491,688 decoded bytes.
DATASET_BYTE_COUNT = 24_193_092_408
FIT_ROW_START = 0
ASSESSMENT_ROW_START = 1_000_000
ROWS_PER_PANEL = 256
SOURCE_FILES = {
    "fit/openwebtext": Path("fit/openwebtext.jsonl"),
    "assessment/openwebtext": Path("assessment/openwebtext.jsonl"),
}
DEFAULT_RAW_ROOT = Path(
    "/Volumes/PrimaryED/ResearchArtifacts/composed-zk-benchmark-os/"
    "gemma3-openwebtext-substitute-raw-v1"
)
DEFAULT_SOURCE_ROOT = Path(
    "/Volumes/PrimaryED/ResearchArtifacts/composed-zk-benchmark-os/"
    "gemma3-openwebtext-substitute-source-v1"
)
VALIDATOR = Path(__file__).with_name(
    "validate_gemma3_openwebtext_substitute_v1.py"
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


def _write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    seen: set[str] = set()
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
            handle.write(json.dumps({"document_id": document_id, "text": text}, sort_keys=True))
            handle.write("\n")
            count += 1
    return count


def _download_dataset(raw_root: Path, *, resume: bool) -> Path:
    dataset_root = raw_root / "dataset"
    if dataset_root.exists() and not dataset_root.is_dir():
        raise ValueError(f"dataset download root is not a directory: {dataset_root}")
    dataset_root.mkdir(parents=True, exist_ok=True)
    from huggingface_hub import snapshot_download

    snapshot_download(
        repo_id=DATASET_REPO,
        repo_type="dataset",
        revision=DATASET_REVISION,
        local_dir=str(dataset_root),
        allow_patterns=["plain_text/*.parquet"],
        max_workers=4,
        tqdm_class=None,
    )
    if not resume:
        expected = [
            dataset_root / "plain_text" / f"train-{index:05d}-of-00080.parquet"
            for index in range(DATASET_FILE_COUNT)
        ]
        missing = [str(path) for path in expected if not path.is_file()]
        if missing:
            raise FileNotFoundError(f"pinned OpenWebText download is incomplete: {missing[:3]}")
    return dataset_root


def _parquet_files(dataset_root: Path) -> list[Path]:
    files = sorted((dataset_root / "plain_text").glob("train-*-of-00080.parquet"))
    if len(files) != DATASET_FILE_COUNT or any(path.is_symlink() for path in files):
        raise ValueError(
            f"expected {DATASET_FILE_COUNT} regular OpenWebText Parquet shards, found {len(files)}"
        )
    return [_regular(path, "OpenWebText Parquet shard") for path in files]


def _row_counts(files: list[Path]) -> list[int]:
    import pyarrow.parquet as pq

    counts = []
    for path in files:
        count = pq.ParquetFile(path).metadata.num_rows
        if not isinstance(count, int) or count <= 0:
            raise ValueError(f"OpenWebText shard has invalid row count: {path}")
        counts.append(count)
    if sum(counts) != DATASET_ROW_COUNT:
        raise ValueError(
            f"OpenWebText row count mismatch: {sum(counts)} != {DATASET_ROW_COUNT}"
        )
    return counts


def _rows_in_range(
    files: list[Path],
    counts: list[int],
    start: int,
    count: int,
) -> Iterator[dict[str, Any]]:
    import pyarrow.parquet as pq

    end = start + count
    global_index = 0
    selected = 0
    for path, row_count in zip(files, counts):
        shard_start = global_index
        shard_end = global_index + row_count
        if shard_end <= start:
            global_index = shard_end
            continue
        if shard_start >= end:
            break
        parquet = pq.ParquetFile(path)
        for batch in parquet.iter_batches(columns=["text"], batch_size=256):
            for text in batch.column("text").to_pylist():
                if start <= global_index < end:
                    if not isinstance(text, str) or not text.strip():
                        raise ValueError(f"OpenWebText row has empty text at {global_index}")
                    yield {
                        "document_id": f"openwebtext:train:{global_index:08d}",
                        "text": text,
                    }
                    selected += 1
                global_index += 1
                if global_index >= end:
                    break
            if global_index >= end:
                break
        if selected >= count:
            break
    if selected != count:
        raise ValueError(f"selected {selected} rows from range {start}:{end}, expected {count}")


def _raw_artifacts(raw_root: Path, files: list[Path], counts: list[int]) -> list[dict[str, Any]]:
    artifacts = []
    for path, row_count in zip(files, counts):
        artifacts.append(
            {
                "relative_path": path.relative_to(raw_root).as_posix(),
                "byte_len": path.stat().st_size,
                "sha256": sha256_file(path),
                "row_count": row_count,
                "source": (
                    f"https://huggingface.co/datasets/{DATASET_REPO}/resolve/"
                    f"{DATASET_REVISION}/{path.relative_to(raw_root / 'dataset').as_posix()}"
                ),
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

    _download_dataset(raw_root, resume=resume)
    dataset_root = raw_root / "dataset"
    files = _parquet_files(dataset_root)
    counts = _row_counts(files)
    byte_count = sum(path.stat().st_size for path in files)
    if byte_count != DATASET_BYTE_COUNT:
        raise ValueError(f"OpenWebText byte count mismatch: {byte_count} != {DATASET_BYTE_COUNT}")

    temporary_source = Path(
        tempfile.mkdtemp(prefix=f".{source_root.name}.staging-", dir=source_root.parent)
    )
    try:
        fit_path = temporary_source / SOURCE_FILES["fit/openwebtext"]
        assessment_path = temporary_source / SOURCE_FILES["assessment/openwebtext"]
        fit_count = _write_jsonl(
            fit_path, _rows_in_range(files, counts, FIT_ROW_START, ROWS_PER_PANEL)
        )
        assessment_count = _write_jsonl(
            assessment_path,
            _rows_in_range(files, counts, ASSESSMENT_ROW_START, ROWS_PER_PANEL),
        )
        raw_artifacts = _raw_artifacts(raw_root, files, counts)
        dataset_url = f"https://huggingface.co/datasets/{DATASET_REPO}"
        body = {
            "schema": SOURCE_SCHEMA,
            "state_slice": STATE_SLICE,
            "claim_ceiling": CLAIM_CEILING,
            "source_record_schema": "gemma3-source-v1-compatible",
            "selection_policy": "fixed-global-row-ranges-document-disjoint-v1",
            "paper_alignment": "mechanism_only_not_c4_webtextlike_replication",
            "dataset": {
                "repo": DATASET_REPO,
                "source": dataset_url,
                "revision": DATASET_REVISION,
                "config": DATASET_CONFIG,
                "split": DATASET_SPLIT,
                "shard_count": DATASET_FILE_COUNT,
                "row_count": DATASET_ROW_COUNT,
                "parquet_byte_count": DATASET_BYTE_COUNT,
            },
            "raw_root": str(raw_root),
            "raw_artifacts": raw_artifacts,
            "datasets": {
                "fit/openwebtext": {
                    "source": dataset_url,
                    "revision": DATASET_REVISION,
                    "config": DATASET_CONFIG,
                    "split": DATASET_SPLIT,
                    "row_start": FIT_ROW_START,
                    "row_count": fit_count,
                    "normalized_path": SOURCE_FILES["fit/openwebtext"].as_posix(),
                    "normalized_sha256": sha256_file(fit_path),
                },
                "assessment/openwebtext": {
                    "source": dataset_url,
                    "revision": DATASET_REVISION,
                    "config": DATASET_CONFIG,
                    "split": DATASET_SPLIT,
                    "row_start": ASSESSMENT_ROW_START,
                    "row_count": assessment_count,
                    "normalized_path": SOURCE_FILES["assessment/openwebtext"].as_posix(),
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
