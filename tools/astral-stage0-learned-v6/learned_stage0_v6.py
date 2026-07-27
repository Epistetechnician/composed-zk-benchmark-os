"""Development-only attribution method panel for V6."""

from __future__ import annotations

import hashlib
import math
from pathlib import Path
import random
import sys

import torch

TOOLS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS / "astral-stage0-learned"))
sys.path.insert(0, str(TOOLS / "astral-stage0-learned-v3"))
sys.path.insert(0, str(TOOLS / "astral-stage0-learned-v5"))
from learned_stage0 import (  # noqa: E402
    intervention_effects, normalized_regret, selected, examples_for,
)
from learned_stage0_v3 import CONFIGS, train_selected as train_v3  # noqa: E402
from learned_stage0_v5 import FrozenScientificTransformer  # noqa: E402

STATE_SLICE = "astral-stage0-exploratory-attribution-method-development-v6"
EXPLORATORY_SEEDS = (157, 163, 167)
TEST_SEED = 151
FUTURE_SEEDS = (173, 179, 181)
DEVELOPMENT_FAMILIES = range(160, 192)
ASSESSMENT_FAMILIES = range(176, 192)
METHODS = (
    "signed_dot_legacy",
    "absolute_product_l1",
    "absolute_product_l2",
    "absolute_product_linf",
    "sign_coherent_mass",
)
NEW_METHODS = METHODS[1:]
BASELINES = ("activation_norm", "attention_mass", "gradient_norm")


def train_actor(seed: int) -> tuple[FrozenScientificTransformer, dict[str, object]]:
    if seed not in EXPLORATORY_SEEDS:
        raise ValueError("V6 training accepts only exploratory seeds")
    base, metrics = train_v3(CONFIGS[0], seed, updates=2_000)
    actor = FrozenScientificTransformer(seed)
    actor.load_state_dict(base.state_dict())
    actor.eval()
    return actor, metrics


def reproduce(seed: int) -> tuple[FrozenScientificTransformer, dict[str, object]]:
    actor, first = train_actor(seed)
    _, second = train_actor(seed)
    reproducible = all(
        first[key] == second[key]
        for key in ("checkpoint_sha256", "selected_step", "trajectory_sha256")
    )
    return actor, {
        "eligible": bool(first["eligible"] and second["eligible"] and reproducible),
        "first": first, "reproducible": reproducible, "second": second, "seed": seed,
    }


def score_example(actor: FrozenScientificTransformer, example) -> dict[str, list[float]]:
    tokens = torch.tensor([example.tokens], dtype=torch.long)
    logits, heads, attention = actor(tokens)
    margin = logits[0, example.label] - logits[0, 1 - example.label]
    gradient = torch.autograd.grad(margin, heads)[0][0]
    capture = heads.detach()[0]
    product = -(gradient * capture)
    scores = {
        "signed_dot_legacy": product.sum(-1),
        "absolute_product_l1": product.abs().sum(-1),
        "absolute_product_l2": product.square().sum(-1).sqrt(),
        "absolute_product_linf": product.abs().amax(-1),
        "sign_coherent_mass": torch.maximum(
            product.clamp_min(0).sum(-1), (-product).clamp_min(0).sum(-1)
        ),
        "activation_norm": capture.norm(dim=-1),
        "attention_mass": attention.detach()[0, :, list(example.causal_positions)].sum(-1),
        "gradient_norm": gradient.norm(dim=-1),
    }
    result = {name: value.tolist() for name, value in scores.items()}
    for method in NEW_METHODS:
        permutation = list(range(4))
        key = f"{example.example_id}:{method}".encode()
        random.Random(int(hashlib.sha256(key).hexdigest()[:16], 16)).shuffle(permutation)
        result[f"permuted_{method}"] = [result[method][index] for index in permutation]
    if not all(math.isfinite(value) for values in result.values() for value in values):
        raise RuntimeError("nonfinite attribution score")
    return result


def effects(actor, example):
    return intervention_effects(actor, example)
