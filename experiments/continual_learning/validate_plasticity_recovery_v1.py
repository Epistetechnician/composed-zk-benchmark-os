#!/usr/bin/env python3
"""Independent aggregate-only validator for plasticity recovery V1.

State slice: ``continual-learning-plasticity-recovery-v1``.

This module deliberately does not import or execute the experiment runner. It
checks the sealed JSON structure, digests, lock ordering, compute equality,
and hard-guard declarations from the emitted artifact only.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any, Mapping


STATE_SLICE = "continual-learning-plasticity-recovery-v1"
SCHEMA_VERSION = "continual-learning-plasticity-recovery-result-v1"
PRIMARY_ENDPOINT = "heldout_adaptation_improvement_over_untouched_base"
ARMS = ("no_update", "fixed_adapter", "replay", "selective_reinit", "replay_selective_reinit")
SEEDS = (20260901, 20260902, 20260903, 20260904)
ORDER_SEEDS = (8111, 8112, 8113)
DIMENSION = 8
FIT_COUNT = 16
UPDATE_BUDGET = 16
GRADIENT_SLOTS = 2
EXPECTED_CASE_COUNT = len(SEEDS) * len(ORDER_SEEDS) * len(ARMS)
MAX_FORGETTING = 0.20
MAX_CALIBRATION_BRIER = 0.25
ROLLBACK_TOLERANCE = 1e-12


class ValidationError(ValueError):
    """Raised when the sealed result violates the independent contract."""


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


def _case_digest(case: Mapping[str, Any]) -> str:
    return digest({key: case[key] for key in case if key != "case_sha256"})


def _summary_digest(summary: Mapping[str, Any]) -> str:
    return digest({key: summary[key] for key in summary if key != "summary_sha256"})


def validate_result(result: Mapping[str, Any]) -> None:
    """Validate one result object without running the producing code."""

    _require(result.get("state_slice") == STATE_SLICE, "state slice mismatch")
    _require(result.get("schema_version") == SCHEMA_VERSION, "schema version mismatch")
    _require(result.get("primary_endpoint") == PRIMARY_ENDPOINT, "primary endpoint mismatch")
    _require(result.get("arms") == list(ARMS), "arm contract mismatch")
    _require(result.get("seeds") == list(SEEDS), "seed contract mismatch")
    _require(result.get("order_seeds") == list(ORDER_SEEDS), "order contract mismatch")

    config = result.get("config")
    _require(isinstance(config, Mapping), "config missing")
    expected_config = {
        "dimension": DIMENSION,
        "fit_count": FIT_COUNT,
        "update_budget": UPDATE_BUDGET,
        "gradient_slots": GRADIENT_SLOTS,
        "replay_capacity": 4,
        "reinit_maturity": 3,
        "reinit_period": 4,
        "learning_rate": 0.18,
        "replay_learning_rate": 0.09,
        "base_weights_updated": False,
        "reversible_adapter_only": True,
    }
    for key, expected in expected_config.items():
        _require(config.get(key) == expected, f"config drift: {key}")

    panel_digests = result.get("panel_digests")
    _require(isinstance(panel_digests, Mapping) and set(panel_digests) == {str(seed) for seed in SEEDS}, "panel custody drift")
    for seed in SEEDS:
        entry = panel_digests[str(seed)]
        _require(isinstance(entry, Mapping), f"panel digest missing: {seed}")
        for key in ("panel_sha256", "fit_sha256", "tune_sha256", "assessment_sha256"):
            value = entry.get(key)
            _require(isinstance(value, str) and len(value) == 64, f"panel digest malformed: {seed}/{key}")

    lock = result.get("prediction_lock")
    _require(isinstance(lock, Mapping), "prediction lock missing")
    lock_body = lock.get("body")
    _require(isinstance(lock_body, Mapping), "prediction lock body missing")
    _require(lock_body.get("state_slice") == STATE_SLICE, "prediction lock state slice mismatch")
    _require(lock_body.get("lock_type") == "tune_predictions_before_assessment", "prediction lock type mismatch")
    _require(lock_body.get("assessment_started") is False, "assessment preceded prediction lock")
    predictions = lock_body.get("predictions")
    _require(isinstance(predictions, list) and len(predictions) == EXPECTED_CASE_COUNT, "prediction lock count drift")
    _require(lock.get("lock_sha256") == digest(lock_body), "prediction lock digest mismatch")

    cases = result.get("cases")
    _require(isinstance(cases, list) and len(cases) == EXPECTED_CASE_COUNT, "case count drift")
    seen: set[tuple[str, str]] = set()
    prediction_map: dict[tuple[str, str], Any] = {}
    for prediction in predictions:
        _require(isinstance(prediction, Mapping), "malformed prediction lock entry")
        key = (str(prediction.get("case")), str(prediction.get("arm")))
        _require(key not in prediction_map, f"duplicate prediction lock entry: {key}")
        _finite(prediction.get("tune_prediction"), "locked tune prediction")
        prediction_map[key] = prediction.get("tune_prediction")

    counts = {arm: 0 for arm in ARMS}
    for case in cases:
        _require(isinstance(case, Mapping), "malformed case")
        key = (str(case.get("case")), str(case.get("arm")))
        _require(key not in seen, f"duplicate case: {key}")
        seen.add(key)
        arm = case.get("arm")
        _require(arm in ARMS, f"unknown case arm: {arm}")
        counts[str(arm)] += 1
        _require(case.get("case_sha256") == _case_digest(case), f"case digest mismatch: {key}")
        _require(case.get("state_slice") == STATE_SLICE, "case state slice mismatch")
        _require(case.get("seed") in SEEDS, "case seed mismatch")
        _require(case.get("order_seed") in ORDER_SEEDS, "case order mismatch")
        _require(len(case.get("order", [])) == FIT_COUNT, "fit order length drift")
        _require(sorted(case["order"]) == [f"fit-{index:03d}" for index in range(FIT_COUNT)], "fit order membership drift")
        _require(len(case.get("updates", [])) == FIT_COUNT, "update record count drift")
        _require(case.get("gradient_evaluations") == UPDATE_BUDGET * GRADIENT_SLOTS, "gradient budget drift")
        _require(case.get("shadow_gradient_evaluations") == UPDATE_BUDGET * GRADIENT_SLOTS, "shadow budget drift")
        _require(case.get("base_weights_unchanged") is True, "base mutation claim drift")
        _require(case.get("adapter_restore_passed") is True, "adapter rollback guard failed")
        _require(case.get("equal_compute_passed") is True, "equal compute guard failed")
        _require(case.get("reinitializations") >= 0, "reinitialization count malformed")
        for field in (
            "tune_prediction",
            "base_assessment_loss",
            "final_assessment_loss",
            "adaptation_gain",
            "forgetting",
            "calibration_brier",
            "rollback_max_abs_error",
        ):
            _finite(case.get(field), field)
        _require(key in prediction_map, f"missing locked prediction: {key}")
        _require(case.get("tune_prediction") == prediction_map[key], f"locked prediction changed: {key}")
        for index, update in enumerate(case["updates"]):
            _require(isinstance(update, Mapping), "malformed update record")
            _require(update.get("step") == index, "update step drift")
            _require(len(update.get("target_shard_ids", [])) == GRADIENT_SLOTS, "update slot drift")
            _require(isinstance(update.get("accepted"), bool), "update acceptance malformed")
            _require(update.get("accepted") is (arm != "no_update"), "update acceptance drift")
        if arm == "no_update":
            _require(case.get("final_weights") == [0.0] * DIMENSION, "no-update control changed state")

    _require(counts == {arm: 12 for arm in ARMS}, f"arm replication count drift: {counts}")
    _require(len(seen) == EXPECTED_CASE_COUNT, "case identity count drift")

    summaries = result.get("summaries")
    _require(isinstance(summaries, Mapping) and set(summaries) == set(ARMS), "summary panel drift")
    for arm in ARMS:
        summary = summaries[arm]
        _require(isinstance(summary, Mapping), f"summary missing: {arm}")
        _require(summary.get("summary_sha256") == _summary_digest(summary), f"summary digest mismatch: {arm}")
        _require(summary.get("case_count") == 12, f"summary count drift: {arm}")
        _require(len(summary.get("case_deltas_vs_no_update", [])) == 12, f"summary delta count drift: {arm}")
        interval = summary.get("bootstrap_95_percent_interval")
        _require(isinstance(interval, list) and len(interval) == 2, f"summary interval drift: {arm}")
        _finite(summary.get("mean_delta_vs_no_update"), f"summary mean: {arm}")
        for value in interval:
            _finite(value, f"summary interval: {arm}")
        guards = summary.get("hard_guards")
        _require(isinstance(guards, Mapping), f"summary guards missing: {arm}")
        _require(set(guards) == {"forgetting", "calibration", "rollback", "base_unchanged", "equal_compute", "order_stability"}, f"summary guard panel drift: {arm}")
        _require(all(isinstance(value, bool) for value in guards.values()), f"summary guard type drift: {arm}")
        selected = [case for case in cases if case["arm"] == arm]
        by_seed: dict[int, list[float]] = {}
        for case in selected:
            by_seed.setdefault(int(case["seed"]), []).append(float(case["adaptation_gain"]))
        expected_guards = {
            "forgetting": all(float(case["forgetting"]) <= MAX_FORGETTING for case in selected),
            "calibration": all(float(case["calibration_brier"]) <= MAX_CALIBRATION_BRIER for case in selected),
            "rollback": all(float(case["rollback_max_abs_error"]) <= ROLLBACK_TOLERANCE for case in selected),
            "base_unchanged": all(bool(case["base_weights_unchanged"]) for case in selected),
            "equal_compute": all(bool(case["equal_compute_passed"]) for case in selected),
            "order_stability": max((max(values) - min(values) for values in by_seed.values()), default=0.0) <= 0.20,
        }
        _require(dict(guards) == expected_guards, f"summary guard result mismatch: {arm}")

    unsigned = {key: result[key] for key in result if key != "result_sha256"}
    _require(result.get("result_sha256") == digest(unsigned), "result digest mismatch")


def validate_file(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    _require(isinstance(value, dict), "result JSON object required")
    validate_result(value)
    return value


def validate_artifact_root(root: Path) -> dict[str, Any]:
    """Validate result JSON, human report custody, and manifest digests."""

    root = root.resolve()
    result_path = root / "result.json"
    report_path = root / "result.md"
    manifest_path = root / "artifact_manifest.json"
    for path in (result_path, report_path, manifest_path):
        _require(path.is_file() and not path.is_symlink(), f"unsafe or missing artifact: {path.name}")
    result = validate_file(result_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    _require(isinstance(manifest, dict), "artifact manifest object required")
    manifest_body = {key: manifest[key] for key in manifest if key != "manifest_sha256"}
    _require(manifest.get("manifest_sha256") == digest(manifest_body), "artifact manifest digest mismatch")
    _require(manifest.get("state_slice") == STATE_SLICE, "artifact manifest state slice mismatch")
    _require(manifest.get("result_sha256") == result["result_sha256"], "artifact/result digest mismatch")
    expected_files = {
        path.name: {"path": path.name, "byte_len": path.stat().st_size, "sha256": sha256_file(path)}
        for path in (result_path, report_path)
    }
    _require(manifest.get("files") == [expected_files["result.json"], expected_files["result.md"]], "artifact file custody mismatch")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--result", type=Path)
    parser.add_argument("--root", type=Path)
    args = parser.parse_args()
    _require((args.result is None) != (args.root is None), "provide exactly one of --result or --root")
    if args.root is not None:
        result = validate_artifact_root(args.root)
        target = args.root
    else:
        result = validate_file(args.result)
        target = args.result
    print(json.dumps({"result": str(target), "result_sha256": result["result_sha256"], "validated": True}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
