"""State slice: astral-trace-completeness-native-instrument-v1."""

import sys
import base64
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import protocol
import review_receipt_v1 as receipts


def test_receipt_verifier_rejects_missing_or_self_signed_accept():
    packet = {"protocol": protocol.PROTOCOL_ID, "state_slice": protocol.STATE_SLICE}
    receipt = {
        "protocol": protocol.PROTOCOL_ID,
        "state_slice": protocol.STATE_SLICE,
        "decision": "ACCEPT",
        "scope": protocol.AUTHORIZATION_SCOPE,
        "packet_sha256": receipts.packet_sha256(packet),
        "reviewer_identity": "Shaan Patel",
        "signing_key_identity": "Shaan Patel",
        "signature_algorithm": "Ed25519",
        "public_key_base64": "AA==",
        "signature_base64": "AA==",
        "reviewed_at": "2026-08-30T00:00:00Z",
        "model_execution_authorized": False,
        "assessment_opened": False,
    }
    result = receipts.verify_accept(packet, receipt)
    assert result["valid"] is False
    assert "reviewer_identity" in result["errors"]
    assert "signing_key_identity" in result["errors"]


def test_receipt_packet_binding_is_digest_sensitive():
    packet = {"protocol": protocol.PROTOCOL_ID, "state_slice": protocol.STATE_SLICE}
    changed = {**packet, "claim_ceiling": protocol.CLAIM_CEILING}
    assert receipts.packet_sha256(packet) != receipts.packet_sha256(changed)


def test_invalid_ed25519_signature_is_rejected_fail_closed():
    packet = {"protocol": protocol.PROTOCOL_ID, "state_slice": protocol.STATE_SLICE}
    receipt = {
        "protocol": protocol.PROTOCOL_ID,
        "state_slice": protocol.STATE_SLICE,
        "decision": "ACCEPT",
        "scope": protocol.AUTHORIZATION_SCOPE,
        "packet_sha256": receipts.packet_sha256(packet),
        "reviewer_identity": "Independent Reviewer",
        "signing_key_identity": "independent-key-1",
        "signature_algorithm": "Ed25519",
        "public_key_base64": base64.b64encode(b"\x00" * 32).decode("ascii"),
        "signature_base64": base64.b64encode(b"\x00" * 64).decode("ascii"),
        "reviewed_at": "2026-08-30T00:00:00Z",
        "model_execution_authorized": False,
        "assessment_opened": False,
    }
    result = receipts.verify_accept(packet, receipt)
    assert result["valid"] is False
    assert "signature_invalid" in result["errors"] or "ed25519_verifier_unavailable" in result["errors"]
