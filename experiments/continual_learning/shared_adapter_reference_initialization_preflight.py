#!/usr/bin/env python3
"""V25 corrected preflight using fixed shared-adapter initialization."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import mlx.core as mx  # noqa: E402
import numpy as np  # noqa: E402
from mlx_lm import load as load_model  # noqa: E402
from mlx_lm.tuner.utils import linear_to_lora_layers  # noqa: E402

from experiments.continual_learning import shared_adapter_task_keyed_optimizer_state_preflight as v24_preflight  # noqa: E402
from experiments.continual_learning import shared_adapter_reference_initialization_protocol as protocol  # noqa: E402


STATE_SLICE = "continual-learning-protocol-v25-shared-adapter-reference-initialization-preflight"
SOURCE_STATE_SLICE = protocol.STATE_SLICE
MODEL_DEFAULT = Path(protocol.MODEL_DEFAULT)


def build_shared_model(model_path: Path):
    # Match mlx_lm.lora.run: NumPy is seeded before model loading because the
    # loader may consume NumPy state.
    np.random.seed(protocol.ADAPTER_INITIALIZATION_SEED)
    model, tokenizer = load_model(str(model_path), tokenizer_config={"trust_remote_code": True})
    model.freeze()
    # Match the stock MLX launcher: seed after base-model load and before LoRA
    # module construction, which is the actual adapter initialization boundary.
    mx.random.seed(protocol.ADAPTER_INITIALIZATION_SEED)
    linear_to_lora_layers(model, v24_preflight.SHARED_ADAPTER_LAYERS, v24_preflight.LORA_CONFIG)
    return model, tokenizer


def run(args: argparse.Namespace) -> dict:
    original_build = v24_preflight.build_shared_model
    original_state = v24_preflight.STATE_SLICE
    original_source = v24_preflight.SOURCE_STATE_SLICE
    original_protocol = v24_preflight.protocol
    v24_preflight.build_shared_model = build_shared_model
    v24_preflight.STATE_SLICE = STATE_SLICE
    v24_preflight.SOURCE_STATE_SLICE = SOURCE_STATE_SLICE
    v24_preflight.protocol = protocol.v24
    try:
        result = v24_preflight.run(args)
    finally:
        v24_preflight.build_shared_model = original_build
        v24_preflight.STATE_SLICE = original_state
        v24_preflight.SOURCE_STATE_SLICE = original_source
        v24_preflight.protocol = original_protocol

    root = args.output.resolve()
    config = result["config"]
    config.update(
        {
            "state_slice": STATE_SLICE,
            "source_state_slice": SOURCE_STATE_SLICE,
            "changed_protocol_variable": "shared_adapter_reference_initialization_v1",
            "adapter_initialization_seed": protocol.ADAPTER_INITIALIZATION_SEED,
            "adapter_initialization_policy": protocol.ADAPTER_INITIALIZATION_POLICY,
        }
    )
    config["contract_sha256"] = v24_preflight.digest({key: value for key, value in config.items() if key != "contract_sha256"})
    v24_preflight.write_json(root / "config.json", config)
    result.update(
        {
            "state_slice": STATE_SLICE,
            "source_state_slice": SOURCE_STATE_SLICE,
            "classification": "CorrectedLocalSharedAdapterReferenceInitializationPreflightNoBreakthroughClaim",
            "claim_ceiling": "LocalDevelopmentSharedAdapterReferenceInitializationPreflight",
            "config": config,
            "adapter_initialization": {
                "seed": protocol.ADAPTER_INITIALIZATION_SEED,
                "policy": protocol.ADAPTER_INITIALIZATION_POLICY,
            },
            "h100_authorized": False,
            "breakthrough_claim_eligible": False,
        }
    )
    result["manifest_sha256"] = v24_preflight.digest(
        {
            "config": config,
            "tasks": json.loads((root / "tasks.json").read_text()),
            "byte_reference": result["byte_reference"],
            "results": result["results"],
        }
    )
    result["result_sha256"] = v24_preflight.digest({key: value for key, value in result.items() if key != "result_sha256"})
    v24_preflight.write_json(root / "result.json", result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--model", type=Path, default=MODEL_DEFAULT)
    parser.add_argument("--seed", type=int, default=20260812)
    parser.add_argument("--order", default="0,1,2,3")
    parser.add_argument("--task-count", type=int, default=protocol.v24.TASK_COUNT)
    parser.add_argument("--iters", type=int, default=protocol.v24.ITERS_PER_UPDATE)
    args = parser.parse_args()
    print(json.dumps(run(args), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
