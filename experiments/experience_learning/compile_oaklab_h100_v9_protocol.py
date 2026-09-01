#!/usr/bin/env python3
"""Compile and recursively validate the Oak Lab H100 V9 protocol.

State slice: ``oaklab-experience-learning-h100-replication-v9``.
The compiler performs no learner, data, provider, H100, energy, or assessment
execution.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
from pathlib import Path
from typing import Any


STATE_SLICE = "oaklab-experience-learning-h100-replication-v9"
PROTOCOL_ID = "oaklab.h100.v9"
SOURCE_SCHEMA = "oaklab.experience-learning.h100-replication-v9.source.v1"
COMPILED_SCHEMA = "oaklab.experience-learning.h100-replication-v9.compiled.v1"
COMPILER_VERSION = "oaklab.h100.v9.protocol-compiler.v1"
ROOT = Path(__file__).resolve().parents[2]
SOURCE_PATH = Path("experiments/experience_learning/oaklab_h100_v9_protocol.json")
COMPILED_PATH = Path("experiments/experience_learning/oaklab_h100_v9_compiled_protocol.json")
CAMPAIGN_ARTIFACT_PATH = Path("experiments/experience_learning/oaklab_h100_v9_campaign_manifest.json")
SECTIONS = ("estimand", "controller", "generator_roster", "hash_prng", "resource_accounting", "statistics", "controls", "locks", "operation_and_byte_algebra", "execution_schemas", "campaign_manifest_artifact", "boundaries")
SOURCE_KEYS = {"schema_version", "protocol_id", "state_slice", "status", "implementation_before_review", "claim_ceiling", *SECTIONS, "stop_rules"}


def canonical(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False) + "\n").encode()


def digest(value: Any) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def closed(value: Any, keys: set[str], label: str) -> None:
    require(isinstance(value, dict) and set(value) == keys, f"{label} object is not closed")


def _validate_estimand(source: dict[str, Any]) -> None:
    expected = {"name", "unit", "control", "treatment", "primary_endpoint", "favorable_direction", "segment_rows", "warmup_segments", "post_washout_segments", "same_stream", "same_initial_checkpoint", "arm_order_randomized", "trajectory", "carryover_control", "loss_timing", "assessment_absent_until_lock"}
    e = source["estimand"]
    closed(e, expected, "estimand")
    require(e["control"] == "fixed_sgd_b1" and e["treatment"] == "segment_budgeted_update_policy", "estimand arms changed")
    require(e["segment_rows"] == 32 and e["warmup_segments"] == 1 and e["post_washout_segments"] == 7, "estimand horizon changed")
    require(e["same_stream"] is True and e["same_initial_checkpoint"] is True and e["arm_order_randomized"] is True, "paired estimand controls missing")
    require(e["favorable_direction"] == "negative" and e["assessment_absent_until_lock"] is True, "estimand direction or absence changed")
    require("previous segment only" in e["carryover_control"] and "no current segment outcome enters action" in e["carryover_control"], "carryover control changed")


def _validate_controller(source: dict[str, Any]) -> None:
    expected = {"name", "decision_boundary", "action_rule", "utility_definition", "recurrence", "simultaneous_rhs", "states", "transition_table", "state_bytes"}
    c = source["controller"]
    closed(c, expected, "controller")
    require(c["decision_boundary"] == "segment boundary only" and c["simultaneous_rhs"].startswith("all right-hand sides"), "controller boundary changed")
    require(c["action_rule"] == "apply iff utility_ema-0.002*cost_ema >= 0; exact tie applies", "controller action rule changed")
    state_names = [row[0] for row in c["states"]]
    require(state_names == ["utility_ema", "cost_ema", "policy_bit", "previous_segment_loss", "previous_segment_ops", "previous_segment_id", "pending_valid", "rows_in_segment", "processed_rows"], "controller state roster changed")
    require(all(isinstance(row, list) and len(row) == 3 and isinstance(row[0], str) and isinstance(row[1], str) and isinstance(row[2], str) for row in c["states"]), "controller state tuples changed")
    require(len(c["transition_table"]) == 6 and [row["index"] for row in c["transition_table"]] == list(range(6)), "controller transition indices changed")
    transition_keys = {"index", "event", "reads", "writes", "rule"}
    for row in c["transition_table"]:
        closed(row, transition_keys, f"controller transition {row.get('index')}")
        require(isinstance(row["reads"], list) and isinstance(row["writes"], list) and all(isinstance(value, str) and value for value in row["reads"] + row["writes"]), "controller transition read/write schema changed")
    require("previous_segment_loss" in c["transition_table"][1]["reads"] and "policy_bit" in c["transition_table"][2]["writes"], "segment carryover transition changed")
    require("no model action" in c["transition_table"][-1]["rule"], "terminal action boundary changed")


def _validate_generators(source: dict[str, Any]) -> None:
    expected = {"stream_order", "rows_per_trajectory", "segment_boundaries", "draw_rule", "draw_roster", "semantics"}
    g = source["generator_roster"]
    closed(g, expected, "generator_roster")
    require(g["rows_per_trajectory"] == 256 and g["segment_boundaries"] == [0, 32, 64, 96, 128, 160, 192, 224, 256], "generator horizon changed")
    require(g["stream_order"] == ["sparse_signal_v9", "drifting_relevance_v9", "delayed_reward_v9", "event_sensor_v9", "long_horizon_v9", "pure_noise_v9"], "generator order changed")
    require("no conditional draws" in g["draw_rule"] and "redraws" in g["draw_rule"] and "future-data" in g["draw_rule"], "generator leakage boundary changed")
    require(set(g["draw_roster"]) == set(g["stream_order"]) and set(g["semantics"]) == set(g["stream_order"]), "generator roster incomplete")
    for stream in g["stream_order"]:
        semantics = g["semantics"][stream]
        closed(semantics, {"family", "dimension", "equation", "segments", "oracle_features"}, f"generator semantics {stream}")
        require(isinstance(semantics["dimension"], int) and semantics["dimension"] > 0 and isinstance(semantics["segments"], list) and semantics["segments"][0] == 0 and semantics["segments"][-1] == 256, f"generator semantics {stream} invalid")
        draws = g["draw_roster"][stream]
        require(all(isinstance(row, list) and len(row) == 4 and row[0] == index and isinstance(row[3], int) and row[3] > 0 for index, row in enumerate(draws)), f"generator draws {stream} invalid")


def _validate_resources(source: dict[str, Any]) -> None:
    expected = {"primary_cost", "cost_formula", "controller_boundary_ops", "storage_formula", "controller_state_bytes", "latency", "energy", "replay_bytes", "batch_one"}
    r = source["resource_accounting"]
    closed(r, expected, "resource_accounting")
    require(r["primary_cost"] == "active_operations" and r["controller_boundary_ops"] == 9 and r["controller_state_bytes"] == 43, "resource accounting changed")
    require(r["replay_bytes"] == 0 and "one row per observe" in r["batch_one"] and "excluded from deterministic result digests" in r["latency"], "resource boundary changed")


def _validate_statistics(source: dict[str, Any]) -> None:
    expected = {"families", "fit_seeds", "tune_seeds", "assessment_seeds", "repeats", "power", "icc", "minimum_effect", "alpha", "holm", "raw_rows_required", "caller_supplied_booleans_forbidden", "adaptation"}
    s = source["statistics"]
    closed(s, expected, "statistics")
    require(s["families"] == ["predictable_noise", "drift", "delayed_reward", "event", "long_horizon", "null"], "statistics families changed")
    require(s["fit_seeds"] == {"start": 9000, "count": 48} and s["tune_seeds"] == {"start": 10000, "count": 24} and s["assessment_seeds"] == {"start": 11000, "count": 48}, "statistics cohorts changed")
    require(s["repeats"] == 3 and s["power"] == 0.80 and s["icc"] == 0.50 and s["minimum_effect"] == 0.05 and s["alpha"] == 0.05, "power/statistical assumptions changed")
    require(s["raw_rows_required"] is True and s["caller_supplied_booleans_forbidden"] is True and "segment-bounded" in s["adaptation"], "statistics derivation boundary changed")


def _validate_algebra(source: dict[str, Any]) -> None:
    algebra = source["operation_and_byte_algebra"]
    closed(algebra, {"numeric_rules", "formula_ast", "byte_layouts", "operation_units", "resource_invariants"}, "operation_and_byte_algebra")
    require(algebra["numeric_rules"].startswith("IEEE-754 binary64") and "operation counts" in algebra["resource_invariants"][-1], "numeric rule changed")
    require(set(algebra["formula_ast"]) == {"forward_dense", "loss_half_squared", "gradient", "model_update", "controller_boundary"}, "formula AST roster changed")
    def check(node: Any) -> None:
        closed(node, {"op", "args"}, "numeric AST node")
        require(node["op"] in {"identity", "add", "mul", "sub"} and isinstance(node["args"], list), "numeric AST operation changed")
        for arg in node["args"]:
            if isinstance(arg, dict):
                check(arg)
            else:
                require(isinstance(arg, (str, int, float)) and not isinstance(arg, bool), "numeric AST literal changed")
    for value in algebra["formula_ast"].values():
        closed(value, {"inputs", "output", "ast"}, "formula declaration")
        check(value["ast"])
    for name in ("counter_row", "lock_receipt", "model_state"):
        layout = algebra["byte_layouts"].get(name)
        require(isinstance(layout, dict), f"byte layout missing: {name}")
        closed(layout, {"alignment", "bytes", "fields"}, f"byte layout {name}")
        require(layout["alignment"] == "none" and all(isinstance(field, list) and len(field) == 4 for field in layout["fields"]), f"byte layout {name} changed")


def _validate_execution_schemas(source: dict[str, Any]) -> None:
    schemas = source["execution_schemas"]
    closed(schemas, {"lock", "counter", "control", "provider", "energy", "result_root"}, "execution_schemas")
    closed(schemas["lock"], {"fit", "tune", "independent"}, "lock schemas")
    for name, value in schemas["lock"].items():
        closed(value, {"schema", "fields"}, f"lock schema {name}")
        require(isinstance(value["fields"], list) and value["fields"], f"lock fields {name} missing")
    closed(schemas["counter"], {"schema", "fields"}, "counter schema")
    closed(schemas["control"], {"schema", "arms", "arm_reset"}, "control schema")
    require(schemas["control"]["arms"] == source["controls"]["arms"], "control schema arms changed")
    closed(schemas["provider"], {"allocation_schema", "cost_schema", "stop_schema", "currency", "signature", "cross_binding"}, "provider schemas")
    require(schemas["provider"]["currency"] == "USD" and len(schemas["provider"]["cross_binding"]) >= 8, "provider binding schema changed")
    closed(schemas["energy"], {"schema", "trace", "formula", "denominator"}, "energy schema")
    require("finite nonnegative" in schemas["energy"]["trace"] and "trapezoid" not in schemas["energy"]["formula"], "energy schema changed")
    closed(schemas["result_root"], {"mode", "reject_extra_paths", "reject_symlinks", "allowlist"}, "result root schema")
    require(schemas["result_root"]["mode"] == "closed_world" and schemas["result_root"]["reject_extra_paths"] is True and schemas["result_root"]["reject_symlinks"] is True and isinstance(schemas["result_root"]["allowlist"], list), "result root closure changed")


def validate_source(source: dict[str, Any]) -> None:
    closed(source, SOURCE_KEYS, "source")
    require(source["schema_version"] == SOURCE_SCHEMA and source["protocol_id"] == PROTOCOL_ID and source["state_slice"] == STATE_SLICE, "source identity mismatch")
    require(source["status"] == "frozen_pending_independent_review" and source["implementation_before_review"] is False, "implementation boundary changed")
    _validate_estimand(source)
    _validate_controller(source)
    _validate_generators(source)
    closed(source["hash_prng"], {"canonical_json", "digest", "frame", "source_bytes", "row_frame", "action_assignment", "test_vector"}, "hash_prng")
    require(source["hash_prng"]["action_assignment"]["probability"] == {"p_num": 1, "p_den": 2} and source["hash_prng"]["action_assignment"]["fit_only"] is True, "action assignment changed")
    _validate_resources(source)
    _validate_statistics(source)
    closed(source["controls"], {"arms", "arm_reset", "null_rule", "ablation_rule"}, "controls")
    require(source["controls"]["arms"] == ["fixed_sgd_b1", "segment_budgeted_update_policy", "lambda_zero", "always_apply", "matched_random", "noise_floor", "oracle_feature_sgd"], "control arms changed")
    closed(source["locks"], {"fit_lock", "tune_lock", "prediction_lock_before_assessment", "assessment_absence"}, "locks")
    require(source["locks"]["prediction_lock_before_assessment"] is True and source["locks"]["assessment_absence"]["materialization_state"] == "absent" and source["locks"]["assessment_absence"]["entry_count"] == 0, "lock/absence boundary changed")
    closed(source["campaign_manifest_artifact"], {"schema", "path", "materialization", "runtime_manifest_required", "result_root_required", "digest_rule", "required_bindings"}, "campaign_manifest_artifact")
    artifact = source["campaign_manifest_artifact"]
    require(artifact["schema"] == "oaklab.h100.v9.campaign-manifest-artifact.v1" and artifact["path"] == str(CAMPAIGN_ARTIFACT_PATH) and artifact["runtime_manifest_required"] is True and artifact["result_root_required"] is True, "campaign artifact contract changed")
    require(set(artifact["required_bindings"]) == {"source_sha256", "compiler_sha256", "validator_sha256", "tests_sha256", "agents_sha256", "compiled_protocol_file_sha256", "review_packet_sha256", "backend_sha256", "guard_sha256", "model_sha256", "data_sha256", "fit_lock_sha256", "tune_lock_sha256", "tune_lock_receipt_sha256", "provider_allocation_sha256", "provider_cost_sha256", "provider_stop_sha256", "energy_receipt_sha256", "result_root_sha256", "hard_usd_ceiling"}, "campaign binding roster changed")
    closed(source["boundaries"], {"implementation", "synthetic_qualification", "real_execution", "provider", "h100", "phase_836", "oaklab_v6", "oaklab_v7", "oaklab_v8", "plasticity_guard", "astral", "publication"}, "boundaries")
    require(source["boundaries"]["implementation"] == "prohibited_before_independent_ACCEPT" and source["boundaries"]["real_execution"].startswith("prohibited_before_synthetic_candidate"), "execution boundaries changed")
    _validate_algebra(source)
    _validate_execution_schemas(source)
    require(isinstance(source["stop_rules"], list) and len(source["stop_rules"]) == 8 and "without retuning" in source["stop_rules"][-1], "stop rules changed")


def lp32(payload: bytes) -> bytes:
    require(len(payload) <= 0xFFFFFFFF, "payload too large")
    return struct.pack(">I", len(payload)) + payload


def transcript(source_sha256: str, source: dict[str, Any]) -> dict[str, Any]:
    protocol_raw = bytes.fromhex(source_sha256)
    frame = lp32(b"oaklab.h100.v9.prng.v1") + protocol_raw + lp32(b"fit") + lp32(b"sparse_signal_v9") + struct.pack("<Q", 9000) + struct.pack("<I", 0)
    root = hashlib.sha256(frame).digest()
    action_frame = lp32(b"oaklab.h100.v9.action.v1") + protocol_raw + lp32(b"fit") + lp32(b"sparse_signal_v9") + struct.pack("<Q", 9000) + struct.pack("<I", 0)
    return {"frame_hex": frame.hex(), "root_sha256": root.hex(), "first_uniform53": (int.from_bytes(root[:8], "little") >> 11) / float(1 << 53), "action_hash_sha256": hashlib.sha256(action_frame).hexdigest(), "action_probability": source["hash_prng"]["action_assignment"]["probability"]}


def compile_protocol(source: dict[str, Any]) -> dict[str, Any]:
    validate_source(source)
    source_sha256 = sha256_file(ROOT / SOURCE_PATH)
    section_digests = {name: digest(source[name]) for name in SECTIONS}
    payload: dict[str, Any] = {
        "schema": COMPILED_SCHEMA,
        "protocol_id": PROTOCOL_ID,
        "state_slice": STATE_SLICE,
        "compiler_version": COMPILER_VERSION,
        "source_sha256": source_sha256,
        "section_digests": section_digests,
        "sections": {name: source[name] for name in SECTIONS},
        "claim_ceiling": source["claim_ceiling"],
        "boundaries": source["boundaries"],
        "stop_rules": source["stop_rules"],
        "assessment_materialization_state": "absent",
        "execution_gate": {"review_accept_required": True, "packet_binding_required": True, "full_validation_required": True, "synthetic_candidate_required": True, "zero_spend_preflight_required": True, "provider_allocation_required": True, "campaign_manifest_artifact_required": True, "actual_campaign_manifest_path_required": True, "one_bounded_job_maximum": True, "assessment_absent": True, "effects_run": False},
        "campaign_manifest_artifact": source["campaign_manifest_artifact"],
        "transcript_test_vector": transcript(source_sha256, source),
    }
    payload["compiled_protocol_sha256"] = digest(payload)
    return payload


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    parser.add_argument("--output", type=Path, default=COMPILED_PATH)
    args = parser.parse_args()
    source = json.loads((args.repo_root / SOURCE_PATH).read_bytes())
    output = compile_protocol(source)
    (args.repo_root / args.output).write_bytes(canonical(output))
    print(json.dumps({"compiled_protocol_sha256": output["compiled_protocol_sha256"], "output": str(args.output), "state_slice": STATE_SLICE}, sort_keys=True))


if __name__ == "__main__":
    main()
