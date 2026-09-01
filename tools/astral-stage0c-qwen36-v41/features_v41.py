"""Pure V41 directional-block feature maps.

State slice: astral-stage0c-qwen36-directional-block-target-v41.

The activation maps contain no fitted quantities and no target labels. They
are fixed functions of the V41 protocol digest and explicit input vectors.
"""

from __future__ import annotations

import hashlib
import re

import numpy as np

import protocol_v41 as protocol


WORD_RE = re.compile(r"[A-Za-z][A-Za-z'-]{3,}")


def _validate_vector(vector: np.ndarray) -> np.ndarray:
    value = np.asarray(vector, dtype=np.float64)
    if value.shape != (protocol.EXPECTED_HIDDEN_WIDTH,):
        raise protocol.ProtocolError(f"expected 2048-scalar activation, got {value.shape}")
    if not np.isfinite(value).all():
        raise protocol.ProtocolError("activation contains non-finite values")
    return value


def block_projection(vector: np.ndarray) -> np.ndarray:
    value = _validate_vector(vector)
    blocks = np.empty(protocol.BLOCK_COUNT, dtype=np.float64)
    normalizer = np.sqrt(float(protocol.BLOCK_WIDTH))
    for block in range(protocol.BLOCK_COUNT):
        start = block * protocol.BLOCK_WIDTH
        signs = np.asarray(
            [protocol.block_sign(block, dimension) for dimension in range(protocol.BLOCK_WIDTH)],
            dtype=np.float64,
        )
        blocks[block] = float(value[start : start + protocol.BLOCK_WIDTH] @ signs / normalizer)
    return blocks


def _scalar_summaries(ordinary: np.ndarray, counterfactual: np.ndarray) -> list[float]:
    delta = ordinary - counterfactual
    ordinary_norm = float(np.linalg.norm(ordinary))
    counterfactual_norm = float(np.linalg.norm(counterfactual))
    delta_norm = float(np.linalg.norm(delta))
    denominator = ordinary_norm * counterfactual_norm
    cosine = float(ordinary @ counterfactual / denominator) if denominator > 0.0 else 0.0
    return [ordinary_norm, counterfactual_norm, delta_norm, cosine]


def pair_features(ordinary: np.ndarray, counterfactual: np.ndarray) -> np.ndarray:
    ordinary_value = _validate_vector(ordinary)
    counterfactual_value = _validate_vector(counterfactual)
    delta = ordinary_value - counterfactual_value
    blocks = np.concatenate(
        [
            block_projection(ordinary_value),
            block_projection(counterfactual_value),
            block_projection(delta),
            block_projection(np.abs(delta)),
        ]
    )
    result = np.concatenate([blocks, np.asarray(_scalar_summaries(ordinary_value, counterfactual_value))])
    if result.shape != (protocol.FEATURE_WIDTH,) or not np.isfinite(result).all():
        raise protocol.ProtocolError("directional-block feature shape or finiteness failure")
    return result


def clean_activation_features(ordinary: np.ndarray, counterfactual: np.ndarray) -> np.ndarray:
    ordinary_value = _validate_vector(ordinary)
    counterfactual_value = _validate_vector(counterfactual)
    blocks = np.concatenate(
        [
            block_projection(ordinary_value),
            block_projection(counterfactual_value),
            block_projection(np.abs(ordinary_value)),
            block_projection(np.abs(counterfactual_value)),
        ]
    )
    result = np.concatenate([blocks, np.asarray(_scalar_summaries(ordinary_value, counterfactual_value))])
    if result.shape != (protocol.FEATURE_WIDTH,) or not np.isfinite(result).all():
        raise protocol.ProtocolError("clean feature shape or finiteness failure")
    return result


def text_features(ordinary_prompt: str, counterfactual_prompt: str) -> np.ndarray:
    vector = np.zeros(protocol.FEATURE_WIDTH, dtype=np.float64)
    for label, text in (("ordinary", ordinary_prompt), ("counterfactual", counterfactual_prompt)):
        for word in WORD_RE.findall(text.lower()):
            digest = hashlib.sha256(f"{protocol.PROTOCOL_ID}:text:{label}:{word}".encode("utf-8")).digest()
            bucket = int.from_bytes(digest[:8], "big") % protocol.FEATURE_WIDTH
            sign = 1.0 if digest[8] & 1 else -1.0
            vector[bucket] += sign
    return vector
