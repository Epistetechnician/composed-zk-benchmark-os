"""Fail-closed signed mailbox and independent-verdict contracts.

State slice: aligned-holistic-continual-learning-interpretability-monorepo-v1.

This module implements the communication boundary only. It does not open a
model/provider lane, grant authority, invoke an agent, or provide an SSH
server. SFTP is an external transport for the files produced here.
"""

from __future__ import annotations

import base64
import binascii
import datetime as dt
import hashlib
import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence


PROTOCOL_ID = "independent-review-communication-boundary-v1"
STATE_SLICE = "aligned-holistic-continual-learning-interpretability-monorepo-v1"
MESSAGE_SCHEMA = f"{PROTOCOL_ID}-message"
SEAL_SCHEMA = f"{PROTOCOL_ID}-seal"
VERDICT_SCHEMA = f"{PROTOCOL_ID}-verdict"

CLARIFICATION_PHASE = "CLARIFICATION"
VERDICT_PHASE = "VERDICT"
SEALED_PHASE = "SEALED"
OPERATOR_ROLE = "OPERATOR"
ADVISORY_REVIEWER_ROLE = "ADVISORY_REVIEWER"
FINAL_REVIEWER_ROLE = "FINAL_REVIEWER"
MESSAGE_KINDS = {"QUESTION", "ANSWER"}
DECISIONS = {"ACCEPT", "REJECT"}
SCOPE_FIELDS = (
    "model_execution",
    "provider_calls",
    "raw_trace_access",
    "evidence_ledger_mutation",
)
DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
KEY_ID_RE = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")
TIMESTAMP_RE = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$")


class ProtocolError(ValueError):
    """Raised when a signed-review communication contract is invalid."""


@dataclass(frozen=True)
class TrustedKey:
    """An externally provisioned key-registry entry.

    ``independently_administered`` is a registry assertion, not something the
    local mailbox can prove. The verifier requires it for final verdicts.
    """

    key_id: str
    identity: str
    role: str
    public_key: bytes
    independently_administered: bool = False
    conflict_free: bool = False


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ProtocolError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def load_json_bytes(raw: bytes) -> Any:
    """Parse strict JSON without duplicate keys or non-standard constants."""

    def reject_constant(value: str) -> Any:
        raise ProtocolError(f"non-standard JSON constant: {value}")

    try:
        return json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_reject_duplicate_keys,
            parse_constant=reject_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ProtocolError("invalid UTF-8 JSON") from exc


def canonical_bytes(value: Any) -> bytes:
    """Return the one canonical JSON encoding used for all signatures."""

    try:
        return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise ProtocolError("value is not canonical JSON") from exc


def digest_bytes(value: bytes) -> str:
    return f"sha256:{hashlib.sha256(value).hexdigest()}"


def canonical_digest(value: Any) -> str:
    return digest_bytes(canonical_bytes(value))


def packet_digest_from_json(path: Path) -> str:
    """Digest a packet's strict canonical JSON representation."""

    return canonical_digest(load_json_bytes(_read_regular(path)))


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ProtocolError(message)


def _strict_keys(value: Mapping[str, Any], expected: set[str], label: str) -> None:
    _require(set(value) == expected, f"{label} schema")


def _require_digest(value: Any, label: str) -> str:
    _require(isinstance(value, str) and DIGEST_RE.fullmatch(value) is not None, f"{label} must be sha256:<64 lowercase hex>")
    return value


def _require_key_id(value: Any, label: str) -> str:
    _require(isinstance(value, str) and KEY_ID_RE.fullmatch(value) is not None, f"{label} is invalid")
    return value


def _parse_timestamp(value: Any, label: str) -> dt.datetime:
    _require(isinstance(value, str) and TIMESTAMP_RE.fullmatch(value) is not None, f"{label} timestamp")
    try:
        parsed = dt.datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=dt.timezone.utc)
    except ValueError as exc:
        raise ProtocolError(f"{label} timestamp") from exc
    return parsed


def _decode_base64(value: Any, label: str) -> bytes:
    _require(isinstance(value, str), f"{label} must be base64 text")
    try:
        return base64.b64decode(value.encode("ascii"), validate=True)
    except (UnicodeEncodeError, binascii.Error, ValueError) as exc:
        raise ProtocolError(f"{label} is invalid base64") from exc


def load_private_key(path: Path) -> Any:
    """Load exactly one raw 32-byte Ed25519 private key from an external file."""

    raw = _read_regular(path)
    _require(path.stat().st_mode & 0o077 == 0, "private key file must be owner-only")
    _require(len(raw) == 32, "private key must be exactly 32 raw bytes")
    try:
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

        return Ed25519PrivateKey.from_private_bytes(raw)
    except ImportError as exc:
        raise ProtocolError("Ed25519 runtime unavailable") from exc


def load_registry(path: Path) -> dict[str, TrustedKey]:
    """Load an externally provisioned registry of trusted public keys."""

    value = load_json_bytes(_read_regular(path))
    _require(isinstance(value, Mapping), "key registry object")
    _strict_keys(value, {"schema_version", "keys"}, "key registry")
    _require(value["schema_version"] == f"{PROTOCOL_ID}-key-registry", "key registry schema version")
    _require(isinstance(value["keys"], list), "key registry keys")
    result: dict[str, TrustedKey] = {}
    for item in value["keys"]:
        _require(isinstance(item, Mapping), "key registry entry")
        expected = {
            "key_id",
            "identity",
            "role",
            "public_key_base64",
            "independently_administered",
            "conflict_free",
        }
        _strict_keys(item, expected, "key registry entry")
        key_id = _require_key_id(item["key_id"], "registry key_id")
        _require(key_id not in result, "duplicate registry key_id")
        _require(isinstance(item["identity"], str) and item["identity"], "registry identity")
        role = _require_role(item["role"], "registry")
        public_key = _decode_base64(item["public_key_base64"], "registry public key")
        _require(len(public_key) == 32, "registry public key length")
        _require(isinstance(item["independently_administered"], bool), "registry independence flag")
        _require(isinstance(item["conflict_free"], bool), "registry conflict flag")
        result[key_id] = TrustedKey(
            key_id=key_id,
            identity=item["identity"],
            role=role,
            public_key=public_key,
            independently_administered=item["independently_administered"],
            conflict_free=item["conflict_free"],
        )
    return result


def _locked_scope() -> dict[str, bool]:
    return {field: False for field in SCOPE_FIELDS}


def _validate_scope(value: Any) -> None:
    _require(isinstance(value, Mapping), "message scope")
    _strict_keys(value, set(SCOPE_FIELDS), "message scope")
    _require(all(item is False for item in value.values()), "communication scope escalation")


def _require_role(value: Any, label: str) -> str:
    _require(value in {OPERATOR_ROLE, ADVISORY_REVIEWER_ROLE, FINAL_REVIEWER_ROLE}, f"{label} role")
    return value


def _signature_payload(envelope: Mapping[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in envelope.items() if key != "signature"}


def _verify_ed25519(signature: Mapping[str, Any], payload: bytes, trusted: TrustedKey) -> None:
    _strict_keys(signature, {"algorithm", "public_key_base64", "signature_base64"}, "signature")
    _require(signature["algorithm"] == "Ed25519", "signature algorithm")
    public_key = _decode_base64(signature["public_key_base64"], "signature public key")
    signed_bytes = _decode_base64(signature["signature_base64"], "signature")
    _require(public_key == trusted.public_key and len(public_key) == 32, "signature key is not registry-bound")
    _require(len(signed_bytes) == 64, "signature length")
    try:
        from cryptography.exceptions import InvalidSignature
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

        Ed25519PublicKey.from_public_bytes(public_key).verify(signed_bytes, payload)
    except ImportError as exc:
        raise ProtocolError("Ed25519 verifier unavailable") from exc
    except (InvalidSignature, TypeError, ValueError) as exc:
        raise ProtocolError("signature invalid") from exc


def _verify_registered_signer(envelope: Mapping[str, Any], registry: Mapping[str, TrustedKey], *, role: str) -> TrustedKey:
    key_id = _require_key_id(envelope.get("signing_key_id"), "signing_key_id")
    trusted = registry.get(key_id)
    _require(trusted is not None, "signing key is not in the external registry")
    assert trusted is not None
    _require(trusted.role == role, "signing key role")
    _require(envelope.get("sender_id") == trusted.identity, "sender identity is not registry-bound")
    return trusted


def _verify_message_shape(envelope: Mapping[str, Any]) -> None:
    expected = {
        "schema_version",
        "protocol",
        "state_slice",
        "phase",
        "message_id",
        "packet_digest",
        "parent_message_id",
        "turn",
        "kind",
        "sender_id",
        "sender_role",
        "recipient_role",
        "signing_key_id",
        "created_at",
        "body_digest",
        "scope",
        "signature",
    }
    _strict_keys(envelope, expected, "message")
    _require(envelope["schema_version"] == MESSAGE_SCHEMA, "message schema version")
    _require(envelope["protocol"] == PROTOCOL_ID and envelope["state_slice"] == STATE_SLICE, "message identity")
    _require(envelope["phase"] == CLARIFICATION_PHASE, "message phase")
    _require_digest(envelope["packet_digest"], "packet_digest")
    _require(isinstance(envelope["parent_message_id"], (str, type(None))), "parent_message_id")
    if envelope["parent_message_id"] is not None:
        _require_digest(envelope["parent_message_id"], "parent_message_id")
    _require(isinstance(envelope["turn"], int) and not isinstance(envelope["turn"], bool) and envelope["turn"] >= 0, "message turn")
    _require(envelope["kind"] in MESSAGE_KINDS, "message kind")
    _require(isinstance(envelope["sender_id"], str) and envelope["sender_id"], "sender_id")
    _require_role(envelope["sender_role"], "sender")
    _require_role(envelope["recipient_role"], "recipient")
    _require_key_id(envelope["signing_key_id"], "signing_key_id")
    _parse_timestamp(envelope["created_at"], "created_at")
    _require_digest(envelope["body_digest"], "body_digest")
    _validate_scope(envelope["scope"])
    _require(isinstance(envelope["signature"], Mapping), "message signature")


def sign_message(
    *,
    packet_digest: str,
    parent_message_id: str | None,
    turn: int,
    kind: str,
    sender_id: str,
    sender_role: str,
    recipient_role: str,
    signing_key_id: str,
    created_at: str,
    body: bytes,
    private_key: Any,
) -> dict[str, Any]:
    """Create one signed clarification envelope.

    The private key is supplied by the caller and is never written by this
    module. Only QUESTION/ANSWER messages can be created in this phase.
    """

    _require_digest(packet_digest, "packet_digest")
    _require(isinstance(parent_message_id, (str, type(None))), "parent_message_id")
    if parent_message_id is not None:
        _require_digest(parent_message_id, "parent_message_id")
    _require(isinstance(turn, int) and not isinstance(turn, bool) and turn >= 0, "turn")
    _require(kind in MESSAGE_KINDS, "kind")
    _require(isinstance(sender_id, str) and sender_id, "sender_id")
    _require_role(sender_role, "sender")
    _require_role(recipient_role, "recipient")
    _require_key_id(signing_key_id, "signing_key_id")
    _parse_timestamp(created_at, "created_at")
    _require(isinstance(body, bytes), "body must be bytes")
    _require(sender_role != FINAL_REVIEWER_ROLE, "final reviewer cannot participate in clarification")
    _require(
        (kind, sender_role, recipient_role) in {
            ("QUESTION", ADVISORY_REVIEWER_ROLE, OPERATOR_ROLE),
            ("ANSWER", OPERATOR_ROLE, ADVISORY_REVIEWER_ROLE),
        },
        "message direction",
    )

    unsigned_without_id: dict[str, Any] = {
        "schema_version": MESSAGE_SCHEMA,
        "protocol": PROTOCOL_ID,
        "state_slice": STATE_SLICE,
        "phase": CLARIFICATION_PHASE,
        "packet_digest": packet_digest,
        "parent_message_id": parent_message_id,
        "turn": turn,
        "kind": kind,
        "sender_id": sender_id,
        "sender_role": sender_role,
        "recipient_role": recipient_role,
        "signing_key_id": signing_key_id,
        "created_at": created_at,
        "body_digest": digest_bytes(body),
        "scope": _locked_scope(),
    }
    unsigned = {**unsigned_without_id, "message_id": canonical_digest(unsigned_without_id)}
    _require(hasattr(private_key, "sign") and hasattr(private_key, "public_key"), "Ed25519 private key")
    try:
        public_key = private_key.public_key().public_bytes_raw()
        signature = private_key.sign(canonical_bytes(unsigned))
    except AttributeError as exc:
        raise ProtocolError("Ed25519 runtime lacks raw public-key export") from exc
    envelope = {
        **unsigned,
        "signature": {
            "algorithm": "Ed25519",
            "public_key_base64": base64.b64encode(public_key).decode("ascii"),
            "signature_base64": base64.b64encode(signature).decode("ascii"),
        },
    }
    _verify_message_shape(envelope)
    return envelope


def verify_message(
    envelope: Mapping[str, Any],
    *,
    body: bytes | None,
    registry: Mapping[str, TrustedKey],
    expected_packet_digest: str,
) -> TrustedKey:
    """Verify one envelope, its body digest, and its external key binding."""

    _verify_message_shape(envelope)
    _require(envelope["packet_digest"] == expected_packet_digest, "message packet binding")
    if body is not None:
        _require(digest_bytes(body) == envelope["body_digest"], "message body binding")
    unsigned = _signature_payload(envelope)
    without_id = {key: value for key, value in unsigned.items() if key != "message_id"}
    _require(unsigned["message_id"] == canonical_digest(without_id), "message id binding")
    role = envelope["sender_role"]
    _require(role in {OPERATOR_ROLE, ADVISORY_REVIEWER_ROLE}, "clarification sender role")
    trusted = _verify_registered_signer(envelope, registry, role=role)
    _verify_ed25519(envelope["signature"], canonical_bytes(unsigned), trusted)
    return trusted


def validate_clarification_log(
    messages: Sequence[Mapping[str, Any]],
    *,
    packet_digest: str,
    max_messages: int,
    deadline: str,
    registry: Mapping[str, TrustedKey],
    bodies: Mapping[str, bytes] | None = None,
) -> None:
    """Validate a contiguous, alternating, bounded clarification transcript."""

    _require_digest(packet_digest, "packet_digest")
    _require(isinstance(max_messages, int) and not isinstance(max_messages, bool) and 1 <= max_messages <= 128, "max_messages")
    deadline_dt = _parse_timestamp(deadline, "deadline")
    _require(len(messages) <= max_messages, "clarification message limit")
    if bodies is not None:
        _require(isinstance(bodies, Mapping), "clarification bodies")
    seen: set[str] = set()
    previous: Mapping[str, Any] | None = None
    for expected_turn, message in enumerate(messages):
        _require(isinstance(message, Mapping), "clarification message")
        if bodies is None:
            body = None
        else:
            message_id = str(message.get("message_id"))
            _require(message_id in bodies, "clarification body missing")
            body = bodies[message_id]
            _require(isinstance(body, bytes), "clarification body must be bytes")
        verify_message(message, body=body, registry=registry, expected_packet_digest=packet_digest)
        _require(message["turn"] == expected_turn, "clarification turns must be contiguous and ordered")
        message_id = message["message_id"]
        _require(message_id not in seen, "duplicate clarification message")
        seen.add(message_id)
        if previous is None:
            _require(message["parent_message_id"] is None, "first clarification message must have no parent")
        else:
            _require(message["parent_message_id"] == previous["message_id"], "clarification parent link")
            _require(
                _parse_timestamp(previous["created_at"], "created_at") <= _parse_timestamp(message["created_at"], "created_at"),
                "clarification timestamps must be monotone",
            )
        if expected_turn % 2 == 0:
            _require(
                message["kind"] == "QUESTION"
                and message["sender_role"] == ADVISORY_REVIEWER_ROLE
                and message["recipient_role"] == OPERATOR_ROLE,
                "clarification question direction",
            )
        else:
            _require(
                message["kind"] == "ANSWER"
                and message["sender_role"] == OPERATOR_ROLE
                and message["recipient_role"] == ADVISORY_REVIEWER_ROLE,
                "clarification answer direction",
            )
        _require(_parse_timestamp(message["created_at"], "created_at") <= deadline_dt, "clarification deadline exceeded")
        previous = message


def _transcript_digest(messages: Sequence[Mapping[str, Any]]) -> str:
    return canonical_digest(list(messages))


def seal_clarifications(
    messages: Sequence[Mapping[str, Any]],
    *,
    packet_digest: str,
    max_messages: int,
    deadline: str,
    claim_ceiling: str,
    operator_identity: str,
    operator_key_id: str,
    registry: Mapping[str, TrustedKey],
    bodies: Mapping[str, bytes],
    sealed_at: str,
) -> dict[str, Any]:
    """Seal a clarification log into the digest reviewed by the final reviewer."""

    _require(isinstance(claim_ceiling, str) and claim_ceiling, "claim_ceiling")
    _require(isinstance(operator_identity, str) and operator_identity, "operator_identity")
    _require_key_id(operator_key_id, "operator_key_id")
    _parse_timestamp(sealed_at, "sealed_at")
    validate_clarification_log(
        messages,
        packet_digest=packet_digest,
        max_messages=max_messages,
        deadline=deadline,
        registry=registry,
        bodies=bodies,
    )
    transcript_digest = _transcript_digest(messages)
    body = {
        "schema_version": SEAL_SCHEMA,
        "protocol": PROTOCOL_ID,
        "state_slice": STATE_SLICE,
        "phase": SEALED_PHASE,
        "packet_digest": packet_digest,
        "clarification_transcript_sha256": transcript_digest,
        "message_count": len(messages),
        "last_message_id": messages[-1]["message_id"] if messages else None,
        "max_messages": max_messages,
        "deadline": deadline,
        "sealed_at": sealed_at,
        "claim_ceiling": claim_ceiling,
        "operator_identity": operator_identity,
        "operator_key_id": operator_key_id,
        "communication_closed": True,
        "execution_enabled": False,
        "provider_calls": False,
        "raw_trace_access": False,
        "evidence_ledger_mutation": False,
    }
    return {**body, "sealed_packet_sha256": canonical_digest(body)}


def verify_seal(seal: Mapping[str, Any], messages: Sequence[Mapping[str, Any]]) -> None:
    """Verify the sealed digest and reject any post-seal transcript change."""

    expected = {
        "schema_version",
        "protocol",
        "state_slice",
        "phase",
        "packet_digest",
        "clarification_transcript_sha256",
        "message_count",
        "last_message_id",
        "max_messages",
        "deadline",
        "sealed_at",
        "claim_ceiling",
        "operator_identity",
        "operator_key_id",
        "communication_closed",
        "execution_enabled",
        "provider_calls",
        "raw_trace_access",
        "evidence_ledger_mutation",
        "sealed_packet_sha256",
    }
    _strict_keys(seal, expected, "seal")
    _require(seal["schema_version"] == SEAL_SCHEMA, "seal schema version")
    _require(seal["protocol"] == PROTOCOL_ID and seal["state_slice"] == STATE_SLICE, "seal identity")
    _require(seal["phase"] == SEALED_PHASE and seal["communication_closed"] is True, "seal phase")
    _require_digest(seal["packet_digest"], "seal packet digest")
    _require(seal["message_count"] == len(messages), "seal message count")
    _require(seal["clarification_transcript_sha256"] == _transcript_digest(messages), "sealed transcript digest")
    _require(seal["last_message_id"] == (messages[-1]["message_id"] if messages else None), "seal last message")
    _require(seal["execution_enabled"] is False, "seal execution scope")
    _require(seal["provider_calls"] is False, "seal provider scope")
    _require(seal["raw_trace_access"] is False, "seal raw scope")
    _require(seal["evidence_ledger_mutation"] is False, "seal ledger scope")
    body = {key: value for key, value in seal.items() if key != "sealed_packet_sha256"}
    _require(seal["sealed_packet_sha256"] == canonical_digest(body), "sealed packet digest")


def sign_verdict(
    seal: Mapping[str, Any],
    *,
    messages: Sequence[Mapping[str, Any]],
    bodies: Mapping[str, bytes],
    registry: Mapping[str, TrustedKey],
    decision: str,
    reviewer_identity: str,
    signing_key_id: str,
    conflict_of_interest: bool,
    reviewed_at: str,
    private_key: Any,
) -> dict[str, Any]:
    """Create the only signed artifact permitted after the seal: ACCEPT/REJECT."""

    _require(decision in DECISIONS, "verdict decision")
    _require(isinstance(reviewer_identity, str) and reviewer_identity, "reviewer_identity")
    _require_key_id(signing_key_id, "signing_key_id")
    _parse_timestamp(reviewed_at, "reviewed_at")
    _require(conflict_of_interest is False, "reviewer conflict of interest")
    _require(seal.get("phase") == SEALED_PHASE, "verdict requires sealed packet")
    verify_seal(seal, messages)
    validate_clarification_log(
        messages,
        packet_digest=seal["packet_digest"],
        max_messages=seal["max_messages"],
        deadline=seal["deadline"],
        registry=registry,
        bodies=bodies,
    )
    _require(reviewer_identity != seal.get("operator_identity"), "reviewer cannot be operator")
    _require(signing_key_id != seal.get("operator_key_id"), "reviewer key cannot be operator key")
    unsigned = {
        "schema_version": VERDICT_SCHEMA,
        "protocol": PROTOCOL_ID,
        "state_slice": STATE_SLICE,
        "phase": VERDICT_PHASE,
        "sealed_packet_sha256": seal["sealed_packet_sha256"],
        "packet_digest": seal["packet_digest"],
        "clarification_transcript_sha256": seal["clarification_transcript_sha256"],
        "decision": decision,
        "claim_ceiling": seal["claim_ceiling"],
        "reviewer_identity": reviewer_identity,
        "reviewer_role": FINAL_REVIEWER_ROLE,
        "signing_key_id": signing_key_id,
        "conflict_of_interest": False,
        "review_mode": "fresh_process_after_seal",
        "review_interaction_closed": True,
        "reviewed_at": reviewed_at,
        "execution_enabled": False,
        "model_execution_authorized": False,
        "assessment_opened": False,
    }
    _require(hasattr(private_key, "sign") and hasattr(private_key, "public_key"), "Ed25519 private key")
    try:
        public_key = private_key.public_key().public_bytes_raw()
        signature = private_key.sign(canonical_bytes(unsigned))
    except AttributeError as exc:
        raise ProtocolError("Ed25519 runtime lacks raw public-key export") from exc
    return {
        **unsigned,
        "signature": {
            "algorithm": "Ed25519",
            "public_key_base64": base64.b64encode(public_key).decode("ascii"),
            "signature_base64": base64.b64encode(signature).decode("ascii"),
        },
    }


def verify_verdict(
    verdict: Mapping[str, Any],
    *,
    seal: Mapping[str, Any],
    messages: Sequence[Mapping[str, Any]],
    bodies: Mapping[str, bytes],
    registry: Mapping[str, TrustedKey],
) -> TrustedKey:
    """Verify one final verdict without treating it as execution authority."""

    verify_seal(seal, messages)
    validate_clarification_log(
        messages,
        packet_digest=seal["packet_digest"],
        max_messages=seal["max_messages"],
        deadline=seal["deadline"],
        registry=registry,
        bodies=bodies,
    )
    expected = {
        "schema_version",
        "protocol",
        "state_slice",
        "phase",
        "sealed_packet_sha256",
        "packet_digest",
        "clarification_transcript_sha256",
        "decision",
        "claim_ceiling",
        "reviewer_identity",
        "reviewer_role",
        "signing_key_id",
        "conflict_of_interest",
        "review_mode",
        "review_interaction_closed",
        "reviewed_at",
        "execution_enabled",
        "model_execution_authorized",
        "assessment_opened",
        "signature",
    }
    _strict_keys(verdict, expected, "verdict")
    _require(verdict["schema_version"] == VERDICT_SCHEMA, "verdict schema version")
    _require(verdict["protocol"] == PROTOCOL_ID and verdict["state_slice"] == STATE_SLICE, "verdict identity")
    _require(verdict["phase"] == VERDICT_PHASE and verdict["decision"] in DECISIONS, "verdict phase or decision")
    _require(verdict["sealed_packet_sha256"] == seal["sealed_packet_sha256"], "verdict sealed-packet binding")
    _require(verdict["packet_digest"] == seal["packet_digest"], "verdict packet binding")
    _require(verdict["clarification_transcript_sha256"] == seal["clarification_transcript_sha256"], "verdict transcript binding")
    _require(verdict["claim_ceiling"] == seal["claim_ceiling"], "verdict claim ceiling binding")
    _require(verdict["reviewer_role"] == FINAL_REVIEWER_ROLE, "verdict reviewer role")
    _require(verdict["reviewer_identity"] != seal["operator_identity"], "verdict reviewer independence")
    _require(verdict["signing_key_id"] != seal["operator_key_id"], "verdict signing-key independence")
    _require(verdict["conflict_of_interest"] is False, "verdict conflict of interest")
    _require(verdict["review_mode"] == "fresh_process_after_seal", "verdict review mode")
    _require(verdict["review_interaction_closed"] is True, "verdict interaction state")
    _require(verdict["execution_enabled"] is False, "verdict execution scope")
    _require(verdict["model_execution_authorized"] is False, "verdict model scope")
    _require(verdict["assessment_opened"] is False, "verdict assessment scope")
    _parse_timestamp(verdict["reviewed_at"], "reviewed_at")
    key_id = _require_key_id(verdict["signing_key_id"], "verdict signing_key_id")
    trusted = registry.get(key_id)
    _require(trusted is not None, "verdict key is not in the external registry")
    assert trusted is not None
    _require(trusted.role == FINAL_REVIEWER_ROLE, "verdict key role")
    _require(trusted.identity == verdict["reviewer_identity"], "verdict reviewer identity")
    _require(trusted.independently_administered and trusted.conflict_free, "verdict reviewer is not externally independent")
    _verify_ed25519(verdict["signature"], canonical_bytes({key: value for key, value in verdict.items() if key != "signature"}), trusted)
    return trusted


def _write_exclusive(path: Path, raw: bytes, *, mode: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        fd = os.open(path, flags, mode)
    except FileExistsError as exc:
        raise ProtocolError(f"refusing to overwrite immutable file: {path}") from exc
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(raw)
            handle.flush()
            os.fsync(handle.fileno())
    except BaseException:
        try:
            path.unlink()
        except OSError:
            pass
        raise


def _read_regular(path: Path) -> bytes:
    _require(not path.is_symlink() and path.is_file(), f"mailbox path is not a regular file: {path.name}")
    return path.read_bytes()


class FileMailbox:
    """A local append-only mailbox suitable for SFTP file exchange.

    The mailbox stores envelopes and body bytes in separate immutable files.
    It does not run SFTP. The transport operator must close the SFTP ACL before
    the seal is handed to the final reviewer.
    """

    def __init__(
        self,
        root: Path,
        *,
        packet_digest: str,
        max_messages: int,
        deadline: str,
        registry: Mapping[str, TrustedKey],
    ) -> None:
        _require_digest(packet_digest, "packet_digest")
        _require(isinstance(max_messages, int) and not isinstance(max_messages, bool) and 1 <= max_messages <= 128, "max_messages")
        _parse_timestamp(deadline, "deadline")
        self.root = Path(root)
        self.messages_dir = self.root / "messages"
        self.bodies_dir = self.root / "bodies"
        self.seal_path = self.root / "seal.json"
        self.packet_digest = packet_digest
        self.max_messages = max_messages
        self.deadline = deadline
        self.registry = registry
        if self.root.exists():
            _require(not self.root.is_symlink(), "mailbox root symlink")
        if self.messages_dir.exists():
            _require(not self.messages_dir.is_symlink(), "mailbox messages directory symlink")
        if self.bodies_dir.exists():
            _require(not self.bodies_dir.is_symlink(), "mailbox bodies directory symlink")
        self.root.mkdir(parents=True, exist_ok=True)
        self.messages_dir.mkdir(parents=True, exist_ok=True)
        self.bodies_dir.mkdir(parents=True, exist_ok=True)
        self.root.chmod(0o700)
        self.messages_dir.chmod(0o700)
        self.bodies_dir.chmod(0o700)
        _require(not self.root.is_symlink() and not self.messages_dir.is_symlink() and not self.bodies_dir.is_symlink(), "mailbox directory symlink")

    def _message_paths(self) -> list[Path]:
        paths = sorted(self.messages_dir.iterdir(), key=lambda item: item.name)
        _require(all(path.suffix == ".json" for path in paths), "unexpected mailbox message path")
        return paths

    def read(self) -> tuple[list[dict[str, Any]], dict[str, bytes]]:
        messages: list[dict[str, Any]] = []
        bodies: dict[str, bytes] = {}
        for path in self._message_paths():
            value = load_json_bytes(_read_regular(path))
            _require(isinstance(value, Mapping), "mailbox message object")
            message_id = value.get("message_id")
            _require(isinstance(message_id, str), "mailbox message id")
            _require(path.name == f"{value['turn']:04d}-{message_id.removeprefix('sha256:')}.json", "mailbox message filename binding")
            body_path = self.bodies_dir / f"{message_id.removeprefix('sha256:')}.bin"
            body = _read_regular(body_path)
            bodies[message_id] = body
            messages.append(dict(value))
        validate_clarification_log(
            messages,
            packet_digest=self.packet_digest,
            max_messages=self.max_messages,
            deadline=self.deadline,
            registry=self.registry,
            bodies=bodies,
        )
        expected_body_names = {f"{message_id.removeprefix('sha256:')}.bin" for message_id in bodies}
        actual_body_names = {path.name for path in self.bodies_dir.iterdir()}
        _require(actual_body_names == expected_body_names, "mailbox body set is not closed")
        return messages, bodies

    def append(self, envelope: Mapping[str, Any], body: bytes) -> None:
        """Append one signed message exactly once, rejecting writes after seal."""

        _require(not self.seal_path.exists(), "mailbox is sealed")
        messages, bodies = self.read()
        verify_message(envelope, body=body, registry=self.registry, expected_packet_digest=self.packet_digest)
        candidate = [*messages, envelope]
        validate_clarification_log(
            candidate,
            packet_digest=self.packet_digest,
            max_messages=self.max_messages,
            deadline=self.deadline,
            registry=self.registry,
            bodies={**bodies, envelope["message_id"]: body},
        )
        message_id = envelope["message_id"]
        _require(isinstance(message_id, str) and message_id.startswith("sha256:"), "message id")
        body_path = self.bodies_dir / f"{message_id.removeprefix('sha256:')}.bin"
        message_path = self.messages_dir / f"{len(messages):04d}-{message_id.removeprefix('sha256:')}.json"
        _write_exclusive(body_path, body, mode=0o600)
        try:
            _write_exclusive(message_path, (json.dumps(dict(envelope), ensure_ascii=True, sort_keys=True, indent=2) + "\n").encode("utf-8"), mode=0o600)
        except BaseException:
            try:
                body_path.unlink()
            except OSError:
                pass
            raise

    def seal(
        self,
        *,
        claim_ceiling: str,
        operator_identity: str,
        operator_key_id: str,
        sealed_at: str,
    ) -> dict[str, Any]:
        """Close the mailbox and write an exclusive seal artifact."""

        _require(not self.seal_path.exists(), "mailbox is already sealed")
        messages, bodies = self.read()
        seal = seal_clarifications(
            messages,
            packet_digest=self.packet_digest,
            max_messages=self.max_messages,
            deadline=self.deadline,
            claim_ceiling=claim_ceiling,
            operator_identity=operator_identity,
            operator_key_id=operator_key_id,
            registry=self.registry,
            bodies=bodies,
            sealed_at=sealed_at,
        )
        _write_exclusive(self.seal_path, (json.dumps(seal, ensure_ascii=True, sort_keys=True, indent=2) + "\n").encode("utf-8"), mode=0o600)
        return seal

    def read_seal(self) -> dict[str, Any]:
        """Read and verify the seal against the current closed mailbox."""

        _require(self.seal_path.exists(), "mailbox is not sealed")
        value = load_json_bytes(_read_regular(self.seal_path))
        _require(isinstance(value, Mapping), "seal object")
        messages, _ = self.read()
        verify_seal(value, messages)
        return dict(value)
