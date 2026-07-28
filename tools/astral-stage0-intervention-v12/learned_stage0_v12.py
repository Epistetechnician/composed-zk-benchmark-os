"""Development-only Stage 0C intervention-effect prediction primitives."""

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
from learned_stage0 import configure_runtime, examples_for, family_examples, tensors  # noqa: E402
from learned_stage0_v3 import semantic_digest, trajectory_digest  # noqa: E402
from learned_stage0_v5 import FrozenScientificTransformer  # noqa: E402

STATE_SLICE = "astral-stage0c-intervention-effect-target-validity-v12"
EXPLORATORY_SEEDS = (211, 223, 229)
RESERVED_SEEDS = (173, 179, 181)
DESIGN_FAMILIES = range(576, 608)
ASSESSMENT_FAMILIES = range(608, 640)
RESERVED_FAMILIES = range(512, 576)
OPERATORS = ("zero_ablation", "matched_patch")
ESTIMATORS = (
    "constant", "input_output_only", "activation_only",
    "shuffled_telemetry", "telemetry",
)
RIDGE_ALPHA = 0.001
PRACTICAL_MARGIN = 0.05


def authorized_families(families: range) -> bool:
    values = set(families)
    allowed = set(DESIGN_FAMILIES) | set(ASSESSMENT_FAMILIES)
    return bool(values) and values <= allowed and not values.intersection(RESERVED_FAMILIES)


def batch_indices(generator: torch.Generator) -> torch.Tensor:
    families = torch.randint(160, (8,), generator=generator)
    return (families[:, None] * 16 + torch.arange(16)[None, :]).reshape(-1)


def train_actor(seed: int) -> tuple[FrozenScientificTransformer, dict[str, object]]:
    if seed not in EXPLORATORY_SEEDS or seed in RESERVED_SEEDS:
        raise ValueError("V12 accepts only frozen exploratory seeds")
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
    trajectory: list[dict[str, float | int]] = []
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
    keys = ("batch_plan_sha256", "checkpoint_sha256", "selected_step", "trajectory_sha256")
    reproducible = all(first[key] == second[key] for key in keys)
    return actor, {
        "eligible": bool(first["eligible"] and second["eligible"] and reproducible),
        "first": first, "reproducible": reproducible, "second": second, "seed": seed,
    }


def measure_example(actor: FrozenScientificTransformer, example) -> list[dict[str, object]]:
    tokens = torch.tensor([example.tokens], dtype=torch.long)
    logits, heads, attention = actor(tokens)
    margin = logits[0, example.label] - logits[0, 1 - example.label]
    gradient = torch.autograd.grad(margin, heads)[0][0]
    capture = heads.detach()[0]
    donor_bits = (1 - example.bits[0], *example.bits[1:])
    donor_packed = sum(bit << index for index, bit in enumerate(donor_bits))
    donor = family_examples(example.family)[donor_packed]
    with torch.no_grad():
        donor_heads = actor(torch.tensor([donor.tokens], dtype=torch.long))[1]
        clean_margin = float(margin.detach())
        clean_logits = [float(value) for value in logits.detach()[0]]
        rows = []
        for head in range(4):
            for operator in OPERATORS:
                replacement = (
                    torch.zeros_like(heads[:, head, :])
                    if operator == "zero_ablation"
                    else donor_heads[:, head, :]
                )
                changed = actor(tokens, {head: replacement})[0]
                changed_margin = changed[0, example.label] - changed[0, 1 - example.label]
                activation = capture[head]
                grad = gradient[head]
                rows.append({
                    "activation_max_abs": float(activation.abs().max()),
                    "activation_mean": float(activation.mean()),
                    "activation_norm": float(activation.norm()),
                    "attention_causal": float(attention.detach()[0, head, list(example.causal_positions)].sum()),
                    "bits": list(example.bits),
                    "clean_logits": clean_logits,
                    "clean_margin": clean_margin,
                    "donor_example_id": donor.example_id,
                    "effect": float(changed_margin - margin.detach()),
                    "example_id": example.example_id,
                    "family": example.family,
                    "gradient_mean": float(grad.mean()),
                    "gradient_norm": float(grad.norm()),
                    "grad_x_activation": float((grad * activation).sum()),
                    "head": head,
                    "label": example.label,
                    "operator": operator,
                })
    if len(rows) != 8 or not all(
        math.isfinite(value)
        for row in rows
        for value in row.values()
        if isinstance(value, float)
    ):
        raise RuntimeError("invalid intervention rows")
    return rows


def features(row: dict[str, object], estimator: str) -> list[float]:
    bits = [float(value) for value in row["bits"]]
    head = int(row["head"])
    operator = str(row["operator"])
    one_head = [float(index == head) for index in range(4)]
    one_operator = [float(name == operator) for name in OPERATORS]
    label = float(row["label"])
    prefix = bits + [float(row["clean_margin"])] + one_head + one_operator + [label]
    if estimator == "input_output_only":
        values = (
            bits + [float(value) for value in row["clean_logits"]]
            + [float(row["clean_margin"])] + one_head + one_operator + [label]
            + [float(int(bits[0]) ^ int(bits[1])), float(int(bits[2]) & int(bits[3]))]
        )
    elif estimator == "activation_only":
        values = prefix + [
            float(row["activation_norm"]), float(row["activation_mean"]),
            float(row["activation_max_abs"]), float(row["attention_causal"]),
        ]
    elif estimator in ("telemetry", "shuffled_telemetry"):
        values = prefix + [
            float(row["activation_norm"]), float(row["gradient_norm"]),
            float(row["grad_x_activation"]), float(row["attention_causal"]),
        ]
    else:
        raise ValueError("unknown learned estimator")
    if len(values) != 16 or not all(math.isfinite(value) for value in values):
        raise RuntimeError("invalid feature vector")
    return values


def _standardize_fit(matrix: torch.Tensor):
    mean = matrix.mean(0)
    scale = matrix.std(0, unbiased=False)
    scale = torch.where(scale < 1e-12, torch.ones_like(scale), scale)
    return (matrix - mean) / scale, mean, scale


def ridge_predict(
    train_x: list[list[float]], train_y: list[float], test_x: list[list[float]]
) -> list[float]:
    x = torch.tensor(train_x, dtype=torch.float64)
    y = torch.tensor(train_y, dtype=torch.float64)
    test = torch.tensor(test_x, dtype=torch.float64)
    standardized, mean, scale = _standardize_fit(x)
    test = (test - mean) / scale
    design = torch.cat((torch.ones((len(x), 1), dtype=x.dtype), standardized), 1)
    test_design = torch.cat((torch.ones((len(test), 1), dtype=x.dtype), test), 1)
    penalty = torch.eye(design.shape[1], dtype=x.dtype) * RIDGE_ALPHA
    penalty[0, 0] = 0
    weights = torch.linalg.solve(design.T @ design + penalty, design.T @ y)
    result = (test_design @ weights).tolist()
    if not all(math.isfinite(value) for value in result):
        raise RuntimeError("nonfinite prediction")
    return result


def shuffled_train_features(rows: list[dict[str, object]], fold_seed: int) -> list[list[float]]:
    matrix = [features(row, "telemetry") for row in rows]
    generator = torch.Generator().manual_seed(
        int(hashlib.sha256(f"v12:{fold_seed}".encode()).hexdigest()[:15], 16)
    )
    permutation = torch.randperm(len(matrix), generator=generator).tolist()
    return [values[:12] + matrix[permutation[index]][12:] for index, values in enumerate(matrix)]


def metric_summary(actual: list[float], predicted: list[float]) -> dict[str, float | None]:
    a = torch.tensor(actual, dtype=torch.float64)
    p = torch.tensor(predicted, dtype=torch.float64)
    residual = a - p
    mse = float(residual.square().mean())
    mae = float(residual.abs().mean())
    total = float((a - a.mean()).square().sum())
    r2 = 1.0 - float(residual.square().sum()) / total if total > 0 else None
    centered_a, centered_p = a - a.mean(), p - p.mean()
    denom = float(centered_a.norm() * centered_p.norm())
    correlation = float((centered_a * centered_p).sum()) / denom if denom > 0 else None
    pred_var = float(centered_p.square().sum())
    slope = float((centered_p * centered_a).sum()) / pred_var if pred_var > 0 else None
    intercept = float(a.mean() - (slope or 0.0) * p.mean()) if slope is not None else None
    return {
        "calibration_intercept": intercept, "calibration_slope": slope,
        "correlation": correlation, "mae": mae, "mse": mse, "r2": r2,
    }
