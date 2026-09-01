#!/usr/bin/env python3
"""Validate one canonical TimesFM3 sidecar request."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from sidecar_v1 import deserialize_request, digest_json


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("request", type=Path)
    args = parser.parse_args()
    request = deserialize_request(args.request.read_bytes())
    print(json.dumps({"status": "valid", "request_digest": digest_json(request)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
