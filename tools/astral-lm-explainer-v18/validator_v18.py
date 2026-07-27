#!/usr/bin/env python3
"""Independent V18 artifact validator."""

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
    if not lock["assessment_effects_absent"] or lock["assessment_family_count"] != 32:
        raise ValueError("prediction lock ordering assertion failure")
    for name, expected in lock["inputs"].items():
        if sha(root / name) != expected:
            raise ValueError(f"lock input mismatch: {name}")
    for name, expected in lock["adapters"].items():
        if sha(root / name) != expected:
            raise ValueError(f"lock adapter mismatch: {name}")
    if len(lock["prediction_methods"]) != 10:
        raise ValueError("prediction method census mismatch")
    predictions = json.loads((root / "assessment-predictions.json").read_text())
    if set(predictions) != set(lock["prediction_methods"]):
        raise ValueError("prediction method lock mismatch")
    for method, rows in predictions.items():
        if len(rows) != 32 or len({x["family_id"] for x in rows}) != 32:
            raise ValueError(f"prediction row census mismatch: {method}")
    return {"lock_valid": True, "prediction_lock_sha256": sha(root / "prediction-lock.json")}


def validate(root: Path) -> dict:
    manifest = json.loads((root / "manifest.json").read_text())
    actual = {str(x.relative_to(root)) for x in root.rglob("*") if x.is_file() and x.name != "manifest.json"}
    if actual != set(manifest["files"]):
        raise ValueError("manifest file census mismatch")
    for name, expected in manifest["files"].items():
        if sha(root / name) != expected:
            raise ValueError(f"digest mismatch: {name}")
    corpus = json.loads((root / "corpus.json").read_text())
    if len(corpus) != 256 or len({x["family_id"] for x in corpus}) != 256:
        raise ValueError("corpus census mismatch")
    effects = json.loads((root / "assessment-effects.json").read_text())
    if len(effects) != 32:
        raise ValueError("assessment census mismatch")
    lock = json.loads((root / "prediction-lock.json").read_text())
    if not lock["assessment_effects_absent"] or lock["assessment_family_count"] != 32:
        raise ValueError("prediction lock ordering assertion failure")
    result = json.loads((root / "result.json").read_text())
    if result["classification"] not in {"TrainedSameModelDevelopmentCandidate", "TrainedLmDevelopmentNoCandidate"}:
        raise ValueError("classification invalid")
    if result["claim_ceiling"] != "LocalDevelopmentTrainedLmInputAblationExplainerPilot":
        raise ValueError("claim ceiling invalid")
    if result["classification"] == "TrainedSameModelDevelopmentCandidate":
        for name in ("llama-ensemble", "qwen-untrained", "majority", "hint-disagreement"):
            if (
                result["primary_comparison_advantages"][name] < 0.05
                or result["paired_bootstrap_balanced_accuracy_advantages"][name]["lower_95"] <= 0
            ):
                raise ValueError(f"positive classification violates gate: {name}")
        if min(
            result["metrics"][f"qwen-{seed}"]["balanced_accuracy"]
            for seed in (1801, 1811, 1823)
        ) < 0.60:
            raise ValueError("positive classification violates seed floor")
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
