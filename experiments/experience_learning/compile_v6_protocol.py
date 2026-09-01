"""Compile and validate the Oak Lab V6 executable protocol contract.

State slice: ``oaklab-experience-learning-constrained-update-policy-v6``.

This module is compiler-only.  It imports no learner, stream runner, backend,
provider, energy, or Astral code.  The compiler emits exactly the seven closed
world sections required by the V6 review boundary.
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
COMPILER_VERSION = "oaklab.cup.v6.protocol-compiler.v1"
COMPILED_SCHEMA = "oaklab.experience-learning.constrained-update-policy-v6.compiled.v1"
SECTIONS = (
    "hash_prng_transcript",
    "controller_transition_table",
    "generator_roster",
    "operation_and_byte_algebra",
    "ablation_execution_multiplicity",
    "adaptation_metrics",
    "lock_counter_control_schemas",
)
SOURCE_KEYS = {
    "schema_version", "protocol_id", "state_slice", "claim_ceiling", "status",
    "implementation_before_review", "estimand", *SECTIONS, "stop_rules", "boundaries",
}


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("utf-8")


def sha256_hex(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _digest(value: Any) -> str:
    return sha256_hex(canonical_json(value))


def _lp32(payload: bytes) -> bytes:
    _require(len(payload) <= 0xFFFFFFFF, "LP32 payload too large")
    return struct.pack(">I", len(payload)) + payload


def _splitmix64(seed_bytes: bytes, count: int) -> list[int]:
    state = int.from_bytes(seed_bytes[:8], "little")
    values: list[int] = []
    for _ in range(count):
        state = (state + 0x9E3779B97F4A7C15) & 0xFFFFFFFFFFFFFFFF
        z = state
        z = ((z ^ (z >> 30)) * 0xBF58476D1CE4E5B9) & 0xFFFFFFFFFFFFFFFF
        z = ((z ^ (z >> 27)) * 0x94D049BB133111EB) & 0xFFFFFFFFFFFFFFFF
        values.append((z ^ (z >> 31)) & 0xFFFFFFFFFFFFFFFF)
    return values


def _transcript_vector(source_digest: str, source: dict[str, Any]) -> dict[str, Any]:
    h = source["hash_prng_transcript"]
    protocol_raw = bytes.fromhex(source_digest)
    cohort = b"fit"
    stream = b"sparse_signal_v6"
    seed = 4000
    frame = (
        _lp32(b"oaklab.cup.v6.prng.seed.v1") + protocol_raw + _lp32(cohort)
        + _lp32(stream) + struct.pack("<Q", seed)
    )
    root = hashlib.sha256(frame).digest()
    raw = _splitmix64(root, 13)
    action_seed = bytes.fromhex(h["action_hash"]["action_seed_hex"])
    action_frame = (
        _lp32(b"oaklab.cup.v6.action.v1") + protocol_raw + action_seed
        + _lp32(cohort) + _lp32(stream) + struct.pack("<Q", seed) + struct.pack("<I", 0)
    )
    return {
        "seed_frame_hex": frame.hex(),
        "root_sha256_hex": root.hex(),
        "initial_state_uint64_le": int.from_bytes(root[:8], "little"),
        "first_12_raw_uint64_hex": [f"{x:016x}" for x in raw[:12]],
        "first_uniform53": (raw[0] >> 11) / float(1 << 53),
        "first_normal12_after_first_draw": sum((x >> 11) / float(1 << 53) for x in raw[1:13]) - 6.0,
        "action_hash_sha256_hex": hashlib.sha256(action_frame).hexdigest(),
    }


def _field_map(fields: Any, name: str) -> None:
    _require(isinstance(fields, list) and fields, f"{name}: fields must be a non-empty list")
    seen: set[str] = set()
    for entry in fields:
        _require(isinstance(entry, list) and len(entry) == 3, f"{name}: malformed field tuple")
        field, field_type, required = entry
        _require(isinstance(field, str) and field and field not in seen, f"{name}: duplicate/invalid field")
        _require(isinstance(field_type, str) and field_type, f"{name}: invalid field type")
        _require(required is True, f"{name}: every field must be required")
        seen.add(field)


def _layout_map(layout: Any, name: str) -> None:
    _require(isinstance(layout, dict), f"{name}: layout must be an object")
    fields = layout.get("fields")
    _require(isinstance(fields, list) and fields, f"{name}: layout fields missing")
    names: set[str] = set()
    for field in fields:
        _require(isinstance(field, list) and len(field) == 4, f"{name}: malformed layout field")
        field_name, field_type, offset, width = field
        _require(isinstance(field_name, str) and field_name not in names, f"{name}: duplicate field")
        _require(isinstance(field_type, str) and isinstance(offset, str) and isinstance(width, str), f"{name}: layout types invalid")
        names.add(field_name)
    _require(layout.get("alignment") == "none", f"{name}: alignment must be none")
    _require(isinstance(layout.get("bytes"), str) and layout["bytes"], f"{name}: byte formula missing")


def validate_source(source: dict[str, Any]) -> None:
    _require(set(source) == SOURCE_KEYS, "V6 source has missing or extra top-level fields")
    _require(source["schema_version"] == "oaklab.experience-learning.constrained-update-policy-v6.source.v1", "V6 source schema mismatch")
    _require(source["protocol_id"] == PROTOCOL_ID and source["state_slice"] == STATE_SLICE, "V6 identity mismatch")
    _require(source["status"] == "frozen_pending_independent_review" and source["implementation_before_review"] is False, "V6 implementation boundary is open")

    estimand = source["estimand"]
    _require(isinstance(estimand, dict) and "complete constrained update-policy trajectory" in estimand["scope"], "complete-policy estimand missing")
    _require("measured before" in estimand["loss"] and "candidate_cumulative_loss" in estimand["primary_transform"], "estimand loss/transform is not pre-update")

    h = source["hash_prng_transcript"]
    _require(h["source_file_bytes"].startswith("UTF-8 without BOM"), "source byte policy is not exact")
    _require(h["lp32"].startswith("u32 big-endian"), "LP32 framing is not exact")
    _require(h["fixed_width"]["uint32"] == "little-endian four bytes" and h["fixed_width"]["uint64"] == "little-endian eight bytes", "fixed-width integer encoding drift")
    _require(len(h["splitmix64"]["next_uint64"]) == 5 and h["splitmix64"]["uniform53"].startswith("(next_uint64()>>11)"), "PRNG recurrence incomplete")
    ah = h["action_hash"]
    _require(ah["probability"] == {"p_num": 1, "p_den": 4, "threshold": "floor((p_num*2^256)/p_den)", "comparison": "apply iff uint256_be(SHA256(frame)) < threshold"}, "treatment probability is not instantiated exactly")
    _require(len(ah["action_seed_hex"]) == 64 and ah["fit_only"] is True, "action seed or fit boundary invalid")
    _require(h["transcript_schema"]["ordering"].endswith("no conditional draws"), "draw transcript is conditional")

    c = source["controller_transition_table"]
    _require(c["actions"] == ["skip", "apply"] and len(c["features"]) == 4, "controller action/feature order changed")
    _require(c["action_features"] == {"skip": "[1,pre_loss_context,event_density,budget_debt]", "apply": "[0,pre_loss_context,event_density,budget_debt]"}, "action feature vectors are not exact")
    _require(c["q_formula"] == "q(action)=left_to_right_dot(theta,action_features[action])", "controller q formula is not exact")
    state_names = [entry[0] for entry in c["state_fields"]]
    _require(len(state_names) == 20 and len(state_names) == len(set(state_names)), "controller state roster is incomplete or duplicated")
    required_state = {"theta", "eligibility", "q_old", "dual_mu", "processed_rows", "cumulative_apply_cost", "pending_valid", "previous_action", "previous_features", "previous_q", "previous_cost", "pending_features", "pending_prediction", "pending_loss", "pending_event_count", "pending_action", "pending_cost", "pending_reward", "pending_local_row", "pending_terminal"}
    _require(required_state.issubset(state_names), "pending/controller fields are incomplete")
    rows = c["rows"]
    _require([row["index"] for row in rows] == list(range(8)), "controller transition indices are not contiguous")
    _require([row["event"] for row in rows] == ["trajectory_init", "observe_pre_action", "credit_previous", "select_action", "model_action", "publish_pending", "terminal_credit", "counter_finalize"], "controller order is not exact")
    _require("pre-transition snapshot" in c["rhs_evaluation"] and "undeclared state is invalid" in c["pending_rule"], "controller state semantics are open")
    _require("pending_reward" in rows[5]["writes"] and "cumulative_apply_cost" in rows[4]["writes"], "controller carryover or budget accounting is incomplete")
    _require(len(c["recurrence"]) == 5 and "clip" in c["recurrence"][3], "controller recurrence is incomplete")
    _require("no model action" in c["terminal_rule"], "terminal model-action prohibition missing")

    roster = source["generator_roster"]
    streams = roster["streams"]
    expected_streams = set(roster["stream_order"])
    _require(expected_streams == {"sparse_signal_v6", "drifting_relevance_v6", "delayed_reward_v6", "event_sensor_v6", "long_horizon_v6", "pure_noise_v6"}, "stream roster mismatch")
    _require(set(streams) == expected_streams and set(roster["draw_roster"]) == expected_streams, "typed generator roster mismatch")
    _require(roster["cohort_order"] == ["fit", "tune", "assessment"] and roster["rows_per_trajectory"] == 256, "cohort/trajectory order changed")
    for stream_id, draws in roster["draw_roster"].items():
        _require(all(isinstance(row, list) and len(row) == 4 for row in draws), f"{stream_id}: draw tuple malformed")
        _require([row[0] for row in draws] == list(range(len(draws))), f"{stream_id}: draw ordinals not contiguous")
        _require(all(isinstance(row[3], int) and row[3] > 0 for row in draws), f"{stream_id}: conditional/empty repeat")
    for stream_id, stream in streams.items():
        _require(isinstance(stream["dimension"], int) and stream["dimension"] > 0, f"{stream_id}: invalid dimension")
        _require(all(isinstance(stream[key], str) and stream[key] for key in ("equation", "draw_order", "draw_mapping", "events")), f"{stream_id}: incomplete generator semantics")
        _require(stream["segments"][0] == 0 and stream["segments"][-1] == 256, f"{stream_id}: segment bounds invalid")
    _require("redraw is forbidden" in roster["draw_policy"] and roster["source_id_frame"] == ["LP32(cohort_id_utf8)", "LP32(stream_id_utf8)", "uint64_le(data_seed)", "uint32_le(local_row)"], "generator custody framing is incomplete")

    algebra = source["operation_and_byte_algebra"]
    _require(algebra["numeric_type_widths"] == {"uint8": 1, "uint32": 4, "uint64": 8, "float64": 8, "sha256_digest": 32}, "numeric widths changed")
    _require("no fused multiply-add" in algebra["numeric_rules"] and "left-to-right" in algebra["numeric_rules"], "numeric evaluation rules incomplete")
    _require(set(algebra["formula_ast"]) == {"forward_dense", "loss_half_squared", "gradient", "model_update", "controller_dot", "eligibility_update", "event_count"}, "operation AST set is incomplete")
    for name in ("model_state", "controller_fit_state", "controller_trajectory_state", "pending_row", "counter_row", "lock_receipt"):
        _layout_map(algebra["byte_layouts"].get(name), name)
    _require("energy joules are absent" in " ".join(algebra["resource_invariants"]), "energy separation invariant missing")

    a = source["ablation_execution_multiplicity"]
    _require(len(a["arm_order"]) == 8 and set(a["execution_matrix"]) == set(a["arm_order"]), "ablation arm set mismatch")
    for arm, phases in a["execution_matrix"].items():
        _require(set(phases) == {"fit", "tune", "assessment"}, f"{arm}: phase participation incomplete")
    _require("no tune-derived probability" in a["matched_random_probability"], "matched-random sealing is not pre-tune")
    _require(len(a["holm_groups"]) == 3 and all("sort raw p" in group["adjustment"] for group in a["holm_groups"]), "Holm tables incomplete")
    _require("missing" in a["missing_rules"] and "nonfinite" in a["missing_rules"], "missing-value rules incomplete")
    _require(len(a["gate_predicates"]) >= 5 and "at least two distinct non-null families" in a["gate_predicates"][0], "multi-family gate missing")
    _require("p_two=erfc" in a["statistic_formula"] and "p_one=0.5*erfc(-z" in a["statistic_formula"] and "95 percent" in a["confidence_interval"], "statistical formula/interval is incomplete")

    m = source["adaptation_metrics"]
    for field in ("baseline", "threshold", "recovery_scan", "lag", "censoring", "aggregation", "zero_and_nonfinite"):
        _require(field in m, f"adaptation metric missing {field}")
    _require("[k,k+8)" in m["recovery_scan"] and "[k+8,k+16)" in m["recovery_scan"], "adaptation windows incomplete")
    _require("next_shift" in m["censoring"] and "never scan across a shift" in m["aggregation"], "shift-bounded adaptation missing")

    schemas = source["lock_counter_control_schemas"]
    required_schemas = {"protocol_compile_receipt", "fit_lock", "tune_lock", "counter_row", "control_result", "assessment_absence", "validator_receipt"}
    _require(set(schemas) == required_schemas | {"schema_policy"}, "schema set has missing or extra entries")
    for name in required_schemas:
        schema = schemas[name]
        _require(schema["schema_id"].startswith("oaklab.cup.v6."), f"{name}: schema identity drift")
        _field_map(schema["fields"], name)
    _require(schemas["assessment_absence"]["fields"][1] == ["materialization_state", "enum(absent)", True], "assessment absence is not explicit")
    _require("must not exist" in schemas["assessment_absence"]["rule"], "assessment absence rule missing")

    _require(isinstance(source["stop_rules"], list) and len(source["stop_rules"]) >= 8, "stop rules incomplete")
    _require(source["boundaries"] == {"plasticity_guard": "closed_historical_comparator_only", "astral": "isolated_not_run", "provider": "not_authorized_in_compiler_slice", "givemeanode_h100": "requires separate operator authorization after synthetic candidate and execution review", "publication": "no_candidate_until_strict_multi_family_gate"}, "execution boundaries changed")


def compile_source(source_path: Path) -> dict[str, Any]:
    source_bytes = source_path.read_bytes()
    _require(source_bytes.startswith(b"{") and source_bytes.endswith(b"\n"), "source must be JSON bytes with one final LF")
    source = json.loads(source_bytes.decode("utf-8"))
    _require(isinstance(source, dict), "source must be an object")
    validate_source(source)
    source_digest = sha256_hex(source_bytes)
    compiled: dict[str, Any] = {
        "schema_version": COMPILED_SCHEMA,
        "protocol_id": PROTOCOL_ID,
        "state_slice": STATE_SLICE,
        "claim_ceiling": source["claim_ceiling"],
        "compiler_version": COMPILER_VERSION,
        "source_spec_sha256": source_digest,
        "sections": list(SECTIONS),
        "section_digests": {name: _digest(source[name]) for name in SECTIONS},
        "transcript_test_vector": _transcript_vector(source_digest, source),
        "assessment_materialization_state": "absent",
        "compiled": {name: source[name] for name in SECTIONS},
        "estimand": source["estimand"],
        "stop_rules": source["stop_rules"],
        "boundaries": source["boundaries"],
    }
    digest_input = dict(compiled)
    compiled["compiled_protocol_sha256"] = sha256_hex(canonical_json(digest_input))
    return compiled


def validate_compiled(compiled: dict[str, Any]) -> None:
    required = {"schema_version", "protocol_id", "state_slice", "claim_ceiling", "compiler_version", "source_spec_sha256", "sections", "section_digests", "transcript_test_vector", "assessment_materialization_state", "compiled", "estimand", "stop_rules", "boundaries", "compiled_protocol_sha256"}
    _require(set(compiled) == required, "compiled artifact has missing or extra fields")
    _require(compiled["schema_version"] == COMPILED_SCHEMA and compiled["protocol_id"] == PROTOCOL_ID and compiled["state_slice"] == STATE_SLICE, "compiled identity mismatch")
    _require(compiled["compiler_version"] == COMPILER_VERSION and compiled["sections"] == list(SECTIONS), "compiled version/section order mismatch")
    _require(compiled["assessment_materialization_state"] == "absent" and set(compiled["compiled"]) == set(SECTIONS), "assessment or section boundary escaped")
    _require(len(compiled["source_spec_sha256"]) == 64 and len(compiled["compiled_protocol_sha256"]) == 64, "compiled digests malformed")
    _require("complete constrained update-policy trajectory" in compiled["estimand"]["scope"], "compiled estimand changed")
    _require(len(compiled["transcript_test_vector"]["first_12_raw_uint64_hex"]) == 12, "compiled transcript vector incomplete")
    no_self = {key: value for key, value in compiled.items() if key != "compiled_protocol_sha256"}
    _require(compiled["compiled_protocol_sha256"] == sha256_hex(canonical_json(no_self)), "compiled protocol digest mismatch")


def main() -> None:
    parser = argparse.ArgumentParser(description="Compile and validate Oak Lab V6 protocol")
    parser.add_argument("source", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--check", type=Path)
    args = parser.parse_args()
    if args.check is not None:
        artifact = json.loads(args.check.read_text(encoding="utf-8"))
        validate_compiled(artifact)
        print(json.dumps({"status": "valid", "state_slice": STATE_SLICE, "compiled_protocol_sha256": artifact["compiled_protocol_sha256"]}, sort_keys=True))
        return
    compiled = compile_source(args.source)
    validate_compiled(compiled)
    encoded = json.dumps(compiled, sort_keys=True, indent=2, ensure_ascii=True, allow_nan=False) + "\n"
    if args.output is not None:
        args.output.write_text(encoded, encoding="utf-8")
    print(json.dumps({"status": "compiled", "state_slice": STATE_SLICE, "source_spec_sha256": compiled["source_spec_sha256"], "compiled_protocol_sha256": compiled["compiled_protocol_sha256"]}, sort_keys=True))


if __name__ == "__main__":
    main()
