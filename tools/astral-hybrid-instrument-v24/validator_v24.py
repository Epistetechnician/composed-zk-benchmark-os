#!/usr/bin/env python3
"""Independent V24 artifact validator."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

STOP_CLASSIFICATIONS = {
    "NotRunHybridInstrumentQualification",
    "InstrumentBehaviorallySilent",
}


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def validate_lock(root: Path) -> dict:
    if (root / "assessment-results.json").exists():
        raise ValueError("assessment exists before lock validation")
    lock = json.loads((root / "configuration-lock.json").read_text())
    if not lock["assessment_results_absent"]:
        raise ValueError("lock ordering failure")
    for name, expected in lock["inputs"].items():
        if sha(root / name) != expected:
            raise ValueError(f"lock digest mismatch: {name}")
    return {"lock_valid": True, "configuration_lock_sha256": sha(root / "configuration-lock.json")}


def validate(root: Path) -> dict:
    manifest = json.loads((root / "manifest.json").read_text())
    actual = {str(path.relative_to(root)) for path in root.rglob("*") if path.is_file() and path.name != "manifest.json"}
    if actual != set(manifest["files"]):
        raise ValueError("manifest census mismatch")
    for name, expected in manifest["files"].items():
        if sha(root / name) != expected:
            raise ValueError(f"manifest digest mismatch: {name}")
    result = json.loads((root / "result.json").read_text())
    if result["classification"] in STOP_CLASSIFICATIONS:
        if not result["assessment_unopened"] or (root / "assessment-results.json").exists():
            raise ValueError("qualification stop opened assessment")
    if result["classification"] == "InstrumentBehaviorallySilent":
        behavioral = json.loads((root / "behavioral-effect.json").read_text())
        selected = result["selected_configuration"]
        cell = next(
            (entry for entry in behavioral
             if entry["site"] == selected["site"] and entry["strength"] == selected["strength"]),
            None,
        )
        if cell is None or not cell["silent"]:
            raise ValueError("silent stop without a silent selected cell")
        if cell != result["selected_behavioral_effect"]:
            raise ValueError("silent stop effect record mismatch")
    return {"valid": True, "classification": result["classification"], "manifest_sha256": sha(root / "manifest.json")}


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
