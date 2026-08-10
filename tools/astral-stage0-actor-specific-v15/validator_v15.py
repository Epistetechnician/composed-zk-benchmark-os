"""Fail-closed V15 bundle validator."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

from actor_specific_v15 import (
    ACTOR_SEEDS, ASSESSMENT_FAMILIES, FIT_FAMILIES, METHODS, OPERATORS, SITES,
    STATE_SLICE, metric_summary,
)
from run_actor_specific_v15 import canonical, classify, identity


def load(path):
    raw = path.read_bytes()
    value = json.loads(raw)
    if raw != canonical(value):
        raise ValueError("noncanonical JSON")
    return value


def rows(path):
    return [json.loads(line) for line in path.read_bytes().splitlines()]


def validate(root: Path, protocol: Path):
    manifest = load(root / "manifest.json")
    if manifest.get("state_slice") != STATE_SLICE:
        raise ValueError("manifest drift")
    expected = {row["path"]: row for row in manifest["files"]}
    actual = {path.name for path in root.iterdir() if path.name != "manifest.json"}
    if set(expected) != actual:
        raise ValueError("manifest census drift")
    for name, row in expected.items():
        raw = (root / name).read_bytes()
        if row != {"bytes": len(raw), "path": name, "sha256": hashlib.sha256(raw).hexdigest()}:
            raise ValueError("manifest digest drift")
    if load(root / "protocol.lock.json") != {
        "protocol_sha256": hashlib.sha256(protocol.read_bytes()).hexdigest(), "state_slice": STATE_SLICE,
    }:
        raise ValueError("protocol drift")
    summary = load(root / "summary.json")
    if summary.get("state_slice") != STATE_SLICE or any(
        summary.get(key) for key in ("accepted_evidence", "confirmation_authorized", "stage0_pass")
    ):
        raise ValueError("claim escalation")
    if summary["classification"] == "DevelopmentQualificationFailed":
        if any((root / name).exists() for name in ("fitting-records.jsonl", "assessment-telemetry.jsonl", "predictions.jsonl", "prediction-lock.json", "assessment-effects.jsonl")):
            raise ValueError("measurement after qualification failure")
        return summary
    fit, telemetry = rows(root / "fitting-records.jsonl"), rows(root / "assessment-telemetry.jsonl")
    predictions, effects = rows(root / "predictions.jsonl"), rows(root / "assessment-effects.jsonl")
    target_fit = len(ACTOR_SEEDS) * len(FIT_FAMILIES) * 16 * len(SITES) * len(OPERATORS)
    target_test = len(ACTOR_SEEDS) * len(ASSESSMENT_FAMILIES) * 16 * len(SITES) * len(OPERATORS)
    if (len(fit), len(telemetry), len(effects), len(predictions)) != (target_fit, target_test, target_test, target_test * len(METHODS)):
        raise ValueError("artifact census drift")
    if (
        summary["fitting_record_census"] != target_fit
        or summary["assessment_telemetry_census"] != target_test
        or summary["assessment_effect_census"] != target_test
        or summary["prediction_census"] != target_test * len(METHODS)
    ):
        raise ValueError("summary census drift")
    for collection, families, effect_required in (
        (fit, FIT_FAMILIES, True), (telemetry, ASSESSMENT_FAMILIES, False), (effects, ASSESSMENT_FAMILIES, True)
    ):
        seen = set()
        for row in collection:
            key = identity(row)
            if key in seen or row["seed"] not in ACTOR_SEEDS or row["family"] not in families or row["site"] not in SITES or row["operator"] not in OPERATORS:
                raise ValueError("row boundary drift")
            seen.add(key)
            if effect_required and not math.isfinite(float(row["effect"])):
                raise ValueError("nonfinite effect")
    lock = load(root / "prediction-lock.json")
    if lock.get("state_slice") != STATE_SLICE or lock.get("prediction_census") != target_test * len(METHODS):
        raise ValueError("prediction lock schema drift")
    for field, name in (
        ("fitting_records_sha256", "fitting-records.jsonl"),
        ("assessment_telemetry_sha256", "assessment-telemetry.jsonl"),
        ("predictions_sha256", "predictions.jsonl"),
    ):
        if lock[field] != hashlib.sha256((root / name).read_bytes()).hexdigest():
            raise ValueError("prediction lock drift")
    lock_hash = hashlib.sha256((root / "prediction-lock.json").read_bytes()).hexdigest()
    if summary["prediction_lock_sha256"] != lock_hash or any(row["prediction_lock_sha256"] != lock_hash for row in effects):
        raise ValueError("effect ordering drift")
    for seed in ACTOR_SEEDS:
        for method in METHODS:
            provenance = lock["projection_provenance"][f"seed={seed};method={method}"]
            fit_seeds = set(provenance["fit_seeds"])
            if method == "other_actor_telemetry":
                if seed in fit_seeds or fit_seeds != set(ACTOR_SEEDS) - {seed} or len(provenance["fit_families"]) != 8:
                    raise ValueError("other-actor leakage")
            elif fit_seeds != {seed}:
                raise ValueError("same-actor leakage")
    actual = {identity(row): float(row["effect"]) for row in effects}
    joined, seen = [], set()
    for row in predictions:
        key = (row["method"], *identity(row))
        if key in seen or row["method"] not in METHODS or not math.isfinite(float(row["predicted"])):
            raise ValueError("prediction drift")
        seen.add(key)
        joined.append({**row, "actual": actual[identity(row)]})
    recomputed = {}
    for method in METHODS:
        method_rows = [row for row in joined if row["method"] == method]
        recomputed[method] = {"pooled": metric_summary([row["actual"] for row in method_rows], [row["predicted"] for row in method_rows])}
        for seed in ACTOR_SEEDS:
            for operator in OPERATORS:
                subset = [row for row in method_rows if row["seed"] == seed and row["operator"] == operator]
                recomputed[method][f"seed={seed};operator={operator}"] = metric_summary(
                    [row["actual"] for row in subset], [row["predicted"] for row in subset]
                )
    if recomputed != summary["metrics"] or classify(recomputed) != summary["classification"]:
        raise ValueError("metric drift")
    return summary
