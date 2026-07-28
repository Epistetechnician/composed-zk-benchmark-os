from __future__ import annotations

from collections import defaultdict
import hashlib
import math
import random
import struct
from typing import Mapping


CellKey = tuple[str, int, str]


def clustered_bootstrap_all(
    contrasts: Mapping[str, Mapping[CellKey, float]],
    *,
    family_categories: Mapping[str, str],
    seed: int,
    replicates: int,
    upper_margins: Mapping[str, float] | None = None,
) -> dict[str, dict[str, float | int | str]]:
    """Paired, equal-family-weighted family/seed bootstrap with fixed task orders."""
    if replicates <= 0:
        raise ValueError("replicates must be positive")
    if not contrasts:
        return {}
    key_sets = [set(values) for values in contrasts.values()]
    expected_keys = key_sets[0]
    if not expected_keys or any(keys != expected_keys for keys in key_sets[1:]):
        raise ValueError("all contrasts must contain the same paired cells")

    families = sorted({key[0] for key in expected_keys})
    if set(families) != set(family_categories):
        raise ValueError("family category census does not match contrast cells")
    seeds_by_family: dict[str, list[int]] = {}
    orders_by_family_seed: dict[tuple[str, int], list[str]] = {}
    for family_id in families:
        seeds = sorted({key[1] for key in expected_keys if key[0] == family_id})
        seeds_by_family[family_id] = seeds
        for run_seed in seeds:
            orders_by_family_seed[(family_id, run_seed)] = sorted(
                key[2] for key in expected_keys if key[0] == family_id and key[1] == run_seed
            )

    cluster_values: dict[str, dict[tuple[str, int], float]] = {}
    for contrast_id, values in contrasts.items():
        aggregate: dict[tuple[str, int], float] = {}
        for family_id in families:
            for run_seed in seeds_by_family[family_id]:
                orders = orders_by_family_seed[(family_id, run_seed)]
                aggregate[(family_id, run_seed)] = _mean(
                    [float(values[(family_id, run_seed, order_id)]) for order_id in orders]
                )
        cluster_values[contrast_id] = aggregate

    observed = {
        contrast_id: _mean(
            [
                _mean([values[(family_id, run_seed)] for run_seed in seeds_by_family[family_id]])
                for family_id in families
            ]
        )
        for contrast_id, values in cluster_values.items()
    }
    strata: dict[str, list[str]] = defaultdict(list)
    for family_id in families:
        strata[family_categories[family_id]].append(family_id)
    ordered_strata = [(category, sorted(members)) for category, members in sorted(strata.items())]

    rng = random.Random(seed)
    stream_hash = hashlib.sha256()
    samples = {contrast_id: [] for contrast_id in contrasts}
    for _ in range(replicates):
        sampled_clusters: list[tuple[str, list[int]]] = []
        for _, stratum_families in ordered_strata:
            for _family_draw in stratum_families:
                family_index = rng.randrange(len(stratum_families))
                family_id = stratum_families[family_index]
                stream_hash.update(struct.pack(">I", family_index))
                available_seeds = seeds_by_family[family_id]
                seed_draws: list[int] = []
                for _seed_draw in available_seeds:
                    seed_index = rng.randrange(len(available_seeds))
                    stream_hash.update(struct.pack(">I", seed_index))
                    seed_draws.append(available_seeds[seed_index])
                sampled_clusters.append((family_id, seed_draws))
        for contrast_id, values in cluster_values.items():
            samples[contrast_id].append(
                _mean(
                    [
                        _mean([values[(family_id, sampled_seed)] for sampled_seed in seed_draws])
                        for family_id, seed_draws in sampled_clusters
                    ]
                )
            )

    stream_digest = f"sha256:{stream_hash.hexdigest()}"
    margins = dict(upper_margins or {})
    reports: dict[str, dict[str, float | int | str]] = {}
    for contrast_id, values in samples.items():
        point = observed[contrast_id]
        ordered = sorted(values)
        q05 = _quantile(ordered, 0.05)
        q95 = _quantile(ordered, 0.95)
        lower = 2.0 * point - q95
        upper = 2.0 * point - q05
        variance = _mean([(value - _mean(values)) ** 2 for value in values])
        report: dict[str, float | int | str] = {
            "mean": round(point, 10),
            "basic_lower_95": round(lower, 10),
            "basic_upper_95": round(upper, 10),
            "clustered_standard_error": round(math.sqrt(variance), 10),
            "one_sided_p_value_positive": round(
                (1 + sum(value <= 0.0 for value in values)) / (replicates + 1),
                10,
            ),
            "bootstrap_seed": seed,
            "bootstrap_replicates": replicates,
            "sample_index_stream_sha256": stream_digest,
        }
        if contrast_id in margins:
            margin = float(margins[contrast_id])
            report["upper_margin"] = margin
            report["one_sided_p_value_at_most_margin"] = round(
                (1 + sum(value >= margin for value in values)) / (replicates + 1),
                10,
            )
        reports[contrast_id] = report
    return reports


def holm_adjust(p_values: Mapping[str, float]) -> dict[str, float]:
    """Return monotone Holm adjusted p-values for a fixed comparison family."""
    ordered = sorted((float(value), key) for key, value in p_values.items())
    count = len(ordered)
    adjusted: dict[str, float] = {}
    running = 0.0
    for rank, (value, key) in enumerate(ordered):
        running = max(running, min(1.0, (count - rank) * value))
        adjusted[key] = round(running, 10)
    return adjusted


def _quantile(ordered: list[float], probability: float) -> float:
    if not ordered:
        raise ValueError("cannot take a quantile of an empty sample")
    position = probability * (len(ordered) - 1)
    low = int(math.floor(position))
    high = int(math.ceil(position))
    if low == high:
        return ordered[low]
    fraction = position - low
    return ordered[low] * (1.0 - fraction) + ordered[high] * fraction


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0
