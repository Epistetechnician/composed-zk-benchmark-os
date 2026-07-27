"""Prospective actor-specific V15 primitives."""

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
sys.path.insert(0, str(TOOLS / "astral-stage0-causal-target-v13"))
from learned_stage0 import configure_runtime, examples_for, tensors  # noqa: E402
from learned_stage0_v3 import semantic_digest, trajectory_digest  # noqa: E402
from learned_stage0_v13 import (  # noqa: E402
    CausalTargetActor, OPERATORS, SITES, effect_rows, features, metric_summary,
    ridge_predict, telemetry_rows,
)

STATE_SLICE = "astral-stage0c-prospective-actor-specific-explainer-v15"
ACTOR_SEEDS = (263, 269, 271)
RESERVED_SEEDS = (173, 179, 181)
FIT_FAMILIES = range(664, 680)
OTHER_ACTOR_FAMILIES = range(664, 672)
ASSESSMENT_FAMILIES = range(680, 688)
RESERVED_FAMILIES = range(512, 576)
PRIOR_FAMILIES = range(576, 664)
METHODS = (
    "same_actor_telemetry", "other_actor_telemetry", "same_actor_activation",
    "same_actor_text_io", "same_actor_shuffled", "same_actor_constant",
)
PRACTICAL_MARGIN = 0.05


def authorized_families(families: range) -> bool:
    values = set(families)
    return bool(values) and values <= (set(FIT_FAMILIES) | set(ASSESSMENT_FAMILIES))


def batch_indices(generator: torch.Generator) -> torch.Tensor:
    families = torch.randint(160, (8,), generator=generator)
    return (families[:, None] * 16 + torch.arange(16)[None, :]).reshape(-1)


def train_actor(seed: int):
    if seed not in ACTOR_SEEDS or seed in RESERVED_SEEDS:
        raise ValueError("V15 accepts only frozen actor seeds")
    configure_runtime()
    torch.manual_seed(seed)
    actor = CausalTargetActor(seed)
    train_rows, dev_rows = examples_for(range(160)), examples_for(range(160, 192))
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
                best_loss, best_step, best_state = dev_loss, step, copy.deepcopy(actor.state_dict())
    if best_state is None:
        raise RuntimeError("checkpoint selection failed")
    actor.load_state_dict(best_state)
    actor.eval()
    with torch.no_grad():
        train_accuracy = float((actor(train_x)[0].argmax(1) == train_y).float().mean())
        dev_accuracy = float((actor(dev_x)[0].argmax(1) == dev_y).float().mean())
    return actor, {
        "batch_plan_sha256": plan.hexdigest(), "checkpoint_sha256": semantic_digest(actor),
        "dev_accuracy": dev_accuracy, "eligible": train_accuracy >= .95 and dev_accuracy >= .95,
        "recipe_id": "family-complete-2000", "selected_dev_loss": best_loss,
        "selected_step": best_step, "seed": seed, "train_accuracy": train_accuracy,
        "trajectory_sha256": trajectory_digest(trajectory),
    }


def reproduce(seed: int):
    actor, first = train_actor(seed)
    _, second = train_actor(seed)
    keys = ("batch_plan_sha256", "checkpoint_sha256", "selected_step", "trajectory_sha256")
    reproducible = all(first[key] == second[key] for key in keys)
    return actor, {
        "eligible": bool(first["eligible"] and second["eligible"] and reproducible),
        "first": first, "reproducible": reproducible, "second": second, "seed": seed,
    }


def shuffled_features(rows: list[dict[str, object]], target_seed: int):
    matrix = [features(row, "telemetry") for row in rows]
    result = [values.copy() for values in matrix]
    for kind in ("head", "mlp"):
        for operator in OPERATORS:
            indices = [
                index for index, row in enumerate(rows)
                if ("head" if str(row["site"]).startswith("head") else "mlp") == kind
                and row["operator"] == operator
            ]
            generator = torch.Generator().manual_seed(
                int(hashlib.sha256(f"v15:{target_seed}:{kind}:{operator}".encode()).hexdigest()[:15], 16)
            )
            permutation = torch.randperm(len(indices), generator=generator).tolist()
            for offset, index in enumerate(indices):
                result[index][16:] = matrix[indices[permutation[offset]]][16:]
    return result


def constant_predictions(train, test):
    means = {}
    for site in SITES:
        for operator in OPERATORS:
            values = [float(row["effect"]) for row in train if row["site"] == site and row["operator"] == operator]
            means[site, operator] = sum(values) / len(values)
    return [means[row["site"], row["operator"]] for row in test]
