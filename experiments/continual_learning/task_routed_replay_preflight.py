#!/usr/bin/env python3
"""V23 corrected local preflight with explicit per-slot optimizer custody.

The stock ``mlx_lm lora`` command resumes adapter weights only.  This runner
owns the bounded MLX training loop invocation and persists each task slot's
optimizer state alongside its adapter, so replay updates are not silently
converted into weight-only resumes.
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
from mlx.utils import tree_flatten, tree_unflatten

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from mlx_lm import load as load_model  # noqa: E402
from mlx_lm.tuner.datasets import CacheDataset, load_dataset  # noqa: E402
from mlx_lm.tuner.trainer import TrainingArgs, train  # noqa: E402
from mlx_lm.tuner.utils import linear_to_lora_layers  # noqa: E402

from experiments.continual_learning import route_boundary_representation_preflight as route  # noqa: E402
from experiments.continual_learning import residue_only_codebook_benchmark as v11  # noqa: E402
from experiments.continual_learning import task_routed_replay_protocol as protocol  # noqa: E402


STATE_SLICE = "continual-learning-protocol-v23-task-routed-replay-consolidation-preflight"
SOURCE_STATE_SLICE = protocol.STATE_SLICE
MODEL_DEFAULT = Path(protocol.MODEL_DEFAULT)
LORA_CONFIG = {"rank": 8, "dropout": 0.0, "scale": 20.0}
SLOT_LAYERS = protocol.SLOT_LAYERS
FULL_SHARED_LAYERS = protocol.FULL_SHARED_LAYERS
ADAMW_LEARNING_RATE = 0.0001
BATCH_SIZE = 2
MAX_SEQUENCE_LENGTH = 192


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf8")


def digest(value) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def file_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def adapter_config() -> dict:
    return {
        "fine_tune_type": "lora",
        "num_layers": SLOT_LAYERS,
        "lora_parameters": dict(LORA_CONFIG),
    }


def training_config(dataset: Path) -> SimpleNamespace:
    return SimpleNamespace(
        data=str(dataset),
        train=True,
        test=False,
        hf_dataset=False,
        mask_prompt=True,
        max_seq_length=MAX_SEQUENCE_LENGTH,
    )


def save_optimizer_state(path: Path, optimizer: optim.Optimizer) -> None:
    flat = dict(tree_flatten(optimizer.state))
    if not flat:
        raise ValueError("optimizer state is empty")
    mx.eval(*flat.values())
    mx.savez(str(path), **flat)


def load_optimizer_state(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(path)
    restored = tree_unflatten(mx.load(str(path)))
    if not isinstance(restored, dict) or "step" not in restored:
        raise ValueError(f"invalid optimizer state: {path}")
    return restored


def optimizer_step(state: dict) -> int:
    return int(state["step"].item())


def write_dataset(path: Path, facts: list) -> None:
    rows = [route.route_bound_training_example(fact) for fact in facts]
    v11.base.write_dataset(path, rows)


def verify_dataset(path: Path, facts: list) -> dict:
    expected = [route.route_bound_training_example(fact) for fact in facts]
    actual = []
    with (path / "train.jsonl").open(encoding="utf8") as handle:
        for line in handle:
            actual.append(json.loads(line))
    if actual != expected:
        raise ValueError(f"training dataset drift: {path}")
    return {
        "verified": True,
        "row_count": len(actual),
        "fact_ids": [fact.fact_id for fact in facts],
    }


def slot_model(
    model_path: Path,
    adapter_file: Path | None,
    slot_seed: int,
):
    """Construct a slot model with deterministic first-activation state."""

    mx.random.seed(slot_seed)
    model, tokenizer = load_model(
        str(model_path), tokenizer_config={"trust_remote_code": True}
    )
    model.freeze()
    linear_to_lora_layers(model, SLOT_LAYERS, LORA_CONFIG)
    if adapter_file is not None:
        model.load_weights(str(adapter_file), strict=False)
    return model, tokenizer


def train_slot_update(
    *,
    model_path: Path,
    dataset: Path,
    adapter_path: Path,
    previous_adapter: Path | None,
    previous_optimizer_state: Path | None,
    slot_seed: int,
    iters: int,
) -> dict:
    """Train one routed slot update and emit immutable adapter/state files."""

    if iters < 1:
        raise ValueError("slot optimizer iterations must be positive")
    if (previous_adapter is None) != (previous_optimizer_state is None):
        raise ValueError("adapter and optimizer-state custody must advance together")

    adapter_path.mkdir(parents=True, exist_ok=False)
    write_json(adapter_path / "adapter_config.json", adapter_config())
    log_path = adapter_path / "training.log"
    adapter_file = adapter_path / "adapters.safetensors"
    optimizer_path = adapter_path / "optimizer_state.npz"

    np.random.seed(slot_seed)
    mx.random.seed(slot_seed)
    model, tokenizer = slot_model(
        model_path,
        previous_adapter / "adapters.safetensors" if previous_adapter else None,
        slot_seed,
    )
    train_set, valid_set, _ = load_dataset(training_config(dataset), tokenizer)
    if len(train_set) == 0 or len(valid_set) == 0:
        raise ValueError(f"empty train/valid dataset: {dataset}")

    optimizer = optim.AdamW(learning_rate=ADAMW_LEARNING_RATE)
    if previous_optimizer_state is None:
        state_before = optimizer_step(optimizer.state)
        custody = "fresh_zero_state"
    else:
        optimizer.state = load_optimizer_state(previous_optimizer_state)
        state_before = optimizer_step(optimizer.state)
        custody = "restored_persistent_slot_state"

    mx.reset_peak_memory()
    started = time.perf_counter()
    training_args = TrainingArgs(
        batch_size=BATCH_SIZE,
        iters=iters,
        val_batches=-1,
        steps_per_report=max(1, min(10, iters)),
        steps_per_eval=iters,
        steps_per_save=iters,
        adapter_file=adapter_file,
        max_seq_length=MAX_SEQUENCE_LENGTH,
    )
    with log_path.open("w", encoding="utf8") as log:
        with redirect_stdout(log), redirect_stderr(log):
            train(
                model=model,
                optimizer=optimizer,
                train_dataset=CacheDataset(train_set),
                val_dataset=CacheDataset(valid_set),
                args=training_args,
            )
    elapsed = time.perf_counter() - started
    state_after = optimizer_step(optimizer.state)
    if state_after - state_before != iters:
        raise ValueError(
            f"optimizer step drift for {adapter_path}: {state_before}->{state_after}"
        )
    save_optimizer_state(optimizer_path, optimizer)
    if not adapter_file.exists():
        raise FileNotFoundError(adapter_file)
    return {
        "adapter_relative_path": str(adapter_path),
        "adapter_bytes": adapter_file.stat().st_size,
        "adapter_sha256": file_digest(adapter_file),
        "optimizer_state_relative_path": str(optimizer_path),
        "optimizer_state_bytes": optimizer_path.stat().st_size,
        "optimizer_state_sha256": file_digest(optimizer_path),
        "optimizer_state_step_before": state_before,
        "optimizer_state_step_after": state_after,
        "optimizer_state_custody": custody,
        "runtime_seconds": elapsed,
        "peak_memory_gb": mx.get_peak_memory() / 1e9,
        "slot_seed": slot_seed,
        "slot_initialization_policy": protocol.SLOT_INITIALIZATION_POLICY,
        "optimizer_state_policy": protocol.OPTIMIZER_STATE_POLICY,
        "num_layers": SLOT_LAYERS,
    }


def static_byte_reference(model_path: Path, root: Path) -> dict:
    """Calibrate adapter shape bytes without a training update."""

    reference_dir = root / "audit" / "byte-reference"
    reference_dir.mkdir(parents=True, exist_ok=False)
    adapter_file = reference_dir / "full-shared-8-layer-template.safetensors"
    mx.random.seed(protocol.SLOT_SEED_BASE)
    model, _ = load_model(
        str(model_path), tokenizer_config={"trust_remote_code": True}
    )
    model.freeze()
    linear_to_lora_layers(model, FULL_SHARED_LAYERS, LORA_CONFIG)
    weights = dict(tree_flatten(model.trainable_parameters()))
    mx.eval(*weights.values())
    mx.save_safetensors(str(adapter_file), weights)
    return {
        "kind": "same_model_zero_step_shape_calibration",
        "full_shared_num_layers": FULL_SHARED_LAYERS,
        "full_shared_adapter_bytes": adapter_file.stat().st_size,
        "full_shared_adapter_sha256": file_digest(adapter_file),
        "relative_path": str(adapter_file),
    }


def facts_by_id(tasks) -> dict[str, object]:
    return {
        fact.fact_id: fact
        for task in tasks
        for fact in task.train_facts + task.test_facts
    }


def evaluate_target(model_path: Path, adapter_path: Path, facts: tuple) -> dict:
    model = v11.base.ChoiceModel(model_path, adapter_path)
    return route.route_bound_accuracy(model, facts)


def run_strategy(
    *,
    root: Path,
    model_path: Path,
    tasks: tuple,
    order: tuple[int, ...],
    strategy: str,
    seed: int,
    iters_per_update: int,
) -> dict:
    replay_enabled = strategy == "routed_replay"
    schedule = protocol.make_schedule(seed, order, replay_enabled)
    task_by_id = {task.task_id: task for task in tasks}
    by_id = facts_by_id(tasks)
    data_root = root / "data" / strategy
    adapter_root = root / "adapters" / strategy
    audit_root = root / "audit"
    data_root.mkdir(parents=True, exist_ok=False)
    adapter_root.mkdir(parents=True, exist_ok=False)
    latest_adapter: dict[int, Path] = {}
    latest_optimizer: dict[int, Path] = {}
    updates = []
    slot_history: dict[int, list[dict]] = {}

    for entry in schedule:
        step = entry["step"]
        task_id = entry["task_id"]
        row_facts = [by_id[row["fact_id"]] for row in entry["rows"]]
        rows_by_task: dict[int, list] = {}
        for fact in row_facts:
            rows_by_task.setdefault(fact.task_id, []).append(fact)
        if sum(len(facts) for facts in rows_by_task.values()) != protocol.UPDATE_BUDGET:
            raise ValueError(f"route row budget drift at step {step}")
        iteration_total = 0
        slot_updates = []
        for slot_task_id in sorted(rows_by_task):
            slot_facts = rows_by_task[slot_task_id]
            slot_count = len(slot_facts)
            slot_iters = (iters_per_update * slot_count) // protocol.UPDATE_BUDGET
            if slot_iters < 1:
                raise ValueError(f"slot received no optimizer iterations at step {step}")
            iteration_total += slot_iters
            dataset = data_root / f"step-{step}" / f"slot-{slot_task_id}"
            write_dataset(dataset, slot_facts)
            dataset_receipt = verify_dataset(dataset, slot_facts)
            adapter_path = adapter_root / f"slot-{slot_task_id}" / f"update-{step}"
            previous_adapter = latest_adapter.get(slot_task_id)
            previous_optimizer = latest_optimizer.get(slot_task_id)
            receipt = train_slot_update(
                model_path=model_path,
                dataset=dataset,
                adapter_path=adapter_path,
                previous_adapter=previous_adapter,
                previous_optimizer_state=previous_optimizer,
                slot_seed=protocol.fixed_slot_seed(slot_task_id),
                iters=slot_iters,
            )
            receipt.update(
                {
                    "step": step,
                    "task_id": slot_task_id,
                    "route_key": f"T{slot_task_id}",
                    "dataset_relative_path": str(dataset),
                    "dataset_row_count": len(slot_facts),
                    "dataset_fact_ids": [fact.fact_id for fact in slot_facts],
                    "dataset_receipt": dataset_receipt,
                    "optimizer_iterations": slot_iters,
                    "previous_adapter_relative_path": str(previous_adapter) if previous_adapter else None,
                    "previous_optimizer_state_relative_path": str(previous_optimizer) if previous_optimizer else None,
                }
            )
            slot_updates.append(receipt)
            latest_adapter[slot_task_id] = adapter_path
            latest_optimizer[slot_task_id] = adapter_path / "optimizer_state.npz"
            slot_history.setdefault(slot_task_id, []).append(receipt)
        if iteration_total != iters_per_update:
            raise ValueError(f"optimizer budget drift at step {step}: {iteration_total}")

        replay_ids = set(entry["replay_fact_ids"])
        present_replay_ids = {
            fact_id
            for receipt in slot_updates
            for fact_id in receipt["dataset_fact_ids"]
            if fact_id in replay_ids
        }
        if present_replay_ids != replay_ids:
            raise ValueError(f"replay dataset exposure failure at step {step}")
        target_adapter = latest_adapter[0]
        target_accuracy = evaluate_target(model_path, target_adapter, task_by_id[0].test_facts)
        current_accuracy = evaluate_target(
            model_path,
            latest_adapter[task_id],
            task_by_id[task_id].test_facts,
        )
        updates.append(
            {
                "step": step,
                "task_id": task_id,
                "current_fact_ids": entry["current_fact_ids"],
                "replay_fact_ids": entry["replay_fact_ids"],
                "selected_fact_ids": entry["selected_fact_ids"],
                "replay_counts_by_task": {} if not entry["replay_fact_ids"] else {
                    str(task): sum(1 for fact_id in entry["replay_fact_ids"] if by_id[fact_id].task_id == task)
                    for task in sorted({by_id[fact_id].task_id for fact_id in entry["replay_fact_ids"]})
                },
                "dataset_replay_fact_ids": sorted(present_replay_ids),
                "replay_examples_present_in_training_datasets": present_replay_ids == replay_ids,
                "dataset_row_count": sum(receipt["dataset_row_count"] for receipt in slot_updates),
                "optimizer_iterations": iteration_total,
                "active_slot_task_ids": sorted(rows_by_task),
                "slot_updates": slot_updates,
                "target_task_id": 0,
                "target_task_accuracy_after_update": target_accuracy,
                "current_task_accuracy_after_update": current_accuracy,
            }
        )

    final_target = updates[-1]["target_task_accuracy_after_update"]
    initial_target = updates[0]["target_task_accuracy_after_update"]
    total_slot_bytes = sum(
        int(receipt["adapter_bytes"])
        for history in slot_history.values()
        for receipt in history[-1:]
    )
    state_persistence = all(
        receipt["optimizer_state_step_before"] == 0
        if index == 0
        else receipt["optimizer_state_step_before"] == history[index - 1]["optimizer_state_step_after"]
        for history in slot_history.values()
        for index, receipt in enumerate(history)
    )
    return {
        "strategy": strategy,
        "replay_enabled": replay_enabled,
        "updates": updates,
        "target_task_acquisition": initial_target,
        "target_task_retention_after_interference": final_target,
        "total_training_examples": sum(update["dataset_row_count"] for update in updates),
        "total_optimizer_iterations": sum(update["optimizer_iterations"] for update in updates),
        "slot_state_persistence_verified": state_persistence,
        "replay_exposure_verified": all(
            update["replay_examples_present_in_training_datasets"] for update in updates
        ),
        "latest_slot_adapter_bytes": {
            str(task_id): slot_history[task_id][-1]["adapter_bytes"]
            for task_id in sorted(slot_history)
        },
        "total_latest_slot_adapter_bytes": total_slot_bytes,
        "max_peak_memory_gb": max(
            receipt["peak_memory_gb"]
            for history in slot_history.values()
            for receipt in history
        ),
        "total_runtime_seconds": sum(
            receipt["runtime_seconds"]
            for history in slot_history.values()
            for receipt in history
        ),
    }


def run(args: argparse.Namespace) -> dict:
    model_path = args.model.resolve()
    order = tuple(int(value) for value in args.order.split(","))
    if (
        args.seed != 20260812
        or order != (0, 1, 2, 3)
        or args.task_count != protocol.TASK_COUNT
        or args.iters != protocol.ITERS_PER_UPDATE
        or model_path != MODEL_DEFAULT.resolve()
    ):
        raise ValueError("V23 corrected preflight fixed contract drift")
    output = args.output.resolve()
    if output.exists():
        raise RuntimeError(f"refusing overwrite of immutable output: {output}")
    output.mkdir(parents=True)
    tasks = tuple(v11.base.make_tasks(args.seed, args.task_count))
    for replay_enabled in (True, False):
        protocol.validate_schedule(args.seed, order, protocol.make_schedule(args.seed, order, replay_enabled), replay_enabled)
    byte_reference = static_byte_reference(model_path, output)
    results = {}
    for strategy in ("routed_replay", "routed_no_replay"):
        results[strategy] = run_strategy(
            root=output,
            model_path=model_path,
            tasks=tasks,
            order=order,
            strategy=strategy,
            seed=args.seed,
            iters_per_update=args.iters,
        )
    full_bytes = byte_reference["full_shared_adapter_bytes"]
    for result in results.values():
        result["parameter_budget"] = {
            "full_shared_adapter_bytes": full_bytes,
            "compact_slot_total_adapter_bytes": result["total_latest_slot_adapter_bytes"],
            "compact_to_full_bytes_ratio": result["total_latest_slot_adapter_bytes"] / full_bytes,
            "matched": 0.75 <= result["total_latest_slot_adapter_bytes"] / full_bytes <= 1.25,
        }
    tasks_payload = [
        {
            "task_id": task.task_id,
            "task_token": task.task_token,
            "train_facts": [fact.__dict__ for fact in task.train_facts],
            "test_facts": [fact.__dict__ for fact in task.test_facts],
        }
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
        "slot_layers": SLOT_LAYERS,
        "full_shared_layers_reference": FULL_SHARED_LAYERS,
        "slot_initialization_policy": protocol.SLOT_INITIALIZATION_POLICY,
        "optimizer_state_policy": protocol.OPTIMIZER_STATE_POLICY,
        "update_route_policy": protocol.UPDATE_ROUTE_POLICY,
        "replay_selection_policy": protocol.REPLAY_SELECTION_POLICY,
        "changed_protocol_variable": "task_routed_replay_consolidation_v1",
    }
    config["contract_sha256"] = digest(config)
    write_json(output / "config.json", config)
    write_json(output / "tasks.json", tasks_payload)
    manifest = {
        "config": config,
        "tasks": tasks_payload,
        "byte_reference": byte_reference,
        "results": results,
    }
    result = {
        "state_slice": STATE_SLICE,
        "source_state_slice": SOURCE_STATE_SLICE,
        "classification": "CorrectedLocalTaskRoutedReplayPreflightNoBreakthroughClaim",
        "claim_ceiling": "LocalDevelopmentTaskRoutedReplayConsolidationPreflight",
        "config": config,
        "byte_reference": byte_reference,
        "results": results,
        "candidate_gates": {
            "replay_exposure_verified": results["routed_replay"]["replay_exposure_verified"],
            "optimizer_state_persistence_verified": results["routed_replay"]["slot_state_persistence_verified"],
            "target_task_acquisition_floor": results["routed_replay"]["target_task_acquisition"]["accuracy"] >= 0.5,
            "replay_retention_above_routed_no_replay": results["routed_replay"]["target_task_retention_after_interference"]["accuracy"] > results["routed_no_replay"]["target_task_retention_after_interference"]["accuracy"],
            "parameter_budget_matched": results["routed_replay"]["parameter_budget"]["matched"],
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
