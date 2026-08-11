#!/usr/bin/env python3
"""V17 task-keyed readout feasibility preflight over a shared adapter."""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import sys
from dataclasses import asdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from experiments.continual_learning.compositional_calibration_benchmark import make_tasks  # noqa: E402
from experiments.continual_learning.model_benchmark import ChoiceModel  # noqa: E402
from experiments.continual_learning.residue_only_codebook_benchmark import residue_only_prompt_for  # noqa: E402


STATE_SLICE = "continual-learning-protocol-v17-task-keyed-readout-feasibility"
SOURCE_STATE_SLICE = "continual-learning-protocol-v14-repaired-objective-retention"
MODEL_DEFAULT = "/Users/shaanp/.lmstudio/models/mlx-community/Qwen2.5-0.5B-Instruct-4bit"
LABELS = ("A", "B", "C", "D")
PERMUTATIONS = tuple(itertools.permutations(LABELS))


def digest(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf8")


def raw_prediction(model: ChoiceModel, fact) -> str:
    outcome = model.answer(residue_only_prompt_for(fact))
    return max(LABELS, key=lambda label: outcome["logits"][label])


def score_readout(predictions: list[str], facts, permutation: tuple[str, ...]) -> dict:
    rows = []
    correct = 0
    for raw, fact in zip(predictions, facts):
        observed = permutation[LABELS.index(raw)]
        hit = observed == fact.label
        correct += int(hit)
        rows.append({"fact_id": fact.fact_id, "raw_prediction": raw, "observed": observed, "expected": fact.label, "correct": hit})
    return {"correct": correct, "n": len(facts), "accuracy": correct / len(facts) if facts else None, "rows": rows}


def fit_permutation(predictions: list[str], facts) -> dict:
    scored = [(score_readout(predictions, facts, permutation)["correct"], permutation) for permutation in PERMUTATIONS]
    best_correct, best_permutation = max(scored, key=lambda item: (item[0], tuple(reversed(item[1]))))
    return {"permutation": list(best_permutation), "train_accuracy": score_readout(predictions, facts, best_permutation), "candidate_count": len(PERMUTATIONS), "best_correct": best_correct}


def run(args: argparse.Namespace) -> dict:
    source = args.source.resolve()
    output = args.output.resolve()
    if output.exists():
        raise RuntimeError(f"refusing overwrite of immutable output: {output}")
    config = json.loads((source / "config.json").read_text())
    source_result = json.loads((source / "result.json").read_text())
    if config["model"] != MODEL_DEFAULT or source_result["state_slice"] != SOURCE_STATE_SLICE:
        raise ValueError("source contract drift")
    if config["seed"] != 20260810 or config["order"] != [0, 1, 2, 3] or config["iters"] != 160:
        raise ValueError("source fixed contract drift")
    tasks = make_tasks(20260810, 4)
    model = ChoiceModel(Path(config["model"]), source / "adapters" / "replay_lora" / "step-3")
    slots = []
    for task in tasks:
        train_raw = [raw_prediction(model, fact) for fact in task.train_facts]
        test_raw = [raw_prediction(model, fact) for fact in task.test_facts]
        fit = fit_permutation(train_raw, task.train_facts)
        permutation = tuple(fit["permutation"])
        slots.append(
            {
                "task_id": task.task_id,
                "route_key": task.task_token,
                "permutation": list(permutation),
                "candidate_count": fit["candidate_count"],
                "train_accuracy": fit["train_accuracy"],
                "heldout_accuracy": score_readout(test_raw, task.test_facts, permutation),
                "raw_train_accuracy": score_readout(train_raw, task.train_facts, LABELS),
                "raw_heldout_accuracy": score_readout(test_raw, task.test_facts, LABELS),
            }
        )
    target = next(slot for slot in slots if slot["task_id"] == 0)
    output.mkdir(parents=True)
    report = {
        "state_slice": STATE_SLICE,
        "source_state_slice": SOURCE_STATE_SLICE,
        "classification": "TaskKeyedReadoutFeasibilityNoBreakthroughClaim",
        "claim_ceiling": "LocalDevelopmentTaskKeyedReadoutFeasibility",
        "source_artifact": str(source),
        "source_result_sha256": hashlib.sha256((source / "result.json").read_bytes()).hexdigest(),
        "fixed_contract": {
            "model": config["model"],
            "seed": config["seed"],
            "order": config["order"],
            "task_count": config["task_count"],
            "update_budget": config["update_budget"],
            "optimizer": config["optimizer"],
            "iters": config["iters"],
            "prompt_contract": config["prompt_contract"],
        },
        "readout_architecture": {
            "type": "task_keyed_permutation_readout_v1",
            "slot_count": len(slots),
            "parameters_per_slot": 16,
            "total_discrete_table_entries": len(slots) * 16,
            "fit_source": "task_train_facts_only",
            "shared_adapter": "replay_lora/step-3",
        },
        "slots": slots,
        "target_task": {
            "task_id": target["task_id"],
            "raw_retention": target["raw_heldout_accuracy"],
            "readout_retention": target["heldout_accuracy"],
            "naive_reference": source_result["results"]["naive_sequential_lora"]["retention_after_interference"],
            "shared_replay_reference": source_result["results"]["replay_lora"]["retention_after_interference"],
        },
        "gates": {
            "route_slot_count": len(slots) == 4 and {slot["route_key"] for slot in slots} == {"T0", "T1", "T2", "T3"},
            "readout_training_fit_floor": all(slot["train_accuracy"]["accuracy"] >= 0.75 for slot in slots),
            "target_readout_above_shared_replay": target["heldout_accuracy"]["accuracy"] > target["raw_heldout_accuracy"]["accuracy"],
            "target_readout_above_naive": target["heldout_accuracy"]["accuracy"] > source_result["results"]["naive_sequential_lora"]["retention_after_interference"]["accuracy"],
        },
        "candidate_eligible": False,
        "breakthrough_claim_eligible": False,
        "decision": "ReadoutFeasibilityOnly",
    }
    report["candidate_eligible"] = all(report["gates"].values())
    report["report_sha256"] = digest(report)
    write_json(output / "report.json", report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=Path("/tmp/continual-learning-model-v14-qwen-seed20260810-order0123"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(run(args), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
