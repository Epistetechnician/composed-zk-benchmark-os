"""State slice: astral-trace-completeness-gemma3-end-to-end-v3."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))

import review_v3
import protocol_v3 as protocol


def test_review_manifest_includes_its_own_source_identity():
    manifest = review_v3._source_manifest(Path(__file__).parents[3])
    assert set(manifest["files"]) == set(review_v3.SOURCE_FILES)
    assert manifest["manifest_sha256"] == protocol.digest_json(manifest["files"])
