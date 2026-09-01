"""Independent validator for the full-campaign publication gate.

State slice: ``oaklab-experience-learning-benchmark-v2``.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from .publication_gate_v2 import STATE_SLICE, _digest


def validate(path: Path) -> dict:
    result = json.loads(path.read_text(encoding="utf-8"))
    if result.get("state_slice") != STATE_SLICE:
        raise ValueError("publication gate state mismatch")
    if result.get("result_digest") != _digest({key: value for key, value in result.items() if key != "result_digest"}):
        raise ValueError("publication gate digest mismatch")
    if result.get("status") not in {"candidate", "no_candidate"}:
        raise ValueError("publication gate status invalid")
    requirements = result.get("requirements")
    if not isinstance(requirements, dict) or not all(isinstance(value, bool) for value in requirements.values()):
        raise ValueError("publication gate requirements invalid")
    if result["status"] == "candidate" and not all(requirements.values()):
        raise ValueError("candidate gate has failed requirements")
    return {"status": "valid", "state_slice": STATE_SLICE, "result_digest": result["result_digest"],
            "decision": result["status"], "candidate_algorithms": result.get("candidate_algorithms", {})}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("receipt", type=Path)
    args = parser.parse_args()
    print(json.dumps(validate(args.receipt), sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
