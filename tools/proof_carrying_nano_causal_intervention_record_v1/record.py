"""Closed record-only schema for declared activation interventions.

State slice: proof-carrying-nano-causal-intervention-record-v1.

This module does not execute a host model or an intervention. It normalizes a
declared observation record and binds every nested observation to a digest.
"""

from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation
from typing import Any, Mapping, Sequence

from tools.proof_carrying_nano_interp_v1.protocol import canonical_digest


STATE_SLICE = "proof-carrying-nano-causal-intervention-record-v1"
PROTOCOL_ID = STATE_SLICE
RECORD_SCHEMA = "causal-intervention-record-v1"
OPERATOR_SCHEMA = "exact-activation-replacement-v1"
REPLAY_SCHEMA = "causal-intervention-replay-v1"
SITE = "decoder_block_output"
OPERATOR_TYPE = "replace_token_vector"
OPERATOR_PARAMETERS = {
    "coefficient",
    "interpolation",
    "source",
    "source_activation_digest",
    "target",
    "target_activation_digest",
}
CONTROL_KINDS = {"exact_copy", "matched_control", "no_op", "shuffled_donor", "constant_donor"}
CLAIM_TYPE = "causal_intervention_record"
CLAIM_SEMANTICS = "declared_record_binding_only_no_causal_claim"
RECORD_STATUS = "UnreviewedObservation"
ASSESSMENT_STATUS = "SEALED_UNTIL_INDEPENDENT_REVIEW"
CLAIM_CEILING = "LocalCausalInterventionRecordBindingOnly"
DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")


class CausalInterventionRecordError(ValueError):
    """Raised when a record cannot satisfy the closed contract."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise CausalInterventionRecordError(message)


def _digest(value: Any) -> str:
    return canonical_digest(value)


def _require_digest(value: Any, label: str) -> str:
    _require(isinstance(value, str) and DIGEST_RE.fullmatch(value) is not None, f"{label} digest is invalid")
    return value


def _require_int(value: Any, label: str, *, minimum: int | None = None) -> int:
    _require(isinstance(value, int) and not isinstance(value, bool), f"{label} is invalid")
    if minimum is not None:
        _require(value >= minimum, f"{label} is invalid")
    return value


def _decimal_text(value: Any, label: str) -> str:
    _require(isinstance(value, str) and bool(value), f"{label} must be decimal text")
    try:
        number = Decimal(value)
    except (InvalidOperation, ValueError) as exc:
        raise CausalInterventionRecordError(f"{label} must be decimal text") from exc
    _require(number.is_finite(), f"{label} must be finite")
    _require(str(number) == value, f"{label} is not canonical decimal text")
    return value


def _endpoint(value: Mapping[str, Any], label: str) -> dict[str, Any]:
    _require(isinstance(value, Mapping), f"{label} must be an object")
    _require(set(value) == {"activation_digest", "checkpoint_digest", "layer", "site", "token_position"}, f"{label} schema is not closed")
    return {
        "activation_digest": _require_digest(value["activation_digest"], f"{label} activation"),
        "checkpoint_digest": _require_digest(value["checkpoint_digest"], f"{label} checkpoint"),
        "layer": _require_int(value["layer"], f"{label} layer", minimum=0),
        "site": value["site"],
        "token_position": _require_int(value["token_position"], f"{label} token position", minimum=0),
    }


def _operator(value: Mapping[str, Any], donor: Mapping[str, Any], target: Mapping[str, Any]) -> dict[str, Any]:
    _require(isinstance(value, Mapping), "operator must be an object")
    _require(set(value) in ({"parameters", "schema", "type"}, {"operator_digest", "parameters", "schema", "type"}), "operator schema is not closed")
    parameters = value["parameters"]
    _require(isinstance(parameters, Mapping) and set(parameters) == OPERATOR_PARAMETERS, "operator parameters schema is not closed")
    normalized_parameters = {
        "coefficient": parameters["coefficient"],
        "interpolation": parameters["interpolation"],
        "source": parameters["source"],
        "source_activation_digest": _require_digest(parameters["source_activation_digest"], "operator source activation"),
        "target": parameters["target"],
        "target_activation_digest": _require_digest(parameters["target_activation_digest"], "operator target activation"),
    }
    _require(normalized_parameters["coefficient"] == "1", "operator coefficient is not exact")
    _require(normalized_parameters["interpolation"] == "none", "operator interpolation is not exact")
    _require(normalized_parameters["source"] == "donor_activation", "operator source is invalid")
    _require(normalized_parameters["target"] == "target_activation", "operator target is invalid")
    _require(normalized_parameters["source_activation_digest"] == donor["activation_digest"], "operator donor binding is invalid")
    _require(normalized_parameters["target_activation_digest"] == target["activation_digest"], "operator target binding is invalid")
    unsigned = {"parameters": normalized_parameters, "schema": OPERATOR_SCHEMA, "type": OPERATOR_TYPE}
    normalized = {**unsigned, "operator_digest": _digest(unsigned)}
    if "operator_digest" in value:
        _require(value["operator_digest"] == normalized["operator_digest"], "operator digest mismatch")
    return normalized


def _effect(value: Mapping[str, Any], label: str) -> dict[str, Any]:
    _require(isinstance(value, Mapping), f"{label} must be an object")
    _require(set(value) in ({"metric", "units", "value"}, {"effect_digest", "metric", "units", "value"}), f"{label} schema is not closed")
    _require(isinstance(value["metric"], str) and bool(value["metric"]), f"{label} metric is invalid")
    _require(isinstance(value["units"], str) and bool(value["units"]), f"{label} units are invalid")
    unsigned = {
        "metric": value["metric"],
        "units": value["units"],
        "value": _decimal_text(value["value"], f"{label} value"),
    }
    normalized = {**unsigned, "effect_digest": _digest(unsigned)}
    if "effect_digest" in value:
        _require(value["effect_digest"] == normalized["effect_digest"], f"{label} digest mismatch")
    return normalized


def _controls(values: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    _require(isinstance(values, Sequence) and not isinstance(values, (str, bytes)) and bool(values), "controls are missing")
    normalized: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, value in enumerate(values):
        _require(isinstance(value, Mapping), f"control {index} must be an object")
        _require(set(value) in ({"control_id", "effect", "kind"}, {"control_id", "effect", "kind", "observation_digest"}), f"control {index} schema is not closed")
        control_id = value["control_id"]
        _require(isinstance(control_id, str) and bool(control_id) and control_id not in seen, f"control {index} identity is invalid")
        _require(value["kind"] in CONTROL_KINDS, f"control {index} kind is invalid")
        effect = _effect(value["effect"], f"control {index} effect")
        unsigned = {"control_id": control_id, "effect": effect, "kind": value["kind"]}
        observation_digest = _digest(unsigned)
        if "observation_digest" in value:
            _require(value["observation_digest"] == observation_digest, f"control {index} digest mismatch")
        normalized.append({**unsigned, "observation_digest": observation_digest})
        seen.add(control_id)
    return normalized


def _replay(value: Mapping[str, Any]) -> dict[str, Any]:
    _require(isinstance(value, Mapping), "replay metadata must be an object")
    _require(set(value) in ({"input_digest", "replay_index", "replay_seed", "runner_identity"}, {"input_digest", "replay_digest", "replay_index", "replay_seed", "runner_identity", "schema"}), "replay schema is not closed")
    unsigned = {
        "input_digest": _require_digest(value["input_digest"], "replay input"),
        "replay_index": _require_int(value["replay_index"], "replay index", minimum=0),
        "replay_seed": _require_int(value["replay_seed"], "replay seed", minimum=0),
        "runner_identity": value["runner_identity"],
        "schema": REPLAY_SCHEMA,
    }
    _require(isinstance(unsigned["runner_identity"], str) and bool(unsigned["runner_identity"]), "replay runner identity is invalid")
    normalized = {**unsigned, "replay_digest": _digest(unsigned)}
    if "replay_digest" in value:
        _require(value["replay_digest"] == normalized["replay_digest"], "replay digest mismatch")
    return normalized


def create_record(
    *,
    parent_activation_action_digest: str,
    donor: Mapping[str, Any],
    target: Mapping[str, Any],
    operator: Mapping[str, Any],
    effect: Mapping[str, Any],
    controls: Sequence[Mapping[str, Any]],
    host_parameter_digest_before: str,
    host_parameter_digest_after: str,
    replay: Mapping[str, Any],
    nano_identity: str,
    timestamp: str,
    proof_status: str,
) -> dict[str, Any]:
    """Normalize one unreviewed intervention observation record."""

    parent = _require_digest(parent_activation_action_digest, "parent activation action")
    donor_value = _endpoint(donor, "donor")
    target_value = _endpoint(target, "target")
    _require(donor_value["site"] == SITE and target_value["site"] == SITE, "endpoint site is invalid")
    operator_value = _operator(operator, donor_value, target_value)
    effect_value = _effect(effect, "effect")
    controls_value = _controls(controls)
    parameter_before = _require_digest(host_parameter_digest_before, "host parameter before")
    parameter_after = _require_digest(host_parameter_digest_after, "host parameter after")
    _require(parameter_before == parameter_after, "host parameter digest changed")
    replay_value = _replay(replay)
    _require(isinstance(nano_identity, str) and bool(nano_identity), "nano identity is invalid")
    _require(isinstance(timestamp, str) and bool(timestamp), "timestamp is invalid")
    _require(proof_status in {"checked", "failed"}, "proof status is invalid")
    controls_digest = _digest(controls_value)
    claim = {
        "claim_key": f"{parent}:{target_value['checkpoint_digest']}:{target_value['layer']}:{target_value['site']}:{target_value['token_position']}:{operator_value['operator_digest']}",
        "controls_digest": controls_digest,
        "effect_digest": effect_value["effect_digest"],
        "host_parameter_digest_after": parameter_after,
        "host_parameter_digest_before": parameter_before,
        "kind": "observation_record",
        "operator_digest": operator_value["operator_digest"],
        "parent_activation_action_digest": parent,
        "semantics": CLAIM_SEMANTICS,
        "target_activation_digest": target_value["activation_digest"],
        "type": CLAIM_TYPE,
    }
    unsigned = {
        "assessment_status": ASSESSMENT_STATUS,
        "claim": claim,
        "controls": controls_value,
        "donor": donor_value,
        "effect": effect_value,
        "host_parameter_digest_after": parameter_after,
        "host_parameter_digest_before": parameter_before,
        "intervention_operator": operator_value,
        "nano_identity": nano_identity,
        "parent_activation_action_digest": parent,
        "proof_status": proof_status,
        "protocol_identity": PROTOCOL_ID,
        "record_schema": RECORD_SCHEMA,
        "record_status": RECORD_STATUS,
        "replay": replay_value,
        "state_slice": STATE_SLICE,
        "target": target_value,
        "timestamp": timestamp,
    }
    return {**unsigned, "record_digest": _digest(unsigned)}


def validate_record(record: Mapping[str, Any]) -> dict[str, Any]:
    """Reconstruct and compare a closed record without executing an intervention."""

    _require(isinstance(record, Mapping), "causal intervention record must be an object")
    expected_keys = {
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
    _require(set(record) == expected_keys, "causal intervention record schema is not closed")
    expected = create_record(
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
    _require(record == expected, "causal intervention record identity or digest mismatch")
    return expected
