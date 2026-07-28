#!/usr/bin/env python3
"""Independent structural validator for a completed V17 bundle."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            h.update(chunk)
    return h.hexdigest()


def validate(root: Path) -> dict:
    required = {
        "prompt-families.json",
        "model-inventory.json",
        "qualification.json",
        "fit-state.npz",
        "training-record.json",
        "explainer-checkpoints.pt",
        "assessment-telemetry.npz",
        "assessment-predictions.jsonl",
        "prediction-lock.json",
        "assessment-effects.npz",
        "result.json",
        "manifest.json",
    }
    present = {p.name for p in root.iterdir() if p.is_file()}
    if present != required:
        raise ValueError(f"file census mismatch: {sorted(present ^ required)}")
    manifest = json.loads((root / "manifest.json").read_text())
    for name, expected in manifest["files"].items():
        if sha(root / name) != expected:
            raise ValueError(f"manifest mismatch: {name}")
    lock = json.loads((root / "prediction-lock.json").read_text())
    if not lock["assessment_effects_absent"]:
        raise ValueError("prediction lock did not attest effect absence")
    if lock["prediction_count"] != 64 * 6 * 6:
        raise ValueError("prediction census mismatch")
    effects = np.load(root / "assessment-effects.npz")["effects"]
    if effects.shape != (64, 6) or not np.isfinite(effects).all():
        raise ValueError("effect shape or finiteness failure")
    lines = (root / "assessment-predictions.jsonl").read_text().splitlines()
    if len(lines) != 64:
        raise ValueError("prediction row census mismatch")
    ids = set()
    for line in lines:
        row = json.loads(line)
        ids.add(row["example_id"])
        if set(row["predictions"]) != {
            "activation",
            "constant",
            "linear_telemetry",
            "shuffled",
            "telemetry",
            "text_io",
        }:
            raise ValueError("prediction method census mismatch")
        for values in row["predictions"].values():
            if len(values) != 6 or not np.isfinite(values).all():
                raise ValueError("prediction shape or finiteness failure")
    if len(ids) != 64:
        raise ValueError("duplicate prediction ids")
    result = json.loads((root / "result.json").read_text())
    allowed = {
        "SingleModelTelemetryFeasibilityObserved",
        "SingleModelFeasibilityNoCandidate",
    }
    if result["classification"] not in allowed:
        raise ValueError("invalid classification")
    predictions = [json.loads(line)["predictions"] for line in lines]
    for method, recorded in result["metrics"].items():
        pred = np.asarray([row[method] for row in predictions])
        recomputed = {
            "mean": float(np.mean((pred[:, :3] - effects[:, :3]) ** 2)),
            "patch": float(np.mean((pred[:, 3:] - effects[:, 3:]) ** 2)),
        }
        for operator in ("mean", "patch"):
            if abs(recomputed[operator] - recorded[operator]) > 1e-6:
                raise ValueError(f"metric mismatch: {method}/{operator}")
    if result["classification"] == "SingleModelTelemetryFeasibilityObserved":
        for operator in ("mean", "patch"):
            diag = result["telemetry_diagnostics"][operator]
            if (
                result["telemetry_activation_advantage"][operator] < 0.10
                or diag["paired_family_bootstrap_difference_lower_95"] <= 0
                or diag["pearson"] <= 0
                or not 0.5 <= diag["calibration_slope"] <= 1.5
                or not all(x > 0 for x in diag["per_site_activation_advantage"])
            ):
                raise ValueError("positive classification violates gate")
    return {
        "valid": True,
        "classification": result["classification"],
        "manifest_sha256": sha(root / "manifest.json"),
        "prediction_lock_sha256": sha(root / "prediction-lock.json"),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    args = parser.parse_args()
    try:
        print(json.dumps(validate(args.root.resolve()), sort_keys=True))
    except Exception as exc:
        print(json.dumps({"valid": False, "reason": str(exc)}, sort_keys=True))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
