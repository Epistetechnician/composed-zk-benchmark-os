import importlib.util
import sys
from collections import Counter
from pathlib import Path


PATH = Path(__file__).resolve().parents[1] / "v22.py"
SPEC = importlib.util.spec_from_file_location("astral_v22_tested", PATH)
V22 = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = V22
SPEC.loader.exec_module(V22)


def test_corpus_census_and_splits():
    rows = V22.build_trials()
    assert len(rows) == 192
    assert Counter(row.split for row in rows) == {"fit": 96, "tune": 48, "assessment": 48}
    assert Counter(row.condition for row in rows) == {"activation": 64, "text": 64, "none": 64}


def test_activation_and_none_have_identical_text():
    rows = V22.build_trials()
    for concept in V22.CONCEPTS:
        for wrapper in range(4):
            selected = {(row.condition): row for row in rows if row.concept == concept and row.wrapper == wrapper}
            assert selected["activation"].prompt == selected["none"].prompt
            assert selected["text"].prompt != selected["none"].prompt


def test_response_positions_and_mappings_are_balanced():
    rows = V22.build_trials()
    for split in ("fit", "tune", "assessment"):
        selected = [row for row in rows if row.split == split]
        assert set(row.correct_token for row in selected) == set(V22.TOKENS)
        assert set(row.wrapper for row in selected) == set(range(4))
        for row in selected:
            assert V22.mapping(row.concept, row.wrapper)[row.condition] == row.correct_token
