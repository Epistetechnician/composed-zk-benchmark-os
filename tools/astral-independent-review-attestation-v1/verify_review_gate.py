#!/usr/bin/env python3
"""Verify two role-bound signed Astral review decisions and emit a sealed report."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from review_gate import sha256_file, verify_gate, write_canonical


HERE = Path(__file__).resolve()
SPEC_PATH = HERE.with_name("gate-spec.json")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry", required=True, type=Path)
    parser.add_argument("--expected-registry-sha256", required=True)
    parser.add_argument("--requests", required=True, type=Path)
    parser.add_argument("--decisions", required=True, type=Path)
    parser.add_argument("--evidence-root", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    args = parser.parse_args()
    sidecar = args.report.with_suffix(args.report.suffix + ".sha256")
    if args.report.exists() or sidecar.exists():
        raise SystemExit("gate report destination already exists")
    spec = json.loads(SPEC_PATH.read_text())
    report = verify_gate(
        spec,
        args.registry,
        args.expected_registry_sha256,
        args.requests,
        args.decisions,
        args.evidence_root,
    )
    write_canonical(args.report, report)
    digest = sha256_file(args.report)
    sidecar.write_text(f"{digest}  {args.report.name}\n")
    print(
        json.dumps(
            {"report": str(args.report), "report_sha256": digest, "status": report["status"]},
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
