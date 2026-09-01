"""Pure-data V40 protocol constants and custody helpers.

State slice: astral-stage0c-qwen36-intervention-conditioned-target-v40.

This module contains no model execution and no filesystem discovery beyond
explicit paths supplied by callers. V40 is a fresh proposal-derived slice; its
scientific inputs and output roots are separate from V39.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


PROTOCOL_ID = "astral-stage0c-qwen36-intervention-conditioned-target-v40"
STATE_SLICE = PROTOCOL_ID
MODEL_BASENAME = "Qwen3.6-35B-A3B-MLX-4bit"
MODEL_ARCHITECTURE = "Qwen3_5MoeForConditionalGeneration"
EXPECTED_LAYER_COUNT = 40
EXPECTED_HIDDEN_WIDTH = 2048
TARGET_LAYER = 19
QUALIFICATION_LAYERS = (12, 19, 26)
REPLACEMENT_SCALE = 0.01
FEATURE_WIDTH = 256
FIXED_TOKEN_LENGTH = 320
RIDGE_ALPHAS = (1e-4, 1e-3, 1e-2, 1e-1)
SPLITS = ("fit", "tune", "assessment")
DOCUMENTS_PER_SPLIT = 6
FAMILIES_PER_DOCUMENT = 8
FAMILIES_PER_SPLIT = DOCUMENTS_PER_SPLIT * FAMILIES_PER_DOCUMENT
TOTAL_FAMILIES = len(SPLITS) * FAMILIES_PER_SPLIT
RESPONSE_LABELS = ("A", "B")
RESPONSE_TOKENS = {"A": " A", "B": " B"}
RESPONSE_POSITION_RULE = "last_input_position_before_response"
PRIMARY_CONTROL = "pair_conditioned_activation"
CONTROL_NAMES = (
    PRIMARY_CONTROL,
    "clean_activation_only",
    "text_only",
    "shuffled",
    "constant",
)
UTILITY_RMSE_MARGIN = 0.01
BOOTSTRAP_RMSE_MARGIN = 0.005
CONTROL_RMSE_MARGIN = 0.005
MIN_ASSESSMENT_TARGET_STD = 0.05
MATCH_NORM_RELATIVE_TOLERANCE = 0.02
MATCHED_CONTROL_MEAN_ABS_MAX = 0.25
BOOTSTRAP_SEED = 4017

V39_GUTENBERG_IDS = frozenset((1342, 2701, 2554, 84, 1661, 16328, 11, 1727, 43, 1513, 100, 345))
FORBIDDEN_TITLE_MARKERS = ("complete works", "selected short stories", "collected works", "anthology")

# Six documents per split; authors are intentionally disjoint across splits.
# Metadata is revalidated from Project Gutenberg RDF before any panel is built.
SELECTION = (
    {"gutenberg_id": 174, "split": "fit"},
    {"gutenberg_id": 1260, "split": "fit"},
    {"gutenberg_id": 98, "split": "fit"},
    {"gutenberg_id": 1184, "split": "fit"},
    {"gutenberg_id": 145, "split": "fit"},
    {"gutenberg_id": 110, "split": "fit"},
    {"gutenberg_id": 74, "split": "tune"},
    {"gutenberg_id": 76, "split": "tune"},
    {"gutenberg_id": 219, "split": "tune"},
    {"gutenberg_id": 2591, "split": "tune"},
    {"gutenberg_id": 1080, "split": "tune"},
    {"gutenberg_id": 1232, "split": "tune"},
    {"gutenberg_id": 35, "split": "assessment"},
    {"gutenberg_id": 36, "split": "assessment"},
    {"gutenberg_id": 45, "split": "assessment"},
    {"gutenberg_id": 514, "split": "assessment"},
    {"gutenberg_id": 135, "split": "assessment"},
    {"gutenberg_id": 863, "split": "assessment"},
)

QUALIFICATION_PROMPTS = (
    "Return one token: A.",
    "Return one token: B.",
)


class ProtocolError(ValueError):
    """Raised when a V40 pure-data or custody invariant fails."""


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def canonical_digest(value: Any) -> str:
    return sha256_bytes(json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8"))


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def assert_external(path: Path, repository_root: Path) -> None:
    resolved = path.resolve()
    repo = repository_root.resolve()
    if resolved == repo or repo in resolved.parents:
        raise ProtocolError(f"path must be repository-external: {resolved}")


def selection_digest() -> str:
    return canonical_digest(list(SELECTION))


def model_manifest(model_root: Path) -> dict[str, Any]:
    root = model_root.resolve()
    if root.name != MODEL_BASENAME:
        raise ProtocolError(f"unexpected model basename: {root.name}")
    if not root.is_dir():
        raise ProtocolError(f"model root is not a directory: {root}")
    files: list[dict[str, Any]] = []
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise ProtocolError(f"symlink is not permitted: {path}")
        if path.is_file():
            relative = path.relative_to(root).as_posix()
            payload = path.read_bytes()
            files.append({"path": relative, "bytes": len(payload), "sha256": sha256_bytes(payload)})
    if not files:
        raise ProtocolError("model root contains no regular files")
    manifest = {"model_root_basename": root.name, "files": files}
    manifest["manifest_sha256"] = canonical_digest(manifest)
    return manifest
