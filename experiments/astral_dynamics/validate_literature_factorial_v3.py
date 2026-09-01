#!/usr/bin/env python3
"""Independent aggregate validator for the v3 literature-informed factorial.

State slice: ``astral-evidence-conditioned-multiscale-plasticity-v3``.

The validator duplicates the closed-form panel, taxonomy, and loss equations.
It does not import the runner's metric functions and never interprets synthetic
verification fields as ZK/PQC evidence.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any, Mapping, Sequence


STATE_SLICE = "astral-evidence-conditioned-multiscale-plasticity-v3"
SCHEMA_VERSION = "astral-evidence-conditioned-literature-factorial-result-v3"
PRIMARY_ENDPOINT = "heldout_adaptation_improvement_after_fixed_update_budget"
MEMORY_POLICIES = ("single", "fast_slow", "replay", "ewc", "plasticity_guard", "integrated")
SCHEDULE_POLICIES = ("fixed", "single_frequency", "dual_frequency", "bounded_stochastic_dual")
CONTROLLERS = ("fixed_admission", "evidence_conditioned")
TAXONOMIES = ("oracle", "noisy", "shuffled", "absent")
SEEDS = (20260831, 20260832, 20260833)
ORDER_SEEDS = (5711, 5712, 5713)
DIMENSION = 6
FIT_COUNT = 24
TUNE_COUNT = 12
ASSESSMENT_COUNT = 12
MICRO_UPDATES_PER_SHARD = 2
MAX_FORGETTING = 0.22
MAX_CALIBRATION_BRIER = 0.12
MIN_PLASTICITY = 0.25
MAX_ORDER_RANGE = 0.20
ROLLBACK_TOLERANCE = 1e-12
MAX_VERIFICATION_COST = FIT_COUNT * 3
CLAIMS = (
    "exact_synthetic_literature_informed_controller_only",
    "no_model_loaded",
    "no_base_weights_updated",
    "no_v48_artifacts_used",
    "no_astral_introspection_claim",
    "no_zk_or_pqc_evidence_generated",
)


class ValidationError(ValueError):
    """Raised when a v3 aggregate fails independent validation."""


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
    return tuple(0.62 * math.sin((index + 1) * 1.13) for index in range(DIMENSION))


def _target(seed: int, split: str, index: int) -> tuple[float, ...]:
    anchor = _anchor()
    risk_draw = _unit(STATE_SLICE, seed, split, index, "risk-draw")
    amplitude = 0.07 + 1.20 * risk_draw if split == "fit" else 0.04 + 0.16 * risk_draw
    return tuple(
        anchor[component] + amplitude * _signed(STATE_SLICE, seed, split, index, component, "direction")
        for component in range(DIMENSION)
    )


def _taxonomy_fields(seed: int, split: str, index: int, target: Sequence[float]) -> tuple[float, float, float, float]:
    anchor = _anchor()
    distance = math.sqrt(sum((target[item] - anchor[item]) ** 2 for item in range(DIMENSION)) / DIMENSION)
    novelty = _clamp(distance / 1.20, 0.0, 1.0)
    uncertainty = _clamp(0.20 + 0.60 * _unit(STATE_SLICE, seed, split, index, "uncertainty-draw") + 0.20 * novelty, 0.0, 1.0)
    utility = _clamp(1.0 - 0.75 * novelty - 0.25 * uncertainty, 0.0, 1.0)
    risk = _clamp(0.50 * novelty + 0.35 * uncertainty + 0.15 * (1.0 - utility), 0.0, 1.0)
    return novelty, uncertainty, utility, risk


def _shard_record(seed: int, split: str, index: int) -> dict[str, Any]:
    target = _target(seed, split, index)
    novelty, uncertainty, utility, risk = _taxonomy_fields(seed, split, index, target)
    draft = {
        "state_slice": STATE_SLICE,
        "shard_id": f"{split}-{index:03d}",
        "split": split,
        "index": index,
        "target": list(target),
        "novelty_truth": novelty,
        "uncertainty_truth": uncertainty,
        "expected_utility_truth": utility,
        "risk_truth": risk,
    }
    return {
        "shard_id": draft["shard_id"],
        "split": split,
        "index": index,
        "target": list(target),
        "novelty_truth": novelty,
        "uncertainty_truth": uncertainty,
        "expected_utility_truth": utility,
        "risk_truth": risk,
        "payload_sha256": _digest(draft),
    }


def _panel_digest(seed: int) -> str:
    records = []
    for split, count in (("fit", FIT_COUNT), ("tune", TUNE_COUNT), ("assessment", ASSESSMENT_COUNT)):
        records.extend(_shard_record(seed, split, index) for index in range(count))
    return _digest(records)


def _loss(parameters: Sequence[float], target: Sequence[float]) -> float:
    return 0.5 * sum((parameters[index] - target[index]) ** 2 for index in range(DIMENSION)) / DIMENSION


def _taxonomy_value(taxonomy: str, seed: int, index: int) -> float:
    target = _target(seed, "fit", index)
    truth = _taxonomy_fields(seed, "fit", index, target)[3]
    if taxonomy == "oracle":
        return truth
    if taxonomy == "noisy":
        return _clamp(truth + 0.15 * _signed(STATE_SLICE, "taxonomy-noise", seed, f"fit-{index:03d}"), 0.0, 1.0)
    if taxonomy == "absent":
        return 0.5
    ordered = sorted(range(FIT_COUNT), key=lambda item: (_unit(STATE_SLICE, "taxonomy-shuffle", seed, f"fit-{item:03d}"), item))
    position = ordered.index(index)
    source = ordered[(position + 1) % FIT_COUNT]
    source_target = _target(seed, "fit", source)
    return _taxonomy_fields(seed, "fit", source, source_target)[3]


def _validate_replicate(replicate: Mapping[str, Any], cell: Mapping[str, Any]) -> None:
    seed = replicate.get("seed")
    order_seed = replicate.get("order_seed")
    _require(seed in SEEDS, "unregistered replicate seed")
    _require(order_seed in ORDER_SEEDS, "unregistered order seed")
    _require(replicate.get("memory_policy") == cell.get("memory_policy"), "memory policy mismatch")
    _require(replicate.get("schedule_policy") == cell.get("schedule_policy"), "schedule policy mismatch")
    _require(replicate.get("controller") == cell.get("controller"), "controller mismatch")
    _require(replicate.get("taxonomy") == cell.get("taxonomy"), "taxonomy mismatch")
    _require(replicate.get("prediction_locked_before_assessment") is True, "assessment precedes prediction lock")
    parameters_raw = replicate.get("final_parameters")
    _require(isinstance(parameters_raw, list) and len(parameters_raw) == DIMENSION, "final parameter shape drift")
    parameters = tuple(float(value) for value in parameters_raw)
    _require(all(math.isfinite(value) for value in parameters), "non-finite final parameter")
    origin = (0.0,) * DIMENSION
    assessment_targets = [_target(seed, "assessment", index) for index in range(ASSESSMENT_COUNT)]
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
        base_loss = sum(_loss(origin, target) for target in committed_targets) / len(committed_targets)
        final_loss = sum(_loss(parameters, target) for target in committed_targets) / len(committed_targets)
        forgetting = max(0.0, final_loss - base_loss) / max(base_loss, 1e-12)
    else:
        forgetting = 0.0
    _require(math.isclose(replicate["forgetting_value"], forgetting, rel_tol=0.0, abs_tol=1e-12), "forgetting mismatch")
    expected_brier = 0.0
    for index in range(FIT_COUNT):
        truth = _taxonomy_fields(seed, "fit", index, _target(seed, "fit", index))[3]
        observed = _taxonomy_value(cell["taxonomy"], seed, index)
        expected_brier += (observed - truth) ** 2
    expected_brier /= FIT_COUNT
    _require(math.isclose(replicate["calibration_brier"], expected_brier, rel_tol=0.0, abs_tol=1e-12), "calibration mismatch")
    _require(replicate["update_attempts"] == FIT_COUNT * MICRO_UPDATES_PER_SHARD, "update budget mismatch")
    _require(replicate["gradient_compute_units"] == FIT_COUNT * MICRO_UPDATES_PER_SHARD * DIMENSION, "gradient compute mismatch")
    _require(replicate["shadow_compute_units"] == FIT_COUNT * MICRO_UPDATES_PER_SHARD * DIMENSION, "shadow compute mismatch")
    _require(0 <= replicate["verification_cost_units"] <= MAX_VERIFICATION_COST, "verification cost mismatch")
    _require(replicate["rollback_max_abs_error"] <= ROLLBACK_TOLERANCE, "rollback mismatch")
    _require(replicate["forgetting_guard_pass"] == (forgetting <= MAX_FORGETTING), "forgetting guard mismatch")
    _require(replicate["calibration_guard_pass"] == (expected_brier <= MAX_CALIBRATION_BRIER), "calibration guard mismatch")
    _require(replicate["rollback_fidelity_guard_pass"] is True, "rollback guard mismatch")
    _require(replicate["plasticity_guard_pass"] == (replicate["final_plasticity"] >= MIN_PLASTICITY), "plasticity guard mismatch")
    _require(replicate["verification_cost_guard_pass"] == (replicate["verification_cost_units"] <= MAX_VERIFICATION_COST), "verification cost guard mismatch")
    _require(replicate["equal_update_compute_guard_pass"] is True, "equal compute guard mismatch")


def validate_result(result: Mapping[str, Any]) -> None:
    """Validate a report using independently duplicated aggregate equations."""

    _require(isinstance(result, Mapping), "result must be an object")
    _require(result.get("state_slice") == STATE_SLICE, "wrong state slice")
    _require(result.get("schema_version") == SCHEMA_VERSION, "wrong schema version")
    _require(result.get("primary_endpoint") == PRIMARY_ENDPOINT, "primary endpoint drift")
    _require(result.get("memory_policies") == list(MEMORY_POLICIES), "memory panel drift")
    _require(result.get("schedule_policies") == list(SCHEDULE_POLICIES), "schedule panel drift")
    _require(result.get("controllers") == list(CONTROLLERS), "controller panel drift")
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
    _require(config.get("micro_updates_per_shard") == MICRO_UPDATES_PER_SHARD, "micro update drift")
    split_records = result.get("fresh_split_records")
    _require(isinstance(split_records, Mapping) and set(split_records) == {str(seed) for seed in SEEDS}, "split record drift")
    for seed in SEEDS:
        _require(split_records[str(seed)].get("panel_sha256") == _panel_digest(seed), f"panel digest mismatch: {seed}")
        for field in ("fit_sha256", "tune_sha256", "assessment_sha256"):
            _require(isinstance(split_records[str(seed)].get(field), str) and len(split_records[str(seed)][field]) == 64, f"split digest missing: {seed}/{field}")
    lock = result.get("prediction_lock")
    _require(isinstance(lock, Mapping), "prediction lock missing")
    _require(lock.get("assessment_started") is False, "assessment order drift")
    _require(result.get("prediction_lock_sha256") == _digest(lock), "prediction lock digest mismatch")
    cells = result.get("cells")
    _require(isinstance(cells, Mapping), "cells must be an object")
    expected_keys = {
        f"{memory}|{schedule}|{controller}|{taxonomy}"
        for memory in MEMORY_POLICIES
        for schedule in SCHEDULE_POLICIES
        for controller in CONTROLLERS
        for taxonomy in TAXONOMIES
    }
    _require(set(cells) == expected_keys, "factorial key set drift")
    for key in expected_keys:
        cell = cells[key]
        _require(cell.get("cell_key") == key, f"cell key mismatch: {key}")
        _require(cell.get("replicate_count") == len(SEEDS) * len(ORDER_SEEDS), f"replicate count mismatch: {key}")
        _require(cell.get("cell_sha256") == _digest({field: cell[field] for field in cell if field != "cell_sha256"}), f"cell digest mismatch: {key}")
        _require(isinstance(cell.get("replicates"), list), f"replicates missing: {key}")
        for replicate in cell["replicates"]:
            _validate_replicate(replicate, cell)
        by_seed: dict[int, list[float]] = {}
        for replicate in cell["replicates"]:
            by_seed.setdefault(replicate["seed"], []).append(replicate["primary_endpoint_value"])
        order_range = max(max(values) - min(values) for values in by_seed.values())
        _require(math.isclose(cell["max_order_range"], order_range, rel_tol=0.0, abs_tol=1e-12), f"order range mismatch: {key}")
        _require(cell["guards"]["shard_order_stability"] == (order_range <= MAX_ORDER_RANGE), f"order guard mismatch: {key}")
    unsigned = {field: result[field] for field in result if field != "result_sha256"}
    _require(result.get("result_sha256") == _digest(unsigned), "result digest mismatch")


def validate_file(path: Path) -> None:
    with path.open(encoding="utf-8") as handle:
        validate_result(json.load(handle))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("result", type=Path)
    args = parser.parse_args()
    validate_file(args.result)
    print(json.dumps({"validated": str(args.result), "state_slice": STATE_SLICE}, sort_keys=True))


if __name__ == "__main__":
    main()
