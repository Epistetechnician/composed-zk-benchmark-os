#!/usr/bin/env python3
"""Bounded offline LoRA compatibility smoke with digest-bound receipts.

State slice: continual-learning-runtime-execution-v22.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from experiments.continual_learning.mlx_tokenizer_policy import tokenizer_policy_for_model
from experiments.continual_learning.model_benchmark import (
    ChoiceModel,
    make_tasks,
    prompt_for,
    safe_training_command,
    training_example,
    write_dataset,
)
from experiments.continual_learning.runtime_seam import DEFAULT_MODEL, digest, sha256_file, write_json


STATE_SLICE = "continual-learning-runtime-execution-v22"
CLAIM_CEILING = "LocalDevelopmentRuntimeExecution"
PROTOCOL = "mlx-tokenizer-policy-training-smoke-v1"
ITERS = 2
TRAINABLE_LAYERS = 1
DATASET_ROWS = 4


def _ensure_external_output(root: Path) -> None:
    if root == REPO_ROOT or REPO_ROOT in root.parents:
        raise ValueError("training smoke output must be outside the repository")
    if root.exists():
        raise FileExistsError(f"refusing overwrite of immutable output: {root}")


def _file_digests(paths: list[Path], root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): sha256_file(path)
        for path in sorted(paths, key=lambda item: str(item))
    }


def run_smoke(output: Path, model_path: Path = DEFAULT_MODEL, seed: int = 20260825) -> dict[str, Any]:
    root = output.resolve()
    model = model_path.resolve()
    _ensure_external_output(root)
    if not model.is_dir():
        raise FileNotFoundError(f"model path does not exist: {model}")

    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    policy = tokenizer_policy_for_model(model)
    model_config_sha256 = sha256_file(model / "config.json")
    config = {
        "state_slice": STATE_SLICE,
        "claim_ceiling": CLAIM_CEILING,
        "protocol": PROTOCOL,
        "model_name": model.name,
        "model_config_sha256": model_config_sha256,
        "seed": seed,
        "iters": ITERS,
        "trainable_layers": TRAINABLE_LAYERS,
        "dataset_rows": DATASET_ROWS,
        "network_access": False,
        "training": True,
        "retention_executed": False,
        "offline_environment": {
            "HF_HUB_OFFLINE": "1",
            "TRANSFORMERS_OFFLINE": "1",
        },
        "tokenizer_policy": policy,
        "trainer_entrypoint": "experiments.continual_learning.safe_mlx_lora",
    }
    config["config_sha256"] = digest(config)

    root.mkdir(parents=True)
    write_json(root / "config.json", config)
    facts = make_tasks(seed, task_count=4, facts_per_task=DATASET_ROWS)[0].facts
    dataset = root / "data"
    write_dataset(dataset, [training_example(fact) for fact in facts])
    adapter = root / "adapter"
    command = safe_training_command(model, dataset, adapter, seed, ITERS, None)
    command[command.index("--num-layers") + 1] = str(TRAINABLE_LAYERS)
    environment = os.environ.copy()
    completed = subprocess.run(
        command,
        env=environment,
        text=True,
        capture_output=True,
        check=False,
    )
    log = root / "training.log"
    log.write_text(completed.stdout + "\n" + completed.stderr, encoding="utf-8")
    if completed.returncode != 0:
        raise RuntimeError(f"safe MLX LoRA smoke failed: {completed.returncode}")

    adapter_file = adapter / "adapters.safetensors"
    if not adapter_file.is_file():
        raise RuntimeError("safe MLX LoRA smoke produced no final adapter")
    model_runtime = ChoiceModel(model, adapter)
    answer = model_runtime.answer(prompt_for(facts[0]))
    dataset_files = [dataset / name for name in ("train.jsonl", "valid.jsonl", "test.jsonl")]
    receipt = {
        "state_slice": STATE_SLICE,
        "claim_ceiling": CLAIM_CEILING,
        "protocol": PROTOCOL,
        "model_name": model.name,
        "model_config_sha256": model_config_sha256,
        "training": True,
        "inference_executed": True,
        "network_access": False,
        "retention_executed": False,
        "tokenizer_policy": policy,
        "candidate_labels": sorted(answer["logits"]),
        "prediction": answer["prediction"],
        "adapter_sha256": sha256_file(adapter_file),
        "training_log_sha256": sha256_file(log),
        "dataset_sha256": _file_digests(dataset_files, root),
        "command_sha256": hashlib.sha256(
            json.dumps(command, separators=(",", ":")).encode("utf-8")
        ).hexdigest(),
    }
    receipt["receipt_sha256"] = digest(receipt)
    write_json(root / "receipt.json", receipt)
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--model", type=Path, default=DEFAULT_MODEL)
    parser.add_argument("--seed", type=int, default=20260825)
    args = parser.parse_args()
    print(json.dumps(run_smoke(args.output, args.model, args.seed), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
