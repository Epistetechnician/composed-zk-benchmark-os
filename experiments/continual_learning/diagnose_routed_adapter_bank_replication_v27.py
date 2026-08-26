#!/usr/bin/env python3
"""Read-only V27 failure diagnosis for task-adapter acquisition collapse.

State slice: continual-learning-diagnosis-task-routed-adapter-bank-v27.

This audit consumes sealed V27 artifacts and runs inference only. It does not
train, mutate adapters, access the network, or promote a scientific claim.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from experiments.continual_learning.compositional_model_benchmark import ChoiceModel, Fact
from experiments.continual_learning.routed_adapter_bank_candidate_v26 import route_bound_accuracy
from experiments.continual_learning.validate_routed_adapter_bank_replication_v27 import validate


STATE_SLICE = "continual-learning-diagnosis-task-routed-adapter-bank-v27"
REPLICATION_STATE_SLICE = "continual-learning-replication-task-routed-adapter-bank-v27"


def _facts(task: dict[str, Any], field: str) -> tuple[Fact, ...]:
    return tuple(Fact(**fact) for fact in task[field])


def _summary(model: ChoiceModel, facts: tuple[Fact, ...]) -> dict[str, Any]:
    metric = route_bound_accuracy(model, facts)
    observed = [row["observed"] for row in metric["rows"]]
    return {
        "correct": metric["correct"],
        "n": metric["n"],
        "accuracy": metric["accuracy"],
        "observed": observed,
        "observed_histogram": dict(sorted(Counter(observed).items())),
        "constant_output": len(set(observed)) == 1,
    }


def run(replication_root: Path, model: Path, output: Path) -> dict[str, Any]:
    root = replication_root.resolve()
    destination = output.resolve()
    if destination == Path(__file__).resolve().parents[2] or Path(__file__).resolve().parents[2] in destination.parents:
        raise ValueError("diagnostic output must remain outside the repository")
    if destination.exists():
        raise FileExistsError(f"refusing overwrite of immutable diagnostic root: {destination}")
    if not model.is_dir():
        raise FileNotFoundError(f"model path does not exist: {model}")

    cases = []
    for case_root in sorted(path for path in root.glob("seed-*") if path.is_dir()):
        structural = validate(case_root)
        manifest = json.loads((case_root / "tasks.json").read_text(encoding="utf8"))
        task_results = []
        for task in manifest:
            task_id = task["task_id"]
            adapter = case_root / "adapters" / "task_adapter_bank" / f"task-{task_id}"
            adapter_model = ChoiceModel(model, adapter)
            train = _summary(adapter_model, _facts(task, "train_facts"))
            test = _summary(adapter_model, _facts(task, "test_facts"))
            task_results.append(
                {
                    "task_id": task_id,
                    "route_key": task["task_token"],
                    "train": train,
                    "test": test,
                    "train_test_accuracy_equal": train["accuracy"] == test["accuracy"],
                }
            )
        target = next(item for item in task_results if item["task_id"] == 0)
        all_train_failed = all(item["train"]["accuracy"] < 1.0 for item in task_results)
        all_constant = all(item["train"]["constant_output"] for item in task_results)
        cases.append(
            {
                "case": case_root.name,
                "structural_validation": structural,
                "task_adapters": task_results,
                "all_task_adapters_failed_exact_train_acquisition": all_train_failed,
                "all_task_adapters_constant_output": all_constant,
                "target_adapter_failed_exact_train_acquisition": target["train"]["accuracy"] < 1.0,
                "target_adapter_constant_output": target["train"]["constant_output"],
                "diagnostic_classification": (
                    "TargetTaskNonAcquisitionConstantOutput"
                    if target["train"]["accuracy"] < 1.0 and target["train"]["constant_output"]
                    else "TargetTaskNonAcquisitionWithoutConstantOutput"
                ),
            }
        )

    if not cases:
        raise ValueError("no V27 case artifacts found")
    report = {
        "state_slice": STATE_SLICE,
        "replication_state_slice": REPLICATION_STATE_SLICE,
        "model": str(model.resolve()),
        "network_access": False,
        "training": False,
        "claim_ceiling": "LocalDevelopmentTaskRoutedAdapterBankFailureDiagnosis",
        "cases": cases,
        "all_cases_show_target_non_acquisition": all(
            case["target_adapter_failed_exact_train_acquisition"]
            for case in cases
        ),
        "all_cases_show_target_constant_output": all(
            case["target_adapter_constant_output"] for case in cases
        ),
        "scientific_promotion": False,
        "production_claim_eligible": False,
    }
    destination.mkdir(parents=True)
    (destination / "diagnosis.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf8"
    )
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--replication-root", type=Path, required=True)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(run(args.replication_root, args.model, args.output), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
