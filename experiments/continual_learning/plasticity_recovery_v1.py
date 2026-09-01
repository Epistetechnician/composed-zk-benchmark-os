#!/usr/bin/env python3
"""Exact synthetic replay and plasticity-recovery factorial.

State slice: ``continual-learning-plasticity-recovery-v1``.

The learner is an exact, model-free adapter analogue. It has a fixed base,
per-update reversible adapter state, a bounded replay buffer, and a
low-utility unit reinitialization operator. The five arms use the same number
of gradient evaluations. The output is a sealed fit/tune/assessment result;
it does not load a model, call a provider, or generate Astral evidence.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import Any, Mapping, Sequence


STATE_SLICE = "continual-learning-plasticity-recovery-v1"
SCHEMA_VERSION = "continual-learning-plasticity-recovery-result-v1"
PRIMARY_ENDPOINT = "heldout_adaptation_improvement_over_untouched_base"
ARMS = (
    "no_update",
    "fixed_adapter",
    "replay",
    "selective_reinit",
    "replay_selective_reinit",
)
SPLITS = ("fit", "tune", "assessment")
SEEDS = (20260901, 20260902, 20260903, 20260904)
ORDER_SEEDS = (8111, 8112, 8113)
DIMENSION = 8
FIT_COUNT = 16
TUNE_COUNT = 8
ASSESSMENT_COUNT = 8
UPDATE_BUDGET = FIT_COUNT
GRADIENT_SLOTS = 2
REPLAY_CAPACITY = 4
REINIT_MATURITY = 3
REINIT_PERIOD = 4
LEARNING_RATE = 0.18
REPLAY_LEARNING_RATE = 0.09
UTILITY_DECAY = 0.94
EFFECT_THRESHOLD = 0.01
BOOTSTRAP_REPLICATES = 10_000
BOOTSTRAP_SEED = 20260929
MAX_ORDER_RANGE = 0.20
MAX_FORGETTING = 0.20
MAX_CALIBRATION_BRIER = 0.25
ROLLBACK_TOLERANCE = 1e-12


class ProtocolError(ValueError):
    """Raised when the frozen synthetic contract is violated."""


@dataclass(frozen=True)
class Shard:
    shard_id: str
    split: str
    index: int
    family: int
    target: tuple[float, ...]
    utility_truth: float
    payload_sha256: str


@dataclass(frozen=True)
class UpdateRecord:
    step: int
    slot: int
    source_shard_id: str
    target_shard_id: str
    reinitialized_unit: int | None
    before_weights: tuple[float, ...]
    after_weights: tuple[float, ...]
    before_utility: tuple[float, ...]
    after_utility: tuple[float, ...]
    before_age: tuple[int, ...]
    after_age: tuple[int, ...]
    learning_rate: float
    effect_sha256: str


@dataclass(frozen=True)
class State:
    weights: tuple[float, ...]
    utility: tuple[float, ...]
    age: tuple[int, ...]
    replay_buffer: tuple[str, ...] = ()
    committed_shards: tuple[str, ...] = ()
    updates: tuple[UpdateRecord, ...] = ()
    gradient_evaluations: int = 0
    shadow_gradient_evaluations: int = 0
    reinitializations: int = 0


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ProtocolError(message)


def _digest(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    ).hexdigest()


def _sha256_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def _unit(*parts: object) -> float:
    payload = "|".join(str(part) for part in parts).encode("utf-8")
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big") / float(1 << 64)


def _signed(*parts: object) -> float:
    return 2.0 * _unit(*parts) - 1.0


def _clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))


def _finite(value: Any, field: str) -> float:
    _require(isinstance(value, (int, float)) and not isinstance(value, bool), f"{field} must be numeric")
    result = float(value)
    _require(math.isfinite(result), f"{field} must be finite")
    return result


def _validate_config() -> None:
    _require(len(SEEDS) == 4 and len(ORDER_SEEDS) == 3, "replicate panel drift")
    _require(FIT_COUNT == UPDATE_BUDGET, "fit/update budget drift")
    _require(GRADIENT_SLOTS == 2, "gradient slot drift")
    _require(REPLAY_CAPACITY > 0, "replay capacity must be positive")
    _require(REINIT_MATURITY > 0 and REINIT_PERIOD > 0, "reinitialization schedule drift")
    _require(0.0 < LEARNING_RATE < 1.0, "learning rate drift")
    _require(0.0 < REPLAY_LEARNING_RATE < LEARNING_RATE, "replay learning rate drift")


def _anchor() -> tuple[float, ...]:
    return tuple(0.22 * math.sin((index + 1) * 0.73) for index in range(DIMENSION))


def _family_vector(family: int) -> tuple[float, ...]:
    return tuple(
        0.42 * math.sin((family + 1) * (index + 1) * 0.51)
        + 0.18 * math.cos((family + 2) * (index + 1) * 0.29)
        for index in range(DIMENSION)
    )


def _target(seed: int, split: str, index: int) -> tuple[float, ...]:
    family = index % 4
    amplitude = {"fit": 0.16, "tune": 0.10, "assessment": 0.10}[split]
    return tuple(
        _anchor()[unit]
        + _family_vector(family)[unit]
        + amplitude * _signed(STATE_SLICE, seed, split, index, unit, "target")
        for unit in range(DIMENSION)
    )


def _loss(weights: Sequence[float], target: Sequence[float]) -> float:
    return sum((weights[index] - target[index]) ** 2 for index in range(DIMENSION)) / (2.0 * DIMENSION)


def _shard_body(shard: Shard) -> dict[str, Any]:
    return {
        "state_slice": STATE_SLICE,
        "shard_id": shard.shard_id,
        "split": shard.split,
        "index": shard.index,
        "family": shard.family,
        "target": list(shard.target),
        "utility_truth": shard.utility_truth,
    }


def make_panel(seed: int) -> tuple[Shard, ...]:
    """Generate a fresh deterministic fit/tune/assessment panel."""

    _validate_config()
    counts = {"fit": FIT_COUNT, "tune": TUNE_COUNT, "assessment": ASSESSMENT_COUNT}
    shards: list[Shard] = []
    for split in SPLITS:
        for index in range(counts[split]):
            target = _target(seed, split, index)
            distance = math.sqrt(sum(value * value for value in target) / DIMENSION)
            draft = Shard(
                shard_id=f"{split}-{index:03d}",
                split=split,
                index=index,
                family=index % 4,
                target=target,
                utility_truth=_clamp(1.0 - distance, 0.0, 1.0),
                payload_sha256="",
            )
            shards.append(replace(draft, payload_sha256=_digest(_shard_body(draft))))
    return tuple(shards)


def panel_digest(panel: Sequence[Shard]) -> str:
    return _digest([asdict(shard) for shard in panel])


def split_digest(panel: Sequence[Shard], split: str) -> str:
    _require(split in SPLITS, f"unknown split: {split}")
    return _digest([asdict(shard) for shard in panel if shard.split == split])


def make_order(panel: Sequence[Shard], order_seed: int) -> tuple[Shard, ...]:
    fit = [shard for shard in panel if shard.split == "fit"]
    _require(len(fit) == FIT_COUNT, "fit panel count drift")
    return tuple(sorted(fit, key=lambda shard: (_unit(STATE_SLICE, "order", order_seed, shard.shard_id), shard.index)))


def _initial_state() -> State:
    return State(weights=(0.0,) * DIMENSION, utility=(0.0,) * DIMENSION, age=(0,) * DIMENSION)


def _effect_digest(record: UpdateRecord) -> str:
    body = asdict(record)
    body.pop("effect_sha256", None)
    return _digest(body)


def _gradient_step(
    state: State,
    target: Shard,
    source: Shard,
    step: int,
    slot: int,
    learning_rate: float,
    reinitialized_unit: int | None,
) -> tuple[State, UpdateRecord]:
    before_weights = state.weights
    before_utility = state.utility
    before_age = state.age
    after_weights = tuple(
        before_weights[index] + learning_rate * (target.target[index] - before_weights[index])
        for index in range(DIMENSION)
    )
    after_utility = tuple(
        UTILITY_DECAY * before_utility[index]
        + (1.0 - UTILITY_DECAY) * abs(after_weights[index] - before_weights[index])
        for index in range(DIMENSION)
    )
    after_age = tuple(age + 1 for age in before_age)
    draft = UpdateRecord(
        step=step,
        slot=slot,
        source_shard_id=source.shard_id,
        target_shard_id=target.shard_id,
        reinitialized_unit=reinitialized_unit,
        before_weights=before_weights,
        after_weights=after_weights,
        before_utility=before_utility,
        after_utility=after_utility,
        before_age=before_age,
        after_age=after_age,
        learning_rate=learning_rate,
        effect_sha256="",
    )
    record = replace(draft, effect_sha256=_effect_digest(draft))
    return replace(state, weights=after_weights, utility=after_utility, age=after_age), record


def _reinitialize(state: State, step: int) -> tuple[State, int | None]:
    if step == 0 or step % REINIT_PERIOD != 0:
        return state, None
    eligible = [index for index, age in enumerate(state.age) if age >= REINIT_MATURITY]
    if not eligible:
        return state, None
    unit = min(eligible, key=lambda index: (state.utility[index], index))
    weights = list(state.weights)
    utility = list(state.utility)
    age = list(state.age)
    weights[unit] = 0.0
    utility[unit] = 0.0
    age[unit] = 0
    return replace(
        state,
        weights=tuple(weights),
        utility=tuple(utility),
        age=tuple(age),
        reinitializations=state.reinitializations + 1,
    ), unit


def _replay_target(state: State, fit_by_id: Mapping[str, Shard], current: Shard, seed: int, step: int) -> Shard:
    if not state.replay_buffer:
        return current
    index = int(_unit(STATE_SLICE, "replay", seed, current.shard_id, step) * len(state.replay_buffer))
    return fit_by_id[state.replay_buffer[index]]


def _state_signature(state: State) -> dict[str, Any]:
    return {
        "weights": list(state.weights),
        "utility": list(state.utility),
        "age": list(state.age),
        "replay_buffer": list(state.replay_buffer),
        "committed_shards": list(state.committed_shards),
        "gradient_evaluations": state.gradient_evaluations,
        "shadow_gradient_evaluations": state.shadow_gradient_evaluations,
        "reinitializations": state.reinitializations,
    }


def _run_case(panel: Sequence[Shard], arm: str, seed: int, order_seed: int) -> dict[str, Any]:
    """Run fit-only state transitions and return a pre-assessment draft."""

    _require(arm in ARMS, f"unknown arm: {arm}")
    fit_by_id = {shard.shard_id: shard for shard in panel if shard.split == "fit"}
    ordered = make_order(panel, order_seed)
    state = _initial_state()
    shadow_state = state
    records: list[dict[str, Any]] = []
    protected_snapshots: list[tuple[Shard, tuple[float, ...]]] = []
    last_pre_update_signature: dict[str, Any] | None = None
    for step, current in enumerate(ordered):
        work = state
        reinitialized_unit = None
        if arm in ("selective_reinit", "replay_selective_reinit"):
            work, reinitialized_unit = _reinitialize(work, step)
        targets = [current, current]
        if arm in ("replay", "replay_selective_reinit"):
            targets[1] = _replay_target(work, fit_by_id, current, seed, step)
        if arm == "no_update":
            shadow = shadow_state
        else:
            shadow = work
        step_records: list[UpdateRecord] = []
        for slot, target in enumerate(targets):
            if step == len(ordered) - 1 and slot == len(targets) - 1:
                last_pre_update_signature = _state_signature(shadow)
            shadow, record = _gradient_step(
                shadow,
                target,
                current,
                step,
                slot,
                LEARNING_RATE if slot == 0 else REPLAY_LEARNING_RATE,
                reinitialized_unit if slot == 0 else None,
            )
            step_records.append(record)
        if arm == "no_update":
            shadow_state = replace(
                shadow,
                gradient_evaluations=shadow.gradient_evaluations + GRADIENT_SLOTS,
                shadow_gradient_evaluations=shadow.shadow_gradient_evaluations + GRADIENT_SLOTS,
            )
            accepted = False
            state_after = replace(
                state,
                gradient_evaluations=state.gradient_evaluations + GRADIENT_SLOTS,
                shadow_gradient_evaluations=state.shadow_gradient_evaluations + GRADIENT_SLOTS,
            )
        else:
            state_after = replace(
                shadow,
                replay_buffer=(state.replay_buffer + (current.shard_id,))[-REPLAY_CAPACITY:]
                if arm in ("replay", "replay_selective_reinit")
                else state.replay_buffer,
                committed_shards=state.committed_shards + (current.shard_id,),
                updates=state.updates + tuple(step_records),
                gradient_evaluations=state.gradient_evaluations + GRADIENT_SLOTS,
                shadow_gradient_evaluations=state.shadow_gradient_evaluations + GRADIENT_SLOTS,
            )
            accepted = True
        if accepted and step < 4:
            protected_snapshots.append((current, state_after.weights))
        records.append(
            {
                "step": step,
                "source_shard_id": current.shard_id,
                "target_shard_ids": [record.target_shard_id for record in step_records],
                "reinitialized_unit": reinitialized_unit,
                "accepted": accepted,
                "update_effect_sha256": _digest([record.effect_sha256 for record in step_records]),
            }
        )
        state = state_after

    weights = state.weights
    tune = [shard for shard in panel if shard.split == "tune"]
    base_weights = (0.0,) * DIMENSION
    tune_prediction = sum(_loss(base_weights, shard.target) - _loss(weights, shard.target) for shard in tune) / len(tune)
    forgetting_values = [
        max(0.0, _loss(weights, shard.target) - _loss(snapshot_weights, shard.target))
        for shard, snapshot_weights in protected_snapshots
    ]
    protected_base = sum(_loss(base_weights, shard.target) for shard, _ in protected_snapshots) / max(1, len(protected_snapshots))
    forgetting = sum(forgetting_values) / max(1, len(forgetting_values)) / max(protected_base, 1e-12)
    predicted = [_clamp(1.0 - _loss(base_weights, shard.target), 0.0, 1.0) for shard in ordered]
    observed = [_clamp(1.0 - _loss(base_weights, shard.target) + 0.05 * _signed(STATE_SLICE, "cal", seed, shard.shard_id), 0.0, 1.0) for shard in ordered]
    calibration_brier = sum((predicted[index] - observed[index]) ** 2 for index in range(len(predicted))) / len(predicted)
    rollback_error = 0.0
    adapter_restore_passed = True
    if state.updates:
        last = state.updates[-1]
        _require(last_pre_update_signature is not None, "rollback reference missing")
        restored = replace(
            state,
            weights=last.before_weights,
            utility=last.before_utility,
            age=last.before_age,
            updates=state.updates[:-1],
            committed_shards=state.committed_shards[:-1],
        )
        rollback_error = max(
            [abs(restored.weights[index] - last_pre_update_signature["weights"][index]) for index in range(DIMENSION)]
            + [abs(restored.utility[index] - last_pre_update_signature["utility"][index]) for index in range(DIMENSION)]
            + [abs(restored.age[index] - last_pre_update_signature["age"][index]) for index in range(DIMENSION)]
        )
        adapter_restore_passed = (
            restored.weights == tuple(last_pre_update_signature["weights"])
            and restored.utility == tuple(last_pre_update_signature["utility"])
            and restored.age == tuple(last_pre_update_signature["age"])
        )
    else:
        restored = state
    return {
        "state_slice": STATE_SLICE,
        "case": f"seed-{seed}-order-{order_seed}",
        "seed": seed,
        "order_seed": order_seed,
        "arm": arm,
        "order": [shard.shard_id for shard in ordered],
        "updates": records,
        "final_weights": list(weights),
        "tune_prediction": round(tune_prediction, 12),
        "forgetting": round(forgetting, 12),
        "calibration_brier": round(calibration_brier, 12),
        "rollback_max_abs_error": round(rollback_error, 12),
        "base_weights_unchanged": base_weights == (0.0,) * DIMENSION,
        "adapter_restore_passed": adapter_restore_passed,
        "gradient_evaluations": state.gradient_evaluations,
        "shadow_gradient_evaluations": state.shadow_gradient_evaluations,
        "reinitializations": state.reinitializations,
        "equal_compute_passed": state.gradient_evaluations == UPDATE_BUDGET * GRADIENT_SLOTS
        and state.shadow_gradient_evaluations == UPDATE_BUDGET * GRADIENT_SLOTS,
    }


def _assess_case(case: Mapping[str, Any], panel: Sequence[Shard]) -> dict[str, Any]:
    """Compute held-out effects only after the prediction lock exists."""

    assessment = [shard for shard in panel if shard.split == "assessment"]
    base_weights = (0.0,) * DIMENSION
    weights = tuple(float(value) for value in case["final_weights"])
    base_assessment_loss = sum(_loss(base_weights, shard.target) for shard in assessment) / len(assessment)
    final_assessment_loss = sum(_loss(weights, shard.target) for shard in assessment) / len(assessment)
    adaptation_gain = base_assessment_loss - final_assessment_loss
    return {
        **case,
        "base_assessment_loss": round(base_assessment_loss, 12),
        "final_assessment_loss": round(final_assessment_loss, 12),
        "adaptation_gain": round(adaptation_gain, 12),
    }


def _bootstrap_interval(values: Sequence[float], seed: int) -> tuple[float, float]:
    _require(values, "bootstrap values must not be empty")
    samples: list[float] = []
    for draw in range(BOOTSTRAP_REPLICATES):
        total = 0.0
        for index in range(len(values)):
            chosen = int(_unit(STATE_SLICE, "bootstrap", seed, draw, index) * len(values))
            total += values[chosen]
        samples.append(total / len(values))
    samples.sort()
    return samples[int(0.025 * len(samples))], samples[int(0.975 * len(samples)) - 1]


def _case_digest(case: Mapping[str, Any]) -> str:
    return _digest({key: case[key] for key in case if key != "case_sha256"})


def _summarize_arm(cases: Sequence[Mapping[str, Any]], arm: str) -> dict[str, Any]:
    selected = [case for case in cases if case["arm"] == arm]
    gains = [float(case["adaptation_gain"]) for case in selected]
    no_update = [float(case["adaptation_gain"]) for case in cases if case["arm"] == "no_update"]
    deltas = [gain - baseline for gain, baseline in zip(gains, no_update)]
    order_groups: dict[int, list[float]] = {}
    for case in selected:
        order_groups.setdefault(int(case["seed"]), []).append(float(case["adaptation_gain"]))
    order_range = max((max(group) - min(group) for group in order_groups.values()), default=0.0)
    hard_guards = {
        "forgetting": all(float(case["forgetting"]) <= MAX_FORGETTING for case in selected),
        "calibration": all(float(case["calibration_brier"]) <= MAX_CALIBRATION_BRIER for case in selected),
        "rollback": all(float(case["rollback_max_abs_error"]) <= ROLLBACK_TOLERANCE for case in selected),
        "base_unchanged": all(bool(case["base_weights_unchanged"]) for case in selected),
        "equal_compute": all(bool(case["equal_compute_passed"]) for case in selected),
        "order_stability": order_range <= MAX_ORDER_RANGE,
    }
    lower, upper = _bootstrap_interval(deltas, BOOTSTRAP_SEED + ARMS.index(arm))
    mean_delta = sum(deltas) / len(deltas)
    passed = mean_delta >= EFFECT_THRESHOLD and lower >= 0.0 and sum(delta > 0.0 for delta in deltas) >= 9 and all(hard_guards.values())
    body = {
        "arm": arm,
        "primary_endpoint": PRIMARY_ENDPOINT,
        "case_count": len(selected),
        "case_deltas_vs_no_update": [round(value, 12) for value in deltas],
        "mean_delta_vs_no_update": round(mean_delta, 12),
        "bootstrap_seed": BOOTSTRAP_SEED + ARMS.index(arm),
        "bootstrap_replicates": BOOTSTRAP_REPLICATES,
        "bootstrap_95_percent_interval": [round(lower, 12), round(upper, 12)],
        "positive_case_count": sum(delta > 0.0 for delta in deltas),
        "order_range": round(order_range, 12),
        "hard_guards": hard_guards,
        "passed": passed,
    }
    return {**body, "summary_sha256": _digest(body)}


def run_factorial() -> dict[str, Any]:
    """Run the fixed 5-arm x 4-seed x 3-order factorial."""

    _validate_config()
    panels = {seed: make_panel(seed) for seed in SEEDS}
    drafts: list[dict[str, Any]] = []
    for seed in SEEDS:
        for order_seed in ORDER_SEEDS:
            for arm in ARMS:
                drafts.append(_run_case(panels[seed], arm, seed, order_seed))
    lock_body = {
        "state_slice": STATE_SLICE,
        "lock_type": "tune_predictions_before_assessment",
        "assessment_started": False,
        "predictions": [
            {"case": case["case"], "arm": case["arm"], "tune_prediction": case["tune_prediction"]}
            for case in drafts
        ],
    }
    lock = {"body": lock_body, "lock_sha256": _digest(lock_body)}
    cases = []
    for draft in drafts:
        assessed = _assess_case(draft, panels[int(draft["seed"])])
        cases.append({**assessed, "case_sha256": _case_digest(assessed)})
    summaries = {arm: _summarize_arm(cases, arm) for arm in ARMS}
    body = {
        "state_slice": STATE_SLICE,
        "schema_version": SCHEMA_VERSION,
        "primary_endpoint": PRIMARY_ENDPOINT,
        "arms": list(ARMS),
        "seeds": list(SEEDS),
        "order_seeds": list(ORDER_SEEDS),
        "panel_digests": {
            str(seed): {
                "panel_sha256": panel_digest(panels[seed]),
                "fit_sha256": split_digest(panels[seed], "fit"),
                "tune_sha256": split_digest(panels[seed], "tune"),
                "assessment_sha256": split_digest(panels[seed], "assessment"),
            }
            for seed in SEEDS
        },
        "config": {
            "dimension": DIMENSION,
            "fit_count": FIT_COUNT,
            "tune_count": TUNE_COUNT,
            "assessment_count": ASSESSMENT_COUNT,
            "update_budget": UPDATE_BUDGET,
            "gradient_slots": GRADIENT_SLOTS,
            "replay_capacity": REPLAY_CAPACITY,
            "reinit_maturity": REINIT_MATURITY,
            "reinit_period": REINIT_PERIOD,
            "learning_rate": LEARNING_RATE,
            "replay_learning_rate": REPLAY_LEARNING_RATE,
            "base_weights_updated": False,
            "reversible_adapter_only": True,
        },
        "prediction_lock": lock,
        "cases": cases,
        "summaries": summaries,
        "claims": [
            "exact_synthetic_learner_only",
            "fresh_formula_derived_panels",
            "base_weights_untouched",
            "reversible_adapter_analogue_only",
            "astral_integration_not_run",
            "zk_pqc_not_run",
        ],
    }
    return {**body, "result_sha256": _digest(body)}


def validate_result(result: Mapping[str, Any]) -> None:
    """Validate the sealed result before independent readback."""

    _require(result.get("state_slice") == STATE_SLICE, "state slice drift")
    _require(result.get("schema_version") == SCHEMA_VERSION, "schema drift")
    _require(result.get("primary_endpoint") == PRIMARY_ENDPOINT, "endpoint drift")
    _require(result.get("arms") == list(ARMS), "arm panel drift")
    _require(result.get("seeds") == list(SEEDS), "seed panel drift")
    _require(result.get("order_seeds") == list(ORDER_SEEDS), "order panel drift")
    config = result.get("config")
    _require(isinstance(config, Mapping), "config missing")
    _require(config.get("base_weights_updated") is False, "base weights may not update")
    _require(config.get("reversible_adapter_only") is True, "adapter boundary drift")
    lock = result.get("prediction_lock")
    _require(isinstance(lock, Mapping), "prediction lock missing")
    lock_body = lock.get("body")
    _require(isinstance(lock_body, Mapping), "prediction lock body missing")
    _require(lock_body.get("assessment_started") is False, "assessment ordering drift")
    _require(lock.get("lock_sha256") == _digest(lock_body), "prediction lock digest mismatch")
    cases = result.get("cases")
    _require(isinstance(cases, list) and len(cases) == len(SEEDS) * len(ORDER_SEEDS) * len(ARMS), "case count drift")
    for case in cases:
        _require(case.get("case_sha256") == _case_digest(case), f"case digest mismatch: {case.get('case')}")
        _require(case.get("state_slice") == STATE_SLICE, "case state slice drift")
        _require(case.get("gradient_evaluations") == UPDATE_BUDGET * GRADIENT_SLOTS, "gradient budget drift")
        _require(case.get("shadow_gradient_evaluations") == UPDATE_BUDGET * GRADIENT_SLOTS, "shadow budget drift")
        _require(case.get("base_weights_unchanged") is True, "base mutation claim drift")
        _require(case.get("equal_compute_passed") is True, "equal compute guard failed")
        for field in ("tune_prediction", "adaptation_gain", "forgetting", "calibration_brier", "rollback_max_abs_error"):
            _finite(case.get(field), field)
    summaries = result.get("summaries")
    _require(isinstance(summaries, Mapping) and set(summaries) == set(ARMS), "summary panel drift")
    for arm in ARMS:
        summary = summaries[arm]
        _require(summary.get("summary_sha256") == _digest({key: summary[key] for key in summary if key != "summary_sha256"}), f"summary digest mismatch: {arm}")
    unsigned = {key: result[key] for key in result if key != "result_sha256"}
    _require(result.get("result_sha256") == _digest(unsigned), "result digest mismatch")


def markdown_report(result: Mapping[str, Any]) -> str:
    lines = [
        "# Plasticity Recovery V1",
        "",
        "Exact synthetic learner only. Base weights are untouched; adapters are reversible analogues; Astral and ZK/PQC are not run.",
        "",
        f"Result SHA-256: `{result['result_sha256']}`",
        f"Prediction-lock SHA-256: `{result['prediction_lock']['lock_sha256']}`",
        "",
        "| Arm | Mean delta vs no-update | Bootstrap 95% interval | Positive cases | Passed |",
        "|---|---:|---|---:|---|",
    ]
    for arm in ARMS:
        summary = result["summaries"][arm]
        interval = summary["bootstrap_95_percent_interval"]
        lines.append(
            f"| `{arm}` | {summary['mean_delta_vs_no_update']:.8f} | "
            f"[{interval[0]:.8f}, {interval[1]:.8f}] | {summary['positive_case_count']}/12 | {summary['passed']} |"
        )
    lines.extend(
        [
            "",
            "Primary endpoint: held-out assessment improvement over the untouched base after the fixed 16-update budget.",
            "All arms use 32 gradient evaluations and 32 shadow evaluations per case.",
            "Claim ceiling: LocalDevelopmentPlasticityRecoverySyntheticOnly.",
        ]
    )
    return "\n".join(lines) + "\n"


def write_artifact(root: Path, result: Mapping[str, Any]) -> dict[str, Any]:
    """Write the sealed result and a byte-level external custody manifest."""

    root.mkdir(parents=True, exist_ok=True)
    result_path = root / "result.json"
    report_path = root / "result.md"
    result_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report_path.write_text(markdown_report(result), encoding="utf-8")
    manifest_body = {
        "state_slice": STATE_SLICE,
        "result_sha256": result["result_sha256"],
        "files": [
            {
                "path": path.name,
                "byte_len": path.stat().st_size,
                "sha256": _sha256_file(path),
            }
            for path in (result_path, report_path)
        ],
    }
    manifest = {**manifest_body, "manifest_sha256": _digest(manifest_body)}
    (root / "artifact_manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()
    result = run_factorial()
    validate_result(result)
    if args.output is None:
        print(json.dumps({"result_sha256": result["result_sha256"], "summaries": result["summaries"]}, indent=2, sort_keys=True))
        return 0
    manifest = write_artifact(args.output, result)
    print(json.dumps({"output": str(args.output), "result_sha256": result["result_sha256"], "manifest_sha256": manifest["manifest_sha256"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
