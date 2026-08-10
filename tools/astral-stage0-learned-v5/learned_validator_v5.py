"""Bind the V4 semantic validator to the corrected V5 protocol."""

from __future__ import annotations

from pathlib import Path
import sys

TOOLS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS / "astral-stage0-learned-v4"))
import learned_validator_v4 as base  # noqa: E402
import run_learned_stage0_v4 as runner_base  # noqa: E402
from learned_stage0_v5 import (  # noqa: E402
    EVALUATION_FAMILIES, SCIENTIFIC_SEEDS, STATE_SLICE,
    FrozenScientificTransformer, examples_for,
)


def validate(root: Path, protocol: Path):
    base.EVALUATION_FAMILIES = EVALUATION_FAMILIES
    base.SCIENTIFIC_SEEDS = SCIENTIFIC_SEEDS
    base.STATE_SLICE = STATE_SLICE
    base.FrozenScientificTransformer = FrozenScientificTransformer
    base.examples_for = examples_for
    runner_base.EVALUATION_FAMILIES = EVALUATION_FAMILIES
    runner_base.SCIENTIFIC_SEEDS = SCIENTIFIC_SEEDS
    return base.validate(root, protocol)
