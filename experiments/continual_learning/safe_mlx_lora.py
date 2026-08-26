#!/usr/bin/env python3
"""MLX-LM LoRA entrypoint with a model-bound tokenizer policy.

State slice: continual-learning-runtime-execution-v22.

This wrapper preserves MLX-LM's parser and training implementation. It only
adds the tokenizer configuration required by the cached model's declared
``model_type`` and restores the library module after execution.
"""

from __future__ import annotations

import copy
import json
import os
import sys
from pathlib import Path
from typing import Any, Sequence

from experiments.continual_learning.mlx_tokenizer_policy import (
    STATE_SLICE,
    tokenizer_config_from_policy,
    tokenizer_policy_for_model,
)


def require_offline_environment(environment: dict[str, str] | None = None) -> None:
    """Reject execution unless both supported model hubs are offline."""

    values = os.environ if environment is None else environment
    required = {"HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1"}
    if any(values.get(key) != expected for key, expected in required.items()):
        raise RuntimeError("safe MLX LoRA requires offline model-hub environment")


def run(argv: Sequence[str] | None = None) -> dict[str, Any]:
    """Run MLX-LM LoRA with deterministic default merging and policy binding."""

    require_offline_environment()

    import mlx_lm.lora as lora
    from mlx_lm import load as mlx_load

    args = lora.build_parser().parse_args(argv)
    for key, value in lora.CONFIG_DEFAULTS.items():
        if getattr(args, key, None) is None:
            setattr(args, key, copy.deepcopy(value))
    model = Path(args.model).resolve()
    policy = tokenizer_policy_for_model(model)
    policy_config = tokenizer_config_from_policy(policy)
    original_load = lora.load

    def policy_bound_load(
        path: str,
        tokenizer_config: dict[str, Any] | None = None,
        **kwargs: Any,
    ):
        merged = dict(tokenizer_config or {})
        merged.update(policy_config)
        return mlx_load(path, tokenizer_config=merged or None, **kwargs)

    lora.load = policy_bound_load
    try:
        print(
            json.dumps(
                {
                    "event": "mlx_tokenizer_policy",
                    "network_access": False,
                    "state_slice": STATE_SLICE,
                    "tokenizer_policy": policy,
                },
                sort_keys=True,
            )
        )
        lora.run(args)
    finally:
        lora.load = original_load
    return policy


def main() -> int:
    run(sys.argv[1:])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
