"""Verify persisted V2 custody receipts and supersede the first reconciliation.

State slice: astral-trace-completeness-gemma3-end-to-end-v2.
No model execution occurs.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import custody_v2 as custody
import protocol_v2 as protocol
import qualify_v2
import reconcile_v2
import validate_v2


DEPENDENCIES = (
    "protocol_v2.py",
    "registry_v2.py",
    "custody_v2.py",
    "validate_v2.py",
    "qualify_v2.py",
    "reconcile_v2.py",
    "verify_reconciliation_v2.py",
)


def execute(repository_root: Path, custody_root: Path, qualification_path: Path) -> dict[str, Any]:
    qualification = protocol.strict_json(qualification_path)
    qualification_sha256 = qualification["qualification_sha256"]
    if qualification.get("status") != "QUALIFICATION_FAILED" or qualification.get("assessment_opened") is not False:
        raise protocol.ProtocolError("only the sealed failed qualification may be reconciled")
    if protocol.digest_json({key: value for key, value in qualification.items() if key != "qualification_sha256"}) != qualification_sha256:
        raise protocol.ProtocolError("qualification digest mismatch")
    if qualify_v2._source_manifest() != qualification["source"]:
        raise protocol.ProtocolError("executed qualification source is not preserved")
    manifest_digests = {}
    receipt_digests = {}
    for run_id, expected_aggregate_sha256 in qualification["run_aggregate_sha256"].items():
        raw_path = custody_root / "raw" / f"{run_id}.events.jsonl"
        events = reconcile_v2._events(raw_path)
        aggregate = protocol.validate_event_stream(events, reconcile_v2._expectation(events))
        if protocol.digest_json(aggregate) != expected_aggregate_sha256:
            raise protocol.ProtocolError(f"run aggregate mismatch: {run_id}")
        manifest_path = custody_root / "aggregate" / f"{run_id}.event-manifest.json"
        receipt_path = custody_root / "receipts" / f"{run_id}.validator-receipt.json"
        manifest = protocol.strict_json(manifest_path)
        receipt = protocol.strict_json(receipt_path)
        if manifest.get("qualification_sha256") != qualification_sha256:
            raise protocol.ProtocolError(f"manifest qualification binding mismatch: {run_id}")
        recomputed_receipt = validate_v2.validate_run(
            aggregate,
            manifest,
            custody_root=custody_root,
            repository_root=repository_root,
        )
        if receipt != recomputed_receipt or not receipt.get("valid"):
            raise protocol.ProtocolError(f"validator receipt mismatch: {run_id}")
        manifest_digests[run_id] = protocol.sha256_file(manifest_path)
        receipt_digests[run_id] = protocol.sha256_file(receipt_path)
    capture_digests = []
    for path in sorted((custody_root / "aggregate").glob("*.capture-manifest.json")):
        value = protocol.strict_json(path)
        if value.get("manifest_sha256") not in qualification["capture_manifest_sha256"]:
            raise protocol.ProtocolError(f"unknown capture manifest: {path.name}")
        raw_path = custody_root / value["relative_path"]
        if protocol.sha256_file(raw_path) != value["sha256"]:
            raise protocol.ProtocolError(f"capture hash mismatch: {path.name}")
        capture_digests.append(protocol.sha256_file(path))
    if len(capture_digests) != len(qualification["capture_manifest_sha256"]):
        raise protocol.ProtocolError("capture manifest count mismatch")
    source_root = Path(__file__).resolve().parent
    source_files = {name: protocol.sha256_file(source_root / name) for name in DEPENDENCIES}
    source = {"files": source_files, "manifest_sha256": protocol.digest_json(source_files)}
    value = {
        "protocol": protocol.PROTOCOL_ID,
        "state_slice": protocol.STATE_SLICE,
        "qualification_sha256": qualification_sha256,
        "qualification_source_preserved": True,
        "source": source,
        "model_execution": False,
        "assessment_opened": False,
        "event_manifest_file_sha256": manifest_digests,
        "validator_receipt_file_sha256": receipt_digests,
        "capture_manifest_file_sha256": capture_digests,
        "supersedes_reconciliation_sha256": "24f6bab21b9749369061b7366a196e081a6e32b2631974ba098a187f3b991db8",
        "valid": True,
    }
    value["reconciliation_sha256"] = protocol.digest_json(value)
    output = custody.write_aggregate(
        custody_root,
        repository_root,
        f"reconciliation-r2-{qualification['campaign_id']}.json",
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

