#!/usr/bin/env python3
"""Compile the Oak Lab H100 V10 protocol only.

State slice: oaklab-experience-learning-h100-replication-v10.
No learner, dataset, provider, H100, energy, or assessment execution occurs.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import struct
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
STATE_SLICE = "oaklab-experience-learning-h100-replication-v10"
PROTOCOL_ID = "oaklab.h100.v10"
SOURCE_SCHEMA = "oaklab.experience-learning.h100-replication-v10.source.v1"
COMPILED_SCHEMA = "oaklab.experience-learning.h100-replication-v10.compiled.v1"
COMPILER_VERSION = "oaklab.h100.v10.protocol-compiler.v1"
SOURCE_PATH = Path("experiments/experience_learning/oaklab_h100_v10_protocol.json")
COMPILED_PATH = Path("experiments/experience_learning/oaklab_h100_v10_compiled_protocol.json")
SECTIONS = ("estimand", "controller", "generator_roster", "hash_prng", "resource_accounting", "statistics", "controls", "locks", "operation_and_byte_algebra", "execution_schemas", "campaign_manifest_artifact", "boundaries")


def canonical(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False) + "\n").encode("utf-8")


def digest(value: Any) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def closed(value: Any, keys: set[str], label: str) -> None:
    require(isinstance(value, dict) and set(value) == keys, f"{label} object is not closed")


def validate_ast(node: Any) -> None:
    closed(node, {"op", "args"}, "numeric AST node")
    require(node["op"] in {"add", "mul", "sub", "identity"} and isinstance(node["args"], list), "numeric AST operation changed")
    for arg in node["args"]:
        if isinstance(arg, dict):
            validate_ast(arg)
        else:
            require(isinstance(arg, (str, int, float)) and not isinstance(arg, bool), "numeric AST literal invalid")


def validate_source(source: dict[str, Any]) -> None:
    expected = {"schema_version", "protocol_id", "state_slice", "status", "implementation_before_review", "claim_ceiling", *SECTIONS, "stop_rules"}
    closed(source, expected, "source")
    require(source["schema_version"] == SOURCE_SCHEMA and source["protocol_id"] == PROTOCOL_ID and source["state_slice"] == STATE_SLICE, "source identity mismatch")
    require(source["status"] == "frozen_pending_independent_review" and source["implementation_before_review"] is False, "implementation boundary changed")

    e = source["estimand"]
    closed(e, {"name", "unit", "control", "treatment", "primary_endpoint", "favorable_direction", "segment_rows", "trajectory_rows", "warmup_segments", "post_washout_segments", "same_stream", "same_initial_checkpoint", "arm_order_randomized", "trajectory", "carryover_control", "loss_timing", "assessment_absent_until_lock", "utility_formula", "resource_targets"}, "estimand")
    require(e["control"] == "fixed_sgd_b1" and e["treatment"] == "dual_budgeted_credit" and e["segment_rows"] == 32 and e["trajectory_rows"] == 256, "estimand changed")
    require(e["same_stream"] is True and e["same_initial_checkpoint"] is True and e["arm_order_randomized"] is True and e["assessment_absent_until_lock"] is True, "paired or assessment controls missing")
    require("no current outcome" in e["carryover_control"] and "previous completed segment only" in e["carryover_control"], "outcome leakage boundary missing")
    closed(e["resource_targets"], {"active_ops_per_row", "storage_bytes_per_parameter"}, "resource targets")

    c = source["controller"]
    closed(c, {"name", "decision_boundary", "action_rule", "state_fields", "state_bytes", "recurrence", "transition_table", "budgets"}, "controller")
    require(c["state_bytes"] == 62 and len(c["state_fields"]) == 10, "controller state accounting changed")
    names = [row[0] for row in c["state_fields"]]
    require(len(names) == len(set(names)) and {row[2] for row in c["state_fields"]} == {"trajectory", "pending"}, "controller state scope invalid")
    required_pending = {"previous_segment_loss", "previous_segment_ops", "previous_segment_storage"}
    require(required_pending.issubset(names), "pending state incomplete")
    rows = c["transition_table"]
    require(len(rows) == 7 and [row["index"] for row in rows] == list(range(7)), "controller transition indices invalid")
    row_keys = {"index", "event", "reads", "writes", "rule"}
    for row in rows:
        closed(row, row_keys, f"controller transition {row.get('index')}")
        require(isinstance(row["reads"], list) and isinstance(row["writes"], list), "controller read/write schema invalid")
    require("pre-boundary snapshot" in rows[4]["rule"] and "current segment is unread" in rows[4]["rule"], "controller leakage rule missing")
    require("no model action" in rows[6]["rule"], "terminal action rule missing")
    closed(c["budgets"], {"ops_budget", "storage_budget"}, "controller budgets")

    g = source["generator_roster"]
    closed(g, {"stream_order", "rows_per_trajectory", "segment_boundaries", "draw_rule", "draw_roster", "streams"}, "generator roster")
    require(g["rows_per_trajectory"] == 256 and g["segment_boundaries"] == [0, 32, 64, 96, 128, 160, 192, 224, 256], "generator horizon changed")
    require(len(g["stream_order"]) == 6 and set(g["draw_roster"]) == set(g["stream_order"]) == set(g["streams"]), "generator identity changed")
    for stream_id in g["stream_order"]:
        draws = g["draw_roster"][stream_id]
        require(all(isinstance(item, list) and len(item) == 4 for item in draws), f"{stream_id} draw tuple invalid")
        require([item[0] for item in draws] == list(range(len(draws))) and all(isinstance(item[3], int) and item[3] > 0 for item in draws), f"{stream_id} draw order invalid")
        stream = g["streams"][stream_id]
        closed(stream, {"family", "dimension", "equation", "segments", "oracle_features"}, f"{stream_id} stream")
        require(stream["segments"][0] == 0 and stream["segments"][-1] == 256 and all(a < b for a, b in zip(stream["segments"], stream["segments"][1:])), f"{stream_id} segment bounds invalid")
    require("no redraws" in g["draw_rule"] and "future-data reads" in g["draw_rule"], "generator leakage boundary missing")

    h = source["hash_prng"]
    closed(h, {"canonical_json", "digest", "frame", "row_frame", "draw_order", "action_assignment", "test_vector"}, "hash_prng")
    closed(h["action_assignment"], {"fit_only", "probability", "comparison"}, "action assignment")
    require(h["action_assignment"]["fit_only"] is True and h["action_assignment"]["probability"] == {"p_num": 1, "p_den": 2}, "action assignment changed")

    r = source["resource_accounting"]
    closed(r, {"primary_cost", "cost_formula", "controller_boundary_ops", "storage_formula", "controller_state_bytes", "operation_units", "latency", "energy", "replay_bytes", "batch_one", "resource_noninferiority"}, "resource accounting")
    require(r["controller_state_bytes"] == 62 and r["replay_bytes"] == 0 and "one row" in r["batch_one"], "resource accounting changed")

    s = source["statistics"]
    closed(s, {"families", "fit_seeds", "tune_seeds", "assessment_seeds", "repeats", "power", "icc", "minimum_effect", "alpha", "holm", "raw_rows_required", "caller_supplied_booleans_forbidden", "adaptation", "multiplicity_families"}, "statistics")
    require(s["families"] == ["predictable_noise", "drift", "delayed_reward", "event", "long_horizon", "null"] and s["fit_seeds"]["count"] == 48 and s["tune_seeds"]["count"] == 24 and s["assessment_seeds"]["count"] == 48, "statistics roster changed")
    require(s["raw_rows_required"] is True and s["caller_supplied_booleans_forbidden"] is True and "sort raw p" in s["holm"], "statistics derivation boundary changed")

    closed(source["controls"], {"arms", "arm_reset", "null_rule", "ablation_rule"}, "controls")
    require(source["controls"]["arms"] == ["fixed_sgd_b1", "dual_budgeted_credit", "lambda_zero", "always_apply", "matched_random", "noise_floor", "oracle_feature_sgd"], "control roster changed")
    closed(source["locks"], {"fit_lock", "tune_lock", "independent_lock", "prediction_lock_before_assessment", "assessment_absence"}, "locks")
    require(source["locks"]["prediction_lock_before_assessment"] is True and source["locks"]["assessment_absence"]["entry_count"] == 0, "lock boundary changed")

    a = source["operation_and_byte_algebra"]
    closed(a, {"numeric_rules", "formula_ast", "byte_layouts", "resource_invariants"}, "operation algebra")
    require(set(a["formula_ast"]) == {"forward_dense", "loss_half_squared", "gradient", "model_update", "controller_boundary"}, "AST roster changed")
    for item in a["formula_ast"].values():
        closed(item, {"inputs", "output", "ast"}, "formula")
        validate_ast(item["ast"])
    for name in ("counter_row", "lock_receipt", "controller_state"):
        layout = a["byte_layouts"][name]
        closed(layout, {"alignment", "bytes", "fields"}, f"byte layout {name}")
        require(layout["alignment"] == "none" and all(isinstance(field, list) and len(field) == 4 for field in layout["fields"]), f"byte layout {name} invalid")
    require("controller state is charged" in " ".join(a["resource_invariants"]), "controller storage invariant missing")

    x = source["execution_schemas"]
    closed(x, {"counter", "control", "provider", "energy", "result_root"}, "execution schemas")
    closed(x["provider"], {"allocation_schema", "cost_schema", "stop_schema", "currency", "signature", "cross_binding"}, "provider schema")
    require(x["provider"]["currency"] == "USD" and len(x["provider"]["cross_binding"]) == 11, "provider binding changed")
    closed(x["energy"], {"schema", "trace", "formula", "denominator"}, "energy schema")
    closed(x["result_root"], {"mode", "reject_extra_paths", "reject_symlinks", "allowlist"}, "result root schema")
    require(x["result_root"]["mode"] == "closed_world" and x["result_root"]["reject_extra_paths"] is True and x["result_root"]["reject_symlinks"] is True, "result-root closure changed")

    m = source["campaign_manifest_artifact"]
    closed(m, {"schema", "path", "materialization", "runtime_manifest_required", "result_root_required", "digest_rule", "required_bindings"}, "campaign manifest contract")
    require(m["schema"] == "oaklab.h100.v10.campaign-manifest-artifact.v1" and m["runtime_manifest_required"] is True and m["result_root_required"] is True, "campaign manifest contract changed")
    require(set(m["required_bindings"]) == {"source_sha256", "compiler_sha256", "validator_sha256", "tests_sha256", "agents_sha256", "compiled_protocol_file_sha256", "review_packet_sha256", "backend_sha256", "guard_sha256", "model_sha256", "data_sha256", "fit_lock_sha256", "tune_lock_sha256", "tune_lock_receipt_sha256", "provider_allocation_sha256", "provider_cost_sha256", "provider_stop_sha256", "energy_receipt_sha256", "result_root_sha256", "hard_usd_ceiling"}, "campaign binding roster changed")
    require(source["boundaries"]["implementation"] == "prohibited_before_independent_ACCEPT" and source["boundaries"]["real_execution"].startswith("prohibited_before_synthetic_candidate"), "execution boundaries changed")
    require(len(source["stop_rules"]) == 8 and "without retuning" in source["stop_rules"][-1], "stop rules changed")


def lp32(payload: bytes) -> bytes:
    return struct.pack(">I", len(payload)) + payload


def transcript(source_sha256: str) -> dict[str, Any]:
    frame = lp32(b"oaklab.h100.v10.prng.v1") + bytes.fromhex(source_sha256) + lp32(b"fit") + lp32(b"sparse_signal_v10") + struct.pack("<Q", 12000) + struct.pack("<I", 0)
    root = hashlib.sha256(frame).digest()
    action = lp32(b"oaklab.h100.v10.action.v1") + bytes.fromhex(source_sha256) + lp32(b"fit") + lp32(b"sparse_signal_v10") + struct.pack("<Q", 12000) + struct.pack("<I", 0)
    return {"frame_hex": frame.hex(), "root_sha256": root.hex(), "first_uniform53": (int.from_bytes(root[:8], "little") >> 11) / float(1 << 53), "action_hash_sha256": hashlib.sha256(action).hexdigest()}


def compile_protocol(source: dict[str, Any]) -> dict[str, Any]:
    validate_source(source)
    source_sha256 = sha256_file(ROOT / SOURCE_PATH)
    payload = {"schema": COMPILED_SCHEMA, "protocol_id": PROTOCOL_ID, "state_slice": STATE_SLICE, "compiler_version": COMPILER_VERSION, "source_sha256": source_sha256, "section_digests": {name: digest(source[name]) for name in SECTIONS}, "sections": {name: source[name] for name in SECTIONS}, "claim_ceiling": source["claim_ceiling"], "boundaries": source["boundaries"], "stop_rules": source["stop_rules"], "assessment_materialization_state": "absent", "execution_gate": {"review_accept_required": True, "packet_binding_required": True, "full_validation_required": True, "synthetic_candidate_required": True, "zero_spend_preflight_required": True, "provider_allocation_required": True, "campaign_manifest_artifact_required": True, "actual_campaign_manifest_path_required": True, "one_bounded_job_maximum": True, "assessment_absent": True, "effects_run": False}, "transcript_test_vector": transcript(source_sha256)}
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
