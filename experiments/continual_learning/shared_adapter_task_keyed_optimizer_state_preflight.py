#!/usr/bin/env python3
"""V24 corrected local preflight with a shared adapter and task-keyed state.

The model parameters remain shared across all tasks. Each task owns a
persistent AdamW state object that is explicitly serialized after activation
and restored before its next update. This is a local preflight, not a general
continual-learning benchmark.
"""

from __future__ import annotations

import argparse
from contextlib import redirect_stderr, redirect_stdout
import hashlib
import json
from pathlib import Path
import sys
import time
from types import SimpleNamespace

import mlx.core as mx
import mlx.optimizers as optim
import numpy as np
from mlx.utils import tree_flatten

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from mlx_lm import load as load_model  # noqa: E402
from mlx_lm.tuner.datasets import CacheDataset, load_dataset  # noqa: E402
from mlx_lm.tuner.trainer import TrainingArgs, train  # noqa: E402
from mlx_lm.tuner.utils import linear_to_lora_layers  # noqa: E402

from experiments.continual_learning import route_boundary_representation_preflight as route  # noqa: E402
from experiments.continual_learning import residue_only_codebook_benchmark as v11  # noqa: E402
from experiments.continual_learning import shared_adapter_task_keyed_optimizer_state_protocol as protocol  # noqa: E402
from experiments.continual_learning import task_routed_replay_preflight as custody  # noqa: E402


STATE_SLICE = "continual-learning-protocol-v24-shared-adapter-task-keyed-optimizer-state-preflight"
SOURCE_STATE_SLICE = protocol.STATE_SLICE
MODEL_DEFAULT = Path(protocol.MODEL_DEFAULT)
LORA_CONFIG = {"rank": 8, "dropout": 0.0, "scale": 20.0}
ADAMW_LEARNING_RATE = 0.0001
BATCH_SIZE = 2
MAX_SEQUENCE_LENGTH = 192
SHARED_ADAPTER_LAYERS = protocol.SHARED_ADAPTER_LAYERS


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf8")


def digest(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def file_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def training_config(dataset: Path) -> SimpleNamespace:
    return SimpleNamespace(
        data=str(dataset),
        train=True,
        test=False,
        hf_dataset=False,
        mask_prompt=True,
        max_seq_length=MAX_SEQUENCE_LENGTH,
    )


def build_shared_model(model_path: Path):
    mx.random.seed(protocol.SLOT_SEED_BASE)
    model, tokenizer = load_model(str(model_path), tokenizer_config={"trust_remote_code": True})
    model.freeze()
    linear_to_lora_layers(model, SHARED_ADAPTER_LAYERS, LORA_CONFIG)
    return model, tokenizer


def write_dataset(path: Path, facts: list) -> None:
    v11.base.write_dataset(path, [route.route_bound_training_example(fact) for fact in facts])


def train_shared_group(
    *,
    model,
    tokenizer,
    dataset: Path,
    optimizer: optim.Optimizer,
    optimizer_state_before: int,
    iters: int,
    task_id: int,
    step: int,
    output: Path,
) -> dict:
    train_set, valid_set, _ = load_dataset(training_config(dataset), tokenizer)
    if len(train_set) == 0 or len(valid_set) == 0:
        raise ValueError(f"empty train/valid dataset: {dataset}")
    log_path = output / "training.log"
    checkpoint = output / "group-adapter.safetensors"
    np.random.seed(protocol.fixed_task_seed(task_id) + step)
    mx.reset_peak_memory()
    started = time.perf_counter()
    args = TrainingArgs(
        batch_size=BATCH_SIZE,
        iters=iters,
        val_batches=-1,
        steps_per_report=max(1, min(10, iters)),
        steps_per_eval=iters,
        steps_per_save=iters,
        adapter_file=checkpoint,
        max_seq_length=MAX_SEQUENCE_LENGTH,
    )
    with log_path.open("w", encoding="utf8") as log:
        with redirect_stdout(log), redirect_stderr(log):
            train(
                model=model,
                optimizer=optimizer,
                train_dataset=CacheDataset(train_set),
                val_dataset=CacheDataset(valid_set),
                args=args,
            )
    elapsed = time.perf_counter() - started
    state_after = custody.optimizer_step(optimizer.state)
    if state_after - optimizer_state_before != iters:
        raise ValueError(f"optimizer step drift for task {task_id} update {step}")
    return {
        "task_id": task_id,
        "step": step,
        "optimizer_iterations": iters,
        "optimizer_state_step_before": optimizer_state_before,
        "optimizer_state_step_after": state_after,
        "runtime_seconds": elapsed,
        "peak_memory_gb": mx.get_peak_memory() / 1e9,
        "group_adapter_bytes": checkpoint.stat().st_size,
        "group_adapter_sha256": file_digest(checkpoint),
        "checkpoint_relative_path": str(checkpoint),
    }


def save_shared_adapter(model, path: Path) -> dict:
    weights = dict(tree_flatten(model.trainable_parameters()))
    mx.eval(*weights.values())
    mx.save_safetensors(str(path), weights)
    return {"adapter_bytes": path.stat().st_size, "adapter_sha256": file_digest(path)}


def evaluate_target(model_path: Path, adapter_path: Path, facts: tuple) -> dict:
    return route.route_bound_accuracy(v11.base.ChoiceModel(model_path, adapter_path), facts)


def facts_by_id(tasks) -> dict:
    return {fact.fact_id: fact for task in tasks for fact in task.train_facts + task.test_facts}


def run_strategy(*, root: Path, model_path: Path, tasks: tuple, order: tuple[int, ...], strategy: str, seed: int, iters: int) -> dict:
    replay_enabled = strategy == "shared_replay"
    schedule = protocol.make_schedule(seed, order, replay_enabled)
    task_by_id = {task.task_id: task for task in tasks}
    by_id = facts_by_id(tasks)
    data_root = root / "data" / strategy
    adapter_root = root / "adapters" / strategy
    state_root = root / "optimizer-states" / strategy
    audit_root = root / "audit"
    data_root.mkdir(parents=True, exist_ok=False)
    adapter_root.mkdir(parents=True, exist_ok=False)
    state_root.mkdir(parents=True, exist_ok=False)
    model, tokenizer = build_shared_model(model_path)
    optimizer_by_task: dict[int, optim.Optimizer] = {}
    previous_state: dict[int, Path] = {}
    updates = []

    for entry in schedule:
        step = entry["step"]
        rows_by_task: dict[int, list] = {}
        for row in entry["rows"]:
            rows_by_task.setdefault(int(row["task_id"]), []).append(by_id[row["fact_id"]])
        if sum(len(facts) for facts in rows_by_task.values()) != protocol.UPDATE_BUDGET:
            raise ValueError(f"row budget drift at step {step}")
        group_receipts = []
        replay_ids = set(entry["replay_fact_ids"])
        present_replay_ids = set()
        for task_id in sorted(rows_by_task):
            facts = rows_by_task[task_id]
            dataset = data_root / f"step-{step}" / f"task-{task_id}"
            write_dataset(dataset, facts)
            dataset_receipt = custody.verify_dataset(dataset, facts)
            present_replay_ids.update(fact.fact_id for fact in facts if fact.fact_id in replay_ids)
            optimizer = optimizer_by_task.get(task_id)
            if optimizer is None:
                optimizer = optim.AdamW(learning_rate=ADAMW_LEARNING_RATE)
                optimizer_by_task[task_id] = optimizer
                state_before = custody.optimizer_step(optimizer.state)
                custody_mode = "fresh_zero_state"
            else:
                optimizer.state = custody.load_optimizer_state(previous_state[task_id])
                state_before = custody.optimizer_step(optimizer.state)
                custody_mode = "restored_persistent_task_state"
            group_output = adapter_root / f"step-{step}" / f"task-{task_id}"
            group_output.mkdir(parents=True, exist_ok=False)
            receipt = train_shared_group(
                model=model,
                tokenizer=tokenizer,
                dataset=dataset,
                optimizer=optimizer,
                optimizer_state_before=state_before,
                iters=entry["optimizer_iterations_by_task"][str(task_id)],
                task_id=task_id,
                step=step,
                output=group_output,
            )
            state_path = state_root / f"task-{task_id}" / f"update-{step}.npz"
            state_path.parent.mkdir(parents=True, exist_ok=True)
            custody.save_optimizer_state(state_path, optimizer)
            receipt.update(
                {
                    "route_key": f"T{task_id}",
                    "optimizer_state_custody": custody_mode,
                    "optimizer_state_policy": protocol.OPTIMIZER_STATE_POLICY,
                    "optimizer_state_relative_path": str(state_path),
                    "optimizer_state_bytes": state_path.stat().st_size,
                    "optimizer_state_sha256": file_digest(state_path),
                    "previous_optimizer_state_relative_path": str(previous_state[task_id]) if task_id in previous_state else None,
                    "dataset_relative_path": str(dataset),
                    "dataset_row_count": len(facts),
                    "dataset_fact_ids": [fact.fact_id for fact in facts],
                    "dataset_receipt": dataset_receipt,
                }
            )
            group_receipts.append(receipt)
            previous_state[task_id] = state_path

        if present_replay_ids != replay_ids:
            raise ValueError(f"replay dataset exposure failure at step {step}")
        if sum(receipt["optimizer_iterations"] for receipt in group_receipts) != iters:
            raise ValueError(f"optimizer budget drift at step {step}")
        adapter_dir = adapter_root / f"step-{step}"
        adapter_file = adapter_dir / "adapters.safetensors"
        adapter_receipt = save_shared_adapter(model, adapter_file)
        write_json(
            adapter_dir / "adapter_config.json",
            {"fine_tune_type": "lora", "num_layers": SHARED_ADAPTER_LAYERS, "lora_parameters": LORA_CONFIG},
        )
        target_accuracy = evaluate_target(model_path, adapter_dir, task_by_id[0].test_facts)
        current_task_id = entry["task_id"]
        current_accuracy = evaluate_target(model_path, adapter_dir, task_by_id[current_task_id].test_facts)
        updates.append(
            {
                "step": step,
                "task_id": current_task_id,
                "current_fact_ids": entry["current_fact_ids"],
                "replay_fact_ids": entry["replay_fact_ids"],
                "selected_fact_ids": entry["selected_fact_ids"],
                "replay_counts_by_task": {
                    str(task): sum(1 for fact_id in entry["replay_fact_ids"] if by_id[fact_id].task_id == task)
                    for task in sorted({by_id[fact_id].task_id for fact_id in entry["replay_fact_ids"]})
                },
                "dataset_replay_fact_ids": sorted(present_replay_ids),
                "replay_examples_present_in_training_datasets": present_replay_ids == replay_ids,
                "dataset_row_count": sum(receipt["dataset_row_count"] for receipt in group_receipts),
                "optimizer_iterations": sum(receipt["optimizer_iterations"] for receipt in group_receipts),
                "active_optimizer_state_task_ids": sorted(rows_by_task),
                "shared_adapter_id": protocol.SHARED_ADAPTER_ID,
                "shared_adapter_layers": SHARED_ADAPTER_LAYERS,
                "adapter_relative_path": str(adapter_dir),
                **adapter_receipt,
                "group_receipts": group_receipts,
                "target_task_id": 0,
                "target_task_accuracy_after_update": target_accuracy,
                "current_task_accuracy_after_update": current_accuracy,
            }
        )

    return {
        "strategy": strategy,
        "replay_enabled": replay_enabled,
        "updates": updates,
        "target_task_acquisition": updates[0]["target_task_accuracy_after_update"],
        "target_task_retention_after_interference": updates[-1]["target_task_accuracy_after_update"],
        "total_training_examples": sum(update["dataset_row_count"] for update in updates),
        "total_optimizer_iterations": sum(update["optimizer_iterations"] for update in updates),
        "replay_exposure_verified": all(update["replay_examples_present_in_training_datasets"] for update in updates),
        "optimizer_state_persistence_verified": all(
            receipt["optimizer_state_step_after"] - receipt["optimizer_state_step_before"] == receipt["optimizer_iterations"]
            and (receipt["optimizer_state_custody"] == "fresh_zero_state" if receipt["step"] == 0 and receipt["task_id"] == 0 else True)
            for update in updates for receipt in update["group_receipts"]
        ),
        "latest_shared_adapter_bytes": updates[-1]["adapter_bytes"],
        "latest_shared_adapter_sha256": updates[-1]["adapter_sha256"],
        "max_peak_memory_gb": max(receipt["peak_memory_gb"] for update in updates for receipt in update["group_receipts"]),
        "total_runtime_seconds": sum(receipt["runtime_seconds"] for update in updates for receipt in update["group_receipts"]),
    }


def run(args: argparse.Namespace) -> dict:
    model_path = args.model.resolve()
    order = tuple(int(value) for value in args.order.split(","))
    if args.seed != 20260812 or order != (0, 1, 2, 3) or args.task_count != protocol.TASK_COUNT or args.iters != protocol.ITERS_PER_UPDATE or model_path != MODEL_DEFAULT.resolve():
        raise ValueError("V24 corrected preflight fixed contract drift")
    output = args.output.resolve()
    if output.exists():
        raise RuntimeError(f"refusing overwrite of immutable output: {output}")
    output.mkdir(parents=True)
    tasks = tuple(v11.base.make_tasks(args.seed, args.task_count))
    for replay_enabled in (True, False):
        protocol.validate_schedule(args.seed, order, protocol.make_schedule(args.seed, order, replay_enabled), replay_enabled)
    reference = custody.static_byte_reference(model_path, output)
    results = {
        strategy: run_strategy(root=output, model_path=model_path, tasks=tasks, order=order, strategy=strategy, seed=args.seed, iters=args.iters)
        for strategy in ("shared_replay", "shared_no_replay")
    }
    for result in results.values():
        result["parameter_budget"] = {
            "full_shared_adapter_bytes": reference["full_shared_adapter_bytes"],
            "shared_adapter_bytes": result["latest_shared_adapter_bytes"],
            "shared_to_full_bytes_ratio": result["latest_shared_adapter_bytes"] / reference["full_shared_adapter_bytes"],
            "matched": 0.75 <= result["latest_shared_adapter_bytes"] / reference["full_shared_adapter_bytes"] <= 1.25,
        }
    tasks_payload = [
        {"task_id": task.task_id, "task_token": task.task_token, "train_facts": [fact.__dict__ for fact in task.train_facts], "test_facts": [fact.__dict__ for fact in task.test_facts]}
        for task in tasks
    ]
    config = {
        "state_slice": STATE_SLICE,
        "source_state_slice": SOURCE_STATE_SLICE,
        "model": str(model_path),
        "seed": args.seed,
        "order": list(order),
        "task_count": args.task_count,
        "train_facts_per_task": protocol.TRAIN_FACTS_PER_TASK,
        "test_facts_per_task": protocol.TEST_FACTS_PER_TASK,
        "update_budget": protocol.UPDATE_BUDGET,
        "iters_per_update": args.iters,
        "total_examples_per_strategy": protocol.UPDATE_BUDGET * protocol.TASK_COUNT,
        "total_optimizer_steps_per_strategy": args.iters * protocol.TASK_COUNT,
        "optimizer": "adamw",
        "learning_rate": ADAMW_LEARNING_RATE,
        "batch_size": BATCH_SIZE,
        "max_sequence_length": MAX_SEQUENCE_LENGTH,
        "shared_adapter_layers": SHARED_ADAPTER_LAYERS,
        "shared_adapter_id": protocol.SHARED_ADAPTER_ID,
        "optimizer_state_policy": protocol.OPTIMIZER_STATE_POLICY,
        "update_route_policy": protocol.UPDATE_ROUTE_POLICY,
        "replay_selection_policy": protocol.REPLAY_SELECTION_POLICY,
        "changed_protocol_variable": "shared_adapter_task_keyed_optimizer_state_v1",
    }
    config["contract_sha256"] = digest(config)
    write_json(output / "config.json", config)
    write_json(output / "tasks.json", tasks_payload)
    manifest = {"config": config, "tasks": tasks_payload, "byte_reference": reference, "results": results}
    result = {
        "state_slice": STATE_SLICE,
        "source_state_slice": SOURCE_STATE_SLICE,
        "classification": "CorrectedLocalSharedAdapterTaskKeyedOptimizerStatePreflightNoBreakthroughClaim",
        "claim_ceiling": "LocalDevelopmentSharedAdapterTaskKeyedOptimizerStatePreflight",
        "config": config,
        "byte_reference": reference,
        "results": results,
        "candidate_gates": {
            "replay_exposure_verified": results["shared_replay"]["replay_exposure_verified"],
            "optimizer_state_persistence_verified": results["shared_replay"]["optimizer_state_persistence_verified"],
            "target_task_acquisition_floor": results["shared_replay"]["target_task_acquisition"]["accuracy"] >= 0.5,
            "replay_retention_above_shared_no_replay": results["shared_replay"]["target_task_retention_after_interference"]["accuracy"] > results["shared_no_replay"]["target_task_retention_after_interference"]["accuracy"],
            "parameter_budget_matched": results["shared_replay"]["parameter_budget"]["matched"],
        },
        "h100_authorized": False,
        "breakthrough_claim_eligible": False,
    }
    result["manifest_sha256"] = digest(manifest)
    result["result_sha256"] = digest(result)
    write_json(output / "result.json", result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--model", type=Path, default=MODEL_DEFAULT)
    parser.add_argument("--seed", type=int, default=20260812)
    parser.add_argument("--order", default="0,1,2,3")
    parser.add_argument("--task-count", type=int, default=protocol.TASK_COUNT)
    parser.add_argument("--iters", type=int, default=protocol.ITERS_PER_UPDATE)
    args = parser.parse_args()
    print(json.dumps(run(args), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
