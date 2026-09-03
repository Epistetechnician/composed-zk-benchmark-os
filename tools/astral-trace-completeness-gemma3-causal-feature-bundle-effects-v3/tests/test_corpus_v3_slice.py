"""State slice: astral-trace-completeness-gemma3-causal-feature-bundle-effects-v3."""

import corpus_v3_slice as corpus
import protocol_v3_slice as protocol


def test_fresh_corpus_is_deterministic_and_split_complete() -> None:
    first = corpus.families()
    assert first == corpus.families()
    assert len(first) == 144
    assert [sum(family.split == split for family in first) for split in ("fit", "tune", "assessment")] == [48, 48, 48]
    assert first[0].family_id == "v3-family-000"
    assert corpus.public_manifest()["corpus_id"] == protocol.CORPUS_ID


def test_arm_assignment_is_fixed_and_covers_every_declared_arm() -> None:
    first = corpus.arm_order("v3-family-000")
    assert first == corpus.arm_order("v3-family-000")
    assert first[0] == "natural"
    assert set(first) == set(protocol.INTERVENTION_KINDS)
    assert len(first) == len(protocol.INTERVENTION_KINDS)
