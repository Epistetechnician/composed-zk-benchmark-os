#!/usr/bin/env python3
"""Independently validate a bounded WET-sample acquisition bundle.

State slice: continual-learning-gemma3-paper-recirculation-c4-bounded-v1.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from experiments.continual_learning import acquire_gemma3_bounded_webtextlike_wet_v1 as acquisition

STATE_SLICE = acquisition.STATE_SLICE
SCHEMA = acquisition.SCHEMA


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


def _root_file(root: Path, relative_path: str, label: str) -> Path:
    path = (root / relative_path).resolve()
    if path != root and root not in path.parents:
        raise ValueError(f"{label} escapes acquisition root: {relative_path}")
    return _regular(path, label)


def _artifact(path: Path, expected: dict[str, Any], label: str) -> None:
    _regular(path, label)
    if path.stat().st_size != expected.get("byte_len"):
        raise ValueError(f"{label} byte length mismatch: {path}")
    if sha256_file(path) != expected.get("sha256"):
        raise ValueError(f"{label} digest mismatch: {path}")


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                raise ValueError(f"blank JSONL line: {path}:{line_number}")
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValueError(f"JSONL record must be an object: {path}:{line_number}")
            rows.append(value)
    return rows


def validate(root: Path) -> dict[str, Any]:
    root = _external(root, "acquisition root")
    if not root.is_dir():
        raise FileNotFoundError(f"acquisition root does not exist: {root}")
    if any(path.is_symlink() for path in root.rglob("*")):
        raise ValueError(f"acquisition root contains a symlink: {root}")
    manifest = json.loads(_regular(root / "acquisition-manifest.json", "acquisition manifest").read_text())
    if not isinstance(manifest, dict):
        raise ValueError("acquisition manifest must be an object")
    if manifest.get("schema") != SCHEMA or manifest.get("state_slice") != STATE_SLICE:
        raise ValueError("manifest identity mismatch")
    if manifest.get("full_c4_webtextlike") is not False:
        raise ValueError("bounded bundle must not claim full c4/webtextlike")
    for field, expected in {
        "network_access": True,
        "training": False,
        "scientific_execution": False,
        "evidence_ledger_mutation": False,
    }.items():
        if manifest.get(field) is not expected:
            raise ValueError(f"manifest safety flag mismatch: {field}")
    body = {key: value for key, value in manifest.items() if key != "manifest_sha256"}
    if manifest.get("manifest_sha256") != digest(body):
        raise ValueError("manifest digest mismatch")

    archive_info = manifest.get("openwebtext_archive")
    inventory_info = manifest.get("record_inventory")
    wet_objects = manifest.get("wet_objects")
    if not isinstance(archive_info, dict) or not isinstance(inventory_info, dict):
        raise ValueError("manifest artifact inventory is incomplete")
    configuration = manifest.get("configuration")
    if not isinstance(configuration, dict):
        raise ValueError("manifest configuration is missing")
    objects_per_collection = configuration.get("objects_per_collection")
    if not isinstance(objects_per_collection, int) or not (
        1 <= objects_per_collection <= acquisition.HARD_OBJECTS_PER_COLLECTION
    ):
        raise ValueError("WET object count configuration is invalid")
    if not isinstance(wet_objects, list) or len(wet_objects) != len(acquisition.base.COLLECTIONS) * objects_per_collection:
        raise ValueError("WET object panel is incomplete")
    archive = _regular(Path(str(archive_info["path"])), "OpenWebText archive")
    _artifact(archive, archive_info, "OpenWebText archive")
    inventory_path = _root_file(root, str(inventory_info["relative_path"]), "record inventory")
    _artifact(inventory_path, inventory_info, "record inventory")

    object_paths: dict[str, dict[str, Any]] = {}
    object_keys: set[tuple[str, int]] = set()
    for item in wet_objects:
        if not isinstance(item, dict) or item.get("collection") not in acquisition.base.COLLECTIONS:
            raise ValueError("WET object collection is not pinned")
        object_index = item.get("object_index")
        if not isinstance(object_index, int) or not (0 <= object_index < objects_per_collection):
            raise ValueError("WET object index is invalid")
        object_key = (item["collection"], object_index)
        if object_key in object_keys:
            raise ValueError("WET object collection/index is duplicated")
        object_keys.add(object_key)
        raw_path = _regular(Path(str(item["raw_path"])), "WET object")
        _artifact(raw_path, item, "WET object")
        object_paths[str(raw_path.resolve())] = item
    if len(object_keys) != len(acquisition.base.COLLECTIONS) * objects_per_collection:
        raise ValueError("WET object collection/index panel is incomplete")

    inventory = _read_jsonl(inventory_path)
    if len(inventory) != manifest.get("record_count"):
        raise ValueError("record inventory count mismatch")
    ids: set[str] = set()
    for item in inventory:
        document_id = item.get("document_id")
        if not isinstance(document_id, str) or not document_id or document_id in ids:
            raise ValueError("record inventory contains invalid or duplicate document id")
        url = item.get("url")
        if not isinstance(url, str) or item.get("split") != acquisition.base._split_for(url):
            raise ValueError("record inventory identity or split mismatch")
        raw_path = str(Path(str(item.get("raw_path"))).resolve())
        wet_object = object_paths.get(raw_path)
        if wet_object is None:
            raise ValueError("record references unlisted WET object")
        if item.get("raw_sha256") != wet_object["sha256"] or item.get("raw_byte_len") != wet_object["byte_len"]:
            raise ValueError("record WET custody binding mismatch")
        if not isinstance(item.get("record_sha256"), str) or len(item["record_sha256"]) != 64:
            raise ValueError("record payload digest is missing")
        ids.add(document_id)

    datasets = manifest.get("datasets")
    if not isinstance(datasets, dict) or set(datasets) != {"fit", "assessment"}:
        raise ValueError("bounded dataset panel mismatch")
    output_ids: set[str] = set()
    output_counts: dict[str, int] = {}
    for split in ("fit", "assessment"):
        metadata = datasets[split]
        path = _root_file(root, str(metadata["relative_path"]), f"normalized {split}")
        _artifact(path, metadata, f"normalized {split}")
        rows = _read_jsonl(path)
        for row in rows:
            if set(row) != {"document_id", "text"}:
                raise ValueError(f"normalized record schema mismatch: {split}")
            document_id = row["document_id"]
            if document_id not in ids or document_id in output_ids or not row["text"].strip():
                raise ValueError(f"normalized record identity mismatch: {split}")
            output_ids.add(document_id)
        if len(rows) != metadata.get("record_count"):
            raise ValueError(f"normalized record count mismatch: {split}")
        output_counts[split] = len(rows)
    if output_ids != ids:
        raise ValueError("normalized outputs do not cover record inventory")

    return {
        "valid": True,
        "schema": SCHEMA,
        "state_slice": STATE_SLICE,
        "acquisition_root": str(root),
        "record_count": len(inventory),
        "fit_records": output_counts["fit"],
        "assessment_records": output_counts["assessment"],
        "downloaded_bytes": manifest.get("downloaded_bytes"),
        "full_c4_webtextlike": False,
        "claim_ceiling": manifest.get("claim_ceiling"),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    args = parser.parse_args()
    print(json.dumps(validate(args.root), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
