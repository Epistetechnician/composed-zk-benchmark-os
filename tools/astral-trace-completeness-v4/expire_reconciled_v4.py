"""Expire exactly the reconciled V4 raw files.

State slice: astral-trace-completeness-gemma3-end-to-end-v4.
"""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import protocol_v4 as protocol


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


def execute(repository_root: Path, custody_root: Path, qualification_path: Path, reconciliation_path: Path) -> dict[str, Any]:
    receipt = protocol.custody_receipt(custody_root, repository_root)
    if not receipt["valid"]:
        raise protocol.ProtocolError("V4 custody validation failed before raw expiry")
    qualification = protocol.strict_json(qualification_path)
    reconciliation = protocol.strict_json(reconciliation_path)
    if qualification.get("assessment_opened") is not False or qualification.get("status") not in {"QUALIFICATION_FAILED", "QUALIFIED_PREASSESSMENT_OPEN"}:
        raise protocol.ProtocolError("V4 raw expiry requires sealed qualification")
    if qualification.get("qualification_sha256") != protocol.digest_json({key: value for key, value in qualification.items() if key != "qualification_sha256"}):
        raise protocol.ProtocolError("V4 qualification digest mismatch")
    if reconciliation.get("valid") is not True or reconciliation.get("assessment_opened") is not False or reconciliation.get("qualification_sha256") != qualification["qualification_sha256"]:
        raise protocol.ProtocolError("V4 raw expiry requires valid reconciliation bound to qualification")
    if reconciliation.get("reconciliation_sha256") != protocol.digest_json({key: value for key, value in reconciliation.items() if key != "reconciliation_sha256"}):
        raise protocol.ProtocolError("V4 reconciliation digest mismatch")

    expected: dict[str, str] = {}
    for run_id in reconciliation["event_manifest_sha256"]:
        manifest = protocol.strict_json(custody_root / "aggregate" / f"{run_id}.event-manifest.json")
        if manifest.get("manifest_sha256") != reconciliation["event_manifest_sha256"][run_id]:
            raise protocol.ProtocolError(f"V4 event manifest changed: {run_id}")
        expected[manifest["raw_relative_path"]] = manifest["raw_sha256"]
    for path in sorted((custody_root / "aggregate").glob("*.capture-manifest.json")):
        manifest = protocol.strict_json(path)
        if manifest.get("manifest_sha256") not in reconciliation["capture_manifest_sha256"]:
            raise protocol.ProtocolError(f"V4 capture manifest is not reconciled: {path.name}")
        expected[manifest["relative_path"]] = manifest["sha256"]
    observed = {path.relative_to(custody_root).as_posix() for path in (custody_root / "raw").iterdir() if path.is_file()}
    if observed != set(expected):
        raise protocol.ProtocolError("V4 raw root contains missing or unknown files")
    for relative, digest in expected.items():
        path = (custody_root / relative).resolve()
        path.relative_to((custody_root / "raw").resolve())
        if path.is_symlink() or protocol.sha256_file(path) != digest:
            raise protocol.ProtocolError(f"V4 raw expiry target failed validation: {relative}")

    body = {"protocol": protocol.PROTOCOL_ID, "state_slice": protocol.STATE_SLICE, "qualification_sha256": qualification["qualification_sha256"], "reconciliation_sha256": reconciliation["reconciliation_sha256"], "targets": [{"relative_path": path, "sha256": expected[path]} for path in sorted(expected)], "recoverable": False}
    intent = {**body, "intent_sha256": protocol.digest_json(body)}
    _write_private(custody_root / "receipts" / "raw-deletion-intent-v4.json", intent)
    for relative in sorted(expected):
        (custody_root / relative).unlink()
    if any((custody_root / "raw").iterdir()):
        raise protocol.ProtocolError("V4 raw root is not empty after expiry")
    completed_body = {"protocol": protocol.PROTOCOL_ID, "state_slice": protocol.STATE_SLICE, "qualification_sha256": qualification["qualification_sha256"], "reconciliation_sha256": reconciliation["reconciliation_sha256"], "intent_sha256": intent["intent_sha256"], "deleted_file_count": len(expected), "raw_root_empty": True, "deleted_at": datetime.now(timezone.utc).isoformat(), "recoverable": False}
    completed = {**completed_body, "completion_sha256": protocol.digest_json(completed_body)}
    _write_private(custody_root / "receipts" / "raw-deletion-completion-v4.json", completed)
    return completed


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--custody-root", type=Path, default=protocol.CUSTODY_ROOT)
    parser.add_argument("--qualification", type=Path, required=True)
    parser.add_argument("--reconciliation", type=Path, required=True)
    args = parser.parse_args(argv)
    print(json.dumps(execute(args.repository_root.resolve(), args.custody_root.resolve(), args.qualification.resolve(), args.reconciliation.resolve()), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
