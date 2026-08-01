"""Execute V5 through the frozen V4 orchestration with corrected bindings."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

TOOLS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS / "astral-stage0-learned-v4"))
import run_learned_stage0_v4 as base  # noqa: E402
from learned_stage0_v5 import (  # noqa: E402
    EVALUATION_FAMILIES, SCIENTIFIC_SEEDS, STATE_SLICE, clean_parity,
    examples_for, intervention_effects, reproduce, score_example,
)


def bind_v5() -> None:
    base.EVALUATION_FAMILIES = EVALUATION_FAMILIES
    base.SCIENTIFIC_SEEDS = SCIENTIFIC_SEEDS
    base.STATE_SLICE = STATE_SLICE
    base.PROTOCOL_RELATIVE_PATH = (
        "docs/research/astral-self-modeling/"
        "13-stage0-autograd-capture-correction-and-fresh-confirmation-v5.md"
    )
    base.clean_parity = clean_parity
    base.examples_for = examples_for
    base.intervention_effects = intervention_effects
    base.reproduce = reproduce
    base.score_example = score_example


def run(output: Path, repository: Path, protocol: Path):
    bind_v5()
    return base.run(output, repository, protocol)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--protocol", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(run(args.output, args.repo, args.protocol), indent=2, sort_keys=True))
