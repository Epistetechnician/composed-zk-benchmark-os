#!/usr/bin/env python3
"""Independent V19 validator."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            h.update(chunk)
    return h.hexdigest()


def validate_lock(root: Path) -> dict:
    if (root / "assessment-effects.json").exists():
        raise ValueError("assessment effects exist before lock validation")
    lock = json.loads((root / "prediction-lock.json").read_text())
    if not lock["assessment_effects_absent"]:
        raise ValueError("lock did not attest effect absence")
    if lock["assessment_family_count"] != 40:
        raise ValueError("assessment census mismatch")
    for name, expected in {**lock["inputs"], **lock["adapters"]}.items():
        if sha(root / name) != expected:
            raise ValueError(f"lock digest mismatch: {name}")
    predictions = json.loads((root / "assessment-predictions.json").read_text())
    if set(predictions) != set(lock["prediction_methods"]):
        raise ValueError("prediction method mismatch")
    for method, rows in predictions.items():
        if len(rows) != 40 or len({x["family_id"] for x in rows}) != 40:
            raise ValueError(f"prediction census mismatch: {method}")
    return {
        "lock_valid": True,
        "prediction_lock_sha256": sha(root / "prediction-lock.json"),
    }


def validate(root: Path) -> dict:
    manifest = json.loads((root / "manifest.json").read_text())
    actual = {
        str(x.relative_to(root))
        for x in root.rglob("*")
        if x.is_file() and x.name != "manifest.json"
    }
    if actual != set(manifest["files"]):
        raise ValueError("manifest census mismatch")
    for name, expected in manifest["files"].items():
        if sha(root / name) != expected:
            raise ValueError(f"manifest digest mismatch: {name}")
    result = json.loads((root / "result.json").read_text())
    corpus = json.loads((root / "corpus.json").read_text())
    if len(corpus) != 320:
        raise ValueError("corpus census mismatch")
    allowed = {
        "OpaquePreferenceReplicationCandidate",
        "OpaquePreferenceReplicationNoCandidate",
        "NotRunTargetLabelImbalance",
    }
    if result["classification"] not in allowed:
        raise ValueError("classification invalid")
    if result["classification"] == "NotRunTargetLabelImbalance":
        if (
            (root / "assessment-effects.json").exists()
            or (root / "prediction-lock.json").exists()
            or (root / "adapters").exists()
            or result["assessment_unhinted_outputs_generated"]
            or result["adapters_trained"]
            or result["qualification"]["splits"]["fit"]["minority_fraction"] >= 0.20
        ):
            raise ValueError("blocked-run boundary violation")
    else:
        effects = json.loads((root / "assessment-effects.json").read_text())
        if len(effects) != 40:
            raise ValueError("assessment census mismatch")
    if result["classification"] == "OpaquePreferenceReplicationCandidate":
        for name, advantage in result["primary_comparison_advantages"].items():
            if (
                advantage < 0.05
                or result["paired_bootstrap_balanced_accuracy_advantages"][name][
                    "lower_95"
                ]
                <= 0
            ):
                raise ValueError(f"candidate gate violation: {name}")
    output = {
        "valid": True,
        "classification": result["classification"],
        "manifest_sha256": sha(root / "manifest.json"),
    }
    if (root / "prediction-lock.json").exists():
        output["prediction_lock_sha256"] = sha(root / "prediction-lock.json")
    return output


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("--lock-only", action="store_true")
    args = parser.parse_args()
    try:
        result = (
            validate_lock(args.root.resolve())
            if args.lock_only
            else validate(args.root.resolve())
        )
        print(json.dumps(result, sort_keys=True))
    except Exception as exc:
        print(json.dumps({"valid": False, "reason": str(exc)}, sort_keys=True))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
