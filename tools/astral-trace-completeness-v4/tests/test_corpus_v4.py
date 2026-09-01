"""State slice: astral-trace-completeness-gemma3-end-to-end-v4."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))

import corpus_v4 as corpus


def test_corpus_is_deterministic_and_split_complete():
    first = corpus.families()
    second = corpus.families()
    assert first == second
    assert len(first) == 48
    assert [family.split for family in first].count("fit") == 16
    assert [family.split for family in first].count("tune") == 16
    assert [family.split for family in first].count("assessment") == 16
    assert len({family.family_id for family in first}) == 48


def test_public_manifest_is_digest_bound():
    manifest = corpus.public_manifest()
    assert manifest["manifest_sha256"] == corpus.protocol.digest_json({key: value for key, value in manifest.items() if key != "manifest_sha256"})
