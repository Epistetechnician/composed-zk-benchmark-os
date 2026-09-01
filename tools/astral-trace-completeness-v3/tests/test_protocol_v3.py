"""State slice: astral-trace-completeness-gemma3-end-to-end-v3."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))

import protocol_v3 as protocol


def test_contract_is_digest_bound_and_uses_pooled_estimand():
    contract = protocol.public_contract()
    assert contract["contract_sha256"] == protocol.digest_json({key: value for key, value in contract.items() if key != "contract_sha256"})
    estimand = contract["normalization_estimand"]
    assert estimand["name"] == "pooled_global_centered_nmse"
    assert estimand["aggregation"] == "pooled sums over every captured fit row; no per-row max, median, or selected-position exclusion"
    assert contract["quality_gate"]["pooled_global_centered_nmse_max"] == 0.05


def test_v3_identity_is_not_v2():
    assert protocol.STATE_SLICE != "astral-trace-completeness-gemma3-end-to-end-v2"
    assert protocol.CORPUS_ID != "gemma3-trace-causal-families-v2-2026-08-30"


def test_trace_event_identity_is_v3():
    event = protocol.TraceEvent(run_id="r", trial_id="t", sequence=0, kind="run_start")
    event.validate()
    assert event.protocol == protocol.PROTOCOL_ID
    assert event.state_slice == protocol.STATE_SLICE
