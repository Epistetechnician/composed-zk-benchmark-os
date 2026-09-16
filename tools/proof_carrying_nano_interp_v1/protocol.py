"""Canonical serialization and digest helpers for the V1 contract.

State slice: proof-carrying-nano-interp-v1.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any


STATE_SLICE = "proof-carrying-nano-interp-v1"
PROTOCOL_ID = "proof-carrying-nano-interp-v1"


class ProtocolError(ValueError):
    """Raised when a V1 record violates its closed-world contract."""


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ProtocolError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def load_json_bytes(raw: bytes) -> Any:
    """Decode JSON while rejecting duplicate keys before mapping collapse."""

    try:
        return json.loads(raw.decode("utf-8"), object_pairs_hook=_reject_duplicate_keys)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ProtocolError("invalid JSON") from exc


def canonical_bytes(value: Any) -> bytes:
    """Return the deterministic UTF-8 JSON representation used for identity."""

    try:
        return json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise ProtocolError("value is not canonicalizable JSON") from exc


def digest_bytes(raw: bytes) -> str:
    return f"sha256:{hashlib.sha256(raw).hexdigest()}"


def canonical_digest(value: Any) -> str:
    return digest_bytes(canonical_bytes(value))
