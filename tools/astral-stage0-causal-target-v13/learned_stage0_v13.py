"""Prediction-locked V13 causal-target primitives."""

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

STATE_SLICE = "astral-stage0c-prediction-locked-causal-target-v13"
FIT_SEEDS = (239, 241)
ASSESSMENT_SEEDS = (251, 257)
ALL_SEEDS = FIT_SEEDS + ASSESSMENT_SEEDS
RESERVED_SEEDS = (173, 179, 181)
FIT_FAMILIES = range(640, 656)
ASSESSMENT_FAMILIES = range(656, 664)
RESERVED_FAMILIES = range(512, 576)
V12_FAMILIES = range(576, 640)
SITES = ("head0.cls", "head1.cls", "head2.cls", "head3.cls", "mlp.cls")
OPERATORS = ("zero_ablation", "matched_patch")
ESTIMATORS = ("constant", "text_io", "activation_only", "shuffled_telemetry", "telemetry")
RIDGE_ALPHA = 0.001
PRACTICAL_MARGIN = 0.05


def authorized_families(families: range) -> bool:
    values = set(families)
    allowed = set(FIT_FAMILIES) | set(ASSESSMENT_FAMILIES)
    return bool(values) and values <= allowed and not values.intersection(
        set(RESERVED_FAMILIES) | set(V12_FAMILIES)
    )


def batch_indices(generator: torch.Generator) -> torch.Tensor:
    families = torch.randint(160, (8,), generator=generator)
    return (families[:, None] * 16 + torch.arange(16)[None, :]).reshape(-1)


class CausalTargetActor(FrozenScientificTransformer):
    """The frozen actor with explicit pre-projection head and pre-residual MLP sites."""

    def forward_sites(
        self,
        tokens: torch.Tensor,
        override: tuple[str, torch.Tensor] | None = None,
    ) -> tuple[torch.Tensor, dict[str, torch.Tensor], torch.Tensor]:
        residual = self.embedding(tokens) + self.position
        block = self.blocks[0]
        batch, length, _ = residual.shape
        query = block.q(residual).view(batch, length, 4, 8).transpose(1, 2)
        key = block.k(residual).view(batch, length, 4, 8).transpose(1, 2)
        value = block.v(residual).view(batch, length, 4, 8).transpose(1, 2)
        attention = (query @ key.transpose(-2, -1) / math.sqrt(8)).softmax(-1)
        attended = attention @ value
        site_values = {f"head{index}.cls": attended[:, index, 0, :] for index in range(4)}
        if override and override[0].startswith("head"):
            site, replacement = override
            if site not in SITES[:-1]:
                raise ValueError("unknown head site")
            index = int(site[4])
            expected = attended[:, index, 0, :]
            _validate_replacement(replacement, expected)
            attended = attended.clone()
            attended[:, index, 0, :] = replacement
        merged = attended.transpose(1, 2).reshape(batch, length, 32)
        after_attention = block.norm1(residual + block.out(merged))
        mlp = block.ff(after_attention)
        site_values["mlp.cls"] = mlp[:, 0, :]
        if override and override[0] == "mlp.cls":
            replacement = override[1]
            expected = mlp[:, 0, :]
            _validate_replacement(replacement, expected)
            mlp = mlp.clone()
            mlp[:, 0, :] = replacement
        elif override and not override[0].startswith("head"):
            raise ValueError("unknown site")
        final = block.norm2(after_attention + mlp)
        return self.classifier(final[:, 0, :]), site_values, attention[:, :, 0, :]


def _validate_replacement(replacement: torch.Tensor, expected: torch.Tensor) -> None:
    if replacement.shape != expected.shape:
        raise ValueError("site override shape mismatch")
    if replacement.dtype != expected.dtype or replacement.device != expected.device:
        raise ValueError("site override dtype or device mismatch")
    if not torch.isfinite(replacement).all():
        raise ValueError("site override must be finite")


def clean_parity(actor: CausalTargetActor, tokens: torch.Tensor) -> bool:
    old = actor(tokens)
    new = actor.forward_sites(tokens)
    return (
        torch.equal(old[0], new[0])
        and all(torch.equal(old[1][:, index, :], new[1][f"head{index}.cls"]) for index in range(4))
        and torch.equal(old[2], new[2])
    )


def train_actor(seed: int) -> tuple[CausalTargetActor, dict[str, object]]:
    if seed not in ALL_SEEDS or seed in RESERVED_SEEDS:
        raise ValueError("V13 accepts only frozen development seeds")
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
            trajectory.append({"dev_loss": dev_loss, "step": step})
            if dev_loss < best_loss:
                best_loss, best_step, best_state = dev_loss, step, copy.deepcopy(actor.state_dict())
    if best_state is None:
        raise RuntimeError("checkpoint selection failed")
    actor.load_state_dict(best_state)
    actor.eval()
    if not clean_parity(actor, dev_x[:16]):
        raise RuntimeError("clean forward parity failed")
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


def telemetry_rows(actor: CausalTargetActor, example) -> list[dict[str, object]]:
    tokens = torch.tensor([example.tokens], dtype=torch.long)
    with torch.no_grad():
        logits, sites, attention = actor.forward_sites(tokens)
    clean_logits = [float(value) for value in logits[0]]
    rows = []
    for site in SITES:
        vector = sites[site].detach()[0]
        for operator in OPERATORS:
            rows.append({
                "bits": list(example.bits),
                "clean_logits": clean_logits,
                "example_id": example.example_id,
                "family": example.family,
                "label": example.label,
                "operator": operator,
                "site": site,
                "site_attention": (
                    float(attention[0, int(site[4]), list(example.causal_positions)].sum())
                    if site.startswith("head") else 0.0
                ),
                "site_max_abs": float(vector.abs().max()),
                "site_mean": float(vector.mean()),
                "site_norm": float(vector.norm()),
                "site_vector": [float(value) for value in vector],
            })
    return rows


def effect_rows(actor: CausalTargetActor, example) -> list[dict[str, object]]:
    tokens = torch.tensor([example.tokens], dtype=torch.long)
    donor_bits = (1 - example.bits[0], *example.bits[1:])
    donor = family_examples(example.family)[sum(bit << index for index, bit in enumerate(donor_bits))]
    with torch.no_grad():
        clean_logits, clean_sites, _ = actor.forward_sites(tokens)
        donor_sites = actor.forward_sites(torch.tensor([donor.tokens], dtype=torch.long))[1]
        clean_margin = clean_logits[0, example.label] - clean_logits[0, 1 - example.label]
        rows = []
        for site in SITES:
            for operator in OPERATORS:
                replacement = (
                    torch.zeros_like(clean_sites[site])
                    if operator == "zero_ablation" else donor_sites[site]
                )
                changed = actor.forward_sites(tokens, (site, replacement))[0]
                margin = changed[0, example.label] - changed[0, 1 - example.label]
                rows.append({
                    "donor_example_id": donor.example_id,
                    "effect": float(margin - clean_margin),
                    "example_id": example.example_id,
                    "family": example.family,
                    "operator": operator,
                    "site": site,
                })
    if len(rows) != 10 or not all(math.isfinite(float(row["effect"])) for row in rows):
        raise RuntimeError("invalid effect rows")
    return rows


def _shared(row: dict[str, object]) -> list[float]:
    bits = [float(value) for value in row["bits"]]
    return (
        bits
        + [float(value) for value in row["clean_logits"]]
        + [float(row["label"])]
        + [float(row["site"] == site) for site in SITES]
        + [float(row["operator"] == operator) for operator in OPERATORS]
        + [float(int(bits[0]) ^ int(bits[1])), float(int(bits[2]) & int(bits[3]))]
    )


def _telemetry_suffix(row: dict[str, object]) -> list[float]:
    vector = [float(value) for value in row["site_vector"]]
    if str(row["site"]).startswith("head"):
        return vector + [0.0] * (32 - len(vector))
    return vector


def features(row: dict[str, object], estimator: str) -> list[float]:
    shared = _shared(row)
    if estimator == "text_io":
        values = shared + [0.0] * 32
    elif estimator == "activation_only":
        values = shared + [
            float(row["site_norm"]), float(row["site_mean"]),
            float(row["site_max_abs"]), float(row["site_attention"]),
        ] + [0.0] * 28
    elif estimator in ("telemetry", "shuffled_telemetry"):
        values = shared + _telemetry_suffix(row)
    else:
        raise ValueError("unknown learned estimator")
    if len(values) != 48 or not all(math.isfinite(value) for value in values):
        raise RuntimeError("invalid feature vector")
    return values


def ridge_predict(train_x, train_y, test_x) -> list[float]:
    x = torch.tensor(train_x, dtype=torch.float64)
    y = torch.tensor(train_y, dtype=torch.float64)
    test = torch.tensor(test_x, dtype=torch.float64)
    mean = x.mean(0)
    scale = x.std(0, unbiased=False)
    scale = torch.where(scale < 1e-12, torch.ones_like(scale), scale)
    x, test = (x - mean) / scale, (test - mean) / scale
    design = torch.cat((torch.ones((len(x), 1), dtype=x.dtype), x), 1)
    test_design = torch.cat((torch.ones((len(test), 1), dtype=x.dtype), test), 1)
    penalty = torch.eye(design.shape[1], dtype=x.dtype) * RIDGE_ALPHA
    penalty[0, 0] = 0
    weights = torch.linalg.solve(design.T @ design + penalty, design.T @ y)
    result = (test_design @ weights).tolist()
    if not all(math.isfinite(value) for value in result):
        raise RuntimeError("nonfinite prediction")
    return result


def shuffled_train_features(rows: list[dict[str, object]]) -> list[list[float]]:
    matrix = [features(row, "telemetry") for row in rows]
    result = [values.copy() for values in matrix]
    for site in SITES:
        for operator in OPERATORS:
            indices = [
                index for index, row in enumerate(rows)
                if row["site"] == site and row["operator"] == operator
            ]
            generator = torch.Generator().manual_seed(
                int(hashlib.sha256(f"v13:{site}:{operator}".encode()).hexdigest()[:15], 16)
            )
            permutation = torch.randperm(len(indices), generator=generator).tolist()
            for offset, index in enumerate(indices):
                result[index][16:] = matrix[indices[permutation[offset]]][16:]
    return result


def metric_summary(actual: list[float], predicted: list[float]) -> dict[str, float | None]:
    a, p = torch.tensor(actual, dtype=torch.float64), torch.tensor(predicted, dtype=torch.float64)
    residual = a - p
    centered_a, centered_p = a - a.mean(), p - p.mean()
    total = float(centered_a.square().sum())
    denom = float(centered_a.norm() * centered_p.norm())
    pred_var = float(centered_p.square().sum())
    slope = float((centered_p * centered_a).sum()) / pred_var if pred_var > 0 else None
    return {
        "calibration_intercept": float(a.mean() - slope * p.mean()) if slope is not None else None,
        "calibration_slope": slope,
        "correlation": float((centered_a * centered_p).sum()) / denom if denom > 0 else None,
        "mae": float(residual.abs().mean()),
        "mse": float(residual.square().mean()),
        "r2": 1.0 - float(residual.square().sum()) / total if total > 0 else None,
    }
