#!/usr/bin/env python3
"""Aggregate-only V29 calibrated prediction analysis.
State slice: astral-calibrated-opaque-causal-channel-v29-aggregation.
"""
from __future__ import annotations
import argparse, json, math, sys
from pathlib import Path

PROTOCOL = "astral-calibrated-opaque-causal-channel-v29"
CLAIM_CEILING = "LocalDevelopmentCalibratedOpaqueCausalChannel"
RIDGES = (0.001, 0.01, 0.1, 1.0)

def solve(matrix: list[list[float]], vector: list[float]) -> list[float]:
    size = len(vector); augmented = [row[:] + [vector[i]] for i, row in enumerate(matrix)]
    for pivot in range(size):
        row = max(range(pivot, size), key=lambda candidate: abs(augmented[candidate][pivot]))
        if abs(augmented[row][pivot]) < 1e-12: raise ValueError("singular_system")
        augmented[pivot], augmented[row] = augmented[row], augmented[pivot]
        divisor = augmented[pivot][pivot]
        augmented[pivot] = [value / divisor for value in augmented[pivot]]
        for other in range(size):
            if other == pivot: continue
            factor = augmented[other][pivot]
            augmented[other] = [left - factor * right for left, right in zip(augmented[other], augmented[pivot])]
    return [augmented[i][-1] for i in range(size)]

def fit(rows: list[dict], key: str, ridge: float) -> list[float]:
    dimensions = len(rows[0][key]); size = dimensions + 1
    matrix = [[0.0] * size for _ in range(size)]; vector = [0.0] * size
    for row in rows:
        features = [1.0] + [float(value) for value in row[key]]; target = float(row["target"])
        for left in range(size):
            vector[left] += features[left] * target
            for right in range(size): matrix[left][right] += features[left] * features[right]
    for index in range(1, size): matrix[index][index] += ridge
    return solve(matrix, vector)

def predict(weights: list[float], row: dict, key: str) -> float:
    return weights[0] + sum(weight * float(value) for weight, value in zip(weights[1:], row[key]))

def mse(weights: list[float], rows: list[dict], key: str) -> float:
    return sum((predict(weights, row, key) - float(row["target"])) ** 2 for row in rows) / len(rows)

def choose(train: list[dict], tune: list[dict], key: str) -> tuple[float, list[float]]:
    candidates = [(mse(fit(train, key, ridge), tune, key), ridge) for ridge in RIDGES]
    _, ridge = min(candidates, key=lambda item: (item[0], item[1]))
    return ridge, fit(train, key, ridge)

def variance(rows: list[dict]) -> float:
    mean = sum(float(row["target"]) for row in rows) / len(rows)
    return sum((float(row["target"]) - mean) ** 2 for row in rows) / len(rows)

def parse(stream: object) -> list[dict]:
    rows = []
    for line in stream:
        if not line.strip(): continue
        value = json.loads(line)
        if not isinstance(value, dict) or len(value.get("full", [])) != 4 or len(value.get("opaque", [])) != 2 or value.get("finite") is not True:
            raise ValueError("invalid_row")
        rows.append(value)
    if len(rows) != 32: raise ValueError("trial_count")
    return rows

def aggregate(rows: list[dict]) -> dict:
    if [row["trial"] for row in rows] != list(range(32)): raise ValueError("trial_order")
    if [row["split"] for row in rows] != [0] * 16 + [1] * 8 + [2] * 8: raise ValueError("split_order")
    train, tune, assessment = rows[:16], rows[16:24], rows[24:]
    full_ridge, full_weights = choose(train, tune, "full")
    opaque_ridge, opaque_weights = choose(train, tune, "opaque")
    shuffled = [dict(row, full=list(reversed(row["full"]))) for row in train]
    shuffled_ridge, shuffled_weights = choose(shuffled, tune, "full")
    tune_full, tune_opaque, tune_shuffled = mse(full_weights, tune, "full"), mse(opaque_weights, tune, "opaque"), mse(shuffled_weights, tune, "full")
    assessment_full, assessment_opaque, assessment_shuffled = mse(full_weights, assessment, "full"), mse(opaque_weights, assessment, "opaque"), mse(shuffled_weights, assessment, "full")
    target_variance = variance(assessment)
    relative = [value / target_variance if target_variance > 0 else math.inf for value in (assessment_full, assessment_opaque, assessment_shuffled)]
    finite = all(math.isfinite(value) for value in (tune_full, tune_opaque, tune_shuffled, assessment_full, assessment_opaque, assessment_shuffled, target_variance, *relative))
    variance_gate = target_variance >= 1e-8
    utility_gate = finite and variance_gate and relative[0] < 1.0 and relative[1] < 1.0 and relative[0] <= relative[2] and relative[1] <= relative[2]
    classification = "CalibratedOpaqueCausalChannelUtilityObserved" if utility_gate else "CalibratedOpaqueCausalChannelDiagnosticOnly"
    return {"protocol": PROTOCOL, "classification": classification, "claim_ceiling": CLAIM_CEILING, "trial_count": 32, "fit_count": 16, "tune_count": 8, "assessment_count": 8, "full_feature_count": 4, "opaque_feature_count": 2, "ridge_candidates": list(RIDGES), "selected_ridge_full": full_ridge, "selected_ridge_opaque": opaque_ridge, "selected_ridge_shuffled": shuffled_ridge, "target": "direct_held_out_intervention_logit_margin_effect", "prediction_locked_before_assessment": True, "tune_full_mse": tune_full, "tune_opaque_mse": tune_opaque, "tune_shuffled_mse": tune_shuffled, "assessment_full_mse": assessment_full, "assessment_opaque_mse": assessment_opaque, "assessment_shuffled_mse": assessment_shuffled, "assessment_target_variance": target_variance, "assessment_full_relative_mse": relative[0], "assessment_opaque_relative_mse": relative[1], "assessment_shuffled_relative_mse": relative[2], "finite": finite, "variance_gate": variance_gate, "utility_gate": utility_gate, "model_execution": True, "network_access": False, "raw_intermediate_retained": False}

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument("--output", type=Path, required=True); args = parser.parse_args(argv)
    try:
        result = aggregate(parse(sys.stdin)); args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print(f"invalid V29 stream: {type(exc).__name__}:{exc}", file=sys.stderr); return 2
    print(json.dumps({"protocol": PROTOCOL, "classification": result["classification"]}, sort_keys=True), file=sys.stderr)
    return 0 if result["classification"] == "CalibratedOpaqueCausalChannelUtilityObserved" else 3

if __name__ == "__main__": sys.exit(main())
