#!/usr/bin/env python3
"""Independently validate V48 qualification.

State slice: astral-stage0c-cross-view-causal-state-transport-v48.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import protocol_v48 as protocol


REQUIRED_GATES = (
    "native_parity", "deterministic_repeat", "noop_replacement",
    "zero_replacement_reached", "nonzero_reach", "capture_shape",
    "replacement_shape", "model_architecture", "runtime_exact",
    "model_source_custody", "no_network_access", "no_model_training",
    "no_raw_intermediates_retained",
)


def validate(qualification_root: Path, model_root: Path, repository_root: Path) -> dict[str, Any]:
    errors: list[str] = []
    qualification_root = qualification_root.resolve()
    model_root = model_root.resolve()
    repository_root = repository_root.resolve()
    try:
        protocol.assert_external(qualification_root, repository_root)
        protocol.assert_external(model_root, repository_root)
        result = protocol.read_json(qualification_root / "qualification-result.json")
    except (OSError, ValueError, json.JSONDecodeError, KeyError) as exc:
        return {"valid": False, "errors": [f"load:{type(exc).__name__}:{exc}"], "state_slice": protocol.STATE_SLICE}
    if result.get("protocol") != protocol.PROTOCOL_ID:
        errors.append("protocol_identity")
    if result.get("state_slice") != protocol.STATE_SLICE:
        errors.append("state_slice_identity")
    if result.get("qualification_id") != protocol.QUALIFICATION_ID:
        errors.append("qualification_identity")
    if result.get("model_root_basename") != protocol.MODEL_BASENAME:
        errors.append("model_identity")
    if result.get("source_layer") != protocol.SOURCE_LAYER or result.get("destination_layer") != protocol.DESTINATION_LAYER:
        errors.append("operator_layers")
    if result.get("alpha") != protocol.ALPHA or result.get("additional_passes") != protocol.ADDITIONAL_PASSES:
        errors.append("operator_parameters")
    if result.get("position_name") != protocol.POSITION_NAME or result.get("position_rule") != protocol.POSITION_RULE:
        errors.append("position_identity")
    if result.get("observed_layer_count") != protocol.EXPECTED_LAYER_COUNT:
        errors.append("layer_count")
    if result.get("observed_hidden_width") != protocol.EXPECTED_HIDDEN_WIDTH:
        errors.append("hidden_width")
    if result.get("assessment_opened") is not False:
        errors.append("assessment_opened")
    try:
        model_manifest = protocol.model_manifest(model_root)
        if result.get("model_manifest_sha256") != model_manifest["manifest_sha256"]:
            errors.append("model_manifest_digest")
        if result.get("config_sha256") != protocol.sha256_file(model_root / "config.json"):
            errors.append("config_digest")
    except (OSError, ValueError, protocol.ProtocolError) as exc:
        errors.append(f"model_custody:{type(exc).__name__}:{exc}")
    gates = result.get("gates")
    if not isinstance(gates, dict):
        errors.append("gate_map")
        gates = {}
    for gate in REQUIRED_GATES:
        if gates.get(gate) is not True:
            errors.append(f"gate_failed:{gate}")
    numeric_checks = {
        "native_parity_max_abs_logit_delta": 1e-4,
        "deterministic_repeat_max_abs_logit_delta": 1e-5,
        "noop_replacement_max_abs_logit_delta": 1e-5,
    }
    for field, bound in numeric_checks.items():
        value = result.get(field)
        if not isinstance(value, (int, float)) or value > bound:
            errors.append(f"numeric_bound:{field}")
    receipt = {
        "protocol": protocol.PROTOCOL_ID,
        "state_slice": protocol.STATE_SLICE,
        "qualification_id": protocol.QUALIFICATION_ID,
        "qualification_result_sha256": protocol.sha256_file(qualification_root / "qualification-result.json"),
        "valid": not errors,
        "errors": errors,
        "classification": "QualificationValidated" if not errors else "QualificationInvalid",
        "claim_ceiling": "LocalDevelopmentV48QualificationValidated" if not errors else "LocalDevelopmentV48QualificationValidationFailed",
        "assessment_opened": False,
    }
    return receipt


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("qualification_root", type=Path)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--repository-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--write-receipt", action="store_true")
    args = parser.parse_args(argv)
    receipt = validate(args.qualification_root, args.model, args.repository_root)
    if args.write_receipt:
        protocol.write_json(args.qualification_root.resolve() / "validator-receipt.json", receipt)
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0 if receipt["valid"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
