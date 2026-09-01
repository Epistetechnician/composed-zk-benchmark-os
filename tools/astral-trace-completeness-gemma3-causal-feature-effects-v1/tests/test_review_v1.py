"""State slice: astral-trace-completeness-gemma3-causal-feature-effects-v1."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))

import protocol_v1 as protocol
import review_v1 as review


def test_packet_is_bound_and_missing_external_authority_rejects(tmp_path):
    packet = review.packet(Path(__file__).parents[3])
    assert packet["packet_sha256"] == protocol.digest_json(
        {key: value for key, value in packet.items() if key != "packet_sha256"}
    )
    result = review.static_review(
        packet,
        node_receipt=None,
        spend_ceiling_usd=None,
        reviewer_receipt=None,
        custody_root=tmp_path,
    )
    assert result["verdict"] == "REJECT"
    assert {finding["id"] for finding in result["findings"]} == {
        "V1-NODE-001",
        "V1-COST-001",
        "V1-BINDING-001",
        "V1-REVIEW-001",
    }


def test_operator_receipt_cannot_be_independent_accept():
    receipt = {
        "protocol": protocol.PROTOCOL_ID,
        "state_slice": protocol.STATE_SLICE,
        "verdict": "ACCEPT",
        "reviewer_role": protocol.OPERATOR_ID,
        "packet_sha256": "0" * 64,
        "signature": {
            "algorithm": "ed25519",
            "public_key_hex": "0" * 64,
            "signature_hex": "0" * 128,
        },
    }
    try:
        review.validate_signed_acceptance(receipt, "0" * 64)
    except protocol.ProtocolError as exc:
        assert "independent" in str(exc)
    else:
        raise AssertionError("operator receipt was incorrectly accepted")


def test_packet_identity_is_stable_across_checkout_roots(tmp_path):
    first = review.packet(tmp_path / "checkout-one")
    second = review.packet(tmp_path / "checkout-two")
    assert first == second


def test_custody_root_requires_the_frozen_state_slice_name(tmp_path):
    root = tmp_path / "wrong-custody-name"
    root.mkdir(mode=0o700)
    for name in protocol.SUBROOTS:
        (root / name).mkdir(mode=0o700)
    receipt = protocol.custody_receipt(root, tmp_path / "repository")
    assert not receipt["valid"]
    assert "custody_root_name" in receipt["errors"]


def test_signed_acceptance_requires_valid_ed25519_message():
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key().public_bytes_raw().hex()
    unsigned = {
        "protocol": protocol.PROTOCOL_ID,
        "state_slice": protocol.STATE_SLICE,
        "verdict": "ACCEPT",
        "reviewer_role": protocol.REVIEWER_ROLE,
        "operator": protocol.OPERATOR_ID,
        "claim_ceiling": protocol.QUALIFICATION_CEILING,
        "packet_sha256": "1" * 64,
    }
    receipt_sha = protocol.digest_json(unsigned)
    message = protocol.canonical_bytes({**unsigned, "receipt_sha256": receipt_sha})
    receipt = {
        **unsigned,
        "receipt_sha256": receipt_sha,
        "signature": {
            "algorithm": "ed25519",
            "public_key_hex": public_key,
            "signature_hex": private_key.sign(message).hex(),
        },
    }
    review.validate_signed_acceptance(receipt, "1" * 64)
