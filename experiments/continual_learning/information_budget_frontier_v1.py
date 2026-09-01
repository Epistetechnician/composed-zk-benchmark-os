#!/usr/bin/env python3
"""Exact synthetic adaptation-forgetting frontier experiment.

State slice: ``continual-learning-information-budget-frontier-v1``.

This module implements a model-free learner with a materially new mechanism
relative to the closed plasticity-recovery family: counterfactual
protected-subspace projection (CPSP).  Each candidate update is decomposed
into a component aligned with protected-task gradients and a component in the
protected-task null space.  A fixed, predeclared risk price selects the
largest mixture on a finite grid using only a shadow counterfactual.

The primary estimand is adaptation-forgetting frontier utility (AFFU):

    mean_lambda(adaptation_gain - lambda * positive_forgetting)

over four preregistered risk prices.  This directly measures the tradeoff
instead of hiding it behind a single forgetting threshold.  The learner is
exact and synthetic; it does not load a model, update weights, or produce
cryptographic evidence.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


STATE_SLICE = "continual-learning-information-budget-frontier-v1"
SCHEMA_VERSION = "continual-learning-information-budget-frontier-result-v1"
PRIMARY_ENDPOINT = "adaptation_forgetting_frontier_utility"
CUSTODY_RUN_ROOT = Path("/Users/shaanp/Documents/research-artifacts/continual-learning-information-budget-frontier-v1-20260829")
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
ARMS = ("untouched", "fixed_adapter", "cpsp_frontier", "random_projection_control")
SPLITS = ("fit", "tune", "assessment")
ORDER_DIRECTIONS = ("forward", "reverse")
RISK_PRICES = (0.25, 0.50, 1.00, 2.00)
ALPHA_GRIDS = {
    "grid3": (0.0, 0.5, 1.0),
    "grid5": (0.0, 0.25, 0.5, 0.75, 1.0),
    "grid7": (0.0, 1.0 / 6.0, 2.0 / 6.0, 3.0 / 6.0, 4.0 / 6.0, 5.0 / 6.0, 1.0),
}
PREDECLARED_CANDIDATES = (
    {"name": "grid3_lr032", "alpha_grid": "grid3", "learning_rate": 0.32},
    {"name": "grid5_lr032", "alpha_grid": "grid5", "learning_rate": 0.32},
    {"name": "grid7_lr032", "alpha_grid": "grid7", "learning_rate": 0.32},
    {"name": "grid5_lr024", "alpha_grid": "grid5", "learning_rate": 0.24},
    {"name": "grid5_lr040", "alpha_grid": "grid5", "learning_rate": 0.40},
)
PREREGISTERED_REPLICATE_SEEDS = (20260841, 20260842, 20260843)
PREREGISTERED_ORDER_SEEDS = (6811, 6812, 6813)
DIMENSION = 6
PROTECTED_SHARD_COUNT = 4
SHARD_COUNTS = {"fit": 8, "tune": 8, "assessment": 8}
UPDATE_BUDGET = SHARD_COUNTS["assessment"]
MAX_FORGETTING = 0.08
MAX_CALIBRATION_BRIER = 0.20
MAX_ORDER_DELTA = 0.08
ROLLBACK_TOLERANCE = 1e-12
ALERT_FORGETTING = 0.03


class ProtocolError(ValueError):
    """Raised when a frozen information-frontier contract is violated."""


@dataclass(frozen=True)
class CandidateConfig:
    name: str
    alpha_grid_name: str
    alpha_grid: tuple[float, ...]
    learning_rate: float


@dataclass(frozen=True)
class Shard:
    shard_id: str
    split: str
    kind: str
    index: int
    target: tuple[float, ...]
    payload_sha256: str


@dataclass(frozen=True)
class UpdateRecord:
    shard_id: str
    committed: bool
    alpha: float
    predicted_forgetting: float
    observed_shadow_forgetting: float
    before: tuple[float, ...]
    after: tuple[float, ...]
    update_sha256: str


@dataclass(frozen=True)
class Trial:
    key: str
    arm: str
    split: str
    seed: int
    order_seed: int
    order_direction: str
    risk_price: float
    base_adaptation_loss: float
    final_adaptation_loss: float
    adaptation_gain: float
    base_protected_loss: float
    final_protected_loss: float
    forgetting_value: float
    positive_forgetting: float
    calibration_brier: float
    rollback_max_abs_error: float
    update_attempts: int
    gradient_compute_units: int
    shadow_compute_units: int
    order_pair_delta: float
    forgetting_guard_pass: bool
    calibration_guard_pass: bool
    rollback_guard_pass: bool
    compute_guard_pass: bool
    order_guard_pass: bool
    trial_digest: str


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ProtocolError(message)


def _digest(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    ).hexdigest()


def _unit(*parts: object) -> float:
    payload = "|".join(str(part) for part in parts).encode("utf-8")
    integer = int.from_bytes(hashlib.sha256(payload).digest()[:8], "big")
    return integer / float(1 << 64)


def _signed(*parts: object) -> float:
    return 2.0 * _unit(*parts) - 1.0


def _clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))


def _dot(left: Sequence[float], right: Sequence[float]) -> float:
    return sum(a * b for a, b in zip(left, right))


def _sub(left: Sequence[float], right: Sequence[float]) -> tuple[float, ...]:
    return tuple(a - b for a, b in zip(left, right))


def _add(left: Sequence[float], right: Sequence[float]) -> tuple[float, ...]:
    return tuple(a + b for a, b in zip(left, right))


def _scale(value: Sequence[float], multiplier: float) -> tuple[float, ...]:
    return tuple(multiplier * item for item in value)


def _anchor() -> tuple[float, ...]:
    return tuple(0.42 * math.sin((index + 1) * 1.17) for index in range(DIMENSION))


def _target(seed: int, split: str, kind: str, index: int) -> tuple[float, ...]:
    _require(split in SPLITS, f"unknown split: {split}")
    _require(kind in ("protected", "adaptation"), f"unknown shard kind: {kind}")
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


def _shards(seed: int, split: str, kind: str) -> tuple[Shard, ...]:
    count = PROTECTED_SHARD_COUNT if kind == "protected" else SHARD_COUNTS[split]
    result = []
    for index in range(count):
        target = _target(seed, split, kind, index)
        shard_id = f"{split}-{kind}-{index:03d}"
        result.append(
            Shard(
                shard_id=shard_id,
                split=split,
                kind=kind,
                index=index,
                target=target,
                payload_sha256=_digest({"shard_id": shard_id, "target": target}),
            )
        )
    return tuple(result)


def _ordered(shards: Iterable[Shard], order_seed: int, direction: str) -> tuple[Shard, ...]:
    _require(direction in ORDER_DIRECTIONS, f"unknown order direction: {direction}")
    ordered = sorted(shards, key=lambda item: (_unit(STATE_SLICE, "order", order_seed, item.shard_id), item.index))
    return tuple(ordered if direction == "forward" else reversed(ordered))


def _loss(vector: Sequence[float], target: Sequence[float]) -> float:
    return sum((left - right) ** 2 for left, right in zip(vector, target)) / DIMENSION


def _mean_loss(vector: Sequence[float], shards: Sequence[Shard]) -> float:
    _require(shards, "loss requires non-empty shards")
    return sum(_loss(vector, shard.target) for shard in shards) / len(shards)


def _orthonormal_basis(vectors: Sequence[Sequence[float]]) -> tuple[tuple[float, ...], ...]:
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


def _random_basis(seed: int, count: int) -> tuple[tuple[float, ...], ...]:
    vectors = tuple(
        tuple(_signed(STATE_SLICE, "random-basis", seed, row, component) for component in range(DIMENSION))
        for row in range(count)
    )
    return _orthonormal_basis(vectors)


def candidate_config(name: str) -> CandidateConfig:
    for raw in PREDECLARED_CANDIDATES:
        if raw["name"] == name:
            return CandidateConfig(
                name=name,
                alpha_grid_name=raw["alpha_grid"],
                alpha_grid=ALPHA_GRIDS[raw["alpha_grid"]],
                learning_rate=float(raw["learning_rate"]),
            )
    raise ProtocolError(f"unknown candidate: {name}")


def _validate_candidate(config: CandidateConfig) -> None:
    _require(config.name in {item["name"] for item in PREDECLARED_CANDIDATES}, "candidate is not preregistered")
    _require(config.alpha_grid == ALPHA_GRIDS[config.alpha_grid_name], "alpha grid drift")
    _require(config.alpha_grid[0] == 0.0 and config.alpha_grid[-1] == 1.0, "alpha grid endpoints required")
    _require(all(0.0 <= value <= 1.0 for value in config.alpha_grid), "alpha grid bounds")
    _require(config.learning_rate > 0.0, "learning rate must be positive")


def _shadow_choice(
    *,
    arm: str,
    state: Sequence[float],
    raw_delta: Sequence[float],
    protected_basis: Sequence[Sequence[float]],
    protected_reference: Sequence[Shard],
    target: Sequence[float],
    risk_price: float,
    config: CandidateConfig,
    random_basis: Sequence[Sequence[float]],
) -> tuple[float, tuple[float, ...], float, float]:
    projected = _project_out(raw_delta, protected_basis if arm == "cpsp_frontier" else random_basis)
    parallel = _sub(raw_delta, projected)
    baseline_adaptation_loss = _loss(state, target)
    baseline_protected_loss = _mean_loss(state, protected_reference)
    choices: list[tuple[float, float, float, tuple[float, ...]]] = []
    for alpha in config.alpha_grid:
        if arm in ("cpsp_frontier", "random_projection_control"):
            delta = _add(projected, _scale(parallel, alpha))
        elif arm == "fixed_adapter":
            delta = raw_delta
        else:
            delta = tuple(0.0 for _ in raw_delta)
        after = _add(state, delta)
        adaptation_gain = baseline_adaptation_loss - _loss(after, target)
        positive_forgetting = max(0.0, _mean_loss(after, protected_reference) - baseline_protected_loss)
        objective = adaptation_gain - risk_price * positive_forgetting
        choices.append((objective, alpha, positive_forgetting, delta))
    if arm in ("untouched", "fixed_adapter"):
        chosen = choices[-1]
    else:
        chosen = max(choices, key=lambda item: (item[0], -item[1]))
    _, alpha, predicted_forgetting, delta = chosen
    return alpha, delta, predicted_forgetting, len(choices)


def _validate_review_receipt(path: Path) -> str:
    resolved = path.resolve()
    _require(resolved.parent.name == "continual-learning", "review receipt must be in continual-learning docs")
    _require(resolved.suffix == ".json", "review receipt must be structured JSON")
    payload = json.loads(resolved.read_text(encoding="utf-8"))
    _require(payload.get("schema_version") == REVIEW_RECEIPT_SCHEMA_VERSION, "review receipt schema mismatch")
    _require(payload.get("state_slice") == STATE_SLICE, "review receipt state slice mismatch")
    _require(payload.get("review_packet_path") == str(REVIEW_PACKET_PATH), "review receipt packet identity mismatch")
    _require(payload.get("review_packet_sha256") == hashlib.sha256(REVIEW_PACKET_PATH.read_bytes()).hexdigest(), "review packet digest mismatch")
    _require(payload.get("reviewer_role") == "independent", "reviewer role is not independent")
    _require(payload.get("disposition") == "APPROVED_FOR_SYNTHETIC_RUN", "review receipt is not approved")
    _require(payload.get("blocking_defects") == [], "review receipt has blocking defects")
    checks = payload.get("checks")
    _require(isinstance(checks, Mapping) and tuple(sorted(checks)) == tuple(sorted(REVIEW_CHECKS)), "review checks incomplete")
    _require(all(checks[item] == "PASS" for item in REVIEW_CHECKS), "review checks not all passing")
    return hashlib.sha256(resolved.read_bytes()).hexdigest()


def _validate_prediction_lock(path: Path, config: CandidateConfig) -> str:
    resolved_lock = path.resolve()
    _require(resolved_lock.parent == CUSTODY_RUN_ROOT.resolve(), "prediction lock path")
    _require(resolved_lock.exists(), "prediction lock missing")
    payload = json.loads(resolved_lock.read_text(encoding="utf-8"))
    _require(payload.get("state_slice") == STATE_SLICE, "prediction lock state slice mismatch")
    _require(payload.get("lock_type") == "fit_tune_prediction_lock", "prediction lock type mismatch")
    candidate = payload.get("candidate")
    _require(isinstance(candidate, Mapping), "prediction lock candidate missing")
    observed_candidate = dict(candidate)
    observed_candidate["alpha_grid"] = tuple(observed_candidate.get("alpha_grid", ()))
    _require(observed_candidate == asdict(config), "prediction lock candidate mismatch")
    _require(payload.get("selection_split") == "tune", "prediction lock split mismatch")
    review_path = Path(str(payload.get("review_receipt_path", ""))).resolve()
    _require(review_path.parent.name == "continual-learning", "prediction lock review path")
    _require(payload.get("review_packet_path") == str(REVIEW_PACKET_PATH), "prediction lock packet identity")
    review_digest = _validate_review_receipt(review_path)
    _require(payload.get("review_receipt_sha256") == review_digest, "prediction lock review digest")
    _require(payload.get("review_packet_sha256") == hashlib.sha256(REVIEW_PACKET_PATH.read_bytes()).hexdigest(), "prediction lock packet digest")
    fit_tune_path = Path(str(payload.get("fit_tune_result_path", ""))).resolve()
    _require(fit_tune_path.parent == (CUSTODY_RUN_ROOT / "candidates").resolve(), "prediction lock fit/tune path")
    _require(fit_tune_path.exists(), "prediction lock fit/tune artifact missing")
    _require(payload.get("fit_tune_result_sha256") == hashlib.sha256(fit_tune_path.read_bytes()).hexdigest(), "prediction lock fit/tune digest")
    fit_tune_result = json.loads(fit_tune_path.read_text(encoding="utf-8"))
    validate_result(fit_tune_result)
    fit_candidate = dict(fit_tune_result.get("candidate", {}))
    fit_candidate["alpha_grid"] = tuple(fit_candidate.get("alpha_grid", ()))
    _require(fit_candidate == asdict(config), "prediction lock fit/tune candidate mismatch")
    observed_splits = {raw.get("split") for raw in fit_tune_result.get("trials", []) if isinstance(raw, Mapping)}
    _require(observed_splits == {"fit", "tune"}, "prediction lock fit/tune split identity")
    candidate_order = tuple(payload.get("candidate_order", ()))
    _require(config.name in candidate_order, "prediction lock candidate order mismatch")
    selected_value = payload.get("selected_value")
    locked_value = fit_tune_result["summary"]["by_split_arm"]["tune:cpsp_frontier"][PRIMARY_ENDPOINT]
    _require(isinstance(selected_value, (int, float)) and math.isclose(float(selected_value), locked_value, rel_tol=0.0, abs_tol=1e-12), "prediction lock selected value mismatch")
    return hashlib.sha256(resolved_lock.read_bytes()).hexdigest()


def run_trial(
    *,
    arm: str,
    split: str,
    seed: int,
    order_seed: int,
    order_direction: str,
    risk_price: float,
    config: CandidateConfig,
) -> Trial:
    _require(arm in ARMS, f"unknown arm: {arm}")
    _require(split in SPLITS, f"unknown split: {split}")
    _require(order_direction in ORDER_DIRECTIONS, f"unknown order direction: {order_direction}")
    _require(risk_price in RISK_PRICES, "risk price is not preregistered")
    _validate_candidate(config)

    protected_reference = _shards(seed, "fit", "protected")
    protected_evaluation = _shards(seed, split, "protected")
    adaptation = _ordered(_shards(seed, split, "adaptation"), order_seed, order_direction)
    state = _anchor()
    updates: list[UpdateRecord] = []
    random_basis = _random_basis(seed + order_seed, len(_orthonormal_basis(tuple(_sub(item.target, state) for item in protected_reference))))
    protected_basis = _orthonormal_basis(tuple(_sub(item.target, state) for item in protected_reference))
    for shard in adaptation:
        raw_delta = _scale(_sub(shard.target, state), config.learning_rate)
        alpha, delta, predicted_forgetting, shadow_count = _shadow_choice(
            arm=arm,
            state=state,
            raw_delta=raw_delta,
            protected_basis=protected_basis,
            protected_reference=protected_reference,
            target=shard.target,
            risk_price=risk_price,
            config=config,
            random_basis=random_basis,
        )
        before = state
        if arm == "untouched":
            delta = tuple(0.0 for _ in delta)
        state = _add(state, delta)
        observed_shadow_forgetting = max(
            0.0,
            _mean_loss(state, protected_reference) - _mean_loss(before, protected_reference),
        )
        updates.append(
            UpdateRecord(
                shard_id=shard.shard_id,
                committed=any(abs(item) > 0.0 for item in delta),
                alpha=alpha,
                predicted_forgetting=predicted_forgetting,
                observed_shadow_forgetting=observed_shadow_forgetting,
                before=before,
                after=state,
                update_sha256=_digest({"shard_id": shard.shard_id, "before": before, "after": state}),
            )
        )
        _require(shadow_count == len(config.alpha_grid), "shadow count mismatch")

    base_adaptation_loss = _mean_loss(_anchor(), _shards(seed, split, "adaptation"))
    final_adaptation_loss = _mean_loss(state, _shards(seed, split, "adaptation"))
    base_protected_loss = _mean_loss(_anchor(), protected_evaluation)
    final_protected_loss = _mean_loss(state, protected_evaluation)
    adaptation_gain = base_adaptation_loss - final_adaptation_loss
    forgetting_value = final_protected_loss - base_protected_loss
    positive_forgetting = max(0.0, forgetting_value)
    predictions = [item.predicted_forgetting for item in updates]
    outcomes = [1.0 if item.observed_shadow_forgetting >= ALERT_FORGETTING else 0.0 for item in updates]
    calibration_brier = sum((prediction - outcome) ** 2 for prediction, outcome in zip(predictions, outcomes)) / len(updates)

    last_before = updates[-1].before if updates else state
    last_after = updates[-1].after if updates else state
    last_delta = _sub(last_after, last_before)
    rollback_state = _sub(state, last_delta)
    rollback_max_abs_error = max(abs(left - right) for left, right in zip(rollback_state, last_before)) if updates else 0.0
    expected_compute = len(adaptation)
    expected_shadow = len(adaptation) * len(config.alpha_grid)
    order_pair_delta = 0.0
    key = f"{config.name}|{arm}|{split}|{seed}|{order_seed}|{order_direction}|{risk_price:.2f}"
    trial_payload = {
        "key": key,
        "arm": arm,
        "split": split,
        "seed": seed,
        "order_seed": order_seed,
        "order_direction": order_direction,
        "risk_price": risk_price,
        "base_adaptation_loss": base_adaptation_loss,
        "final_adaptation_loss": final_adaptation_loss,
        "adaptation_gain": adaptation_gain,
        "base_protected_loss": base_protected_loss,
        "final_protected_loss": final_protected_loss,
        "forgetting_value": forgetting_value,
        "positive_forgetting": positive_forgetting,
        "calibration_brier": calibration_brier,
        "rollback_max_abs_error": rollback_max_abs_error,
        "update_attempts": len(adaptation),
        "gradient_compute_units": expected_compute,
        "shadow_compute_units": expected_shadow,
        "order_pair_delta": order_pair_delta,
    }
    return Trial(
        **trial_payload,
        forgetting_guard_pass=positive_forgetting <= MAX_FORGETTING,
        calibration_guard_pass=calibration_brier <= MAX_CALIBRATION_BRIER,
        rollback_guard_pass=rollback_max_abs_error <= ROLLBACK_TOLERANCE,
        compute_guard_pass=(expected_compute == UPDATE_BUDGET and expected_shadow == UPDATE_BUDGET * len(config.alpha_grid)),
        order_guard_pass=order_pair_delta <= MAX_ORDER_DELTA,
        trial_digest=_digest(trial_payload),
    )


def _replace_order_pair(trials: list[Trial]) -> list[Trial]:
    grouped: dict[tuple[str, str, int, int, float], list[Trial]] = {}
    for trial in trials:
        grouped.setdefault((trial.arm, trial.split, trial.seed, trial.order_seed, trial.risk_price), []).append(trial)
    result: list[Trial] = []
    for group in grouped.values():
        forward = next((item for item in group if item.order_direction == "forward"), None)
        reverse = next((item for item in group if item.order_direction == "reverse"), None)
        if forward and reverse:
            delta = max(
                abs(forward.adaptation_gain - reverse.adaptation_gain),
                abs(forward.positive_forgetting - reverse.positive_forgetting),
                abs(
                    (forward.adaptation_gain - forward.risk_price * forward.positive_forgetting)
                    - (reverse.adaptation_gain - reverse.risk_price * reverse.positive_forgetting)
                ),
            )
        else:
            delta = float("inf")
        for trial in group:
            payload = {**asdict(trial), "order_pair_delta": delta}
            digest_fields = (
                "key", "arm", "split", "seed", "order_seed", "order_direction", "risk_price",
                "base_adaptation_loss", "final_adaptation_loss", "adaptation_gain", "base_protected_loss",
                "final_protected_loss", "forgetting_value", "positive_forgetting", "calibration_brier",
                "rollback_max_abs_error", "update_attempts", "gradient_compute_units", "shadow_compute_units",
                "order_pair_delta",
            )
            payload["order_guard_pass"] = delta <= MAX_ORDER_DELTA
            payload["trial_digest"] = _digest({field: payload[field] for field in digest_fields})
            result.append(Trial(**payload))
    return sorted(result, key=lambda item: item.key)


def run_campaign(
    config: CandidateConfig,
    splits: Sequence[str] = SPLITS,
    *,
    review_receipt: Path | None = None,
    prediction_lock: Path | None = None,
) -> dict[str, Any]:
    _validate_candidate(config)
    _require(tuple(splits), "campaign requires at least one split")
    review_digest = None
    lock_digest = None
    packet_digest = None
    if "assessment" in splits:
        _require(review_receipt is not None, "assessment requires independent review receipt")
        _require(prediction_lock is not None, "assessment requires prediction lock")
        review_digest = _validate_review_receipt(review_receipt)
        lock_digest = _validate_prediction_lock(prediction_lock, config)
        packet_digest = hashlib.sha256(REVIEW_PACKET_PATH.read_bytes()).hexdigest()
    trials: list[Trial] = []
    for split in splits:
        _require(split in SPLITS, f"unknown campaign split: {split}")
        for seed in PREREGISTERED_REPLICATE_SEEDS:
            for order_seed in PREREGISTERED_ORDER_SEEDS:
                for order_direction in ORDER_DIRECTIONS:
                    for arm in ARMS:
                        for risk_price in RISK_PRICES:
                            trials.append(
                                run_trial(
                                    arm=arm,
                                    split=split,
                                    seed=seed,
                                    order_seed=order_seed,
                                    order_direction=order_direction,
                                    risk_price=risk_price,
                                    config=config,
                                )
                            )
    trials = _replace_order_pair(trials)
    summary = summarize_trials(trials)
    return {
        "schema_version": SCHEMA_VERSION,
        "state_slice": STATE_SLICE,
        "primary_endpoint": PRIMARY_ENDPOINT,
        "candidate": asdict(config),
        "protocol": {
            "arms": ARMS,
            "splits": SPLITS,
            "risk_prices": RISK_PRICES,
            "replicate_seeds": PREREGISTERED_REPLICATE_SEEDS,
            "order_seeds": PREREGISTERED_ORDER_SEEDS,
            "update_budget": UPDATE_BUDGET,
            "max_forgetting": MAX_FORGETTING,
            "max_calibration_brier": MAX_CALIBRATION_BRIER,
            "max_order_delta": MAX_ORDER_DELTA,
            "claims": (
                "exact_synthetic_controller_only",
                "no_model_loaded",
                "no_base_weights_updated",
                "no_astral_integration",
                "no_zk_or_pqc_evidence",
            ),
            "custody_root": str(CUSTODY_RUN_ROOT),
            "review_receipt_sha256": review_digest,
            "prediction_lock_sha256": lock_digest,
            "review_packet_sha256": packet_digest,
            "review_receipt_path": str(review_receipt.resolve()) if review_receipt else None,
            "prediction_lock_path": str(prediction_lock.resolve()) if prediction_lock else None,
        },
        "trials": [asdict(item) for item in trials],
        "summary": summary,
    }


def summarize_trials(trials: Sequence[Trial]) -> dict[str, Any]:
    summary: dict[str, Any] = {"by_split_arm": {}}
    for split in SPLITS:
        for arm in ARMS:
            rows = [item for item in trials if item.split == split and item.arm == arm]
            if not rows:
                continue
            by_price = {}
            for price in RISK_PRICES:
                price_rows = [item for item in rows if item.risk_price == price]
                by_price[f"{price:.2f}"] = {
                    "adaptation_gain": sum(item.adaptation_gain for item in price_rows) / len(price_rows),
                    "positive_forgetting": sum(item.positive_forgetting for item in price_rows) / len(price_rows),
                    "calibration_brier": sum(item.calibration_brier for item in price_rows) / len(price_rows),
                    "order_pair_delta": max(item.order_pair_delta for item in price_rows),
                }
            affu_values = [
                item.adaptation_gain - item.risk_price * item.positive_forgetting
                for item in rows
            ]
            summary["by_split_arm"][f"{split}:{arm}"] = {
                "adaptation_forgetting_frontier_utility": sum(affu_values) / len(affu_values),
                "mean_adaptation_gain": sum(item.adaptation_gain for item in rows) / len(rows),
                "mean_positive_forgetting": sum(item.positive_forgetting for item in rows) / len(rows),
                "max_positive_forgetting": max(item.positive_forgetting for item in rows),
                "max_calibration_brier": max(item.calibration_brier for item in rows),
                "max_order_pair_delta": max(item.order_pair_delta for item in rows),
                "all_hard_guards_pass": all(
                    item.forgetting_guard_pass
                    and item.calibration_guard_pass
                    and item.rollback_guard_pass
                    and item.compute_guard_pass
                    and item.order_guard_pass
                    for item in rows
                ),
                "by_risk_price": by_price,
            }
    return summary


def validate_result(result: Mapping[str, Any]) -> None:
    _require(result.get("schema_version") == SCHEMA_VERSION, "schema version mismatch")
    _require(result.get("state_slice") == STATE_SLICE, "state slice mismatch")
    candidate = result.get("candidate")
    _require(isinstance(candidate, Mapping), "candidate missing")
    config = candidate_config(str(candidate.get("name")))
    observed_candidate = dict(candidate)
    observed_candidate["alpha_grid"] = tuple(observed_candidate.get("alpha_grid", ()))
    _require(observed_candidate == asdict(config), "candidate digest/config mismatch")
    protocol = result.get("protocol")
    _require(isinstance(protocol, Mapping), "protocol missing")
    _require(tuple(protocol.get("arms", ())) == ARMS, "arm lock mismatch")
    _require(tuple(protocol.get("risk_prices", ())) == RISK_PRICES, "risk-price lock mismatch")
    _require(protocol.get("custody_root") == str(CUSTODY_RUN_ROOT), "custody root mismatch")
    if "assessment" in {raw.get("split") for raw in result.get("trials", []) if isinstance(raw, Mapping)}:
        for field in ("review_receipt_sha256", "prediction_lock_sha256", "review_packet_sha256", "review_receipt_path", "prediction_lock_path"):
            _require(isinstance(protocol.get(field), str), f"assessment {field} missing")
        for field in ("review_receipt_sha256", "prediction_lock_sha256", "review_packet_sha256"):
            _require(len(protocol[field]) == 64, f"assessment {field} digest")
    trials = result.get("trials")
    _require(isinstance(trials, list) and trials, "trials missing")
    for raw in trials:
        _require(isinstance(raw, Mapping), "trial must be object")
        _require(raw.get("trial_digest") == _digest({key: raw[key] for key in (
            "key", "arm", "split", "seed", "order_seed", "order_direction", "risk_price",
            "base_adaptation_loss", "final_adaptation_loss", "adaptation_gain", "base_protected_loss",
            "final_protected_loss", "forgetting_value", "positive_forgetting", "calibration_brier",
            "rollback_max_abs_error", "update_attempts", "gradient_compute_units", "shadow_compute_units",
            "order_pair_delta",
        )}), "trial digest mismatch")
        _require(math.isclose(raw["adaptation_gain"], raw["base_adaptation_loss"] - raw["final_adaptation_loss"], abs_tol=1e-12), "adaptation gain mismatch")
        _require(math.isclose(raw["forgetting_value"], raw["final_protected_loss"] - raw["base_protected_loss"], abs_tol=1e-12), "forgetting mismatch")
        _require(math.isclose(raw["positive_forgetting"], max(0.0, raw["forgetting_value"]), abs_tol=1e-12), "positive forgetting mismatch")
        _require(raw["forgetting_guard_pass"] == (raw["positive_forgetting"] <= MAX_FORGETTING), "forgetting guard mismatch")
        _require(raw["calibration_guard_pass"] == (raw["calibration_brier"] <= MAX_CALIBRATION_BRIER), "calibration guard mismatch")
        _require(raw["rollback_guard_pass"] == (raw["rollback_max_abs_error"] <= ROLLBACK_TOLERANCE), "rollback guard mismatch")
        _require(raw["compute_guard_pass"] is True, "compute guard mismatch")
        _require(raw["order_guard_pass"] == (raw["order_pair_delta"] <= MAX_ORDER_DELTA), "order guard mismatch")
    expected_summary = summarize_trials(tuple(Trial(**raw) for raw in trials))
    _require(result.get("summary") == expected_summary, "summary mismatch")


def write_result(result: Mapping[str, Any], path: Path) -> None:
    validate_result(result)
    _require(path.resolve().parent == CUSTODY_RUN_ROOT.resolve(), "result path must be the declared custody root")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", default=PREDECLARED_CANDIDATES[1]["name"], choices=[item["name"] for item in PREDECLARED_CANDIDATES])
    parser.add_argument("--splits", nargs="+", choices=SPLITS, default=list(SPLITS))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--review-receipt", type=Path)
    parser.add_argument("--prediction-lock", type=Path)
    args = parser.parse_args()
    result = run_campaign(
        candidate_config(args.candidate),
        tuple(args.splits),
        review_receipt=args.review_receipt,
        prediction_lock=args.prediction_lock,
    )
    write_result(result, args.output)
    print(json.dumps({"state_slice": STATE_SLICE, "candidate": args.candidate, "output": str(args.output)}, sort_keys=True))


if __name__ == "__main__":
    main()
