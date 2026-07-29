from __future__ import annotations

import argparse
import json
from pathlib import Path

from v28r3 import validate_campaign


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a V28R3 integrated acquisition campaign")
    parser.add_argument("--campaign", type=Path, required=True)
    parser.add_argument("--predecessor-fingerprint", type=Path, required=True)
    parser.add_argument("--artifact-root", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    campaign = json.loads(args.campaign.read_text(encoding="utf-8"))
    fingerprint = json.loads(args.predecessor_fingerprint.read_text(encoding="utf-8"))
    result = validate_campaign(
        campaign, fingerprint=fingerprint, artifact_root=args.artifact_root
    )
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
