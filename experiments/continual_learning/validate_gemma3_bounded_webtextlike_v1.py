#!/usr/bin/env python3
"""Independently validate a bounded WebText-like acquisition bundle.

State slice: continual-learning-gemma3-paper-recirculation-c4-bounded-v1.

This validator verifies the external manifest, selected URL inventory, raw
Common Crawl range records, normalized JSONL outputs, and digest bindings. It
does not validate the full TFDS C4 dataset because this bounded protocol is not
that dataset.
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

from experiments.continual_learning import acquire_gemma3_bounded_webtextlike_v1 as acquisition

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
        raise ValueError(f"{label} escapes destination root: {relative_path}")
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

    manifest_path = _regular(root / "acquisition-manifest.json", "acquisition manifest")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(manifest, dict):
        raise ValueError("acquisition manifest must be an object")
    for field, expected in (("schema", SCHEMA), ("state_slice", STATE_SLICE)):
        if manifest.get(field) != expected:
            raise ValueError(f"manifest {field} mismatch")
    if manifest.get("full_c4_webtextlike") is not False:
        raise ValueError("bounded bundle must not claim full c4/webtextlike")
    expected_flags = {
        "network_access": True,
        "training": False,
        "scientific_execution": False,
        "evidence_ledger_mutation": False,
    }
    for field, expected in expected_flags.items():
        if manifest.get(field) is not expected:
            raise ValueError(f"manifest safety flag mismatch: {field}")
    body = {key: value for key, value in manifest.items() if key != "manifest_sha256"}
    if manifest.get("manifest_sha256") != digest(body):
        raise ValueError("manifest digest mismatch")

    selected_info = manifest.get("selected_urls")
    inventory_info = manifest.get("record_inventory")
    archive_info = manifest.get("openwebtext_archive")
    if not all(isinstance(item, dict) for item in (selected_info, inventory_info, archive_info)):
        raise ValueError("manifest artifact inventory is incomplete")
    selected_path = _root_file(root, str(selected_info["relative_path"]), "selected URL inventory")
    inventory_path = _root_file(root, str(inventory_info["relative_path"]), "record inventory")
    _artifact(selected_path, selected_info, "selected URL inventory")
    _artifact(inventory_path, inventory_info, "record inventory")
    archive_path = _regular(Path(str(archive_info["path"])), "OpenWebText archive")
    if _external(archive_path, "OpenWebText archive") == root or root in archive_path.parents:
        raise ValueError("OpenWebText archive must be outside acquisition root")
    _artifact(archive_path, archive_info, "OpenWebText archive")

    selected = _read_jsonl(selected_path)
    if any(
        item.get("selection_rank") != index
        or not isinstance(item.get("url"), str)
        or not isinstance(item.get("selection_sha256"), str)
        or hashlib.sha256(item["url"].encode("utf-8")).hexdigest() != item["selection_sha256"]
        for index, item in enumerate(selected)
    ):
        raise ValueError("selected URL inventory is not bound to deterministic selection")
    selected_urls = {item["url"] for item in selected}
    if len(selected_urls) != len(selected):
        raise ValueError("selected URL inventory contains duplicates")

    inventory = _read_jsonl(inventory_path)
    if len(inventory) != manifest.get("record_count"):
        raise ValueError("record inventory count mismatch")
    records_by_url: dict[str, dict[str, Any]] = {}
    records_by_id: set[str] = set()
    for item in inventory:
        url = item.get("url")
        document_id = item.get("document_id")
        if not isinstance(url, str) or url not in selected_urls:
            raise ValueError("record inventory contains an unselected URL")
        if url in records_by_url:
            raise ValueError(f"record inventory contains duplicate URL: {url}")
        if not isinstance(document_id, str) or not document_id or document_id in records_by_id:
            raise ValueError("record inventory contains invalid or duplicate document id")
        if item.get("split") != acquisition._split_for(url):
            raise ValueError(f"record split is not deterministic: {url}")
        if item.get("collection") not in acquisition.COLLECTIONS:
            raise ValueError("record collection is not pinned")
        try:
            length = int(item["length"])
            offset = int(item["offset"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError("record offset/length is invalid") from exc
        if offset < 0 or length <= 0:
            raise ValueError("record offset/length is out of range")
        raw_path = _regular(Path(str(item["raw_path"])), "raw WARC")
        if raw_path.stat().st_size != length:
            raise ValueError(f"raw WARC length mismatch: {raw_path}")
        if sha256_file(raw_path) != item.get("raw_sha256"):
            raise ValueError(f"raw WARC digest mismatch: {raw_path}")
        records_by_url[url] = item
        records_by_id.add(document_id)

    datasets = manifest.get("datasets")
    if not isinstance(datasets, dict) or set(datasets) != {"fit", "assessment"}:
        raise ValueError("bounded dataset panel mismatch")
    output_ids: set[str] = set()
    output_counts: dict[str, int] = {}
    for split in ("fit", "assessment"):
        metadata = datasets[split]
        if not isinstance(metadata, dict):
            raise ValueError(f"dataset metadata is invalid: {split}")
        output_path = _root_file(root, str(metadata["relative_path"]), f"normalized {split}")
        _artifact(output_path, metadata, f"normalized {split}")
        rows = _read_jsonl(output_path)
        for row in rows:
            if set(row) != {"document_id", "text"}:
                raise ValueError(f"normalized record schema mismatch: {split}")
            document_id = row["document_id"]
            if document_id not in records_by_id or document_id in output_ids:
                raise ValueError(f"normalized record identity mismatch: {document_id}")
            if not isinstance(row["text"], str) or not row["text"].strip():
                raise ValueError(f"normalized record text is invalid: {split}")
            output_ids.add(document_id)
        if len(rows) != metadata.get("record_count"):
            raise ValueError(f"normalized record count mismatch: {split}")
        output_counts[split] = len(rows)
    if output_ids != records_by_id:
        raise ValueError("normalized outputs do not cover record inventory")

    return {
        "valid": True,
        "schema": SCHEMA,
        "state_slice": STATE_SLICE,
        "acquisition_root": str(root),
        "record_count": len(inventory),
        "fit_records": output_counts["fit"],
        "assessment_records": output_counts["assessment"],
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
