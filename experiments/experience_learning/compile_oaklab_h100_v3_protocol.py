#!/usr/bin/env python3
"""Compile the Oak Lab H100 V3 closed-world protocol.

State slice: oaklab-experience-learning-h100-replication-v3.
"""

from __future__ import annotations

import sys

if __package__ in {None, ""} and sys.path:
    sys.path.pop(0)

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


STATE_SLICE = "oaklab-experience-learning-h100-replication-v3"
SPEC_PATH = Path("experiments/experience_learning/oaklab_h100_v3_protocol.json")
PROTOCOL_PATH = Path("docs/research/experience-learning/48-oaklab-h100-replication-v3-protocol.md")
PACKET_PATH = Path("docs/research/experience-learning/49-oaklab-h100-replication-v3-review-packet.md")
OUTPUT_PATH = Path("experiments/experience_learning/oaklab_h100_v3_compiled_protocol.json")
FREEZE_FILES = (
    str(PROTOCOL_PATH), str(PACKET_PATH), str(SPEC_PATH),
    "experiments/experience_learning/compile_oaklab_h100_v3_protocol.py",
    "experiments/experience_learning/validate_oaklab_h100_v3_protocol.py",
    "experiments/experience_learning/tests/test_oaklab_h100_v3_protocol.py",
    "AGENTS.md",
)


def canonical(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def digest(value: dict[str, Any], field: str) -> str:
    return sha256_bytes(canonical({key: item for key, item in value.items() if key != field}))


def compile_protocol(repo_root: Path) -> dict[str, Any]:
    spec = json.loads((repo_root / SPEC_PATH).read_text(encoding="utf-8"))
    if spec.get("schema") != "oaklab-h100-replication-v3-protocol" or spec.get("state_slice") != STATE_SLICE:
        raise ValueError("protocol identity mismatch")
    if spec.get("execution", {}).get("effects_run") is not False:
        raise ValueError("effects must be disabled")
    if spec.get("provider", {}).get("hard_usd_ceiling_required") is not True:
        raise ValueError("hard USD ceiling requirement missing")
    freeze = {path: sha256_file(repo_root / path) for path in FREEZE_FILES}
    body: dict[str, Any] = {
        "schema": "oaklab-h100-replication-v3-compiled",
        "state_slice": STATE_SLICE,
        "protocol_version": spec["protocol_version"],
        "freeze_file_sha256": freeze,
        "hash_prng": {"algorithm": "sha256-counter", "counter_encoding": "uint64_le", "seed_encoding": "uint64_le", "draw_order": ["episode_id", "arm_order", "bootstrap_index"], "seed_roster": [2301, 2302, 2303, 2304, 2305, 2306, 2307, 2308]},
        "paired_trajectory_estimand": {"unit": "episode", "control": "sgd_b1", "treatment": "lagged_selective_credit", "same_stream": True, "same_initial_checkpoint": True, "post_washout_blocks": 32, "items_per_block": 128, "formula": "mean_e mean_b(loss_treatment[e,b]-loss_control[e,b])", "arm_order_randomized": True},
        "controller": {"name": "lagged_selective_credit", "decision_inputs": ["previous_block_residual", "previous_block_uncertainty", "previous_block_resource_counters"], "current_block_outcome_access": False, "threshold": 0.25, "replay": False, "reshuffle": False, "state_reset": "episode_boundary"},
        "stream_roster": {"synthetic": ["predictable_noise", "delayed_reward", "feature_relevance_drift", "event_sparsity"], "real": ["noisy_mnist", "event_camera_or_sensor"], "split": "fit_tune_assessment_disjoint"},
        "statistics": {"test": "paired_sha256_counter_randomization", "multiplicity": "holm", "alpha": 0.05, "planned_power": 0.8, "minimum_effect": 0.05, "bootstrap_resamples": 10000, "favorable_direction": "negative"},
        "resource_energy": {"noninferiority_margin": 0.05, "metrics": ["active_operations", "parameter_updates", "storage_bytes", "wall_clock_latency", "joules_per_learned_event"], "joules": {"samples": "finite_nonnegative_watts_at_monotone_utc_ns", "integral": "sum(0.5*(w_i+w_i+1)*(t_i+1-t_i))", "denominator": "successfully_learned_events"}},
        "campaign_manifest": {"schema": "oaklab-h100-v3-campaign", "serialization": "canonical_utf8_json_sorted_compact_trailing_newline", "self_digest": "sha256(body_without_manifest_sha256)", "required_bindings": ["compiled_protocol_sha256", "code_sha256", "model_sha256", "data_sha256", "backend_sha256", "guard_sha256", "tune_lock_sha256", "provider_receipt_sha256", "energy_receipt_sha256", "result_root_sha256"]},
        "provider_receipt": {"schema": "oaklab-h100-v3-provider-receipt", "required_fields": ["allocation_id", "node_id", "start_utc", "stop_utc", "charged_usd", "hard_usd_ceiling", "launch_manifest_sha256", "raw_trace_sha256", "public_key_hex", "signature_hex", "receipt_sha256"], "timestamp_regex": "^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$", "signature": "ed25519_canonical_body_without_signature_hex", "signature_verification": "independent_ed25519_verification", "charged_leq_ceiling": True},
        "tune_lock": {"schema": "oaklab-h100-v3-tune-lock", "required_fields": ["selected_controller_sha256", "hyperparameters_sha256", "seed_roster_sha256", "prediction_sha256", "assessment_forbidden_before_validation"], "assessment_forbidden_before_validation": True, "independent_receipt_required": True},
        "result_root": {"mode": "closed_world", "allowlist": ["campaign_manifest.json", "compiled_protocol.json", "tune/lock.json", "tune/lock_receipt.json", "provider/allocation.json", "provider/cost.json", "provider/stop.json", "energy/raw_trace.csv", "energy/joules.json", "result/aggregate.json", "validation/independent.json"], "reject_symlinks": True, "reject_extra_paths": True, "validate_all_file_digests": True, "validate_all_file_contents": True},
        "execution_boundary": {"effects_run": False, "implementation_before_review": False, "real_before_synthetic_candidate": False, "assessment_before_independent_lock": False, "provider_before_preflight": False},
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
