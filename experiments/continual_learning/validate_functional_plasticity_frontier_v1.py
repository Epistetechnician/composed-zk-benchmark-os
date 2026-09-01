#!/usr/bin/env python3
"""Independent aggregate-only validator for the functional-plasticity slice.

State slice: ``continual-learning-functional-plasticity-frontier-v1``.

This module intentionally does not import the experiment runner. It recomputes
the exact synthetic learner, all scalar records, event digests, estimands,
guards, and classification from the retained aggregate result.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
from pathlib import Path
from typing import Any, Mapping, Sequence


STATE_SLICE = "continual-learning-functional-plasticity-frontier-v1"
PROTOCOL_ID = "functional-plasticity-frontier-v1"
CLAIM_CEILING = "LocalDevelopmentFunctionalPlasticityFrontierSynthetic"
SCHEMA_VERSION = "continual-learning-functional-plasticity-frontier-result-v1"
PROTOCOL_PATH = Path(__file__).resolve().parents[2] / "docs/research/continual-learning/functional-plasticity-frontier-v1-protocol.md"
CONTRACT_PATH = Path(__file__).resolve().parents[2] / ".autoresearch/continual-learning-functional-plasticity-frontier-v1/contract.md"
REVIEW_PACKET_PATH = Path(__file__).resolve().parents[2] / "docs/research/continual-learning/functional-plasticity-frontier-v1-review-packet.md"
EXPECTED_RUN_ROOT = Path("/Users/shaanp/Documents/research-artifacts/continual-learning-functional-plasticity-frontier-v1-20260830-r1")
EXPECTED_PROTOCOL_SHA256 = "e80cd2c5997352f6362556ff274ed65e64dfb4301b51cef62787be40f36dba2e"
EXPECTED_CONTRACT_SHA256 = "32eb94cbd481d3d0699fc45ce3466f864efb5ef43562511ff65b75a5e87dfa87"
EXPECTED_REVIEW_PACKET_SHA256 = "8e328e40a647dc5543ad9df88436ee25cae5d4d9ad9ffaa228af0a5508c60a8b"
DIMENSION = 8
REPLICATE_SEEDS = (5101, 5102, 5103, 5104, 5105, 5106, 5107, 5108)
ORDER_SEEDS = (6101, 6102)
DIRECTIONS = ("forward", "reverse")
ARMS = ("untouched_base", "fixed_adapter", "function_projected")
SPLIT_COUNTS = {"protected": 8, "fit": 12, "tune": 6, "assessment": 8, "probe": 8}
LEARNING_RATE = 0.18
PROBE_LEARNING_RATE = 0.22
BOOTSTRAP_SEED = 73001
BOOTSTRAP_REPLICATES = 10_000
PRIMARY_THRESHOLD = 0.0020
BOOTSTRAP_LOWER_THRESHOLD = 0.0
WIN_COUNT_THRESHOLD = 20
ABSOLUTE_REFERENCE_FLOOR = -0.0020
MAX_TREATMENT_FORGETTING = 0.0500
MIN_TREATMENT_PROBE_GAIN = -0.0200
MAX_TREATMENT_FUNCTION_ERROR = 1e-10
ROLLBACK_TOLERANCE = 1e-12
MAX_ORDER_DELTA = 0.1000
BASE_THETA = (0.0,) * DIMENSION
RAW_FIELD_NAMES = {"feature", "target", "theta", "delta", "vector", "state", "exception_text"}
CONFIGURATION = {
    "assessment_shard_count": 8,
    "bootstrap_replicates": 10_000,
    "dimension": 8,
    "fit_shard_count": 12,
    "learning_rate": 0.18,
    "order_directions": ["forward", "reverse"],
    "order_seeds": [6101, 6102],
    "probe_learning_rate": 0.22,
    "probe_shard_count": 8,
    "protected_shard_count": 8,
    "replicate_seeds": [5101, 5102, 5103, 5104, 5105, 5106, 5107, 5108],
    "state_slice": STATE_SLICE,
    "tune_shard_count": 6,
}


class ValidationError(ValueError):
    """Raised when the aggregate artifact violates the contract."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)


def _canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("utf-8")


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _unit(*parts: object) -> float:
    payload = "|".join(str(part) for part in parts).encode("utf-8")
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big") / float(1 << 64)


def _signed(*parts: object) -> float:
    return 2.0 * _unit(*parts) - 1.0


def _finite(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def _dot(left: Sequence[float], right: Sequence[float]) -> float:
    return sum(a * b for a, b in zip(left, right))


def _add(left: Sequence[float], right: Sequence[float]) -> tuple[float, ...]:
    return tuple(a + b for a, b in zip(left, right))


def _sub(left: Sequence[float], right: Sequence[float]) -> tuple[float, ...]:
    return tuple(a - b for a, b in zip(left, right))


def _scale(left: Sequence[float], factor: float) -> tuple[float, ...]:
    return tuple(factor * value for value in left)


def _norm(value: Sequence[float]) -> float:
    return math.sqrt(_dot(value, value))


def _feature(seed: int, split: str, index: int) -> tuple[float, ...]:
    raw = tuple(_signed(STATE_SLICE, "feature", seed, split, index, component) for component in range(DIMENSION))
    length = _norm(raw)
    _require(length > 1e-12 and _finite(length), "feature normalization failure")
    return _scale(raw, 1.0 / length)


def _target_theta(seed: int, split: str) -> tuple[float, ...]:
    return tuple(0.31 * _signed(STATE_SLICE, "target-theta", seed, split, component) for component in range(DIMENSION))


def _shard(seed: int, split: str, index: int) -> tuple[tuple[float, ...], float]:
    feature = _feature(seed, split, index)
    target = _dot(_target_theta(seed, split), feature) + 0.025 * _signed(STATE_SLICE, "target-noise", seed, split, index)
    return feature, target


def _shards(seed: int, split: str) -> tuple[tuple[tuple[float, ...], float], ...]:
    return tuple(_shard(seed, split, index) for index in range(SPLIT_COUNTS[split]))


def _ordered_fit_indices(order_seed: int, direction: str) -> tuple[int, ...]:
    indices = list(range(SPLIT_COUNTS["fit"]))
    indices.sort(key=lambda index: (_unit(STATE_SLICE, "order", order_seed, "fit", index), index))
    if direction == "reverse":
        indices.reverse()
    return tuple(indices)


def _gram_schmidt(vectors: Sequence[Sequence[float]]) -> tuple[tuple[float, ...], ...]:
    basis: list[tuple[float, ...]] = []
    for vector in vectors:
        residual = tuple(float(value) for value in vector)
        for unit_vector in basis:
            residual = _sub(residual, _scale(unit_vector, _dot(residual, unit_vector)))
        length = _norm(residual)
        _require(_finite(length), "basis norm is non-finite")
        if length > 1e-12:
            basis.append(_scale(residual, 1.0 / length))
    _require(bool(basis), "protected basis is empty")
    return tuple(basis)


def _project(delta: Sequence[float], basis: Sequence[Sequence[float]]) -> tuple[float, ...]:
    result = tuple(float(value) for value in delta)
    for unit_vector in basis:
        result = _sub(result, _scale(unit_vector, _dot(result, unit_vector)))
    return result


def _loss(theta: Sequence[float], shard: tuple[Sequence[float], float]) -> float:
    feature, target = shard
    residual = _dot(theta, feature) - target
    return residual * residual


def _mean_loss(theta: Sequence[float], shards: Sequence[tuple[Sequence[float], float]]) -> float:
    _require(bool(shards), "mean loss requires shards")
    return sum(_loss(theta, shard) for shard in shards) / len(shards)


def _raw_delta(theta: Sequence[float], shard: tuple[Sequence[float], float], rate: float) -> tuple[float, ...]:
    feature, target = shard
    return _scale(feature, rate * (target - _dot(theta, feature)))


def _state_digest(theta: Sequence[float]) -> str:
    return _digest({"state_slice": STATE_SLICE, "values": [float(value) for value in theta]})


BASE_STATE_SHA256 = _state_digest(BASE_THETA)
CONFIG_SHA256 = _digest(CONFIGURATION)


def _restore_checkpoint(current: Sequence[float], checkpoint: Sequence[float]) -> tuple[float, ...]:
    del current
    return tuple(float(value) for value in checkpoint)


def _state_error(left: Sequence[float], right: Sequence[float]) -> float:
    return max(abs(a - b) for a, b in zip(left, right))


def _payload(case_index: int, arm: str, name: str, case: Mapping[str, Any]) -> dict[str, Any]:
    if name == "synthetic_initialized":
        return {"case_index": case_index, "arm": arm, "base_state_sha256": BASE_STATE_SHA256}
    if name == "fit_completed":
        return {"case_index": case_index, "arm": arm, "fit_order_digest": case["fit_order_digest"]}
    if name == "tune_completed":
        return {"case_index": case_index, "arm": arm, "tune_gain": case["tune_gain"]}
    if name == "prediction_lock_sealed":
        return {"case_index": case_index, "arm": arm, "lock_sha256": case["lock_sha256"]}
    if name == "assessment_completed":
        return {"case_index": case_index, "arm": arm, "assessment_gain": case["assessment_gain"]}
    if name == "probe_completed":
        return {"case_index": case_index, "arm": arm, "probe_gain": case["probe_gain"]}
    if name == "rollback_verified":
        return {"case_index": case_index, "arm": arm, "rollback_max_abs_error": case["rollback_max_abs_error"]}
    raise ValidationError(f"unknown event {name}")


EVENT_NAMES = (
    "synthetic_initialized",
    "fit_completed",
    "tune_completed",
    "prediction_lock_sealed",
    "assessment_completed",
    "probe_completed",
    "rollback_verified",
)


def _events(case_index: int, arm: str, case: Mapping[str, Any]) -> list[dict[str, Any]]:
    result = []
    for index, name in enumerate(EVENT_NAMES):
        event = {
            "event_index": index,
            "event_name": name,
            "predecessor_event_index": None if index == 0 else index - 1,
            "payload_sha256": _digest(_payload(case_index, arm, name, case)),
        }
        event["event_sha256"] = _digest(event)
        result.append(event)
    return result


def _expected_case(case_index: int, replicate_seed: int, order_seed: int, direction: str, arm: str) -> dict[str, Any]:
    fit = _shards(replicate_seed, "fit")
    tune = _shards(replicate_seed, "tune")
    assessment = _shards(replicate_seed, "assessment")
    probe = _shards(replicate_seed, "probe")
    protected = _shards(replicate_seed, "protected")
    basis = _gram_schmidt(tuple(shard[0] for shard in protected))
    indices = _ordered_fit_indices(order_seed, direction)
    theta = BASE_THETA
    candidate_digests: list[str] = []
    for fit_index in indices:
        shard = fit[fit_index]
        raw = _raw_delta(theta, shard, LEARNING_RATE)
        projected = _project(raw, basis)
        raw_state = _add(theta, raw)
        projected_state = _add(theta, projected)
        candidate_digests.extend((
            _digest({"case_index": case_index, "fit_index": fit_index, "candidate": "raw", "fit_loss": _loss(raw_state, shard), "protected_loss": _mean_loss(raw_state, protected)}),
            _digest({"case_index": case_index, "fit_index": fit_index, "candidate": "projected", "fit_loss": _loss(projected_state, shard), "protected_loss": _mean_loss(projected_state, protected)}),
        ))
        if arm == "fixed_adapter":
            theta = raw_state
        elif arm == "function_projected":
            theta = projected_state
        elif arm != "untouched_base":
            raise ValidationError(f"unknown arm {arm}")
    fit_gain = _mean_loss(BASE_THETA, fit) - _mean_loss(theta, fit)
    tune_gain = _mean_loss(BASE_THETA, tune) - _mean_loss(theta, tune)
    protected_forgetting = max(0.0, _mean_loss(theta, protected) - _mean_loss(BASE_THETA, protected))
    function_error = max(abs(_dot(shard[0], _sub(theta, BASE_THETA))) for shard in protected)
    lock = {
        "state_slice": STATE_SLICE,
        "case_index": case_index,
        "arm": arm,
        "primary_estimand": "G_FP",
        "predicted_direction": "function_projected_beats_fixed_adapter",
        "assessment_started": False,
        "probe_started": False,
    }
    lock_sha256 = _digest(lock)
    assessment_gain = _mean_loss(BASE_THETA, assessment) - _mean_loss(theta, assessment)
    probe_gain = sum(
        _loss(theta, shard) - _loss(_add(theta, _raw_delta(theta, shard, PROBE_LEARNING_RATE)), shard)
        for shard in probe
    ) / len(probe)
    checkpoint = tuple(BASE_THETA)
    restored = _restore_checkpoint(theta, checkpoint)
    rollback_error = _state_error(restored, checkpoint)
    case: dict[str, Any] = {
        "case_index": case_index,
        "replicate_seed": replicate_seed,
        "order_seed": order_seed,
        "direction": direction,
        "arm": arm,
        "base_state_sha256": BASE_STATE_SHA256,
        "fit_order_digest": _digest({"case_index": case_index, "fit_indices": list(indices)}),
        "lock_sha256": lock_sha256,
        "fit_gain": fit_gain,
        "tune_gain": tune_gain,
        "assessment_gain": assessment_gain,
        "protected_forgetting": protected_forgetting,
        "probe_gain": probe_gain,
        "function_preservation_error": function_error,
        "rollback_max_abs_error": rollback_error,
        "compute_counts": {
            "fit_shards": 12,
            "candidate_states": 24,
            "candidate_fit_evaluations": 24,
            "candidate_protected_evaluations": 24,
            "committed_updates": 0 if arm == "untouched_base" else 12,
        },
        "fit_candidate_digests": candidate_digests,
        "assessment_digest": _digest({"case_index": case_index, "split": "assessment", "gain": assessment_gain}),
        "probe_digest": _digest({"case_index": case_index, "split": "probe", "gain": probe_gain}),
    }
    case["event_log"] = _events(case_index, arm, case)
    case["case_sha256"] = _digest(case)
    return case


def _percentile(values: Sequence[float], fraction: float) -> float:
    position = fraction * (len(values) - 1)
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return values[lower]
    return values[lower] + (position - lower) * (values[upper] - values[lower])


def _bootstrap(values: Sequence[float]) -> tuple[float, float]:
    rng = random.Random(BOOTSTRAP_SEED)
    means = []
    for _ in range(BOOTSTRAP_REPLICATES):
        means.append(sum(values[rng.randrange(len(values))] for _ in values) / len(values))
    means.sort()
    return _percentile(means, 0.025), _percentile(means, 0.975)


def _order_delta(cases: Sequence[Mapping[str, Any]], arm: str, seed: int, order_seed: int) -> float:
    pair = [item for item in cases if item["arm"] == arm and item["replicate_seed"] == seed and item["order_seed"] == order_seed]
    _require(len(pair) == 2, "order pair coverage")
    forward = next(item for item in pair if item["direction"] == "forward")
    reverse = next(item for item in pair if item["direction"] == "reverse")
    return max(abs(float(forward[key]) - float(reverse[key])) for key in ("fit_gain", "tune_gain", "assessment_gain", "probe_gain", "protected_forgetting"))


def _validate_scalar_case(case: Mapping[str, Any]) -> None:
    expected = {"case_index", "replicate_seed", "order_seed", "direction", "arm", "base_state_sha256", "fit_order_digest", "lock_sha256", "event_log", "fit_gain", "tune_gain", "assessment_gain", "protected_forgetting", "probe_gain", "function_preservation_error", "rollback_max_abs_error", "compute_counts", "fit_candidate_digests", "assessment_digest", "probe_digest", "case_sha256"}
    _require(set(case) == expected, "case keys")
    _require(isinstance(case["case_index"], int) and not isinstance(case["case_index"], bool), "case index type")
    _require(case["direction"] in DIRECTIONS and case["arm"] in ARMS, "case identity")
    _require(case["base_state_sha256"] == BASE_STATE_SHA256, "base digest")
    for key in ("fit_gain", "tune_gain", "assessment_gain", "protected_forgetting", "probe_gain", "function_preservation_error", "rollback_max_abs_error"):
        _require(_finite(case[key]), f"non-finite case scalar: {key}")
    _require(isinstance(case["compute_counts"], dict), "compute counts type")
    _require(case["fit_candidate_digests"] and len(case["fit_candidate_digests"]) == 24, "candidate digest count")
    _require(all(isinstance(value, str) and len(value) == 64 for value in case["fit_candidate_digests"]), "candidate digest format")
    _require(isinstance(case["event_log"], list) and len(case["event_log"]) == len(EVENT_NAMES), "event log count")


def _validate_no_raw_keys(value: Any) -> None:
    if isinstance(value, Mapping):
        for key, nested in value.items():
            _require(key not in RAW_FIELD_NAMES, f"raw field retained: {key}")
            _validate_no_raw_keys(nested)
    elif isinstance(value, list):
        for nested in value:
            _validate_no_raw_keys(nested)


def _summary(cases: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    groups = []
    for seed in REPLICATE_SEEDS:
        for order_seed in ORDER_SEEDS:
            for direction in DIRECTIONS:
                group = {item["arm"]: item for item in cases if item["replicate_seed"] == seed and item["order_seed"] == order_seed and item["direction"] == direction}
                _require(set(group) == set(ARMS), "incomplete case group")
                groups.append(group)
    differences = [float(group["function_projected"]["probe_gain"]) - float(group["fixed_adapter"]["probe_gain"]) for group in groups]
    lower, upper = _bootstrap(differences)
    projected = [item for item in cases if item["arm"] == "function_projected"]
    fixed = [item for item in cases if item["arm"] == "fixed_adapter"]
    untouched = [item for item in cases if item["arm"] == "untouched_base"]
    primary_mean = sum(differences) / len(differences)
    win_count = sum(value > 0.0 for value in differences)
    reference = sum(float(item["probe_gain"]) for item in projected) / len(projected) - sum(float(item["probe_gain"]) for item in untouched) / len(untouched)
    hard = _hard_guards(cases)
    primary = primary_mean >= PRIMARY_THRESHOLD and lower >= BOOTSTRAP_LOWER_THRESHOLD and win_count >= WIN_COUNT_THRESHOLD and reference >= ABSOLUTE_REFERENCE_FLOOR and hard
    return {
        "primary_mean": primary_mean,
        "primary_bootstrap_lower": lower,
        "primary_bootstrap_upper": upper,
        "win_count": win_count,
        "mean_probe_untouched_base": sum(float(item["probe_gain"]) for item in untouched) / len(untouched),
        "mean_probe_fixed_adapter": sum(float(item["probe_gain"]) for item in fixed) / len(fixed),
        "mean_probe_function_projected": sum(float(item["probe_gain"]) for item in projected) / len(projected),
        "mean_assessment_function_projected": sum(float(item["assessment_gain"]) for item in projected) / len(projected),
        "mean_adaptation_function_projected": sum(float(item["fit_gain"]) for item in projected) / len(projected),
        "mean_forgetting_function_projected": sum(float(item["protected_forgetting"]) for item in projected) / len(projected),
        "all_hard_guards_pass": hard,
        "primary_gate_pass": primary,
    }


def _hard_guards(cases: Sequence[Mapping[str, Any]]) -> bool:
    if len(cases) != 96 or {item.get("case_index") for item in cases} != set(range(96)):
        return False
    if any(item.get("base_state_sha256") != BASE_STATE_SHA256 for item in cases):
        return False
    for item in cases:
        if item["arm"] == "function_projected":
            if float(item["protected_forgetting"]) > MAX_TREATMENT_FORGETTING or float(item["probe_gain"]) < MIN_TREATMENT_PROBE_GAIN or float(item["function_preservation_error"]) > MAX_TREATMENT_FUNCTION_ERROR:
                return False
        for key in ("fit_gain", "tune_gain", "assessment_gain", "protected_forgetting", "probe_gain", "function_preservation_error", "rollback_max_abs_error"):
            if not _finite(item[key]):
                return False
        if float(item["rollback_max_abs_error"]) > ROLLBACK_TOLERANCE:
            return False
        expected_counts = {"fit_shards": 12, "candidate_states": 24, "candidate_fit_evaluations": 24, "candidate_protected_evaluations": 24, "committed_updates": 0 if item["arm"] == "untouched_base" else 12}
        if item["compute_counts"] != expected_counts:
            return False
        if len(item["fit_candidate_digests"]) != 24:
            return False
        if item["event_log"] != _events(item["case_index"], item["arm"], item):
            return False
    for seed in REPLICATE_SEEDS:
        for order_seed in ORDER_SEEDS:
            for arm in ARMS:
                if _order_delta(cases, arm, seed, order_seed) > MAX_ORDER_DELTA:
                    return False
    return True


def validate_result(result: Mapping[str, Any]) -> None:
    expected = {"schema_version", "state_slice", "protocol_id", "claim_ceiling", "execution_authorized", "base_state_sha256", "config_sha256", "case_group_count", "case_count", "arms", "cases", "summary", "classification", "result_sha256"}
    _require(set(result) == expected, "result keys")
    _require(result["schema_version"] == SCHEMA_VERSION and result["state_slice"] == STATE_SLICE and result["protocol_id"] == PROTOCOL_ID, "result identity")
    _require(result["claim_ceiling"] == CLAIM_CEILING and result["execution_authorized"] is False, "result boundary")
    _require(result["base_state_sha256"] == BASE_STATE_SHA256 and result["config_sha256"] == CONFIG_SHA256, "result digest bindings")
    _require(result["case_group_count"] == 32 and result["case_count"] == 96 and result["arms"] == list(ARMS), "result cardinality")
    _validate_no_raw_keys(result)
    _require(result["result_sha256"] == _digest({key: value for key, value in result.items() if key != "result_sha256"}), "result digest")
    cases = result["cases"]
    _require(isinstance(cases, list), "cases type")
    for case in cases:
        _validate_scalar_case(case)
    _require(_hard_guards(cases), "hard guards or event log")
    expected_cases = []
    case_index = 0
    for replicate_seed in REPLICATE_SEEDS:
        for order_seed in ORDER_SEEDS:
            for direction in DIRECTIONS:
                for arm in ARMS:
                    expected_cases.append(_expected_case(case_index, replicate_seed, order_seed, direction, arm))
                    case_index += 1
    _require(cases == expected_cases, "case aggregate mismatch")
    expected_summary = _summary(cases)
    _require(result["summary"] == expected_summary, "summary mismatch")
    classification = "LocalSyntheticFunctionalPlasticityCandidate" if expected_summary["primary_gate_pass"] else "NoCandidate"
    _require(result["classification"] == classification, "classification mismatch")


def validate_path(path: Path) -> None:
    resolved = path.resolve()
    expected = (EXPECTED_RUN_ROOT / "result.json").resolve()
    _require(resolved == expected, "result path is not the declared custody path")
    _require(path.is_file() and not path.is_symlink(), "result path is not a regular file")
    _require(EXPECTED_RUN_ROOT.is_dir() and not EXPECTED_RUN_ROOT.is_symlink(), "custody root invalid")
    names = sorted(item.name for item in EXPECTED_RUN_ROOT.iterdir())
    _require(names == ["result.json"], "unexpected custody files")
    raw = path.read_bytes()
    _require(raw.endswith(b"\n") and not raw[:-1].endswith(b"\n"), "result final LF")
    result = json.loads(raw.decode("utf-8"))
    _require(raw == _canonical(result) + b"\n", "result is not canonical")
    validate_result(result)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("result", type=Path)
    args = parser.parse_args()
    validate_path(args.result)
    print(json.dumps({"state_slice": STATE_SLICE, "validated": str(args.result.resolve())}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
