"""Pure-data contract for Astral V46.

State slice: astral-stage0c-qwen36-answer-aligned-causal-target-v46.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


PROTOCOL_ID = "astral-stage0c-qwen36-answer-aligned-causal-target-v46"
STATE_SLICE = PROTOCOL_ID
MODEL_BASENAME = "Qwen3.6-35B-A3B-MLX-4bit"
MODEL_ARCHITECTURE = "Qwen3_5MoeForConditionalGeneration"
EXPECTED_LAYER_COUNT = 40
EXPECTED_HIDDEN_WIDTH = 2048
CANDIDATE_LAYERS = (12, 19, 26)
POSITION_NAME = "content_anchor"
CONTENT_ANCHOR_OFFSET = 8
POSITION_RULE = "eighth_token_before_tokenized_passage_content_boundary"
FIXED_TOKEN_LENGTH = 320
SPLITS = ("fit", "tune", "assessment")
DOCUMENTS_PER_SPLIT = 8
FAMILIES_PER_DOCUMENT = 4
FAMILIES_PER_SPLIT = DOCUMENTS_PER_SPLIT * FAMILIES_PER_DOCUMENT
TOTAL_DOCUMENTS = len(SPLITS) * DOCUMENTS_PER_SPLIT
TOTAL_FAMILIES = len(SPLITS) * FAMILIES_PER_SPLIT
RESPONSE_TOKENS = {"A": " A", "B": " B"}
CANONICAL_WRAPPER = "Use the passage to choose which listed word occurs in it. Respond with only A or B."
CONTROL_NAMES = ("activation_only", "text_only", "exact_copy", "shuffled", "constant", "matched")
RIDGE_ALPHAS = (0.1, 1.0, 10.0, 100.0)
BATCH_SIZE = 16
REPLACEMENT_SCALE = 0.01
MATCH_NORM_RELATIVE_TOLERANCE = 0.02
MAX_EXACT_COPY_ABS_EFFECT = 1e-5
MAX_CONTROL_MEAN_ABS_EFFECT = 0.25
MAX_REPEAT_ABS_EFFECT_DELTA = 1e-5
MIN_TARGET_EFFECT_STD = 0.05
MIN_PREDICTION_CORRELATION = 0.25
MIN_PREDICTION_SIGN_AGREEMENT = 0.70
MIN_BOOTSTRAP_CORRELATION_LOWER = 0.10
BOOTSTRAP_RESAMPLES = 1000
BOOTSTRAP_SEED = 4601
PANEL_ID = f"{PROTOCOL_ID}-panel-v1"
QUALIFICATION_ID = f"{PROTOCOL_ID}-qualification-v1"
FEATURE_MAP_ID = "fixed-response-unembedding-margin-of-counterfactual-minus-ordinary-v1"
FEATURE_DIMENSION = 1
MAX_PANEL_CANDIDATE_PARAGRAPHS = 96
MAX_DISTRACTOR_OPTIONS = 64
SELECTION_ALGORITHM_ID = "fresh-metadata-audited-candidate-pool-greedy-author-disjoint-eight-per-split-v46"

# This pool is sealed in source before acquisition and contains no V39-V45
# candidate or reserved ID. Selection is metadata-only and never sees model
# activations or intervention effects.
CANDIDATE_GUTENBERG_IDS = (
    46, 158, 1399, 17396, 19942, 3207, 4513, 4587, 21816, 230, 57426,
    76000, 77000, 65238, 34413, 59828, 62215, 5197, 21839, 831, 6133, 42,
    564, 47530, 75201, 45839, 7326, 42671, 589, 31100, 36462, 53874, 40284,
    24793, 18143, 1212, 1608, 245, 204, 161, 2147, 2002, 223, 108, 834,
    2825, 4499, 48296, 2620, 31472, 3922, 1063, 69087, 55179, 61851, 38177,
    38311, 2097, 921, 24739, 8492, 7889,
)

KNOWN_RESERVED_GUTENBERG_IDS = frozenset({
    11, 35, 36, 43, 45, 47, 55, 60, 61, 72, 74, 76, 84, 98, 100, 103, 106,
    110, 113, 1184, 1232, 1259, 1260, 1342, 1400, 145, 1513, 155, 174,
    17460, 16328, 1661, 1695, 1727, 1998, 2009, 2048, 215, 219, 2440, 2554,
    2591, 2600, 2610, 2641, 2680, 2701, 2868, 289, 3011, 3021, 31635, 3268,
    3296, 33823, 345, 3543, 37106, 393, 4300, 43063, 4517, 4530, 48438, 5372,
    5530, 560, 58585, 58820, 601, 70854, 67979, 15399, 18875, 19476, 19771,
    20546, 20628, 22541, 2641, 36965, 46976, 57669,
    # V45 candidate intake was also excluded, including rejected candidates.
    205, 244, 5200, 730, 848, 887, 1023, 1082, 1155, 1200, 1251, 1322, 1351,
    14838, 1600, 1635, 1999, 2148, 2372, 2489, 27827, 2852, 4061, 4099, 5630,
    6000, 6700, 7000, 7600, 8200, 8800, 10007, 11000, 12000, 13806, 15659,
    17513, 18857, 20000, 21439, 22693, 25929, 27107, 28539, 30254, 32032,
    32904, 34206, 35688, 38984, 40274, 41562, 44215, 45109, 46295, 47860,
    49345, 50852, 52402, 53961, 55530, 57113, 58627, 60000, 61500, 63000,
    64500, 66000, 67500, 69000, 70500, 72000,
})
FRESHNESS_EXCLUSION_INVENTORY = tuple(sorted(KNOWN_RESERVED_GUTENBERG_IDS))
FORBIDDEN_TITLE_MARKERS = (
    "complete works", "selected short stories", "collected works", "anthology", "volume ", " and other ",
)
QUALIFICATION_PROMPTS = ("Output exactly one token: A.", "Output exactly one token: B.")


class ProtocolError(ValueError):
    """Raised when a V46 contract or custody invariant fails."""


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(file_path: Path) -> str:
    return sha256_bytes(file_path.read_bytes())


def canonical_digest(value: Any) -> str:
    return sha256_bytes(json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8"))


def read_json(file_path: Path) -> Any:
    return json.loads(file_path.read_text(encoding="utf-8"))


def write_json(file_path: Path, value: Any) -> None:
    file_path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def assert_external(file_path: Path, repository_root: Path) -> None:
    resolved = file_path.resolve()
    repo = repository_root.resolve()
    if resolved == repo or repo in resolved.parents:
        raise ProtocolError(f"path must be repository-external: {resolved}")


def freshness_exclusion_digest(ids: list[int] | tuple[int, ...]) -> str:
    return canonical_digest(sorted({int(value) for value in ids}))


def selection_digest(selection: list[dict[str, Any]] | tuple[dict[str, Any], ...]) -> str:
    return canonical_digest(list(selection))


def model_manifest(model_root: Path) -> dict[str, Any]:
    root = model_root.resolve()
    if root.name != MODEL_BASENAME or not root.is_dir():
        raise ProtocolError(f"unexpected model root: {root}")
    files: list[dict[str, Any]] = []
    for candidate in sorted(root.rglob("*")):
        if candidate.is_symlink():
            raise ProtocolError(f"symlink is not permitted: {candidate}")
        if candidate.is_file():
            payload = candidate.read_bytes()
            files.append({"path": candidate.relative_to(root).as_posix(), "bytes": len(payload), "sha256": sha256_bytes(payload)})
    if not files:
        raise ProtocolError("model root contains no files")
    manifest = {"model_root_basename": root.name, "files": files}
    manifest["manifest_sha256"] = canonical_digest(manifest)
    return manifest


def protocol_manifest() -> dict[str, Any]:
    return {
        "protocol": PROTOCOL_ID,
        "state_slice": STATE_SLICE,
        "model": {"basename": MODEL_BASENAME, "architecture": MODEL_ARCHITECTURE, "layer_count": EXPECTED_LAYER_COUNT, "hidden_width": EXPECTED_HIDDEN_WIDTH, "candidate_layers": list(CANDIDATE_LAYERS), "runtime": {"mlx": "0.31.2", "mlx_lm": "0.31.3"}},
        "task": {"wrapper": CANONICAL_WRAPPER, "fixed_token_length": FIXED_TOKEN_LENGTH, "response_tokens": RESPONSE_TOKENS, "position_name": POSITION_NAME, "content_anchor_offset": CONTENT_ANCHOR_OFFSET, "position_rule": POSITION_RULE},
        "feature_map": {"id": FEATURE_MAP_ID, "dimension": FEATURE_DIMENSION, "uses_fixed_response_unembedding_margin": True},
        "model_batch_size": BATCH_SIZE,
        "controls": list(CONTROL_NAMES),
        "ridge_alphas": list(RIDGE_ALPHAS),
        "splits": list(SPLITS),
        "documents_per_split": DOCUMENTS_PER_SPLIT,
        "families_per_document": FAMILIES_PER_DOCUMENT,
        "panel_candidate_paragraph_limit": MAX_PANEL_CANDIDATE_PARAGRAPHS,
        "distractor_option_limit": MAX_DISTRACTOR_OPTIONS,
        "selection_algorithm": SELECTION_ALGORITHM_ID,
        "prediction_lock_before_assessment": True,
        "aggregate_only_result_retention": True,
    }
