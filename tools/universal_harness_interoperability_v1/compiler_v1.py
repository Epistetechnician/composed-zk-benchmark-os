"""Compile the universal harness interoperability manifest.

State slice: ``universal-harness-interoperability-v1``.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from .protocol_v1 import (
    CLAIM_CEILING,
    MANIFEST_SCHEMA_VERSION,
    PROTOCOL_ID,
    STATE_SLICE,
    digest,
    protocol_spec,
    validate_manifest_shape,
)


SOURCE_FILES = (
    "tools/universal_harness_interoperability_v1/__init__.py",
    "tools/universal_harness_interoperability_v1/protocol_v1.py",
    "tools/universal_harness_interoperability_v1/compiler_v1.py",
    "tools/universal_harness_interoperability_v1/validator_v1.py",
)


def _source_identity() -> list[dict[str, str]]:
    root = Path(__file__).resolve().parents[2]
    return [
        {
            "path": relative,
            "sha256": hashlib.sha256((root / Path(relative)).read_bytes()).hexdigest(),
        }
        for relative in SOURCE_FILES
    ]


def compile_manifest() -> dict[str, Any]:
    """Return a canonical non-authorizing interoperability manifest."""

    protocol = protocol_spec()
    body = {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "state_slice": STATE_SLICE,
        "protocol_id": PROTOCOL_ID,
        "claim_ceiling": CLAIM_CEILING,
        "execution_authorized": False,
        "assessment_open": False,
        "source_identity": _source_identity(),
        "protocol_sha256": digest(protocol),
        "protocol": protocol,
    }
    manifest = {**body, "manifest_sha256": digest(body)}
    validate_manifest_shape(manifest)
    return manifest


def write_manifest(manifest: dict[str, Any], output: Path) -> None:
    """Write one manifest and reject replacement of an existing artifact."""

    validate_manifest_shape(manifest)
    if output.exists():
        raise FileExistsError(f"refusing to overwrite existing manifest: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(json.dumps(manifest, ensure_ascii=True, sort_keys=True, indent=2).encode("utf-8") + b"\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="write the universal harness interoperability manifest")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    manifest = compile_manifest()
    write_manifest(manifest, args.output)
    print(json.dumps({"state_slice": STATE_SLICE, "manifest": str(args.output)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
