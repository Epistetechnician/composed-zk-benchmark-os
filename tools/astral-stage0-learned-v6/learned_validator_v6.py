"""Structural and metric validator for V6."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from learned_stage0_v6 import (
    BASELINES, DEVELOPMENT_FAMILIES, EXPLORATORY_SEEDS, METHODS, NEW_METHODS,
    STATE_SLICE, normalized_regret, selected,
)
from run_learned_stage0_v6 import metrics


def load(path: Path):
    raw = path.read_bytes()
    value = json.loads(raw)
    expected = (json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode()
    if raw != expected:
        raise ValueError("noncanonical JSON")
    return value


def validate(root: Path, protocol: Path) -> dict[str, object]:
    manifest = load(root / "manifest.json")
    actual = sorted(path.name for path in root.iterdir() if path.name != "manifest.json")
    if sorted(row["path"] for row in manifest["files"]) != actual:
        raise ValueError("file census drift")
    for row in manifest["files"]:
        raw = (root / row["path"]).read_bytes()
        if row["bytes"] != len(raw) or row["sha256"] != hashlib.sha256(raw).hexdigest():
            raise ValueError("digest drift")
    lock = load(root / "protocol.lock.json")
    if lock["protocol_sha256"] != hashlib.sha256(protocol.read_bytes()).hexdigest():
        raise ValueError("protocol drift")
    summary = load(root / "summary.json")
    if summary.get("classification") == "ExploratoryQualificationFailed":
        qualification = summary.get("qualification", [])
        if not qualification or qualification[-1].get("eligible") is not False:
            raise ValueError("qualification failure drift")
        if any(path.name.startswith("scores-") or path.name == "records.jsonl" for path in root.iterdir()):
            raise ValueError("failed qualification opened measurement phase")
        return {
            "classification": "ExploratoryQualificationFailed",
            "selected_method": None,
            "valid": True,
        }
    records = [json.loads(line) for line in (root / "records.jsonl").read_bytes().splitlines()]
    if len(records) != 1536:
        raise ValueError("record census drift")
    expected = {
        (seed, family, f"f{family:03d}-b{packed:02d}")
        for seed in EXPLORATORY_SEEDS
        for family in DEVELOPMENT_FAMILIES
        for packed in range(16)
    }
    if {(row["seed"], row["family"], row["example_id"]) for row in records} != expected:
        raise ValueError("development example census drift")
    all_methods = (*METHODS, *BASELINES, *(f"permuted_{method}" for method in NEW_METHODS))
    for row in records:
        for method in all_methods:
            regret, informative = normalized_regret(row["ablation_effects"], row["scores"][method])
            if abs(regret - row["regrets"][method]) > 1e-7:
                raise ValueError("regret drift")
            if selected(row["scores"][method]) != row["selections"][method]:
                raise ValueError("selection drift")
            if informative != row["informative"]:
                raise ValueError("informative drift")
    recomputed = metrics(records)
    for key, value in recomputed.items():
        if summary[key] != value:
            raise ValueError(f"summary drift: {key}")
    if summary["stage0_pass"] or summary["accepted_evidence"]:
        raise ValueError("claim escalation")
    return {
        "classification": summary["classification"],
        "selected_method": summary["selected_method"],
        "valid": True,
    }
