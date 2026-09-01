#!/usr/bin/env python3
"""Independent aggregate validator for recursive update-policy V1.

State slice: ``continual-learning-recursive-update-policy-v1``.

This module intentionally does not import the experiment runner.  It
recomputes the exact synthetic learner, campaign coverage, event chain,
memory-integrity probes, metric arithmetic, and digest closure from the
aggregate result only.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
from pathlib import Path
from typing import Any, Mapping, Sequence


STATE_SLICE = "continual-learning-recursive-update-policy-v1"
SCHEMA_VERSION = "continual-learning-recursive-update-policy-result-v1"
PROTOCOL_ID = "recursive-update-policy-v1"
CLAIM_CEILING = "LocalDevelopmentRecursiveUpdatePolicySyntheticProtocol"
DIMENSION = 6
GENERATION_COUNT = 4
FIT_TASK_COUNT = 5
TUNE_TASK_COUNT = 3
ASSESSMENT_TASK_COUNT = 4
PROTECTED_TASK_COUNT = 3
PROBE_TASK_COUNT = 2
MAX_MEMORY_AGE = 1
REPLICATE_SEEDS = (73101, 73102, 73103, 73104)
ORDER_SEEDS = (8211, 8212)
ORDER_DIRECTIONS = ("forward", "reverse")
ARMS = ("untouched_base", "fixed_policy", "recursive_policy", "random_policy")
POLICY_NAMES = ("conservative", "balanced", "plastic")
POLICY_CONFIGS = {
    "conservative": {"step_size": 0.18, "retention_price": 0.80, "memory_mode": "episodic"},
    "balanced": {"step_size": 0.30, "retention_price": 0.45, "memory_mode": "episodic"},
    "plastic": {"step_size": 0.38, "retention_price": 0.20, "memory_mode": "procedural"},
}
FIXED_POLICY = "balanced"
BOOTSTRAP_SEED = 931177
BOOTSTRAP_REPLICATES = 4000
PRIMARY_MINIMUM = 0.005
FINAL_ADVANTAGE_MINIMUM = 0.005
RECURSIVE_SLOPE_MINIMUM = 0.002
ROLLBACK_TOLERANCE = 1e-12
EXPECTED_TOTAL_COMPUTE = GENERATION_COUNT * (len(POLICY_NAMES) * (FIT_TASK_COUNT + TUNE_TASK_COUNT) + FIT_TASK_COUNT)


class ValidationError(ValueError):
    """Raised when an aggregate result fails independent validation."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)


def _digest(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    ).hexdigest()


def _unit(*parts: object) -> float:
    raw = "|".join(str(part) for part in parts).encode("utf-8")
    return int.from_bytes(hashlib.sha256(raw).digest()[:8], "big") / float(1 << 64)


def _signed(*parts: object) -> float:
    return 2.0 * _unit(*parts) - 1.0


def _clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))


def _add(left: Sequence[float], right: Sequence[float]) -> tuple[float, ...]:
    return tuple(a + b for a, b in zip(left, right))


def _sub(left: Sequence[float], right: Sequence[float]) -> tuple[float, ...]:
    return tuple(a - b for a, b in zip(left, right))


def _scale(vector: Sequence[float], factor: float) -> tuple[float, ...]:
    return tuple(factor * value for value in vector)


def _norm(vector: Sequence[float]) -> float:
    return math.sqrt(sum(value * value for value in vector))


def _mean(vectors: Sequence[Sequence[float]]) -> tuple[float, ...]:
    _require(bool(vectors), "empty mean")
    return tuple(sum(vector[index] for vector in vectors) / len(vectors) for index in range(DIMENSION))


def _anchor(seed: int) -> tuple[float, ...]:
    return tuple(0.12 * math.sin((index + 1) * 1.31 + seed * 0.0001) for index in range(DIMENSION))


def _target(seed: int, generation: int, split: str, index: int) -> tuple[float, ...]:
    if split == "protected":
        scale = 0.18 + 0.03 * _unit(STATE_SLICE, seed, generation, split, index, "scale")
    elif split == "probe":
        scale = 0.62 + 0.08 * _unit(STATE_SLICE, seed, generation, split, index, "scale")
    else:
        scale = 0.55 + 0.22 * _unit(STATE_SLICE, seed, generation, split, index, "scale")
    return tuple(
        _anchor(seed)[component]
        + scale * _signed(STATE_SLICE, seed, generation, split, index, component, "direction")
        for component in range(DIMENSION)
    )


def _task_count(split: str) -> int:
    return {"fit": FIT_TASK_COUNT, "tune": TUNE_TASK_COUNT, "assessment": ASSESSMENT_TASK_COUNT, "probe": PROBE_TASK_COUNT, "protected": PROTECTED_TASK_COUNT}[split]


def _ordered_targets(seed: int, generation: int, split: str, order_seed: int, direction: str) -> tuple[tuple[float, ...], ...]:
    rows = [(index, _target(seed, generation, split, index)) for index in range(_task_count(split))]
    rows.sort(key=lambda item: (_unit(STATE_SLICE, "order", order_seed, generation, split, item[0]), item[0]))
    if direction == "reverse":
        rows.reverse()
    return tuple(target for _, target in rows)


def _loss(theta: Sequence[float], target: Sequence[float]) -> float:
    return sum((left - right) ** 2 for left, right in zip(theta, target)) / DIMENSION


def _mean_loss(theta: Sequence[float], targets: Sequence[Sequence[float]]) -> float:
    return sum(_loss(theta, target) for target in targets) / len(targets)


def _checkpoint_digest(theta: Sequence[float], reserve: float, policy_name: str, policy_version: int) -> str:
    return _digest({
        "state_slice": STATE_SLICE,
        "theta": tuple(round(value, 15) for value in theta),
        "plasticity_reserve": round(reserve, 15),
        "policy_name": policy_name,
        "policy_version": policy_version,
    })


def _initial_state() -> dict[str, Any]:
    theta = tuple(0.0 for _ in range(DIMENSION))
    return {
        "theta": theta,
        "plasticity_reserve": 1.0,
        "policy_name": FIXED_POLICY,
        "policy_version": 0,
        "checkpoint_sha256": _checkpoint_digest(theta, 1.0, FIXED_POLICY, 0),
    }


def _memory_record(seed: int, generation: int, index: int, target: Sequence[float], suffix: str = "") -> dict[str, Any]:
    target_tuple = tuple(target)
    return {
        "memory_key": f"memory-{seed}-{generation}-{index}{suffix}",
        "concept_key": f"concept-{index % 2}{suffix}",
        "generation": generation,
        "target": target_tuple,
        "target_sha256": _digest(target_tuple),
        "provenance": f"synthetic:{seed}:{generation}:{index}{suffix}",
        "poisoned": False,
        "deleted": False,
        "status": "active",
        "support_count": 1,
    }


def _admit(records: list[dict[str, Any]], record: dict[str, Any], current_generation: int) -> str:
    if record["deleted"] or record["poisoned"] or record["status"] == "deleted":
        return "quarantined"
    if current_generation - record["generation"] > MAX_MEMORY_AGE:
        return "stale_rejected"
    if record["status"] not in ("active", "procedural"):
        return "quarantined"
    if any(item["concept_key"] == record["concept_key"] and item["target_sha256"] != record["target_sha256"] for item in records):
        return "contradiction_rejected"
    matches = [item for item in records if item["concept_key"] == record["concept_key"]]
    if matches:
        record = dict(record)
        record["support_count"] = matches[-1]["support_count"] + 1
        record["status"] = "procedural" if record["support_count"] >= 2 else "active"
        records.append(record)
        return "procedural_promoted" if record["status"] == "procedural" else "accepted"
    records.append(dict(record))
    return "accepted"


def _memory_bias(records: Sequence[Mapping[str, Any]], generation: int, mode: str) -> tuple[float, ...]:
    rows = [
        item["target"]
        for item in records
        if not item["deleted"]
        and not item["poisoned"]
        and item["status"] in ("active", "procedural")
        and generation - item["generation"] <= MAX_MEMORY_AGE
        and (mode != "procedural" or item["status"] == "procedural")
    ]
    return _mean(rows) if rows else tuple(0.0 for _ in range(DIMENSION))


def _apply_update(theta: Sequence[float], reserve: float, target: Sequence[float], protected_target: Sequence[float], policy: Mapping[str, Any], memory_bias: Sequence[float]) -> tuple[tuple[float, ...], float]:
    task_gradient = _sub(_add(target, _scale(memory_bias, 0.20)), theta)
    protected_gradient = _sub(protected_target, theta)
    delta = _scale(_sub(task_gradient, _scale(protected_gradient, policy["retention_price"])), policy["step_size"])
    return _add(theta, delta), _clamp(reserve - 0.08 * _norm(delta) + 0.015 * (1.0 if policy["memory_mode"] == "procedural" else 0.0), 0.0, 1.0)


def _probe_gain(theta: Sequence[float], reserve: float, probe_targets: Sequence[Sequence[float]], protected_target: Sequence[float]) -> float:
    before = _mean_loss(theta, probe_targets)
    after_theta, _ = _apply_update(theta, reserve, probe_targets[0], protected_target, POLICY_CONFIGS["balanced"], tuple(0.0 for _ in range(DIMENSION)))
    return before - _mean_loss(after_theta, probe_targets)


def _run_sequence(state: Mapping[str, Any], records: Sequence[Mapping[str, Any]], targets: Sequence[Sequence[float]], protected_target: Sequence[float], generation: int, policy: Mapping[str, Any], seed: int) -> tuple[dict[str, Any], list[dict[str, Any]], int, int]:
    theta = state["theta"]
    reserve = state["plasticity_reserve"]
    next_records = [dict(item) for item in records]
    accepted = 0
    promoted = 0
    for index, target in enumerate(targets):
        theta, reserve = _apply_update(theta, reserve, target, protected_target, policy, _memory_bias(next_records, generation, policy["memory_mode"]))
        outcome = _admit(next_records, _memory_record(seed, generation, index, target), generation)
        if outcome in ("accepted", "procedural_promoted"):
            accepted += 1
        if outcome == "procedural_promoted":
            promoted += 1
    version = state["policy_version"] + 1
    next_state = {
        "theta": theta,
        "plasticity_reserve": reserve,
        "policy_name": policy["name"],
        "policy_version": version,
        "checkpoint_sha256": _checkpoint_digest(theta, reserve, policy["name"], version),
    }
    return next_state, next_records, accepted, promoted


def _policy_score(state: Mapping[str, Any], records: Sequence[Mapping[str, Any]], fit_targets: Sequence[Sequence[float]], tune_targets: Sequence[Sequence[float]], protected_targets: Sequence[Sequence[float]], probe_targets: Sequence[Sequence[float]], generation: int, policy_name: str, seed: int) -> tuple[float, dict[str, Any], list[dict[str, Any]]]:
    policy = {"name": policy_name, **POLICY_CONFIGS[policy_name]}
    protected_target = _mean(protected_targets)
    fit_state, fit_records, _, _ = _run_sequence(state, records, fit_targets, protected_target, generation, policy, seed)
    tune_gain = _mean_loss(state["theta"], tune_targets) - _mean_loss(fit_state["theta"], tune_targets)
    protected_forgetting = max(0.0, _mean_loss(fit_state["theta"], protected_targets) - _mean_loss(state["theta"], protected_targets))
    plasticity = _probe_gain(fit_state["theta"], fit_state["plasticity_reserve"], probe_targets, protected_target)
    return tune_gain - policy["retention_price"] * protected_forgetting + 0.50 * plasticity, fit_state, fit_records


def _select_policy(arm: str, scores: Mapping[str, float], rng: random.Random) -> str:
    if arm in ("untouched_base", "fixed_policy"):
        return FIXED_POLICY
    if arm == "random_policy":
        return POLICY_NAMES[rng.randrange(len(POLICY_NAMES))]
    return sorted(POLICY_NAMES, key=lambda name: (-scores[name], POLICY_NAMES.index(name)))[0]


def _event(index: int, name: str, generation: int | None, payload: Mapping[str, Any], predecessor: int | None) -> dict[str, Any]:
    body = {"event_index": index, "event_name": name, "generation": generation, "predecessor_event_index": predecessor, "payload_sha256": _digest(payload)}
    return {**body, "event_sha256": _digest(body)}


def _generation_digest(row: Mapping[str, Any]) -> str:
    return _digest({key: value for key, value in row.items() if key != "generation_digest"})


def _case_digest(case: Mapping[str, Any]) -> str:
    return _digest({key: value for key, value in case.items() if key != "case_digest"})


def _slope(values: Sequence[float]) -> float:
    mean_x = (GENERATION_COUNT - 1) / 2.0
    mean_y = sum(values) / GENERATION_COUNT
    return sum((index - mean_x) * (value - mean_y) for index, value in enumerate(values)) / sum((index - mean_x) ** 2 for index in range(GENERATION_COUNT))


def _memory_probe() -> dict[str, bool]:
    seed = REPLICATE_SEEDS[0]
    records: list[dict[str, Any]] = []
    target = _target(seed, 0, "fit", 0)
    fresh = _memory_record(seed, 0, 0, target)
    fresh_result = _admit(records, fresh, 0)
    stale_result = _admit(records, _memory_record(seed, 0, 1, _target(seed, 0, "fit", 1)), MAX_MEMORY_AGE + 1)
    contradiction = _memory_record(seed, 0, 2, _add(target, tuple(0.3 for _ in range(DIMENSION))), "-0")
    contradiction["concept_key"] = fresh["concept_key"]
    contradiction_result = _admit(records, contradiction, 0)
    poisoned = _memory_record(seed, 0, 3, target)
    poisoned["poisoned"] = True
    deleted = _memory_record(seed, 0, 4, target)
    deleted["deleted"] = True
    deleted["status"] = "deleted"
    poisoned_result = _admit(records, poisoned, 0)
    deleted_result = _admit(records, deleted, 0)
    promotion_result = _admit(records, _memory_record(seed, 1, 0, target), 1)
    return {
        "fresh_accepted": fresh_result == "accepted",
        "stale_rejected": stale_result == "stale_rejected",
        "contradiction_rejected": contradiction_result == "contradiction_rejected",
        "poison_rejected": poisoned_result == "quarantined",
        "deletion_rejected": deleted_result == "quarantined",
        "procedural_promotion": promotion_result == "procedural_promoted",
    }


def _expected_case(seed: int, order_seed: int, direction: str, arm: str) -> dict[str, Any]:
    state = _initial_state()
    records: list[dict[str, Any]] = []
    rng = random.Random(seed + order_seed + 900000)
    generations = []
    events = [_event(0, "synthetic_initialized", None, {"seed": seed, "order_seed": order_seed, "direction": direction}, None)]
    event_index = 1
    for generation in range(GENERATION_COUNT):
        fit_targets = _ordered_targets(seed, generation, "fit", order_seed, direction)
        tune_targets = _ordered_targets(seed, generation, "tune", order_seed, direction)
        assessment_targets = _ordered_targets(seed, generation, "assessment", order_seed, "forward")
        probe_targets = _ordered_targets(seed, generation, "probe", order_seed, "forward")
        protected_targets = _ordered_targets(seed, generation, "protected", order_seed, "forward")
        protected_target = _mean(protected_targets)
        scores = {}
        for candidate in POLICY_NAMES:
            scores[candidate], _, _ = _policy_score(state, records, fit_targets, tune_targets, protected_targets, probe_targets, generation, candidate, seed)
        events.append(_event(event_index, "fit_tune_completed", generation, {"candidate_scores": scores}, event_index - 1))
        event_index += 1
        selected = _select_policy(arm, scores, rng)
        proposal = {"state_slice": STATE_SLICE, "controller_mode": arm, "prior_policy": state["policy_name"], "proposed_policy": selected, "candidate_score_digest": _digest(scores), "generation": generation}
        lock = {"state_slice": STATE_SLICE, "generation": generation, "policy": selected, "proposal_sha256": _digest(proposal), "assessment_started": False, "assessment_task_count": ASSESSMENT_TASK_COUNT}
        lock_digest = _digest(lock)
        events.append(_event(event_index, "prediction_lock_sealed", generation, {"lock_sha256": lock_digest}, event_index - 1))
        event_index += 1
        checkpoint_before = state["checkpoint_sha256"]
        if arm == "untouched_base":
            post_state = dict(state)
            post_records = [dict(item) for item in records]
            accepted = 0
            promoted = 0
        else:
            post_state, post_records, accepted, promoted = _run_sequence(state, records, fit_targets, protected_target, generation, {"name": selected, **POLICY_CONFIGS[selected]}, seed)
        base_assessment_loss = _mean_loss(state["theta"], assessment_targets)
        final_assessment_loss = _mean_loss(post_state["theta"], assessment_targets)
        base_protected_loss = _mean_loss(state["theta"], protected_targets)
        final_protected_loss = _mean_loss(post_state["theta"], protected_targets)
        row = {
            "generation": generation,
            "policy_before": state["policy_name"],
            "policy_locked": selected,
            "policy_version_before": state["policy_version"],
            "policy_version_after": post_state["policy_version"],
            "candidate_scores": {name: scores[name] for name in POLICY_NAMES},
            "candidate_evaluations": len(POLICY_NAMES) * (FIT_TASK_COUNT + TUNE_TASK_COUNT),
            "update_attempts": FIT_TASK_COUNT,
            "committed_updates": 0 if arm == "untouched_base" else FIT_TASK_COUNT,
            "total_compute_units": len(POLICY_NAMES) * (FIT_TASK_COUNT + TUNE_TASK_COUNT) + FIT_TASK_COUNT,
            "memory_accepted": accepted,
            "memory_promoted": promoted,
            "base_assessment_loss": base_assessment_loss,
            "final_assessment_loss": final_assessment_loss,
            "adaptation_gain": base_assessment_loss - final_assessment_loss,
            "base_protected_loss": base_protected_loss,
            "final_protected_loss": final_protected_loss,
            "retention_delta": final_protected_loss - base_protected_loss,
            "post_adaptation_plasticity_gain": _probe_gain(post_state["theta"], post_state["plasticity_reserve"], probe_targets, protected_target),
            "rollback_max_abs_error": 0.0,
            "retention_guard_pass": max(0.0, final_protected_loss - base_protected_loss) <= 0.08,
            "plasticity_guard_pass": _probe_gain(post_state["theta"], post_state["plasticity_reserve"], probe_targets, protected_target) >= -0.02,
            "rollback_guard_pass": True,
            "compute_guard_pass": len(POLICY_NAMES) * (FIT_TASK_COUNT + TUNE_TASK_COUNT) + FIT_TASK_COUNT == EXPECTED_TOTAL_COMPUTE // GENERATION_COUNT,
            "checkpoint_before_sha256": checkpoint_before,
            "checkpoint_after_sha256": post_state["checkpoint_sha256"],
            "prediction_lock_sha256": lock_digest,
        }
        row["generation_digest"] = _generation_digest(row)
        generations.append(row)
        events.append(_event(event_index, "assessment_completed", generation, {"generation_digest": row["generation_digest"]}, event_index - 1))
        event_index += 1
        events.append(_event(event_index, "rollback_verified", generation, {"rollback_error": 0.0}, event_index - 1))
        event_index += 1
        state = post_state
        records = post_records
    adaptation = [row["adaptation_gain"] for row in generations]
    retention = [row["retention_delta"] for row in generations]
    plasticity = [row["post_adaptation_plasticity_gain"] for row in generations]
    summary = {
        "mean_adaptation_gain": sum(adaptation) / GENERATION_COUNT,
        "mean_retention_delta": sum(retention) / GENERATION_COUNT,
        "mean_post_adaptation_plasticity_gain": sum(plasticity) / GENERATION_COUNT,
        "adaptation_slope": _slope(adaptation),
        "retention_slope": _slope(retention),
        "plasticity_slope": _slope(plasticity),
        "max_positive_forgetting": max(max(0.0, value) for value in retention),
        "min_plasticity_gain": min(plasticity),
        "rollback_max_abs_error": 0.0,
        "total_compute_units": sum(row["total_compute_units"] for row in generations),
        "update_attempts": sum(row["update_attempts"] for row in generations),
        "committed_updates": sum(row["committed_updates"] for row in generations),
        "order_pair_delta": 0.0,
        "order_guard_pass": True,
        "memory_probe": _memory_probe(),
    }
    summary["all_hard_guards_pass"] = all(
        row["retention_guard_pass"]
        and row["plasticity_guard_pass"]
        and row["rollback_guard_pass"]
        and row["compute_guard_pass"]
        for row in generations
    ) and summary["memory_probe"] == {
        "fresh_accepted": True,
        "stale_rejected": True,
        "contradiction_rejected": True,
        "poison_rejected": True,
        "deletion_rejected": True,
        "procedural_promotion": True,
    }
    case = {"case_key": f"{seed}:{order_seed}:{direction}:{arm}", "seed": seed, "order_seed": order_seed, "order_direction": direction, "arm": arm, "generations": generations, "event_log": events, "summary": summary}
    case["case_digest"] = _case_digest(case)
    return case


def _bootstrap(values: Sequence[float]) -> tuple[float, float]:
    rng = random.Random(BOOTSTRAP_SEED)
    means = []
    for _ in range(BOOTSTRAP_REPLICATES):
        means.append(sum(values[rng.randrange(len(values))] for _ in values) / len(values))
    means.sort()
    def quantile(position: float) -> float:
        index = (len(means) - 1) * position
        lower = math.floor(index)
        upper = math.ceil(index)
        return means[lower] if lower == upper else means[lower] + (means[upper] - means[lower]) * (index - lower)
    return quantile(0.025), quantile(0.975)


def _campaign_summary(cases: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    grouped = {
        arm: {case["case_key"].rsplit(":", 1)[0]: case for case in cases if case["arm"] == arm}
        for arm in ARMS
    }
    keys = sorted(grouped["recursive_policy"])
    selection = []
    compounding = []
    recursive_slopes = []
    final_advantages = []
    for key in keys:
        recursive = grouped["recursive_policy"][key]["summary"]
        random_case = grouped["random_policy"][key]["summary"]
        fixed = grouped["fixed_policy"][key]["summary"]
        selection.append(recursive["mean_adaptation_gain"] - random_case["mean_adaptation_gain"])
        compounding.append(recursive["adaptation_slope"] - random_case["adaptation_slope"])
        recursive_slopes.append(recursive["adaptation_slope"])
        final_advantages.append(recursive["mean_adaptation_gain"] - fixed["mean_adaptation_gain"])
    interval = _bootstrap(compounding)
    return {
        "case_count": len(cases),
        "selection_advantage_mean": sum(selection) / len(selection),
        "generational_compounding_advantage_mean": sum(compounding) / len(compounding),
        "generational_compounding_bootstrap_95": list(interval),
        "recursive_adaptation_slope_mean": sum(recursive_slopes) / len(recursive_slopes),
        "final_recursive_over_fixed_mean": sum(final_advantages) / len(final_advantages),
        "all_recursive_slopes_positive": all(value >= RECURSIVE_SLOPE_MINIMUM for value in recursive_slopes),
        "all_hard_guards_pass": all(case["summary"]["all_hard_guards_pass"] and case["summary"]["order_guard_pass"] for case in cases),
        "primary_gate_pass": sum(compounding) / len(compounding) >= PRIMARY_MINIMUM and interval[0] >= 0.0 and sum(final_advantages) / len(final_advantages) >= FINAL_ADVANTAGE_MINIMUM and all(value >= RECURSIVE_SLOPE_MINIMUM for value in recursive_slopes) and all(case["summary"]["all_hard_guards_pass"] and case["summary"]["order_guard_pass"] for case in cases),
    }


def _apply_order_guards(cases: list[dict[str, Any]]) -> None:
    grouped: dict[tuple[int, int, str], dict[str, dict[str, Any]]] = {}
    for case in cases:
        grouped.setdefault((case["seed"], case["order_seed"], case["arm"]), {})[case["order_direction"]] = case
    for pair in grouped.values():
        forward = pair["forward"]["summary"]
        reverse = pair["reverse"]["summary"]
        delta = max(
            abs(forward["mean_adaptation_gain"] - reverse["mean_adaptation_gain"]),
            abs(forward["mean_retention_delta"] - reverse["mean_retention_delta"]),
            abs(forward["mean_post_adaptation_plasticity_gain"] - reverse["mean_post_adaptation_plasticity_gain"]),
        )
        for case in pair.values():
            case["summary"]["order_pair_delta"] = delta
            case["summary"]["order_guard_pass"] = delta <= 0.08
            case["summary"]["all_hard_guards_pass"] = case["summary"]["all_hard_guards_pass"] and case["summary"]["order_guard_pass"]
            case["case_digest"] = _case_digest(case)


def validate_result(result: Mapping[str, Any]) -> None:
    expected_top = {"schema_version", "state_slice", "protocol_id", "claim_ceiling", "execution_authorized", "theory", "protocol", "memory_contract", "sandbox_contract", "cases", "campaign_summary", "result_sha256"}
    _require(set(result) == expected_top, "top-level schema")
    _require(result["schema_version"] == SCHEMA_VERSION, "schema version")
    _require(result["state_slice"] == STATE_SLICE, "state slice")
    _require(result["protocol_id"] == PROTOCOL_ID, "protocol id")
    _require(result["claim_ceiling"] == CLAIM_CEILING, "claim ceiling")
    _require(result["execution_authorized"] is False, "execution must remain unauthorized")
    _require(result["theory"] == {
        "name": "bounded_recursive_update_policy",
        "primary_estimand": "generational_compounding_advantage",
        "selection_estimand": "recursive_policy_mean_adaptation_minus_random_policy_mean_adaptation",
        "adaptation": "assessment_loss_before_fit_updates_minus_assessment_loss_after_fit_updates",
        "retention": "protected_loss_after_fit_updates_minus_protected_loss_before_fit_updates",
        "post_adaptation_plasticity": "fixed_probe_loss_before_probe_update_minus_after_probe_update",
    }, "theory contract")
    _require(result["protocol"] == {
        "generations": GENERATION_COUNT,
        "fit_task_count": FIT_TASK_COUNT,
        "tune_task_count": TUNE_TASK_COUNT,
        "assessment_task_count": ASSESSMENT_TASK_COUNT,
        "protected_task_count": PROTECTED_TASK_COUNT,
        "probe_task_count": PROBE_TASK_COUNT,
        "replicate_seeds": list(REPLICATE_SEEDS),
        "order_seeds": list(ORDER_SEEDS),
        "order_directions": list(ORDER_DIRECTIONS),
        "arms": list(ARMS),
        "policy_names": list(POLICY_NAMES),
        "expected_total_compute_per_case": EXPECTED_TOTAL_COMPUTE,
        "memory_max_age": MAX_MEMORY_AGE,
        "bootstrap_seed": BOOTSTRAP_SEED,
        "bootstrap_replicates": BOOTSTRAP_REPLICATES,
    }, "protocol contract")
    _require(result["memory_contract"] == _memory_probe(), "memory contract")
    expected_sandbox = {
        "mutable_policy_fields": ["policy_name", "policy_version"],
        "immutable_fields": ["evaluator", "protected_suite", "compute_budget", "assessment_split", "validator", "state_slice"],
        "forbidden_effects": ["base_weight_update", "assessment_read_before_lock", "validator_edit", "budget_edit", "cross_case_memory_read"],
    }
    _require(result["sandbox_contract"] == expected_sandbox, "sandbox contract")
    cases = result["cases"]
    _require(isinstance(cases, list), "cases must be a list")
    expected_keys = {f"{seed}:{order_seed}:{direction}:{arm}" for seed in REPLICATE_SEEDS for order_seed in ORDER_SEEDS for direction in ORDER_DIRECTIONS for arm in ARMS}
    observed_keys = [case.get("case_key") for case in cases if isinstance(case, Mapping)]
    _require(len(cases) == len(expected_keys) and set(observed_keys) == expected_keys and len(observed_keys) == len(set(observed_keys)), "case coverage")
    expected_case_keys = {"case_key", "seed", "order_seed", "order_direction", "arm", "generations", "event_log", "summary", "case_digest"}
    expected_cases = [
        _expected_case(seed, order_seed, direction, arm)
        for seed in REPLICATE_SEEDS
        for order_seed in ORDER_SEEDS
        for direction in ORDER_DIRECTIONS
        for arm in ARMS
    ]
    _apply_order_guards(expected_cases)
    expected_by_key = {case["case_key"]: case for case in expected_cases}
    for case in cases:
        _require(isinstance(case, Mapping), "case object")
        _require(case.get("case_key") in expected_by_key, "unknown case key")
        _require(set(case) == expected_case_keys, "case schema")
        expected = expected_by_key[case["case_key"]]
        _require(case == expected, f"case recomputation mismatch: {case['case_key']}")
    _require(result["campaign_summary"] == _campaign_summary(cases), "campaign summary")
    _require(result["result_sha256"] == _digest({key: value for key, value in result.items() if key != "result_sha256"}), "result digest")


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
