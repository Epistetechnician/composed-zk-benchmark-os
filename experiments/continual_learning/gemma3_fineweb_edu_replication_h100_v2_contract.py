#!/usr/bin/env python3
"""Closed-world contract checks for the Gemma3 FineWeb-Edu H100 V2 slice.

State slice: continual-learning-gemma3-fineweb-edu-replication-h100-v2.

This module is deliberately model-free and provider-free. It validates frozen
bytes and post-run custody boundaries; it never loads a model, contacts a
provider, or submits a job.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import math
import os
import re
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence


STATE_SLICE = "continual-learning-gemma3-fineweb-edu-replication-h100-v2"
IMPLEMENTATION_MANIFEST_SCHEMA = (
    "gemma3-fineweb-edu-replication-h100-v2-implementation"
)
LAUNCH_SCHEMA = "gemma3-fineweb-edu-replication-h100-v2-launch"
PROVIDER_RECEIPT_SCHEMA = "gemma3-fineweb-edu-replication-h100-v2-provider-receipt"
ALLOWED_STOP_REASONS = frozenset(
    {"completed", "failed_gate", "budget_boundary", "provider_cancelled"}
)
PROVIDER_RECEIPT_KEYS = {
    "schema",
    "state_slice",
    "provider",
    "provider_project",
    "node_type",
    "job_mode",
    "allocation_id",
    "node_id",
    "start_utc",
    "stop_utc",
    "quoted_gpu_usd_per_minute",
    "charged_usd",
    "hard_usd_ceiling",
    "estimated_max_total_usd",
    "stop_reason",
    "launch_manifest_sha256",
    "container_digest",
    "provider_attestation",
    "receipt_sha256",
}
ATTESTATION_KEYS = {"issuer", "key_id", "algorithm", "payload_sha256", "signature"}
RESULT_FILES = frozenset(
    {"provider-receipt.json", "result.json", "result-receipt.json"}
)


def canonical(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode(
        "utf-8"
    )


def digest(value: Mapping[str, Any], field: str) -> str:
    body = {key: item for key, item in value.items() if key != field}
    return hashlib.sha256(canonical(body)).hexdigest()


def sha256_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def _safe_relative(path: str) -> Path:
    relative = Path(path)
    if relative.is_absolute() or ".." in relative.parts or not path:
        raise ValueError("manifest path is unsafe")
    return relative


def _hex(value: Any, label: str) -> str:
    if not isinstance(value, str) or re.fullmatch(r"[0-9a-f]{64}", value) is None:
        raise ValueError(f"{label} is not a lowercase SHA-256 digest")
    return value


def _oci_digest(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.startswith("sha256:"):
        raise ValueError(f"{label} is not an OCI SHA-256 digest")
    return _hex(value[7:], label)


def _finite(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{label} is not numeric")
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"{label} is not finite")
    return number


def _utc(value: Any, label: str) -> dt.datetime:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise ValueError(f"{label} is not UTC")
    try:
        parsed = dt.datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as error:
        raise ValueError(f"{label} is invalid") from error
    if parsed.tzinfo is None or parsed.utcoffset() != dt.timedelta(0):
        raise ValueError(f"{label} is not UTC")
    return parsed


def _load_object(path: Path, label: str) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"{label} must be a regular file")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be an object")
    return value


def build_implementation_manifest(
    repo_root: Path, implementation_files: Sequence[str]
) -> dict[str, Any]:
    """Build a self-digested manifest without recursively listing the manifest."""
    files: list[dict[str, str]] = []
    for name in implementation_files:
        relative = _safe_relative(name)
        path = repo_root / relative
        if path.is_symlink() or not path.is_file():
            raise ValueError(f"implementation file is missing: {relative}")
        files.append({"path": relative.as_posix(), "sha256": sha256_file(path)})
    if len({item["path"] for item in files}) != len(files):
        raise ValueError("implementation file list contains duplicates")
    body: dict[str, Any] = {
        "schema": IMPLEMENTATION_MANIFEST_SCHEMA,
        "state_slice": STATE_SLICE,
        "files": files,
    }
    return {**body, "manifest_sha256": digest(body, "manifest_sha256")}


def validate_implementation_manifest(
    path: Path, repo_root: Path, expected_files: Sequence[str]
) -> dict[str, Any]:
    manifest = _load_object(path, "implementation manifest")
    if set(manifest) != {"schema", "state_slice", "files", "manifest_sha256"}:
        raise ValueError("implementation manifest schema is not closed")
    if (
        manifest["schema"] != IMPLEMENTATION_MANIFEST_SCHEMA
        or manifest["state_slice"] != STATE_SLICE
    ):
        raise ValueError("implementation manifest identity mismatch")
    files = manifest["files"]
    if not isinstance(files, list):
        raise ValueError("implementation manifest files are invalid")
    if [item.get("path") for item in files if isinstance(item, dict)] != list(
        expected_files
    ):
        raise ValueError("implementation manifest file set is not exact")
    for item in files:
        if not isinstance(item, dict) or set(item) != {"path", "sha256"}:
            raise ValueError("implementation manifest entry is invalid")
        relative = _safe_relative(item["path"])
        _hex(item["sha256"], "implementation file digest")
        file_path = repo_root / relative
        if file_path.is_symlink() or not file_path.is_file():
            raise ValueError(f"implementation file is missing: {relative}")
        if sha256_file(file_path) != item["sha256"]:
            raise ValueError(f"implementation file digest mismatch: {relative}")
    if manifest["manifest_sha256"] != digest(manifest, "manifest_sha256"):
        raise ValueError("implementation manifest self digest mismatch")
    return manifest


def provider_payload_digest(receipt: Mapping[str, Any]) -> str:
    payload = {
        key: value
        for key, value in receipt.items()
        if key not in {"provider_attestation", "receipt_sha256"}
    }
    return hashlib.sha256(canonical(payload)).hexdigest()


def validate_provider_receipt(
    receipt: Mapping[str, Any],
    launch: Mapping[str, Any],
    verify_attestation: Callable[[Mapping[str, Any], Mapping[str, Any]], bool] | None = None,
) -> dict[str, Any]:
    """Validate provider facts and require an independent signature verifier."""
    if set(receipt) != PROVIDER_RECEIPT_KEYS:
        raise ValueError("provider receipt schema is not closed")
    required_launch = {
        "schema", "state_slice", "provider", "provider_project", "node_type",
        "job_mode", "container_digest", "manifest_sha256",
        "quoted_gpu_usd_per_minute", "max_runtime_minutes",
        "estimated_max_total_usd", "hard_usd_ceiling",
    }
    if (
        set(launch) != required_launch
        or launch["schema"] != LAUNCH_SCHEMA
        or launch["state_slice"] != STATE_SLICE
    ):
        raise ValueError("launch contract schema or identity mismatch")
    for key in ("manifest_sha256", "launch_manifest_sha256"):
        _hex(launch["manifest_sha256"] if key == "manifest_sha256" else receipt[key], key)
    _oci_digest(launch["container_digest"], "launch container digest")
    _oci_digest(receipt["container_digest"], "provider container digest")
    if receipt["schema"] != PROVIDER_RECEIPT_SCHEMA or receipt["state_slice"] != STATE_SLICE:
        raise ValueError("provider receipt identity mismatch")
    for key in ("provider", "provider_project", "node_type", "job_mode", "container_digest"):
        if receipt[key] != launch[key]:
            raise ValueError(f"provider receipt {key} binding mismatch")
    if receipt["provider"] != "givemeanode" or receipt["node_type"] != "h100-1" or receipt["job_mode"] != "batch":
        raise ValueError("provider job shape mismatch")
    if receipt["launch_manifest_sha256"] != launch["manifest_sha256"]:
        raise ValueError("provider receipt launch binding mismatch")
    for key in ("allocation_id", "node_id"):
        if not isinstance(receipt[key], str) or not receipt[key].strip():
            raise ValueError(f"provider receipt {key} is missing")
    start = _utc(receipt["start_utc"], "provider start time")
    stop = _utc(receipt["stop_utc"], "provider stop time")
    if stop <= start:
        raise ValueError("provider stop time must be after start time")
    if (stop - start).total_seconds() > _finite(launch["max_runtime_minutes"], "maximum runtime") * 60:
        raise ValueError("provider runtime exceeds sealed maximum")
    if receipt["stop_reason"] not in ALLOWED_STOP_REASONS:
        raise ValueError("provider stop reason is not allowed")
    quote = _finite(receipt["quoted_gpu_usd_per_minute"], "provider quote")
    charged = _finite(receipt["charged_usd"], "provider charged USD")
    estimate = _finite(receipt["estimated_max_total_usd"], "provider estimated USD")
    ceiling = _finite(receipt["hard_usd_ceiling"], "provider hard USD ceiling")
    if quote <= 0 or charged < 0 or estimate <= 0 or ceiling <= 0:
        raise ValueError("provider billing values are outside the allowed domain")
    for key, value in (
        ("quoted_gpu_usd_per_minute", quote),
        ("estimated_max_total_usd", estimate),
        ("hard_usd_ceiling", ceiling),
    ):
        if value != _finite(launch[key], f"launch {key}"):
            raise ValueError(f"provider {key} does not match launch")
    if estimate > ceiling or charged > estimate or charged > ceiling:
        raise ValueError("provider charge exceeds sealed budget")
    attestation = receipt["provider_attestation"]
    if not isinstance(attestation, dict) or set(attestation) != ATTESTATION_KEYS:
        raise ValueError("provider attestation schema is not closed")
    if attestation["issuer"] != "givemeanode" or attestation["algorithm"] != "ed25519":
        raise ValueError("provider attestation identity mismatch")
    if not isinstance(attestation["key_id"], str) or not attestation["key_id"].strip():
        raise ValueError("provider attestation key is missing")
    if _hex(attestation["payload_sha256"], "provider attestation payload") != provider_payload_digest(receipt):
        raise ValueError("provider attestation payload mismatch")
    if not isinstance(attestation["signature"], str) or re.fullmatch(r"[0-9a-f]{128}", attestation["signature"]) is None:
        raise ValueError("provider attestation signature is invalid")
    attestation_payload = {
        key: value
        for key, value in receipt.items()
        if key not in {"provider_attestation", "receipt_sha256"}
    }
    if verify_attestation is None or not verify_attestation(attestation_payload, attestation):
        raise ValueError("provider attestation is not independently verified")
    if receipt["receipt_sha256"] != digest(receipt, "receipt_sha256"):
        raise ValueError("provider receipt self digest mismatch")
    return dict(receipt)


def _snapshot(root: Path) -> dict[str, str]:
    if root.is_symlink() or not root.is_dir():
        raise ValueError("result root must be a real directory")
    snapshot: dict[str, str] = {}
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root).as_posix()
        if path.is_symlink():
            raise ValueError(f"result root contains symlink: {relative}")
        if not path.is_file():
            raise ValueError(f"result root contains unexpected directory: {relative}")
        snapshot[relative] = sha256_file(path)
    return snapshot


def validate_result_root(root: Path) -> dict[str, str]:
    snapshot = _snapshot(root)
    if set(snapshot) != set(RESULT_FILES):
        raise ValueError("result root exact file set mismatch")
    return snapshot


def assert_unchanged(root: Path, before: Mapping[str, str]) -> None:
    after = validate_result_root(root)
    if dict(after) != dict(before):
        raise ValueError("result root changed after validation")


def publish_no_replace(
    staging: Path, final: Path, validated_snapshot: Mapping[str, str]
) -> Path:
    """Publish a validated sibling staging directory without overwriting final."""
    if final.exists() or final.is_symlink():
        raise FileExistsError("final result root already exists")
    if staging.parent != final.parent:
        raise ValueError("staging and final roots must share a parent")
    assert_unchanged(staging, validated_snapshot)
    os.rename(staging, final)
    return final
