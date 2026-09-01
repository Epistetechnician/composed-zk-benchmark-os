#!/usr/bin/env python3
"""Independent V8 protocol and runtime-receipt validator.

State slice: oaklab-experience-learning-h100-replication-v8.
The validator does not import the compiler or any learner/backend/provider
implementation. Runtime helpers are fail-closed and are exercised by tests.
"""

from __future__ import annotations

import sys

if __package__ in {None, ""} and sys.path:
    sys.path.pop(0)

import csv
import datetime as dt
import hashlib
import io
import json
import math
import re
import struct
from pathlib import Path
from typing import Any


STATE_SLICE = "oaklab-experience-learning-h100-replication-v8"
PROTOCOL_ID = "oaklab.h100.v8"
SOURCE_SCHEMA = "oaklab.experience-learning.h100-replication-v8.source.v1"
COMPILED_SCHEMA = "oaklab.experience-learning.h100-replication-v8.compiled.v1"
SOURCE = Path("experiments/experience_learning/oaklab_h100_v8_protocol.json")
COMPILED = Path("experiments/experience_learning/oaklab_h100_v8_compiled_protocol.json")
CAMPAIGN_MANIFEST_ARTIFACT = Path("experiments/experience_learning/oaklab_h100_v8_campaign_manifest.json")
REVIEW_PACKET = Path("docs/research/experience-learning/62-oaklab-h100-replication-v8-review-packet.md")
SECTIONS = (
    "hash_prng_transcript", "controller_transition_table", "generator_roster",
    "operation_and_byte_algebra", "ablation_execution_multiplicity",
    "adaptation_metrics", "lock_counter_control_schemas",
)
FREEZE_FILES = (
    str(SOURCE),
    "experiments/experience_learning/compile_oaklab_h100_v8_protocol.py",
    "experiments/experience_learning/validate_oaklab_h100_v8_protocol.py",
    "experiments/experience_learning/tests/test_oaklab_h100_v8_protocol.py",
    "AGENTS.md",
)
ROOT_ALLOWLIST = {
    "campaign_manifest.json", "compiled_protocol.json", "review/protocol_accept.json", "fit/lock.json", "tune/lock.json",
    "tune/lock_receipt.json", "provider/allocation.json", "provider/cost.json",
    "provider/stop.json", "energy/raw_trace.csv", "energy/joules.json", "result/counter_rows.json", "result/family_rows.json",
    "result/aggregate.json", "validation/independent.json",
}
HEX64 = re.compile(r"^[0-9a-f]{64}$")
UTC_SECONDS = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$")
MAX_PROVIDER_INTERVAL_SECONDS = 86400


def canonical(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False) + "\n").encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def digest(value: Any) -> str:
    return sha256_bytes(canonical(value))


def digest_without(value: dict[str, Any], *fields: str) -> str:
    return digest({key: item for key, item in value.items() if key not in set(fields)})


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _closed(value: Any, keys: set[str], label: str) -> None:
    require(isinstance(value, dict) and set(value) == keys, f"{label} object is not closed")


def validate_strict_contract(source: dict[str, Any]) -> None:
    contract = source["strict_contract"]
    _closed(contract, {"schema", "unknown_fields", "estimand", "controller", "generators", "operations", "statistics", "runtime"}, "strict_contract")
    require(contract["schema"] == "oaklab.h100.v8.strict-contract.v1" and contract["unknown_fields"] == "reject_at_every_object", "strict contract identity changed")
    e = source["estimand"]
    ec = contract["estimand"]
    _closed(ec, {"required_keys", "exact_values", "carryover_required_phrases"}, "strict_contract.estimand")
    require(set(e) == set(ec["required_keys"]) and {key: e[key] for key in ec["exact_values"]} == ec["exact_values"], "estimand nested contract changed")
    require(all(isinstance(item, str) and item in e["carryover_control"] for item in ec["carryover_required_phrases"]), "estimand carryover contract changed")

    c = source["controller_transition_table"]
    cc = contract["controller"]
    _closed(cc, {"state_tuple_arity", "state_names", "state_types", "state_scopes", "transition_indices", "transition_events", "transition_keys", "transition_reads_writes_rules", "recurrence_equations", "simultaneous_rhs_phrase", "terminal_phrase"}, "strict_contract.controller")
    require(cc["state_tuple_arity"] == 3 and [row[0] for row in c["state_fields"]] == cc["state_names"], "controller state names changed")
    require({row[0]: row[1] for row in c["state_fields"]} == cc["state_types"], "controller state types changed")
    require(set(cc["state_scopes"]) == {"fit_persistent", "trajectory", "pending"} and sorted(name for names in cc["state_scopes"].values() for name in names) == sorted(cc["state_names"]), "controller scope partition changed")
    require([row["index"] for row in c["rows"]] == cc["transition_indices"] and [row["event"] for row in c["rows"]] == cc["transition_events"], "controller transition order changed")
    for row in c["rows"]:
        _closed(row, set(cc["transition_keys"]), f"controller row {row.get('index')}")
        require(isinstance(row["reads"], list) and isinstance(row["writes"], list) and all(isinstance(item, str) and item for item in row["reads"] + row["writes"]), "controller read/write schema changed")
        require({key: row[key] for key in ("reads", "writes", "rule")} == cc["transition_reads_writes_rules"][str(row["index"])], f"controller row {row['index']} semantics changed")
    require(c["recurrence"] == [f"{key}={cc['recurrence_equations'][key]}" for key in ("delta", "eligibility_new", "theta_new", "dual_mu_new", "q_old_new")] and c["rhs_rule"] == cc["simultaneous_rhs_phrase"] and cc["terminal_phrase"] in c["terminal_rule"], "controller recurrence changed")

    roster = source["generator_roster"]
    gc = contract["generators"]
    _closed(gc, {"stream_ids", "stream_required_keys", "draw_tuple_arity", "draw_ordinals", "draw_repeats", "row_count", "segment_rules", "no_future_or_redraw_phrase", "stream_semantics"}, "strict_contract.generators")
    require(roster["stream_order"] == gc["stream_ids"] and set(roster["streams"]) == set(gc["stream_ids"]) and set(roster["draw_roster"]) == set(gc["stream_ids"]), "generator identity changed")
    require(gc["row_count"] == roster["rows_per_trajectory"] and gc["draw_tuple_arity"] == 4 and gc["draw_ordinals"] == "exact_contiguous_zero_based" and gc["draw_repeats"] == "positive_integer_unconditional", "generator draw contract changed")
    for stream_id in gc["stream_ids"]:
        stream = roster["streams"][stream_id]
        _closed(stream, set(gc["stream_required_keys"]), f"{stream_id} stream")
        require({key: stream[key] for key in ("equation", "draw_order", "events", "oracle_features")} == gc["stream_semantics"][stream_id], f"{stream_id} stream semantics changed")
        segments = stream["segments"]
        require(isinstance(segments, list) and segments[0] == 0 and segments[-1] == gc["row_count"] and all(isinstance(v, int) for v in segments) and all(left < right for left, right in zip(segments, segments[1:])), f"{stream_id} segment contract changed")
        draws = roster["draw_roster"][stream_id]
        require(all(isinstance(row, list) and len(row) == gc["draw_tuple_arity"] for row in draws) and [row[0] for row in draws] == list(range(len(draws))) and all(isinstance(row[3], int) and row[3] > 0 for row in draws), f"{stream_id} draw contract changed")
    require(gc["no_future_or_redraw_phrase"] in roster["draw_rule"], "generator future/redraw boundary changed")

    algebra = source["operation_and_byte_algebra"]
    oc = contract["operations"]
    _closed(oc, {"required_ast_names", "ast_node_keys", "numeric_rules_exact", "byte_layout_required", "resource_separation_phrase", "allowed_ast_ops", "byte_field_tuple_arity", "byte_offsets_rule"}, "strict_contract.operations")
    require(set(algebra["formula_ast"]) == set(oc["required_ast_names"]) and algebra["numeric_rules"] == oc["numeric_rules_exact"], "operation contract changed")
    def check_ast(node: Any) -> None:
        require(isinstance(node, dict) and set(node) == set(oc["ast_node_keys"]) and node["op"] in oc["allowed_ast_ops"] and isinstance(node["args"], list), "numeric AST is not closed")
        for arg in node["args"]:
            check_ast(arg) if isinstance(arg, dict) else require(isinstance(arg, (str, int, float)) and not isinstance(arg, bool), "numeric AST literal invalid")
    for node in algebra["formula_ast"].values():
        check_ast(node["ast"])
    require(all(name in algebra["byte_layouts"] for name in oc["byte_layout_required"]) and oc["resource_separation_phrase"] in algebra["resource_invariants"], "operation byte/resource contract changed")
    for layout_name in oc["byte_layout_required"]:
        layout = algebra["byte_layouts"][layout_name]
        require(layout["alignment"] == "none" and all(isinstance(field, list) and len(field) == oc["byte_field_tuple_arity"] and ((isinstance(field[2], int) and field[2] >= 0) or (isinstance(field[2], str) and field[2] in {"8*dimension"})) and isinstance(field[3], (int, str)) and field[3] for field in layout["fields"]), f"{layout_name}: byte field schema changed")

    stats = contract["statistics"]
    _closed(stats, {"families_required", "holm", "raw_rows_required", "caller_supplied_gate_booleans_forbidden", "adaptation_shift_scan_forbidden"}, "strict_contract.statistics")
    require(stats["families_required"] == ["predictable_noise", "drift", "delayed_reward", "event", "long_horizon", "null"] and set(roster["family_map"]) == set(stats["families_required"]) and stats["raw_rows_required"] is True and stats["caller_supplied_gate_booleans_forbidden"] is True and stats["adaptation_shift_scan_forbidden"] is True and stats["holm"] == source["ablation_execution_multiplicity"]["holm_groups"][0]["adjustment"], "statistics derivation contract changed")

    runtime = contract["runtime"]
    _closed(runtime, {"provider_currency", "provider_max_interval_seconds", "provider_cross_binding_fields", "counter_derived_fields", "assessment_order", "authorization_revalidates_current_packet", "historical_isolation"}, "strict_contract.runtime")
    require(runtime["provider_currency"] == "USD" and runtime["provider_max_interval_seconds"] == 86400 and runtime["authorization_revalidates_current_packet"] is True and runtime["historical_isolation"] == ["phase_836", "oaklab_v6", "plasticity_guard", "astral"], "runtime contract changed")
    require(runtime["provider_cross_binding_fields"] == ["manifest_core_sha256", "allocation_id", "node_id", "public_key_hex", "hard_usd_ceiling", "campaign_manifest_path", "source_sha256", "compiler_sha256", "validator_sha256", "compiled_protocol_sha256", "review_packet_sha256"], "runtime campaign binding fields changed")


def require_hex(value: Any, name: str) -> str:
    require(isinstance(value, str) and HEX64.fullmatch(value) is not None, f"{name} must be lowercase SHA-256 hex")
    return value


def load_canonical_json(path: Path) -> dict[str, Any]:
    require(path.is_file() and not path.is_symlink(), f"missing or symlinked JSON: {path}")
    raw = path.read_bytes()
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError(f"invalid JSON: {path}") from error
    require(isinstance(value, dict), f"JSON object required: {path}")
    require(raw == canonical(value), f"noncanonical JSON bytes: {path}")
    return value


def lp32(payload: bytes) -> bytes:
    require(len(payload) <= 0xFFFFFFFF, "LP32 payload too large")
    return struct.pack(">I", len(payload)) + payload


def splitmix64(seed_bytes: bytes, count: int) -> list[int]:
    state = int.from_bytes(seed_bytes[:8], "little")
    values: list[int] = []
    for _ in range(count):
        state = (state + 0x9E3779B97F4A7C15) & 0xFFFFFFFFFFFFFFFF
        z = state
        z = ((z ^ (z >> 30)) * 0xBF58476D1CE4E5B9) & 0xFFFFFFFFFFFFFFFF
        z = ((z ^ (z >> 27)) * 0x94D049BB133111EB) & 0xFFFFFFFFFFFFFFFF
        values.append((z ^ (z >> 31)) & 0xFFFFFFFFFFFFFFFF)
    return values


def transcript_vector(source_digest: str, source: dict[str, Any]) -> dict[str, Any]:
    protocol_raw = bytes.fromhex(source_digest)
    cohort = b"fit"
    stream = b"sparse_signal_v8"
    seed = 4000
    row = 0
    frame = lp32(b"oaklab.h100.v8.prng.v1") + protocol_raw + lp32(cohort) + lp32(stream) + struct.pack("<Q", seed) + struct.pack("<I", row)
    root = hashlib.sha256(frame).digest()
    raw = splitmix64(root, 13)
    action_seed = bytes.fromhex(source["hash_prng_transcript"]["action_assignment"]["action_seed_hex"])
    action_frame = lp32(b"oaklab.h100.v8.action.v1") + protocol_raw + action_seed + lp32(cohort) + lp32(stream) + struct.pack("<Q", seed) + struct.pack("<I", row)
    return {
        "frame_hex": frame.hex(), "root_sha256": root.hex(),
        "initial_state_uint64_le": int.from_bytes(root[:8], "little"),
        "first_12_raw_uint64_hex": [f"{value:016x}" for value in raw[:12]],
        "first_uniform53": (raw[0] >> 11) / float(1 << 53),
        "first_normal12": sum((value >> 11) / float(1 << 53) for value in raw[1:13]) - 6.0,
        "action_hash_sha256": hashlib.sha256(action_frame).hexdigest(),
    }


def validate_campaign_manifest_contract(source: dict[str, Any]) -> None:
    artifact = source["campaign_manifest_artifact"]
    require(set(artifact) == {"schema", "path", "materialization", "runtime_manifest_required", "result_root_required", "validation", "required_bindings", "digest_rule"}, "campaign manifest artifact contract is not closed")
    require(artifact["schema"] == "oaklab.h100.v8.campaign-manifest-artifact.v1", "campaign manifest artifact identity changed")
    require(artifact["path"] == str(CAMPAIGN_MANIFEST_ARTIFACT), "campaign manifest artifact path changed")
    require(artifact["materialization"] == "declared_pre_execution" and artifact["runtime_manifest_required"] is True and artifact["result_root_required"] is True, "campaign manifest materialization boundary changed")
    require(artifact["validation"] == "validate_campaign_manifest_artifact(path, current_source_sha256, current_compiled_file_sha256, current_review_packet_sha256)", "campaign manifest validator binding changed")
    required = artifact["required_bindings"]
    require(isinstance(required, list) and len(required) == len(set(required)) and set(required) == {"source_sha256", "compiler_sha256", "validator_sha256", "tests_sha256", "agents_sha256", "compiled_protocol_file_sha256", "review_packet_sha256", "backend_sha256", "guard_sha256", "model_sha256", "data_sha256", "fit_lock_sha256", "tune_lock_sha256", "tune_lock_receipt_sha256", "provider_allocation_sha256", "provider_cost_sha256", "provider_stop_sha256", "energy_receipt_sha256", "result_root_sha256", "hard_usd_ceiling"}, "campaign manifest binding roster changed")
    require(artifact["digest_rule"] == "manifest_sha256 is SHA-256 of canonical JSON excluding only manifest_sha256", "campaign manifest digest rule changed")


def validate_source(source: dict[str, Any]) -> None:
    expected = {"schema_version", "protocol_id", "state_slice", "claim_ceiling", "status", "implementation_before_review", "estimand", *SECTIONS, "strict_contract", "stop_rules", "boundaries", "campaign_manifest_artifact"}
    require(set(source) == expected, "source schema is not closed")
    require(source["schema_version"] == SOURCE_SCHEMA and source["protocol_id"] == PROTOCOL_ID and source["state_slice"] == STATE_SLICE, "source identity mismatch")
    require(source["status"] == "frozen_pending_independent_review" and source["implementation_before_review"] is False, "implementation boundary is open")
    validate_campaign_manifest_contract(source)
    e = source["estimand"]
    require(e["control"] == "fixed_sgd_b1" and e["treatment"] == "lagged_selective_credit", "estimand arms mismatch")
    require(e["same_stream"] is True and e["same_initial_checkpoint"] is True and e["arm_order_randomized"] is True, "paired trajectory controls missing")
    require(e["primary_endpoint"] == "mean_e_mean_b(loss_treatment[e,b]-loss_control[e,b])" and e["assessment_absent_until_lock"] is True, "estimand contract mismatch")
    require("previous block only" in e["carryover_control"] and "before_row_action" in e["loss_timing"], "carryover or loss timing is open")
    validate_strict_contract(source)

    h = source["hash_prng_transcript"]
    require("no conditional draws" in h["draw_policy"] and "no redraws" in h["draw_policy"], "draw policy is open")
    require(h["action_assignment"]["probability"] == {"p_num": 1, "p_den": 4}, "action probability mismatch")
    require(h["action_assignment"]["fit_only"] is True and len(h["action_assignment"]["action_seed_hex"]) == 64, "action assignment boundary mismatch")

    c = source["controller_transition_table"]
    require([row["index"] for row in c["rows"]] == list(range(8)), "controller indices are not contiguous")
    require([row["event"] for row in c["rows"]] == ["trajectory_init", "observe_pre_action", "credit_previous", "select_action", "model_action", "publish_pending", "terminal_credit", "counter_finalize"], "controller order mismatch")
    names = [row[0] for row in c["state_fields"]]
    require(len(names) == 20 and len(names) == len(set(names)), "controller state roster mismatch")
    require({"pending_valid", "pending_features", "pending_prediction", "pending_loss", "pending_event_count", "pending_action", "pending_cost", "pending_reward", "pending_local_row", "pending_terminal"}.issubset(names), "pending state incomplete")
    require("pre-transition snapshot" in c["rhs_rule"] and "undeclared carryover" in c["rows"][5]["rule"], "controller recurrence not closed")
    require("no model action" in c["terminal_rule"], "terminal action boundary missing")

    roster = source["generator_roster"]
    expected_streams = {"sparse_signal_v8", "drifting_relevance_v8", "delayed_reward_v8", "event_sensor_v8", "long_horizon_v8", "pure_noise_v8"}
    require(set(roster["stream_order"]) == expected_streams and set(roster["streams"]) == expected_streams and set(roster["draw_roster"]) == expected_streams, "generator roster mismatch")
    for stream_id, draws in roster["draw_roster"].items():
        require([row[0] for row in draws] == list(range(len(draws))), f"{stream_id}: draw ordinal mismatch")
        require(all(isinstance(row[3], int) and row[3] > 0 for row in draws), f"{stream_id}: conditional draw")
    for stream_id, stream in roster["streams"].items():
        require(stream["segments"][0] == 0 and stream["segments"][-1] == 256, f"{stream_id}: segment bounds mismatch")
        require(all(isinstance(stream[field], str) and stream[field] for field in ("equation", "draw_order", "events")), f"{stream_id}: semantics incomplete")
    require("redraw is forbidden" in roster["draw_rule"], "redraw rule missing")

    algebra = source["operation_and_byte_algebra"]
    require("no fused multiply-add" in algebra["numeric_rules"] and "left-to-right" in algebra["numeric_rules"], "numeric rules incomplete")
    require(set(algebra["formula_ast"]) == {"forward_dense", "loss_half_squared", "gradient", "model_update", "controller_dot", "event_count"}, "formula AST mismatch")
    for name in ("model_state", "counter_row", "lock_receipt"):
        layout = algebra["byte_layouts"][name]
        require(layout["alignment"] == "none" and layout["fields"] and layout["bytes"], f"{name}: byte layout incomplete")
    require("joules remain absent" in " ".join(algebra["resource_invariants"]), "energy separation missing")

    a = source["ablation_execution_multiplicity"]
    require(len(a["arm_order"]) == 8 and set(a["execution_matrix"]) == set(a["arm_order"]), "ablation set mismatch")
    require(all(set(phases) == {"fit", "tune", "assessment"} for phases in a["execution_matrix"].values()), "ablation phases incomplete")
    require("no tune-derived probability" in a["matched_random_rule"], "matched-random lock missing")
    require(len(a["holm_groups"]) == 3 and all("sort raw p" in group["adjustment"] for group in a["holm_groups"]), "Holm groups incomplete")
    require("cannot be imputed" in a["missing_rules"] and len(a["gate_predicates"]) >= 5, "missing/gate rules incomplete")

    m = source["adaptation_metrics"]
    require("[k,k+8)" in m["recovery_scan"] and "[k+8,k+16)" in m["recovery_scan"] and "never scan across shifts" in m["aggregation"], "adaptation metric not shift bounded")

    schemas = source["lock_counter_control_schemas"]
    required_schemas = {"fit_lock", "tune_lock", "lock_receipt", "counter_row", "review_accept", "family_rows", "campaign_manifest", "provider_receipts", "energy_receipt", "result_root", "independent_validation", "assessment_absence"}
    require(set(schemas) == required_schemas | {"schema_policy"}, "runtime schema roster is not closed")
    for name in ("fit_lock", "tune_lock", "lock_receipt", "counter_row", "campaign_manifest"):
        fields = schemas[name]["fields"]
        require(fields and len(fields) == len(set(fields)), f"{name}: duplicate or missing fields")
    require(schemas["campaign_manifest"]["core_digest_scope"] == ["schema", "state_slice", "source_sha256", "compiler_sha256", "validator_sha256", "tests_sha256", "agents_sha256", "campaign_manifest_artifact_sha256", "compiled_protocol_sha256", "protocol_review_sha256", "review_packet_sha256", "code_sha256", "model_sha256", "data_sha256", "backend_sha256", "guard_sha256", "hard_usd_ceiling"], "campaign core digest scope changed")
    root = schemas["result_root"]
    require(root["mode"] == "closed_world" and root["reject_extra_paths"] is True and root["validate_all_content"] is True and root["validate_all_bindings"] is True, "result-root contract is open")
    provider = schemas["provider_receipts"]
    require(provider["signature"].startswith("Ed25519") and "same allocation_id" in provider["cross_binding"], "provider receipt contract incomplete")
    energy = schemas["energy_receipt"]
    require(energy["formula"].startswith("sum(0.5") and "successfully_learned_events" in energy["denominator"], "energy contract incomplete")
    absence = schemas["assessment_absence"]
    require(absence["materialization_state"] == "absent" and absence["entry_count"] == 0, "assessment absence changed")
    require(schemas["independent_validation"]["manifest_binding"] == "manifest_core_sha256", "independent manifest binding changed")
    require(isinstance(source["stop_rules"], list) and len(source["stop_rules"]) >= 9, "stop rules incomplete")
    require(source["boundaries"]["phase_836"] == "closed_historical_only" and source["boundaries"]["oaklab_v6"] == "closed_historical_only" and source["boundaries"]["astral"] == "isolated_and_blocked", "historical lane boundary changed")


def validate_compiled(repo_root: Path = Path.cwd()) -> dict[str, Any]:
    source_path = repo_root / SOURCE
    source_bytes = source_path.read_bytes()
    source = json.loads(source_bytes.decode("utf-8"))
    require(isinstance(source, dict), "source must be an object")
    require(source_bytes == canonical(source), "source bytes must be canonical JSON")
    validate_source(source)
    compiled_path = repo_root / COMPILED
    compiled = load_canonical_json(compiled_path)
    required = {"schema_version", "protocol_id", "state_slice", "claim_ceiling", "compiler_version", "source_spec_sha256", "freeze_file_sha256", "sections", "section_digests", "transcript_test_vector", "assessment_materialization_state", "compiled", "strict_contract", "estimand", "stop_rules", "boundaries", "campaign_manifest_artifact", "execution_gate", "compiled_protocol_sha256"}
    require(set(compiled) == required, "compiled schema is not closed")
    require(compiled["schema_version"] == COMPILED_SCHEMA and compiled["protocol_id"] == PROTOCOL_ID and compiled["state_slice"] == STATE_SLICE, "compiled identity mismatch")
    require(compiled["source_spec_sha256"] == sha256_bytes(source_bytes), "source digest mismatch")
    require(compiled["sections"] == list(SECTIONS) and compiled["compiled"] == {name: source[name] for name in SECTIONS} and compiled["strict_contract"] == source["strict_contract"] and compiled["campaign_manifest_artifact"] == source["campaign_manifest_artifact"], "compiled section mismatch")
    require(compiled["section_digests"] == {name: digest(source[name]) for name in SECTIONS}, "section digest mismatch")
    require(compiled["transcript_test_vector"] == transcript_vector(compiled["source_spec_sha256"], source), "PRNG transcript mismatch")
    require(compiled["assessment_materialization_state"] == "absent", "assessment materialized")
    require(compiled["estimand"] == source["estimand"] and compiled["stop_rules"] == source["stop_rules"] and compiled["boundaries"] == source["boundaries"], "compiled metadata mismatch")
    require(compiled["execution_gate"] == {"review_accept_required": True, "packet_binding_required": True, "full_validation_required": True, "synthetic_candidate_required": True, "zero_spend_preflight_required": True, "provider_allocation_required": True, "campaign_manifest_artifact_required": True, "actual_campaign_manifest_path_required": True, "one_bounded_job_maximum": True, "assessment_absent": True, "effects_run": False}, "execution gate changed")
    require(compiled["compiled"]["lock_counter_control_schemas"]["result_root"]["allowlist"] == ["campaign_manifest.json", "compiled_protocol.json", "review/protocol_accept.json", "fit/lock.json", "tune/lock.json", "tune/lock_receipt.json", "provider/allocation.json", "provider/cost.json", "provider/stop.json", "energy/raw_trace.csv", "energy/joules.json", "result/counter_rows.json", "result/family_rows.json", "result/aggregate.json", "validation/independent.json"], "compiled result-root allowlist changed")
    freeze = compiled["freeze_file_sha256"]
    require(isinstance(freeze, dict) and set(freeze) == set(FREEZE_FILES), "freeze roster mismatch")
    for relative, expected in freeze.items():
        require_hex(expected, f"freeze digest {relative}")
        path = repo_root / relative
        require(path.is_file() and not path.is_symlink() and sha256_file(path) == expected, f"freeze digest mismatch: {relative}")
    require(compiled["compiled_protocol_sha256"] == digest_without(compiled, "compiled_protocol_sha256"), "compiled self-digest mismatch")
    return compiled


def validate_campaign_manifest(path: Path, compiled_sha256: str) -> dict[str, Any]:
    value = load_canonical_json(path)
    keys = {"schema", "state_slice", "source_sha256", "compiler_sha256", "validator_sha256", "tests_sha256", "agents_sha256", "campaign_manifest_artifact_sha256", "compiled_protocol_sha256", "protocol_review_sha256", "review_packet_sha256", "code_sha256", "model_sha256", "data_sha256", "backend_sha256", "guard_sha256", "fit_lock_sha256", "tune_lock_sha256", "tune_lock_receipt_sha256", "provider_allocation_sha256", "provider_cost_sha256", "provider_stop_sha256", "energy_receipt_sha256", "result_root_sha256", "hard_usd_ceiling", "manifest_core_sha256", "manifest_sha256"}
    require(set(value) == keys and value["schema"] == "oaklab.h100.v8.campaign.v1" and value["state_slice"] == STATE_SLICE, "campaign manifest schema is not closed")
    require(value["compiled_protocol_sha256"] == compiled_sha256, "campaign compiled binding mismatch")
    for key, item in value.items():
        if key.endswith("_sha256") and key != "manifest_sha256":
            require_hex(item, key)
    ceiling = value["hard_usd_ceiling"]
    require(isinstance(ceiling, (int, float)) and not isinstance(ceiling, bool) and math.isfinite(float(ceiling)) and ceiling > 0, "hard USD ceiling invalid")
    core_keys = ("schema", "state_slice", "source_sha256", "compiler_sha256", "validator_sha256", "tests_sha256", "agents_sha256", "campaign_manifest_artifact_sha256", "compiled_protocol_sha256", "protocol_review_sha256", "review_packet_sha256", "code_sha256", "model_sha256", "data_sha256", "backend_sha256", "guard_sha256", "hard_usd_ceiling")
    require(value["manifest_core_sha256"] == digest({key: value[key] for key in core_keys}), "campaign core digest mismatch")
    require(value["manifest_sha256"] == digest_without(value, "manifest_sha256"), "campaign self-digest mismatch")
    return value


def validate_campaign_manifest_artifact(path: Path, current_source_sha256: str, current_compiled_file_sha256: str, current_review_packet_sha256: str, repo_root: Path = Path.cwd()) -> dict[str, Any]:
    value = load_canonical_json(path)
    expected = {"schema", "state_slice", "materialization", "runtime_manifest_required", "result_root_required", "source_sha256", "compiler_sha256", "validator_sha256", "tests_sha256", "agents_sha256", "compiled_protocol_file_sha256", "review_packet_sha256", "backend_sha256", "guard_sha256", "model_sha256", "data_sha256", "hard_usd_ceiling", "manifest_sha256"}
    require(set(value) == expected and value["schema"] == "oaklab.h100.v8.campaign-manifest-artifact.v1" and value["state_slice"] == STATE_SLICE, "campaign manifest artifact schema is not closed")
    require(value["materialization"] == "declared_pre_execution" and value["runtime_manifest_required"] is True and value["result_root_required"] is True, "campaign manifest artifact execution boundary is open")
    require(value["source_sha256"] == current_source_sha256 and value["compiled_protocol_file_sha256"] == current_compiled_file_sha256 and value["review_packet_sha256"] == current_review_packet_sha256, "campaign manifest artifact current binding mismatch")
    expected_files = {
        "compiler_sha256": repo_root / "experiments/experience_learning/compile_oaklab_h100_v8_protocol.py",
        "validator_sha256": repo_root / "experiments/experience_learning/validate_oaklab_h100_v8_protocol.py",
        "tests_sha256": repo_root / "experiments/experience_learning/tests/test_oaklab_h100_v8_protocol.py",
        "agents_sha256": repo_root / "AGENTS.md",
    }
    for key, file_path in expected_files.items():
        require(value[key] == sha256_file(file_path), f"campaign manifest artifact {key} binding mismatch")
    for key in ("backend_sha256", "guard_sha256", "model_sha256", "data_sha256"):
        require_hex(value[key], f"campaign manifest artifact {key}")
    require(isinstance(value["hard_usd_ceiling"], (int, float)) and not isinstance(value["hard_usd_ceiling"], bool) and math.isfinite(float(value["hard_usd_ceiling"])) and value["hard_usd_ceiling"] > 0, "campaign manifest artifact USD ceiling invalid")
    require(value["manifest_sha256"] == digest_without(value, "manifest_sha256"), "campaign manifest artifact self-digest mismatch")
    return value


def _valid_utc(value: Any, label: str) -> dt.datetime:
    require(isinstance(value, str) and UTC_SECONDS.fullmatch(value) is not None, f"{label} timestamp invalid")
    try:
        return dt.datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=dt.timezone.utc)
    except ValueError as error:
        raise ValueError(f"{label} timestamp invalid") from error


# Minimal RFC 8032 Ed25519 verifier. This avoids trusting a provider library.
_Q = 2**255 - 19
_L = 2**252 + 27742317777372353535851937790883648493
_D = (-121665 * pow(121666, _Q - 2, _Q)) % _Q
_I = pow(2, (_Q - 1) // 4, _Q)


def _xrecover(y: int) -> int:
    xx = (y * y - 1) * pow(_D * y * y + 1, _Q - 2, _Q) % _Q
    x = pow(xx, (_Q + 3) // 8, _Q)
    if (x * x - xx) % _Q:
        x = (x * _I) % _Q
    if x & 1:
        x = _Q - x
    return x


def _decodepoint(data: bytes) -> tuple[int, int]:
    require(len(data) == 32, "Ed25519 point length invalid")
    y = int.from_bytes(data, "little") & ((1 << 255) - 1)
    x = _xrecover(y)
    if (x & 1) != (data[31] >> 7):
        x = _Q - x
    require(((-x * x + y * y - 1 - _D * x * x * y * y) % _Q) == 0, "Ed25519 point invalid")
    return x, y


def _encodepoint(point: tuple[int, int]) -> bytes:
    x, y = point
    return ((y | ((x & 1) << 255)) % (1 << 256)).to_bytes(32, "little")


def _ed_add(left: tuple[int, int], right: tuple[int, int]) -> tuple[int, int]:
    x1, y1 = left
    x2, y2 = right
    product = (_D * x1 * x2 * y1 * y2) % _Q
    x3 = (x1 * y2 + x2 * y1) * pow(1 + product, _Q - 2, _Q) % _Q
    y3 = (y1 * y2 + x1 * x2) * pow(1 - product, _Q - 2, _Q) % _Q
    return x3, y3


def _ed_scalarmult(point: tuple[int, int], scalar: int) -> tuple[int, int]:
    result = (0, 1)
    addend = point
    while scalar:
        if scalar & 1:
            result = _ed_add(result, addend)
        addend = _ed_add(addend, addend)
        scalar >>= 1
    return result


_BASE = (_xrecover(4 * pow(5, _Q - 2, _Q) % _Q), 4 * pow(5, _Q - 2, _Q) % _Q)


def verify_ed25519(public_key: bytes, signature: bytes, message: bytes) -> bool:
    try:
        require(len(public_key) == 32 and len(signature) == 64, "Ed25519 encoding invalid")
        r_point = _decodepoint(signature[:32])
        a_point = _decodepoint(public_key)
        scalar = int.from_bytes(signature[32:], "little")
        require(scalar < _L, "Ed25519 scalar out of range")
        challenge = int.from_bytes(hashlib.sha512(signature[:32] + public_key + message).digest(), "little") % _L
        return _encodepoint(_ed_scalarmult(_BASE, scalar)) == _encodepoint(_ed_add(r_point, _ed_scalarmult(a_point, challenge)))
    except (ValueError, OverflowError):
        return False


def validate_protocol_accept(path: Path, packet_sha256: str, source_sha256: str, compiled_sha256: str) -> dict[str, Any]:
    value = load_canonical_json(path)
    expected = {"schema", "state_slice", "packet_sha256", "source_sha256", "compiled_sha256", "reviewer", "review_decision", "effects_run", "findings", "reviewed_at_utc", "receipt_sha256", "signature_hex", "public_key_hex"}
    require(set(value) == expected and value["schema"] == "oaklab.h100.v8.protocol-review.v1" and value["state_slice"] == STATE_SLICE, "protocol review schema is not closed")
    require(value["packet_sha256"] == packet_sha256 and value["source_sha256"] == source_sha256 and value["compiled_sha256"] == compiled_sha256, "protocol review digest binding mismatch")
    require(isinstance(value["reviewer"], str) and value["reviewer"] and value["review_decision"] == "ACCEPT" and value["effects_run"] is False and isinstance(value["findings"], dict) and value["findings"] and all(item is True for item in value["findings"].values()), "independent protocol ACCEPT is absent")
    _valid_utc(value["reviewed_at_utc"], "protocol review")
    key_hex = value["public_key_hex"]; sig_hex = value["signature_hex"]
    require(isinstance(key_hex, str) and re.fullmatch(r"[0-9a-f]{64}", key_hex) and isinstance(sig_hex, str) and re.fullmatch(r"[0-9a-f]{128}", sig_hex), "protocol review signature encoding invalid")
    body = {key: item for key, item in value.items() if key not in {"signature_hex", "receipt_sha256"}}
    require(value["receipt_sha256"] == digest(body) and verify_ed25519(bytes.fromhex(key_hex), bytes.fromhex(sig_hex), canonical(body)), "protocol review signature invalid")
    return value


def _signed_provider(path: Path, schema: str, manifest_sha256: str, expected_keys: set[str]) -> dict[str, Any]:
    value = load_canonical_json(path)
    require(set(value) == expected_keys and value["schema"] == schema and value["state_slice"] == STATE_SLICE, f"provider schema is not closed: {path}")
    require_hex(value["launch_manifest_sha256"], "launch_manifest_sha256")
    require(value["launch_manifest_sha256"] == manifest_sha256, f"provider launch binding mismatch: {path}")
    key_hex = value.get("public_key_hex")
    sig_hex = value.get("signature_hex")
    require(isinstance(key_hex, str) and re.fullmatch(r"[0-9a-f]{64}", key_hex) is not None, "provider public key encoding invalid")
    require(isinstance(sig_hex, str) and re.fullmatch(r"[0-9a-f]{128}", sig_hex) is not None, "provider signature encoding invalid")
    message_body = {key: item for key, item in value.items() if key not in {"signature_hex", "receipt_sha256"}}
    require(value["receipt_sha256"] == digest(message_body), f"provider receipt self-digest mismatch: {path}")
    require(verify_ed25519(bytes.fromhex(key_hex), bytes.fromhex(sig_hex), canonical(message_body)), f"provider signature invalid: {path}")
    return value


def validate_provider_receipts(root: Path, manifest: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    allocation = _signed_provider(root / "provider/allocation.json", "oaklab.h100.v8.provider-allocation.v1", manifest["manifest_core_sha256"], {"schema", "state_slice", "allocation_id", "node_id", "provider", "gpu_model", "start_utc", "hard_usd_ceiling", "launch_manifest_sha256", "public_key_hex", "signature_hex", "receipt_sha256"})
    cost = _signed_provider(root / "provider/cost.json", "oaklab.h100.v8.provider-cost.v1", manifest["manifest_core_sha256"], {"schema", "state_slice", "allocation_id", "node_id", "charged_usd", "currency", "hard_usd_ceiling", "launch_manifest_sha256", "public_key_hex", "signature_hex", "receipt_sha256"})
    stop = _signed_provider(root / "provider/stop.json", "oaklab.h100.v8.provider-stop.v1", manifest["manifest_core_sha256"], {"schema", "state_slice", "allocation_id", "node_id", "start_utc", "stop_utc", "stop_reason", "launch_manifest_sha256", "public_key_hex", "signature_hex", "receipt_sha256"})
    for value in (cost, stop):
        require(value["allocation_id"] == allocation["allocation_id"] and value["node_id"] == allocation["node_id"] and value["public_key_hex"] == allocation["public_key_hex"], "provider allocation/node/key cross-binding mismatch")
        require(value["launch_manifest_sha256"] == allocation["launch_manifest_sha256"], "provider manifest cross-binding mismatch")
    require(allocation["node_id"] and allocation["provider"] == "givemeanode" and allocation["gpu_model"] == "H100", "provider allocation identity invalid")
    start = _valid_utc(allocation["start_utc"], "provider start")
    require(stop["start_utc"] == allocation["start_utc"], "provider start timestamp cross-binding mismatch")
    stop_time = _valid_utc(stop["stop_utc"], "provider stop")
    require(stop_time >= start and (stop_time - start).total_seconds() <= MAX_PROVIDER_INTERVAL_SECONDS, "provider interval is outside bounded window")
    ceiling = manifest["hard_usd_ceiling"]
    require(all(value["hard_usd_ceiling"] == ceiling for value in (allocation, cost)) and isinstance(cost["charged_usd"], (int, float)) and not isinstance(cost["charged_usd"], bool), "provider hard USD ceiling cross-binding invalid")
    require(cost["currency"] == "USD", "provider cost currency must be USD")
    require(math.isfinite(float(cost["charged_usd"])) and cost["charged_usd"] >= 0 and cost["charged_usd"] <= ceiling, "provider cost exceeds hard ceiling")
    require(allocation["allocation_id"] and stop["stop_reason"], "provider allocation/stop fields empty")
    return allocation, cost, stop


def validate_fit_lock(path: Path, compiled_sha256: str, review_receipt_sha256: str) -> dict[str, Any]:
    value = load_canonical_json(path)
    expected = {"schema", "state_slice", "protocol_sha256", "review_receipt_sha256", "implementation_sha256", "runtime_sha256", "generator_sha256", "fit_data_sha256", "selected_controller_sha256", "theta_hex", "fit_result_sha256", "decision", "lock_sha256"}
    require(set(value) == expected and value["schema"] == "oaklab.h100.v8.fit-lock.v1" and value["state_slice"] == STATE_SLICE, "fit lock schema is not closed")
    require(value["protocol_sha256"] == compiled_sha256 and value["review_receipt_sha256"] == review_receipt_sha256, "fit lock protocol/review binding mismatch")
    for key in expected:
        if key.endswith("_sha256") and key != "lock_sha256":
            require_hex(value[key], key)
    require(isinstance(value["theta_hex"], str) and len(value["theta_hex"]) == 64, "fit theta encoding invalid")
    require(value["decision"] == "locked" and value["lock_sha256"] == digest_without(value, "lock_sha256"), "fit lock decision or digest invalid")
    return value


def validate_tune_lock(path: Path, fit_lock_sha256: str) -> dict[str, Any]:
    value = load_canonical_json(path)
    expected = {"schema", "state_slice", "fit_lock_sha256", "tune_data_sha256", "hyperparameters_sha256", "prediction_sha256", "prediction_lock_sha256", "prediction_locked_at_utc", "assessment_started", "tune_result_sha256", "decision", "lock_sha256"}
    require(set(value) == expected and value["schema"] == "oaklab.h100.v8.tune-lock.v1" and value["state_slice"] == STATE_SLICE, "tune lock schema is not closed")
    require(value["fit_lock_sha256"] == fit_lock_sha256, "tune lock fit binding mismatch")
    for key in expected:
        if key.endswith("_sha256") and key != "lock_sha256":
            require_hex(value[key], key)
    require(value["decision"] == "locked" and value["assessment_started"] is False and value["prediction_lock_sha256"] == value["prediction_sha256"] and isinstance(value["prediction_locked_at_utc"], str), "tune prediction lock ordering invalid")
    _valid_utc(value["prediction_locked_at_utc"], "prediction lock")
    require(value["lock_sha256"] == digest_without(value, "lock_sha256"), "tune lock decision or digest invalid")
    return value


def validate_lock_receipt(path: Path, tune_lock_sha256: str, review_receipt_sha256: str) -> dict[str, Any]:
    value = load_canonical_json(path)
    expected = {"schema", "state_slice", "tune_lock_sha256", "review_receipt_sha256", "independent_reviewer", "prediction_lock_sha256", "prediction_locked_before_assessment", "decision", "receipt_sha256"}
    require(set(value) == expected and value["schema"] == "oaklab.h100.v8.lock-receipt.v1" and value["state_slice"] == STATE_SLICE, "lock receipt schema is not closed")
    require(value["tune_lock_sha256"] == tune_lock_sha256 and value["review_receipt_sha256"] == review_receipt_sha256 and isinstance(value["independent_reviewer"], str) and value["independent_reviewer"], "lock receipt binding invalid")
    require(value["decision"] == "accepted" and value["prediction_locked_before_assessment"] is True and require_hex(value["prediction_lock_sha256"], "prediction lock"), "lock receipt ordering or decision invalid")
    require(value["receipt_sha256"] == digest_without(value, "receipt_sha256"), "lock receipt decision or digest invalid")
    return value


def validate_energy_trace(path: Path) -> tuple[list[tuple[int, float]], str]:
    require(path.is_file() and not path.is_symlink(), "energy trace missing or symlinked")
    raw = path.read_bytes()
    require(raw.startswith(b"utc_ns,watts\n"), "energy trace header invalid")
    rows: list[tuple[int, float]] = []
    previous = -1
    for line in raw[len(b"utc_ns,watts\n"):].splitlines():
        fields = line.decode("utf-8").split(",")
        require(len(fields) == 2, "energy trace row has extra fields")
        try:
            timestamp = int(fields[0])
            watts = float(fields[1])
        except ValueError as error:
            raise ValueError("energy trace value invalid") from error
        require(timestamp > previous and math.isfinite(watts) and watts >= 0, "energy trace not increasing finite nonnegative")
        previous = timestamp
        rows.append((timestamp, watts))
    require(len(rows) >= 2, "energy trace requires at least two samples")
    return rows, sha256_bytes(raw)


def validate_energy_receipt(receipt_path: Path, trace_path: Path, expected_learned_events: int) -> dict[str, Any]:
    value = load_canonical_json(receipt_path)
    expected = {"schema", "state_slice", "trace_sha256", "sample_count", "joules", "learned_events", "joules_per_learned_event", "reference_joules_per_learned_event", "formula", "denominator", "receipt_sha256"}
    require(set(value) == expected and value["schema"] == "oaklab.h100.v8.energy.v1" and value["state_slice"] == STATE_SLICE, "energy receipt schema is not closed")
    rows, trace_digest = validate_energy_trace(trace_path)
    require(value["trace_sha256"] == trace_digest and value["sample_count"] == len(rows), "energy trace binding mismatch")
    integral = sum(0.5 * (left_watts + right_watts) * (right_ns - left_ns) / 1e9 for (left_ns, left_watts), (right_ns, right_watts) in zip(rows, rows[1:]))
    require(value["formula"] == "sum(0.5*(w_i+w_i+1)*(t_i+1-t_i)/1e9)" and value["denominator"] == "successfully_learned_events", "energy formula mismatch")
    events = value["learned_events"]
    require(isinstance(events, int) and not isinstance(events, bool) and events > 0 and events == expected_learned_events, "learned-event denominator is not counter-derived")
    for key in ("joules", "joules_per_learned_event", "reference_joules_per_learned_event"):
        require(isinstance(value[key], (int, float)) and not isinstance(value[key], bool) and math.isfinite(float(value[key])) and value[key] >= 0, f"energy value invalid: {key}")
    require(math.isclose(float(value["joules"]), integral, rel_tol=1e-12, abs_tol=1e-12), "joule integration mismatch")
    require(math.isclose(float(value["joules_per_learned_event"]), integral / events, rel_tol=1e-12, abs_tol=1e-12), "joule denominator mismatch")
    require(value["receipt_sha256"] == digest_without(value, "receipt_sha256"), "energy receipt self-digest mismatch")
    return value


def _finite_number(value: Any, label: str, nonnegative: bool = False) -> None:
    require(isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value)), f"{label} must be finite")
    if nonnegative:
        require(float(value) >= 0, f"{label} must be nonnegative")


def _validate_rows_container(path: Path, schema: str, row_keys: set[str], row_digest_key: str) -> list[dict[str, Any]]:
    value = load_canonical_json(path)
    require(set(value) == {"schema", "state_slice", "rows", "rows_sha256"} and value["schema"] == schema and value["state_slice"] == STATE_SLICE, f"row container schema invalid: {path}")
    rows = value["rows"]
    require(isinstance(rows, list) and rows, f"row container empty: {path}")
    require(value["rows_sha256"] == digest(rows), f"row container digest mismatch: {path}")
    for row in rows:
        require(isinstance(row, dict) and set(row) == row_keys, f"row schema invalid: {path}")
        require(row[row_digest_key] == digest_without(row, row_digest_key), f"row self-digest mismatch: {path}")
    return rows


def validate_counter_rows(path: Path) -> list[dict[str, Any]]:
    keys = {"schema", "state_slice", "phase", "cohort", "family", "seed", "local_row", "arm_id", "learned_events", "active_operations", "parameter_updates", "storage_bytes", "latency_ns", "counter_sha256"}
    rows = _validate_rows_container(path, "oaklab.h100.v8.counter-rows.v1", keys, "counter_sha256")
    for row in rows:
        require(row["phase"] in {"fit", "tune", "assessment"} and row["cohort"] in {"fit", "tune", "assessment"} and row["arm_id"] in {"candidate", "reference"}, "counter categorical field invalid")
        require(isinstance(row["seed"], int) and not isinstance(row["seed"], bool) and row["seed"] >= 0 and isinstance(row["local_row"], int) and not isinstance(row["local_row"], bool) and row["local_row"] >= 0, "counter index invalid")
        for key in ("learned_events", "active_operations", "parameter_updates", "storage_bytes", "latency_ns"):
            require(isinstance(row[key], int) and not isinstance(row[key], bool) and row[key] >= 0, f"counter metric invalid: {key}")
    return rows


def validate_family_rows(path: Path) -> list[dict[str, Any]]:
    keys = {"schema", "state_slice", "family", "seed", "candidate_loss", "reference_loss", "candidate_adaptation_lag", "reference_adaptation_lag", "candidate_null_loss", "reference_null_loss", "row_sha256"}
    rows = _validate_rows_container(path, "oaklab.h100.v8.family-rows.v1", keys, "row_sha256")
    allowed = {"predictable_noise", "drift", "delayed_reward", "event", "long_horizon", "null"}
    for row in rows:
        require(row["family"] in allowed and isinstance(row["seed"], int) and not isinstance(row["seed"], bool) and row["seed"] >= 0, "family row identity invalid")
        for key in ("candidate_loss", "reference_loss", "candidate_adaptation_lag", "reference_adaptation_lag", "candidate_null_loss", "reference_null_loss"):
            _finite_number(row[key], f"family row {key}", True)
    return rows


def paired_stats(differences: list[float]) -> dict[str, float]:
    require(len(differences) >= 2 and all(math.isfinite(value) for value in differences), "paired statistic requires finite n>=2")
    mean = sum(differences) / len(differences)
    variance = sum((value - mean) ** 2 for value in differences) / (len(differences) - 1)
    require(math.isfinite(variance) and variance >= 0, "paired variance invalid")
    if variance == 0:
        raw_p = 0.0 if mean != 0 else 1.0
    else:
        z = mean / math.sqrt(variance / len(differences))
        raw_p = math.erfc(abs(z) / math.sqrt(2.0))
    return {"mean_delta": mean, "raw_p": raw_p, "n": float(len(differences))}


def holm_adjust(values: dict[str, float]) -> dict[str, float]:
    ordered = sorted(values.items(), key=lambda item: (item[1], item[0]))
    adjusted: dict[str, float] = {}
    previous = 0.0
    count = len(ordered)
    for rank, (key, raw) in enumerate(ordered, 1):
        current = max(previous, min(1.0, (count - rank + 1) * raw))
        adjusted[key] = current
        previous = current
    return adjusted


def counter_totals(rows: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    totals = {arm: {metric: 0 for metric in ("learned_events", "active_operations", "parameter_updates", "storage_bytes", "latency_ns")} for arm in ("candidate", "reference")}
    for row in rows:
        for metric in totals[row["arm_id"]]:
            totals[row["arm_id"]][metric] += row[metric]
    require(all(totals[arm]["learned_events"] > 0 for arm in totals), "counter learned-event total must be positive")
    return totals


def validate_aggregate(path: Path, family_rows: list[dict[str, Any]], totals: dict[str, dict[str, int]], energy: dict[str, Any], custody_ok: bool) -> dict[str, Any]:
    value = load_canonical_json(path)
    expected = {"schema", "state_slice", "families", "family_statistics", "resource", "statistics", "publication_gate", "aggregate_sha256"}
    require(set(value) == expected and value["schema"] == "oaklab.h100.v8.aggregate.v1" and value["state_slice"] == STATE_SLICE, "aggregate schema is not closed")
    required_families = ["predictable_noise", "drift", "delayed_reward", "event", "long_horizon", "null"]
    require(value["families"] == required_families, "aggregate family roster is not the frozen roster")
    by_family: dict[str, list[dict[str, Any]]] = {family: [] for family in required_families}
    for row in family_rows:
        by_family[row["family"]].append(row)
    require(all(len(rows) >= 2 and len({row["seed"] for row in rows}) == len(rows) for rows in by_family.values()), "family rows lack independent paired seeds")
    loss_stats = {family: paired_stats([row["candidate_loss"] - row["reference_loss"] for row in rows]) for family, rows in by_family.items() if family != "null"}
    adaptation_families = ["drift", "delayed_reward", "event", "long_horizon"]
    adaptation_stats = {family: paired_stats([row["candidate_adaptation_lag"] - row["reference_adaptation_lag"] for row in by_family[family]]) for family in adaptation_families}
    null_stats = paired_stats([row["candidate_null_loss"] - row["reference_null_loss"] for row in by_family["null"]])
    loss_holm = holm_adjust({family: item["raw_p"] for family, item in loss_stats.items()})
    adaptation_holm = holm_adjust({family: item["raw_p"] for family, item in adaptation_stats.items()})
    stats_by_family: dict[str, dict[str, Any]] = {}
    for family in required_families:
        if family == "null":
            loss = paired_stats([row["candidate_loss"] - row["reference_loss"] for row in by_family[family]])
            loss_holm_p = holm_adjust({family: loss["raw_p"]})[family]
            adaptation = {"mean_delta": 0.0, "raw_p": 1.0, "n": float(len(by_family[family]))}
            adaptation_holm_p = 1.0
        else:
            loss = loss_stats[family]
            loss_holm_p = loss_holm[family]
            adaptation = adaptation_stats[family] if family in adaptation_stats else {"mean_delta": 0.0, "raw_p": 1.0, "n": float(len(by_family[family]))}
            adaptation_holm_p = adaptation_holm.get(family, 1.0)
        null = paired_stats([row["candidate_null_loss"] - row["reference_null_loss"] for row in by_family[family]])
        stats_by_family[family] = {
            "loss_mean_delta": loss["mean_delta"], "loss_raw_p": loss["raw_p"], "loss_holm_p": loss_holm_p, "loss_direction_pass": loss["mean_delta"] <= 0,
            "adaptation_mean_delta": adaptation["mean_delta"], "adaptation_raw_p": adaptation["raw_p"], "adaptation_holm_p": adaptation_holm_p, "adaptation_direction_pass": adaptation["mean_delta"] <= 0,
            "null_mean_delta": null["mean_delta"], "null_raw_p": null["raw_p"], "null_no_advantage": null["mean_delta"] >= 0,
        }
    require(value["family_statistics"] == stats_by_family, "family statistics are not derived from raw rows")
    resource_metrics = {"active_operations": "active_operations", "parameter_updates": "parameter_updates", "storage_bytes": "storage_bytes", "wall_clock_latency": "latency_ns", "learned_events": "learned_events"}
    resource: dict[str, dict[str, Any]] = {}
    for name, metric in resource_metrics.items():
        candidate = totals["candidate"][metric]; reference = totals["reference"][metric]
        noninferior = candidate <= reference * 1.05
        resource[name] = {"candidate": candidate, "reference": reference, "margin": 0.05, "noninferior": noninferior}
    resource["joules_per_learned_event"] = {"candidate": energy["joules_per_learned_event"], "reference": energy["reference_joules_per_learned_event"], "margin": 0.05, "noninferior": float(energy["joules_per_learned_event"]) <= float(energy["reference_joules_per_learned_event"]) * 1.05}
    require(value["resource"] == resource, "resource values are not counter/trace-derived")
    quality = all(item["loss_direction_pass"] for family, item in stats_by_family.items() if family != "null") and sum(item["loss_holm_p"] <= 0.05 for family, item in stats_by_family.items() if family != "null") >= 2 and stats_by_family["null"]["null_no_advantage"]
    adaptation = all(stats_by_family[family]["adaptation_direction_pass"] for family in adaptation_families) and any(stats_by_family[family]["adaptation_mean_delta"] < 0 and stats_by_family[family]["adaptation_holm_p"] <= 0.05 for family in adaptation_families)
    statistics = all(0 <= stats_by_family[family]["loss_holm_p"] <= 1 and 0 <= stats_by_family[family]["adaptation_holm_p"] <= 1 for family in required_families)
    resource_gate = all(item["noninferior"] for item in resource.values())
    energy_gate = resource["joules_per_learned_event"]["noninferior"] and energy["learned_events"] == totals["candidate"]["learned_events"]
    gate = {"quality": quality, "adaptation": adaptation, "resource": resource_gate, "statistics": statistics, "custody": custody_ok, "energy": energy_gate, "candidate": all((quality, adaptation, resource_gate, statistics, custody_ok, energy_gate))}
    require(value["publication_gate"] == gate, "publication gate is not derived")
    require(value["statistics"] == {"multiplicity": "holm", "alpha": 0.05, "power": 0.8, "paired_tests": len(family_rows)}, "statistics metadata is not frozen")
    require(value["aggregate_sha256"] == digest_without(value, "aggregate_sha256"), "aggregate self-digest mismatch")
    return value


def validate_independent_result(path: Path, manifest: dict[str, Any], aggregate: dict[str, Any]) -> dict[str, Any]:
    value = load_canonical_json(path)
    expected = {"schema", "state_slice", "validator_id", "review_digest", "manifest_core_sha256", "aggregate_sha256", "checks", "decision", "receipt_sha256"}
    require(set(value) == expected and value["schema"] == "oaklab.h100.v8.independent-validation.v1" and value["state_slice"] == STATE_SLICE, "independent validation schema is not closed")
    require(isinstance(value["validator_id"], str) and value["validator_id"], "validator identity missing")
    require(value["manifest_core_sha256"] == manifest["manifest_core_sha256"] and value["aggregate_sha256"] == aggregate["aggregate_sha256"], "independent result binding mismatch")
    require(isinstance(value["checks"], dict) and value["checks"] and all(isinstance(item, bool) for item in value["checks"].values()) and all(value["checks"].values()), "independent checks are not all true")
    require(value["decision"] == "accepted" and value["receipt_sha256"] == digest_without(value, "receipt_sha256"), "independent decision or digest invalid")
    return value


def result_root_digest(root: Path) -> str:
    entries = {relative: sha256_file(root / relative) for relative in sorted(ROOT_ALLOWLIST) if relative != "campaign_manifest.json"}
    return digest(entries)


def validate_result_root(root: Path, repo_root: Path = Path.cwd()) -> dict[str, Any]:
    require(root.is_dir() and not root.is_symlink(), "result root invalid")
    observed: set[str] = set()
    for path in root.rglob("*"):
        relative = path.relative_to(root).as_posix()
        if path.is_symlink():
            raise ValueError(f"result root symlink: {relative}")
        if path.is_file():
            observed.add(relative)
        elif path.is_dir() and not any(candidate.startswith(relative + "/") for candidate in ROOT_ALLOWLIST):
            raise ValueError(f"unlisted result directory: {relative}")
    require(observed == ROOT_ALLOWLIST, "result root file set mismatch")
    compiled = validate_compiled(repo_root)
    manifest = validate_campaign_manifest(root / "campaign_manifest.json", sha256_file(repo_root / COMPILED))
    require(manifest["source_sha256"] == sha256_file(repo_root / SOURCE), "source manifest binding mismatch")
    require(manifest["compiler_sha256"] == sha256_file(repo_root / "experiments/experience_learning/compile_oaklab_h100_v8_protocol.py"), "compiler manifest binding mismatch")
    require(manifest["validator_sha256"] == sha256_file(repo_root / "experiments/experience_learning/validate_oaklab_h100_v8_protocol.py"), "validator manifest binding mismatch")
    require(manifest["tests_sha256"] == sha256_file(repo_root / "experiments/experience_learning/tests/test_oaklab_h100_v8_protocol.py"), "tests manifest binding mismatch")
    require(manifest["agents_sha256"] == sha256_file(repo_root / "AGENTS.md"), "AGENTS manifest binding mismatch")
    require(manifest["campaign_manifest_artifact_sha256"] == sha256_file(repo_root / CAMPAIGN_MANIFEST_ARTIFACT), "campaign artifact manifest binding mismatch")
    require(manifest["review_packet_sha256"] == sha256_file(repo_root / REVIEW_PACKET), "review packet manifest binding mismatch")
    require(sha256_file(root / "compiled_protocol.json") == manifest["compiled_protocol_sha256"], "compiled result binding mismatch")
    review = validate_protocol_accept(root / "review/protocol_accept.json", manifest["review_packet_sha256"], sha256_file(repo_root / SOURCE), manifest["compiled_protocol_sha256"])
    review_sha = sha256_file(root / "review/protocol_accept.json")
    require(review_sha == manifest["protocol_review_sha256"], "protocol review manifest binding mismatch")
    fit = validate_fit_lock(root / "fit/lock.json", manifest["compiled_protocol_sha256"], review_sha)
    fit_digest = sha256_file(root / "fit/lock.json")
    tune = validate_tune_lock(root / "tune/lock.json", fit_digest)
    receipt = validate_lock_receipt(root / "tune/lock_receipt.json", sha256_file(root / "tune/lock.json"), review_sha)
    require(fit_digest == manifest["fit_lock_sha256"], "fit lock manifest binding mismatch")
    require(sha256_file(root / "tune/lock.json") == manifest["tune_lock_sha256"], "tune lock manifest binding mismatch")
    require(sha256_file(root / "tune/lock_receipt.json") == manifest["tune_lock_receipt_sha256"], "lock receipt manifest binding mismatch")
    allocation, cost, stop = validate_provider_receipts(root, manifest)
    require(sha256_file(root / "provider/allocation.json") == manifest["provider_allocation_sha256"], "allocation manifest binding mismatch")
    require(sha256_file(root / "provider/cost.json") == manifest["provider_cost_sha256"], "cost manifest binding mismatch")
    require(sha256_file(root / "provider/stop.json") == manifest["provider_stop_sha256"], "stop manifest binding mismatch")
    counters = validate_counter_rows(root / "result/counter_rows.json")
    totals = counter_totals(counters)
    family_rows = validate_family_rows(root / "result/family_rows.json")
    energy = validate_energy_receipt(root / "energy/joules.json", root / "energy/raw_trace.csv", totals["candidate"]["learned_events"])
    require(sha256_file(root / "energy/joules.json") == manifest["energy_receipt_sha256"], "energy manifest binding mismatch")
    aggregate = validate_aggregate(root / "result/aggregate.json", family_rows, totals, energy, True)
    require(aggregate["resource"]["joules_per_learned_event"]["candidate"] == energy["joules_per_learned_event"], "aggregate energy binding mismatch")
    independent = validate_independent_result(root / "validation/independent.json", manifest, aggregate)
    require(manifest["result_root_sha256"] == result_root_digest(root), "result-root digest mismatch")
    return {"valid": True, "compiled": compiled["compiled_protocol_sha256"], "review": review["review_decision"], "fit": fit["lock_sha256"], "tune": tune["lock_sha256"], "lock_receipt": receipt["receipt_sha256"], "allocation": allocation["allocation_id"], "charged_usd": cost["charged_usd"], "stop_reason": stop["stop_reason"], "energy_joules": energy["joules"], "aggregate": aggregate["aggregate_sha256"], "independent": independent["receipt_sha256"]}


def validate_execution_authorization(review_path: Path, synthetic_path: Path, preflight_path: Path, provider_plan_path: Path) -> dict[str, Any]:
    repo_root = Path.cwd()
    compiled = validate_compiled(repo_root)
    artifact = validate_campaign_manifest_artifact(repo_root / CAMPAIGN_MANIFEST_ARTIFACT, sha256_file(repo_root / SOURCE), sha256_file(repo_root / COMPILED), sha256_file(repo_root / REVIEW_PACKET), repo_root)
    plan = load_canonical_json(provider_plan_path)
    require(set(plan) == {"schema", "state_slice", "provider", "gpu_model", "hard_usd_ceiling", "job_count", "bounded", "packet_sha256", "source_sha256", "compiled_sha256", "campaign_manifest_path", "campaign_manifest_sha256", "campaign_core_sha256"} and plan["schema"] == "oaklab.h100.v8.provider-plan.v1" and plan["state_slice"] == STATE_SLICE, "provider plan schema is not closed")
    for key in ("packet_sha256", "source_sha256", "compiled_sha256", "campaign_manifest_sha256", "campaign_core_sha256"):
        require_hex(plan[key], f"provider plan {key}")
    require(plan["packet_sha256"] == sha256_file(REVIEW_PACKET) and plan["source_sha256"] == sha256_file(SOURCE) and plan["compiled_sha256"] == sha256_file(COMPILED) and plan["provider"] == "givemeanode" and plan["gpu_model"] == "H100" and plan["job_count"] == 1 and plan["bounded"] is True and isinstance(plan["hard_usd_ceiling"], (int, float)) and not isinstance(plan["hard_usd_ceiling"], bool) and math.isfinite(float(plan["hard_usd_ceiling"])) and plan["hard_usd_ceiling"] > 0 and plan["campaign_manifest_path"], "provider plan is not bound to current packet/source/compiled artifact")
    manifest_path = Path(plan["campaign_manifest_path"])
    manifest = validate_campaign_manifest(manifest_path, sha256_file(repo_root / COMPILED))
    require(plan["campaign_manifest_sha256"] == manifest["manifest_sha256"] and plan["campaign_core_sha256"] == manifest["manifest_core_sha256"] and manifest["hard_usd_ceiling"] == plan["hard_usd_ceiling"], "provider plan campaign manifest digest or USD binding mismatch")
    require(manifest["source_sha256"] == plan["source_sha256"] and manifest["compiler_sha256"] == sha256_file(repo_root / "experiments/experience_learning/compile_oaklab_h100_v8_protocol.py") and manifest["validator_sha256"] == sha256_file(repo_root / "experiments/experience_learning/validate_oaklab_h100_v8_protocol.py") and manifest["tests_sha256"] == sha256_file(repo_root / "experiments/experience_learning/tests/test_oaklab_h100_v8_protocol.py") and manifest["agents_sha256"] == sha256_file(repo_root / "AGENTS.md") and manifest["campaign_manifest_artifact_sha256"] == sha256_file(repo_root / CAMPAIGN_MANIFEST_ARTIFACT) and manifest["review_packet_sha256"] == plan["packet_sha256"], "campaign manifest is not bound to the current frozen packet")
    review = validate_protocol_accept(review_path, plan["packet_sha256"], plan["source_sha256"], plan["compiled_sha256"])
    require(sha256_file(review_path) == manifest["protocol_review_sha256"], "campaign manifest protocol review binding mismatch")
    synthetic = load_canonical_json(synthetic_path)
    require(set(synthetic) == {"schema", "state_slice", "candidate", "source_digest", "result_digest"} and synthetic["schema"] == "oaklab.h100.v8.synthetic-qualification.v1" and synthetic["state_slice"] == STATE_SLICE and synthetic["source_digest"] == sha256_file(SOURCE) and synthetic["candidate"] is True and require_hex(synthetic["result_digest"], "synthetic result digest"), "synthetic candidate is absent or unbound")
    preflight = load_canonical_json(preflight_path)
    require(set(preflight) == {"schema", "state_slice", "spend_usd", "network_access", "model_loaded", "bounded", "receipt_sha256"} and preflight["schema"] == "oaklab.h100.v8.no-spend-preflight.v1" and preflight["state_slice"] == STATE_SLICE, "preflight schema is not closed")
    require(preflight["spend_usd"] == 0 and preflight["network_access"] is False and preflight["model_loaded"] is False and preflight["bounded"] is True and preflight["receipt_sha256"] == digest_without(preflight, "receipt_sha256"), "no-spend preflight failed")
    return {"authorized": True, "state_slice": STATE_SLICE, "review": review["review_decision"], "campaign_core_sha256": plan["campaign_core_sha256"]}


def validate_packet(repo_root: Path = Path.cwd()) -> dict[str, Any]:
    compiled = validate_compiled(repo_root)
    artifact = validate_campaign_manifest_artifact(repo_root / CAMPAIGN_MANIFEST_ARTIFACT, compiled["source_spec_sha256"], sha256_file(repo_root / COMPILED), sha256_file(repo_root / REVIEW_PACKET), repo_root)
    return {"valid": True, "state_slice": STATE_SLICE, "source_sha256": compiled["source_spec_sha256"], "compiled_sha256": sha256_file(repo_root / COMPILED), "compiled_self_digest": compiled["compiled_protocol_sha256"], "campaign_manifest_artifact_sha256": artifact["manifest_sha256"], "assessment_materialization_state": "absent"}


if __name__ == "__main__":
    print(json.dumps(validate_packet(), sort_keys=True, allow_nan=False))
