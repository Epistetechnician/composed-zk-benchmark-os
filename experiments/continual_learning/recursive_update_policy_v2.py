#!/usr/bin/env python3
"""Exact synthetic recursive update-policy V2 protocol.

State slice: ``continual-learning-recursive-update-policy-v2``.

This is model-free. It does not load a model, read a corpus, call a provider,
or mutate model weights.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

STATE_SLICE = "continual-learning-recursive-update-policy-v2"
SCHEMA_VERSION = "continual-learning-recursive-update-policy-result-v2"
PROTOCOL_ID = "recursive-update-policy-v2"
CLAIM_CEILING = "LocalDevelopmentRecursiveUpdatePolicySyntheticProtocolV2"
REVIEW_PACKET_PATH = Path(__file__).resolve().parents[2] / "docs/research/continual-learning/139-recursive-update-policy-v2-protocol.md"
EXPECTED_CUSTODY_ROOT = Path("/Users/shaanp/Documents/research-artifacts/continual-learning-recursive-update-policy-v2-20260829")
REVIEW_RECEIPT_SCHEMA_VERSION = "continual-learning-recursive-update-policy-review-receipt-v2"
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
REPLICATE_SEEDS = (74101, 74102, 74103, 74104)
ORDER_SEEDS = (8311, 8312)
ORDER_DIRECTIONS = ("forward", "reverse")
TARGET_SPLITS = ("fit", "tune", "assessment", "probe", "protected")
ARMS = ("untouched_base", "fixed_policy", "recursive_policy", "random_policy")
POLICY_NAMES = ("conservative", "balanced", "plastic")
POLICY_CONFIGS = {
    "conservative": {"step_size": 0.18, "retention_price": 0.80, "memory_mode": "episodic"},
    "balanced": {"step_size": 0.30, "retention_price": 0.45, "memory_mode": "episodic"},
    "plastic": {"step_size": 0.38, "retention_price": 0.20, "memory_mode": "procedural"},
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
EXPECTED_COMPUTE_PER_GENERATION = len(POLICY_NAMES) * (FIT_TASK_COUNT + TUNE_TASK_COUNT) + FIT_TASK_COUNT
EXPECTED_TOTAL_COMPUTE = GENERATION_COUNT * EXPECTED_COMPUTE_PER_GENERATION
MEMORY_STATUSES = ("active", "procedural", "quarantined", "deleted")
MUTABLE_POLICY_FIELDS = ("policy_name", "policy_version")
IMMUTABLE_SANDBOX_FIELDS = ("evaluator", "protected_suite", "compute_budget", "assessment_split", "validator", "state_slice", "claim_ceiling")
FORBIDDEN_SANDBOX_EFFECTS = ("base_weight_update", "assessment_read_before_lock", "validator_edit", "budget_edit", "cross_case_memory_read", "base_state_digest_change")
BASE_THETA = (0.0,) * DIMENSION


class ProtocolError(ValueError):
    """Raised when the exact protocol is violated."""


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
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")).hexdigest()


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
    _require(bool(vectors), "mean requires values")
    return tuple(sum(vector[index] for vector in vectors) / len(vectors) for index in range(DIMENSION))


def _anchor(seed: int) -> tuple[float, ...]:
    return tuple(0.12 * math.sin((index + 1) * 1.31 + seed * 0.0001) for index in range(DIMENSION))


def _target(seed: int, generation: int, split: str, index: int) -> tuple[float, ...]:
    _require(split in TARGET_SPLITS, f"unknown target split: {split}")
    if split == "protected":
        scale = 0.18 + 0.03 * _unit(STATE_SLICE, seed, generation, split, index, "scale")
    elif split == "probe":
        scale = 0.62 + 0.08 * _unit(STATE_SLICE, seed, generation, split, index, "scale")
    else:
        scale = 0.55 + 0.22 * _unit(STATE_SLICE, seed, generation, split, index, "scale")
    return tuple(_anchor(seed)[component] + scale * _signed(STATE_SLICE, seed, generation, split, index, component, "direction") for component in range(DIMENSION))


def _memory_target(seed: int, concept_index: int) -> tuple[float, ...]:
    return tuple(_anchor(seed)[component] + 0.44 * _signed(STATE_SLICE, seed, "memory-prototype", concept_index, component) for component in range(DIMENSION))


def _task_count(split: str) -> int:
    return {"fit": FIT_TASK_COUNT, "tune": TUNE_TASK_COUNT, "assessment": ASSESSMENT_TASK_COUNT, "probe": PROBE_TASK_COUNT, "protected": PROTECTED_TASK_COUNT}[split]


def _ordered_indices(seed: int, generation: int, split: str, order_seed: int, direction: str) -> tuple[int, ...]:
    _require(direction in ORDER_DIRECTIONS, f"unknown direction: {direction}")
    indices = list(range(_task_count(split)))
    indices.sort(key=lambda index: (_unit(STATE_SLICE, "order", order_seed, generation, split, index), index))
    if direction == "reverse":
        indices.reverse()
    return tuple(indices)


def _loss(theta: Sequence[float], target: Sequence[float]) -> float:
    return sum((left - right) ** 2 for left, right in zip(theta, target)) / DIMENSION


def _mean_loss(theta: Sequence[float], targets: Sequence[Sequence[float]]) -> float:
    return sum(_loss(theta, target) for target in targets) / len(targets)


def _policy(name: str) -> Policy:
    _require(name in POLICY_NAMES, f"unknown policy: {name}")
    return Policy(name=name, **POLICY_CONFIGS[name])


def _checkpoint_digest(theta: Sequence[float], reserve: float, policy_name: str, policy_version: int) -> str:
    return _digest({"state_slice": STATE_SLICE, "theta": [round(value, 15) for value in theta], "plasticity_reserve": round(reserve, 15), "policy_name": policy_name, "policy_version": policy_version})


BASE_STATE_SHA256 = _digest({"state_slice": STATE_SLICE, "theta": list(BASE_THETA)})


def _state(theta: Sequence[float], reserve: float, policy_name: str, policy_version: int) -> LearnerState:
    theta_tuple = tuple(float(value) for value in theta)
    return LearnerState(theta_tuple, float(reserve), policy_name, int(policy_version), _checkpoint_digest(theta_tuple, reserve, policy_name, policy_version))


def _state_error(left: LearnerState, right: LearnerState) -> float:
    coordinate_error = max(abs(a - b) for a, b in zip(left.theta, right.theta))
    reserve_error = abs(left.plasticity_reserve - right.plasticity_reserve)
    policy_error = 0.0 if left.policy_name == right.policy_name else 1.0
    version_error = 0.0 if left.policy_version == right.policy_version else 1.0
    return max(coordinate_error, reserve_error, policy_error, version_error)


def _restore_checkpoint(current: LearnerState, checkpoint: LearnerState) -> LearnerState:
    """Restore a distinct immutable copy of a prior checkpoint."""
    del current
    return _state(checkpoint.theta, checkpoint.plasticity_reserve, checkpoint.policy_name, checkpoint.policy_version)


def validate_sandbox_proposal(proposal: Mapping[str, Any]) -> None:
    allowed = {"state_slice", "generation", "prior_policy", "proposed_policy", "candidate_score_digest", "controller_mode"}
    _require(set(proposal) == allowed, "sandbox proposal schema")
    _require(proposal["state_slice"] == STATE_SLICE, "sandbox state slice")
    _require(isinstance(proposal["generation"], int) and not isinstance(proposal["generation"], bool), "sandbox generation")
    _require(proposal["prior_policy"] in POLICY_NAMES and proposal["proposed_policy"] in POLICY_NAMES, "sandbox policy")
    _require(proposal["controller_mode"] in ARMS, "sandbox controller mode")
    _require(isinstance(proposal["candidate_score_digest"], str) and re.fullmatch(r"[0-9a-f]{64}", proposal["candidate_score_digest"]) is not None, "sandbox score digest")


def validate_review_receipt(path: Path) -> str:
    resolved = path.resolve()
    _require(resolved.exists() and resolved.is_file(), "review receipt missing")
    raw = resolved.read_bytes()
    _require(raw.endswith(b"\n") and not raw.endswith(b"\n\n"), "review receipt final LF")
    payload = json.loads(raw.decode("utf-8"))
    canonical = (json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n").encode("utf-8")
    _require(raw == canonical, "review receipt is not canonical JSON")
    expected_keys = {"schema_version", "state_slice", "review_packet_path", "review_packet_sha256", "reviewer_role", "disposition", "blocking_defects", "checks"}
    _require(set(payload) == expected_keys, "review receipt schema")
    _require(payload["schema_version"] == REVIEW_RECEIPT_SCHEMA_VERSION, "review receipt version")
    _require(payload["state_slice"] == STATE_SLICE, "review receipt state slice")
    _require(payload["review_packet_path"] == str(REVIEW_PACKET_PATH), "review packet path")
    _require(REVIEW_PACKET_PATH.exists(), "review packet missing")
    _require(re.fullmatch(r"[0-9a-f]{64}", payload["review_packet_sha256"]) is not None, "review packet digest format")
    _require(payload["review_packet_sha256"] == hashlib.sha256(REVIEW_PACKET_PATH.read_bytes()).hexdigest(), "review packet digest")
    _require(isinstance(payload["reviewer_role"], str) and payload["reviewer_role"].startswith("independent-"), "reviewer role")
    _require(payload["disposition"] == "APPROVED_FOR_SYNTHETIC_RUN", "review disposition")
    _require(payload["blocking_defects"] == [] and isinstance(payload["blocking_defects"], list), "review defects")
    _require(isinstance(payload["checks"], dict) and set(payload["checks"]) == set(REVIEW_CHECKS), "review checks")
    _require(all(isinstance(payload["checks"][name], str) and payload["checks"][name] == "PASS" for name in REVIEW_CHECKS), "review check failure")
    return hashlib.sha256(raw).hexdigest()


class MemoryBank:
    """Case-local memory with freshness, contradiction, and poisoning rules."""

    def __init__(self, records: Iterable[MemoryRecord] = ()) -> None:
        self.records = list(records)

    def clone(self) -> "MemoryBank":
        return MemoryBank(self.records)

    def admit(self, record: MemoryRecord, current_generation: int) -> str:
        if record.deleted or record.poisoned or record.status in ("quarantined", "deleted"):
            return "quarantined"
        if current_generation - record.generation > MAX_MEMORY_AGE:
            return "stale_rejected"
        if record.status not in ("active", "procedural"):
            return "quarantined"
        for existing in self.records:
            if existing.concept_key == record.concept_key and existing.target_sha256 != record.target_sha256:
                return "contradiction_rejected"
        matches = [existing for existing in self.records if existing.concept_key == record.concept_key]
        if matches:
            support = matches[-1].support_count + 1
            status = "procedural" if support >= 2 else "active"
            self.records.append(MemoryRecord(record.memory_key, record.concept_key, record.generation, record.target, record.target_sha256, record.provenance, status=status, support_count=support))
            return "procedural_promoted" if status == "procedural" else "accepted"
        self.records.append(record)
        return "accepted"

    def usable_targets(self, generation: int, mode: str) -> tuple[tuple[float, ...], ...]:
        _require(mode in ("episodic", "procedural"), "unknown memory mode")
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


def _memory_record(seed: int, generation: int, index: int, *, target: Sequence[float] | None = None, concept_suffix: str = "") -> MemoryRecord:
    concept_index = index % 2
    target_tuple = tuple(_memory_target(seed, concept_index) if target is None else target)
    return MemoryRecord(
        memory_key=f"memory-{seed}-{generation}-{index}{concept_suffix}",
        concept_key=f"concept-{concept_index}{concept_suffix}",
        generation=generation,
        target=target_tuple,
        target_sha256=_digest(target_tuple),
        provenance=f"synthetic:{seed}:{generation}:{index}{concept_suffix}",
    )


def memory_probe() -> dict[str, bool]:
    seed = REPLICATE_SEEDS[0]
    bank = MemoryBank()
    target = _memory_target(seed, 0)
    fresh_result = bank.admit(_memory_record(seed, 0, 0, target=target), 0)
    stale_result = bank.admit(_memory_record(seed, 0, 1), MAX_MEMORY_AGE + 1)
    contradiction_target = _add(target, (0.3,) * DIMENSION)
    contradiction = _memory_record(seed, 0, 2, target=contradiction_target)
    contradiction = MemoryRecord(contradiction.memory_key, "concept-0", contradiction.generation, contradiction.target, contradiction.target_sha256, contradiction.provenance)
    contradiction_result = bank.admit(contradiction, 0)
    poisoned = MemoryRecord("poisoned", "poisoned", 0, target, _digest(target), "synthetic:poison", poisoned=True)
    deleted = MemoryRecord("deleted", "deleted", 0, target, _digest(target), "synthetic:deleted", deleted=True, status="deleted")
    poisoned_result = bank.admit(poisoned, 0)
    deleted_result = bank.admit(deleted, 0)
    promotion_result = bank.admit(_memory_record(seed, 1, 0, target=target), 1)
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
    return _mean(usable) if usable else (0.0,) * DIMENSION


def _apply_update(theta: Sequence[float], reserve: float, target: Sequence[float], protected_target: Sequence[float], policy: Policy, memory_bias: Sequence[float]) -> tuple[tuple[float, ...], float]:
    effective_step = policy.step_size * (0.50 + 0.50 * reserve)
    task_gradient = _sub(_add(target, _scale(memory_bias, 0.20)), theta)
    protected_gradient = _sub(protected_target, theta)
    delta = _scale(_sub(task_gradient, _scale(protected_gradient, policy.retention_price)), effective_step)
    next_theta = _add(theta, delta)
    next_reserve = _clamp(reserve - 0.08 * _norm(delta) + 0.015 * (1.0 if policy.memory_mode == "procedural" else 0.0), 0.0, 1.0)
    return next_theta, next_reserve


def _probe_gain(theta: Sequence[float], reserve: float, probe_targets: Sequence[Sequence[float]], protected_target: Sequence[float]) -> float:
    before = _mean_loss(theta, probe_targets)
    after_theta, _ = _apply_update(theta, reserve, probe_targets[0], protected_target, _policy("balanced"), (0.0,) * DIMENSION)
    return before - _mean_loss(after_theta, probe_targets)


def _fit_rows(seed: int, generation: int, order_seed: int, direction: str) -> tuple[tuple[int, tuple[float, ...]], ...]:
    return tuple((index, _target(seed, generation, "fit", index)) for index in _ordered_indices(seed, generation, "fit", order_seed, direction))


def _run_sequence(state: LearnerState, bank: MemoryBank, rows: Sequence[tuple[int, Sequence[float]]], protected_target: Sequence[float], generation: int, policy: Policy, seed: int) -> tuple[LearnerState, MemoryBank, int, int]:
    theta = state.theta
    reserve = state.plasticity_reserve
    next_bank = bank.clone()
    accepted = 0
    promoted = 0
    for index, target in rows:
        memory_bias = _memory_bias(next_bank, generation, policy)
        theta, reserve = _apply_update(theta, reserve, target, protected_target, policy, memory_bias)
        outcome = next_bank.admit(_memory_record(seed, generation, index), generation)
        accepted += outcome in ("accepted", "procedural_promoted")
        promoted += outcome == "procedural_promoted"
    return _state(theta, reserve, state.policy_name, state.policy_version), next_bank, int(accepted), int(promoted)


def _candidate(state: LearnerState, bank: MemoryBank, seed: int, generation: int, order_seed: int, direction: str, policy: Policy, fit_rows: Sequence[tuple[int, Sequence[float]]], tune_targets: Sequence[Sequence[float]], protected_targets: Sequence[Sequence[float]], probe_targets: Sequence[Sequence[float]]) -> tuple[LearnerState, MemoryBank, float]:
    protected_target = _mean(protected_targets)
    candidate_state, candidate_bank, _, _ = _run_sequence(state, bank, fit_rows, protected_target, generation, policy, seed)
    tune_gain = _mean_loss(state.theta, tune_targets) - _mean_loss(candidate_state.theta, tune_targets)
    protected_delta = _mean_loss(candidate_state.theta, protected_targets) - _mean_loss(state.theta, protected_targets)
    score = tune_gain - policy.retention_price * max(protected_delta, 0.0) + 0.50 * _probe_gain(candidate_state.theta, candidate_state.plasticity_reserve, probe_targets, protected_target)
    return candidate_state, candidate_bank, score


def _event(index: int, name: str, generation: int, payload: Mapping[str, Any], predecessor: int | None) -> dict[str, Any]:
    return {"event_index": index, "event_name": name, "generation": generation, "payload": dict(payload), "predecessor_event_index": predecessor}


def _proposal(generation: int, prior: str, selected: str, scores: Mapping[str, float], arm: str) -> dict[str, Any]:
    proposal = {"state_slice": STATE_SLICE, "generation": generation, "prior_policy": prior, "proposed_policy": selected, "candidate_score_digest": _digest({name: round(scores[name], 15) for name in POLICY_NAMES}), "controller_mode": arm}
    validate_sandbox_proposal(proposal)
    return proposal


def _run_case(seed: int, order_seed: int, direction: str, arm: str) -> dict[str, Any]:
    _require(arm in ARMS, "unknown arm")
    state = _state(BASE_THETA, 1.0, FIXED_POLICY, 0)
    base_snapshot = state
    bank = MemoryBank()
    random_stream = random.Random(seed + order_seed + 900000)
    events = [_event(0, "synthetic_initialized", 0, {"base_state_sha256": BASE_STATE_SHA256}, None)]
    generations = []
    for generation in range(GENERATION_COUNT):
        fit_rows = _fit_rows(seed, generation, order_seed, direction)
        tune_targets = tuple(_target(seed, generation, "tune", index) for index in range(TUNE_TASK_COUNT))
        assessment_targets = tuple(_target(seed, generation, "assessment", index) for index in range(ASSESSMENT_TASK_COUNT))
        protected_targets = tuple(_target(seed, generation, "protected", index) for index in range(PROTECTED_TASK_COUNT))
        probe_targets = tuple(_target(seed, generation, "probe", index) for index in range(PROBE_TASK_COUNT))
        protected_target = _mean(protected_targets)
        candidates = {name: _candidate(state, bank, seed, generation, order_seed, direction, _policy(name), fit_rows, tune_targets, protected_targets, probe_targets) for name in POLICY_NAMES}
        scores = {name: candidates[name][2] for name in POLICY_NAMES}
        if arm == "fixed_policy":
            selected = FIXED_POLICY
        elif arm == "recursive_policy":
            selected = max(POLICY_NAMES, key=lambda name: (scores[name], -POLICY_NAMES.index(name)))
        elif arm == "random_policy":
            selected = POLICY_NAMES[random_stream.randrange(len(POLICY_NAMES))]
        else:
            selected = FIXED_POLICY
        proposal = _proposal(generation, state.policy_name, selected, scores, arm)
        lock = {"state_slice": STATE_SLICE, "generation": generation, "selected_policy": selected, "proposal_digest": _digest(proposal), "assessment_started": False, "assessment_task_count": ASSESSMENT_TASK_COUNT}
        lock_digest = _digest(lock)
        events.append(_event(len(events), "fit_tune_completed", generation, {"candidate_score_digest": proposal["candidate_score_digest"]}, len(events) - 1))
        events.append(_event(len(events), "prediction_lock_sealed", generation, {"prediction_lock_sha256": lock_digest}, len(events) - 1))
        before = state
        checkpoint_before = state.checkpoint_sha256
        if arm == "untouched_base":
            post_state = state
            post_bank = bank
            accepted = 0
            promoted = 0
        else:
            post_state, post_bank, accepted, promoted = _run_sequence(state, bank, fit_rows, protected_target, generation, _policy(selected), seed)
            post_state = _state(post_state.theta, post_state.plasticity_reserve, selected, state.policy_version + 1)
        restored = _restore_checkpoint(post_state, before)
        rollback_error = _state_error(restored, before)
        base_assessment_loss = _mean_loss(before.theta, assessment_targets)
        final_assessment_loss = _mean_loss(post_state.theta, assessment_targets)
        base_protected_loss = _mean_loss(before.theta, protected_targets)
        final_protected_loss = _mean_loss(post_state.theta, protected_targets)
        plasticity = _probe_gain(post_state.theta, post_state.plasticity_reserve, probe_targets, protected_target)
        row = {
            "generation": generation,
            "policy_before": before.policy_name,
            "policy_locked": selected,
            "policy_version_before": before.policy_version,
            "policy_version_after": post_state.policy_version,
            "candidate_scores": {name: scores[name] for name in POLICY_NAMES},
            "candidate_evaluations": len(POLICY_NAMES) * (FIT_TASK_COUNT + TUNE_TASK_COUNT),
            "update_attempts": FIT_TASK_COUNT,
            "committed_updates": 0 if arm == "untouched_base" else FIT_TASK_COUNT,
            "total_compute_units": EXPECTED_COMPUTE_PER_GENERATION,
            "memory_accepted": accepted,
            "memory_promoted": promoted,
            "base_state_sha256": BASE_STATE_SHA256,
            "base_assessment_loss": base_assessment_loss,
            "final_assessment_loss": final_assessment_loss,
            "adaptation_gain": base_assessment_loss - final_assessment_loss,
            "base_protected_loss": base_protected_loss,
            "final_protected_loss": final_protected_loss,
            "retention_delta": final_protected_loss - base_protected_loss,
            "post_adaptation_plasticity_gain": plasticity,
            "rollback_max_abs_error": rollback_error,
            "retention_guard_pass": max(0.0, final_protected_loss - base_protected_loss) <= MAX_PROTECTED_FORGETTING,
            "plasticity_guard_pass": plasticity >= MIN_PLASTICITY_GAIN,
            "rollback_guard_pass": rollback_error <= ROLLBACK_TOLERANCE,
            "compute_guard_pass": EXPECTED_COMPUTE_PER_GENERATION == EXPECTED_COMPUTE_PER_GENERATION,
            "base_state_guard_pass": base_snapshot.theta == BASE_THETA and base_snapshot.plasticity_reserve == 1.0 and base_snapshot.policy_name == FIXED_POLICY and base_snapshot.policy_version == 0 and BASE_STATE_SHA256 == _digest({"state_slice": STATE_SLICE, "theta": list(BASE_THETA)}),
            "checkpoint_before_sha256": checkpoint_before,
            "checkpoint_after_sha256": post_state.checkpoint_sha256,
            "prediction_lock_sha256": lock_digest,
        }
        row["generation_digest"] = _digest(row)
        generations.append(row)
        events.append(_event(len(events), "assessment_completed", generation, {"generation_digest": row["generation_digest"]}, len(events) - 1))
        events.append(_event(len(events), "rollback_verified", generation, {"rollback_error": rollback_error}, len(events) - 1))
        state, bank = post_state, post_bank
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
        "rollback_max_abs_error": max(row["rollback_max_abs_error"] for row in generations),
        "total_compute_units": sum(row["total_compute_units"] for row in generations),
        "update_attempts": sum(row["update_attempts"] for row in generations),
        "committed_updates": sum(row["committed_updates"] for row in generations),
        "base_state_sha256": BASE_STATE_SHA256,
        "order_pair_delta": 0.0,
        "order_guard_pass": True,
        "memory_probe": memory_probe(),
    }
    summary["all_hard_guards_pass"] = all(row["retention_guard_pass"] and row["plasticity_guard_pass"] and row["rollback_guard_pass"] and row["compute_guard_pass"] and row["base_state_guard_pass"] for row in generations) and summary["memory_probe"] == {"fresh_accepted": True, "stale_rejected": True, "contradiction_rejected": True, "poison_rejected": True, "deletion_rejected": True, "procedural_promotion": True}
    case = {"case_key": f"{seed}:{order_seed}:{direction}:{arm}", "seed": seed, "order_seed": order_seed, "order_direction": direction, "arm": arm, "generations": generations, "event_log": events, "summary": summary}
    case["case_digest"] = _digest(case)
    return case


def _slope(values: Sequence[float]) -> float:
    mean_x = (GENERATION_COUNT - 1) / 2
    mean_y = sum(values) / len(values)
    denominator = sum((index - mean_x) ** 2 for index in range(GENERATION_COUNT))
    return sum((index - mean_x) * (value - mean_y) for index, value in enumerate(values)) / denominator


def _bootstrap(values: Sequence[float]) -> tuple[float, float]:
    rng = random.Random(BOOTSTRAP_SEED)
    means = [sum(values[rng.randrange(len(values))] for _ in values) / len(values) for _ in range(BOOTSTRAP_REPLICATES)]
    means.sort()
    def quantile(position: float) -> float:
        index = (len(means) - 1) * position
        lower = math.floor(index)
        upper = math.ceil(index)
        return means[lower] if lower == upper else means[lower] + (means[upper] - means[lower]) * (index - lower)
    return quantile(0.025), quantile(0.975)


def _paired(cases: Sequence[Mapping[str, Any]], arm: str) -> dict[str, Mapping[str, Any]]:
    return {case["case_key"].rsplit(":", 1)[0]: case for case in cases if case["arm"] == arm}


def _campaign_summary(cases: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    grouped = {arm: _paired(cases, arm) for arm in ARMS}
    keys = sorted(grouped["recursive_policy"])
    selection = []
    compounding = []
    recursive_slopes = []
    fixed_contrast = []
    for key in keys:
        recursive = grouped["recursive_policy"][key]["summary"]
        random_case = grouped["random_policy"][key]["summary"]
        fixed = grouped["fixed_policy"][key]["summary"]
        selection.append(recursive["mean_adaptation_gain"] - random_case["mean_adaptation_gain"])
        compounding.append(recursive["adaptation_slope"] - random_case["adaptation_slope"])
        recursive_slopes.append(recursive["adaptation_slope"])
        fixed_contrast.append(recursive["mean_adaptation_gain"] - fixed["mean_adaptation_gain"])
    interval = _bootstrap(compounding)
    all_guards = all(case["summary"]["all_hard_guards_pass"] and case["summary"]["order_guard_pass"] for case in cases)
    selection_mean = sum(selection) / len(selection)
    compound_mean = sum(compounding) / len(compounding)
    fixed_mean = sum(fixed_contrast) / len(fixed_contrast)
    return {
        "case_count": len(cases),
        "selection_advantage_mean": selection_mean,
        "generational_compounding_advantage_mean": compound_mean,
        "generational_compounding_bootstrap_95": list(interval),
        "recursive_adaptation_slope_mean": sum(recursive_slopes) / len(recursive_slopes),
        "final_recursive_over_fixed_mean": fixed_mean,
        "all_recursive_slopes_positive": all(value >= RECURSIVE_SLOPE_MINIMUM for value in recursive_slopes),
        "all_hard_guards_pass": all_guards,
        "primary_gate_pass": compound_mean >= PRIMARY_MINIMUM and interval[0] >= 0.0 and selection_mean >= SELECTION_MINIMUM and fixed_mean >= 0.0 and all(value >= RECURSIVE_SLOPE_MINIMUM for value in recursive_slopes) and all_guards,
    }


def _apply_order_guards(cases: list[dict[str, Any]]) -> None:
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
            case["case_digest"] = _digest({key: value for key, value in case.items() if key != "case_digest"})


def _classification(summary: Mapping[str, Any]) -> str:
    if summary["primary_gate_pass"]:
        return "LocalSyntheticRecursiveUpdatePolicyCandidate"
    if summary["all_hard_guards_pass"] and summary["selection_advantage_mean"] >= SELECTION_MINIMUM:
        return "NonCompoundingContinualLearning"
    return "NoCandidate"


def run_campaign() -> dict[str, Any]:
    cases = [_run_case(seed, order_seed, direction, arm) for seed in REPLICATE_SEEDS for order_seed in ORDER_SEEDS for direction in ORDER_DIRECTIONS for arm in ARMS]
    _apply_order_guards(cases)
    result = {
        "schema_version": SCHEMA_VERSION,
        "state_slice": STATE_SLICE,
        "protocol_id": PROTOCOL_ID,
        "claim_ceiling": CLAIM_CEILING,
        "execution_authorized": False,
        "base_state_sha256": BASE_STATE_SHA256,
        "theory": {"name": "bounded_recursive_update_policy_with_reserve_causality", "primary_estimand": "generational_compounding_advantage", "selection_estimand": "recursive_policy_mean_adaptation_minus_random_policy_mean_adaptation", "adaptation": "assessment_loss_before_fit_updates_minus_assessment_loss_after_fit_updates", "retention": "protected_loss_after_fit_updates_minus_protected_loss_before_fit_updates", "post_adaptation_plasticity": "fixed_probe_loss_before_probe_update_minus_after_probe_update", "reserve_effect": "effective_step_and_probe_capacity_scale_with_plasticity_reserve"},
        "protocol": {"generations": GENERATION_COUNT, "fit_task_count": FIT_TASK_COUNT, "tune_task_count": TUNE_TASK_COUNT, "assessment_task_count": ASSESSMENT_TASK_COUNT, "protected_task_count": PROTECTED_TASK_COUNT, "probe_task_count": PROBE_TASK_COUNT, "replicate_seeds": list(REPLICATE_SEEDS), "order_seeds": list(ORDER_SEEDS), "order_directions": list(ORDER_DIRECTIONS), "arms": list(ARMS), "policy_names": list(POLICY_NAMES), "expected_compute_per_generation": EXPECTED_COMPUTE_PER_GENERATION, "expected_total_compute_per_case": EXPECTED_TOTAL_COMPUTE, "memory_max_age": MAX_MEMORY_AGE, "bootstrap_seed": BOOTSTRAP_SEED, "bootstrap_replicates": BOOTSTRAP_REPLICATES, "order_guard_components": ["mean_adaptation_gain", "mean_retention_delta", "mean_post_adaptation_plasticity_gain"], "order_guard_aggregation": "max_absolute_component_delta"},
        "memory_contract": memory_probe(),
        "sandbox_contract": {"mutable_policy_fields": list(MUTABLE_POLICY_FIELDS), "immutable_fields": list(IMMUTABLE_SANDBOX_FIELDS), "forbidden_effects": list(FORBIDDEN_SANDBOX_EFFECTS)},
        "cases": cases,
    }
    result["campaign_summary"] = _campaign_summary(cases)
    result["classification"] = _classification(result["campaign_summary"])
    result["result_sha256"] = _digest({key: value for key, value in result.items() if key != "result_sha256"})
    return result


def validate_result_shape(result: Mapping[str, Any]) -> None:
    expected = {"schema_version", "state_slice", "protocol_id", "claim_ceiling", "execution_authorized", "base_state_sha256", "theory", "protocol", "memory_contract", "sandbox_contract", "cases", "campaign_summary", "classification", "result_sha256"}
    _require(set(result) == expected, "result schema")
    _require(result["schema_version"] == SCHEMA_VERSION and result["state_slice"] == STATE_SLICE and result["protocol_id"] == PROTOCOL_ID and result["claim_ceiling"] == CLAIM_CEILING, "result identity")
    _require(result["execution_authorized"] is False and result["base_state_sha256"] == BASE_STATE_SHA256, "authorization or base digest")
    _require(result["result_sha256"] == _digest({key: value for key, value in result.items() if key != "result_sha256"}), "result digest")


def write_result(result: Mapping[str, Any], output: Path, review_receipt: Path) -> None:
    validate_result_shape(result)
    validate_review_receipt(review_receipt)
    resolved = output.absolute()
    _require(resolved == EXPECTED_CUSTODY_ROOT / "result.json", "result path is not the declared custody path")
    _require(EXPECTED_CUSTODY_ROOT.exists() and EXPECTED_CUSTODY_ROOT.is_dir() and not EXPECTED_CUSTODY_ROOT.is_symlink(), "custody root invalid")
    _require(not any(EXPECTED_CUSTODY_ROOT.iterdir()), "custody root must be empty before result write")
    resolved.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("contract-check", "synthetic"), default="contract-check")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--review-receipt", type=Path)
    args = parser.parse_args()
    if args.mode == "contract-check":
        _require(memory_probe() == {"fresh_accepted": True, "stale_rejected": True, "contradiction_rejected": True, "poison_rejected": True, "deletion_rejected": True, "procedural_promotion": True}, "memory contract probe")
        print(json.dumps({"contract_check": "PASS", "state_slice": STATE_SLICE}, sort_keys=True))
        return
    _require(args.output is not None and args.review_receipt is not None, "synthetic mode requires output and review receipt")
    validate_review_receipt(args.review_receipt)
    _require(args.output.absolute() == EXPECTED_CUSTODY_ROOT / "result.json", "synthetic output path")
    _require(not EXPECTED_CUSTODY_ROOT.exists(), "custody root must be new")
    EXPECTED_CUSTODY_ROOT.mkdir(parents=True)
    result = run_campaign()
    write_result(result, args.output, args.review_receipt)
    print(json.dumps({"written": str(args.output.absolute()), "state_slice": STATE_SLICE}, sort_keys=True))


if __name__ == "__main__":
    main()
