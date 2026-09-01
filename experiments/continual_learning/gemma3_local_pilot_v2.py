#!/usr/bin/env python3
"""Run the fresh-cohort V2 Gemma3 recirculation mechanics pilot.

State slice: continual-learning-gemma3-local-pilot-v2.

V2 reuses the tested local-pilot engine with a new immutable protocol identity
and selects the next four eligible NEWSROOM test documents after the V1 cohort.
The model, recurrence, window size, fit grid, controls, and storage policy are
unchanged. This is an independent local replication, not a paper replication.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from experiments.continual_learning.gemma3_local_pilot_v1 import (
    DEFAULT_INPUT,
    DEFAULT_MODEL,
    PilotSpec,
    run_campaign as run_pilot_campaign,
)

STATE_SLICE = "continual-learning-gemma3-local-pilot-v2"
CLAIM_CEILING = "LocalDevelopmentGemma3NewsroomIndependentRecirculationPilot"
CORPUS_SCHEMA = "gemma3-newsroom-recirculation-pilot-corpus-v2"
SOURCE_SCHEMA = "gemma3-newsroom-recirculation-pilot-input-v2"
SELECTION_POLICY = "next-four-after-v1-eligible-newsroom-test-records-v1"
SPEC = PilotSpec(
    state_slice=STATE_SLICE,
    claim_ceiling=CLAIM_CEILING,
    corpus_schema=CORPUS_SCHEMA,
    source_schema=SOURCE_SCHEMA,
    protocol="mechanism-only-newsroom-256-token-independent-pilot-v2",
    selection_offset=4,
    selection_policy=SELECTION_POLICY,
)
VALIDATOR = Path(__file__).with_name("validate_gemma3_local_pilot_v2.py")
DEFAULT_PRIMARY_ROOT = Path(
    "/Volumes/PrimaryED/ResearchArtifacts/composed-zk-benchmark-os/"
    "continual-learning-gemma3-local-pilot-v2-20260827-r1"
)
DEFAULT_DAED_ROOT = Path(
    "/Volumes/DAed/Archives/composed-zk-benchmark-os/"
    "continual-learning-gemma3-local-pilot-v2-20260827-r1"
)


def run_campaign(
    primary_root: Path = DEFAULT_PRIMARY_ROOT,
    daed_root: Path = DEFAULT_DAED_ROOT,
    input_path: Path = DEFAULT_INPUT,
    model_path: Path = DEFAULT_MODEL,
) -> dict:
    return run_pilot_campaign(
        primary_root,
        daed_root,
        input_path,
        model_path,
        spec=SPEC,
        validator=VALIDATOR,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--primary-root", type=Path, default=DEFAULT_PRIMARY_ROOT)
    parser.add_argument("--daed-root", type=Path, default=DEFAULT_DAED_ROOT)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--model", type=Path, default=DEFAULT_MODEL)
    args = parser.parse_args()
    print(
        json.dumps(
            run_campaign(args.primary_root, args.daed_root, args.input, args.model),
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
