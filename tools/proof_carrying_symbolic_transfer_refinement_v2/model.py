"""Canonical data model for the closed-world synthetic evaluator.

State slice: proof-carrying-symbolic-transfer-refinement-v2.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any

SCHEMA_VERSION = "proof-carrying-symbolic-transfer-refinement-v2"
PRIMITIVES = (0, 1, 2, 3)


def canonical_json(value: Any) -> str:
    """Return the only JSON representation accepted by this lane."""

    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def digest_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def digest_json(value: Any) -> str:
    return digest_bytes(canonical_json(value).encode("utf-8"))


def digest_file(path: str) -> str:
    with open(path, "rb") as handle:
        return digest_bytes(handle.read())


@dataclass(frozen=True)
class PublicTask:
    task_id: str
    family_id: str
    public_examples: tuple[tuple[int, int], ...]
    assessment_inputs: tuple[int, ...]
    max_depth: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "family_id": self.family_id,
            "public_examples": [[x, y] for x, y in self.public_examples],
            "assessment_inputs": list(self.assessment_inputs),
            "max_depth": self.max_depth,
        }


@dataclass(frozen=True)
class TruthTask:
    public: PublicTask
    hidden_program: tuple[int, ...]
    assessment_outputs: tuple[int, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            **self.public.to_dict(),
            "hidden_program": list(self.hidden_program),
            "assessment_outputs": list(self.assessment_outputs),
        }


@dataclass(frozen=True)
class Episode:
    split: str
    seed: int
    tasks: tuple[TruthTask, ...]

    def to_dict(self) -> dict[str, Any]:
        return {"split": self.split, "seed": self.seed, "tasks": [task.to_dict() for task in self.tasks]}


@dataclass(frozen=True)
class Discovery:
    task_id: str
    discovery_id: str
    program: tuple[int, ...]
    reported_metric: float | None = None

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "task_id": self.task_id,
            "discovery_id": self.discovery_id,
            "program": list(self.program),
        }
        if self.reported_metric is not None:
            result["reported_metric"] = self.reported_metric
        return result


def parse_public_task(value: dict[str, Any]) -> PublicTask:
    if set(value) != {"task_id", "family_id", "public_examples", "assessment_inputs", "max_depth", "hidden_program", "assessment_outputs"}:
        raise ValueError("task schema is not canonical")
    return PublicTask(
        task_id=value["task_id"],
        family_id=value["family_id"],
        public_examples=tuple((int(x), int(y)) for x, y in value["public_examples"]),
        assessment_inputs=tuple(int(x) for x in value["assessment_inputs"]),
        max_depth=int(value["max_depth"]),
    )


def parse_episode(value: dict[str, Any]) -> Episode:
    if set(value) != {"split", "seed", "tasks"}:
        raise ValueError("episode schema is not canonical")
    tasks = []
    for raw in value["tasks"]:
        public = parse_public_task(raw)
        tasks.append(
            TruthTask(
                public=public,
                hidden_program=tuple(int(token) for token in raw["hidden_program"]),
                assessment_outputs=tuple(int(output) for output in raw["assessment_outputs"]),
            )
        )
    return Episode(split=value["split"], seed=int(value["seed"]), tasks=tuple(tasks))


def public_view(episode: Episode) -> tuple[PublicTask, ...]:
    return tuple(task.public for task in episode.tasks)


def replace_truth(episode: Episode, replacement: tuple[int, ...]) -> Episode:
    """Change hidden truth while preserving every public byte."""

    tasks = tuple(
        TruthTask(
            public=task.public,
            hidden_program=replacement,
            assessment_outputs=tuple(apply_program(replacement, x) for x in task.public.assessment_inputs),
        )
        for task in episode.tasks
    )
    return Episode(split=episode.split, seed=episode.seed, tasks=tasks)


def apply_program(program: tuple[int, ...], value: int) -> int:
    result = value
    for token in program:
        if token == 0:
            result += 1
        elif token == 1:
            result *= 2
        elif token == 2:
            result -= 1
        elif token == 3:
            result *= result
        else:
            raise ValueError(f"unknown primitive token: {token}")
        if abs(result) > 10**9:
            raise ValueError("program output exceeds bounded integer domain")
    return result
