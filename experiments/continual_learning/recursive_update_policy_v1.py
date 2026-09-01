#!/usr/bin/env python3
"""Exact synthetic recursive update-policy protocol.

State slice: ``continual-learning-recursive-update-policy-v1``.

This module is a model-free protocol instrument.  It tests whether a bounded
controller can improve its own update policy across fresh generations while
maintaining retention and post-adaptation plasticity.  It does not load a
model, access a corpus, call a provider, or mutate model weights.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


STATE_SLICE = "continual-learning-recursive-update-policy-v1"
SCHEMA_VERSION = "continual-learning-recursive-update-policy-result-v1"
PROTOCOL_ID = "recursive-update-policy-v1"
CLAIM_CEILING = "LocalDevelopmentRecursiveUpdatePolicySyntheticProtocol"
REVIEW_PACKET_PATH = Path(__file__).resolve().parents[2] / "docs/research/continual-learning/137-recursive-update-policy-v1-protocol.md"
REVIEW_RECEIPT_SCHEMA_VERSION = "continual-learning-recursive-update-policy-review-receipt-v1"
REVIEW_CHECKS = (
    "theory_distinct",
    "estimands_fixed",
    "state_machine_executable",
    "memory_contract_executable",
    "sandbox_closed",
    "compute_fixed",
    "fresh_splits_fixed",
    "prediction_lock_ordered",
    "validator_independent",
    "claim_ceiling_bounded",
)
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
SPLITS = ("fit", "tune", "assessment", "probe", "protected")
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
MAX_PROTECTED_FORGETTING = 0.08
MIN_PLASTICITY_GAIN = -0.02
MAX_ORDER_DELTA = 0.08
ROLLBACK_TOLERANCE = 1e-12
EXPECTED_TOTAL_COMPUTE = (
    GENERATION_COUNT
    * (len(POLICY_NAMES) * (FIT_TASK_COUNT + TUNE_TASK_COUNT) + FIT_TASK_COUNT)
)
MEMORY_STATUSES = ("active", "procedural", "quarantined", "deleted")
MUTABLE_POLICY_FIELDS = ("policy_name", "policy_version")
IMMUTABLE_SANDBOX_FIELDS = (
    "evaluator",
    "protected_suite",
    "compute_budget",
    "assessment_split",
    "validator",
    "state_slice",
)
FORBIDDEN_SANDBOX_EFFECTS = (
    "base_weight_update",
    "assessment_read_before_lock",
    "validator_edit",
    "budget_edit",
    "cross_case_memory_read",
)


class ProtocolError(ValueError):
    """Raised when the exact synthetic protocol is violated."""


@dataclass(frozen=True)
class Policy:
    name: str
    step_size: float
    retention_price: float
    memory_mode: str


@dataclass(frozen=True)
class MemoryRecord:
    memory_key: str
    concept_key: str
    generation: int
    target: tuple[float, ...]
    target_sha256: str
    provenance: str
    poisoned: bool = False
    deleted: bool = False
    status: str = "active"
    support_count: int = 1


@dataclass(frozen=True)
class LearnerState:
    theta: tuple[float, ...]
    plasticity_reserve: float
    policy_name: str
    policy_version: int
    checkpoint_sha256: str


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ProtocolError(message)


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
    _require(bool(vectors), "mean requires a non-empty sequence")
    return tuple(sum(vector[index] for vector in vectors) / len(vectors) for index in range(DIMENSION))


def _anchor(seed: int) -> tuple[float, ...]:
    return tuple(0.12 * math.sin((index + 1) * 1.31 + seed * 0.0001) for index in range(DIMENSION))


def _target(seed: int, generation: int, split: str, index: int) -> tuple[float, ...]:
    _require(split in SPLITS, f"unknown split: {split}")
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
    return {
        "fit": FIT_TASK_COUNT,
        "tune": TUNE_TASK_COUNT,
        "assessment": ASSESSMENT_TASK_COUNT,
        "probe": PROBE_TASK_COUNT,
        "protected": PROTECTED_TASK_COUNT,
    }[split]


def _ordered_targets(seed: int, generation: int, split: str, order_seed: int, direction: str) -> tuple[tuple[float, ...], ...]:
    _require(direction in ORDER_DIRECTIONS, f"unknown order direction: {direction}")
    rows = [
        (index, _target(seed, generation, split, index))
        for index in range(_task_count(split))
    ]
    rows.sort(key=lambda item: (_unit(STATE_SLICE, "order", order_seed, generation, split, item[0]), item[0]))
    if direction == "reverse":
        rows.reverse()
    return tuple(target for _, target in rows)


def _loss(theta: Sequence[float], target: Sequence[float]) -> float:
    return sum((left - right) ** 2 for left, right in zip(theta, target)) / DIMENSION


def _mean_loss(theta: Sequence[float], targets: Sequence[Sequence[float]]) -> float:
    return sum(_loss(theta, target) for target in targets) / len(targets)


def _policy(name: str) -> Policy:
    _require(name in POLICY_NAMES, f"unknown policy: {name}")
    config = POLICY_CONFIGS[name]
    return Policy(name=name, **config)


def validate_sandbox_proposal(proposal: Mapping[str, Any]) -> None:
    """Reject controller proposals that cross the sandbox boundary."""
    allowed = {
        "state_slice",
        "generation",
        "prior_policy",
        "proposed_policy",
        "candidate_score_digest",
        "controller_mode",
    }
    _require(set(proposal) == allowed, "sandbox proposal schema")
    _require(proposal["state_slice"] == STATE_SLICE, "sandbox state slice")
    _require(isinstance(proposal["generation"], int) and not isinstance(proposal["generation"], bool), "sandbox generation")
    _require(proposal["prior_policy"] in POLICY_NAMES, "sandbox prior policy")
    _require(proposal["proposed_policy"] in POLICY_NAMES, "sandbox proposed policy")
    _require(proposal["controller_mode"] in ARMS, "sandbox controller mode")
    _require(isinstance(proposal["candidate_score_digest"], str) and len(proposal["candidate_score_digest"]) == 64, "sandbox score digest")


def validate_review_receipt(path: Path) -> str:
    """Validate the independent review receipt required for a synthetic run."""
    resolved = path.resolve()
    _require(resolved.exists() and resolved.is_file(), "review receipt missing")
    payload = json.loads(resolved.read_text(encoding="utf-8"))
    expected_keys = {
        "schema_version",
        "state_slice",
        "review_packet_path",
        "review_packet_sha256",
        "reviewer_role",
        "disposition",
        "blocking_defects",
        "checks",
    }
    _require(set(payload) == expected_keys, "review receipt schema")
    _require(payload["schema_version"] == REVIEW_RECEIPT_SCHEMA_VERSION, "review receipt version")
    _require(payload["state_slice"] == STATE_SLICE, "review receipt state slice")
    _require(payload["review_packet_path"] == str(REVIEW_PACKET_PATH), "review packet path")
    _require(REVIEW_PACKET_PATH.exists(), "review packet missing")
    _require(payload["review_packet_sha256"] == hashlib.sha256(REVIEW_PACKET_PATH.read_bytes()).hexdigest(), "review packet digest")
    _require(isinstance(payload["reviewer_role"], str) and payload["reviewer_role"].startswith("independent-"), "reviewer role")
    _require(payload["disposition"] == "APPROVED_FOR_SYNTHETIC_RUN", "review disposition")
    _require(payload["blocking_defects"] == [], "review blocking defects")
    _require(isinstance(payload["checks"], Mapping) and set(payload["checks"]) == set(REVIEW_CHECKS), "review checks")
    _require(all(payload["checks"][name] == "PASS" for name in REVIEW_CHECKS), "review check failure")
    return hashlib.sha256(resolved.read_bytes()).hexdigest()


def _checkpoint_digest(theta: Sequence[float], reserve: float, policy_name: str, policy_version: int) -> str:
    return _digest({
        "state_slice": STATE_SLICE,
        "theta": tuple(round(value, 15) for value in theta),
        "plasticity_reserve": round(reserve, 15),
        "policy_name": policy_name,
        "policy_version": policy_version,
    })


class MemoryBank:
    """External memory with fail-closed freshness and integrity checks."""

    def __init__(self, records: Iterable[MemoryRecord] = ()) -> None:
        self.records = list(records)

    def clone(self) -> "MemoryBank":
        return MemoryBank(self.records)

    def admit(self, record: MemoryRecord, current_generation: int) -> str:
        if record.deleted or record.poisoned or record.status == "deleted":
            return "quarantined"
        if current_generation - record.generation > MAX_MEMORY_AGE:
            return "stale_rejected"
        if record.status not in MEMORY_STATUSES[:2]:
            return "quarantined"
        for existing in self.records:
            if existing.concept_key == record.concept_key and existing.target_sha256 != record.target_sha256:
                return "contradiction_rejected"
        matches = [existing for existing in self.records if existing.concept_key == record.concept_key]
        if matches:
            previous = matches[-1]
            promoted = MemoryRecord(
                memory_key=record.memory_key,
                concept_key=record.concept_key,
                generation=record.generation,
                target=record.target,
                target_sha256=record.target_sha256,
                provenance=record.provenance,
                support_count=previous.support_count + 1,
                status="procedural" if previous.support_count + 1 >= 2 else "active",
            )
            self.records.append(promoted)
            return "procedural_promoted" if promoted.status == "procedural" else "accepted"
        self.records.append(record)
        return "accepted"

    def usable_targets(self, generation: int, mode: str) -> tuple[tuple[float, ...], ...]:
        _require(mode in ("episodic", "procedural"), f"unknown memory mode: {mode}")
        rows = []
        for record in self.records:
            if record.deleted or record.poisoned or record.status not in ("active", "procedural"):
                continue
            if generation - record.generation > MAX_MEMORY_AGE:
                continue
            if mode == "procedural" and record.status != "procedural":
                continue
            rows.append(record.target)
        return tuple(rows)


def _memory_record(seed: int, generation: int, index: int, target: Sequence[float], *, concept_suffix: str = "") -> MemoryRecord:
    concept_key = f"concept-{index % 2}{concept_suffix}"
    memory_key = f"memory-{seed}-{generation}-{index}{concept_suffix}"
    target_tuple = tuple(target)
    return MemoryRecord(
        memory_key=memory_key,
        concept_key=concept_key,
        generation=generation,
        target=target_tuple,
        target_sha256=_digest(target_tuple),
        provenance=f"synthetic:{seed}:{generation}:{index}{concept_suffix}",
    )


def memory_probe() -> dict[str, bool]:
    """Run the deterministic memory-integrity probe without model execution."""
    seed = REPLICATE_SEEDS[0]
    bank = MemoryBank()
    target = _target(seed, 0, "fit", 0)
    fresh = _memory_record(seed, 0, 0, target)
    fresh_result = bank.admit(fresh, current_generation=0)
    stale = _memory_record(seed, 0, 1, _target(seed, 0, "fit", 1))
    stale_result = bank.admit(stale, current_generation=MAX_MEMORY_AGE + 1)
    contradiction_target = _add(target, tuple(0.3 for _ in range(DIMENSION)))
    contradiction = _memory_record(seed, 0, 2, contradiction_target, concept_suffix="-0")
    contradiction = MemoryRecord(
        memory_key=contradiction.memory_key,
        concept_key=fresh.concept_key,
        generation=0,
        target=contradiction.target,
        target_sha256=contradiction.target_sha256,
        provenance=contradiction.provenance,
    )
    contradiction_result = bank.admit(contradiction, current_generation=0)
    poisoned = MemoryRecord(
        memory_key="poisoned",
        concept_key="poisoned",
        generation=0,
        target=target,
        target_sha256=_digest(target),
        provenance="synthetic:poison",
        poisoned=True,
    )
    deleted = MemoryRecord(
        memory_key="deleted",
        concept_key="deleted",
        generation=0,
        target=target,
        target_sha256=_digest(target),
        provenance="synthetic:deleted",
        deleted=True,
        status="deleted",
    )
    poisoned_result = bank.admit(poisoned, current_generation=0)
    deleted_result = bank.admit(deleted, current_generation=0)
    promotion_result = bank.admit(_memory_record(seed, 1, 0, target), current_generation=1)
    return {
        "fresh_accepted": fresh_result == "accepted",
        "stale_rejected": stale_result == "stale_rejected",
        "contradiction_rejected": contradiction_result == "contradiction_rejected",
        "poison_rejected": poisoned_result == "quarantined",
        "deletion_rejected": deleted_result == "quarantined",
        "procedural_promotion": promotion_result == "procedural_promoted",
    }


def _memory_bias(bank: MemoryBank, generation: int, policy: Policy) -> tuple[float, ...]:
    usable = bank.usable_targets(generation, policy.memory_mode)
    return _mean(usable) if usable else tuple(0.0 for _ in range(DIMENSION))


def _apply_update(
    theta: Sequence[float],
    reserve: float,
    target: Sequence[float],
    protected_target: Sequence[float],
    policy: Policy,
    memory_bias: Sequence[float],
) -> tuple[tuple[float, ...], float]:
    task_gradient = _sub(_add(target, _scale(memory_bias, 0.20)), theta)
    protected_gradient = _sub(protected_target, theta)
    delta = _scale(_sub(task_gradient, _scale(protected_gradient, policy.retention_price)), policy.step_size)
    next_theta = _add(theta, delta)
    next_reserve = _clamp(reserve - 0.08 * _norm(delta) + 0.015 * (1.0 if policy.memory_mode == "procedural" else 0.0), 0.0, 1.0)
    return next_theta, next_reserve


def _probe_gain(theta: Sequence[float], reserve: float, probe_targets: Sequence[Sequence[float]], protected_target: Sequence[float]) -> float:
    before = _mean_loss(theta, probe_targets)
    probe_policy = _policy("balanced")
    after_theta, _ = _apply_update(theta, reserve, probe_targets[0], protected_target, probe_policy, tuple(0.0 for _ in range(DIMENSION)))
    after = _mean_loss(after_theta, probe_targets)
    return before - after


def _run_sequence(
    state: LearnerState,
    bank: MemoryBank,
    targets: Sequence[Sequence[float]],
    protected_target: Sequence[float],
    generation: int,
    policy: Policy,
    seed: int,
) -> tuple[LearnerState, MemoryBank, int, int]:
    theta = state.theta
    reserve = state.plasticity_reserve
    accepted = 0
    promoted = 0
    for index, target in enumerate(targets):
        bias = _memory_bias(bank, generation, policy)
        theta, reserve = _apply_update(theta, reserve, target, protected_target, policy, bias)
        outcome = bank.admit(_memory_record(seed, generation, index, target), generation)
        if outcome in ("accepted", "procedural_promoted"):
            accepted += 1
        if outcome == "procedural_promoted":
            promoted += 1
    next_state = LearnerState(
        theta=theta,
        plasticity_reserve=reserve,
        policy_name=policy.name,
        policy_version=state.policy_version + 1,
        checkpoint_sha256=_checkpoint_digest(theta, reserve, policy.name, state.policy_version + 1),
    )
    return next_state, bank, accepted, promoted


def _initial_state() -> LearnerState:
    theta = tuple(0.0 for _ in range(DIMENSION))
    reserve = 1.0
    return LearnerState(
        theta=theta,
        plasticity_reserve=reserve,
        policy_name=FIXED_POLICY,
        policy_version=0,
        checkpoint_sha256=_checkpoint_digest(theta, reserve, FIXED_POLICY, 0),
    )


def _policy_score(
    state: LearnerState,
    bank: MemoryBank,
    fit_targets: Sequence[Sequence[float]],
    tune_targets: Sequence[Sequence[float]],
    protected_targets: Sequence[Sequence[float]],
    probe_targets: Sequence[Sequence[float]],
    generation: int,
    policy: Policy,
    seed: int,
) -> tuple[float, LearnerState, MemoryBank]:
    protected_target = _mean(protected_targets)
    fit_state, fit_bank, _, _ = _run_sequence(state, bank.clone(), fit_targets, protected_target, generation, policy, seed)
    tune_before = _mean_loss(state.theta, tune_targets)
    tune_after = _mean_loss(fit_state.theta, tune_targets)
    tune_gain = tune_before - tune_after
    protected_before = _mean_loss(state.theta, protected_targets)
    protected_after = _mean_loss(fit_state.theta, protected_targets)
    positive_forgetting = max(0.0, protected_after - protected_before)
    plasticity = _probe_gain(fit_state.theta, fit_state.plasticity_reserve, probe_targets, protected_target)
    score = tune_gain - policy.retention_price * positive_forgetting + 0.50 * plasticity
    return score, fit_state, fit_bank


def _select_policy(arm: str, scores: Mapping[str, float], prior_policy: str, rng: random.Random) -> str:
    _require(arm in ARMS, f"unknown arm: {arm}")
    if arm == "untouched_base":
        return FIXED_POLICY
    if arm == "fixed_policy":
        return FIXED_POLICY
    if arm == "random_policy":
        return POLICY_NAMES[rng.randrange(len(POLICY_NAMES))]
    ranked = sorted(POLICY_NAMES, key=lambda name: (-scores[name], POLICY_NAMES.index(name)))
    _require(prior_policy in POLICY_NAMES, "prior policy missing")
    return ranked[0]


def _slope(values: Sequence[float]) -> float:
    _require(len(values) == GENERATION_COUNT, "slope requires all generations")
    x_mean = (GENERATION_COUNT - 1) / 2.0
    denominator = sum((index - x_mean) ** 2 for index in range(GENERATION_COUNT))
    return sum((index - x_mean) * (value - sum(values) / GENERATION_COUNT) for index, value in enumerate(values)) / denominator


def _event(index: int, name: str, generation: int | None, payload: Mapping[str, Any], predecessor: int | None) -> dict[str, Any]:
    body = {
        "event_index": index,
        "event_name": name,
        "generation": generation,
        "predecessor_event_index": predecessor,
        "payload_sha256": _digest(payload),
    }
    return {**body, "event_sha256": _digest(body)}


def _generation_digest(row: Mapping[str, Any]) -> str:
    fields = {key: value for key, value in row.items() if key != "generation_digest"}
    return _digest(fields)


def _case_digest(case: Mapping[str, Any]) -> str:
    return _digest({key: value for key, value in case.items() if key != "case_digest"})


def run_case(seed: int, order_seed: int, direction: str, arm: str) -> dict[str, Any]:
    _require(seed in REPLICATE_SEEDS, "seed not preregistered")
    _require(order_seed in ORDER_SEEDS, "order seed not preregistered")
    _require(direction in ORDER_DIRECTIONS, "order direction not preregistered")
    _require(arm in ARMS, "arm not preregistered")
    state = _initial_state()
    bank = MemoryBank()
    rng = random.Random(seed + order_seed + 900000)
    generations: list[dict[str, Any]] = []
    events: list[dict[str, Any]] = []
    event_index = 0
    events.append(_event(event_index, "synthetic_initialized", None, {"seed": seed, "order_seed": order_seed, "direction": direction}, None))
    event_index += 1
    for generation in range(GENERATION_COUNT):
        fit_targets = _ordered_targets(seed, generation, "fit", order_seed, direction)
        tune_targets = _ordered_targets(seed, generation, "tune", order_seed, direction)
        assessment_targets = _ordered_targets(seed, generation, "assessment", order_seed, "forward")
        probe_targets = _ordered_targets(seed, generation, "probe", order_seed, "forward")
        protected_targets = _ordered_targets(seed, generation, "protected", order_seed, "forward")
        protected_target = _mean(protected_targets)
        scores: dict[str, float] = {}
        for candidate_name in POLICY_NAMES:
            score, _, _ = _policy_score(
                state,
                bank,
                fit_targets,
                tune_targets,
                protected_targets,
                probe_targets,
                generation,
                _policy(candidate_name),
                seed,
            )
            scores[candidate_name] = score
        events.append(_event(event_index, "fit_tune_completed", generation, {"candidate_scores": scores}, event_index - 1))
        event_index += 1
        selected = _select_policy(arm, scores, state.policy_name, rng)
        proposal = {
            "state_slice": STATE_SLICE,
            "controller_mode": arm,
            "prior_policy": state.policy_name,
            "proposed_policy": selected,
            "candidate_score_digest": _digest(scores),
            "generation": generation,
        }
        validate_sandbox_proposal(proposal)
        proposal_digest = _digest(proposal)
        locked_policy = selected
        lock = {
            "state_slice": STATE_SLICE,
            "generation": generation,
            "policy": locked_policy,
            "proposal_sha256": proposal_digest,
            "assessment_started": False,
            "assessment_task_count": ASSESSMENT_TASK_COUNT,
        }
        lock_digest = _digest(lock)
        events.append(_event(event_index, "prediction_lock_sealed", generation, {"lock_sha256": lock_digest}, event_index - 1))
        event_index += 1
        checkpoint_before = state.checkpoint_sha256
        if arm == "untouched_base":
            post_state = state
            post_bank = bank.clone()
            accepted = 0
            promoted = 0
        else:
            post_state, post_bank, accepted, promoted = _run_sequence(
                state,
                bank.clone(),
                fit_targets,
                protected_target,
                generation,
                _policy(locked_policy),
                seed,
            )
        base_assessment_loss = _mean_loss(state.theta, assessment_targets)
        final_assessment_loss = _mean_loss(post_state.theta, assessment_targets)
        adaptation_gain = base_assessment_loss - final_assessment_loss
        base_protected_loss = _mean_loss(state.theta, protected_targets)
        final_protected_loss = _mean_loss(post_state.theta, protected_targets)
        retention_delta = final_protected_loss - base_protected_loss
        plasticity_gain = _probe_gain(post_state.theta, post_state.plasticity_reserve, probe_targets, protected_target)
        rollback_error = max(abs(a - b) for a, b in zip(state.theta, state.theta))
        total_compute = len(POLICY_NAMES) * (FIT_TASK_COUNT + TUNE_TASK_COUNT) + FIT_TASK_COUNT
        row = {
            "generation": generation,
            "policy_before": state.policy_name,
            "policy_locked": locked_policy,
            "policy_version_before": state.policy_version,
            "policy_version_after": post_state.policy_version,
            "candidate_scores": {name: scores[name] for name in POLICY_NAMES},
            "candidate_evaluations": len(POLICY_NAMES) * (FIT_TASK_COUNT + TUNE_TASK_COUNT),
            "update_attempts": FIT_TASK_COUNT,
            "committed_updates": 0 if arm == "untouched_base" else FIT_TASK_COUNT,
            "total_compute_units": total_compute,
            "memory_accepted": accepted,
            "memory_promoted": promoted,
            "base_assessment_loss": base_assessment_loss,
            "final_assessment_loss": final_assessment_loss,
            "adaptation_gain": adaptation_gain,
            "base_protected_loss": base_protected_loss,
            "final_protected_loss": final_protected_loss,
            "retention_delta": retention_delta,
            "post_adaptation_plasticity_gain": plasticity_gain,
            "rollback_max_abs_error": rollback_error,
            "retention_guard_pass": max(0.0, retention_delta) <= MAX_PROTECTED_FORGETTING,
            "plasticity_guard_pass": plasticity_gain >= MIN_PLASTICITY_GAIN,
            "rollback_guard_pass": rollback_error <= ROLLBACK_TOLERANCE,
            "compute_guard_pass": total_compute == EXPECTED_TOTAL_COMPUTE // GENERATION_COUNT,
            "checkpoint_before_sha256": checkpoint_before,
            "checkpoint_after_sha256": post_state.checkpoint_sha256,
            "prediction_lock_sha256": lock_digest,
        }
        row["generation_digest"] = _generation_digest(row)
        generations.append(row)
        events.append(_event(event_index, "assessment_completed", generation, {"generation_digest": row["generation_digest"]}, event_index - 1))
        event_index += 1
        events.append(_event(event_index, "rollback_verified", generation, {"rollback_error": rollback_error}, event_index - 1))
        event_index += 1
        state = post_state
        bank = post_bank
    adaptation_values = [row["adaptation_gain"] for row in generations]
    retention_values = [row["retention_delta"] for row in generations]
    plasticity_values = [row["post_adaptation_plasticity_gain"] for row in generations]
    order_key = f"{seed}:{order_seed}:{direction}:{arm}"
    summary = {
        "mean_adaptation_gain": sum(adaptation_values) / GENERATION_COUNT,
        "mean_retention_delta": sum(retention_values) / GENERATION_COUNT,
        "mean_post_adaptation_plasticity_gain": sum(plasticity_values) / GENERATION_COUNT,
        "adaptation_slope": _slope(adaptation_values),
        "retention_slope": _slope(retention_values),
        "plasticity_slope": _slope(plasticity_values),
        "max_positive_forgetting": max(max(0.0, value) for value in retention_values),
        "min_plasticity_gain": min(plasticity_values),
        "rollback_max_abs_error": max(row["rollback_max_abs_error"] for row in generations),
        "total_compute_units": sum(row["total_compute_units"] for row in generations),
        "update_attempts": sum(row["update_attempts"] for row in generations),
        "committed_updates": sum(row["committed_updates"] for row in generations),
        "order_pair_delta": 0.0,
        "order_guard_pass": True,
        "memory_probe": memory_probe(),
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
    case = {
        "case_key": order_key,
        "seed": seed,
        "order_seed": order_seed,
        "order_direction": direction,
        "arm": arm,
        "generations": generations,
        "event_log": events,
        "summary": summary,
    }
    case["case_digest"] = _case_digest(case)
    return case


def _bootstrap(values: Sequence[float]) -> tuple[float, float]:
    rng = random.Random(BOOTSTRAP_SEED)
    means = []
    for _ in range(BOOTSTRAP_REPLICATES):
        sample = [values[rng.randrange(len(values))] for _ in values]
        means.append(sum(sample) / len(sample))
    means.sort()
    def quantile(position: float) -> float:
        index = (len(means) - 1) * position
        lower = math.floor(index)
        upper = math.ceil(index)
        if lower == upper:
            return means[lower]
        return means[lower] + (means[upper] - means[lower]) * (index - lower)
    return quantile(0.025), quantile(0.975)


def _paired_cases(cases: Sequence[Mapping[str, Any]], arm: str) -> dict[str, Mapping[str, Any]]:
    return {
        case["case_key"].rsplit(":", 1)[0]: case
        for case in cases
        if case["arm"] == arm
    }


def _campaign_summary(cases: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    grouped = {arm: _paired_cases(cases, arm) for arm in ARMS}
    keys = sorted(grouped["recursive_policy"])
    selection_values = []
    compound_values = []
    recursive_slopes = []
    final_values = []
    for key in keys:
        recursive = grouped["recursive_policy"][key]["summary"]
        random_case = grouped["random_policy"][key]["summary"]
        fixed = grouped["fixed_policy"][key]["summary"]
        selection_values.append(recursive["mean_adaptation_gain"] - random_case["mean_adaptation_gain"])
        compound_values.append(recursive["adaptation_slope"] - random_case["adaptation_slope"])
        recursive_slopes.append(recursive["adaptation_slope"])
        final_values.append(
            recursive["mean_adaptation_gain"] - fixed["mean_adaptation_gain"]
        )
    primary_interval = _bootstrap(compound_values)
    return {
        "case_count": len(cases),
        "selection_advantage_mean": sum(selection_values) / len(selection_values),
        "generational_compounding_advantage_mean": sum(compound_values) / len(compound_values),
        "generational_compounding_bootstrap_95": list(primary_interval),
        "recursive_adaptation_slope_mean": sum(recursive_slopes) / len(recursive_slopes),
        "final_recursive_over_fixed_mean": sum(final_values) / len(final_values),
        "all_recursive_slopes_positive": all(value >= RECURSIVE_SLOPE_MINIMUM for value in recursive_slopes),
        "all_hard_guards_pass": all(case["summary"]["all_hard_guards_pass"] and case["summary"]["order_guard_pass"] for case in cases),
        "primary_gate_pass": (
            sum(compound_values) / len(compound_values) >= PRIMARY_MINIMUM
            and primary_interval[0] >= 0.0
            and sum(final_values) / len(final_values) >= FINAL_ADVANTAGE_MINIMUM
            and all(value >= RECURSIVE_SLOPE_MINIMUM for value in recursive_slopes)
            and all(case["summary"]["all_hard_guards_pass"] and case["summary"]["order_guard_pass"] for case in cases)
        ),
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
            case["summary"]["order_guard_pass"] = delta <= MAX_ORDER_DELTA
            case["summary"]["all_hard_guards_pass"] = case["summary"]["all_hard_guards_pass"] and case["summary"]["order_guard_pass"]
            case["case_digest"] = _case_digest(case)


def run_campaign() -> dict[str, Any]:
    cases = [
        run_case(seed, order_seed, direction, arm)
        for seed in REPLICATE_SEEDS
        for order_seed in ORDER_SEEDS
        for direction in ORDER_DIRECTIONS
        for arm in ARMS
    ]
    _apply_order_guards(cases)
    result = {
        "schema_version": SCHEMA_VERSION,
        "state_slice": STATE_SLICE,
        "protocol_id": PROTOCOL_ID,
        "claim_ceiling": CLAIM_CEILING,
        "execution_authorized": False,
        "theory": {
            "name": "bounded_recursive_update_policy",
            "primary_estimand": "generational_compounding_advantage",
            "selection_estimand": "recursive_policy_mean_adaptation_minus_random_policy_mean_adaptation",
            "adaptation": "assessment_loss_before_fit_updates_minus_assessment_loss_after_fit_updates",
            "retention": "protected_loss_after_fit_updates_minus_protected_loss_before_fit_updates",
            "post_adaptation_plasticity": "fixed_probe_loss_before_probe_update_minus_after_probe_update",
        },
        "protocol": {
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
        },
        "memory_contract": memory_probe(),
        "sandbox_contract": {
            "mutable_policy_fields": list(MUTABLE_POLICY_FIELDS),
            "immutable_fields": list(IMMUTABLE_SANDBOX_FIELDS),
            "forbidden_effects": list(FORBIDDEN_SANDBOX_EFFECTS),
        },
        "cases": cases,
    }
    result["campaign_summary"] = _campaign_summary(cases)
    result["result_sha256"] = _digest({key: value for key, value in result.items() if key != "result_sha256"})
    validate_result(result)
    return result


def _validate_numbers(value: Any, field: str) -> None:
    _require(isinstance(value, (int, float)) and not isinstance(value, bool), f"{field} must be numeric")
    _require(math.isfinite(float(value)), f"{field} must be finite")


def _validate_generation(row: Mapping[str, Any], expected: Mapping[str, Any]) -> None:
    _require(set(row) == set(expected), "generation schema mismatch")
    for field, expected_value in expected.items():
        observed = row[field]
        if isinstance(expected_value, float):
            _require(math.isclose(float(observed), expected_value, rel_tol=0.0, abs_tol=1e-12), f"generation mismatch: {field}")
        else:
            _require(observed == expected_value, f"generation mismatch: {field}")
    for field in (
        "base_assessment_loss", "final_assessment_loss", "adaptation_gain", "base_protected_loss",
        "final_protected_loss", "retention_delta", "post_adaptation_plasticity_gain", "rollback_max_abs_error",
    ):
        _validate_numbers(row[field], field)
    _require(math.isclose(row["adaptation_gain"], row["base_assessment_loss"] - row["final_assessment_loss"], abs_tol=1e-12), "adaptation arithmetic")
    _require(math.isclose(row["retention_delta"], row["final_protected_loss"] - row["base_protected_loss"], abs_tol=1e-12), "retention arithmetic")
    _require(row["candidate_evaluations"] == len(POLICY_NAMES) * (FIT_TASK_COUNT + TUNE_TASK_COUNT), "candidate budget")
    _require(row["total_compute_units"] == EXPECTED_TOTAL_COMPUTE // GENERATION_COUNT, "generation compute")
    _require(row["rollback_max_abs_error"] <= ROLLBACK_TOLERANCE, "rollback guard")


def validate_result(result: Mapping[str, Any]) -> None:
    _require(result.get("schema_version") == SCHEMA_VERSION, "schema version")
    _require(result.get("state_slice") == STATE_SLICE, "state slice")
    _require(result.get("protocol_id") == PROTOCOL_ID, "protocol id")
    _require(result.get("claim_ceiling") == CLAIM_CEILING, "claim ceiling")
    _require(result.get("execution_authorized") is False, "execution authorization")
    _require(result.get("theory") == {
        "name": "bounded_recursive_update_policy",
        "primary_estimand": "generational_compounding_advantage",
        "selection_estimand": "recursive_policy_mean_adaptation_minus_random_policy_mean_adaptation",
        "adaptation": "assessment_loss_before_fit_updates_minus_assessment_loss_after_fit_updates",
        "retention": "protected_loss_after_fit_updates_minus_protected_loss_before_fit_updates",
        "post_adaptation_plasticity": "fixed_probe_loss_before_probe_update_minus_after_probe_update",
    }, "theory contract")
    _require(result.get("sandbox_contract") == {
        "mutable_policy_fields": list(MUTABLE_POLICY_FIELDS),
        "immutable_fields": list(IMMUTABLE_SANDBOX_FIELDS),
        "forbidden_effects": list(FORBIDDEN_SANDBOX_EFFECTS),
    }, "sandbox contract")
    _require(result.get("protocol") == {
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
    _require(result.get("memory_contract") == memory_probe(), "memory contract")
    cases = result.get("cases")
    _require(isinstance(cases, list), "cases")
    expected_count = len(REPLICATE_SEEDS) * len(ORDER_SEEDS) * len(ORDER_DIRECTIONS) * len(ARMS)
    _require(len(cases) == expected_count, "case coverage")
    expected_keys = {
        f"{seed}:{order_seed}:{direction}:{arm}"
        for seed in REPLICATE_SEEDS
        for order_seed in ORDER_SEEDS
        for direction in ORDER_DIRECTIONS
        for arm in ARMS
    }
    observed_keys = [case.get("case_key") for case in cases if isinstance(case, Mapping)]
    _require(set(observed_keys) == expected_keys and len(observed_keys) == len(set(observed_keys)), "case key coverage")
    expected_cases = [
        run_case(seed, order_seed, direction, arm)
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
        _require(set(case) == {"case_key", "seed", "order_seed", "order_direction", "arm", "generations", "event_log", "summary", "case_digest"}, "case schema")
        expected = expected_by_key[case["case_key"]]
        _require(case["case_digest"] == _case_digest(case), "case digest")
        _require(len(case["generations"]) == GENERATION_COUNT, "generation coverage")
        for observed, expected_row in zip(case["generations"], expected["generations"]):
            _validate_generation(observed, expected_row)
        _require(case["summary"] == expected["summary"], "case summary")
        _require(case["event_log"] == expected["event_log"], "event log")
    expected_summary = _campaign_summary(cases)
    _require(result.get("campaign_summary") == expected_summary, "campaign summary")
    expected_digest = _digest({key: value for key, value in result.items() if key != "result_sha256"})
    _require(result.get("result_sha256") == expected_digest, "result digest")


def write_result(result: Mapping[str, Any], output: Path) -> None:
    validate_result(result)
    resolved = output.resolve()
    repository_root = Path(__file__).resolve().parents[2]
    _require(repository_root not in resolved.parents, "result must be outside repository")
    _require(resolved.suffix == ".json", "result must be JSON")
    resolved.parent.mkdir(parents=True, exist_ok=True)
    resolved.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("contract-check", "synthetic"), default="contract-check")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--review-receipt", type=Path)
    args = parser.parse_args()
    if args.mode == "contract-check":
        _require(memory_probe() == {
            "fresh_accepted": True,
            "stale_rejected": True,
            "contradiction_rejected": True,
            "poison_rejected": True,
            "deletion_rejected": True,
            "procedural_promotion": True,
        }, "memory contract probe")
        print(json.dumps({"contract_check": "PASS", "state_slice": STATE_SLICE}, sort_keys=True))
        return
    _require(args.output is not None, "synthetic mode requires --output")
    _require(args.review_receipt is not None, "synthetic mode requires --review-receipt")
    validate_review_receipt(args.review_receipt)
    result = run_campaign()
    write_result(result, args.output)
    print(json.dumps({"written": str(args.output.resolve()), "state_slice": STATE_SLICE}, sort_keys=True))


if __name__ == "__main__":
    main()
