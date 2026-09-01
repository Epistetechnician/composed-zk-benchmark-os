"""CLI for the fresh real-panel sensitivity protocol.

State slice: ``oaklab-experience-learning-real-sensitivity-v1``.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .real_sensitivity_v1 import run_campaign, review_protocol, write_protocol


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--artifact-root", type=Path, required=True)
    parser.add_argument("--prepare", action="store_true")
    parser.add_argument("--review", action="store_true")
    parser.add_argument("--run", action="store_true", dest="execute")
    args = parser.parse_args()
    protocol_path = args.artifact_root / "protocol_manifest.json"
    review_path = args.artifact_root / "review_receipt.json"
    result_path = args.artifact_root / "real_sensitivity_v1.json"
    if args.prepare:
        protocol = write_protocol(args.source_root, args.artifact_root)
        print(protocol["protocol_digest"])
        return
    if args.review:
        receipt = review_protocol(protocol_path)
        review_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(receipt["review_digest"])
        return
    if args.execute:
        result = run_campaign(protocol_path, review_path, result_path)
        print(result["result_digest"])
        return
    parser.error("one of --prepare, --review, or --run is required")


if __name__ == "__main__":
    main()
