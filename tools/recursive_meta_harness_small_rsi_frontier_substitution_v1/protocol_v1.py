"""Frozen pure-data contract for small-model RSI substitution.

State slice: ``recursive-meta-harness-small-rsi-frontier-substitution-v1``.

This module contains no model, provider, network, subprocess, or filesystem
execution.  The fixture runner is deliberately separate and is not evidence
of model performance.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from typing import Any, Mapping, Sequence


STATE_SLICE = "recursive-meta-harness-small-rsi-frontier-substitution-v1"
PROTOCOL_ID = "small-rsi-frontier-substitution-v1"
PROTOCOL_SCHEMA_VERSION = "recursive-meta-harness-small-rsi-frontier-substitution-protocol-v1"
MANIFEST_SCHEMA_VERSION = "recursive-meta-harness-small-rsi-frontier-substitution-manifest-v1"
FIXTURE_SCHEMA_VERSION = "recursive-meta-harness-small-rsi-frontier-substitution-fixture-v1"
CLAIM_CEILING = "LocalDevelopmentSmallRSIFrontierSubstitutionProtocol"
FIXTURE_CLAIM_CEILING = "LocalDevelopmentSmallRSIFrontierSubstitutionContractFixture"

ARM_IDS = (
    "frontier_single",
    "small_single",
    "small_swarm_fixed",
    "small_swarm_rsi",
)
TASK_FAMILIES = (
    "repository_coding",
    "structured_reconciliation",
    "research_synthesis",
    "long_horizon_recovery",
)
SPLITS = ("fit", "tune", "assessment")
COST_COMPONENTS = (
    "uncached_model_micros",
    "cached_model_micros",
    "reasoning_micros",
    "router_micros",
    "verifier_micros",
    "retry_micros",
    "compaction_micros",
    "memory_micros",
    "tool_api_micros",
    "compute_micros",
    "storage_micros",
    "cleanup_micros",
    "human_review_micros",
)
CONSTRAINTS = (
    "safety",
    "integrity",
    "authority",
    "leakage",
    "audit_completeness",
)
HEX_DIGEST = re.compile(r"^[0-9a-f]{64}$")


class ProtocolError(ValueError):
    """Raised when a contract or observation is invalid."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ProtocolError(message)


def canonical_bytes(value: Any) -> bytes:
    """Return the only byte representation permitted for contract hashing."""

    try:
        encoded = json.dumps(
            value,
            allow_nan=False,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
        )
    except (TypeError, ValueError) as exc:
        raise ProtocolError("value is not canonically serializable") from exc
    return encoded.encode("utf-8")


def digest(value: Any) -> str:
    """Hash canonical JSON with SHA-256."""

    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def _strict_keys(value: Mapping[str, Any], expected: Sequence[str], label: str) -> None:
    _require(set(value) == set(expected), f"{label} schema")


def _is_digest(value: Any) -> bool:
    return isinstance(value, str) and bool(HEX_DIGEST.fullmatch(value))


def protocol_spec() -> dict[str, Any]:
    """Return a fresh copy of the frozen protocol specification."""

    return {
        "identity": {
            "state_slice": STATE_SLICE,
            "protocol_id": PROTOCOL_ID,
            "schema_version": PROTOCOL_SCHEMA_VERSION,
            "claim_ceiling": CLAIM_CEILING,
            "execution_authorized": False,
            "assessment_open": False,
        },
        "question": {
            "primary": "Can a small-model swarm with bounded RSI substitute for a frontier single-agent system on a declared task distribution?",
            "primary_candidate_arm": "small_swarm_rsi",
            "primary_baseline_arm": "frontier_single",
            "claim_scope": "conditional task-distribution substitution only",
            "excluded_claims": [
                "general frontier parity",
                "recursive model-weight self-improvement",
                "equal performance at equal cost, latency, robustness, and broad capability",
                "production readiness",
                "SOTA or breakthrough status",
            ],
        },
        "arms": [
            {
                "arm_id": "frontier_single",
                "model_lane": "frontier_single_lane",
                "orchestrator": "single_agent",
                "memory_policy": "declared_native_memory",
                "tool_policy": "declared_common_tools",
                "verifier_policy": "independent_terminal_grader",
                "rsi_policy": "none",
            },
            {
                "arm_id": "small_single",
                "model_lane": "small_single_lane",
                "orchestrator": "single_agent",
                "memory_policy": "declared_native_memory",
                "tool_policy": "declared_common_tools",
                "verifier_policy": "independent_terminal_grader",
                "rsi_policy": "none",
            },
            {
                "arm_id": "small_swarm_fixed",
                "model_lane": "small_swarm_lane",
                "orchestrator": "fixed_swarm",
                "memory_policy": "declared_shared_memory",
                "tool_policy": "declared_common_tools",
                "verifier_policy": "independent_terminal_grader",
                "rsi_policy": "frozen_prompt_and_routing_policy",
            },
            {
                "arm_id": "small_swarm_rsi",
                "model_lane": "small_swarm_lane",
                "orchestrator": "bounded_recursive_swarm",
                "memory_policy": "declared_shared_memory",
                "tool_policy": "declared_common_tools",
                "verifier_policy": "independent_terminal_grader",
                "rsi_policy": "development_only_bounded_policy_update",
            },
        ],
        "regimes": [
            {
                "regime_id": "system_substitution",
                "primary": True,
                "purpose": "Compare complete declared systems under a matched external task and full-cost envelope.",
                "same_fields": ["task_digest", "tool_authority_digest", "budget_digest", "grader_digest"],
            },
            {
                "regime_id": "component_ablation",
                "primary": False,
                "purpose": "Estimate whether swarm coordination and bounded RSI add utility within the small-model lane.",
                "same_fields": ["model_lane", "task_digest", "tool_authority_digest", "budget_digest", "grader_digest"],
            },
        ],
        "task_plan": {
            "families": list(TASK_FAMILIES),
            "splits": {
                "fit": {"tasks_per_family": 2, "purpose": "candidate development only"},
                "tune": {"tasks_per_family": 2, "purpose": "lock thresholds and configuration only"},
                "assessment": {"tasks_per_family": 2, "purpose": "sealed confirmation only"},
            },
            "replicates": 3,
            "order_seeds": [11031, 11032, 11033],
            "disjoint_by": ["author_id", "template_lineage", "task_digest"],
            "assessment_access": "sealed_until_prediction_lock_and_independent_review",
            "minimum_task_families_for_claim": 3,
        },
        "metric": {
            "unit": "task",
            "objective_scale": "integer_micro_utility_0_to_1000000",
            "verified_utility": "objective_score if every hard constraint passes and status is completed, otherwise zero",
            "primary_estimand": "paired_verified_utility_small_swarm_rsi_minus_frontier_single",
            "non_inferiority_margin_micros": -20000,
            "minimum_full_cost_reduction_fraction_bps": 2000,
            "reliability_rule": "pass_all_k_not_pass_at_k",
            "zero_utility_rules": [
                "safety_failure",
                "integrity_failure",
                "authority_failure",
                "leakage_failure",
                "audit_incompleteness",
                "timeout_or_infrastructure_failure",
                "unverified_terminal_state",
            ],
        },
        "cost": {
            "currency": "USD_micros",
            "component_fields": list(COST_COMPONENTS),
            "missing_component_policy": "reject_not_zero",
            "per_task_ceiling_micros": 200000,
            "includes": [
                "uncached_and_cached_model_calls",
                "reasoning_tokens",
                "router_and_verifier_calls",
                "retries_and_compaction",
                "memory_ingestion_retrieval_storage_and_deletion",
                "tools_and_external_apis",
                "local_compute_and_energy",
                "cleanup",
                "human_review",
            ],
            "price_snapshot_policy": "immutable_and_digest_bound_before_execution",
        },
        "rsi_contract": {
            "mutable_development_fields": ["prompt_template", "plan_template", "routing_policy", "verifier_escalation_policy"],
            "immutable_fields": [
                "task_contracts",
                "assessment_membership",
                "grader_and_oracle",
                "hard_constraints",
                "thresholds",
                "pricing_snapshot",
                "authority_policy",
                "stop_rules",
                "claim_ceiling",
            ],
            "forbidden_effects": ["base_weight_update", "adapter_merge", "grader_mutation", "assessment_read", "authority_grant", "provider_purchase"],
            "rollback": "candidate_bundle_digest_and_parent_digest_required",
            "independence": "descendants_with_shared_history_are_not_independent_replicates",
        },
        "hard_constraints": list(CONSTRAINTS),
        "execution_boundary": {
            "model_execution_allowed": False,
            "provider_calls_allowed": False,
            "network_during_execution_allowed": False,
            "accepted_evidence_writes_allowed": False,
            "requires_before_any_model_run": [
                "fresh_protocol_review",
                "packet_bound_independent_signed_accept",
                "exact_model_runtime_and_task_identity",
                "positive_user_authorized_hard_usd_ceiling",
                "external_0700_custody_root",
            ],
        },
        "stop_rules": [
            "any_digest_or_custody_mismatch",
            "any_missing_cost_component",
            "any hard-constraint failure in a claimed comparison",
            "any assessment access before lock and independent review",
            "any failed independent validation",
            "any failed primary gate",
        ],
    }


def validate_cost(cost: Mapping[str, Any]) -> int:
    """Validate fixed-point full-cost components and return their sum."""

    _strict_keys(cost, COST_COMPONENTS, "cost")
    total = 0
    for component in COST_COMPONENTS:
        value = cost[component]
        _require(isinstance(value, int) and not isinstance(value, bool), f"cost component {component}")
        _require(value >= 0, f"cost component {component} negative")
        total += value
    _require(total <= 200000, "per-task cost ceiling")
    return total


def validate_observation(observation: Mapping[str, Any]) -> dict[str, Any]:
    """Validate one fixture observation and calculate verified utility."""

    expected = (
        "state_slice",
        "protocol_id",
        "task_id",
        "family_id",
        "split",
        "replicate",
        "arm_id",
        "status",
        "objective_score_micros",
        "constraint_results",
        "cost",
        "latency_ms",
        "trace_digest",
    )
    _strict_keys(observation, expected, "observation")
    _require(observation["state_slice"] == STATE_SLICE, "observation state slice")
    _require(observation["protocol_id"] == PROTOCOL_ID, "observation protocol")
    _require(isinstance(observation["task_id"], str) and observation["task_id"], "task id")
    _require(observation["family_id"] in TASK_FAMILIES, "task family")
    _require(observation["split"] in ("fit", "tune"), "assessment is sealed")
    _require(isinstance(observation["replicate"], int) and observation["replicate"] in range(3), "replicate")
    _require(observation["arm_id"] in ARM_IDS, "arm")
    _require(observation["status"] in ("completed", "timeout", "infrastructure_failure", "refused"), "status")
    score = observation["objective_score_micros"]
    _require(isinstance(score, int) and not isinstance(score, bool) and 0 <= score <= 1000000, "objective score")
    constraints = observation["constraint_results"]
    _strict_keys(constraints, CONSTRAINTS, "constraint results")
    _require(all(isinstance(value, bool) for value in constraints.values()), "constraint result types")
    total_cost = validate_cost(observation["cost"])
    _require(isinstance(observation["latency_ms"], int) and observation["latency_ms"] >= 0, "latency")
    _require(_is_digest(observation["trace_digest"]), "trace digest")
    hard_pass = all(constraints.values())
    verified = score if observation["status"] == "completed" and hard_pass else 0
    failures = sorted(name for name, passed in constraints.items() if not passed)
    if observation["status"] != "completed":
        failures.append(observation["status"])
    return {
        "task_id": observation["task_id"],
        "family_id": observation["family_id"],
        "split": observation["split"],
        "replicate": observation["replicate"],
        "arm_id": observation["arm_id"],
        "full_cost_micros": total_cost,
        "verified_utility_micros": verified,
        "constraint_failures": failures,
    }


def summarize(evaluated: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Aggregate fixture observations without creating a comparison claim."""

    _require(bool(evaluated), "empty evaluated observations")
    arms: dict[str, dict[str, Any]] = {}
    for arm_id in ARM_IDS:
        rows = [row for row in evaluated if row["arm_id"] == arm_id]
        _require(rows, f"missing arm {arm_id}")
        total_cost = sum(int(row["full_cost_micros"]) for row in rows)
        total_utility = sum(int(row["verified_utility_micros"]) for row in rows)
        arms[arm_id] = {
            "observation_count": len(rows),
            "total_full_cost_micros": total_cost,
            "total_verified_utility_micros": total_utility,
            "mean_verified_utility_micros": total_utility // len(rows),
            "constraint_failure_count": sum(bool(row["constraint_failures"]) for row in rows),
            "cost_per_verified_utility_micros": None if total_utility == 0 else (total_cost * 1000000) // total_utility,
        }
    return {"arms": arms, "assessment_comparison": "sealed_not_computed"}


def validate_numeric_finiteness(value: Any) -> None:
    """Reject non-finite numeric values before any future statistical use."""

    if isinstance(value, float):
        _require(math.isfinite(value), "non-finite numeric value")
    elif isinstance(value, Mapping):
        for nested in value.values():
            validate_numeric_finiteness(nested)
    elif isinstance(value, (list, tuple)):
        for nested in value:
            validate_numeric_finiteness(nested)

