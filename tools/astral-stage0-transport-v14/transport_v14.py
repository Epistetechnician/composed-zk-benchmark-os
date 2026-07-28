"""Read-only V14 transportability diagnostic over a validated V13 bundle."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import sys

TOOLS = Path(__file__).resolve().parents[1]
V13 = TOOLS / "astral-stage0-causal-target-v13"
sys.path.insert(0, str(V13))
from learned_stage0_v13 import (  # noqa: E402
    ASSESSMENT_SEEDS, OPERATORS, SITES, features, metric_summary, ridge_predict,
)
from learned_validator_v13 import validate as validate_v13  # noqa: E402

STATE_SLICE = "astral-stage0c-effect-transportability-diagnostic-v14"
FIT_FAMILIES = range(656, 660)
TEST_FAMILIES = range(660, 664)
METHODS = (
    "v13_cross_actor", "cross_actor_constant", "actor_constant",
    "actor_activation", "actor_telemetry",
)


def canonical(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode()


def jsonl(path: Path) -> list[dict[str, object]]:
    return [json.loads(line) for line in path.read_bytes().splitlines()]


def identity(row: dict[str, object]) -> tuple[object, ...]:
    return row["seed"], row["family"], row["example_id"], row["site"], row["operator"]


def join_v13(root: Path) -> list[dict[str, object]]:
    telemetry = jsonl(root / "assessment-telemetry.jsonl")
    effects = {identity(row): row for row in jsonl(root / "assessment-effects.jsonl")}
    if len(effects) != len(telemetry):
        raise ValueError("V13 assessment census mismatch")
    joined = []
    for row in telemetry:
        effect = effects.get(identity(row))
        if effect is None or effect["donor_example_id"] != _donor_id(str(row["example_id"])):
            raise ValueError("V13 telemetry/effect join mismatch")
        joined.append({**row, "effect": float(effect["effect"])})
    return sorted(joined, key=identity)


def _donor_id(example_id: str) -> str:
    family, packed = example_id.split("-b")
    return f"{family}-b{int(packed) ^ 1:02d}"


def _group_mean(rows, keys):
    groups: dict[tuple[object, ...], list[float]] = {}
    for row in rows:
        groups.setdefault(tuple(row[key] for key in keys), []).append(float(row["effect"]))
    return {key: sum(values) / len(values) for key, values in groups.items()}


def diagnostic_predictions(
    joined: list[dict[str, object]],
    fitting_records: list[dict[str, object]],
    v13_predictions: list[dict[str, object]],
) -> list[dict[str, object]]:
    fit = [row for row in joined if row["family"] in FIT_FAMILIES]
    test = [row for row in joined if row["family"] in TEST_FAMILIES]
    cross_mean = _group_mean(fitting_records, ("site", "operator"))
    actor_mean = _group_mean(fit, ("seed", "site", "operator"))
    v13_map = {
        identity(row): float(row["predicted"])
        for row in v13_predictions if row["estimator"] == "telemetry"
    }
    learned = {}
    for seed in ASSESSMENT_SEEDS:
        train = [row for row in fit if row["seed"] == seed]
        held = [row for row in test if row["seed"] == seed]
        target = [float(row["effect"]) for row in train]
        for method, estimator in (("actor_activation", "activation_only"), ("actor_telemetry", "telemetry")):
            predicted = ridge_predict(
                [features(row, estimator) for row in train], target,
                [features(row, estimator) for row in held],
            )
            learned[method, seed] = dict(zip((identity(row) for row in held), predicted))
    result = []
    for row in test:
        key = identity(row)
        values = {
            "v13_cross_actor": v13_map[key],
            "cross_actor_constant": cross_mean[(row["site"], row["operator"])],
            "actor_constant": actor_mean[(row["seed"], row["site"], row["operator"])],
            "actor_activation": learned["actor_activation", row["seed"]][key],
            "actor_telemetry": learned["actor_telemetry", row["seed"]][key],
        }
        for method, predicted in values.items():
            result.append({
                "actual": float(row["effect"]), "example_id": row["example_id"],
                "family": row["family"], "method": method, "operator": row["operator"],
                "predicted": predicted, "seed": row["seed"], "site": row["site"],
            })
    return sorted(result, key=lambda row: (row["method"], *identity(row)))


def summarize(predictions):
    metrics = {}
    for method in METHODS:
        rows = [row for row in predictions if row["method"] == method]
        metrics[method] = {"pooled": metric_summary(
            [row["actual"] for row in rows], [row["predicted"] for row in rows]
        )}
        for seed in ASSESSMENT_SEEDS:
            for operator in OPERATORS:
                subset = [row for row in rows if row["seed"] == seed and row["operator"] == operator]
                metrics[method][f"seed={seed};operator={operator}"] = metric_summary(
                    [row["actual"] for row in subset], [row["predicted"] for row in subset]
                )
    return metrics


def variance_decomposition(rows):
    values = [float(row["effect"]) for row in rows]
    grand = sum(values) / len(values)
    total = sum((value - grand) ** 2 for value in values)
    actor_means = _group_mean(rows, ("seed",))
    site_means = _group_mean(rows, ("site", "operator"))
    actor_ss = sum((actor_means[(row["seed"],)] - grand) ** 2 for row in rows)
    site_ss = sum((site_means[(row["site"], row["operator"])] - grand) ** 2 for row in rows)
    residual_ss = sum(
        (float(row["effect"]) - actor_means[(row["seed"],)] - site_means[(row["site"], row["operator"])] + grand) ** 2
        for row in rows
    )
    if total <= 0:
        return {"actor_fraction": 0.0, "residual_fraction": 0.0, "site_operator_fraction": 0.0}
    return {
        "actor_fraction": actor_ss / total,
        "residual_fraction": residual_ss / total,
        "site_operator_fraction": site_ss / total,
    }


def classify(metrics):
    cross = metrics["cross_actor_constant"]["pooled"]["mse"]
    actor = metrics["actor_constant"]["pooled"]["mse"]
    conditioning = cross > 0 and actor <= 0.8 * cross
    telemetry_better = (
        metrics["actor_telemetry"]["pooled"]["mse"]
        < metrics["actor_activation"]["pooled"]["mse"]
    )
    if conditioning and telemetry_better:
        return "CrossActorTransportFailure"
    if conditioning:
        return "ActorBaselineShiftOnly"
    if not telemetry_better:
        return "LocalTelemetryNonpredictive"
    return "MixedDiagnostic"


def analyze(v13_root: Path, v13_protocol: Path):
    validate_v13(v13_root, v13_protocol)
    joined = join_v13(v13_root)
    predictions = diagnostic_predictions(
        joined, jsonl(v13_root / "fitting-records.jsonl"),
        jsonl(v13_root / "predictions.jsonl"),
    )
    metrics = summarize(predictions)
    test_rows = [row for row in joined if row["family"] in TEST_FAMILIES]
    return predictions, {
        "accepted_evidence": False,
        "claim_class": "LocalPostHocEffectTransportabilityDiagnostic",
        "classification": classify(metrics),
        "confirmation_authorized": False,
        "metrics": metrics,
        "prediction_census": len(predictions),
        "source_manifest_sha256": hashlib.sha256((v13_root / "manifest.json").read_bytes()).hexdigest(),
        "source_prediction_lock_sha256": hashlib.sha256((v13_root / "prediction-lock.json").read_bytes()).hexdigest(),
        "stage0_pass": False,
        "state_slice": STATE_SLICE,
        "test_target_census": len(test_rows),
        "variance_decomposition": variance_decomposition(test_rows),
    }
