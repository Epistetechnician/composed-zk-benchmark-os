"""State slice: astral-trace-completeness-gemma3-causal-feature-bundle-effects-v3."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))

import run_v3


def test_final_artifacts_are_append_only_per_execution() -> None:
    aggregate, expiry = run_v3._artifact_names("execution-123")
    assert aggregate == "v3-causal-feature-bundle-aggregate-execution-123.json"
    assert expiry == "v3-raw-deletion-completion-execution-123.json"
    assert aggregate != "v3-causal-feature-bundle-aggregate.json"
    assert expiry != "v3-raw-deletion-completion-v3.json"


def test_feature_selection_requires_cross_half_bundle_coactivation(monkeypatch, tmp_path: Path) -> None:
    import torch

    stable_features = (7, 11, 19, 23, 29, 31)
    families = [type("Family", (), {"family_id": f"v3-family-{index:03d}"})() for index in range(48)]

    def fake_run(_generator, _tokenizer, family, **_kwargs):
        index = int(family.family_id.rsplit("-", 1)[-1]) + 1
        values = torch.zeros(1, 1, run_v3.protocol.FEATURE_WIDTH)
        for offset, feature_index in enumerate(stable_features):
            values[0, 0, feature_index] = index * (10.0 + offset)
        return type(
            "Run",
            (),
            {
                "logits": (torch.zeros(1, 10),),
                "_v3_feature_store": {
                    "features": values,
                    "reconstruction": {"sum_squared_error": 1.0, "target_squared_sum": 100.0},
                },
            },
        )(), None

    monkeypatch.setattr(run_v3, "_run_one", fake_run)
    selected, reconstruction, stability = run_v3._feature_selection(None, None, None, families, tmp_path)
    assert len(selected) == 3
    assert set(selected).issubset(stable_features)
    assert reconstruction["pass"] is True
    assert stability["intersection_count"] >= run_v3.protocol.FEATURE_STABILITY_MIN_INTERSECTION
    assert stability["pass"] is True
