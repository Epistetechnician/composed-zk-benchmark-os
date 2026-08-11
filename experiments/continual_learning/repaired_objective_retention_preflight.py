#!/usr/bin/env python3
"""V14 retention preflight using the V13 training-objective repair."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from experiments.continual_learning import residue_only_codebook_benchmark as v11  # noqa: E402


STATE_SLICE = "continual-learning-protocol-v14-repaired-objective-retention"
SOURCE_STATE_SLICE = "continual-learning-protocol-v13-training-objective-repair"
MODEL_DEFAULT = Path("/Users/shaanp/.lmstudio/models/mlx-community/Qwen2.5-0.5B-Instruct-4bit")


def digest(value) -> str:
    return v11.base.digest(value)


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf8")


def run(args: argparse.Namespace) -> dict:
    model = args.model.resolve()
    order = tuple(int(value) for value in args.order.split(","))
    if (
        args.seed != 20260810
        or order != (0, 1, 2, 3)
        or args.task_count != 4
        or args.iters != 160
        or model != MODEL_DEFAULT.resolve()
    ):
        raise ValueError("V14 fixed contract drift")

    original_state_slice = v11.STATE_SLICE
    v11.STATE_SLICE = STATE_SLICE
    try:
        result = v11.run(args)
    finally:
        v11.STATE_SLICE = original_state_slice

    root = args.output.resolve()
    config = result["config"]
    config.update(
        {
            "source_state_slice": SOURCE_STATE_SLICE,
            "objective_repair": "iterations_only_v1",
            "baseline_iters": 40,
            "recovery_iters": 20,
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
            "claim_ceiling": "LocalDevelopmentRepairedObjectiveRetentionPilot",
            "classification": "RepairedObjectiveRetentionPilotNoBreakthroughClaim",
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
