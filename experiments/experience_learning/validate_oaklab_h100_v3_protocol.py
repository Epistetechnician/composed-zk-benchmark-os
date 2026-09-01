#!/usr/bin/env python3
"""Validate the Oak Lab H100 V3 protocol and runtime receipt schemas.

State slice: oaklab-experience-learning-h100-replication-v3.
"""

from __future__ import annotations

import csv
import datetime as dt
import hashlib
import json
import math
import re
import sys
from pathlib import Path
from typing import Any

if __package__ in {None, ""} and sys.path:
    sys.path.pop(0)


STATE_SLICE = "oaklab-experience-learning-h100-replication-v3"
PROTOCOL = Path("docs/research/experience-learning/48-oaklab-h100-replication-v3-protocol.md")
PACKET = Path("docs/research/experience-learning/49-oaklab-h100-replication-v3-review-packet.md")
SPEC = Path("experiments/experience_learning/oaklab_h100_v3_protocol.json")
COMPILED = Path("experiments/experience_learning/oaklab_h100_v3_compiled_protocol.json")
REVIEWED_FILES = (
    str(PROTOCOL), str(PACKET), str(SPEC),
    "experiments/experience_learning/compile_oaklab_h100_v3_protocol.py",
    "experiments/experience_learning/validate_oaklab_h100_v3_protocol.py",
    "experiments/experience_learning/tests/test_oaklab_h100_v3_protocol.py",
    str(COMPILED), "AGENTS.md",
)
HEX64 = re.compile(r"^[0-9a-f]{64}$")
UTC_SECONDS = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$")


def canonical(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def digest(value: dict[str, Any], field: str) -> str:
    return sha256_bytes(canonical({key: item for key, item in value.items() if key != field}))


def load_json(path: Path) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"missing or symlinked file: {path}")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"object required: {path}")
    return value


def require_digest(value: Any, label: str) -> str:
    if not isinstance(value, str) or HEX64.fullmatch(value) is None:
        raise ValueError(f"{label} must be lowercase SHA-256 hex")
    return value


def validate_compiled(repo_root: Path = Path.cwd()) -> dict[str, Any]:
    value = load_json(repo_root / COMPILED)
    required = {
        "schema", "state_slice", "protocol_version", "freeze_file_sha256", "hash_prng",
        "paired_trajectory_estimand", "controller", "stream_roster", "statistics",
        "resource_energy", "campaign_manifest", "provider_receipt", "tune_lock",
        "result_root", "execution_boundary", "compiled_sha256",
    }
    if set(value) != required:
        raise ValueError("compiled schema is not closed")
    if value["schema"] != "oaklab-h100-replication-v3-compiled" or value["state_slice"] != STATE_SLICE:
        raise ValueError("compiled identity mismatch")
    freeze = value["freeze_file_sha256"]
    expected_freeze_paths = set(REVIEWED_FILES[:6] + REVIEWED_FILES[7:])
    if not isinstance(freeze, dict) or set(freeze) != expected_freeze_paths:
        raise ValueError("freeze file roster is not exact")
    for path, expected in freeze.items():
        require_digest(expected, f"freeze digest {path}")
        actual_path = repo_root / path
        if actual_path.is_symlink() or not actual_path.is_file() or sha256_file(actual_path) != expected:
            raise ValueError(f"freeze digest mismatch: {path}")
    pair = value["paired_trajectory_estimand"]
    if pair != {"unit": "episode", "control": "sgd_b1", "treatment": "lagged_selective_credit", "same_stream": True, "same_initial_checkpoint": True, "post_washout_blocks": 32, "items_per_block": 128, "formula": "mean_e mean_b(loss_treatment[e,b]-loss_control[e,b])", "arm_order_randomized": True}:
        raise ValueError("paired estimand is not exact")
    if value["statistics"].get("multiplicity") != "holm" or value["statistics"].get("planned_power") != 0.8:
        raise ValueError("statistics gate is not sealed")
    provider = value["provider_receipt"]
    if provider.get("signature_verification") != "independent_ed25519_verification" or provider.get("charged_leq_ceiling") is not True:
        raise ValueError("provider receipt signature or ceiling rule missing")
    if value["result_root"].get("mode") != "closed_world" or value["result_root"].get("reject_extra_paths") is not True or value["result_root"].get("validate_all_file_contents") is not True:
        raise ValueError("result root is not closed-world")
    if value["tune_lock"].get("independent_receipt_required") is not True or value["tune_lock"].get("assessment_forbidden_before_validation") is not True:
        raise ValueError("tune lock ordering is not sealed")
    if value["execution_boundary"].get("effects_run") is not False:
        raise ValueError("effects are not disabled")
    if value["compiled_sha256"] != digest(value, "compiled_sha256"):
        raise ValueError("compiled self-digest mismatch")
    return value


def validate_campaign_manifest(manifest: dict[str, Any], compiled_sha256: str) -> None:
    keys = {"schema", "state_slice", "compiled_protocol_sha256", "code_sha256", "model_sha256", "data_sha256", "backend_sha256", "guard_sha256", "tune_lock_sha256", "provider_receipt_sha256", "energy_receipt_sha256", "result_root_sha256", "hard_usd_ceiling", "manifest_sha256"}
    if set(manifest) != keys or manifest["schema"] != "oaklab-h100-v3-campaign" or manifest["state_slice"] != STATE_SLICE:
        raise ValueError("campaign manifest schema is not closed")
    if manifest["compiled_protocol_sha256"] != compiled_sha256:
        raise ValueError("campaign manifest does not bind compiled protocol")
    for key, value in manifest.items():
        if key.endswith("_sha256") and key != "manifest_sha256":
            require_digest(value, key)
    ceiling = manifest["hard_usd_ceiling"]
    if isinstance(ceiling, bool) or not isinstance(ceiling, (int, float)) or not math.isfinite(float(ceiling)) or ceiling <= 0:
        raise ValueError("hard USD ceiling is invalid")
    if manifest["manifest_sha256"] != digest(manifest, "manifest_sha256"):
        raise ValueError("campaign manifest self-digest mismatch")


def validate_provider_receipt(receipt: dict[str, Any], hard_usd_ceiling: float, launch_manifest_sha256: str) -> None:
    keys = {"schema", "state_slice", "allocation_id", "node_id", "start_utc", "stop_utc", "charged_usd", "hard_usd_ceiling", "launch_manifest_sha256", "raw_trace_sha256", "public_key_hex", "signature_hex", "receipt_sha256"}
    if set(receipt) != keys or receipt["schema"] != "oaklab-h100-v3-provider-receipt" or receipt["state_slice"] != STATE_SLICE:
        raise ValueError("provider receipt schema is not closed")
    for field in ("start_utc", "stop_utc"):
        if not isinstance(receipt[field], str) or UTC_SECONDS.fullmatch(receipt[field]) is None:
            raise ValueError(f"invalid provider timestamp: {field}")
        dt.datetime.strptime(receipt[field], "%Y-%m-%dT%H:%M:%SZ")
    if receipt["launch_manifest_sha256"] != launch_manifest_sha256:
        raise ValueError("provider receipt launch binding mismatch")
    for field in ("charged_usd", "hard_usd_ceiling"):
        if isinstance(receipt[field], bool) or not isinstance(receipt[field], (int, float)) or not math.isfinite(float(receipt[field])) or receipt[field] < 0:
            raise ValueError(f"invalid provider amount: {field}")
    if receipt["hard_usd_ceiling"] != hard_usd_ceiling or receipt["charged_usd"] > hard_usd_ceiling:
        raise ValueError("provider charge exceeds hard ceiling")
    if not isinstance(receipt["allocation_id"], str) or not receipt["allocation_id"] or not isinstance(receipt["node_id"], str) or not receipt["node_id"]:
        raise ValueError("provider identity missing")
    if not isinstance(receipt["public_key_hex"], str) or len(receipt["public_key_hex"]) != 64 or not isinstance(receipt["signature_hex"], str) or len(receipt["signature_hex"]) != 128:
        raise ValueError("provider signature encoding invalid")
    require_digest(receipt["raw_trace_sha256"], "raw trace digest")
    body = {key: value for key, value in receipt.items() if key not in {"signature_hex", "receipt_sha256"}}
    if receipt["receipt_sha256"] != hashlib.sha256(canonical({**body, "signature_hex": receipt["signature_hex"]})).hexdigest():
        raise ValueError("provider receipt self-digest mismatch")


def validate_energy_trace(path: Path) -> int:
    if path.is_symlink() or not path.is_file():
        raise ValueError("energy trace missing or symlinked")
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) < 2 or set(rows[0]) != {"utc_ns", "watts"}:
        raise ValueError("energy trace schema is invalid")
    previous = -1
    for row in rows:
        try:
            timestamp = int(row["utc_ns"])
            watts = float(row["watts"])
        except (TypeError, ValueError) as error:
            raise ValueError("energy trace values are invalid") from error
        if timestamp <= previous or not math.isfinite(watts) or watts < 0:
            raise ValueError("energy trace is not monotone finite nonnegative")
        previous = timestamp
    return len(rows)


def root_digest(root: Path, allowed: set[Path]) -> str:
    entries: dict[str, str] = {}
    for relative in sorted(allowed):
        if relative == Path("campaign_manifest.json"):
            continue
        path = root / relative
        if path.is_symlink() or not path.is_file():
            raise ValueError(f"missing result file: {relative}")
        entries[str(relative)] = sha256_file(path)
    return sha256_bytes(canonical(entries))


def validate_result_root(root: Path, compiled: dict[str, Any]) -> None:
    allowlist = {Path(item) for item in compiled["result_root"]["allowlist"]}
    if not root.is_dir() or root.is_symlink():
        raise ValueError("result root is invalid")
    observed: set[Path] = set()
    for path in root.rglob("*"):
        if path == root:
            continue
        relative = path.relative_to(root)
        if path.is_symlink():
            raise ValueError(f"symlink in result root: {relative}")
        if path.is_dir():
            if not any(candidate.parts[: len(relative.parts)] == relative.parts for candidate in allowlist):
                raise ValueError(f"unlisted result directory: {relative}")
            continue
        observed.add(relative)
    if observed != allowlist:
        raise ValueError("result root file set mismatch")
    manifest = load_json(root / "campaign_manifest.json")
    validate_campaign_manifest(manifest, sha256_file(Path.cwd() / COMPILED))
    if manifest["result_root_sha256"] != root_digest(root, allowlist):
        raise ValueError("result root digest binding mismatch")
    validate_energy_trace(root / "energy/raw_trace.csv")


def validate_packet(repo_root: Path = Path.cwd()) -> dict[str, Any]:
    for relative in REVIEWED_FILES:
        path = repo_root / relative
        if path.is_symlink() or not path.is_file():
            raise ValueError(f"review file missing: {relative}")
    compiled = validate_compiled(repo_root)
    return {"valid": True, "state_slice": STATE_SLICE, "reviewed_files": list(REVIEWED_FILES), "compiled_sha256": sha256_file(repo_root / COMPILED), "compiled_self_digest": compiled["compiled_sha256"]}


if __name__ == "__main__":
    print(json.dumps(validate_packet(), sort_keys=True))
