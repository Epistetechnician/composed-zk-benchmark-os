"""Fail-closed validator for a completed V12 artifact bundle."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

from learned_stage0_v12 import (
    ASSESSMENT_FAMILIES, DESIGN_FAMILIES, ESTIMATORS, EXPLORATORY_SEEDS,
    OPERATORS, STATE_SLICE,
)
from run_learned_stage0_v12 import classify, summarize


def load_json(path: Path):
    return json.loads(path.read_text())


def jsonl(path: Path):
    return [json.loads(line) for line in path.read_text().splitlines() if line]


def validate(root: Path, protocol: Path):
    root = root.resolve()
    manifest = load_json(root / "manifest.json")
    if manifest.get("state_slice") != STATE_SLICE:
        raise ValueError("manifest state slice drift")
    expected = {row["path"]: row for row in manifest["files"]}
    actual_names = {path.name for path in root.iterdir() if path.name != "manifest.json"}
    if set(expected) != actual_names:
        raise ValueError("manifest census mismatch")
    for name, row in expected.items():
        raw = (root / name).read_bytes()
        if row != {"bytes": len(raw), "path": name, "sha256": hashlib.sha256(raw).hexdigest()}:
            raise ValueError("manifest digest mismatch")
    lock = load_json(root / "protocol.lock.json")
    if lock != {
        "protocol_sha256": hashlib.sha256(protocol.read_bytes()).hexdigest(),
        "state_slice": STATE_SLICE,
    }:
        raise ValueError("protocol binding mismatch")
    summary = load_json(root / "summary.json")
    if summary.get("state_slice") != STATE_SLICE:
        raise ValueError("summary state slice drift")
    if summary.get("accepted_evidence") or summary.get("stage0_pass") or summary.get("confirmation_authorized"):
        raise ValueError("claim boundary escalation")
    if summary["classification"] == "DevelopmentQualificationFailed":
        if (root / "records.jsonl").exists() or (root / "predictions.jsonl").exists():
            raise ValueError("measurement exists after qualification failure")
        return summary
    records = jsonl(root / "records.jsonl")
    predictions = jsonl(root / "predictions.jsonl")
    expected_records = len(EXPLORATORY_SEEDS) * (len(DESIGN_FAMILIES) + len(ASSESSMENT_FAMILIES)) * 16 * 4 * len(OPERATORS)
    expected_predictions = len(ESTIMATORS) * len(EXPLORATORY_SEEDS) * len(ASSESSMENT_FAMILIES) * 16 * 4 * len(OPERATORS)
    if len(records) != expected_records or summary["record_census"] != expected_records:
        raise ValueError("record census mismatch")
    if len(predictions) != expected_predictions or summary["prediction_census"] != expected_predictions:
        raise ValueError("prediction census mismatch")
    identities = set()
    for row in records:
        identity = (row["seed"], row["fold"], row["example_id"], row["head"], row["operator"])
        if identity in identities:
            raise ValueError("duplicate record")
        identities.add(identity)
        allowed = DESIGN_FAMILIES if row["fold"] == "design" else ASSESSMENT_FAMILIES
        if row["seed"] not in EXPLORATORY_SEEDS or row["family"] not in allowed:
            raise ValueError("record boundary breach")
        if row["operator"] not in OPERATORS or row["head"] not in range(4):
            raise ValueError("record schema drift")
        if not all(math.isfinite(value) for value in (row["effect"], row["clean_margin"])):
            raise ValueError("nonfinite record")
    for row in predictions:
        if (
            row["estimator"] not in ESTIMATORS
            or row["seed"] not in EXPLORATORY_SEEDS
            or row["family"] not in ASSESSMENT_FAMILIES
            or row["operator"] not in OPERATORS
            or not math.isfinite(row["actual"])
            or not math.isfinite(row["predicted"])
        ):
            raise ValueError("prediction boundary breach")
    recomputed = {}
    for estimator in ESTIMATORS:
        estimator_rows = [row for row in predictions if row["estimator"] == estimator]
        recomputed[estimator] = {"pooled": summarize(estimator_rows)}
        for seed in EXPLORATORY_SEEDS:
            for operator in OPERATORS:
                subset = [
                    row for row in estimator_rows
                    if row["seed"] == seed and row["operator"] == operator
                ]
                recomputed[estimator][f"seed={seed};operator={operator}"] = summarize(subset)
    if recomputed != summary["metrics"]:
        raise ValueError("metric aggregate drift")
    if classify(summary["metrics"]) != summary["classification"]:
        raise ValueError("classification drift")
    return summary


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--protocol", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(validate(args.root, args.protocol), indent=2, sort_keys=True))
