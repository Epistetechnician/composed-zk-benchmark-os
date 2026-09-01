#!/usr/bin/env python3
"""Validate one canonical scenario manifest against request and result."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from sidecar_v1 import deserialize_request, deserialize_result, deserialize_scenario_manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("request", type=Path)
    parser.add_argument("result", type=Path)
    parser.add_argument("manifest", type=Path)
    args = parser.parse_args()
    request = deserialize_request(args.request.read_bytes())
    result = deserialize_result(args.result.read_bytes(), request)
    manifest = deserialize_scenario_manifest(args.manifest.read_bytes(), result, request)
    print(json.dumps({"status": "valid", "manifest_digest": manifest["manifest_digest"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
