"""Hermetic V44 protocol contract tests.

State slice: astral-stage0c-qwen36-causal-target-measurement-invariance-v44.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import protocol_v44 as protocol


def test_selection_is_fresh_complete_and_split_balanced() -> None:
    ids = [int(item["gutenberg_id"]) for item in protocol.SELECTION]
    assert len(ids) == protocol.TOTAL_DOCUMENTS
    assert len(set(ids)) == protocol.TOTAL_DOCUMENTS
    assert not set(ids) & protocol.KNOWN_RESERVED_GUTENBERG_IDS
    assert all(sum(1 for item in protocol.SELECTION if item["split"] == split) == protocol.DOCUMENTS_PER_SPLIT for split in protocol.SPLITS)


def test_measurement_contract_is_predeclared_and_controls_are_unchanged() -> None:
    assert protocol.WRAPPER_NAMES == ("wrapper_alpha", "wrapper_beta", "wrapper_gamma")
    assert protocol.CONTROL_NAMES == ("activation_only", "text_only", "exact_copy", "shuffled", "constant", "matched")
    assert protocol.CANDIDATE_LAYERS == (12, 19, 26)
    assert protocol.POSITION_NAMES == ("final", "penultimate")
    assert protocol.POSITION_OFFSETS == (1, 2)
    assert protocol.FIXED_POSITION_RULE == "final_or_penultimate_input_position_before_response"
    assert protocol.protocol_manifest()["prediction_lock_before_assessment"] is True
    assert protocol.protocol_manifest()["aggregate_only_result_retention"] is True


def test_protocol_identity_and_digest_are_stable() -> None:
    assert protocol.PROTOCOL_ID == "astral-stage0c-qwen36-causal-target-measurement-invariance-v44"
    assert protocol.STATE_SLICE == protocol.PROTOCOL_ID
    assert protocol.selection_digest() == protocol.canonical_digest(list(protocol.SELECTION))
    assert protocol.freshness_exclusion_digest(protocol.FRESHNESS_EXCLUSION_INVENTORY) == protocol.canonical_digest(sorted(protocol.KNOWN_RESERVED_GUTENBERG_IDS))
