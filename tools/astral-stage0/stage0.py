"""Deterministic planted-circuit Stage 0 measurement-validity harness."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
import random
from typing import Iterable

STATE_SLICE = "astral-stage0-compiled-circuit-measurement-validity"
SEEDS = (11, 23, 37)
FAMILY_COUNT = 64
COMPONENTS = ("layer0.attn.distractor", "layer0.attn.signal")
METHODS = ("activation_magnitude", "candidate_tracer", "reversed_tracer", "zero")
PRACTICAL_MARGIN = 0.50
BOOTSTRAP_DRAWS = 2_000
DEAD_ZONE = 1e-12


@dataclass(frozen=True)
class Example:
    example_id: str
    seed: int
    family: int
    signal: int
    distractor: int
    split: str

    @property
    def expected_label(self) -> int:
        return self.signal


@dataclass(frozen=True)
class Forward:
    logits: tuple[float, float]
    hooks: dict[str, float]

    @property
    def label(self) -> int:
        return int(self.logits[1] > self.logits[0])


class PlantedTwoHeadActor:
    """Frozen transformer-shaped residual circuit with two attention heads."""

    actor_id = "astral.planted-two-head.v1"

    def __init__(self, seed: int) -> None:
        if seed not in SEEDS:
            raise ValueError("unregistered actor seed")
        rng = random.Random(seed)
        self.seed = seed
        self.signal_scale = 0.90 + rng.random() * 0.20
        self.distractor_scale = 3.50 + rng.random()
        self.signal_readout = 3.0 / self.signal_scale
        self.distractor_readout = 0.05 / self.distractor_scale

    def forward(
        self, example: Example, overrides: dict[str, float] | None = None
    ) -> Forward:
        overrides = {} if overrides is None else dict(overrides)
        unknown = set(overrides).difference(COMPONENTS)
        if unknown:
            raise ValueError(f"unknown intervention components: {sorted(unknown)}")
        signal = self.signal_scale * (1.0 if example.signal else -1.0)
        distractor = self.distractor_scale * (
            1.0 if example.distractor else -1.0
        )
        signal = _finite_override(overrides, "layer0.attn.signal", signal)
        distractor = _finite_override(
            overrides, "layer0.attn.distractor", distractor
        )
        signed_margin = (
            self.signal_readout * signal
            + self.distractor_readout * distractor
        )
        return Forward(
            logits=(-signed_margin / 2.0, signed_margin / 2.0),
            hooks={
                "layer0.attn.distractor": distractor,
                "layer0.attn.signal": signal,
            },
        )

    def task_margin(self, example: Example, result: Forward) -> float:
        raw = result.logits[1] - result.logits[0]
        return raw if example.expected_label == 1 else -raw

    def ablation_effect(self, example: Example, component: str) -> float:
        _require_component(component)
        base = self.task_margin(example, self.forward(example))
        changed = self.task_margin(example, self.forward(example, {component: 0.0}))
        return changed - base

    def patch_effect(
        self, example: Example, donor: Example, component: str
    ) -> float:
        _require_component(component)
        if example.seed != donor.seed or example.family != donor.family:
            raise ValueError("patch donor must match seed and family")
        if example.distractor != donor.distractor or example.signal == donor.signal:
            raise ValueError("patch donor must preserve distractor and flip signal")
        donor_value = self.forward(donor).hooks[component]
        base = self.task_margin(example, self.forward(example))
        changed = self.task_margin(
            example, self.forward(example, {component: donor_value})
        )
        return changed - base

    def tracer_effect(self, example: Example, component: str) -> float:
        _require_component(component)
        hook = self.forward(example).hooks[component]
        weight = (
            self.signal_readout
            if component == "layer0.attn.signal"
            else self.distractor_readout
        )
        orientation = 1.0 if example.expected_label == 1 else -1.0
        return -orientation * hook * weight


def _finite_override(
    overrides: dict[str, float], component: str, default: float
) -> float:
    value = overrides.get(component, default)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError("intervention value must be numeric")
    value = float(value)
    if not math.isfinite(value):
        raise ValueError("intervention value must be finite")
    return value


def _require_component(component: str) -> None:
    if component not in COMPONENTS:
        raise ValueError("unknown component")


def generate_examples() -> list[Example]:
    rows = []
    for seed in SEEDS:
        for family in range(FAMILY_COUNT):
            split = "development" if family % 4 == 0 else "evaluation"
            for signal in (0, 1):
                for distractor in (0, 1):
                    rows.append(
                        Example(
                            example_id=f"s{seed}-f{family:02d}-x{signal}{distractor}",
                            seed=seed,
                            family=family,
                            signal=signal,
                            distractor=distractor,
                            split=split,
                        )
                    )
    return rows


def matched_donor(example: Example, examples: Iterable[Example]) -> Example:
    candidates = [
        row
        for row in examples
        if row.seed == example.seed
        and row.family == example.family
        and row.distractor == example.distractor
        and row.signal != example.signal
        and row.split == example.split
    ]
    if len(candidates) != 1:
        raise ValueError("matched donor census must equal one")
    return candidates[0]


def method_predictions(
    actor: PlantedTwoHeadActor, example: Example
) -> dict[str, dict[str, float]]:
    hooks = actor.forward(example).hooks
    tracer = {
        component: actor.tracer_effect(example, component)
        for component in COMPONENTS
    }
    return {
        "activation_magnitude": {
            component: abs(hooks[component]) for component in COMPONENTS
        },
        "candidate_tracer": tracer,
        "reversed_tracer": {
            COMPONENTS[0]: tracer[COMPONENTS[1]],
            COMPONENTS[1]: tracer[COMPONENTS[0]],
        },
        "zero": {component: 0.0 for component in COMPONENTS},
    }


def selected_component(scores: dict[str, float]) -> str:
    if set(scores) != set(COMPONENTS):
        raise ValueError("score candidate census drift")
    return min(
        COMPONENTS, key=lambda component: (-abs(scores[component]), component)
    )


def selection_regret(
    measured: dict[str, float], predicted: dict[str, float]
) -> float:
    best = max(abs(value) for value in measured.values())
    return best - abs(measured[selected_component(predicted)])


def percentile(values: list[float], probability: float) -> float:
    ordered = sorted(values)
    index = (len(ordered) - 1) * probability
    lower = math.floor(index)
    upper = math.ceil(index)
    if lower == upper:
        return ordered[lower]
    fraction = index - lower
    return ordered[lower] * (1.0 - fraction) + ordered[upper] * fraction


def family_bootstrap_interval(
    family_differences: dict[int, float], draws: int = BOOTSTRAP_DRAWS
) -> tuple[float, float]:
    families = sorted(family_differences)
    rng = random.Random(20260726)
    estimates = []
    for _ in range(draws):
        sample = [families[rng.randrange(len(families))] for _ in families]
        estimates.append(
            sum(family_differences[family] for family in sample) / len(sample)
        )
    return percentile(estimates, 0.025), percentile(estimates, 0.975)


def canonical_json_bytes(value: object) -> bytes:
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)
        + "\n"
    ).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()
