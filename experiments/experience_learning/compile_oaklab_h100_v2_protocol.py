#!/usr/bin/env python3
"""Compile the closed Oak Lab H100 V2 protocol packet.

State slice: oaklab-experience-learning-h100-replication-v2.
"""

from __future__ import annotations

import sys

# Direct file execution otherwise places this directory ahead of the stdlib,
# making the local ``types.py`` shadow ``types`` from Python's standard library.
if __package__ in {None, ""} and sys.path:
    sys.path.pop(0)

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


STATE_SLICE = "oaklab-experience-learning-h100-replication-v2"
SPEC_PATH = Path("experiments/experience_learning/oaklab_h100_v2_protocol.json")
PROTOCOL_PATH = Path("docs/research/experience-learning/43-oaklab-h100-replication-v2-protocol.md")
PACKET_PATH = Path("docs/research/experience-learning/44-oaklab-h100-replication-v2-review-packet.md")
OUTPUT_PATH = Path("experiments/experience_learning/oaklab_h100_v2_compiled_protocol.json")


def canonical(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def digest(value: dict[str, Any], field: str) -> str:
    return sha256_bytes(canonical({key: item for key, item in value.items() if key != field}))


def load_spec(repo_root: Path) -> dict[str, Any]:
    spec = json.loads((repo_root / SPEC_PATH).read_text(encoding="utf-8"))
    if spec.get("schema") != "oaklab-h100-replication-v2-protocol" or spec.get("state_slice") != STATE_SLICE:
        raise ValueError("protocol identity mismatch")
    if spec.get("execution", {}).get("effects_run") is not False:
        raise ValueError("effects must be disabled in the compiled packet")
    if spec.get("provider", {}).get("hard_usd_ceiling_required") is not True:
        raise ValueError("hard USD ceiling requirement is not sealed")
    return spec


def compile_protocol(repo_root: Path) -> dict[str, Any]:
    spec = load_spec(repo_root)
    body: dict[str, Any] = {
        "schema": "oaklab-h100-replication-v2-compiled",
        "state_slice": STATE_SLICE,
        "protocol_version": spec["protocol_version"],
        "source_protocol_sha256": sha256_file(repo_root / PROTOCOL_PATH),
        "review_packet_sha256": sha256_file(repo_root / PACKET_PATH),
        "agents_sha256": sha256_file(repo_root / "AGENTS.md"),
        "hash_prng_transcript": {
            "hash": "sha256",
            "counter_encoding": "uint64_le",
            "seed_encoding": "uint64_le",
            "draw_domain": "arm_assignment_then_bootstrap",
            "seed_roster": [1701, 1702, 1703, 1704, 1705, 1706, 1707, 1708],
            "draw_order": ["episode_id", "arm_assignment", "bootstrap_index"],
        },
        "controller_transition_table": [
            {"state": "START", "input": "episode_start", "next": "WASHOUT", "action": "reset_state", "pending": {"residual": None, "uncertainty": None, "resources": {}}},
            {"state": "WASHOUT", "input": "block_complete", "next": "READY", "action": "record_lagged_summary_only", "pending": {"residual": "previous_block_residual", "uncertainty": "previous_block_uncertainty", "resources": "previous_block_resources"}},
            {"state": "READY", "input": "block_start", "next": "UPDATE" , "action": "evaluate_fixed_threshold", "pending": {"threshold": 0.25, "current_outcome_access": False}},
            {"state": "UPDATE", "input": "utility_above_threshold", "next": "READY", "action": "update_affected_parameters", "pending": {"decision_block": "current", "source_block": "previous"}},
            {"state": "UPDATE", "input": "utility_below_threshold", "next": "READY", "action": "no_update", "pending": {"decision_block": "current", "source_block": "previous"}},
            {"state": "READY", "input": "horizon_complete", "next": "END", "action": "finalize_episode", "pending": {"terminal_credit": "post_washout_regret", "resource_counters": "complete"}},
        ],
        "generator_roster_and_draw_order": {
            "families": ["predictable_noise", "delayed_reward", "feature_relevance_drift", "event_sparsity", "noisy_mnist", "event_camera_or_sensor"],
            "fit_tune_assessment_order": ["fit", "tune", "assessment"],
            "draw_order": ["family", "cohort", "episode", "block", "item", "feature_noise", "target_noise", "event_time"],
            "sign_convention": {"prediction_error": "target_minus_prediction", "regret": "policy_minus_sgd_b1", "favorable_effect": "negative"},
        },
        "numeric_operations_and_byte_layouts": {
            "float": "float64_ieee754_le",
            "integer": "uint64_le",
            "probability": "propensity_num / propensity_den",
            "regret": "mean(post_washout_loss_policy - post_washout_loss_sgd_b1)",
            "bootstrap": "sha256(seed || uint64_le(replicate_index))",
            "record_layout": ["episode_id:u64", "block_id:u64", "arm:utf8_lenprefixed", "loss:f64", "updates:u64", "ops:u64", "storage_bytes:u64"],
            "absent": "length_zero_for_optional_utf8_only",
        },
        "ablation_and_multiplicity_tables": {
            "ablations": ["sgd_b1", "lagged_selective_credit", "lagged_selective_credit_no_uncertainty", "lagged_selective_credit_no_lag"],
            "family_order": ["quality", "adaptation", "operations", "storage", "energy"],
            "correction": "holm",
            "alpha": 0.05,
        },
        "segment_bounded_adaptation_metrics": {
            "shift_segments": "predeclared_stream_segments_only",
            "scan_start": "first_post_shift_item",
            "scan_domain": "integer_item_index",
            "scan_increment": 1,
            "success": "first_index_with_loss_at_or_below_pre_shift_reference_for_8_consecutive_items",
            "censoring": "right_censored_at_segment_end",
            "missingness": "missing_segment_is_invalid_not_zero",
        },
        "canonical_lock_counter_control_absence_schemas": {
            "lock": {"encoding": "canonical_json_utf8", "field_order": "lexicographic", "digest": "sha256", "immutable": True},
            "counter": {"scope": "per_episode", "fields": ["updates", "active_synapses", "events", "storage_bytes", "wall_clock_ns"], "all_required": True},
            "control": {"required": ["noise_floor", "oracle_feature", "untouched_sgd_b1", "deterministic_repeat"], "missing": "explicit_status_only"},
            "assessment_absence": {"effects_run": False, "provider_contacted": False, "model_loaded": False, "result_written": False},
        },
        "provider_receipt_schema": {
            "required": ["allocation_id", "node_id", "start_utc", "stop_utc", "quoted_gpu_usd_per_minute", "charged_usd", "stop_reason", "raw_trace_sha256", "launch_manifest_sha256"],
            "currency": "USD",
            "charged_must_not_exceed_hard_ceiling": True,
        },
        "result_root_schema": {
            "mode": "closed_world",
            "allowed_paths": ["campaign_manifest.json", "provider/allocation.json", "provider/cost.json", "provider/stop.json", "energy/raw_trace.csv", "energy/joules.json", "result/aggregate.json", "validation/independent.json"],
            "reject_symlinks": True,
            "reject_unlisted_paths": True,
        },
        "compiled_sha256": "",
    }
    body["compiled_sha256"] = digest(body, "compiled_sha256")
    return body


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH)
    args = parser.parse_args()
    value = compile_protocol(args.repo_root)
    output = args.output if args.output.is_absolute() else args.repo_root / args.output
    output.write_bytes(canonical(value))
    print(json.dumps({"state_slice": STATE_SLICE, "compiled_sha256": value["compiled_sha256"], "output": str(output)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
