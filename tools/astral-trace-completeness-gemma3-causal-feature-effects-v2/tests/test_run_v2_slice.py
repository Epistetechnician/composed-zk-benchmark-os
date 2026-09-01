"""State slice: astral-trace-completeness-gemma3-causal-feature-effects-v2."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))

import run_v2


def test_final_artifacts_are_append_only_per_execution() -> None:
    aggregate, expiry = run_v2._artifact_names("execution-123")
    assert aggregate == "v2-causal-feature-effects-aggregate-execution-123.json"
    assert expiry == "raw-deletion-completion-execution-123.json"
    assert aggregate != "v2-causal-feature-effects-aggregate.json"
    assert expiry != "raw-deletion-completion-v2.json"


def test_feature_selection_requires_cross_half_replication(monkeypatch, tmp_path: Path) -> None:
    import torch

    stable_features = (7, 11, 19, 23)
    families = [type("Family", (), {"family_id": f"v2-family-{index:03d}"})() for index in range(32)]

    def fake_run(_generator, _tokenizer, family, **_kwargs):
        values = torch.zeros(1, 1, run_v2.protocol.FEATURE_WIDTH)
        for offset, feature_index in enumerate(stable_features):
            values[0, 0, feature_index] = 16 - offset
        if family.family_id.endswith(tuple(f"{index:03d}" for index in range(16))):
            values[0, 0, 101] = 100
        else:
            values[0, 0, 102] = 100
        return type(
            "Run",
            (),
            {
                "logits": (torch.zeros(1, 10),),
                "_v2_slice_feature_store": {
                    "features": values,
                    "reconstruction": {
                        "sum_squared_error": 1.0,
                        "target_squared_sum": 100.0,
                    },
                },
            },
        )(), None

    monkeypatch.setattr(run_v2, "_run_one", fake_run)
    selected, _reconstruction, stability = run_v2._feature_selection(
        None, None, None, families, tmp_path
    )
    assert selected == stable_features
    assert stability["intersection_count"] >= run_v2.protocol.FEATURE_SELECTION_COUNT
    assert stability["pass"] is True
