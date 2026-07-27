"""Validate V7 selection and qualification artifacts."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from learned_stage0_v7 import QUALIFICATION_SEEDS, RECIPES, SELECTION_SEEDS, select_recipe


def load(path: Path):
    raw = path.read_bytes()
    value = json.loads(raw)
    if raw != (json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode():
        raise ValueError("noncanonical JSON")
    return value


def validate(root: Path, protocol: Path) -> dict[str, object]:
    manifest = load(root / "manifest.json")
    actual = sorted(path.name for path in root.iterdir() if path.name != "manifest.json")
    if sorted(row["path"] for row in manifest["files"]) != actual:
        raise ValueError("file census drift")
    for row in manifest["files"]:
        raw = (root / row["path"]).read_bytes()
        if len(raw) != row["bytes"] or hashlib.sha256(raw).hexdigest() != row["sha256"]:
            raise ValueError("digest drift")
    lock = load(root / "protocol.lock.json")
    if lock["protocol_sha256"] != hashlib.sha256(protocol.read_bytes()).hexdigest():
        raise ValueError("protocol drift")
    selection = [
        load(root / f"selection-{recipe.recipe_id}-{seed}.json")
        for recipe in RECIPES for seed in SELECTION_SEEDS
    ]
    selected = select_recipe(selection)
    summary = load(root / "summary.json")
    if selected is None:
        if summary["classification"] != "TrainingRecipePanelFailed":
            raise ValueError("panel verdict drift")
    else:
        if load(root / "selection.lock.json")["recipe_id"] != selected.recipe_id:
            raise ValueError("selection drift")
        qualification = summary["qualification"]
        if [row["seed"] for row in qualification] != list(QUALIFICATION_SEEDS[:len(qualification)]):
            raise ValueError("qualification order drift")
        if summary["classification"] == "FreshQualificationFailed":
            if qualification[-1]["eligible"] or (root / "qualification.lock.json").exists():
                raise ValueError("failed qualification drift")
        elif summary["classification"] == "ActorTrainingRecipeQualified":
            if len(qualification) != 3 or not all(row["eligible"] for row in qualification):
                raise ValueError("qualification success drift")
        else:
            raise ValueError("unknown classification")
    if summary["stage0_pass"] or summary["accepted_evidence"]:
        raise ValueError("claim escalation")
    return {"classification": summary["classification"], "selected_recipe": summary.get("selected_recipe"), "valid": True}
