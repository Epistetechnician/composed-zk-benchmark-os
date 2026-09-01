#!/usr/bin/env python3
"""Independent aggregate-only validator for plasticity recovery V2.

State slice: ``continual-learning-plasticity-recovery-v2``.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any, Mapping, Sequence


STATE_SLICE = "continual-learning-plasticity-recovery-v2"
SCHEMA_VERSION = "continual-learning-plasticity-recovery-v2-result-v1"
PRIMARY_ENDPOINT = "heldout_adaptation_improvement_over_untouched_base"
ARMS = ("no_update", "fixed_adapter", "replay", "selective_reinit", "replay_selective_reinit", "protected_replay")
SEEDS = (20261001, 20261002, 20261003, 20261004)
ORDER_SEEDS = (9111, 9112, 9113)
DIMENSION = 8
FIT_COUNT = 16
UPDATE_BUDGET = 16
GRADIENT_SLOTS = 2
EXPECTED_CASE_COUNT = 72
EFFECT_THRESHOLD = 0.01
BOOTSTRAP_SEED = 20261029
BOOTSTRAP_REPLICATES = 10_000
MAX_ORDER_RANGE = 0.20
MAX_FORGETTING = 0.20
MAX_CALIBRATION_BRIER = 0.25
ROLLBACK_TOLERANCE = 1e-12


class ValidationError(ValueError):
    """Raised when the V2 result is malformed or tampered."""


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


def _unit(*parts: object) -> float:
    payload = "|".join(str(part) for part in parts).encode("utf-8")
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big") / float(1 << 64)


def _finite(value: Any, field: str) -> float:
    _require(isinstance(value, (int, float)) and not isinstance(value, bool), f"{field} must be numeric")
    result = float(value)
    _require(math.isfinite(result), f"{field} must be finite")
    return result


def _case_digest(case: Mapping[str, Any]) -> str:
    return digest({key: case[key] for key in case if key != "case_sha256"})


def _bootstrap_interval(values: Sequence[float], seed: int) -> tuple[float, float]:
    samples = []
    for draw in range(BOOTSTRAP_REPLICATES):
        total = 0.0
        for index in range(len(values)):
            total += values[int(_unit(STATE_SLICE, "bootstrap", seed, draw, index) * len(values))]
        samples.append(total / len(values))
    samples.sort()
    return samples[int(0.025 * len(samples))], samples[int(0.975 * len(samples)) - 1]


def validate_result(result: Mapping[str, Any]) -> None:
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
        "tune_count": 8,
        "assessment_count": 8,
        "update_budget": UPDATE_BUDGET,
        "gradient_slots": GRADIENT_SLOTS,
        "replay_capacity": 4,
        "protected_replay_capacity": 4,
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
            _require(isinstance(entry.get(key), str) and len(entry[key]) == 64, f"panel digest malformed: {seed}/{key}")

    lock = result.get("prediction_lock")
    _require(isinstance(lock, Mapping), "prediction lock missing")
    lock_body = lock.get("body")
    _require(isinstance(lock_body, Mapping), "prediction lock body missing")
    _require(lock_body.get("state_slice") == STATE_SLICE, "prediction lock state slice mismatch")
    _require(lock_body.get("lock_type") == "tune_predictions_before_assessment", "prediction lock type mismatch")
    _require(lock_body.get("assessment_started") is False, "assessment ordering drift")
    predictions = lock_body.get("predictions")
    _require(isinstance(predictions, list) and len(predictions) == EXPECTED_CASE_COUNT, "prediction lock count drift")
    _require(lock.get("lock_sha256") == digest(lock_body), "prediction lock digest mismatch")
    prediction_map = {}
    for prediction in predictions:
        _require(isinstance(prediction, Mapping), "malformed prediction lock entry")
        key = (str(prediction.get("case")), str(prediction.get("arm")))
        _require(key not in prediction_map, f"duplicate prediction lock entry: {key}")
        _finite(prediction.get("tune_prediction"), "locked tune prediction")
        prediction_map[key] = prediction["tune_prediction"]

    cases = result.get("cases")
    _require(isinstance(cases, list) and len(cases) == EXPECTED_CASE_COUNT, "case count drift")
    counts = {arm: 0 for arm in ARMS}
    seen = set()
    for case in cases:
        _require(isinstance(case, Mapping), "malformed case")
        key = (str(case.get("case")), str(case.get("arm")))
        _require(key not in seen, f"duplicate case: {key}")
        seen.add(key)
        arm = case.get("arm")
        _require(arm in ARMS, f"unknown arm: {arm}")
        counts[str(arm)] += 1
        _require(case.get("case_sha256") == _case_digest(case), f"case digest mismatch: {key}")
        _require(case.get("state_slice") == STATE_SLICE, "case state slice mismatch")
        _require(case.get("seed") in SEEDS and case.get("order_seed") in ORDER_SEEDS, "case identity drift")
        _require(sorted(case.get("order", [])) == [f"fit-{index:03d}" for index in range(FIT_COUNT)], "fit order drift")
        _require(len(case.get("updates", [])) == FIT_COUNT, "update count drift")
        _require(case.get("gradient_evaluations") == UPDATE_BUDGET * GRADIENT_SLOTS, "gradient budget drift")
        _require(case.get("shadow_gradient_evaluations") == UPDATE_BUDGET * GRADIENT_SLOTS, "shadow budget drift")
        _require(case.get("base_weights_unchanged") is True, "base mutation claim drift")
        _require(case.get("adapter_restore_passed") is True, "rollback guard failed")
        _require(case.get("equal_compute_passed") is True, "equal compute guard failed")
        _require(key in prediction_map and case.get("tune_prediction") == prediction_map[key], f"prediction lock drift: {key}")
        for field in ("tune_prediction", "base_assessment_loss", "final_assessment_loss", "adaptation_gain", "forgetting", "calibration_brier", "rollback_max_abs_error"):
            _finite(case.get(field), field)
        protected = case.get("protected_replay_shard_ids")
        _require(protected == [] if arm != "protected_replay" else len(protected) == 4, f"protected replay memory drift: {key}")
        for index, update in enumerate(case["updates"]):
            _require(isinstance(update, Mapping), "malformed update")
            _require(update.get("step") == index, "update step drift")
            _require(len(update.get("target_shard_ids", [])) == GRADIENT_SLOTS, "update slot drift")
            _require(update.get("accepted") is (arm != "no_update"), "update acceptance drift")
        if arm == "no_update":
            _require(case.get("final_weights") == [0.0] * DIMENSION, "no-update state changed")
    _require(counts == {arm: 12 for arm in ARMS}, f"arm count drift: {counts}")

    summaries = result.get("summaries")
    _require(isinstance(summaries, Mapping) and set(summaries) == set(ARMS), "summary panel drift")
    no_update = [float(case["adaptation_gain"]) for case in cases if case["arm"] == "no_update"]
    for arm in ARMS:
        summary = summaries[arm]
        _require(summary.get("summary_sha256") == digest({key: summary[key] for key in summary if key != "summary_sha256"}), f"summary digest mismatch: {arm}")
        selected = [case for case in cases if case["arm"] == arm]
        deltas = [float(case["adaptation_gain"]) - no_update[index] for index, case in enumerate(selected)]
        _require(summary.get("case_deltas_vs_no_update") == [round(value, 12) for value in deltas], f"summary deltas drift: {arm}")
        lower, upper = _bootstrap_interval(deltas, BOOTSTRAP_SEED + ARMS.index(arm))
        expected_guards = {
            "forgetting": all(float(case["forgetting"]) <= MAX_FORGETTING for case in selected),
            "calibration": all(float(case["calibration_brier"]) <= MAX_CALIBRATION_BRIER for case in selected),
            "rollback": all(float(case["rollback_max_abs_error"]) <= ROLLBACK_TOLERANCE for case in selected),
            "base_unchanged": all(bool(case["base_weights_unchanged"]) for case in selected),
            "equal_compute": all(bool(case["equal_compute_passed"]) for case in selected),
            "order_stability": max((max(float(case["adaptation_gain"]) for case in selected if int(case["seed"]) == seed) - min(float(case["adaptation_gain"]) for case in selected if int(case["seed"]) == seed) for seed in SEEDS), default=0.0) <= MAX_ORDER_RANGE,
        }
        _require(summary.get("hard_guards") == expected_guards, f"summary guards drift: {arm}")
        expected_passed = sum(deltas) / len(deltas) >= EFFECT_THRESHOLD and lower >= 0.0 and sum(delta > 0.0 for delta in deltas) >= 9 and all(expected_guards.values())
        _require(summary.get("passed") is expected_passed, f"summary decision drift: {arm}")

    unsigned = {key: result[key] for key in result if key != "result_sha256"}
    _require(result.get("result_sha256") == digest(unsigned), "result digest mismatch")


def validate_artifact_root(root: Path) -> dict[str, Any]:
    root = root.resolve()
    result_path = root / "result.json"
    report_path = root / "result.md"
    manifest_path = root / "artifact_manifest.json"
    for path in (result_path, report_path, manifest_path):
        _require(path.is_file() and not path.is_symlink(), f"unsafe or missing artifact: {path.name}")
    result = json.loads(result_path.read_text(encoding="utf-8"))
    _require(isinstance(result, dict), "result JSON object required")
    validate_result(result)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    _require(isinstance(manifest, dict), "artifact manifest object required")
    body = {key: manifest[key] for key in manifest if key != "manifest_sha256"}
    _require(manifest.get("manifest_sha256") == digest(body), "artifact manifest digest mismatch")
    _require(manifest.get("state_slice") == STATE_SLICE and manifest.get("result_sha256") == result["result_sha256"], "artifact identity mismatch")
    expected_files = [
        {"path": path.name, "byte_len": path.stat().st_size, "sha256": sha256_file(path)}
        for path in (result_path, report_path)
    ]
    _require(manifest.get("files") == expected_files, "artifact file custody mismatch")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    result = validate_artifact_root(args.root)
    print(json.dumps({"result": str(args.root), "result_sha256": result["result_sha256"], "validated": True}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
