"""Deterministic benchmark orchestration and result schema."""

from __future__ import annotations

import hashlib
import json
import time
from typing import Sequence

from .learners import (
    AdamLearner, EWCLearner, EventDrivenLearner, IDBDLearner,
    NetworkIDBDLearner, OnlineLearner, PlasticityGuardLearner,
    ReplayLearner, SGDLearner, TIDBDLearner,
)
from .metrics import MetricAccumulator
from .streams import STREAMS

STATE_SLICE = "oaklab-experience-learning-baselines-v1"
SCHEMA_VERSION = "oaklab.experience-learning.result.v1"


ALGORITHM_IDS = (
    "sgd_b1", "sgd_b32", "sgd_b128", "adam_b1", "adam_b32", "adam_b128",
    "idbd", "networkidbd", "tidbd", "replay_sgd", "ewc_sgd",
    "plasticity_guard", "event_driven",
)


def make_learner(name: str, dimensions: int, hyperparameters: dict | None = None) -> OnlineLearner:
    params = hyperparameters or {}
    if name.startswith("sgd_b"):
        return SGDLearner(dimensions, learning_rate=params.get("learning_rate", 0.03), batch_size=int(name[5:]))
    if name.startswith("adam_b"):
        return AdamLearner(dimensions, learning_rate=params.get("learning_rate", 0.01), batch_size=int(name[6:]))
    if name == "idbd": return IDBDLearner(dimensions, meta_step=params.get("meta_step", 0.01), initial_step=params.get("initial_step", 0.03))
    if name == "networkidbd": return NetworkIDBDLearner(dimensions, hidden_size=params.get("hidden_size", 8), meta_step=params.get("meta_step", 0.002), initial_step=params.get("initial_step", 0.01))
    if name == "tidbd": return TIDBDLearner(dimensions, gamma=params.get("gamma", 0.9), meta_step=params.get("meta_step", 0.01), initial_step=params.get("initial_step", 0.03), trace_decay=params.get("trace_decay", 0.8))
    if name == "replay_sgd": return ReplayLearner(dimensions, capacity=params.get("capacity", 64), replay_ratio=params.get("replay_ratio", 1), learning_rate=params.get("learning_rate", 0.03))
    if name == "ewc_sgd": return EWCLearner(dimensions, learning_rate=params.get("learning_rate", 0.03), ewc_lambda=params.get("ewc_lambda", 2.0))
    if name == "plasticity_guard": return PlasticityGuardLearner(dimensions, learning_rate=params.get("learning_rate", 0.03), guard_floor=params.get("guard_floor", 0.2), recovery=params.get("recovery", 0.02), surprise_threshold=params.get("surprise_threshold", 1.0))
    if name == "event_driven": return EventDrivenLearner(dimensions, learning_rate=params.get("learning_rate", 0.03), threshold=params.get("threshold", 0.5))
    raise ValueError(f"unknown algorithm: {name}")


def _canonical_for_digest(value):
    if isinstance(value, dict):
        return {key: _canonical_for_digest(item) for key, item in value.items()
                if key != "wall_clock_latency_ns"}
    if isinstance(value, list): return [_canonical_for_digest(item) for item in value]
    return value


def _digest(payload: dict) -> str:
    return hashlib.sha256(json.dumps(_canonical_for_digest(payload), sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def run_benchmark(stream_names: Sequence[str] | None = None, steps: int | None = None,
                  seed_offset: int = 0, algorithms: Sequence[str] = ALGORITHM_IDS,
                  hyperparameters: dict[str, dict] | None = None) -> dict:
    """Run all requested streams and learners with fixed fit/tune/assessment splits."""
    names = tuple(stream_names or STREAMS.keys())
    stream_results = {}
    for stream_name in names:
        if stream_name not in STREAMS:
            raise ValueError(f"unknown stream: {stream_name}")
        kwargs = {"steps": steps} if steps is not None and stream_name not in ("delayed_reward",) else {}
        if stream_name == "delayed_reward" and steps is not None:
            kwargs = {"episodes": max(1, steps // 8), "horizon": 8}
        stream = STREAMS[stream_name](seed=7 + seed_offset, **kwargs)
        experiences = list(stream)
        if not experiences: raise ValueError("stream produced no experiences")
        dimensions = len(experiences[0].features)
        fit_end = max(1, len(experiences) // 3)
        tune_end = max(fit_end + 1, 2 * len(experiences) // 3)
        split_ranges = {"fit": (0, fit_end), "tune": (fit_end, tune_end), "assessment": (tune_end, len(experiences))}
        change_points = [i for i in range(1, len(experiences)) if experiences[i].task_id != experiences[i - 1].task_id]
        algorithm_results = {}
        for algorithm in algorithms:
            if algorithm == "tidbd" and stream_name != "delayed_reward":
                algorithm_results[algorithm] = {
                    "status": "not_applicable",
                    "reason": "TIDBD is a temporal-difference predictor and requires delayed_reward experiences",
                }
                continue
            learner = make_learner(algorithm, dimensions, (hyperparameters or {}).get(algorithm))
            accumulators = {split: MetricAccumulator.create() for split in split_ranges}
            state_snapshots = {}
            previous_task = experiences[0].task_id
            observe_calls = 0
            for index, item in enumerate(experiences):
                if isinstance(learner, EWCLearner) and item.task_id != previous_task:
                    learner.mark_task_boundary()
                previous_task = item.task_id
                split = "fit" if index < fit_end else "tune" if index < tune_end else "assessment"
                started = time.perf_counter_ns()
                stats = learner.observe(item)
                latency = time.perf_counter_ns() - started
                accumulators[split].add(stats, item.target, latency)
                observe_calls += 1
                if index + 1 == fit_end:
                    state_snapshots["fit"] = learner.digest()
                elif index + 1 == tune_end:
                    state_snapshots["tune"] = learner.digest()
            flushed = learner.flush()
            state_snapshots["assessment"] = learner.digest()
            summaries = {split: accumulator.summary(change_points) for split, accumulator in accumulators.items()}
            accounting = {
                "presented_experiences": len(experiences),
                "learner_observe_calls": observe_calls,
                "max_experience_items_per_observe": 1,
                "batch_size": getattr(learner, "batch_size", 1),
                "strict_batch_one": getattr(learner, "batch_size", 1) == 1 and not getattr(learner, "allows_replay", False),
                "explicit_replay": bool(getattr(learner, "allows_replay", False)),
                "flushed_experiences": flushed,
                "hidden_gradient_accumulation": False,
                "event_driven": bool(getattr(learner, "event_driven", False)),
            }
            algorithm_results[algorithm] = {
                "status": "executed",
                "summaries": summaries,
                "accounting": accounting,
                "state_snapshot_digests": state_snapshots,
                "final_state_digest": learner.digest(),
            }
        stream_results[stream_name] = {
            "dimensions": dimensions,
            "n_experiences": len(experiences),
            "predictable_feature_indices": list(getattr(stream, "predictable_feature_indices", ())),
            "split_ranges": {key: list(value) for key, value in split_ranges.items()},
            "change_points": change_points,
            "algorithms": algorithm_results,
        }
    payload = {"schema_version": SCHEMA_VERSION, "state_slice": STATE_SLICE,
               "protocol": "fit-tune-assessment; one immutable experience per observe",
               "stream_names": list(names), "algorithm_names": list(algorithms),
               "seed_offset": seed_offset,
               "streams": stream_results}
    payload["result_digest"] = _digest(payload)
    return payload


def write_result(result: dict, path: str) -> None:
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2, sort_keys=True)
        handle.write("\n")
