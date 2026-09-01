#!/usr/bin/env python3
"""Pure control-plane harness for evidence-conditioned multi-timescale updates.

State slice: ``astral-evidence-conditioned-multiscale-plasticity-v1``.

This module deliberately does not load a model, train weights, invoke a
provider, or implement a ZK/PQC backend.  It tests the surrounding contract:
shard identity, receipt binding, dynamic verification policy, bounded
oscillators, shadow-before-commit ordering, reversible rollback, and a small
aggregate-only fixture report.  Fixture receipts are contract placeholders;
they must not be described as cryptographic proof evidence.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import Any, Mapping


STATE_SLICE = "astral-evidence-conditioned-multiscale-plasticity-v1"
SCHEMA_VERSION = "astral-evidence-conditioned-dynamics-result-v1"
RECEIPT_SOURCE = "deterministic-contract-fixture-not-zk-or-pqc"
MODES = ("fixed_baseline", "adaptive_gate", "wave_only", "adaptive_wave")
STATES = ("new", "captured", "classified", "verified", "shadowed", "committed", "quarantined", "rolled_back")
MIN_REPEAT_AGREEMENT = 0.90


class ProtocolError(ValueError):
    """Raised when a fixture violates the frozen control-plane contract."""


@dataclass(frozen=True)
class ProtocolConfig:
    seed: int = 20260828
    shard_count: int = 12
    commit_threshold: float = 0.10
    high_frequency: float = 0.25
    low_frequency: float = 0.0625
    high_amplitude: float = 0.12
    low_amplitude: float = 0.08
    min_wave_multiplier: float = 0.75
    max_wave_multiplier: float = 1.25


@dataclass(frozen=True)
class Shard:
    shard_id: str
    seed: int
    sequence: int
    category: str
    novelty: float
    uncertainty: float
    contradiction: float
    ontological_stability: float
    heldout_gain: float
    forgetting_cost: float
    payload_sha256: str


@dataclass(frozen=True)
class VerificationReceipt:
    shard_id: str
    statement_sha256: str
    integrity_verified: bool
    computation_verified: bool
    verifier_cost_units: int
    receipt_source: str
    receipt_sha256: str


@dataclass(frozen=True)
class ShadowEvaluation:
    shard_id: str
    heldout_gain: float
    forgetting_cost: float
    repeat_agreement: float


@dataclass(frozen=True)
class AdmissionPlan:
    mode: str
    risk_score: float
    verification_ratio: float
    requires_integrity: bool
    requires_computation: bool
    wave_multiplier: float
    effective_gain: float


@dataclass(frozen=True)
class LearnerState:
    version: int = 0
    committed_shards: tuple[str, ...] = ()
    quarantined_shards: tuple[str, ...] = ()
    rolled_back_shards: tuple[str, ...] = ()
    committed_effects: tuple[tuple[str, float], ...] = ()
    fast_value: float = 0.0
    slow_value: float = 0.0


@dataclass(frozen=True)
class Transition:
    shard_id: str
    step: int
    action: str
    state_before: str
    state_after: str
    reason: str
    event_sha256: str


@dataclass(frozen=True)
class ProcessResult:
    state: LearnerState
    final_state: str
    plan: AdmissionPlan
    transitions: tuple[Transition, ...]


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


def _validate_config(config: ProtocolConfig) -> None:
    _require(isinstance(config.seed, int) and not isinstance(config.seed, bool), "seed must be an integer")
    _require(isinstance(config.shard_count, int) and not isinstance(config.shard_count, bool), "shard_count must be an integer")
    for field in (
        "commit_threshold",
        "high_frequency",
        "low_frequency",
        "high_amplitude",
        "low_amplitude",
        "min_wave_multiplier",
        "max_wave_multiplier",
    ):
        _finite(getattr(config, field), field)
    _require(config.shard_count >= 4, "shard_count must be at least 4")
    _require(config.commit_threshold >= 0.0, "commit_threshold must be nonnegative")
    _require(config.high_frequency > config.low_frequency > 0.0, "frequencies must be positive and ordered")
    _require(config.high_amplitude >= 0.0 and config.low_amplitude >= 0.0, "wave amplitudes must be nonnegative")
    _require(0.0 < config.min_wave_multiplier <= 1.0, "min_wave_multiplier must be in (0, 1]")
    _require(config.max_wave_multiplier >= 1.0, "max_wave_multiplier must be at least 1")
    _require(config.min_wave_multiplier < config.max_wave_multiplier, "wave bounds must be ordered")


def _payload_body(config: ProtocolConfig, index: int, category: str) -> dict[str, Any]:
    return {
        "seed": config.seed,
        "sequence": index,
        "category": category,
        "state_slice": STATE_SLICE,
    }


def make_shards(config: ProtocolConfig = ProtocolConfig()) -> tuple[Shard, ...]:
    """Create deterministic fixture shards with distinct evidence profiles."""

    _validate_config(config)
    profiles = (
        ("stable", 0.15, 0.10, 0.00, 0.90, 0.18, 0.01),
        ("novel", 0.80, 0.45, 0.05, 0.65, 0.14, 0.04),
        ("contested", 0.62, 0.78, 0.72, 0.30, 0.12, 0.22),
        ("stable", 0.20, 0.12, 0.02, 0.86, 0.16, 0.02),
    )
    shards: list[Shard] = []
    for index in range(config.shard_count):
        category, novelty, uncertainty, contradiction, stability, gain, forgetting = profiles[index % len(profiles)]
        body = _payload_body(config, index, category)
        shards.append(
            Shard(
                shard_id=f"shard-{index:03d}",
                seed=config.seed,
                sequence=index,
                category=category,
                novelty=novelty,
                uncertainty=uncertainty,
                contradiction=contradiction,
                ontological_stability=stability,
                heldout_gain=gain,
                forgetting_cost=forgetting,
                payload_sha256=_digest(body),
            )
        )
    return tuple(shards)


def make_receipt(shard: Shard, *, computation_verified: bool | None = None) -> VerificationReceipt:
    """Create a digest-bound fixture receipt, never a real ZK/PQC proof."""

    _validate_shard(shard)
    computation = shard.category != "contested" if computation_verified is None else computation_verified
    body = {
        "shard_id": shard.shard_id,
        "statement_sha256": shard.payload_sha256,
        "integrity_verified": True,
        "computation_verified": computation,
        "verifier_cost_units": 2 if computation else 1,
        "receipt_source": RECEIPT_SOURCE,
    }
    return VerificationReceipt(**body, receipt_sha256=_digest(body))


def make_shadow_evaluation(shard: Shard) -> ShadowEvaluation:
    """Return a deterministic held-out fixture evaluation for one shard."""

    return ShadowEvaluation(
        shard_id=shard.shard_id,
        heldout_gain=shard.heldout_gain,
        forgetting_cost=shard.forgetting_cost,
        repeat_agreement=1.0 if shard.category != "novel" else 0.97,
    )


def wave_multiplier(step: int, config: ProtocolConfig = ProtocolConfig()) -> float:
    """Return a bounded high/low-frequency control multiplier."""

    _validate_config(config)
    _require(isinstance(step, int) and not isinstance(step, bool) and step >= 0, "step must be a nonnegative integer")
    fast = config.high_amplitude * math.sin(2.0 * math.pi * config.high_frequency * step)
    slow = config.low_amplitude * math.cos(2.0 * math.pi * config.low_frequency * step)
    return _clamp(1.0 + fast + slow, config.min_wave_multiplier, config.max_wave_multiplier)


def risk_score(shard: Shard) -> float:
    """Compute a measurable uncertainty/risk proxy, not an ontological truth claim."""

    return _clamp(
        0.45 * shard.uncertainty
        + 0.25 * shard.novelty
        + 0.20 * shard.contradiction
        + 0.10 * (1.0 - shard.ontological_stability),
        0.0,
        1.0,
    )


def admission_plan(shard: Shard, step: int, mode: str, config: ProtocolConfig = ProtocolConfig()) -> AdmissionPlan:
    """Derive fixed or adaptive admission requirements from measurable fields."""

    _validate_config(config)
    _require(mode in MODES, f"unknown mode: {mode}")
    risk = risk_score(shard)
    wave = wave_multiplier(step, config) if mode in ("wave_only", "adaptive_wave") else 1.0
    adaptive = mode in ("adaptive_gate", "adaptive_wave")
    ratio = 0.0
    if adaptive:
        ratio = _clamp(0.20 + (0.65 * risk) + (0.15 * (wave - 1.0)), 0.0, 1.0)
    return AdmissionPlan(
        mode=mode,
        risk_score=risk,
        verification_ratio=ratio,
        requires_integrity=adaptive and ratio >= 0.45,
        requires_computation=adaptive and ratio >= 0.62,
        wave_multiplier=wave,
        effective_gain=make_shadow_evaluation(shard).heldout_gain * wave,
    )


def _validate_shard(shard: Shard) -> None:
    _require(isinstance(shard.shard_id, str) and shard.shard_id, "shard_id required")
    _require(isinstance(shard.seed, int) and not isinstance(shard.seed, bool), "invalid shard seed")
    _require(isinstance(shard.sequence, int) and not isinstance(shard.sequence, bool) and shard.sequence >= 0, "invalid shard sequence")
    _require(shard.category in {"stable", "novel", "contested"}, "unknown shard category")
    for field in ("novelty", "uncertainty", "contradiction", "ontological_stability"):
        _unit(getattr(shard, field), field)
    for field in ("heldout_gain", "forgetting_cost"):
        _finite(getattr(shard, field), field)
    _require(shard.forgetting_cost >= 0.0, "forgetting_cost must be nonnegative")
    _require(isinstance(shard.payload_sha256, str) and len(shard.payload_sha256) == 64, "invalid payload digest")
    expected_payload = _payload_body(
        ProtocolConfig(seed=shard.seed, shard_count=4),
        shard.sequence,
        shard.category,
    )
    _require(shard.payload_sha256 == _digest(expected_payload), "payload digest mismatch")


def _validate_receipt(receipt: VerificationReceipt, shard: Shard) -> None:
    _require(receipt.shard_id == shard.shard_id, "receipt/shard identity mismatch")
    _require(receipt.statement_sha256 == shard.payload_sha256, "receipt statement digest mismatch")
    _require(isinstance(receipt.integrity_verified, bool), "integrity_verified must be boolean")
    _require(isinstance(receipt.computation_verified, bool), "computation_verified must be boolean")
    _require(receipt.receipt_source == RECEIPT_SOURCE, "unsupported receipt source")
    _require(isinstance(receipt.verifier_cost_units, int) and receipt.verifier_cost_units > 0, "invalid verifier cost")
    _require(isinstance(receipt.receipt_sha256, str) and len(receipt.receipt_sha256) == 64, "invalid receipt digest")
    unsigned = asdict(receipt)
    declared = unsigned.pop("receipt_sha256")
    _require(declared == _digest(unsigned), "receipt digest mismatch")


def _transition(shard_id: str, step: int, action: str, before: str, after: str, reason: str) -> Transition:
    _require(before in STATES and after in STATES, "invalid transition state")
    body = {
        "shard_id": shard_id,
        "step": step,
        "action": action,
        "state_before": before,
        "state_after": after,
        "reason": reason,
    }
    return Transition(**body, event_sha256=_digest(body))


def _commit_state(state: LearnerState, shard: Shard, applied_gain: float, config: ProtocolConfig) -> LearnerState:
    _require(shard.shard_id not in state.committed_shards, "duplicate committed shard")
    effects = state.committed_effects + ((shard.shard_id, applied_gain),)
    fast = sum(effect for _, effect in effects)
    return replace(
        state,
        version=state.version + 1,
        committed_shards=state.committed_shards + (shard.shard_id,),
        committed_effects=effects,
        fast_value=fast,
        slow_value=fast * (config.low_frequency / config.high_frequency),
    )


def rollback(
    state: LearnerState,
    shard_id: str,
    step: int,
    config: ProtocolConfig = ProtocolConfig(),
) -> tuple[LearnerState, Transition]:
    """Remove one committed update and emit a reversible state transition."""

    _validate_config(config)
    _require(shard_id in state.committed_shards, "cannot rollback an uncommitted shard")
    remaining = tuple(item for item in state.committed_shards if item != shard_id)
    effects = tuple(item for item in state.committed_effects if item[0] != shard_id)
    fast = sum(effect for _, effect in effects)
    updated = replace(
        state,
        version=state.version + 1,
        committed_shards=remaining,
        rolled_back_shards=state.rolled_back_shards + (shard_id,),
        committed_effects=effects,
        fast_value=fast,
        slow_value=fast * (config.low_frequency / config.high_frequency),
    )
    event = _transition(shard_id, step, "rollback", "committed", "rolled_back", "operator_reversible_rollback")
    return updated, event


def process_shard(
    state: LearnerState,
    shard: Shard,
    receipt: VerificationReceipt | None,
    evaluation: ShadowEvaluation,
    step: int,
    mode: str,
    config: ProtocolConfig = ProtocolConfig(),
) -> ProcessResult:
    """Run one shard through the fixed state machine."""

    _validate_config(config)
    _validate_shard(shard)
    _require(evaluation.shard_id == shard.shard_id, "evaluation/shard identity mismatch")
    _finite(evaluation.heldout_gain, "evaluation.heldout_gain")
    _finite(evaluation.forgetting_cost, "evaluation.forgetting_cost")
    _unit(evaluation.repeat_agreement, "evaluation.repeat_agreement")
    _require(mode in MODES, f"unknown mode: {mode}")
    plan = admission_plan(shard, step, mode, config)
    transitions = [
        _transition(shard.shard_id, step, "capture", "new", "captured", "payload_digest_bound"),
        _transition(shard.shard_id, step, "classify", "captured", "classified", "measurable_risk_features"),
    ]

    if receipt is not None:
        try:
            _validate_receipt(receipt, shard)
        except ProtocolError as exc:
            transitions.append(_transition(shard.shard_id, step, "quarantine", "classified", "quarantined", str(exc)))
            updated = replace(state, version=state.version + 1, quarantined_shards=state.quarantined_shards + (shard.shard_id,))
            return ProcessResult(updated, "quarantined", plan, tuple(transitions))

    if plan.requires_integrity and (receipt is None or not receipt.integrity_verified):
        transitions.append(_transition(shard.shard_id, step, "quarantine", "classified", "quarantined", "integrity_receipt_required"))
        updated = replace(state, version=state.version + 1, quarantined_shards=state.quarantined_shards + (shard.shard_id,))
        return ProcessResult(updated, "quarantined", plan, tuple(transitions))
    if plan.requires_computation and (receipt is None or not receipt.computation_verified):
        transitions.append(_transition(shard.shard_id, step, "quarantine", "classified", "quarantined", "computation_receipt_required"))
        updated = replace(state, version=state.version + 1, quarantined_shards=state.quarantined_shards + (shard.shard_id,))
        return ProcessResult(updated, "quarantined", plan, tuple(transitions))

    transitions.append(_transition(shard.shard_id, step, "verify", "classified", "verified", "requirements_satisfied"))
    transitions.append(_transition(shard.shard_id, step, "shadow", "verified", "shadowed", "heldout_evaluation_before_commit"))
    effective_gain = evaluation.heldout_gain * plan.wave_multiplier
    if evaluation.repeat_agreement < MIN_REPEAT_AGREEMENT:
        transitions.append(_transition(shard.shard_id, step, "quarantine", "shadowed", "quarantined", "repeatability_guard_failed"))
        updated = replace(state, version=state.version + 1, quarantined_shards=state.quarantined_shards + (shard.shard_id,))
        return ProcessResult(updated, "quarantined", plan, tuple(transitions))
    if effective_gain < config.commit_threshold:
        transitions.append(_transition(shard.shard_id, step, "quarantine", "shadowed", "quarantined", "heldout_gain_below_commit_threshold"))
        updated = replace(state, version=state.version + 1, quarantined_shards=state.quarantined_shards + (shard.shard_id,))
        return ProcessResult(updated, "quarantined", plan, tuple(transitions))

    updated = _commit_state(state, shard, effective_gain, config)
    transitions.append(_transition(shard.shard_id, step, "commit", "shadowed", "committed", "heldout_gain_and_guards_passed"))
    return ProcessResult(updated, "committed", plan, tuple(transitions))


def _state_dict(state: LearnerState) -> dict[str, Any]:
    return asdict(state)


def _validate_transition(transition: Mapping[str, Any]) -> None:
    _require(isinstance(transition, Mapping), "transition must be an object")
    required = ("shard_id", "step", "action", "state_before", "state_after", "reason", "event_sha256")
    for field in required:
        _require(field in transition, f"transition missing {field}")
    _require(isinstance(transition["step"], int) and not isinstance(transition["step"], bool) and transition["step"] >= 0, "invalid transition step")
    _require(transition["state_before"] in STATES and transition["state_after"] in STATES, "invalid transition state")
    unsigned = {key: transition[key] for key in required if key != "event_sha256"}
    _require(transition["event_sha256"] == _digest(unsigned), "transition digest mismatch")


def run_protocol(config: ProtocolConfig = ProtocolConfig()) -> dict[str, Any]:
    """Run all fixture modes and return a digest-bound aggregate report."""

    _validate_config(config)
    shards = make_shards(config)
    results: dict[str, Any] = {}
    for mode in MODES:
        state = LearnerState()
        transitions: list[dict[str, Any]] = []
        for step, shard in enumerate(shards):
            receipt = make_receipt(shard) if mode in ("adaptive_gate", "adaptive_wave") else None
            result = process_shard(state, shard, receipt, make_shadow_evaluation(shard), step, mode, config)
            state = result.state
            transitions.extend(asdict(item) for item in result.transitions)
        rollback_state = state
        rollback_event: Transition | None = None
        if state.committed_shards:
            rollback_state, rollback_event = rollback(state, state.committed_shards[0], len(shards), config)
        results[mode] = {
            "committed_count": len(state.committed_shards),
            "quarantined_count": len(state.quarantined_shards),
            "primary_metric_heldout_gain": state.fast_value,
            "guard_mean_forgetting_cost": (
                sum(shard.forgetting_cost for shard in shards if shard.shard_id in state.committed_shards)
                / len(state.committed_shards)
                if state.committed_shards
                else 0.0
            ),
            "final_state": _state_dict(state),
            "transition_count": len(transitions),
            "transitions": transitions,
            "rollback_demo": {
                "before_version": state.version,
                "after_version": rollback_state.version,
                "rolled_back_shard": rollback_event.shard_id if rollback_event else None,
                "event": asdict(rollback_event) if rollback_event else None,
                "after_state": _state_dict(rollback_state),
            },
        }

    body = {
        "state_slice": STATE_SLICE,
        "schema_version": SCHEMA_VERSION,
        "receipt_boundary": RECEIPT_SOURCE,
        "config": asdict(config),
        "modes": list(MODES),
        "shard_ids": [shard.shard_id for shard in shards],
        "results": results,
        "claims": [
            "contract_mechanics_only",
            "no_model_loaded",
            "no_weights_updated",
            "no_zk_or_pqc_proof_generated",
            "no_astral_scientific_evidence",
        ],
    }
    return {**body, "result_sha256": _digest(body)}


def validate_result(result: Mapping[str, Any]) -> None:
    """Independently validate the aggregate report and transition digests."""

    _require(isinstance(result, Mapping), "result must be an object")
    _require(result.get("state_slice") == STATE_SLICE, "wrong state slice")
    _require(result.get("schema_version") == SCHEMA_VERSION, "wrong schema version")
    _require(result.get("receipt_boundary") == RECEIPT_SOURCE, "receipt boundary drift")
    _require(result.get("modes") == list(MODES), "mode panel drift")
    _require(result.get("claims") == [
        "contract_mechanics_only",
        "no_model_loaded",
        "no_weights_updated",
        "no_zk_or_pqc_proof_generated",
        "no_astral_scientific_evidence",
    ], "claim boundary drift")
    config_raw = result.get("config")
    _require(isinstance(config_raw, Mapping), "config must be an object")
    try:
        config = ProtocolConfig(**dict(config_raw))
    except (TypeError, ValueError) as exc:
        raise ProtocolError(f"invalid config: {exc}") from exc
    _validate_config(config)
    shard_ids = result.get("shard_ids")
    _require(isinstance(shard_ids, list) and len(shard_ids) == config.shard_count, "shard identity panel drift")
    _require(all(isinstance(shard_id, str) and shard_id for shard_id in shard_ids), "invalid shard identity")
    _require(len(set(shard_ids)) == len(shard_ids), "duplicate shard identity")
    results = result.get("results")
    _require(isinstance(results, Mapping), "results must be an object")
    for mode in MODES:
        summary = results.get(mode)
        _require(isinstance(summary, Mapping), f"missing mode result: {mode}")
        for field in ("committed_count", "quarantined_count", "transition_count", "final_state", "rollback_demo", "transitions"):
            _require(field in summary, f"missing result field: {mode}/{field}")
        _require(isinstance(summary["transitions"], list), f"transitions must be a list: {mode}")
        _require(summary["transition_count"] == len(summary["transitions"]), f"transition count mismatch: {mode}")
        for transition in summary["transitions"]:
            _validate_transition(transition)
        final_state = summary["final_state"]
        _require(isinstance(final_state, Mapping), f"final_state must be an object: {mode}")
        for field in (
            "version",
            "committed_shards",
            "quarantined_shards",
            "rolled_back_shards",
            "committed_effects",
            "fast_value",
            "slow_value",
        ):
            _require(field in final_state, f"final_state missing {field}: {mode}")
        _require(isinstance(final_state["version"], int) and not isinstance(final_state["version"], bool), f"invalid state version: {mode}")
        for field in ("committed_shards", "quarantined_shards", "rolled_back_shards", "committed_effects"):
            _require(isinstance(final_state[field], (list, tuple)), f"invalid state collection: {mode}/{field}")
        _finite(final_state["fast_value"], f"fast state: {mode}")
        _finite(final_state["slow_value"], f"slow state: {mode}")
        _require(final_state["version"] == summary["committed_count"] + summary["quarantined_count"], f"state version mismatch: {mode}")
        _require(len(final_state["committed_shards"]) == summary["committed_count"], f"committed count mismatch: {mode}")
        _require(len(final_state["quarantined_shards"]) == summary["quarantined_count"], f"quarantined count mismatch: {mode}")
        _finite(summary["primary_metric_heldout_gain"], f"primary metric: {mode}")
        _unit(summary["guard_mean_forgetting_cost"], f"forgetting guard: {mode}")
        rollback_demo = summary["rollback_demo"]
        _require(isinstance(rollback_demo, Mapping), f"rollback demo must be an object: {mode}")
        for field in ("before_version", "after_version", "rolled_back_shard", "event", "after_state"):
            _require(field in rollback_demo, f"rollback demo missing {field}: {mode}")
        if summary["committed_count"]:
            _require(rollback_demo["after_version"] == rollback_demo["before_version"] + 1, f"rollback version mismatch: {mode}")
            _require(isinstance(rollback_demo["after_state"], Mapping), f"rollback state must be an object: {mode}")
            _require(rollback_demo["rolled_back_shard"] not in rollback_demo["after_state"]["committed_shards"], f"rollback failed: {mode}")
    unsigned = {key: result[key] for key in result if key != "result_sha256"}
    _require(result.get("result_sha256") == _digest(unsigned), "result digest mismatch")


def markdown_report(result: Mapping[str, Any]) -> str:
    """Render a compact mechanics-only report."""

    lines = [
        "# Evidence-Conditioned Multiscale Plasticity v1",
        "",
        "Contract mechanics only: no model execution, weight update, ZK proof, or PQC proof.",
        "",
        f"Result SHA-256: `{result['result_sha256']}`",
        "",
        "| Mode | Committed | Quarantined | Held-out fixture gain | Mean forgetting guard |",
        "|---|---:|---:|---:|---:|",
    ]
    for mode in MODES:
        summary = result["results"][mode]
        lines.append(
            f"| `{mode}` | {summary['committed_count']} | {summary['quarantined_count']} | "
            f"{summary['primary_metric_heldout_gain']:.4f} | {summary['guard_mean_forgetting_cost']:.4f} |"
        )
    lines.extend(
        [
            "",
            "Claim ceiling: local control-plane mechanics only. This report is not neural-learning evidence, Astral evidence, ZK/PQC evidence, or production evidence.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()
    result = run_protocol()
    validate_result(result)
    if args.output is None:
        print(json.dumps(result, indent=2, sort_keys=True))
        return
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (args.output / "result.md").write_text(markdown_report(result), encoding="utf-8")
    print(json.dumps({"output": str(args.output), "result_sha256": result["result_sha256"]}, sort_keys=True))


if __name__ == "__main__":
    main()
