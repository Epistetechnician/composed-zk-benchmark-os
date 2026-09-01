"""External ephemeral custody checks for trace completeness V1.

State slice: astral-trace-completeness-native-instrument-v1.
"""

from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Any

import protocol


def validate_custody_root(root: Path, repository_root: Path, *, require_existing: bool = True) -> dict[str, Any]:
    root = Path(root)
    repository_root = repository_root.resolve()
    errors: list[str] = []
    if root.is_symlink():
        errors.append("root_is_symlink")
    root = root.resolve()
    try:
        protocol.assert_external(root, repository_root)
    except protocol.ProtocolError as exc:
        errors.append(f"repository_local:{exc}")
    if require_existing and not root.is_dir():
        errors.append("root_missing")
    if root.exists() and (os.stat(root).st_mode & 0o777) != 0o700:
        errors.append("root_permissions_not_0700")
    if root.exists() and os.stat(root).st_uid != os.getuid():
        errors.append("root_owner_mismatch")
    if root.exists():
        for name in ("raw", "aggregate"):
            child = root / name
            if not child.is_dir():
                errors.append(f"{name}_subroot_missing")
            elif (os.stat(child).st_mode & 0o777) != 0o700:
                errors.append(f"{name}_subroot_permissions_not_0700")
            elif os.stat(child).st_uid != os.getuid():
                errors.append(f"{name}_subroot_owner_mismatch")
        for path in root.rglob("*"):
            if path.is_symlink():
                errors.append(f"symlink:{path.relative_to(root).as_posix()}")
    return {
        "protocol": protocol.PROTOCOL_ID,
        "state_slice": protocol.STATE_SLICE,
        "root": str(root),
        "valid": not errors,
        "errors": sorted(set(errors)),
        "raw_retention_hours": protocol.RAW_RETENTION_HOURS,
        "aggregate_only_publication": True,
    }


def aggregate_file_manifest(root: Path, repository_root: Path) -> dict[str, Any]:
    """Hash only non-raw aggregate files below an external custody root."""

    receipt = validate_custody_root(root, repository_root)
    if not receipt["valid"]:
        raise protocol.ProtocolError("custody root failed validation")
    files: list[dict[str, Any]] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.is_symlink():
            continue
        relative = path.relative_to(root).as_posix()
        if relative.startswith("raw/"):
            continue
        files.append({"path": relative, "bytes": path.stat().st_size, "sha256": protocol.sha256_file(path)})
    manifest = {
        "protocol": protocol.PROTOCOL_ID,
        "state_slice": protocol.STATE_SLICE,
        "root": str(root.resolve()),
        "files": files,
        "raw_files_hashed": False,
    }
    manifest["manifest_sha256"] = protocol.canonical_digest(manifest)
    return manifest


def build_event_manifest(
    aggregate: dict[str, Any],
    root: Path,
    raw_trace_relative_path: str,
    repository_root: Path,
) -> dict[str, Any]:
    """Bind an aggregate to a hashed external raw event file."""

    receipt = validate_custody_root(root, repository_root)
    if not receipt["valid"]:
        raise protocol.ProtocolError("custody root failed validation")
    root = root.resolve()
    relative = Path(raw_trace_relative_path)
    raw_path_unresolved = root / relative
    raw_path = raw_path_unresolved.resolve()
    if relative.is_absolute() or relative.parts[:1] != ("raw",) or root / "raw" not in raw_path.parents:
        raise protocol.ProtocolError("raw trace must be below the custody raw subroot")
    if raw_path_unresolved.is_symlink() or not raw_path.is_file():
        raise protocol.ProtocolError("raw trace is missing or symlinked")
    manifest = {
        "protocol": protocol.PROTOCOL_ID,
        "state_slice": protocol.STATE_SLICE,
        "raw_trace_relative_path": relative.as_posix(),
        "raw_trace_sha256": protocol.sha256_file(raw_path),
        "event_count": aggregate.get("event_count"),
        "event_counts": aggregate.get("event_counts"),
        "expected_event_counts": aggregate.get("expected_event_counts"),
        "event_expectation_sha256": aggregate.get("event_expectation_sha256"),
        "module_registry": aggregate.get("module_registry"),
        "module_registry_sha256": aggregate.get("module_registry_sha256"),
        "event_stream_sha256": aggregate.get("event_stream_sha256"),
    }
    manifest["manifest_sha256"] = protocol.canonical_digest(manifest)
    return manifest


def expire_raw(root: Path, repository_root: Path, *, now: float | None = None) -> dict[str, Any]:
    """Delete only expired regular files below the validated raw subroot."""

    receipt = validate_custody_root(root, repository_root)
    if not receipt["valid"]:
        raise protocol.ProtocolError("custody root failed validation")
    raw_root = root.resolve() / "raw"
    cutoff = (time.time() if now is None else now) - protocol.RAW_RETENTION_HOURS * 60 * 60
    deleted: list[str] = []
    expired_symlinks: list[str] = []
    for path in sorted(raw_root.rglob("*")):
        if path.is_symlink():
            expired_symlinks.append(path.relative_to(raw_root).as_posix())
        elif path.is_file() and path.stat().st_mtime < cutoff:
            path.unlink()
            deleted.append(path.relative_to(raw_root).as_posix())
    return {
        "protocol": protocol.PROTOCOL_ID,
        "state_slice": protocol.STATE_SLICE,
        "raw_retention_hours": protocol.RAW_RETENTION_HOURS,
        "deleted": deleted,
        "symlinks_not_deleted": expired_symlinks,
    }
