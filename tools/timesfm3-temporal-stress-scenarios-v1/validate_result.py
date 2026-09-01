#!/usr/bin/env python3
"""Validate one canonical result against its request."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from sidecar_v1 import deserialize_request, deserialize_result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("request", type=Path)
    parser.add_argument("result", type=Path)
    args = parser.parse_args()
    request = deserialize_request(args.request.read_bytes())
    result = deserialize_result(args.result.read_bytes(), request)
    print(json.dumps({"status": result["status"], "request_id": result["request_id"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
