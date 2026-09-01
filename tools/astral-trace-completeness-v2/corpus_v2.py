"""Deterministic fresh prompt-family generator for V2.

State slice: astral-trace-completeness-gemma3-end-to-end-v2.
"""

from __future__ import annotations

import dataclasses
import random
from typing import Any

import protocol_v2 as protocol


SEED = 20260830
FAMILY_COUNT = 48
SPLIT_SIZE = 16
VARIANTS = (
    "clean",
    "corrupted",
    "exact_copy_noop",
    "shuffled",
    "constant",
    "matched_norm",
    "activation_only",
    "text_only",
    "access_null",
)


@dataclasses.dataclass(frozen=True)
class PromptFamily:
    family_id: str
    split: str
    left: int
    right: int
    operation: str

    def prompt(self, variant: str = "clean") -> str:
        if variant not in VARIANTS:
            raise protocol.ProtocolError(f"unknown corpus variant: {variant}")
        operator = "+" if self.operation == "sum" else "-"
        if variant in {"corrupted", "text_only"}:
            operator = "-" if operator == "+" else "+"
        return f"Compute exactly. {self.left} {operator} {self.right} ="

    def answer(self, variant: str = "clean") -> int:
        if variant in {"corrupted", "text_only"}:
            return self.left - self.right if self.operation == "sum" else self.left + self.right
        return self.left + self.right if self.operation == "sum" else self.left - self.right

    def public_identity(self) -> dict[str, Any]:
        return {"family_id": self.family_id, "split": self.split, "spec_sha256": protocol.digest_json(dataclasses.asdict(self))}


def families() -> tuple[PromptFamily, ...]:
    rng = random.Random(SEED)
    values = []
    for index in range(FAMILY_COUNT):
        operation = "sum" if index % 2 == 0 else "difference"
        left = rng.randrange(20, 90)
        right = rng.randrange(2, 19)
        if operation == "difference" and right >= left:
            left, right = right + 20, left % 19 + 1
        split = "fit" if index < SPLIT_SIZE else "tune" if index < 2 * SPLIT_SIZE else "assessment"
        values.append(PromptFamily(f"family-{index:03d}", split, left, right, operation))
    return tuple(values)


def public_manifest() -> dict[str, Any]:
    value = {
        "protocol": protocol.PROTOCOL_ID,
        "state_slice": protocol.STATE_SLICE,
        "corpus_id": protocol.CORPUS_ID,
        "seed": SEED,
        "family_count": FAMILY_COUNT,
        "split_counts": {"fit": SPLIT_SIZE, "tune": SPLIT_SIZE, "assessment": SPLIT_SIZE},
        "variants": list(VARIANTS),
        "families": [family.public_identity() for family in families()],
    }
    return {**value, "manifest_sha256": protocol.digest_json(value)}

