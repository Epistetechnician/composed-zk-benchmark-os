#!/usr/bin/env python3
"""Independent V21 artifact validator."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def validate_lock(root: Path) -> dict:
    if (root / "assessment-effects.json").exists():
        raise ValueError("assessment effects exist before lock validation")
    lock = json.loads((root / "prediction-lock.json").read_text())
    if not lock["assessment_effects_absent"] or lock["assessment_family_count"] != 100:
        raise ValueError("lock ordering or census failure")
    for name, expected in {**lock["inputs"], **lock["adapters"]}.items():
        if sha(root / name) != expected:
            raise ValueError(f"lock digest mismatch: {name}")
    predictions = json.loads((root / "assessment-predictions.json").read_text())
    if set(predictions) != set(lock["prediction_methods"]):
        raise ValueError("prediction method mismatch")
    if any(len(rows) != 100 for rows in predictions.values()):
        raise ValueError("prediction census mismatch")
    return {"lock_valid": True, "prediction_lock_sha256": sha(root / "prediction-lock.json")}


def validate(root: Path) -> dict:
    manifest = json.loads((root / "manifest.json").read_text())
    actual = {str(path.relative_to(root)) for path in root.rglob("*") if path.is_file() and path.name != "manifest.json"}
    if actual != set(manifest["files"]):
        raise ValueError("manifest census mismatch")
    for name, expected in manifest["files"].items():
        if sha(root / name) != expected:
            raise ValueError(f"manifest digest mismatch: {name}")
    result = json.loads((root / "result.json").read_text())
    allowed = {"NaturalTextResidualReplicationCandidate", "NaturalTextResidualReplicationNoCandidate"}
    if result["classification"] not in allowed:
        raise ValueError("classification invalid")
    if len(json.loads((root / "assessment-effects.json").read_text())) != 100:
        raise ValueError("effect census mismatch")
    if result["classification"].endswith("Candidate") and not result["classification"].endswith("NoCandidate"):
        for name, advantage in result["primary_mse_advantages"].items():
            if advantage < 0.10 or result["paired_bootstrap_mse_differences"][name]["lower_95"] <= 0:
                raise ValueError(f"candidate gate violation: {name}")
    return {"valid": True, "classification": result["classification"], "manifest_sha256": sha(root / "manifest.json"), "prediction_lock_sha256": sha(root / "prediction-lock.json")}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("--lock-only", action="store_true")
    args = parser.parse_args()
    try:
        result = validate_lock(args.root.resolve()) if args.lock_only else validate(args.root.resolve())
        print(json.dumps(result, sort_keys=True))
    except Exception as exc:
        print(json.dumps({"valid": False, "reason": str(exc)}, sort_keys=True))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
