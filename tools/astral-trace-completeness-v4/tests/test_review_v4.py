"""State slice: astral-trace-completeness-gemma3-end-to-end-v4."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))

import protocol_v4 as protocol
import review_v4


def test_review_manifest_is_source_bound():
    manifest = review_v4._source_manifest(Path(__file__).parents[3])
    assert set(manifest["files"]) == set(review_v4.SOURCE_FILES)
    assert manifest["manifest_sha256"] == protocol.digest_json(manifest["files"])
