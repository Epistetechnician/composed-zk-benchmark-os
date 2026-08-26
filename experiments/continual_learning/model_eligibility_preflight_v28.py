#!/usr/bin/env python3
"""V28 inference-only model eligibility preflight for routed adapter artifacts.

State slice: continual-learning-model-eligibility-preflight-v28.

This audit consumes sealed V26 or V27 adapter-bank artifacts. It runs no
training and makes no provider or production claim. A model is eligible for a
future retention campaign only if every task adapter first acquires its own
training facts above the no-update baseline and the preregistered T0 floors
also pass.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from experiments.continual_learning.compositional_model_benchmark import ChoiceModel, Fact
from experiments.continual_learning.routed_adapter_bank_candidate_v26 import route_bound_accuracy
from experiments.continual_learning import validate_routed_adapter_bank_candidate_v26 as validate_v26
from experiments.continual_learning import validate_routed_adapter_bank_replication_v27 as validate_v27


STATE_SLICE = "continual-learning-model-eligibility-preflight-v28"
CLAIM_CEILING = "LocalDevelopmentModelEligibilityPreflight"
TARGET_TASK_ID = 0
TARGET_FLOOR = 0.75


def digest(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf8")
    ).hexdigest()


def _facts(task: dict[str, Any], field: str) -> tuple[Fact, ...]:
    return tuple(Fact(**fact) for fact in task[field])


def _validate_case(root: Path, protocol: str) -> dict[str, Any]:
    if protocol == "v26":
        return validate_v26.validate(root)
    if protocol == "v27":
        return validate_v27.validate(root)
    raise ValueError(f"unsupported protocol: {protocol}")


def _metric(model: ChoiceModel, facts: tuple[Fact, ...]) -> dict[str, Any]:
    result = route_bound_accuracy(model, facts)
    observed = [row["observed"] for row in result["rows"]]
    result["constant_output"] = len(set(observed)) == 1
    return result


def eligibility_gates(task_results: list[dict[str, Any]]) -> dict[str, bool]:
    target = next(item for item in task_results if item["task_id"] == TARGET_TASK_ID)
    return {
        "all_task_train_above_no_update": all(
            item["adapter_train"]["accuracy"] > item["no_update_train"]["accuracy"]
            for item in task_results
        ),
        "target_train_floor": target["adapter_train"]["accuracy"] >= TARGET_FLOOR,
        "target_heldout_floor": target["adapter_test"]["accuracy"] >= TARGET_FLOOR,
        "target_not_constant_output": target["adapter_train"]["constant_output"] is False,
    }


def case_is_eligible(structural_validation: dict[str, Any], gates: dict[str, bool]) -> bool:
    return structural_validation.get("valid") is True and all(gates.values())


def run(artifact_root: Path, model: Path, protocol: str, output: Path) -> dict[str, Any]:
    root = artifact_root.resolve()
    model = model.resolve()
    destination = output.resolve()
    repo_root = Path(__file__).resolve().parents[2]
    if destination == repo_root or repo_root in destination.parents:
        raise ValueError("eligibility output must remain outside the repository")
    if destination.exists():
        raise FileExistsError(f"refusing overwrite of immutable eligibility root: {destination}")
    if not model.is_dir():
        raise FileNotFoundError(f"model path does not exist: {model}")

    cases = []
    for case_root in sorted(path for path in root.glob("seed-*") if path.is_dir()):
        structural = _validate_case(case_root, protocol)
        config = json.loads((case_root / "config.json").read_text(encoding="utf8"))
        if Path(config["model"]).resolve() != model:
            raise ValueError(f"model binding drift: {case_root}")
        tasks = json.loads((case_root / "tasks.json").read_text(encoding="utf8"))
        base = ChoiceModel(model)
        task_results = []
        for task in tasks:
            train = _facts(task, "train_facts")
            test = _facts(task, "test_facts")
            adapter = case_root / "adapters" / "task_adapter_bank" / f"task-{task['task_id']}"
            adapter_model = ChoiceModel(model, adapter)
            task_results.append(
                {
                    "task_id": task["task_id"],
                    "route_key": task["task_token"],
                    "no_update_train": _metric(base, train),
                    "adapter_train": _metric(adapter_model, train),
                    "adapter_test": _metric(adapter_model, test),
                }
            )
        gates = eligibility_gates(task_results)
        case_eligible = case_is_eligible(structural, gates)
        cases.append(
            {
                "case": case_root.name,
                "structural_validation": structural,
                "task_results": task_results,
                "eligibility_gates": gates,
                "eligible": case_eligible,
            }
        )

    if not cases:
        raise ValueError("no campaign cases found")
    report = {
        "state_slice": STATE_SLICE,
        "claim_ceiling": CLAIM_CEILING,
        "protocol": protocol,
        "model": str(model),
        "target_task_id": TARGET_TASK_ID,
        "target_floor": TARGET_FLOOR,
        "network_access": False,
        "training": False,
        "cases": cases,
        "all_cases_valid": all(case["structural_validation"]["valid"] for case in cases),
        "all_cases_eligible": all(case["eligible"] for case in cases),
        "scientific_promotion": False,
        "production_claim_eligible": False,
    }
    report["report_sha256"] = digest(report)
    destination.mkdir(parents=True)
    (destination / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf8"
    )
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-root", type=Path, required=True)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--protocol", choices=("v26", "v27"), required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = run(args.artifact_root, args.model, args.protocol, args.output)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["all_cases_eligible"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
