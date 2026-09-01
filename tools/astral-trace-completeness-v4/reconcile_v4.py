"""Reconcile V4 persisted manifests and receipts without model execution.

State slice: astral-trace-completeness-gemma3-end-to-end-v4.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import custody_v4 as custody
import protocol_v4 as protocol
import registry_v4 as registry
import validate_v4 as validator


def _events(path: Path) -> tuple[protocol.TraceEvent, ...]:
    def no_duplicate_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise protocol.ProtocolError(f"duplicate JSON key: {key}")
            result[key] = value
        return result

    def reject_constant(value: str) -> None:
        raise protocol.ProtocolError(f"nonstandard JSON constant: {value}")

    return tuple(protocol.TraceEvent.from_dict(json.loads(line, object_pairs_hook=no_duplicate_pairs, parse_constant=reject_constant)) for line in path.read_text(encoding="utf-8").splitlines() if line)


def _expectation(events: tuple[protocol.TraceEvent, ...]) -> protocol.RunExpectation:
    steps = sum(event.kind == "generation_step_start" for event in events)
    token_events = sum(event.kind == "input_token" for event in events)
    if steps <= 0:
        raise protocol.ProtocolError("empty V4 generation stream")
    counts = {kind: sum(event.kind == kind for event in events) for kind in protocol.EVENT_KINDS}
    return protocol.RunExpectation(
        generation_steps=steps,
        input_token_count=token_events - steps + 1,
        module_input_paths=registry.expected_input_paths(),
        module_output_paths=registry.expected_output_paths(),
        attention_modules=registry.attention_paths(),
        interventions=counts["intervention"],
        sae_feature_events=counts["sae_features"],
        sae_reconstruction_events=counts["sae_reconstruction"],
        graph_prediction_events=counts["graph_prediction"],
    )


def execute(repository_root: Path, custody_root: Path, qualification_path: Path) -> dict[str, Any]:
    if not custody.validate_root(custody_root, repository_root)["valid"]:
        raise protocol.ProtocolError("V4 custody validation failed before reconciliation")
    qualification = protocol.strict_json(qualification_path)
    if qualification.get("assessment_opened") is not False or qualification.get("status") not in {"QUALIFICATION_FAILED", "QUALIFIED_PREASSESSMENT_OPEN"}:
        raise protocol.ProtocolError("V4 reconciliation requires sealed qualification")
    qualification_sha256 = qualification.get("qualification_sha256")
    if qualification_sha256 != protocol.digest_json({key: value for key, value in qualification.items() if key != "qualification_sha256"}):
        raise protocol.ProtocolError("V4 qualification digest mismatch")

    event_manifests: dict[str, str] = {}
    validator_receipts: dict[str, str] = {}
    for run_id, expected_aggregate_sha256 in qualification["run_aggregate_sha256"].items():
        manifest_path = custody_root / "aggregate" / f"{run_id}.event-manifest.json"
        manifest = protocol.strict_json(manifest_path)
        if manifest.get("manifest_sha256") != qualification["event_manifest_sha256"].get(run_id):
            raise protocol.ProtocolError(f"V4 event manifest digest mismatch: {run_id}")
        if manifest.get("qualification_sha256") is not None:
            raise protocol.ProtocolError("V4 event manifest unexpectedly binds a post-run qualification digest")
        raw_path = custody_root / str(manifest["raw_relative_path"])
        events = _events(raw_path)
        aggregate = protocol.validate_event_stream(events, _expectation(events))
        if protocol.digest_json(aggregate) != expected_aggregate_sha256:
            raise protocol.ProtocolError(f"V4 run aggregate mismatch: {run_id}")
        receipt = validator.validate_run(aggregate, manifest, custody_root=custody_root, repository_root=repository_root)
        if not receipt["valid"]:
            raise protocol.ProtocolError(f"V4 reconciled validation failed: {run_id}:{receipt['errors']}")
        receipt_path = custody_root / "receipts" / f"{run_id}.validator-receipt.json"
        stored_receipt = protocol.strict_json(receipt_path)
        if stored_receipt != receipt or stored_receipt.get("receipt_sha256") != qualification["validator_receipt_sha256"].get(run_id):
            raise protocol.ProtocolError(f"V4 stored validator receipt mismatch: {run_id}")
        event_manifests[run_id] = manifest["manifest_sha256"]
        validator_receipts[run_id] = receipt["receipt_sha256"]

    capture_manifests = []
    for path in sorted((custody_root / "aggregate").glob("*.capture-manifest.json")):
        manifest = protocol.strict_json(path)
        if manifest.get("manifest_sha256") not in qualification["capture_manifest_sha256"]:
            raise protocol.ProtocolError(f"V4 capture manifest is not bound to qualification: {path.name}")
        capture_manifests.append(manifest["manifest_sha256"])
    if sorted(capture_manifests) != sorted(qualification["capture_manifest_sha256"]):
        raise protocol.ProtocolError("V4 capture manifest set mismatch")

    value = {
        "protocol": protocol.PROTOCOL_ID,
        "state_slice": protocol.STATE_SLICE,
        "campaign_id": qualification["campaign_id"],
        "qualification_sha256": qualification_sha256,
        "reconciliation_source_sha256": protocol.sha256_file(Path(__file__).resolve()),
        "model_execution": False,
        "assessment_opened": False,
        "event_manifest_sha256": event_manifests,
        "validator_receipt_sha256": validator_receipts,
        "capture_manifest_sha256": sorted(capture_manifests),
        "valid": True,
    }
    value["reconciliation_sha256"] = protocol.digest_json(value)
    output = custody.write_aggregate(custody_root, repository_root, f"reconciliation-{qualification['campaign_id']}.json", value)
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
