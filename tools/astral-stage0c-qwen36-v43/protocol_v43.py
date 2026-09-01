"""Pure-data contract for the V43 causal-target localization slice.

State slice: astral-stage0c-qwen36-causal-target-localization-v43.

V43 is a fresh successor to the V42 reliability stop. It may re-custody the
cached model bytes, but it cannot consume any prior Astral corpus, panel,
activation, prediction, effect, or result artifact as a scientific input.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


PROTOCOL_ID = "astral-stage0c-qwen36-causal-target-localization-v43"
STATE_SLICE = PROTOCOL_ID
MODEL_BASENAME = "Qwen3.6-35B-A3B-MLX-4bit"
MODEL_ARCHITECTURE = "Qwen3_5MoeForConditionalGeneration"
EXPECTED_LAYER_COUNT = 40
EXPECTED_HIDDEN_WIDTH = 2048
CANDIDATE_LAYERS = (12, 19, 26)
QUALIFICATION_LAYERS = CANDIDATE_LAYERS
FIXED_POSITION = "last_input_position_before_response"
REPLACEMENT_SCALE = 0.01
FIXED_TOKEN_LENGTH = 320
SPLITS = ("fit", "tune", "assessment")
DOCUMENTS_PER_SPLIT = 6
FAMILIES_PER_DOCUMENT = 4
FAMILIES_PER_SPLIT = DOCUMENTS_PER_SPLIT * FAMILIES_PER_DOCUMENT
TOTAL_DOCUMENTS = len(SPLITS) * DOCUMENTS_PER_SPLIT
TOTAL_FAMILIES = len(SPLITS) * FAMILIES_PER_SPLIT
RESPONSE_TOKENS = {"A": " A", "B": " B"}
WRAPPER_NAMES = ("wrapper_alpha", "wrapper_beta")
CONTROL_NAMES = ("activation_only", "text_only", "exact_copy", "shuffled", "constant", "matched")
REPEATS = 2
MATCH_NORM_RELATIVE_TOLERANCE = 0.02
MAX_EXACT_COPY_ABS_EFFECT = 1e-5
MAX_CONTROL_MEAN_ABS_EFFECT = 0.25
MAX_REPEAT_ABS_EFFECT_DELTA = 1e-5
MIN_TARGET_EFFECT_STD = 0.05
MIN_TARGET_CORRELATION = 0.25
MIN_TARGET_SIGN_AGREEMENT = 0.70
MIN_BOOTSTRAP_CORRELATION_LOWER = 0.10
BOOTSTRAP_RESAMPLES = 2000
BOOTSTRAP_SEED = 4301
PANEL_ID = "astral-stage0c-qwen36-causal-target-localization-v43-panel-v1"
QUALIFICATION_ID = f"{PROTOCOL_ID}-qualification-v1"

WRAPPER_PREFIXES = {
    "wrapper_alpha": "Read the passage and select the listed word found in it.",
    "wrapper_beta": "Examine the passage and choose the option that occurs in the text.",
}

# Six fresh single works per split. These IDs are disjoint from the V39, V40,
# V41, and V42 inventories and were metadata-audited before this protocol was
# sealed. The acquisition command rechecks the metadata and rights markers.
SELECTION = (
    {"gutenberg_id": 2641, "split": "fit"},
    {"gutenberg_id": 3268, "split": "fit"},
    {"gutenberg_id": 2868, "split": "fit"},
    {"gutenberg_id": 19476, "split": "fit"},
    {"gutenberg_id": 22541, "split": "fit"},
    {"gutenberg_id": 67979, "split": "fit"},
    {"gutenberg_id": 601, "split": "tune"},
    {"gutenberg_id": 3011, "split": "tune"},
    {"gutenberg_id": 37106, "split": "tune"},
    {"gutenberg_id": 72, "split": "tune"},
    {"gutenberg_id": 17460, "split": "tune"},
    {"gutenberg_id": 3296, "split": "tune"},
    {"gutenberg_id": 33823, "split": "assessment"},
    {"gutenberg_id": 393, "split": "assessment"},
    {"gutenberg_id": 19771, "split": "assessment"},
    {"gutenberg_id": 15399, "split": "assessment"},
    {"gutenberg_id": 560, "split": "assessment"},
    {"gutenberg_id": 58820, "split": "assessment"},
)

KNOWN_RESERVED_GUTENBERG_IDS = frozenset(
    {
        # V39.
        11, 43, 84, 100, 345, 1513, 16328, 1661, 1727, 2554, 2701, 5372, 5530,
        # V40.
        35, 36, 45, 74, 76, 98, 110, 1184, 1232, 1260, 135, 145, 174, 219, 514, 863, 1080, 2591,
        # V41.
        55, 60, 103, 143, 155, 215, 408, 768, 1259, 1400, 1497, 2600, 2610, 4300, 4517, 20203, 25344, 58585,
        # V42.
        23, 47, 61, 106, 113, 175, 209, 289, 491, 690, 996, 1695, 1998, 2009, 2048, 2440, 3021, 3543,
    }
)
FRESHNESS_EXCLUSION_INVENTORY = tuple(sorted(KNOWN_RESERVED_GUTENBERG_IDS))
FORBIDDEN_TITLE_MARKERS = (
    "complete works",
    "selected short stories",
    "collected works",
    "anthology",
    "volume ",
    " and other ",
)
QUALIFICATION_PROMPTS = (
    "Output exactly one token: A.",
    "Output exactly one token: B.",
)


class ProtocolError(ValueError):
    """Raised when a V43 contract or custody invariant fails."""


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


def selection_digest() -> str:
    return canonical_digest(list(SELECTION))


def freshness_exclusion_digest(ids: list[int] | tuple[int, ...]) -> str:
    return canonical_digest(sorted({int(value) for value in ids}))


def model_manifest(model_root: Path) -> dict[str, Any]:
    root = model_root.resolve()
    if root.name != MODEL_BASENAME:
        raise ProtocolError(f"unexpected model basename: {root.name}")
    if not root.is_dir():
        raise ProtocolError(f"model root is not a directory: {root}")
    files: list[dict[str, Any]] = []
    for candidate in sorted(root.rglob("*")):
        if candidate.is_symlink():
            raise ProtocolError(f"symlink is not permitted: {candidate}")
        if candidate.is_file():
            relative = candidate.relative_to(root).as_posix()
            payload = candidate.read_bytes()
            files.append({"path": relative, "bytes": len(payload), "sha256": sha256_bytes(payload)})
    if not files:
        raise ProtocolError("model root contains no regular files")
    manifest = {"model_root_basename": root.name, "files": files}
    manifest["manifest_sha256"] = canonical_digest(manifest)
    return manifest


def protocol_manifest() -> dict[str, Any]:
    return {
        "protocol": PROTOCOL_ID,
        "state_slice": STATE_SLICE,
        "model": {
            "basename": MODEL_BASENAME,
            "architecture": MODEL_ARCHITECTURE,
            "layer_count": EXPECTED_LAYER_COUNT,
            "hidden_width": EXPECTED_HIDDEN_WIDTH,
            "candidate_layers": list(CANDIDATE_LAYERS),
            "position": FIXED_POSITION,
            "runtime": {"mlx": "0.31.2", "mlx_lm": "0.31.3"},
        },
        "target": {
            "kind": "paired_final_position_layer_localization",
            "candidate_layers": list(CANDIDATE_LAYERS),
            "wrappers": list(WRAPPER_NAMES),
            "selection_rule": "lowest_numeric_candidate_layer_passing_all_tune_gates",
            "repeats": REPEATS,
            "effect_formula": "half of ordinary and counterfactual margin changes after reciprocal activation replacement",
        },
        "controls": list(CONTROL_NAMES),
        "splits": list(SPLITS),
        "documents_per_split": DOCUMENTS_PER_SPLIT,
        "families_per_document": FAMILIES_PER_DOCUMENT,
        "fixed_token_length": FIXED_TOKEN_LENGTH,
        "assessment_effects_require_review": True,
        "prediction_lock_before_assessment": True,
        "aggregate_only_result_retention": True,
        "thresholds": {
            "min_target_effect_std": MIN_TARGET_EFFECT_STD,
            "min_target_correlation": MIN_TARGET_CORRELATION,
            "min_target_sign_agreement": MIN_TARGET_SIGN_AGREEMENT,
            "min_bootstrap_correlation_lower": MIN_BOOTSTRAP_CORRELATION_LOWER,
            "max_exact_copy_abs_effect": MAX_EXACT_COPY_ABS_EFFECT,
            "max_control_mean_abs_effect": MAX_CONTROL_MEAN_ABS_EFFECT,
            "max_repeat_abs_effect_delta": MAX_REPEAT_ABS_EFFECT_DELTA,
        },
    }
