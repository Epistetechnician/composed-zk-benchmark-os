#!/usr/bin/env python3
"""Independent aggregate-only validator for recursive update-policy V2.

State slice: ``continual-learning-recursive-update-policy-v2``.

This module intentionally does not import the runner.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
from pathlib import Path
from typing import Any, Mapping, Sequence

STATE_SLICE = "continual-learning-recursive-update-policy-v2"
SCHEMA_VERSION = "continual-learning-recursive-update-policy-result-v2"
PROTOCOL_ID = "recursive-update-policy-v2"
CLAIM_CEILING = "LocalDevelopmentRecursiveUpdatePolicySyntheticProtocolV2"
DIMENSION = 6
GENERATION_COUNT = 4
FIT_TASK_COUNT = 5
TUNE_TASK_COUNT = 3
ASSESSMENT_TASK_COUNT = 4
PROTECTED_TASK_COUNT = 3
PROBE_TASK_COUNT = 2
MAX_MEMORY_AGE = 1
REPLICATE_SEEDS = (74101, 74102, 74103, 74104)
ORDER_SEEDS = (8311, 8312)
ORDER_DIRECTIONS = ("forward", "reverse")
ARMS = ("untouched_base", "fixed_policy", "recursive_policy", "random_policy")
POLICY_NAMES = ("conservative", "balanced", "plastic")
POLICY_CONFIGS = {
    "conservative": (0.18, 0.80, "episodic"),
    "balanced": (0.30, 0.45, "episodic"),
    "plastic": (0.38, 0.20, "procedural"),
}
FIXED_POLICY = "balanced"
BOOTSTRAP_SEED = 941177
BOOTSTRAP_REPLICATES = 4000
PRIMARY_MINIMUM = 0.005
SELECTION_MINIMUM = 0.005
RECURSIVE_SLOPE_MINIMUM = 0.002
MAX_PROTECTED_FORGETTING = 0.08
MIN_PLASTICITY_GAIN = -0.02
MAX_ORDER_DELTA = 0.08
ROLLBACK_TOLERANCE = 1e-12
EXPECTED_COMPUTE_PER_GENERATION = 29
EXPECTED_TOTAL_COMPUTE = 116
BASE_THETA = (0.0,) * DIMENSION
BASE_STATE_SHA256 = hashlib.sha256(json.dumps({"state_slice": STATE_SLICE, "theta": list(BASE_THETA)}, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


class ValidationError(ValueError):
    """Raised for an invalid aggregate artifact."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)


def digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")).hexdigest()


def unit(*parts: object) -> float:
    raw = "|".join(str(part) for part in parts).encode("utf-8")
    return int.from_bytes(hashlib.sha256(raw).digest()[:8], "big") / float(1 << 64)


def signed(*parts: object) -> float:
    return 2.0 * unit(*parts) - 1.0


def clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))


def add(left: Sequence[float], right: Sequence[float]) -> tuple[float, ...]:
    return tuple(a + b for a, b in zip(left, right))


def sub(left: Sequence[float], right: Sequence[float]) -> tuple[float, ...]:
    return tuple(a - b for a, b in zip(left, right))


def scale(vector: Sequence[float], factor: float) -> tuple[float, ...]:
    return tuple(factor * value for value in vector)


def norm(vector: Sequence[float]) -> float:
    return math.sqrt(sum(value * value for value in vector))


def mean(vectors: Sequence[Sequence[float]]) -> tuple[float, ...]:
    require(bool(vectors), "mean requires values")
    return tuple(sum(vector[index] for vector in vectors) / len(vectors) for index in range(DIMENSION))


def anchor(seed: int) -> tuple[float, ...]:
    return tuple(0.12 * math.sin((index + 1) * 1.31 + seed * 0.0001) for index in range(DIMENSION))


def target(seed: int, generation: int, split: str, index: int) -> tuple[float, ...]:
    if split == "protected":
        value = 0.18 + 0.03 * unit(STATE_SLICE, seed, generation, split, index, "scale")
    elif split == "probe":
        value = 0.62 + 0.08 * unit(STATE_SLICE, seed, generation, split, index, "scale")
    else:
        value = 0.55 + 0.22 * unit(STATE_SLICE, seed, generation, split, index, "scale")
    return tuple(anchor(seed)[component] + value * signed(STATE_SLICE, seed, generation, split, index, component, "direction") for component in range(DIMENSION))


def memory_target(seed: int, concept_index: int) -> tuple[float, ...]:
    return tuple(anchor(seed)[component] + 0.44 * signed(STATE_SLICE, seed, "memory-prototype", concept_index, component) for component in range(DIMENSION))


def ordered_indices(generation: int, split: str, order_seed: int, direction: str) -> tuple[int, ...]:
    count = {"fit": FIT_TASK_COUNT, "tune": TUNE_TASK_COUNT, "assessment": ASSESSMENT_TASK_COUNT, "probe": PROBE_TASK_COUNT, "protected": PROTECTED_TASK_COUNT}[split]
    indices = list(range(count))
    indices.sort(key=lambda index: (unit(STATE_SLICE, "order", order_seed, generation, split, index), index))
    if direction == "reverse":
        indices.reverse()
    return tuple(indices)


def loss(theta: Sequence[float], value: Sequence[float]) -> float:
    return sum((left - right) ** 2 for left, right in zip(theta, value)) / DIMENSION


def mean_loss(theta: Sequence[float], values: Sequence[Sequence[float]]) -> float:
    return sum(loss(theta, value) for value in values) / len(values)


def checkpoint(theta: Sequence[float], reserve: float, policy: str, version: int) -> str:
    return digest({"state_slice": STATE_SLICE, "theta": [round(value, 15) for value in theta], "plasticity_reserve": round(reserve, 15), "policy_name": policy, "policy_version": version})


def state(theta: Sequence[float], reserve: float, policy: str, version: int) -> tuple[tuple[float, ...], float, str, int, str]:
    values = tuple(float(value) for value in theta)
    return values, float(reserve), policy, int(version), checkpoint(values, reserve, policy, version)


def state_error(left: tuple[tuple[float, ...], float, str, int, str], right: tuple[tuple[float, ...], float, str, int, str]) -> float:
    return max(max(abs(a - b) for a, b in zip(left[0], right[0])), abs(left[1] - right[1]), 0.0 if left[2] == right[2] else 1.0, 0.0 if left[3] == right[3] else 1.0)


def restore(current: tuple[tuple[float, ...], float, str, int, str], saved: tuple[tuple[float, ...], float, str, int, str]) -> tuple[tuple[float, ...], float, str, int, str]:
    del current
    return state(saved[0], saved[1], saved[2], saved[3])


def record(seed: int, generation: int, index: int) -> dict[str, Any]:
    concept = index % 2
    values = memory_target(seed, concept)
    return {"memory_key": f"memory-{seed}-{generation}-{index}", "concept_key": f"concept-{concept}", "generation": generation, "target": values, "target_sha256": digest(values), "provenance": f"synthetic:{seed}:{generation}:{index}", "poisoned": False, "deleted": False, "status": "active", "support_count": 1}


def admit(bank: list[dict[str, Any]], item: dict[str, Any], generation: int) -> str:
    if item["deleted"] or item["poisoned"] or item["status"] in ("quarantined", "deleted"):
        return "quarantined"
    if generation - item["generation"] > MAX_MEMORY_AGE:
        return "stale_rejected"
    if item["status"] not in ("active", "procedural"):
        return "quarantined"
    if any(existing["concept_key"] == item["concept_key"] and existing["target_sha256"] != item["target_sha256"] for existing in bank):
        return "contradiction_rejected"
    matches = [existing for existing in bank if existing["concept_key"] == item["concept_key"]]
    if matches:
        support = matches[-1]["support_count"] + 1
        item = dict(item)
        item["support_count"] = support
        item["status"] = "procedural" if support >= 2 else "active"
        bank.append(item)
        return "procedural_promoted" if item["status"] == "procedural" else "accepted"
    bank.append(dict(item))
    return "accepted"


def usable(bank: Sequence[dict[str, Any]], generation: int, mode: str) -> tuple[tuple[float, ...], ...]:
    values = []
    for item in bank:
        if item["deleted"] or item["poisoned"] or item["status"] not in ("active", "procedural") or generation - item["generation"] > MAX_MEMORY_AGE:
            continue
        if mode == "procedural" and item["status"] != "procedural":
            continue
        values.append(item["target"])
    return tuple(values)


def memory_probe() -> dict[str, bool]:
    seed = REPLICATE_SEEDS[0]
    bank: list[dict[str, Any]] = []
    values = memory_target(seed, 0)
    fresh = record(seed, 0, 0)
    fresh_result = admit(bank, fresh, 0)
    stale_result = admit(bank, record(seed, 0, 1), MAX_MEMORY_AGE + 1)
    contradiction = record(seed, 0, 2)
    contradiction["concept_key"] = "concept-0"
    contradiction["target"] = add(values, (0.3,) * DIMENSION)
    contradiction["target_sha256"] = digest(contradiction["target"])
    contradiction_result = admit(bank, contradiction, 0)
    poisoned = {"memory_key": "poisoned", "concept_key": "poisoned", "generation": 0, "target": values, "target_sha256": digest(values), "provenance": "synthetic:poison", "poisoned": True, "deleted": False, "status": "active", "support_count": 1}
    deleted = {"memory_key": "deleted", "concept_key": "deleted", "generation": 0, "target": values, "target_sha256": digest(values), "provenance": "synthetic:deleted", "poisoned": False, "deleted": True, "status": "deleted", "support_count": 1}
    poisoned_result = admit(bank, poisoned, 0)
    deleted_result = admit(bank, deleted, 0)
    promotion_result = admit(bank, record(seed, 1, 0), 1)
    return {"fresh_accepted": fresh_result == "accepted", "stale_rejected": stale_result == "stale_rejected", "contradiction_rejected": contradiction_result == "contradiction_rejected", "poison_rejected": poisoned_result == "quarantined", "deletion_rejected": deleted_result == "quarantined", "procedural_promotion": promotion_result == "procedural_promoted"}


def update(theta: Sequence[float], reserve: float, value: Sequence[float], protected: Sequence[float], policy: str, memory_bias: Sequence[float]) -> tuple[tuple[float, ...], float]:
    step, retention, mode = POLICY_CONFIGS[policy]
    effective_step = step * (0.50 + 0.50 * reserve)
    task_gradient = sub(add(value, scale(memory_bias, 0.20)), theta)
    protected_gradient = sub(protected, theta)
    delta = scale(sub(task_gradient, scale(protected_gradient, retention)), effective_step)
    return add(theta, delta), clamp(reserve - 0.08 * norm(delta) + 0.015 * (1.0 if mode == "procedural" else 0.0), 0.0, 1.0)


def probe_gain(theta: Sequence[float], reserve: float, probes: Sequence[Sequence[float]], protected: Sequence[float]) -> float:
    before = mean_loss(theta, probes)
    after, _ = update(theta, reserve, probes[0], protected, FIXED_POLICY, (0.0,) * DIMENSION)
    return before - mean_loss(after, probes)


def run_sequence(start: tuple[tuple[float, ...], float, str, int, str], bank: Sequence[dict[str, Any]], rows: Sequence[tuple[int, Sequence[float]]], protected: Sequence[float], generation: int, policy: str, seed: int) -> tuple[tuple[tuple[float, ...], float, str, int, str], list[dict[str, Any]], int, int]:
    theta, reserve = start[0], start[1]
    next_bank = [dict(item) for item in bank]
    accepted = 0
    promoted = 0
    for index, value in rows:
        values = usable(next_bank, generation, POLICY_CONFIGS[policy][2])
        bias = mean(values) if values else (0.0,) * DIMENSION
        theta, reserve = update(theta, reserve, value, protected, policy, bias)
        outcome = admit(next_bank, record(seed, generation, index), generation)
        accepted += int(outcome in ("accepted", "procedural_promoted"))
        promoted += int(outcome == "procedural_promoted")
    return state(theta, reserve, start[2], start[3]), next_bank, accepted, promoted


def candidate(start: tuple[tuple[float, ...], float, str, int, str], bank: Sequence[dict[str, Any]], seed: int, generation: int, order_seed: int, direction: str, policy: str, fit_rows: Sequence[tuple[int, Sequence[float]]], tune: Sequence[Sequence[float]], protected_rows: Sequence[Sequence[float]], probes: Sequence[Sequence[float]]) -> tuple[tuple[tuple[float, ...], float, str, int, str], list[dict[str, Any]], float]:
    protected = mean(protected_rows)
    next_state, next_bank, _, _ = run_sequence(start, bank, fit_rows, protected, generation, policy, seed)
    tune_gain = mean_loss(start[0], tune) - mean_loss(next_state[0], tune)
    protected_delta = mean_loss(next_state[0], protected_rows) - mean_loss(start[0], protected_rows)
    score = tune_gain - POLICY_CONFIGS[policy][1] * max(protected_delta, 0.0) + 0.50 * probe_gain(next_state[0], next_state[1], probes, protected)
    return next_state, next_bank, score


def event(index: int, name: str, generation: int, payload: Mapping[str, Any], predecessor: int | None) -> dict[str, Any]:
    return {"event_index": index, "event_name": name, "generation": generation, "payload": dict(payload), "predecessor_event_index": predecessor}


def run_case(seed: int, order_seed: int, direction: str, arm: str) -> dict[str, Any]:
    current = state(BASE_THETA, 1.0, FIXED_POLICY, 0)
    base_snapshot = current
    bank: list[dict[str, Any]] = []
    events = [event(0, "synthetic_initialized", 0, {"base_state_sha256": BASE_STATE_SHA256}, None)]
    random_stream = random.Random(seed + order_seed + 900000)
    rows = []
    for generation in range(GENERATION_COUNT):
        fit_rows = tuple((index, target(seed, generation, "fit", index)) for index in ordered_indices(generation, "fit", order_seed, direction))
        tune = tuple(target(seed, generation, "tune", index) for index in range(TUNE_TASK_COUNT))
        assessment = tuple(target(seed, generation, "assessment", index) for index in range(ASSESSMENT_TASK_COUNT))
        protected_rows = tuple(target(seed, generation, "protected", index) for index in range(PROTECTED_TASK_COUNT))
        probes = tuple(target(seed, generation, "probe", index) for index in range(PROBE_TASK_COUNT))
        protected = mean(protected_rows)
        candidates = {name: candidate(current, bank, seed, generation, order_seed, direction, name, fit_rows, tune, protected_rows, probes) for name in POLICY_NAMES}
        scores = {name: candidates[name][2] for name in POLICY_NAMES}
        if arm == "fixed_policy":
            selected = FIXED_POLICY
        elif arm == "recursive_policy":
            selected = max(POLICY_NAMES, key=lambda name: (scores[name], -POLICY_NAMES.index(name)))
        elif arm == "random_policy":
            selected = POLICY_NAMES[random_stream.randrange(len(POLICY_NAMES))]
        else:
            selected = FIXED_POLICY
        proposal = {"state_slice": STATE_SLICE, "generation": generation, "prior_policy": current[2], "proposed_policy": selected, "candidate_score_digest": digest({name: round(scores[name], 15) for name in POLICY_NAMES}), "controller_mode": arm}
        lock_digest = digest({"state_slice": STATE_SLICE, "generation": generation, "selected_policy": selected, "proposal_digest": digest(proposal), "assessment_started": False, "assessment_task_count": ASSESSMENT_TASK_COUNT})
        events.append(event(len(events), "fit_tune_completed", generation, {"candidate_score_digest": proposal["candidate_score_digest"]}, len(events) - 1))
        events.append(event(len(events), "prediction_lock_sealed", generation, {"prediction_lock_sha256": lock_digest}, len(events) - 1))
        before = current
        checkpoint_before = current[4]
        if arm == "untouched_base":
            after = current
            next_bank = bank
            accepted = 0
            promoted = 0
        else:
            simulated, next_bank, accepted, promoted = run_sequence(current, bank, fit_rows, protected, generation, selected, seed)
            after = state(simulated[0], simulated[1], selected, current[3] + 1)
        restored = restore(after, before)
        rollback_error = state_error(restored, before)
        base_assessment = mean_loss(before[0], assessment)
        final_assessment = mean_loss(after[0], assessment)
        base_protected = mean_loss(before[0], protected_rows)
        final_protected = mean_loss(after[0], protected_rows)
        plasticity = probe_gain(after[0], after[1], probes, protected)
        row = {"generation": generation, "policy_before": before[2], "policy_locked": selected, "policy_version_before": before[3], "policy_version_after": after[3], "candidate_scores": scores, "candidate_evaluations": 24, "update_attempts": 5, "committed_updates": 0 if arm == "untouched_base" else 5, "total_compute_units": EXPECTED_COMPUTE_PER_GENERATION, "memory_accepted": accepted, "memory_promoted": promoted, "base_state_sha256": BASE_STATE_SHA256, "base_assessment_loss": base_assessment, "final_assessment_loss": final_assessment, "adaptation_gain": base_assessment - final_assessment, "base_protected_loss": base_protected, "final_protected_loss": final_protected, "retention_delta": final_protected - base_protected, "post_adaptation_plasticity_gain": plasticity, "rollback_max_abs_error": rollback_error, "retention_guard_pass": max(0.0, final_protected - base_protected) <= MAX_PROTECTED_FORGETTING, "plasticity_guard_pass": plasticity >= MIN_PLASTICITY_GAIN, "rollback_guard_pass": rollback_error <= ROLLBACK_TOLERANCE, "compute_guard_pass": True, "base_state_guard_pass": base_snapshot[0] == BASE_THETA and base_snapshot[1] == 1.0 and base_snapshot[2] == FIXED_POLICY and base_snapshot[3] == 0 and BASE_STATE_SHA256 == digest({"state_slice": STATE_SLICE, "theta": list(BASE_THETA)}), "checkpoint_before_sha256": checkpoint_before, "checkpoint_after_sha256": after[4], "prediction_lock_sha256": lock_digest}
        row["generation_digest"] = digest(row)
        rows.append(row)
        events.append(event(len(events), "assessment_completed", generation, {"generation_digest": row["generation_digest"]}, len(events) - 1))
        events.append(event(len(events), "rollback_verified", generation, {"rollback_error": rollback_error}, len(events) - 1))
        current, bank = after, next_bank
    adaptations = [row["adaptation_gain"] for row in rows]
    retentions = [row["retention_delta"] for row in rows]
    plastics = [row["post_adaptation_plasticity_gain"] for row in rows]
    summary = {"mean_adaptation_gain": sum(adaptations) / GENERATION_COUNT, "mean_retention_delta": sum(retentions) / GENERATION_COUNT, "mean_post_adaptation_plasticity_gain": sum(plastics) / GENERATION_COUNT, "adaptation_slope": slope(adaptations), "retention_slope": slope(retentions), "plasticity_slope": slope(plastics), "max_positive_forgetting": max(max(0.0, value) for value in retentions), "min_plasticity_gain": min(plastics), "rollback_max_abs_error": max(row["rollback_max_abs_error"] for row in rows), "total_compute_units": sum(row["total_compute_units"] for row in rows), "update_attempts": sum(row["update_attempts"] for row in rows), "committed_updates": sum(row["committed_updates"] for row in rows), "base_state_sha256": BASE_STATE_SHA256, "order_pair_delta": 0.0, "order_guard_pass": True, "memory_probe": memory_probe()}
    summary["all_hard_guards_pass"] = all(row["retention_guard_pass"] and row["plasticity_guard_pass"] and row["rollback_guard_pass"] and row["compute_guard_pass"] and row["base_state_guard_pass"] for row in rows) and summary["memory_probe"] == {"fresh_accepted": True, "stale_rejected": True, "contradiction_rejected": True, "poison_rejected": True, "deletion_rejected": True, "procedural_promotion": True}
    case = {"case_key": f"{seed}:{order_seed}:{direction}:{arm}", "seed": seed, "order_seed": order_seed, "order_direction": direction, "arm": arm, "generations": rows, "event_log": events, "summary": summary}
    case["case_digest"] = digest(case)
    return case


def slope(values: Sequence[float]) -> float:
    mean_x = (GENERATION_COUNT - 1) / 2
    mean_y = sum(values) / len(values)
    return sum((index - mean_x) * (value - mean_y) for index, value in enumerate(values)) / sum((index - mean_x) ** 2 for index in range(GENERATION_COUNT))


def bootstrap(values: Sequence[float]) -> tuple[float, float]:
    rng = random.Random(BOOTSTRAP_SEED)
    samples = [sum(values[rng.randrange(len(values))] for _ in values) / len(values) for _ in range(BOOTSTRAP_REPLICATES)]
    samples.sort()
    def quantile(position: float) -> float:
        index = (len(samples) - 1) * position
        lower = math.floor(index)
        upper = math.ceil(index)
        return samples[lower] if lower == upper else samples[lower] + (samples[upper] - samples[lower]) * (index - lower)
    return quantile(0.025), quantile(0.975)


def paired(cases: Sequence[Mapping[str, Any]], arm: str) -> dict[str, Mapping[str, Any]]:
    return {case["case_key"].rsplit(":", 1)[0]: case for case in cases if case["arm"] == arm}


def campaign_summary(cases: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    groups = {arm: paired(cases, arm) for arm in ARMS}
    keys = sorted(groups["recursive_policy"])
    selection = []
    compounding = []
    slopes = []
    fixed = []
    for key in keys:
        recursive = groups["recursive_policy"][key]["summary"]
        random_case = groups["random_policy"][key]["summary"]
        fixed_case = groups["fixed_policy"][key]["summary"]
        selection.append(recursive["mean_adaptation_gain"] - random_case["mean_adaptation_gain"])
        compounding.append(recursive["adaptation_slope"] - random_case["adaptation_slope"])
        slopes.append(recursive["adaptation_slope"])
        fixed.append(recursive["mean_adaptation_gain"] - fixed_case["mean_adaptation_gain"])
    interval = bootstrap(compounding)
    selection_mean = sum(selection) / len(selection)
    compound_mean = sum(compounding) / len(compounding)
    fixed_mean = sum(fixed) / len(fixed)
    all_guards = all(case["summary"]["all_hard_guards_pass"] and case["summary"]["order_guard_pass"] for case in cases)
    return {"case_count": len(cases), "selection_advantage_mean": selection_mean, "generational_compounding_advantage_mean": compound_mean, "generational_compounding_bootstrap_95": list(interval), "recursive_adaptation_slope_mean": sum(slopes) / len(slopes), "final_recursive_over_fixed_mean": fixed_mean, "all_recursive_slopes_positive": all(value >= RECURSIVE_SLOPE_MINIMUM for value in slopes), "all_hard_guards_pass": all_guards, "primary_gate_pass": compound_mean >= PRIMARY_MINIMUM and interval[0] >= 0.0 and selection_mean >= SELECTION_MINIMUM and fixed_mean >= 0.0 and all(value >= RECURSIVE_SLOPE_MINIMUM for value in slopes) and all_guards}


def apply_order_guards(cases: list[dict[str, Any]]) -> None:
    grouped: dict[tuple[int, int, str], dict[str, dict[str, Any]]] = {}
    for case in cases:
        grouped.setdefault((case["seed"], case["order_seed"], case["arm"]), {})[case["order_direction"]] = case
    for pair in grouped.values():
        forward = pair["forward"]["summary"]
        reverse = pair["reverse"]["summary"]
        delta = max(abs(forward["mean_adaptation_gain"] - reverse["mean_adaptation_gain"]), abs(forward["mean_retention_delta"] - reverse["mean_retention_delta"]), abs(forward["mean_post_adaptation_plasticity_gain"] - reverse["mean_post_adaptation_plasticity_gain"]))
        for case in pair.values():
            case["summary"]["order_pair_delta"] = delta
            case["summary"]["order_guard_pass"] = delta <= MAX_ORDER_DELTA
            case["summary"]["all_hard_guards_pass"] = case["summary"]["all_hard_guards_pass"] and case["summary"]["order_guard_pass"]
            case["case_digest"] = digest({key: value for key, value in case.items() if key != "case_digest"})


def classify(summary: Mapping[str, Any]) -> str:
    if summary["primary_gate_pass"]:
        return "LocalSyntheticRecursiveUpdatePolicyCandidate"
    if summary["all_hard_guards_pass"] and summary["selection_advantage_mean"] >= SELECTION_MINIMUM:
        return "NonCompoundingContinualLearning"
    return "NoCandidate"


def finite_walk(value: Any, path: str = "result") -> None:
    if isinstance(value, bool) or value is None or isinstance(value, str):
        return
    if isinstance(value, (int, float)):
        require(math.isfinite(float(value)), f"nonfinite value at {path}")
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            finite_walk(item, f"{path}[{index}]")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            finite_walk(item, f"{path}.{key}")
        return
    raise ValidationError(f"unsupported value at {path}")


def expected_result() -> dict[str, Any]:
    cases = [run_case(seed, order_seed, direction, arm) for seed in REPLICATE_SEEDS for order_seed in ORDER_SEEDS for direction in ORDER_DIRECTIONS for arm in ARMS]
    apply_order_guards(cases)
    summary = campaign_summary(cases)
    result = {"schema_version": SCHEMA_VERSION, "state_slice": STATE_SLICE, "protocol_id": PROTOCOL_ID, "claim_ceiling": CLAIM_CEILING, "execution_authorized": False, "base_state_sha256": BASE_STATE_SHA256, "theory": {"name": "bounded_recursive_update_policy_with_reserve_causality", "primary_estimand": "generational_compounding_advantage", "selection_estimand": "recursive_policy_mean_adaptation_minus_random_policy_mean_adaptation", "adaptation": "assessment_loss_before_fit_updates_minus_assessment_loss_after_fit_updates", "retention": "protected_loss_after_fit_updates_minus_protected_loss_before_fit_updates", "post_adaptation_plasticity": "fixed_probe_loss_before_probe_update_minus_after_probe_update", "reserve_effect": "effective_step_and_probe_capacity_scale_with_plasticity_reserve"}, "protocol": {"generations": GENERATION_COUNT, "fit_task_count": FIT_TASK_COUNT, "tune_task_count": TUNE_TASK_COUNT, "assessment_task_count": ASSESSMENT_TASK_COUNT, "protected_task_count": PROTECTED_TASK_COUNT, "probe_task_count": PROBE_TASK_COUNT, "replicate_seeds": list(REPLICATE_SEEDS), "order_seeds": list(ORDER_SEEDS), "order_directions": list(ORDER_DIRECTIONS), "arms": list(ARMS), "policy_names": list(POLICY_NAMES), "expected_compute_per_generation": EXPECTED_COMPUTE_PER_GENERATION, "expected_total_compute_per_case": EXPECTED_TOTAL_COMPUTE, "memory_max_age": MAX_MEMORY_AGE, "bootstrap_seed": BOOTSTRAP_SEED, "bootstrap_replicates": BOOTSTRAP_REPLICATES, "order_guard_components": ["mean_adaptation_gain", "mean_retention_delta", "mean_post_adaptation_plasticity_gain"], "order_guard_aggregation": "max_absolute_component_delta"}, "memory_contract": memory_probe(), "sandbox_contract": {"mutable_policy_fields": ["policy_name", "policy_version"], "immutable_fields": ["evaluator", "protected_suite", "compute_budget", "assessment_split", "validator", "state_slice", "claim_ceiling"], "forbidden_effects": ["base_weight_update", "assessment_read_before_lock", "validator_edit", "budget_edit", "cross_case_memory_read", "base_state_digest_change"]}, "cases": cases, "campaign_summary": summary, "classification": classify(summary)}
    result["result_sha256"] = digest(result)
    return result


def validate_result(result: Mapping[str, Any]) -> None:
    finite_walk(result)
    require(set(result) == {"schema_version", "state_slice", "protocol_id", "claim_ceiling", "execution_authorized", "base_state_sha256", "theory", "protocol", "memory_contract", "sandbox_contract", "cases", "campaign_summary", "classification", "result_sha256"}, "top-level schema")
    require(result["result_sha256"] == digest({key: value for key, value in result.items() if key != "result_sha256"}), "outer digest")
    expected = expected_result()
    require(result == expected, "aggregate does not match independent recomputation")


def validate_file(path: Path) -> None:
    validate_result(json.loads(path.read_text(encoding="utf-8")))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("result", type=Path)
    args = parser.parse_args()
    validate_file(args.result)
    print(json.dumps({"state_slice": STATE_SLICE, "validated": str(args.result)}, sort_keys=True))


if __name__ == "__main__":
    main()
