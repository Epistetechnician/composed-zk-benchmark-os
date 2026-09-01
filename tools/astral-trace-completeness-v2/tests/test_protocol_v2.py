"""State slice: astral-trace-completeness-gemma3-end-to-end-v2."""

import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import protocol_v2 as protocol


def _event(run, trial, sequence, kind, step=None, **kwargs):
    return protocol.TraceEvent(run, trial, sequence, kind, step=step, **kwargs)


def test_trace_event_rejects_raw_metadata_and_digest_tampering():
    event = _event("r", "t", 0, "run_start", metadata={"prompt_text": "x"})
    with pytest.raises(protocol.ProtocolError, match="raw field"):
        event.validate()
    clean = _event("r", "t", 0, "run_start").to_dict()
    clean["sequence"] = 1
    with pytest.raises(protocol.ProtocolError, match="digest mismatch"):
        protocol.TraceEvent.from_dict(clean)


def test_expectation_has_behavior_and_attention_score_census():
    expectation = protocol.RunExpectation(2, 3, ("a", "b"), ("a", "b"), ("b",), cache_updates_per_step=1)
    counts = expectation.counts()
    assert counts["attention_score"] == 2
    assert counts["behavioral_outcome"] == 2
    assert counts["input_token"] == 4


def test_expectation_rejects_different_module_call_multisets():
    expectation = protocol.RunExpectation(1, 1, ("a", "a"), ("a", "b"), ())
    with pytest.raises(protocol.ProtocolError, match="output registry"):
        expectation.validate()

