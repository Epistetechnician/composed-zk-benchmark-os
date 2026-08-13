#!/usr/bin/env python3
"""V29 confirmation preflight on the other frozen 20260812 V27 tie cell."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from experiments.continual_learning import replay_anchored_temporal_confirmation_protocol as protocol  # noqa: E402
from experiments.continual_learning import replay_anchored_temporal_preflight as v29_preflight  # noqa: E402


STATE_SLICE = "continual-learning-protocol-v29-replay-anchored-temporal-confirmation-preflight"
SOURCE_STATE_SLICE = protocol.STATE_SLICE


def digest(value) -> str:
    return protocol.digest(value)


def write_json(path: Path, value) -> None:
    protocol.write_json(path, value)


def run(args: argparse.Namespace) -> dict:
    output = args.output.resolve()
    if output.exists():
        raise RuntimeError(f"refusing overwrite of immutable output: {output}")
    if args.seed != protocol.DATA_SEED or tuple(int(value) for value in args.order.split(",")) != protocol.PREFLIGHT_ORDER:
        raise ValueError("V29 confirmation preflight fixed cell drift")
    plan = protocol.build_plan()
    protocol.validate_plan(plan)
    originals = {
        "protocol": v29_preflight.protocol,
        "state": v29_preflight.STATE_SLICE,
        "source": v29_preflight.SOURCE_STATE_SLICE,
    }
    v29_preflight.protocol = protocol
    v29_preflight.STATE_SLICE = STATE_SLICE
    v29_preflight.SOURCE_STATE_SLICE = SOURCE_STATE_SLICE
    try:
        result = v29_preflight.run(args)
    finally:
        v29_preflight.protocol = originals["protocol"]
        v29_preflight.STATE_SLICE = originals["state"]
        v29_preflight.SOURCE_STATE_SLICE = originals["source"]
    config = result["config"]
    config.update(
        {
            "state_slice": STATE_SLICE,
            "source_state_slice": SOURCE_STATE_SLICE,
            "confirmation_of_state_slice": protocol.CONFIRMATION_OF_STATE_SLICE,
            "confirmation_cell": plan["confirmation_cell"],
            "protocol_plan_sha256": plan["plan_sha256"],
        }
    )
    config["contract_sha256"] = digest({key: value for key, value in config.items() if key != "contract_sha256"})
    write_json(output / "config.json", config)
    result.update(
        {
            "state_slice": STATE_SLICE,
            "source_state_slice": SOURCE_STATE_SLICE,
            "confirmation_of_state_slice": protocol.CONFIRMATION_OF_STATE_SLICE,
            "confirmation_cell": plan["confirmation_cell"],
            "classification": "CorrectedLocalReplayAnchoredTemporalConfirmationPreflightNoBreakthroughClaim",
            "claim_ceiling": "LocalDevelopmentReplayAnchoredTemporalConfirmationPreflight",
            "config": config,
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
