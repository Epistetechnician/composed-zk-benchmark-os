"""Discard raw traces from an unpublished failed V3 attempt.

State slice: astral-trace-completeness-gemma3-end-to-end-v3.
The target prefix is fixed and cannot select arbitrary custody files.
"""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import protocol_v3 as protocol


PREFIX = "v3-hypothesis-1-affine-pooled-20260830-run-"


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


def execute(repository_root: Path, custody_root: Path) -> dict[str, Any]:
    receipt = protocol.custody_receipt(custody_root, repository_root)
    if not receipt["valid"]:
        raise protocol.ProtocolError("V3 custody validation failed before failed-attempt discard")
    raw_root = custody_root / "raw"
    files = sorted(path for path in raw_root.iterdir() if path.is_file())
    if not files or any(not path.name.startswith(PREFIX) for path in files):
        raise protocol.ProtocolError("raw root does not contain exactly the fixed failed-attempt prefix")
    targets = [{"relative_path": path.relative_to(custody_root).as_posix(), "sha256": protocol.sha256_file(path)} for path in files]
    body = {
        "protocol": protocol.PROTOCOL_ID,
        "state_slice": protocol.STATE_SLICE,
        "attempt": "v3-hypothesis-1-affine-pooled-20260830",
        "reason": "qualification_aggregate_not_published_after_feature_stability_type_error",
        "targets": targets,
        "deleted_at": datetime.now(timezone.utc).isoformat(),
        "recoverable": False,
    }
    completion = {**body, "completion_sha256": protocol.digest_json(body)}
    _write_private(custody_root / "receipts" / "failed-attempt-discard-v3.json", completion)
    for path in files:
        path.unlink()
    if any(raw_root.iterdir()):
        raise protocol.ProtocolError("V3 raw root is not empty after failed-attempt discard")
    return completion


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--custody-root", type=Path, default=protocol.CUSTODY_ROOT)
    args = parser.parse_args(argv)
    print(json.dumps(execute(args.repository_root.resolve(), args.custody_root.resolve()), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
