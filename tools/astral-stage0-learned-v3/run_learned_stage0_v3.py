"""Run the preregistered V3 development-only capacity study."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import platform

import torch

from learned_stage0_v3 import (
    CLAIM_CLASS,
    CONFIGS,
    QUALIFICATION_SEEDS,
    SELECTION_SEEDS,
    STATE_SLICE,
    parameter_count,
    reproduce,
    select_architecture,
)


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n")


def prepare_output(root: Path) -> None:
    if root.is_symlink():
        raise ValueError("output must be an empty real directory")
    root = root.resolve()
    repository = Path(__file__).resolve().parents[2]
    if root == repository or repository in root.parents:
        raise ValueError("output must be repository-external")
    if root.exists():
        if not root.is_dir() or any(root.iterdir()):
            raise ValueError("output must be an empty real directory")
    else:
        root.mkdir(parents=True)


def run(root: Path) -> dict[str, object]:
    prepare_output(root)
    protocol = {
        "accepted_evidence": False,
        "claim_class": CLAIM_CLASS,
        "independent_replication": False,
        "platform": platform.platform(),
        "qualification_seeds": list(QUALIFICATION_SEEDS),
        "scientific_verdict": False,
        "selection_seeds": list(SELECTION_SEEDS),
        "state_slice": STATE_SLICE,
        "torch_version": torch.__version__,
    }
    write_json(root / "protocol.json", protocol)
    selection = []
    for config in CONFIGS:
        for seed in SELECTION_SEEDS:
            row = reproduce(config, seed)
            selection.append(row)
            write_json(root / f"selection-{config.architecture_id}-seed-{seed}.json", row)
    write_json(root / "selection-matrix.json", selection)
    selected = select_architecture(selection)
    if selected is None:
        outcome = {"classification": "CapacityPanelFailed", **protocol}
        write_json(root / "outcome.json", outcome)
        return outcome
    selection_lock = {
        "architecture_id": selected.architecture_id,
        "parameter_count": parameter_count(selected),
        "state_slice": STATE_SLICE,
    }
    write_json(root / "selection.lock.json", selection_lock)
    qualification = []
    for seed in QUALIFICATION_SEEDS:
        row = reproduce(selected, seed)
        qualification.append(row)
        write_json(root / f"qualification-seed-{seed}.json", row)
        if not row["eligible"]:
            outcome = {
                "classification": "QualificationFailed",
                "failed_seed": seed,
                "qualification": qualification,
                "selection_lock": selection_lock,
                **protocol,
            }
            write_json(root / "outcome.json", outcome)
            return outcome
    qualification_lock = {
        "architecture_id": selected.architecture_id,
        "qualification_seeds": list(QUALIFICATION_SEEDS),
        "state_slice": STATE_SLICE,
    }
    write_json(root / "qualification.lock.json", qualification_lock)
    outcome = {
        "classification": "ActorQualifiedForFuturePreregistration",
        "qualification": qualification,
        "qualification_lock": qualification_lock,
        "selection_lock": selection_lock,
        **protocol,
    }
    write_json(root / "outcome.json", outcome)
    return outcome


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    arguments = parser.parse_args()
    print(json.dumps(run(arguments.output), indent=2, sort_keys=True))
