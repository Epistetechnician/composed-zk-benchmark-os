"""Synthetic-only qualification for Oak Lab H100 replication V8.

State slice: ``oaklab-experience-learning-h100-replication-v8``.

This module is additive implementation after the independent V8 packet-bound
``ACCEPT``.  It deliberately stops before fit/tune locks, assessment rows,
provider allocation, real data, model execution, energy capture, and
publication.  The result is a qualification artifact, not a campaign result.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import struct
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Sequence

from .benchmark import _canonical_for_digest
from .compile_oaklab_h100_v8_protocol import lp32, sha256_file, splitmix64
from .statistics import estimate, paired_test


STATE_SLICE = "oaklab-experience-learning-h100-replication-v8"
SCHEMA = "oaklab.h100.v8.synthetic-qualification.v1"
ROOT = Path(__file__).resolve().parents[2]
SOURCE = Path("experiments/experience_learning/oaklab_h100_v8_protocol.json")
COMPILED = Path("experiments/experience_learning/oaklab_h100_v8_compiled_protocol.json")
REVIEW = Path("docs/research/experience-learning/63-oaklab-h100-replication-v8-independent-review.json")
IMPLEMENTATION = Path("experiments/experience_learning/oaklab_h100_v8_synthetic_qualification.py")
RESULT = Path("experiments/experience_learning/oaklab_h100_v8_synthetic_qualification.json")

FAMILIES = (
    "predictable_noise",
    "drift",
    "delayed_reward",
    "event",
    "long_horizon",
    "null",
)
STREAMS = (
    "sparse_signal_v8",
    "drifting_relevance_v8",
    "delayed_reward_v8",
    "event_sensor_v8",
    "long_horizon_v8",
    "pure_noise_v8",
)
SEEDS = tuple(range(4000, 4048))
ROWS = 256
FIT_ROWS = 128
LEARNING_RATE = 0.05
GAMMA = 0.90
LAMBDA = 0.80
THETA_RATE = 0.05
DUAL_RATE = 0.01
ACTION_P_NUM = 1
ACTION_P_DEN = 4
CONTROLLER_STATE_BYTES = 216
ACTION_SEED = bytes.fromhex(
    "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
)


@dataclass(frozen=True)
class Item:
    row: int
    features: tuple[float, ...]
    target: float
    events: tuple[int, ...]
    segment: int


@dataclass
class Counter:
    rows: int = 0
    updates: int = 0
    active_operations: int = 0
    storage_bytes: int = 0
    learned_events: int = 0
    latency_ns: int = 0


def canonical(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                       ensure_ascii=True, allow_nan=False) + "\n").encode()


def digest(value: Any) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def _stable_digest(value: Any) -> str:
    """Digest evidence while excluding the explicitly volatile latency field."""
    if isinstance(value, dict):
        return digest({key: _stable_digest_value(item) for key, item in value.items()
                       if key != "latency_ns"})
    return digest(value)


def _stable_digest_value(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _stable_digest_value(item) for key, item in value.items()
                if key != "latency_ns"}
    if isinstance(value, list):
        return [_stable_digest_value(item) for item in value]
    return value


def _source_digest() -> str:
    return sha256_file(ROOT / SOURCE)


def _protocol_raw() -> bytes:
    return bytes.fromhex(_source_digest())


def _row_root(cohort: str, stream: str, seed: int, row: int) -> bytes:
    frame = (
        lp32(b"oaklab.h100.v8.prng.v1")
        + _protocol_raw()
        + lp32(cohort.encode())
        + lp32(stream.encode())
        + struct.pack("<Q", seed)
        + struct.pack("<I", row)
    )
    return hashlib.sha256(frame).digest()


def _uniform53(raw: int) -> float:
    return (raw >> 11) / float(1 << 53)


def _normal12(raws: Sequence[int]) -> float:
    return sum(_uniform53(raw) for raw in raws) - 6.0


def _rademacher(raw: int) -> float:
    return 1.0 if (raw & 1) else -1.0


def _draws(stream: str, seed: int, row: int, repeats: int) -> list[int]:
    """Consume every declared draw in ordinal order, with no redraw path."""
    return splitmix64(_row_root("fit", stream, seed, row), repeats)


def _segment(stream: str, row: int) -> int:
    if stream in {"drifting_relevance_v8", "event_sensor_v8", "long_horizon_v8"}:
        return 0 if row < 128 else 1
    return 0


def generate(stream: str, seed: int, rows: int = ROWS) -> list[Item]:
    """Generate the exact V8 synthetic roster without conditional draws."""
    if stream not in STREAMS:
        raise ValueError(f"unknown V8 stream: {stream}")
    output: list[Item] = []
    cached_cue = 1.0
    ring = [0.0] * 32
    for row in range(rows):
        if stream == "sparse_signal_v8":
            raw = _draws(stream, seed, row, 32)
            signal = _rademacher(raw[0])
            activities = [_uniform53(value) for value in raw[1:16]]
            polarities = [_rademacher(value) for value in raw[16:31]]
            noise = _normal12(raw[31:])
            features = [signal]
            for activity, polarity in zip(activities, polarities):
                features.append(polarity if activity < 0.15 else 0.0)
            events = tuple(index for index, value in enumerate(features) if value != 0.0)
            target = 1.5 * signal + 0.25 * noise
        elif stream == "drifting_relevance_v8":
            raw = _draws(stream, seed, row, 9)
            features = [2.0 * _uniform53(value) - 1.0 for value in raw[:8]]
            noise = _normal12(raw[8:])
            target = (2.0 * features[0] if row < 128 else -2.0 * features[1]) + 0.1 * noise
            events = tuple(range(8))
        elif stream == "delayed_reward_v8":
            raw = _draws(stream, seed, row, 14)
            episode_row = row % 8
            if episode_row == 0:
                cached_cue = _rademacher(raw[0])
            unused_cue = _rademacher(raw[1])
            noise = _normal12(raw[2:14])
            sign = 1.0 if row < 16 * 8 else -1.0
            features = [cached_cue, unused_cue, 0.0, 0.0]
            target = sign if episode_row == 7 else 0.0
            target += 0.1 * noise
            events = tuple(index for index, value in enumerate(features) if value != 0.0)
        elif stream == "event_sensor_v8":
            raw = _draws(stream, seed, row, 7)
            indices = [min(63, int(_uniform53(value) * 64.0)) for value in raw[:3]]
            polarities = [_rademacher(value) for value in raw[3:6]]
            noise = _normal12(raw[6:])
            values = [0.0] * 64
            for index, polarity in zip(indices, polarities):
                values[index] = polarity
            anchor = 1.0 if row % 2 else -1.0
            values[0] = anchor
            events = tuple(sorted(index for index, value in enumerate(values) if value != 0.0))
            target = (1.0 if row < 128 else -1.0) * anchor + 0.15 * noise
            features = values
        elif stream == "long_horizon_v8":
            raw = _draws(stream, seed, row, 9)
            features = [2.0 * _uniform53(value) - 1.0 for value in raw[:8]]
            noise = _normal12(raw[8:])
            delayed = ring[row % 32]
            sign = 1.0 if row < 128 else -1.0
            target = sign * delayed + 0.25 * noise
            ring[row % 32] = features[0]
            events = tuple(range(8))
        else:
            raw = _draws(stream, seed, row, 33)
            activities = [_uniform53(value) for value in raw[:16]]
            polarities = [_rademacher(value) for value in raw[16:32]]
            noise = _normal12(raw[32:])
            features = [polarity if activity < 0.15 else 0.0
                        for activity, polarity in zip(activities, polarities)]
            events = tuple(index for index, value in enumerate(features) if value != 0.0)
            target = noise
        if not all(math.isfinite(value) for value in (*features, target)):
            raise FloatingPointError(f"nonfinite generated row: {stream}/{seed}/{row}")
        output.append(Item(row, tuple(features), float(target), events, _segment(stream, row)))
    return output


def _action_hash(stream: str, seed: int, row: int) -> int:
    frame = (
        lp32(b"oaklab.h100.v8.action.v1")
        + _protocol_raw()
        + ACTION_SEED
        + lp32(b"fit")
        + lp32(stream.encode())
        + struct.pack("<Q", seed)
        + struct.pack("<I", row)
    )
    return int.from_bytes(hashlib.sha256(frame).digest(), "big")


def _features(loss: float, events: int, dimension: int, debt: float) -> tuple[float, ...]:
    # The context map is fixed, finite, and computed before any model write.
    return (1.0, min(1.0, max(0.0, loss)), events / max(1, dimension), debt)


def _dot(left: Sequence[float], right: Sequence[float]) -> float:
    value = 0.0
    for lhs, rhs in zip(left, right):
        value += lhs * rhs
    return value


@dataclass
class Model:
    dimension: int
    weights: list[float] = field(init=False)
    bias: float = 0.0

    def __post_init__(self) -> None:
        self.weights = [0.0] * self.dimension

    def predict(self, features: Sequence[float]) -> float:
        return self.bias + _dot(self.weights, features)

    def apply(self, features: Sequence[float], target: float, scale: float) -> None:
        error = self.predict(features) - target
        for index, value in enumerate(features):
            self.weights[index] -= LEARNING_RATE * scale * error * value
        self.bias -= LEARNING_RATE * scale * error


@dataclass
class Controller:
    dimension: int
    model: Model = field(init=False)
    theta: list[float] = field(default_factory=lambda: [0.0] * 4)
    eligibility: list[float] = field(default_factory=lambda: [0.0] * 4)
    q_old: float = 0.0
    dual_mu: float = 0.0
    previous_features: list[float] = field(default_factory=lambda: [0.0] * 4)
    previous_q: float = 0.0
    previous_cost: float = 0.0
    pending_valid: bool = False
    pending_loss: float = 0.0
    pending_action: int = 0
    pending_prediction: float = 0.0
    cumulative_apply_cost: float = 0.0
    processed_rows: int = 0
    gated_rows: int = 0

    def __post_init__(self) -> None:
        self.model = Model(self.dimension)

    def _q(self, action: int, context: Sequence[float]) -> float:
        action_features = (0.0 if action == 0 else 1.0, *context[1:])
        return _dot(self.theta, action_features)

    def _credit_previous(self, current_loss: float, current_context: Sequence[float]) -> None:
        if not self.pending_valid:
            return
        reward = self.pending_loss - current_loss - self.dual_mu * (self.previous_cost - 0.50)
        q_current = self._q(self.pending_action, current_context)
        delta = reward + GAMMA * q_current - self.previous_q
        eligibility_new = [GAMMA * LAMBDA * value + previous
                           for value, previous in zip(self.eligibility, self.previous_features)]
        theta_new = [theta + THETA_RATE * delta * trace
                      for theta, trace in zip(self.theta, eligibility_new)]
        dual_mu_new = min(2.0, max(0.0, self.dual_mu + DUAL_RATE * (self.previous_cost - 0.50)))
        self.eligibility = eligibility_new
        self.theta = theta_new
        self.q_old = q_current
        self.dual_mu = dual_mu_new

    def step(self, item: Item, stream: str, seed: int, fit: bool, counter: Counter) -> tuple[float, int, int]:
        started = time.perf_counter_ns()
        prediction = self.model.predict(item.features)
        error = prediction - item.target
        loss = 0.5 * error * error
        context = _features(loss, len(item.events), self.dimension,
                            self.cumulative_apply_cost / max(1, self.processed_rows))
        # Fit is the only phase allowed to update the controller.  Tune uses
        # the frozen controller policy and cannot feed current-block outcomes
        # back into action selection or theta.
        if fit:
            self._credit_previous(loss, context)
        if fit:
            threshold = (ACTION_P_NUM * (1 << 256)) // ACTION_P_DEN
            action = 0 if _action_hash(stream, seed, item.row) < threshold else 1
        else:
            apply_q = self._q(0, context)
            skip_q = self._q(1, context)
            action = 0 if apply_q >= skip_q else 1
        cost = 1.0 if action == 0 else 0.0
        if action == 0:
            self.model.apply(item.features, item.target, 1.0)
            self.cumulative_apply_cost += cost
        else:
            self.gated_rows += 1
        self.processed_rows += 1
        self.pending_valid = True
        self.pending_loss = loss
        self.pending_action = action
        self.pending_prediction = prediction
        self.previous_features = list(context)
        self.previous_q = self._q(action, context)
        self.previous_cost = cost
        counter.rows += 1
        counter.updates += int(action == 0)
        apply = int(action == 0)
        # controller_dot + forward + loss + gradient + model update + writes,
        # with every unit counted separately under the frozen operation AST.
        counter.active_operations += (2 * 4 - 1) + (2 * self.dimension + 1) + 3 + apply * 4 * (self.dimension + 1)
        counter.storage_bytes = 8 * (self.dimension + 1) + CONTROLLER_STATE_BYTES
        counter.learned_events += len(item.events)
        counter.latency_ns += time.perf_counter_ns() - started
        return loss, action, item.segment

    def terminal_credit(self, terminal_loss: float) -> None:
        # The terminal row receives gamma-zero credit and performs no action.
        if not self.pending_valid:
            return
        reward = self.pending_loss - terminal_loss - self.dual_mu * (self.previous_cost - 0.50)
        eligibility_new = [GAMMA * LAMBDA * value + previous
                           for value, previous in zip(self.eligibility, self.previous_features)]
        delta = reward - self.previous_q
        self.theta = [theta + THETA_RATE * delta * trace
                      for theta, trace in zip(self.theta, eligibility_new)]
        self.eligibility = eligibility_new
        self.dual_mu = min(2.0, max(0.0, self.dual_mu + DUAL_RATE * (self.previous_cost - 0.50)))
        self.pending_valid = False


def _run_arm(stream: str, seed: int, candidate: bool) -> dict[str, Any]:
    items = generate(stream, seed)
    dimension = len(items[0].features)
    counter = Counter()
    model = Model(dimension)
    controller = Controller(dimension) if candidate else None
    tune_losses: list[float] = []
    tune_segments: list[int] = []
    actions = 0
    for item in items:
        if candidate:
            loss, action, segment = controller.step(item, stream, seed, item.row < FIT_ROWS, counter)
            actions += int(action == 0)
        else:
            started = time.perf_counter_ns()
            prediction = model.predict(item.features)
            error = prediction - item.target
            loss = 0.5 * error * error
            model.apply(item.features, item.target, 1.0)
            segment = item.segment
            counter.rows += 1
            counter.updates += 1
            counter.active_operations += (2 * 4 - 1) + (2 * dimension + 1) + 3 + 4 * (dimension + 1)
            counter.storage_bytes = 8 * (dimension + 1)
            counter.learned_events += len(item.events)
            counter.latency_ns += time.perf_counter_ns() - started
            actions += 1
        if item.row >= FIT_ROWS:
            tune_losses.append(loss)
            tune_segments.append(segment)
    if candidate:
        controller.terminal_credit(tune_losses[-1])
        final_digest = digest({"model": controller.model.__dict__, "theta": controller.theta,
                               "eligibility": controller.eligibility, "q_old": controller.q_old,
                               "dual_mu": controller.dual_mu, "processed_rows": controller.processed_rows})
        gated = controller.gated_rows
    else:
        final_digest = digest(model.__dict__)
        gated = 0
    segments = sorted(set(tune_segments))
    lags: list[int] = []
    for segment in segments:
        if segment == 0 or segment not in tune_segments:
            continue
        point = tune_segments.index(segment)
        pre = tune_losses[max(0, point - 16):point]
        post = tune_losses[point:]
        if len(pre) < 16 or not post:
            lags.append(len(post))
            continue
        baseline = sorted(pre)[len(pre) // 2]
        threshold = 1.10 * baseline
        lag = len(post)
        for index in range(0, max(0, len(post) - 15)):
            first = post[index:index + 8]
            second = post[index + 8:index + 16]
            if len(first) == 8 and len(second) == 8 and sum(first) / 8 <= threshold and sum(second) / 8 <= threshold:
                lag = index
                break
        lags.append(lag)
    return {
        "seed": seed,
        "mean_loss": sum(tune_losses) / len(tune_losses),
        "adaptation_lag": max(lags) if lags else 0,
        "updates": counter.updates,
        "active_operations": counter.active_operations,
        "storage_bytes": counter.storage_bytes,
        "learned_events": counter.learned_events,
        "latency_ns": counter.latency_ns,
        "apply_rows": actions,
        "gated_rows": gated,
        "counter": counter.__dict__,
        "final_state_digest": final_digest,
        "row_digest": _stable_digest({"stream": stream, "seed": seed, "losses": tune_losses,
                                       "segments": tune_segments, "counter": counter.__dict__}),
    }


def _holm(raw: dict[str, float], group: str) -> dict[str, Any]:
    ordered = sorted(raw.items(), key=lambda pair: (pair[1], pair[0]))
    adjusted: dict[str, float] = {}
    previous = 0.0
    total = len(ordered)
    for rank, (key, value) in enumerate(ordered, start=1):
        adjusted_value = min(1.0, (total - rank + 1) * value)
        adjusted_value = max(previous, adjusted_value)
        adjusted[key] = adjusted_value
        previous = adjusted_value
    return {"group": group, "raw_p_values": raw, "adjusted_p_values": adjusted,
            "method": "Holm step-down over raw paired tests"}


def _family_gate(rows: list[dict[str, Any]], family: str) -> dict[str, Any]:
    reference = [row["reference"]["mean_loss"] for row in rows]
    candidate = [row["candidate"]["mean_loss"] for row in rows]
    paired = paired_test(candidate, reference)
    ref_adapt = [row["reference"]["adaptation_lag"] for row in rows]
    cand_adapt = [row["candidate"]["adaptation_lag"] for row in rows]
    ref_ops = [row["reference"]["active_operations"] for row in rows]
    cand_ops = [row["candidate"]["active_operations"] for row in rows]
    ref_updates = [row["reference"]["updates"] for row in rows]
    cand_updates = [row["candidate"]["updates"] for row in rows]
    ref_storage = [row["reference"]["storage_bytes"] for row in rows]
    cand_storage = [row["candidate"]["storage_bytes"] for row in rows]
    return {
        "family": family,
        "candidate_estimate": estimate(candidate).as_dict(),
        "reference_estimate": estimate(reference).as_dict(),
        "paired_test": paired,
        "adaptation": {"candidate": estimate(cand_adapt).as_dict(), "reference": estimate(ref_adapt).as_dict()},
        "resources": {
            "updates": {"candidate": estimate(cand_updates).as_dict(), "reference": estimate(ref_updates).as_dict()},
            "active_operations": {"candidate": estimate(cand_ops).as_dict(), "reference": estimate(ref_ops).as_dict()},
            "storage_bytes": {"candidate": estimate(cand_storage).as_dict(), "reference": estimate(ref_storage).as_dict()},
        },
        "derived_predicates": {
            "loss_no_worse": sum(candidate) / len(candidate) <= sum(reference) / len(reference),
            "loss_strictly_lower": sum(candidate) / len(candidate) < sum(reference) / len(reference),
            "adaptation_no_worse": sum(cand_adapt) / len(cand_adapt) <= sum(ref_adapt) / len(ref_adapt),
            "operations_noninferior_5pct": sum(cand_ops) / len(cand_ops) <= 1.05 * sum(ref_ops) / len(ref_ops),
            "updates_noninferior_5pct": sum(cand_updates) / len(cand_updates) <= 1.05 * sum(ref_updates) / len(ref_updates),
            "storage_noninferior_5pct": sum(cand_storage) / len(cand_storage) <= 1.05 * sum(ref_storage) / len(ref_storage),
        },
    }


def run_qualification() -> dict[str, Any]:
    source_digest = _source_digest()
    compiled_digest = sha256_file(ROOT / COMPILED)
    review = json.loads((ROOT / REVIEW).read_bytes())
    if review.get("review_decision") != "ACCEPT":
        raise ValueError("synthetic qualification requires independent ACCEPT")
    rows_by_family: dict[str, list[dict[str, Any]]] = {family: [] for family in FAMILIES}
    qualification_rows: list[dict[str, Any]] = []
    for stream, family in zip(STREAMS, FAMILIES):
        for seed in SEEDS:
            reference = _run_arm(stream, seed, False)
            candidate = _run_arm(stream, seed, True)
            row = {"schema": "oaklab.h100.v8.synthetic-family-row.v1", "state_slice": STATE_SLICE,
                   "family": family, "stream": stream, "seed": seed,
                   "reference": reference, "candidate": candidate}
            row["row_sha256"] = _stable_digest({key: value for key, value in row.items() if key != "row_sha256"})
            rows_by_family[family].append(row)
            qualification_rows.append(row)
    family_results = {family: _family_gate(rows, family) for family, rows in rows_by_family.items()}
    raw_primary = {family: result["paired_test"]["p_value"] for family, result in family_results.items() if family != "null"}
    holm_primary = _holm(raw_primary, "primary_loss")
    qualifying = []
    for family, result in family_results.items():
        predicates = result["derived_predicates"]
        adjusted = holm_primary["adjusted_p_values"].get(family, 1.0)
        primary_ok = adjusted <= 0.05 and predicates["loss_no_worse"]
        if family != "null" and primary_ok:
            qualifying.append(family)
    shift_families = ("drift", "delayed_reward", "event", "long_horizon")
    adaptation_no_worse = all(family_results[family]["derived_predicates"]["adaptation_no_worse"] for family in shift_families)
    adaptation_strict = any(
        sum(row["candidate"]["adaptation_lag"] for row in rows_by_family[family]) <
        sum(row["reference"]["adaptation_lag"] for row in rows_by_family[family])
        for family in shift_families
    )
    resource_noninferior = all(
        all(family_results[family]["derived_predicates"][metric]
            for metric in ("operations_noninferior_5pct", "updates_noninferior_5pct", "storage_noninferior_5pct"))
        for family in FAMILIES
    )
    null_no_advantage = not family_results["null"]["derived_predicates"]["loss_strictly_lower"]
    gate = {
        "at_least_two_holm_primary_families": len(qualifying) >= 2,
        "adaptation_no_worse_all_shift_families": adaptation_no_worse,
        "adaptation_strictly_better_one_shift_family": adaptation_strict,
        "resources_noninferior_within_5_percent": resource_noninferior,
        "pure_noise_null_no_candidate_advantage": null_no_advantage,
    }
    status = "candidate" if all(gate.values()) else "no_candidate"
    payload: dict[str, Any] = {
        "schema": SCHEMA,
        "state_slice": STATE_SLICE,
        "source_sha256": source_digest,
        "compiled_protocol_sha256": compiled_digest,
        "review_receipt_sha256": review["receipt_sha256"],
        "implementation_sha256": sha256_file(ROOT / IMPLEMENTATION),
        "synthetic_only": True,
        "assessment_materialization_state": "absent",
        "real_execution": "prohibited_pending_synthetic_candidate_and_separate_authorization",
        "hardware_energy": "not_run",
        "seeds": list(SEEDS),
        "rows_per_trajectory": ROWS,
        "fit_rows": FIT_ROWS,
        "hyperparameters": {"learning_rate": LEARNING_RATE, "gamma": GAMMA, "lambda": LAMBDA,
                             "theta_rate": THETA_RATE, "dual_rate": DUAL_RATE,
                             "action_probability": {"p_num": ACTION_P_NUM, "p_den": ACTION_P_DEN}},
        "families": family_results,
        "holm_primary": holm_primary,
        "qualification_rows": qualification_rows,
        "gate": gate,
        "status": status,
        "claim_ceiling": "LocalDevelopmentOakLabH100ReplicationV8SyntheticQualification",
    }
    payload["result_sha256"] = _stable_digest({key: value for key, value in payload.items() if key != "result_sha256"})
    return payload


def write_result(path: Path = RESULT) -> dict[str, Any]:
    result = run_qualification()
    path.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=RESULT)
    args = parser.parse_args()
    result = write_result(args.output)
    print(json.dumps({"status": result["status"], "result_sha256": result["result_sha256"],
                      "qualifying_families": [family for family, value in result["families"].items()
                                               if value["derived_predicates"]["loss_no_worse"]]}, sort_keys=True))


if __name__ == "__main__":
    main()
