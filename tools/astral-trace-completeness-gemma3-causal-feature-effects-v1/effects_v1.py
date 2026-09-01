"""Pure causal-effect and locking calculations for V1.

State slice: astral-trace-completeness-gemma3-causal-feature-effects-v1.
"""

from __future__ import annotations

import math
from collections.abc import Iterable, Sequence
from typing import Any, Mapping


def _finite(value: float) -> float:
    if not math.isfinite(value):
        raise ValueError("nonfinite effect")
    return value


def paired_mean(values: Sequence[float]) -> float:
    if not values:
        raise ValueError("empty paired effect")
    return _finite(sum(values) / len(values))


def sign_agreement(observed: Sequence[float], predicted: Sequence[float]) -> float:
    if len(observed) != len(predicted) or not observed:
        raise ValueError("paired sign vectors are incomplete")
    matches = 0
    for left, right in zip(observed, predicted):
        if not math.isfinite(left) or not math.isfinite(right):
            raise ValueError("nonfinite sign vector")
        if (left == 0.0 and right == 0.0) or (left > 0.0) == (right > 0.0):
            matches += 1
    return matches / len(observed)


def holm_adjust(p_values: Sequence[float]) -> tuple[float, ...]:
    if not p_values:
        raise ValueError("empty multiplicity family")
    if any(not math.isfinite(value) or value < 0.0 or value > 1.0 for value in p_values):
        raise ValueError("invalid p value")
    order = sorted(range(len(p_values)), key=p_values.__getitem__)
    adjusted = [0.0] * len(p_values)
    running = 0.0
    for rank, index in enumerate(order):
        running = max(running, (len(p_values) - rank) * p_values[index])
        adjusted[index] = min(1.0, running)
    return tuple(adjusted)


def total_variation(first: Sequence[float], second: Sequence[float]) -> float:
    if len(first) != len(second) or not first:
        raise ValueError("distribution vectors are incomplete")
    first_sum = sum(first)
    second_sum = sum(second)
    if first_sum <= 0.0 or second_sum <= 0.0:
        raise ValueError("distribution mass is not positive")
    left = [value / first_sum for value in first]
    right = [value / second_sum for value in second]
    return _finite(0.5 * sum(abs(a - b) for a, b in zip(left, right)))


def logit_margin(logits: Sequence[float], target_index: int, distractor_index: int) -> float:
    if target_index < 0 or distractor_index < 0 or target_index >= len(logits) or distractor_index >= len(logits):
        raise ValueError("logit index outside output distribution")
    return _finite(float(logits[target_index]) - float(logits[distractor_index]))


def paired_effect(baseline: Sequence[float], treatment: Sequence[float]) -> tuple[float, ...]:
    if len(baseline) != len(treatment) or not baseline:
        raise ValueError("paired baseline and treatment vectors are incomplete")
    return tuple(_finite(float(right) - float(left)) for left, right in zip(baseline, treatment))


def percentile(values: Sequence[float], probability: float) -> float:
    if not values or probability < 0.0 or probability > 1.0:
        raise ValueError("invalid percentile request")
    ordered = sorted(float(value) for value in values)
    position = (len(ordered) - 1) * probability
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return _finite(ordered[lower])
    fraction = position - lower
    return _finite(ordered[lower] + fraction * (ordered[upper] - ordered[lower]))


def fixed_seed_bootstrap(values: Sequence[float], *, repeats: int = 10_000, seed: int = 2026083102) -> tuple[float, float, float]:
    if not values or repeats <= 0:
        raise ValueError("bootstrap requires values and positive repeats")
    import random

    rng = random.Random(seed)
    means = []
    for _ in range(repeats):
        sample = [values[rng.randrange(len(values))] for _ in values]
        means.append(paired_mean(sample))
    return (
        paired_mean(values),
        percentile(means, 0.025),
        percentile(means, 0.975),
    )


def balanced_accuracy(labels: Sequence[int], predictions: Sequence[int]) -> float:
    if len(labels) != len(predictions) or not labels:
        raise ValueError("classification vectors are incomplete")
    groups: dict[int, list[bool]] = {0: [], 1: []}
    for label, prediction in zip(labels, predictions):
        if label not in groups or prediction not in (0, 1):
            raise ValueError("binary classification vectors required")
        groups[label].append(label == prediction)
    if not groups[0] or not groups[1]:
        raise ValueError("both classes are required")
    return _finite(0.5 * (sum(groups[0]) / len(groups[0]) + sum(groups[1]) / len(groups[1])))


def power_pass(simulated_power: float) -> bool:
    return _finite(simulated_power) >= 0.80


def repeat_means(
    rows: Sequence[Mapping[str, Any]],
    *,
    key_fields: Sequence[str],
    value_field: str = "margin_delta",
    repeat_count: int,
) -> dict[tuple[Any, ...], float]:
    """Collapse exact repeat cells and reject incomplete or duplicate cells."""

    if repeat_count <= 0 or not key_fields:
        raise ValueError("repeat aggregation requires keys and positive repeats")
    grouped: dict[tuple[Any, ...], dict[int, float]] = {}
    for row in rows:
        key = tuple(row.get(field) for field in key_fields)
        repeat_index = row.get("repeat_index")
        value = row.get(value_field)
        if not isinstance(repeat_index, int) or not 0 <= repeat_index < repeat_count:
            raise ValueError("repeat index is outside the frozen cell")
        if not isinstance(value, (int, float)) or not math.isfinite(float(value)):
            raise ValueError("repeat value is nonfinite")
        cell = grouped.setdefault(key, {})
        if repeat_index in cell:
            raise ValueError("duplicate repeat cell")
        cell[repeat_index] = float(value)
    expected = set(range(repeat_count))
    if any(set(cell) != expected for cell in grouped.values()):
        raise ValueError("repeat cell is incomplete")
    return {key: paired_mean(tuple(cell.values())) for key, cell in grouped.items()}


def exact_two_sided_sign_p(values: Sequence[float]) -> float:
    """Return the exact two-sided sign-test p-value, excluding zero signs."""

    signs = [1 if value > 0 else -1 if value < 0 else 0 for value in values]
    positive = sum(sign == 1 for sign in signs)
    negative = sum(sign == -1 for sign in signs)
    n = positive + negative
    if n == 0:
        return 1.0
    minority = min(positive, negative)
    lower_tail = sum(math.comb(n, index) for index in range(minority + 1)) / (2**n)
    return min(1.0, _finite(2.0 * lower_tail))


def primary_feature_summary(
    rows: Sequence[Mapping[str, Any]],
    selected_features: Sequence[int],
    *,
    repeat_count: int,
    alpha: float,
    bootstrap_repeats: int = 10_000,
    bootstrap_seed: int = 2026083102,
) -> dict[str, Any]:
    """Summarize locked feature-ablation effects by family before multiplicity."""

    means = repeat_means(
        [row for row in rows if row.get("kind") == "feature_ablation"],
        key_fields=("family_id", "feature_index", "kind"),
        repeat_count=repeat_count,
    )
    summaries: list[dict[str, Any]] = []
    p_values: list[float] = []
    for feature in selected_features:
        values = [
            value
            for (family_id, feature_index, _kind), value in means.items()
            if feature_index == feature
        ]
        if not values:
            raise ValueError("selected feature has no complete effect cells")
        mean, lower, upper = fixed_seed_bootstrap(
            values,
            repeats=bootstrap_repeats,
            seed=bootstrap_seed + int(feature),
        )
        p_value = exact_two_sided_sign_p(values)
        p_values.append(p_value)
        summaries.append(
            {
                "feature_index": feature,
                "family_count": len(values),
                "mean_margin_delta": mean,
                "bootstrap_95_low": lower,
                "bootstrap_95_high": upper,
                "sign_p": p_value,
                "nonzero_family_rate": sum(abs(value) > 1e-5 for value in values) / len(values),
            }
        )
    adjusted = holm_adjust(p_values)
    for summary, adjusted_p in zip(summaries, adjusted):
        summary["holm_adjusted_p"] = adjusted_p
        summary["pass"] = adjusted_p <= alpha and summary["nonzero_family_rate"] > 0.0
    return {
        "features": summaries,
        "multiplicity": "Holm",
        "alpha": alpha,
        "all_pass": all(summary["pass"] for summary in summaries),
    }


def causal_scrub_score(
    rows: Sequence[Mapping[str, Any]],
    lock: Mapping[str, Any],
    *,
    repeat_count: int,
    kind: str = "feature_ablation",
    minimum: float | None = None,
    maximum: float | None = None,
) -> dict[str, Any]:
    """Score held-out sign predictions against family-clustered effect cells."""

    if minimum is None and maximum is None:
        raise ValueError("causal scrub requires a fixed lower or upper bound")
    if minimum is not None and not 0.0 <= minimum <= 1.0:
        raise ValueError("causal scrub minimum is outside the unit interval")
    if maximum is not None and not 0.0 <= maximum <= 1.0:
        raise ValueError("causal scrub maximum is outside the unit interval")
    if minimum is not None and maximum is not None and minimum > maximum:
        raise ValueError("causal scrub bounds are inverted")

    means = repeat_means(
        [row for row in rows if row.get("kind") == kind],
        key_fields=("family_id", "feature_index", "kind"),
        repeat_count=repeat_count,
    )
    labels: list[int] = []
    predictions: list[int] = []
    for (family_id, feature_index, _kind), value in sorted(means.items()):
        coefficient = float(lock["coefficients"].get(str(feature_index), 0.0))
        labels.append(1 if value > 0.0 else 0)
        predictions.append(1 if coefficient > 0.0 else 0)
    try:
        score = balanced_accuracy(labels, predictions)
    except ValueError as exc:
        return {
            "balanced_accuracy": None,
            "n": len(labels),
            "kind": kind,
            "minimum": minimum,
            "maximum": maximum,
            "estimable": False,
            "error": str(exc),
            "pass": False,
        }
    return {
        "balanced_accuracy": score,
        "n": len(labels),
        "kind": kind,
        "minimum": minimum,
        "maximum": maximum,
        "estimable": True,
        "pass": (minimum is None or score >= minimum) and (maximum is None or score <= maximum),
    }


def fixed_seed_power_simulation(
    *,
    family_count: int,
    repeat_count: int,
    standardized_effect: float,
    icc: float,
    alpha: float = 0.05,
    simulations: int = 10_000,
    seed: int = 2026083103,
) -> float:
    """Estimate known-variance two-sided power under clustered repeats."""

    if family_count <= 0 or repeat_count <= 0 or simulations <= 0:
        raise ValueError("power dimensions must be positive")
    if not 0.0 <= icc < 1.0 or standardized_effect < 0.0:
        raise ValueError("power parameters are outside the frozen domain")
    if not 0.0 < alpha < 1.0:
        raise ValueError("power alpha is outside the unit interval")
    import random

    rng = random.Random(seed)
    family_mean_sd = math.sqrt(icc + (1.0 - icc) / repeat_count)
    standard_error = family_mean_sd / math.sqrt(family_count)
    from statistics import NormalDist

    critical = NormalDist().inv_cdf(1.0 - alpha / 2.0)
    detected = 0
    for _ in range(simulations):
        mean = standardized_effect + sum(rng.gauss(0.0, family_mean_sd) for _ in range(family_count)) / family_count
        if abs(mean / standard_error) >= critical:
            detected += 1
    return detected / simulations
