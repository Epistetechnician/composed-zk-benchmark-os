#!/usr/bin/env python3
"""No-spend H100 launch-manifest preflight.

State slice: continual-learning-gemma3-fineweb-edu-replication-h100-v6.

This module validates a sealed launch manifest only. It never contacts a
provider, starts a container, loads a model, or reads external custody roots.
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


STATE_SLICE = "continual-learning-gemma3-fineweb-edu-replication-h100-v6"
PROTOCOL_PATH = Path(
    "docs/research/"
    "continual-learning/270-gemma3-fineweb-edu-replication-h100-v6-protocol.md"
)
PACKET_PATH = Path(
    "docs/research/"
    "continual-learning/271-gemma3-fineweb-edu-replication-h100-v6-review-packet.md"
)
SCHEMA = "gemma3-fineweb-edu-replication-h100-v6-launch-manifest"
EXPECTED_KEYS = {
    "schema",
    "state_slice",
    "provider",
    "node_type",
    "job_mode",
    "hard_usd_ceiling",
    "quoted_gpu_usd_per_minute",
    "max_runtime_minutes",
    "estimated_max_total_usd",
    "provider_project",
    "provider_attestation_key_id",
    "provider_trust_root_id",
    "provider_trust_root_public_key",
    "provider_trust_root_registry_path",
    "provider_trust_root_registry_sha256",
    "container_image",
    "container_digest",
    "cuda_driver_version",
    "container_network_mode",
    "code_bundle_path",
    "code_bundle_sha256",
    "runner_entrypoint",
    "runtime_lock_path",
    "runtime_lock_sha256",
    "network_lock",
    "implementation_manifest_path",
    "implementation_manifest_sha256",
    "model_bundle_path",
    "model_id",
    "model_revision",
    "model_architecture",
    "model_manifest_sha256",
    "data_bundle_path",
    "source_bundle_path",
    "raw_bundle_path",
    "data_manifest_sha256",
    "source_manifest_sha256",
    "external_storage_namespace",
    "review_receipt_path",
    "review_receipt_sha256",
    "protocol_sha256",
    "packet_sha256",
    "launch_command",
    "launch_command_sha256",
    "stop_rule",
    "assessment_enabled",
    "training_enabled",
    "network_during_effects",
    "effects_run",
    "manifest_sha256",
}
REVIEWED_FILES = (
    "docs/research/continual-learning/270-gemma3-fineweb-edu-replication-h100-v6-protocol.md",
    "docs/research/continual-learning/271-gemma3-fineweb-edu-replication-h100-v6-review-packet.md",
    "experiments/continual_learning/gemma3_fineweb_edu_replication_h100_v6_preflight.py",
    "experiments/continual_learning/gemma3_fineweb_edu_replication_h100_v6.py",
    "experiments/continual_learning/validate_gemma3_fineweb_edu_replication_h100_v6.py",
    "experiments/continual_learning/pack_gemma3_fineweb_edu_replication_h100_v6.py",
    "experiments/continual_learning/tests/test_gemma3_fineweb_edu_replication_h100_v6_preflight.py",
    "experiments/continual_learning/tests/test_gemma3_fineweb_edu_replication_h100_v6.py",
    "experiments/continual_learning/gemma3_fineweb_edu_replication_h100_v6_provider/Dockerfile",
    "experiments/continual_learning/gemma3_fineweb_edu_replication_h100_v6_provider/requirements.lock",
    "experiments/continual_learning/gemma3_fineweb_edu_replication_h100_v6_provider/runtime-lock.json",
    "experiments/continual_learning/gemma3_fineweb_edu_replication_h100_v6_provider/run_h100_v6.sh",
    "AGENTS.md",
    "docs/research/continual-learning/272-gemma3-fineweb-edu-replication-h100-v6-implementation-manifest.json",
)
IMPLEMENTATION_FILES = tuple(
    path for path in REVIEWED_FILES
    if path != "docs/research/continual-learning/272-gemma3-fineweb-edu-replication-h100-v6-implementation-manifest.json"
)
REVIEW_FINDINGS = {
    "custody_and_fresh_disjoint_cohort",
    "provider_shape_and_hard_budget_gate",
    "runtime_and_model_freeze",
    "qualification_and_network_boundary",
    "locked_recurrence_controls_and_uncertainty",
    "independent_validator_and_publication_order",
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
HARD_USD_CEILING = 100.0
PROVIDER_TRUST_ROOT_SCHEMA = "givemeanode-attestation-trust-root-v1"


def canonical(value: Any) -> bytes:
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n"
    ).encode("utf-8")


def digest(value: dict[str, Any], field: str) -> str:
    body = {key: item for key, item in value.items() if key != field}
    return hashlib.sha256(canonical(body)).hexdigest()


def sha256_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def finite_positive(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{label} must be a number")
    number = float(value)
    if not math.isfinite(number) or number <= 0:
        raise ValueError(f"{label} must be finite and positive")
    return number


def exact_decimal(value: Any, label: str) -> Decimal:
    if isinstance(value, bool) or not isinstance(value, (int, float, str)):
        raise ValueError(f"{label} must be a decimal number")
    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError) as error:
        raise ValueError(f"{label} must be a decimal number") from error
    if not number.is_finite():
        raise ValueError(f"{label} must be finite")
    return number


def sha256_hex(value: Any, label: str) -> str:
    if not isinstance(value, str) or len(value) != 64:
        raise ValueError(f"{label} must be a SHA-256 hex digest")
    try:
        int(value, 16)
    except ValueError as error:
        raise ValueError(f"{label} must be a SHA-256 hex digest") from error
    return value


def oci_sha256(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.startswith("sha256:"):
        raise ValueError(f"{label} must use OCI sha256: form")
    sha256_hex(value[7:], label)
    return value


def load_object(path: Path, label: str) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"{label} must be a regular file")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be an object")
    return value


def _immutable_existing_path(
    value: Any,
    label: str,
    repo_root: Path,
) -> Path:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be nonblank")
    path = Path(value).expanduser()
    if not path.is_absolute():
        raise ValueError(f"{label} must be absolute")
    if path.is_symlink() or not path.exists():
        raise ValueError(f"{label} must be an existing non-symlink path")
    resolved = path.resolve()
    repository = repo_root.expanduser().resolve()
    if resolved == repository or repository in resolved.parents:
        raise ValueError(f"{label} must be outside the repository")
    current = path
    while True:
        if current.is_symlink():
            raise ValueError(f"{label} has a symlinked path component")
        if current.parent == current:
            break
        current = current.parent
    parent = path.parent
    if parent.is_symlink() or not parent.is_dir():
        raise ValueError(f"{label} parent must be a real directory")
    if parent.stat().st_mode & 0o222:
        raise ValueError(f"{label} parent is mutable")
    if path.is_dir():
        if path.stat().st_mode & 0o222:
            raise ValueError(f"{label} is mutable")
        for candidate in path.rglob("*"):
            if candidate.is_symlink():
                raise ValueError(f"{label} contains symlink")
            if candidate.stat().st_mode & 0o222:
                raise ValueError(f"{label} contains mutable entry: {candidate}")
    elif path.is_file():
        if path.stat().st_mode & 0o222:
            raise ValueError(f"{label} is mutable")
    else:
        raise ValueError(f"{label} must be a regular file or directory")
    return resolved


def validate_implementation_manifest(
    path: Path, repo_root: Path | None = None
) -> dict[str, Any]:
    manifest = load_object(path, "implementation manifest")
    expected = {"schema", "state_slice", "files", "manifest_sha256"}
    if set(manifest) != expected:
        raise ValueError("implementation manifest schema is not closed")
    if (
        manifest["schema"]
        != "gemma3-fineweb-edu-replication-h100-v6-implementation"
        or manifest["state_slice"] != STATE_SLICE
    ):
        raise ValueError("implementation manifest identity mismatch")
    files = manifest["files"]
    if (
        not isinstance(files, list)
        or not files
        or any(
            not isinstance(item, dict)
            or set(item) != {"path", "sha256"}
            or not isinstance(item["path"], str)
            or not item["path"]
            or not isinstance(item["sha256"], str)
            or len(item["sha256"]) != 64
            for item in files
        )
        or len({item["path"] for item in files}) != len(files)
    ):
        raise ValueError("implementation manifest files are invalid")
    if [item["path"] for item in files] != list(IMPLEMENTATION_FILES):
        raise ValueError("implementation manifest file set is not the exact reviewed set")
    for item in files:
        sha256_hex(item["sha256"], "implementation file digest")
        if repo_root is not None:
            relative = Path(item["path"])
            if relative.is_absolute() or ".." in relative.parts:
                raise ValueError("implementation manifest path is unsafe")
            file_path = repo_root / relative
            if file_path.is_symlink() or not file_path.is_file():
                raise ValueError(f"implementation file is missing: {relative}")
            if sha256_file(file_path) != item["sha256"]:
                raise ValueError(f"implementation file digest mismatch: {relative}")
    if manifest["manifest_sha256"] != digest(manifest, "manifest_sha256"):
        raise ValueError("implementation manifest digest mismatch")
    return manifest


def validate_review_receipt(
    path: Path,
    protocol: Path,
    packet: Path,
    repo_root: Path,
    implementation_manifest: dict[str, Any],
) -> dict[str, Any]:
    receipt = load_object(path, "review receipt")
    if set(receipt) != REVIEW_RECEIPT_KEYS:
        raise ValueError("review receipt schema is not closed")
    if receipt["schema"] != "gemma3-fineweb-edu-replication-h100-v6-independent-review" or receipt["state_slice"] != STATE_SLICE or receipt["review_decision"] != "ACCEPT" or receipt["effects_run"] is not False:
        raise ValueError("review receipt identity or effects flag invalid")
    if not isinstance(receipt["reviewer"], str) or not receipt["reviewer"].strip() or not isinstance(receipt["reviewed_at_utc"], str) or not receipt["reviewed_at_utc"].endswith("Z"):
        raise ValueError("review receipt identity or timestamp missing")
    try:
        timestamp = dt.datetime.fromisoformat(receipt["reviewed_at_utc"].replace("Z", "+00:00"))
    except ValueError as error:
        raise ValueError("review receipt timestamp invalid") from error
    if timestamp.tzinfo is None or timestamp.utcoffset() != dt.timedelta(0):
        raise ValueError("review receipt timestamp is not UTC")
    if receipt["reviewed_files"] != list(REVIEWED_FILES) or not isinstance(receipt["reviewed_file_sha256"], dict) or set(receipt["reviewed_file_sha256"]) != set(REVIEWED_FILES):
        raise ValueError("review receipt file binding is not exact")
    for relative in REVIEWED_FILES:
        file_path = repo_root / relative
        if file_path.is_symlink() or not file_path.is_file() or receipt["reviewed_file_sha256"][relative] != sha256_file(file_path):
            raise ValueError(f"review receipt file digest mismatch: {relative}")
        sha256_hex(receipt["reviewed_file_sha256"][relative], "reviewed file digest")
    if receipt["protocol_sha256"] != sha256_file(protocol) or receipt["review_packet_sha256"] != sha256_file(packet) or receipt["implementation_manifest_sha256"] != implementation_manifest["manifest_sha256"] or receipt["reviewed_file_sha256"]["AGENTS.md"] != sha256_file(repo_root / "AGENTS.md"):
        raise ValueError("review receipt digest binding mismatch")
    if not isinstance(receipt["findings"], dict) or set(receipt["findings"]) != REVIEW_FINDINGS or any(receipt["findings"][name] is not True for name in REVIEW_FINDINGS):
        raise ValueError("review findings are not an all-true closed set")
    for field in ("review_thread_id", "reviewer_key_id", "reviewer_public_key", "review_signature"):
        if not isinstance(receipt[field], str) or not receipt[field].strip():
            raise ValueError(f"review {field} is missing")
    if re.fullmatch(r"[A-Za-z0-9._:-]+", receipt["review_thread_id"]) is None or re.fullmatch(r"[A-Za-z0-9._:-]+", receipt["reviewer_key_id"]) is None:
        raise ValueError("review identity binding is invalid")
    try:
        public_key = base64.b64decode(receipt["reviewer_public_key"], validate=True)
        signature = base64.b64decode(receipt["review_signature"], validate=True)
        if len(public_key) != 32 or len(signature) != 64:
            raise ValueError("review signature length is invalid")
        from cryptography.exceptions import InvalidSignature
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
        payload = {key: value for key, value in receipt.items() if key not in {"review_signature", "receipt_sha256"}}
        Ed25519PublicKey.from_public_bytes(public_key).verify(signature, canonical(payload))
    except (ImportError, InvalidSignature, ValueError, TypeError) as error:
        raise ValueError("review signature is not independently verified") from error
    sha256_hex(receipt["receipt_sha256"], "review receipt digest")
    if receipt["receipt_sha256"] != digest(receipt, "receipt_sha256"):
        raise ValueError("review receipt digest mismatch")
    return receipt


def validate_launch_manifest(
    path: Path, repo_root: Path | None = None
) -> dict[str, Any]:
    if repo_root is None:
        repo_root = Path(__file__).resolve().parents[2]
    manifest = load_object(path, "launch manifest")
    if set(manifest) != EXPECTED_KEYS:
        raise ValueError("launch manifest schema is not closed")
    if manifest["schema"] != SCHEMA or manifest["state_slice"] != STATE_SLICE:
        raise ValueError("launch manifest identity mismatch")
    if manifest["provider"] != "givemeanode":
        raise ValueError("provider must be givemeanode")
    if manifest["node_type"] != "h100-1" or manifest["job_mode"] != "batch":
        raise ValueError("only one h100-1 batch job is permitted")

    ceiling = finite_positive(manifest["hard_usd_ceiling"], "hard_usd_ceiling")
    rate = finite_positive(
        manifest["quoted_gpu_usd_per_minute"],
        "quoted_gpu_usd_per_minute",
    )
    minutes = finite_positive(manifest["max_runtime_minutes"], "max_runtime_minutes")
    estimate = finite_positive(
        manifest["estimated_max_total_usd"],
        "estimated_max_total_usd",
    )
    if ceiling != HARD_USD_CEILING:
        raise ValueError("hard_usd_ceiling must be exactly USD 100.00")
    if exact_decimal(manifest["quoted_gpu_usd_per_minute"], "quoted_gpu_usd_per_minute") * exact_decimal(manifest["max_runtime_minutes"], "max_runtime_minutes") != exact_decimal(manifest["estimated_max_total_usd"], "estimated_max_total_usd") or estimate > ceiling:
        raise ValueError("launch budget arithmetic exceeds the hard ceiling")

    for field in (
        "code_bundle_sha256",
        "implementation_manifest_sha256",
        "runtime_lock_sha256",
        "model_manifest_sha256",
        "data_manifest_sha256",
        "source_manifest_sha256",
        "review_receipt_sha256",
        "protocol_sha256",
        "packet_sha256",
        "launch_command_sha256",
    ):
        sha256_hex(manifest[field], field)
    oci_sha256(manifest["container_digest"], "container_digest")
    for field in (
        "container_image",
        "cuda_driver_version",
        "provider_project",
        "provider_attestation_key_id",
        "provider_trust_root_id",
        "provider_trust_root_public_key",
        "provider_trust_root_registry_path",
        "provider_trust_root_registry_sha256",
        "runner_entrypoint",
        "runtime_lock_path",
        "network_lock",
        "implementation_manifest_path",
        "external_storage_namespace",
        "review_receipt_path",
        "launch_command",
    ):
        if not isinstance(manifest[field], str) or not manifest[field].strip():
            raise ValueError(f"{field} must be nonblank")
    if re.fullmatch(r"[0-9][0-9.]*", manifest["cuda_driver_version"]) is None:
        raise ValueError("cuda_driver_version must be an exact numeric driver version")
    for field in ("provider_attestation_key_id", "provider_trust_root_id"):
        if re.fullmatch(r"[A-Za-z0-9._:-]+", manifest[field]) is None:
            raise ValueError(f"{field} is invalid")
    for field in ("provider_trust_root_public_key",):
        try:
            public_key = base64.b64decode(manifest[field], validate=True)
        except (ValueError, TypeError) as error:
            raise ValueError(f"{field} must be base64 Ed25519 bytes") from error
        if len(public_key) != 32:
            raise ValueError(f"{field} must be base64 Ed25519 bytes")
    if manifest["assessment_enabled"] is not True:
        raise ValueError("H100 replication must include locked assessment")
    if manifest["model_id"] != "google/gemma-3-1b-pt" or manifest["model_architecture"] != "Gemma3ForCausalLM" or re.fullmatch(r"[0-9a-f]{40}", manifest["model_revision"]) is None:
        raise ValueError("model identity is not exact and revision-pinned")
    if manifest["runner_entrypoint"] != "run_h100_v6.sh":
        raise ValueError("runner entrypoint is not the reviewed provider entrypoint")
    if manifest["launch_command"] != "./run_h100_v6.sh":
        raise ValueError("launch command is not the reviewed provider command")
    if manifest["launch_command_sha256"] != hashlib.sha256(
        manifest["launch_command"].encode("utf-8")
    ).hexdigest():
        raise ValueError("launch command digest mismatch")
    if manifest["stop_rule"] != STOP_RULE:
        raise ValueError("stop_rule is not the exact reviewed stop rule")
    if manifest["network_lock"] != "network-none-v6":
        raise ValueError("network lock is not sealed")
    if manifest["container_network_mode"] != "none":
        raise ValueError("container network mode must be none")
    if manifest["runtime_lock_path"] != "runtime-lock.json":
        raise ValueError("runtime lock path is not the reviewed provider lock")
    for field in ("implementation_manifest_path", "review_receipt_path"):
        relative = Path(manifest[field])
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError(f"{field} must be repository-relative")
    if manifest["training_enabled"] is not False:
        raise ValueError("training is forbidden")
    if manifest["network_during_effects"] is not False:
        raise ValueError("network during effects is forbidden")
    if manifest["effects_run"] is not False:
        raise ValueError("launch manifest cannot claim effects already ran")
    for field in (
        "code_bundle_path", "model_bundle_path", "data_bundle_path",
        "source_bundle_path", "raw_bundle_path", "provider_trust_root_registry_path",
    ):
        _immutable_existing_path(manifest[field], field, repo_root)

    registry_path = Path(manifest["provider_trust_root_registry_path"]).expanduser().resolve()
    registry = load_object(registry_path, "provider trust-root registry")
    if set(registry) != {
        "schema", "issuer", "trust_root_id", "public_key", "source_url",
        "source_sha256", "registry_sha256",
    } or registry["schema"] != PROVIDER_TRUST_ROOT_SCHEMA or registry["issuer"] != "givemeanode":
        raise ValueError("provider trust-root registry schema mismatch")
    if registry["trust_root_id"] != manifest["provider_trust_root_id"] or registry["public_key"] != manifest["provider_trust_root_public_key"]:
        raise ValueError("provider trust-root registry does not bind launch root")
    if not isinstance(registry["source_url"], str) or not registry["source_url"].startswith("https://"):
        raise ValueError("provider trust-root registry source is not HTTPS")
    sha256_hex(registry["source_sha256"], "provider trust-root source digest")
    if registry["registry_sha256"] != digest(registry, "registry_sha256") or registry["registry_sha256"] != manifest["provider_trust_root_registry_sha256"]:
        raise ValueError("provider trust-root registry digest mismatch")

    protocol = repo_root / PROTOCOL_PATH
    packet = repo_root / PACKET_PATH
    receipt = repo_root / manifest["review_receipt_path"]
    implementation_manifest = repo_root / manifest["implementation_manifest_path"]
    if manifest["protocol_sha256"] != sha256_file(protocol):
        raise ValueError("launch manifest protocol digest mismatch")
    if manifest["packet_sha256"] != sha256_file(packet):
        raise ValueError("launch manifest packet digest mismatch")
    implementation = validate_implementation_manifest(implementation_manifest, repo_root)
    review = validate_review_receipt(receipt, protocol, packet, repo_root, implementation)
    if manifest["review_receipt_sha256"] != sha256_file(receipt):
        raise ValueError("launch manifest review receipt digest mismatch")
    if (
        manifest["implementation_manifest_sha256"]
        != implementation["manifest_sha256"]
        or review.get("implementation_manifest_sha256")
        != implementation["manifest_sha256"]
    ):
        raise ValueError("review receipt does not bind the implementation manifest")
    if manifest["manifest_sha256"] != digest(manifest, "manifest_sha256"):
        raise ValueError("launch manifest digest mismatch")

    return {
        **manifest,
        "valid": True,
        "state_slice": STATE_SLICE,
        "provider": manifest["provider"],
        "node_type": manifest["node_type"],
        "job_mode": manifest["job_mode"],
        "hard_usd_ceiling": ceiling,
        "estimated_max_total_usd": estimate,
        "model_manifest_sha256": manifest["model_manifest_sha256"],
        "data_manifest_sha256": manifest["data_manifest_sha256"],
        "source_manifest_sha256": manifest["source_manifest_sha256"],
        "protocol_sha256": manifest["protocol_sha256"],
        "packet_sha256": manifest["packet_sha256"],
        "implementation_manifest_sha256": manifest[
            "implementation_manifest_sha256"
        ],
        "code_bundle_sha256": manifest["code_bundle_sha256"],
        "container_digest": manifest["container_digest"],
        "review_receipt_sha256": manifest["review_receipt_sha256"],
        "manifest_sha256": manifest["manifest_sha256"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = validate_launch_manifest(args.manifest)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(json.dumps({"valid": False, "error": str(error)}, sort_keys=True))
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
