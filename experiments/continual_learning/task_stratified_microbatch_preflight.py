#!/usr/bin/env python3
"""V28 corrected local preflight with task-stratified microbatches."""

from __future__ import annotations

import argparse
from collections import defaultdict
from contextlib import redirect_stderr, redirect_stdout
import json
import re
from pathlib import Path
import sys

import numpy as np
from mlx_lm.tuner.datasets import CacheDataset
from mlx_lm.tuner.trainer import train as stock_train

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from experiments.continual_learning import shared_global_update_stream_preflight as v26_preflight  # noqa: E402
from experiments.continual_learning import task_stratified_microbatch_protocol as protocol  # noqa: E402


STATE_SLICE = "continual-learning-protocol-v28-task-stratified-microbatch-preflight"
SOURCE_STATE_SLICE = protocol.STATE_SLICE
BATCH_SCHEDULE_AUDIT: list[dict] = []


def digest(value) -> str:
    return protocol.digest(value)


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf8")


def task_id_from_prompt(prompt: str) -> int:
    match = re.search(r"Task token: T(\d+)\.", prompt)
    if not match:
        raise ValueError("missing task token in training prompt")
    return int(match.group(1))


def task_stratified_iterate_batches(
    dataset,
    batch_size,
    max_seq_length,
    loop=False,
    seed=None,
    comm_group=None,
):
    if not isinstance(dataset, CacheDataset):
        raise TypeError("V28 requires CacheDataset inputs")
    if comm_group is not None and comm_group.size() != 1:
        raise ValueError("V28 preflight does not support distributed execution")
    raw_data = dataset._data._data
    task_ids = [task_id_from_prompt(row["prompt"]) for row in raw_data]
    if len(dataset) < batch_size or len(dataset) % batch_size:
        raise ValueError("V28 dataset must divide exactly into microbatches")
    buckets = defaultdict(list)
    for index, task_id in enumerate(task_ids):
        buckets[task_id].append(index)
    ordered_indices = []
    for task_id in buckets:
        buckets[task_id].sort(key=dataset.itemlen)
    while any(buckets.values()):
        for task_id in sorted(buckets):
            if buckets[task_id]:
                ordered_indices.append(buckets[task_id].pop(0))
    batch_idx = [
        ordered_indices[i : i + batch_size]
        for i in range(0, len(ordered_indices), batch_size)
    ]
    batch_task_ids = [[task_ids[index] for index in batch] for batch in batch_idx]
    if len(dataset) == 32:
        BATCH_SCHEDULE_AUDIT.append(
            {
                "call_index": len(BATCH_SCHEDULE_AUDIT),
                "dataset_example_count": len(dataset),
                "batch_size": batch_size,
                "batch_count": len(batch_idx),
                "batch_task_ids": batch_task_ids,
                "task_counts": {
                    str(task_id): task_ids.count(task_id)
                    for task_id in sorted(set(task_ids))
                },
                "batch_policy": protocol.BATCH_POLICY,
            }
        )
    if seed:
        np.random.seed(seed)
    while True:
        indices = np.random.permutation(len(batch_idx))
        for batch_number in indices:
            batch = [dataset[index] for index in batch_idx[batch_number]]
            if len(batch[0]) == 2:
                batch, offsets = zip(*batch)
            else:
                offsets = [0] * len(batch)
            lengths = [len(item) for item in batch]
            if max(lengths) > max_seq_length:
                print(
                    f"[WARNING] Some sequences are longer than {max_seq_length} tokens. "
                    f"The longest sentence {max(lengths)} will be truncated to {max_seq_length}. "
                )
            pad_to = 32
            max_length_in_batch = 1 + pad_to * ((max(lengths) + pad_to - 1) // pad_to)
            max_length_in_batch = min(max_length_in_batch, max_seq_length)
            batch_arr = np.zeros((batch_size, max_length_in_batch), np.int32)
            for index, item in enumerate(batch):
                truncated_length = min(lengths[index], max_seq_length)
                batch_arr[index, :truncated_length] = item[:truncated_length]
                lengths[index] = truncated_length
            import mlx.core as mx

            yield mx.array(batch_arr), mx.array(list(zip(offsets, lengths)))
        if not loop:
            break


def train_with_task_stratified_microbatches(*args, **kwargs):
    return stock_train(
        *args,
        iterate_batches=task_stratified_iterate_batches,
        **kwargs,
    )


def run(args: argparse.Namespace) -> dict:
    output = args.output.resolve()
    if output.exists():
        raise RuntimeError(f"refusing overwrite of immutable output: {output}")
    if args.seed != protocol.DATA_SEED or tuple(int(value) for value in args.order.split(",")) != protocol.PREFLIGHT_ORDER:
        raise ValueError("V28 preflight fixed cell drift")
    BATCH_SCHEDULE_AUDIT.clear()
    originals = {
        "protocol": v26_preflight.protocol,
        "state": v26_preflight.STATE_SLICE,
        "source": v26_preflight.SOURCE_STATE_SLICE,
        "order": v26_preflight.FIXED_PREFLIGHT_ORDER,
        "train": v26_preflight.train,
    }
    v26_preflight.protocol = protocol
    v26_preflight.STATE_SLICE = STATE_SLICE
    v26_preflight.SOURCE_STATE_SLICE = SOURCE_STATE_SLICE
    v26_preflight.FIXED_PREFLIGHT_ORDER = protocol.PREFLIGHT_ORDER
    v26_preflight.train = train_with_task_stratified_microbatches
    try:
        result = v26_preflight.run(args)
    finally:
        v26_preflight.protocol = originals["protocol"]
        v26_preflight.STATE_SLICE = originals["state"]
        v26_preflight.SOURCE_STATE_SLICE = originals["source"]
        v26_preflight.FIXED_PREFLIGHT_ORDER = originals["order"]
        v26_preflight.train = originals["train"]
    root = output
    config = result["config"]
    config.update(
        {
            "state_slice": STATE_SLICE,
            "source_state_slice": SOURCE_STATE_SLICE,
            "changed_protocol_variable": protocol.CHANGED_PROTOCOL_VARIABLE,
            "batch_policy": protocol.BATCH_POLICY,
        }
    )
    config["contract_sha256"] = digest({key: value for key, value in config.items() if key != "contract_sha256"})
    write_json(root / "config.json", config)
    result.update(
        {
            "state_slice": STATE_SLICE,
            "source_state_slice": SOURCE_STATE_SLICE,
            "classification": "CorrectedLocalTaskStratifiedMicrobatchPreflightNoBreakthroughClaim",
            "claim_ceiling": "LocalDevelopmentTaskStratifiedMicrobatchPreflight",
            "config": config,
            "batch_policy": protocol.BATCH_POLICY,
            "batch_schedule_audit": BATCH_SCHEDULE_AUDIT,
            "h100_authorized": False,
            "breakthrough_claim_eligible": False,
        }
    )
    tasks = json.loads((root / "tasks.json").read_text())
    result["manifest_sha256"] = digest(
        {
            "config": config,
            "tasks": tasks,
            "byte_reference": result["byte_reference"],
            "results": result["results"],
            "batch_schedule_audit": BATCH_SCHEDULE_AUDIT,
        }
    )
    result["result_sha256"] = digest({key: value for key, value in result.items() if key != "result_sha256"})
    write_json(root / "result.json", result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--model", type=Path, default=protocol.MODEL_DEFAULT)
    parser.add_argument("--seed", type=int, default=protocol.DATA_SEED)
    parser.add_argument("--order", default="0,2,3,1")
    parser.add_argument("--task-count", type=int, default=protocol.v24.TASK_COUNT)
    parser.add_argument("--iters", type=int, default=protocol.v24.ITERS_PER_UPDATE)
    args = parser.parse_args()
    print(json.dumps(run(args), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
