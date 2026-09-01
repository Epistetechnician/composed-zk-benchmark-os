"""Deterministic non-semantic fixture corpus for trace accounting V1.

State slice: astral-trace-completeness-native-instrument-v1.

The fixture manifest contains identifiers, counts, and digests only.  It is
not a prompt corpus and cannot be used as model-bearing assessment evidence.
"""

from __future__ import annotations

import hashlib
from typing import Any

import protocol


FIXTURE_SEED = 20260830
FIXTURE_COUNT = 8
FIXTURE_TOKEN_COUNT = 3


def fixture_token_digest(fixture_index: int, token_index: int) -> str:
    if not 0 <= fixture_index < FIXTURE_COUNT or not 0 <= token_index < FIXTURE_TOKEN_COUNT:
        raise protocol.ProtocolError("fixture index is outside the frozen corpus")
    return hashlib.sha256(f"{FIXTURE_SEED}:{fixture_index}:{token_index}".encode("ascii")).hexdigest()


def fixture_manifest() -> list[dict[str, Any]]:
    return [
        {
            "fixture_id": f"fixture-{index:02d}",
            "token_count": FIXTURE_TOKEN_COUNT,
            "token_digests": [fixture_token_digest(index, token) for token in range(FIXTURE_TOKEN_COUNT)],
        }
        for index in range(FIXTURE_COUNT)
    ]


def corpus_digest() -> str:
    return protocol.canonical_digest(
        {
            "corpus_id": protocol.FRESH_CORPUS_ID,
            "seed": FIXTURE_SEED,
            "fixtures": fixture_manifest(),
        }
    )
