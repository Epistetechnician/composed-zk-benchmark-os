"""Hermetic V7 protocol compiler and fail-closed validator tests.

State slice: oaklab-experience-learning-h100-replication-v7.
No learner, model, dataset, provider, H100, paid job, or network execution is
performed by this test module.
"""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from experiments.experience_learning import compile_oaklab_h100_v7_protocol as compiler
from experiments.experience_learning import validate_oaklab_h100_v7_protocol as validator


ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / compiler.SOURCE_PATH
COMPILED = ROOT / compiler.COMPILED_PATH


def _write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(validator.canonical(value))


def _signed(body: dict, private: Ed25519PrivateKey) -> dict:
    public = private.public_key().public_bytes_raw().hex()
    signed_body = {**body, "public_key_hex": public}
    return {**signed_body, "signature_hex": private.sign(validator.canonical(signed_body)).hex(), "receipt_sha256": validator.digest(signed_body)}


def test_compiler_is_deterministic_and_packet_valid():
    first = compiler.compile_protocol(ROOT)
    second = compiler.compile_protocol(ROOT)
    assert first == second
    assert first["strict_contract"]["unknown_fields"] == "reject_at_every_object"
    assert validator.validate_packet(ROOT)["valid"] is True


def test_recursive_estimand_contract_rejects_nested_tamper():
    source = json.loads(SOURCE.read_text(encoding="utf-8"))
    source["estimand"]["post_washout_blocks"] = 31
    with pytest.raises(ValueError, match="estimand"):
        compiler.validate_source(source)


def test_recursive_controller_and_ast_contract_rejects_tamper():
    source = json.loads(SOURCE.read_text(encoding="utf-8"))
    source["controller_transition_table"]["state_fields"][0][1] = "float32[4]"
    with pytest.raises(ValueError, match="controller state types"):
        compiler.validate_source(source)
    source = json.loads(SOURCE.read_text(encoding="utf-8"))
    source["operation_and_byte_algebra"]["formula_ast"]["loss_half_squared"]["ast"]["extra"] = True
    with pytest.raises(ValueError, match="numeric AST"):
        compiler.validate_source(source)


def test_provider_receipts_require_same_node_currency_ceiling_and_interval(tmp_path: Path):
    private = Ed25519PrivateKey.from_private_bytes(bytes(range(32)))
    core = {"schema": "oaklab.h100.v7.campaign.v1", "state_slice": validator.STATE_SLICE, "compiled_protocol_sha256": "1" * 64, "protocol_review_sha256": "2" * 64, "review_packet_sha256": "3" * 64, "code_sha256": "4" * 64, "model_sha256": "5" * 64, "data_sha256": "6" * 64, "backend_sha256": "7" * 64, "guard_sha256": "8" * 64, "hard_usd_ceiling": 5.0}
    core_sha = validator.digest(core)
    manifest = {**core, "fit_lock_sha256": "9" * 64, "tune_lock_sha256": "a" * 64, "tune_lock_receipt_sha256": "b" * 64, "provider_allocation_sha256": "c" * 64, "provider_cost_sha256": "d" * 64, "provider_stop_sha256": "e" * 64, "energy_receipt_sha256": "f" * 64, "result_root_sha256": "0" * 64, "manifest_core_sha256": core_sha, "manifest_sha256": "1" * 64}
    alloc = {"schema": "oaklab.h100.v7.provider-allocation.v1", "state_slice": validator.STATE_SLICE, "allocation_id": "a", "node_id": "node-a", "provider": "givemeanode", "gpu_model": "H100", "start_utc": "2026-08-31T20:00:00Z", "hard_usd_ceiling": 5.0, "launch_manifest_sha256": core_sha}
    cost = {"schema": "oaklab.h100.v7.provider-cost.v1", "state_slice": validator.STATE_SLICE, "allocation_id": "a", "node_id": "node-a", "charged_usd": 1.0, "currency": "USD", "hard_usd_ceiling": 5.0, "launch_manifest_sha256": core_sha}
    stop = {"schema": "oaklab.h100.v7.provider-stop.v1", "state_slice": validator.STATE_SLICE, "allocation_id": "a", "node_id": "node-a", "start_utc": "2026-08-31T20:00:00Z", "stop_utc": "2026-08-31T20:01:00Z", "stop_reason": "bounded", "launch_manifest_sha256": core_sha}
    _write_json(tmp_path / "provider/allocation.json", _signed(alloc, private))
    _write_json(tmp_path / "provider/cost.json", _signed(cost, private))
    _write_json(tmp_path / "provider/stop.json", _signed(stop, private))
    assert validator.validate_provider_receipts(tmp_path, manifest)[0]["node_id"] == "node-a"
    bad = copy.deepcopy(stop); bad["node_id"] = "node-b"; _write_json(tmp_path / "provider/stop.json", _signed(bad, private))
    with pytest.raises(ValueError, match="node|cross-binding"):
        validator.validate_provider_receipts(tmp_path, manifest)


def test_energy_denominator_must_match_counter_total(tmp_path: Path):
    trace = tmp_path / "raw.csv"; trace.write_bytes(b"utc_ns,watts\n0,2\n1000000000,2\n")
    body = {"schema": "oaklab.h100.v7.energy.v1", "state_slice": validator.STATE_SLICE, "trace_sha256": validator.sha256_file(trace), "sample_count": 2, "joules": 2.0, "learned_events": 9, "joules_per_learned_event": 2 / 9, "reference_joules_per_learned_event": 0.2, "formula": "sum(0.5*(w_i+w_i+1)*(t_i+1-t_i)/1e9)", "denominator": "successfully_learned_events"}
    receipt = tmp_path / "joules.json"; _write_json(receipt, {**body, "receipt_sha256": validator.digest(body)})
    with pytest.raises(ValueError, match="counter-derived"):
        validator.validate_energy_receipt(receipt, trace, 10)


def test_counter_and_family_rows_are_closed_and_digest_bound(tmp_path: Path):
    counter = {"schema": "oaklab.h100.v7.counter-rows.v1", "state_slice": validator.STATE_SLICE, "rows": [], "rows_sha256": validator.digest([])}
    row = {"schema": "oaklab.h100.v7.counter-row.v1", "state_slice": validator.STATE_SLICE, "phase": "fit", "cohort": "fit", "family": "drift", "seed": 1, "local_row": 0, "arm_id": "candidate", "learned_events": 1, "active_operations": 2, "parameter_updates": 1, "storage_bytes": 8, "latency_ns": 3}
    row["counter_sha256"] = validator.digest(row)
    counter["rows"] = [row]; counter["rows_sha256"] = validator.digest(counter["rows"])
    path = tmp_path / "counter.json"; _write_json(path, counter)
    assert validator.validate_counter_rows(path)[0]["learned_events"] == 1
    row["local_row"] = 2; _write_json(path, counter)
    with pytest.raises(ValueError, match="row container"):
        validator.validate_counter_rows(path)


def test_holm_and_paired_statistics_are_deterministic():
    stats = validator.paired_stats([-1.0, -1.0, -1.0])
    assert stats["mean_delta"] == -1.0 and stats["raw_p"] == 0.0
    assert validator.holm_adjust({"b": 0.02, "a": 0.01}) == {"a": 0.02, "b": 0.02}


def test_execution_authorization_rejects_unbound_or_missing_accept(tmp_path: Path):
    plan = {"schema": "oaklab.h100.v7.provider-plan.v1", "state_slice": validator.STATE_SLICE, "provider": "givemeanode", "gpu_model": "H100", "hard_usd_ceiling": 1.0, "job_count": 1, "bounded": True, "packet_sha256": "1" * 64, "source_sha256": validator.sha256_file(SOURCE), "compiled_sha256": validator.sha256_file(COMPILED), "campaign_core_sha256": "2" * 64, "manifest_sha256": "3" * 64}
    review = {"schema": "oaklab.h100.v7.protocol-review.v1", "state_slice": validator.STATE_SLICE, "packet_sha256": plan["packet_sha256"], "source_sha256": plan["source_sha256"], "compiled_sha256": plan["compiled_sha256"], "reviewer": "x", "review_decision": "REJECT", "effects_run": False, "findings": {"all": False}, "reviewed_at_utc": "2026-08-31T20:00:00Z", "receipt_sha256": "0" * 64, "signature_hex": "0" * 128, "public_key_hex": "0" * 64}
    synthetic = {"schema": "oaklab.h100.v7.synthetic-qualification.v1", "state_slice": validator.STATE_SLICE, "candidate": True, "source_digest": validator.sha256_file(SOURCE), "result_digest": "4" * 64}
    preflight = {"schema": "oaklab.h100.v7.no-spend-preflight.v1", "state_slice": validator.STATE_SLICE, "spend_usd": 0, "network_access": False, "model_loaded": False, "bounded": True, "receipt_sha256": "0" * 64}
    for name, value in (("plan.json", plan), ("review.json", review), ("synthetic.json", synthetic), ("preflight.json", preflight)):
        _write_json(tmp_path / name, value)
    with pytest.raises(ValueError, match="provider plan|ACCEPT|signature"):
        validator.validate_execution_authorization(tmp_path / "review.json", tmp_path / "synthetic.json", tmp_path / "preflight.json", tmp_path / "plan.json")


def test_compiled_gate_is_fail_closed_before_assessment():
    compiled = compiler.compile_protocol(ROOT)
    assert compiled["execution_gate"]["review_accept_required"] is True
    assert compiled["execution_gate"]["assessment_absent"] is True
    assert compiled["execution_gate"]["effects_run"] is False
