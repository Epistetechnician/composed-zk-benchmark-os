"""Run V13 with a prediction lock before assessment-effect materialization."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from learned_stage0_v13 import (
    ALL_SEEDS, ASSESSMENT_FAMILIES, ASSESSMENT_SEEDS, ESTIMATORS, FIT_FAMILIES,
    FIT_SEEDS, OPERATORS, PRACTICAL_MARGIN, SITES, STATE_SLICE,
    authorized_families, effect_rows, examples_for, features, metric_summary,
    reproduce, ridge_predict, shuffled_train_features, telemetry_rows,
)


def canonical(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode()


def write(path: Path, value: object) -> None:
    path.write_bytes(canonical(value))


def write_jsonl(path: Path, rows: list[dict[str, object]]) -> str:
    payload = b"".join(canonical(row) for row in rows)
    path.write_bytes(payload)
    return hashlib.sha256(payload).hexdigest()


def prepare(root: Path, repo: Path) -> Path:
    if root.is_symlink():
        raise ValueError("output must be real")
    root, repo = root.resolve(), repo.resolve()
    if root == repo or repo in root.parents or root in repo.parents:
        raise ValueError("output must be repository-external")
    if root.exists() and (not root.is_dir() or any(root.iterdir())):
        raise ValueError("output must be empty")
    root.mkdir(parents=True, exist_ok=True)
    return root


def finalize(root: Path, summary: dict[str, object]) -> dict[str, object]:
    write(root / "summary.json", summary)
    files = []
    for path in sorted(root.iterdir()):
        raw = path.read_bytes()
        files.append({"bytes": len(raw), "path": path.name, "sha256": hashlib.sha256(raw).hexdigest()})
    write(root / "manifest.json", {"files": files, "state_slice": STATE_SLICE})
    return summary


def identity(row: dict[str, object]) -> tuple[object, ...]:
    return row["seed"], row["family"], row["example_id"], row["site"], row["operator"]


def constant_predictions(train, test):
    means = {}
    for site_kind in ("head", "mlp"):
        for operator in OPERATORS:
            values = [
                float(row["effect"]) for row in train
                if ("head" if str(row["site"]).startswith("head") else "mlp") == site_kind
                and row["operator"] == operator
            ]
            means[site_kind, operator] = sum(values) / len(values)
    return [
        means[("head" if str(row["site"]).startswith("head") else "mlp"), row["operator"]]
        for row in test
    ]


def classify(metrics):
    telemetry = metrics["telemetry"]["pooled"]
    if telemetry["correlation"] is None or telemetry["correlation"] <= 0:
        return "DevelopmentNoCandidate"
    if telemetry["calibration_slope"] is None or not .5 <= telemetry["calibration_slope"] <= 1.5:
        return "DevelopmentNoCandidate"
    for estimator in ("constant", "text_io", "shuffled_telemetry"):
        if telemetry["mse"] >= metrics[estimator]["pooled"]["mse"]:
            return "DevelopmentNoCandidate"
    for seed in ASSESSMENT_SEEDS:
        for operator in OPERATORS:
            key = f"seed={seed};operator={operator}"
            if metrics["telemetry"][key]["mse"] > (1 - PRACTICAL_MARGIN) * metrics["activation_only"][key]["mse"]:
                return "DevelopmentNoCandidate"
    return "DevelopmentCandidateEligible"


def run(root: Path, repo: Path, protocol: Path):
    root = prepare(root, repo)
    if not authorized_families(FIT_FAMILIES) or not authorized_families(ASSESSMENT_FAMILIES):
        raise RuntimeError("family authorization drift")
    write(root / "protocol.lock.json", {
        "protocol_sha256": hashlib.sha256(protocol.read_bytes()).hexdigest(),
        "state_slice": STATE_SLICE,
    })
    actors, qualifications = {}, []
    for seed in ALL_SEEDS:
        actor, row = reproduce(seed)
        qualifications.append(row)
        write(root / f"qualification-{seed}.json", row)
        if not row["eligible"]:
            return finalize(root, {
                "accepted_evidence": False, "classification": "DevelopmentQualificationFailed",
                "confirmation_authorized": False, "failed_seed": seed,
                "qualifications": qualifications, "stage0_pass": False, "state_slice": STATE_SLICE,
            })
        actors[seed] = actor

    fit = []
    for seed in FIT_SEEDS:
        for example in examples_for(FIT_FAMILIES):
            telemetry = { (row["site"], row["operator"]): row for row in telemetry_rows(actors[seed], example) }
            for effect in effect_rows(actors[seed], example):
                fit.append({**telemetry[(effect["site"], effect["operator"])], **effect, "seed": seed})
    fit.sort(key=identity)
    fit_hash = write_jsonl(root / "fitting-records.jsonl", fit)

    assessment = []
    for seed in ASSESSMENT_SEEDS:
        for example in examples_for(ASSESSMENT_FAMILIES):
            assessment.extend({**row, "seed": seed} for row in telemetry_rows(actors[seed], example))
    assessment.sort(key=identity)
    telemetry_hash = write_jsonl(root / "assessment-telemetry.jsonl", assessment)

    predictions = []
    target = [float(row["effect"]) for row in fit]
    for estimator in ESTIMATORS:
        if estimator == "constant":
            values = constant_predictions(fit, assessment)
        else:
            train_x = shuffled_train_features(fit) if estimator == "shuffled_telemetry" else [features(row, estimator) for row in fit]
            test_kind = "telemetry" if estimator == "shuffled_telemetry" else estimator
            values = ridge_predict(train_x, target, [features(row, test_kind) for row in assessment])
        for row, predicted in zip(assessment, values):
            predictions.append({
                "estimator": estimator, "example_id": row["example_id"], "family": row["family"],
                "operator": row["operator"], "predicted": predicted, "seed": row["seed"], "site": row["site"],
            })
    predictions.sort(key=lambda row: (row["estimator"], *identity(row)))
    prediction_hash = write_jsonl(root / "predictions.jsonl", predictions)
    lock_body = {
        "assessment_telemetry_sha256": telemetry_hash,
        "fitting_records_sha256": fit_hash,
        "prediction_census": len(predictions),
        "predictions_sha256": prediction_hash,
        "state_slice": STATE_SLICE,
    }
    write(root / "prediction-lock.json", lock_body)
    lock_hash = hashlib.sha256((root / "prediction-lock.json").read_bytes()).hexdigest()

    effects = []
    for seed in ASSESSMENT_SEEDS:
        for example in examples_for(ASSESSMENT_FAMILIES):
            effects.extend({**row, "prediction_lock_sha256": lock_hash, "seed": seed} for row in effect_rows(actors[seed], example))
    effects.sort(key=identity)
    write_jsonl(root / "assessment-effects.jsonl", effects)
    effect_map = {identity(row): float(row["effect"]) for row in effects}
    joined = [{**row, "actual": effect_map[identity(row)]} for row in predictions]
    metrics = {}
    for estimator in ESTIMATORS:
        rows = [row for row in joined if row["estimator"] == estimator]
        metrics[estimator] = {"pooled": metric_summary([row["actual"] for row in rows], [row["predicted"] for row in rows])}
        for seed in ASSESSMENT_SEEDS:
            for operator in OPERATORS:
                subset = [row for row in rows if row["seed"] == seed and row["operator"] == operator]
                metrics[estimator][f"seed={seed};operator={operator}"] = metric_summary(
                    [row["actual"] for row in subset], [row["predicted"] for row in subset]
                )
    classification = classify(metrics)
    return finalize(root, {
        "accepted_evidence": False, "assessment_effect_census": len(effects),
        "assessment_telemetry_census": len(assessment),
        "claim_class": "LocalDevelopmentCausalTargetDiagnostic",
        "classification": classification, "confirmation_authorized": False,
        "fitting_record_census": len(fit), "metrics": metrics,
        "prediction_census": len(predictions), "prediction_lock_sha256": lock_hash,
        "qualifications": qualifications, "stage0_pass": False, "state_slice": STATE_SLICE,
    })


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--protocol", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(run(args.output, args.repo, args.protocol), indent=2, sort_keys=True))
