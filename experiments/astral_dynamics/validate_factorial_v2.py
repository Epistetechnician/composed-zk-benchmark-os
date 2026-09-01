#!/usr/bin/env python3
"""Independent aggregate-only validator for the v2 synthetic factorial.

State slice: ``astral-evidence-conditioned-multiscale-plasticity-v2``.

This validator deliberately duplicates the small closed-form panel and loss
equations instead of importing the experiment runner's metric functions.  It
checks the serialized aggregate, split custody digests, prediction lock,
equal-compute invariants, and the primary/guard metrics.  It never treats a
synthetic verification boolean as cryptographic evidence.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any, Mapping, Sequence


STATE_SLICE = "astral-evidence-conditioned-multiscale-plasticity-v2"
SCHEMA_VERSION = "astral-evidence-conditioned-factorial-result-v2"
PRIMARY_ENDPOINT = "heldout_adaptation_improvement_after_fixed_update_budget"
MODES = ("fixed_cadence", "adaptive_verification", "wave_scheduling", "adaptive_wave")
SCHEDULERS = ("deterministic", "bounded_stochastic")
TAXONOMIES = ("oracle", "noisy", "shuffled", "absent")
SPLITS = ("fit", "tune", "assessment")
SEEDS = (20260828, 20260829, 20260830)
ORDER_SEEDS = (4701, 4702, 4703)
DIMENSION = 6
FIT_COUNT = 24
TUNE_COUNT = 12
ASSESSMENT_COUNT = 12
MAX_FORGETTING = 0.22
MAX_CALIBRATION_BRIER = 0.12
MAX_ORDER_RANGE = 0.20
ROLLBACK_TOLERANCE = 1e-12
MAX_VERIFICATION_COST = FIT_COUNT * 3
CLAIMS = (
    "exact_synthetic_learner_only",
    "no_model_loaded",
    "no_base_weights_updated",
    "no_v48_artifacts_used",
    "no_astral_introspection_claim",
    "no_zk_or_pqc_evidence_generated",
)


class ValidationError(ValueError):
    """Raised when an aggregate report fails independent validation."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)


def _digest(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    ).hexdigest()


def _unit(*parts: object) -> float:
    payload = "|".join(str(part) for part in parts).encode("utf-8")
    integer = int.from_bytes(hashlib.sha256(payload).digest()[:8], "big")
    return integer / float(1 << 64)


def _signed(*parts: object) -> float:
    return 2.0 * _unit(*parts) - 1.0


def _clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))


def _anchor() -> tuple[float, ...]:
    return tuple(0.70 * math.sin((index + 1) * 1.17) for index in range(DIMENSION))


def _target(seed: int, split: str, index: int) -> tuple[float, ...]:
    anchor = _anchor()
    risk_draw = _unit(STATE_SLICE, seed, split, index, "risk")
    amplitude = (0.08 + 1.30 * risk_draw) if split == "fit" else (0.05 + 0.18 * risk_draw)
    return tuple(
        anchor[component] + amplitude * _signed(STATE_SLICE, seed, split, index, component, "direction")
        for component in range(DIMENSION)
    )


def _risk_truth(target: Sequence[float]) -> float:
    anchor = _anchor()
    distance = math.sqrt(sum((target[index] - anchor[index]) ** 2 for index in range(DIMENSION)) / DIMENSION)
    return _clamp(distance / 1.30, 0.0, 1.0)


def _shard_payload(seed: int, split: str, index: int) -> dict[str, Any]:
    target = _target(seed, split, index)
    return {
        "state_slice": STATE_SLICE,
        "shard_id": f"{split}-{index:03d}",
        "split": split,
        "index": index,
        "target": list(target),
        "risk_truth": _risk_truth(target),
    }


def _loss(parameters: Sequence[float], target: Sequence[float]) -> float:
    return 0.5 * sum((parameters[index] - target[index]) ** 2 for index in range(DIMENSION)) / DIMENSION


def _fit_order(seed: int, order_seed: int) -> list[int]:
    return sorted(range(FIT_COUNT), key=lambda index: (_unit(STATE_SLICE, "order", order_seed, f"fit-{index:03d}"), index))


def _taxonomy_value(taxonomy: str, seed: int, index: int) -> float:
    truth = _risk_truth(_target(seed, "fit", index))
    if taxonomy == "oracle":
        return truth
    if taxonomy == "noisy":
        return _clamp(truth + 0.15 * _signed(STATE_SLICE, "taxonomy-noise", seed, f"fit-{index:03d}"), 0.0, 1.0)
    if taxonomy == "absent":
        return 0.5
    ordered = sorted(range(FIT_COUNT), key=lambda item: (_unit(STATE_SLICE, "taxonomy-shuffle", seed, f"fit-{item:03d}"), item))
    position = ordered.index(index)
    source = ordered[(position + 1) % FIT_COUNT]
    return _risk_truth(_target(seed, "fit", source))


def _recomputed_panel_digest(seed: int) -> str:
    records = []
    for split, count in (("fit", FIT_COUNT), ("tune", TUNE_COUNT), ("assessment", ASSESSMENT_COUNT)):
        for index in range(count):
            target = _target(seed, split, index)
            body = _shard_payload(seed, split, index)
            records.append(
                {
                    "shard_id": body["shard_id"],
                    "split": split,
                    "index": index,
                    "target": list(target),
                    "risk_truth": _risk_truth(target),
                    "payload_sha256": _digest(body),
                }
            )
    return _digest(records)


def _validate_replicate(replicate: Mapping[str, Any], cell: Mapping[str, Any], config: Mapping[str, Any]) -> None:
    seed = replicate.get("seed")
    order_seed = replicate.get("order_seed")
    _require(seed in SEEDS, "replicate seed is not preregistered")
    _require(order_seed in ORDER_SEEDS, "order seed is not preregistered")
    _require(replicate.get("mode") == cell.get("mode"), "replicate mode mismatch")
    _require(replicate.get("scheduler") == cell.get("scheduler"), "replicate scheduler mismatch")
    _require(replicate.get("taxonomy") == cell.get("taxonomy"), "replicate taxonomy mismatch")
    _require(replicate.get("prediction_locked_before_assessment") is True, "assessment ran before prediction lock")
    _require(isinstance(replicate.get("final_parameters"), list), "final parameters must be serialized")
    _require(len(replicate["final_parameters"]) == DIMENSION, "parameter dimension drift")
    parameters = tuple(float(value) for value in replicate["final_parameters"])
    _require(all(math.isfinite(value) for value in parameters), "non-finite final parameter")
    assessment_targets = [_target(seed, "assessment", index) for index in range(ASSESSMENT_COUNT)]
    origin = (0.0,) * DIMENSION
    baseline = sum(_loss(origin, target) for target in assessment_targets) / ASSESSMENT_COUNT
    final = sum(_loss(parameters, target) for target in assessment_targets) / ASSESSMENT_COUNT
    _require(math.isclose(replicate["assessment_baseline_loss"], baseline, rel_tol=0.0, abs_tol=1e-12), "assessment baseline mismatch")
    _require(math.isclose(replicate["assessment_final_loss"], final, rel_tol=0.0, abs_tol=1e-12), "assessment final mismatch")
    _require(math.isclose(replicate["primary_endpoint_value"], baseline - final, rel_tol=0.0, abs_tol=1e-12), "primary endpoint mismatch")
    committed = replicate.get("committed_shards")
    quarantined = replicate.get("quarantined_shards")
    _require(isinstance(committed, list) and isinstance(quarantined, list), "state collections must be lists")
    _require(len(committed) + len(quarantined) == FIT_COUNT, "fit state partition mismatch")
    _require(len(set(committed + quarantined)) == FIT_COUNT, "fit state identity mismatch")
    _require(all(isinstance(item, str) and item.startswith("fit-") for item in committed + quarantined), "invalid fit identity")
    committed_indices = [int(item.split("-")[1]) for item in committed]
    committed_targets = [_target(seed, "fit", index) for index in committed_indices]
    if committed_targets:
        base_fit_loss = sum(_loss(origin, target) for target in committed_targets) / len(committed_targets)
        final_fit_loss = sum(_loss(parameters, target) for target in committed_targets) / len(committed_targets)
        forgetting = max(0.0, final_fit_loss - base_fit_loss) / max(base_fit_loss, 1e-12)
    else:
        forgetting = 0.0
    _require(math.isclose(replicate["forgetting_value"], forgetting, rel_tol=0.0, abs_tol=1e-12), "forgetting mismatch")
    expected_brier = 0.0
    for index in range(FIT_COUNT):
        truth = _risk_truth(_target(seed, "fit", index))
        observed = _taxonomy_value(cell["taxonomy"], seed, index)
        expected_brier += (observed - truth) ** 2
    expected_brier /= FIT_COUNT
    _require(math.isclose(replicate["calibration_brier"], expected_brier, rel_tol=0.0, abs_tol=1e-12), "calibration mismatch")
    _require(replicate["update_attempts"] == FIT_COUNT, "update budget mismatch")
    _require(replicate["gradient_compute_units"] == FIT_COUNT * DIMENSION, "gradient compute mismatch")
    _require(replicate["shadow_compute_units"] == FIT_COUNT * DIMENSION, "shadow compute mismatch")
    _require(0 <= replicate["verification_cost_units"] <= MAX_VERIFICATION_COST, "verification cost out of bounds")
    _require(replicate["rollback_max_abs_error"] <= ROLLBACK_TOLERANCE, "rollback fidelity mismatch")
    _require(replicate["forgetting_guard_pass"] == (forgetting <= MAX_FORGETTING), "forgetting guard mismatch")
    _require(replicate["calibration_guard_pass"] == (expected_brier <= MAX_CALIBRATION_BRIER), "calibration guard mismatch")
    _require(replicate["rollback_fidelity_guard_pass"] is True, "rollback guard mismatch")
    _require(replicate["verification_cost_guard_pass"] == (replicate["verification_cost_units"] <= MAX_VERIFICATION_COST), "verification cost guard mismatch")
    _require(replicate["equal_update_compute_guard_pass"] is True, "equal compute guard mismatch")
    _require(len(replicate.get("decision_digest", "")) == 64, "decision digest missing")
    _require(len(replicate.get("prediction_lock_sha256", "")) == 64, "prediction lock digest missing")


def validate_result(result: Mapping[str, Any]) -> None:
    """Validate a v2 report without importing the runner's metric functions."""

    _require(isinstance(result, Mapping), "result must be an object")
    _require(result.get("state_slice") == STATE_SLICE, "wrong state slice")
    _require(result.get("schema_version") == SCHEMA_VERSION, "wrong schema version")
    _require(result.get("primary_endpoint") == PRIMARY_ENDPOINT, "primary endpoint drift")
    _require(result.get("modes") == list(MODES), "mode panel drift")
    _require(result.get("schedulers") == list(SCHEDULERS), "scheduler panel drift")
    _require(result.get("taxonomies") == list(TAXONOMIES), "taxonomy panel drift")
    _require(result.get("preregistered_replicate_seeds") == list(SEEDS), "replicate seed lock drift")
    _require(result.get("preregistered_order_seeds") == list(ORDER_SEEDS), "order seed lock drift")
    _require(result.get("claims") == list(CLAIMS), "claim ceiling drift")
    config = result.get("config")
    _require(isinstance(config, Mapping), "config must be an object")
    _require(config.get("dimension") == DIMENSION, "dimension drift")
    _require(config.get("fit_shard_count") == FIT_COUNT, "fit count drift")
    _require(config.get("tune_shard_count") == TUNE_COUNT, "tune count drift")
    _require(config.get("assessment_shard_count") == ASSESSMENT_COUNT, "assessment count drift")
    _require(config.get("update_budget") == FIT_COUNT, "update budget drift")
    split_records = result.get("fresh_split_records")
    _require(isinstance(split_records, Mapping) and set(split_records) == {str(seed) for seed in SEEDS}, "fresh split record drift")
    for seed in SEEDS:
        record = split_records[str(seed)]
        _require(record.get("panel_sha256") == _recomputed_panel_digest(seed), f"panel digest mismatch: {seed}")
        for field in ("fit_sha256", "tune_sha256", "assessment_sha256"):
            _require(isinstance(record.get(field), str) and len(record[field]) == 64, f"split digest missing: {seed}/{field}")
    lock = result.get("prediction_lock")
    _require(isinstance(lock, Mapping), "prediction lock missing")
    _require(lock.get("assessment_started") is False, "prediction lock order drift")
    _require(result.get("prediction_lock_sha256") == _digest(lock), "prediction lock digest mismatch")
    cells = result.get("cells")
    _require(isinstance(cells, Mapping), "cells must be an object")
    expected_keys = {
        f"{mode}|{scheduler}|{taxonomy}"
        for mode in MODES
        for scheduler in SCHEDULERS
        for taxonomy in TAXONOMIES
    }
    _require(set(cells) == expected_keys, "factorial key set drift")
    all_replicates: list[Mapping[str, Any]] = []
    for key in sorted(expected_keys):
        cell = cells[key]
        _require(cell.get("cell_key") == key, f"cell key mismatch: {key}")
        _require(cell.get("replicate_count") == len(SEEDS) * len(ORDER_SEEDS), f"replicate count mismatch: {key}")
        _require(isinstance(cell.get("replicates"), list), f"replicates missing: {key}")
        _require(cell.get("cell_sha256") == _digest({field: cell[field] for field in cell if field != "cell_sha256"}), f"cell digest mismatch: {key}")
        for replicate in cell["replicates"]:
            _validate_replicate(replicate, cell, config)
            all_replicates.append(replicate)
        _require(cell.get("guards", {}).get("equal_update_compute") is True, f"cell equal compute guard failed: {key}")
        by_seed: dict[int, list[float]] = {}
        for replicate in cell["replicates"]:
            by_seed.setdefault(replicate["seed"], []).append(replicate["primary_endpoint_value"])
        order_range = max(max(values) - min(values) for values in by_seed.values())
        _require(math.isclose(cell["max_order_range"], order_range, rel_tol=0.0, abs_tol=1e-12), f"order range mismatch: {key}")
        _require(cell["guards"]["shard_order_stability"] == (order_range <= MAX_ORDER_RANGE), f"order guard mismatch: {key}")
    _require(len(all_replicates) == 32 * 9, "replicate total drift")
    unsigned = {field: result[field] for field in result if field != "result_sha256"}
    _require(result.get("result_sha256") == _digest(unsigned), "result digest mismatch")


def validate_file(path: Path) -> None:
    with path.open(encoding="utf-8") as handle:
        result = json.load(handle)
    validate_result(result)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("result", type=Path)
    args = parser.parse_args()
    validate_file(args.result)
    print(json.dumps({"validated": str(args.result), "state_slice": STATE_SLICE}, sort_keys=True))


if __name__ == "__main__":
    main()
