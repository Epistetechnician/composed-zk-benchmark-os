#!/usr/bin/env python3
"""Build a canonical q10/q50/q90 scenario manifest from a validated result."""

from __future__ import annotations

import argparse
from pathlib import Path

from sidecar_v1 import (
    ValidationError,
    build_scenario_manifest,
    deserialize_request,
    deserialize_result,
    parse_json,
    serialize_scenario_manifest,
)


def load_canonical_config(path: Path) -> dict:
    """Load a canonical scenario configuration object."""

    raw = path.read_bytes()
    config = parse_json(raw)
    if not isinstance(config, dict):
        raise ValidationError("scenario config must be an object")
    from sidecar_v1 import canonical_bytes

    if canonical_bytes(config) != raw:
        raise ValidationError("scenario config bytes are not canonical JSON")
    return config


def build(request_path: Path, result_path: Path, config_path: Path, output_path: Path) -> None:
    """Build and write one canonical scenario manifest."""

    request = deserialize_request(request_path.read_bytes())
    result = deserialize_result(result_path.read_bytes(), request)
    config = load_canonical_config(config_path)
    manifest = build_scenario_manifest(result, request, config)
    output_path.write_bytes(serialize_scenario_manifest(manifest, result, request))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("request", type=Path)
    parser.add_argument("result", type=Path)
    parser.add_argument("config", type=Path)
    parser.add_argument("manifest", type=Path)
    args = parser.parse_args()
    build(args.request, args.result, args.config, args.manifest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
