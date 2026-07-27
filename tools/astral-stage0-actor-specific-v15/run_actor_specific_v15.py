"""Run V15 with assessment effects blocked until predictions are sealed."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from actor_specific_v15 import (
    ACTOR_SEEDS, ASSESSMENT_FAMILIES, FIT_FAMILIES, METHODS,
    OPERATORS, OTHER_ACTOR_FAMILIES, PRACTICAL_MARGIN, STATE_SLICE,
    authorized_families, constant_predictions, effect_rows, examples_for,
    features, metric_summary, reproduce, ridge_predict, shuffled_features,
    telemetry_rows,
)


def canonical(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode()


def write_jsonl(path, rows):
    raw = b"".join(canonical(row) for row in rows)
    path.write_bytes(raw)
    return hashlib.sha256(raw).hexdigest()


def identity(row):
    return row["seed"], row["family"], row["example_id"], row["site"], row["operator"]


def prepare(root: Path, repo: Path):
    if root.is_symlink():
        raise ValueError("output must be real")
    root, repo = root.resolve(), repo.resolve()
    if root == repo or repo in root.parents or root in repo.parents:
        raise ValueError("output must be repository-external")
    if root.exists() and (not root.is_dir() or any(root.iterdir())):
        raise ValueError("output must be empty")
    root.mkdir(parents=True, exist_ok=True)
    return root


def classify(metrics):
    telemetry = metrics["same_actor_telemetry"]["pooled"]
    if telemetry["correlation"] is None or telemetry["correlation"] <= 0:
        return "DevelopmentNoCandidate"
    if telemetry["calibration_slope"] is None or not .5 <= telemetry["calibration_slope"] <= 1.5:
        return "DevelopmentNoCandidate"
    for method in METHODS[1:]:
        if telemetry["mse"] >= metrics[method]["pooled"]["mse"]:
            return "DevelopmentNoCandidate"
    for seed in ACTOR_SEEDS:
        for operator in OPERATORS:
            key = f"seed={seed};operator={operator}"
            if metrics["same_actor_telemetry"][key]["mse"] > (
                (1 - PRACTICAL_MARGIN) * metrics["same_actor_activation"][key]["mse"]
            ):
                return "DevelopmentNoCandidate"
    return "DevelopmentCandidateEligible"


def run(root: Path, repo: Path, protocol: Path):
    root = prepare(root, repo)
    if not authorized_families(FIT_FAMILIES) or not authorized_families(ASSESSMENT_FAMILIES):
        raise RuntimeError("family boundary drift")
    (root / "protocol.lock.json").write_bytes(canonical({
        "protocol_sha256": hashlib.sha256(protocol.read_bytes()).hexdigest(), "state_slice": STATE_SLICE,
    }))
    actors, qualifications = {}, []
    for seed in ACTOR_SEEDS:
        actor, qualification = reproduce(seed)
        qualifications.append(qualification)
        (root / f"qualification-{seed}.json").write_bytes(canonical(qualification))
        if not qualification["eligible"]:
            return finalize(root, {
                "accepted_evidence": False, "classification": "DevelopmentQualificationFailed",
                "confirmation_authorized": False, "failed_seed": seed,
                "qualifications": qualifications, "stage0_pass": False, "state_slice": STATE_SLICE,
            })
        actors[seed] = actor
    fit = []
    for seed, actor in actors.items():
        for example in examples_for(FIT_FAMILIES):
            telemetry = {(row["site"], row["operator"]): row for row in telemetry_rows(actor, example)}
            for effect in effect_rows(actor, example):
                fit.append({**telemetry[(effect["site"], effect["operator"])], **effect, "seed": seed})
    fit.sort(key=identity)
    fit_hash = write_jsonl(root / "fitting-records.jsonl", fit)
    assessment = []
    for seed, actor in actors.items():
        for example in examples_for(ASSESSMENT_FAMILIES):
            assessment.extend({**row, "seed": seed} for row in telemetry_rows(actor, example))
    assessment.sort(key=identity)
    assessment_hash = write_jsonl(root / "assessment-telemetry.jsonl", assessment)
    predictions, provenance = [], {}
    for seed in ACTOR_SEEDS:
        same = [row for row in fit if row["seed"] == seed]
        other = [
            row for row in fit
            if row["seed"] != seed and row["family"] in OTHER_ACTOR_FAMILIES
        ]
        test = [row for row in assessment if row["seed"] == seed]
        targets = [float(row["effect"]) for row in same]
        specifications = {
            "same_actor_telemetry": (same, "telemetry", None),
            "other_actor_telemetry": (other, "telemetry", None),
            "same_actor_activation": (same, "activation_only", None),
            "same_actor_text_io": (same, "text_io", None),
            "same_actor_shuffled": (same, "telemetry", shuffled_features(same, seed)),
        }
        values_by_method = {"same_actor_constant": constant_predictions(same, test)}
        for method, (train, estimator, overridden) in specifications.items():
            train_x = overridden if overridden is not None else [features(row, estimator) for row in train]
            values_by_method[method] = ridge_predict(
                train_x, [float(row["effect"]) for row in train],
                [features(row, estimator) for row in test],
            )
            provenance[f"seed={seed};method={method}"] = {
                "excluded_target_actor": method == "other_actor_telemetry",
                "fit_families": sorted({row["family"] for row in train}),
                "fit_seeds": sorted({row["seed"] for row in train}),
                "target_seed": seed,
            }
        provenance[f"seed={seed};method=same_actor_constant"] = {
            "excluded_target_actor": False, "fit_families": list(FIT_FAMILIES),
            "fit_seeds": [seed], "target_seed": seed,
        }
        for method in METHODS:
            for row, predicted in zip(test, values_by_method[method]):
                predictions.append({
                    "example_id": row["example_id"], "family": row["family"],
                    "method": method, "operator": row["operator"], "predicted": predicted,
                    "seed": seed, "site": row["site"],
                })
    predictions.sort(key=lambda row: (row["method"], *identity(row)))
    prediction_hash = write_jsonl(root / "predictions.jsonl", predictions)
    lock = {
        "assessment_telemetry_sha256": assessment_hash, "fitting_records_sha256": fit_hash,
        "prediction_census": len(predictions), "predictions_sha256": prediction_hash,
        "projection_provenance": provenance, "state_slice": STATE_SLICE,
    }
    (root / "prediction-lock.json").write_bytes(canonical(lock))
    lock_hash = hashlib.sha256((root / "prediction-lock.json").read_bytes()).hexdigest()
    if (root / "assessment-effects.jsonl").exists():
        raise RuntimeError("assessment effects predate prediction lock")
    effects = []
    for seed, actor in actors.items():
        for example in examples_for(ASSESSMENT_FAMILIES):
            effects.extend({**row, "prediction_lock_sha256": lock_hash, "seed": seed} for row in effect_rows(actor, example))
    effects.sort(key=identity)
    write_jsonl(root / "assessment-effects.jsonl", effects)
    actual = {identity(row): float(row["effect"]) for row in effects}
    joined = [{**row, "actual": actual[identity(row)]} for row in predictions]
    metrics = {}
    for method in METHODS:
        rows = [row for row in joined if row["method"] == method]
        metrics[method] = {"pooled": metric_summary([row["actual"] for row in rows], [row["predicted"] for row in rows])}
        for seed in ACTOR_SEEDS:
            for operator in OPERATORS:
                subset = [row for row in rows if row["seed"] == seed and row["operator"] == operator]
                metrics[method][f"seed={seed};operator={operator}"] = metric_summary(
                    [row["actual"] for row in subset], [row["predicted"] for row in subset]
                )
    return finalize(root, {
        "accepted_evidence": False, "assessment_effect_census": len(effects),
        "assessment_telemetry_census": len(assessment),
        "claim_class": "LocalDevelopmentProspectiveActorSpecificPredictionDiagnostic",
        "classification": classify(metrics), "confirmation_authorized": False,
        "fitting_record_census": len(fit), "metrics": metrics,
        "prediction_census": len(predictions), "prediction_lock_sha256": lock_hash,
        "qualifications": qualifications, "stage0_pass": False, "state_slice": STATE_SLICE,
    })


def finalize(root, summary):
    (root / "summary.json").write_bytes(canonical(summary))
    files = []
    for path in sorted(root.iterdir()):
        raw = path.read_bytes()
        files.append({"bytes": len(raw), "path": path.name, "sha256": hashlib.sha256(raw).hexdigest()})
    (root / "manifest.json").write_bytes(canonical({"files": files, "state_slice": STATE_SLICE}))
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--repo", required=True, type=Path)
    parser.add_argument("--protocol", required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(run(args.output, args.repo, args.protocol), indent=2, sort_keys=True))
