"""Fresh deterministic prompt-family roster for the causal feature slice.

State slice: astral-trace-completeness-gemma3-causal-feature-effects-v2.
Raw prompt strings are generated only in memory by ``PromptFamily.prompt``;
the public manifest contains identities and digests, not prompt text.
"""

from __future__ import annotations

import dataclasses
import random
from typing import Any

import protocol_v2_slice as protocol


VARIANTS = ("clean", "corrupted", "text_only")
PROMPT_TEMPLATES = (
    "Compute exactly. {left} {operator} {right} =",
    "Calculate exactly. {left} {operator} {right} =",
    "Evaluate exactly. {left} {operator} {right} =",
    "Return only the result. {left} {operator} {right} =",
)


@dataclasses.dataclass(frozen=True)
class PromptFamily:
    family_id: str
    split: str
    template_index: int
    left: int
    right: int
    operation: str

    def prompt(self, variant: str = "clean") -> str:
        if variant not in VARIANTS:
            raise protocol.ProtocolError(f"unknown V2 corpus variant: {variant}")
        operator = "+" if self.operation == "sum" else "-"
        if variant in {"corrupted", "text_only"}:
            operator = "-" if operator == "+" else "+"
        try:
            template = PROMPT_TEMPLATES[self.template_index]
        except IndexError as exc:
            raise protocol.ProtocolError("V2 prompt template index is outside the frozen corpus") from exc
        return template.format(left=self.left, operator=operator, right=self.right)

    def answer(self, variant: str = "clean") -> int:
        if variant in {"corrupted", "text_only"}:
            return self.left - self.right if self.operation == "sum" else self.left + self.right
        return self.left + self.right if self.operation == "sum" else self.left - self.right

    def public_identity(self) -> dict[str, Any]:
        value = {
            "family_id": self.family_id,
            "split": self.split,
            "spec_sha256": protocol.digest_json(dataclasses.asdict(self)),
        }
        return value


def families() -> tuple[PromptFamily, ...]:
    rng = random.Random(protocol.CORPUS_SEED)
    token_safe_pairs = [
        (left, right, operation)
        for operation in ("sum", "difference")
        for left in range(1, 9)
        for right in range(1, 9)
        if 0 <= (left + right if operation == "sum" else left - right) <= 9
        and 0 <= (left - right if operation == "sum" else left + right) <= 9
        and (left + right if operation == "sum" else left - right)
        != (left - right if operation == "sum" else left + right)
    ]
    roster = [
        (template_index, left, right, operation)
        for template_index in range(len(PROMPT_TEMPLATES))
        for left, right, operation in token_safe_pairs
    ]
    rng.shuffle(roster)
    if len(roster) < protocol.FAMILY_COUNT:
        raise protocol.ProtocolError("token-safe V2 corpus roster is smaller than the frozen family count")
    result: list[PromptFamily] = []
    for index in range(protocol.FAMILY_COUNT):
        template_index, left, right, operation = roster[index]
        split = (
            "fit"
            if index < protocol.SPLIT_SIZE
            else "tune"
            if index < 2 * protocol.SPLIT_SIZE
            else "assessment"
        )
        result.append(PromptFamily(f"v2-family-{index:03d}", split, template_index, left, right, operation))
    return tuple(result)


def arm_order(family_id: str) -> tuple[str, ...]:
    """Return the fixed assignment order for one family.

    The natural arm is first because every paired effect needs a baseline
    captured before any donor is constructed. The remaining declared arms are
    deterministically permuted from the frozen corpus seed and family ID.
    """

    if not any(family.family_id == family_id for family in families()):
        raise protocol.ProtocolError("unknown V2 family ID")
    suffix = family_id.rsplit("-", 1)[-1]
    rng = random.Random(protocol.CORPUS_SEED + int(suffix))
    remaining = [kind for kind in protocol.INTERVENTION_KINDS if kind != "natural"]
    rng.shuffle(remaining)
    return ("natural", *remaining)


def public_manifest() -> dict[str, Any]:
    value = {
        "protocol": protocol.PROTOCOL_ID,
        "state_slice": protocol.STATE_SLICE,
        "corpus_id": protocol.CORPUS_ID,
        "seed": protocol.CORPUS_SEED,
        "family_count": protocol.FAMILY_COUNT,
        "split_counts": {
            "fit": protocol.SPLIT_SIZE,
            "tune": protocol.SPLIT_SIZE,
            "assessment": protocol.SPLIT_SIZE,
        },
        "variants": list(VARIANTS),
        "answer_token_contract": "clean and corrupted decimal answers are distinct values in 0..9; the bound Gemma tokenizer must encode each as one token",
        "prompt_templates": list(PROMPT_TEMPLATES),
        "feature_stability": {
            "discovery_half_family_ids": [family.family_id for family in families()[: protocol.FIT_HALF_SIZE]],
            "replication_half_family_ids": [
                family.family_id for family in families()[protocol.FIT_HALF_SIZE : protocol.SPLIT_SIZE]
            ],
            "top_k_per_half": protocol.FEATURE_STABILITY_TOP_K,
            "minimum_intersection": protocol.FEATURE_SELECTION_COUNT,
            "selection": "pooled absolute final-position activation score over the intersection only",
        },
        "families": [family.public_identity() for family in families()],
    }
    return {**value, "manifest_sha256": protocol.digest_json(value)}
