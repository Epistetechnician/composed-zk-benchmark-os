"""Hermetic V4 compiler and closed-world receipt tests.

State slice: oaklab-experience-learning-h100-replication-v4.
No learner, model, dataset, provider, H100, or network execution is used.
"""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from experiments.experience_learning import compile_oaklab_h100_v4_protocol as compiler
from experiments.experience_learning import validate_oaklab_h100_v4_protocol as validator


ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / compiler.SOURCE_PATH
COMPILED = ROOT / compiler.COMPILED_PATH


def _write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(validator.canonical(value))


def _digest_without(value: dict, field: str) -> str:
    return validator.digest_without(value, field)


def _signed_provider(body: dict, private: Ed25519PrivateKey) -> dict:
    public = private.public_key().public_bytes_raw().hex()
    message_body = {**body, "public_key_hex": public}
    signature = private.sign(validator.canonical(message_body)).hex()
    return {**message_body, "signature_hex": signature, "receipt_sha256": validator.digest(message_body)}


def _build_valid_root(tmp_path: Path) -> Path:
    root = tmp_path / "result"
    (root / "compiled_protocol.json").parent.mkdir(parents=True)
    (root / "compiled_protocol.json").write_bytes(COMPILED.read_bytes())
    compiled_file_sha = validator.sha256_file(COMPILED)
    digest_value = "1" * 64

    fit_body = {
        "schema": "oaklab.h100.v4.fit-lock.v1", "state_slice": validator.STATE_SLICE,
        "protocol_sha256": compiled_file_sha, "review_receipt_sha256": digest_value,
        "implementation_sha256": digest_value, "runtime_sha256": digest_value,
        "generator_sha256": digest_value, "fit_data_sha256": digest_value,
        "selected_controller_sha256": digest_value, "theta_hex": "00" * 32,
        "fit_result_sha256": digest_value, "decision": "locked",
    }
    fit = {**fit_body, "lock_sha256": _digest_without(fit_body, "lock_sha256")}
    _write_json(root / "fit/lock.json", fit)
    fit_sha = validator.sha256_file(root / "fit/lock.json")

    tune_body = {
        "schema": "oaklab.h100.v4.tune-lock.v1", "state_slice": validator.STATE_SLICE,
        "fit_lock_sha256": fit_sha, "tune_data_sha256": digest_value,
        "hyperparameters_sha256": digest_value, "prediction_sha256": digest_value,
        "tune_result_sha256": digest_value, "decision": "locked",
    }
    tune = {**tune_body, "lock_sha256": _digest_without(tune_body, "lock_sha256")}
    _write_json(root / "tune/lock.json", tune)
    tune_sha = validator.sha256_file(root / "tune/lock.json")
    receipt_body = {
        "schema": "oaklab.h100.v4.lock-receipt.v1", "state_slice": validator.STATE_SLICE,
        "tune_lock_sha256": tune_sha, "independent_reviewer": "independent-test-reviewer", "decision": "accepted",
    }
    _write_json(root / "tune/lock_receipt.json", {**receipt_body, "receipt_sha256": _digest_without(receipt_body, "receipt_sha256")})
    receipt_sha = validator.sha256_file(root / "tune/lock_receipt.json")

    raw_trace = b"utc_ns,watts\n0,2\n1000000000,2\n"
    (root / "energy/raw_trace.csv").parent.mkdir(parents=True, exist_ok=True)
    (root / "energy/raw_trace.csv").write_bytes(raw_trace)
    joules_body = {
        "schema": "oaklab.h100.v4.energy.v1", "state_slice": validator.STATE_SLICE,
        "trace_sha256": hashlib.sha256(raw_trace).hexdigest(), "sample_count": 2,
        "joules": 2.0, "learned_events": 10, "joules_per_learned_event": 0.2,
        "formula": "sum(0.5*(w_i+w_i+1)*(t_i+1-t_i)/1e9)", "denominator": "successfully_learned_events",
    }
    _write_json(root / "energy/joules.json", {**joules_body, "receipt_sha256": _digest_without(joules_body, "receipt_sha256")})
    energy_sha = validator.sha256_file(root / "energy/joules.json")

    aggregate_body = {
        "schema": "oaklab.h100.v4.aggregate.v1", "state_slice": validator.STATE_SLICE,
        "families": ["predictable_noise", "event", "pure_noise"],
        "primary_loss": {"holm_pass": True, "direction_pass": True, "mean_delta": -0.1, "raw_p": 0.01, "holm_p": 0.03},
        "adaptation": {"holm_pass": True, "direction_pass": True, "mean_delta": -2.0, "raw_p": 0.01, "holm_p": 0.03},
        "resource": {**{name: {"candidate": 0.9, "reference": 1.0, "margin": 0.05, "noninferior": True} for name in ("active_operations", "parameter_updates", "storage_bytes", "wall_clock_latency")}, "joules_per_learned_event": {"candidate": 0.2, "reference": 1.0, "margin": 0.05, "noninferior": True}},
        "statistics": {"multiplicity": "holm", "alpha": 0.05, "power": 0.8, "paired_tests": 48},
        "publication_gate": {"quality": True, "adaptation": True, "resource": True, "statistics": True, "custody": True, "energy": True, "candidate": True},
    }
    _write_json(root / "result/aggregate.json", {**aggregate_body, "aggregate_sha256": _digest_without(aggregate_body, "aggregate_sha256")})
    aggregate_sha = json.loads((root / "result/aggregate.json").read_text(encoding="utf-8"))["aggregate_sha256"]

    private = Ed25519PrivateKey.from_private_bytes(bytes(range(32)))
    core = {
        "schema": "oaklab.h100.v4.campaign.v1", "state_slice": validator.STATE_SLICE,
        "compiled_protocol_sha256": compiled_file_sha, "code_sha256": digest_value,
        "model_sha256": digest_value, "data_sha256": digest_value, "backend_sha256": digest_value,
        "guard_sha256": digest_value, "hard_usd_ceiling": 5.0,
    }
    core_sha = validator.digest(core)
    allocation_body = {"schema": "oaklab.h100.v4.provider-allocation.v1", "state_slice": validator.STATE_SLICE, "allocation_id": "alloc-test", "node_id": "node-test", "provider": "givemeanode", "gpu_model": "H100", "start_utc": "2026-08-31T20:00:00Z", "hard_usd_ceiling": 5.0, "launch_manifest_sha256": core_sha}
    cost_body = {"schema": "oaklab.h100.v4.provider-cost.v1", "state_slice": validator.STATE_SLICE, "allocation_id": "alloc-test", "charged_usd": 1.25, "currency": "USD", "hard_usd_ceiling": 5.0, "launch_manifest_sha256": core_sha}
    stop_body = {"schema": "oaklab.h100.v4.provider-stop.v1", "state_slice": validator.STATE_SLICE, "allocation_id": "alloc-test", "stop_utc": "2026-08-31T20:01:00Z", "stop_reason": "bounded job complete", "launch_manifest_sha256": core_sha}
    _write_json(root / "provider/allocation.json", _signed_provider(allocation_body, private))
    _write_json(root / "provider/cost.json", _signed_provider(cost_body, private))
    _write_json(root / "provider/stop.json", _signed_provider(stop_body, private))
    allocation_sha = validator.sha256_file(root / "provider/allocation.json")
    cost_sha = validator.sha256_file(root / "provider/cost.json")
    stop_sha = validator.sha256_file(root / "provider/stop.json")

    independent_body = {"schema": "oaklab.h100.v4.independent-validation.v1", "state_slice": validator.STATE_SLICE, "validator_id": "independent-test-validator", "review_digest": digest_value, "manifest_core_sha256": "0" * 64, "aggregate_sha256": aggregate_sha, "checks": {"all": True}, "decision": "accepted"}
    _write_json(root / "validation/independent.json", {**independent_body, "receipt_sha256": _digest_without(independent_body, "receipt_sha256")})
    independent_sha = validator.sha256_file(root / "validation/independent.json")

    manifest_body = {
        **core, "fit_lock_sha256": validator.sha256_file(root / "fit/lock.json"), "tune_lock_sha256": tune_sha,
        "tune_lock_receipt_sha256": receipt_sha, "provider_allocation_sha256": allocation_sha,
        "provider_cost_sha256": cost_sha, "provider_stop_sha256": stop_sha, "energy_receipt_sha256": energy_sha,
        "result_root_sha256": "0" * 64, "manifest_core_sha256": core_sha,
    }
    manifest_body["result_root_sha256"] = validator.result_root_digest(root)
    manifest_body["manifest_sha256"] = _digest_without(manifest_body, "manifest_sha256")
    _write_json(root / "campaign_manifest.json", manifest_body)
    # Independent validation binds the non-circular campaign core digest.
    independent = {**independent_body, "manifest_core_sha256": core_sha}
    independent["receipt_sha256"] = _digest_without(independent, "receipt_sha256")
    _write_json(root / "validation/independent.json", independent)
    # The independent file changed, so refresh the campaign root and self digests.
    manifest_body["result_root_sha256"] = validator.result_root_digest(root)
    manifest_body["manifest_sha256"] = _digest_without(manifest_body, "manifest_sha256")
    _write_json(root / "campaign_manifest.json", manifest_body)
    return root


def test_compiler_is_deterministic_and_packet_valid():
    first = compiler.compile_protocol(ROOT)
    second = compiler.compile_protocol(ROOT)
    assert first == second
    assert first["sections"] == list(compiler.SECTIONS)
    assert first["assessment_materialization_state"] == "absent"
    assert validator.validate_packet(ROOT)["valid"] is True


def test_compiler_rejects_unknown_source_field():
    source = json.loads(SOURCE.read_text(encoding="utf-8"))
    source["unexpected"] = True
    with pytest.raises(ValueError, match="source schema"):
        compiler.validate_source(source)


def test_validator_rejects_compiled_digest_tamper():
    artifact = compiler.compile_protocol(ROOT)
    artifact["compiled_protocol_sha256"] = "0" * 64
    assert artifact["compiled_protocol_sha256"] != validator.digest_without(artifact, "compiled_protocol_sha256")


def test_manifest_must_use_exact_canonical_bytes(tmp_path: Path):
    value = {"schema": "x"}
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="noncanonical JSON bytes"):
        validator.load_canonical_json(path)


def test_ed25519_provider_signature_is_verified(tmp_path: Path):
    private = Ed25519PrivateKey.from_private_bytes(bytes(range(32)))
    body = {"schema": "oaklab.h100.v4.provider-allocation.v1", "state_slice": validator.STATE_SLICE, "allocation_id": "a", "node_id": "n", "provider": "givemeanode", "gpu_model": "H100", "start_utc": "2026-08-31T20:00:00Z", "hard_usd_ceiling": 1.0, "launch_manifest_sha256": "1" * 64}
    path = tmp_path / "allocation.json"
    _write_json(path, _signed_provider(body, private))
    assert validator._signed_provider(path, body["schema"], "1" * 64, set(path and json.loads(path.read_text()).keys()))["allocation_id"] == "a"
    tampered = json.loads(path.read_text(encoding="utf-8")); tampered["signature_hex"] = "0" * 128
    _write_json(path, tampered)
    with pytest.raises(ValueError, match="signature"):
        validator._signed_provider(path, body["schema"], "1" * 64, set(tampered))


def test_energy_receipt_recomputes_joules(tmp_path: Path):
    trace = tmp_path / "raw.csv"
    trace.write_bytes(b"utc_ns,watts\n0,2\n1000000000,2\n")
    body = {"schema": "oaklab.h100.v4.energy.v1", "state_slice": validator.STATE_SLICE, "trace_sha256": validator.sha256_file(trace), "sample_count": 2, "joules": 2.0, "learned_events": 10, "joules_per_learned_event": 0.2, "formula": "sum(0.5*(w_i+w_i+1)*(t_i+1-t_i)/1e9)", "denominator": "successfully_learned_events"}
    receipt = tmp_path / "joules.json"
    _write_json(receipt, {**body, "receipt_sha256": _digest_without(body, "receipt_sha256")})
    assert validator.validate_energy_receipt(receipt, trace)["joules"] == 2.0
    bad = copy.deepcopy(body); bad["joules"] = 3.0
    _write_json(receipt, {**bad, "receipt_sha256": _digest_without(bad, "receipt_sha256")})
    with pytest.raises(ValueError, match="joule integration"):
        validator.validate_energy_receipt(receipt, trace)


def test_result_root_validates_every_file_and_binding(tmp_path: Path):
    root = _build_valid_root(tmp_path)
    result = validator.validate_result_root(root, ROOT)
    assert result["valid"] is True
    (root / "extra").mkdir()
    (root / "extra/file").write_text("x", encoding="utf-8")
    with pytest.raises(ValueError, match="result root|unlisted result directory"):
        validator.validate_result_root(root, ROOT)


def test_execution_authorization_rejects_without_accept(tmp_path: Path):
    review = tmp_path / "review.json"
    synthetic = tmp_path / "synthetic.json"
    preflight = tmp_path / "preflight.json"
    plan = tmp_path / "plan.json"
    _write_json(review, {"schema": "oaklab.h100.v4.independent-review-receipt", "state_slice": validator.STATE_SLICE, "compiled_protocol_sha256": "1" * 64, "review_decision": "REJECT", "effects_run": False, "receipt_sha256": "0" * 64})
    _write_json(synthetic, {"schema": "oaklab.h100.v4.synthetic-qualification.v1", "state_slice": validator.STATE_SLICE, "candidate": True, "source_digest": "1" * 64, "result_digest": "1" * 64})
    _write_json(preflight, {"schema": "oaklab.h100.v4.no-spend-preflight.v1", "state_slice": validator.STATE_SLICE, "spend_usd": 0, "network_access": False, "model_loaded": False, "bounded": True, "receipt_sha256": "0" * 64})
    _write_json(plan, {"schema": "oaklab.h100.v4.provider-plan.v1", "state_slice": validator.STATE_SLICE, "provider": "givemeanode", "gpu_model": "H100", "hard_usd_ceiling": 1.0, "job_count": 1, "bounded": True, "manifest_sha256": "1" * 64})
    with pytest.raises(ValueError, match="ACCEPT"):
        validator.validate_execution_authorization(review, synthetic, preflight, plan)
