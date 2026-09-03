"""Compile the frozen small-RSI substitution manifest.

State slice: ``recursive-meta-harness-small-rsi-frontier-substitution-v1``.
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
)


SOURCE_FILES = (
    "tools/recursive_meta_harness_small_rsi_frontier_substitution_v1/protocol_v1.py",
    "tools/recursive_meta_harness_small_rsi_frontier_substitution_v1/compiler_v1.py",
    "tools/recursive_meta_harness_small_rsi_frontier_substitution_v1/runner_v1.py",
    "tools/recursive_meta_harness_small_rsi_frontier_substitution_v1/review_v1.py",
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
    """Return the canonical manifest with a digest over all frozen fields."""

    protocol = protocol_spec()
    body = {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "state_slice": STATE_SLICE,
        "protocol_id": PROTOCOL_ID,
        "claim_ceiling": CLAIM_CEILING,
        "execution_authorized": False,
        "assessment_open": False,
        "protocol_sha256": digest(protocol),
        "source_identity": _source_identity(),
        "protocol": protocol,
    }
    return {**body, "manifest_sha256": digest(body)}


def write_manifest(manifest: dict[str, Any], output: Path) -> None:
    """Write a manifest once without overwriting an existing artifact."""

    if output.exists():
        raise FileExistsError(f"refusing to overwrite existing manifest: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(json.dumps(manifest, ensure_ascii=True, sort_keys=True, indent=2).encode("utf-8") + b"\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="write the frozen small-RSI substitution manifest")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    write_manifest(compile_manifest(), args.output)
    print(json.dumps({"state_slice": STATE_SLICE, "manifest": str(args.output)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
