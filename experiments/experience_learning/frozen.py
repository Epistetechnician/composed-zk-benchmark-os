"""Sealed V2 learner configuration.

State slice: ``oaklab-experience-learning-benchmark-v2``. Hyperparameters are
declared once, hashed, and reused unchanged for every seed and assessment.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass


STATE_SLICE = "oaklab-experience-learning-benchmark-v2"
CONFIG_VERSION = "oaklab.experience-learning.config.v2"


DEFAULT_HYPERPARAMETERS = {
    "sgd_b1": {"learning_rate": 0.03}, "sgd_b32": {"learning_rate": 0.03},
    "sgd_b128": {"learning_rate": 0.03}, "adam_b1": {"learning_rate": 0.01},
    "adam_b32": {"learning_rate": 0.01}, "adam_b128": {"learning_rate": 0.01},
    "idbd": {"meta_step": 0.01, "initial_step": 0.03},
    "networkidbd": {"hidden_size": 8, "meta_step": 0.002, "initial_step": 0.01},
    "tidbd": {"gamma": 0.9, "meta_step": 0.01, "initial_step": 0.03, "trace_decay": 0.8},
    "replay_sgd": {"capacity": 64, "replay_ratio": 1, "learning_rate": 0.03},
    "ewc_sgd": {"learning_rate": 0.03, "ewc_lambda": 2.0},
    "plasticity_guard": {"learning_rate": 0.03, "guard_floor": 0.2, "recovery": 0.02, "surprise_threshold": 1.0},
    "event_driven": {"learning_rate": 0.03, "threshold": 0.5},
}


@dataclass(frozen=True)
class FrozenHyperparameters:
    algorithms: dict[str, dict]
    version: str = CONFIG_VERSION
    status: str = "sealed"

    def canonical(self) -> dict:
        return {"version": self.version, "status": self.status, "algorithms": self.algorithms}

    @property
    def digest(self) -> str:
        encoded = json.dumps(self.canonical(), sort_keys=True, separators=(",", ":")).encode()
        return hashlib.sha256(encoded).hexdigest()


DEFAULT_FROZEN = FrozenHyperparameters({key: dict(value) for key, value in DEFAULT_HYPERPARAMETERS.items()})
