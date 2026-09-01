#!/usr/bin/env python3
"""Independently validate the V41 qualification receipt.

State slice: astral-stage0c-qwen36-directional-block-target-v41.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import protocol_v41 as protocol


def validate(qualification_root: Path, model_root: Path, repository_root: Path) -> dict[str, Any]:
    errors: list[str] = []
    qualification_root = qualification_root.resolve()
    model_root = model_root.resolve()
    try:
        protocol.assert_external(qualification_root, repository_root)
        protocol.assert_external(model_root, repository_root)
        result_path = qualification_root / "qualification-result.json"
        result = protocol.read_json(result_path)
        manifest = protocol.model_manifest(model_root)
        if result.get("protocol") != protocol.PROTOCOL_ID or result.get("state_slice") != protocol.STATE_SLICE:
            errors.append("protocol_or_state_slice_mismatch")
        if result.get("model_root_basename") != protocol.MODEL_BASENAME:
            errors.append("model_basename_mismatch")
        if result.get("model_manifest_sha256") != manifest.get("manifest_sha256"):
            errors.append("model_manifest_mismatch")
        if result.get("protocol_source_sha256") != protocol.sha256_file(Path(protocol.__file__).resolve()):
            errors.append("protocol_source_mismatch")
        runner_path = Path(__file__).resolve().parent / "qualify_v41.py"
        if result.get("runner_source_sha256") != protocol.sha256_file(runner_path):
            errors.append("runner_source_mismatch")
        if result.get("qualification_prompt_sha256") != protocol.canonical_digest(list(protocol.QUALIFICATION_PROMPTS)):
            errors.append("prompt_digest_mismatch")
        if result.get("feature_map_sha256") != protocol.feature_map_digest():
            errors.append("feature_map_digest_mismatch")
        gates = result.get("gates")
        if not isinstance(gates, dict) or not all(value is True for value in gates.values()):
            errors.append("qualification_gate_failure")
        if result.get("assessment_opened") is not False:
            errors.append("assessment_opened")
        if result.get("observed_layer_count") != protocol.EXPECTED_LAYER_COUNT or result.get("observed_hidden_width") != protocol.EXPECTED_HIDDEN_WIDTH:
            errors.append("shape_summary_mismatch")
        expected_layers = {str(layer) for layer in protocol.QUALIFICATION_LAYERS}
        for key in ("zero_replacement_max_abs_logit_delta_by_layer", "nonzero_reach_max_abs_logit_delta_by_layer"):
            values = result.get(key)
            if not isinstance(values, dict) or set(values) != expected_layers:
                errors.append(f"{key}_shape_mismatch")
    except (OSError, json.JSONDecodeError, protocol.ProtocolError, KeyError, TypeError, AttributeError) as exc:
        errors.append(f"validator_error:{type(exc).__name__}:{exc}")
    return {
        "protocol": protocol.PROTOCOL_ID,
        "state_slice": protocol.STATE_SLICE,
        "claim_ceiling": "LocalDevelopmentV41InstrumentFeasibilityOnly",
        "classification": "InstrumentFeasibility" if not errors else "InstrumentQualificationInvalid",
        "valid": not errors,
        "errors": errors,
        "qualification_result_sha256": protocol.sha256_file(qualification_root / "qualification-result.json") if (qualification_root / "qualification-result.json").is_file() else None,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("qualification_root", type=Path)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--repository-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--write-receipt", action="store_true")
    args = parser.parse_args(argv)
    receipt = validate(args.qualification_root, args.model, args.repository_root)
    if args.write_receipt:
        protocol.write_json(args.qualification_root / "validator-receipt.json", receipt)
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0 if receipt["valid"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
