"""Development-only actor training stability recipes for V7."""

from __future__ import annotations

import copy
from dataclasses import dataclass
import hashlib
import math
from pathlib import Path
import sys

import torch
from torch import nn

TOOLS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS / "astral-stage0-learned"))
sys.path.insert(0, str(TOOLS / "astral-stage0-learned-v3"))
from learned_stage0 import configure_runtime, examples_for, tensors  # noqa: E402
from learned_stage0_v3 import (  # noqa: E402
    CONFIGS, CapacityTransformer, parameter_count, semantic_digest,
    trajectory_digest,
)

STATE_SLICE = "astral-stage0-exploratory-actor-training-stability-v7"
SELECTION_SEEDS = (157, 163, 167)
QUALIFICATION_SEEDS = (191, 193, 197)
TEST_SEED = 227
RESERVED_SEEDS = (173, 179, 181)


@dataclass(frozen=True)
class TrainingRecipe:
    recipe_id: str
    sampler: str
    updates: int


RECIPES = (
    TrainingRecipe("iid-2000", "iid", 2_000),
    TrainingRecipe("family-complete-2000", "family_complete", 2_000),
    TrainingRecipe("family-complete-4000", "family_complete", 4_000),
)


def batch_indices(recipe: TrainingRecipe, generator: torch.Generator) -> torch.Tensor:
    if recipe.sampler == "iid":
        return torch.randint(2_560, (128,), generator=generator)
    if recipe.sampler == "family_complete":
        families = torch.randint(160, (8,), generator=generator)
        packed = torch.arange(16)
        return (families[:, None] * 16 + packed[None, :]).reshape(-1)
    raise ValueError("unknown sampler")


def train_recipe(
    recipe: TrainingRecipe, seed: int, updates_override: int | None = None
) -> tuple[CapacityTransformer, dict[str, object]]:
    allowed = set(SELECTION_SEEDS) | set(QUALIFICATION_SEEDS) | {TEST_SEED}
    if seed not in allowed or seed in RESERVED_SEEDS:
        raise ValueError("seed is not authorized for V7")
    updates = recipe.updates if updates_override is None else updates_override
    if updates <= 0 or updates % 25:
        raise ValueError("updates must be a positive multiple of 25")
    configure_runtime()
    torch.manual_seed(seed)
    model = CapacityTransformer(CONFIGS[0], seed)
    train_rows = examples_for(range(0, 160))
    dev_rows = examples_for(range(160, 192))
    if any(row.family >= 192 for row in (*train_rows, *dev_rows)):
        raise RuntimeError("family boundary breached")
    train_x, train_y = tensors(train_rows)
    dev_x, dev_y = tensors(dev_rows)
    optimizer = torch.optim.AdamW(model.parameters(), lr=.003, weight_decay=.01)
    generator = torch.Generator().manual_seed(seed)
    batch_digest = hashlib.sha256()
    best_loss, best_step, best_state = float("inf"), 0, None
    trajectory = []
    for step in range(1, updates + 1):
        model.train()
        indices = batch_indices(recipe, generator)
        batch_digest.update(indices.numpy().tobytes())
        optimizer.zero_grad(set_to_none=True)
        loss = nn.functional.cross_entropy(model(train_x[indices])[0], train_y[indices])
        if not torch.isfinite(loss):
            raise RuntimeError("nonfinite training loss")
        loss.backward()
        nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        optimizer.step()
        if step % 25 == 0:
            model.eval()
            with torch.no_grad():
                dev_loss = float(nn.functional.cross_entropy(model(dev_x)[0], dev_y))
            if not math.isfinite(dev_loss):
                raise RuntimeError("nonfinite development loss")
            trajectory.append({"dev_loss": dev_loss, "step": step})
            if dev_loss < best_loss:
                best_loss, best_step = dev_loss, step
                best_state = copy.deepcopy(model.state_dict())
    if best_state is None:
        raise RuntimeError("checkpoint selection failed")
    model.load_state_dict(best_state)
    model.eval()
    with torch.no_grad():
        train_accuracy = float((model(train_x)[0].argmax(1) == train_y).float().mean())
        dev_accuracy = float((model(dev_x)[0].argmax(1) == dev_y).float().mean())
    return model, {
        "batch_plan_sha256": batch_digest.hexdigest(),
        "checkpoint_sha256": semantic_digest(model),
        "dev_accuracy": dev_accuracy,
        "eligible": train_accuracy >= .95 and dev_accuracy >= .95,
        "parameter_count": parameter_count(CONFIGS[0]),
        "recipe_id": recipe.recipe_id,
        "selected_dev_loss": best_loss,
        "selected_step": best_step,
        "seed": seed,
        "train_accuracy": train_accuracy,
        "trajectory_sha256": trajectory_digest(trajectory),
        "updates": updates,
    }


def reproduce(recipe: TrainingRecipe, seed: int) -> dict[str, object]:
    _, first = train_recipe(recipe, seed)
    _, second = train_recipe(recipe, seed)
    reproducible = all(
        first[key] == second[key]
        for key in (
            "batch_plan_sha256", "checkpoint_sha256", "selected_step",
            "trajectory_sha256",
        )
    )
    return {
        "eligible": bool(first["eligible"] and second["eligible"] and reproducible),
        "first": first, "recipe_id": recipe.recipe_id,
        "reproducible": reproducible, "second": second, "seed": seed,
    }


def select_recipe(records: list[dict[str, object]]) -> TrainingRecipe | None:
    for recipe in RECIPES:
        rows = [row for row in records if row["recipe_id"] == recipe.recipe_id]
        if [row["seed"] for row in rows] == list(SELECTION_SEEDS) and all(
            row["eligible"] for row in rows
        ):
            return recipe
    return None
