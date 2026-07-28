"""Development-only training qualification for learned Stage 0 V2."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import sys

import torch
from torch import nn

V1_ROOT = Path(__file__).resolve().parents[1] / "astral-stage0-learned"
sys.path.insert(0, str(V1_ROOT))
from learned_stage0 import (  # noqa: E402
    TinyTransformer, checkpoint_digest, configure_runtime, examples_for, tensors,
)

QUALIFICATION_SEEDS = (41, 43, 47, 53, 59)
CONFIRMATORY_SEEDS = (11, 23, 37)
STATE_SLICE = "astral-stage0-training-qualification-and-independent-replication-v2"


def _trajectory_digest(rows: list[dict[str, float | int]]) -> str:
    raw = (
        json.dumps(rows, sort_keys=True, separators=(",", ":"), allow_nan=False)
        + "\n"
    ).encode()
    return hashlib.sha256(raw).hexdigest()


def train_selected(seed: int) -> tuple[TinyTransformer, dict[str, object]]:
    configure_runtime()
    torch.manual_seed(seed)
    model = TinyTransformer(seed)
    train_rows = examples_for(range(160))
    dev_rows = examples_for(range(160, 192))
    train_x, train_y = tensors(train_rows)
    dev_x, dev_y = tensors(dev_rows)
    optimizer = torch.optim.AdamW(
        model.parameters(), lr=0.003, weight_decay=0.01
    )
    generator = torch.Generator().manual_seed(seed)
    best_loss = float("inf")
    best_step = 0
    best_state = None
    trajectory = []
    model.train()
    for step in range(1, 1_501):
        indices = torch.randint(
            len(train_rows), (128,), generator=generator
        )
        optimizer.zero_grad(set_to_none=True)
        logits, _, _ = model(train_x[indices])
        loss = nn.functional.cross_entropy(logits, train_y[indices])
        if not torch.isfinite(loss):
            raise RuntimeError("nonfinite training loss")
        loss.backward()
        nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        optimizer.step()
        if step % 25 == 0:
            model.eval()
            with torch.no_grad():
                dev_loss = float(nn.functional.cross_entropy(model(dev_x)[0], dev_y))
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
        "checkpoint_sha256": checkpoint_digest(model),
        "dev_accuracy": dev_accuracy,
        "selected_dev_loss": best_loss,
        "selected_step": best_step,
        "train_accuracy": train_accuracy,
        "trajectory_sha256": _trajectory_digest(trajectory),
    }
    return model, metrics


def qualify_seed(seed: int) -> tuple[TinyTransformer, dict[str, object]]:
    first_model, first = train_selected(seed)
    _, second = train_selected(seed)
    reproducible = (
        first["checkpoint_sha256"] == second["checkpoint_sha256"]
        and first["trajectory_sha256"] == second["trajectory_sha256"]
        and first["selected_step"] == second["selected_step"]
    )
    eligible = (
        reproducible
        and first["train_accuracy"] >= 0.95
        and first["dev_accuracy"] >= 0.95
    )
    return first_model, {
        "eligible": eligible,
        "first": first,
        "reproducible": reproducible,
        "second": second,
    }
