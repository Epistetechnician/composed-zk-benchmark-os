"""Persist replayable V2 event manifests and validator receipts without model execution.

State slice: astral-trace-completeness-gemma3-end-to-end-v2.
"""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import custody_v2 as custody
import protocol_v2 as protocol
import registry_v2 as registry
import validate_v2


def _write_private_json(root: Path, repository_root: Path, subroot: str, filename: str, value: dict[str, Any]) -> Path:
    receipt = custody.validate_root(root, repository_root)
    if not receipt["valid"] or subroot not in custody.SUBROOTS:
        raise protocol.ProtocolError("private JSON target failed custody validation")
    path = root / subroot / filename
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(protocol.canonical_bytes(value) + b"\n")
            handle.flush()
            os.fsync(handle.fileno())
    except BaseException:
        path.unlink(missing_ok=True)
        raise
    return path


def _events(path: Path) -> list[protocol.TraceEvent]:
    values = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line:
            values.append(protocol.TraceEvent.from_dict(json.loads(line)))
    return values


def _expectation(events: list[protocol.TraceEvent]) -> protocol.RunExpectation:
    steps = sum(event.kind == "generation_step_start" for event in events)
    token_events = sum(event.kind == "input_token" for event in events)
    return protocol.RunExpectation(
        generation_steps=steps,
        input_token_count=token_events - steps + 1,
        module_input_paths=registry.expected_input_paths(),
        module_output_paths=registry.expected_output_paths(),
        attention_modules=registry.attention_paths(),
        interventions=sum(event.kind == "intervention" for event in events),
        sae_feature_events=sum(event.kind == "sae_features" for event in events),
        sae_reconstruction_events=sum(event.kind == "sae_reconstruction" for event in events),
        graph_prediction_events=sum(event.kind == "graph_prediction" for event in events),
    )


def execute(repository_root: Path, custody_root: Path, qualification_path: Path) -> dict[str, Any]:
    qualification = protocol.strict_json(qualification_path)
    if qualification.get("status") != "QUALIFICATION_FAILED" or qualification.get("assessment_opened") is not False:
        raise protocol.ProtocolError("reconciliation is restricted to the sealed failed qualification")
    qualification_sha256 = qualification.get("qualification_sha256")
    expected_qualification = {key: value for key, value in qualification.items() if key != "qualification_sha256"}
    if qualification_sha256 != protocol.digest_json(expected_qualification):
        raise protocol.ProtocolError("qualification digest mismatch")
    manifests = {}
    receipts = {}
    for run_id, expected_aggregate_sha256 in qualification["run_aggregate_sha256"].items():
        raw_path = custody_root / "raw" / f"{run_id}.events.jsonl"
        events = _events(raw_path)
        aggregate = protocol.validate_event_stream(events, _expectation(events))
        if protocol.digest_json(aggregate) != expected_aggregate_sha256:
            raise protocol.ProtocolError(f"run aggregate hash mismatch: {run_id}")
        created = datetime.fromtimestamp(raw_path.stat().st_mtime, tz=timezone.utc)
        manifest_body = {
            "protocol": protocol.PROTOCOL_ID,
            "state_slice": protocol.STATE_SLICE,
            "qualification_sha256": qualification_sha256,
            "run_id": run_id,
            "raw_relative_path": raw_path.relative_to(custody_root).as_posix(),
            "raw_sha256": protocol.sha256_file(raw_path),
            "event_count": len(events),
            "event_stream_sha256": aggregate["event_stream_sha256"],
            "created_at": created.isoformat(),
            "expires_at": (created + timedelta(hours=protocol.RAW_RETENTION_HOURS)).isoformat(),
        }
        manifest = {**manifest_body, "manifest_sha256": protocol.digest_json(manifest_body)}
        receipt = validate_v2.validate_run(
            aggregate,
            manifest,
            custody_root=custody_root,
            repository_root=repository_root,
        )
        if not receipt["valid"]:
            raise protocol.ProtocolError(f"reconciled validation failed: {run_id}:{receipt['errors']}")
        _write_private_json(custody_root, repository_root, "aggregate", f"{run_id}.event-manifest.json", manifest)
        _write_private_json(custody_root, repository_root, "receipts", f"{run_id}.validator-receipt.json", receipt)
        manifests[run_id] = manifest["manifest_sha256"]
        receipts[run_id] = receipt["receipt_sha256"]
    capture_manifests = []
    for path in sorted((custody_root / "raw").glob("*.captures.safetensors")):
        run_id = path.name.removesuffix(".captures.safetensors")
        from safetensors import safe_open

        with safe_open(path, framework="pt", device="cpu") as handle:
            tensor_count = len(handle.keys())
        value = {
            "run_id": run_id,
            "relative_path": path.relative_to(custody_root).as_posix(),
            "sha256": protocol.sha256_file(path),
            "tensor_count": tensor_count,
        }
        value["manifest_sha256"] = protocol.digest_json(value)
        capture_manifests.append(value["manifest_sha256"])
        _write_private_json(custody_root, repository_root, "aggregate", f"{run_id}.capture-manifest.json", value)
    if sorted(capture_manifests) != sorted(qualification["capture_manifest_sha256"]):
        raise protocol.ProtocolError("capture manifest reconciliation mismatch")
    source_sha256 = protocol.sha256_file(Path(__file__).resolve())
    value = {
        "protocol": protocol.PROTOCOL_ID,
        "state_slice": protocol.STATE_SLICE,
        "qualification_sha256": qualification_sha256,
        "reconciliation_source_sha256": source_sha256,
        "model_execution": False,
        "assessment_opened": False,
        "event_manifest_sha256": manifests,
        "validator_receipt_sha256": receipts,
        "capture_manifest_sha256": sorted(capture_manifests),
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
    parser.add_argument(
        "--qualification",
        type=Path,
        default=protocol.CUSTODY_ROOT / "aggregate" / "qualification-29c2eb957a79419995992533d3b843a7.json",
    )
    args = parser.parse_args(argv)
    result = execute(args.repository_root.resolve(), args.custody_root.resolve(), args.qualification.resolve())
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
