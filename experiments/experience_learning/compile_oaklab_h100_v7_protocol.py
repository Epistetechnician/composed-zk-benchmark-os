#!/usr/bin/env python3
"""Compile the Oak Lab H100 replication V7 protocol.

State slice: oaklab-experience-learning-h100-replication-v7.
This compiler is protocol-only and performs no learner, provider, model, data,
or energy execution.
"""

from __future__ import annotations

import sys

if __package__ in {None, ""} and sys.path:
    sys.path.pop(0)

import argparse
import hashlib
import json
import struct
from pathlib import Path
from typing import Any


STATE_SLICE = "oaklab-experience-learning-h100-replication-v7"
PROTOCOL_ID = "oaklab.h100.v7"
SOURCE_SCHEMA = "oaklab.experience-learning.h100-replication-v7.source.v1"
COMPILED_SCHEMA = "oaklab.experience-learning.h100-replication-v7.compiled.v1"
COMPILER_VERSION = "oaklab.h100.v7.protocol-compiler.v1"
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
    "implementation_before_review", "estimand", *SECTIONS, "strict_contract", "stop_rules", "boundaries",
}
ROOT = Path(__file__).resolve().parents[2]
SOURCE_PATH = Path("experiments/experience_learning/oaklab_h100_v7_protocol.json")
COMPILED_PATH = Path("experiments/experience_learning/oaklab_h100_v7_compiled_protocol.json")
FREEZE_FILES = (
    str(SOURCE_PATH),
    "experiments/experience_learning/compile_oaklab_h100_v7_protocol.py",
    "experiments/experience_learning/validate_oaklab_h100_v7_protocol.py",
    "experiments/experience_learning/tests/test_oaklab_h100_v7_protocol.py",
    "AGENTS.md",
)


def canonical(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False) + "\n").encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def digest(value: Any) -> str:
    return sha256_bytes(canonical(value))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _closed(value: Any, keys: set[str], label: str) -> None:
    require(isinstance(value, dict) and set(value) == keys, f"{label} object is not closed")


def validate_strict_contract(source: dict[str, Any]) -> None:
    contract = source["strict_contract"]
    _closed(contract, {"schema", "unknown_fields", "estimand", "controller", "generators", "operations", "statistics", "runtime"}, "strict_contract")
    require(contract["schema"] == "oaklab.h100.v7.strict-contract.v1" and contract["unknown_fields"] == "reject_at_every_object", "strict contract identity changed")
    e = source["estimand"]
    ec = contract["estimand"]
    _closed(ec, {"required_keys", "exact_values", "carryover_required_phrases"}, "strict_contract.estimand")
    require(set(e) == set(ec["required_keys"]), "estimand keys are not recursively closed")
    require({key: e[key] for key in ec["exact_values"]} == ec["exact_values"], "estimand exact values changed")
    require(all(isinstance(item, str) and item in e["carryover_control"] for item in ec["carryover_required_phrases"]), "estimand carryover contract changed")

    c = source["controller_transition_table"]
    cc = contract["controller"]
    _closed(cc, {"state_tuple_arity", "state_names", "state_types", "state_scopes", "transition_indices", "transition_events", "transition_keys", "transition_reads_writes_rules", "recurrence_equations", "simultaneous_rhs_phrase", "terminal_phrase"}, "strict_contract.controller")
    require(cc["state_tuple_arity"] == 3 and [row[0] for row in c["state_fields"]] == cc["state_names"], "controller state names changed")
    require({row[0]: row[1] for row in c["state_fields"]} == cc["state_types"], "controller state types changed")
    require(set(cc["state_scopes"]) == {"fit_persistent", "trajectory", "pending"}, "controller scopes changed")
    require(sorted(name for names in cc["state_scopes"].values() for name in names) == sorted(cc["state_names"]), "controller scope partition changed")
    require([row["index"] for row in c["rows"]] == cc["transition_indices"] and [row["event"] for row in c["rows"]] == cc["transition_events"], "controller transition order changed")
    for row in c["rows"]:
        _closed(row, set(cc["transition_keys"]), f"controller row {row.get('index')}")
        require(isinstance(row["reads"], list) and isinstance(row["writes"], list) and all(isinstance(item, str) and item for item in row["reads"] + row["writes"]), "controller read/write schema changed")
        expected_row = cc["transition_reads_writes_rules"][str(row["index"])]
        require({key: row[key] for key in ("reads", "writes", "rule")} == expected_row, f"controller row {row['index']} semantics changed")
    require(c["recurrence"] == [f"{key}={cc['recurrence_equations'][key]}" for key in ("delta", "eligibility_new", "theta_new", "dual_mu_new", "q_old_new")], "controller recurrence changed")
    require(c["rhs_rule"] == cc["simultaneous_rhs_phrase"] and cc["terminal_phrase"] in c["terminal_rule"], "controller transition semantics changed")

    roster = source["generator_roster"]
    gc = contract["generators"]
    _closed(gc, {"stream_ids", "stream_required_keys", "draw_tuple_arity", "draw_ordinals", "draw_repeats", "row_count", "segment_rules", "no_future_or_redraw_phrase", "stream_semantics"}, "strict_contract.generators")
    require(roster["stream_order"] == gc["stream_ids"] and set(roster["streams"]) == set(gc["stream_ids"]) and set(roster["draw_roster"]) == set(gc["stream_ids"],), "generator identity changed")
    require(gc["row_count"] == roster["rows_per_trajectory"] and gc["draw_tuple_arity"] == 4 and gc["draw_ordinals"] == "exact_contiguous_zero_based" and gc["draw_repeats"] == "positive_integer_unconditional", "generator draw contract changed")
    for stream_id in gc["stream_ids"]:
        stream = roster["streams"][stream_id]
        require(set(stream) == set(gc["stream_required_keys"]), f"{stream_id}: stream schema is not closed")
        require({key: stream[key] for key in ("equation", "draw_order", "events", "oracle_features")} == gc["stream_semantics"][stream_id], f"{stream_id}: stream semantics changed")
        segments = stream["segments"]
        require(isinstance(segments, list) and segments[0] == 0 and segments[-1] == gc["row_count"] and all(isinstance(v, int) for v in segments) and all(left < right for left, right in zip(segments, segments[1:])), f"{stream_id}: segment contract changed")
        draws = roster["draw_roster"][stream_id]
        require(all(isinstance(row, list) and len(row) == gc["draw_tuple_arity"] for row in draws), f"{stream_id}: draw tuple schema changed")
        require([row[0] for row in draws] == list(range(len(draws))) and all(isinstance(row[3], int) and row[3] > 0 for row in draws), f"{stream_id}: draw order/repeats changed")
    require(gc["no_future_or_redraw_phrase"] in roster["draw_rule"], "generator future/redraw boundary changed")

    algebra = source["operation_and_byte_algebra"]
    oc = contract["operations"]
    _closed(oc, {"required_ast_names", "ast_node_keys", "numeric_rules_exact", "byte_layout_required", "resource_separation_phrase", "allowed_ast_ops", "byte_field_tuple_arity", "byte_offsets_rule"}, "strict_contract.operations")
    require(set(algebra["formula_ast"]) == set(oc["required_ast_names"]) and algebra["numeric_rules"] == oc["numeric_rules_exact"], "operation contract changed")
    def check_ast(node: Any) -> None:
        require(isinstance(node, dict) and set(node) == set(oc["ast_node_keys"]), "numeric AST node is not closed")
        require(node["op"] in oc["allowed_ast_ops"] and isinstance(node["args"], list), "numeric AST node type changed")
        for arg in node["args"]:
            if isinstance(arg, dict):
                check_ast(arg)
            else:
                require(isinstance(arg, (str, int, float)) and not isinstance(arg, bool), "numeric AST literal type changed")
    for node in algebra["formula_ast"].values():
        check_ast(node["ast"])
    require(all(name in algebra["byte_layouts"] for name in oc["byte_layout_required"]) and oc["resource_separation_phrase"] in algebra["resource_invariants"], "operation byte/resource contract changed")
    for layout_name in oc["byte_layout_required"]:
        layout = algebra["byte_layouts"][layout_name]
        require(layout["alignment"] == "none" and all(isinstance(field, list) and len(field) == oc["byte_field_tuple_arity"] and ((isinstance(field[2], int) and field[2] >= 0) or (isinstance(field[2], str) and field[2] in {"8*dimension"})) and isinstance(field[3], (int, str)) and field[3] for field in layout["fields"]), f"{layout_name}: byte field schema changed")

    stats = contract["statistics"]
    _closed(stats, {"families_required", "holm", "raw_rows_required", "caller_supplied_gate_booleans_forbidden", "adaptation_shift_scan_forbidden"}, "strict_contract.statistics")
    require(stats["families_required"] == ["predictable_noise", "drift", "delayed_reward", "event", "long_horizon", "null"] and set(roster["family_map"]) == set(stats["families_required"]), "statistics family roster changed")
    require(stats["raw_rows_required"] is True and stats["caller_supplied_gate_booleans_forbidden"] is True and stats["adaptation_shift_scan_forbidden"] is True and stats["holm"] == source["ablation_execution_multiplicity"]["holm_groups"][0]["adjustment"], "statistics derivation contract changed")

    runtime = contract["runtime"]
    _closed(runtime, {"provider_currency", "provider_max_interval_seconds", "provider_cross_binding_fields", "counter_derived_fields", "assessment_order", "authorization_revalidates_current_packet", "historical_isolation"}, "strict_contract.runtime")
    require(runtime["provider_currency"] == "USD" and runtime["provider_max_interval_seconds"] == 86400 and runtime["authorization_revalidates_current_packet"] is True, "runtime provider/authorization contract changed")
    require(runtime["historical_isolation"] == ["phase_836", "oaklab_v6", "plasticity_guard", "astral"], "runtime lane isolation contract changed")


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
    stream = b"sparse_signal_v7"
    seed = 4000
    row = 0
    frame = lp32(b"oaklab.h100.v7.prng.v1") + protocol_raw + lp32(cohort) + lp32(stream) + struct.pack("<Q", seed) + struct.pack("<I", row)
    root = hashlib.sha256(frame).digest()
    raw = splitmix64(root, 13)
    action_seed = bytes.fromhex(source["hash_prng_transcript"]["action_assignment"]["action_seed_hex"])
    action_frame = lp32(b"oaklab.h100.v7.action.v1") + protocol_raw + action_seed + lp32(cohort) + lp32(stream) + struct.pack("<Q", seed) + struct.pack("<I", row)
    return {
        "frame_hex": frame.hex(),
        "root_sha256": root.hex(),
        "initial_state_uint64_le": int.from_bytes(root[:8], "little"),
        "first_12_raw_uint64_hex": [f"{value:016x}" for value in raw[:12]],
        "first_uniform53": (raw[0] >> 11) / float(1 << 53),
        "first_normal12": sum((value >> 11) / float(1 << 53) for value in raw[1:13]) - 6.0,
        "action_hash_sha256": hashlib.sha256(action_frame).hexdigest(),
    }


def validate_source(source: dict[str, Any]) -> None:
    require(set(source) == SOURCE_KEYS, "source schema is not closed")
    require(source["schema_version"] == SOURCE_SCHEMA and source["protocol_id"] == PROTOCOL_ID and source["state_slice"] == STATE_SLICE, "source identity mismatch")
    require(source["status"] == "frozen_pending_independent_review" and source["implementation_before_review"] is False, "implementation boundary is open")
    estimand = source["estimand"]
    require(estimand["control"] == "fixed_sgd_b1" and estimand["treatment"] == "lagged_selective_credit", "estimand arms changed")
    require(estimand["same_stream"] is True and estimand["same_initial_checkpoint"] is True and estimand["arm_order_randomized"] is True, "paired controls missing")
    require(estimand["primary_endpoint"] == "mean_e_mean_b(loss_treatment[e,b]-loss_control[e,b])", "primary estimand changed")
    require(estimand["assessment_absent_until_lock"] is True and "previous block only" in estimand["carryover_control"], "carryover boundary missing")
    validate_strict_contract(source)

    h = source["hash_prng_transcript"]
    require("no conditional draws" in h["draw_policy"] and "no redraws" in h["draw_policy"], "draw policy is open")
    require(h["action_assignment"]["probability"] == {"p_num": 1, "p_den": 4}, "action probability is not exact")
    require(h["action_assignment"]["fit_only"] is True and len(h["action_assignment"]["action_seed_hex"]) == 64, "action seed boundary invalid")

    c = source["controller_transition_table"]
    require([row["index"] for row in c["rows"]] == list(range(8)), "controller indices are not contiguous")
    require([row["event"] for row in c["rows"]] == ["trajectory_init", "observe_pre_action", "credit_previous", "select_action", "model_action", "publish_pending", "terminal_credit", "counter_finalize"], "controller order changed")
    names = [row[0] for row in c["state_fields"]]
    require(len(names) == 20 and len(names) == len(set(names)), "controller state roster is incomplete")
    require({"pending_valid", "pending_features", "pending_prediction", "pending_loss", "pending_event_count", "pending_action", "pending_cost", "pending_reward", "pending_local_row", "pending_terminal"}.issubset(names), "pending state is incomplete")
    require("pre-transition snapshot" in c["rhs_rule"] and "undeclared carryover" in c["rows"][5]["rule"], "simultaneous recurrence or carryover rule missing")
    require("no model action" in c["terminal_rule"], "terminal action prohibition missing")

    roster = source["generator_roster"]
    expected = {"sparse_signal_v7", "drifting_relevance_v7", "delayed_reward_v7", "event_sensor_v7", "long_horizon_v7", "pure_noise_v7"}
    require(set(roster["stream_order"]) == expected and set(roster["streams"]) == expected and set(roster["draw_roster"]) == expected, "generator roster mismatch")
    for stream_id, draws in roster["draw_roster"].items():
        require([row[0] for row in draws] == list(range(len(draws))), f"{stream_id}: draw order is not contiguous")
        require(all(isinstance(row[3], int) and row[3] > 0 for row in draws), f"{stream_id}: conditional draw repeat")
    for stream_id, stream in roster["streams"].items():
        require(stream["segments"][0] == 0 and stream["segments"][-1] == 256, f"{stream_id}: segment bounds invalid")
        require(all(isinstance(stream[field], str) and stream[field] for field in ("equation", "draw_order", "events")), f"{stream_id}: semantic fields missing")
    require("redraw is forbidden" in roster["draw_rule"], "redraw policy missing")

    algebra = source["operation_and_byte_algebra"]
    require("no fused multiply-add" in algebra["numeric_rules"] and "left-to-right" in algebra["numeric_rules"], "numeric rules incomplete")
    require(set(algebra["formula_ast"]) == {"forward_dense", "loss_half_squared", "gradient", "model_update", "controller_dot", "event_count"}, "formula AST set changed")
    for name in ("model_state", "counter_row", "lock_receipt"):
        layout = algebra["byte_layouts"][name]
        require(layout["alignment"] == "none" and layout["fields"] and layout["bytes"], f"{name}: byte layout incomplete")
    require("joules remain absent" in " ".join(algebra["resource_invariants"]), "energy separation missing")

    a = source["ablation_execution_multiplicity"]
    require(len(a["arm_order"]) == 8 and set(a["execution_matrix"]) == set(a["arm_order"]), "ablation roster mismatch")
    require(all(set(phases) == {"fit", "tune", "assessment"} for phases in a["execution_matrix"].values()), "ablation phases incomplete")
    require("no tune-derived probability" in a["matched_random_rule"], "matched random is not pre-tune")
    require(len(a["holm_groups"]) == 3 and all("sort raw p" in group["adjustment"] for group in a["holm_groups"]), "Holm groups incomplete")
    require("cannot be imputed" in a["missing_rules"] and len(a["gate_predicates"]) >= 5, "missing or gate rules incomplete")

    m = source["adaptation_metrics"]
    require("[k,k+8)" in m["recovery_scan"] and "[k+8,k+16)" in m["recovery_scan"] and "never scan across shifts" in m["aggregation"], "adaptation scan is not shift-bounded")

    schemas = source["lock_counter_control_schemas"]
    required_schema_names = {"fit_lock", "tune_lock", "lock_receipt", "counter_row", "review_accept", "family_rows", "campaign_manifest", "provider_receipts", "energy_receipt", "result_root", "independent_validation", "assessment_absence"}
    require(set(schemas) == required_schema_names | {"schema_policy"}, "runtime schema roster is not closed")
    for name in ("fit_lock", "tune_lock", "lock_receipt", "counter_row", "campaign_manifest"):
        fields = schemas[name]["fields"]
        require(fields and len(fields) == len(set(fields)), f"{name}: fields are not unique")
    require(schemas["campaign_manifest"]["core_digest_scope"] == ["schema", "state_slice", "compiled_protocol_sha256", "protocol_review_sha256", "review_packet_sha256", "code_sha256", "model_sha256", "data_sha256", "backend_sha256", "guard_sha256", "hard_usd_ceiling"], "campaign core digest scope changed")
    require(schemas["result_root"]["allowlist"] == ["campaign_manifest.json", "compiled_protocol.json", "review/protocol_accept.json", "fit/lock.json", "tune/lock.json", "tune/lock_receipt.json", "provider/allocation.json", "provider/cost.json", "provider/stop.json", "energy/raw_trace.csv", "energy/joules.json", "result/counter_rows.json", "result/family_rows.json", "result/aggregate.json", "validation/independent.json"], "result-root allowlist changed")
    require(schemas["result_root"]["mode"] == "closed_world" and schemas["result_root"]["reject_extra_paths"] is True and schemas["result_root"]["validate_all_content"] is True and schemas["result_root"]["validate_all_bindings"] is True, "result root is not closed")
    require(schemas["provider_receipts"]["signature"].startswith("Ed25519") and "same allocation_id" in schemas["provider_receipts"]["cross_binding"], "provider cross-binding is incomplete")
    require(schemas["energy_receipt"]["formula"].startswith("sum(0.5") and "successfully_learned_events" in schemas["energy_receipt"]["denominator"], "energy formula is not declared")
    require(schemas["assessment_absence"]["materialization_state"] == "absent" and schemas["assessment_absence"]["entry_count"] == 0, "assessment absence changed")
    require(isinstance(source["stop_rules"], list) and len(source["stop_rules"]) >= 9, "stop rules incomplete")
    require(source["boundaries"]["phase_836"] == "closed_historical_only" and source["boundaries"]["oaklab_v6"] == "closed_historical_only" and source["boundaries"]["astral"] == "isolated_and_blocked", "historical lane boundary changed")


def compile_protocol(repo_root: Path = ROOT) -> dict[str, Any]:
    source_path = repo_root / SOURCE_PATH
    source_bytes = source_path.read_bytes()
    require(source_bytes.startswith(b"{") and source_bytes.endswith(b"\n"), "source bytes must be JSON with final LF")
    source = json.loads(source_bytes.decode("utf-8"))
    require(isinstance(source, dict), "source must be an object")
    require(source_bytes == canonical(source), "source bytes must be canonical JSON")
    validate_source(source)
    source_digest = sha256_bytes(source_bytes)
    freeze = {path: sha256_file(repo_root / path) for path in FREEZE_FILES}
    compiled: dict[str, Any] = {
        "schema_version": COMPILED_SCHEMA,
        "protocol_id": PROTOCOL_ID,
        "state_slice": STATE_SLICE,
        "claim_ceiling": source["claim_ceiling"],
        "compiler_version": COMPILER_VERSION,
        "source_spec_sha256": source_digest,
        "freeze_file_sha256": freeze,
        "sections": list(SECTIONS),
        "section_digests": {name: digest(source[name]) for name in SECTIONS},
        "transcript_test_vector": transcript_vector(source_digest, source),
        "assessment_materialization_state": "absent",
        "compiled": {name: source[name] for name in SECTIONS},
        "strict_contract": source["strict_contract"],
        "estimand": source["estimand"],
        "stop_rules": source["stop_rules"],
        "boundaries": source["boundaries"],
        "execution_gate": {"review_accept_required": True, "packet_binding_required": True, "full_validation_required": True, "synthetic_candidate_required": True, "zero_spend_preflight_required": True, "provider_allocation_required": True, "one_bounded_job_maximum": True, "assessment_absent": True, "effects_run": False},
        "compiled_protocol_sha256": "",
    }
    compiled["compiled_protocol_sha256"] = digest({key: value for key, value in compiled.items() if key != "compiled_protocol_sha256"})
    return compiled


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    parser.add_argument("--output", type=Path, default=COMPILED_PATH)
    args = parser.parse_args()
    value = compile_protocol(args.repo_root)
    output = args.output if args.output.is_absolute() else args.repo_root / args.output
    output.write_bytes(canonical(value))
    print(json.dumps({"state_slice": STATE_SLICE, "compiled_protocol_sha256": value["compiled_protocol_sha256"], "output": str(output)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
