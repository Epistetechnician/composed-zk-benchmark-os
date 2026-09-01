"""Reconcile persisted V3 raw streams after qualification publication.

State slice: astral-trace-completeness-gemma3-end-to-end-v3.
No model execution occurs.
"""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import custody_v3 as custody
import protocol_v3 as protocol
import registry_v3 as registry
import validate_v3 as validator


def _write_private(path: Path, value: dict[str, Any]) -> None:
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(protocol.canonical_bytes(value) + b"\n")
            handle.flush()
            os.fsync(handle.fileno())
    except BaseException:
        path.unlink(missing_ok=True)
        raise


def _events(path: Path) -> tuple[protocol.TraceEvent, ...]:
    def no_duplicate_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        value: dict[str, Any] = {}
        for key, item in pairs:
            if key in value:
                raise protocol.ProtocolError(f"duplicate JSON key: {key}")
            value[key] = item
        return value

    def reject_constant(value: str) -> None:
        raise protocol.ProtocolError(f"nonstandard JSON constant: {value}")

    return tuple(
        protocol.TraceEvent.from_dict(
            json.loads(line, object_pairs_hook=no_duplicate_pairs, parse_constant=reject_constant)
        )
        for line in path.read_text(encoding="utf-8").splitlines()
        if line
    )


def _expectation(events: tuple[protocol.TraceEvent, ...]) -> protocol.RunExpectation:
    steps = sum(event.kind == "generation_step_start" for event in events)
    token_events = sum(event.kind == "input_token" for event in events)
    if steps <= 0:
        raise protocol.ProtocolError("empty V3 generation stream")
    counts = {kind: sum(event.kind == kind for event in events) for kind in protocol.EVENT_KINDS}
    return protocol.RunExpectation(
        generation_steps=steps,
        input_token_count=token_events - steps + 1,
        module_input_paths=registry.expected_input_paths(),
        module_output_paths=registry.expected_output_paths(),
        attention_modules=registry.attention_paths(),
        cache_updates_per_step=protocol._legacy_protocol.LAYER_COUNT,
        interventions=counts["intervention"],
        sae_feature_events=counts["sae_features"],
        sae_reconstruction_events=counts["sae_reconstruction"],
        graph_prediction_events=counts["graph_prediction"],
    )


def _capture_manifest(path: Path, root: Path) -> dict[str, Any]:
    from safetensors import safe_open

    with safe_open(str(path), framework="pt", device="cpu") as handle:
        tensor_count = len(handle.keys())
    value = {
        "protocol": protocol.PROTOCOL_ID,
        "state_slice": protocol.STATE_SLICE,
        "run_id": path.name.removesuffix(".captures.safetensors"),
        "relative_path": path.relative_to(root).as_posix(),
        "sha256": protocol.sha256_file(path),
        "tensor_count": tensor_count,
    }
    return {**value, "manifest_sha256": protocol.digest_json(value)}


def execute(repository_root: Path, custody_root: Path, qualification_path: Path) -> dict[str, Any]:
    receipt = protocol.custody_receipt(custody_root, repository_root)
    if not receipt["valid"]:
        raise protocol.ProtocolError("V3 custody validation failed before reconciliation")
    qualification = protocol.strict_json(qualification_path)
    if qualification.get("assessment_opened") is not False or qualification.get("status") != "QUALIFICATION_FAILED":
        raise protocol.ProtocolError("V3 reconciliation requires the sealed failed qualification")
    if protocol.digest_json({key: value for key, value in qualification.items() if key != "qualification_sha256"}) != qualification["qualification_sha256"]:
        raise protocol.ProtocolError("V3 qualification digest mismatch")
    manifest_digests: dict[str, str] = {}
    validator_digests: dict[str, str] = {}
    for run_id, expected_hash in qualification["run_aggregate_sha256"].items():
        raw_path = custody_root / "raw" / f"{run_id}.events.jsonl"
        events = _events(raw_path)
        aggregate = protocol.validate_event_stream(events, _expectation(events))
        if protocol.digest_json(aggregate) != expected_hash:
            raise protocol.ProtocolError(f"V3 run aggregate mismatch: {run_id}")
        created = datetime.fromtimestamp(raw_path.stat().st_mtime, tz=timezone.utc)
        manifest_body = {
            "protocol": protocol.PROTOCOL_ID,
            "state_slice": protocol.STATE_SLICE,
            "qualification_sha256": qualification["qualification_sha256"],
            "run_id": run_id,
            "raw_relative_path": raw_path.relative_to(custody_root).as_posix(),
            "raw_sha256": protocol.sha256_file(raw_path),
            "event_count": len(events),
            "event_stream_sha256": aggregate["event_stream_sha256"],
            "created_at": created.isoformat(),
            "expires_at": (created + timedelta(hours=protocol.RAW_RETENTION_HOURS)).isoformat(),
        }
        manifest = {**manifest_body, "manifest_sha256": protocol.digest_json(manifest_body)}
        receipt = validator.validate_run(
            aggregate,
            manifest,
            custody_root=custody_root,
            repository_root=repository_root,
        )
        if not receipt["valid"]:
            raise protocol.ProtocolError(f"reconciled V3 validation failed: {run_id}:{receipt['errors']}")
        custody.write_aggregate(custody_root, repository_root, f"{run_id}.event-manifest.json", manifest)
        _write_private(custody_root / "receipts" / f"{run_id}.validator-receipt.json", receipt)
        manifest_digests[run_id] = manifest["manifest_sha256"]
        validator_digests[run_id] = receipt["receipt_sha256"]

    capture_manifests: list[str] = []
    for path in sorted((custody_root / "raw").glob("*.captures.safetensors")):
        manifest = _capture_manifest(path, custody_root)
        custody.write_aggregate(
            custody_root,
            repository_root,
            f"{manifest['run_id']}.capture-manifest.json",
            manifest,
        )
        capture_manifests.append(manifest["manifest_sha256"])
    if sorted(capture_manifests) != sorted(qualification["capture_manifest_sha256"]):
        raise protocol.ProtocolError("V3 capture manifest reconciliation mismatch")

    value = {
        "protocol": protocol.PROTOCOL_ID,
        "state_slice": protocol.STATE_SLICE,
        "campaign_id": qualification["campaign_id"],
        "qualification_sha256": qualification["qualification_sha256"],
        "reconciliation_source_sha256": protocol.sha256_file(Path(__file__).resolve()),
        "model_execution": False,
        "assessment_opened": False,
        "event_manifest_sha256": manifest_digests,
        "validator_receipt_sha256": validator_digests,
        "capture_manifest_sha256": sorted(capture_manifests),
        "qualification_event_manifest_sha256_unpersisted": qualification["event_manifest_sha256"],
        "raw_manifest_reconstructed_from_existing_stream": True,
        "valid": True,
    }
    value["reconciliation_sha256"] = protocol.digest_json(value)
    output = custody.write_aggregate(
        custody_root,
        repository_root,
        f"reconciliation-{qualification['campaign_id']}.json",
        value,
    )
    return {**value, "aggregate_path": str(output)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--custody-root", type=Path, default=protocol.CUSTODY_ROOT)
    parser.add_argument("--qualification", type=Path, required=True)
    args = parser.parse_args(argv)
    print(json.dumps(execute(args.repository_root.resolve(), args.custody_root.resolve(), args.qualification.resolve()), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
