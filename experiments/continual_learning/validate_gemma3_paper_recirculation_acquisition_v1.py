#!/usr/bin/env python3
"""Independently validate the external Gemma3 acquisition bundle."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

MANIFEST_SCHEMA = "gemma3-paper-recirculation-acquisition-v1"
SOURCE_RECORD_SCHEMA = "gemma3-source-v1"
ACQUISITION_STATE_SLICE = "continual-learning-gemma3-paper-recirculation-acquisition-v1"
CONSUMER_STATE_SLICE = "continual-learning-gemma3-paper-recirculation-v1"
FIT_DATASETS = ("arxiv", "c4", "pg19")
ASSESSMENT_DATASETS = (
    "arxiv",
    "big_patent",
    "billsum",
    "booksum/book",
    "c4/webtextlike",
    "gov_report",
    "lambada",
    "newsroom",
    "pg19",
    "pubmed",
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
    repo = REPO_ROOT.resolve()
    if resolved == repo or repo in resolved.parents:
        raise ValueError(f"{label} must be outside the repository: {resolved}")
    return resolved


def _regular(path: Path, label: str) -> Path:
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"{label} must be a regular file: {path}")
    return path


def _load_manifest(root: Path) -> dict[str, Any]:
    path = _regular(root / "acquisition-manifest.json", "acquisition manifest")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("acquisition manifest must be an object")
    if value.get("schema") != MANIFEST_SCHEMA:
        raise ValueError("acquisition manifest schema mismatch")
    if value.get("source_record_schema") != SOURCE_RECORD_SCHEMA:
        raise ValueError("source record schema mismatch")
    if value.get("state_slice") != CONSUMER_STATE_SLICE:
        raise ValueError("consumer state slice mismatch")
    if value.get("acquisition_state_slice") != ACQUISITION_STATE_SLICE:
        raise ValueError("acquisition state slice mismatch")
    if value.get("selection_policy") != "fixed-upstream-order-v1":
        raise ValueError("selection policy mismatch")
    expected_flags = {
        "network_access": True,
        "training": False,
        "scientific_execution": False,
        "evidence_ledger_mutation": False,
    }
    for field, expected in expected_flags.items():
        if not isinstance(value.get(field), bool) or value[field] != expected:
            raise ValueError(f"invalid acquisition safety flag: {field}")
    body = {key: item for key, item in value.items() if key != "manifest_sha256"}
    if value.get("manifest_sha256") != digest(body):
        raise ValueError("acquisition manifest digest mismatch")
    datasets = value.get("datasets")
    expected = {f"fit/{name}" for name in FIT_DATASETS} | {
        f"assessment/{name}" for name in ASSESSMENT_DATASETS
    }
    if not isinstance(datasets, dict) or set(datasets) != expected:
        raise ValueError("acquisition dataset panel mismatch")
    return value


def validate(source_root: Path) -> dict[str, Any]:
    source_root = _external(source_root, "source root")
    if not source_root.is_dir():
        raise FileNotFoundError(f"source root does not exist: {source_root}")
    for path in source_root.rglob("*"):
        if path.is_symlink():
            raise ValueError(f"source root contains a symlink: {path}")
    manifest = _load_manifest(source_root)
    raw_artifacts = manifest.get("raw_artifacts")
    if not isinstance(raw_artifacts, list) or not raw_artifacts:
        raise ValueError("raw artifact inventory is missing")
    raw_by_path: dict[str, dict[str, Any]] = {}
    for item in raw_artifacts:
        if not isinstance(item, dict):
            raise ValueError("raw artifact entry must be an object")
        path = _regular(Path(str(item.get("path"))), "raw artifact")
        _external(path, "raw artifact")
        expected_sha = item.get("sha256")
        if not isinstance(expected_sha, str) or sha256_file(path) != expected_sha:
            raise ValueError(f"raw artifact digest mismatch: {path}")
        if not isinstance(item.get("byte_len"), int) or item["byte_len"] != path.stat().st_size:
            raise ValueError(f"raw artifact byte length mismatch: {path}")
        raw_by_path[str(path.resolve())] = item

    seen_ids: dict[str, str] = {}
    normalized = {}
    for key, metadata in sorted(manifest["datasets"].items()):
        if not isinstance(metadata, dict):
            raise ValueError(f"dataset metadata must be an object: {key}")
        for field in ("source", "revision", "split", "normalized_path", "normalized_sha256", "record_count"):
            if field not in metadata:
                raise ValueError(f"dataset metadata missing {field}: {key}")
        source = metadata["source"]
        if not isinstance(source, str) or not source.startswith("https://"):
            raise ValueError(f"dataset source is not a documented HTTPS source: {key}")
        path = source_root / str(metadata["normalized_path"])
        _regular(path, f"normalized source {key}")
        if sha256_file(path) != metadata["normalized_sha256"]:
            raise ValueError(f"normalized source digest mismatch: {key}")
        count = 0
        with path.open(encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, 1):
                if not line.strip():
                    raise ValueError(f"blank normalized JSONL line: {key}:{line_number}")
                value = json.loads(line)
                if set(value) != {"document_id", "text"}:
                    raise ValueError(f"normalized record schema mismatch: {key}:{line_number}")
                document_id = value["document_id"]
                text = value["text"]
                if not isinstance(document_id, str) or not document_id:
                    raise ValueError(f"normalized record id is invalid: {key}:{line_number}")
                if not isinstance(text, str) or not text.strip():
                    raise ValueError(f"normalized record text is invalid: {key}:{line_number}")
                previous = seen_ids.get(document_id)
                if previous is not None:
                    raise ValueError(f"document reused across source files: {document_id} ({previous}, {key})")
                seen_ids[document_id] = key
                count += 1
        if count != metadata["record_count"] or count == 0:
            raise ValueError(f"normalized record count mismatch: {key}")
        for raw_path in metadata.get("raw_artifacts", []):
            if str(Path(raw_path).resolve()) not in raw_by_path:
                raise ValueError(f"dataset references unlisted raw artifact: {key}: {raw_path}")
        normalized[key] = {"record_count": count, "normalized_sha256": metadata["normalized_sha256"]}
    return {
        "valid": True,
        "schema": MANIFEST_SCHEMA,
        "source_root": str(source_root),
        "dataset_count": len(normalized),
        "record_counts": normalized,
        "raw_artifact_count": len(raw_by_path),
        "network_access": True,
        "training": False,
        "scientific_execution": False,
        "evidence_ledger_mutation": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(validate(args.source_root), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
