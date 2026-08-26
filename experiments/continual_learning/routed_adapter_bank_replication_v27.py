#!/usr/bin/env python3
"""V27 second-model replication of the V26 routed adapter-bank contract.

State slice: continual-learning-replication-task-routed-adapter-bank-v27.

The V26 route contract is reused without scientific changes. This process
only changes the eligible cached model and binds the run to a separately
validated runtime receipt.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from experiments.continual_learning import routed_adapter_bank_candidate_v26 as v26


STATE_SLICE = "continual-learning-replication-task-routed-adapter-bank-v27"
PARENT_STATE_SLICE = "continual-learning-candidate-task-routed-adapter-bank-v26"
EXCLUDED_MODEL = "/Users/shaanp/.lmstudio/models/mlx-community/Qwen2.5-0.5B-Instruct-4bit"
MODEL_DEFAULT = Path("/Users/shaanp/.lmstudio/models/mlx-community/Llama-3.2-1B-Instruct-4bit")
CLAIM_CEILING = "LocalDevelopmentTaskRoutedAdapterBankReplication"


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf8")


def run(args: argparse.Namespace) -> dict:
    model = args.model.resolve()
    if model == Path(EXCLUDED_MODEL).resolve():
        raise ValueError("V27 requires a second model distinct from the V26 Qwen checkpoint")
    if not model.is_dir():
        raise FileNotFoundError(f"model path does not exist: {model}")
    if len(args.runtime_manifest_sha256) != 64 or len(args.runtime_receipt_sha256) != 64:
        raise ValueError("runtime preflight digests must be SHA-256 hex strings")

    # The V26 implementation is the frozen mechanism implementation. Its
    # constants are rebound only in this subprocess so the emitted artifact
    # is owned by the V27 replication state slice.
    v26.MODEL_DEFAULT = model
    v26.STATE_SLICE = STATE_SLICE
    result = v26.run(args)

    root = args.output.resolve()
    config = result["config"]
    config.update(
        {
            "state_slice": STATE_SLICE,
            "parent_candidate_state_slice": PARENT_STATE_SLICE,
            "replication_model_relation": "second_eligible_cached_model_v1",
            "excluded_parent_model": EXCLUDED_MODEL,
            "runtime_preflight_manifest_sha256": args.runtime_manifest_sha256,
            "runtime_preflight_receipt_sha256": args.runtime_receipt_sha256,
            "candidate_claim_ceiling": CLAIM_CEILING,
        }
    )
    config["contract_sha256"] = v26.v11.base.digest(
        {key: value for key, value in config.items() if key != "contract_sha256"}
    )
    result.update(
        {
            "state_slice": STATE_SLICE,
            "claim_ceiling": CLAIM_CEILING,
            "classification": "TaskRoutedAdapterBankSecondModelReplicationNoProductionClaim",
            "config": config,
            "breakthrough_claim_eligible": False,
            "production_claim_eligible": False,
        }
    )
    # Rebind the manifest digest after the replication-only config fields are
    # added. The V26 runner computed this digest before the V27 wrapper
    # extended the config, so carrying it forward would make the independent
    # validator reject an otherwise complete artifact.
    audits = {
        strategy: json.loads((root / "audit" / f"{strategy}.json").read_text(encoding="utf8"))
        for strategy in ("naive_sequential_lora", "replay_lora", "task_adapter_bank")
    }
    result["manifest_sha256"] = v26.v11.base.digest(
        {"config": config, "tasks": result["tasks"], "audits": audits}
    )
    result["result_sha256"] = v26.v11.base.digest(
        {key: value for key, value in result.items() if key != "result_sha256"}
    )
    write_json(root / "config.json", config)
    write_json(root / "result.json", result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--model", type=Path, default=MODEL_DEFAULT)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--order", required=True)
    parser.add_argument("--task-count", type=int, default=4)
    parser.add_argument("--iters", type=int, default=160)
    parser.add_argument("--runtime-manifest-sha256", required=True)
    parser.add_argument("--runtime-receipt-sha256", required=True)
    args = parser.parse_args()
    print(json.dumps(run(args), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
