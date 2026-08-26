#!/usr/bin/env python3
"""V22 offline local-model runtime seam and bounded inference receipt."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any

STATE_SLICE = "continual-learning-runtime-execution-v22"
CLAIM_CEILING = "LocalDevelopmentRuntimeExecution"
DEFAULT_MODEL = Path(
    "/Users/shaanp/.lmstudio/models/mlx-community/Qwen2.5-0.5B-Instruct-4bit"
)
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from experiments.continual_learning.model_benchmark import ChoiceModel, make_tasks, prompt_for
from experiments.continual_learning.mlx_tokenizer_policy import tokenizer_policy_for_model


def digest(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def sha256_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def model_manifest(model_path: Path) -> dict[str, Any]:
    files = []
    for path in sorted(path for path in model_path.rglob("*") if path.is_file() and not path.is_symlink()):
        files.append(
            {
                "path": path.relative_to(model_path).as_posix(),
                "byte_len": path.stat().st_size,
                "sha256": sha256_file(path),
            }
        )
    if not files:
        raise ValueError(f"cached model directory has no regular files: {model_path}")
    manifest = {"model_name": model_path.name, "files": files}
    return {"manifest": manifest, "manifest_sha256": digest(manifest)}


def package_version(name: str) -> str:
    try:
        return version(name)
    except PackageNotFoundError:
        return "unavailable"


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _ensure_external_output(root: Path) -> None:
    if root == REPO_ROOT or REPO_ROOT in root.parents:
        raise ValueError("runtime output must be outside the repository")
    if root.exists():
        raise FileExistsError(f"refusing overwrite of immutable output: {root}")


def run_smoke(output: Path, model_path: Path = DEFAULT_MODEL, seed: int = 20260819) -> dict[str, Any]:
    """Load the cached model, execute one constrained probe, and write a receipt."""

    root = output.resolve()
    model = model_path.resolve()
    _ensure_external_output(root)
    if not model.is_dir():
        raise FileNotFoundError(f"model path does not exist: {model}")

    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    manifest = model_manifest(model)
    tokenizer_policy = tokenizer_policy_for_model(model)
    config = {
        "state_slice": STATE_SLICE,
        "claim_ceiling": CLAIM_CEILING,
        "model_name": model.name,
        "seed": seed,
        "probe": "single-token-four-label-logit-selection-v1",
        "network_access": False,
        "training": False,
        "offline_environment": {
            "HF_HUB_OFFLINE": os.environ.get("HF_HUB_OFFLINE"),
            "TRANSFORMERS_OFFLINE": os.environ.get("TRANSFORMERS_OFFLINE"),
        },
        "runtime": {
            "python": package_version("pip"),
            "mlx": package_version("mlx"),
            "mlx_lm": package_version("mlx-lm"),
        },
        "tokenizer_policy": tokenizer_policy,
        "model_manifest_sha256": manifest["manifest_sha256"],
    }
    config["config_sha256"] = digest(config)

    root.mkdir(parents=True)
    write_json(root / "config.json", config)
    fact = make_tasks(seed, task_count=4, facts_per_task=2)[0].facts[0]
    prompt = prompt_for(fact)
    started = time.perf_counter()
    model_runtime = ChoiceModel(model)
    answer = model_runtime.answer(prompt)
    elapsed_ms = round((time.perf_counter() - started) * 1000, 3)
    receipt = {
        "state_slice": STATE_SLICE,
        "claim_ceiling": CLAIM_CEILING,
        "model_loaded": True,
        "inference_executed": True,
        "training": False,
        "network_access": False,
        "tokenizer_policy": tokenizer_policy,
        "candidate_labels": sorted(answer["logits"]),
        "prediction": answer["prediction"],
        "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
        "fact_id": fact.fact_id,
        "elapsed_ms": elapsed_ms,
        "model_manifest_sha256": manifest["manifest_sha256"],
    }
    receipt["receipt_sha256"] = digest(receipt)
    write_json(root / "model-manifest.json", manifest)
    write_json(root / "receipt.json", receipt)
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--model", type=Path, default=DEFAULT_MODEL)
    parser.add_argument("--seed", type=int, default=20260819)
    args = parser.parse_args()
    print(json.dumps(run_smoke(args.output, args.model, args.seed), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
