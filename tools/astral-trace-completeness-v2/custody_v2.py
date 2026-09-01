"""External raw-trace custody and aggregate manifests for V2.

State slice: astral-trace-completeness-gemma3-end-to-end-v2.
"""

from __future__ import annotations

import json
import os
import stat
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Sequence

import protocol_v2 as protocol


SUBROOTS = ("raw", "aggregate", "assets", "review", "receipts")


def validate_root(root: Path, repository_root: Path) -> dict[str, Any]:
    root = root.resolve()
    repository_root = repository_root.resolve()
    errors = []
    try:
        root.relative_to(repository_root)
        errors.append("custody_inside_repository")
    except ValueError:
        pass
    if not root.is_dir() or root.is_symlink():
        errors.append("custody_root_missing_or_symlink")
    else:
        mode = stat.S_IMODE(root.stat().st_mode)
        if mode != 0o700:
            errors.append("custody_root_mode")
        if root.stat().st_uid != os.getuid():
            errors.append("custody_root_owner")
    for name in SUBROOTS:
        path = root / name
        if not path.is_dir() or path.is_symlink() or stat.S_IMODE(path.stat().st_mode) != 0o700:
            errors.append(f"subroot:{name}")
    value = {
        "protocol": protocol.PROTOCOL_ID,
        "state_slice": protocol.STATE_SLICE,
        "root": str(root),
        "owner_uid": os.getuid(),
        "mode": "0700",
        "valid": not errors,
        "errors": errors,
    }
    return {**value, "receipt_sha256": protocol.digest_json(value)}


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


def write_raw_events(
    root: Path,
    repository_root: Path,
    run_id: str,
    events: Sequence[protocol.TraceEvent],
    *,
    event_stream_sha256: str,
) -> dict[str, Any]:
    receipt = validate_root(root, repository_root)
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


def write_aggregate(root: Path, repository_root: Path, filename: str, aggregate: dict[str, Any]) -> Path:
    receipt = validate_root(root, repository_root)
    if not receipt["valid"]:
        raise protocol.ProtocolError("custody validation failed")
    lowered = " ".join(aggregate.keys()).lower()
    if any(fragment in lowered for fragment in protocol.RAW_FIELD_FRAGMENTS):
        raise protocol.ProtocolError("raw aggregate field rejected")
    path = root / "aggregate" / filename
    _write_private(path, protocol.canonical_bytes(aggregate) + b"\n")
    return path
