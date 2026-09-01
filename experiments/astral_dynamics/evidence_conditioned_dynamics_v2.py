#!/usr/bin/env python3
"""Exact synthetic learner and factorial controller evaluation.

State slice: ``astral-evidence-conditioned-multiscale-plasticity-v2``.

This is a model-free, closed-form continual-learning experiment.  The learner
is a quadratic target-tracking system with an exact state vector, exact update
effect, exact interference calculation, and exact held-out loss.  It exists to
test the controller before any model-bearing execution is considered.

The verification field in this module is a synthetic control check.  It is not
a ZK proof, a PQC signature, a provenance statement, or semantic truth.  Real
cryptographic backends are intentionally absent from this slice.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import Any, Mapping, Sequence


STATE_SLICE = "astral-evidence-conditioned-multiscale-plasticity-v2"
SCHEMA_VERSION = "astral-evidence-conditioned-factorial-result-v2"
PRIMARY_ENDPOINT = "heldout_adaptation_improvement_after_fixed_update_budget"
MODES = (
    "fixed_cadence",
    "adaptive_verification",
    "wave_scheduling",
    "adaptive_wave",
)
SCHEDULERS = ("deterministic", "bounded_stochastic")
TAXONOMIES = ("oracle", "noisy", "shuffled", "absent")
SPLITS = ("fit", "tune", "assessment")
CLAIMS = (
    "exact_synthetic_learner_only",
    "no_model_loaded",
    "no_base_weights_updated",
    "no_v48_artifacts_used",
    "no_astral_introspection_claim",
    "no_zk_or_pqc_evidence_generated",
)
PREREGISTERED_REPLICATE_SEEDS = (20260828, 20260829, 20260830)
PREREGISTERED_ORDER_SEEDS = (4701, 4702, 4703)
DIMENSION = 6
FIT_SHARD_COUNT = 24
TUNE_SHARD_COUNT = 12
ASSESSMENT_SHARD_COUNT = 12
UPDATE_BUDGET = FIT_SHARD_COUNT
MAX_ORDER_RANGE = 0.20
MAX_FORGETTING = 0.22
MAX_CALIBRATION_BRIER = 0.12
ROLLBACK_TOLERANCE = 1e-12
MAX_VERIFICATION_COST = UPDATE_BUDGET * 3


class ProtocolError(ValueError):
    """Raised when a v2 synthetic experiment violates its frozen contract."""


@dataclass(frozen=True)
class ProtocolConfig:
    dimension: int = DIMENSION
    fit_shard_count: int = FIT_SHARD_COUNT
    tune_shard_count: int = TUNE_SHARD_COUNT
    assessment_shard_count: int = ASSESSMENT_SHARD_COUNT
    update_budget: int = UPDATE_BUDGET
    base_learning_rate: float = 0.18
    high_frequency: float = 0.25
    low_frequency: float = 0.0625
    high_amplitude: float = 0.12
    low_amplitude: float = 0.08
    stochastic_schedule_bound: float = 0.04
    min_wave_multiplier: float = 0.75
    max_wave_multiplier: float = 1.25
    taxonomy_noise_bound: float = 0.15
    risk_gate_threshold: float = 0.42
    interference_limit: float = 0.018
    replicate_seeds: tuple[int, ...] = PREREGISTERED_REPLICATE_SEEDS
    order_seeds: tuple[int, ...] = PREREGISTERED_ORDER_SEEDS


@dataclass(frozen=True)
class SyntheticShard:
    shard_id: str
    split: str
    index: int
    target: tuple[float, ...]
    risk_truth: float
    payload_sha256: str


@dataclass(frozen=True)
class UpdateRecord:
    shard_id: str
    before_parameters: tuple[float, ...]
    after_parameters: tuple[float, ...]
    applied_delta: tuple[float, ...]
    learning_rate: float
    interference: float
    effect_sha256: str


@dataclass(frozen=True)
class SyntheticState:
    parameters: tuple[float, ...]
    committed_shards: tuple[str, ...] = ()
    quarantined_shards: tuple[str, ...] = ()
    rolled_back_shards: tuple[str, ...] = ()
    updates: tuple[UpdateRecord, ...] = ()
    version: int = 0
    update_attempts: int = 0
    gradient_compute_units: int = 0
    shadow_compute_units: int = 0
    verification_cost_units: int = 0


@dataclass(frozen=True)
class PreparedTrial:
    key: str
    mode: str
    scheduler: str
    taxonomy: str
    seed: int
    order_seed: int
    state: SyntheticState
    tune_prediction: float
    calibration_brier: float
    verification_ratio_sum: float
    verification_checks: int
    decision_digest: str


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ProtocolError(message)


def _finite(value: Any, field: str) -> float:
    _require(isinstance(value, (int, float)) and not isinstance(value, bool), f"{field} must be numeric")
    converted = float(value)
    _require(math.isfinite(converted), f"{field} must be finite")
    return converted


def _unit(value: Any, field: str) -> float:
    converted = _finite(value, field)
    _require(0.0 <= converted <= 1.0, f"{field} must be in [0, 1]")
    return converted


def _digest(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    ).hexdigest()


def _clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))


def _unit_from_parts(*parts: object) -> float:
    payload = "|".join(str(part) for part in parts).encode("utf-8")
    integer = int.from_bytes(hashlib.sha256(payload).digest()[:8], "big")
    return integer / float(1 << 64)


def _signed_from_parts(*parts: object) -> float:
    return 2.0 * _unit_from_parts(*parts) - 1.0


def _validate_config(config: ProtocolConfig) -> None:
    for field in (
        "base_learning_rate",
        "high_frequency",
        "low_frequency",
        "high_amplitude",
        "low_amplitude",
        "stochastic_schedule_bound",
        "min_wave_multiplier",
        "max_wave_multiplier",
        "taxonomy_noise_bound",
        "risk_gate_threshold",
        "interference_limit",
    ):
        _finite(getattr(config, field), field)
    for field in (
        "dimension",
        "fit_shard_count",
        "tune_shard_count",
        "assessment_shard_count",
        "update_budget",
    ):
        value = getattr(config, field)
        _require(isinstance(value, int) and not isinstance(value, bool) and value > 0, f"{field} must be a positive integer")
    _require(config.dimension == DIMENSION, "dimension is frozen by the protocol")
    _require(config.fit_shard_count == FIT_SHARD_COUNT, "fit shard count is frozen by the protocol")
    _require(config.tune_shard_count == TUNE_SHARD_COUNT, "tune shard count is frozen by the protocol")
    _require(config.assessment_shard_count == ASSESSMENT_SHARD_COUNT, "assessment shard count is frozen by the protocol")
    _require(config.update_budget == config.fit_shard_count, "update budget must equal fit shard count")
    _require(config.high_frequency > config.low_frequency > 0.0, "frequencies must be positive and ordered")
    _require(config.high_amplitude >= 0.0 and config.low_amplitude >= 0.0, "wave amplitudes must be nonnegative")
    _require(config.stochastic_schedule_bound >= 0.0, "stochastic schedule bound must be nonnegative")
    _require(0.0 < config.min_wave_multiplier <= 1.0, "minimum wave multiplier must be in (0, 1]")
    _require(config.max_wave_multiplier >= 1.0, "maximum wave multiplier must be at least 1")
    _require(config.min_wave_multiplier < config.max_wave_multiplier, "wave bounds must be ordered")
    _require(0.0 <= config.taxonomy_noise_bound <= 1.0, "taxonomy noise bound must be in [0, 1]")
    _require(0.0 <= config.risk_gate_threshold <= 1.0, "risk gate threshold must be in [0, 1]")
    _require(config.interference_limit >= 0.0, "interference limit must be nonnegative")
    _require(config.replicate_seeds == PREREGISTERED_REPLICATE_SEEDS, "replicate seeds are not preregistered")
    _require(config.order_seeds == PREREGISTERED_ORDER_SEEDS, "order seeds are not preregistered")


def _anchor(config: ProtocolConfig) -> tuple[float, ...]:
    return tuple(0.70 * math.sin((component + 1) * 1.17) for component in range(config.dimension))


def _target(config: ProtocolConfig, seed: int, split: str, index: int) -> tuple[float, ...]:
    _require(split in SPLITS, f"unknown split: {split}")
    anchor = _anchor(config)
    risk_draw = _unit_from_parts(STATE_SLICE, seed, split, index, "risk")
    if split == "fit":
        amplitude = 0.08 + 1.30 * risk_draw
    else:
        amplitude = 0.05 + 0.18 * risk_draw
    return tuple(
        anchor[component]
        + amplitude * _signed_from_parts(STATE_SLICE, seed, split, index, component, "direction")
        for component in range(config.dimension)
    )


def _risk_truth(config: ProtocolConfig, target: Sequence[float]) -> float:
    anchor = _anchor(config)
    distance = math.sqrt(sum((target[index] - anchor[index]) ** 2 for index in range(config.dimension)) / config.dimension)
    return _clamp(distance / 1.30, 0.0, 1.0)


def _shard_payload(shard: SyntheticShard) -> dict[str, Any]:
    return {
        "state_slice": STATE_SLICE,
        "shard_id": shard.shard_id,
        "split": shard.split,
        "index": shard.index,
        "target": list(shard.target),
        "risk_truth": shard.risk_truth,
    }


def make_panel(config: ProtocolConfig = ProtocolConfig(), seed: int = PREREGISTERED_REPLICATE_SEEDS[0]) -> tuple[SyntheticShard, ...]:
    """Generate fresh fit/tune/assessment shards from a closed-form process."""

    _validate_config(config)
    _require(isinstance(seed, int) and not isinstance(seed, bool), "seed must be an integer")
    counts = {
        "fit": config.fit_shard_count,
        "tune": config.tune_shard_count,
        "assessment": config.assessment_shard_count,
    }
    shards: list[SyntheticShard] = []
    for split in SPLITS:
        for index in range(counts[split]):
            target = _target(config, seed, split, index)
            shard = SyntheticShard(
                shard_id=f"{split}-{index:03d}",
                split=split,
                index=index,
                target=target,
                risk_truth=_risk_truth(config, target),
                payload_sha256="",
            )
            shards.append(replace(shard, payload_sha256=_digest(_shard_payload(shard))))
    return tuple(shards)


def panel_digest(panel: Sequence[SyntheticShard]) -> str:
    return _digest([asdict(shard) for shard in panel])


def split_digest(panel: Sequence[SyntheticShard], split: str) -> str:
    return _digest([asdict(shard) for shard in panel if shard.split == split])


def make_order(panel: Sequence[SyntheticShard], order_seed: int) -> tuple[SyntheticShard, ...]:
    """Create a fixed, reproducible permutation of only the fit shards."""

    fit = [shard for shard in panel if shard.split == "fit"]
    _require(len(fit) == FIT_SHARD_COUNT, "fit panel count drift")
    return tuple(sorted(fit, key=lambda shard: (_unit_from_parts(STATE_SLICE, "order", order_seed, shard.shard_id), shard.index)))


def wave_multiplier(step: int, config: ProtocolConfig = ProtocolConfig()) -> float:
    """Return bounded high-frequency sine plus low-frequency cosine control."""

    _validate_config(config)
    _require(isinstance(step, int) and not isinstance(step, bool) and step >= 0, "step must be a nonnegative integer")
    fast = config.high_amplitude * math.sin(2.0 * math.pi * config.high_frequency * step)
    slow = config.low_amplitude * math.cos(2.0 * math.pi * config.low_frequency * step)
    return _clamp(1.0 + fast + slow, config.min_wave_multiplier, config.max_wave_multiplier)


def _schedule_multiplier(
    mode: str,
    scheduler: str,
    step: int,
    seed: int,
    shard_id: str,
    config: ProtocolConfig,
) -> float:
    base = wave_multiplier(step, config) if mode in ("wave_scheduling", "adaptive_wave") else 1.0
    if scheduler == "deterministic":
        return base
    jitter = config.stochastic_schedule_bound * _signed_from_parts(STATE_SLICE, "schedule", seed, shard_id, step)
    return _clamp(base * (1.0 + jitter), config.min_wave_multiplier, config.max_wave_multiplier)


def _verification_slot(scheduler: str, seed: int, order_seed: int, shard_id: str, step: int) -> float:
    if scheduler == "deterministic":
        return _unit_from_parts(STATE_SLICE, "verification-slot", seed, order_seed, shard_id, step)
    return _unit_from_parts(STATE_SLICE, "bounded-stochastic-verification-slot", seed, order_seed, shard_id, step)


def taxonomy_value(
    taxonomy: str,
    shard: SyntheticShard,
    fit_shards: Sequence[SyntheticShard],
    seed: int,
    config: ProtocolConfig = ProtocolConfig(),
) -> float:
    """Return the controller-visible taxonomy without exposing ground truth."""

    _validate_config(config)
    _require(taxonomy in TAXONOMIES, f"unknown taxonomy: {taxonomy}")
    _require(shard.split == "fit", "taxonomy is defined for fit shards only")
    if taxonomy == "oracle":
        return shard.risk_truth
    if taxonomy == "noisy":
        noise = config.taxonomy_noise_bound * _signed_from_parts(STATE_SLICE, "taxonomy-noise", seed, shard.shard_id)
        return _clamp(shard.risk_truth + noise, 0.0, 1.0)
    if taxonomy == "absent":
        return 0.5
    ordered = sorted(
        fit_shards,
        key=lambda item: (_unit_from_parts(STATE_SLICE, "taxonomy-shuffle", seed, item.shard_id), item.index),
    )
    position = next(index for index, item in enumerate(ordered) if item.shard_id == shard.shard_id)
    source = ordered[(position + 1) % len(ordered)]
    return source.risk_truth


def loss(parameters: Sequence[float], target: Sequence[float]) -> float:
    _require(len(parameters) == len(target), "parameter/target dimension mismatch")
    return 0.5 * sum((parameters[index] - target[index]) ** 2 for index in range(len(target))) / len(target)


def _update(parameters: Sequence[float], target: Sequence[float], learning_rate: float) -> tuple[float, ...]:
    return tuple(parameters[index] + learning_rate * (target[index] - parameters[index]) for index in range(len(target)))


def _interference(state: SyntheticState, after: Sequence[float], fit_by_id: Mapping[str, SyntheticShard], config: ProtocolConfig) -> float:
    protected_targets = [_anchor(config)]
    protected_targets.extend(fit_by_id[shard_id].target for shard_id in state.committed_shards)
    increases = [max(0.0, loss(after, target) - loss(state.parameters, target)) for target in protected_targets]
    return _clamp(sum(increases) / len(increases), 0.0, 1.0)


def _effect_digest(shard_id: str, before: Sequence[float], after: Sequence[float], learning_rate: float, interference: float) -> str:
    return _digest(
        {
            "shard_id": shard_id,
            "before_parameters": list(before),
            "after_parameters": list(after),
            "learning_rate": learning_rate,
            "interference": interference,
        }
    )


def _event_digest(shard_id: str, step: int, action: str, reason: str, accepted: bool, observed_risk: float) -> str:
    return _digest(
        {
            "shard_id": shard_id,
            "step": step,
            "action": action,
            "reason": reason,
            "accepted": accepted,
            "observed_risk": observed_risk,
        }
    )


def _initial_state(config: ProtocolConfig) -> SyntheticState:
    return SyntheticState(parameters=(0.0,) * config.dimension)


def _process_shard(
    state: SyntheticState,
    shard: SyntheticShard,
    fit_by_id: Mapping[str, SyntheticShard],
    fit_shards: Sequence[SyntheticShard],
    taxonomy: str,
    mode: str,
    scheduler: str,
    seed: int,
    order_seed: int,
    step: int,
    config: ProtocolConfig,
) -> tuple[SyntheticState, dict[str, Any]]:
    observed_risk = taxonomy_value(taxonomy, shard, fit_shards, seed, config)
    multiplier = _schedule_multiplier(mode, scheduler, step, seed, shard.shard_id, config)
    learning_rate = config.base_learning_rate * multiplier
    after = _update(state.parameters, shard.target, learning_rate)
    delta = tuple(after[index] - state.parameters[index] for index in range(config.dimension))
    interference = _interference(state, after, fit_by_id, config)
    adaptive = mode in ("adaptive_verification", "adaptive_wave")
    verification_ratio = _clamp(0.15 + 0.80 * observed_risk, 0.0, 1.0) if adaptive else 0.0
    requires_verification = adaptive and observed_risk >= config.risk_gate_threshold
    selected = requires_verification and _verification_slot(scheduler, seed, order_seed, shard.shard_id, step) < verification_ratio
    verification_cost = (1 + math.ceil(2.0 * observed_risk)) if selected else 0
    if not adaptive:
        accepted = True
        reason = "fixed_cadence_commit"
    elif not requires_verification:
        accepted = True
        reason = "low_risk_no_verification"
    elif not selected:
        accepted = False
        reason = "verification_slot_not_selected"
    elif interference > config.interference_limit:
        accepted = False
        reason = "exact_interference_check_failed"
    else:
        accepted = True
        reason = "exact_interference_check_passed"

    next_state = replace(
        state,
        version=state.version + 1,
        update_attempts=state.update_attempts + 1,
        gradient_compute_units=state.gradient_compute_units + config.dimension,
        shadow_compute_units=state.shadow_compute_units + config.dimension,
        verification_cost_units=state.verification_cost_units + verification_cost,
    )
    if accepted:
        effect_sha256 = _effect_digest(shard.shard_id, state.parameters, after, learning_rate, interference)
        update = UpdateRecord(
            shard_id=shard.shard_id,
            before_parameters=state.parameters,
            after_parameters=after,
            applied_delta=delta,
            learning_rate=learning_rate,
            interference=interference,
            effect_sha256=effect_sha256,
        )
        next_state = replace(
            next_state,
            parameters=after,
            committed_shards=state.committed_shards + (shard.shard_id,),
            updates=state.updates + (update,),
        )
    else:
        next_state = replace(next_state, quarantined_shards=state.quarantined_shards + (shard.shard_id,))
    decision = {
        "shard_id": shard.shard_id,
        "step": step,
        "observed_risk": observed_risk,
        "true_risk": shard.risk_truth,
        "verification_ratio": verification_ratio,
        "verification_selected": selected,
        "verification_cost_units": verification_cost,
        "learning_rate": learning_rate,
        "interference": interference,
        "accepted": accepted,
        "reason": reason,
        "event_sha256": _event_digest(shard.shard_id, step, "commit" if accepted else "quarantine", reason, accepted, observed_risk),
    }
    return next_state, decision


def _mean(values: Sequence[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _forgetting(state: SyntheticState, fit_by_id: Mapping[str, SyntheticShard], config: ProtocolConfig) -> float:
    if not state.committed_shards:
        return 0.0
    targets = [fit_by_id[shard_id].target for shard_id in state.committed_shards]
    origin = _mean([loss((0.0,) * config.dimension, target) for target in targets])
    after = _mean([loss(state.parameters, target) for target in targets])
    return max(0.0, after - origin) / max(origin, 1e-12)


def _rollback_last(state: SyntheticState) -> tuple[SyntheticState, float]:
    _require(state.updates, "rollback requires at least one committed update")
    update = state.updates[-1]
    rollback_error = max(
        abs(state.parameters[index] - update.after_parameters[index]) for index in range(len(state.parameters))
    )
    restored = replace(
        state,
        parameters=update.before_parameters,
        committed_shards=state.committed_shards[:-1],
        rolled_back_shards=state.rolled_back_shards + (update.shard_id,),
        updates=state.updates[:-1],
        version=state.version + 1,
    )
    return restored, rollback_error


def _prepare_trial(
    panel: Sequence[SyntheticShard],
    mode: str,
    scheduler: str,
    taxonomy: str,
    seed: int,
    order_seed: int,
    config: ProtocolConfig,
) -> PreparedTrial:
    fit_shards = [shard for shard in panel if shard.split == "fit"]
    fit_by_id = {shard.shard_id: shard for shard in fit_shards}
    ordered_fit = make_order(panel, order_seed)
    state = _initial_state(config)
    decisions: list[dict[str, Any]] = []
    ratio_sum = 0.0
    verification_checks = 0
    for step, shard in enumerate(ordered_fit):
        state, decision = _process_shard(
            state,
            shard,
            fit_by_id,
            fit_shards,
            taxonomy,
            mode,
            scheduler,
            seed,
            order_seed,
            step,
            config,
        )
        decisions.append(decision)
        ratio_sum += decision["verification_ratio"]
        verification_checks += int(decision["verification_selected"])
    tune_shards = [shard for shard in panel if shard.split == "tune"]
    origin = (0.0,) * config.dimension
    tune_prediction = _mean([loss(origin, shard.target) - loss(state.parameters, shard.target) for shard in tune_shards])
    calibration_brier = _mean([(decision["observed_risk"] - decision["true_risk"]) ** 2 for decision in decisions])
    decision_digest = _digest(decisions)
    return PreparedTrial(
        key=f"{mode}|{scheduler}|{taxonomy}|seed-{seed}|order-{order_seed}",
        mode=mode,
        scheduler=scheduler,
        taxonomy=taxonomy,
        seed=seed,
        order_seed=order_seed,
        state=state,
        tune_prediction=tune_prediction,
        calibration_brier=calibration_brier,
        verification_ratio_sum=ratio_sum,
        verification_checks=verification_checks,
        decision_digest=decision_digest,
    )


def _finalize_trial(prepared: PreparedTrial, panel: Sequence[SyntheticShard], lock_sha256: str, config: ProtocolConfig) -> dict[str, Any]:
    assessment_shards = [shard for shard in panel if shard.split == "assessment"]
    origin = (0.0,) * config.dimension
    assessment_baseline = _mean([loss(origin, shard.target) for shard in assessment_shards])
    assessment_final = _mean([loss(prepared.state.parameters, shard.target) for shard in assessment_shards])
    primary = assessment_baseline - assessment_final
    fit_by_id = {shard.shard_id: shard for shard in panel if shard.split == "fit"}
    forgetting = _forgetting(prepared.state, fit_by_id, config)
    rollback_state, rollback_error = _rollback_last(prepared.state) if prepared.state.updates else (prepared.state, 0.0)
    equal_update_compute = (
        prepared.state.update_attempts == config.update_budget
        and prepared.state.gradient_compute_units == config.update_budget * config.dimension
        and prepared.state.shadow_compute_units == config.update_budget * config.dimension
    )
    return {
        "replicate_key": prepared.key,
        "mode": prepared.mode,
        "scheduler": prepared.scheduler,
        "taxonomy": prepared.taxonomy,
        "seed": prepared.seed,
        "order_seed": prepared.order_seed,
        "tune_prediction": prepared.tune_prediction,
        "prediction_lock_sha256": lock_sha256,
        "prediction_locked_before_assessment": True,
        "assessment_baseline_loss": assessment_baseline,
        "assessment_final_loss": assessment_final,
        "primary_endpoint_value": primary,
        "committed_shards": list(prepared.state.committed_shards),
        "quarantined_shards": list(prepared.state.quarantined_shards),
        "committed_count": len(prepared.state.committed_shards),
        "quarantined_count": len(prepared.state.quarantined_shards),
        "final_parameters": list(prepared.state.parameters),
        "forgetting_value": forgetting,
        "calibration_brier": prepared.calibration_brier,
        "rollback_max_abs_error": rollback_error,
        "verification_ratio_mean": prepared.verification_ratio_sum / config.update_budget,
        "verification_checks": prepared.verification_checks,
        "verification_cost_units": prepared.state.verification_cost_units,
        "update_attempts": prepared.state.update_attempts,
        "gradient_compute_units": prepared.state.gradient_compute_units,
        "shadow_compute_units": prepared.state.shadow_compute_units,
        "decision_digest": prepared.decision_digest,
        "equal_update_compute_guard_pass": equal_update_compute,
        "forgetting_guard_pass": forgetting <= MAX_FORGETTING,
        "calibration_guard_pass": prepared.calibration_brier <= MAX_CALIBRATION_BRIER,
        "rollback_fidelity_guard_pass": rollback_error <= ROLLBACK_TOLERANCE,
        "verification_cost_guard_pass": prepared.state.verification_cost_units <= MAX_VERIFICATION_COST,
    }


def _cell_key(mode: str, scheduler: str, taxonomy: str) -> str:
    return f"{mode}|{scheduler}|{taxonomy}"


def _cell_summary(replicates: Sequence[Mapping[str, Any]], mode: str, scheduler: str, taxonomy: str, config: ProtocolConfig) -> dict[str, Any]:
    primaries = [float(item["primary_endpoint_value"]) for item in replicates]
    by_seed: dict[int, list[float]] = {}
    for item in replicates:
        by_seed.setdefault(int(item["seed"]), []).append(float(item["primary_endpoint_value"]))
    order_range = max((max(values) - min(values) for values in by_seed.values()), default=0.0)
    equal_compute = len({(item["update_attempts"], item["gradient_compute_units"], item["shadow_compute_units"]) for item in replicates}) == 1
    guards = {
        "forgetting": all(bool(item["forgetting_guard_pass"]) for item in replicates),
        "calibration": all(bool(item["calibration_guard_pass"]) for item in replicates),
        "rollback_fidelity": all(bool(item["rollback_fidelity_guard_pass"]) for item in replicates),
        "shard_order_stability": order_range <= MAX_ORDER_RANGE,
        "verification_cost": all(bool(item["verification_cost_guard_pass"]) for item in replicates),
        "equal_update_compute": equal_compute and all(bool(item["equal_update_compute_guard_pass"]) for item in replicates),
    }
    body = {
        "cell_key": _cell_key(mode, scheduler, taxonomy),
        "mode": mode,
        "scheduler": scheduler,
        "taxonomy": taxonomy,
        "replicate_count": len(replicates),
        "primary_endpoint": PRIMARY_ENDPOINT,
        "primary_mean": _mean(primaries),
        "primary_min": min(primaries),
        "primary_max": max(primaries),
        "tune_prediction_mean": _mean([float(item["tune_prediction"]) for item in replicates]),
        "max_order_range": order_range,
        "max_verification_cost_units": max(int(item["verification_cost_units"]) for item in replicates),
        "guards": guards,
        "eligible_for_controller_comparison": all(guards.values()),
        "replicates": [dict(item) for item in replicates],
    }
    return {**body, "cell_sha256": _digest(body)}


def _decision_diagnostics(cells: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    def primary(mode: str, scheduler: str = "deterministic", taxonomy: str = "oracle") -> float:
        return float(cells[_cell_key(mode, scheduler, taxonomy)]["primary_mean"])

    gating_delta = primary("adaptive_verification") - primary("fixed_cadence")
    wave_delta_after_gating = primary("adaptive_wave") - primary("adaptive_verification")
    stochastic_pairs = []
    for mode in MODES:
        for taxonomy in TAXONOMIES:
            deterministic = cells[_cell_key(mode, "deterministic", taxonomy)]
            stochastic = cells[_cell_key(mode, "bounded_stochastic", taxonomy)]
            stochastic_pairs.append(
                {
                    "mode": mode,
                    "taxonomy": taxonomy,
                    "primary_delta_stochastic_minus_deterministic": stochastic["primary_mean"] - deterministic["primary_mean"],
                    "all_deterministic_replicates": [
                        item["primary_endpoint_value"] for item in deterministic["replicates"]
                    ],
                    "all_stochastic_replicates": [
                        item["primary_endpoint_value"] for item in stochastic["replicates"]
                    ],
                }
            )
    return {
        "oracle_deterministic_gating_delta": gating_delta,
        "oracle_deterministic_wave_delta_after_gating": wave_delta_after_gating,
        "oracle_deterministic_gating_improves_primary": gating_delta > 0.0,
        "oracle_deterministic_wave_improves_after_gating": wave_delta_after_gating > 0.0,
        "stochastic_pairs": stochastic_pairs,
        "model_or_astral_integration": "not_run_synthetic_controller_only",
    }


def run_factorial(config: ProtocolConfig = ProtocolConfig()) -> dict[str, Any]:
    """Run the complete preregistered 4 x 2 x 4 factorial."""

    _validate_config(config)
    panels = {seed: make_panel(config, seed) for seed in config.replicate_seeds}
    prepared: list[PreparedTrial] = []
    for mode in MODES:
        for scheduler in SCHEDULERS:
            for taxonomy in TAXONOMIES:
                for seed in config.replicate_seeds:
                    for order_seed in config.order_seeds:
                        prepared.append(
                            _prepare_trial(panels[seed], mode, scheduler, taxonomy, seed, order_seed, config)
                        )
    lock_body = {
        "state_slice": STATE_SLICE,
        "lock_type": "fit_and_tune_predictions_only",
        "assessment_started": False,
        "predictions": [
            {"replicate_key": trial.key, "tune_prediction": trial.tune_prediction}
            for trial in prepared
        ],
    }
    lock_sha256 = _digest(lock_body)
    finalized = [_finalize_trial(trial, panels[trial.seed], lock_sha256, config) for trial in prepared]
    cells: dict[str, dict[str, Any]] = {}
    for mode in MODES:
        for scheduler in SCHEDULERS:
            for taxonomy in TAXONOMIES:
                key = _cell_key(mode, scheduler, taxonomy)
                cells[key] = _cell_summary(
                    [item for item in finalized if item["mode"] == mode and item["scheduler"] == scheduler and item["taxonomy"] == taxonomy],
                    mode,
                    scheduler,
                    taxonomy,
                    config,
                )
    split_records = {
        str(seed): {
            "panel_sha256": panel_digest(panels[seed]),
            "fit_sha256": split_digest(panels[seed], "fit"),
            "tune_sha256": split_digest(panels[seed], "tune"),
            "assessment_sha256": split_digest(panels[seed], "assessment"),
        }
        for seed in config.replicate_seeds
    }
    body = {
        "state_slice": STATE_SLICE,
        "schema_version": SCHEMA_VERSION,
        "primary_endpoint": PRIMARY_ENDPOINT,
        "config": asdict(config),
        "modes": list(MODES),
        "schedulers": list(SCHEDULERS),
        "taxonomies": list(TAXONOMIES),
        "preregistered_replicate_seeds": list(config.replicate_seeds),
        "preregistered_order_seeds": list(config.order_seeds),
        "fresh_split_records": split_records,
        "prediction_lock": lock_body,
        "prediction_lock_sha256": lock_sha256,
        "factorial_cell_count": len(cells),
        "cells": cells,
        "decision_diagnostics": _decision_diagnostics(cells),
        "claims": list(CLAIMS),
    }
    return {**body, "result_sha256": _digest(body)}


def _validate_mapping(result: Mapping[str, Any]) -> None:
    _require(result.get("state_slice") == STATE_SLICE, "wrong state slice")
    _require(result.get("schema_version") == SCHEMA_VERSION, "wrong schema version")
    _require(result.get("primary_endpoint") == PRIMARY_ENDPOINT, "primary endpoint drift")
    _require(result.get("modes") == list(MODES), "mode panel drift")
    _require(result.get("schedulers") == list(SCHEDULERS), "scheduler panel drift")
    _require(result.get("taxonomies") == list(TAXONOMIES), "taxonomy panel drift")
    _require(result.get("claims") == list(CLAIMS), "claim ceiling drift")
    _require(result.get("factorial_cell_count") == len(MODES) * len(SCHEDULERS) * len(TAXONOMIES), "factorial cell count drift")
    config_raw = result.get("config")
    _require(isinstance(config_raw, Mapping), "config must be an object")
    try:
        config_values = dict(config_raw)
        for field in ("replicate_seeds", "order_seeds"):
            if isinstance(config_values.get(field), list):
                config_values[field] = tuple(config_values[field])
        config = ProtocolConfig(**config_values)
    except (TypeError, ValueError) as exc:
        raise ProtocolError(f"invalid config: {exc}") from exc
    _validate_config(config)
    _require(result.get("preregistered_replicate_seeds") == list(PREREGISTERED_REPLICATE_SEEDS), "replicate seed lock drift")
    _require(result.get("preregistered_order_seeds") == list(PREREGISTERED_ORDER_SEEDS), "order seed lock drift")
    lock = result.get("prediction_lock")
    _require(isinstance(lock, Mapping), "prediction lock must be an object")
    _require(lock.get("assessment_started") is False, "prediction lock assessment ordering drift")
    _require(result.get("prediction_lock_sha256") == _digest(lock), "prediction lock digest mismatch")
    cells = result.get("cells")
    _require(isinstance(cells, Mapping) and len(cells) == result["factorial_cell_count"], "cell panel drift")
    for mode in MODES:
        for scheduler in SCHEDULERS:
            for taxonomy in TAXONOMIES:
                key = _cell_key(mode, scheduler, taxonomy)
                cell = cells.get(key)
                _require(isinstance(cell, Mapping), f"missing cell: {key}")
                _require(cell.get("cell_key") == key, f"cell key mismatch: {key}")
                _require(cell.get("replicate_count") == len(config.replicate_seeds) * len(config.order_seeds), f"replicate count mismatch: {key}")
                _require(isinstance(cell.get("replicates"), list), f"replicates must be a list: {key}")
                _require(cell.get("cell_sha256") == _digest({field: cell[field] for field in cell if field != "cell_sha256"}), f"cell digest mismatch: {key}")
                for replicate in cell["replicates"]:
                    _require(replicate.get("prediction_locked_before_assessment") is True, f"prediction lock ordering drift: {key}")
                    _require(replicate.get("prediction_lock_sha256") == result["prediction_lock_sha256"], f"replicate lock mismatch: {key}")
                    for field in ("primary_endpoint_value", "assessment_baseline_loss", "assessment_final_loss", "forgetting_value", "calibration_brier"):
                        _finite(replicate.get(field), f"{key}/{field}")
                    for field in ("update_attempts", "gradient_compute_units", "shadow_compute_units", "verification_cost_units"):
                        _require(isinstance(replicate.get(field), int) and not isinstance(replicate.get(field), bool), f"invalid compute field: {key}/{field}")
    unsigned = {field: result[field] for field in result if field != "result_sha256"}
    _require(result.get("result_sha256") == _digest(unsigned), "result digest mismatch")


def validate_result(result: Mapping[str, Any]) -> None:
    """Validate report shape and digest binding before external audit."""

    _require(isinstance(result, Mapping), "result must be an object")
    _validate_mapping(result)


def markdown_report(result: Mapping[str, Any]) -> str:
    lines = [
        "# Evidence-Conditioned Multiscale Plasticity v2",
        "",
        "Exact synthetic learner only. No model, base weights, V48 artifacts, Astral introspection lane, ZK proof, or PQC proof.",
        "",
        f"Result SHA-256: `{result['result_sha256']}`",
        f"Prediction lock SHA-256: `{result['prediction_lock_sha256']}`",
        "",
        "| Mode | Scheduler | Taxonomy | Primary mean | Eligible |",
        "|---|---|---|---:|---|",
    ]
    for key in sorted(result["cells"]):
        cell = result["cells"][key]
        lines.append(
            f"| `{cell['mode']}` | `{cell['scheduler']}` | `{cell['taxonomy']}` | "
            f"{cell['primary_mean']:.8f} | {cell['eligible_for_controller_comparison']} |"
        )
    lines.extend(
        [
            "",
            "Primary endpoint: held-out adaptation improvement after the fixed 24-update budget.",
            "All update attempts, gradient units, and shadow units are equalized; verification cost is reported separately as a guard.",
            "Claim ceiling: local exact-synthetic-controller mechanics only.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()
    result = run_factorial()
    validate_result(result)
    if args.output is None:
        print(json.dumps({
            "result_sha256": result["result_sha256"],
            "prediction_lock_sha256": result["prediction_lock_sha256"],
            "factorial_cell_count": result["factorial_cell_count"],
            "decision_diagnostics": result["decision_diagnostics"],
        }, indent=2, sort_keys=True))
        return
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (args.output / "result.md").write_text(markdown_report(result), encoding="utf-8")
    print(json.dumps({"output": str(args.output), "result_sha256": result["result_sha256"]}, sort_keys=True))


if __name__ == "__main__":
    main()
