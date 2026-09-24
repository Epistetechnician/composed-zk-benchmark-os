"""Hermetic contract tests for the Bend lane renderer."""

import pytest

from tools.bend_independent_semantic_lane_v1.run_v1 import (
    LaneError,
    PROTOCOL_IDENTITY,
    STATE_SLICE,
    _nat,
    _trace,
    render_laws,
    render_proof,
    render_suite,
)


def _suite():
    return {
        "state_slice": STATE_SLICE,
        "protocol_identity": PROTOCOL_IDENTITY,
        "generator_families": 1,
        "seeds_per_family": 1,
        "cases": [
            {
                "id": "contract",
                "family": "baseline_fsm",
                "seed": 0,
                "trace_id": "accept",
                "expected_code": 0,
                "machine": {
                    "initial_state": 0,
                    "initial_fields": [{"kind": "Int", "value": 0}],
                    "transitions": [
                        {
                            "from": 0,
                            "to": 1,
                            "guard": {"kind": "Bool", "value": True},
                            "actions": [],
                        }
                    ],
                    "invariants": [],
                },
                "trace": {
                    "initial_state": 0,
                    "initial_fields": [],
                    "steps": [0],
                    "expected_final_state": 1,
                    "expected_final_fields": [],
                },
            }
        ],
    }


def test_renderer_keeps_expected_outcomes_out_of_bend_program():
    rendered = render_suite(_suite(), stress_depth=2)
    assert "expected_code" not in rendered
    assert "Case{" in rendered
    assert "Transition{" in rendered


def test_laws_and_proof_follow_bend_gate_shape():
    laws = render_laws()
    proof = render_proof()
    assert "law always_guard_is_true" in laws
    assert "def Laws.always_guard_is_true" in proof
    assert "Suite.main()" in proof


def test_renderer_rejects_unsupported_natural_and_transition_references():
    with pytest.raises(LaneError, match="negative natural"):
        _nat(-1)
    with pytest.raises(LaneError, match="missing transition"):
        _trace(_suite()["cases"][0]["trace"] | {"steps": [9]}, _suite()["cases"][0]["machine"])
