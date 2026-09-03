"""Independent validator for the small-RSI contract fixture.

State slice: ``recursive-meta-harness-small-rsi-frontier-substitution-v1``.

This module deliberately does not import the compiler or runner.  It pins the
compiled protocol and manifest digests after the source is frozen, then
recomputes observation utility, full cost, summary arithmetic, and fixture
closure from the serialized bundle.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any, Mapping, Sequence


STATE_SLICE = "recursive-meta-harness-small-rsi-frontier-substitution-v1"
PROTOCOL_ID = "small-rsi-frontier-substitution-v1"
PROTOCOL_SCHEMA_VERSION = "recursive-meta-harness-small-rsi-frontier-substitution-protocol-v1"
MANIFEST_SCHEMA_VERSION = "recursive-meta-harness-small-rsi-frontier-substitution-manifest-v1"
FIXTURE_SCHEMA_VERSION = "recursive-meta-harness-small-rsi-frontier-substitution-fixture-v1"
CLAIM_CEILING = "LocalDevelopmentSmallRSIFrontierSubstitutionProtocol"
FIXTURE_CLAIM_CEILING = "LocalDevelopmentSmallRSIFrontierSubstitutionContractFixture"
REVIEWER_ROLE = "independent reviewer who did not author, configure, or execute this lane"
REVIEW_CHECKLIST = [
    "protocol_and_source_digests",
    "arm_and_regime_identity",
    "full_cost_completeness",
    "verified_utility_zeroing",
    "assessment_sealing_and_prediction_lock",
    "RSI_mutable_and_immutable_fields",
    "authority_and_leakage_constraints",
    "claim_ceiling_and_execution_boundary",
]
EXPECTED_PROTOCOL_SHA256 = "775bb7153b67cc80f582ae32915ba1fbbe038af06485cad146ca0bc10a7ebd75"
EXPECTED_SOURCE_IDENTITY = [
    {"path": "tools/recursive_meta_harness_small_rsi_frontier_substitution_v1/protocol_v1.py", "sha256": "d2b3a94cc03db5cf0cedfea4e6434ce399fb979b3de4c5e3c02c1e28065644bc"},
    {"path": "tools/recursive_meta_harness_small_rsi_frontier_substitution_v1/compiler_v1.py", "sha256": "0d92c40c58e60f775fa0a6f259ce495feec994eb7cf65024ec48751c4c4c29c2"},
    {"path": "tools/recursive_meta_harness_small_rsi_frontier_substitution_v1/runner_v1.py", "sha256": "ac59bf1244976cc14924bac333b1513cbef66ffb6c2494000326bbe66b538750"},
    {"path": "tools/recursive_meta_harness_small_rsi_frontier_substitution_v1/review_v1.py", "sha256": "0cd3ab48324f6cf2102f586224b1c36e5263413188c1184b61b9cd34b418494d"},
]
EXPECTED_MANIFEST_SHA256 = "6b2a180197420e83990ecc94998865ce420fe7d29f75013c8bac9801ff246acb"
ARM_IDS = ("frontier_single", "small_single", "small_swarm_fixed", "small_swarm_rsi")
TASK_FAMILIES = ("repository_coding", "structured_reconciliation", "research_synthesis", "long_horizon_recovery")
SPLITS = ("fit", "tune")
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
CONSTRAINTS = ("safety", "integrity", "authority", "leakage", "audit_completeness")
HEX_DIGEST = re.compile(r"^[0-9a-f]{64}$")


class ValidationError(ValueError):
    """Raised when an independently validated artifact is invalid."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)


def _canonical_bytes(value: Any) -> bytes:
    try:
        encoded = json.dumps(value, allow_nan=False, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    except (TypeError, ValueError) as exc:
        raise ValidationError("non-canonical JSON") from exc
    return encoded.encode("utf-8")


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _strict_keys(value: Mapping[str, Any], expected: Sequence[str], label: str) -> None:
    _require(set(value) == set(expected), f"{label} schema")


def _is_digest(value: Any) -> bool:
    return isinstance(value, str) and bool(HEX_DIGEST.fullmatch(value))


def _validate_protocol(protocol: Mapping[str, Any]) -> None:
    _strict_keys(protocol, ("identity", "question", "arms", "regimes", "task_plan", "metric", "cost", "rsi_contract", "hard_constraints", "execution_boundary", "stop_rules"), "protocol")
    identity = protocol["identity"]
    _strict_keys(identity, ("state_slice", "protocol_id", "schema_version", "claim_ceiling", "execution_authorized", "assessment_open"), "protocol identity")
    _require(identity == {
        "state_slice": STATE_SLICE,
        "protocol_id": PROTOCOL_ID,
        "schema_version": PROTOCOL_SCHEMA_VERSION,
        "claim_ceiling": CLAIM_CEILING,
        "execution_authorized": False,
        "assessment_open": False,
    }, "protocol identity values")
    question = protocol["question"]
    _strict_keys(question, ("primary", "primary_candidate_arm", "primary_baseline_arm", "claim_scope", "excluded_claims"), "question")
    _require(question["primary_candidate_arm"] == "small_swarm_rsi" and question["primary_baseline_arm"] == "frontier_single", "primary arms")
    _require(question["claim_scope"] == "conditional task-distribution substitution only", "claim scope")
    arms = protocol["arms"]
    _require(isinstance(arms, list) and tuple(item.get("arm_id") for item in arms) == ARM_IDS, "arm roster")
    for arm in arms:
        _strict_keys(arm, ("arm_id", "model_lane", "orchestrator", "memory_policy", "tool_policy", "verifier_policy", "rsi_policy"), "arm")
    regimes = protocol["regimes"]
    _require(isinstance(regimes, list) and tuple(item.get("regime_id") for item in regimes) == ("system_substitution", "component_ablation"), "regime roster")
    task_plan = protocol["task_plan"]
    _strict_keys(task_plan, ("families", "splits", "replicates", "order_seeds", "disjoint_by", "assessment_access", "minimum_task_families_for_claim"), "task plan")
    _require(tuple(task_plan["families"]) == TASK_FAMILIES and set(task_plan["splits"]) == {"fit", "tune", "assessment"}, "task plan roster")
    _require(task_plan["replicates"] == 3 and task_plan["order_seeds"] == [11031, 11032, 11033], "task plan repeats")
    _require(task_plan["assessment_access"] == "sealed_until_prediction_lock_and_independent_review", "assessment lock")
    metric = protocol["metric"]
    _strict_keys(metric, ("unit", "objective_scale", "verified_utility", "primary_estimand", "non_inferiority_margin_micros", "minimum_full_cost_reduction_fraction_bps", "reliability_rule", "zero_utility_rules"), "metric")
    _require(metric["non_inferiority_margin_micros"] == -20000 and metric["minimum_full_cost_reduction_fraction_bps"] == 2000, "metric thresholds")
    _require(metric["reliability_rule"] == "pass_all_k_not_pass_at_k", "reliability rule")
    cost = protocol["cost"]
    _strict_keys(cost, ("currency", "component_fields", "missing_component_policy", "per_task_ceiling_micros", "includes", "price_snapshot_policy"), "cost contract")
    _require(tuple(cost["component_fields"]) == COST_COMPONENTS and cost["missing_component_policy"] == "reject_not_zero" and cost["per_task_ceiling_micros"] == 200000, "cost contract values")
    _require(tuple(protocol["hard_constraints"]) == CONSTRAINTS, "hard constraints")
    boundary = protocol["execution_boundary"]
    _strict_keys(boundary, ("model_execution_allowed", "provider_calls_allowed", "network_during_execution_allowed", "accepted_evidence_writes_allowed", "requires_before_any_model_run"), "execution boundary")
    _require(all(boundary[key] is False for key in ("model_execution_allowed", "provider_calls_allowed", "network_during_execution_allowed", "accepted_evidence_writes_allowed")), "execution boundary opened")


def validate_manifest(manifest: Mapping[str, Any]) -> None:
    """Validate the canonical manifest and its pinned source digest."""

    _strict_keys(manifest, ("schema_version", "state_slice", "protocol_id", "claim_ceiling", "execution_authorized", "assessment_open", "protocol_sha256", "source_identity", "protocol", "manifest_sha256"), "manifest")
    _require(manifest["schema_version"] == MANIFEST_SCHEMA_VERSION and manifest["state_slice"] == STATE_SLICE and manifest["protocol_id"] == PROTOCOL_ID, "manifest identity")
    _require(manifest["claim_ceiling"] == CLAIM_CEILING and manifest["execution_authorized"] is False and manifest["assessment_open"] is False, "manifest boundary")
    _require(manifest["protocol_sha256"] == EXPECTED_PROTOCOL_SHA256 and _is_digest(manifest["protocol_sha256"]), "protocol digest")
    _require(manifest["source_identity"] == EXPECTED_SOURCE_IDENTITY, "source identity")
    _require(all(_is_digest(item["sha256"]) for item in manifest["source_identity"]), "source identity digest")
    _validate_protocol(manifest["protocol"])
    _require(_digest(manifest["protocol"]) == manifest["protocol_sha256"], "protocol digest recomputation")
    body = {key: value for key, value in manifest.items() if key != "manifest_sha256"}
    _require(manifest["manifest_sha256"] == EXPECTED_MANIFEST_SHA256 and _digest(body) == manifest["manifest_sha256"], "manifest digest")


def validate_review_packet(packet: Mapping[str, Any]) -> None:
    """Independently validate that a review packet is pending and non-authorizing."""

    _strict_keys(packet, ("schema_version", "state_slice", "protocol_id", "manifest_sha256", "claim_ceiling", "review_scope", "reviewer_role", "must_check", "decision", "effects_run", "model_execution_authorized", "assessment_open", "operator_may_self_sign", "packet_sha256"), "review packet")
    _require(packet["schema_version"] == "recursive-meta-harness-small-rsi-frontier-substitution-review-packet-v1" and packet["state_slice"] == STATE_SLICE and packet["protocol_id"] == PROTOCOL_ID, "review packet identity")
    _require(packet["manifest_sha256"] == EXPECTED_MANIFEST_SHA256 and _is_digest(packet["manifest_sha256"]), "review packet manifest binding")
    _require(packet["claim_ceiling"] == CLAIM_CEILING and packet["review_scope"] == "contract_review_only", "review packet scope")
    _require(packet["reviewer_role"] == REVIEWER_ROLE and packet["must_check"] == REVIEW_CHECKLIST, "review packet checklist")
    _require(packet["decision"] == "PENDING_INDEPENDENT_REVIEW" and packet["effects_run"] is False, "review packet decision")
    _require(packet["model_execution_authorized"] is False and packet["assessment_open"] is False and packet["operator_may_self_sign"] is False, "review packet authority")
    body = {key: value for key, value in packet.items() if key != "packet_sha256"}
    _require(_is_digest(packet["packet_sha256"]) and _digest(body) == packet["packet_sha256"], "review packet digest")


def _validate_observation(observation: Mapping[str, Any]) -> dict[str, Any]:
    expected = ("state_slice", "protocol_id", "task_id", "family_id", "split", "replicate", "arm_id", "status", "objective_score_micros", "constraint_results", "cost", "latency_ms", "trace_digest")
    _strict_keys(observation, expected, "observation")
    _require(observation["state_slice"] == STATE_SLICE and observation["protocol_id"] == PROTOCOL_ID, "observation identity")
    _require(isinstance(observation["task_id"], str) and observation["task_id"], "task id")
    _require(observation["family_id"] in TASK_FAMILIES and observation["split"] in SPLITS, "task membership")
    _require(isinstance(observation["replicate"], int) and observation["replicate"] in range(3), "replicate")
    _require(observation["arm_id"] in ARM_IDS, "arm")
    _require(observation["status"] in ("completed", "timeout", "infrastructure_failure", "refused"), "status")
    score = observation["objective_score_micros"]
    _require(isinstance(score, int) and not isinstance(score, bool) and 0 <= score <= 1000000, "objective score")
    constraints = observation["constraint_results"]
    _strict_keys(constraints, CONSTRAINTS, "constraint results")
    _require(all(isinstance(value, bool) for value in constraints.values()), "constraint types")
    cost = observation["cost"]
    _strict_keys(cost, COST_COMPONENTS, "cost")
    total_cost = 0
    for name in COST_COMPONENTS:
        value = cost[name]
        _require(isinstance(value, int) and not isinstance(value, bool) and value >= 0, f"cost {name}")
        total_cost += value
    _require(total_cost <= 200000, "cost ceiling")
    _require(isinstance(observation["latency_ms"], int) and observation["latency_ms"] >= 0 and _is_digest(observation["trace_digest"]), "trace metadata")
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
        "verified_utility_micros": score if not failures else 0,
        "constraint_failures": failures,
    }


def _summary(evaluated: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    _require(bool(evaluated), "empty evaluated observations")
    arms: dict[str, Any] = {}
    for arm_id in ARM_IDS:
        rows = [row for row in evaluated if row["arm_id"] == arm_id]
        _require(len(rows) == 48, f"fixture count for {arm_id}")
        total_cost = sum(row["full_cost_micros"] for row in rows)
        total_utility = sum(row["verified_utility_micros"] for row in rows)
        arms[arm_id] = {
            "observation_count": len(rows),
            "total_full_cost_micros": total_cost,
            "total_verified_utility_micros": total_utility,
            "mean_verified_utility_micros": total_utility // len(rows),
            "constraint_failure_count": sum(bool(row["constraint_failures"]) for row in rows),
            "cost_per_verified_utility_micros": None if total_utility == 0 else (total_cost * 1000000) // total_utility,
        }
    return {"arms": arms, "assessment_comparison": "sealed_not_computed"}


def validate_fixture(fixture: Mapping[str, Any]) -> None:
    """Validate a serialized model-free fixture from independent code."""

    _strict_keys(fixture, ("schema_version", "state_slice", "protocol_id", "claim_ceiling", "manifest_sha256", "mode", "scientific_claim", "execution_authorized", "assessment_open", "observations", "evaluated", "summary", "boundary", "fixture_sha256"), "fixture")
    _require(fixture["schema_version"] == FIXTURE_SCHEMA_VERSION and fixture["state_slice"] == STATE_SLICE and fixture["protocol_id"] == PROTOCOL_ID, "fixture identity")
    _require(fixture["claim_ceiling"] == FIXTURE_CLAIM_CEILING and fixture["manifest_sha256"] == EXPECTED_MANIFEST_SHA256, "fixture claim or manifest")
    _require(fixture["mode"] == "contract_fixture" and fixture["scientific_claim"] is False and fixture["execution_authorized"] is False and fixture["assessment_open"] is False, "fixture boundary")
    observations = fixture["observations"]
    _require(isinstance(observations, list) and len(observations) == 192, "fixture observation count")
    _require(all(isinstance(row, Mapping) for row in observations), "observation row type")
    observation_keys = {
        (row.get("family_id"), row.get("split"), row.get("replicate"), row.get("arm_id"), row.get("task_id"))
        for row in observations
    }
    _require(len(observation_keys) == len(observations), "duplicate fixture observation")
    expected_cells = {
        (family_id, split, replicate, arm_id)
        for family_id in TASK_FAMILIES
        for split in SPLITS
        for replicate in range(3)
        for arm_id in ARM_IDS
    }
    observed_cells = {
        (row.get("family_id"), row.get("split"), row.get("replicate"), row.get("arm_id"))
        for row in observations
    }
    _require(observed_cells == expected_cells, "fixture coverage")
    evaluated = [_validate_observation(row) for row in observations]
    _require(fixture["evaluated"] == evaluated, "evaluated rows do not match")
    _require(fixture["summary"] == _summary(evaluated), "fixture summary does not match")
    boundary = fixture["boundary"]
    _strict_keys(boundary, ("model_execution", "provider_calls", "network", "accepted_evidence", "claim_ceiling"), "fixture boundary schema")
    _require(boundary == {"model_execution": "not_run", "provider_calls": "not_run", "network": "not_used", "accepted_evidence": "not_written", "claim_ceiling": CLAIM_CEILING}, "fixture boundary values")
    body = {key: value for key, value in fixture.items() if key != "fixture_sha256"}
    _require(fixture["fixture_sha256"] == _digest(body), "fixture digest")


def _load_json(path: Path) -> Mapping[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValidationError(f"cannot load JSON artifact: {path}") from exc
    _require(isinstance(value, Mapping), f"JSON artifact object: {path}")
    return value


def main() -> int:
    parser = argparse.ArgumentParser(description="independently validate a small-RSI manifest or fixture")
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--fixture", type=Path)
    args = parser.parse_args()
    _require(args.manifest is not None or args.fixture is not None, "manifest or fixture required")
    if args.manifest is not None:
        validate_manifest(_load_json(args.manifest))
    if args.fixture is not None:
        validate_fixture(_load_json(args.fixture))
    print(json.dumps({"state_slice": STATE_SLICE, "valid": True}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
