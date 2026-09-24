"""Public record-construction tests for causal-intervention records.

State slice: proof-carrying-nano-causal-intervention-record-v1.
"""

from __future__ import annotations

import pytest

from tools.proof_carrying_nano_causal_intervention_record_v1.record import (
    CausalInterventionRecordError,
    create_record,
)


DIGESTS = iter("abcdef0123456789" * 8)


def _digest(seed: str) -> str:
    return "sha256:" + (seed * 64)[:64]


def _endpoint(checkpoint: str, activation: str, layer: int, position: int) -> dict:
    return {
        "activation_digest": _digest(activation),
        "checkpoint_digest": _digest(checkpoint),
        "layer": layer,
        "site": "decoder_block_output",
        "token_position": position,
    }


def _record(*, proof_status: str = "checked") -> dict:
    return create_record(
        parent_activation_action_digest=_digest("1"),
        donor=_endpoint("2", "3", 2, 4),
        target=_endpoint("4", "5", 2, 4),
        operator={
            "parameters": {
                "coefficient": "1",
                "interpolation": "none",
                "source": "donor_activation",
                "source_activation_digest": _digest("3"),
                "target": "target_activation",
                "target_activation_digest": _digest("5"),
            },
            "schema": "exact-activation-replacement-v1",
            "type": "replace_token_vector",
        },
        effect={
            "metric": "logit_margin_delta",
            "units": "logit",
            "value": "0.250000",
        },
        controls=(
            {
                "control_id": "no_op",
                "effect": {"metric": "logit_margin_delta", "units": "logit", "value": "0.000000"},
                "kind": "no_op",
            },
            {
                "control_id": "exact_copy",
                "effect": {"metric": "logit_margin_delta", "units": "logit", "value": "0.000000"},
                "kind": "exact_copy",
            },
        ),
        host_parameter_digest_before=_digest("6"),
        host_parameter_digest_after=_digest("6"),
        replay={
            "input_digest": _digest("7"),
            "replay_index": 0,
            "replay_seed": 17,
            "runner_identity": "fixture-record-runner-v1",
        },
        nano_identity="causal-record-nano-v1",
        timestamp="2026-09-17T12:00:00Z",
        proof_status=proof_status,
    )


def test_create_record_is_closed_and_binds_exact_operator_and_effect() -> None:
    record = _record()
    assert set(record) == {
        "assessment_status",
        "claim",
        "controls",
        "donor",
        "effect",
        "host_parameter_digest_after",
        "host_parameter_digest_before",
        "intervention_operator",
        "nano_identity",
        "parent_activation_action_digest",
        "proof_status",
        "protocol_identity",
        "record_digest",
        "record_schema",
        "record_status",
        "replay",
        "state_slice",
        "target",
        "timestamp",
    }
    assert record["record_status"] == "UnreviewedObservation"
    assert record["assessment_status"] == "SEALED_UNTIL_INDEPENDENT_REVIEW"
    assert record["proof_status"] == "checked"
    assert record["intervention_operator"]["type"] == "replace_token_vector"
    assert record["intervention_operator"]["parameters"]["coefficient"] == "1"
    assert record["effect"]["value"] == "0.250000"
    assert all("observation_digest" in control for control in record["controls"])


@pytest.mark.parametrize(
    "change, match",
    [
        (lambda record: record["intervention_operator"]["parameters"].update({"coefficient": "0.5"}), "operator"),
        (lambda record: record["effect"].update({"value": "NaN"}), "effect"),
        (lambda record: record.update({"proof_status": "pending"}), "proof status"),
    ],
)
def test_create_record_rejects_unsafe_direct_inputs(change, match: str) -> None:
    record = _record()
    change(record)
    with pytest.raises(CausalInterventionRecordError, match=match):
        create_record(
            parent_activation_action_digest=record["parent_activation_action_digest"],
            donor=record["donor"],
            target=record["target"],
            operator=record["intervention_operator"],
            effect=record["effect"],
            controls=record["controls"],
            host_parameter_digest_before=record["host_parameter_digest_before"],
            host_parameter_digest_after=record["host_parameter_digest_after"],
            replay=record["replay"],
            nano_identity=record["nano_identity"],
            timestamp=record["timestamp"],
            proof_status=record["proof_status"],
        )
