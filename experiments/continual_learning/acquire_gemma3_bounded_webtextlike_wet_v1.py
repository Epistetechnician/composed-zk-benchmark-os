#!/usr/bin/env python3
"""Download and filter a bounded set of official Common Crawl WET objects.

State slice: continual-learning-gemma3-paper-recirculation-c4-bounded-v1.

This bounded path downloads a caller-bounded number of deterministic WET
objects from each of the 12 Common Crawl collections already pinned for the
TFDS C4 WebText-like source. It filters those local WET records against the
staged OpenWebText URL archive and emits a checksum-bound two-way JSONL panel.
It is not the full TFDS ``c4/webtextlike`` dataset and must not be labelled as
that dataset.

The command does not query the rate-limited CDX API, load a model, train, run a
scientific experiment, or mutate an Evidence Ledger.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import re
import shutil
import sys
import time
import urllib.request
from pathlib import Path
from typing import Any, Iterator

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from experiments.continual_learning import acquire_gemma3_bounded_webtextlike_v1 as base

STATE_SLICE = base.STATE_SLICE
SCHEMA = "gemma3-c4-bounded-wet-acquisition-v1"
CLAIM_CEILING = "LocalDevelopmentGemma3BoundedWebTextLikeRecirculationPilot"
MANUAL_ROOT = Path(
    "/Volumes/PrimaryED/ResearchArtifacts/composed-zk-benchmark-os/"
    "gemma3-c4-webtextlike-manual-v1/raw-upstream"
)
DEFAULT_ARCHIVE = MANUAL_ROOT / "OpenWebText.zip"
DEFAULT_DESTINATION = Path(
    "/Volumes/PrimaryED/ResearchArtifacts/composed-zk-benchmark-os/"
    "gemma3-c4-webtextlike-bounded-wet-v1"
)
DEFAULT_MAX_RECORDS = 2_000
HARD_MAX_RECORDS = 10_000
DEFAULT_MAX_BYTES = 4 * 1024**3
HARD_MAX_BYTES = 40 * 1024**3
DEFAULT_OBJECTS_PER_COLLECTION = 8
HARD_OBJECTS_PER_COLLECTION = 16
DEFAULT_RESERVE_BYTES = 20 * 1024**3
DEFAULT_MIN_RECORDS = 25
DEFAULT_MIN_TEXT_CHARS = 200
DEFAULT_TIMEOUT = 120.0
DEFAULT_DELAY_SECONDS = 1.0


def _download(url: str, destination: Path, expected_bytes: int, timeout: float) -> str:
    if destination.exists():
        base.regular_file(destination, "WET object")
        if destination.stat().st_size != expected_bytes:
            raise ValueError(f"existing WET object size mismatch: {destination}")
        return base.sha256_file(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(f".{destination.name}.partial")
    if temporary.exists():
        raise FileExistsError(f"refusing to reuse incomplete WET object: {temporary}")
    request = urllib.request.Request(
        url,
        headers={"User-Agent": f"{STATE_SLICE}/1.0"},
    )
    received = 0
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            with temporary.open("wb") as handle:
                while chunk := response.read(1024 * 1024):
                    received += len(chunk)
                    if received > expected_bytes:
                        raise ValueError(f"WET object exceeded expected size: {url}")
                    handle.write(chunk)
                handle.flush()
                os.fsync(handle.fileno())
        if received != expected_bytes:
            raise ValueError(f"WET object size mismatch: expected {expected_bytes}, got {received}")
        os.replace(temporary, destination)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise
    return base.sha256_file(destination)


def _head_size(url: str, timeout: float) -> int:
    request = urllib.request.Request(
        url,
        method="HEAD",
        headers={"User-Agent": f"{STATE_SLICE}/1.0"},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        value = response.headers.get("Content-Length")
    if value is None:
        raise ValueError(f"WET object has no Content-Length: {url}")
    try:
        size = int(value)
    except ValueError as exc:
        raise ValueError(f"WET object Content-Length is invalid: {url}") from exc
    if size <= 0:
        raise ValueError(f"WET object Content-Length is not positive: {url}")
    return size


def _first_paths(path_manifest: Path, count: int) -> list[str]:
    if count < 1 or count > HARD_OBJECTS_PER_COLLECTION:
        raise ValueError(f"object count must be between 1 and {HARD_OBJECTS_PER_COLLECTION}")
    paths: list[str] = []
    with gzip.open(path_manifest, "rt", encoding="utf-8") as handle:
        for line in handle:
            value = line.strip()
            if value:
                if not value.startswith("crawl-data/"):
                    raise ValueError(f"WET manifest path is invalid: {value}")
                paths.append(value)
                if len(paths) == count:
                    return paths
    if not paths:
        raise ValueError(f"WET path manifest is empty: {path_manifest}")
    raise ValueError(f"WET path manifest has fewer than {count} objects: {path_manifest}")


def _openwebtext_urls(archive: Path) -> set[str]:
    urls: set[str] = set()
    for member in base.URL_MEMBERS:
        for url in base._open_url_member(archive, member):
            if base._valid_url(url):
                urls.add(url)
    if not urls:
        raise ValueError("OpenWebText archive yielded no valid URLs")
    return urls


def _iter_wet_records(path: Path) -> Iterator[tuple[dict[str, str], bytes]]:
    with gzip.open(path, "rb") as stream:
        while True:
            line = stream.readline()
            if not line:
                return
            if not line.startswith(b"WARC/"):
                continue
            headers: dict[str, str] = {}
            while True:
                line = stream.readline()
                if not line:
                    raise ValueError(f"WET record headers are incomplete: {path}")
                if line in {b"\r\n", b"\n"}:
                    break
                name, separator, value = line.rstrip(b"\r\n").partition(b":")
                if separator:
                    headers[name.decode("latin-1").lower()] = value.decode("latin-1").strip()
            try:
                length = int(headers["content-length"])
            except (KeyError, ValueError) as exc:
                raise ValueError(f"WET record content length is invalid: {path}") from exc
            if length < 1:
                raise ValueError(f"WET record content length is not positive: {path}")
            payload = stream.read(length)
            if len(payload) != length:
                raise ValueError(f"WET record payload is truncated: {path}")
            yield headers, payload


def _normalize_text(payload: bytes, min_chars: int) -> str | None:
    text = re.sub(r"\s+", " ", payload.decode("utf-8", errors="replace")).strip()
    if len(text) < min_chars:
        return None
    return text


def _artifact(path: Path, root: Path) -> dict[str, Any]:
    base.regular_file(path, "artifact")
    return {
        "relative_path": str(path.relative_to(root)),
        "path": str(path.resolve()),
        "byte_len": path.stat().st_size,
        "sha256": base.sha256_file(path),
    }


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    if path.exists():
        raise FileExistsError(f"refusing to overwrite output: {path}")
    base.atomic_write_text(
        path,
        "".join(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n" for row in rows),
    )


def _capacity_guard(root: Path, max_bytes: int, reserve_bytes: int) -> None:
    if max_bytes < 1 or max_bytes > HARD_MAX_BYTES:
        raise ValueError(f"max_bytes must be between 1 and {HARD_MAX_BYTES}")
    if reserve_bytes < 0:
        raise ValueError("reserve_bytes must not be negative")
    root.mkdir(parents=True, exist_ok=True)
    usage = shutil.disk_usage(root)
    if usage.free < max_bytes + reserve_bytes:
        raise OSError(
            f"insufficient free space on {root}: need {max_bytes + reserve_bytes} bytes, "
            f"have {usage.free} bytes"
        )


def acquire(
    archive: Path,
    manifest_root: Path,
    destination: Path,
    *,
    max_records: int = DEFAULT_MAX_RECORDS,
    objects_per_collection: int = DEFAULT_OBJECTS_PER_COLLECTION,
    max_bytes: int = DEFAULT_MAX_BYTES,
    reserve_bytes: int = DEFAULT_RESERVE_BYTES,
    min_records: int = DEFAULT_MIN_RECORDS,
    min_text_chars: int = DEFAULT_MIN_TEXT_CHARS,
    timeout: float = DEFAULT_TIMEOUT,
    delay_seconds: float = DEFAULT_DELAY_SECONDS,
    resume: bool = False,
) -> dict[str, Any]:
    archive = base.regular_file(base.external_path(archive, "OpenWebText archive"), "OpenWebText archive")
    manifest_root = base.external_path(manifest_root, "WET manifest root")
    destination = base.external_path(destination, "destination root")
    if max_records < 1 or max_records > HARD_MAX_RECORDS:
        raise ValueError(f"max_records must be between 1 and {HARD_MAX_RECORDS}")
    if objects_per_collection < 1 or objects_per_collection > HARD_OBJECTS_PER_COLLECTION:
        raise ValueError(
            f"objects_per_collection must be between 1 and {HARD_OBJECTS_PER_COLLECTION}"
        )
    if min_records < 1 or min_records > max_records:
        raise ValueError("min_records must be between 1 and max_records")
    if min_text_chars < 1 or timeout <= 0 or delay_seconds < 0:
        raise ValueError("bounded acquisition settings are invalid")
    if destination.exists() and not resume:
        raise FileExistsError(f"destination exists; choose a new root or use --resume: {destination}")
    if destination.is_symlink():
        raise ValueError(f"destination must not be a symlink: {destination}")
    _capacity_guard(destination, max_bytes, reserve_bytes)

    urls = _openwebtext_urls(archive)
    raw_root = destination / "raw" / "wet"
    raw_root.mkdir(parents=True, exist_ok=True)
    wet_objects: list[dict[str, Any]] = []
    total_bytes = 0
    for collection in base.COLLECTIONS:
        manifest_path = manifest_root / f"{collection}-wet.paths.gz"
        manifest_path = base.regular_file(manifest_path, "WET path manifest")
        for object_index, relative_source in enumerate(
            _first_paths(manifest_path, objects_per_collection)
        ):
            source_url = f"{base.COMMON_CRAWL_DATA_ROOT}/{relative_source}"
            expected_bytes = _head_size(source_url, timeout)
            total_bytes += expected_bytes
            if total_bytes > max_bytes:
                raise OSError("selected WET objects exceed bounded download byte ceiling")
            if object_index == 0:
                raw_path = raw_root / f"{collection}.warc.wet.gz"
            else:
                raw_path = raw_root / f"{collection}-{object_index:05d}.warc.wet.gz"
            raw_sha256 = _download(source_url, raw_path, expected_bytes, timeout)
            wet_objects.append(
                {
                    "collection": collection,
                    "object_index": object_index,
                    "source_path": relative_source,
                    "source_url": source_url,
                    "raw_path": str(raw_path.resolve()),
                    "byte_len": expected_bytes,
                    "sha256": raw_sha256,
                }
            )
            if delay_seconds:
                time.sleep(delay_seconds)

    records: list[dict[str, Any]] = []
    seen_urls: set[str] = set()
    for object_info in wet_objects:
        raw_path = Path(object_info["raw_path"])
        for headers, payload in _iter_wet_records(raw_path):
            url = headers.get("warc-target-uri")
            if not url or url not in urls or url in seen_urls:
                continue
            text = _normalize_text(payload, min_text_chars)
            if text is None:
                continue
            source_digest = headers.get("warc-payload-digest", "")
            document_id = base._record_id(url, object_info["collection"], source_digest or url)
            records.append(
                {
                    "document_id": document_id,
                    "url": url,
                    "split": base._split_for(url),
                    "collection": object_info["collection"],
                    "source_digest": source_digest,
                    "raw_path": str(raw_path),
                    "raw_sha256": object_info["sha256"],
                    "raw_byte_len": object_info["byte_len"],
                    "record_sha256": hashlib.sha256(payload).hexdigest(),
                    "min_text_chars": min_text_chars,
                    "text": text,
                }
            )
            seen_urls.add(url)
            if len(records) >= max_records:
                break
        if len(records) >= max_records:
            break
    if len(records) < min_records:
        raise RuntimeError(
            f"bounded WET sample found only {len(records)} records; minimum is {min_records}"
        )

    records.sort(key=lambda item: item["document_id"])
    inventory_rows = []
    fit_rows = []
    assessment_rows = []
    for record in records:
        inventory = {key: value for key, value in record.items() if key != "text"}
        inventory_rows.append(inventory)
        normalized = {"document_id": record["document_id"], "text": record["text"]}
        (fit_rows if record["split"] == "fit" else assessment_rows).append(normalized)
    inventory_path = destination / "record-inventory.jsonl"
    _write_jsonl(inventory_path, inventory_rows)
    fit_path = destination / "data" / "fit.jsonl"
    assessment_path = destination / "data" / "assessment.jsonl"
    _write_jsonl(fit_path, fit_rows)
    _write_jsonl(assessment_path, assessment_rows)

    body: dict[str, Any] = {
        "schema": SCHEMA,
        "state_slice": STATE_SLICE,
        "claim_ceiling": CLAIM_CEILING,
        "full_c4_webtextlike": False,
        "retrieval_format": "commoncrawl-wet-object-sample-v1",
        "selection_policy": "first-n-wet-objects-per-pinned-collection-v1",
        "network_access": True,
        "training": False,
        "scientific_execution": False,
        "evidence_ledger_mutation": False,
        "openwebtext_archive": {
            "path": str(archive.resolve()),
            "source": base.OPENWEBTEXT_SOURCE,
            "byte_len": archive.stat().st_size,
            "sha256": base.sha256_file(archive),
        },
        "wet_objects": wet_objects,
        "configuration": {
            "max_records": max_records,
            "max_bytes": max_bytes,
            "min_records": min_records,
            "min_text_chars": min_text_chars,
            "objects_per_collection": objects_per_collection,
            "collections": list(base.COLLECTIONS),
        },
        "record_count": len(records),
        "downloaded_bytes": total_bytes,
        "record_inventory": _artifact(inventory_path, destination),
        "datasets": {
            "fit": {
                **_artifact(fit_path, destination),
                "record_count": len(fit_rows),
            },
            "assessment": {
                **_artifact(assessment_path, destination),
                "record_count": len(assessment_rows),
            },
        },
    }
    body["manifest_sha256"] = base.digest(body)
    manifest_path = destination / "acquisition-manifest.json"
    if manifest_path.exists():
        raise FileExistsError(f"refusing to overwrite acquisition manifest: {manifest_path}")
    base.atomic_write_text(manifest_path, json.dumps(body, indent=2, sort_keys=True) + "\n")
    return {
        "valid": True,
        "state_slice": STATE_SLICE,
        "claim_ceiling": CLAIM_CEILING,
        "destination": str(destination),
        "record_count": len(records),
        "downloaded_bytes": total_bytes,
        "fit_records": len(fit_rows),
        "assessment_records": len(assessment_rows),
        "full_c4_webtextlike": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--openwebtext-archive", type=Path, default=DEFAULT_ARCHIVE)
    parser.add_argument("--manifest-root", type=Path, default=MANUAL_ROOT / "commoncrawl")
    parser.add_argument("--destination-root", type=Path, default=DEFAULT_DESTINATION)
    parser.add_argument("--max-records", type=int, default=DEFAULT_MAX_RECORDS)
    parser.add_argument(
        "--objects-per-collection",
        type=int,
        default=DEFAULT_OBJECTS_PER_COLLECTION,
    )
    parser.add_argument("--max-bytes", type=int, default=DEFAULT_MAX_BYTES)
    parser.add_argument("--reserve-bytes", type=int, default=DEFAULT_RESERVE_BYTES)
    parser.add_argument("--min-records", type=int, default=DEFAULT_MIN_RECORDS)
    parser.add_argument("--min-text-chars", type=int, default=DEFAULT_MIN_TEXT_CHARS)
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT)
    parser.add_argument("--delay-seconds", type=float, default=DEFAULT_DELAY_SECONDS)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    print(
        json.dumps(
            acquire(
                args.openwebtext_archive,
                args.manifest_root,
                args.destination_root,
                max_records=args.max_records,
                objects_per_collection=args.objects_per_collection,
                max_bytes=args.max_bytes,
                reserve_bytes=args.reserve_bytes,
                min_records=args.min_records,
                min_text_chars=args.min_text_chars,
                timeout=args.timeout,
                delay_seconds=args.delay_seconds,
                resume=args.resume,
            ),
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
