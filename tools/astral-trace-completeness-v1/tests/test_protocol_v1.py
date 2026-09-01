"""State slice: astral-trace-completeness-native-instrument-v1."""

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import protocol


def test_manifest_is_a_new_separately_named_slice_and_keeps_execution_closed():
    manifest = protocol.protocol_manifest()
    assert manifest["protocol"] == "astral-trace-completeness-native-instrument-v1"
    assert manifest["state_slice"] == manifest["protocol"]
    assert manifest["claim_ceiling"] == "LocalDevelopmentTraceCompletenessInstrumentFeasibilityOnly"
    assert manifest["authorization"]["model_execution_authorized"] is False
    assert manifest["execution"]["execution_authorized"] is False
    assert manifest["independent_review_receipt"] == "PENDING_SIGNED_ACCEPT"


def test_event_identity_digest_excludes_raw_payloads():
    event = protocol.TraceEvent(
        run_id="fixture-run",
        sequence=0,
        kind="run_start",
        metadata={"runner": protocol.RUNNER_ID},
    )
    value = event.to_dict()
    assert set(value) == protocol.EVENT_FIELDS
    assert not any(marker in value for marker in protocol.RAW_FIELD_MARKERS)
    assert value["event_id"] == protocol.canonical_digest({key: value[key] for key in value if key != "event_id"})


def test_event_expectation_is_exact_and_has_paired_boundaries():
    expectation = protocol.EventExpectation(2, 3, 6, 1, 1, 1, 0)
    counts = expectation.counts()
    assert counts["token"] == 2
    assert counts["layer_enter"] == counts["layer_exit"] == 3
    assert counts["module_enter"] == counts["module_exit"] == 6
    assert counts["intervention"] == 0
