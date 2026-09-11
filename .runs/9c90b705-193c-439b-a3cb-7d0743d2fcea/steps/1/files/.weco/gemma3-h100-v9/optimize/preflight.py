#!/usr/bin/env python3
"""No-spend H100 launch-manifest preflight.

State slice: continual-learning-gemma3-fineweb-edu-replication-h100-v9.
"""

from __future__ import annotations

import argparse
import base64
import datetime as dt
import hashlib
import json
import math
import re
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any


STATE_SLICE = "continual-learning-gemma3-fineweb-edu-replication-h100-v9"
PROTO_PATH = "docs/research/continual-learning/320-gemma3-fineweb-edu-replication-h100-v9-protocol.md"
PACKET_PATH = "docs/research/continual-learning/321-gemma3-fineweb-edu-replication-h100-v9-review-packet.md"
SCHEMA = "gemma3-fineweb-edu-replication-h100-v9-launch-manifest"
EXPECTED_KEYS = {
    "schema", "state_slice", "provider", "node_type", "job_mode", "hard_usd_ceiling",
    "quoted_gpu_usd_per_minute", "max_runtime_minutes", "estimated_max_total_usd",
    "provider_project", "provider_attestation_key_id", "provider_trust_root_id",
    "provider_trust_root_public_key", "provider_trust_root_registry_path",
    "provider_trust_root_registry_sha256", "container_image", "container_digest",
    "cuda_driver_version", "container_network_mode", "code_bundle_path",
    "code_bundle_sha256", "runner_entrypoint", "runtime_lock_path",
    "runtime_lock_sha256", "network_lock", "implementation_manifest_path",
    "implementation_manifest_sha256", "model_bundle_path", "model_id",
    "model_revision", "model_architecture", "model_manifest_sha256",
    "data_bundle_path", "source_bundle_path", "raw_bundle_path",
    "data_manifest_sha256", "source_manifest_sha256", "external_storage_namespace",
    "review_receipt_path", "review_receipt_sha256", "protocol_sha256",
    "packet_sha256", "launch_command", "launch_command_sha256", "stop_rule",
    "assessment_enabled", "training_enabled", "network_during_effects",
    "effects_run", "manifest_sha256",
}
REVIEWED_FILES = (
    "docs/research/continual-learning/320-gemma3-fineweb-edu-replication-h100-v9-protocol.md",
    "docs/research/continual-learning/321-gemma3-fineweb-edu-replication-h100-v9-review-packet.md",
    "experiments/continual_learning/gemma3_fineweb_edu_replication_h100_v9_preflight.py",
    "experiments/continual_learning/gemma3_fineweb_edu_replication_h100_v9.py",
    "experiments/continual_learning/validate_gemma3_fineweb_edu_replication_h100_v9.py",
    "experiments/continual_learning/pack_gemma3_fineweb_edu_replication_h100_v9.py",
    "experiments/continual_learning/tests/test_gemma3_fineweb_edu_replication_h100_v9_preflight.py",
    "experiments/continual_learning/tests/test_gemma3_fineweb_edu_replication_h100_v9.py",
    "experiments/continual_learning/gemma3_fineweb_edu_replication_h100_v9_provider/Dockerfile",
    "experiments/continual_learning/gemma3_fineweb_edu_replication_h100_v9_provider/requirements.lock",
    "experiments/continual_learning/gemma3_fineweb_edu_replication_h100_v9_provider/runtime-lock.json",
    "experiments/continual_learning/gemma3_fineweb_edu_replication_h100_v9_provider/run_h100_v9.sh",
    "AGENTS.md",
    "docs/research/continual-learning/322-gemma3-fineweb-edu-replication-h100-v9-implementation-manifest.json",
)
IMPLEMENTATION_FILES = tuple(
    p for p in REVIEWED_FILES if p != "docs/research/continual-learning/322-gemma3-fineweb-edu-replication-h100-v9-implementation-manifest.json"
)
REVIEW_FINDINGS = {
    "custody_and_fresh_disjoint_cohort", "provider_shape_and_hard_budget_gate",
    "runtime_and_model_freeze", "qualification_and_network_boundary",
    "locked_recurrence_controls_and_uncertainty", "independent_validator_and_publication_order",
    "v1_v2_identity_preserved_without_scientific_reuse",
}
REVIEW_RECEIPT_KEYS = {
    "schema", "state_slice", "review_decision", "reviewer", "reviewed_at_utc",
    "reviewed_files", "reviewed_file_sha256", "protocol_sha256",
    "review_packet_sha256", "implementation_manifest_sha256", "findings",
    "effects_run", "review_thread_id", "reviewer_key_id", "reviewer_public_key",
    "review_signature", "receipt_sha256",
}
STOP_RULE = "terminate at first failed gate or budget boundary"
HARD_USD_CEILING = Decimal("69.00")
PROVIDER_TRUST_ROOT_SCHEMA = "givemeanode-attestation-trust-root-v1"


def canonical(value: Any) -> bytes:
    def encode(item: Any) -> str:
        if isinstance(item, Decimal):
            return format(item, "f")
        if isinstance(item, dict):
            entries = []
            for key in sorted(item):
                entries.append(json.dumps(str(key), ensure_ascii=False) + ":" + encode(item[key]))
            return "{" + ",".join(entries) + "}"
        if isinstance(item, (list, tuple)):
            return "[" + ",".join(encode(element) for element in item) + "]"
        return json.dumps(item, ensure_ascii=False, separators=(",", ":"))
    return (encode(value) + "\n").encode("utf-8")


def digest(value: dict[str, Any], field: str) -> str:
    return hashlib.sha256(canonical({k: v for k, v in value.items() if k != field})).hexdigest()


def sha256_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def exact_decimal(value: Any, label: str) -> Decimal:
    if isinstance(value, bool) or not isinstance(value, (int, float, str, Decimal)):
        raise ValueError(f"{label} must be a decimal number")
    try:
        number = value if isinstance(value, Decimal) else Decimal(str(value))
    except (InvalidOperation, ValueError) as error:
        raise ValueError(f"{label} must be a decimal number") from error
    if not number.is_finite():
        raise ValueError(f"{label} must be finite")
    return number


def exact_usd(value: Any, label: str) -> Decimal:
    d = exact_decimal(value, label)
    if d.as_tuple().exponent != -2:
        raise ValueError(f"{label} must have exactly two fractional digits: {value}")
    return d


def finite_positive(value: Any, label: str) -> Decimal:
    number = exact_decimal(value, label)
    if number <= 0:
        raise ValueError(f"{label} must be finite and positive")
    return number


def sha256_hex(value: Any, label: str) -> str:
    if not isinstance(value, str) or len(value) != 64:
        raise ValueError(f"{label} must be a SHA-256 hex digest")
    try:
        int(value, 16)
    except ValueError as error:
        raise ValueError(f"{label} must be a SHA-256 hex digest") from error
    return value


def validate_implementation_manifest(path: Path, repo_root: Path | None = None) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise ValueError("implementation manifest must be a regular file")
    manifest = json.loads(path.read_text(encoding="utf-8"), parse_float=Decimal)
    if set(manifest) != {"schema", "state_slice", "files", "manifest_sha256"}:
        raise ValueError("implementation manifest schema is not closed")
    if manifest["schema"] != "gemma3-fineweb-edu-replication-h100-v9-implementation" or manifest["state_slice"] != STATE_SLICE:
        raise ValueError("implementation manifest identity mismatch")
    files = manifest["files"]
    if [f["path"] for f in files] != list(IMPLEMENTATION_FILES):
        raise ValueError("implementation manifest file set mismatch")
    for f in files:
        sha256_hex(f["sha256"], "implementation file digest")
        if repo_root is not None:
            if sha256_file(repo_root / f["path"]) != f["sha256"]:
                raise ValueError(f"implementation file digest mismatch: {f['path']}")
    if manifest["manifest_sha256"] != digest(manifest, "manifest_sha256"):
        raise ValueError("implementation manifest digest mismatch")
    return manifest


def validate_review_receipt(path: Path, protocol: Path, packet: Path, repo_root: Path, implementation: dict[str, Any]) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise ValueError("review receipt must be a regular file")
    receipt = json.loads(path.read_text(encoding="utf-8"), parse_float=Decimal)
    if set(receipt) != REVIEW_RECEIPT_KEYS:
        raise ValueError("review receipt schema is not closed")
    if receipt["schema"] != "gemma3-fineweb-edu-replication-h100-v9-independent-review" or receipt["state_slice"] != STATE_SLICE or receipt["review_decision"] != "ACCEPT":
        raise ValueError("review receipt identity mismatch")
    if receipt["reviewed_files"] != list(REVIEWED_FILES):
        raise ValueError("review receipt file binding is not exact")
    for rel in REVIEWED_FILES:
        if receipt["reviewed_file_sha256"][rel] != sha256_file(repo_root / rel):
            raise ValueError(f"review receipt file digest mismatch: {rel}")
    if receipt["protocol_sha256"] != sha256_file(protocol) or receipt["review_packet_sha256"] != sha256_file(packet) or receipt["implementation_manifest_sha256"] != implementation["manifest_sha256"]:
        raise ValueError("review receipt digest binding mismatch")
    if set(receipt["findings"]) != REVIEW_FINDINGS or any(not receipt["findings"][n] for n in REVIEW_FINDINGS):
        raise ValueError("review findings are not an all-true closed set")
    try:
        pk = base64.b64decode(receipt["reviewer_public_key"], validate=True)
        sig = base64.b64decode(receipt["review_signature"], validate=True)
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
        payload = {k: v for k, v in receipt.items() if k not in {"review_signature", "receipt_sha256"}}
        Ed25519PublicKey.from_public_bytes(pk).verify(sig, canonical(payload))
    except Exception as e:
        raise ValueError("review signature is not independently verified") from e
    if receipt["receipt_sha256"] != digest(receipt, "receipt_sha256"):
        raise ValueError("review receipt digest mismatch")
    return receipt


def _immutable(p: Any, label: str, repo: Path) -> Path:
    path = Path(p).expanduser().resolve()
    if repo in path.parents or path == repo:
        raise ValueError(f"{label} must be outside repository")
    if path.is_symlink() or not path.exists():
        raise ValueError(f"{label} must be an existing non-symlink path")
    curr = path
    while True:
        if curr.is_symlink() or (curr.stat().st_mode & 0o002):
            raise ValueError(f"{label} path component insecure: {curr}")
        if curr.parent == curr: break
        curr = curr.parent
    if (path.stat().st_mode & 0o222) or (path.parent.stat().st_mode & 0o222):
        raise ValueError(f"{label} or parent is mutable")
    return path


def validate_launch_manifest(path: Path, repo_root: Path | None = None) -> dict[str, Any]:
    if repo_root is None: repo_root = Path(__file__).resolve().parents[2]
    if path.is_symlink() or not path.is_file():
        raise ValueError("launch manifest must be a regular file")
    manifest = json.loads(path.read_text(encoding="utf-8"), parse_float=Decimal)
    if set(manifest) != EXPECTED_KEYS:
        raise ValueError("launch manifest schema is not closed")
    if manifest["schema"] != SCHEMA or manifest["state_slice"] != STATE_SLICE:
        raise ValueError("launch manifest identity mismatch")
    ceiling = exact_usd(manifest["hard_usd_ceiling"], "hard_usd_ceiling")
    rate = exact_usd(manifest["quoted_gpu_usd_per_minute"], "quoted_gpu_usd_per_minute")
    minutes = finite_positive(manifest["max_runtime_minutes"], "max_runtime_minutes")
    estimate = exact_usd(manifest["estimated_max_total_usd"], "estimated_max_total_usd")
    if ceiling != HARD_USD_CEILING:
        raise ValueError("hard_usd_ceiling must be exactly USD 69.00")
    if (rate * minutes).quantize(Decimal("0.01")) != estimate or estimate > ceiling:
        raise ValueError("launch budget arithmetic exceeds the hard ceiling")
    for f in ("code_bundle_sha256", "model_manifest_sha256", "data_manifest_sha256", "source_manifest_sha256", "review_receipt_sha256", "protocol_sha256", "packet_sha256"):
        sha256_hex(manifest[f], f)
    if manifest["assessment_enabled"] is not True or manifest["training_enabled"] is not False:
        raise ValueError("H100 replication must include assessment and no training")
    if manifest["model_id"] != "google/gemma-3-1b-pt" or manifest["model_architecture"] != "Gemma3ForCausalLM":
        raise ValueError("model identity mismatch")
    for f in ("code_bundle_path", "model_bundle_path", "data_bundle_path", "source_bundle_path", "raw_bundle_path"):
        _immutable(manifest[f], f, repo_root)
    if sha256_file(Path(manifest["code_bundle_path"]).expanduser().resolve()) != manifest["code_bundle_sha256"]:
        raise ValueError("code bundle digest mismatch")
    proto, pack = repo_root / PROTO_PATH, repo_root / PACKET_PATH
    impl = validate_implementation_manifest(repo_root / manifest["implementation_manifest_path"], repo_root)
    validate_review_receipt(repo_root / manifest["review_receipt_path"], proto, pack, repo_root, impl)
    if manifest["manifest_sha256"] != digest(manifest, "manifest_sha256"):
        raise ValueError("launch manifest digest mismatch")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    args = parser.parse_args()
    try:
        print(json.dumps(validate_launch_manifest(args.manifest), indent=2, sort_keys=True, default=str))
        return 0
    except Exception as e:
        print(json.dumps({"valid": False, "error": str(e)}, sort_keys=True))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
