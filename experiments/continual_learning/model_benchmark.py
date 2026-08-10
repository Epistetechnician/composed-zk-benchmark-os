#!/usr/bin/env python3
"""Offline MLX continual-learning pilot with frozen evaluation boundaries."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable


STATE_SLICE = "continual-learning-model-adapter-v6-balanced-full-memory-replay"
LABELS = ("A", "B", "C", "D")
ANSWER_SUFFIX = "\nAnswer:"
DEFAULT_MODEL = Path(
    "/Users/shaanp/.lmstudio/models/mlx-community/Qwen2.5-0.5B-Instruct-4bit"
)
STRATEGIES = ("no_update", "context_only", "retrieval", "naive_sequential_lora", "replay_lora")


@dataclass(frozen=True)
class Fact:
    task_id: int
    fact_id: str
    label: str


@dataclass(frozen=True)
class Task:
    task_id: int
    facts: tuple[Fact, ...]


def digest(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def make_tasks(seed: int, task_count: int = 4, facts_per_task: int = 8) -> tuple[Task, ...]:
    if task_count < 4 or facts_per_task < 2:
        raise ValueError("task_count must be >= 4 and facts_per_task must be >= 2")
    tasks = []
    for task_id in range(task_count):
        label_order = sorted(
            LABELS,
            key=lambda label: hashlib.sha256(
                f"{seed}:task:{task_id}:label:{label}".encode()
            ).hexdigest(),
        )
        facts = []
        for index in range(facts_per_task):
            token = hashlib.sha256(f"{seed}:task:{task_id}:fact:{index}".encode()).hexdigest()
            facts.append(
                Fact(task_id=task_id, fact_id=f"F{task_id}{index}{token[:5]}", label=label_order[index % len(label_order)])
            )
        tasks.append(Task(task_id=task_id, facts=tuple(facts)))
    return tuple(tasks)


def prompt_for(fact: Fact, variant: str = "direct", context: Iterable[Fact] = ()) -> str:
    context = tuple(context)
    reference = ""
    if context:
        reference = "Reference facts:\n" + "\n".join(
            f"- {item.fact_id} maps to option {item.label}." for item in context
        ) + "\n\n"
    if variant == "direct":
        query = f"What option is stored for identifier {fact.fact_id}?"
    elif variant == "paraphrase":
        query = f"Select the memorized choice associated with code {fact.fact_id}."
    else:
        raise ValueError(f"unknown prompt variant: {variant}")
    return (
        "Answer with exactly one letter: A, B, C, or D.\n"
        f"{reference}{query}\n"
        "Return only the letter."
        f"{ANSWER_SUFFIX}"
    )


def training_example(fact: Fact) -> dict[str, str]:
    return {
        # The supervised prefix is byte-identical to the direct assessment
        # prompt. The label is the only masked completion.
        "prompt": prompt_for(fact),
        "completion": f" {fact.label}",
    }


def choose_replay(
    previous: Iterable[Fact], capacity: int, seed: int, limit: int | None = None
) -> list[Fact]:
    """Select a bounded, task-stratified, deterministic replay sample."""

    facts = list(previous)
    groups: dict[int, list[Fact]] = {}
    for fact in facts:
        groups.setdefault(fact.task_id, []).append(fact)
    if not groups or capacity <= 0:
        return []
    task_ids = sorted(groups)
    quota, remainder = divmod(capacity, len(task_ids))
    pool: list[Fact] = []
    for index, task_id in enumerate(task_ids):
        ranked = sorted(
            groups[task_id],
            key=lambda fact: hashlib.sha256(
                f"{seed}:replay:{fact.fact_id}".encode()
            ).hexdigest(),
        )
        pool.extend(ranked[: quota + int(index < remainder)])
    pool = pool[:capacity]
    if limit is None or limit >= len(pool):
        return pool
    by_task = {task_id: [fact for fact in pool if fact.task_id == task_id] for task_id in task_ids}
    selected: list[Fact] = []
    while len(selected) < limit:
        progressed = False
        for task_id in task_ids:
            if by_task[task_id]:
                selected.append(by_task[task_id].pop(0))
                progressed = True
                if len(selected) == limit:
                    break
        if not progressed:
            break
    return selected


def replay_counts_by_task(facts: Iterable[Fact]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for fact in facts:
        key = str(fact.task_id)
        counts[key] = counts.get(key, 0) + 1
    return dict(sorted(counts.items()))


def choose_balanced_full_replay(
    previous: Iterable[Fact], capacity: int, limit: int | None = None
) -> list[Fact]:
    """Return every prior fact once, ordered deterministically by task and id."""

    if capacity <= 0:
        return []
    facts = sorted(previous, key=lambda fact: (fact.task_id, fact.fact_id))
    selected = facts[:capacity]
    return selected if limit is None else selected[:limit]


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf8")


def write_dataset(path: Path, rows: list[dict[str, str]]) -> None:
    path.mkdir(parents=True, exist_ok=False)
    # Keep the update budget and validation shape explicit. Training uses the
    # same rows as validation only for this adapter smoke/pilot; assessment
    # answers are never read by mlx_lm.
    for name in ("train.jsonl", "valid.jsonl", "test.jsonl"):
        with (path / name).open("w", encoding="utf8") as handle:
            for row in rows:
                handle.write(json.dumps(row, sort_keys=True) + "\n")


def training_command(
    model: Path,
    dataset: Path,
    adapter_path: Path,
    seed: int,
    iters: int,
    resume: Path | None,
) -> list[str]:
    command = [
        sys.executable,
        "-m",
        "mlx_lm",
        "lora",
        "--model",
        str(model),
        "--train",
        "--data",
        str(dataset),
        "--fine-tune-type",
        "lora",
        "--optimizer",
        "adamw",
        "--mask-prompt",
        "--num-layers",
        "8",
        "--batch-size",
        "2",
        "--iters",
        str(iters),
        "--learning-rate",
        "0.0001",
        "--steps-per-report",
        str(max(1, min(10, iters))),
        "--steps-per-eval",
        str(max(1, min(20, iters))),
        "--val-batches",
        "-1",
        "--max-seq-length",
        "192",
        "--adapter-path",
        str(adapter_path),
        "--save-every",
        str(iters),
        "--seed",
        str(seed),
    ]
    if resume is not None:
        command.extend(["--resume-adapter-file", str(resume)])
    return command


def train_sequence(
    root: Path,
    model: Path,
    tasks: tuple[Task, ...],
    order: tuple[int, ...],
    strategy: str,
    seed: int,
    iters: int,
    replay_capacity: int,
    update_budget: int,
) -> list[Path]:
    data_root = root / "data" / strategy
    adapter_root = root / "adapters" / strategy
    data_root.mkdir(parents=True, exist_ok=False)
    adapter_root.mkdir(parents=True, exist_ok=False)
    audit_root = root / "audit"
    audit_root.mkdir(exist_ok=True)
    task_by_id = {task.task_id: task for task in tasks}
    observed: list[Fact] = []
    previous_adapter: Path | None = None
    adapter_paths: list[Path] = []
    updates: list[dict[str, Any]] = []
    for step, task_id in enumerate(order):
        current = list(task_by_id[task_id].facts)
        if strategy == "naive_sequential_lora":
            selected = current
        elif strategy == "replay_lora":
            replay = choose_balanced_full_replay(
                observed,
                replay_capacity,
                limit=update_budget - len(current),
            )
            selected = current + replay
        else:
            raise ValueError(f"training strategy not supported: {strategy}")
        if not selected:
            raise ValueError("empty update set")
        replay_facts = [fact for fact in selected if fact not in current]
        rows = [training_example(fact) for fact in selected]
        # Equalize the number of examples per update. Repetition is explicit
        # and deterministic, so replay does not receive a hidden budget.
        rows = (rows * ((update_budget + len(rows) - 1) // len(rows)))[:update_budget]
        dataset = data_root / f"step-{step}"
        write_dataset(dataset, rows)
        adapter_path = adapter_root / f"step-{step}"
        command = training_command(
            model,
            dataset,
            adapter_path,
            seed + step,
            iters,
            previous_adapter / "adapters.safetensors" if previous_adapter else None,
        )
        env = os.environ.copy()
        env.update({"HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1"})
        completed = subprocess.run(command, env=env, text=True, capture_output=True, check=False)
        (adapter_path.parent / f"step-{step}.log").write_text(
            completed.stdout + "\n" + completed.stderr, encoding="utf8"
        )
        if completed.returncode != 0:
            raise RuntimeError(f"training failed for {strategy}/step-{step}: {completed.returncode}")
        checkpoint = ChoiceModel(model, adapter_path)
        checkpoint_result = accuracy(
            checkpoint, task_by_id[0].facts, "direct", "none"
        )
        updates.append(
            {
                "step": step,
                "task_id": task_id,
                "current_fact_ids": [fact.fact_id for fact in current],
                "replay_fact_ids": [fact.fact_id for fact in replay_facts],
                "selected_fact_ids": [fact.fact_id for fact in selected],
                "replay_counts_by_task": replay_counts_by_task(replay_facts),
                "dataset_row_count": len(rows),
                "target_task_id": 0,
                "target_task_accuracy_after_update": checkpoint_result,
            }
        )
        previous_adapter = adapter_path
        adapter_paths.append(adapter_path)
        observed.extend(current)
    write_json(audit_root / f"{strategy}.json", updates)
    return adapter_paths


class ChoiceModel:
    def __init__(self, model_path: Path, adapter_path: Path | None = None):
        import mlx.core as mx
        from mlx_lm import load

        self.mx = mx
        self.model, self.tokenizer = load(
            str(model_path),
            adapter_path=str(adapter_path) if adapter_path else None,
        )
        self.candidate_ids = {
            label: self.tokenizer.encode(f" {label}", add_special_tokens=False)
            for label in LABELS
        }
        if any(len(ids) != 1 for ids in self.candidate_ids.values()):
            raise RuntimeError(f"NotRunSingleTokenFailure:{self.candidate_ids}")

    def answer(self, prompt: str) -> dict[str, Any]:
        ids = self.tokenizer.encode(prompt, add_special_tokens=False)
        if len(ids) > 192:
            raise RuntimeError(f"NotRunSequenceLength:{len(ids)}")
        output = self.model(self.mx.array([ids]))
        self.mx.eval(output)
        logits = {
            label: float(output[0, -1, token_ids[0]])
            for label, token_ids in self.candidate_ids.items()
        }
        prediction = max(LABELS, key=lambda label: logits[label])
        return {"prediction": prediction, "logits": logits}


def accuracy(model: ChoiceModel, facts: Iterable[Fact], variant: str, context_mode: str) -> dict[str, Any]:
    facts = tuple(facts)
    correct = 0
    rows = []
    all_context = facts if context_mode == "all" else ()
    for fact in facts:
        context = all_context if context_mode == "all" else ((fact,) if context_mode == "one" else ())
        outcome = model.answer(prompt_for(fact, variant, context))
        hit = outcome["prediction"] == fact.label
        correct += int(hit)
        rows.append({"fact_id": fact.fact_id, "expected": fact.label, "observed": outcome["prediction"], "correct": hit})
    return {"correct": correct, "n": len(facts), "accuracy": correct / len(facts) if facts else None, "rows": rows}


def exact_retrieval_accuracy(facts: Iterable[Fact]) -> dict[str, Any]:
    """Non-parametric upper control: retrieved memory returns the stored label."""

    facts = tuple(facts)
    rows = [
        {
            "fact_id": fact.fact_id,
            "expected": fact.label,
            "observed": fact.label,
            "correct": True,
        }
        for fact in facts
    ]
    return {
        "correct": len(facts),
        "n": len(facts),
        "accuracy": 1.0 if facts else None,
        "rows": rows,
    }


def evaluate_strategy(
    model_path: Path,
    tasks: tuple[Task, ...],
    adapter_paths: list[Path] | None,
    order: tuple[int, ...],
    root: Path,
    strategy: str,
) -> dict[str, Any]:
    task_by_id = {task.task_id: task for task in tasks}
    target = task_by_id[0].facts
    base = ChoiceModel(model_path)
    result: dict[str, Any] = {}
    if strategy == "no_update":
        result["acquisition"] = accuracy(base, target, "direct", "none")
        result["retention_after_interference"] = result["acquisition"]
        result["recovery_after_reacquisition"] = result["acquisition"]
        return result
    if strategy == "context_only":
        result["acquisition"] = accuracy(base, target, "direct", "all")
        result["retention_after_interference"] = accuracy(base, target, "direct", "none")
        result["recovery_after_reacquisition"] = result["retention_after_interference"]
        return result
    if strategy == "retrieval":
        result["acquisition"] = exact_retrieval_accuracy(target)
        result["retention_after_interference"] = result["acquisition"]
        result["recovery_after_reacquisition"] = result["acquisition"]
        return result

    assert adapter_paths
    first_adapter = adapter_paths[0]
    acquired = ChoiceModel(model_path, first_adapter)
    result["acquisition"] = accuracy(acquired, target, "direct", "none")
    final_adapter = adapter_paths[-1]
    retained = ChoiceModel(model_path, final_adapter)
    result["retention_after_interference"] = accuracy(retained, target, "direct", "none")
    result["retention_paraphrase"] = accuracy(retained, target, "paraphrase", "none")
    recovery_data = root / "data" / strategy / "recovery"
    recovery_adapter = root / "adapters" / strategy / "recovery"
    write_dataset(recovery_data, [training_example(fact) for fact in target] * 2)
    command = training_command(
        model_path,
        recovery_data,
        recovery_adapter,
        int(digest({"strategy": strategy, "order": order})[:8], 16),
        20,
        final_adapter / "adapters.safetensors",
    )
    env = os.environ.copy()
    env.update({"HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1"})
    completed = subprocess.run(command, env=env, text=True, capture_output=True, check=False)
    (recovery_adapter.parent / "recovery.log").write_text(completed.stdout + "\n" + completed.stderr, encoding="utf8")
    if completed.returncode != 0:
        raise RuntimeError(f"recovery training failed for {strategy}: {completed.returncode}")
    recovered = ChoiceModel(model_path, recovery_adapter)
    result["recovery_after_reacquisition"] = accuracy(recovered, target, "direct", "none")
    return result


def run(args: argparse.Namespace) -> dict[str, Any]:
    root = args.output.resolve()
    if root.exists():
        raise RuntimeError(f"refusing overwrite of immutable output: {root}")
    root.mkdir(parents=True)
    model = args.model.resolve()
    if not model.is_dir():
        raise RuntimeError(f"model path does not exist: {model}")
    order = tuple(int(value) for value in args.order.split(","))
    tasks = make_tasks(args.seed, args.task_count, args.facts_per_task)
    if sorted(order) != list(range(args.task_count)) or order[0] != 0:
        raise ValueError("order must be a permutation with target task 0 first")
    write_json(root / "tasks.json", [asdict(task) for task in tasks])
    config = {
        "state_slice": STATE_SLICE,
        "model": str(model),
        "seed": args.seed,
        "order": order,
        "task_count": args.task_count,
        "facts_per_task": args.facts_per_task,
        "replay_capacity": args.replay_capacity,
        "update_budget": args.update_budget,
        "current_examples_per_update": args.facts_per_task,
        "replay_examples_per_update": args.update_budget - args.facts_per_task,
        "replay_policy": "balanced_full_memory_v1",
        "optimizer": "adamw",
        "learning_rate": 0.0001,
        "batch_size": 2,
        "num_layers": 8,
        "mask_prompt": True,
        "max_seq_length": 192,
        "fine_tune_type": "lora",
        "audit_schema": "replay_exposure_audit_v1",
        "checkpoint_target_task_id": 0,
        "checkpoint_assessment_variant": "direct",
        "checkpoint_assessment_context_mode": "none",
        "prompt_contract": {
            "training_prompt_equals_assessment_prompt": True,
            "answer_suffix": ANSWER_SUFFIX,
        },
        "iters": args.iters,
        "source_context_removed_for": ["acquisition", "retention_after_interference", "recovery_after_reacquisition"],
        "assessment_effects_generated_before_prediction_lock": False,
    }
    config["contract_sha256"] = digest(config)
    write_json(root / "config.json", config)
    adapters: dict[str, list[Path]] = {}
    for strategy in ("naive_sequential_lora", "replay_lora"):
        adapters[strategy] = train_sequence(
            root, model, tasks, order, strategy, args.seed, args.iters, args.replay_capacity, args.update_budget
        )
    audits = {
        strategy: json.loads((root / "audit" / f"{strategy}.json").read_text())
        for strategy in adapters
    }
    results = {
        strategy: evaluate_strategy(model, tasks, adapters.get(strategy), order, root, strategy)
        for strategy in STRATEGIES
    }
    result = {
        "state_slice": STATE_SLICE,
        "claim_ceiling": "LocalDevelopmentModelContinualLearningPilot",
        "classification": "ModelContinualLearningPilotNoBreakthroughClaim",
        "config": config,
        "results": results,
        "audit_sha256": {strategy: digest(audit) for strategy, audit in audits.items()},
        "manifest_sha256": digest(
            {
                "config": config,
                "tasks": [asdict(task) for task in tasks],
                "audits": audits,
            }
        ),
        "breakthrough_claim_eligible": False,
    }
    write_json(root / "result.json", result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--model", type=Path, default=DEFAULT_MODEL)
    parser.add_argument("--seed", type=int, default=20260810)
    parser.add_argument("--order", default="0,1,2,3")
    parser.add_argument("--task-count", type=int, default=4)
    parser.add_argument("--facts-per-task", type=int, default=8)
    parser.add_argument("--replay-capacity", type=int, default=24)
    parser.add_argument("--update-budget", type=int, default=32)
    parser.add_argument("--iters", type=int, default=40)
    args = parser.parse_args()
    print(json.dumps(run(args), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
