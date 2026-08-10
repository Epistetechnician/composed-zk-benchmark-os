#!/usr/bin/env python3
"""Run the bounded V6 same-model replication campaign."""

from __future__ import annotations

import argparse
import json
import os
import statistics
import subprocess
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
MODEL_BENCHMARK = REPO_ROOT / "experiments/continual_learning/model_benchmark.py"
VALIDATOR = REPO_ROOT / "experiments/continual_learning/validate_model_benchmark.py"
SEEDS = (20260810, 20260811, 20260812)
ORDERS = ((0, 1, 2, 3), (0, 2, 3, 1), (0, 3, 1, 2))


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf8")


def campaign_cases() -> list[tuple[int, tuple[int, ...]]]:
    return [(seed, order) for seed in SEEDS for order in ORDERS]


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    deltas = [row["retention_delta"] for row in rows]
    return {
        "state_slice": "continual-learning-model-adapter-v6-replication-campaign",
        "primary_metric": "replay_retention_minus_naive_retention",
        "campaign_size": len(rows),
        "rows": rows,
        "mean_retention_delta": statistics.mean(deltas),
        "median_retention_delta": statistics.median(deltas),
        "all_nine_retention_deltas_positive": all(delta > 0 for delta in deltas),
        "replication_gate_passed": len(rows) == 9 and all(delta > 0 for delta in deltas),
        "second_model_or_h100_authorized": False,
    }


def run_campaign(output_root: Path, model: Path, iters: int) -> dict[str, Any]:
    if output_root.exists():
        raise RuntimeError(f"refusing overwrite of immutable output: {output_root}")
    output_root.mkdir(parents=True)
    env = os.environ.copy()
    env.update({"HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1"})
    rows: list[dict[str, Any]] = []
    for seed, order in campaign_cases():
        order_name = "".join(str(value) for value in order)
        run_root = output_root / f"seed-{seed}-order-{order_name}"
        command = [
            sys.executable,
            str(MODEL_BENCHMARK),
            "--output",
            str(run_root),
            "--model",
            str(model),
            "--seed",
            str(seed),
            "--order",
            ",".join(str(value) for value in order),
            "--task-count",
            "4",
            "--facts-per-task",
            "8",
            "--replay-capacity",
            "24",
            "--update-budget",
            "32",
            "--iters",
            str(iters),
        ]
        completed = subprocess.run(command, env=env, text=True, capture_output=True, check=False)
        (output_root / f"seed-{seed}-order-{order_name}.log").write_text(
            completed.stdout + "\n" + completed.stderr,
            encoding="utf8",
        )
        if completed.returncode != 0:
            raise RuntimeError(f"replication failed for seed={seed}, order={order}: {completed.returncode}")
        validation = subprocess.run(
            [
                sys.executable,
                str(VALIDATOR),
                str(run_root),
                "--expected-seed",
                str(seed),
                "--expected-order",
                ",".join(str(value) for value in order),
            ],
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )
        (output_root / f"seed-{seed}-order-{order_name}.validation.json").write_text(
            validation.stdout + "\n" + validation.stderr,
            encoding="utf8",
        )
        if validation.returncode != 0:
            raise RuntimeError(f"validation failed for seed={seed}, order={order}: {validation.returncode}")
        result = json.loads((run_root / "result.json").read_text())
        naive = result["results"]["naive_sequential_lora"]["retention_after_interference"]["accuracy"]
        replay = result["results"]["replay_lora"]["retention_after_interference"]["accuracy"]
        rows.append(
            {
                "seed": seed,
                "order": list(order),
                "manifest_sha256": result["manifest_sha256"],
                "naive_retention": naive,
                "replay_retention": replay,
                "retention_delta": replay - naive,
                "candidate_gates": {
                    "retrieval_above_no_update": result["results"]["retrieval"]["acquisition"]["accuracy"]
                    > result["results"]["no_update"]["acquisition"]["accuracy"],
                    "trainable_acquisition_above_no_update": max(
                        result["results"]["naive_sequential_lora"]["acquisition"]["accuracy"],
                        result["results"]["replay_lora"]["acquisition"]["accuracy"],
                    ) > result["results"]["no_update"]["acquisition"]["accuracy"],
                    "replay_retention_above_naive": replay > naive,
                },
            }
        )
    summary = summarize(rows)
    write_json(output_root / "campaign-summary.json", summary)
    return summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--model",
        type=Path,
        default=Path("/Users/shaanp/.lmstudio/models/mlx-community/Qwen2.5-0.5B-Instruct-4bit"),
    )
    parser.add_argument("--iters", type=int, default=40)
    args = parser.parse_args()
    print(json.dumps(run_campaign(args.output.resolve(), args.model.resolve(), args.iters), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
