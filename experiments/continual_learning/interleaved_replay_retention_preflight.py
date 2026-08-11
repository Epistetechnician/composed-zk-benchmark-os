#!/usr/bin/env python3
"""V15 task/update-protocol redesign with interleaved replay scheduling."""

from __future__ import annotations

import argparse
import itertools
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from experiments.continual_learning import repaired_objective_retention_preflight as v14  # noqa: E402
from experiments.continual_learning import residue_only_codebook_benchmark as v11  # noqa: E402


STATE_SLICE = "continual-learning-protocol-v15-interleaved-replay-retention"
SOURCE_STATE_SLICE = "continual-learning-protocol-v14-repaired-objective-retention"
MODEL_DEFAULT = Path("/Users/shaanp/.lmstudio/models/mlx-community/Qwen2.5-0.5B-Instruct-4bit")
_ORIGINAL_WRITE_DATASET = None


def digest(value) -> str:
    return v11.base.digest(value)


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf8")


def task_token(row: dict[str, str]) -> str:
    return row["prompt"].split("Task token: ", 1)[1].split(".", 1)[0]


def interleave_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    grouped: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        grouped.setdefault(task_token(row), []).append(row)
    return [row for group in itertools.zip_longest(*(grouped[key] for key in sorted(grouped)), fillvalue=None) for row in group if row is not None]


def scheduled_write_dataset(path: Path, rows: list[dict[str, str]]) -> None:
    if len(path.parts) >= 2 and path.parts[-2] == "replay_lora":
        rows = interleave_rows(rows)
    assert _ORIGINAL_WRITE_DATASET is not None
    _ORIGINAL_WRITE_DATASET(path, rows)


def run(args: argparse.Namespace) -> dict:
    if args.model.resolve() != MODEL_DEFAULT.resolve() or args.seed != 20260810 or args.order != "0,1,2,3" or args.task_count != 4 or args.iters != 160:
        raise ValueError("V15 fixed contract drift")
    global _ORIGINAL_WRITE_DATASET
    original_write_dataset = v11.base.write_dataset
    _ORIGINAL_WRITE_DATASET = original_write_dataset
    original_state_slice = v14.STATE_SLICE
    original_source_state_slice = v14.SOURCE_STATE_SLICE
    v11.base.write_dataset = scheduled_write_dataset
    v14.STATE_SLICE = STATE_SLICE
    v14.SOURCE_STATE_SLICE = SOURCE_STATE_SLICE
    try:
        result = v14.run(args)
    finally:
        v11.base.write_dataset = original_write_dataset
        _ORIGINAL_WRITE_DATASET = None
        v14.STATE_SLICE = original_state_slice
        v14.SOURCE_STATE_SLICE = original_source_state_slice

    root = args.output.resolve()
    config = result["config"]
    config.update(
        {
            "source_state_slice": SOURCE_STATE_SLICE,
            "task_update_redesign": "interleaved_replay_v1",
            "replay_row_schedule": "task_stratified_round_robin_v1",
        }
    )
    config["contract_sha256"] = digest({key: value for key, value in config.items() if key != "contract_sha256"})
    write_json(root / "config.json", config)
    tasks = json.loads((root / "tasks.json").read_text())
    audits = {
        strategy: json.loads((root / "audit" / f"{strategy}.json").read_text())
        for strategy in ("naive_sequential_lora", "replay_lora", "task_adapter_bank")
    }
    result.update(
        {
            "state_slice": STATE_SLICE,
            "claim_ceiling": "LocalDevelopmentInterleavedReplayRetentionPilot",
            "classification": "InterleavedReplayRetentionPilotNoBreakthroughClaim",
            "config": config,
            "tasks": tasks,
            "retention_comparison_run": True,
            "breakthrough_claim_eligible": False,
            "manifest_sha256": digest({"config": config, "tasks": tasks, "audits": audits}),
        }
    )
    result["result_sha256"] = digest({key: value for key, value in result.items() if key != "result_sha256"})
    write_json(root / "result.json", result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--model", type=Path, default=MODEL_DEFAULT)
    parser.add_argument("--seed", type=int, default=20260810)
    parser.add_argument("--order", default="0,1,2,3")
    parser.add_argument("--task-count", type=int, default=4)
    parser.add_argument("--iters", type=int, default=160)
    args = parser.parse_args()
    print(json.dumps(run(args), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
