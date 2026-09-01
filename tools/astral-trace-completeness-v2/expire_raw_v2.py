"""Expire validated V2 raw traces and emit intent/completion receipts.

State slice: astral-trace-completeness-gemma3-end-to-end-v2.
"""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import custody_v2 as custody
import protocol_v2 as protocol


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
    receipt = custody.validate_root(custody_root, repository_root)
    if not receipt["valid"]:
        raise protocol.ProtocolError("custody validation failed before expiry")
    qualification = protocol.strict_json(qualification_path)
    reconciliation = protocol.strict_json(reconciliation_path)
    if qualification.get("status") != "QUALIFICATION_FAILED" or qualification.get("assessment_opened") is not False:
        raise protocol.ProtocolError("raw expiry requires sealed failed qualification")
    if reconciliation.get("valid") is not True or reconciliation.get("qualification_sha256") != qualification.get("qualification_sha256"):
        raise protocol.ProtocolError("valid reconciliation R2 is required before expiry")
    expected: dict[str, str] = {}
    for run_id in qualification["run_aggregate_sha256"]:
        manifest = protocol.strict_json(custody_root / "aggregate" / f"{run_id}.event-manifest.json")
        expected[manifest["raw_relative_path"]] = manifest["raw_sha256"]
    for path in sorted((custody_root / "aggregate").glob("*.capture-manifest.json")):
        manifest = protocol.strict_json(path)
        expected[manifest["relative_path"]] = manifest["sha256"]
    observed = {
        path.relative_to(custody_root).as_posix()
        for path in (custody_root / "raw").iterdir()
        if path.is_file()
    }
    if observed != set(expected):
        raise protocol.ProtocolError("raw root contains missing or unknown files")
    for relative, digest in expected.items():
        path = (custody_root / relative).resolve()
        path.relative_to((custody_root / "raw").resolve())
        if path.is_symlink() or protocol.sha256_file(path) != digest:
            raise protocol.ProtocolError(f"raw expiry target failed validation: {relative}")
    intent_body = {
        "protocol": protocol.PROTOCOL_ID,
        "state_slice": protocol.STATE_SLICE,
        "qualification_sha256": qualification["qualification_sha256"],
        "reconciliation_sha256": reconciliation["reconciliation_sha256"],
        "targets": [{"relative_path": path, "sha256": expected[path]} for path in sorted(expected)],
        "recoverable": False,
    }
    intent = {**intent_body, "intent_sha256": protocol.digest_json(intent_body)}
    _write_private(custody_root / "receipts" / "raw-deletion-intent.json", intent)
    for relative in sorted(expected):
        (custody_root / relative).unlink()
    remaining = list((custody_root / "raw").iterdir())
    if remaining:
        raise protocol.ProtocolError("raw root is not empty after targeted expiry")
    completion_body = {
        "protocol": protocol.PROTOCOL_ID,
        "state_slice": protocol.STATE_SLICE,
        "qualification_sha256": qualification["qualification_sha256"],
        "reconciliation_sha256": reconciliation["reconciliation_sha256"],
        "intent_sha256": intent["intent_sha256"],
        "deleted_file_count": len(expected),
        "raw_root_empty": True,
        "deleted_at": datetime.now(timezone.utc).isoformat(),
        "recoverable": False,
    }
    completion = {**completion_body, "completion_sha256": protocol.digest_json(completion_body)}
    _write_private(custody_root / "receipts" / "raw-deletion-completion.json", completion)
    return completion


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--custody-root", type=Path, default=protocol.CUSTODY_ROOT)
    parser.add_argument(
        "--qualification",
        type=Path,
        default=protocol.CUSTODY_ROOT / "aggregate" / "qualification-29c2eb957a79419995992533d3b843a7.json",
    )
    parser.add_argument(
        "--reconciliation",
        type=Path,
        default=protocol.CUSTODY_ROOT / "aggregate" / "reconciliation-r2-29c2eb957a79419995992533d3b843a7.json",
    )
    args = parser.parse_args(argv)
    result = execute(
        args.repository_root.resolve(),
        args.custody_root.resolve(),
        args.qualification.resolve(),
        args.reconciliation.resolve(),
    )
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

