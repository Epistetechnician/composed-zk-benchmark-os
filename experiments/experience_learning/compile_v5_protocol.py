"""Compile the Oak Lab V5 protocol into a deterministic executable contract.

State slice: ``oaklab-experience-learning-constrained-update-policy-v5``.

This module is intentionally compiler-only.  It imports no learner, stream,
backend, or execution module.  The generated digest is over the canonical
compiled payload with its own digest field omitted, so a reviewer can
recompute it without trusting this implementation's hash helper.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
from pathlib import Path
from typing import Any


STATE_SLICE = "oaklab-experience-learning-constrained-update-policy-v5"
COMPILER_VERSION = "oaklab.cup.v5.protocol-compiler.v1"
COMPILED_SCHEMA_VERSION = "oaklab.experience-learning.constrained-update-policy-v5.compiled.v1"
SECTION_NAMES = (
    "hash_prng_transcript",
    "controller_transition_table",
    "generator_roster",
    "operation_and_byte_algebra",
    "ablation_execution_multiplicity",
    "adaptation_metrics",
    "lock_counter_control_schemas",
)
SOURCE_REQUIRED = {
    "schema_version",
    "protocol_id",
    "state_slice",
    "claim_ceiling",
    "status",
    "implementation_before_review",
    "estimand",
    *SECTION_NAMES,
    "stop_rules",
    "boundaries",
}


def canonical_json(value: Any) -> bytes:
    """Return the protocol's byte-exact canonical JSON encoding."""

    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")


def sha256_hex(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _lp32(payload: bytes) -> bytes:
    if len(payload) > 0xFFFFFFFF:
        raise ValueError("LP32 payload too large")
    return struct.pack(">I", len(payload)) + payload


def _splitmix64_vector(seed_bytes: bytes, count: int) -> list[int]:
    state = int.from_bytes(seed_bytes[:8], "big")
    values: list[int] = []
    for _ in range(count):
        state = (state + 0x9E3779B97F4A7C15) & 0xFFFFFFFFFFFFFFFF
        value = state
        value = ((value ^ (value >> 30)) * 0xBF58476D1CE4E5B9) & 0xFFFFFFFFFFFFFFFF
        value = ((value ^ (value >> 27)) * 0x94D049BB133111EB) & 0xFFFFFFFFFFFFFFFF
        values.append((value ^ (value >> 31)) & 0xFFFFFFFFFFFFFFFF)
    return values


def _transcript_vector(source_digest_hex: str) -> dict[str, Any]:
    protocol_digest = bytes.fromhex(source_digest_hex)
    cohort = b"fit"
    stream = b"sparse_predictable_v5"
    seed = 4000
    init_frame = (
        _lp32(b"oaklab.cup.v5.splitmix64.seed.v1")
        + protocol_digest
        + _lp32(cohort)
        + _lp32(stream)
        + struct.pack(">Q", seed)
    )
    init_digest = hashlib.sha256(init_frame).digest()
    raw = _splitmix64_vector(init_digest, 13)
    uniform53 = (raw[0] >> 11) / float(1 << 53)
    normal12 = sum((value >> 11) / float(1 << 53) for value in raw[1:13]) - 6.0
    action_frame = (
        _lp32(b"oaklab.cup.v5.action.v1")
        + protocol_digest
        + bytes.fromhex("7fefd5e1fbc346fbe8c20dfba40c7c362a0f6935d6d5f4707291ded5ea87cd56")
        + _lp32(cohort)
        + _lp32(stream)
        + struct.pack(">Q", seed)
        + struct.pack(">I", 0)
    )
    return {
        "frame_hex": init_frame.hex(),
        "root_sha256_hex": init_digest.hex(),
        "initial_state_uint64_be": int.from_bytes(init_digest[:8], "big"),
        "first_12_raw_uint64_hex": [f"{value:016x}" for value in raw[:12]],
        "first_uniform53": uniform53,
        "first_normal12_after_first_draw": normal12,
        "action_hash_sha256_hex": hashlib.sha256(action_frame).hexdigest(),
    }


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _is_hex_digest(value: Any) -> bool:
    if not isinstance(value, str) or len(value) != 64:
        return False
    try:
        int(value, 16)
    except ValueError:
        return False
    return True


def _require_field_map(fields: Any, schema_id: str) -> None:
    _require(isinstance(fields, list) and fields, f"{schema_id}: fields must be a non-empty list")
    names: list[str] = []
    for entry in fields:
        _require(isinstance(entry, list) and len(entry) == 3, f"{schema_id}: malformed field tuple")
        name, field_type, required = entry
        _require(isinstance(name, str) and name, f"{schema_id}: field name is invalid")
        _require(isinstance(field_type, str) and field_type, f"{schema_id}: field type is invalid")
        _require(required is True, f"{schema_id}: every field is required")
        _require(name not in names, f"{schema_id}: duplicate field {name}")
        names.append(name)


def _validate_source(source: dict[str, Any]) -> None:
    _require(set(source) == SOURCE_REQUIRED, "V5 source has missing or extra top-level fields")
    _require(source["schema_version"] == "oaklab.experience-learning.constrained-update-policy-v5.source.v1", "V5 source schema mismatch")
    _require(source["protocol_id"] == "oaklab.cup.v5", "V5 protocol identity mismatch")
    _require(source["state_slice"] == STATE_SLICE, "V5 state slice mismatch")
    _require(source["implementation_before_review"] is False, "V5 implementation-before-review must remain false")
    _require(source["status"] == "frozen_pending_independent_review", "V5 source must be pending independent review")
    _require(source["claim_ceiling"] == "LocalDevelopmentOakLabConstrainedUpdatePolicyV5ProtocolCompilerOnly", "V5 claim ceiling changed")
    estimand = source["estimand"]
    _require(isinstance(estimand, dict), "V5 estimand must be an object")
    for field in ("name", "notation", "unit", "loss", "scope", "identification", "primary_transform", "favorable_direction"):
        _require(field in estimand, f"V5 estimand missing {field}")
    _require("complete-policy" in estimand["scope"], "V5 estimand must remain complete-policy")

    hash_spec = source["hash_prng_transcript"]
    _require(hash_spec["canonical_json"].startswith("UTF-8 bytes"), "canonical JSON codec is not explicit")
    _require(hash_spec.get("file_bytes") == "UTF-8 without BOM, LF line endings, exactly one final LF; source digest is over these exact bytes", "source byte policy is not exact")
    _require(hash_spec["frame"].startswith("LP32"), "hash framing is not length-prefixed")
    _require(hash_spec["field_encodings"]["uint32"] == "unsigned 32-bit big-endian payload", "uint32 encoding drift")
    _require(hash_spec["field_encodings"]["uint64"] == "unsigned 64-bit big-endian payload", "uint64 encoding drift")
    _require(hash_spec["splitmix64"]["uniform53"] == "(next_uint64()>>11)/9007199254740992", "uniform53 codec drift")
    _require(len(hash_spec["splitmix64"]["next_uint64"]) == 5, "SplitMix64 recurrence is incomplete")
    _require(hash_spec["transcript_schema"]["ordering"] == "ascending draw_ordinal; no conditional draws", "draw transcript ordering is not unconditional")
    _require(hash_spec["action_hash"]["ties"] == "apply", "action tie rule changed")

    controller = source["controller_transition_table"]
    _require(controller["actions"] == ["skip", "apply"], "controller action order changed")
    _require(len(controller["state_fields"]) == 20, "controller pending/state field roster is incomplete")
    state_names = [field["name"] for field in controller["state_fields"]]
    _require(len(state_names) == len(set(state_names)), "controller state field names are not unique")
    _require({"pending_valid", "previous_action", "previous_features", "previous_q", "previous_apply_cost", "previous_mu_at_action", "pending_features", "pending_prediction", "pending_loss", "pending_event_count", "pending_action", "pending_apply_cost", "pending_mu_at_action", "pending_reward", "pending_terminal", "pending_local_row"}.issubset(state_names), "pending field roster changed")
    rows = controller["rows"]
    _require(sorted(row["index"] for row in rows) == list(range(8)), "controller transition indices must be contiguous")
    _require(rows[1]["event"] == "observe_pre_action" and rows[2]["event"] == "select_action", "controller order is not explicit")
    _require(any(row["event"] == "model_action" and row["index"] == 4 for row in rows), "controller model action transition missing")
    _require(any(row["event"] in {"credit_previous_fit_only", "controller_update_fit_only"} and row["index"] == 3 for row in rows), "controller credit transition missing")
    _require("pending_rule" in controller and "undeclared state is invalid" in controller["pending_rule"], "pending state rule missing")
    _require(len(controller["controller_recurrence"]) == 5, "controller recurrence is incomplete")

    roster = source["generator_roster"]
    _require(roster["rows_per_trajectory"] == 252, "row count must be 252")
    _require(roster["cohort_order"] == ["fit", "tune", "assessment"], "cohort order changed")
    _require(roster["stream_order"] == ["delayed_reward_v5", "feature_relevance_v5", "piecewise_drift_v5", "event_camera_v5", "sparse_predictable_v5", "noisy_mnist_v5", "long_horizon_v5", "pure_noise_v5"], "stream roster/order changed")
    streams = roster["streams"]
    expected_streams = {"sparse_predictable_v5", "noisy_mnist_v5", "feature_relevance_v5", "piecewise_drift_v5", "delayed_reward_v5", "event_camera_v5", "long_horizon_v5", "pure_noise_v5"}
    _require(set(streams) == expected_streams, "generator stream roster is incomplete or has extras")
    _require(set(roster.get("draw_roster", {})) == expected_streams, "typed draw roster is incomplete")
    for stream_id, draw_list in roster["draw_roster"].items():
        _require([entry.get("ordinal") for entry in draw_list] == list(range(len(draw_list))), f"{stream_id}: draw ordinals are not contiguous")
        _require(all(isinstance(entry.get("repeat"), int) and entry["repeat"] > 0 for entry in draw_list), f"{stream_id}: draw repeat is invalid")
    for stream_id, stream in streams.items():
        _require(isinstance(stream.get("dimension"), int) and stream["dimension"] > 0, f"{stream_id}: dimension is invalid")
        _require(isinstance(stream.get("draws"), list) and stream["draws"], f"{stream_id}: unconditional draw roster missing")
        _require(isinstance(stream.get("segments"), list) and stream["segments"][0] == 0 and stream["segments"][-1] == 252, f"{stream_id}: segment boundaries invalid")
        _require("equation" in stream and "events" in stream, f"{stream_id}: equation or event rule missing")
    _require(roster["family_map"]["null"] == ["pure_noise_v5"], "pure-noise null control missing")
    _require("conditional branches select or zero already-drawn values" in roster["draw_policy"], "conditional draw prohibition missing")

    algebra = source["operation_and_byte_algebra"]
    widths = algebra["numeric_type_widths"]
    _require(widths == {"boolean": 1, "uint8": 1, "uint32": 4, "uint64": 8, "float64": 8, "sha256_digest": 32}, "numeric byte widths changed")
    for formula in ("forward", "gradient", "update", "parameter_writes", "active_parameter_writes"):
        _require(formula in algebra["model_formulas"], f"missing model formula {formula}")
    for layout in ("model_state", "fit_controller_state", "pending_row", "counter_row", "assessment_compiled_controller", "lock_receipt"):
        _require(layout in algebra["byte_layouts"], f"missing byte layout {layout}")
    _require(set(algebra.get("formula_ast", {})) >= {"model_forward_dense", "model_gradient", "model_update", "parameter_writes", "controller_dot", "event_count"}, "typed operation formula AST is incomplete")
    _require("joules are separate" in " ".join(algebra["resource_invariants"]), "energy separation invariant missing")

    ablations = source["ablation_execution_multiplicity"]
    _require(ablations["arm_order"] == ["fixed_sgd_b1", "complete_policy", "lambda_zero", "no_dual", "matched_random", "reward_shift_37", "always_skip", "noise_floor", "oracle_feature_sgd", "twin_oracle"], "ablation order changed")
    _require(set(ablations["arms"]) == set(ablations["arm_order"]), "ablation arm table mismatch")
    _require([row["phase"] for row in ablations["execution_table"]] == ["fit", "tune", "assessment"], "ablation execution phases must be ordered")
    _require(len(ablations["holm_groups"]) == 3, "multiplicity groups are incomplete")
    _require(all(group.get("adjustment", "").startswith("sort raw p then") for group in ablations["holm_groups"]), "Holm adjustment rule is not exact")
    _require(any("at least two primary families" in predicate for predicate in ablations["gate_predicates"]), "primary multi-family gate missing")

    adaptation = source["adaptation_metrics"]
    for field in ("primary_temporal_endpoint", "baseline", "threshold", "recovery_scan", "lag", "censoring", "aggregation"):
        _require(field in adaptation, f"adaptation metric missing {field}")
    _require("never scan across a shift" in adaptation["aggregation"], "shift-bounded adaptation aggregation missing")
    _require("next_shift" in adaptation["recovery_scan"], "next-shift bound missing")
    _require("adjacent means" in adaptation["recovery_scan"] and "[k,k+8)" in adaptation["recovery_scan"] and "[k+8,k+16)" in adaptation["recovery_scan"], "two-window recovery rule missing")

    schemas = source["lock_counter_control_schemas"]
    for schema_name in ("protocol_compile_receipt", "fit_lock", "tune_lock", "counter_row", "control_result", "assessment_absence", "validator_receipt"):
        schema = schemas[schema_name]
        _require(isinstance(schema.get("schema_id"), str) and schema["schema_id"].startswith("oaklab.cup.v5."), f"{schema_name}: schema id is not V5")
        _require_field_map(schema.get("fields"), schema_name)
    absence = schemas["assessment_absence"]
    _require(absence["fields"][1] == ["materialization_state", "enum(absent)", True], "assessment absence must be explicit")
    _require("assessment files, rows, and effects must not exist" in schemas["assessment_materialization_rule"], "assessment materialization gate missing")

    _require(isinstance(source["stop_rules"], list) and len(source["stop_rules"]) >= 6, "stop rules are incomplete")
    _require(source["boundaries"]["astral"] == "isolated_not_run", "Astral boundary changed")
    _require(source["boundaries"]["plasticity_guard"] == "closed_historical_comparator_only", "plasticity guard boundary changed")


def compile_source(source_path: Path) -> dict[str, Any]:
    source_bytes = source_path.read_bytes()
    source = json.loads(source_bytes.decode("utf-8"))
    _require(isinstance(source, dict), "V5 source must be a JSON object")
    _validate_source(source)
    source_digest = sha256_hex(source_bytes)
    compiled: dict[str, Any] = {
        "schema_version": COMPILED_SCHEMA_VERSION,
        "protocol_id": source["protocol_id"],
        "state_slice": STATE_SLICE,
        "claim_ceiling": source["claim_ceiling"],
        "compiler_version": COMPILER_VERSION,
        "source_spec_sha256": source_digest,
        "sections": list(SECTION_NAMES),
        "section_digests": {name: sha256_hex(canonical_json(source[name])) for name in SECTION_NAMES},
        "transcript_test_vector": _transcript_vector(source_digest),
        "assessment_materialization_state": "absent",
        "compiled": {name: source[name] for name in SECTION_NAMES},
        "stop_rules": source["stop_rules"],
        "boundaries": source["boundaries"],
        "estimand": source["estimand"],
    }
    compiled["compiled_protocol_sha256"] = sha256_hex(canonical_json(compiled))
    return compiled


def validate_compiled(compiled: dict[str, Any]) -> None:
    _require(set(compiled) == {"schema_version", "protocol_id", "state_slice", "claim_ceiling", "compiler_version", "source_spec_sha256", "sections", "section_digests", "transcript_test_vector", "assessment_materialization_state", "compiled", "stop_rules", "boundaries", "estimand", "compiled_protocol_sha256"}, "compiled artifact has missing or extra top-level fields")
    _require(compiled["schema_version"] == COMPILED_SCHEMA_VERSION, "compiled schema mismatch")
    _require(compiled["protocol_id"] == "oaklab.cup.v5" and compiled["state_slice"] == STATE_SLICE, "compiled identity mismatch")
    _require(compiled["compiler_version"] == COMPILER_VERSION, "compiler version mismatch")
    _require(_is_hex_digest(compiled["source_spec_sha256"]), "source digest is malformed")
    _require(compiled["sections"] == list(SECTION_NAMES), "compiled sections are not the exact seven required sections")
    _require(set(compiled["section_digests"]) == set(SECTION_NAMES) and all(_is_hex_digest(value) for value in compiled["section_digests"].values()), "section digest table is incomplete")
    _require(compiled["assessment_materialization_state"] == "absent", "assessment materialization escaped absence gate")
    _require(set(compiled["compiled"]) == set(SECTION_NAMES), "compiled section map is incomplete")
    vector = compiled["transcript_test_vector"]
    _require(len(vector.get("first_12_raw_uint64_hex", [])) == 12 and _is_hex_digest(vector.get("action_hash_sha256_hex")), "PRNG/action transcript vector is incomplete")
    _require(isinstance(compiled["estimand"], dict) and "complete-policy" in compiled["estimand"]["scope"], "compiled estimand changed")
    digest_input = {key: value for key, value in compiled.items() if key != "compiled_protocol_sha256"}
    _require(compiled["compiled_protocol_sha256"] == sha256_hex(canonical_json(digest_input)), "compiled protocol digest mismatch")


def main() -> None:
    parser = argparse.ArgumentParser(description="Compile and validate Oak Lab V5 protocol")
    parser.add_argument("source", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--check", type=Path, help="validate an existing compiled artifact instead of compiling")
    args = parser.parse_args()
    if args.check is not None:
        artifact = json.loads(args.check.read_text(encoding="utf-8"))
        validate_compiled(artifact)
        print(json.dumps({"status": "valid", "compiled_protocol_sha256": artifact["compiled_protocol_sha256"], "state_slice": STATE_SLICE}, sort_keys=True))
        return
    compiled = compile_source(args.source)
    validate_compiled(compiled)
    encoded = json.dumps(compiled, sort_keys=True, indent=2, ensure_ascii=True, allow_nan=False) + "\n"
    if args.output is not None:
        args.output.write_text(encoded, encoding="utf-8")
    else:
        print(encoded, end="")
    print(json.dumps({"status": "compiled", "compiled_protocol_sha256": compiled["compiled_protocol_sha256"], "source_spec_sha256": compiled["source_spec_sha256"], "state_slice": STATE_SLICE}, sort_keys=True))


if __name__ == "__main__":
    main()
