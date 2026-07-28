"""Frozen actor and measurement primitives for fresh-holdout V4."""

from __future__ import annotations

import copy
import math
from pathlib import Path
import sys

import torch
from torch import nn

TOOLS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS / "astral-stage0-learned"))
sys.path.insert(0, str(TOOLS / "astral-stage0-learned-v3"))
from learned_stage0 import (  # noqa: E402
    COMPETITIVE, METHODS, canonical_json, configure_runtime, examples_for,
    intervention_effects, normalized_regret, score_example, selected, tensors,
)
from learned_stage0_v3 import (  # noqa: E402
    CONFIGS, CapacityTransformer, semantic_digest, trajectory_digest,
)

STATE_SLICE = "astral-stage0-fresh-holdout-scientific-confirmation-v4"
SCIENTIFIC_SEEDS = (109, 113, 127)
EVALUATION_FAMILIES = range(384, 448)
FROZEN_CONFIG = CONFIGS[0]
UPDATES = 2_000


class FrozenScientificTransformer(CapacityTransformer):
    def __init__(self, seed: int) -> None:
        super().__init__(FROZEN_CONFIG, seed)

    def forward(
        self,
        tokens: torch.Tensor,
        overrides: dict[int, torch.Tensor] | None = None,
    ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        if not overrides:
            return super().forward(tokens)
        unknown = set(overrides).difference(range(4))
        if unknown:
            raise ValueError("unknown attention head override")
        residual = self.embedding(tokens) + self.position
        block = self.blocks[0]
        batch, length, _ = residual.shape
        query = block.q(residual).view(batch, length, 4, 8).transpose(1, 2)
        key = block.k(residual).view(batch, length, 4, 8).transpose(1, 2)
        value = block.v(residual).view(batch, length, 4, 8).transpose(1, 2)
        attention_full = (query @ key.transpose(-2, -1) / math.sqrt(8)).softmax(-1)
        attended = attention_full @ value
        heads = attended[:, :, 0, :].clone()
        for index, replacement in overrides.items():
            if replacement.shape != heads[:, index, :].shape:
                raise ValueError("head override shape mismatch")
            if not torch.isfinite(replacement).all():
                raise ValueError("head override must be finite")
            attended[:, index, 0, :] = replacement
            heads[:, index, :] = replacement
        merged = attended.transpose(1, 2).reshape(batch, length, 32)
        residual = block.norm1(residual + block.out(merged))
        residual = block.norm2(residual + block.ff(residual))
        return self.classifier(residual[:, 0, :]), heads, attention_full[:, :, 0, :]


def clean_parity(seed: int = 131) -> bool:
    base = CapacityTransformer(FROZEN_CONFIG, seed)
    actor = FrozenScientificTransformer(seed)
    actor.load_state_dict(base.state_dict())
    tokens, _ = tensors(examples_for(range(160, 161)))
    expected = base(tokens[:4])
    actual = actor(tokens[:4])
    return all(torch.equal(left, right) for left, right in zip(expected, actual))


def train_selected(seed: int) -> tuple[FrozenScientificTransformer, dict[str, object]]:
    if seed not in SCIENTIFIC_SEEDS:
        raise ValueError("V4 training accepts only frozen scientific seeds")
    configure_runtime()
    torch.manual_seed(seed)
    model = FrozenScientificTransformer(seed)
    train_rows = examples_for(range(0, 160))
    dev_rows = examples_for(range(160, 192))
    train_x, train_y = tensors(train_rows)
    dev_x, dev_y = tensors(dev_rows)
    optimizer = torch.optim.AdamW(model.parameters(), lr=0.003, weight_decay=0.01)
    generator = torch.Generator().manual_seed(seed)
    best_loss = float("inf")
    best_step = 0
    best_state = None
    trajectory = []
    for step in range(1, UPDATES + 1):
        model.train()
        indices = torch.randint(len(train_rows), (128,), generator=generator)
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
        "checkpoint_sha256": semantic_digest(model),
        "dev_accuracy": dev_accuracy,
        "eligible": train_accuracy >= 0.95 and dev_accuracy >= 0.95,
        "selected_dev_loss": best_loss,
        "selected_step": best_step,
        "seed": seed,
        "train_accuracy": train_accuracy,
        "trajectory_sha256": trajectory_digest(trajectory),
    }


def reproduce(seed: int) -> tuple[FrozenScientificTransformer, dict[str, object]]:
    model, first = train_selected(seed)
    _, second = train_selected(seed)
    reproducible = all(
        first[key] == second[key]
        for key in ("checkpoint_sha256", "selected_step", "trajectory_sha256")
    )
    return model, {
        "eligible": bool(first["eligible"] and second["eligible"] and reproducible),
        "first": first,
        "reproducible": reproducible,
        "second": second,
        "seed": seed,
    }
