from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


ACQUISITION = tuple(range(4, 8))
PROTECTED = tuple(range(16, 32))
PRIOR_ACQUISITION = tuple(range(4))
PRIOR_PROTECTED = tuple(range(16))


def sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def validate(rgs_root: Path) -> dict[str, object]:
    required = {
        "runner": rgs_root / "scripts/run_v41r25_disjoint_replay.py",
        "method": rgs_root / "mesh_brain/meshmodel/v41r25_disjoint_replay_replication.py",
        "test": rgs_root / "tests/test_v41r25_disjoint_replay_replication.py",
        "preregistration": rgs_root / "docs/v41r25-disjoint-protected-replay-preregistration.md",
    }
    errors = [f"missing:{name}" for name, path in required.items() if not path.is_file()]
    if set(ACQUISITION) & set(PRIOR_ACQUISITION): errors.append("acquisition_overlap")
    if set(PROTECTED) & set(PRIOR_PROTECTED): errors.append("protected_overlap")
    if len(ACQUISITION) != 4 or len(PROTECTED) != 16: errors.append("census")
    return {
        "version": "astral.v41r25_disjoint_replay_local_validation.v1",
        "valid": not errors,
        "errors": sorted(errors),
        "acquisition_indices": list(ACQUISITION),
        "protected_indices": list(PROTECTED),
        "source_sha256": {name: sha256(path) for name, path in required.items() if path.is_file()},
        "runtime_authorized": False,
        "claim_ceiling": "LocalQualifiedDisjointReplayProtocolV41R25" if not errors else None,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rgs-root", type=Path, required=True)
    args = parser.parse_args()
    report = validate(args.rgs_root.resolve())
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
