"""Independent, aggregate-only result validator.

The validator intentionally recomputes the result digest and checks accounting
invariants without importing the benchmark runner's implementation.
"""

from __future__ import annotations

import hashlib
import json
import sys

STATE_SLICE = "oaklab-experience-learning-baselines-v1"
SCHEMA_VERSION = "oaklab.experience-learning.result.v1"
EXPECTED_ALGORITHMS = {
    "sgd_b1", "sgd_b32", "sgd_b128", "adam_b1", "adam_b32", "adam_b128",
    "idbd", "networkidbd", "tidbd", "replay_sgd", "ewc_sgd",
    "plasticity_guard", "event_driven",
}


def _canonical_for_digest(value):
    if isinstance(value, dict):
        return {key: _canonical_for_digest(item) for key, item in value.items()
                if key not in {"result_digest", "wall_clock_latency_ns"}}
    if isinstance(value, list): return [_canonical_for_digest(item) for item in value]
    return value


def _digest(payload: dict) -> str:
    return hashlib.sha256(json.dumps(_canonical_for_digest(payload), sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def validate_result(result: dict) -> list[str]:
    findings: list[str] = []
    if result.get("schema_version") != SCHEMA_VERSION: findings.append("schema_version mismatch")
    if result.get("state_slice") != STATE_SLICE: findings.append("state_slice mismatch")
    if result.get("result_digest") != _digest(result): findings.append("result_digest mismatch")
    streams = result.get("streams")
    if not isinstance(streams, dict) or not streams: findings.append("streams missing")
    for stream_name, stream in (streams or {}).items():
        n = stream.get("n_experiences", 0)
        ranges = stream.get("split_ranges", {})
        if not (ranges.get("fit") and ranges.get("tune") and ranges.get("assessment")):
            findings.append(f"{stream_name}: split ranges missing")
        algorithms = stream.get("algorithms", {})
        for algorithm, record in algorithms.items():
            if algorithm not in EXPECTED_ALGORITHMS: findings.append(f"{stream_name}/{algorithm}: unknown algorithm")
            if record.get("status") == "not_applicable":
                if algorithm != "tidbd" or stream_name == "delayed_reward":
                    findings.append(f"{stream_name}/{algorithm}: invalid not_applicable status")
                continue
            if record.get("status") != "executed": findings.append(f"{stream_name}/{algorithm}: status missing")
            accounting = record.get("accounting", {})
            if accounting.get("presented_experiences") != n: findings.append(f"{stream_name}/{algorithm}: presented count mismatch")
            if accounting.get("learner_observe_calls") != n: findings.append(f"{stream_name}/{algorithm}: observe count mismatch")
            if accounting.get("max_experience_items_per_observe") != 1: findings.append(f"{stream_name}/{algorithm}: batch-one invariant failed")
            if accounting.get("hidden_gradient_accumulation") is not False: findings.append(f"{stream_name}/{algorithm}: hidden accumulation flag")
            if accounting.get("strict_batch_one") and (accounting.get("batch_size") != 1 or accounting.get("explicit_replay")):
                findings.append(f"{stream_name}/{algorithm}: strict batch-one arm has replay or wrong batch")
            if accounting.get("event_driven") and algorithm != "event_driven": findings.append(f"{stream_name}/{algorithm}: event flag mismatch")
            if not isinstance(record.get("final_state_digest"), str) or len(record["final_state_digest"]) != 64:
                findings.append(f"{stream_name}/{algorithm}: final digest missing")
            snapshots = record.get("state_snapshot_digests", {})
            for split in ("fit", "tune", "assessment"):
                digest = snapshots.get(split)
                if not isinstance(digest, str) or len(digest) != 64:
                    findings.append(f"{stream_name}/{algorithm}: {split} state snapshot missing")
            for split, summary in record.get("summaries", {}).items():
                for field in ("cumulative_prediction_loss", "mean_prediction_loss", "updates", "samples", "model_bytes", "state_bytes"):
                    value = summary.get(field)
                    if not isinstance(value, (int, float)) or value < 0 or value != value:
                        findings.append(f"{stream_name}/{algorithm}/{split}: invalid {field}")
    return findings


def validate_file(path: str) -> list[str]:
    with open(path, encoding="utf-8") as handle:
        return validate_result(json.load(handle))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: python -m experiments.experience_learning.validate RESULT.json")
    errors = validate_file(sys.argv[1])
    if errors:
        for error in errors: print(error)
        raise SystemExit(1)
    print("VALID")
