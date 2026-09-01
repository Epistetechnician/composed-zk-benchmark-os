"""Pure-data V41 protocol constants and custody helpers.

State slice: astral-stage0c-qwen36-directional-block-target-v41.

This module has no model execution and performs no filesystem discovery beyond
explicit paths supplied by callers. V41 is a fresh successor to V40; its
scientific inputs and output roots are separate.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


PROTOCOL_ID = "astral-stage0c-qwen36-directional-block-target-v41"
STATE_SLICE = PROTOCOL_ID
MODEL_BASENAME = "Qwen3.6-35B-A3B-MLX-4bit"
MODEL_ARCHITECTURE = "Qwen3_5MoeForConditionalGeneration"
EXPECTED_LAYER_COUNT = 40
EXPECTED_HIDDEN_WIDTH = 2048
TARGET_LAYER = 19
QUALIFICATION_LAYERS = (12, 19, 26)
REPLACEMENT_SCALE = 0.01
BLOCK_COUNT = 128
BLOCK_WIDTH = 16
FEATURE_WIDTH = BLOCK_COUNT * 4 + 4
FIXED_TOKEN_LENGTH = 320
RIDGE_ALPHAS = (1e-4, 1e-3, 1e-2, 1e-1)
SPLITS = ("fit", "tune", "assessment")
DOCUMENTS_PER_SPLIT = 6
FAMILIES_PER_DOCUMENT = 8
FAMILIES_PER_SPLIT = DOCUMENTS_PER_SPLIT * FAMILIES_PER_DOCUMENT
TOTAL_DOCUMENTS = len(SPLITS) * DOCUMENTS_PER_SPLIT
TOTAL_FAMILIES = len(SPLITS) * FAMILIES_PER_SPLIT
RESPONSE_LABELS = ("A", "B")
RESPONSE_TOKENS = {"A": " A", "B": " B"}
RESPONSE_POSITION_RULE = "last_input_position_before_response"
PRIMARY_CONTROL = "directional_block_primary"
CONTROL_NAMES = (
    PRIMARY_CONTROL,
    "clean_activation_only",
    "text_only",
    "shuffled",
    "constant",
    "matched",
)
UTILITY_RMSE_MARGIN = 0.01
BOOTSTRAP_RMSE_MARGIN = 0.005
CONTROL_RMSE_MARGIN = 0.005
MIN_ASSESSMENT_TARGET_STD = 0.05
MATCH_NORM_RELATIVE_TOLERANCE = 0.02
MATCHED_CONTROL_MEAN_ABS_MAX = 0.25
BOOTSTRAP_SEED = 4101
PANEL_ID = "astral-stage0c-qwen36-directional-block-target-v41-panel-v1"

# Six documents per split. IDs, authors, and source text are fresh relative to
# the reserved inventory; metadata is independently revalidated from
# Project Gutenberg RDF before panel construction.
SELECTION = (
    {"gutenberg_id": 1400, "split": "fit"},
    {"gutenberg_id": 768, "split": "fit"},
    {"gutenberg_id": 55, "split": "fit"},
    {"gutenberg_id": 215, "split": "fit"},
    {"gutenberg_id": 2600, "split": "fit"},
    {"gutenberg_id": 58585, "split": "fit"},
    {"gutenberg_id": 25344, "split": "tune"},
    {"gutenberg_id": 4300, "split": "tune"},
    {"gutenberg_id": 1497, "split": "tune"},
    {"gutenberg_id": 4517, "split": "tune"},
    {"gutenberg_id": 2610, "split": "tune"},
    {"gutenberg_id": 408, "split": "tune"},
    {"gutenberg_id": 103, "split": "assessment"},
    {"gutenberg_id": 1259, "split": "assessment"},
    {"gutenberg_id": 60, "split": "assessment"},
    {"gutenberg_id": 155, "split": "assessment"},
    {"gutenberg_id": 143, "split": "assessment"},
    {"gutenberg_id": 20203, "split": "assessment"},
)

# Known reserved IDs from the supplied prior Astral Gutenberg panels. A future
# external selection manifest must also bind its complete prior-panel
# exclusion inventory; this list is a local fail-closed minimum.
KNOWN_RESERVED_GUTENBERG_IDS = frozenset(
    {
        1342,
        2701,
        2554,
        84,
        1661,
        16328,
        11,
        1727,
        43,
        1513,
        100,
        345,
        174,
        1260,
        98,
        1184,
        145,
        110,
        74,
        76,
        219,
        2591,
        1080,
        1232,
        35,
        36,
        45,
        514,
        135,
        863,
    }
)
FRESHNESS_EXCLUSION_INVENTORY = tuple(sorted(KNOWN_RESERVED_GUTENBERG_IDS))
FORBIDDEN_TITLE_MARKERS = (
    "complete works",
    "selected short stories",
    "collected works",
    "anthology",
)
QUALIFICATION_PROMPTS = (
    "Output exactly one token: A.",
    "Output exactly one token: B.",
)


class ProtocolError(ValueError):
    """Raised when a V41 pure-data or custody invariant fails."""


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def canonical_digest(value: Any) -> str:
    return sha256_bytes(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    )


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def assert_external(path: Path, repository_root: Path) -> None:
    resolved = path.resolve()
    repo = repository_root.resolve()
    if resolved == repo or repo in resolved.parents:
        raise ProtocolError(f"path must be repository-external: {resolved}")


def block_sign(block: int, dimension: int) -> int:
    if not 0 <= block < BLOCK_COUNT or not 0 <= dimension < BLOCK_WIDTH:
        raise ProtocolError("directional-block coordinate is out of range")
    digest = hashlib.sha256(
        f"{PROTOCOL_ID}:directional-block:{block}:{dimension}".encode("utf-8")
    ).digest()
    return 1 if digest[0] & 1 else -1


def feature_map_manifest() -> dict[str, Any]:
    return {
        "protocol": PROTOCOL_ID,
        "kind": "non-overlapping-signed-directional-block-v1",
        "hidden_width": EXPECTED_HIDDEN_WIDTH,
        "block_count": BLOCK_COUNT,
        "block_width": BLOCK_WIDTH,
        "feature_width": FEATURE_WIDTH,
        "sign_derivation": "sha256(protocol:block:dimension), low-bit Rademacher sign",
        "feature_order": [
            "B(u)",
            "B(v)",
            "B(u-v)",
            "B(abs(u-v))",
            "norm(u)",
            "norm(v)",
            "norm(u-v)",
            "cosine(u,v)",
        ],
    }


def feature_map_digest() -> str:
    return canonical_digest(feature_map_manifest())


def selection_digest() -> str:
    return canonical_digest(list(SELECTION))


def freshness_exclusion_digest(ids: list[int] | tuple[int, ...]) -> str:
    normalized = sorted({int(value) for value in ids})
    return canonical_digest(normalized)


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
            files.append(
                {"path": relative, "bytes": len(payload), "sha256": sha256_bytes(payload)}
            )
    if not files:
        raise ProtocolError("model root contains no regular files")
    manifest = {"model_root_basename": root.name, "files": files}
    manifest["manifest_sha256"] = canonical_digest(manifest)
    return manifest
