"""State slice: astral-trace-completeness-gemma3-end-to-end-v4."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))

import protocol_v4 as protocol


def test_contract_is_digest_bound_and_reconstruction_gate_is_frozen():
    contract = protocol.public_contract()
    assert contract["contract_sha256"] == protocol.digest_json({key: value for key, value in contract.items() if key != "contract_sha256"})
    assert contract["asset_variant"].endswith("l0_big_affine")
    assert contract["normalization_estimand"]["name"] == "pooled_global_centered_nmse"
    assert contract["quality_gate"]["pooled_global_centered_nmse_max"] == 0.05


def test_v4_identity_is_fresh_from_v2_and_v3():
    assert protocol.STATE_SLICE == "astral-trace-completeness-gemma3-end-to-end-v4"
    assert protocol.CORPUS_ID == "gemma3-trace-causal-families-v4-2026-08-30"
    assert protocol.CORPUS_ID not in {"gemma3-trace-causal-families-v2-2026-08-30", "gemma3-trace-causal-families-v3-2026-08-30"}


def test_trace_event_is_bound_to_v4():
    event = protocol.TraceEvent(run_id="r", trial_id="t", sequence=0, kind="run_start")
    event.validate()
    assert event.protocol == protocol.PROTOCOL_ID
    assert event.state_slice == protocol.STATE_SLICE
