"""Bounded signed communication for independent-review handoffs.

State slice: aligned-holistic-continual-learning-interpretability-monorepo-v1.
"""

from .protocol import (
    ADVISORY_REVIEWER_ROLE,
    FINAL_REVIEWER_ROLE,
    OPERATOR_ROLE,
    PROTOCOL_ID,
    STATE_SLICE,
    FileMailbox,
    ProtocolError,
    TrustedKey,
    load_private_key,
    load_registry,
    packet_digest_from_json,
    seal_clarifications,
    sign_message,
    sign_verdict,
    validate_clarification_log,
    verify_message,
    verify_seal,
    verify_verdict,
)

__all__ = [
    "ADVISORY_REVIEWER_ROLE",
    "FINAL_REVIEWER_ROLE",
    "OPERATOR_ROLE",
    "PROTOCOL_ID",
    "STATE_SLICE",
    "FileMailbox",
    "ProtocolError",
    "TrustedKey",
    "load_private_key",
    "load_registry",
    "packet_digest_from_json",
    "seal_clarifications",
    "sign_message",
    "sign_verdict",
    "validate_clarification_log",
    "verify_message",
    "verify_seal",
    "verify_verdict",
]
