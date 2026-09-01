"""Bounded TimesFM3 temporal stress-scenario sidecar contracts.

State slice: timesfm3-temporal-stress-scenarios-v1.
"""

from __future__ import annotations

import json
import hashlib
import math
import re
from typing import Any


STATE_SLICE = "timesfm3-temporal-stress-scenarios-v1"
REQUEST_SCHEMA_VERSION = "timesfm3-temporal-stress-scenarios-request-v1"
RESULT_SCHEMA_VERSION = "timesfm3-temporal-stress-scenarios-result-v1"
SCENARIO_SCHEMA_VERSION = "timesfm3-temporal-stress-scenarios-scenario-v1"
CLAIM_CEILING = "LocalDevelopmentTimesFM3TemporalStressScenarioQualificationV1"
REAL_MODEL_ID = "google/timesfm-3.0-pytorch"
FAKE_MODEL_ID = "fake-timesfm3-v1"
TIMESFM_SOURCE_REPOSITORY = "google-research/timesfm"
TIMESFM_SOURCE_REVISION = "331c6d33cb1ac2611de3056d0ac7164aab6301eb"
CHECKPOINT_REVISION = "900fcab43d1bfe71733a33b3fec61a41fce28a27"
MAX_SERIES = 32
MAX_CONTEXT_LENGTH = 15_360
MAX_HORIZON = 1_024
MAX_COVARIATES = 31
MAX_ARTIFACT_BYTES = 4 * 1024 * 1024
MAX_LIST_ITEMS = 10_000
QUANTILE_LEVELS = (0.1, 0.5, 0.9)
SCENARIO_ARMS = ("low", "median", "high")
WORKLOAD_METRICS = (
    "arrival_rate",
    "queue_depth",
    "trace_length",
    "recursion_depth",
    "context_size",
    "memory_pressure",
    "latency_demand",
    "workload_volume",
)
NON_CLAIM_CODES = {
    "forecast_quality_not_measured",
    "not_backend_outcome",
    "not_official_status",
    "not_score_axis",
    "not_authority",
    "not_proof_evidence",
}
FORBIDDEN_CLAIM_TERMS = (
    "proof",
    "soundness",
    "official benchmark",
    "zk performance",
    "formal validity",
)
_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
_HEX_RE = re.compile(r"^[0-9a-f]{64}$")


class ValidationError(ValueError):
    """Raised when a sidecar contract fails closed."""


def _reject_constant(value: str) -> None:
    raise ValidationError(f"nonfinite JSON constant: {value}")


def _reject_duplicate(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValidationError(f"duplicate JSON field: {key}")
        result[key] = value
    return result


def parse_json(payload: str | bytes) -> Any:
    """Parse JSON while rejecting duplicate keys and nonstandard constants."""

    try:
        return json.loads(
            payload,
            object_pairs_hook=_reject_duplicate,
            parse_constant=_reject_constant,
        )
    except ValidationError:
        raise
    except (TypeError, json.JSONDecodeError) as exc:
        raise ValidationError(f"invalid JSON: {exc}") from exc


def canonical_bytes(value: Any) -> bytes:
    """Encode a value using the sidecar's deterministic JSON representation."""

    try:
        return json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise ValidationError(f"value is not canonical JSON: {exc}") from exc


def digest_bytes(value: bytes) -> str:
    """Return the lowercase SHA-256 digest for bytes."""

    return hashlib.sha256(value).hexdigest()


def digest_json(value: Any) -> str:
    """Return the SHA-256 digest of canonical JSON bytes."""

    return digest_bytes(canonical_bytes(value))


def _ensure_finite(value: Any, path: str) -> None:
    if isinstance(value, bool):
        return
    if isinstance(value, float) and not math.isfinite(value):
        raise ValidationError(f"{path} contains a nonfinite value")
    if isinstance(value, dict):
        for key, child in value.items():
            _ensure_finite(child, f"{path}.{key}")
    elif isinstance(value, (list, tuple)):
        for index, child in enumerate(value):
            _ensure_finite(child, f"{path}[{index}]")


def _object(value: Any, path: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValidationError(f"{path} must be an object")
    if not all(isinstance(key, str) for key in value):
        raise ValidationError(f"{path} has a non-string field name")
    return value


def _fields(
    value: Any,
    required: set[str],
    optional: set[str],
    path: str,
) -> dict[str, Any]:
    result = _object(value, path)
    missing = sorted(required - result.keys())
    if missing:
        raise ValidationError(f"{path} missing required field: {missing[0]}")
    unknown = sorted(result.keys() - required - optional)
    if unknown:
        raise ValidationError(f"{path} has unknown field: {unknown[0]}")
    return result


def _string(value: Any, path: str, *, pattern: re.Pattern[str] | None = None) -> str:
    if not isinstance(value, str) or not value:
        raise ValidationError(f"{path} must be a non-empty string")
    if pattern is not None and pattern.fullmatch(value) is None:
        raise ValidationError(f"{path} has an invalid format")
    return value


def _bool(value: Any, path: str) -> bool:
    if not isinstance(value, bool):
        raise ValidationError(f"{path} must be boolean")
    return value


def _integer(value: Any, path: str, *, minimum: int = 0, maximum: int | None = None) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValidationError(f"{path} must be an integer")
    if value < minimum or (maximum is not None and value > maximum):
        raise ValidationError(f"{path} is outside the allowed bound")
    return value


def _number(value: Any, path: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValidationError(f"{path} must be numeric")
    result = float(value)
    if not math.isfinite(result):
        raise ValidationError(f"{path} is nonfinite")
    return result


def _list(value: Any, path: str, *, minimum: int = 0, maximum: int = MAX_LIST_ITEMS) -> list[Any]:
    if not isinstance(value, list):
        raise ValidationError(f"{path} must be an array")
    if len(value) < minimum or len(value) > maximum:
        raise ValidationError(f"{path} has an invalid length")
    return value


def _identifier(value: Any, path: str) -> str:
    return _string(value, path, pattern=_ID_RE)


def _relative_ref(value: Any, path: str) -> str:
    ref = _string(value, path)
    if "\\" in ref or "\x00" in ref or ref.startswith("/"):
        raise ValidationError(f"{path} must be a relative path")
    parts = ref.split("/")
    if any(part in ("", ".", "..") for part in parts):
        raise ValidationError(f"{path} must not contain traversal")
    return ref


def _digest(value: Any, path: str) -> dict[str, Any]:
    result = _fields(value, {"algorithm", "hex_digest", "byte_len"}, set(), path)
    if result["algorithm"] != "sha256":
        raise ValidationError(f"{path}.algorithm must be sha256")
    digest = _string(result["hex_digest"], f"{path}.hex_digest")
    if _HEX_RE.fullmatch(digest) is None:
        raise ValidationError(f"{path}.hex_digest must be lowercase SHA-256")
    _integer(result["byte_len"], f"{path}.byte_len", maximum=MAX_ARTIFACT_BYTES)
    return result


def _artifact_ref(value: Any, path: str) -> dict[str, Any]:
    result = _fields(value, {"artifact_ref", "artifact_digest"}, set(), path)
    _relative_ref(result["artifact_ref"], f"{path}.artifact_ref")
    _digest(result["artifact_digest"], f"{path}.artifact_digest")
    return result


def _same_digest(actual: dict[str, Any], expected: dict[str, Any], path: str) -> None:
    if actual != expected:
        raise ValidationError(f"{path} digest mismatch")


def _validate_finite_values(value: Any, path: str) -> None:
    _ensure_finite(value, path)


def _validate_claims(value: Any, path: str) -> list[str]:
    claims = _list(value, path, maximum=64)
    for index, claim in enumerate(claims):
        text = _string(claim, f"{path}[{index}]").lower()
        if any(term in text for term in FORBIDDEN_CLAIM_TERMS):
            raise ValidationError(f"{path}[{index}] contains a forbidden claim")
    return claims


def _validate_non_claims(value: Any, path: str) -> list[str]:
    codes = _list(value, path, minimum=1, maximum=32)
    for index, code in enumerate(codes):
        code = _string(code, f"{path}[{index}]")
        if code not in NON_CLAIM_CODES:
            raise ValidationError(f"{path}[{index}] is not a recognized non-claim")
    if len(set(codes)) != len(codes):
        raise ValidationError(f"{path} contains duplicate codes")
    return codes


def _hex_digest(value: Any, path: str, *, allow_zero: bool = True) -> str:
    digest = _string(value, path)
    if _HEX_RE.fullmatch(digest) is None:
        raise ValidationError(f"{path} must be lowercase SHA-256")
    if not allow_zero and digest == "0" * 64:
        raise ValidationError(f"{path} must not be the zero digest")
    return digest


def _quantiles(value: Any, path: str) -> list[float]:
    values = _list(value, path, minimum=3, maximum=3)
    parsed = [_number(item, f"{path}[{index}]") for index, item in enumerate(values)]
    if parsed != list(QUANTILE_LEVELS):
        raise ValidationError(f"{path} must be exactly q10, q50, q90")
    return parsed


def _validate_series(value: Any, path: str) -> dict[str, Any]:
    result = _fields(value, {"series_id", "timestamps_ms", "values"}, set(), path)
    _identifier(result["series_id"], f"{path}.series_id")
    timestamps = _list(
        result["timestamps_ms"],
        f"{path}.timestamps_ms",
        minimum=1,
        maximum=MAX_CONTEXT_LENGTH + MAX_HORIZON,
    )
    previous = None
    for index, timestamp in enumerate(timestamps):
        timestamp = _integer(timestamp, f"{path}.timestamps_ms[{index}]")
        if previous is not None and timestamp <= previous:
            raise ValidationError(f"{path}.timestamps_ms must be strictly increasing")
        previous = timestamp
    values = _list(
        result["values"],
        f"{path}.values",
        minimum=1,
        maximum=MAX_CONTEXT_LENGTH + MAX_HORIZON,
    )
    if len(values) != len(timestamps):
        raise ValidationError(f"{path} timestamp/value lengths differ")
    for index, item in enumerate(values):
        _number(item, f"{path}.values[{index}]")
    return result


def _validate_covariate(value: Any, path: str) -> dict[str, Any]:
    result = _fields(
        value,
        {"covariate_id", "kind", "artifact_ref", "artifact_digest", "timestamps_ms", "values"},
        set(),
        path,
    )
    _identifier(result["covariate_id"], f"{path}.covariate_id")
    if result["kind"] not in ("past_only", "past_future"):
        raise ValidationError(f"{path}.kind is not recognized")
    _relative_ref(result["artifact_ref"], f"{path}.artifact_ref")
    _digest(result["artifact_digest"], f"{path}.artifact_digest")
    timestamps = _list(
        result["timestamps_ms"],
        f"{path}.timestamps_ms",
        minimum=1,
        maximum=MAX_CONTEXT_LENGTH + MAX_HORIZON,
    )
    previous = None
    for index, timestamp in enumerate(timestamps):
        timestamp = _integer(timestamp, f"{path}.timestamps_ms[{index}]")
        if previous is not None and timestamp <= previous:
            raise ValidationError(f"{path}.timestamps_ms must be strictly increasing")
        previous = timestamp
    values = _list(
        result["values"],
        f"{path}.values",
        minimum=1,
        maximum=MAX_CONTEXT_LENGTH + MAX_HORIZON,
    )
    if len(values) != len(timestamps):
        raise ValidationError(f"{path} timestamp/value lengths differ")
    for index, item in enumerate(values):
        _number(item, f"{path}.values[{index}]")
    payload = {
        "covariate_id": result["covariate_id"],
        "kind": result["kind"],
        "timestamps_ms": result["timestamps_ms"],
        "values": result["values"],
    }
    encoded = canonical_bytes(payload)
    expected = {
        "algorithm": "sha256",
        "hex_digest": digest_bytes(encoded),
        "byte_len": len(encoded),
    }
    _same_digest(result["artifact_digest"], expected, f"{path}.artifact_digest")
    return result


def _validate_model(value: Any, forecast_quantiles: list[float], path: str) -> dict[str, Any]:
    result = _fields(
        value,
        {
            "model_id",
            "implementation",
            "source_repository",
            "source_revision",
            "checkpoint_reference",
            "checkpoint_revision",
            "weight_digest",
            "config",
            "config_digest",
        },
        set(),
        path,
    )
    model_id = _string(result["model_id"], f"{path}.model_id")
    implementation = _string(result["implementation"], f"{path}.implementation")
    if (model_id, implementation) == (FAKE_MODEL_ID, "fake_fixture"):
        expected_identity = (
            "benchmark-os-fixture",
            "fixture-v1",
            "fake://timesfm3-v1",
            "fixture-v1",
        )
    elif (model_id, implementation) == (REAL_MODEL_ID, "timesfm3_external"):
        expected_identity = (
            TIMESFM_SOURCE_REPOSITORY,
            TIMESFM_SOURCE_REVISION,
            REAL_MODEL_ID,
            CHECKPOINT_REVISION,
        )
    else:
        raise ValidationError(f"{path} has an unrecognized model identity")
    for field, expected in zip(
        ("source_repository", "source_revision", "checkpoint_reference", "checkpoint_revision"),
        expected_identity,
    ):
        if result[field] != expected:
            raise ValidationError(f"{path}.{field} does not match the model identity")
    _hex_digest(result["weight_digest"], f"{path}.weight_digest", allow_zero=model_id == FAKE_MODEL_ID)
    config = _object(result["config"], f"{path}.config")
    _fields(
        config,
        {
            "input_patch_length",
            "output_patch_length",
            "quantiles",
            "use_stitching",
            "use_linear_detrending",
            "linear_detrending_threshold",
            "use_iterative_cpm_revin",
            "use_frozen_running_stats",
            "use_variate_attention",
            "value_clip",
            "input_transform",
            "use_sdpa",
            "per_core_batch_size",
        },
        set(),
        f"{path}.config",
    )
    _integer(config["input_patch_length"], f"{path}.config.input_patch_length", minimum=1, maximum=1024)
    _integer(config["output_patch_length"], f"{path}.config.output_patch_length", minimum=1, maximum=1024)
    if _quantiles(config["quantiles"], f"{path}.config.quantiles") != forecast_quantiles:
        raise ValidationError(f"{path}.config.quantiles do not match forecast.quantiles")
    for field in (
        "use_stitching",
        "use_linear_detrending",
        "use_iterative_cpm_revin",
        "use_frozen_running_stats",
        "use_variate_attention",
        "use_sdpa",
    ):
        _bool(config[field], f"{path}.config.{field}")
    _number(config["linear_detrending_threshold"], f"{path}.config.linear_detrending_threshold")
    if _number(config["value_clip"], f"{path}.config.value_clip") <= 0:
        raise ValidationError(f"{path}.config.value_clip must be positive")
    _string(config["input_transform"], f"{path}.config.input_transform")
    _integer(config["per_core_batch_size"], f"{path}.config.per_core_batch_size", minimum=1, maximum=1024)
    if result["config_digest"] != digest_json(config):
        raise ValidationError(f"{path}.config_digest mismatch")
    return result


def _validate_runtime(value: Any, path: str) -> dict[str, Any]:
    result = _fields(
        value,
        {"runtime_kind", "python", "pytorch", "numpy", "device", "same_device_repeat_required"},
        set(),
        path,
    )
    runtime_kind = _string(result["runtime_kind"], f"{path}.runtime_kind")
    device = _string(result["device"], f"{path}.device")
    if runtime_kind == "fake":
        if device != "cpu" or any(result[field] != "fixture" for field in ("python", "pytorch", "numpy")):
            raise ValidationError(f"{path} fake runtime identity is invalid")
    elif runtime_kind == "pytorch":
        if device not in ("cpu", "mps", "cuda"):
            raise ValidationError(f"{path}.device is unrecognized")
        for field in ("python", "pytorch", "numpy"):
            _string(result[field], f"{path}.{field}")
    else:
        raise ValidationError(f"{path}.runtime_kind is unrecognized")
    _bool(result["same_device_repeat_required"], f"{path}.same_device_repeat_required")
    if not result["same_device_repeat_required"]:
        raise ValidationError(f"{path}.same_device_repeat_required must be true")
    return result


def _validate_network_policy(value: Any, path: str) -> dict[str, Any]:
    result = _fields(
        value,
        {"acquisition_separate", "execution_network_enabled", "local_files_only"},
        set(),
        path,
    )
    if not _bool(result["acquisition_separate"], f"{path}.acquisition_separate"):
        raise ValidationError(f"{path}.acquisition_separate must be true")
    if _bool(result["execution_network_enabled"], f"{path}.execution_network_enabled"):
        raise ValidationError(f"{path}.execution_network_enabled must be false")
    if not _bool(result["local_files_only"], f"{path}.local_files_only"):
        raise ValidationError(f"{path}.local_files_only must be true")
    return result


def _validate_benchmark_binding(value: Any, path: str) -> dict[str, Any]:
    result = _fields(
        value,
        {
            "benchmark_pack_id",
            "instance_ids",
            "semantic_ir_digest",
            "oracle_digest",
            "mutation_digest",
            "scenario_requested",
        },
        set(),
        path,
    )
    _identifier(result["benchmark_pack_id"], f"{path}.benchmark_pack_id")
    instance_ids = _list(result["instance_ids"], f"{path}.instance_ids", minimum=1, maximum=1024)
    for index, instance_id in enumerate(instance_ids):
        _identifier(instance_id, f"{path}.instance_ids[{index}]")
    if len(set(instance_ids)) != len(instance_ids):
        raise ValidationError(f"{path}.instance_ids contains duplicates")
    for field in ("semantic_ir_digest", "oracle_digest", "mutation_digest"):
        _hex_digest(result[field], f"{path}.{field}")
    _bool(result["scenario_requested"], f"{path}.scenario_requested")
    if not result["scenario_requested"]:
        raise ValidationError(f"{path}.scenario_requested must be true for this slice")
    return result


def validate_request(request: Any) -> dict[str, Any]:
    """Validate a complete canonical sidecar request and return it unchanged."""

    result = _fields(
        request,
        {
            "schema_version",
            "state_slice",
            "request_id",
            "telemetry",
            "forecast",
            "model",
            "runtime",
            "network_policy",
            "benchmark_binding",
            "claim_boundary",
            "claims",
            "non_claims",
        },
        set(),
        "request",
    )
    if result["schema_version"] != REQUEST_SCHEMA_VERSION:
        raise ValidationError("request.schema_version is unsupported")
    if result["state_slice"] != STATE_SLICE:
        raise ValidationError("request.state_slice mismatch")
    _identifier(result["request_id"], "request.request_id")
    _validate_claims(result["claims"], "request.claims")
    _validate_non_claims(result["non_claims"], "request.non_claims")
    _ensure_finite(result, "request")

    telemetry = _fields(
        result["telemetry"],
        {"artifact_ref", "artifact_digest", "series", "covariates"},
        set(),
        "request.telemetry",
    )
    _relative_ref(telemetry["artifact_ref"], "request.telemetry.artifact_ref")
    _digest(telemetry["artifact_digest"], "request.telemetry.artifact_digest")
    series = _list(telemetry["series"], "request.telemetry.series", minimum=1, maximum=MAX_SERIES)
    series_ids = []
    for index, item in enumerate(series):
        parsed = _validate_series(item, f"request.telemetry.series[{index}]")
        series_ids.append(parsed["series_id"])
    if len(set(series_ids)) != len(series_ids):
        raise ValidationError("request.telemetry.series contains duplicate identities")
    covariates = _list(telemetry["covariates"], "request.telemetry.covariates", maximum=MAX_COVARIATES)
    covariate_ids = []
    for index, item in enumerate(covariates):
        parsed = _validate_covariate(item, f"request.telemetry.covariates[{index}]")
        covariate_ids.append(parsed["covariate_id"])
    if len(set(covariate_ids)) != len(covariate_ids):
        raise ValidationError("request.telemetry.covariates contains duplicate identities")
    telemetry_payload = {"series": telemetry["series"], "covariates": telemetry["covariates"]}
    encoded_telemetry = canonical_bytes(telemetry_payload)
    expected_telemetry_digest = {
        "algorithm": "sha256",
        "hex_digest": digest_bytes(encoded_telemetry),
        "byte_len": len(encoded_telemetry),
    }
    _same_digest(telemetry["artifact_digest"], expected_telemetry_digest, "request.telemetry.artifact_digest")

    forecast = _fields(
        result["forecast"],
        {"context_length", "horizon", "quantiles", "required_covariate_ids", "return_quantiles"},
        set(),
        "request.forecast",
    )
    context_length = _integer(forecast["context_length"], "request.forecast.context_length", minimum=1, maximum=MAX_CONTEXT_LENGTH)
    horizon = _integer(forecast["horizon"], "request.forecast.horizon", minimum=1, maximum=MAX_HORIZON)
    forecast_quantiles = _quantiles(forecast["quantiles"], "request.forecast.quantiles")
    required_covariate_ids = _list(
        forecast["required_covariate_ids"],
        "request.forecast.required_covariate_ids",
        maximum=MAX_COVARIATES,
    )
    for index, covariate_id in enumerate(required_covariate_ids):
        _identifier(covariate_id, f"request.forecast.required_covariate_ids[{index}]")
    if len(set(required_covariate_ids)) != len(required_covariate_ids):
        raise ValidationError("request.forecast.required_covariate_ids contains duplicates")
    if not _bool(forecast["return_quantiles"], "request.forecast.return_quantiles"):
        raise ValidationError("request.forecast.return_quantiles must be true")
    covariate_by_id = {item["covariate_id"]: item for item in covariates}
    for covariate_id in required_covariate_ids:
        if covariate_id not in covariate_by_id:
            raise ValidationError(f"request.forecast.required covariate is missing: {covariate_id}")
    for index, item in enumerate(series):
        if len(item["values"]) < context_length:
            raise ValidationError(f"request.telemetry.series[{index}] has insufficient context")
    target_timestamps = series[0]["timestamps_ms"]
    for covariate_id, item in covariate_by_id.items():
        expected_length = context_length if item["kind"] == "past_only" else context_length + horizon
        if len(item["values"]) != expected_length:
            raise ValidationError(f"request.telemetry.covariates[{covariate_id}] has insufficient span")
        if item["timestamps_ms"][:context_length] != target_timestamps[-context_length:]:
            raise ValidationError(f"request.telemetry.covariates[{covariate_id}] does not align to target time")

    model = _validate_model(result["model"], forecast_quantiles, "request.model")
    runtime = _validate_runtime(result["runtime"], "request.runtime")
    if (model["implementation"], runtime["runtime_kind"]) not in (
        ("fake_fixture", "fake"),
        ("timesfm3_external", "pytorch"),
    ):
        raise ValidationError("request model implementation and runtime kind do not match")
    _validate_network_policy(result["network_policy"], "request.network_policy")
    _validate_benchmark_binding(result["benchmark_binding"], "request.benchmark_binding")
    if result["claim_boundary"] != CLAIM_CEILING:
        raise ValidationError("request.claim_boundary exceeds the slice ceiling")
    return result


def serialize_request(request: Any) -> bytes:
    """Validate and serialize a request to canonical JSON bytes."""

    validate_request(request)
    return canonical_bytes(request)


def deserialize_request(payload: str | bytes) -> dict[str, Any]:
    """Parse, require canonical encoding, and validate request bytes."""

    raw = payload.encode("utf-8") if isinstance(payload, str) else payload
    parsed = parse_json(raw)
    validate_request(parsed)
    if canonical_bytes(parsed) != raw:
        raise ValidationError("request bytes are not canonical JSON")
    return parsed


def _shape(value: Any, path: str) -> list[int]:
    values = _list(value, path, minimum=1, maximum=4)
    return [_integer(item, f"{path}[{index}]", minimum=1, maximum=MAX_HORIZON) for index, item in enumerate(values)]


def _validate_tensor(value: Any, shape: list[int], path: str, depth: int = 0) -> None:
    if depth == len(shape):
        _number(value, path)
        return
    values = _list(value, path, minimum=shape[depth], maximum=shape[depth])
    for index, item in enumerate(values):
        _validate_tensor(item, shape, f"{path}[{index}]", depth + 1)


def _validate_forecast_artifact(
    value: Any,
    path: str,
    *,
    expected_shape: list[int],
    quantile_levels: list[float] | None = None,
) -> dict[str, Any]:
    required = {"artifact_ref", "artifact_digest", "shape", "values"}
    if quantile_levels is not None:
        required.add("quantile_levels")
    result = _fields(value, required, set(), path)
    _relative_ref(result["artifact_ref"], f"{path}.artifact_ref")
    _digest(result["artifact_digest"], f"{path}.artifact_digest")
    shape = _shape(result["shape"], f"{path}.shape")
    if shape != expected_shape:
        raise ValidationError(f"{path}.shape does not match request")
    _validate_tensor(result["values"], shape, f"{path}.values")
    if quantile_levels is None:
        payload = {"shape": result["shape"], "values": result["values"]}
    else:
        parsed_levels = _quantiles(result["quantile_levels"], f"{path}.quantile_levels")
        if parsed_levels != quantile_levels:
            raise ValidationError(f"{path}.quantile_levels do not match request")
        payload = {
            "shape": result["shape"],
            "quantile_levels": result["quantile_levels"],
            "values": result["values"],
        }
    encoded = canonical_bytes(payload)
    expected_digest = {
        "algorithm": "sha256",
        "hex_digest": digest_bytes(encoded),
        "byte_len": len(encoded),
    }
    _same_digest(result["artifact_digest"], expected_digest, f"{path}.artifact_digest")
    return result


def _validate_result_provenance(
    value: Any,
    request: dict[str, Any],
    result: dict[str, Any],
) -> dict[str, Any]:
    path = "result.provenance"
    provenance = _fields(
        value,
        {
            "request_digest",
            "input_artifact_digest",
            "source_repository",
            "source_revision",
            "checkpoint_reference",
            "checkpoint_revision",
            "weight_digest",
            "model_config_digest",
            "runtime_kind",
            "python",
            "pytorch",
            "numpy",
            "device",
            "acquisition_separate",
            "execution_network_enabled",
            "local_files_only",
            "output_digest",
        },
        set(),
        path,
    )
    model = request["model"]
    runtime = request["runtime"]
    expected = {
        "request_digest": digest_json(request),
        "input_artifact_digest": request["telemetry"]["artifact_digest"],
        "source_repository": model["source_repository"],
        "source_revision": model["source_revision"],
        "checkpoint_reference": model["checkpoint_reference"],
        "checkpoint_revision": model["checkpoint_revision"],
        "weight_digest": model["weight_digest"],
        "model_config_digest": model["config_digest"],
        "runtime_kind": runtime["runtime_kind"],
        "python": runtime["python"],
        "pytorch": runtime["pytorch"],
        "numpy": runtime["numpy"],
        "device": runtime["device"],
        "acquisition_separate": request["network_policy"]["acquisition_separate"],
        "execution_network_enabled": request["network_policy"]["execution_network_enabled"],
        "local_files_only": request["network_policy"]["local_files_only"],
        "output_digest": result["output_digest"],
    }
    for field, expected_value in expected.items():
        if provenance[field] != expected_value:
            raise ValidationError(f"{path}.{field} does not match bound provenance")
    _digest(provenance["input_artifact_digest"], f"{path}.input_artifact_digest")
    _hex_digest(provenance["weight_digest"], f"{path}.weight_digest", allow_zero=True)
    _hex_digest(provenance["request_digest"], f"{path}.request_digest", allow_zero=False)
    _hex_digest(provenance["model_config_digest"], f"{path}.model_config_digest", allow_zero=False)
    if provenance["output_digest"] is not None:
        _hex_digest(provenance["output_digest"], f"{path}.output_digest", allow_zero=False)
    _bool(provenance["acquisition_separate"], f"{path}.acquisition_separate")
    _bool(provenance["execution_network_enabled"], f"{path}.execution_network_enabled")
    _bool(provenance["local_files_only"], f"{path}.local_files_only")
    return provenance


def _validate_repeatability(value: Any, request: dict[str, Any], output_digest: str) -> dict[str, Any]:
    result = _fields(
        value,
        {"status", "device", "first_output_digest", "repeat_output_digest", "same_device"},
        set(),
        "result.repeatability",
    )
    if result["status"] not in ("same_device_match", "not_run"):
        raise ValidationError("result.repeatability.status is unrecognized")
    if result["status"] == "same_device_match":
        if result["device"] != request["runtime"]["device"]:
            raise ValidationError("result.repeatability.device does not match runtime")
        _hex_digest(result["first_output_digest"], "result.repeatability.first_output_digest", allow_zero=False)
        _hex_digest(result["repeat_output_digest"], "result.repeatability.repeat_output_digest", allow_zero=False)
        if result["first_output_digest"] != output_digest or result["repeat_output_digest"] != output_digest:
            raise ValidationError("result.repeatability digest mismatch")
        if not _bool(result["same_device"], "result.repeatability.same_device"):
            raise ValidationError("result.repeatability.same_device must be true")
    else:
        if result["device"] is not None or result["first_output_digest"] is not None or result["repeat_output_digest"] is not None:
            raise ValidationError("result.not_run repeatability must not contain digests")
        if result["same_device"] is not False:
            raise ValidationError("result.not_run repeatability must be false")
    return result


def validate_result(result: Any, request: Any) -> dict[str, Any]:
    """Validate a result against its exact request and provenance bindings."""

    request = validate_request(request)
    result = _fields(
        result,
        {
            "schema_version",
            "state_slice",
            "request_id",
            "status",
            "input_digest",
            "model_digest",
            "config_digest",
            "runtime_digest",
            "output_digest",
            "point_forecast_artifact",
            "quantile_forecast_artifact",
            "repeatability",
            "provenance",
            "claim_boundary",
            "non_claims",
        },
        set(),
        "result",
    )
    if result["schema_version"] != RESULT_SCHEMA_VERSION:
        raise ValidationError("result.schema_version is unsupported")
    if result["state_slice"] != STATE_SLICE:
        raise ValidationError("result.state_slice mismatch")
    if result["request_id"] != request["request_id"]:
        raise ValidationError("result.request_id does not match request")
    if result["status"] not in ("completed", "inconclusive", "invalid", "resource_limited"):
        raise ValidationError("result.status is unrecognized")
    _validate_non_claims(result["non_claims"], "result.non_claims")
    if result["claim_boundary"] != CLAIM_CEILING:
        raise ValidationError("result.claim_boundary exceeds the slice ceiling")
    _hex_digest(result["input_digest"], "result.input_digest", allow_zero=False)
    _hex_digest(result["model_digest"], "result.model_digest", allow_zero=False)
    _hex_digest(result["config_digest"], "result.config_digest", allow_zero=False)
    _hex_digest(result["runtime_digest"], "result.runtime_digest", allow_zero=False)
    if result["input_digest"] != digest_json(request):
        raise ValidationError("result.input_digest mismatch")
    if result["model_digest"] != digest_json(request["model"]):
        raise ValidationError("result.model_digest mismatch")
    if result["config_digest"] != request["model"]["config_digest"]:
        raise ValidationError("result.config_digest mismatch")
    if result["runtime_digest"] != digest_json(request["runtime"]):
        raise ValidationError("result.runtime_digest mismatch")

    expected_shape = [len(request["telemetry"]["series"]), request["forecast"]["horizon"]]
    expected_quantile_shape = expected_shape + [3]
    if result["status"] == "completed":
        if not isinstance(result["output_digest"], str):
            raise ValidationError("completed result requires output_digest")
        _hex_digest(result["output_digest"], "result.output_digest", allow_zero=False)
        point = _validate_forecast_artifact(
            result["point_forecast_artifact"],
            "result.point_forecast_artifact",
            expected_shape=expected_shape,
        )
        quantiles = _validate_forecast_artifact(
            result["quantile_forecast_artifact"],
            "result.quantile_forecast_artifact",
            expected_shape=expected_quantile_shape,
            quantile_levels=request["forecast"]["quantiles"],
        )
        for series_index in range(expected_shape[0]):
            for horizon_index in range(expected_shape[1]):
                q_values = quantiles["values"][series_index][horizon_index]
                if not q_values[0] <= q_values[1] <= q_values[2]:
                    raise ValidationError("result quantiles are not ordered")
                if abs(point["values"][series_index][horizon_index] - q_values[1]) > 1e-6:
                    raise ValidationError("result point forecast does not match q50")
        output_payload = {
            "point_forecast": point["values"],
            "quantile_forecast": quantiles["values"],
            "quantile_levels": quantiles["quantile_levels"],
        }
        if result["output_digest"] != digest_json(output_payload):
            raise ValidationError("result.output_digest mismatch")
        _validate_repeatability(result["repeatability"], request, result["output_digest"])
    else:
        if result["point_forecast_artifact"] is not None or result["quantile_forecast_artifact"] is not None:
            raise ValidationError("non-completed result must not contain forecast artifacts")
        if result["output_digest"] is not None:
            raise ValidationError("non-completed result must not contain output_digest")
        _validate_repeatability(result["repeatability"], request, "0" * 64)
    _validate_result_provenance(result["provenance"], request, result)
    return result


def serialize_result(result: Any, request: Any) -> bytes:
    """Validate and serialize a result to canonical JSON bytes."""

    validate_result(result, request)
    return canonical_bytes(result)


def deserialize_result(payload: str | bytes, request: Any) -> dict[str, Any]:
    """Parse, require canonical encoding, and validate result bytes."""

    raw = payload.encode("utf-8") if isinstance(payload, str) else payload
    parsed = parse_json(raw)
    validate_result(parsed, request)
    if canonical_bytes(parsed) != raw:
        raise ValidationError("result bytes are not canonical JSON")
    return parsed


def _forecast_artifact(artifact_ref: str, shape: list[int], values: list[Any], *, quantile_levels: list[float] | None = None) -> dict[str, Any]:
    if quantile_levels is None:
        payload = {"shape": shape, "values": values}
    else:
        payload = {"shape": shape, "quantile_levels": quantile_levels, "values": values}
    encoded = canonical_bytes(payload)
    return {
        "artifact_ref": artifact_ref,
        "artifact_digest": {
            "algorithm": "sha256",
            "hex_digest": digest_bytes(encoded),
            "byte_len": len(encoded),
        },
        **payload,
    }


def run_fake_model(request: Any) -> dict[str, Any]:
    """Produce a deterministic fixture result without loading TimesFM3."""

    request = validate_request(request)
    if request["model"]["model_id"] != FAKE_MODEL_ID:
        raise ValidationError("fake model runner requires the fake fixture identity")
    horizon = request["forecast"]["horizon"]
    context_length = request["forecast"]["context_length"]
    point_values: list[list[float]] = []
    quantile_values: list[list[list[float]]] = []
    for series in request["telemetry"]["series"]:
        context = [float(item) for item in series["values"][-context_length:]]
        first = context[0]
        last = context[-1]
        slope = (last - first) / max(1, len(context) - 1)
        point_row: list[float] = []
        quantile_row: list[list[float]] = []
        for offset in range(1, horizon + 1):
            median = last + slope * offset
            spread = max(0.1, abs(slope) * offset * 0.25 + 0.1)
            q10 = median - spread
            q90 = median + spread
            point_row.append(median)
            quantile_row.append([q10, median, q90])
        point_values.append(point_row)
        quantile_values.append(quantile_row)
    point_shape = [len(point_values), horizon]
    quantile_shape = [len(point_values), horizon, 3]
    point_artifact = _forecast_artifact(
        f"outputs/{request['request_id']}/point_forecast.json",
        point_shape,
        point_values,
    )
    quantile_artifact = _forecast_artifact(
        f"outputs/{request['request_id']}/quantile_forecast.json",
        quantile_shape,
        quantile_values,
        quantile_levels=list(QUANTILE_LEVELS),
    )
    output_payload = {
        "point_forecast": point_values,
        "quantile_forecast": quantile_values,
        "quantile_levels": list(QUANTILE_LEVELS),
    }
    output_digest = digest_json(output_payload)
    runtime = request["runtime"]
    result = {
        "schema_version": RESULT_SCHEMA_VERSION,
        "state_slice": STATE_SLICE,
        "request_id": request["request_id"],
        "status": "completed",
        "input_digest": digest_json(request),
        "model_digest": digest_json(request["model"]),
        "config_digest": request["model"]["config_digest"],
        "runtime_digest": digest_json(runtime),
        "output_digest": output_digest,
        "point_forecast_artifact": point_artifact,
        "quantile_forecast_artifact": quantile_artifact,
        "repeatability": {
            "status": "same_device_match",
            "device": runtime["device"],
            "first_output_digest": output_digest,
            "repeat_output_digest": output_digest,
            "same_device": True,
        },
        "provenance": {
            "request_digest": digest_json(request),
            "input_artifact_digest": request["telemetry"]["artifact_digest"],
            "source_repository": request["model"]["source_repository"],
            "source_revision": request["model"]["source_revision"],
            "checkpoint_reference": request["model"]["checkpoint_reference"],
            "checkpoint_revision": request["model"]["checkpoint_revision"],
            "weight_digest": request["model"]["weight_digest"],
            "model_config_digest": request["model"]["config_digest"],
            "runtime_kind": runtime["runtime_kind"],
            "python": runtime["python"],
            "pytorch": runtime["pytorch"],
            "numpy": runtime["numpy"],
            "device": runtime["device"],
            "acquisition_separate": request["network_policy"]["acquisition_separate"],
            "execution_network_enabled": request["network_policy"]["execution_network_enabled"],
            "local_files_only": request["network_policy"]["local_files_only"],
            "output_digest": output_digest,
        },
        "claim_boundary": CLAIM_CEILING,
        "non_claims": list(request["non_claims"]),
    }
    validate_result(result, request)
    return result


def _validate_scenario_config(value: Any, path: str = "scenario_config") -> dict[str, Any]:
    result = _fields(
        value,
        {"workload_metric", "load_plan", "rounding", "max_load", "seed"},
        set(),
        path,
    )
    if result["workload_metric"] not in WORKLOAD_METRICS:
        raise ValidationError(f"{path}.workload_metric is unrecognized")
    if result["load_plan"] != "deterministic_local_shard_plan_v1":
        raise ValidationError(f"{path}.load_plan is unrecognized")
    if result["rounding"] != "ceil_nonnegative":
        raise ValidationError(f"{path}.rounding is unrecognized")
    _integer(result["max_load"], f"{path}.max_load", minimum=1, maximum=1_000_000_000)
    _integer(result["seed"], f"{path}.seed", maximum=2**32 - 1)
    return result


def _scenario_arm_payload(arm: dict[str, Any]) -> dict[str, Any]:
    return {
        "arm": arm["arm"],
        "quantile": arm["quantile"],
        "label": arm["label"],
        "fixed_case_ids": arm["fixed_case_ids"],
        "forecast_values": arm["forecast_values"],
        "load_values": arm["load_values"],
    }


def _validate_integer_tensor(value: Any, shape: list[int], path: str) -> None:
    _validate_tensor(value, shape, path)
    def visit(node: Any, location: str) -> None:
        if isinstance(node, list):
            for index, child in enumerate(node):
                visit(child, f"{location}[{index}]")
        elif isinstance(node, bool) or not isinstance(node, int):
            raise ValidationError(f"{location} must contain integers")
    visit(value, path)


def validate_scenario_manifest(
    manifest: Any,
    result: Any,
    request: Any,
) -> dict[str, Any]:
    """Validate a q10/q50/q90 scenario manifest against one result."""

    request = validate_request(request)
    result = validate_result(result, request)
    manifest = _fields(
        manifest,
        {
            "schema_version",
            "state_slice",
            "scenario_manifest_id",
            "request_id",
            "forecast_output_digest",
            "benchmark_binding",
            "scenario_config",
            "arms",
            "claim_boundary",
            "non_claims",
            "manifest_digest",
        },
        set(),
        "scenario_manifest",
    )
    if manifest["schema_version"] != SCENARIO_SCHEMA_VERSION:
        raise ValidationError("scenario_manifest.schema_version is unsupported")
    if manifest["state_slice"] != STATE_SLICE:
        raise ValidationError("scenario_manifest.state_slice mismatch")
    _identifier(manifest["scenario_manifest_id"], "scenario_manifest.scenario_manifest_id")
    if manifest["request_id"] != request["request_id"]:
        raise ValidationError("scenario_manifest.request_id does not match request")
    if manifest["forecast_output_digest"] != result["output_digest"]:
        raise ValidationError("scenario_manifest.forecast_output_digest mismatch")
    _hex_digest(manifest["forecast_output_digest"], "scenario_manifest.forecast_output_digest", allow_zero=False)
    _validate_benchmark_binding(manifest["benchmark_binding"], "scenario_manifest.benchmark_binding")
    if manifest["benchmark_binding"] != request["benchmark_binding"]:
        raise ValidationError("scenario_manifest.benchmark_binding does not match request")
    scenario_config = _validate_scenario_config(manifest["scenario_config"])
    _validate_non_claims(manifest["non_claims"], "scenario_manifest.non_claims")
    if manifest["claim_boundary"] != CLAIM_CEILING:
        raise ValidationError("scenario_manifest.claim_boundary exceeds the slice ceiling")
    arms = _list(manifest["arms"], "scenario_manifest.arms", minimum=3, maximum=3)
    expected_shape = [len(request["telemetry"]["series"]), request["forecast"]["horizon"]]
    quantile_values = result["quantile_forecast_artifact"]["values"]
    expected_by_arm = {"low": 0, "median": 1, "high": 2}
    seen_arms: set[str] = set()
    for index, value in enumerate(arms):
        path = f"scenario_manifest.arms[{index}]"
        arm = _fields(
            value,
            {
                "arm",
                "quantile",
                "label",
                "artifact_ref",
                "fixed_case_ids",
                "forecast_values",
                "load_values",
                "artifact_digest",
            },
            set(),
            path,
        )
        arm_name = _string(arm["arm"], f"{path}.arm")
        if arm_name not in expected_by_arm or arm_name in seen_arms:
            raise ValidationError(f"{path}.arm is duplicated or unrecognized")
        seen_arms.add(arm_name)
        expected_quantile = QUANTILE_LEVELS[expected_by_arm[arm_name]]
        if _number(arm["quantile"], f"{path}.quantile") != expected_quantile:
            raise ValidationError(f"{path}.quantile does not match arm")
        if arm["label"] != "model_derived_synthetic_input":
            raise ValidationError(f"{path}.label is not the synthetic-input label")
        _relative_ref(arm["artifact_ref"], f"{path}.artifact_ref")
        if arm["fixed_case_ids"] != request["benchmark_binding"]["instance_ids"]:
            raise ValidationError(f"{path}.fixed_case_ids do not match request")
        forecast_values = arm["forecast_values"]
        _validate_tensor(forecast_values, expected_shape, f"{path}.forecast_values")
        quantile_index = expected_by_arm[arm_name]
        expected_forecast = [
            [row[quantile_index] for row in series_row]
            for series_row in quantile_values
        ]
        if forecast_values != expected_forecast:
            raise ValidationError(f"{path}.forecast_values do not match forecast output")
        load_values = arm["load_values"]
        _validate_integer_tensor(load_values, expected_shape, f"{path}.load_values")
        for row in load_values:
            for load in row:
                if load < 0 or load > scenario_config["max_load"]:
                    raise ValidationError(f"{path}.load_values exceeds configured bound")
        expected_load_values = [
            [int(math.ceil(max(0.0, min(float(item), scenario_config["max_load"])))) for item in row]
            for row in forecast_values
        ]
        if load_values != expected_load_values:
            raise ValidationError(f"{path}.load_values do not match deterministic mapping")
        encoded = canonical_bytes(_scenario_arm_payload(arm))
        expected_digest = {
            "algorithm": "sha256",
            "hex_digest": digest_bytes(encoded),
            "byte_len": len(encoded),
        }
        _same_digest(arm["artifact_digest"], expected_digest, f"{path}.artifact_digest")
    if seen_arms != set(SCENARIO_ARMS):
        raise ValidationError("scenario_manifest.arms are incomplete")
    digest_payload = {key: value for key, value in manifest.items() if key != "manifest_digest"}
    if manifest["manifest_digest"] != digest_json(digest_payload):
        raise ValidationError("scenario_manifest.manifest_digest mismatch")
    _hex_digest(manifest["manifest_digest"], "scenario_manifest.manifest_digest", allow_zero=False)
    return manifest


def build_scenario_manifest(
    result: Any,
    request: Any,
    scenario_config: Any,
) -> dict[str, Any]:
    """Build deterministic low, median, and high load scenarios."""

    request = validate_request(request)
    result = validate_result(result, request)
    scenario_config = _validate_scenario_config(scenario_config)
    quantile_values = result["quantile_forecast_artifact"]["values"]
    fixed_case_ids = request["benchmark_binding"]["instance_ids"]
    arms: list[dict[str, Any]] = []
    for arm_name, quantile_index in zip(SCENARIO_ARMS, range(3)):
        forecast_values = [
            [row[quantile_index] for row in series_row]
            for series_row in quantile_values
        ]
        load_values = [
            [int(math.ceil(max(0.0, min(float(item), scenario_config["max_load"])))) for item in row]
            for row in forecast_values
        ]
        arm = {
            "arm": arm_name,
            "quantile": QUANTILE_LEVELS[quantile_index],
            "label": "model_derived_synthetic_input",
            "artifact_ref": f"scenarios/{request['request_id']}/{arm_name}.json",
            "fixed_case_ids": list(fixed_case_ids),
            "forecast_values": forecast_values,
            "load_values": load_values,
        }
        encoded = canonical_bytes(_scenario_arm_payload(arm))
        arm["artifact_digest"] = {
            "algorithm": "sha256",
            "hex_digest": digest_bytes(encoded),
            "byte_len": len(encoded),
        }
        arms.append(arm)
    manifest = {
        "schema_version": SCENARIO_SCHEMA_VERSION,
        "state_slice": STATE_SLICE,
        "scenario_manifest_id": f"scenario-{digest_json(request)[:24]}",
        "request_id": request["request_id"],
        "forecast_output_digest": result["output_digest"],
        "benchmark_binding": request["benchmark_binding"],
        "scenario_config": scenario_config,
        "arms": arms,
        "claim_boundary": CLAIM_CEILING,
        "non_claims": [
            "forecast_quality_not_measured",
            "not_backend_outcome",
            "not_official_status",
            "not_score_axis",
            "not_authority",
        ],
    }
    manifest["manifest_digest"] = digest_json(manifest)
    validate_scenario_manifest(manifest, result, request)
    return manifest


def serialize_scenario_manifest(manifest: Any, result: Any, request: Any) -> bytes:
    """Validate and serialize a scenario manifest to canonical JSON bytes."""

    validate_scenario_manifest(manifest, result, request)
    return canonical_bytes(manifest)


def deserialize_scenario_manifest(
    payload: str | bytes,
    result: Any,
    request: Any,
) -> dict[str, Any]:
    """Parse, require canonical encoding, and validate a scenario manifest."""

    raw = payload.encode("utf-8") if isinstance(payload, str) else payload
    parsed = parse_json(raw)
    validate_scenario_manifest(parsed, result, request)
    if canonical_bytes(parsed) != raw:
        raise ValidationError("scenario manifest bytes are not canonical JSON")
    return parsed
