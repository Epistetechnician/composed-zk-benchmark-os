"""Synthetic semantic-oracle harness for Gemma recirculation V2 development.

State slice: gemma3-paper-recirculation-schema-resolution-v2-development.
This module is development-only. It never loads a model or external corpus.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from statistics import median
from typing import Any


STATE_SLICE = "gemma3-paper-recirculation-schema-resolution-v2-development"
PROTOCOL_ID = "gemma3-paper-recirculation-development-fixture-v2"
FIXTURE_SCHEMA = "gemma3-paper-recirculation-development-fixture-v2"
FIXTURE_ROOT = Path(__file__).resolve().parent / "fixtures"
REFERENCE_FIXTURE = FIXTURE_ROOT / "gemma3_recirculation_v2_reference.json"
CANDIDATE_FIXTURE = FIXTURE_ROOT / "gemma3_recirculation_v2_candidate.json"
EXPECTED_WINDOW_COUNT = 16
EXPECTED_TARGET_TOKENS = 16_384
EXPECTED_POLICY = {
    "warmup_iterations": 2,
    "timed_iterations": 3,
    "measurement_unit": "windows_per_second",
    "fit_only": True,
    "validated_windows": EXPECTED_WINDOW_COUNT,
    "target_tokens": EXPECTED_TARGET_TOKENS,
}
FROZEN_FILE_DIGESTS: dict[str, str] = {
    "gemma3_recirculation_v2_reference.json":
        "d409816c3131fe287dcf1c7e66e781246379a146ef9328599f31244835d1a54e",
    "gemma3_recirculation_v2_candidate.json":
        "697c79e0e028bd0cc88af7a184c6c6f88dee36b1427f3ee9e59c6aff03759e23",
}


class FixtureError(ValueError):
    """Raised when a fixture violates the frozen development contract."""


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise FixtureError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _canonical(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def file_sha256(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _payload_digest(document: dict[str, Any]) -> str:
    payload = dict(document)
    payload.pop("fixture_sha256", None)
    return _sha256_bytes(_canonical(payload))


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(
            path.read_text(encoding="utf-8"), object_pairs_hook=_reject_duplicate_keys
        )
    except (OSError, json.JSONDecodeError, FixtureError) as exc:
        raise FixtureError(f"invalid fixture JSON: {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise FixtureError(f"fixture must be an object: {path}")
    return value


def load_fixture(path: Path, expected_fixture_id: str | None = None) -> dict[str, Any]:
    document = _read_json(path)
    if document.get("schema") != FIXTURE_SCHEMA:
        raise FixtureError("fixture schema changed")
    if document.get("protocol_id") != PROTOCOL_ID:
        raise FixtureError("fixture protocol identity changed")
    if expected_fixture_id is not None and document.get("fixture_id") != expected_fixture_id:
        raise FixtureError("fixture identity changed")
    supplied_digest = document.get("fixture_sha256")
    if not isinstance(supplied_digest, str) or len(supplied_digest) != 64:
        raise FixtureError("fixture digest is malformed")
    if supplied_digest != _payload_digest(document):
        raise FixtureError("fixture digest does not match canonical payload")
    return document


def validate_frozen_files() -> None:
    for name, expected in FROZEN_FILE_DIGESTS.items():
        actual = file_sha256(FIXTURE_ROOT / name)
        if expected and actual != expected:
            raise FixtureError(f"frozen fixture file digest changed: {name}")


def _finite_number(value: Any, label: str) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise FixtureError(f"{label} is not numeric")
    result = float(value)
    if not math.isfinite(result):
        raise FixtureError(f"{label} is non-finite")
    return result


def _validate_measurement(fixture: dict[str, Any]) -> None:
    metadata = fixture.get("throughput_metadata")
    if metadata != EXPECTED_POLICY:
        raise FixtureError("throughput metadata changed")
    measurement = fixture.get("measurement")
    if not isinstance(measurement, dict):
        raise FixtureError("measurement section is missing")
    samples = measurement.get("timing_samples_seconds")
    if not isinstance(samples, list) or len(samples) != EXPECTED_POLICY["timed_iterations"]:
        raise FixtureError("timing sample count changed")
    values = [_finite_number(value, "timing sample") for value in samples]
    if any(value <= 0.0 for value in values):
        raise FixtureError("timing sample is not positive")
    expected_throughput = EXPECTED_WINDOW_COUNT / median(values)
    observed_throughput = _finite_number(
        measurement.get("throughput_windows_per_second"),
        "throughput",
    )
    observed_wall_clock = _finite_number(
        measurement.get("representative_wall_clock_seconds"),
        "representative wall clock",
    )
    if not math.isclose(observed_throughput, expected_throughput, rel_tol=0.0, abs_tol=1e-12):
        raise FixtureError("throughput is not reproducible from timing samples")
    if not math.isclose(observed_wall_clock, median(values), rel_tol=0.0, abs_tol=1e-12):
        raise FixtureError("wall-clock metadata is not reproducible")


def _validate_policy(fixture: dict[str, Any]) -> None:
    policy = fixture.get("policy")
    if not isinstance(policy, dict):
        raise FixtureError("search policy is missing")
    fit_rows = policy.get("fit_rows_read")
    assessment_rows = policy.get("assessment_rows_read")
    discoveries = policy.get("discovery_ids")
    if not isinstance(fit_rows, list) or fit_rows != ["fit-001", "fit-002"]:
        raise FixtureError("fit-row policy changed")
    if not isinstance(assessment_rows, list) or assessment_rows:
        raise FixtureError("assessment leakage detected")
    if not isinstance(discoveries, list) or len(discoveries) != len(set(discoveries)):
        raise FixtureError("duplicate discovery detected")
    if not discoveries:
        raise FixtureError("no discovery artifact was recorded")


def _validate_semantics(reference: dict[str, Any], candidate: dict[str, Any]) -> None:
    reference_semantics = reference.get("semantic")
    candidate_semantics = candidate.get("semantic")
    if reference_semantics != candidate_semantics:
        raise FixtureError("semantic drift detected")
    if reference.get("throughput_metadata") != candidate.get("throughput_metadata"):
        raise FixtureError("throughput protocol metadata drift detected")
    _validate_policy(candidate)
    _validate_measurement(candidate)


def _receipt(
    status: str,
    reason_codes: list[str],
    reference_digest: str | None,
    candidate_digest: str | None,
    metric: float | None = None,
) -> dict[str, Any]:
    body: dict[str, Any] = {
        "schema": "gemma3-paper-recirculation-development-receipt-v2",
        "state_slice": STATE_SLICE,
        "protocol_id": PROTOCOL_ID,
        "status": status,
        "reason_codes": sorted(reason_codes),
        "reference_fixture_sha256": reference_digest,
        "candidate_fixture_sha256": candidate_digest,
        "metric": metric,
    }
    body["receipt_sha256"] = _sha256_bytes(_canonical(body))
    return body


def _reason_code(exc: Exception) -> str:
    message = str(exc).lower()
    known = (
        ("duplicate json key", "duplicate_json_key"),
        ("throughput is not reproducible", "throughput_is_not_reproducible"),
        ("duplicate discovery", "duplicate_discovery_detected"),
        ("assessment leakage", "assessment_leakage_detected"),
        ("fixture digest does not match", "fixture_digest_does_not_match_canonical_payload"),
        ("semantic drift", "semantic_drift_detected"),
        ("wall-clock metadata", "wall_clock_metadata_is_not_reproducible"),
        ("throughput protocol metadata", "throughput_protocol_metadata_drift_detected"),
        ("fit-row policy", "fit_row_policy_changed"),
        ("timing sample count", "timing_sample_count_changed"),
    )
    for fragment, code in known:
        if fragment in message:
            return code
    if "invalid fixture json" in message:
        return "invalid_fixture_json"
    return "fixture_contract_rejected"


def run_oracle(reference_path: Path, candidate_path: Path) -> dict[str, Any]:
    reference_digest = file_sha256(reference_path) if reference_path.is_file() else None
    candidate_digest = file_sha256(candidate_path) if candidate_path.is_file() else None
    try:
        validate_frozen_files()
        reference = load_fixture(reference_path, "reference-v2")
        candidate = load_fixture(candidate_path, "candidate-v2")
        _validate_semantics(reference, candidate)
        measurement = candidate["measurement"]
        metric = float(measurement["throughput_windows_per_second"])
        return _receipt("PASS", [], reference_digest, candidate_digest, metric)
    except (FixtureError, OSError, KeyError, TypeError, ValueError) as exc:
        return _receipt(
            "REJECT",
            [_reason_code(exc)],
            reference_digest,
            candidate_digest,
        )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reference", type=Path, default=REFERENCE_FIXTURE)
    parser.add_argument("--candidate", type=Path, default=CANDIDATE_FIXTURE)
    parser.add_argument("--receipt", type=Path)
    args = parser.parse_args()
    result = run_oracle(args.reference, args.candidate)
    encoded = json.dumps(result, sort_keys=True, indent=2) + "\n"
    if args.receipt is not None:
        args.receipt.parent.mkdir(parents=True, exist_ok=True)
        args.receipt.write_text(encoded, encoding="utf-8")
    print(encoded, end="")
    return 0 if result["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
