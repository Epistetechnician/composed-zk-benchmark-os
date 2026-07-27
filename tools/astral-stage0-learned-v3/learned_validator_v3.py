"""Validate V3 capacity-study artifacts without training actors."""

from __future__ import annotations

import json
from pathlib import Path

from learned_stage0_v3 import (
    CLAIM_CLASS,
    CONFIGS,
    QUALIFICATION_SEEDS,
    SELECTION_SEEDS,
    STATE_SLICE,
    parameter_count,
    select_architecture,
)

FORBIDDEN_KEYS = {"scores", "interventions", "bootstrap", "tracer"}


def _load(path: Path) -> object:
    return json.loads(path.read_text())


def validate(root: Path) -> dict[str, object]:
    protocol = _load(root / "protocol.json")
    outcome = _load(root / "outcome.json")
    if protocol["state_slice"] != STATE_SLICE or protocol["claim_class"] != CLAIM_CLASS:
        raise ValueError("claim boundary mismatch")
    if any(protocol[key] for key in ("accepted_evidence", "independent_replication", "scientific_verdict")):
        raise ValueError("claim escalation")
    selection = _load(root / "selection-matrix.json")
    expected_pairs = [
        (config.architecture_id, seed) for config in CONFIGS for seed in SELECTION_SEEDS
    ]
    actual_pairs = [(row["architecture_id"], row["seed"]) for row in selection]
    if actual_pairs != expected_pairs:
        raise ValueError("selection matrix census or order mismatch")
    for row in selection:
        if FORBIDDEN_KEYS.intersection(row):
            raise ValueError("scientific measurement field forbidden")
    selected = select_architecture(selection)
    if selected is None:
        if outcome["classification"] != "CapacityPanelFailed":
            raise ValueError("incorrect failed-panel classification")
        return outcome
    lock = _load(root / "selection.lock.json")
    if lock != {
        "architecture_id": selected.architecture_id,
        "parameter_count": parameter_count(selected),
        "state_slice": STATE_SLICE,
    }:
        raise ValueError("selection lock mismatch")
    qualification = outcome["qualification"]
    expected_prefix = list(QUALIFICATION_SEEDS[: len(qualification)])
    if [row["seed"] for row in qualification] != expected_prefix:
        raise ValueError("qualification seed order mismatch")
    if outcome["classification"] == "QualificationFailed":
        if qualification[-1]["eligible"]:
            raise ValueError("failure lacks failed terminal record")
        if (root / "qualification.lock.json").exists():
            raise ValueError("failed qualification cannot issue lock")
    elif outcome["classification"] == "ActorQualifiedForFuturePreregistration":
        if len(qualification) != len(QUALIFICATION_SEEDS) or not all(
            row["eligible"] for row in qualification
        ):
            raise ValueError("qualification lock lacks complete passes")
        _load(root / "qualification.lock.json")
    else:
        raise ValueError("unknown classification")
    return outcome
