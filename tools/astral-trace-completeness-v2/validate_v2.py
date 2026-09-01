"""Independent aggregate-only validator for V2 raw event manifests.

State slice: astral-trace-completeness-gemma3-end-to-end-v2.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import custody_v2 as custody
import protocol_v2 as protocol
import registry_v2 as registry


def _no_duplicate_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise protocol.ProtocolError(f"duplicate JSON key: {key}")
        value[key] = item
    return value


def _strict_line(line: str) -> Any:
    return json.loads(line, object_pairs_hook=_no_duplicate_pairs, parse_constant=lambda item: (_ for _ in ()).throw(protocol.ProtocolError(f"nonstandard JSON constant: {item}")))


def validate_run(
    aggregate: dict[str, Any],
    manifest: dict[str, Any],
    *,
    custody_root: Path,
    repository_root: Path,
) -> dict[str, Any]:
    errors = []
    custody_receipt = custody.validate_root(custody_root, repository_root)
    if not custody_receipt["valid"]:
        errors.append("custody")
    expected_manifest = {key: value for key, value in manifest.items() if key != "manifest_sha256"}
    if manifest.get("manifest_sha256") != protocol.digest_json(expected_manifest):
        errors.append("manifest_digest")
    try:
        raw_path = (custody_root / str(manifest["raw_relative_path"])).resolve()
        raw_path.relative_to((custody_root / "raw").resolve())
        if raw_path.is_symlink() or not raw_path.is_file():
            raise protocol.ProtocolError("raw event path invalid")
        if protocol.sha256_file(raw_path) != manifest.get("raw_sha256"):
            raise protocol.ProtocolError("raw event hash mismatch")
        events = [protocol.TraceEvent.from_dict(_strict_line(line)) for line in raw_path.read_text(encoding="utf-8").splitlines() if line]
        expectation = protocol.RunExpectation(
            generation_steps=int(aggregate["generation_steps"]),
            input_token_count=int(aggregate["input_token_count"]),
            module_input_paths=registry.expected_input_paths(),
            module_output_paths=registry.expected_output_paths(),
            attention_modules=registry.attention_paths(),
            interventions=int(aggregate["event_counts"]["intervention"]),
            sae_feature_events=int(aggregate["event_counts"]["sae_features"]),
            sae_reconstruction_events=int(aggregate["event_counts"]["sae_reconstruction"]),
            graph_prediction_events=int(aggregate["event_counts"]["graph_prediction"]),
        )
        recomputed = protocol.validate_event_stream(events, expectation)
        if recomputed != aggregate:
            errors.append("aggregate_recomputation")
        if len(events) != manifest.get("event_count"):
            errors.append("manifest_event_count")
        if recomputed.get("event_stream_sha256") != manifest.get("event_stream_sha256"):
            errors.append("manifest_stream_digest")
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError, protocol.ProtocolError) as exc:
        errors.append(f"event_replay:{type(exc).__name__}:{exc}")
    lowered = " ".join(aggregate.keys()).lower()
    if any(fragment in lowered for fragment in protocol.RAW_FIELD_FRAGMENTS):
        errors.append("raw_aggregate_field")
    value = {
        "protocol": protocol.PROTOCOL_ID,
        "state_slice": protocol.STATE_SLICE,
        "run_id": aggregate.get("run_id"),
        "valid": not errors,
        "errors": errors,
        "aggregate_sha256": protocol.digest_json(aggregate),
        "manifest_sha256": manifest.get("manifest_sha256"),
        "validator": "validate_v2.validate_run",
    }
    return {**value, "receipt_sha256": protocol.digest_json(value)}

