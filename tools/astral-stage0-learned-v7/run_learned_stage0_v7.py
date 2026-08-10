"""Run the V7 recipe panel and fresh qualification."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from learned_stage0_v7 import (
    QUALIFICATION_SEEDS, RECIPES, SELECTION_SEEDS, STATE_SLICE,
    reproduce, select_recipe,
)


def canonical(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode()


def write(path: Path, value: object) -> None:
    path.write_bytes(canonical(value))


def prepare(root: Path, repo: Path) -> Path:
    if root.is_symlink():
        raise ValueError("output must be real")
    root, repo = root.resolve(), repo.resolve()
    if root == repo or repo in root.parents:
        raise ValueError("output must be repository-external")
    if root.exists() and (not root.is_dir() or any(root.iterdir())):
        raise ValueError("output must be empty")
    root.mkdir(parents=True, exist_ok=True)
    return root


def finalize(root: Path, summary: dict[str, object]) -> dict[str, object]:
    write(root / "summary.json", summary)
    files = []
    for path in sorted(root.iterdir()):
        raw = path.read_bytes()
        files.append({"bytes": len(raw), "path": path.name, "sha256": hashlib.sha256(raw).hexdigest()})
    write(root / "manifest.json", {"files": files, "state_slice": STATE_SLICE})
    return summary


def run(root: Path, repo: Path, protocol: Path) -> dict[str, object]:
    root = prepare(root, repo)
    write(root / "protocol.lock.json", {
        "protocol_sha256": hashlib.sha256(protocol.read_bytes()).hexdigest(),
        "state_slice": STATE_SLICE,
    })
    selection = []
    for recipe in RECIPES:
        for seed in SELECTION_SEEDS:
            row = reproduce(recipe, seed)
            selection.append(row)
            write(root / f"selection-{recipe.recipe_id}-{seed}.json", row)
    selected = select_recipe(selection)
    if selected is None:
        return finalize(root, {
            "accepted_evidence": False, "classification": "TrainingRecipePanelFailed",
            "selection": selection, "stage0_pass": False, "state_slice": STATE_SLICE,
        })
    lock = {"recipe_id": selected.recipe_id, "state_slice": STATE_SLICE}
    write(root / "selection.lock.json", lock)
    qualification = []
    for seed in QUALIFICATION_SEEDS:
        row = reproduce(selected, seed)
        qualification.append(row)
        write(root / f"qualification-{seed}.json", row)
        if not row["eligible"]:
            return finalize(root, {
                "accepted_evidence": False, "classification": "FreshQualificationFailed",
                "qualification": qualification, "selected_recipe": selected.recipe_id,
                "stage0_pass": False, "state_slice": STATE_SLICE,
            })
    write(root / "qualification.lock.json", {
        "recipe_id": selected.recipe_id, "seeds": list(QUALIFICATION_SEEDS),
        "state_slice": STATE_SLICE,
    })
    return finalize(root, {
        "accepted_evidence": False, "classification": "ActorTrainingRecipeQualified",
        "qualification": qualification, "selected_recipe": selected.recipe_id,
        "stage0_pass": False, "state_slice": STATE_SLICE,
    })


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--protocol", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(run(args.output, args.repo, args.protocol), indent=2, sort_keys=True))
