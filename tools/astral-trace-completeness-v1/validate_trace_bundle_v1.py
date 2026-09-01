"""Independent aggregate-only validator for trace completeness V1.

State slice: astral-trace-completeness-native-instrument-v1.

This validator accepts only the public aggregate envelope.  It never reads or
reconstructs raw event payloads and rejects raw/sensitive field names.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Sequence

import protocol


ALLOWED_AGGREGATE_KEYS = {
    "protocol",
    "state_slice",
    "run_id",
    "event_count",
    "event_counts",
    "expected_event_counts",
    "event_expectation_sha256",
    "module_registry",
    "module_registry_sha256",
    "event_manifest_sha256",
    "token_count",
    "layer_count",
    "module_count",
    "event_stream_sha256",
    "raw_events_retained",
    "aggregate_only",
    "missing_event_count",
    "duplicate_event_count",
    "unaccounted_state_transition_count",
    "output_count",
}


def _walk_keys(value: Any) -> list[str]:
    if isinstance(value, dict):
        return [str(key).lower() for key in value for _ in (0,)] + [child for item in value.values() for child in _walk_keys(item)]
    if isinstance(value, list):
        return [child for item in value for child in _walk_keys(item)]
    return []


ALLOWED_EVENT_MANIFEST_KEYS = {
    "protocol",
    "state_slice",
    "raw_trace_relative_path",
    "raw_trace_sha256",
    "event_count",
    "event_counts",
    "expected_event_counts",
    "event_expectation_sha256",
    "module_registry",
    "module_registry_sha256",
    "event_stream_sha256",
    "manifest_sha256",
}


def _expectation_from_manifest(event_manifest: dict[str, Any]) -> protocol.EventExpectation:
    expected = event_manifest["expected_event_counts"]
    registry = tuple((int(item[0]), str(item[1])) for item in event_manifest["module_registry"])
    return protocol.EventExpectation(
        token_count=int(expected["token"]),
        layer_count=int(expected["layer_enter"]),
        module_count=int(expected["module_enter"]),
        cache_read_count=int(expected["cache_read"]),
        cache_write_count=int(expected["cache_write"]),
        state_transition_count=int(expected["state_transition"]),
        intervention_count=int(expected["intervention"]),
        output_count=int(expected["output"]),
        expected_module_paths=registry,
    )


def validate_aggregate(
    value: Any,
    event_manifest: Any | None = None,
    events: Sequence[protocol.TraceEvent] | None = None,
) -> dict[str, Any]:
    errors: list[str] = []
    if not isinstance(value, dict):
        errors.append("aggregate_not_object")
    else:
        if set(value) != ALLOWED_AGGREGATE_KEYS:
            errors.append("aggregate_schema")
        if value.get("protocol") != protocol.PROTOCOL_ID:
            errors.append("protocol_identity")
        if value.get("state_slice") != protocol.STATE_SLICE:
            errors.append("state_slice_identity")
        if value.get("raw_events_retained") is not False or value.get("aggregate_only") is not True:
            errors.append("retention_policy")
        if value.get("missing_event_count") != 0:
            errors.append("missing_events")
        if value.get("duplicate_event_count") != 0:
            errors.append("duplicate_events")
        if value.get("unaccounted_state_transition_count") != 0:
            errors.append("unaccounted_state_transitions")
        if value.get("output_count") != 1:
            errors.append("output_count")
        try:
            protocol._validate_digest(value["event_stream_sha256"], "event_stream_sha256")
        except (KeyError, protocol.ProtocolError):
            errors.append("event_stream_digest")
        if isinstance(value.get("event_counts"), dict):
            if set(value["event_counts"]) != set(protocol.EVENT_KINDS):
                errors.append("event_kind_census_schema")
            elif any(not isinstance(item, int) or item < 0 for item in value["event_counts"].values()):
                errors.append("event_kind_census_values")
        else:
            errors.append("event_kind_census_type")
        if isinstance(value.get("expected_event_counts"), dict):
            if value.get("event_counts") != value.get("expected_event_counts"):
                errors.append("event_kind_census_mismatch")
            elif value.get("event_count") != sum(value["expected_event_counts"].values()):
                errors.append("event_count_sum_mismatch")
        else:
            errors.append("expected_event_kind_census_type")
        try:
            protocol._validate_digest(value["event_expectation_sha256"], "event_expectation_sha256")
            protocol._validate_digest(value["module_registry_sha256"], "module_registry_sha256")
            protocol._validate_digest(value["event_manifest_sha256"], "event_manifest_sha256")
        except (KeyError, protocol.ProtocolError):
            errors.append("expectation_digest")
        if isinstance(value.get("module_registry"), list):
            expected_counts = value.get("expected_event_counts")
            expected_digest = protocol.canonical_digest(
                {"counts": expected_counts, "expected_module_paths": value["module_registry"]}
            ) if isinstance(expected_counts, dict) else None
            registry_digest = protocol.canonical_digest(value["module_registry"])
            if value.get("event_expectation_sha256") != expected_digest:
                errors.append("event_expectation_digest_mismatch")
            if value.get("module_registry_sha256") != registry_digest:
                errors.append("module_registry_digest_mismatch")
        else:
            errors.append("module_registry_type")
        if not isinstance(event_manifest, dict):
            errors.append("event_manifest_required")
        else:
            if set(event_manifest) != ALLOWED_EVENT_MANIFEST_KEYS:
                errors.append("event_manifest_schema")
            if event_manifest.get("protocol") != protocol.PROTOCOL_ID or event_manifest.get("state_slice") != protocol.STATE_SLICE:
                errors.append("event_manifest_identity")
            raw_relative = Path(str(event_manifest.get("raw_trace_relative_path", "")))
            if raw_relative.is_absolute() or raw_relative.parts[:1] != ("raw",) or ".." in raw_relative.parts:
                errors.append("event_manifest_raw_path")
            manifest_without_digest = dict(event_manifest)
            manifest_without_digest.pop("manifest_sha256", None)
            if event_manifest.get("manifest_sha256") != protocol.canonical_digest(manifest_without_digest):
                errors.append("event_manifest_digest")
            if value.get("event_manifest_sha256") != event_manifest.get("manifest_sha256"):
                errors.append("event_manifest_binding")
            for key in ("raw_trace_sha256", "event_stream_sha256"):
                try:
                    protocol._validate_digest(event_manifest[key], key)
                except (KeyError, protocol.ProtocolError):
                    errors.append(f"event_manifest_{key}")
            for key in ("event_count", "event_counts", "expected_event_counts", "event_expectation_sha256", "module_registry", "module_registry_sha256"):
                if key in event_manifest and value.get(key) != event_manifest[key]:
                    errors.append(f"event_manifest_{key}_binding")
        if events is None:
            errors.append("raw_event_stream_required")
        elif isinstance(event_manifest, dict):
            try:
                recomputed = protocol.validate_event_stream(
                    events,
                    _expectation_from_manifest(event_manifest),
                    event_manifest_sha256=event_manifest.get("manifest_sha256"),
                )
                for key in ALLOWED_AGGREGATE_KEYS - {"event_manifest_sha256"}:
                    if value.get(key) != recomputed.get(key):
                        errors.append(f"recomputed_{key}_mismatch")
            except (KeyError, TypeError, ValueError, protocol.ProtocolError) as exc:
                errors.append(f"raw_event_validation:{type(exc).__name__}:{exc}")
        for key in _walk_keys(value):
            if key in protocol.RAW_FIELD_MARKERS or (key.startswith("raw_") and key != "raw_events_retained") or key.endswith("_payload"):
                errors.append(f"raw_field:{key}")
    return {
        "protocol": protocol.PROTOCOL_ID,
        "state_slice": protocol.STATE_SLICE,
        "claim_ceiling": protocol.CLAIM_CEILING,
        "valid": not errors,
        "classification": "AggregateOnlyValidated" if not errors else "AggregateOnlyInvalid",
        "errors": sorted(set(errors)),
    }


def validate_aggregate_file(path: Path, repository_root: Path, event_manifest_path: Path | None = None) -> dict[str, Any]:
    path = path.resolve()
    repository_root = repository_root.resolve()
    try:
        protocol.assert_external(path, repository_root)
        value = protocol.strict_json(path)
        if event_manifest_path is not None:
            protocol.assert_external(event_manifest_path.resolve(), repository_root)
        event_manifest = protocol.strict_json(event_manifest_path.resolve()) if event_manifest_path is not None else None
        events: list[protocol.TraceEvent] | None = None
        if event_manifest_path is not None and isinstance(event_manifest, dict):
            custody_root = event_manifest_path.resolve().parent.parent
            raw_path = custody_root / str(event_manifest.get("raw_trace_relative_path", ""))
            if raw_path.is_file() and not raw_path.is_symlink():
                if protocol.sha256_file(raw_path) != event_manifest.get("raw_trace_sha256"):
                    events = []
                else:
                    events = []
                    for line in raw_path.read_text(encoding="utf-8").splitlines():
                        if line.strip():
                            decoded = json.loads(line)
                            if not isinstance(decoded, dict):
                                raise protocol.ProtocolError("raw event line is not an object")
                            events.append(protocol.TraceEvent.from_dict(decoded))
        receipt = validate_aggregate(value, event_manifest, events)
        if event_manifest_path is not None and isinstance(event_manifest, dict):
            custody_root = event_manifest_path.resolve().parent.parent
            raw_path = custody_root / str(event_manifest.get("raw_trace_relative_path", ""))
            if not raw_path.is_file() or raw_path.is_symlink():
                receipt["errors"].append("raw_trace_missing_or_symlink")
            elif protocol.sha256_file(raw_path) != event_manifest.get("raw_trace_sha256"):
                receipt["errors"].append("raw_trace_digest_mismatch")
            receipt["errors"] = sorted(set(receipt["errors"]))
            receipt["valid"] = not receipt["errors"]
            receipt["classification"] = "AggregateOnlyValidated" if receipt["valid"] else "AggregateOnlyInvalid"
        receipt["aggregate_sha256"] = protocol.sha256_file(path)
        receipt["aggregate_path"] = str(path)
        return receipt
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, protocol.ProtocolError) as exc:
        return {
            "protocol": protocol.PROTOCOL_ID,
            "state_slice": protocol.STATE_SLICE,
            "claim_ceiling": protocol.CLAIM_CEILING,
            "valid": False,
            "classification": "AggregateOnlyInvalid",
            "errors": [f"validator_error:{type(exc).__name__}:{exc}"],
        }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("aggregate", type=Path)
    parser.add_argument("--event-manifest", type=Path)
    parser.add_argument("--repository-root", type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args(argv)
    receipt = validate_aggregate_file(args.aggregate, args.repository_root, args.event_manifest)
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0 if receipt["valid"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
