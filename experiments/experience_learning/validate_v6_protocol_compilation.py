"""Independent V6 protocol compiler validator.

State slice: ``oaklab-experience-learning-constrained-update-policy-v6``.
The validator reimplements canonicalization, framing, PRNG, digest, and
closed-world checks without importing the compiler or any execution code.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
from pathlib import Path
from typing import Any


STATE_SLICE = "oaklab-experience-learning-constrained-update-policy-v6"
PROTOCOL_ID = "oaklab.cup.v6"
COMPILED_SCHEMA = "oaklab.experience-learning.constrained-update-policy-v6.compiled.v1"
SECTIONS = [
    "hash_prng_transcript",
    "controller_transition_table",
    "generator_roster",
    "operation_and_byte_algebra",
    "ablation_execution_multiplicity",
    "adaptation_metrics",
    "lock_counter_control_schemas",
]


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("utf-8")


def digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def lp32(value: bytes) -> bytes:
    return struct.pack(">I", len(value)) + value


def splitmix64(seed_bytes: bytes, count: int) -> list[int]:
    state = int.from_bytes(seed_bytes[:8], "little")
    output: list[int] = []
    for _ in range(count):
        state = (state + 0x9E3779B97F4A7C15) & 0xFFFFFFFFFFFFFFFF
        z = state
        z = ((z ^ (z >> 30)) * 0xBF58476D1CE4E5B9) & 0xFFFFFFFFFFFFFFFF
        z = ((z ^ (z >> 27)) * 0x94D049BB133111EB) & 0xFFFFFFFFFFFFFFFF
        output.append((z ^ (z >> 31)) & 0xFFFFFFFFFFFFFFFF)
    return output


def independent_vector(source_digest: str, source: dict[str, Any]) -> dict[str, Any]:
    protocol_raw = bytes.fromhex(source_digest)
    frame = lp32(b"oaklab.cup.v6.prng.seed.v1") + protocol_raw + lp32(b"fit") + lp32(b"sparse_signal_v6") + struct.pack("<Q", 4000)
    root = hashlib.sha256(frame).digest()
    raw = splitmix64(root, 13)
    action_raw = bytes.fromhex(source["hash_prng_transcript"]["action_hash"]["action_seed_hex"])
    action = lp32(b"oaklab.cup.v6.action.v1") + protocol_raw + action_raw + lp32(b"fit") + lp32(b"sparse_signal_v6") + struct.pack("<Q", 4000) + struct.pack("<I", 0)
    return {
        "seed_frame_hex": frame.hex(),
        "root_sha256_hex": root.hex(),
        "initial_state_uint64_le": int.from_bytes(root[:8], "little"),
        "first_12_raw_uint64_hex": [f"{value:016x}" for value in raw[:12]],
        "first_uniform53": (raw[0] >> 11) / float(1 << 53),
        "first_normal12_after_first_draw": sum((value >> 11) / float(1 << 53) for value in raw[1:13]) - 6.0,
        "action_hash_sha256_hex": hashlib.sha256(action).hexdigest(),
    }


def validate(source_path: Path, artifact_path: Path) -> dict[str, Any]:
    source_bytes = source_path.read_bytes()
    require(source_bytes.startswith(b"{") and source_bytes.endswith(b"\n"), "source must be UTF-8 JSON with a final LF")
    source = json.loads(source_bytes.decode("utf-8"))
    artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
    require(isinstance(source, dict), "source must be an object")
    require(isinstance(artifact, dict), "compiled artifact must be an object")
    expected = {"schema_version", "protocol_id", "state_slice", "claim_ceiling", "compiler_version", "source_spec_sha256", "sections", "section_digests", "transcript_test_vector", "assessment_materialization_state", "compiled", "estimand", "stop_rules", "boundaries", "compiled_protocol_sha256"}
    require(set(artifact) == expected, "compiled artifact has missing or extra fields")
    source_digest = digest(source_bytes)
    require(artifact["source_spec_sha256"] == source_digest, "source digest mismatch")
    require(artifact["schema_version"] == COMPILED_SCHEMA and artifact["protocol_id"] == PROTOCOL_ID and artifact["state_slice"] == STATE_SLICE, "compiled identity mismatch")
    require(artifact["sections"] == SECTIONS and set(artifact["compiled"]) == set(SECTIONS), "compiled seven sections mismatch")
    require(artifact["compiled"] == {name: source[name] for name in SECTIONS}, "compiled sections differ from source")
    require(artifact["section_digests"] == {name: digest(canonical(source[name])) for name in SECTIONS}, "section digest mismatch")
    require(artifact["transcript_test_vector"] == independent_vector(source_digest, source), "PRNG/action transcript vector mismatch")
    require(artifact["assessment_materialization_state"] == "absent", "assessment materialized before review")
    no_self = {key: value for key, value in artifact.items() if key != "compiled_protocol_sha256"}
    require(artifact["compiled_protocol_sha256"] == digest(canonical(no_self)), "compiled digest mismatch")

    require(source["protocol_id"] == PROTOCOL_ID and source["state_slice"] == STATE_SLICE, "source identity mismatch")
    require(source["implementation_before_review"] is False and source["status"] == "frozen_pending_independent_review", "source review boundary changed")
    h = source["hash_prng_transcript"]
    require(h["action_hash"]["probability"]["p_num"] == 1 and h["action_hash"]["probability"]["p_den"] == 4, "treatment probability is not 1/4")
    require(h["transcript_schema"]["ordering"].endswith("no conditional draws"), "draw order is conditional")

    c = source["controller_transition_table"]
    require([row["index"] for row in c["rows"]] == list(range(8)), "controller row indices are not contiguous")
    require([row["event"] for row in c["rows"]] == ["trajectory_init", "observe_pre_action", "credit_previous", "select_action", "model_action", "publish_pending", "terminal_credit", "counter_finalize"], "controller order mismatch")
    require(c["action_features"] == {"skip": "[1,pre_loss_context,event_density,budget_debt]", "apply": "[0,pre_loss_context,event_density,budget_debt]"}, "action feature vectors mismatch")
    require(c["q_formula"] == "q(action)=left_to_right_dot(theta,action_features[action])", "controller q formula mismatch")
    names = [row[0] for row in c["state_fields"]]
    require(len(names) == 20 and len(names) == len(set(names)), "controller state fields are not unique")
    require(set(names) == {"theta", "eligibility", "q_old", "dual_mu", "processed_rows", "cumulative_apply_cost", "pending_valid", "previous_action", "previous_features", "previous_q", "previous_cost", "pending_features", "pending_prediction", "pending_loss", "pending_event_count", "pending_action", "pending_cost", "pending_reward", "pending_local_row", "pending_terminal"} and "undeclared state is invalid" in c["pending_rule"], "pending state schema incomplete")
    require("pending_reward" in c["rows"][5]["writes"] and "cumulative_apply_cost" in c["rows"][4]["writes"], "controller carryover or budget accounting incomplete")
    require("pre-transition snapshot" in c["rhs_evaluation"] and "no model action" in c["terminal_rule"], "controller recurrence boundary incomplete")

    roster = source["generator_roster"]
    expected_streams = {"sparse_signal_v6", "drifting_relevance_v6", "delayed_reward_v6", "event_sensor_v6", "long_horizon_v6", "pure_noise_v6"}
    require(set(roster["stream_order"]) == expected_streams and set(roster["streams"]) == expected_streams and set(roster["draw_roster"]) == expected_streams, "generator roster mismatch")
    for stream_id, draws in roster["draw_roster"].items():
        require([row[0] for row in draws] == list(range(len(draws))), f"{stream_id}: draw ordinals mismatch")
        require(all(len(row) == 4 and isinstance(row[3], int) and row[3] > 0 for row in draws), f"{stream_id}: draw repeats invalid")
    require("redraw is forbidden" in roster["draw_policy"], "generator redraw policy missing")
    for stream_id, stream in roster["streams"].items():
        require(stream["segments"][0] == 0 and stream["segments"][-1] == 256, f"{stream_id}: segment bounds invalid")
        require(all(isinstance(stream[key], str) and stream[key] for key in ("equation", "draw_order", "draw_mapping", "events")), f"{stream_id}: semantic fields missing")

    algebra = source["operation_and_byte_algebra"]
    require("no fused multiply-add" in algebra["numeric_rules"], "numeric rule incomplete")
    require(set(algebra["formula_ast"]) == {"forward_dense", "loss_half_squared", "gradient", "model_update", "controller_dot", "eligibility_update", "event_count"}, "operation AST mismatch")
    for name in ("model_state", "controller_fit_state", "controller_trajectory_state", "pending_row", "counter_row", "lock_receipt"):
        layout = algebra["byte_layouts"][name]
        require(layout["alignment"] == "none" and layout["fields"] and layout["bytes"], f"{name}: byte layout incomplete")
    require("energy joules are absent" in " ".join(algebra["resource_invariants"]), "energy must remain separate")

    ablations = source["ablation_execution_multiplicity"]
    require(len(ablations["arm_order"]) == 8 and set(ablations["execution_matrix"]) == set(ablations["arm_order"]), "ablation set mismatch")
    for arm, phases in ablations["execution_matrix"].items():
        require(set(phases) == {"fit", "tune", "assessment"}, f"{arm}: incomplete phase participation")
    require("no tune-derived probability" in ablations["matched_random_probability"], "matched random not locked before tune")
    require(len(ablations["holm_groups"]) == 3 and all("sort raw p" in group["adjustment"] for group in ablations["holm_groups"]), "multiplicity table incomplete")
    require(len(ablations["gate_predicates"]) >= 5 and "at least two distinct non-null families" in ablations["gate_predicates"][0], "quality gate incomplete")
    require("p_two=erfc" in ablations["statistic_formula"] and "p_one=0.5*erfc(-z" in ablations["statistic_formula"] and "95 percent" in ablations["confidence_interval"], "statistical formula/interval incomplete")

    metrics = source["adaptation_metrics"]
    require("[k,k+8)" in metrics["recovery_scan"] and "[k+8,k+16)" in metrics["recovery_scan"], "adaptation windows incomplete")
    require("next_shift" in metrics["censoring"] and "never scan across a shift" in metrics["aggregation"], "adaptation shift bound incomplete")

    schemas = source["lock_counter_control_schemas"]
    expected_schemas = {"protocol_compile_receipt", "fit_lock", "tune_lock", "counter_row", "control_result", "assessment_absence", "validator_receipt"}
    require(set(schemas) == expected_schemas | {"schema_policy"}, "lock/counter/control schema set mismatch")
    for name in expected_schemas:
        schema = schemas[name]
        require(schema["schema_id"].startswith("oaklab.cup.v6."), f"{name}: schema id mismatch")
        fields = schema["fields"]
        require(fields and len(fields) == len({entry[0] for entry in fields}), f"{name}: duplicate/missing field")
        require(all(isinstance(entry, list) and len(entry) == 3 and entry[2] is True for entry in fields), f"{name}: not closed-world")
    require(schemas["assessment_absence"]["fields"][1] == ["materialization_state", "enum(absent)", True], "assessment absence changed")
    require("must not exist" in schemas["assessment_absence"]["rule"], "assessment absence rule missing")

    require(source["boundaries"]["givemeanode_h100"].startswith("requires separate operator"), "H100 boundary was broadened")
    return {"status": "valid", "decision": "pending_independent_review", "state_slice": STATE_SLICE, "source_spec_sha256": source_digest, "compiled_protocol_sha256": artifact["compiled_protocol_sha256"], "assessment_materialization_state": "absent"}


def main() -> None:
    parser = argparse.ArgumentParser(description="Independently validate Oak Lab V6 compilation")
    parser.add_argument("source", type=Path)
    parser.add_argument("artifact", type=Path)
    args = parser.parse_args()
    print(json.dumps(validate(args.source, args.artifact), sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
