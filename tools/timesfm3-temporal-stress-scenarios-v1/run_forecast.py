#!/usr/bin/env python3
"""Run the bounded sidecar fixture; real TimesFM3 loading is a later gate."""

from __future__ import annotations

import argparse
from pathlib import Path

from sidecar_v1 import (
    ValidationError,
    deserialize_request,
    run_fake_model,
    serialize_result,
)


def run_request(request_path: Path, output_path: Path, *, fake_model: bool) -> None:
    """Validate one request and write a canonical result."""

    if not fake_model:
        raise ValidationError(
            "real TimesFM3 execution is withheld until independent contract review and qualification"
        )
    request = deserialize_request(request_path.read_bytes())
    result = run_fake_model(request)
    output_path.write_bytes(serialize_result(result, request))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("request", type=Path)
    parser.add_argument("result", type=Path)
    parser.add_argument(
        "--fake-model",
        action="store_true",
        help="use the deterministic hermetic fixture model",
    )
    args = parser.parse_args()
    run_request(args.request, args.result, fake_model=args.fake_model)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
