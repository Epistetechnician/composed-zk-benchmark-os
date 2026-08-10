import importlib.util
import sys
from collections import Counter
from pathlib import Path


PATH = Path(__file__).resolve().parents[1] / "v23.py"
SPEC = importlib.util.spec_from_file_location("astral_v23_tested", PATH)
V23 = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = V23
SPEC.loader.exec_module(V23)


def test_fresh_corpus_census():
    rows = V23.V22.build_trials()
    assert len(rows) == 192
    assert Counter(row.split for row in rows) == {"fit": 96, "tune": 48, "assessment": 48}
    assert set(V23.CONCEPTS).isdisjoint({
        "cedar", "violin", "glacier", "lantern", "meadow", "copper", "harbor", "velvet",
        "canyon", "marble", "orchid", "compass", "willow", "tunnel", "saffron", "anchor",
    })


def test_activation_none_identity_and_label_balance():
    rows = V23.V22.build_trials()
    for concept in V23.CONCEPTS:
        for wrapper in range(4):
            selected = {row.condition: row for row in rows if row.concept == concept and row.wrapper == wrapper}
            assert selected["activation"].prompt == selected["none"].prompt
    assert set(row.correct_token for row in rows) == set(V23.V22.TOKENS)


def test_model_contract_is_proportional_and_distinct():
    assert V23.SITES == (3, 7, 11)
    assert V23.MODEL_PATH != V23.V22.V17.MODEL_PATH
    assert V23.CLAIM == "LocalDevelopmentCapabilityTierPerturbationReplication"
