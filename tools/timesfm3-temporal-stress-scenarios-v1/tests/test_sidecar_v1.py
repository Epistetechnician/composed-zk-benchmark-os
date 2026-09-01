"""Hermetic tests for the TimesFM3 temporal stress-scenario sidecar V1."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest


HERE = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("timesfm3_sidecar_v1_tested", HERE / "sidecar_v1.py")
assert SPEC is not None and SPEC.loader is not None
SIDECAR = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = SIDECAR
SPEC.loader.exec_module(SIDECAR)


def test_strict_json_rejects_duplicate_fields():
    with pytest.raises(SIDECAR.ValidationError, match="duplicate JSON field"):
        SIDECAR.parse_json('{"request_id":"first","request_id":"second"}')


def test_canonical_bytes_are_stable_and_reject_nonfinite_values():
    assert SIDECAR.canonical_bytes({"b": 1, "a": 2}) == b'{"a":2,"b":1}'
    with pytest.raises(SIDECAR.ValidationError, match="canonical JSON"):
        SIDECAR.canonical_bytes({"value": float("nan")})


def _artifact_digest(payload):
    encoded = SIDECAR.canonical_bytes(payload)
    return {
        "algorithm": "sha256",
        "hex_digest": SIDECAR.digest_bytes(encoded),
        "byte_len": len(encoded),
    }


def valid_request():
    series = [
        {
            "series_id": "arrival_rate",
            "timestamps_ms": [0, 1000, 2000, 3000, 4000, 5000, 6000, 7000],
            "values": [2.0, 3.0, 2.5, 4.0, 5.0, 4.5, 6.0, 7.0],
        }
    ]
    covariates = []
    telemetry_payload = {"series": series, "covariates": covariates}
    config = {
        "input_patch_length": 32,
        "output_patch_length": 64,
        "quantiles": [0.1, 0.5, 0.9],
        "use_stitching": True,
        "use_linear_detrending": True,
        "linear_detrending_threshold": 0.5,
        "use_iterative_cpm_revin": True,
        "use_frozen_running_stats": False,
        "use_variate_attention": True,
        "value_clip": 1.0e20,
        "input_transform": "identity",
        "use_sdpa": True,
        "per_core_batch_size": 1,
    }
    model = {
        "model_id": "fake-timesfm3-v1",
        "implementation": "fake_fixture",
        "source_repository": "benchmark-os-fixture",
        "source_revision": "fixture-v1",
        "checkpoint_reference": "fake://timesfm3-v1",
        "checkpoint_revision": "fixture-v1",
        "weight_digest": "f" * 64,
        "config": config,
        "config_digest": SIDECAR.digest_json(config),
    }
    return {
        "schema_version": SIDECAR.REQUEST_SCHEMA_VERSION,
        "state_slice": SIDECAR.STATE_SLICE,
        "request_id": "request-fixture-001",
        "telemetry": {
            "artifact_ref": "fixtures/telemetry.json",
            "artifact_digest": _artifact_digest(telemetry_payload),
            "series": series,
            "covariates": covariates,
        },
        "forecast": {
            "context_length": 8,
            "horizon": 4,
            "quantiles": [0.1, 0.5, 0.9],
            "required_covariate_ids": [],
            "return_quantiles": True,
        },
        "model": model,
        "runtime": {
            "runtime_kind": "fake",
            "python": "fixture",
            "pytorch": "fixture",
            "numpy": "fixture",
            "device": "cpu",
            "same_device_repeat_required": True,
        },
        "network_policy": {
            "acquisition_separate": True,
            "execution_network_enabled": False,
            "local_files_only": True,
        },
        "benchmark_binding": {
            "benchmark_pack_id": "pack-fixture-001",
            "instance_ids": ["instance.counter_loop.001"],
            "semantic_ir_digest": "1" * 64,
            "oracle_digest": "2" * 64,
            "mutation_digest": "3" * 64,
            "scenario_requested": True,
        },
        "claim_boundary": SIDECAR.CLAIM_CEILING,
        "claims": [],
        "non_claims": [
            "forecast_quality_not_measured",
            "not_backend_outcome",
            "not_official_status",
            "not_score_axis",
            "not_authority",
        ],
    }


def test_valid_request_canonical_round_trip():
    request = valid_request()
    assert SIDECAR.validate_request(request) == request
    encoded = SIDECAR.serialize_request(request)
    assert SIDECAR.deserialize_request(encoded) == request


@pytest.mark.parametrize(
    ("change", "message"),
    [
        (lambda request: request.update({"unexpected": True}), "unknown field"),
        (lambda request: request["telemetry"].update({"artifact_ref": "../outside.json"}), "traversal"),
        (lambda request: request["telemetry"]["artifact_digest"].update({"hex_digest": "0" * 64}), "digest mismatch"),
        (lambda request: request["telemetry"]["series"][0]["values"].__setitem__(0, float("nan")), "nonfinite"),
        (lambda request: request["forecast"].update({"context_length": SIDECAR.MAX_CONTEXT_LENGTH + 1}), "allowed bound"),
        (lambda request: request["network_policy"].update({"execution_network_enabled": True}), "must be false"),
        (lambda request: request.update({"claim_boundary": "Level6IndependentlyReproducedEvidence"}), "claim_boundary"),
    ],
)
def test_request_rejects_tampering_and_scope_elevation(change, message):
    request = valid_request()
    change(request)
    with pytest.raises(SIDECAR.ValidationError, match=message):
        SIDECAR.validate_request(request)


def request_with_future_covariate():
    request = valid_request()
    covariate = {
        "covariate_id": "known_pressure",
        "kind": "past_future",
        "artifact_ref": "fixtures/known_pressure.json",
        "timestamps_ms": list(range(0, 12_000, 1000)),
        "values": [1.0 + index / 10 for index in range(12)],
    }
    covariate["artifact_digest"] = _artifact_digest(
        {
            "covariate_id": covariate["covariate_id"],
            "kind": covariate["kind"],
            "timestamps_ms": covariate["timestamps_ms"],
            "values": covariate["values"],
        }
    )
    request["telemetry"]["covariates"] = [covariate]
    request["telemetry"]["artifact_digest"] = _artifact_digest(
        {
            "series": request["telemetry"]["series"],
            "covariates": request["telemetry"]["covariates"],
        }
    )
    request["forecast"]["required_covariate_ids"] = ["known_pressure"]
    return request


def test_request_validates_covariate_identity_and_future_span():
    assert SIDECAR.validate_request(request_with_future_covariate())["forecast"]["required_covariate_ids"] == [
        "known_pressure"
    ]
    missing = valid_request()
    missing["forecast"]["required_covariate_ids"] = ["missing_pressure"]
    with pytest.raises(SIDECAR.ValidationError, match="required covariate is missing"):
        SIDECAR.validate_request(missing)
    short = request_with_future_covariate()
    short["telemetry"]["covariates"][0]["values"] = short["telemetry"]["covariates"][0]["values"][:-1]
    with pytest.raises(SIDECAR.ValidationError, match="timestamp/value lengths differ"):
        SIDECAR.validate_request(short)


def test_fake_model_result_is_deterministic_and_digest_bound():
    request = valid_request()
    result = SIDECAR.run_fake_model(request)
    assert SIDECAR.validate_result(result, request) == result
    assert result["status"] == "completed"
    assert result["point_forecast_artifact"]["shape"] == [1, 4]
    assert result["quantile_forecast_artifact"]["shape"] == [1, 4, 3]
    assert result["repeatability"]["status"] == "same_device_match"
    assert result["repeatability"]["first_output_digest"] == result["output_digest"]
    assert SIDECAR.run_fake_model(request) == result
    encoded = SIDECAR.serialize_result(result, request)
    assert SIDECAR.deserialize_result(encoded, request) == result


@pytest.mark.parametrize(
    ("change", "message"),
    [
        (
            lambda result: result["point_forecast_artifact"].update({"shape": [1, 3]}),
            "does not match request",
        ),
        (
            lambda result: result["point_forecast_artifact"]["values"][0].__setitem__(0, 999.0),
            "artifact_digest digest mismatch",
        ),
        (
            lambda result: result["repeatability"].update({"same_device": False}),
            "same_device must be true",
        ),
        (lambda result: result.update({"input_digest": "0" * 64}), "must not be the zero digest"),
    ],
)
def test_result_rejects_tampering(change, message):
    request = valid_request()
    result = SIDECAR.run_fake_model(request)
    change(result)
    with pytest.raises(SIDECAR.ValidationError, match=message):
        SIDECAR.validate_result(result, request)


def test_result_rejects_unordered_quantiles_even_when_digests_are_rebound():
    request = valid_request()
    result = SIDECAR.run_fake_model(request)
    result["quantile_forecast_artifact"]["values"][0][0] = [2.0, 1.0, 3.0]
    quantile_payload = {
        "shape": result["quantile_forecast_artifact"]["shape"],
        "quantile_levels": result["quantile_forecast_artifact"]["quantile_levels"],
        "values": result["quantile_forecast_artifact"]["values"],
    }
    result["quantile_forecast_artifact"]["artifact_digest"] = _artifact_digest(quantile_payload)
    result["output_digest"] = SIDECAR.digest_json(
        {
            "point_forecast": result["point_forecast_artifact"]["values"],
            "quantile_forecast": quantile_payload["values"],
            "quantile_levels": quantile_payload["quantile_levels"],
        }
    )
    result["repeatability"]["first_output_digest"] = result["output_digest"]
    result["repeatability"]["repeat_output_digest"] = result["output_digest"]
    result["provenance"]["output_digest"] = result["output_digest"]
    with pytest.raises(SIDECAR.ValidationError, match="quantiles are not ordered"):
        SIDECAR.validate_result(result, request)


def test_request_claim_text_is_rejected():
    request = valid_request()
    request["claims"] = ["official benchmark performance"]
    with pytest.raises(SIDECAR.ValidationError, match="forbidden claim"):
        SIDECAR.validate_request(request)


def test_request_rejects_non_string_identity_arrays_as_validation_errors():
    request = valid_request()
    request["benchmark_binding"]["instance_ids"] = [{}]
    with pytest.raises(SIDECAR.ValidationError, match="non-empty string"):
        SIDECAR.validate_request(request)
    request = valid_request()
    request["non_claims"] = [{}]
    with pytest.raises(SIDECAR.ValidationError, match="non-empty string"):
        SIDECAR.validate_request(request)


@pytest.mark.parametrize(
    ("change", "message"),
    [
        (lambda request: request["model"].update({"weight_digest": "e" * 64}), "input_digest mismatch"),
        (lambda request: request["runtime"].update({"device": "mps"}), "fake runtime identity"),
        (lambda request: request["model"]["config"].update({"use_sdpa": False}), "config_digest mismatch"),
    ],
)
def test_changed_identity_changes_bound_digests(change, message):
    request = valid_request()
    result = SIDECAR.run_fake_model(request)
    change(request)
    with pytest.raises(SIDECAR.ValidationError, match=message):
        SIDECAR.validate_result(result, request)


def test_result_rejects_nonfinite_output_and_backend_outcome_fields():
    request = valid_request()
    result = SIDECAR.run_fake_model(request)
    result["point_forecast_artifact"]["values"][0][0] = float("inf")
    with pytest.raises(SIDECAR.ValidationError, match="nonfinite"):
        SIDECAR.validate_result(result, request)
    clean_result = SIDECAR.run_fake_model(request)
    clean_result["backend_outcome"] = "Accepted"
    with pytest.raises(SIDECAR.ValidationError, match="unknown field"):
        SIDECAR.validate_result(clean_result, request)


def test_explicit_failure_statuses_carry_no_forecast_artifacts():
    request = valid_request()
    result = SIDECAR.run_fake_model(request)
    result["status"] = "resource_limited"
    result["output_digest"] = None
    result["point_forecast_artifact"] = None
    result["quantile_forecast_artifact"] = None
    result["repeatability"] = {
        "status": "not_run",
        "device": None,
        "first_output_digest": None,
        "repeat_output_digest": None,
        "same_device": False,
    }
    result["provenance"]["output_digest"] = None
    assert SIDECAR.validate_result(result, request)["status"] == "resource_limited"


def test_scenario_manifest_is_deterministic_and_binds_fixed_cases():
    request = valid_request()
    result = SIDECAR.run_fake_model(request)
    config = {
        "workload_metric": "queue_depth",
        "load_plan": "deterministic_local_shard_plan_v1",
        "rounding": "ceil_nonnegative",
        "max_load": 100,
        "seed": 7,
    }
    manifest = SIDECAR.build_scenario_manifest(result, request, config)
    assert SIDECAR.validate_scenario_manifest(manifest, result, request) == manifest
    assert [arm["arm"] for arm in manifest["arms"]] == ["low", "median", "high"]
    assert {arm["label"] for arm in manifest["arms"]} == {"model_derived_synthetic_input"}
    assert all(arm["fixed_case_ids"] == ["instance.counter_loop.001"] for arm in manifest["arms"])
    assert SIDECAR.build_scenario_manifest(result, request, config) == manifest


def test_scenario_manifest_canonical_round_trip():
    request = valid_request()
    result = SIDECAR.run_fake_model(request)
    manifest = SIDECAR.build_scenario_manifest(
        result,
        request,
        {
            "workload_metric": "queue_depth",
            "load_plan": "deterministic_local_shard_plan_v1",
            "rounding": "ceil_nonnegative",
            "max_load": 100,
            "seed": 7,
        },
    )
    encoded = SIDECAR.serialize_scenario_manifest(manifest, result, request)
    assert SIDECAR.deserialize_scenario_manifest(encoded, result, request) == manifest


@pytest.mark.parametrize(
    ("change", "message"),
    [
        (lambda manifest: manifest["arms"][0].update({"label": "observed_trace"}), "synthetic-input label"),
        (lambda manifest: manifest["arms"][0].update({"fixed_case_ids": ["other-instance"]}), "fixed_case_ids"),
        (lambda manifest: manifest.update({"forecast_output_digest": "f" * 64}), "forecast_output_digest mismatch"),
        (lambda manifest: manifest.update({"manifest_digest": "0" * 64}), "manifest_digest mismatch"),
    ],
)
def test_scenario_manifest_rejects_tampering(change, message):
    request = valid_request()
    result = SIDECAR.run_fake_model(request)
    manifest = SIDECAR.build_scenario_manifest(
        result,
        request,
        {
            "workload_metric": "queue_depth",
            "load_plan": "deterministic_local_shard_plan_v1",
            "rounding": "ceil_nonnegative",
            "max_load": 100,
            "seed": 7,
        },
    )
    change(manifest)
    with pytest.raises(SIDECAR.ValidationError, match=message):
        SIDECAR.validate_scenario_manifest(manifest, result, request)


def test_scenario_manifest_rejects_assessment_selection_after_lock():
    request = valid_request()
    result = SIDECAR.run_fake_model(request)
    manifest = SIDECAR.build_scenario_manifest(
        result,
        request,
        {
            "workload_metric": "queue_depth",
            "load_plan": "deterministic_local_shard_plan_v1",
            "rounding": "ceil_nonnegative",
            "max_load": 100,
            "seed": 7,
        },
    )
    manifest["assessment_selection"] = {"after_prediction_lock": True}
    with pytest.raises(SIDECAR.ValidationError, match="unknown field"):
        SIDECAR.validate_scenario_manifest(manifest, result, request)


def test_cli_fake_execution_is_canonical_and_real_execution_is_withheld(tmp_path):
    request = valid_request()
    request_path = tmp_path / "request.json"
    result_path = tmp_path / "result.json"
    request_path.write_bytes(SIDECAR.serialize_request(request))
    command = [
        sys.executable,
        str(HERE / "run_forecast.py"),
        str(request_path),
        str(result_path),
    ]
    environment = {"PYTHONDONTWRITEBYTECODE": "1", "PYTHONPATH": str(HERE)}
    withheld = subprocess.run(command, capture_output=True, text=True, env=environment)
    assert withheld.returncode != 0
    assert "withheld" in withheld.stderr
    assert not result_path.exists()
    completed = subprocess.run([*command, "--fake-model"], capture_output=True, text=True, env=environment)
    assert completed.returncode == 0, completed.stderr
    result = SIDECAR.deserialize_result(result_path.read_bytes(), request)
    assert result["status"] == "completed"


def test_schema_documents_are_strict_json_objects():
    for name in ("request_schema.json", "result_schema.json", "scenario_schema.json"):
        schema = json.loads((HERE / name).read_text(encoding="utf-8"))
        assert schema["type"] == "object"
        assert schema["additionalProperties"] is False
