#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from release_v2 import build_release


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build the immutable Astral-RGS V27-R1 clean-room release."
    )
    parser.add_argument("--astral-repository", type=Path, required=True)
    parser.add_argument("--rgs-repository", type=Path, required=True)
    parser.add_argument("--historical-report", type=Path, required=True)
    parser.add_argument("--tencent-packet", type=Path, required=True)
    parser.add_argument("--tencent-subset-manifest", type=Path, required=True)
    parser.add_argument("--tencent-source-license", type=Path)
    parser.add_argument("--tencent-dataset-license", type=Path)
    parser.add_argument("--rgs-input", type=Path)
    parser.add_argument("--rgs-report", type=Path)
    parser.add_argument("--output-parent", type=Path, required=True)
    args = parser.parse_args()
    release = build_release(
        astral_repository=args.astral_repository,
        rgs_repository=args.rgs_repository,
        historical_report=args.historical_report,
        tencent_packet_path=args.tencent_packet,
        tencent_subset_manifest=args.tencent_subset_manifest,
        tencent_source_license=args.tencent_source_license,
        tencent_dataset_license=args.tencent_dataset_license,
        output_parent=args.output_parent,
        rgs_input=args.rgs_input,
        rgs_report=args.rgs_report,
    )
    print(
        json.dumps(
            {
                "state_slice": "astral-rgs-v27-model-backed-qualification-r1",
                "status": "immutable_release_built",
                "release": str(release),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
