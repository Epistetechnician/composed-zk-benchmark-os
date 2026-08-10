"""Fail-closed validator for completed V13 bundles."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

from learned_stage0_v13 import (
    ASSESSMENT_FAMILIES, ASSESSMENT_SEEDS, ESTIMATORS, FIT_FAMILIES, FIT_SEEDS,
    OPERATORS, SITES, STATE_SLICE, metric_summary,
)
from run_learned_stage0_v13 import classify, identity


def load(path: Path):
    raw = path.read_bytes()
    value = json.loads(raw)
    if raw != (json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode():
        raise ValueError("noncanonical JSON")
    return value


def jsonl(path: Path):
    return [json.loads(line) for line in path.read_bytes().splitlines()]


def validate(root: Path, protocol: Path):
    root = root.resolve()
    manifest = load(root / "manifest.json")
    if manifest.get("state_slice") != STATE_SLICE:
        raise ValueError("manifest state slice drift")
    expected = {row["path"]: row for row in manifest["files"]}
    actual = {path.name for path in root.iterdir() if path.name != "manifest.json"}
    if set(expected) != actual:
        raise ValueError("manifest census mismatch")
    for name, row in expected.items():
        raw = (root / name).read_bytes()
        if row != {"bytes": len(raw), "path": name, "sha256": hashlib.sha256(raw).hexdigest()}:
            raise ValueError("manifest digest mismatch")
    if load(root / "protocol.lock.json") != {
        "protocol_sha256": hashlib.sha256(protocol.read_bytes()).hexdigest(), "state_slice": STATE_SLICE,
    }:
        raise ValueError("protocol binding mismatch")
    summary = load(root / "summary.json")
    if summary.get("state_slice") != STATE_SLICE or any(
        summary.get(key) for key in ("accepted_evidence", "stage0_pass", "confirmation_authorized")
    ):
        raise ValueError("claim boundary drift")
    if summary["classification"] == "DevelopmentQualificationFailed":
        forbidden = ("fitting-records.jsonl", "assessment-telemetry.jsonl", "predictions.jsonl", "prediction-lock.json", "assessment-effects.jsonl")
        if any((root / name).exists() for name in forbidden):
            raise ValueError("measurement exists after qualification failure")
        return summary

    fit, telemetry = jsonl(root / "fitting-records.jsonl"), jsonl(root / "assessment-telemetry.jsonl")
    predictions, effects = jsonl(root / "predictions.jsonl"), jsonl(root / "assessment-effects.jsonl")
    counts = {
        "fitting_record_census": len(FIT_SEEDS) * len(FIT_FAMILIES) * 16 * len(SITES) * len(OPERATORS),
        "assessment_telemetry_census": len(ASSESSMENT_SEEDS) * len(ASSESSMENT_FAMILIES) * 16 * len(SITES) * len(OPERATORS),
    }
    counts["assessment_effect_census"] = counts["assessment_telemetry_census"]
    counts["prediction_census"] = counts["assessment_telemetry_census"] * len(ESTIMATORS)
    for key, value in counts.items():
        if summary[key] != value:
            raise ValueError(f"{key} mismatch")
    if (len(fit), len(telemetry), len(effects), len(predictions)) != (
        counts["fitting_record_census"], counts["assessment_telemetry_census"],
        counts["assessment_effect_census"], counts["prediction_census"],
    ):
        raise ValueError("artifact census mismatch")

    def check_rows(rows, seeds, families, effect_required=False):
        seen = set()
        for row in rows:
            key = identity(row)
            if key in seen:
                raise ValueError("duplicate row")
            seen.add(key)
            if row["seed"] not in seeds or row["family"] not in families or row["site"] not in SITES or row["operator"] not in OPERATORS:
                raise ValueError("row boundary breach")
            if effect_required and not math.isfinite(float(row["effect"])):
                raise ValueError("nonfinite effect")

    check_rows(fit, FIT_SEEDS, FIT_FAMILIES, True)
    check_rows(telemetry, ASSESSMENT_SEEDS, ASSESSMENT_FAMILIES)
    check_rows(effects, ASSESSMENT_SEEDS, ASSESSMENT_FAMILIES, True)
    lock = load(root / "prediction-lock.json")
    hashes = {
        "assessment_telemetry_sha256": hashlib.sha256((root / "assessment-telemetry.jsonl").read_bytes()).hexdigest(),
        "fitting_records_sha256": hashlib.sha256((root / "fitting-records.jsonl").read_bytes()).hexdigest(),
        "predictions_sha256": hashlib.sha256((root / "predictions.jsonl").read_bytes()).hexdigest(),
    }
    if any(lock.get(key) != value for key, value in hashes.items()) or lock.get("state_slice") != STATE_SLICE:
        raise ValueError("prediction lock mismatch")
    lock_hash = hashlib.sha256((root / "prediction-lock.json").read_bytes()).hexdigest()
    if summary["prediction_lock_sha256"] != lock_hash or any(row.get("prediction_lock_sha256") != lock_hash for row in effects):
        raise ValueError("assessment effect predates prediction lock")

    effect_map = {identity(row): float(row["effect"]) for row in effects}
    joined = []
    prediction_seen = set()
    for row in predictions:
        key = (row["estimator"], *identity(row))
        if key in prediction_seen or row["estimator"] not in ESTIMATORS or not math.isfinite(float(row["predicted"])):
            raise ValueError("prediction boundary breach")
        prediction_seen.add(key)
        joined.append({**row, "actual": effect_map[identity(row)]})
    recomputed = {}
    for estimator in ESTIMATORS:
        rows = [row for row in joined if row["estimator"] == estimator]
        recomputed[estimator] = {"pooled": metric_summary([row["actual"] for row in rows], [row["predicted"] for row in rows])}
        for seed in ASSESSMENT_SEEDS:
            for operator in OPERATORS:
                subset = [row for row in rows if row["seed"] == seed and row["operator"] == operator]
                recomputed[estimator][f"seed={seed};operator={operator}"] = metric_summary(
                    [row["actual"] for row in subset], [row["predicted"] for row in subset]
                )
    if recomputed != summary["metrics"] or classify(recomputed) != summary["classification"]:
        raise ValueError("summary metric drift")
    return summary


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--protocol", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(validate(args.root, args.protocol), indent=2, sort_keys=True))
