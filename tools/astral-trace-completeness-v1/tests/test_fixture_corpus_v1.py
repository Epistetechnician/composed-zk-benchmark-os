import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import fixture_corpus_v1 as fixtures


def test_fixture_corpus_is_fresh_deterministic_and_aggregate_safe():
    first = fixtures.fixture_manifest()
    second = fixtures.fixture_manifest()
    assert first == second
    assert len(first) == fixtures.FIXTURE_COUNT == 8
    assert all(len(row["token_digests"]) == fixtures.FIXTURE_TOKEN_COUNT for row in first)
    assert len(fixtures.corpus_digest()) == 64
