"""Independent validator for the strict publication gate receipt."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from .plasticity_guard_assessment_v1 import PLAN_DIGEST, STATE_SLICE


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--result", type=Path, required=True)
    args = parser.parse_args()
    result = json.loads(args.result.read_text(encoding="utf-8"))
    expected = result.get("result_digest")
    payload = {key: value for key, value in result.items() if key != "result_digest"}
    actual = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()
    if expected != actual:
        raise ValueError("publication gate digest mismatch")
    if result.get("state_slice") != STATE_SLICE or result.get("plan_digest") != PLAN_DIGEST:
        raise ValueError("publication gate state or plan mismatch")
    if result.get("status") not in {"candidate", "no_candidate"}:
        raise ValueError("publication gate status invalid")
    requirements = result.get("requirements", {})
    if result["status"] == "candidate" and not all(requirements.values()):
        raise ValueError("candidate publication gate has a failed requirement")
    print(json.dumps({"status": "valid", "publication_status": result["status"], "result_digest": expected}, sort_keys=True))


if __name__ == "__main__":
    main()
