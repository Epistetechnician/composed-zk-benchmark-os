"""Independent validator for a digest-bound backend parity receipt.

State slice: ``oaklab-experience-learning-benchmark-v2``.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .acquire_real_data_v1 import validate_manifest
from .backends import validate_backend_result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--result", type=Path, required=True)
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    result = json.loads(args.result.read_text(encoding="utf-8"))
    parity = validate_backend_result(result)
    custody = result.get("custody", {})
    manifest = validate_manifest(args.root)
    if custody.get("manifest_sha256") != manifest["manifest_sha256"]:
        raise ValueError("backend receipt is not bound to validated custody manifest")
    manifest_payload = json.loads((args.root / "manifest.json").read_text(encoding="utf-8"))
    record = next((item for item in manifest_payload["datasets"] if item["name"] == custody.get("dataset")), None)
    if record is None or custody.get("derived_sha256") != record["derived_sha256"]:
        raise ValueError("backend receipt derived digest mismatch")
    if custody.get("rows") != record["rows"] or result.get("steps") != record["rows"]:
        raise ValueError("backend receipt row count mismatch")
    print(json.dumps({"status": "valid", "parity": parity, "custody": custody}, sort_keys=True))


if __name__ == "__main__":
    main()
