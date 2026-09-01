"""Hermetic V46 contract tests.

State slice: astral-stage0c-qwen36-answer-aligned-causal-target-v46.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import protocol_v46 as protocol


def test_fresh_pool_is_unique_and_disjoint_from_prior_intake() -> None:
    assert len(protocol.CANDIDATE_GUTENBERG_IDS) == len(set(protocol.CANDIDATE_GUTENBERG_IDS))
    assert not set(protocol.CANDIDATE_GUTENBERG_IDS) & set(protocol.FRESHNESS_EXCLUSION_INVENTORY)


def test_answer_aligned_contract_is_frozen() -> None:
    assert protocol.STATE_SLICE == protocol.PROTOCOL_ID
    assert protocol.FEATURE_MAP_ID == "fixed-response-unembedding-margin-of-counterfactual-minus-ordinary-v1"
    assert protocol.FEATURE_DIMENSION == 1
    assert protocol.CANDIDATE_LAYERS == (12, 19, 26)
    assert protocol.CONTENT_ANCHOR_OFFSET == 8
    assert protocol.FIXED_TOKEN_LENGTH == 320
    assert protocol.CONTROL_NAMES == ("activation_only", "text_only", "exact_copy", "shuffled", "constant", "matched")
    assert protocol.RIDGE_ALPHAS == (0.1, 1.0, 10.0, 100.0)


def test_manifest_is_stable_and_claim_ceiling_is_local() -> None:
    manifest = protocol.protocol_manifest()
    assert protocol.canonical_digest(manifest) == protocol.canonical_digest(protocol.protocol_manifest())
    assert manifest["feature_map"]["uses_fixed_response_unembedding_margin"] is True
    assert manifest["prediction_lock_before_assessment"] is True
    assert manifest["aggregate_only_result_retention"] is True
