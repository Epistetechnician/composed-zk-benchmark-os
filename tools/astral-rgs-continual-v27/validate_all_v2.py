#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import v27


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Astral V1-V27 state without promoting open scientific gates.")
    parser.add_argument("--historical-report", type=Path, required=True)
    parser.add_argument("--tencent-packet", type=Path)
    parser.add_argument("--tencent-subset-manifest", type=Path)
    parser.add_argument("--rgs-report", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists() or args.output.with_suffix(args.output.suffix + ".sha256").exists():
        raise ValueError("output and sidecar must not already exist")
    historical = v27.load_object(args.historical_report)
    if (args.tencent_packet is None) != (args.tencent_subset_manifest is None):
        raise ValueError("Tencent packet and subset manifest must be supplied together")
    tencent = v27.load_object(args.tencent_packet) if args.tencent_packet else None
    subset_manifest = (
        v27.load_object(args.tencent_subset_manifest)
        if args.tencent_subset_manifest
        else None
    )
    rgs = v27.load_object(args.rgs_report) if args.rgs_report else None
    report = v27.build_validation(
        historical_report=historical,
        tencent_packet=tencent,
        tencent_subset_manifest=subset_manifest,
        rgs_report=rgs,
        historical_report_sha256=v27.sha256(args.historical_report),
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.output.with_suffix(args.output.suffix + ".sha256").write_text(v27.sha256(args.output) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] != "Invalid" else 1


if __name__ == "__main__":
    raise SystemExit(main())
