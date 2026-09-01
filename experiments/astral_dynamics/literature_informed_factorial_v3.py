#!/usr/bin/env python3
"""Literature-informed exact synthetic continual-learning factorial.

State slice: ``astral-evidence-conditioned-multiscale-plasticity-v3``.

The learner is closed form and model-free. It separates fast and slow state,
uses exact replay and EWC-style retention variants, tracks a bounded
plasticity variable, computes measurable surprise/risk fields, and compares
fixed, single-frequency, dual-frequency, and bounded seeded-stochastic
schedules. The experiment does not load a model or claim that a taxonomy is
epistemic or ontological truth.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import Any, Mapping, Sequence


STATE_SLICE = "astral-evidence-conditioned-multiscale-plasticity-v3"
SCHEMA_VERSION = "astral-evidence-conditioned-literature-factorial-result-v3"
PRIMARY_ENDPOINT = "heldout_adaptation_improvement_after_fixed_update_budget"
MEMORY_POLICIES = ("single", "fast_slow", "replay", "ewc", "plasticity_guard", "integrated")
SCHEDULE_POLICIES = ("fixed", "single_frequency", "dual_frequency", "bounded_stochastic_dual")
CONTROLLERS = ("fixed_admission", "evidence_conditioned")
TAXONOMIES = ("oracle", "noisy", "shuffled", "absent")
SPLITS = ("fit", "tune", "assessment")
CLAIMS = (
    "exact_synthetic_literature_informed_controller_only",
    "no_model_loaded",
    "no_base_weights_updated",
    "no_v48_artifacts_used",
    "no_astral_introspection_claim",
    "no_zk_or_pqc_evidence_generated",
)
PREREGISTERED_REPLICATE_SEEDS = (20260831, 20260832, 20260833)
PREREGISTERED_ORDER_SEEDS = (5711, 5712, 5713)
DIMENSION = 6
FIT_SHARD_COUNT = 24
TUNE_SHARD_COUNT = 12
ASSESSMENT_SHARD_COUNT = 12
UPDATE_BUDGET = FIT_SHARD_COUNT
MICRO_UPDATES_PER_SHARD = 2
MAX_ORDER_RANGE = 0.20
MAX_FORGETTING = 0.22
MAX_CALIBRATION_BRIER = 0.12
MIN_PLASTICITY = 0.25
ROLLBACK_TOLERANCE = 1e-12
MAX_VERIFICATION_COST = UPDATE_BUDGET * 3


class ProtocolError(ValueError):
    """Raised when the frozen v3 experiment contract is violated."""


@dataclass(frozen=True)
class ProtocolConfig:
    dimension: int = DIMENSION
    fit_shard_count: int = FIT_SHARD_COUNT
    tune_shard_count: int = TUNE_SHARD_COUNT
    assessment_shard_count: int = ASSESSMENT_SHARD_COUNT
    update_budget: int = UPDATE_BUDGET
    micro_updates_per_shard: int = MICRO_UPDATES_PER_SHARD
    base_learning_rate: float = 0.16
    slow_learning_rate: float = 0.06
    replay_capacity: int = 4
    ewc_strength: float = 0.09
    plasticity_decay: float = 0.004
    plasticity_recovery: float = 0.020
    high_frequency: float = 0.25
    low_frequency: float = 0.0625
    single_frequency_amplitude: float = 0.08
    dual_frequency_amplitude: float = 0.05
    stochastic_schedule_bound: float = 0.03
    min_schedule_multiplier: float = 0.70
    max_schedule_multiplier: float = 1.30
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
    novelty_truth: float
    uncertainty_truth: float
    expected_utility_truth: float
    risk_truth: float
    payload_sha256: str


@dataclass(frozen=True)
class UpdateRecord:
    shard_id: str
    slot: int
    target_shard_id: str
    before_fast: tuple[float, ...]
    after_fast: tuple[float, ...]
    before_slow: tuple[float, ...]
    after_slow: tuple[float, ...]
    before_importance: tuple[float, ...]
    after_importance: tuple[float, ...]
    learning_rate: float
    interference: float
    effect_sha256: str


@dataclass(frozen=True)
class SyntheticState:
    fast: tuple[float, ...]
    slow: tuple[float, ...]
    importance: tuple[float, ...]
    plasticity: float = 1.0
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
    memory_policy: str
    schedule_policy: str
    controller: str
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


def _validate_config(config: ProtocolConfig) -> None:
    numeric_fields = (
        "base_learning_rate",
        "slow_learning_rate",
        "ewc_strength",
        "plasticity_decay",
        "plasticity_recovery",
        "high_frequency",
        "low_frequency",
        "single_frequency_amplitude",
        "dual_frequency_amplitude",
        "stochastic_schedule_bound",
        "min_schedule_multiplier",
        "max_schedule_multiplier",
        "taxonomy_noise_bound",
        "risk_gate_threshold",
        "interference_limit",
    )
    for field in numeric_fields:
        _finite(getattr(config, field), field)
    integer_fields = (
        "dimension",
        "fit_shard_count",
        "tune_shard_count",
        "assessment_shard_count",
        "update_budget",
        "micro_updates_per_shard",
        "replay_capacity",
    )
    for field in integer_fields:
        value = getattr(config, field)
        _require(isinstance(value, int) and not isinstance(value, bool) and value > 0, f"{field} must be positive integer")
    _require(config.dimension == DIMENSION, "dimension is frozen")
    _require(config.fit_shard_count == FIT_SHARD_COUNT, "fit count is frozen")
    _require(config.tune_shard_count == TUNE_SHARD_COUNT, "tune count is frozen")
    _require(config.assessment_shard_count == ASSESSMENT_SHARD_COUNT, "assessment count is frozen")
    _require(config.update_budget == FIT_SHARD_COUNT, "update budget is frozen")
    _require(config.micro_updates_per_shard == MICRO_UPDATES_PER_SHARD, "micro update count is frozen")
    _require(config.high_frequency > config.low_frequency > 0.0, "frequencies must be ordered and positive")
    _require(config.min_schedule_multiplier < config.max_schedule_multiplier, "schedule bounds must be ordered")
    _require(0.0 <= config.taxonomy_noise_bound <= 1.0, "taxonomy noise bound must be in [0, 1]")
    _require(0.0 <= config.risk_gate_threshold <= 1.0, "risk threshold must be in [0, 1]")
    _require(config.replay_capacity >= 1, "replay capacity must be positive")
    _require(config.replicate_seeds == PREREGISTERED_REPLICATE_SEEDS, "replicate seed lock drift")
    _require(config.order_seeds == PREREGISTERED_ORDER_SEEDS, "order seed lock drift")


def _anchor(config: ProtocolConfig) -> tuple[float, ...]:
    return tuple(0.62 * math.sin((index + 1) * 1.13) for index in range(config.dimension))


def _target(config: ProtocolConfig, seed: int, split: str, index: int) -> tuple[float, ...]:
    _require(split in SPLITS, f"unknown split: {split}")
    anchor = _anchor(config)
    risk_draw = _unit(STATE_SLICE, seed, split, index, "risk-draw")
    amplitude = 0.07 + 1.20 * risk_draw if split == "fit" else 0.04 + 0.16 * risk_draw
    return tuple(
        anchor[component]
        + amplitude * _signed(STATE_SLICE, seed, split, index, component, "direction")
        for component in range(config.dimension)
    )


def _taxonomy_fields(config: ProtocolConfig, seed: int, split: str, index: int, target: Sequence[float]) -> tuple[float, float, float, float]:
    anchor = _anchor(config)
    distance = math.sqrt(sum((target[item] - anchor[item]) ** 2 for item in range(config.dimension)) / config.dimension)
    novelty = _clamp(distance / 1.20, 0.0, 1.0)
    uncertainty = _clamp(
        0.20 + 0.60 * _unit(STATE_SLICE, seed, split, index, "uncertainty-draw") + 0.20 * novelty,
        0.0,
        1.0,
    )
    utility = _clamp(1.0 - 0.75 * novelty - 0.25 * uncertainty, 0.0, 1.0)
    risk = _clamp(0.50 * novelty + 0.35 * uncertainty + 0.15 * (1.0 - utility), 0.0, 1.0)
    return novelty, uncertainty, utility, risk


def _shard_payload(shard: SyntheticShard) -> dict[str, Any]:
    return {
        "state_slice": STATE_SLICE,
        "shard_id": shard.shard_id,
        "split": shard.split,
        "index": shard.index,
        "target": list(shard.target),
        "novelty_truth": shard.novelty_truth,
        "uncertainty_truth": shard.uncertainty_truth,
        "expected_utility_truth": shard.expected_utility_truth,
        "risk_truth": shard.risk_truth,
    }


def make_panel(config: ProtocolConfig = ProtocolConfig(), seed: int = PREREGISTERED_REPLICATE_SEEDS[0]) -> tuple[SyntheticShard, ...]:
    """Generate fresh formula-derived fit, tune, and assessment shards."""

    _validate_config(config)
    counts = {"fit": config.fit_shard_count, "tune": config.tune_shard_count, "assessment": config.assessment_shard_count}
    shards: list[SyntheticShard] = []
    for split in SPLITS:
        for index in range(counts[split]):
            target = _target(config, seed, split, index)
            novelty, uncertainty, utility, risk = _taxonomy_fields(config, seed, split, index, target)
            draft = SyntheticShard(
                shard_id=f"{split}-{index:03d}",
                split=split,
                index=index,
                target=target,
                novelty_truth=novelty,
                uncertainty_truth=uncertainty,
                expected_utility_truth=utility,
                risk_truth=risk,
                payload_sha256="",
            )
            shards.append(replace(draft, payload_sha256=_digest(_shard_payload(draft))))
    return tuple(shards)


def panel_digest(panel: Sequence[SyntheticShard]) -> str:
    return _digest([asdict(shard) for shard in panel])


def split_digest(panel: Sequence[SyntheticShard], split: str) -> str:
    return _digest([asdict(shard) for shard in panel if shard.split == split])


def make_order(panel: Sequence[SyntheticShard], order_seed: int) -> tuple[SyntheticShard, ...]:
    fit = [shard for shard in panel if shard.split == "fit"]
    _require(len(fit) == FIT_SHARD_COUNT, "fit panel count drift")
    return tuple(sorted(fit, key=lambda shard: (_unit(STATE_SLICE, "order", order_seed, shard.shard_id), shard.index)))


def _schedule_multiplier_unchecked(schedule_policy: str, step: int, seed: int, shard_id: str, config: ProtocolConfig) -> float:
    _require(schedule_policy in SCHEDULE_POLICIES, f"unknown schedule policy: {schedule_policy}")
    if schedule_policy == "fixed":
        base = 1.0
    else:
        fast = config.single_frequency_amplitude * math.sin(2.0 * math.pi * config.high_frequency * step)
        base = 1.0 + fast
        if schedule_policy in ("dual_frequency", "bounded_stochastic_dual"):
            base += config.dual_frequency_amplitude * math.cos(2.0 * math.pi * config.low_frequency * step)
    if schedule_policy == "bounded_stochastic_dual":
        base *= 1.0 + config.stochastic_schedule_bound * _signed(STATE_SLICE, "schedule-jitter", seed, shard_id, step)
    return _clamp(base, config.min_schedule_multiplier, config.max_schedule_multiplier)


def schedule_multiplier(schedule_policy: str, step: int, seed: int, shard_id: str, config: ProtocolConfig = ProtocolConfig()) -> float:
    """Return a bounded fixed, single, dual, or seeded stochastic schedule."""

    _validate_config(config)
    return _schedule_multiplier_unchecked(schedule_policy, step, seed, shard_id, config)


def _effective(state: SyntheticState, memory_policy: str) -> tuple[float, ...]:
    if memory_policy in ("fast_slow", "integrated"):
        return tuple(0.70 * state.fast[index] + 0.30 * state.slow[index] for index in range(len(state.fast)))
    return state.fast


def _loss(parameters: Sequence[float], target: Sequence[float]) -> float:
    return 0.5 * sum((parameters[index] - target[index]) ** 2 for index in range(len(target))) / len(target)


def _surprise(parameters: Sequence[float], target: Sequence[float]) -> float:
    return _clamp(2.0 * _loss(parameters, target), 0.0, 1.0)


def _interference(
    before: Sequence[float],
    after: Sequence[float],
    state: SyntheticState,
    fit_by_id: Mapping[str, SyntheticShard],
    config: ProtocolConfig,
) -> float:
    targets = [_anchor(config)]
    targets.extend(fit_by_id[shard_id].target for shard_id in state.committed_shards)
    increases = [max(0.0, _loss(after, target) - _loss(before, target)) for target in targets]
    return _clamp(sum(increases) / len(increases), 0.0, 1.0)


def _effect_digest(
    shard_id: str,
    slot: int,
    target_shard_id: str,
    before_fast: Sequence[float],
    after_fast: Sequence[float],
    before_slow: Sequence[float],
    after_slow: Sequence[float],
    learning_rate: float,
    interference: float,
) -> str:
    return _digest(
        {
            "shard_id": shard_id,
            "slot": slot,
            "target_shard_id": target_shard_id,
            "before_fast": list(before_fast),
            "after_fast": list(after_fast),
            "before_slow": list(before_slow),
            "after_slow": list(after_slow),
            "learning_rate": learning_rate,
            "interference": interference,
        }
    )


def _event_digest(decision: Mapping[str, Any]) -> str:
    return _digest({key: decision[key] for key in decision if key != "event_sha256"})


def _initial_state(config: ProtocolConfig) -> SyntheticState:
    zero = (0.0,) * config.dimension
    return SyntheticState(fast=zero, slow=zero, importance=zero)


def _replay_target(
    state: SyntheticState,
    fit_by_id: Mapping[str, SyntheticShard],
    current: SyntheticShard,
    seed: int,
    step: int,
    config: ProtocolConfig,
) -> SyntheticShard:
    if not state.committed_shards:
        return current
    buffer = state.committed_shards[-config.replay_capacity :]
    chosen = buffer[int(_unit(STATE_SLICE, "replay", seed, current.shard_id, step) * len(buffer))]
    return fit_by_id[chosen]


def _micro_update(
    state: SyntheticState,
    target_shard: SyntheticShard,
    source_shard: SyntheticShard,
    slot: int,
    memory_policy: str,
    schedule_policy: str,
    seed: int,
    step: int,
    fit_by_id: Mapping[str, SyntheticShard],
    config: ProtocolConfig,
) -> tuple[SyntheticState, UpdateRecord, float]:
    before_fast = state.fast
    before_slow = state.slow
    before_importance = state.importance
    effective = _effective(state, memory_policy)
    multiplier = _schedule_multiplier_unchecked(
        schedule_policy,
        step * config.micro_updates_per_shard + slot,
        seed,
        source_shard.shard_id,
        config,
    )
    learning_rate = config.base_learning_rate * multiplier * state.plasticity
    if memory_policy in ("plasticity_guard", "integrated"):
        shrunk_fast = tuple((1.0 - config.plasticity_decay) * value for value in before_fast)
    else:
        shrunk_fast = before_fast
    ewc_penalty = (
        tuple(config.ewc_strength * before_importance[index] * (effective[index] - before_slow[index]) for index in range(config.dimension))
        if memory_policy in ("ewc", "integrated")
        else (0.0,) * config.dimension
    )
    after_fast = tuple(
        shrunk_fast[index]
        + learning_rate * (target_shard.target[index] - effective[index])
        - learning_rate * ewc_penalty[index]
        for index in range(config.dimension)
    )
    if memory_policy in ("fast_slow", "integrated"):
        after_slow = tuple(before_slow[index] + config.slow_learning_rate * (after_fast[index] - before_slow[index]) for index in range(config.dimension))
    elif memory_policy == "ewc":
        after_slow = tuple(before_slow[index] + config.slow_learning_rate * (after_fast[index] - before_slow[index]) for index in range(config.dimension))
    else:
        after_slow = before_slow
    if memory_policy in ("ewc", "integrated"):
        after_importance = tuple(
            before_importance[index] + 0.04 * (target_shard.target[index] - effective[index]) ** 2
            for index in range(config.dimension)
        )
    else:
        after_importance = before_importance
    candidate_effective = _effective(replace(state, fast=after_fast, slow=after_slow), memory_policy)
    interference = _interference(effective, candidate_effective, state, fit_by_id, config)
    surprise = _surprise(effective, target_shard.target)
    if memory_policy in ("plasticity_guard", "integrated"):
        after_plasticity = _clamp(
            state.plasticity - config.plasticity_decay + config.plasticity_recovery * surprise,
            MIN_PLASTICITY,
            1.0,
        )
    else:
        after_plasticity = state.plasticity
    after_state = replace(
        state,
        fast=after_fast,
        slow=after_slow,
        importance=after_importance,
        plasticity=after_plasticity,
    )
    delta = tuple(after_fast[index] - before_fast[index] for index in range(config.dimension))
    record = UpdateRecord(
        shard_id=source_shard.shard_id,
        slot=slot,
        target_shard_id=target_shard.shard_id,
        before_fast=before_fast,
        after_fast=after_fast,
        before_slow=before_slow,
        after_slow=after_slow,
        before_importance=before_importance,
        after_importance=after_importance,
        learning_rate=learning_rate,
        interference=interference,
        effect_sha256=_effect_digest(
            source_shard.shard_id,
            slot,
            target_shard.shard_id,
            before_fast,
            after_fast,
            before_slow,
            after_slow,
            learning_rate,
            interference,
        ),
    )
    return after_state, record, surprise


def _prepare_trial(
    panel: Sequence[SyntheticShard],
    memory_policy: str,
    schedule_policy: str,
    controller: str,
    taxonomy: str,
    seed: int,
    order_seed: int,
    config: ProtocolConfig,
) -> PreparedTrial:
    _require(memory_policy in MEMORY_POLICIES, f"unknown memory policy: {memory_policy}")
    _require(controller in CONTROLLERS, f"unknown controller: {controller}")
    fit_shards = [shard for shard in panel if shard.split == "fit"]
    fit_by_id = {shard.shard_id: shard for shard in fit_shards}
    ordered_fit = make_order(panel, order_seed)
    state = _initial_state(config)
    decisions: list[dict[str, Any]] = []
    ratio_sum = 0.0
    verification_checks = 0
    for step, shard in enumerate(ordered_fit):
        observed_risk = _taxonomy_value_unchecked(taxonomy, shard, fit_shards, seed, config)
        shadow = state
        records: list[UpdateRecord] = []
        surprises: list[float] = []
        for slot in range(config.micro_updates_per_shard):
            target_shard = shard
            if memory_policy in ("replay", "integrated") and slot == config.micro_updates_per_shard - 1:
                target_shard = _replay_target(shadow, fit_by_id, shard, seed, step, config)
            shadow, record, surprise = _micro_update(
                shadow,
                target_shard,
                shard,
                slot,
                memory_policy,
                schedule_policy,
                seed,
                step,
                fit_by_id,
                config,
            )
            records.append(record)
            surprises.append(surprise)
        initial_effective = _effective(state, memory_policy)
        final_effective = _effective(shadow, memory_policy)
        total_interference = _interference(initial_effective, final_effective, state, fit_by_id, config)
        adaptive = controller == "evidence_conditioned"
        verification_ratio = _clamp(0.15 + 0.80 * observed_risk, 0.0, 1.0) if adaptive else 0.0
        requires_verification = adaptive and observed_risk >= config.risk_gate_threshold
        selected = requires_verification and _unit(STATE_SLICE, "verification", seed, order_seed, shard.shard_id, step) < verification_ratio
        verification_cost = (1 + math.ceil(2.0 * observed_risk)) if selected else 0
        if not adaptive:
            accepted = True
            reason = "fixed_admission"
        elif not requires_verification:
            accepted = True
            reason = "low_risk_admission"
        elif not selected:
            accepted = False
            reason = "verification_slot_not_selected"
        elif total_interference > config.interference_limit:
            accepted = False
            reason = "exact_interference_check_failed"
        else:
            accepted = True
            reason = "exact_interference_check_passed"
        next_state = replace(
            state,
            version=state.version + 1,
            update_attempts=state.update_attempts + config.micro_updates_per_shard,
            gradient_compute_units=state.gradient_compute_units + config.micro_updates_per_shard * config.dimension,
            shadow_compute_units=state.shadow_compute_units + config.micro_updates_per_shard * config.dimension,
            verification_cost_units=state.verification_cost_units + verification_cost,
        )
        if accepted:
            next_state = replace(
                shadow,
                version=next_state.version,
                update_attempts=next_state.update_attempts,
                gradient_compute_units=next_state.gradient_compute_units,
                shadow_compute_units=next_state.shadow_compute_units,
                verification_cost_units=next_state.verification_cost_units,
                committed_shards=state.committed_shards + (shard.shard_id,),
                updates=state.updates + tuple(records),
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
            "total_interference": total_interference,
            "mean_surprise": sum(surprises) / len(surprises),
            "plasticity_after": next_state.plasticity,
            "accepted": accepted,
            "reason": reason,
            "effect_sha256": _digest([record.effect_sha256 for record in records]),
        }
        decision["event_sha256"] = _event_digest(decision)
        decisions.append(decision)
        ratio_sum += verification_ratio
        verification_checks += int(selected)
        state = next_state
    tune_shards = [shard for shard in panel if shard.split == "tune"]
    origin = (0.0,) * config.dimension
    final_parameters = _effective(state, memory_policy)
    tune_prediction = sum(_loss(origin, shard.target) - _loss(final_parameters, shard.target) for shard in tune_shards) / len(tune_shards)
    calibration_brier = sum((decision["observed_risk"] - decision["true_risk"]) ** 2 for decision in decisions) / len(decisions)
    return PreparedTrial(
        key=f"{memory_policy}|{schedule_policy}|{controller}|{taxonomy}|seed-{seed}|order-{order_seed}",
        memory_policy=memory_policy,
        schedule_policy=schedule_policy,
        controller=controller,
        taxonomy=taxonomy,
        seed=seed,
        order_seed=order_seed,
        state=state,
        tune_prediction=tune_prediction,
        calibration_brier=calibration_brier,
        verification_ratio_sum=ratio_sum,
        verification_checks=verification_checks,
        decision_digest=_digest(decisions),
    )


def _rollback_last(state: SyntheticState) -> tuple[SyntheticState, float]:
    _require(state.updates, "rollback requires a committed update")
    last_shard = state.committed_shards[-1]
    shard_records = [record for record in state.updates if record.shard_id == last_shard]
    _require(shard_records, "last committed shard has no update records")
    first = shard_records[0]
    error = max(
        [abs(state.fast[index] - shard_records[-1].after_fast[index]) for index in range(len(state.fast))]
        + [abs(state.slow[index] - shard_records[-1].after_slow[index]) for index in range(len(state.slow))]
        + [abs(state.importance[index] - shard_records[-1].after_importance[index]) for index in range(len(state.importance))]
    )
    restored = replace(
        state,
        fast=first.before_fast,
        slow=first.before_slow,
        importance=first.before_importance,
        committed_shards=state.committed_shards[:-1],
        rolled_back_shards=state.rolled_back_shards + (last_shard,),
        updates=state.updates[:-len(shard_records)],
        version=state.version + 1,
    )
    return restored, error


def _taxonomy_value_unchecked(
    taxonomy: str,
    shard: SyntheticShard,
    fit_shards: Sequence[SyntheticShard],
    seed: int,
    config: ProtocolConfig,
) -> float:
    _require(taxonomy in TAXONOMIES, f"unknown taxonomy: {taxonomy}")
    if taxonomy == "oracle":
        return shard.risk_truth
    if taxonomy == "noisy":
        return _clamp(shard.risk_truth + config.taxonomy_noise_bound * _signed(STATE_SLICE, "taxonomy-noise", seed, shard.shard_id), 0.0, 1.0)
    if taxonomy == "absent":
        return 0.5
    ordered = sorted(fit_shards, key=lambda item: (_unit(STATE_SLICE, "taxonomy-shuffle", seed, item.shard_id), item.index))
    position = next(index for index, item in enumerate(ordered) if item.shard_id == shard.shard_id)
    return ordered[(position + 1) % len(ordered)].risk_truth


def taxonomy_value(
    taxonomy: str,
    shard: SyntheticShard,
    fit_shards: Sequence[SyntheticShard],
    seed: int,
    config: ProtocolConfig = ProtocolConfig(),
) -> float:
    """Return controller-visible taxonomy after validating the public call."""

    _validate_config(config)
    return _taxonomy_value_unchecked(taxonomy, shard, fit_shards, seed, config)


def _mean(values: Sequence[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _forgetting(state: SyntheticState, fit_by_id: Mapping[str, SyntheticShard], memory_policy: str, config: ProtocolConfig) -> float:
    if not state.committed_shards:
        return 0.0
    parameters = _effective(state, memory_policy)
    targets = [fit_by_id[shard_id].target for shard_id in state.committed_shards]
    origin = _mean([_loss((0.0,) * config.dimension, target) for target in targets])
    after = _mean([_loss(parameters, target) for target in targets])
    return max(0.0, after - origin) / max(origin, 1e-12)


def _finalize_trial(prepared: PreparedTrial, panel: Sequence[SyntheticShard], lock_sha256: str, config: ProtocolConfig) -> dict[str, Any]:
    assessment_shards = [shard for shard in panel if shard.split == "assessment"]
    parameters = _effective(prepared.state, prepared.memory_policy)
    origin = (0.0,) * config.dimension
    baseline = _mean([_loss(origin, shard.target) for shard in assessment_shards])
    final = _mean([_loss(parameters, shard.target) for shard in assessment_shards])
    primary = baseline - final
    fit_by_id = {shard.shard_id: shard for shard in panel if shard.split == "fit"}
    forgetting = _forgetting(prepared.state, fit_by_id, prepared.memory_policy, config)
    rollback_state, rollback_error = _rollback_last(prepared.state) if prepared.state.updates else (prepared.state, 0.0)
    equal_compute = (
        prepared.state.update_attempts == config.update_budget * config.micro_updates_per_shard
        and prepared.state.gradient_compute_units == config.update_budget * config.micro_updates_per_shard * config.dimension
        and prepared.state.shadow_compute_units == config.update_budget * config.micro_updates_per_shard * config.dimension
    )
    return {
        "replicate_key": prepared.key,
        "memory_policy": prepared.memory_policy,
        "schedule_policy": prepared.schedule_policy,
        "controller": prepared.controller,
        "taxonomy": prepared.taxonomy,
        "seed": prepared.seed,
        "order_seed": prepared.order_seed,
        "tune_prediction": prepared.tune_prediction,
        "prediction_lock_sha256": lock_sha256,
        "prediction_locked_before_assessment": True,
        "assessment_baseline_loss": baseline,
        "assessment_final_loss": final,
        "primary_endpoint_value": primary,
        "committed_shards": list(prepared.state.committed_shards),
        "quarantined_shards": list(prepared.state.quarantined_shards),
        "committed_count": len(prepared.state.committed_shards),
        "quarantined_count": len(prepared.state.quarantined_shards),
        "final_fast": list(prepared.state.fast),
        "final_slow": list(prepared.state.slow),
        "final_importance": list(prepared.state.importance),
        "final_parameters": list(parameters),
        "final_plasticity": prepared.state.plasticity,
        "forgetting_value": forgetting,
        "calibration_brier": prepared.calibration_brier,
        "rollback_max_abs_error": rollback_error,
        "rollback_restored_fast": list(rollback_state.fast),
        "verification_ratio_mean": prepared.verification_ratio_sum / config.update_budget,
        "verification_checks": prepared.verification_checks,
        "verification_cost_units": prepared.state.verification_cost_units,
        "update_attempts": prepared.state.update_attempts,
        "gradient_compute_units": prepared.state.gradient_compute_units,
        "shadow_compute_units": prepared.state.shadow_compute_units,
        "decision_digest": prepared.decision_digest,
        "equal_update_compute_guard_pass": equal_compute,
        "forgetting_guard_pass": forgetting <= MAX_FORGETTING,
        "calibration_guard_pass": prepared.calibration_brier <= MAX_CALIBRATION_BRIER,
        "rollback_fidelity_guard_pass": rollback_error <= ROLLBACK_TOLERANCE,
        "plasticity_guard_pass": prepared.state.plasticity >= MIN_PLASTICITY,
        "verification_cost_guard_pass": prepared.state.verification_cost_units <= MAX_VERIFICATION_COST,
    }


def _cell_key(memory_policy: str, schedule_policy: str, controller: str, taxonomy: str) -> str:
    return f"{memory_policy}|{schedule_policy}|{controller}|{taxonomy}"


def _cell_summary(replicates: Sequence[Mapping[str, Any]], memory_policy: str, schedule_policy: str, controller: str, taxonomy: str) -> dict[str, Any]:
    primaries = [float(item["primary_endpoint_value"]) for item in replicates]
    by_seed: dict[int, list[float]] = {}
    for item in replicates:
        by_seed.setdefault(int(item["seed"]), []).append(float(item["primary_endpoint_value"]))
    order_range = max((max(values) - min(values) for values in by_seed.values()), default=0.0)
    compute_signatures = {(item["update_attempts"], item["gradient_compute_units"], item["shadow_compute_units"]) for item in replicates}
    guards = {
        "forgetting": all(bool(item["forgetting_guard_pass"]) for item in replicates),
        "calibration": all(bool(item["calibration_guard_pass"]) for item in replicates),
        "rollback_fidelity": all(bool(item["rollback_fidelity_guard_pass"]) for item in replicates),
        "plasticity": all(bool(item["plasticity_guard_pass"]) for item in replicates),
        "shard_order_stability": order_range <= MAX_ORDER_RANGE,
        "verification_cost": all(bool(item["verification_cost_guard_pass"]) for item in replicates),
        "equal_update_compute": len(compute_signatures) == 1 and all(bool(item["equal_update_compute_guard_pass"]) for item in replicates),
    }
    body = {
        "cell_key": _cell_key(memory_policy, schedule_policy, controller, taxonomy),
        "memory_policy": memory_policy,
        "schedule_policy": schedule_policy,
        "controller": controller,
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
    def primary(memory: str, schedule: str, controller: str = "evidence_conditioned", taxonomy: str = "oracle") -> float:
        return float(cells[_cell_key(memory, schedule, controller, taxonomy)]["primary_mean"])

    mechanism_deltas = {}
    base = primary("single", "fixed")
    for policy in MEMORY_POLICIES[1:]:
        mechanism_deltas[policy] = primary(policy, "fixed") - base
    return {
        "baseline_cell": _cell_key("single", "fixed", "evidence_conditioned", "oracle"),
        "memory_policy_deltas_vs_single_fixed": mechanism_deltas,
        "evidence_gating_delta_integrated_dual_oracle": primary("integrated", "dual_frequency") - primary("integrated", "dual_frequency", "fixed_admission"),
        "single_frequency_delta_vs_fixed_integrated_oracle": primary("integrated", "single_frequency") - primary("integrated", "fixed"),
        "dual_frequency_delta_vs_single_frequency_integrated_oracle": primary("integrated", "dual_frequency") - primary("integrated", "single_frequency"),
        "stochastic_dual_delta_vs_dual_integrated_oracle": primary("integrated", "bounded_stochastic_dual") - primary("integrated", "dual_frequency"),
        "all_learning_compute_equal": all(
            cell["guards"]["equal_update_compute"]
            for cell in cells.values()
        ),
        "astral_integration": "not_run_synthetic_controller_only",
    }


def run_factorial(config: ProtocolConfig = ProtocolConfig()) -> dict[str, Any]:
    """Run the 6 x 4 x 2 x 4 literature-informed factorial."""

    _validate_config(config)
    panels = {seed: make_panel(config, seed) for seed in config.replicate_seeds}
    prepared: list[PreparedTrial] = []
    for memory_policy in MEMORY_POLICIES:
        for schedule_policy in SCHEDULE_POLICIES:
            for controller in CONTROLLERS:
                for taxonomy in TAXONOMIES:
                    for seed in config.replicate_seeds:
                        for order_seed in config.order_seeds:
                            prepared.append(
                                _prepare_trial(
                                    panels[seed],
                                    memory_policy,
                                    schedule_policy,
                                    controller,
                                    taxonomy,
                                    seed,
                                    order_seed,
                                    config,
                                )
                            )
    lock_body = {
        "state_slice": STATE_SLICE,
        "lock_type": "fit_and_tune_predictions_only",
        "assessment_started": False,
        "predictions": [{"replicate_key": trial.key, "tune_prediction": trial.tune_prediction} for trial in prepared],
    }
    lock_sha256 = _digest(lock_body)
    finalized = [_finalize_trial(trial, panels[trial.seed], lock_sha256, config) for trial in prepared]
    cells: dict[str, dict[str, Any]] = {}
    for memory_policy in MEMORY_POLICIES:
        for schedule_policy in SCHEDULE_POLICIES:
            for controller in CONTROLLERS:
                for taxonomy in TAXONOMIES:
                    key = _cell_key(memory_policy, schedule_policy, controller, taxonomy)
                    cells[key] = _cell_summary(
                        [
                            item
                            for item in finalized
                            if item["memory_policy"] == memory_policy
                            and item["schedule_policy"] == schedule_policy
                            and item["controller"] == controller
                            and item["taxonomy"] == taxonomy
                        ],
                        memory_policy,
                        schedule_policy,
                        controller,
                        taxonomy,
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
        "memory_policies": list(MEMORY_POLICIES),
        "schedule_policies": list(SCHEDULE_POLICIES),
        "controllers": list(CONTROLLERS),
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
    _require(result.get("memory_policies") == list(MEMORY_POLICIES), "memory panel drift")
    _require(result.get("schedule_policies") == list(SCHEDULE_POLICIES), "schedule panel drift")
    _require(result.get("controllers") == list(CONTROLLERS), "controller panel drift")
    _require(result.get("taxonomies") == list(TAXONOMIES), "taxonomy panel drift")
    _require(result.get("claims") == list(CLAIMS), "claim ceiling drift")
    _require(result.get("factorial_cell_count") == len(MEMORY_POLICIES) * len(SCHEDULE_POLICIES) * len(CONTROLLERS) * len(TAXONOMIES), "factorial count drift")
    config_raw = result.get("config")
    _require(isinstance(config_raw, Mapping), "config must be an object")
    values = dict(config_raw)
    for field in ("replicate_seeds", "order_seeds"):
        if isinstance(values.get(field), list):
            values[field] = tuple(values[field])
    try:
        config = ProtocolConfig(**values)
    except (TypeError, ValueError) as exc:
        raise ProtocolError(f"invalid config: {exc}") from exc
    _validate_config(config)
    _require(result.get("preregistered_replicate_seeds") == list(PREREGISTERED_REPLICATE_SEEDS), "replicate seed lock drift")
    _require(result.get("preregistered_order_seeds") == list(PREREGISTERED_ORDER_SEEDS), "order seed lock drift")
    lock = result.get("prediction_lock")
    _require(isinstance(lock, Mapping), "prediction lock missing")
    _require(lock.get("assessment_started") is False, "assessment ordering drift")
    _require(result.get("prediction_lock_sha256") == _digest(lock), "prediction lock digest mismatch")
    cells = result.get("cells")
    _require(isinstance(cells, Mapping), "cells must be an object")
    expected_keys = {
        _cell_key(memory, schedule, controller, taxonomy)
        for memory in MEMORY_POLICIES
        for schedule in SCHEDULE_POLICIES
        for controller in CONTROLLERS
        for taxonomy in TAXONOMIES
    }
    _require(set(cells) == expected_keys, "factorial key set drift")
    for key in expected_keys:
        cell = cells[key]
        _require(cell.get("cell_key") == key, f"cell key mismatch: {key}")
        _require(cell.get("replicate_count") == len(PREREGISTERED_REPLICATE_SEEDS) * len(PREREGISTERED_ORDER_SEEDS), f"replicate count mismatch: {key}")
        _require(cell.get("cell_sha256") == _digest({field: cell[field] for field in cell if field != "cell_sha256"}), f"cell digest mismatch: {key}")
        _require(isinstance(cell.get("replicates"), list), f"replicates missing: {key}")
        for replicate in cell["replicates"]:
            _require(replicate.get("prediction_locked_before_assessment") is True, f"prediction ordering drift: {key}")
            _require(replicate.get("prediction_lock_sha256") == result["prediction_lock_sha256"], f"lock binding drift: {key}")
            for field in ("primary_endpoint_value", "assessment_baseline_loss", "assessment_final_loss", "forgetting_value", "calibration_brier", "final_plasticity"):
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
        "# Evidence-Conditioned Multiscale Plasticity v3",
        "",
        "Exact synthetic literature-informed controller only. No model, base weights, V48 artifacts, Astral introspection lane, ZK proof, or PQC proof.",
        "",
        f"Result SHA-256: `{result['result_sha256']}`",
        f"Prediction lock SHA-256: `{result['prediction_lock_sha256']}`",
        "",
        "| Memory | Schedule | Controller | Taxonomy | Primary mean | Eligible |",
        "|---|---|---|---|---:|---|",
    ]
    for key in sorted(result["cells"]):
        cell = result["cells"][key]
        lines.append(
            f"| `{cell['memory_policy']}` | `{cell['schedule_policy']}` | `{cell['controller']}` | `{cell['taxonomy']}` | "
            f"{cell['primary_mean']:.8f} | {cell['eligible_for_controller_comparison']} |"
        )
    lines.extend(
        [
            "",
            "Primary endpoint: held-out adaptation improvement after the fixed 24-shard, 48-micro-update budget.",
            "All arms use equal update, gradient, and shadow compute; verification cost is separate overhead.",
            "Claim ceiling: local exact-synthetic literature-informed controller mechanics only.",
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
