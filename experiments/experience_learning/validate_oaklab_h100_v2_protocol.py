#!/usr/bin/env python3
"""Validate the Oak Lab H100 V2 closed-world protocol packet.

State slice: oaklab-experience-learning-h100-replication-v2.
"""

from __future__ import annotations

import sys

if __package__ in {None, ""} and sys.path:
    sys.path.pop(0)

import hashlib
import json
from pathlib import Path
from typing import Any


STATE_SLICE = "oaklab-experience-learning-h100-replication-v2"
PROTOCOL = Path("docs/research/experience-learning/43-oaklab-h100-replication-v2-protocol.md")
PACKET = Path("docs/research/experience-learning/44-oaklab-h100-replication-v2-review-packet.md")
SPEC = Path("experiments/experience_learning/oaklab_h100_v2_protocol.json")
COMPILED = Path("experiments/experience_learning/oaklab_h100_v2_compiled_protocol.json")
REVIEWED_FILES = (
    str(PROTOCOL), str(PACKET), str(SPEC),
    "experiments/experience_learning/compile_oaklab_h100_v2_protocol.py",
    "experiments/experience_learning/validate_oaklab_h100_v2_protocol.py",
    "experiments/experience_learning/tests/test_oaklab_h100_v2_protocol.py",
    str(COMPILED), "AGENTS.md",
)


def canonical(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def digest(value: dict[str, Any], field: str) -> str:
    return hashlib.sha256(canonical({k: v for k, v in value.items() if k != field})).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"missing or symlinked file: {path}")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"object required: {path}")
    return value


def validate_compiled(repo_root: Path = Path.cwd()) -> dict[str, Any]:
    value = load_json(repo_root / COMPILED)
    required = {
        "schema", "state_slice", "protocol_version", "source_protocol_sha256",
        "review_packet_sha256", "agents_sha256", "hash_prng_transcript",
        "controller_transition_table", "generator_roster_and_draw_order",
        "numeric_operations_and_byte_layouts", "ablation_and_multiplicity_tables",
        "segment_bounded_adaptation_metrics", "canonical_lock_counter_control_absence_schemas",
        "provider_receipt_schema", "result_root_schema", "compiled_sha256",
    }
    if set(value) != required:
        raise ValueError("compiled protocol schema is not closed")
    if value["schema"] != "oaklab-h100-replication-v2-compiled" or value["state_slice"] != STATE_SLICE:
        raise ValueError("compiled protocol identity mismatch")
    if value["source_protocol_sha256"] != sha256_file(repo_root / PROTOCOL):
        raise ValueError("protocol digest mismatch")
    if value["review_packet_sha256"] != sha256_file(repo_root / PACKET):
        raise ValueError("review packet digest mismatch")
    if value["agents_sha256"] != sha256_file(repo_root / "AGENTS.md"):
        raise ValueError("AGENTS digest mismatch")
    transitions = value["controller_transition_table"]
    if not isinstance(transitions, list) or len(transitions) != 6:
        raise ValueError("controller transition table is incomplete")
    for row in transitions:
        if set(row) != {"state", "input", "next", "action", "pending"} or not isinstance(row["pending"], dict):
            raise ValueError("controller transition row is not closed")
    provider = value["provider_receipt_schema"]
    if provider != {
        "required": ["allocation_id", "node_id", "start_utc", "stop_utc", "quoted_gpu_usd_per_minute", "charged_usd", "stop_reason", "raw_trace_sha256", "launch_manifest_sha256"],
        "currency": "USD",
        "charged_must_not_exceed_hard_ceiling": True,
    }:
        raise ValueError("provider receipt schema mismatch")
    root = value["result_root_schema"]
    if root.get("mode") != "closed_world" or root.get("reject_symlinks") is not True or root.get("reject_unlisted_paths") is not True:
        raise ValueError("result root is not closed-world")
    if not isinstance(root.get("allowed_paths"), list) or len(root["allowed_paths"]) != 8 or len(set(root["allowed_paths"])) != 8:
        raise ValueError("result root allowlist is invalid")
    if value["compiled_sha256"] != digest(value, "compiled_sha256"):
        raise ValueError("compiled self-digest mismatch")
    return value


def validate_result_root(root: Path, compiled: dict[str, Any]) -> None:
    allowed = {Path(item) for item in compiled["result_root_schema"]["allowed_paths"]}
    observed: set[Path] = set()
    if not root.is_dir() or root.is_symlink():
        raise ValueError("result root must be a regular directory")
    for path in root.rglob("*"):
        if path == root:
            continue
        relative = path.relative_to(root)
        if path.is_symlink():
            raise ValueError(f"symlink in result root: {relative}")
        if not path.is_file():
            if not any(candidate.parts[: len(relative.parts)] == relative.parts for candidate in allowed):
                raise ValueError(f"unlisted directory in result root: {relative}")
            continue
        observed.add(relative)
    if observed != allowed:
        raise ValueError(f"result root file set mismatch: observed={sorted(map(str, observed))}")


def validate_provider_receipt(receipt: dict[str, Any], hard_usd_ceiling: float) -> None:
    required = {"allocation_id", "node_id", "start_utc", "stop_utc", "quoted_gpu_usd_per_minute", "charged_usd", "stop_reason", "raw_trace_sha256", "launch_manifest_sha256"}
    if set(receipt) != required:
        raise ValueError("provider receipt schema is not closed")
    if not receipt["allocation_id"] or not receipt["node_id"] or not receipt["stop_reason"]:
        raise ValueError("provider receipt identity is missing")
    for field in ("quoted_gpu_usd_per_minute", "charged_usd"):
        if isinstance(receipt[field], bool) or not isinstance(receipt[field], (int, float)) or receipt[field] < 0:
            raise ValueError(f"invalid provider amount: {field}")
    if receipt["charged_usd"] > hard_usd_ceiling:
        raise ValueError("provider charge exceeds hard USD ceiling")
    for field in ("raw_trace_sha256", "launch_manifest_sha256"):
        value = receipt[field]
        if not isinstance(value, str) or len(value) != 64:
            raise ValueError(f"invalid provider digest: {field}")


def validate_packet(repo_root: Path = Path.cwd()) -> dict[str, Any]:
    packet_text = (repo_root / PACKET).read_text(encoding="utf-8")
    for path in REVIEWED_FILES:
        file_path = repo_root / path
        if file_path.is_symlink() or not file_path.is_file():
            raise ValueError(f"review file missing: {path}")
    if "44-oaklab-h100-replication-v2-review-packet.md" not in packet_text:
        raise ValueError("packet self-reference missing")
    compiled = validate_compiled(repo_root)
    return {"valid": True, "state_slice": STATE_SLICE, "reviewed_files": list(REVIEWED_FILES), "compiled_sha256": sha256_file(repo_root / COMPILED), "compiled_self_digest": compiled["compiled_sha256"]}


if __name__ == "__main__":
    print(json.dumps(validate_packet(), sort_keys=True))
