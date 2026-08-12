#!/usr/bin/env python3
"""V25 pure-data protocol for fixed shared-adapter initialization.

V25 changes only the shared adapter's initialization seed relative to V24.
The V24 task/update schedule and task-keyed optimizer-state contract remain
frozen. This module does not train a model or authorize replication.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from experiments.continual_learning import shared_adapter_task_keyed_optimizer_state_protocol as v24  # noqa: E402


STATE_SLICE = "continual-learning-protocol-v25-shared-adapter-reference-initialization"
SOURCE_STATE_SLICE = v24.STATE_SLICE
MODEL_DEFAULT = v24.MODEL_DEFAULT
ADAPTER_INITIALIZATION_SEED = 20260811
ADAPTER_INITIALIZATION_POLICY = "fixed_reference_seed_post_model_load_from_prior_successful_family_v1"


def digest(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf8")


def build_plan() -> dict:
    base = v24.build_plan()
    plan = dict(base)
    plan.update(
        {
            "state_slice": STATE_SLICE,
            "source_state_slice": SOURCE_STATE_SLICE,
            "classification": "SharedAdapterReferenceInitializationProtocolOnlyNoBreakthroughClaim",
            "claim_ceiling": "LocalDevelopmentSharedAdapterReferenceInitializationProtocol",
            "changed_protocol_variable": "shared_adapter_reference_initialization_v1",
            "adapter_initialization_seed": ADAPTER_INITIALIZATION_SEED,
            "adapter_initialization_policy": ADAPTER_INITIALIZATION_POLICY,
            "next_run_condition": "one_corrected_local_preflight_after_independent_schedule_validation",
        }
    )
    gates = dict(base["gates"])
    gates.update(
        {
            "adapter_initialization_seed_fixed": ADAPTER_INITIALIZATION_SEED == 20260811,
            "only_initialization_changed_from_v24": True,
            "h100_authorized": False,
            "breakthrough_claim_eligible": False,
        }
    )
    plan["gates"] = gates
    plan["model_training_authorized"] = False
    plan["h100_authorized"] = False
    plan["breakthrough_claim_eligible"] = False
    plan["plan_sha256"] = digest({key: value for key, value in plan.items() if key != "plan_sha256"})
    return plan


def validate_plan(plan: dict) -> dict:
    expected = build_plan()
    if plan != expected:
        raise ValueError("V25 protocol plan drift")
    if plan["plan_sha256"] != digest({key: value for key, value in plan.items() if key != "plan_sha256"}):
        raise ValueError("V25 plan digest mismatch")
    contract_keys = [key for key in plan["gates"] if key not in {"h100_authorized", "breakthrough_claim_eligible"}]
    if not all(plan["gates"][key] for key in contract_keys):
        raise ValueError("V25 protocol gate failure")
    if plan["h100_authorized"] or plan["breakthrough_claim_eligible"]:
        raise ValueError("V25 authority boundary drift")
    return {
        "valid": True,
        "state_slice": plan["state_slice"],
        "source_state_slice": plan["source_state_slice"],
        "cell_count": len(plan["cells"]),
        "gates": plan["gates"],
        "adapter_initialization_seed": plan["adapter_initialization_seed"],
        "model_training_authorized": plan["model_training_authorized"],
        "h100_authorized": plan["h100_authorized"],
        "plan_sha256": plan["plan_sha256"],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    if output.exists():
        raise RuntimeError(f"refusing overwrite of immutable output: {output}")
    plan = build_plan()
    output.parent.mkdir(parents=True, exist_ok=True)
    write_json(output, plan)
    print(json.dumps(validate_plan(plan), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
