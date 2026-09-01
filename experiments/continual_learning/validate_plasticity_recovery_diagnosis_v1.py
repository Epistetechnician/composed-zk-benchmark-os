#!/usr/bin/env python3
"""Independent validator for the read-only plasticity recovery diagnosis.

State slice: ``continual-learning-plasticity-recovery-v1``.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any, Mapping


STATE_SLICE = "continual-learning-plasticity-recovery-v1"
DIAGNOSIS_SCHEMA = "continual-learning-plasticity-recovery-diagnosis-v1"
ARMS = ("no_update", "fixed_adapter", "replay", "selective_reinit", "replay_selective_reinit")
EXPECTED_CASE_COUNT = 60


class ValidationError(ValueError):
    """Raised when the diagnosis artifact is malformed or tampered."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)


def digest(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    ).hexdigest()


def sha256_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def _finite(value: Any, field: str) -> None:
    _require(isinstance(value, (int, float)) and not isinstance(value, bool), f"{field} must be numeric")
    _require(math.isfinite(float(value)), f"{field} must be finite")


def validate_result(result: Mapping[str, Any]) -> None:
    _require(result.get("state_slice") == STATE_SLICE, "state slice mismatch")
    _require(result.get("schema_version") == DIAGNOSIS_SCHEMA, "diagnosis schema mismatch")
    _require(result.get("diagnosis_type") == "read_only_forgetting_diagnosis", "diagnosis type mismatch")
    _require(result.get("source_case_count") == EXPECTED_CASE_COUNT, "source case count drift")
    _require(result.get("case_count") == EXPECTED_CASE_COUNT, "diagnosis case count drift")
    _require(result.get("thresholds_changed") is False, "threshold mutation claim drift")
    _require(result.get("new_mechanism_preregistered") is False, "new mechanism claim drift")
    _require(result.get("classification") == "NoCandidate", "classification drift")
    for field in ("source_result_sha256", "source_result_file_sha256"):
        value = result.get(field)
        _require(isinstance(value, str) and len(value) == 64, f"{field} malformed")
    arms = result.get("arms")
    _require(isinstance(arms, Mapping) and set(arms) == set(ARMS), "arm diagnosis panel drift")
    for arm in ARMS:
        data = arms[arm]
        _require(isinstance(data, Mapping), f"arm diagnosis missing: {arm}")
        _require(data.get("case_count") == 12, f"arm case count drift: {arm}")
        for field in ("max_forgetting", "mean_forgetting", "protected_row_count", "replay_target_slot_count", "reinitialization_count"):
            _finite(data.get(field), f"{arm}/{field}")
        _require(data["protected_row_count"] >= 0, f"protected row count malformed: {arm}")
        _require(data["replay_target_slot_count"] == 0 if arm not in ("replay", "replay_selective_reinit") else data["replay_target_slot_count"] > 0, f"replay accounting drift: {arm}")
        _require(data["reinitialization_count"] == 0 if arm not in ("selective_reinit", "replay_selective_reinit") else data["reinitialization_count"] > 0, f"reinitialization accounting drift: {arm}")
        sensitivity = data.get("order_sensitivity")
        _require(isinstance(sensitivity, Mapping), f"order sensitivity missing: {arm}")
        _finite(sensitivity.get("adaptation_gain_range_by_seed"), f"{arm}/adaptation order range")
        _finite(sensitivity.get("forgetting_range_by_seed"), f"{arm}/forgetting order range")
        _require(len(sensitivity.get("adaptation_gain_rows", [])) == 12, f"order row count drift: {arm}")
        for row in sensitivity["adaptation_gain_rows"]:
            _require(isinstance(row, Mapping), f"malformed order row: {arm}")
            _finite(row.get("adaptation_gain"), f"{arm}/adaptation gain")
            _finite(row.get("forgetting"), f"{arm}/forgetting")

    unsigned = {key: result[key] for key in result if key != "diagnosis_sha256"}
    _require(result.get("diagnosis_sha256") == digest(unsigned), "diagnosis digest mismatch")


def validate_file(path: Path, source_result: Path | None = None) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    _require(isinstance(value, dict), "diagnosis JSON object required")
    validate_result(value)
    if source_result is not None:
        _require(value["source_result_file_sha256"] == sha256_file(source_result), "source result file custody mismatch")
    return value


def validate_artifact_root(root: Path, source_result: Path | None = None) -> dict[str, Any]:
    root = root.resolve()
    diagnosis_path = root / "diagnosis.json"
    report_path = root / "diagnosis.md"
    manifest_path = root / "artifact_manifest.json"
    for path in (diagnosis_path, report_path, manifest_path):
        _require(path.is_file() and not path.is_symlink(), f"unsafe or missing artifact: {path.name}")
    diagnosis = validate_file(diagnosis_path, source_result)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    _require(isinstance(manifest, dict), "artifact manifest object required")
    body = {key: manifest[key] for key in manifest if key != "manifest_sha256"}
    _require(manifest.get("manifest_sha256") == digest(body), "artifact manifest digest mismatch")
    _require(manifest.get("state_slice") == STATE_SLICE, "artifact manifest state slice mismatch")
    _require(manifest.get("diagnosis_sha256") == diagnosis["diagnosis_sha256"], "artifact/diagnosis digest mismatch")
    expected_files = [
        {"path": path.name, "byte_len": path.stat().st_size, "sha256": sha256_file(path)}
        for path in (diagnosis_path, report_path)
    ]
    _require(manifest.get("files") == expected_files, "artifact file custody mismatch")
    return diagnosis


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--source-result", type=Path)
    args = parser.parse_args()
    diagnosis = validate_artifact_root(args.root, args.source_result)
    print(json.dumps({"diagnosis": str(args.root), "diagnosis_sha256": diagnosis["diagnosis_sha256"], "validated": True}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
