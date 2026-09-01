"""State slice: astral-trace-completeness-gemma3-causal-feature-effects-v2."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))

import effects_v2_slice as effects
import pytest


def test_effect_metrics_and_holm_are_deterministic():
    assert effects.paired_effect((1.0, 2.0), (2.5, 1.0)) == (1.5, -1.0)
    assert effects.sign_agreement((1.0, -1.0), (2.0, -3.0)) == 1.0
    assert effects.holm_adjust((0.01, 0.02)) == (0.02, 0.02)
    assert effects.total_variation((0.8, 0.2), (0.5, 0.5)) == pytest.approx(0.3)


def test_repeat_aggregation_and_primary_summary_are_fail_closed():
    rows = [
        {"family_id": family, "feature_index": 7, "kind": "feature_ablation", "repeat_index": repeat, "margin_delta": 1.0}
        for family in (f"family-{index}" for index in range(32))
        for repeat in range(3)
    ]
    means = effects.repeat_means(rows, key_fields=("family_id", "feature_index", "kind"), repeat_count=3)
    assert means[("family-0", 7, "feature_ablation")] == 1.0
    summary = effects.primary_feature_summary(rows, (7,), repeat_count=3, alpha=0.05, bootstrap_repeats=100)
    assert summary["all_pass"] is True
    assert summary["features"][0]["holm_adjusted_p"] == pytest.approx(4.656612873077393e-10)


def test_power_simulation_is_deterministic_and_passes_frozen_design():
    first = effects.fixed_seed_power_simulation(
        family_count=32,
        repeat_count=3,
        standardized_effect=0.50,
        icc=0.50,
        simulations=1000,
    )
    assert first == effects.fixed_seed_power_simulation(
        family_count=32,
        repeat_count=3,
        standardized_effect=0.50,
        icc=0.50,
        simulations=1000,
    )
    assert first >= 0.80


def test_causal_scrub_supports_fixed_lower_and_upper_control_bounds():
    rows = [
        {
            "family_id": family,
            "feature_index": feature,
            "kind": kind,
            "repeat_index": repeat,
            "margin_delta": (1.0 if feature == 7 else -1.0)
            if kind == "feature_ablation"
            else (-1.0 if feature == 7 else 1.0),
        }
        for family in (f"family-{index}" for index in range(2))
        for feature in (7, 8)
        for kind in ("feature_ablation", "shuffled")
        for repeat in range(3)
    ]
    lock = {"coefficients": {"7": 1.0, "8": -1.0}}
    assert effects.causal_scrub_score(rows, lock, repeat_count=3, minimum=0.80)["pass"] is True
    assert effects.causal_scrub_score(rows, lock, repeat_count=3, kind="shuffled", maximum=0.60)["pass"] is True

