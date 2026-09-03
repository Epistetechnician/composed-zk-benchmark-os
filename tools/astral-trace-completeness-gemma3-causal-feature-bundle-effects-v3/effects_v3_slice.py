"""Pure causal-bundle estimators and locked validation calculations.

State slice: astral-trace-completeness-gemma3-causal-feature-bundle-effects-v3.
The functions collapse repeats at the family boundary before uncertainty or
prediction scoring. Raw rows remain runner-local and are never publication
artifacts.
"""

from __future__ import annotations

import itertools
import math
import random
from collections.abc import Sequence
from statistics import NormalDist
from typing import Any, Mapping


def _finite(value: float) -> float:
    if not math.isfinite(value):
        raise ValueError("nonfinite effect")
    return float(value)


def paired_mean(values: Sequence[float]) -> float:
    if not values:
        raise ValueError("empty paired effect")
    return _finite(sum(float(value) for value in values) / len(values))


def sign_agreement(observed: Sequence[float], predicted: Sequence[float]) -> float:
    if len(observed) != len(predicted) or not observed:
        raise ValueError("paired sign vectors are incomplete")
    matches = 0
    for left, right in zip(observed, predicted):
        left = _finite(float(left))
        right = _finite(float(right))
        if left == 0.0 or right == 0.0:
            continue
        matches += int((left > 0.0) == (right > 0.0))
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
    return _finite(0.5 * sum(abs(a / first_sum - b / second_sum) for a, b in zip(first, second)))


def logit_margin(logits: Sequence[float], target_index: int, distractor_index: int) -> float:
    if min(target_index, distractor_index) < 0 or max(target_index, distractor_index) >= len(logits):
        raise ValueError("logit index outside output distribution")
    return _finite(float(logits[target_index]) - float(logits[distractor_index]))


def percentile(values: Sequence[float], probability: float) -> float:
    if not values or not 0.0 <= probability <= 1.0:
        raise ValueError("invalid percentile request")
    ordered = sorted(float(value) for value in values)
    position = (len(ordered) - 1) * probability
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return _finite(ordered[lower])
    fraction = position - lower
    return _finite(ordered[lower] + fraction * (ordered[upper] - ordered[lower]))


def fixed_seed_bootstrap(
    values: Sequence[float], *, repeats: int = 10_000, seed: int = 2026090202
) -> tuple[float, float, float]:
    if not values or repeats <= 0:
        raise ValueError("bootstrap requires values and positive repeats")
    rng = random.Random(seed)
    means = [paired_mean([values[rng.randrange(len(values))] for _ in values]) for _ in range(repeats)]
    return paired_mean(values), percentile(means, 0.025), percentile(means, 0.975)


def repeat_means(
    rows: Sequence[Mapping[str, Any]],
    *,
    key_fields: Sequence[str],
    value_field: str = "margin_delta",
    repeat_count: int,
) -> dict[tuple[Any, ...], float]:
    """Collapse exactly three repeat observations into one family-level cell."""

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
    signs = [1 if value > 0 else -1 if value < 0 else 0 for value in values]
    positive = sum(sign == 1 for sign in signs)
    negative = sum(sign == -1 for sign in signs)
    n = positive + negative
    if n == 0:
        return 1.0
    minority = min(positive, negative)
    lower_tail = sum(math.comb(n, index) for index in range(minority + 1)) / (2**n)
    return min(1.0, _finite(2.0 * lower_tail))


def _cell_values(rows: Sequence[Mapping[str, Any]], kind: str, repeat_count: int) -> dict[tuple[Any, ...], float]:
    return repeat_means(
        [row for row in rows if row.get("kind") == kind],
        key_fields=("family_id", "feature_index", "kind"),
        repeat_count=repeat_count,
    )


def bundle_effect_summary(
    rows: Sequence[Mapping[str, Any]],
    bundle_indices: Sequence[int],
    *,
    repeat_count: int,
    alpha: float,
    bootstrap_repeats: int = 10_000,
    bootstrap_seed: int = 2026090202,
) -> dict[str, Any]:
    """Estimate joint bundle necessity and non-additivity over family means."""

    bundle = tuple(int(index) for index in bundle_indices)
    if len(bundle) != 3 or len(set(bundle)) != 3:
        raise ValueError("V3 bundle must contain exactly three distinct features")
    joint = _cell_values(rows, "bundle_ablation", repeat_count)
    singleton = _cell_values(rows, "singleton_ablation", repeat_count)
    bundle_by_family = {key[0]: value for key, value in joint.items() if key[1] is None}
    if len(bundle_by_family) != len(joint):
        raise ValueError("bundle effect rows must have feature_index null")
    singleton_by_feature: dict[int, dict[Any, float]] = {index: {} for index in bundle}
    for (family_id, feature_index, _kind), value in singleton.items():
        if feature_index not in singleton_by_feature:
            raise ValueError("unexpected singleton feature")
        singleton_by_feature[feature_index][family_id] = value
    families = sorted(bundle_by_family)
    if not families or any(
        family_id not in singleton_by_feature[index] for family_id in families for index in bundle
    ):
        raise ValueError("joint and singleton family cells are incomplete")
    joint_values = [bundle_by_family[family_id] for family_id in families]
    interaction_values = [
        bundle_by_family[family_id] - sum(singleton_by_feature[index][family_id] for index in bundle)
        for family_id in families
    ]
    joint_mean, joint_low, joint_high = fixed_seed_bootstrap(
        joint_values, repeats=bootstrap_repeats, seed=bootstrap_seed
    )
    interaction_mean, interaction_low, interaction_high = fixed_seed_bootstrap(
        interaction_values, repeats=bootstrap_repeats, seed=bootstrap_seed + 1
    )
    raw_p = (exact_two_sided_sign_p(joint_values), exact_two_sided_sign_p(interaction_values))
    adjusted = holm_adjust(raw_p)
    quantities = (
        {
            "name": "tau_bundle",
            "mean_margin_delta": joint_mean,
            "bootstrap_95_low": joint_low,
            "bootstrap_95_high": joint_high,
            "sign_p": raw_p[0],
        },
        {
            "name": "kappa_bundle",
            "mean_margin_delta": interaction_mean,
            "bootstrap_95_low": interaction_low,
            "bootstrap_95_high": interaction_high,
            "sign_p": raw_p[1],
        },
    )
    summaries = []
    for quantity, adjusted_p in zip(quantities, adjusted):
        interval_excludes_zero = quantity["bootstrap_95_low"] > 0.0 or quantity["bootstrap_95_high"] < 0.0
        summaries.append(
            {
                **quantity,
                "holm_adjusted_p": adjusted_p,
                "interval_excludes_zero": interval_excludes_zero,
                "pass": adjusted_p <= alpha and interval_excludes_zero,
            }
        )
    relative_interaction = abs(interaction_mean) / max(abs(joint_mean), 1e-5)
    return {
        "bundle_indices": list(bundle),
        "family_count": len(families),
        "repeat_count": repeat_count,
        "primary_quantities": summaries,
        "interaction_ratio": relative_interaction,
        "interaction_ratio_min": 0.25,
        "multiplicity": "Holm over tau_bundle and kappa_bundle",
        "alpha": alpha,
        "all_pass": all(item["pass"] for item in summaries) and relative_interaction >= 0.25,
    }


def family_sign_prediction(
    rows: Sequence[Mapping[str, Any]],
    *,
    kind: str,
    prediction: float,
    repeat_count: int,
) -> dict[str, Any]:
    means = repeat_means(
        [row for row in rows if row.get("kind") == kind],
        key_fields=("family_id", "feature_index", "kind"),
        repeat_count=repeat_count,
    )
    values = [value for (_family_id, _feature_index, _kind), value in sorted(means.items())]
    if not values or prediction == 0.0:
        return {"family_count": len(values), "sign_agreement": 0.0, "pass": False}
    score = sign_agreement(values, [prediction] * len(values))
    return {"family_count": len(values), "sign_agreement": score, "pass": score >= 0.80}


def causal_scrub_score(
    rows: Sequence[Mapping[str, Any]],
    *,
    minimum: float | None = None,
    maximum: float | None = None,
) -> dict[str, Any]:
    """Score one predeclared held-out interchange arm at family level."""

    if (minimum is None) == (maximum is None):
        raise ValueError("causal scrub requires exactly one fixed bound")
    grouped = repeat_means(
        rows,
        key_fields=("family_id", "scrub_arm", "kind"),
        value_field="scrub_correct",
        repeat_count=3,
    )
    values = [value for _key, value in sorted(grouped.items())]
    score = paired_mean(values) if values else 0.0
    passed = bool(values) and ((minimum is not None and score >= minimum) or (maximum is not None and score <= maximum))
    return {
        "balanced_accuracy": score,
        "family_count": len(values),
        "minimum": minimum,
        "maximum": maximum,
        "pass": passed,
    }


def fixed_seed_power_simulation(
    *,
    family_count: int,
    repeat_count: int,
    standardized_effect: float,
    icc: float,
    alpha: float = 0.05,
    simulations: int = 10_000,
    seed: int = 2026090203,
) -> float:
    if family_count <= 0 or repeat_count <= 0 or simulations <= 0:
        raise ValueError("power dimensions must be positive")
    if not 0.0 <= icc < 1.0 or standardized_effect < 0.0 or not 0.0 < alpha < 1.0:
        raise ValueError("power parameters are outside the frozen domain")
    rng = random.Random(seed)
    family_mean_sd = math.sqrt(icc + (1.0 - icc) / repeat_count)
    standard_error = family_mean_sd / math.sqrt(family_count)
    critical = NormalDist().inv_cdf(1.0 - alpha / 2.0)
    detected = 0
    for _ in range(simulations):
        mean = standardized_effect + sum(rng.gauss(0.0, family_mean_sd) for _ in range(family_count)) / family_count
        detected += int(abs(mean / standard_error) >= critical)
    return detected / simulations


def power_pass(simulated_power: float, target: float = 0.80) -> bool:
    return _finite(simulated_power) >= target


def candidate_triples(indices: Sequence[int]) -> tuple[tuple[int, int, int], ...]:
    return tuple(itertools.combinations(sorted(set(int(index) for index in indices)), 3))
