"""Pure-data contract for Astral V48.

State slice: astral-stage0c-cross-view-causal-state-transport-v48.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


PROTOCOL_ID = "astral-stage0c-cross-view-causal-state-transport-v48"
STATE_SLICE = PROTOCOL_ID
MODEL_BASENAME = "Qwen3.6-35B-A3B-MLX-4bit"
MODEL_ARCHITECTURE = "Qwen3_5MoeForConditionalGeneration"
EXPECTED_LAYER_COUNT = 40
EXPECTED_HIDDEN_WIDTH = 2048
SOURCE_LAYER = 26
DESTINATION_LAYER = 12
POSITION_NAME = "state_anchor"
POSITION_RULE = "eighth_token_before_tokenized_state_payload_boundary"
CONTENT_ANCHOR_OFFSET = 8
ALPHA = 0.10
ADDITIONAL_PASSES = 1
MATCH_NORM_RELATIVE_TOLERANCE = 0.02
RESPONSE_LABELS = ("A", "B", "C", "D")
RESPONSE_TOKENS = {label: f" {label}" for label in RESPONSE_LABELS}
STATE_COUNT = 4
VIEWS = ("view_1", "view_2")
DIRECTIONS = ("plus", "minus")
SPLITS = ("fit", "tune", "assessment")
DOCUMENTS_PER_SPLIT = 16
FAMILIES_PER_DOCUMENT = 4
TOTAL_DOCUMENTS = len(SPLITS) * DOCUMENTS_PER_SPLIT
TOTAL_FAMILIES = TOTAL_DOCUMENTS * FAMILIES_PER_DOCUMENT
FIXED_TOKEN_LENGTH = 320
BATCH_SIZE = 16
REPEATS = 2
BOOTSTRAP_RESAMPLES = 1000
BOOTSTRAP_SEED = 4801
POWER_SIMULATION_SEED = 4802
POWER_SIMULATION_REPS = 5000
SHUFFLE_SEED = 4803
POWER_D = 0.35
ICC_SENSITIVITY = (0.10, 0.30)
MIN_POWER = 0.90
RIDGE_ALPHAS = (0.1, 1.0, 10.0, 100.0)
MIN_PREDICTION_CORRELATION = 0.25
MIN_PREDICTION_SIGN_AGREEMENT = 0.70
MIN_BOOTSTRAP_CORRELATION_LOWER = 0.10
MIN_LOCALIZATION_MARGIN = 0.10
MIN_LOCALIZATION_STANDARDIZED = 0.20
MAX_GENERIC_CONTROL_MARGIN = 0.05
MIN_RECOVERABILITY_BALANCED_ACCURACY = 0.35
RECOVERABILITY_CHANCE = 0.25
RECOVERABILITY_MARGIN = 0.10
VIEW_EQUIVALENCE_MARGIN = 0.10
MIN_ICC_LOWER = 0.80
MIN_SIGN_STABILITY = 0.80
MAX_CELL_MISSINGNESS = 0.05
MAX_EXACT_COPY_ABS_EFFECT = 1e-5
MAX_REPEAT_ABS_EFFECT_DELTA = 1e-5
MAX_ZERO_REPLACEMENT_ABS_EFFECT = 1e-5
MIN_NONZERO_REACH = 1e-6
MAX_NORM_ERROR = 0.02
FEATURE_MAP_ID = "fixed-four-state-cross-view-transport-summary-v1"
QUALIFICATION_ID = f"{PROTOCOL_ID}-qualification-v1"
PANEL_ID = f"{PROTOCOL_ID}-panel-v1"
MEASUREMENT_ID = f"{PROTOCOL_ID}-measurement-v1"
CORPUS_ID = "astral-v48-gutenberg-cross-view-state-transport-r1-2026-08-28"
# Frozen metadata-screened Gutenberg catalog for V48.  The list length is
# deliberately asserted against TOTAL_DOCUMENTS below; changing it creates a
# new protocol slice rather than silently changing this one.
CORPUS_DOCUMENTS = (
    201, 202, 203, 204, 208, 217, 220, 221, 222, 224, 225, 230, 233, 234,
    236, 238, 241, 242, 245, 257, 261, 267, 268, 269, 270, 271, 285, 286,
    287, 288, 292, 293, 297, 298, 299, 301, 305, 308, 310, 313, 316, 319,
    322, 324, 327, 328, 330, 331,
)
CORPUS_DOCUMENT_IDS = CORPUS_DOCUMENTS
CANDIDATE_GUTENBERG_IDS = CORPUS_DOCUMENTS
SELECTION_ALGORITHM_ID = "fixed-48-id-list-r1-document-order-split-assignment-v48"
FORBIDDEN_TITLE_MARKERS = (
    "complete works", "selected short stories", "collected works", "anthology", "volume ",
    " and other ", "symphony", "catalog", "dictionary", "manual", "hand book", "handbook",
    "bibliography", "index", "interview", "appreciations", "open letter", "disputation",
    "guide to", "history of", "journal of", "letters", "poems", "ballads", "fables",
    "essays", "theory of", "science of", "hand-book",
)
FRESHNESS_EXCLUSION_INVENTORY = (
    11, 35, 36, 43, 45, 47, 55, 60, 61, 72, 74, 76, 84, 98, 100, 103,
    106, 110, 113, 1184, 1232, 1259, 1260, 1342, 1400, 145, 1513, 155,
    174, 17460, 16328, 1661, 1695, 1727, 1998, 2009, 2048, 215, 219,
    2440, 2554, 2591, 2600, 2610, 2641, 2680, 2701, 2868, 289, 3011,
    3021, 31635, 3268, 3296, 33823, 345, 3543, 37106, 393, 4300, 43063,
    4517, 4530, 48438, 5372, 5530, 560, 58585, 58820, 601, 70854, 67979,
    15399, 18875, 19476, 19771, 20546, 20628, 22541, 2641, 36965, 46976,
    57669, 205, 244, 5200, 730, 848, 887, 1023, 1082, 1155, 1200, 1251,
    1322, 1351, 14838, 1600, 1635, 1999, 2148, 2372, 2489, 27827, 2852,
    4061, 4099, 5630, 6000, 6700, 7000, 7600, 8200, 8800, 10007, 11000,
    12000, 13806, 15659, 17513, 18857, 20000, 21439, 22693, 25929, 27107,
    28539, 30254, 32032, 32904, 34206, 35688, 38984, 40274, 41562, 44215,
    45109, 46295, 47860, 49345, 50852, 52402, 53961, 55530, 57113, 58627,
    60000, 61500, 63000, 64500, 66000, 67500, 69000, 70500, 72000,
)


class ProtocolError(ValueError):
    """Raised when a V48 contract or custody invariant fails."""


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(file_path: Path) -> str:
    return sha256_bytes(file_path.read_bytes())


def canonical_digest(value: Any) -> str:
    return sha256_bytes(json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8"))


def freshness_exclusion_digest(ids: list[int] | tuple[int, ...]) -> str:
    return canonical_digest(sorted({int(value) for value in ids}))


def selection_digest(selection: list[dict[str, Any]] | tuple[dict[str, Any], ...]) -> str:
    return canonical_digest(list(selection))


def read_json(file_path: Path) -> Any:
    return json.loads(file_path.read_text(encoding="utf-8"))


def write_json(file_path: Path, value: Any) -> None:
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def assert_external(file_path: Path, repository_root: Path) -> None:
    resolved = file_path.resolve()
    repo = repository_root.resolve()
    if resolved == repo or repo in resolved.parents:
        raise ProtocolError(f"path must be repository-external: {resolved}")


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
        "model": {
            "basename": MODEL_BASENAME,
            "architecture": MODEL_ARCHITECTURE,
            "layer_count": EXPECTED_LAYER_COUNT,
            "hidden_width": EXPECTED_HIDDEN_WIDTH,
            "source_layer": SOURCE_LAYER,
            "destination_layer": DESTINATION_LAYER,
            "runtime": {"python": "3.14.5", "mlx": "0.31.2", "mlx_lm": "0.31.3"},
        },
        "operator": {
            "alpha": ALPHA,
            "additional_passes": ADDITIONAL_PASSES,
            "position_name": POSITION_NAME,
            "position_rule": POSITION_RULE,
            "normalization": "source-to-receiver-l2-norm",
        },
        "task": {
            "corpus_id": CORPUS_ID,
            "corpus_document_ids": list(CORPUS_DOCUMENTS),
            "selection_algorithm": SELECTION_ALGORITHM_ID,
            "freshness_exclusion_sha256": freshness_exclusion_digest(FRESHNESS_EXCLUSION_INVENTORY),
            "state_count": STATE_COUNT,
            "views": list(VIEWS),
            "directions": list(DIRECTIONS),
            "fixed_token_length": FIXED_TOKEN_LENGTH,
            "response_tokens": RESPONSE_TOKENS,
        },
        "feature_map": {"id": FEATURE_MAP_ID},
        "ridge_alphas": list(RIDGE_ALPHAS),
        "prediction_gates": {
            "minimum_correlation": MIN_PREDICTION_CORRELATION,
            "minimum_sign_agreement": MIN_PREDICTION_SIGN_AGREEMENT,
            "minimum_bootstrap_correlation_lower_95": MIN_BOOTSTRAP_CORRELATION_LOWER,
        },
        "controls": ["activation_only", "text_only", "input_only", "exact_copy", "shuffled", "constant", "matched", "access_null", "matched_norm"],
        "splits": list(SPLITS),
        "documents_per_split": DOCUMENTS_PER_SPLIT,
        "families_per_document": FAMILIES_PER_DOCUMENT,
        "total_documents": TOTAL_DOCUMENTS,
        "total_families": TOTAL_FAMILIES,
        "prediction_lock_before_assessment": True,
        "aggregate_only_result_retention": True,
        "assessment_opened": False,
    }
