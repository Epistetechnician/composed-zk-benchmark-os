#!/usr/bin/env python3
"""Aggregate-only V28 prediction-locked channel comparison.

State slice: astral-opaque-causal-channel-separation-v28-aggregation.
The input stream is transient derived data. Only aggregate metrics are written.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

PROTOCOL = "astral-opaque-causal-channel-separation-v28"
CLAIM_CEILING = "LocalDevelopmentOpaqueCausalChannelSeparation"
FULL_FEATURES = 16
OPAQUE_FEATURES = 4
RIDGE = 1e-3


def solve(matrix: list[list[float]], vector: list[float]) -> list[float]:
    size = len(vector)
    augmented = [row[:] + [vector[index]] for index, row in enumerate(matrix)]
    for pivot in range(size):
        row = max(range(pivot, size), key=lambda candidate: abs(augmented[candidate][pivot]))
        if abs(augmented[row][pivot]) < 1e-12:
            raise ValueError("singular_system")
        augmented[pivot], augmented[row] = augmented[row], augmented[pivot]
        divisor = augmented[pivot][pivot]
        augmented[pivot] = [value / divisor for value in augmented[pivot]]
        for other in range(size):
            if other == pivot:
                continue
            factor = augmented[other][pivot]
            augmented[other] = [
                left - factor * right for left, right in zip(augmented[other], augmented[pivot])
            ]
    return [augmented[index][-1] for index in range(size)]


def fit(rows: list[dict], key: str, dimensions: int) -> list[float]:
    matrix = [[0.0 for _ in range(dimensions + 1)] for _ in range(dimensions + 1)]
    vector = [0.0 for _ in range(dimensions + 1)]
    for row in rows:
        features = [1.0] + [float(value) for value in row[key]]
        target = float(row["target"])
        for left in range(dimensions + 1):
            vector[left] += features[left] * target
            for right in range(dimensions + 1):
                matrix[left][right] += features[left] * features[right]
    for index in range(1, dimensions + 1):
        matrix[index][index] += RIDGE
    return solve(matrix, vector)


def predict(weights: list[float], row: dict, key: str) -> float:
    return weights[0] + sum(weight * float(value) for weight, value in zip(weights[1:], row[key]))


def mse(weights: list[float], rows: list[dict], key: str) -> float:
    return sum((predict(weights, row, key) - float(row["target"])) ** 2 for row in rows) / len(rows)


def variance(rows: list[dict]) -> float:
    mean = sum(float(row["target"]) for row in rows) / len(rows)
    return sum((float(row["target"]) - mean) ** 2 for row in rows) / len(rows)


def parse_rows(stream: object) -> list[dict]:
    rows: list[dict] = []
    for line in stream:
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError("row_not_object")
        if len(value.get("full", [])) != FULL_FEATURES or len(value.get("opaque", [])) != OPAQUE_FEATURES:
            raise ValueError("feature_dimension_mismatch")
        if value.get("finite") is not True:
            raise ValueError("nonfinite_row")
        rows.append(value)
    if len(rows) != 16:
        raise ValueError("trial_count")
    return rows


def aggregate(rows: list[dict]) -> dict:
    if [row["trial"] for row in rows] != list(range(16)):
        raise ValueError("trial_order")
    if [row["split"] for row in rows] != [0] * 8 + [1] * 4 + [2] * 4:
        raise ValueError("split_order")
    fit_rows = rows[:8]
    tune_rows = rows[8:12]
    assessment_rows = rows[12:]
    full_weights = fit(fit_rows, "full", FULL_FEATURES)
    opaque_weights = fit(fit_rows, "opaque", OPAQUE_FEATURES)
    shuffled_rows = [dict(row, full=list(reversed(row["full"]))) for row in fit_rows]
    shuffled_weights = fit(shuffled_rows, "full", FULL_FEATURES)
    # Prediction locking occurs before assessment scoring and before the
    # assessment target values are accessed by the metric calculations.
    tune_full = mse(full_weights, tune_rows, "full")
    tune_opaque = mse(opaque_weights, tune_rows, "opaque")
    tune_shuffled = mse(shuffled_weights, tune_rows, "full")
    assessment_full = mse(full_weights, assessment_rows, "full")
    assessment_opaque = mse(opaque_weights, assessment_rows, "opaque")
    assessment_shuffled = mse(shuffled_weights, assessment_rows, "full")
    target_variance = variance(assessment_rows)
    full_relative = assessment_full / target_variance if target_variance > 0 else math.inf
    opaque_relative = assessment_opaque / target_variance if target_variance > 0 else math.inf
    shuffled_relative = assessment_shuffled / target_variance if target_variance > 0 else math.inf
    finite = all(math.isfinite(value) for value in (
        tune_full, tune_opaque, tune_shuffled, assessment_full, assessment_opaque,
        assessment_shuffled, target_variance, full_relative, opaque_relative, shuffled_relative,
    ))
    variance_gate = target_variance >= 1e-8
    channel_order_gate = finite and variance_gate and full_relative < shuffled_relative and opaque_relative < shuffled_relative
    utility_gate = finite and variance_gate and full_relative < 1.0 and opaque_relative < 1.0
    separation_gate = channel_order_gate and utility_gate
    classification = "OpaqueCausalChannelSeparationObserved" if separation_gate else "OpaqueCausalChannelOrderingSignalOnly"
    return {
        "protocol": PROTOCOL,
        "classification": classification,
        "claim_ceiling": CLAIM_CEILING,
        "trial_count": len(rows),
        "fit_count": len(fit_rows),
        "tune_count": len(tune_rows),
        "assessment_count": len(assessment_rows),
        "full_feature_count": FULL_FEATURES,
        "opaque_feature_count": OPAQUE_FEATURES,
        "ridge": RIDGE,
        "target": "direct_held_out_intervention_logit_margin_effect",
        "prediction_locked_before_assessment": True,
        "tune_full_mse": tune_full,
        "tune_opaque_mse": tune_opaque,
        "tune_shuffled_mse": tune_shuffled,
        "assessment_full_mse": assessment_full,
        "assessment_opaque_mse": assessment_opaque,
        "assessment_shuffled_mse": assessment_shuffled,
        "assessment_target_variance": target_variance,
        "assessment_full_relative_mse": full_relative,
        "assessment_opaque_relative_mse": opaque_relative,
        "assessment_shuffled_relative_mse": shuffled_relative,
        "finite": finite,
        "variance_gate": variance_gate,
        "channel_order_gate": channel_order_gate,
        "utility_gate": utility_gate,
        "separation_gate": separation_gate,
        "model_execution": True,
        "network_access": False,
        "raw_intermediate_retained": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        rows = parse_rows(sys.stdin)
        result = aggregate(rows)
        args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print(f"invalid V28 stream: {type(exc).__name__}:{exc}", file=sys.stderr)
        return 2
    print(json.dumps({"protocol": PROTOCOL, "classification": result["classification"]}, sort_keys=True), file=sys.stderr)
    return 0 if result["classification"] == "OpaqueCausalChannelSeparationObserved" else 3


if __name__ == "__main__":
    sys.exit(main())
