"""Prepare and verify the small-RSI lane's independent-review boundary.

State slice: ``recursive-meta-harness-small-rsi-frontier-substitution-v1``.

The packet builder never creates an ACCEPT.  A reviewer outside the operator
identity must sign the exact packet digest.  Even a valid review receipt does
not open this contract-only manifest for model execution.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping

from . import protocol_v1 as protocol


REVIEW_PACKET_SCHEMA_VERSION = "recursive-meta-harness-small-rsi-frontier-substitution-review-packet-v1"
REVIEW_RECEIPT_SCHEMA_VERSION = "recursive-meta-harness-small-rsi-frontier-substitution-review-receipt-v1"
REVIEW_SCOPE = "contract_review_only"
REVIEWER_ROLE = "independent reviewer who did not author, configure, or execute this lane"
REVIEW_CHECKLIST = (
    "protocol_and_source_digests",
    "arm_and_regime_identity",
    "full_cost_completeness",
    "verified_utility_zeroing",
    "assessment_sealing_and_prediction_lock",
    "RSI_mutable_and_immutable_fields",
    "authority_and_leakage_constraints",
    "claim_ceiling_and_execution_boundary",
)


def build_packet(manifest: Mapping[str, Any]) -> dict[str, Any]:
    """Build a pending packet bound to one compiled manifest."""

    protocol._require(manifest.get("state_slice") == protocol.STATE_SLICE, "review packet manifest state slice")
    protocol._require(manifest.get("protocol_id") == protocol.PROTOCOL_ID, "review packet manifest protocol")
    protocol._require(protocol._is_digest(manifest.get("manifest_sha256")), "review packet manifest digest")
    body = {
        "schema_version": REVIEW_PACKET_SCHEMA_VERSION,
        "state_slice": protocol.STATE_SLICE,
        "protocol_id": protocol.PROTOCOL_ID,
        "manifest_sha256": manifest["manifest_sha256"],
        "claim_ceiling": protocol.CLAIM_CEILING,
        "review_scope": REVIEW_SCOPE,
        "reviewer_role": REVIEWER_ROLE,
        "must_check": list(REVIEW_CHECKLIST),
        "decision": "PENDING_INDEPENDENT_REVIEW",
        "effects_run": False,
        "model_execution_authorized": False,
        "assessment_open": False,
        "operator_may_self_sign": False,
    }
    return {**body, "packet_sha256": protocol.digest(body)}


def validate_signed_acceptance(
    packet: Mapping[str, Any],
    receipt: Mapping[str, Any],
    *,
    operator_identity: str,
) -> None:
    """Verify an independent Ed25519 ACCEPT bound to the exact packet."""

    protocol._require(packet.get("decision") == "PENDING_INDEPENDENT_REVIEW", "review packet is not pending")
    packet_digest = packet.get("packet_sha256")
    protocol._require(protocol._is_digest(packet_digest), "review packet digest")
    expected = (
        "schema_version",
        "state_slice",
        "protocol_id",
        "review_scope",
        "decision",
        "packet_sha256",
        "reviewer_identity",
        "reviewer_role",
        "operator_identity",
        "model_execution_authorized",
        "assessment_open",
        "public_key_hex",
        "signature_hex",
        "receipt_sha256",
    )
    protocol._strict_keys(receipt, expected, "review receipt")
    protocol._require(receipt["schema_version"] == REVIEW_RECEIPT_SCHEMA_VERSION, "review receipt schema version")
    protocol._require(receipt["state_slice"] == protocol.STATE_SLICE and receipt["protocol_id"] == protocol.PROTOCOL_ID, "review receipt identity")
    protocol._require(receipt["review_scope"] == REVIEW_SCOPE and receipt["decision"] == "ACCEPT", "review receipt scope or decision")
    protocol._require(receipt["packet_sha256"] == packet_digest, "review receipt packet binding")
    protocol._require(isinstance(receipt["reviewer_identity"], str) and receipt["reviewer_identity"], "reviewer identity")
    protocol._require(receipt["reviewer_identity"] != operator_identity and receipt["operator_identity"] == operator_identity, "reviewer is not independent")
    protocol._require(receipt["reviewer_role"] == REVIEWER_ROLE, "reviewer role")
    protocol._require(receipt["model_execution_authorized"] is False and receipt["assessment_open"] is False, "review receipt scope escalation")
    protocol._require(isinstance(receipt["public_key_hex"], str) and len(receipt["public_key_hex"]) == 64, "review public key")
    protocol._require(isinstance(receipt["signature_hex"], str) and len(receipt["signature_hex"]) == 128, "review signature")
    unsigned = {key: value for key, value in receipt.items() if key not in {"signature_hex", "receipt_sha256"}}
    protocol._require(receipt["receipt_sha256"] == protocol.digest(unsigned), "review receipt digest")
    message = protocol.canonical_bytes({**unsigned, "receipt_sha256": receipt["receipt_sha256"]})
    try:
        from cryptography.exceptions import InvalidSignature
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

        public_key = Ed25519PublicKey.from_public_bytes(bytes.fromhex(receipt["public_key_hex"]))
        public_key.verify(bytes.fromhex(receipt["signature_hex"]), message)
    except ImportError as exc:
        raise protocol.ProtocolError("Ed25519 verifier unavailable") from exc
    except (InvalidSignature, ValueError, TypeError) as exc:
        raise protocol.ProtocolError("review Ed25519 signature cannot be verified") from exc


def write_packet(packet: Mapping[str, Any], output: Path) -> None:
    """Write one pending packet without permitting replacement."""

    if output.exists():
        raise FileExistsError(f"refusing to overwrite review packet: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(packet, ensure_ascii=True, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Write a pending small-RSI independent-review packet.")
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    write_packet(build_packet(manifest), args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
