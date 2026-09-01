"""State slice: astral-trace-completeness-native-instrument-v1."""

import json
import sys
from contextlib import contextmanager
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import protocol
import native_adapter
import validate_trace_bundle_v1 as validator


def _complete_run():
    expectation = protocol.EventExpectation(
        1,
        1,
        1,
        0,
        0,
        0,
        0,
        expected_module_paths=((0, "module"),),
    )
    adapter = native_adapter.NativeModelAdapter(expectation, run_id_factory=lambda: "validator-run")

    def forward(hooks, tokens):
        digest = native_adapter.digest_value([1])
        with hooks.layer(0, shape=(1, 1, 1), dtype="float32", value_digest=digest) as finish_layer:
            with hooks.module(0, "module", shape=(1, 1, 1), dtype="float32", value_digest=digest) as finish_module:
                finish_module(output_digest=digest, output_shape=(1, 1, 1), output_dtype="float32")
            finish_layer(output_digest=digest, output_shape=(1, 1, 1), output_dtype="float32")
        hooks.output(output_digest=digest, shape=(1, 1), dtype="float32")

    return adapter.execute([1], forward)


def _aggregate():
    value = {
        "protocol": protocol.PROTOCOL_ID,
        "state_slice": protocol.STATE_SLICE,
        "run_id": "fixture-run",
        "event_count": 10,
        "event_counts": {"run_start": 1, "token": 1, "layer_enter": 1, "layer_output": 1, "module_enter": 1, "module_output": 1, "cache_read": 0, "cache_write": 0, "state_transition": 0, "intervention": 0, "module_exit": 1, "layer_exit": 1, "output": 1, "run_end": 1},
        "expected_event_counts": {"run_start": 1, "token": 1, "layer_enter": 1, "layer_output": 1, "module_enter": 1, "module_output": 1, "cache_read": 0, "cache_write": 0, "state_transition": 0, "intervention": 0, "module_exit": 1, "layer_exit": 1, "output": 1, "run_end": 1},
        "module_registry": [],
        "event_expectation_sha256": protocol.canonical_digest({"counts": {"run_start": 1, "token": 1, "layer_enter": 1, "layer_output": 1, "module_enter": 1, "module_output": 1, "cache_read": 0, "cache_write": 0, "state_transition": 0, "intervention": 0, "module_exit": 1, "layer_exit": 1, "output": 1, "run_end": 1}, "expected_module_paths": []}),
        "module_registry_sha256": protocol.canonical_digest([]),
        "token_count": 1,
        "layer_count": 1,
        "module_count": 1,
        "event_stream_sha256": "0" * 64,
        "raw_events_retained": False,
        "aggregate_only": True,
        "missing_event_count": 0,
        "duplicate_event_count": 0,
        "unaccounted_state_transition_count": 0,
        "output_count": 1,
    }
    manifest = _manifest(value)
    value["event_manifest_sha256"] = manifest["manifest_sha256"]
    return value


def _manifest(value):
    manifest = {
        "protocol": protocol.PROTOCOL_ID,
        "state_slice": protocol.STATE_SLICE,
        "raw_trace_relative_path": "raw/fixture-events.jsonl",
        "raw_trace_sha256": "1" * 64,
        "event_count": value["event_count"],
        "event_counts": value["event_counts"],
        "expected_event_counts": value["expected_event_counts"],
        "event_expectation_sha256": value["event_expectation_sha256"],
        "module_registry": value["module_registry"],
        "module_registry_sha256": value["module_registry_sha256"],
        "event_stream_sha256": value["event_stream_sha256"],
    }
    manifest["manifest_sha256"] = protocol.canonical_digest(manifest)
    return manifest


def test_validator_accepts_aggregate_only_envelope():
    run = _complete_run()
    value = dict(run.aggregate)
    manifest = _manifest(value)
    value["event_manifest_sha256"] = manifest["manifest_sha256"]
    receipt = validator.validate_aggregate(value, manifest, run.events)
    assert receipt["valid"] is True


def test_validator_rejects_raw_fields_and_nonzero_missingness():
    value = _aggregate()
    value["missing_event_count"] = 1
    value["raw_activation"] = [1.0]
    receipt = validator.validate_aggregate(value, _manifest(value))
    assert receipt["valid"] is False
    assert "aggregate_schema" in receipt["errors"]
    assert "missing_events" in receipt["errors"]
    assert any(error.startswith("raw_field:") for error in receipt["errors"])


def test_validator_rejects_aggregate_without_external_event_manifest():
    receipt = validator.validate_aggregate(_aggregate())
    assert receipt["valid"] is False
    assert "event_manifest_required" in receipt["errors"]


def test_validator_binds_aggregate_to_external_raw_manifest(tmp_path):
    custody_root = tmp_path / "custody"
    raw_root = custody_root / "raw"
    aggregate_root = custody_root / "aggregate"
    raw_root.mkdir(parents=True)
    aggregate_root.mkdir()
    import os

    os.chmod(custody_root, 0o700)
    os.chmod(raw_root, 0o700)
    os.chmod(aggregate_root, 0o700)
    raw_path = raw_root / "fixture-events.jsonl"
    run = _complete_run()
    raw_path.write_text("\n".join(json.dumps(event.to_dict(), sort_keys=True) for event in run.events) + "\n", encoding="utf-8")
    value = dict(run.aggregate)
    manifest = _manifest(value)
    manifest["raw_trace_sha256"] = protocol.sha256_file(raw_path)
    manifest["manifest_sha256"] = protocol.canonical_digest({key: manifest[key] for key in manifest if key != "manifest_sha256"})
    value["event_manifest_sha256"] = manifest["manifest_sha256"]
    aggregate_path = aggregate_root / "aggregate.json"
    manifest_path = aggregate_root / "event-manifest.json"
    protocol.write_json(aggregate_path, value)
    protocol.write_json(manifest_path, manifest)
    receipt = validator.validate_aggregate_file(aggregate_path, ROOT, manifest_path)
    assert receipt["valid"] is True
