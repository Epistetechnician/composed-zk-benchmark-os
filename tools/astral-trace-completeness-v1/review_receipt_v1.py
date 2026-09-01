"""Verify an independent signed ACCEPT receipt for trace completeness V1.

State slice: astral-trace-completeness-native-instrument-v1.

This module verifies a receipt; it never creates one. A receipt is valid only
for the contract-and-hermetic-fixture scope and cannot silently authorize
model-bearing assessment.
"""

from __future__ import annotations

import base64
import binascii
from typing import Any, Mapping

import protocol


RECEIPT_FIELDS = {
    "protocol",
    "state_slice",
    "decision",
    "scope",
    "packet_sha256",
    "reviewer_identity",
    "signing_key_identity",
    "signature_algorithm",
    "public_key_base64",
    "signature_base64",
    "reviewed_at",
    "model_execution_authorized",
    "assessment_opened",
}


def packet_sha256(packet: Mapping[str, Any]) -> str:
    return protocol.canonical_digest(packet)


def _decode(value: Any, field_name: str) -> bytes:
    if not isinstance(value, str):
        raise protocol.ProtocolError(f"{field_name} must be base64 text")
    try:
        return base64.b64decode(value.encode("ascii"), validate=True)
    except (ValueError, UnicodeEncodeError, binascii.Error) as exc:
        raise protocol.ProtocolError(f"{field_name} is not valid base64") from exc


def verify_accept(packet: Mapping[str, Any], receipt: Mapping[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    if packet.get("status") != "READY_FOR_INDEPENDENT_REVIEW":
        errors.append("packet_not_ready")
    if packet.get("missing_required_fields"):
        errors.append("packet_has_missing_required_fields")
    if packet.get("execution_authorized") is not False or packet.get("assessment_opened") is not False:
        errors.append("packet_scope_escalation")
    if set(receipt) != RECEIPT_FIELDS:
        errors.append("receipt_schema")
    if receipt.get("protocol") != protocol.PROTOCOL_ID or receipt.get("state_slice") != protocol.STATE_SLICE:
        errors.append("receipt_identity")
    if receipt.get("decision") != "ACCEPT":
        errors.append("decision_not_accept")
    if receipt.get("scope") != protocol.AUTHORIZATION_SCOPE:
        errors.append("scope_mismatch")
    if receipt.get("packet_sha256") != packet_sha256(packet):
        errors.append("packet_binding")
    if not receipt.get("reviewer_identity") or receipt.get("reviewer_identity") == "Shaan Patel":
        errors.append("reviewer_identity")
    if not receipt.get("signing_key_identity") or receipt.get("signing_key_identity") == "Shaan Patel":
        errors.append("signing_key_identity")
    if receipt.get("model_execution_authorized") is not False or receipt.get("assessment_opened") is not False:
        errors.append("scope_escalation")
    try:
        public_key = _decode(receipt["public_key_base64"], "public_key_base64")
        signature = _decode(receipt["signature_base64"], "signature_base64")
    except (KeyError, protocol.ProtocolError) as exc:
        errors.append(str(exc))
    else:
        if receipt.get("signature_algorithm") != "Ed25519":
            errors.append("signature_algorithm")
        elif len(public_key) != 32 or len(signature) != 64:
            errors.append("signature_length")
        else:
            try:
                from cryptography.exceptions import InvalidSignature
                from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

                Ed25519PublicKey.from_public_bytes(public_key).verify(signature, packet_sha256(packet).encode("ascii"))
            except ImportError:
                errors.append("ed25519_verifier_unavailable")
            except (InvalidSignature, ValueError, TypeError):
                errors.append("signature_invalid")
    return {
        "protocol": protocol.PROTOCOL_ID,
        "state_slice": protocol.STATE_SLICE,
        "decision": receipt.get("decision"),
        "valid": not errors,
        "errors": sorted(set(errors)),
        "model_execution_authorized": False,
        "assessment_opened": False,
    }
