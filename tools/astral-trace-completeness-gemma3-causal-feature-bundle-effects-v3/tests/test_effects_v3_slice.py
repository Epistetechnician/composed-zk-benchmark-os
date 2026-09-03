"""State slice: astral-trace-completeness-gemma3-causal-feature-bundle-effects-v3."""

import effects_v3_slice as effects
import pytest


def test_repeat_aggregation_is_family_clustered() -> None:
    rows = [
        {"family_id": "family-0", "feature_index": None, "kind": "bundle_ablation", "repeat_index": repeat, "margin_delta": 1.0 + repeat}
        for repeat in range(3)
    ]
    means = effects.repeat_means(rows, key_fields=("family_id", "feature_index", "kind"), repeat_count=3)
    assert means[("family-0", None, "bundle_ablation")] == 2.0


def test_bundle_summary_estimates_non_additivity_with_holm() -> None:
    rows = []
    for family_index in range(16):
        family = f"family-{family_index}"
        for repeat in range(3):
            rows.append({"family_id": family, "feature_index": None, "kind": "bundle_ablation", "repeat_index": repeat, "margin_delta": 1.0})
            for feature, value in ((7, 0.1), (11, 0.2), (19, 0.3)):
                rows.append({"family_id": family, "feature_index": feature, "kind": "singleton_ablation", "repeat_index": repeat, "margin_delta": value})
    summary = effects.bundle_effect_summary(rows, (7, 11, 19), repeat_count=3, alpha=0.05, bootstrap_repeats=100)
    assert summary["all_pass"] is True
    assert summary["interaction_ratio"] == pytest.approx(0.4)
    assert summary["primary_quantities"][1]["name"] == "kappa_bundle"


def test_causal_scrub_uses_precomputed_family_correctness() -> None:
    rows = [
        {"family_id": f"family-{family}", "scrub_arm": "true", "kind": "scrub", "repeat_index": repeat, "scrub_correct": 1}
        for family in range(4)
        for repeat in range(3)
    ]
    assert effects.causal_scrub_score(rows, minimum=0.80)["pass"] is True
    for row in rows:
        row["scrub_correct"] = 0
    assert effects.causal_scrub_score(rows, maximum=0.60)["pass"] is True
