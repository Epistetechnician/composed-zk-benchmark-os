#!/usr/bin/env python3
"""Leakage-controlled sequential retention and recovery benchmark.

This is a protocol harness, not a neural-training implementation.  It makes
the continual-learning endpoints executable before a model or training budget
is introduced.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, Iterable, Mapping, Optional


STRATEGIES = ("no_update", "context_only", "naive_sequential", "replay", "retrieval")


@dataclass(frozen=True)
class Fact:
    key: str
    value: str
    task_id: int


@dataclass(frozen=True)
class Task:
    task_id: int
    facts: tuple[Fact, ...]


@dataclass(frozen=True)
class ProtocolConfig:
    seed: int = 20260810
    task_count: int = 4
    facts_per_task: int = 16
    replay_capacity: int = 24


def _value(seed: int, task_id: int, index: int) -> str:
    digest = hashlib.sha256(f"{seed}:task:{task_id}:fact:{index}".encode()).hexdigest()
    return f"v-{digest[:12]}"


def make_tasks(config: ProtocolConfig = ProtocolConfig()) -> tuple[Task, ...]:
    """Create disjoint, deterministic fact families for the locked protocol."""

    if config.task_count < 2 or config.facts_per_task < 1:
        raise ValueError("task_count must be >= 2 and facts_per_task must be >= 1")
    tasks = []
    for task_id in range(config.task_count):
        facts = tuple(
            Fact(
                key=f"task-{task_id}-key-{index}",
                value=_value(config.seed, task_id, index),
                task_id=task_id,
            )
            for index in range(config.facts_per_task)
        )
        tasks.append(Task(task_id=task_id, facts=facts))
    return tuple(tasks)


class Learner:
    """Small deterministic stand-in for strategy and endpoint testing."""

    def __init__(self, strategy: str, config: ProtocolConfig):
        if strategy not in STRATEGIES:
            raise ValueError(f"unknown strategy: {strategy}")
        self.strategy = strategy
        self.config = config
        self.memory: Dict[str, str] = {}
        self.context: Dict[str, str] = {}

    def update(self, task: Task) -> None:
        self.context = {fact.key: fact.value for fact in task.facts}
        if self.strategy in ("no_update", "context_only"):
            return
        if self.strategy == "naive_sequential":
            self.memory = dict(self.context)
            return
        if self.strategy == "retrieval":
            self.memory.update(self.context)
            return

        # Deterministic replay control: every observed fact competes for a
        # fixed memory budget using a seed-bound, order-independent priority.
        self.memory.update(self.context)
        ranked = sorted(
            self.memory.items(),
            key=lambda item: hashlib.sha256(
                f"{self.config.seed}:replay:{item[0]}".encode()
            ).hexdigest(),
        )
        self.memory = dict(ranked[: self.config.replay_capacity])

    def answer(self, key: str, *, context_available: bool) -> Optional[str]:
        if self.strategy == "context_only":
            return self.context.get(key) if context_available else None
        return self.memory.get(key)


def _accuracy(learner: Learner, facts: Iterable[Fact], *, context_available: bool) -> dict:
    facts = tuple(facts)
    correct = sum(
        learner.answer(fact.key, context_available=context_available) == fact.value
        for fact in facts
    )
    return {"correct": correct, "n": len(facts), "accuracy": correct / len(facts) if facts else None}


def run_protocol(config: ProtocolConfig = ProtocolConfig()) -> dict:
    """Run acquisition, retention, and recovery with source context removed."""

    tasks = make_tasks(config)
    target = tasks[0].facts
    results = {}
    for strategy in STRATEGIES:
        learner = Learner(strategy, config)
        learner.update(tasks[0])
        acquisition = _accuracy(learner, target, context_available=False)
        acquisition_with_context = _accuracy(learner, target, context_available=True)
        for task in tasks[1:]:
            learner.update(task)
        retention = _accuracy(learner, target, context_available=False)
        interference = _accuracy(learner, tasks[-1].facts, context_available=False)
        memory_size_after_interference = len(learner.memory)
        learner.update(tasks[0])
        recovery = _accuracy(learner, target, context_available=False)
        results[strategy] = {
            "acquisition": acquisition,
            "acquisition_with_context": acquisition_with_context,
            "retention_after_interference": retention,
            "interference_task_accuracy": interference,
            "recovery_after_reacquisition": recovery,
            "memory_size_after_interference": memory_size_after_interference,
            "memory_size_after_recovery": len(learner.memory),
        }

    protocol = {
        "protocol": "continual-learning-sequential-retention-recovery-v1",
        "config": asdict(config),
        "task_ids": [task.task_id for task in tasks],
        "task_fact_counts": [len(task.facts) for task in tasks],
        "source_context_removed_for": ["acquisition", "retention_after_interference", "recovery_after_reacquisition"],
        "strategies": list(STRATEGIES),
        "results": results,
    }
    protocol_bytes = json.dumps(protocol, sort_keys=True, separators=(",", ":")).encode()
    protocol["protocol_sha256"] = hashlib.sha256(protocol_bytes).hexdigest()
    return protocol


def validate_protocol(result: Mapping) -> None:
    """Reject malformed or leakage-prone result bundles."""

    config = result["config"]
    expected_n = config["facts_per_task"]
    if result["source_context_removed_for"] != [
        "acquisition",
        "retention_after_interference",
        "recovery_after_reacquisition",
    ]:
        raise ValueError("source-context removal gate is not locked")
    if tuple(result["strategies"]) != STRATEGIES:
        raise ValueError("strategy panel is not locked")
    for strategy in STRATEGIES:
        metrics = result["results"][strategy]
        for endpoint in ("acquisition", "acquisition_with_context", "retention_after_interference", "interference_task_accuracy", "recovery_after_reacquisition"):
            if metrics[endpoint]["n"] != expected_n:
                raise ValueError(f"{strategy}/{endpoint} has the wrong denominator")
            if not 0 <= metrics[endpoint]["accuracy"] <= 1:
                raise ValueError(f"{strategy}/{endpoint} is outside [0, 1]")
        if metrics["memory_size_after_interference"] > config["replay_capacity"] and strategy == "replay":
            raise ValueError("replay capacity gate failed")
    unsigned = {key: value for key, value in result.items() if key != "protocol_sha256"}
    digest = hashlib.sha256(json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    if result.get("protocol_sha256") != digest:
        raise ValueError("protocol digest mismatch")


def markdown_report(result: Mapping) -> str:
    lines = [
        "# Continual-Learning Sequential Retention and Recovery v1",
        "",
        "Deterministic protocol harness; no neural training or external model execution.",
        "",
        f"Protocol SHA-256: `{result['protocol_sha256']}`",
        "",
        "| Strategy | Acquisition | Retention after interference | Recovery | Context-only acquisition |",
        "|---|---:|---:|---:|---:|",
    ]
    for strategy in STRATEGIES:
        metrics = result["results"][strategy]
        lines.append(
            f"| `{strategy}` | {metrics['acquisition']['accuracy']:.3f} | "
            f"{metrics['retention_after_interference']['accuracy']:.3f} | "
            f"{metrics['recovery_after_reacquisition']['accuracy']:.3f} | "
            f"{metrics['acquisition_with_context']['accuracy']:.3f} |"
        )
    lines.extend(
        [
            "",
            "Interpretation ceiling: protocol and control validation only. These results do not establish neural continual learning, transfer, production readiness, or a breakthrough.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--seed", type=int, default=ProtocolConfig.seed)
    parser.add_argument("--facts-per-task", type=int, default=ProtocolConfig.facts_per_task)
    parser.add_argument("--replay-capacity", type=int, default=ProtocolConfig.replay_capacity)
    args = parser.parse_args()
    config = ProtocolConfig(seed=args.seed, facts_per_task=args.facts_per_task, replay_capacity=args.replay_capacity)
    result = run_protocol(config)
    validate_protocol(result)
    payload = json.dumps(result, indent=2) + "\n"
    if args.output is None:
        print(payload, end="")
        return
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "result.json").write_text(payload, encoding="utf8")
    (args.output / "result.md").write_text(markdown_report(result), encoding="utf8")
    print(json.dumps({"output": str(args.output), "protocol_sha256": result["protocol_sha256"]}, indent=2))


if __name__ == "__main__":
    main()
