import importlib.util
import sys
from collections import Counter
from pathlib import Path

import numpy as np


PATH = Path(__file__).resolve().parents[1] / "v24.py"
SPEC = importlib.util.spec_from_file_location("astral_v24_tested", PATH)
V24 = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = V24
SPEC.loader.exec_module(V24)


def test_fresh_corpus_and_split_census():
    rows = V24.build_trials()
    assert len(rows) == 240
    assert Counter(row.split for row in rows) == {
        "fit": 96,
        "development": 48,
        "tune": 48,
        "assessment": 48,
    }
    exposed = set(V24.V22.CONCEPTS) | {
        "birch",
        "cello",
        "fjord",
        "beacon",
        "prairie",
        "bronze",
        "marina",
        "satin",
        "ravine",
        "granite",
        "lilac",
        "astrolabe",
        "poplar",
        "subway",
        "turmeric",
        "mooring",
    }
    assert set(V24.CONCEPTS).isdisjoint(exposed)


def test_activation_none_prompts_are_identical():
    rows = V24.build_trials()
    for concept in V24.CONCEPTS:
        for wrapper in range(4):
            selected = {
                row.condition: row
                for row in rows
                if row.concept == concept and row.wrapper == wrapper
            }
            assert selected["activation"].prompt == selected["none"].prompt
            assert selected["text"].prompt != selected["none"].prompt


def test_configuration_is_fixed_and_development_only():
    config = V24.fixed_configuration()
    assert config["injection_site"] == 5
    assert config["readout_site"] == 17
    assert config["strength"] == 1.0
    assert config["pca_components"] == 16
    assert config["ridge_penalty"] == 1.0
    assert config["direction_normalization"] == "unit_l2"
    assert config["author_development_authorized"] is True
    assert config["independently_verified"] == "NotRun"


def test_direction_normalization_is_unit_l2_and_rejects_zero():
    direction = V24.normalize_direction(np.asarray([3.0, 4.0], dtype=np.float32))
    assert np.isclose(np.linalg.norm(direction), 1.0)
    with np.testing.assert_raises_regex(
        RuntimeError, "NotRunInvalidConceptDirection"
    ):
        V24.normalize_direction(np.zeros(2, dtype=np.float32))


def test_metrics_and_gate_on_separable_synthetic_features():
    labels = np.tile(np.arange(3), 16)
    wrappers = np.tile(np.arange(4), 12)
    probabilities = np.full((48, 3), 0.05)
    probabilities[np.arange(48), labels] = 0.90
    telemetry = V24.metrics(probabilities, labels, wrappers)
    control_probabilities = np.full((48, 3), 1 / 3)
    control = V24.metrics(control_probabilities, labels, wrappers)
    shuffled = dict(control)
    result = V24.gate(
        {
            "telemetry": telemetry,
            "text": control,
            "output": control,
            "anomaly": control,
            "shuffled": shuffled,
        }
    )
    assert result["passed"]
    assert result["primary_advantage"] == 0.5


def test_open_material_controls_cannot_be_hidden_by_macro_average():
    labels = np.tile(np.arange(3), 16)
    wrappers = np.tile(np.arange(4), 12)
    probabilities = np.zeros((48, 3))
    probabilities[:, 1] = 1.0
    collapsed = V24.metrics(probabilities, labels, wrappers)
    result = V24.gate(
        {
            method: collapsed
            for method in V24.METHODS
        }
    )
    assert not result["passed"]
    assert not result["checks"]["activation_recall"]
    assert not result["checks"]["none_recall"]
