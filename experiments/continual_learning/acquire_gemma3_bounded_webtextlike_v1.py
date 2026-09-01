#!/usr/bin/env python3
"""Acquire a bounded Common Crawl/OpenWebText WebText-like panel.

State slice: continual-learning-gemma3-paper-recirculation-c4-bounded-v1.

This is a deliberately bounded acquisition path. It uses the staged official
OpenWebText URL archive, queries pinned Common Crawl CDX indexes, and retrieves
only selected WARC records with HTTP byte ranges. It does not reconstruct the
official TFDS ``c4/webtextlike`` dataset and must never be labelled as that
dataset.

The output is an external, checksum-bound two-way JSONL panel suitable only for
the bounded Gemma3 local pilot documented by the matching protocol record.
This command does not load a model, train, run a scientific experiment, or
mutate an Evidence Ledger.
"""

from __future__ import annotations

import argparse
import bz2
import gzip
import hashlib
import heapq
import html
import json
import os
import re
import shutil
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Iterable, Iterator

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

STATE_SLICE = "continual-learning-gemma3-paper-recirculation-c4-bounded-v1"
SCHEMA = "gemma3-c4-bounded-webtextlike-acquisition-v1"
CLAIM_CEILING = "LocalDevelopmentGemma3BoundedWebTextLikeRecirculationPilot"
OPENWEBTEXT_SOURCE = "https://mega.nz/#F!EZZD0YwJ!9_PlEQzdMVLaNdKv_ICNVQ"
COMMON_CRAWL_INDEX_ROOT = "https://index.commoncrawl.org"
COMMON_CRAWL_DATA_ROOT = "https://data.commoncrawl.org"
DEFAULT_ARCHIVE = Path(
    "/Volumes/PrimaryED/ResearchArtifacts/composed-zk-benchmark-os/"
    "gemma3-c4-webtextlike-manual-v1/raw-upstream/OpenWebText.zip"
)
DEFAULT_DESTINATION = Path(
    "/Volumes/PrimaryED/ResearchArtifacts/composed-zk-benchmark-os/"
    "gemma3-c4-webtextlike-bounded-v1"
)
DEFAULT_MAX_RECORDS = 2_000
HARD_MAX_RECORDS = 10_000
DEFAULT_MAX_BYTES = 4 * 1024**3
HARD_MAX_BYTES = 20 * 1024**3
DEFAULT_RESERVE_BYTES = 20 * 1024**3
DEFAULT_MIN_TEXT_CHARS = 200
DEFAULT_MAX_RECORD_BYTES = 16 * 1024**2
DEFAULT_MAX_INDEX_REQUESTS = 30_000
DEFAULT_INDEX_TIMEOUT = 30.0
DEFAULT_INDEX_RETRIES = 3
DEFAULT_DELAY_SECONDS = 1.0
URL_MEMBERS = (
    "OpenWebText/Version 1/URLs/RS_2011-01.bz2.deduped.txt",
    "OpenWebText/Version 1/URLs/RS_2012-06.bz2.deduped.txt",
    "OpenWebText/Version 1/URLs/RS_2014-01.bz2.deduped.txt",
)
COLLECTIONS = (
    "CC-MAIN-2018-34",
    "CC-MAIN-2018-39",
    "CC-MAIN-2018-43",
    "CC-MAIN-2018-47",
    "CC-MAIN-2018-51",
    "CC-MAIN-2019-04",
    "CC-MAIN-2019-09",
    "CC-MAIN-2019-13",
    "CC-MAIN-2019-18",
    "CC-MAIN-2019-22",
    "CC-MAIN-2019-26",
    "CC-MAIN-2019-30",
)


def sha256_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def digest(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def external_path(path: Path, label: str) -> Path:
    resolved = path.expanduser().resolve()
    repo = REPO_ROOT.resolve()
    if resolved == repo or repo in resolved.parents:
        raise ValueError(f"{label} must be outside the repository: {resolved}")
    return resolved


def regular_file(path: Path, label: str) -> Path:
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"{label} must be a regular file: {path}")
    return path


def atomic_write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.partial")
    if temporary.exists():
        raise FileExistsError(f"refusing to reuse incomplete file: {temporary}")
    try:
        temporary.write_text(value, encoding="utf-8", newline="\n")
        os.replace(temporary, path)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise


def append_jsonl(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(value, sort_keys=True, separators=(",", ":")))
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())


def _read_jsonl(path: Path) -> Iterator[dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                raise ValueError(f"blank JSONL line: {path}:{line_number}")
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValueError(f"JSONL record must be an object: {path}:{line_number}")
            yield value


def _open_url_member(archive: Path, member: str) -> Iterator[str]:
    with zipfile.ZipFile(archive) as bundle:
        try:
            info = bundle.getinfo(member)
        except KeyError as exc:
            raise FileNotFoundError(f"OpenWebText member missing: {member}") from exc
        if info.is_dir():
            raise ValueError(f"OpenWebText member is a directory: {member}")
        with bundle.open(info) as raw:
            first = raw.read(3)
            raw.seek(0)
            stream: Any = raw
            if first == b"BZh":
                stream = bz2.BZ2File(raw)
            for line in stream:
                if isinstance(line, bytes):
                    line = line.decode("utf-8", errors="strict")
                url = line.strip()
                if url:
                    yield url
            if stream is not raw:
                stream.close()


def _valid_url(url: str) -> bool:
    try:
        parsed = urllib.parse.urlsplit(url)
    except ValueError:
        return False
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def select_urls(archive: Path, max_records: int) -> list[dict[str, Any]]:
    """Select the lowest URL hashes without loading all URLs into memory."""

    if max_records < 1:
        raise ValueError("max_records must be positive")
    heap: list[tuple[int, str, str]] = []
    seen: set[str] = set()
    for member in URL_MEMBERS:
        for url in _open_url_member(archive, member):
            if not _valid_url(url) or url in seen:
                continue
            seen.add(url)
            score = int(hashlib.sha256(url.encode("utf-8")).hexdigest(), 16)
            item = (-score, url, member)
            if len(heap) < max_records:
                heapq.heappush(heap, item)
            elif item > heap[0]:
                heapq.heapreplace(heap, item)
    selected = [(-score, url, member) for score, url, member in heap]
    selected.sort(key=lambda item: (item[0], item[1]))
    return [
        {
            "selection_rank": rank,
            "selection_sha256": hashlib.sha256(url.encode("utf-8")).hexdigest(),
            "url": url,
            "openwebtext_member": member,
        }
        for rank, (_, url, member) in enumerate(selected)
    ]


def _collection_order(url: str) -> list[str]:
    start = int(hashlib.sha256(url.encode("utf-8")).hexdigest()[:16], 16) % len(COLLECTIONS)
    return list(COLLECTIONS[start:]) + list(COLLECTIONS[:start])


def _index_url(collection: str, url: str) -> str:
    query = urllib.parse.urlencode(
        {
            "url": url,
            "output": "json",
            "filter": ["status:200", "mime-detected:text/html"],
            "collapse": "digest",
        },
        doseq=True,
    )
    return f"{COMMON_CRAWL_INDEX_ROOT}/{collection}-index?{query}"


def query_index(
    collection: str,
    url: str,
    timeout: float = DEFAULT_INDEX_TIMEOUT,
    retries: int = DEFAULT_INDEX_RETRIES,
) -> list[dict[str, Any]]:
    request = urllib.request.Request(
        _index_url(collection, url),
        headers={"User-Agent": f"{STATE_SLICE}/1.0"},
    )
    if retries < 0:
        raise ValueError("retries must be non-negative")
    for attempt in range(retries + 1):
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                payload = response.read().decode("utf-8")
            break
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                return []
            if exc.code not in {429, 500, 502, 503, 504} or attempt >= retries:
                raise
            time.sleep(2**attempt)
        except (TimeoutError, OSError):
            if attempt >= retries:
                raise
            time.sleep(2**attempt)
    else:  # pragma: no cover - loop either breaks or raises
        raise RuntimeError("Common Crawl index request did not complete")
    records: list[dict[str, Any]] = []
    for line in payload.splitlines():
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            continue
        if value.get("status") != "200":
            continue
        if value.get("mime") not in {"text/html", "application/xhtml+xml", "text/plain"} and value.get(
            "mime-detected"
        ) not in {"text/html", "application/xhtml+xml", "text/plain"}:
            continue
        try:
            value["offset"] = int(value["offset"])
            value["length"] = int(value["length"])
            if value["offset"] < 0 or value["length"] <= 0:
                continue
            if not str(value["filename"]).startswith("crawl-data/"):
                continue
        except (KeyError, TypeError, ValueError):
            continue
        records.append(value)
    return sorted(
        records,
        key=lambda value: (
            str(value.get("timestamp", "")),
            str(value.get("digest", "")),
            str(value["filename"]),
            value["offset"],
        ),
    )


def _range_url(record: dict[str, Any]) -> str:
    filename = str(record["filename"])
    return f"{COMMON_CRAWL_DATA_ROOT}/{filename}"


def fetch_range(record: dict[str, Any], max_record_bytes: int, timeout: float = 120.0) -> bytes:
    length = int(record["length"])
    offset = int(record["offset"])
    if length > max_record_bytes:
        raise ValueError(f"WARC record exceeds byte guard: {length} > {max_record_bytes}")
    request = urllib.request.Request(
        _range_url(record),
        headers={
            "User-Agent": f"{STATE_SLICE}/1.0",
            "Range": f"bytes={offset}-{offset + length - 1}",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        if getattr(response, "status", None) != 206:
            raise ValueError(f"Common Crawl did not honor byte range: {response.status}")
        payload = response.read(length + 1)
    if len(payload) != length:
        raise ValueError(f"byte-range length mismatch: expected {length}, got {len(payload)}")
    return payload


class _TextExtractor(HTMLParser):
    _IGNORED = frozenset({"script", "style", "noscript", "template", "svg"})

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.ignored_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() in self._IGNORED:
            self.ignored_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in self._IGNORED and self.ignored_depth:
            self.ignored_depth -= 1

    def handle_data(self, data: str) -> None:
        if not self.ignored_depth:
            self.parts.append(data)


def _http_payload(warc: bytes) -> bytes:
    try:
        warc = gzip.decompress(warc)
    except OSError as exc:
        raise ValueError("retrieved WARC member is not valid gzip") from exc
    if not warc.startswith(b"WARC/"):
        raise ValueError("retrieved record is not WARC")
    warc_header_end = warc.find(b"\r\n\r\n")
    if warc_header_end < 0:
        raise ValueError("WARC headers are incomplete")
    http_start = warc_header_end + 4
    http_header_end = warc.find(b"\r\n\r\n", http_start)
    if http_header_end < 0:
        raise ValueError("HTTP headers are incomplete")
    http_headers = warc[http_start:http_header_end].split(b"\r\n")
    if not http_headers or not http_headers[0].startswith(b"HTTP/"):
        raise ValueError("WARC response does not contain an HTTP response")
    headers: dict[str, str] = {}
    for line in http_headers[1:]:
        name, separator, value = line.partition(b":")
        if separator:
            headers[name.decode("latin-1").lower()] = value.decode("latin-1").strip()
    content_type = headers.get("content-type", "").split(";", 1)[0].strip().lower()
    if content_type not in {"text/html", "application/xhtml+xml", "text/plain"}:
        raise ValueError(f"HTTP payload is not text content: {content_type or 'missing content type'}")
    payload = warc[http_header_end + 4 :]
    if headers.get("content-encoding", "").lower() == "gzip":
        payload = gzip.decompress(payload)
    if headers.get("transfer-encoding", "").lower() == "chunked":
        payload = _decode_chunked(payload)
    return payload


def _decode_chunked(payload: bytes) -> bytes:
    output = bytearray()
    cursor = 0
    while cursor < len(payload):
        line_end = payload.find(b"\r\n", cursor)
        if line_end < 0:
            raise ValueError("chunked HTTP payload is incomplete")
        size_text = payload[cursor:line_end].split(b";", 1)[0].strip()
        size = int(size_text, 16)
        cursor = line_end + 2
        if size == 0:
            return bytes(output)
        end = cursor + size
        if end + 2 > len(payload) or payload[end : end + 2] != b"\r\n":
            raise ValueError("chunked HTTP payload has invalid framing")
        output.extend(payload[cursor:end])
        cursor = end + 2
    raise ValueError("chunked HTTP payload has no terminator")


def html_to_text(warc: bytes, min_chars: int) -> str:
    payload = _http_payload(warc)
    decoded = payload.decode("utf-8", errors="replace")
    parser = _TextExtractor()
    parser.feed(decoded)
    parser.close()
    text = html.unescape(re.sub(r"\s+", " ", " ".join(parser.parts))).strip()
    if len(text) < min_chars:
        raise ValueError(f"normalized text is below minimum length: {len(text)} < {min_chars}")
    return text


def _record_id(url: str, collection: str, digest_value: str) -> str:
    url_digest = hashlib.sha256(url.encode("utf-8")).hexdigest()[:24]
    record_digest = hashlib.sha256(digest_value.encode("utf-8")).hexdigest()[:16]
    return f"cc-{collection.lower()}-{url_digest}-{record_digest}"


def _split_for(url: str) -> str:
    value = int(hashlib.sha256(f"split-v1:{url}".encode("utf-8")).hexdigest()[:2], 16)
    return "fit" if value < 204 else "assessment"


def _artifact(path: Path, root: Path) -> dict[str, Any]:
    regular_file(path, "artifact")
    return {
        "relative_path": str(path.relative_to(root)),
        "path": str(path.resolve()),
        "byte_len": path.stat().st_size,
        "sha256": sha256_file(path),
    }


def _ensure_destination(root: Path, resume: bool) -> None:
    if root.exists() and not resume:
        raise FileExistsError(f"destination exists; choose a new root or use --resume: {root}")
    if root.is_symlink():
        raise ValueError(f"destination must not be a symlink: {root}")
    root.mkdir(parents=True, exist_ok=True)
    if any(path.is_symlink() for path in root.rglob("*")):
        raise ValueError(f"destination contains a symlink: {root}")


def _capacity_guard(destination: Path, max_bytes: int, reserve_bytes: int) -> None:
    if max_bytes < 1 or max_bytes > HARD_MAX_BYTES:
        raise ValueError(f"max_bytes must be between 1 and {HARD_MAX_BYTES}")
    usage = shutil.disk_usage(destination)
    required = max_bytes + reserve_bytes
    if usage.free < required:
        raise OSError(
            f"insufficient free space on {destination}: need {required} bytes, "
            f"have {usage.free} bytes"
        )


def _write_selected(path: Path, selected: list[dict[str, Any]]) -> None:
    atomic_write_text(
        path,
        "".join(json.dumps(item, sort_keys=True, separators=(",", ":")) + "\n" for item in selected),
    )


def _load_records(path: Path) -> dict[str, dict[str, Any]]:
    if not path.exists():
        return {}
    records: dict[str, dict[str, Any]] = {}
    for value in _read_jsonl(path):
        url = value.get("url")
        if not isinstance(url, str) or not url:
            raise ValueError(f"record inventory has invalid URL: {path}")
        if url in records:
            raise ValueError(f"record inventory has duplicate URL: {url}")
        records[url] = value
    return records


def _build_outputs(root: Path, records: Iterable[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    rows = {"fit": [], "assessment": []}
    ids: set[str] = set()
    for value in records:
        split = value["split"]
        if split not in rows:
            raise ValueError(f"invalid record split: {split}")
        document_id = value["document_id"]
        if document_id in ids:
            raise ValueError(f"duplicate normalized document id: {document_id}")
        ids.add(document_id)
        raw = regular_file(Path(value["raw_path"]), "raw WARC")
        text = html_to_text(raw.read_bytes(), int(value["min_text_chars"]))
        rows[split].append({"document_id": document_id, "text": text})
    data_root = root / "data"
    data_root.mkdir(parents=True, exist_ok=True)
    result: dict[str, dict[str, Any]] = {}
    for split, split_rows in rows.items():
        split_rows.sort(key=lambda item: item["document_id"])
        path = data_root / f"{split}.jsonl"
        if path.exists():
            raise FileExistsError(f"refusing to overwrite normalized output: {path}")
        content = "".join(
            json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n"
            for row in split_rows
        )
        atomic_write_text(path, content)
        result[split] = {
            "relative_path": str(path.relative_to(root)),
            "path": str(path.resolve()),
            "record_count": len(split_rows),
            "byte_len": path.stat().st_size,
            "sha256": sha256_file(path),
        }
    return result


def acquire(
    archive: Path,
    destination: Path,
    *,
    max_records: int = DEFAULT_MAX_RECORDS,
    max_bytes: int = DEFAULT_MAX_BYTES,
    reserve_bytes: int = DEFAULT_RESERVE_BYTES,
    min_records: int = 1,
    min_text_chars: int = DEFAULT_MIN_TEXT_CHARS,
    max_record_bytes: int = DEFAULT_MAX_RECORD_BYTES,
    max_index_requests: int = DEFAULT_MAX_INDEX_REQUESTS,
    index_timeout: float = DEFAULT_INDEX_TIMEOUT,
    index_retries: int = DEFAULT_INDEX_RETRIES,
    delay_seconds: float = DEFAULT_DELAY_SECONDS,
    resume: bool = False,
) -> dict[str, Any]:
    archive = regular_file(external_path(archive, "OpenWebText archive"), "OpenWebText archive")
    destination = external_path(destination, "destination root")
    if destination == archive or archive in destination.parents:
        raise ValueError("destination root cannot contain the OpenWebText archive")
    if max_records < 1 or max_records > HARD_MAX_RECORDS:
        raise ValueError(f"max_records must be between 1 and {HARD_MAX_RECORDS}")
    if min_records < 1 or min_records > max_records:
        raise ValueError("min_records must be between 1 and max_records")
    if min_text_chars < 1 or max_record_bytes < 1:
        raise ValueError("text and record byte guards must be positive")
    if max_index_requests < 1 or index_timeout <= 0 or index_retries < 0 or delay_seconds < 0:
        raise ValueError("index request and delay settings are invalid")
    _ensure_destination(destination, resume)
    _capacity_guard(destination, max_bytes, reserve_bytes)

    selected_path = destination / "selected-openwebtext-urls.jsonl"
    if selected_path.exists():
        selected = list(_read_jsonl(selected_path))
    else:
        selected = select_urls(archive, max_records)
        _write_selected(selected_path, selected)
    if not selected:
        raise ValueError("OpenWebText archive yielded no valid URLs")
    if len(selected) > max_records:
        raise ValueError("selected URL inventory exceeds max_records")

    records_path = destination / "record-inventory.jsonl"
    done = _load_records(records_path)
    raw_root = destination / "raw" / "warc"
    raw_root.mkdir(parents=True, exist_ok=True)
    errors_path = destination / "retrieval-errors.jsonl"
    bytes_downloaded = sum(int(value.get("length", 0)) for value in done.values())
    index_requests = 0
    for position, selected_item in enumerate(selected, 1):
        url = selected_item["url"]
        if url in done:
            continue
        found: tuple[str, dict[str, Any]] | None = None
        for collection in _collection_order(url):
            if index_requests >= max_index_requests:
                raise RuntimeError("maximum Common Crawl index requests reached")
            index_requests += 1
            try:
                candidates = query_index(
                    collection,
                    url,
                    timeout=index_timeout,
                    retries=index_retries,
                )
            except Exception as exc:  # noqa: BLE001 - persisted and bounded per URL
                append_jsonl(
                    errors_path,
                    {
                        "url": url,
                        "collection": collection,
                        "stage": "index",
                        "error_type": type(exc).__name__,
                        "error": str(exc),
                    },
                )
                candidates = []
            if candidates:
                found = (collection, candidates[0])
                break
        if found is None:
            if delay_seconds:
                time.sleep(delay_seconds)
            continue
        collection, index_record = found
        length = int(index_record["length"])
        if bytes_downloaded + length > max_bytes:
            raise OSError("bounded download byte ceiling reached")
        try:
            warc = fetch_range(index_record, max_record_bytes)
            text = html_to_text(warc, min_text_chars)
        except Exception as exc:  # noqa: BLE001 - persisted and bounded per URL
            append_jsonl(
                errors_path,
                {
                    "url": url,
                    "collection": collection,
                    "stage": "record",
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                },
            )
            continue
        del text
        digest_value = str(index_record.get("digest", "")) or hashlib.sha256(url.encode()).hexdigest()
        document_id = _record_id(url, collection, digest_value)
        raw_path = raw_root / f"{document_id}.warc.gz"
        if raw_path.exists():
            raise FileExistsError(f"refusing to overwrite raw WARC: {raw_path}")
        temporary = raw_path.with_name(f".{raw_path.name}.partial")
        if temporary.exists():
            raise FileExistsError(f"refusing to reuse incomplete raw WARC: {temporary}")
        try:
            temporary.write_bytes(warc)
            os.replace(temporary, raw_path)
        except Exception:
            temporary.unlink(missing_ok=True)
            raise
        record = {
            "document_id": document_id,
            "url": url,
            "split": _split_for(url),
            "collection": collection,
            "timestamp": str(index_record.get("timestamp", "")),
            "source_digest": digest_value,
            "filename": str(index_record["filename"]),
            "offset": int(index_record["offset"]),
            "length": length,
            "raw_path": str(raw_path.resolve()),
            "raw_sha256": hashlib.sha256(warc).hexdigest(),
            "min_text_chars": min_text_chars,
        }
        append_jsonl(records_path, record)
        done[url] = record
        bytes_downloaded += length
        if delay_seconds:
            time.sleep(delay_seconds)
        if position % 100 == 0:
            print(f"retrieved {len(done)}/{len(selected)} records ({bytes_downloaded} bytes)")

    if len(done) < min_records:
        raise RuntimeError(
            f"bounded acquisition found only {len(done)} records; minimum is {min_records}"
        )
    outputs = _build_outputs(destination, done.values())
    inventory = _artifact(records_path, destination)
    selected_artifact = _artifact(selected_path, destination)
    archive_artifact = {
        "path": str(archive.resolve()),
        "source": OPENWEBTEXT_SOURCE,
        "byte_len": archive.stat().st_size,
        "sha256": sha256_file(archive),
    }
    body: dict[str, Any] = {
        "schema": SCHEMA,
        "state_slice": STATE_SLICE,
        "claim_ceiling": CLAIM_CEILING,
        "full_c4_webtextlike": False,
        "retrieval_format": "commoncrawl-warc-range-v1",
        "selection_policy": "lowest-openwebtext-url-sha256-v1",
        "network_access": True,
        "training": False,
        "scientific_execution": False,
        "evidence_ledger_mutation": False,
        "source": {
            "openwebtext": OPENWEBTEXT_SOURCE,
            "common_crawl_index_root": COMMON_CRAWL_INDEX_ROOT,
            "common_crawl_data_root": COMMON_CRAWL_DATA_ROOT,
            "collections": list(COLLECTIONS),
            "tfds_reference": "https://www.tensorflow.org/datasets/catalog/c4",
        },
        "configuration": {
            "max_records": max_records,
            "max_bytes": max_bytes,
            "min_records": min_records,
            "min_text_chars": min_text_chars,
            "max_record_bytes": max_record_bytes,
            "index_timeout": index_timeout,
            "index_retries": index_retries,
            "delay_seconds": delay_seconds,
        },
        "record_count": len(done),
        "downloaded_bytes": bytes_downloaded,
        "selected_urls": selected_artifact,
        "record_inventory": inventory,
        "openwebtext_archive": archive_artifact,
        "datasets": outputs,
    }
    body["manifest_sha256"] = digest(body)
    manifest_path = destination / "acquisition-manifest.json"
    if manifest_path.exists():
        raise FileExistsError(f"refusing to overwrite acquisition manifest: {manifest_path}")
    atomic_write_text(manifest_path, json.dumps(body, indent=2, sort_keys=True) + "\n")
    return {
        "valid": True,
        "state_slice": STATE_SLICE,
        "claim_ceiling": CLAIM_CEILING,
        "destination": str(destination),
        "record_count": len(done),
        "downloaded_bytes": bytes_downloaded,
        "fit_records": outputs["fit"]["record_count"],
        "assessment_records": outputs["assessment"]["record_count"],
        "full_c4_webtextlike": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--openwebtext-archive", type=Path, default=DEFAULT_ARCHIVE)
    parser.add_argument("--destination-root", type=Path, default=DEFAULT_DESTINATION)
    parser.add_argument("--max-records", type=int, default=DEFAULT_MAX_RECORDS)
    parser.add_argument("--max-bytes", type=int, default=DEFAULT_MAX_BYTES)
    parser.add_argument("--reserve-bytes", type=int, default=DEFAULT_RESERVE_BYTES)
    parser.add_argument("--min-records", type=int, default=1)
    parser.add_argument("--min-text-chars", type=int, default=DEFAULT_MIN_TEXT_CHARS)
    parser.add_argument("--max-record-bytes", type=int, default=DEFAULT_MAX_RECORD_BYTES)
    parser.add_argument("--max-index-requests", type=int, default=DEFAULT_MAX_INDEX_REQUESTS)
    parser.add_argument("--index-timeout", type=float, default=DEFAULT_INDEX_TIMEOUT)
    parser.add_argument("--index-retries", type=int, default=DEFAULT_INDEX_RETRIES)
    parser.add_argument("--delay-seconds", type=float, default=DEFAULT_DELAY_SECONDS)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    result = acquire(
        args.openwebtext_archive,
        args.destination_root,
        max_records=args.max_records,
        max_bytes=args.max_bytes,
        reserve_bytes=args.reserve_bytes,
        min_records=args.min_records,
        min_text_chars=args.min_text_chars,
        max_record_bytes=args.max_record_bytes,
        max_index_requests=args.max_index_requests,
        index_timeout=args.index_timeout,
        index_retries=args.index_retries,
        delay_seconds=args.delay_seconds,
        resume=args.resume,
    )
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
