"""V10 actors: V5 scientific forward plus V7 family-complete training."""

from __future__ import annotations

import copy
import hashlib
import math
from pathlib import Path
import sys

import torch
from torch import nn

TOOLS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS / "astral-stage0-learned"))
sys.path.insert(0, str(TOOLS / "astral-stage0-learned-v3"))
sys.path.insert(0, str(TOOLS / "astral-stage0-learned-v5"))
sys.path.insert(0, str(TOOLS / "astral-stage0-learned-v6"))
from learned_stage0 import configure_runtime, examples_for, tensors  # noqa: E402
from learned_stage0_v3 import semantic_digest, trajectory_digest  # noqa: E402
from learned_stage0_v5 import FrozenScientificTransformer  # noqa: E402
from learned_stage0_v6 import (  # noqa: E402
    ASSESSMENT_FAMILIES, BASELINES, DEVELOPMENT_FAMILIES, METHODS, NEW_METHODS,
    effects, normalized_regret, score_example, selected,
)

STATE_SLICE = "astral-stage0-family-complete-method-development-v10"
EXPLORATORY_SEEDS = (157, 163, 167)
RESERVED_CONFIRMATION_SEEDS = (173, 179, 181)


def batch_indices(generator: torch.Generator) -> torch.Tensor:
    families = torch.randint(160, (8,), generator=generator)
    return (families[:, None] * 16 + torch.arange(16)[None, :]).reshape(-1)


def train_actor(seed: int) -> tuple[FrozenScientificTransformer, dict[str, object]]:
    if seed not in EXPLORATORY_SEEDS:
        raise ValueError("V10 accepts only frozen exploratory seeds")
    configure_runtime()
    torch.manual_seed(seed)
    actor = FrozenScientificTransformer(seed)
    train_rows = examples_for(range(0, 160))
    dev_rows = examples_for(range(160, 192))
    train_x, train_y = tensors(train_rows)
    dev_x, dev_y = tensors(dev_rows)
    optimizer = torch.optim.AdamW(actor.parameters(), lr=.003, weight_decay=.01)
    generator = torch.Generator().manual_seed(seed)
    plan = hashlib.sha256()
    best_loss, best_step, best_state = float("inf"), 0, None
    trajectory = []
    for step in range(1, 2_001):
        actor.train()
        indices = batch_indices(generator)
        plan.update(indices.numpy().tobytes())
        optimizer.zero_grad(set_to_none=True)
        loss = nn.functional.cross_entropy(actor(train_x[indices])[0], train_y[indices])
        if not torch.isfinite(loss):
            raise RuntimeError("nonfinite training loss")
        loss.backward()
        nn.utils.clip_grad_norm_(actor.parameters(), 1.0)
        optimizer.step()
        if step % 25 == 0:
            actor.eval()
            with torch.no_grad():
                dev_loss = float(nn.functional.cross_entropy(actor(dev_x)[0], dev_y))
            if not math.isfinite(dev_loss):
                raise RuntimeError("nonfinite development loss")
            trajectory.append({"dev_loss": dev_loss, "step": step})
            if dev_loss < best_loss:
                best_loss, best_step = dev_loss, step
                best_state = copy.deepcopy(actor.state_dict())
    if best_state is None:
        raise RuntimeError("checkpoint selection failed")
    actor.load_state_dict(best_state)
    actor.eval()
    with torch.no_grad():
        train_accuracy = float((actor(train_x)[0].argmax(1) == train_y).float().mean())
        dev_accuracy = float((actor(dev_x)[0].argmax(1) == dev_y).float().mean())
    return actor, {
        "batch_plan_sha256": plan.hexdigest(),
        "checkpoint_sha256": semantic_digest(actor),
        "dev_accuracy": dev_accuracy,
        "eligible": train_accuracy >= .95 and dev_accuracy >= .95,
        "recipe_id": "family-complete-2000",
        "selected_dev_loss": best_loss,
        "selected_step": best_step,
        "seed": seed,
        "train_accuracy": train_accuracy,
        "trajectory_sha256": trajectory_digest(trajectory),
    }


def reproduce(seed: int):
    actor, first = train_actor(seed)
    _, second = train_actor(seed)
    reproducible = all(
        first[key] == second[key]
        for key in ("batch_plan_sha256", "checkpoint_sha256", "selected_step", "trajectory_sha256")
    )
    return actor, {
        "eligible": bool(first["eligible"] and second["eligible"] and reproducible),
        "first": first, "reproducible": reproducible, "second": second, "seed": seed,
    }
