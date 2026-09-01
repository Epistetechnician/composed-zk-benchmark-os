"""Hermetic V45 contract tests.

State slice: astral-stage0c-qwen36-response-anchored-causal-target-v45.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import protocol_v45 as protocol


def test_candidate_pool_is_unique_and_excludes_prior_custody() -> None:
    assert len(protocol.CANDIDATE_GUTENBERG_IDS) == len(set(protocol.CANDIDATE_GUTENBERG_IDS))
    assert not set(protocol.CANDIDATE_GUTENBERG_IDS) & set(protocol.FRESHNESS_EXCLUSION_INVENTORY)


def test_canonical_measurement_contract_is_frozen() -> None:
    assert protocol.STATE_SLICE == protocol.PROTOCOL_ID
    assert protocol.BLOCK_COUNT * protocol.BLOCK_WIDTH == protocol.EXPECTED_HIDDEN_WIDTH
    assert protocol.POSITION_NAME == "content_anchor"
    assert protocol.CONTENT_ANCHOR_OFFSET == 8
    assert protocol.FIXED_TOKEN_LENGTH == 320
    assert protocol.CONTROL_NAMES == ("activation_only", "text_only", "exact_copy", "shuffled", "constant", "matched")
    assert protocol.RIDGE_ALPHAS == (0.1, 1.0, 10.0, 100.0)
    assert "only A or B" in protocol.CANONICAL_WRAPPER


def test_protocol_manifest_digest_is_stable_and_claims_are_narrow() -> None:
    manifest = protocol.protocol_manifest()
    assert manifest["protocol"] == protocol.PROTOCOL_ID
    assert manifest["state_slice"] == protocol.STATE_SLICE
    assert protocol.canonical_digest(manifest) == protocol.canonical_digest(protocol.protocol_manifest())
    assert manifest["prediction_lock_before_assessment"] is True
    assert manifest["aggregate_only_result_retention"] is True
