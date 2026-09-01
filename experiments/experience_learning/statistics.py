"""Dependency-free multi-seed estimates, paired tests, and Pareto gates."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Mapping, Sequence


@dataclass(frozen=True)
class Estimate:
    n: int
    mean: float
    std: float
    ci95_low: float | None
    ci95_high: float | None

    def as_dict(self) -> dict:
        return {"n": self.n, "mean": self.mean, "std": self.std,
                "ci95_low": self.ci95_low, "ci95_high": self.ci95_high}


def estimate(values: Sequence[float]) -> Estimate:
    values = [float(value) for value in values]
    if not values:
        raise ValueError("at least one value is required")
    mean = sum(values) / len(values)
    variance = sum((value - mean) ** 2 for value in values) / max(1, len(values) - 1)
    std = math.sqrt(variance)
    half = 1.96 * std / math.sqrt(len(values)) if len(values) > 1 else None
    return Estimate(len(values), mean, std, None if half is None else mean - half,
                    None if half is None else mean + half)


def paired_test(candidate: Sequence[float], reference: Sequence[float]) -> dict:
    if len(candidate) != len(reference) or not candidate:
        raise ValueError("paired samples must be non-empty and equally sized")
    differences = [float(a) - float(b) for a, b in zip(candidate, reference)]
    result = estimate(differences)
    if len(differences) < 2 or result.std == 0.0:
        # Keep the JSON result finite. A zero-variance paired sample has a
        # deterministic sign; an infinite t statistic is represented by the
        # explicit ``degenerate`` flag instead of a non-standard JSON value.
        statistic = 0.0 if result.mean == 0.0 else math.copysign(1.0, result.mean)
        p_value = 1.0 if result.mean == 0.0 else 0.0
        degenerate = True
    else:
        statistic = result.mean / (result.std / math.sqrt(result.n))
        # Normal approximation is explicitly labeled; SciPy is not required.
        p_value = math.erfc(abs(statistic) / math.sqrt(2.0))
        degenerate = False
    return {"test": "paired_t_normal_approximation", "n": result.n,
            "mean_difference": result.mean, "difference_estimate": result.as_dict(),
            "statistic": statistic, "p_value": p_value, "degenerate": degenerate}


def pareto_frontier(records: Mapping[str, Mapping[str, float]],
                    metrics: Sequence[str] = ("mean_loss", "updates", "active_synaptic_ops", "state_bytes")) -> list[str]:
    """Return non-dominated algorithms, treating every metric as lower-is-better."""
    names = list(records)
    frontier = []
    for name in names:
        point = records[name]
        dominated = False
        for other in names:
            if other == name: continue
            candidate = records[other]
            if all(candidate.get(metric, float("inf")) <= point.get(metric, float("inf")) for metric in metrics) and \
               any(candidate.get(metric, float("inf")) < point.get(metric, float("inf")) for metric in metrics):
                dominated = True
                break
        if not dominated: frontier.append(name)
    return frontier


def publish_gate(stream_records: Mapping[str, Mapping[str, Mapping[str, float]]],
                 reference: str = "sgd_b1", alpha: float = 0.05) -> dict:
    """Require a paired-significant loss and resource improvement in >=2 families."""
    qualifying = []
    details = {}
    for algorithm in sorted({name for records in stream_records.values() for name in records}):
        if algorithm == reference: continue
        wins = 0
        for stream, records in stream_records.items():
            if algorithm not in records or reference not in records: continue
            candidate, baseline = records[algorithm], records[reference]
            lower_loss = candidate["mean_loss"] < baseline["mean_loss"]
            lower_resource = (
                candidate["updates"] <= baseline["updates"] and
                candidate["active_synaptic_ops"] <= baseline["active_synaptic_ops"] and
                candidate["state_bytes"] <= baseline["state_bytes"]
            )
            paired_p = candidate.get("paired_p_value")
            statistically_supported = paired_p is not None and paired_p <= alpha
            if lower_loss and lower_resource and statistically_supported:
                wins += 1
        details[algorithm] = {"qualifying_streams": wins}
        if wins >= 2: qualifying.append(algorithm)
    return {"status": "candidate" if qualifying else "no_candidate",
            "reference": reference, "alpha": alpha,
            "requirement": "lower loss, non-inferior resources, paired p <= alpha in >=2 streams",
            "qualifying_algorithms": qualifying, "details": details}
