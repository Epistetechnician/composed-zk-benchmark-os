"""Verify an external CL-Bench review receipt without granting execution.

State slice: ``aligned-holistic-continual-learning-interpretability-monorepo-v1``.

This bridge is intentionally verifier-only. It creates no reviewer key, signs
no verdict, contacts no reviewer, and cannot open model, provider, spend,
assessment, trace, or Evidence Ledger authority. The external registry owner
must provide the reviewer registry and its trust-anchor public key out of band.
"""

from __future__ import annotations

import argparse
import base64
import binascii
import datetime as dt
import hashlib
import json
import re
from pathlib import Path
from typing import Any, Mapping

from experiments.continual_learning import clbench_task_level_alignment_v1 as contract


STATE_SLICE = contract.STATE_SLICE
PROTOCOL_ID = contract.PROTOCOL_ID
REVIEW_RECEIPT_SCHEMA = f"{PROTOCOL_ID}-independent-review-receipt"
REGISTRY_SCHEMA = f"{PROTOCOL_ID}-external-reviewer-registry"
FINAL_REVIEWER_ROLE = "FINAL_REVIEWER"
DECISIONS = {"ACCEPT", "REJECT"}
DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
PREFIXED_DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
TIMESTAMP_RE = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$")
REQUIRED_CHECKS = (
    "benchmark_identity",
    "benchmark_semantics",
    "life_exclusion",
    "arm_completeness",
    "incoming_estimand",
    "protected_estimand",
    "split_integrity",
    "resource_equality",
    "statistics",
    "prediction_lock",
    "custody",
    "replication",
    "claim_ceiling",
    "execution_closure",
)


class ReviewBridgeError(ValueError):
    """Raised when an external review binding or receipt is invalid."""


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ReviewBridgeError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def load_json(path: Path) -> Any:
    """Load strict JSON without duplicate keys or non-standard numbers."""

    try:
        return json.loads(
            path.read_bytes().decode("utf-8"),
            object_pairs_hook=_reject_duplicate_keys,
            parse_constant=lambda value: (_ for _ in ()).throw(
                ReviewBridgeError(f"non-standard JSON constant: {value}")
            ),
        )
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ReviewBridgeError(f"cannot read JSON: {path}") from exc


def canonical_bytes(value: Any) -> bytes:
    """Return the exact JSON bytes covered by detached signatures."""

    try:
        return json.dumps(
            value,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise ReviewBridgeError("value is not canonical JSON") from exc


def digest_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def canonical_digest(value: Any) -> str:
    return digest_bytes(canonical_bytes(value))


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ReviewBridgeError(message)


def _strict_keys(value: Mapping[str, Any], expected: set[str], label: str) -> None:
    _require(set(value) == expected, f"{label} schema")


def _timestamp(value: Any, label: str) -> dt.datetime:
    _require(isinstance(value, str) and TIMESTAMP_RE.fullmatch(value) is not None, f"{label} timestamp")
    try:
        return dt.datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=dt.timezone.utc)
    except ValueError as exc:
        raise ReviewBridgeError(f"{label} timestamp") from exc


def _decode(value: Any, label: str, *, length: int) -> bytes:
    _require(isinstance(value, str), f"{label} must be base64 text")
    try:
        decoded = base64.b64decode(value.encode("ascii"), validate=True)
    except (UnicodeEncodeError, binascii.Error, ValueError) as exc:
        raise ReviewBridgeError(f"{label} encoding") from exc
    _require(len(decoded) == length, f"{label} length")
    return decoded


def _regular_external(path: Path, label: str) -> Path:
    _require(path.is_absolute(), f"{label} must be absolute")
    _require(not path.is_symlink(), f"{label} cannot be a symlink")
    resolved = path.resolve()
    _require(resolved.is_file() and not resolved.is_symlink(), f"{label} must be a regular file")
    try:
        resolved.relative_to(contract.REPO_ROOT)
    except ValueError:
        return resolved
    raise ReviewBridgeError(f"{label} must be outside the repository")


def _verify_signature(payload: bytes, signature: Mapping[str, Any], expected_public_key: bytes, label: str) -> None:
    _strict_keys(signature, {"algorithm", "public_key_base64", "signature_base64"}, f"{label} signature")
    _require(signature["algorithm"] == "Ed25519", f"{label} signature algorithm")
    public_key = _decode(signature["public_key_base64"], f"{label} public key", length=32)
    signed = _decode(signature["signature_base64"], f"{label} signature", length=64)
    _require(public_key == expected_public_key, f"{label} key binding")
    try:
        from cryptography.exceptions import InvalidSignature
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

        Ed25519PublicKey.from_public_bytes(public_key).verify(signed, payload)
    except ImportError as exc:
        raise ReviewBridgeError("Ed25519 verifier unavailable") from exc
    except (InvalidSignature, TypeError, ValueError) as exc:
        raise ReviewBridgeError(f"{label} signature invalid") from exc


def _load_owner_key(path: Path) -> bytes:
    resolved = _regular_external(path, "registry owner key")
    _require(resolved.stat().st_mode & 0o077 == 0, "registry owner key must be owner-only")
    raw = resolved.read_bytes()
    _require(len(raw) == 32, "registry owner key length")
    return raw


def _load_registry(path: Path, owner_key_path: Path) -> tuple[dict[str, dict[str, Any]], dt.datetime, dt.datetime]:
    registry_path = _regular_external(path, "reviewer registry")
    owner_public_key = _load_owner_key(owner_key_path)
    value = load_json(registry_path)
    _require(isinstance(value, Mapping), "reviewer registry object")
    _strict_keys(
        value,
        {"schema_version", "registry_id", "issuer", "issued_at_utc", "expires_at_utc", "keys", "registry_signature"},
        "reviewer registry",
    )
    _require(value["schema_version"] == REGISTRY_SCHEMA, "reviewer registry schema version")
    _require(isinstance(value["registry_id"], str) and value["registry_id"], "registry id")
    _require(isinstance(value["issuer"], str) and value["issuer"], "registry issuer")
    issued = _timestamp(value["issued_at_utc"], "registry issued_at_utc")
    expires = _timestamp(value["expires_at_utc"], "registry expires_at_utc")
    _require(expires > issued, "reviewer registry expiry")
    _require(isinstance(value["keys"], list) and value["keys"], "reviewer registry keys")
    _verify_signature(
        canonical_bytes({key: item for key, item in value.items() if key != "registry_signature"}),
        value["registry_signature"],
        owner_public_key,
        "reviewer registry",
    )

    result: dict[str, dict[str, Any]] = {}
    for item in value["keys"]:
        _require(isinstance(item, Mapping), "reviewer registry entry")
        _strict_keys(
            item,
            {"key_id", "identity", "role", "public_key_base64", "independently_administered", "conflict_free"},
            "reviewer registry entry",
        )
        key_id = item["key_id"]
        _require(isinstance(key_id, str) and key_id and key_id not in result, "reviewer registry key id")
        _require(isinstance(item["identity"], str) and item["identity"], "reviewer identity")
        _require(item["role"] == FINAL_REVIEWER_ROLE, "reviewer registry role")
        public_key = _decode(item["public_key_base64"], "reviewer public key", length=32)
        _require(item["independently_administered"] is True, "reviewer independence assertion")
        _require(item["conflict_free"] is True, "reviewer conflict assertion")
        _require(public_key != owner_public_key, "reviewer key cannot be registry owner key")
        result[key_id] = dict(item)
    return result, issued, expires


def review_binding(manifest_path: Path = contract.MANIFEST_PATH) -> dict[str, Any]:
    """Return the portable, non-authorizing digest binding for handoff."""

    resolved = manifest_path.resolve()
    _require(resolved == contract.MANIFEST_PATH.resolve(), "manifest path")
    manifest = contract.load_json(resolved)
    _require(isinstance(manifest, Mapping), "manifest object")
    protocol_digest = contract.validate_manifest(manifest, manifest_path=resolved)
    return {
        "protocol_id": PROTOCOL_ID,
        "state_slice": STATE_SLICE,
        "protocol_digest": protocol_digest,
        "mailbox_packet_digest": f"sha256:{protocol_digest}",
        "manifest_sha256": digest_bytes(resolved.read_bytes()),
        "packet_sha256": manifest["review_packet_sha256"],
        "review_bundle_sha256": canonical_digest(manifest["review_bundle"]),
        "required_checks": list(REQUIRED_CHECKS),
        "execution_authorized": False,
    }


def verify_receipt(receipt_path: Path, registry_path: Path, owner_key_path: Path) -> dict[str, Any]:
    """Verify an externally supplied typed receipt against current bytes."""

    receipt_file = _regular_external(receipt_path, "review receipt")
    binding = review_binding()
    value = load_json(receipt_file)
    _require(isinstance(value, Mapping), "review receipt object")
    _strict_keys(
        value,
        {
            "schema_version",
            "protocol_id",
            "state_slice",
            "decision",
            "reviewer_identity",
            "reviewer_role",
            "conflict_of_interest",
            "reviewed_at_utc",
            "protocol_digest",
            "manifest_sha256",
            "packet_sha256",
            "review_bundle_sha256",
            "checks",
            "execution_enabled",
            "model_execution_authorized",
            "provider_calls_authorized",
            "assessment_opened",
            "signature",
        },
        "review receipt",
    )
    _require(value["schema_version"] == REVIEW_RECEIPT_SCHEMA, "review receipt schema version")
    _require(value["protocol_id"] == PROTOCOL_ID and value["state_slice"] == STATE_SLICE, "review receipt identity")
    _require(value["decision"] in DECISIONS, "review decision")
    _require(isinstance(value["reviewer_identity"], str) and value["reviewer_identity"], "reviewer identity")
    _require(value["reviewer_role"] == FINAL_REVIEWER_ROLE, "reviewer role")
    _require(value["conflict_of_interest"] is False, "reviewer conflict of interest")
    reviewed_at = _timestamp(value["reviewed_at_utc"], "reviewed_at_utc")
    _require(value["protocol_digest"] == binding["protocol_digest"], "review protocol digest")
    _require(value["manifest_sha256"] == binding["manifest_sha256"], "review manifest digest")
    _require(value["packet_sha256"] == binding["packet_sha256"], "review packet digest")
    _require(value["review_bundle_sha256"] == binding["review_bundle_sha256"], "review bundle digest")
    _require(isinstance(value["checks"], Mapping), "review checks object")
    _require(set(value["checks"]) == set(REQUIRED_CHECKS), "review check roster")
    _require(all(item in {"PASS", "FAIL"} for item in value["checks"].values()), "review check values")
    if value["decision"] == "ACCEPT":
        _require(all(item == "PASS" for item in value["checks"].values()), "ACCEPT requires every check to PASS")
    for field in ("execution_enabled", "model_execution_authorized", "provider_calls_authorized", "assessment_opened"):
        _require(value[field] is False, f"review receipt {field}")

    registry, registry_issued, registry_expires = _load_registry(registry_path, owner_key_path)
    _require(registry_issued <= reviewed_at < registry_expires, "reviewed_at_utc outside registry validity")
    signature = value["signature"]
    _require(isinstance(signature, Mapping), "review receipt signature")
    _strict_keys(signature, {"algorithm", "key_id", "public_key_base64", "signature_base64"}, "review receipt signature")
    key_id = signature["key_id"]
    _require(isinstance(key_id, str) and key_id in registry, "reviewer signing key")
    entry = registry[key_id]
    _require(entry["identity"] == value["reviewer_identity"], "reviewer key identity")
    reviewer_public_key = _decode(entry["public_key_base64"], "reviewer public key", length=32)
    _verify_signature(
        canonical_bytes({key: item for key, item in value.items() if key != "signature"}),
        {key: item for key, item in signature.items() if key != "key_id"},
        reviewer_public_key,
        "review receipt",
    )
    return {
        "valid": True,
        "decision": value["decision"],
        "protocol_id": PROTOCOL_ID,
        "state_slice": STATE_SLICE,
        "reviewer_identity": value["reviewer_identity"],
        "execution_authorized": False,
    }


def _main() -> int:
    parser = argparse.ArgumentParser(description="verify the external CL-Bench review binding")
    subparsers = parser.add_subparsers(dest="command", required=True)

    binding = subparsers.add_parser("binding")
    binding.set_defaults(handler=lambda args: print(json.dumps(review_binding(), sort_keys=True, indent=2)))

    verify = subparsers.add_parser("verify-receipt")
    verify.add_argument("--receipt", type=Path, required=True)
    verify.add_argument("--registry", type=Path, required=True)
    verify.add_argument("--registry-owner-key", type=Path, required=True)
    verify.set_defaults(
        handler=lambda args: print(
            json.dumps(verify_receipt(args.receipt, args.registry, args.registry_owner_key), sort_keys=True, indent=2)
        )
    )
    args = parser.parse_args()
    args.handler(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
