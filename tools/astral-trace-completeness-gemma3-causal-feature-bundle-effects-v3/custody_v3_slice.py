"""External custody and raw-expiry helpers for the V3 causal slice.

State slice: astral-trace-completeness-gemma3-causal-feature-bundle-effects-v3.
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Sequence

import protocol_v3_slice as protocol


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
    receipt = protocol.custody_receipt(root, repository_root)
    if not receipt["valid"]:
        raise protocol.ProtocolError("V3 custody validation failed")
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
        raise protocol.ProtocolError("V3 custody validation failed")
    protocol.reject_raw_fields(value)
    path = root / "aggregate" / filename
    _write_private(path, protocol.canonical_bytes(value) + b"\n")
    return path


def _write_binding(root: Path, name: str, payload: dict[str, Any]) -> Path:
    path = protocol.binding_paths(root)[name]
    if path.exists() or path.is_symlink():
        raise protocol.ProtocolError(f"V3 {name} binding already exists")
    unsigned = {
        "protocol": protocol.PROTOCOL_ID,
        "state_slice": protocol.STATE_SLICE,
        "binding_type": name,
        "payload": payload,
    }
    value = {**unsigned, "receipt_sha256": protocol.digest_json(unsigned)}
    _write_private(path, protocol.canonical_bytes(value) + b"\n")
    return path


def write_identity_bindings(
    root: Path,
    repository_root: Path,
    *,
    model_root: Path,
    asset_root: Path,
) -> dict[str, Any]:
    """Create fresh V3 identity receipts without copying scientific results.

    State slice: astral-trace-completeness-gemma3-causal-feature-bundle-effects-v3.
    """

    if not protocol.custody_receipt(root, repository_root)["valid"]:
        raise protocol.ProtocolError("V3 custody validation failed")
    if any(path.exists() or path.is_symlink() for path in protocol.binding_paths(root).values()):
        raise protocol.ProtocolError("V3 identity bindings are immutable once written")

    model_manifest = protocol.tree_manifest(model_root)
    if model_manifest["manifest_sha256"] != protocol.MODEL_MANIFEST_SHA256:
        raise protocol.ProtocolError("model tree does not match the frozen V3 model")
    model_payload = {
        "model_id": protocol.MODEL_ID,
        "manifest_sha256": model_manifest["manifest_sha256"],
        "manifest": model_manifest,
        "transfer": {
            "provider": protocol.NODE_PROVIDER,
            "bucket": protocol.TRANSFER_BUCKET,
            "prefix": protocol.TRANSFER_PREFIXES["model"],
        },
    }

    runtime = {
        **protocol.REQUIRED_RUNTIME_PAYLOAD,
        "manifest_sha256": protocol.digest_json(protocol.REQUIRED_RUNTIME_PAYLOAD),
    }
    if runtime["manifest_sha256"] != protocol.RUNTIME_MANIFEST_SHA256:
        raise protocol.ProtocolError("frozen runtime payload does not match its digest")
    runtime_payload = {
        "runtime_manifest_sha256": runtime["manifest_sha256"],
        "runtime": runtime,
        "transfer": {
            "provider": protocol.NODE_PROVIDER,
            "bucket": protocol.TRANSFER_BUCKET,
            "prefix": protocol.TRANSFER_PREFIXES["source"],
            "execution_network": "offline after bootstrap",
        },
    }

    variant_root = asset_root / protocol.ASSET_VARIANT
    asset_manifest = protocol.tree_manifest(variant_root)
    expected_names = {"config.json", "examples.safetensors", "params.safetensors"}
    if {entry["path"] for entry in asset_manifest["files"]} != expected_names:
        raise protocol.ProtocolError("V3 asset file set is not the frozen Gemma Scope asset")
    asset_qc_core = {
        "asset_repository": protocol.ASSET_REPOSITORY,
        "asset_revision": protocol.ASSET_REVISION,
        "asset_variant": protocol.ASSET_VARIANT,
        "hidden_width": protocol.HIDDEN_WIDTH,
        "feature_width": protocol.FEATURE_WIDTH,
        "file_manifest": asset_manifest,
        "examples_are_metadata_only": True,
        "model_execution": False,
        "reconstruction_target_source": "fresh_model_v3_slice_fit_rows_only",
        "schema": {
            "config": {"path": "config.json", "json": True},
            "examples": {"path": "examples.safetensors", "metadata_only": True},
            "params": {"path": "params.safetensors", "dtype": "float32"},
        },
    }
    asset_qc_sha256 = protocol.digest_json(asset_qc_core)
    if asset_qc_sha256 != protocol.FRESH_ASSET_QC_SHA256:
        raise protocol.ProtocolError("asset QC does not match the frozen V3 asset identity")
    asset_payload = {
        **asset_qc_core,
        "asset_qc_sha256": asset_qc_sha256,
        "transfer": {
            "provider": protocol.NODE_PROVIDER,
            "bucket": protocol.TRANSFER_BUCKET,
            "prefix": protocol.TRANSFER_PREFIXES["asset"],
        },
    }

    import corpus_v3_slice as corpus

    corpus_manifest = corpus.public_manifest()
    corpus_payload = {
        "corpus_id": protocol.CORPUS_ID,
        "seed": protocol.CORPUS_SEED,
        "family_count": protocol.FAMILY_COUNT,
        "manifest_sha256": corpus_manifest["manifest_sha256"],
        "manifest": corpus_manifest,
        "raw_prompt_retention": "external custody raw root only",
    }
    if (
        corpus_payload["manifest_sha256"] != protocol.CORPUS_MANIFEST_SHA256
    ):
        raise protocol.ProtocolError("corpus generator does not match the frozen V3 corpus")

    paths = (
        _write_binding(root, "model", model_payload),
        _write_binding(root, "runtime", runtime_payload),
        _write_binding(root, "asset", asset_payload),
        _write_binding(root, "corpus", corpus_payload),
    )
    return {
        "protocol": protocol.PROTOCOL_ID,
        "state_slice": protocol.STATE_SLICE,
        "paths": [path.relative_to(root).as_posix() for path in paths],
        "digests": protocol.binding_digest_map(root),
        "valid": protocol.validate_external_bindings(root)["valid"],
    }


def validate_root(root: Path, repository_root: Path) -> dict[str, Any]:
    """Return the canonical custody-root validation receipt for V3.

    State slice: astral-trace-completeness-gemma3-causal-feature-bundle-effects-v3.
    The validator imports this adapter so raw-event validation uses the same
    root, mode, owner, and state-slice checks as the custody writer.
    """

    return protocol.custody_receipt(root, repository_root)


def expire_raw(root: Path, repository_root: Path) -> dict[str, Any]:
    receipt = protocol.custody_receipt(root, repository_root)
    if not receipt["valid"]:
        raise protocol.ProtocolError("V3 custody validation failed")
    removed: list[str] = []
    for path in sorted((root / "raw").iterdir()):
        if path.is_symlink() or not path.is_file():
            raise protocol.ProtocolError("raw root contains a non-regular file")
        removed.append(path.relative_to(root).as_posix())
        path.unlink()
    value = {
        "protocol": protocol.PROTOCOL_ID,
        "state_slice": protocol.STATE_SLICE,
        "removed_relative_paths": removed,
        "raw_root_empty": not any((root / "raw").iterdir()),
    }
    if not value["raw_root_empty"]:
        raise protocol.ProtocolError("raw root did not become empty")
    return {**value, "completion_sha256": protocol.digest_json(value)}
