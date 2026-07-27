"""Learned tiny-transformer Stage 0 experiment primitives."""

from __future__ import annotations

import hashlib
import json
import math
import random
from dataclasses import dataclass

import torch
from torch import nn

STATE_SLICE = "astral-stage0-learned-transformer-measurement-validity"
SEEDS = (11, 23, 37)
COMPONENTS = tuple(f"block0.attn.head{index}.cls" for index in range(4))
METHODS = (
    "activation_norm",
    "attention_mass",
    "candidate_grad_x_activation",
    "gradient_norm",
    "permuted_candidate",
    "zero",
)
COMPETITIVE = ("activation_norm", "attention_mass", "gradient_norm")
DEAD_ZONE = 1e-4


def configure_runtime() -> None:
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)


@dataclass(frozen=True)
class Example:
    example_id: str
    family: int
    bits: tuple[int, int, int, int]
    tokens: tuple[int, ...]
    causal_positions: tuple[int, ...]
    label: int
    split: str


def family_examples(family: int) -> list[Example]:
    rng = random.Random(20260726 + family)
    positions = rng.sample(range(1, 12), 4)
    template = [15] + [rng.randrange(16, 32) for _ in range(11)]
    split = (
        "train" if family < 160
        else "development" if family < 192
        else "reserved_audit" if family < 256
        else "evaluation"
    )
    rows = []
    for packed in range(16):
        bits = tuple((packed >> index) & 1 for index in range(4))
        tokens = template.copy()
        for tag, position in enumerate(positions):
            tokens[position] = 2 * tag + bits[tag]
        label = (bits[0] ^ bits[1]) ^ (bits[2] & bits[3])
        rows.append(
            Example(
                example_id=f"f{family:03d}-b{packed:02d}",
                family=family,
                bits=bits,
                tokens=tuple(tokens),
                causal_positions=tuple(sorted(positions)),
                label=label,
                split=split,
            )
        )
    return rows


def examples_for(families: range) -> list[Example]:
    return [row for family in families for row in family_examples(family)]


def tensors(rows: list[Example]) -> tuple[torch.Tensor, torch.Tensor]:
    return (
        torch.tensor([row.tokens for row in rows], dtype=torch.long),
        torch.tensor([row.label for row in rows], dtype=torch.long),
    )


class TinyTransformer(nn.Module):
    architecture_id = "astral.learned-tiny-transformer.v1"

    def __init__(self, seed: int) -> None:
        super().__init__()
        torch.manual_seed(seed)
        self.embedding = nn.Embedding(32, 32)
        self.position = nn.Parameter(torch.randn(12, 32) * 0.02)
        self.q = nn.Linear(32, 32, bias=False)
        self.k = nn.Linear(32, 32, bias=False)
        self.v = nn.Linear(32, 32, bias=False)
        self.out = nn.Linear(32, 32, bias=False)
        self.norm1 = nn.LayerNorm(32)
        self.ff = nn.Sequential(nn.Linear(32, 64), nn.GELU(), nn.Linear(64, 32))
        self.norm2 = nn.LayerNorm(32)
        self.classifier = nn.Linear(32, 2)

    def forward(
        self,
        tokens: torch.Tensor,
        overrides: dict[int, torch.Tensor] | None = None,
    ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        residual = self.embedding(tokens) + self.position
        batch = tokens.shape[0]
        query = self.q(residual).view(batch, 12, 4, 8).transpose(1, 2)
        key = self.k(residual).view(batch, 12, 4, 8).transpose(1, 2)
        value = self.v(residual).view(batch, 12, 4, 8).transpose(1, 2)
        attention = (
            query @ key.transpose(-2, -1) / math.sqrt(8)
        ).softmax(dim=-1)
        heads = (attention @ value)[:, :, 0, :]
        if overrides:
            unknown = set(overrides).difference(range(4))
            if unknown:
                raise ValueError("unknown attention head override")
            heads = heads.clone()
            for index, replacement in overrides.items():
                if replacement.shape != heads[:, index, :].shape:
                    raise ValueError("head override shape mismatch")
                if not torch.isfinite(replacement).all():
                    raise ValueError("head override must be finite")
                heads[:, index, :] = replacement
        cls = self.norm1(residual[:, 0, :] + self.out(heads.reshape(batch, 32)))
        cls = self.norm2(cls + self.ff(cls))
        return self.classifier(cls), heads, attention[:, :, 0, :]


def train_actor(seed: int) -> tuple[TinyTransformer, dict[str, float]]:
    torch.manual_seed(seed)
    model = TinyTransformer(seed)
    model.train()
    train_rows = examples_for(range(160))
    dev_rows = examples_for(range(160, 192))
    train_x, train_y = tensors(train_rows)
    dev_x, dev_y = tensors(dev_rows)
    optimizer = torch.optim.AdamW(
        model.parameters(), lr=0.003, weight_decay=0.01
    )
    generator = torch.Generator().manual_seed(seed)
    for _ in range(800):
        indices = torch.randint(
            len(train_rows), (128,), generator=generator
        )
        optimizer.zero_grad(set_to_none=True)
        logits, _, _ = model(train_x[indices])
        loss = nn.functional.cross_entropy(logits, train_y[indices])
        loss.backward()
        nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        optimizer.step()
    model.eval()
    with torch.no_grad():
        train_accuracy = float((model(train_x)[0].argmax(1) == train_y).float().mean())
        dev_accuracy = float((model(dev_x)[0].argmax(1) == dev_y).float().mean())
    return model, {
        "dev_accuracy": dev_accuracy,
        "train_accuracy": train_accuracy,
    }


def checkpoint_digest(model: TinyTransformer) -> str:
    digest = hashlib.sha256()
    for name, value in sorted(model.state_dict().items()):
        tensor = value.detach().cpu().contiguous()
        digest.update(name.encode())
        digest.update(str(tensor.dtype).encode())
        digest.update(json.dumps(list(tensor.shape)).encode())
        digest.update(tensor.numpy().tobytes())
    return digest.hexdigest()


def score_example(
    model: TinyTransformer, example: Example
) -> tuple[dict[str, dict[str, float]], float, list[float]]:
    tokens = torch.tensor([example.tokens], dtype=torch.long)
    logits, heads, attention = model(tokens)
    margin = logits[0, example.label] - logits[0, 1 - example.label]
    gradient = torch.autograd.grad(margin, heads)[0][0]
    capture = heads.detach()[0]
    tracer = -(gradient * capture).sum(dim=-1)
    activation = capture.norm(dim=-1)
    gradient_norm = gradient.norm(dim=-1)
    attention_mass = attention.detach()[0, :, list(example.causal_positions)].sum(dim=-1)
    permutation = list(range(4))
    random.Random(int(hashlib.sha256(example.example_id.encode()).hexdigest()[:16], 16)).shuffle(permutation)
    scores = {
        "activation_norm": activation.tolist(),
        "attention_mass": attention_mass.tolist(),
        "candidate_grad_x_activation": tracer.tolist(),
        "gradient_norm": gradient_norm.tolist(),
        "permuted_candidate": tracer[permutation].tolist(),
        "zero": [0.0] * 4,
    }
    return scores, float(margin.detach()), [float(value) for value in capture.flatten()]


def intervention_effects(
    model: TinyTransformer, example: Example
) -> tuple[list[float], list[float]]:
    tokens = torch.tensor([example.tokens], dtype=torch.long)
    with torch.no_grad():
        clean_logits, _, _ = model(tokens)
        clean_margin = clean_logits[0, example.label] - clean_logits[0, 1 - example.label]
        donor_bits = (1 - example.bits[0], *example.bits[1:])
        donor_packed = sum(bit << index for index, bit in enumerate(donor_bits))
        donor = family_examples(example.family)[donor_packed]
        donor_heads = model(torch.tensor([donor.tokens], dtype=torch.long))[1]
        ablations = []
        patches = []
        for index in range(4):
            zero = torch.zeros_like(donor_heads[:, index, :])
            changed = model(tokens, {index: zero})[0]
            patched = model(tokens, {index: donor_heads[:, index, :]})[0]
            ablations.append(
                float(changed[0, example.label] - changed[0, 1 - example.label] - clean_margin)
            )
            patches.append(
                float(patched[0, example.label] - patched[0, 1 - example.label] - clean_margin)
            )
    return ablations, patches


def selected(scores: list[float]) -> int:
    return min(range(4), key=lambda index: (-abs(scores[index]), index))


def normalized_regret(effects: list[float], scores: list[float]) -> tuple[float, bool]:
    oracle = max(abs(value) for value in effects)
    if oracle <= DEAD_ZONE:
        return 0.0, False
    chosen = abs(effects[selected(scores)])
    return max(0.0, min(1.0, (oracle - chosen) / oracle)), True


def canonical_json(value: object) -> bytes:
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)
        + "\n"
    ).encode()
