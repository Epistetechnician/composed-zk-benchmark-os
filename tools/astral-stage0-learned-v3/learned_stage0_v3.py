"""Development-only actor-capacity qualification for learned Stage 0 V3."""

from __future__ import annotations

import copy
import hashlib
import json
import math
from dataclasses import dataclass
from pathlib import Path
import sys

import torch
from torch import nn

V1_ROOT = Path(__file__).resolve().parents[1] / "astral-stage0-learned"
sys.path.insert(0, str(V1_ROOT))
from learned_stage0 import configure_runtime, examples_for, tensors  # noqa: E402

STATE_SLICE = "astral-stage0-exploratory-actor-capacity-qualification-v3"
CLAIM_CLASS = "LocalExploratoryActorCapacityDiagnostic"
SELECTION_SEEDS = (67, 71, 73)
QUALIFICATION_SEEDS = (79, 83, 89)
TEST_SEED = 131
FUTURE_SCIENTIFIC_SEEDS = (109, 113, 127)
UPDATES = 2_000
CHECKPOINT_INTERVAL = 25


@dataclass(frozen=True)
class ActorConfig:
    architecture_id: str
    blocks: int
    width: int
    feed_forward_width: int


CONFIGS = (
    ActorConfig("a-width32-block1", 1, 32, 64),
    ActorConfig("b-width64-block1", 1, 64, 128),
    ActorConfig("c-width64-block2", 2, 64, 128),
)


class AttentionBlock(nn.Module):
    def __init__(self, width: int, feed_forward_width: int) -> None:
        super().__init__()
        self.width = width
        self.head_width = width // 4
        self.q = nn.Linear(width, width, bias=False)
        self.k = nn.Linear(width, width, bias=False)
        self.v = nn.Linear(width, width, bias=False)
        self.out = nn.Linear(width, width, bias=False)
        self.norm1 = nn.LayerNorm(width)
        self.ff = nn.Sequential(
            nn.Linear(width, feed_forward_width),
            nn.GELU(),
            nn.Linear(feed_forward_width, width),
        )
        self.norm2 = nn.LayerNorm(width)

    def forward(
        self, residual: torch.Tensor
    ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        batch, length, _ = residual.shape
        query = self.q(residual).view(batch, length, 4, self.head_width).transpose(1, 2)
        key = self.k(residual).view(batch, length, 4, self.head_width).transpose(1, 2)
        value = self.v(residual).view(batch, length, 4, self.head_width).transpose(1, 2)
        attention = (query @ key.transpose(-2, -1) / math.sqrt(self.head_width)).softmax(-1)
        attended = attention @ value
        merged = attended.transpose(1, 2).reshape(batch, length, self.width)
        residual = self.norm1(residual + self.out(merged))
        residual = self.norm2(residual + self.ff(residual))
        return residual, attended[:, :, 0, :], attention[:, :, 0, :]


class CapacityTransformer(nn.Module):
    def __init__(self, config: ActorConfig, seed: int) -> None:
        super().__init__()
        if config.width % 4:
            raise ValueError("width must be divisible by four heads")
        torch.manual_seed(seed)
        self.architecture_id = config.architecture_id
        self.embedding = nn.Embedding(32, config.width)
        self.position = nn.Parameter(torch.randn(12, config.width) * 0.02)
        self.blocks = nn.ModuleList(
            AttentionBlock(config.width, config.feed_forward_width)
            for _ in range(config.blocks)
        )
        self.classifier = nn.Linear(config.width, 2)

    def forward(
        self, tokens: torch.Tensor
    ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        residual = self.embedding(tokens) + self.position
        heads = attention = None
        for block in self.blocks:
            residual, heads, attention = block(residual)
        if heads is None or attention is None:
            raise RuntimeError("actor must contain an attention block")
        return self.classifier(residual[:, 0, :]), heads, attention


def semantic_digest(model: nn.Module) -> str:
    digest = hashlib.sha256()
    for name, value in sorted(model.state_dict().items()):
        tensor = value.detach().cpu().contiguous()
        digest.update(name.encode())
        digest.update(str(tensor.dtype).encode())
        digest.update(json.dumps(list(tensor.shape)).encode())
        digest.update(tensor.numpy().tobytes())
    return digest.hexdigest()


def trajectory_digest(rows: list[dict[str, float | int]]) -> str:
    raw = (json.dumps(rows, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode()
    return hashlib.sha256(raw).hexdigest()


def parameter_count(config: ActorConfig) -> int:
    return sum(
        parameter.numel()
        for parameter in CapacityTransformer(config, 0).parameters()
        if parameter.requires_grad
    )


def train_selected(
    config: ActorConfig, seed: int, updates: int = UPDATES
) -> tuple[CapacityTransformer, dict[str, object]]:
    if seed in FUTURE_SCIENTIFIC_SEEDS:
        raise ValueError("future scientific seed is sealed")
    if updates <= 0 or updates % CHECKPOINT_INTERVAL:
        raise ValueError("updates must be a positive multiple of checkpoint interval")
    configure_runtime()
    torch.manual_seed(seed)
    model = CapacityTransformer(config, seed)
    train_rows = examples_for(range(0, 160))
    dev_rows = examples_for(range(160, 192))
    if any(row.family >= 192 for row in (*train_rows, *dev_rows)):
        raise RuntimeError("development-only family boundary breached")
    train_x, train_y = tensors(train_rows)
    dev_x, dev_y = tensors(dev_rows)
    optimizer = torch.optim.AdamW(model.parameters(), lr=0.003, weight_decay=0.01)
    generator = torch.Generator().manual_seed(seed)
    best_loss = float("inf")
    best_step = 0
    best_state = None
    trajectory: list[dict[str, float | int]] = []
    model.train()
    for step in range(1, updates + 1):
        indices = torch.randint(len(train_rows), (128,), generator=generator)
        optimizer.zero_grad(set_to_none=True)
        logits, _, _ = model(train_x[indices])
        loss = nn.functional.cross_entropy(logits, train_y[indices])
        if not torch.isfinite(loss):
            raise RuntimeError("nonfinite training loss")
        loss.backward()
        nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        optimizer.step()
        if not all(torch.isfinite(parameter).all() for parameter in model.parameters()):
            raise RuntimeError("nonfinite model parameter")
        if step % CHECKPOINT_INTERVAL == 0:
            model.eval()
            with torch.no_grad():
                dev_loss = float(nn.functional.cross_entropy(model(dev_x)[0], dev_y))
            if not math.isfinite(dev_loss):
                raise RuntimeError("nonfinite development loss")
            trajectory.append({"dev_loss": dev_loss, "step": step})
            if dev_loss < best_loss:
                best_loss = dev_loss
                best_step = step
                best_state = copy.deepcopy(model.state_dict())
            model.train()
    if best_state is None:
        raise RuntimeError("checkpoint selection failed")
    model.load_state_dict(best_state)
    model.eval()
    with torch.no_grad():
        train_accuracy = float((model(train_x)[0].argmax(1) == train_y).float().mean())
        dev_accuracy = float((model(dev_x)[0].argmax(1) == dev_y).float().mean())
    metrics = {
        "architecture_id": config.architecture_id,
        "checkpoint_sha256": semantic_digest(model),
        "dev_accuracy": dev_accuracy,
        "eligible": train_accuracy >= 0.95 and dev_accuracy >= 0.95,
        "parameter_count": parameter_count(config),
        "selected_dev_loss": best_loss,
        "selected_step": best_step,
        "seed": seed,
        "train_accuracy": train_accuracy,
        "trajectory_sha256": trajectory_digest(trajectory),
        "updates": updates,
    }
    return model, metrics


def reproduce(config: ActorConfig, seed: int) -> dict[str, object]:
    _, first = train_selected(config, seed)
    _, second = train_selected(config, seed)
    reproducible = all(
        first[key] == second[key]
        for key in ("checkpoint_sha256", "selected_step", "trajectory_sha256")
    )
    return {
        "architecture_id": config.architecture_id,
        "eligible": bool(first["eligible"] and second["eligible"] and reproducible),
        "first": first,
        "reproducible": reproducible,
        "second": second,
        "seed": seed,
    }


def select_architecture(records: list[dict[str, object]]) -> ActorConfig | None:
    eligible = []
    for config in CONFIGS:
        matching = [row for row in records if row["architecture_id"] == config.architecture_id]
        if [row["seed"] for row in matching] == list(SELECTION_SEEDS) and all(
            row["eligible"] for row in matching
        ):
            eligible.append(config)
    return min(eligible, key=lambda item: (parameter_count(item), item.architecture_id), default=None)
