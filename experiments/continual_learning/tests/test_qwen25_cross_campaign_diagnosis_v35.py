from __future__ import annotations

import pytest

from experiments.continual_learning.diagnose_qwen25_cross_campaign_v35 import _stable, run


def _task(train: float, no_update: float, heldout: float, observed: str) -> dict:
    return {
        "no_update_train": {"accuracy": no_update},
        "adapter_train": {"accuracy": train, "rows": [{"observed": value} for value in observed]},
        "adapter_test": {"accuracy": heldout},
    }


def test_v35_stability_metric_requires_gain_floor_and_nonconstant_output():
    assert _stable(_task(1.0, 0.5, 1.0, "AABBCCDD")) is True
    assert _stable(_task(0.5, 0.5, 1.0, "AABBCCDD")) is False
    assert _stable(_task(1.0, 0.5, 0.5, "AABBCCDD")) is False
    assert _stable(_task(0.75, 0.0, 0.75, "CCCCCCCC")) is False


def test_v35_diagnosis_refuses_overwrite(tmp_path):
    output = tmp_path / "diagnosis"
    output.mkdir()
    with pytest.raises(FileExistsError, match="refusing overwrite"):
        run(tmp_path / "v32", tmp_path / "v34", output)
