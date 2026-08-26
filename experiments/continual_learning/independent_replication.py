#!/usr/bin/env python3
"""V23 independent subprocess campaign over the cached local model."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import statistics
import subprocess
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
STATE_SLICE = "continual-learning-independent-replication-v23"
CLAIM_CEILING = "LocalDevelopmentIndependentExecutionCampaign"
MODEL_BENCHMARK = REPO_ROOT / "experiments/continual_learning/model_benchmark.py"
VALIDATOR = REPO_ROOT / "experiments/continual_learning/validate_model_benchmark.py"
CASES = ((20260819, (0, 1, 2, 3)), (20260820, (0, 2, 3, 1)))


def digest_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _ensure_external_output(root: Path) -> None:
    if root == REPO_ROOT or REPO_ROOT in root.parents:
        raise ValueError("replication output must be outside the repository")


def campaign_cases() -> list[tuple[int, tuple[int, ...]]]:
    return list(CASES)


def summarize(rows: list[dict[str, Any]], iters: int) -> dict[str, Any]:
    deltas = [row["retention_delta"] for row in rows]
    return {
        "state_slice": STATE_SLICE,
        "claim_ceiling": CLAIM_CEILING,
        "executor": "model_benchmark.py subprocess",
        "validator": "validate_model_benchmark.py subprocess",
        "campaign_size": len(rows),
        "iters": iters,
        "primary_metric": "replay_retention_minus_naive_retention",
        "rows": rows,
        "mean_retention_delta": statistics.mean(deltas) if deltas else None,
        "all_retention_deltas_positive": bool(deltas) and all(delta > 0 for delta in deltas),
        "campaign_gate_passed": len(rows) == len(CASES) and bool(deltas) and all(delta > 0 for delta in deltas),
        "network_access": False,
        "production_claim_eligible": False,
    }


def run_campaign(output_root: Path, model: Path, iters: int = 40, resume: bool = False) -> dict[str, Any]:
    root = output_root.resolve()
    _ensure_external_output(root)
    if root.exists() and not resume:
        raise FileExistsError(f"refusing overwrite of immutable output: {root}")
    root.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env.update({"HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1"})
    rows = []
    for seed, order in CASES:
        order_name = "".join(str(value) for value in order)
        run_root = root / f"seed-{seed}-order-{order_name}"
        if not run_root.exists():
            command = [
                sys.executable,
                str(MODEL_BENCHMARK),
                "--output",
                str(run_root),
                "--model",
                str(model.resolve()),
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
            (root / f"seed-{seed}-order-{order_name}.executor.log").write_text(
                completed.stdout + "\n" + completed.stderr, encoding="utf-8"
            )
            if completed.returncode != 0:
                raise RuntimeError(f"executor failed for seed={seed}, order={order}: {completed.returncode}")
        elif not (run_root / "result.json").exists():
            raise ValueError(f"incomplete immutable run root: {run_root}")

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
        (root / f"seed-{seed}-order-{order_name}.validator.log").write_text(
            validation.stdout + "\n" + validation.stderr, encoding="utf-8"
        )
        if validation.returncode != 0:
            raise RuntimeError(f"validator failed for seed={seed}, order={order}: {validation.returncode}")
        result = json.loads((run_root / "result.json").read_text(encoding="utf-8"))
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
                "executor_sha256": digest_file(MODEL_BENCHMARK),
                "validator_sha256": digest_file(VALIDATOR),
            }
        )
    summary = summarize(rows, iters)
    write_json(root / "campaign-summary.json", summary)
    return summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--model", type=Path, default=Path(
        "/Users/shaanp/.lmstudio/models/mlx-community/Qwen2.5-0.5B-Instruct-4bit"
    ))
    parser.add_argument("--iters", type=int, default=40)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    summary = run_campaign(args.output, args.model, args.iters, args.resume)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if summary["campaign_gate_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
