"""Noise-floor and oracle-feature controls for V2."""

from __future__ import annotations

from typing import Sequence

from .benchmark import make_learner
from .metrics import MetricAccumulator
from .streams import STREAMS
from .types import Experience, StepStats


class RunningMeanLearner:
    """Causal noise-floor control: predicts only the running target mean."""

    batch_size = 1
    allows_replay = False
    event_driven = False

    def __init__(self):
        self.mean = 0.0; self.count = 0; self.updates = 0

    def predict(self, features):
        return self.mean

    def observe(self, item: Experience):
        prediction = self.mean
        loss = 0.5 * (prediction - item.target) ** 2
        self.count += 1
        self.mean += (item.target - self.mean) / self.count
        self.updates += 1
        return StepStats(prediction, loss, True, 1, self.count, 0,
                         len(item.event_indices), 0, 0, 0, 8)

    def flush(self): return 0
    def digest(self): return ""


def _project(item: Experience, indices: Sequence[int]) -> Experience:
    index_map = {value: position for position, value in enumerate(indices)}
    next_features = None if item.next_features is None else tuple(item.next_features[i] for i in indices)
    events = tuple(index_map[i] for i in item.event_indices if i in index_map)
    return Experience(item.step, tuple(item.features[i] for i in indices), item.target,
                      reward=item.reward, next_features=next_features, done=item.done,
                      task_id=item.task_id, event_indices=events, source_id=item.source_id)


def evaluate_control(stream_name: str, steps: int | None, seed_offset: int,
                     control: str, hyperparameters: dict[str, dict]) -> dict:
    kwargs = {"steps": steps} if steps is not None and stream_name != "delayed_reward" else {}
    if stream_name == "delayed_reward" and steps is not None:
        kwargs = {"episodes": max(1, steps // 8), "horizon": 8}
    stream = STREAMS[stream_name](seed=7 + seed_offset, **kwargs)
    experiences = list(stream)
    fit_end, tune_end = max(1, len(experiences) // 3), max(2, 2 * len(experiences) // 3)
    if control == "noise_floor":
        learner = RunningMeanLearner()
        projected = experiences
    elif control == "oracle_feature_sgd_b1":
        indices = tuple(getattr(stream, "predictable_feature_indices", ()))
        learner = make_learner("sgd_b1", len(indices), hyperparameters.get("sgd_b1"))
        projected = [_project(item, indices) for item in experiences]
    else:
        raise ValueError(f"unknown control: {control}")
    accumulators = {"fit": MetricAccumulator.create(), "tune": MetricAccumulator.create(), "assessment": MetricAccumulator.create()}
    for index, item in enumerate(projected):
        split = "fit" if index < fit_end else "tune" if index < tune_end else "assessment"
        accumulators[split].add(learner.observe(item), item.target)
    learner.flush()
    assessment = accumulators["assessment"].summary()
    return {"status": "executed", "summaries": {key: value.summary() for key, value in accumulators.items()},
            "assessment_metrics": {"mean_loss": assessment["mean_prediction_loss"],
                                   "updates": assessment["updates"],
                                   "active_synaptic_ops": assessment["active_synaptic_ops"],
                                   "state_bytes": assessment["state_bytes"]}}
