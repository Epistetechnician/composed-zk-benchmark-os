#!/usr/bin/env python3
"""Independent aggregate-only validator for the information-frontier slice.

State slice: ``continual-learning-information-budget-frontier-v1``.

This validator intentionally checks the report schema, arithmetic, guards,
compute equality, order pairing, and aggregate summary without importing the
experiment runner.  It is not cryptographic verification and it cannot prove
semantic truth outside the exact synthetic generator contract.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any, Mapping, Sequence


STATE_SLICE = "continual-learning-information-budget-frontier-v1"
SCHEMA_VERSION = "continual-learning-information-budget-frontier-result-v1"
ARMS = ("untouched", "fixed_adapter", "cpsp_frontier", "random_projection_control")
SPLITS = ("fit", "tune", "assessment")
RISK_PRICES = (0.25, 0.50, 1.00, 2.00)
ORDER_DIRECTIONS = ("forward", "reverse")
PREREGISTERED_REPLICATE_SEEDS = (20260841, 20260842, 20260843)
PREREGISTERED_ORDER_SEEDS = (6811, 6812, 6813)
UPDATE_BUDGET = 8
MAX_FORGETTING = 0.08
MAX_CALIBRATION_BRIER = 0.20
MAX_ORDER_DELTA = 0.08
ROLLBACK_TOLERANCE = 1e-12
DIMENSION = 6
PROTECTED_SHARD_COUNT = 4
SHARD_COUNTS = {"fit": 8, "tune": 8, "assessment": 8}
CUSTODY_RUN_ROOT = "/Users/shaanp/Documents/research-artifacts/continual-learning-information-budget-frontier-v1-20260829"
ALERT_FORGETTING = 0.03
ALPHA_GRIDS = {
    "grid3": (0.0, 0.5, 1.0),
    "grid5": (0.0, 0.25, 0.5, 0.75, 1.0),
    "grid7": (0.0, 1.0 / 6.0, 2.0 / 6.0, 3.0 / 6.0, 4.0 / 6.0, 5.0 / 6.0, 1.0),
}
CANDIDATES = {
    "grid3_lr032": ("grid3", 0.32),
    "grid5_lr032": ("grid5", 0.32),
    "grid7_lr032": ("grid7", 0.32),
    "grid5_lr024": ("grid5", 0.24),
    "grid5_lr040": ("grid5", 0.40),
}
REVIEW_PACKET_PATH = Path(__file__).resolve().parents[2] / "docs/research/continual-learning/125-information-budget-frontier-v1-independent-review-packet.md"
REVIEW_RECEIPT_SCHEMA_VERSION = "continual-learning-information-budget-frontier-review-receipt-v1"
REVIEW_CHECKS = (
    "mechanism_distinct",
    "estimand_fixed",
    "lock_ordered",
    "assessment_isolated",
    "controls_meaningful",
    "compute_equalized",
    "guards_executable",
    "claim_ceiling_bounded",
    "closed_records_untouched",
    "budget_finite",
)


class ValidationError(ValueError):
    """Raised when an aggregate result violates the frozen contract."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)


def _digest(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    ).hexdigest()


def _unit(*parts: object) -> float:
    payload = "|".join(str(part) for part in parts).encode("utf-8")
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big") / float(1 << 64)


def _signed(*parts: object) -> float:
    return 2.0 * _unit(*parts) - 1.0


def _add(left: Sequence[float], right: Sequence[float]) -> tuple[float, ...]:
    return tuple(a + b for a, b in zip(left, right))


def _sub(left: Sequence[float], right: Sequence[float]) -> tuple[float, ...]:
    return tuple(a - b for a, b in zip(left, right))


def _scale(value: Sequence[float], multiplier: float) -> tuple[float, ...]:
    return tuple(multiplier * item for item in value)


def _dot(left: Sequence[float], right: Sequence[float]) -> float:
    return sum(a * b for a, b in zip(left, right))


def _anchor() -> tuple[float, ...]:
    return tuple(0.42 * math.sin((index + 1) * 1.17) for index in range(DIMENSION))


def _target(seed: int, split: str, kind: str, index: int) -> tuple[float, ...]:
    anchor = _anchor()
    if kind == "protected":
        scale = 0.055 + 0.010 * _unit(STATE_SLICE, seed, split, kind, index, "scale")
    else:
        scale = 0.56 + 0.18 * _unit(STATE_SLICE, seed, split, kind, index, "scale")
    return tuple(
        anchor[component]
        + scale * _signed(STATE_SLICE, seed, split, kind, index, component, "direction")
        for component in range(DIMENSION)
    )


def _targets(seed: int, split: str, kind: str) -> tuple[tuple[float, ...], ...]:
    count = PROTECTED_SHARD_COUNT if kind == "protected" else SHARD_COUNTS[split]
    return tuple(_target(seed, split, kind, index) for index in range(count))


def _ordered(targets: Sequence[tuple[float, ...]], order_seed: int, split: str, kind: str, direction: str) -> tuple[tuple[float, ...], ...]:
    indexed = list(enumerate(targets))
    indexed.sort(key=lambda item: (_unit(STATE_SLICE, "order", order_seed, f"{split}-{kind}-{item[0]:03d}"), item[0]))
    if direction == "reverse":
        indexed.reverse()
    return tuple(item[1] for item in indexed)


def _loss(vector: Sequence[float], target: Sequence[float]) -> float:
    return sum((left - right) ** 2 for left, right in zip(vector, target)) / DIMENSION


def _mean_loss(vector: Sequence[float], targets: Sequence[Sequence[float]]) -> float:
    return sum(_loss(vector, target) for target in targets) / len(targets)


def _basis(vectors: Sequence[Sequence[float]]) -> tuple[tuple[float, ...], ...]:
    basis: list[tuple[float, ...]] = []
    for vector in vectors:
        residual = tuple(float(item) for item in vector)
        for unit_vector in basis:
            residual = _sub(residual, _scale(unit_vector, _dot(residual, unit_vector)))
        norm = math.sqrt(_dot(residual, residual))
        if norm > 1e-12:
            basis.append(_scale(residual, 1.0 / norm))
    return tuple(basis)


def _project_out(vector: Sequence[float], basis: Sequence[Sequence[float]]) -> tuple[float, ...]:
    result = tuple(float(item) for item in vector)
    for unit_vector in basis:
        result = _sub(result, _scale(unit_vector, _dot(result, unit_vector)))
    return result


def _candidate(name: str) -> dict[str, Any]:
    grid_name, learning_rate = CANDIDATES[name]
    return {
        "name": name,
        "alpha_grid_name": grid_name,
        "alpha_grid": ALPHA_GRIDS[grid_name],
        "learning_rate": learning_rate,
    }


def _expected_trial(
    *,
    candidate: Mapping[str, Any],
    arm: str,
    split: str,
    seed: int,
    order_seed: int,
    direction: str,
    risk_price: float,
) -> dict[str, Any]:
    protected_reference = _targets(seed, "fit", "protected")
    protected_evaluation = _targets(seed, split, "protected")
    adaptation = _ordered(_targets(seed, split, "adaptation"), order_seed, split, "adaptation", direction)
    state = _anchor()
    protected_basis = _basis(tuple(_sub(target, state) for target in protected_reference))
    random_basis = _basis(tuple(
        tuple(_signed(STATE_SLICE, "random-basis", seed + order_seed, row, component) for component in range(DIMENSION))
        for row in range(len(protected_basis))
    ))
    update_details: list[tuple[float, float]] = []
    last_before = state
    for target in adaptation:
        raw_delta = _scale(_sub(target, state), candidate["learning_rate"])
        basis = protected_basis if arm == "cpsp_frontier" else random_basis
        projected = _project_out(raw_delta, basis)
        parallel = _sub(raw_delta, projected)
        baseline_adaptation_loss = _loss(state, target)
        baseline_protected_loss = _mean_loss(state, protected_reference)
        choices = []
        for alpha in candidate["alpha_grid"]:
            if arm in ("cpsp_frontier", "random_projection_control"):
                delta = _add(projected, _scale(parallel, alpha))
            elif arm == "fixed_adapter":
                delta = raw_delta
            else:
                delta = tuple(0.0 for _ in raw_delta)
            after = _add(state, delta)
            gain = baseline_adaptation_loss - _loss(after, target)
            forgetting = max(0.0, _mean_loss(after, protected_reference) - baseline_protected_loss)
            choices.append((gain - risk_price * forgetting, alpha, forgetting, delta))
        chosen = choices[-1] if arm in ("untouched", "fixed_adapter") else max(choices, key=lambda item: (item[0], -item[1]))
        _, _, predicted_forgetting, delta = chosen
        if arm == "untouched":
            delta = tuple(0.0 for _ in delta)
        last_before = state
        state = _add(state, delta)
        observed_forgetting = max(0.0, _mean_loss(state, protected_reference) - _mean_loss(last_before, protected_reference))
        update_details.append((predicted_forgetting, observed_forgetting))

    base_adaptation_loss = _mean_loss(_anchor(), _targets(seed, split, "adaptation"))
    final_adaptation_loss = _mean_loss(state, _targets(seed, split, "adaptation"))
    base_protected_loss = _mean_loss(_anchor(), protected_evaluation)
    final_protected_loss = _mean_loss(state, protected_evaluation)
    adaptation_gain = base_adaptation_loss - final_adaptation_loss
    forgetting_value = final_protected_loss - base_protected_loss
    positive_forgetting = max(0.0, forgetting_value)
    calibration_brier = sum(
        (prediction - (1.0 if observed >= ALERT_FORGETTING else 0.0)) ** 2
        for prediction, observed in update_details
    ) / len(update_details)
    last_delta = _sub(state, last_before)
    rollback_state = _sub(state, last_delta)
    rollback_error = max(abs(left - right) for left, right in zip(rollback_state, last_before))
    key = f"{candidate['name']}|{arm}|{split}|{seed}|{order_seed}|{direction}|{risk_price:.2f}"
    payload = {
        "key": key,
        "arm": arm,
        "split": split,
        "seed": seed,
        "order_seed": order_seed,
        "order_direction": direction,
        "risk_price": risk_price,
        "base_adaptation_loss": base_adaptation_loss,
        "final_adaptation_loss": final_adaptation_loss,
        "adaptation_gain": adaptation_gain,
        "base_protected_loss": base_protected_loss,
        "final_protected_loss": final_protected_loss,
        "forgetting_value": forgetting_value,
        "positive_forgetting": positive_forgetting,
        "calibration_brier": calibration_brier,
        "rollback_max_abs_error": rollback_error,
        "update_attempts": len(adaptation),
        "gradient_compute_units": len(adaptation),
        "shadow_compute_units": len(adaptation) * len(candidate["alpha_grid"]),
        "order_pair_delta": 0.0,
    }
    payload.update({
        "forgetting_guard_pass": positive_forgetting <= MAX_FORGETTING,
        "calibration_guard_pass": calibration_brier <= MAX_CALIBRATION_BRIER,
        "rollback_guard_pass": rollback_error <= ROLLBACK_TOLERANCE,
        "compute_guard_pass": True,
        "order_guard_pass": True,
    })
    return payload


def _trial_digest(raw: Mapping[str, Any]) -> str:
    fields = (
        "key", "arm", "split", "seed", "order_seed", "order_direction", "risk_price",
        "base_adaptation_loss", "final_adaptation_loss", "adaptation_gain", "base_protected_loss",
        "final_protected_loss", "forgetting_value", "positive_forgetting", "calibration_brier",
        "rollback_max_abs_error", "update_attempts", "gradient_compute_units", "shadow_compute_units",
        "order_pair_delta",
    )
    return _digest({field: raw[field] for field in fields})


def _validate_review_receipt(path: Path) -> tuple[str, str]:
    resolved = path.resolve()
    _require(resolved.parent.name == "continual-learning", "review receipt path")
    _require(resolved.suffix == ".json", "review receipt format")
    payload = json.loads(resolved.read_text(encoding="utf-8"))
    _require(payload.get("schema_version") == REVIEW_RECEIPT_SCHEMA_VERSION, "review receipt schema")
    _require(payload.get("state_slice") == STATE_SLICE, "review receipt state slice")
    _require(payload.get("review_packet_path") == str(REVIEW_PACKET_PATH), "review receipt packet path")
    packet_digest = hashlib.sha256(REVIEW_PACKET_PATH.read_bytes()).hexdigest()
    _require(payload.get("review_packet_sha256") == packet_digest, "review receipt packet digest")
    _require(payload.get("reviewer_role") == "independent", "reviewer role")
    _require(payload.get("disposition") == "APPROVED_FOR_SYNTHETIC_RUN", "review disposition")
    _require(payload.get("blocking_defects") == [], "review blocking defects")
    checks = payload.get("checks")
    _require(isinstance(checks, Mapping) and tuple(sorted(checks)) == tuple(sorted(REVIEW_CHECKS)), "review check coverage")
    _require(all(checks[item] == "PASS" for item in REVIEW_CHECKS), "review checks")
    return hashlib.sha256(resolved.read_bytes()).hexdigest(), packet_digest


def _validate_lock(path: Path, candidate: Mapping[str, Any]) -> str:
    resolved = path.resolve()
    _require(resolved.parent == Path(CUSTODY_RUN_ROOT).resolve(), "lock path")
    _require(resolved.exists(), "lock missing")
    payload = json.loads(resolved.read_text(encoding="utf-8"))
    _require(payload.get("state_slice") == STATE_SLICE, "lock state slice")
    _require(payload.get("lock_type") == "fit_tune_prediction_lock", "lock type")
    observed_candidate = dict(payload.get("candidate", {}))
    observed_candidate["alpha_grid"] = tuple(observed_candidate.get("alpha_grid", ()))
    _require(observed_candidate == dict(candidate), "lock candidate")
    _require(payload.get("selection_metric") == "adaptation_forgetting_frontier_utility", "lock metric")
    _require(payload.get("selection_split") == "tune", "lock split")
    review_path = Path(str(payload.get("review_receipt_path", ""))).resolve()
    review_digest, packet_digest = _validate_review_receipt(review_path)
    _require(payload.get("review_packet_path") == str(REVIEW_PACKET_PATH), "lock packet path")
    _require(payload.get("review_packet_sha256") == packet_digest, "lock packet digest")
    _require(payload.get("review_receipt_sha256") == review_digest, "lock receipt digest")
    fit_tune_path = Path(str(payload.get("fit_tune_result_path", ""))).resolve()
    expected_parent = (Path(CUSTODY_RUN_ROOT) / "candidates").resolve()
    _require(fit_tune_path.parent == expected_parent, "lock fit/tune path")
    _require(fit_tune_path.exists(), "lock fit/tune artifact")
    _require(payload.get("fit_tune_result_sha256") == hashlib.sha256(fit_tune_path.read_bytes()).hexdigest(), "lock fit/tune digest")
    fit_tune_result = json.loads(fit_tune_path.read_text(encoding="utf-8"))
    validate_result(fit_tune_result)
    fit_candidate = dict(fit_tune_result.get("candidate", {}))
    fit_candidate["alpha_grid"] = tuple(fit_candidate.get("alpha_grid", ()))
    _require(fit_candidate == dict(candidate), "lock fit/tune candidate")
    splits = {raw.get("split") for raw in fit_tune_result.get("trials", []) if isinstance(raw, Mapping)}
    _require(splits == {"fit", "tune"}, "lock fit/tune split identity")
    locked_value = fit_tune_result["summary"]["by_split_arm"]["tune:cpsp_frontier"]["adaptation_forgetting_frontier_utility"]
    _require(math.isclose(float(payload.get("selected_value")), locked_value, rel_tol=0.0, abs_tol=1e-12), "lock selected value")
    candidate_order = tuple(payload.get("candidate_order", ()))
    _require(candidate_order == tuple(CANDIDATES)[: len(candidate_order)], "lock candidate order")
    _require(candidate["name"] in candidate_order, "lock candidate order membership")
    return hashlib.sha256(resolved.read_bytes()).hexdigest()


def _validate_numeric(raw: Mapping[str, Any], field: str) -> None:
    value = raw.get(field)
    _require(isinstance(value, (int, float)) and not isinstance(value, bool), f"{field} must be numeric")
    _require(math.isfinite(float(value)), f"{field} must be finite")


def _validate_trial(raw: Mapping[str, Any], expected: Mapping[str, Any]) -> None:
    required = (
        "key", "arm", "split", "seed", "order_seed", "order_direction", "risk_price",
        "base_adaptation_loss", "final_adaptation_loss", "adaptation_gain", "base_protected_loss",
        "final_protected_loss", "forgetting_value", "positive_forgetting", "calibration_brier",
        "rollback_max_abs_error", "update_attempts", "gradient_compute_units", "shadow_compute_units",
        "order_pair_delta", "forgetting_guard_pass", "calibration_guard_pass", "rollback_guard_pass",
        "compute_guard_pass", "order_guard_pass", "trial_digest",
    )
    for field in required:
        _require(field in raw, f"missing trial field: {field}")
    _require(raw["arm"] in ARMS, "unknown arm")
    _require(raw["split"] in SPLITS, "unknown split")
    _require(raw["order_direction"] in ORDER_DIRECTIONS, "unknown order direction")
    _require(raw["seed"] in PREREGISTERED_REPLICATE_SEEDS, "seed not preregistered")
    _require(raw["order_seed"] in PREREGISTERED_ORDER_SEEDS, "order seed not preregistered")
    _require(raw["risk_price"] in RISK_PRICES, "risk price not preregistered")
    numeric_fields = (
        "risk_price", "base_adaptation_loss", "final_adaptation_loss", "adaptation_gain",
        "base_protected_loss", "final_protected_loss", "forgetting_value", "positive_forgetting",
        "calibration_brier", "rollback_max_abs_error", "order_pair_delta",
    )
    for field in numeric_fields:
        _validate_numeric(raw, field)
    _require(math.isclose(raw["adaptation_gain"], raw["base_adaptation_loss"] - raw["final_adaptation_loss"], abs_tol=1e-12), "adaptation arithmetic")
    _require(math.isclose(raw["forgetting_value"], raw["final_protected_loss"] - raw["base_protected_loss"], abs_tol=1e-12), "forgetting arithmetic")
    _require(math.isclose(raw["positive_forgetting"], max(0.0, raw["forgetting_value"]), abs_tol=1e-12), "positive forgetting arithmetic")
    _require(raw["update_attempts"] == UPDATE_BUDGET, "update budget drift")
    _require(raw["gradient_compute_units"] == UPDATE_BUDGET, "gradient compute drift")
    _require(raw["shadow_compute_units"] > 0, "shadow compute absent")
    _require(raw["compute_guard_pass"] is True, "compute guard false")
    _require(raw["forgetting_guard_pass"] == (raw["positive_forgetting"] <= MAX_FORGETTING), "forgetting guard arithmetic")
    _require(raw["calibration_guard_pass"] == (raw["calibration_brier"] <= MAX_CALIBRATION_BRIER), "calibration guard arithmetic")
    _require(raw["rollback_guard_pass"] == (raw["rollback_max_abs_error"] <= ROLLBACK_TOLERANCE), "rollback guard arithmetic")
    _require(raw["order_guard_pass"] == (raw["order_pair_delta"] <= MAX_ORDER_DELTA), "order guard arithmetic")
    digest_fields = (
        "key", "arm", "split", "seed", "order_seed", "order_direction", "risk_price",
        "base_adaptation_loss", "final_adaptation_loss", "adaptation_gain", "base_protected_loss",
        "final_protected_loss", "forgetting_value", "positive_forgetting", "calibration_brier",
        "rollback_max_abs_error", "update_attempts", "gradient_compute_units", "shadow_compute_units",
        "order_pair_delta",
    )
    _require(raw["trial_digest"] == _digest({field: raw[field] for field in digest_fields}), "trial digest")
    for field in required:
        if field == "trial_digest":
            continue
        if isinstance(expected[field], float):
            _require(math.isclose(raw[field], expected[field], rel_tol=0.0, abs_tol=1e-12), f"synthetic recomputation mismatch: {field}")
        else:
            _require(raw[field] == expected[field], f"synthetic recomputation mismatch: {field}")
    _require(raw["trial_digest"] == _trial_digest(expected), "recomputed trial digest")


def _summary(trials: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {"by_split_arm": {}}
    for split in SPLITS:
        for arm in ARMS:
            rows = [item for item in trials if item["split"] == split and item["arm"] == arm]
            if not rows:
                continue
            by_price = {}
            for price in RISK_PRICES:
                price_rows = [item for item in rows if item["risk_price"] == price]
                by_price[f"{price:.2f}"] = {
                    "adaptation_gain": sum(item["adaptation_gain"] for item in price_rows) / len(price_rows),
                    "positive_forgetting": sum(item["positive_forgetting"] for item in price_rows) / len(price_rows),
                    "calibration_brier": sum(item["calibration_brier"] for item in price_rows) / len(price_rows),
                    "order_pair_delta": max(item["order_pair_delta"] for item in price_rows),
                }
            utility = sum(item["adaptation_gain"] - item["risk_price"] * item["positive_forgetting"] for item in rows) / len(rows)
            result["by_split_arm"][f"{split}:{arm}"] = {
                "adaptation_forgetting_frontier_utility": utility,
                "mean_adaptation_gain": sum(item["adaptation_gain"] for item in rows) / len(rows),
                "mean_positive_forgetting": sum(item["positive_forgetting"] for item in rows) / len(rows),
                "max_positive_forgetting": max(item["positive_forgetting"] for item in rows),
                "max_calibration_brier": max(item["calibration_brier"] for item in rows),
                "max_order_pair_delta": max(item["order_pair_delta"] for item in rows),
                "all_hard_guards_pass": all(
                    item["forgetting_guard_pass"]
                    and item["calibration_guard_pass"]
                    and item["rollback_guard_pass"]
                    and item["compute_guard_pass"]
                    and item["order_guard_pass"]
                    for item in rows
                ),
                "by_risk_price": by_price,
            }
    return result


def validate_result(result: Mapping[str, Any]) -> None:
    _require(result.get("schema_version") == SCHEMA_VERSION, "schema version")
    _require(result.get("state_slice") == STATE_SLICE, "state slice")
    candidate = result.get("candidate")
    _require(isinstance(candidate, Mapping), "candidate")
    candidate_name = candidate.get("name")
    _require(candidate_name in CANDIDATES, "candidate lock")
    expected_candidate = _candidate(str(candidate_name))
    observed_candidate = dict(candidate)
    observed_candidate["alpha_grid"] = tuple(observed_candidate.get("alpha_grid", ()))
    _require(observed_candidate == expected_candidate, "candidate configuration")
    protocol = result.get("protocol")
    _require(isinstance(protocol, Mapping), "protocol")
    _require(tuple(protocol.get("arms", ())) == ARMS, "arms")
    _require(tuple(protocol.get("splits", ())) == SPLITS, "splits")
    _require(tuple(protocol.get("risk_prices", ())) == RISK_PRICES, "risk prices")
    _require(tuple(protocol.get("replicate_seeds", ())) == PREREGISTERED_REPLICATE_SEEDS, "replicate seeds")
    _require(tuple(protocol.get("order_seeds", ())) == PREREGISTERED_ORDER_SEEDS, "order seeds")
    _require(protocol.get("custody_root") == CUSTODY_RUN_ROOT, "custody root")
    trials = result.get("trials")
    _require(isinstance(trials, list) and trials, "trials")
    observed_splits = tuple(dict.fromkeys(trial.get("split") for trial in trials if isinstance(trial, Mapping)))
    _require(all(split in SPLITS for split in observed_splits), "unknown observed split")
    expected_keys = set()
    expected_trials: dict[str, dict[str, Any]] = {}
    for split in observed_splits:
        for seed in PREREGISTERED_REPLICATE_SEEDS:
            for order_seed in PREREGISTERED_ORDER_SEEDS:
                for direction in ORDER_DIRECTIONS:
                    for arm in ARMS:
                        for risk_price in RISK_PRICES:
                            expected = _expected_trial(
                                candidate=expected_candidate,
                                arm=arm,
                                split=split,
                                seed=seed,
                                order_seed=order_seed,
                                direction=direction,
                                risk_price=risk_price,
                            )
                            expected_keys.add(expected["key"])
                            expected_trials[expected["key"]] = expected
    _require(len(trials) == len(expected_keys), "incomplete or duplicate trial coverage")
    observed_keys = [trial.get("key") for trial in trials if isinstance(trial, Mapping)]
    _require(len(set(observed_keys)) == len(observed_keys), "duplicate trial key")
    _require(set(observed_keys) == expected_keys, "trial coverage mismatch")
    grouped: dict[tuple[str, str, int, int, float], dict[str, dict[str, Any]]] = {}
    for expected in expected_trials.values():
        grouped.setdefault((expected["arm"], expected["split"], expected["seed"], expected["order_seed"], expected["risk_price"]), {})[expected["order_direction"]] = expected
    for pair in grouped.values():
        forward = pair["forward"]
        reverse = pair["reverse"]
        delta = max(
            abs(forward["adaptation_gain"] - reverse["adaptation_gain"]),
            abs(forward["positive_forgetting"] - reverse["positive_forgetting"]),
            abs(
                (forward["adaptation_gain"] - forward["risk_price"] * forward["positive_forgetting"])
                - (reverse["adaptation_gain"] - reverse["risk_price"] * reverse["positive_forgetting"])
            ),
        )
        for expected in pair.values():
            expected["order_pair_delta"] = delta
            expected["order_guard_pass"] = delta <= MAX_ORDER_DELTA
            expected["trial_digest"] = _trial_digest(expected)
    for trial in trials:
        _require(isinstance(trial, Mapping), "trial object")
        _validate_trial(trial, expected_trials[trial["key"]])
    if "assessment" in observed_splits:
        review_path = Path(str(protocol.get("review_receipt_path", ""))).resolve()
        lock_path = Path(str(protocol.get("prediction_lock_path", ""))).resolve()
        review_digest, packet_digest = _validate_review_receipt(review_path)
        _require(protocol.get("review_receipt_sha256") == review_digest, "assessment review receipt digest")
        _require(protocol.get("review_packet_sha256") == packet_digest, "assessment packet digest")
        _require(protocol.get("prediction_lock_sha256") == _validate_lock(lock_path, expected_candidate), "assessment prediction lock digest")
        _require(protocol.get("review_receipt_path") == str(review_path), "assessment review receipt path")
        _require(protocol.get("prediction_lock_path") == str(lock_path), "assessment prediction lock path")
    _require(result.get("summary") == _summary(trials), "summary")


def validate_file(path: Path) -> None:
    with path.open("r", encoding="utf-8") as handle:
        result = json.load(handle)
    validate_result(result)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("result", type=Path)
    args = parser.parse_args()
    validate_file(args.result)
    print(json.dumps({"validated": str(args.result), "state_slice": STATE_SLICE}, sort_keys=True))


if __name__ == "__main__":
    main()
