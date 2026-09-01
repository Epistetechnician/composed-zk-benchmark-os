#!/usr/bin/env python3
"""Fail-closed validator for the frozen Oak Lab H100 V10 packet.

State slice: oaklab-experience-learning-h100-replication-v10.
This validator performs no learner, data, provider, H100, energy, or assessment work.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
STATE_SLICE = "oaklab-experience-learning-h100-replication-v10"
PROTOCOL_ID = "oaklab.h100.v10"
SOURCE = ROOT / "experiments/experience_learning/oaklab_h100_v10_protocol.json"
COMPILED = ROOT / "experiments/experience_learning/oaklab_h100_v10_compiled_protocol.json"
ARTIFACT = ROOT / "experiments/experience_learning/oaklab_h100_v10_campaign_manifest.json"
PACKET = ROOT / "docs/research/experience-learning/71-oaklab-h100-replication-v10-review-packet.md"
HEX64 = re.compile(r"^[0-9a-f]{64}$")


def canonical(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False) + "\n").encode("utf-8")


def file_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def object_digest(value: Any) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def closed(value: Any, keys: set[str], label: str) -> None:
    require(isinstance(value, dict) and set(value) == keys, f"{label} object is not closed")


def validate_source(source: dict[str, Any]) -> None:
    expected = {"schema_version", "protocol_id", "state_slice", "status", "implementation_before_review", "claim_ceiling", "estimand", "controller", "generator_roster", "hash_prng", "resource_accounting", "statistics", "controls", "locks", "operation_and_byte_algebra", "execution_schemas", "campaign_manifest_artifact", "boundaries", "stop_rules"}
    closed(source, expected, "source")
    require(source["schema_version"] == "oaklab.experience-learning.h100-replication-v10.source.v1" and source["protocol_id"] == PROTOCOL_ID and source["state_slice"] == STATE_SLICE, "source identity mismatch")
    require(source["status"] == "frozen_pending_independent_review" and source["implementation_before_review"] is False, "implementation boundary changed")
    e = source["estimand"]
    require(e["control"] == "fixed_sgd_b1" and e["treatment"] == "dual_budgeted_credit" and e["segment_rows"] == 32 and e["trajectory_rows"] == 256, "estimand mismatch")
    require(e["same_stream"] is True and e["same_initial_checkpoint"] is True and e["arm_order_randomized"] is True and e["assessment_absent_until_lock"] is True, "paired/assessment boundary mismatch")
    require("no current outcome" in e["carryover_control"] and "previous completed segment only" in e["carryover_control"], "current-outcome leakage")
    c = source["controller"]
    require(c["state_bytes"] == 62 and len(c["state_fields"]) == 10 and len(c["transition_table"]) == 7, "controller schema mismatch")
    require([row["index"] for row in c["transition_table"]] == list(range(7)), "controller transition order mismatch")
    require("pre-boundary snapshot" in c["transition_table"][4]["rule"] and "current segment is unread" in c["transition_table"][4]["rule"], "controller leakage rule missing")
    g = source["generator_roster"]
    require(g["rows_per_trajectory"] == 256 and g["segment_boundaries"] == [0, 32, 64, 96, 128, 160, 192, 224, 256] and len(g["stream_order"]) == 6, "generator roster mismatch")
    require(set(g["stream_order"]) == set(g["streams"]) == set(g["draw_roster"]), "generator IDs mismatch")
    for stream_id in g["stream_order"]:
        draws = g["draw_roster"][stream_id]
        require([row[0] for row in draws] == list(range(len(draws))) and all(row[3] > 0 for row in draws), f"{stream_id} draw order mismatch")
        stream = g["streams"][stream_id]
        require(stream["segments"][0] == 0 and stream["segments"][-1] == 256, f"{stream_id} bounds mismatch")
    h = source["hash_prng"]
    require(h["action_assignment"]["fit_only"] is True and h["action_assignment"]["probability"] == {"p_num": 1, "p_den": 2}, "action assignment mismatch")
    r = source["resource_accounting"]
    require(r["controller_state_bytes"] == 62 and r["replay_bytes"] == 0 and "one row" in r["batch_one"] and "controller state is charged" in " ".join(source["operation_and_byte_algebra"]["resource_invariants"]), "resource accounting mismatch")
    s = source["statistics"]
    require(s["families"] == ["predictable_noise", "drift", "delayed_reward", "event", "long_horizon", "null"] and s["fit_seeds"]["count"] == 48 and s["tune_seeds"]["count"] == 24 and s["assessment_seeds"]["count"] == 48 and s["raw_rows_required"] is True and s["caller_supplied_booleans_forbidden"] is True, "statistics mismatch")
    require(source["controls"]["arms"] == ["fixed_sgd_b1", "dual_budgeted_credit", "lambda_zero", "always_apply", "matched_random", "noise_floor", "oracle_feature_sgd"], "control roster mismatch")
    require(source["locks"]["prediction_lock_before_assessment"] is True and source["locks"]["assessment_absence"]["materialization_state"] == "absent" and source["locks"]["assessment_absence"]["entry_count"] == 0, "lock/absence mismatch")
    a = source["operation_and_byte_algebra"]
    require(set(a["formula_ast"]) == {"forward_dense", "loss_half_squared", "gradient", "model_update", "controller_boundary"}, "AST roster mismatch")
    x = source["execution_schemas"]
    require(x["provider"]["currency"] == "USD" and x["result_root"]["mode"] == "closed_world" and x["result_root"]["reject_extra_paths"] is True and x["result_root"]["reject_symlinks"] is True, "execution schema mismatch")
    m = source["campaign_manifest_artifact"]
    require(m["schema"] == "oaklab.h100.v10.campaign-manifest-artifact.v1" and m["runtime_manifest_required"] is True and m["result_root_required"] is True, "campaign contract mismatch")
    require(source["boundaries"]["implementation"] == "prohibited_before_independent_ACCEPT" and source["boundaries"]["real_execution"].startswith("prohibited_before_synthetic_candidate"), "execution boundary mismatch")
    require(len(source["stop_rules"]) == 8 and "without retuning" in source["stop_rules"][-1], "stop rules mismatch")


def validate_compiled(source: dict[str, Any]) -> dict[str, str]:
    require(COMPILED.is_file() and not COMPILED.is_symlink(), "compiled artifact missing")
    compiled = json.loads(COMPILED.read_bytes())
    closed(compiled, {"schema", "protocol_id", "state_slice", "compiler_version", "source_sha256", "section_digests", "sections", "claim_ceiling", "boundaries", "stop_rules", "assessment_materialization_state", "execution_gate", "transcript_test_vector", "compiled_protocol_sha256"}, "compiled artifact")
    source_sha = file_digest(SOURCE)
    require(compiled["schema"] == "oaklab.experience-learning.h100-replication-v10.compiled.v1" and compiled["protocol_id"] == PROTOCOL_ID and compiled["state_slice"] == STATE_SLICE and compiled["source_sha256"] == source_sha, "compiled identity/source binding mismatch")
    require(compiled["assessment_materialization_state"] == "absent" and compiled["execution_gate"]["review_accept_required"] is True and compiled["execution_gate"]["effects_run"] is False, "compiled execution gate opened")
    body = {key: value for key, value in compiled.items() if key != "compiled_protocol_sha256"}
    require(compiled["compiled_protocol_sha256"] == object_digest(body), "compiled self-digest mismatch")
    return {"source_sha256": source_sha, "compiled_sha256": file_digest(COMPILED), "compiled_self_digest": compiled["compiled_protocol_sha256"]}


def validate_manifest(current: dict[str, str]) -> str:
    require(ARTIFACT.is_file() and not ARTIFACT.is_symlink(), "campaign manifest artifact missing")
    artifact = json.loads(ARTIFACT.read_bytes())
    keys = {"schema", "state_slice", "source_sha256", "compiler_sha256", "validator_sha256", "tests_sha256", "agents_sha256", "campaign_manifest_artifact_sha256", "compiled_protocol_file_sha256", "review_packet_sha256", "backend_sha256", "guard_sha256", "model_sha256", "data_sha256", "fit_lock_sha256", "tune_lock_sha256", "tune_lock_receipt_sha256", "provider_allocation_sha256", "provider_cost_sha256", "provider_stop_sha256", "energy_receipt_sha256", "result_root_sha256", "hard_usd_ceiling", "manifest_sha256"}
    closed(artifact, keys, "campaign manifest artifact")
    require(artifact["schema"] == "oaklab.h100.v10.campaign-manifest-artifact.v1" and artifact["state_slice"] == STATE_SLICE and artifact["source_sha256"] == current["source_sha256"] and artifact["compiled_protocol_file_sha256"] == current["compiled_sha256"], "campaign manifest identity/staleness mismatch")
    paths = {"compiler_sha256": ROOT / "experiments/experience_learning/compile_oaklab_h100_v10_protocol.py", "validator_sha256": ROOT / "experiments/experience_learning/validate_oaklab_h100_v10_protocol.py", "tests_sha256": ROOT / "experiments/experience_learning/tests/test_oaklab_h100_v10_protocol.py", "agents_sha256": ROOT / "AGENTS.md", "review_packet_sha256": PACKET}
    for key, path in paths.items():
        require(artifact[key] == file_digest(path), f"campaign manifest {key} binding mismatch")
    for key in keys - {"schema", "state_slice", "hard_usd_ceiling", "manifest_sha256"}:
        require(isinstance(artifact[key], str) and HEX64.fullmatch(artifact[key]) is not None, f"{key} is not a digest")
    require(artifact["hard_usd_ceiling"] == 25, "hard USD ceiling changed")
    require(artifact["manifest_sha256"] == object_digest({key: value for key, value in artifact.items() if key != "manifest_sha256"}), "campaign manifest self-digest mismatch")
    return artifact["manifest_sha256"]


def validate() -> dict[str, Any]:
    source = json.loads(SOURCE.read_bytes())
    validate_source(source)
    current = validate_compiled(source)
    manifest_sha = validate_manifest(current)
    require(PACKET.is_file() and not PACKET.is_symlink(), "review packet missing")
    return {"valid": True, "state_slice": STATE_SLICE, "source_sha256": current["source_sha256"], "compiled_sha256": current["compiled_sha256"], "compiled_self_digest": current["compiled_self_digest"], "campaign_manifest_sha256": manifest_sha, "assessment_materialization_state": "absent", "real_execution": "prohibited", "provider": "prohibited"}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    parser.parse_args()
    print(json.dumps(validate(), sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
