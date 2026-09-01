"""External V4 custody helpers.

State slice: astral-trace-completeness-gemma3-end-to-end-v4.
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Sequence

import protocol_v4 as protocol


def validate_root(root: Path, repository_root: Path) -> dict[str, Any]:
    return protocol.custody_receipt(root, repository_root)


def _write_private(path: Path, data: bytes) -> None:
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
    except BaseException:
        path.unlink(missing_ok=True)
        raise


def write_raw_events(root: Path, repository_root: Path, run_id: str, events: Sequence[protocol.TraceEvent], *, event_stream_sha256: str) -> dict[str, Any]:
    receipt = protocol.custody_receipt(root, repository_root)
    if not receipt["valid"]:
        raise protocol.ProtocolError("custody validation failed")
    raw_path = root / "raw" / f"{run_id}.events.jsonl"
    rows = b"".join(protocol.canonical_bytes(event.to_dict()) + b"\n" for event in events)
    _write_private(raw_path, rows)
    created = datetime.now(timezone.utc)
    value = {
        "protocol": protocol.PROTOCOL_ID,
        "state_slice": protocol.STATE_SLICE,
        "run_id": run_id,
        "raw_relative_path": raw_path.relative_to(root).as_posix(),
        "raw_sha256": protocol.sha256_file(raw_path),
        "event_count": len(events),
        "event_stream_sha256": event_stream_sha256,
        "created_at": created.isoformat(),
        "expires_at": (created + timedelta(hours=protocol.RAW_RETENTION_HOURS)).isoformat(),
    }
    return {**value, "manifest_sha256": protocol.digest_json(value)}


def write_aggregate(root: Path, repository_root: Path, filename: str, value: dict[str, Any]) -> Path:
    receipt = protocol.custody_receipt(root, repository_root)
    if not receipt["valid"]:
        raise protocol.ProtocolError("custody validation failed")
    protocol.reject_raw_fields(value)
    path = root / "aggregate" / filename
    _write_private(path, protocol.canonical_bytes(value) + b"\n")
    return path
