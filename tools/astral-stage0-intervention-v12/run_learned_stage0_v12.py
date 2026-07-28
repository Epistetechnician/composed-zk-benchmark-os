"""Run the frozen V12 development-only intervention-prediction panel."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from learned_stage0_v12 import (
    ASSESSMENT_FAMILIES, DESIGN_FAMILIES, ESTIMATORS, EXPLORATORY_SEEDS,
    OPERATORS, PRACTICAL_MARGIN, STATE_SLICE, authorized_families, examples_for,
    features, measure_example, metric_summary, reproduce, ridge_predict,
    shuffled_train_features,
)


def canonical(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode()


def write(path: Path, value: object) -> None:
    path.write_bytes(canonical(value))


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


def classify(metrics: dict[str, dict[str, dict[str, object]]]) -> str:
    telemetry_pooled = metrics["telemetry"]["pooled"]
    if telemetry_pooled["correlation"] is None or telemetry_pooled["correlation"] <= 0:
        return "DevelopmentNoCandidate"
    slope = telemetry_pooled["calibration_slope"]
    if slope is None or not .5 <= slope <= 1.5:
        return "DevelopmentNoCandidate"
    for estimator in ("constant", "input_output_only", "shuffled_telemetry"):
        if telemetry_pooled["mse"] >= metrics[estimator]["pooled"]["mse"]:
            return "DevelopmentNoCandidate"
    for seed in EXPLORATORY_SEEDS:
        for operator in OPERATORS:
            key = f"seed={seed};operator={operator}"
            if metrics["telemetry"][key]["mse"] > (
                (1.0 - PRACTICAL_MARGIN) * metrics["activation_only"][key]["mse"]
            ):
                return "DevelopmentNoCandidate"
    return "DevelopmentCandidateEligible"


def top_one_regret(rows: list[dict[str, object]]) -> float:
    grouped: dict[tuple[object, ...], list[dict[str, object]]] = {}
    for row in rows:
        key = (row["seed"], row["operator"], row["example_id"])
        grouped.setdefault(key, []).append(row)
    regrets = []
    for group in grouped.values():
        if len(group) != 4:
            raise ValueError("incomplete head vector")
        group.sort(key=lambda row: row["head"])
        actual = [abs(float(row["actual"])) for row in group]
        predicted = [abs(float(row["predicted"])) for row in group]
        oracle = max(actual)
        if oracle <= 1e-4:
            continue
        selected = min(range(4), key=lambda index: (-predicted[index], index))
        regrets.append((oracle - actual[selected]) / oracle)
    return sum(regrets) / len(regrets) if regrets else 0.0


def summarize(rows: list[dict[str, object]]) -> dict[str, object]:
    result = metric_summary(
        [float(row["actual"]) for row in rows],
        [float(row["predicted"]) for row in rows],
    )
    result["top_one_regret"] = top_one_regret(rows)
    return result


def run(root: Path, repo: Path, protocol: Path):
    root = prepare(root, repo)
    if not authorized_families(DESIGN_FAMILIES) or not authorized_families(ASSESSMENT_FAMILIES):
        raise RuntimeError("family authorization drift")
    write(root / "protocol.lock.json", {
        "protocol_sha256": hashlib.sha256(protocol.read_bytes()).hexdigest(),
        "state_slice": STATE_SLICE,
    })
    actors = {}
    qualifications = []
    for seed in EXPLORATORY_SEEDS:
        actor, row = reproduce(seed)
        qualifications.append(row)
        write(root / f"qualification-{seed}.json", row)
        if not row["eligible"]:
            return finalize(root, {
                "accepted_evidence": False,
                "classification": "DevelopmentQualificationFailed",
                "confirmation_authorized": False,
                "failed_seed": seed,
                "qualifications": qualifications,
                "stage0_pass": False,
                "state_slice": STATE_SLICE,
            })
        actors[seed] = actor
    records = []
    for seed, actor in actors.items():
        for fold, families in (("design", DESIGN_FAMILIES), ("assessment", ASSESSMENT_FAMILIES)):
            for example in examples_for(families):
                for row in measure_example(actor, example):
                    records.append({**row, "fold": fold, "seed": seed})
    records.sort(key=lambda row: (row["seed"], row["fold"], row["family"], row["example_id"], row["head"], row["operator"]))
    (root / "records.jsonl").write_bytes(b"".join(canonical(row) for row in records))
    predictions = []
    for held_seed in EXPLORATORY_SEEDS:
        train = [row for row in records if row["fold"] == "design" and row["seed"] != held_seed]
        test = [row for row in records if row["fold"] == "assessment" and row["seed"] == held_seed]
        target = [float(row["effect"]) for row in train]
        for estimator in ESTIMATORS:
            if estimator == "constant":
                predicted = [sum(target) / len(target)] * len(test)
            else:
                train_x = (
                    shuffled_train_features(train, held_seed)
                    if estimator == "shuffled_telemetry"
                    else [features(row, estimator) for row in train]
                )
                test_kind = "telemetry" if estimator == "shuffled_telemetry" else estimator
                predicted = ridge_predict(
                    train_x, target, [features(row, test_kind) for row in test]
                )
            for row, value in zip(test, predicted):
                predictions.append({
                    "actual": row["effect"], "estimator": estimator,
                    "example_id": row["example_id"], "family": row["family"],
                    "head": row["head"], "operator": row["operator"],
                    "predicted": value, "seed": held_seed,
                })
    predictions.sort(key=lambda row: (row["estimator"], row["seed"], row["family"], row["example_id"], row["head"], row["operator"]))
    (root / "predictions.jsonl").write_bytes(b"".join(canonical(row) for row in predictions))
    metrics: dict[str, dict[str, dict[str, object]]] = {}
    for estimator in ESTIMATORS:
        rows = [row for row in predictions if row["estimator"] == estimator]
        metrics[estimator] = {
            "pooled": summarize(rows)
        }
        for seed in EXPLORATORY_SEEDS:
            for operator in OPERATORS:
                subset = [row for row in rows if row["seed"] == seed and row["operator"] == operator]
                metrics[estimator][f"seed={seed};operator={operator}"] = summarize(subset)
    classification = classify(metrics)
    return finalize(root, {
        "accepted_evidence": False,
        "claim_class": "LocalExploratoryInterventionPredictionDiagnostic",
        "classification": classification,
        "confirmation_authorized": False,
        "metrics": metrics,
        "prediction_census": len(predictions),
        "qualification": qualifications,
        "record_census": len(records),
        "stage0_pass": False,
        "state_slice": STATE_SLICE,
    })


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--protocol", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(run(args.output, args.repo, args.protocol), indent=2, sort_keys=True))
