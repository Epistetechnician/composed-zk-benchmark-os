"""State slice: astral-trace-completeness-gemma3-causal-feature-effects-v2."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))

import corpus_v2_slice as corpus
import protocol_v2_slice as protocol


def test_fresh_corpus_is_deterministic_and_split_complete():
    first = corpus.families()
    assert first == corpus.families()
    assert len(first) == 96
    assert [family.split for family in first].count("fit") == 32
    assert [family.split for family in first].count("tune") == 32
    assert [family.split for family in first].count("assessment") == 32
    assert len({family.family_id for family in first}) == 96
    assert corpus.public_manifest()["corpus_id"] == "gemma3-causal-feature-effects-cross-half-stability-v2-20260901"


def test_families_are_unique_and_token_safe_by_contract():
    families = corpus.families()
    assert len({family.prompt() for family in families}) == protocol.FAMILY_COUNT
    for family in families:
        assert 0 <= family.answer() <= 9
        assert 0 <= family.answer("corrupted") <= 9
        assert family.answer() != family.answer("corrupted")


def test_arm_assignment_is_fixed_balanced_and_reproducible():
    first = corpus.arm_order("v2-family-000")
    assert first == corpus.arm_order("v2-family-000")
    assert first[0] == "natural"
    assert set(first) == set(__import__("protocol_v2_slice").INTERVENTION_KINDS)
