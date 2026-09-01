#!/usr/bin/env python3
"""Independently validate the fresh-cohort V2 pilot artifact.

State slice: continual-learning-gemma3-local-pilot-v2.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from experiments.continual_learning.validate_gemma3_local_pilot_v1 import (
    validate as validate_common,
)

STATE_SLICE = "continual-learning-gemma3-local-pilot-v2"
CLAIM_CEILING = "LocalDevelopmentGemma3NewsroomIndependentRecirculationPilot"
CORPUS_SCHEMA = "gemma3-newsroom-recirculation-pilot-corpus-v2"
SOURCE_SCHEMA = "gemma3-newsroom-recirculation-pilot-input-v2"
SELECTION_POLICY = "next-four-after-v1-eligible-newsroom-test-records-v1"


def validate(root: Path, model_path: Path) -> dict:
    return validate_common(
        root,
        model_path,
        state_slice=STATE_SLICE,
        claim_ceiling=CLAIM_CEILING,
        corpus_schema=CORPUS_SCHEMA,
        source_schema=SOURCE_SCHEMA,
        selection_offset=4,
        selection_policy=SELECTION_POLICY,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact-root", type=Path, required=True)
    parser.add_argument("--model", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(validate(args.artifact_root, args.model), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
