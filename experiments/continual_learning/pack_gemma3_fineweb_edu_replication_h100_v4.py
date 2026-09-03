#!/usr/bin/env python3
"""Pack and revalidate the exact H100 FineWeb-Edu input contract.

State slice: continual-learning-gemma3-fineweb-edu-replication-h100-v4.

This is a network-free packer.  Acquisition happens outside this module.  It
reads only the two pinned Parquet objects already present below the external
PrimaryED raw root, rederives the fresh row interval and all excluded IDs, and
publishes no-overwrite source and token-window bundles below external custody.
It never loads model weights, trains, or runs the recurrence.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any, Iterable, Iterator


STATE_SLICE = "continual-learning-gemma3-fineweb-edu-replication-h100-v4"
SOURCE_SCHEMA = "gemma3-fineweb-edu-replication-h100-v4-source"
CORPUS_SCHEMA = "gemma3-fineweb-edu-replication-h100-v4-corpus"
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
FRESH_START, FRESH_END = 67_584, 83_968
WINDOW_TOKENS, WINDOW_COUNT = 1_024, 64
EXCLUSION_RANGES = (
    ("prior-pilot", 0, 2_048),
    ("prior-v31", 2_048, 18_432),
    ("discarded", 18_432, 34_816), ("prior-h100-v1", 34_816, 51_200),
    ("prior-h100-v3", 51_200, FRESH_START),
)
NORMALIZED_FIELDS = (
    "id", "url", "date", "dump", "file_path", "language", "language_score",
    "token_count", "score", "int_score",
)


def canonical(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def digest(value: dict[str, Any], field: str = "manifest_sha256") -> str:
    return hashlib.sha256(canonical({k: v for k, v in value.items() if k != field})).hexdigest()


def sha256_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def canonical_jsonl(rows: Iterable[dict[str, Any]]) -> bytes:
    return b"".join(
        (json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8")
        for row in rows
    )


def _external(path: Path, label: str) -> Path:
    path = path.expanduser()
    if path.is_symlink():
        raise ValueError(f"{label} must not be a symlink")
    resolved = path.resolve()
    repository = Path(__file__).resolve().parents[2]
    if resolved == repository or repository in resolved.parents:
        raise ValueError(f"{label} must be outside the repository")
    if not resolved.is_absolute() or resolved.parts[1:2] != ("Volumes",):
        raise ValueError(f"{label} must be below an external mounted volume")
    return resolved


def _regular(path: Path, label: str) -> Path:
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"{label} must be a regular file: {path}")
    return path


def _exact_files(root: Path, expected: set[str], label: str) -> None:
    if root.is_symlink() or not root.is_dir():
        raise ValueError(f"{label} root is not a real directory")
    actual = set()
    for path in root.rglob("*"):
        if path.is_symlink():
            raise ValueError(f"{label} contains symlink: {path}")
        if path.is_file():
            actual.add(path.relative_to(root).as_posix())
    if actual != expected:
        raise ValueError(f"{label} exact file set mismatch: {sorted(actual)}")


def _readonly(root: Path, label: str) -> None:
    if root.is_symlink() or not root.is_dir():
        raise ValueError(f"{label} root is not a real directory")
    if root.stat().st_mode & 0o222:
        raise ValueError(f"{label} root is mutable")
    for path in root.rglob("*"):
        if path.is_symlink():
            raise ValueError(f"{label} contains symlink: {path}")
        if path.stat().st_mode & 0o222:
            raise ValueError(f"{label} contains mutable entry: {path}")


def _make_readonly(root: Path) -> None:
    for path in sorted(root.rglob("*"), reverse=True):
        if path.is_file():
            path.chmod(0o444)
        elif path.is_dir():
            path.chmod(0o555)
    root.chmod(0o555)


def _json_value(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


def parquet_rows(path: Path, item: dict[str, Any], start: int, end: int) -> Iterator[dict[str, Any]]:
    import pyarrow.parquet as pq

    parquet = pq.ParquetFile(path)
    if "text" not in parquet.schema.names:
        raise ValueError(f"FineWeb-Edu shard has no text column: {path}")
    fields = [field for field in NORMALIZED_FIELDS if field in parquet.schema.names]
    columns = ["text", *fields]
    position = 0
    selected = 0
    for batch in parquet.iter_batches(columns=columns, batch_size=256):
        values = {name: batch.column(name).to_pylist() for name in columns}
        for offset in range(batch.num_rows):
            if start <= position < end:
                text = values["text"][offset]
                if not isinstance(text, str) or not text.strip():
                    raise ValueError(f"empty text at row {position}: {path}")
                upstream_id = values.get("id", [None] * batch.num_rows)[offset]
                if not isinstance(upstream_id, str) or not upstream_id:
                    upstream_id = f"row-{position:08d}"
                metadata = {
                    field: _json_value(values[field][offset])
                    for field in fields
                    if values[field][offset] is not None
                }
                body = {
                    "document_id": f"fineweb-edu:{item['crawl']}:{upstream_id}",
                    "text": text,
                    "metadata": metadata,
                    "source_crawl": item["crawl"],
                    "source_path": item["path"],
                    "source_row_index": position,
                    "source_row_id": upstream_id,
                }
                yield {**body, "source_row_sha256": digest(body, "source_row_sha256")}
                selected += 1
            position += 1
            if position >= end:
                break
        if position >= end:
            break
    if selected != end - start:
        raise ValueError(f"expected {end - start} rows from {path}, got {selected}")


def raw_artifacts(raw_root: Path) -> list[dict[str, Any]]:
    import pyarrow.parquet as pq

    dataset_root = raw_root / "dataset"
    expected = {Path("dataset") / item["path"] for item in DATASET_FILES}
    actual = set()
    for path in dataset_root.rglob("*"):
        if path.is_symlink():
            raise ValueError(f"raw dataset contains symlink: {path}")
        if path.is_file():
            actual.add(path.relative_to(raw_root))
    if actual != expected:
        raise ValueError("raw Parquet file set is not the exact two-file pin")
    artifacts = []
    for item in DATASET_FILES:
        path = _regular(raw_root / Path("dataset") / item["path"], "FineWeb-Edu Parquet")
        if path.stat().st_size != item["byte_len"] or sha256_file(path) != item["sha256"]:
            raise ValueError(f"raw Parquet pin mismatch: {path}")
        count = pq.ParquetFile(path).metadata.num_rows
        if count < FRESH_END:
            raise ValueError(f"raw Parquet is shorter than the fresh interval: {path}")
        artifacts.append({
            "crawl": item["crawl"],
            "relative_path": path.relative_to(raw_root).as_posix(),
            "source": f"{DATASET_SOURCE}/resolve/{DATASET_REVISION}/{item['path']}",
            "byte_len": path.stat().st_size,
            "sha256": sha256_file(path),
            "row_count": count,
        })
    return artifacts


def validate_source_bundle(raw_root: Path, source_root: Path) -> tuple[dict[str, Any], dict[str, list[dict[str, Any]]]]:
    """Recompute source rows, raw pins, and exclusions from raw custody."""
    _readonly(raw_root, "raw bundle")
    _readonly(source_root, "source bundle")
    _exact_files(
        source_root,
        {"manifest.json", "fit/fineweb_edu.jsonl", "assessment/fineweb_edu.jsonl"},
        "source bundle",
    )
    manifest = json.loads((source_root / "manifest.json").read_text(encoding="utf-8"))
    expected_keys = {
        "schema", "state_slice", "dataset", "raw_root", "raw_artifacts",
        "fresh_row_range", "split_sources", "excluded_ranges",
        "excluded_id_sha256", "network_access", "training",
        "scientific_execution", "evidence_ledger_mutation", "manifest_sha256",
    }
    if not isinstance(manifest, dict) or set(manifest) != expected_keys:
        raise ValueError("source manifest schema is not closed")
    expected_dataset = {
        "repo": DATASET_REPO, "source": DATASET_SOURCE, "revision": DATASET_REVISION,
        "config": DATASET_CONFIG, "split": DATASET_SPLIT,
    }
    if (
        manifest["schema"] != SOURCE_SCHEMA
        or manifest["state_slice"] != STATE_SLICE
        or manifest["dataset"] != expected_dataset
        or manifest["raw_root"] != "raw"
        or manifest["fresh_row_range"] != {"start": FRESH_START, "end_exclusive": FRESH_END, "count_per_shard": FRESH_END - FRESH_START}
        or manifest["excluded_ranges"] != [
            {"name": name, "start": start, "end_exclusive": end, "count_per_shard": end - start}
            for name, start, end in EXCLUSION_RANGES
        ]
        or manifest["network_access"] is not False
        or manifest["training"] is not False
        or manifest["scientific_execution"] is not False
        or manifest["evidence_ledger_mutation"] is not False
        or manifest["manifest_sha256"] != digest(manifest)
    ):
        raise ValueError("source manifest contract mismatch")
    split_sources = manifest["split_sources"]
    if not isinstance(split_sources, dict) or set(split_sources) != {"fit", "assessment"}:
        raise ValueError("source split metadata schema is not closed")
    if manifest["raw_artifacts"] != raw_artifacts(raw_root):
        raise ValueError("source raw artifact binding mismatch")
    excluded_ids: list[str] = []
    for item in DATASET_FILES:
        path = raw_root / "dataset" / item["path"]
        for _name, start, end in EXCLUSION_RANGES:
            excluded_ids.extend(row["document_id"] for row in parquet_rows(path, item, start, end))
    if manifest["excluded_id_sha256"] != hashlib.sha256(canonical(excluded_ids)).hexdigest():
        raise ValueError("source excluded ID binding mismatch")
    rows_by_split: dict[str, list[dict[str, Any]]] = {}
    all_ids: set[str] = set()
    expected_split_sources = {
        "fit": DATASET_FILES[0],
        "assessment": DATASET_FILES[1],
    }
    for split, item in expected_split_sources.items():
        metadata = split_sources[split]
        expected_metadata = {
            "crawl": item["crawl"], "source_path": item["path"], "row_start": FRESH_START,
            "row_end_exclusive": FRESH_END, "normalized_path": f"{split}/fineweb_edu.jsonl",
        }
        if not isinstance(metadata, dict) or set(metadata) != set(expected_metadata) | {"normalized_sha256"} or any(metadata.get(k) != v for k, v in expected_metadata.items()):
            raise ValueError(f"source {split} metadata mismatch")
        path = source_root / metadata["normalized_path"]
        if sha256_file(path) != metadata.get("normalized_sha256"):
            raise ValueError(f"source {split} digest mismatch")
        observed = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
        expected = list(parquet_rows(raw_root / "dataset" / item["path"], item, FRESH_START, FRESH_END))
        if path.read_bytes() != canonical_jsonl(expected) or observed != expected:
            raise ValueError(f"source {split} rows do not rederive from raw custody")
        split_ids = {row["document_id"] for row in observed}
        if len(split_ids) != len(observed) or all_ids & split_ids:
            raise ValueError("source document IDs are not globally unique")
        all_ids.update(split_ids)
        rows_by_split[split] = observed
    return manifest, rows_by_split


def _write_jsonl(path: Path, rows: Iterable[dict[str, Any]], expected_count: int) -> str:
    seen: set[str] = set()
    count = 0
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            if row["document_id"] in seen:
                raise ValueError(f"duplicate document ID: {row['document_id']}")
            seen.add(row["document_id"])
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
            count += 1
    if count != expected_count:
        raise ValueError(f"expected {expected_count} records, got {count}")
    return sha256_file(path)


def pack_source(raw_root: Path, source_root: Path) -> dict[str, Any]:
    raw_root = _external(raw_root, "raw root")
    source_root = _external(source_root, "source root")
    if source_root.exists() or source_root.is_symlink():
        raise FileExistsError(f"refusing to overwrite source root: {source_root}")
    _readonly(raw_root, "raw bundle")
    artifacts = raw_artifacts(raw_root)
    excluded_ids: list[str] = []
    for item in DATASET_FILES:
        path = raw_root / "dataset" / item["path"]
        for name, start, end in EXCLUSION_RANGES:
            excluded_ids.extend(row["document_id"] for row in parquet_rows(path, item, start, end))
    if len(excluded_ids) != 2 * FRESH_START or len(set(excluded_ids)) != len(excluded_ids):
        raise ValueError("excluded source ID proof is not unique")
    staging = Path(tempfile.mkdtemp(prefix=f".{source_root.name}.staging-", dir=source_root.parent))
    try:
        fit_path = staging / "fit/fineweb_edu.jsonl"
        assessment_path = staging / "assessment/fineweb_edu.jsonl"
        fit_path.parent.mkdir(parents=True)
        assessment_path.parent.mkdir(parents=True)
        fit_sha = _write_jsonl(
            fit_path,
            parquet_rows(raw_root / "dataset" / DATASET_FILES[0]["path"], DATASET_FILES[0], FRESH_START, FRESH_END),
            FRESH_END - FRESH_START,
        )
        assessment_sha = _write_jsonl(
            assessment_path,
            parquet_rows(raw_root / "dataset" / DATASET_FILES[1]["path"], DATASET_FILES[1], FRESH_START, FRESH_END),
            FRESH_END - FRESH_START,
        )
        body = {
            "schema": SOURCE_SCHEMA,
            "state_slice": STATE_SLICE,
            "dataset": {
                "repo": DATASET_REPO,
                "source": DATASET_SOURCE,
                "revision": DATASET_REVISION,
                "config": DATASET_CONFIG,
                "split": DATASET_SPLIT,
            },
            "raw_root": "raw",
            "raw_artifacts": artifacts,
            "fresh_row_range": {"start": FRESH_START, "end_exclusive": FRESH_END, "count_per_shard": FRESH_END - FRESH_START},
            "split_sources": {
                "fit": {"crawl": DATASET_FILES[0]["crawl"], "source_path": DATASET_FILES[0]["path"], "row_start": FRESH_START, "row_end_exclusive": FRESH_END, "normalized_path": "fit/fineweb_edu.jsonl", "normalized_sha256": fit_sha},
                "assessment": {"crawl": DATASET_FILES[1]["crawl"], "source_path": DATASET_FILES[1]["path"], "row_start": FRESH_START, "row_end_exclusive": FRESH_END, "normalized_path": "assessment/fineweb_edu.jsonl", "normalized_sha256": assessment_sha},
            },
            "excluded_ranges": [
                {"name": name, "start": start, "end_exclusive": end, "count_per_shard": end - start}
                for name, start, end in EXCLUSION_RANGES
            ],
            "excluded_id_sha256": hashlib.sha256(canonical(excluded_ids)).hexdigest(),
            "network_access": False,
            "training": False,
            "scientific_execution": False,
            "evidence_ledger_mutation": False,
        }
        manifest = {**body, "manifest_sha256": digest(body)}
        (staging / "manifest.json").write_bytes(canonical(manifest))
        _make_readonly(staging)
        os.replace(staging, source_root)
        return manifest
    except Exception:
        for path in sorted(staging.rglob("*"), reverse=True):
            if path.is_file():
                path.unlink()
        for directory in sorted((path for path in staging.rglob("*") if path.is_dir()), reverse=True):
            directory.rmdir()
        staging.rmdir()
        raise


def pack_corpus(raw_root: Path, source_root: Path, corpus_root: Path, model_root: Path, tokenizer: Any) -> dict[str, Any]:
    raw_root = _external(raw_root, "raw root")
    source_root = _external(source_root, "source root")
    corpus_root = _external(corpus_root, "corpus root")
    model_root = _external(model_root, "model root")
    if corpus_root.exists() or corpus_root.is_symlink():
        raise FileExistsError(f"refusing to overwrite corpus root: {corpus_root}")
    source_manifest, source_rows = validate_source_bundle(raw_root, source_root)
    staging = Path(tempfile.mkdtemp(prefix=f".{corpus_root.name}.staging-", dir=corpus_root.parent))
    try:
        split_sha: dict[str, str] = {}
        for split in ("fit", "assessment"):
            windows = []
            for row in source_rows[split]:
                token_ids = tuple(int(value) for value in tokenizer.encode(row["text"], add_special_tokens=False))
                if len(token_ids) < WINDOW_TOKENS:
                    continue
                ids = list(token_ids[:WINDOW_TOKENS])
                text = tokenizer.decode(ids)
                window = {
                    "dataset": "fineweb_edu",
                    "document_id": row["document_id"],
                    "relative_path": f"{split}/window-{len(windows):06d}.txt",
                    "window_ordinal": 0,
                    "text": text,
                    "source_sha256": hashlib.sha256(row["text"].encode()).hexdigest(),
                    "source_row_sha256": row["source_row_sha256"],
                    "source_row_index": row["source_row_index"],
                    "source_row_id": row["source_row_id"],
                    "text_sha256": hashlib.sha256(text.encode()).hexdigest(),
                    "token_count": WINDOW_TOKENS,
                    "token_ids": ids,
                }
                windows.append(window)
                if len(windows) == WINDOW_COUNT:
                    break
            if len(windows) != WINDOW_COUNT:
                raise ValueError(f"{split} has fewer than {WINDOW_COUNT} eligible windows")
            path = staging / f"{split}/windows.jsonl"
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("w", encoding="utf-8", newline="\n") as handle:
                for window in windows:
                    handle.write(json.dumps(window, ensure_ascii=False, sort_keys=True) + "\n")
            split_sha[split] = sha256_file(path)
        model_manifest = _regular(model_root / "model-manifest.json", "model manifest")
        body = {
            "schema": CORPUS_SCHEMA,
            "state_slice": STATE_SLICE,
            "source_manifest_sha256": source_manifest["manifest_sha256"],
            "model_bundle_path": "model",
            "model_manifest_sha256": sha256_file(model_manifest),
            "fit_sha256": split_sha["fit"],
            "assessment_sha256": split_sha["assessment"],
            "window_tokens": WINDOW_TOKENS,
            "fit_window_count": WINDOW_COUNT,
            "assessment_window_count": WINDOW_COUNT,
        }
        (staging / "manifest.json").write_bytes(canonical({**body, "manifest_sha256": digest(body)}))
        _make_readonly(staging)
        os.replace(staging, corpus_root)
        return json.loads((corpus_root / "manifest.json").read_text(encoding="utf-8"))
    except Exception:
        for path in sorted(staging.rglob("*"), reverse=True):
            if path.is_file():
                path.unlink()
        for directory in sorted((path for path in staging.rglob("*") if path.is_dir()), reverse=True):
            directory.rmdir()
        staging.rmdir()
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-root", type=Path, required=True)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--corpus-root", type=Path, required=True)
    parser.add_argument("--model-root", type=Path, required=True)
    parser.add_argument("--tokenizer", type=Path, required=True)
    parser.add_argument("--source-only", action="store_true")
    args = parser.parse_args()
    source = pack_source(args.raw_root, args.source_root)
    if args.source_only:
        print(json.dumps(source, indent=2, sort_keys=True))
        return 0
    from transformers import AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained(args.tokenizer, local_files_only=True, use_fast=True)
    corpus = pack_corpus(args.raw_root, args.source_root, args.corpus_root, args.model_root, tokenizer)
    print(json.dumps({"source_manifest_sha256": source["manifest_sha256"], "corpus_manifest_sha256": corpus["manifest_sha256"]}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
