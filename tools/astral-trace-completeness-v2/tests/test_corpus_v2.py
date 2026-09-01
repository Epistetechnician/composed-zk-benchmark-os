"""State slice: astral-trace-completeness-gemma3-end-to-end-v2."""

import sys
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import corpus_v2


def test_fresh_corpus_is_deterministic_and_split_before_effects():
    first = corpus_v2.families()
    second = corpus_v2.families()
    assert first == second
    assert len(first) == 48
    assert Counter(item.split for item in first) == {"fit": 16, "tune": 16, "assessment": 16}
    assert corpus_v2.public_manifest() == corpus_v2.public_manifest()


def test_corrupted_variant_changes_operator_and_answer():
    family = corpus_v2.families()[0]
    assert family.prompt("clean") != family.prompt("corrupted")
    assert family.answer("clean") != family.answer("corrupted")

