#!/usr/bin/env python3
"""V29 local preflight with deterministic replay-anchored temporal batches."""

from __future__ import annotations

import argparse
from collections import defaultdict
import json
from pathlib import Path
import sys

import numpy as np
from mlx_lm.tuner.datasets import CacheDataset

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from experiments.continual_learning import replay_anchored_temporal_protocol as protocol  # noqa: E402
from experiments.continual_learning import task_stratified_microbatch_preflight as v28_preflight  # noqa: E402


STATE_SLICE = "continual-learning-protocol-v29-replay-anchored-temporal-microbatch-preflight"
SOURCE_STATE_SLICE = protocol.STATE_SLICE


def digest(value) -> str:
    return protocol.digest(value)


def write_json(path: Path, value) -> None:
    protocol.write_json(path, value)


def replay_anchored_iterate_batches(
    dataset,
    batch_size,
    max_seq_length,
    loop=False,
    seed=None,
    comm_group=None,
):
    if not isinstance(dataset, CacheDataset):
        raise TypeError("V29 requires CacheDataset inputs")
    if comm_group is not None and comm_group.size() != 1:
        raise ValueError("V29 preflight does not support distributed execution")
    raw_data = dataset._data._data
    task_ids = [v28_preflight.task_id_from_prompt(row["prompt"]) for row in raw_data]
    if len(dataset) < batch_size or len(dataset) % batch_size:
        raise ValueError("V29 dataset must divide exactly into microbatches")
    buckets = defaultdict(list)
    for index, task_id in enumerate(task_ids):
        buckets[task_id].append(index)
    for task_id in buckets:
        buckets[task_id].sort(key=dataset.itemlen)
    within_task_order = [index for task_id in sorted(buckets) for index in buckets[task_id]]
    ordered_task_ids = [task_ids[index] for index in within_task_order]
    current_task_id = task_ids[0]
    position_batches = protocol.replay_anchored_batch_indices(ordered_task_ids, current_task_id, batch_size)
    batch_idx = [[within_task_order[position] for position in batch] for batch in position_batches]
    batch_task_ids = [[task_ids[index] for index in batch] for batch in batch_idx]
    if len(dataset) == 32:
        v28_preflight.BATCH_SCHEDULE_AUDIT.append(
            {
                "call_index": len(v28_preflight.BATCH_SCHEDULE_AUDIT),
                "dataset_example_count": len(dataset),
                "batch_size": batch_size,
                "batch_count": len(batch_idx),
                "batch_task_ids": batch_task_ids,
                "task_counts": {str(task_id): task_ids.count(task_id) for task_id in sorted(set(task_ids))},
                "current_task_id": current_task_id,
                "batch_policy": protocol.BATCH_POLICY,
                "temporal_batch_order_policy": protocol.TEMPORAL_BATCH_ORDER_POLICY,
            }
        )
    while True:
        for batch_number in range(len(batch_idx)):
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


def run(args: argparse.Namespace) -> dict:
    output = args.output.resolve()
    if output.exists():
        raise RuntimeError(f"refusing overwrite of immutable output: {output}")
    if args.seed != protocol.DATA_SEED or tuple(int(value) for value in args.order.split(",")) != protocol.PREFLIGHT_ORDER:
        raise ValueError("V29 preflight fixed cell drift")
    plan = protocol.build_plan()
    protocol.validate_plan(plan)
    originals = {
        "protocol": v28_preflight.protocol,
        "state": v28_preflight.STATE_SLICE,
        "source": v28_preflight.SOURCE_STATE_SLICE,
        "iterate": v28_preflight.task_stratified_iterate_batches,
    }
    v28_preflight.protocol = protocol
    v28_preflight.STATE_SLICE = STATE_SLICE
    v28_preflight.SOURCE_STATE_SLICE = SOURCE_STATE_SLICE
    v28_preflight.task_stratified_iterate_batches = replay_anchored_iterate_batches
    try:
        result = v28_preflight.run(args)
    finally:
        v28_preflight.protocol = originals["protocol"]
        v28_preflight.STATE_SLICE = originals["state"]
        v28_preflight.SOURCE_STATE_SLICE = originals["source"]
        v28_preflight.task_stratified_iterate_batches = originals["iterate"]
    config = result["config"]
    config.update(
        {
            "state_slice": STATE_SLICE,
            "source_state_slice": SOURCE_STATE_SLICE,
            "changed_protocol_variable": protocol.CHANGED_PROTOCOL_VARIABLE,
            "batch_policy": protocol.BATCH_POLICY,
            "temporal_batch_order_policy": protocol.TEMPORAL_BATCH_ORDER_POLICY,
            "protocol_plan_sha256": plan["plan_sha256"],
        }
    )
    config["contract_sha256"] = digest({key: value for key, value in config.items() if key != "contract_sha256"})
    write_json(output / "config.json", config)
    result.update(
        {
            "state_slice": STATE_SLICE,
            "source_state_slice": SOURCE_STATE_SLICE,
            "classification": "CorrectedLocalReplayAnchoredTemporalMicrobatchPreflightNoBreakthroughClaim",
            "claim_ceiling": "LocalDevelopmentReplayAnchoredTemporalMicrobatchPreflight",
            "config": config,
            "batch_policy": protocol.BATCH_POLICY,
            "temporal_batch_order_policy": protocol.TEMPORAL_BATCH_ORDER_POLICY,
            "h100_authorized": False,
            "breakthrough_claim_eligible": False,
        }
    )
    tasks = json.loads((output / "tasks.json").read_text())
    result["manifest_sha256"] = digest(
        {
            "config": config,
            "tasks": tasks,
            "byte_reference": result["byte_reference"],
            "results": result["results"],
            "batch_schedule_audit": result["batch_schedule_audit"],
        }
    )
    result["result_sha256"] = digest({key: value for key, value in result.items() if key != "result_sha256"})
    write_json(output / "result.json", result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--model", type=Path, default=protocol.MODEL_DEFAULT)
    parser.add_argument("--seed", type=int, default=protocol.DATA_SEED)
    parser.add_argument("--order", default=",".join(str(value) for value in protocol.PREFLIGHT_ORDER))
    parser.add_argument("--task-count", type=int, default=protocol.v24.TASK_COUNT)
    parser.add_argument("--iters", type=int, default=protocol.v24.ITERS_PER_UPDATE)
    args = parser.parse_args()
    print(json.dumps(run(args), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
