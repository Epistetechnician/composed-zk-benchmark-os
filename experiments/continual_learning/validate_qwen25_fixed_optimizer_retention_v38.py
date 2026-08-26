#!/usr/bin/env python3
"""Independent validator for one V38 retention case."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from experiments.continual_learning import factorized_solvability_benchmark as base
from experiments.continual_learning.qwen25_fixed_optimizer_retention_v38 import (
    CLAIM_CEILING,
    FIXED_OPTIMIZER_SEED,
    ITERS,
    ORDER,
    PROTOCOL,
    REPLAY_CAPACITY,
    RECOVERY_ITERS,
    SOURCE_STATE_SLICE,
    STATE_SLICE,
    TARGET_FLOOR,
    UPDATE_BUDGET,
)


def load(path: Path):
    return json.loads(path.read_text(encoding="utf8"))


def metric_valid(metric: dict) -> bool:
    rows = metric["rows"]
    return (
        metric["n"] == len(rows)
        and metric["n"] == 8
        and metric["correct"] == sum(row["correct"] is True for row in rows)
        and metric["accuracy"] == metric["correct"] / metric["n"]
    )


def validate(case_root: Path, source_case: Path, model: Path, expected_task_seed: int) -> dict:
    config = load(case_root / "config.json")
    result = load(case_root / "result.json")
    tasks = load(case_root / "tasks.json")
    source_result = load(source_case / "result.json")
    source_tasks = load(source_case / "tasks.json")
    if config["state_slice"] != STATE_SLICE or result["state_slice"] != STATE_SLICE:
        raise ValueError("V38 state slice drift")
    if config["protocol"] != PROTOCOL or result["protocol"] != PROTOCOL:
        raise ValueError("V38 protocol drift")
    if config["task_seed"] != expected_task_seed or result["config"]["task_seed"] != expected_task_seed:
        raise ValueError("V38 task seed drift")
    if config["model"] != str(model.resolve()):
        raise ValueError("V38 model drift")
    if config["source_state_slice"] != SOURCE_STATE_SLICE:
        raise ValueError("V38 source state slice drift")
    if tasks != source_tasks:
        raise ValueError("V38 task manifest changed from V37 source")
    if source_result["state_slice"] != SOURCE_STATE_SLICE or source_result["eligible"] is not True:
        raise ValueError("V38 source is not acquisition eligible")
    if source_result["result_sha256"] != config["source_result_sha256"]:
        raise ValueError("V38 source result binding drift")
    if config["optimizer_seed_base"] != FIXED_OPTIMIZER_SEED:
        raise ValueError("V38 optimizer seed drift")
    if config["order"] != list(ORDER) or config["iters"] != ITERS or config["recovery_iters"] != RECOVERY_ITERS:
        raise ValueError("V38 schedule drift")
    if config["update_budget"] != UPDATE_BUDGET or config["replay_capacity"] != REPLAY_CAPACITY:
        raise ValueError("V38 update budget drift")
    for key in ("network_access", "provider_executed", "production_claim_eligible"):
        if result[key] is not False:
            raise ValueError(f"V38 boundary drift: {key}")
    if result["retention_executed"] is not True or result["interference_executed"] is not True:
        raise ValueError("V38 retention execution marker missing")

    audits = {}
    for strategy in ("naive_sequential", "replay_sequential"):
        audit = load(case_root / "audit" / f"{strategy}.json")
        if len(audit) != 4:
            raise ValueError(f"V38 {strategy} audit length drift")
        previous: list[tuple[int, str]] = []
        for step, item in enumerate(audit):
            expected_task = ORDER[step]
            if item["step"] != step or item["task_id"] != expected_task:
                raise ValueError(f"V38 {strategy} order drift")
            if item["optimizer_seed_base"] != FIXED_OPTIMIZER_SEED:
                raise ValueError(f"V38 {strategy} optimizer seed drift")
            if item["training_seed"] != FIXED_OPTIMIZER_SEED + expected_task:
                raise ValueError(f"V38 {strategy} training seed drift")
            if item["dataset_row_count"] != UPDATE_BUDGET:
                raise ValueError(f"V38 {strategy} update row drift")
            if strategy == "naive_sequential" and item["replay_fact_ids"]:
                raise ValueError("V38 naive strategy contains replay")
            if strategy == "replay_sequential":
                expected_replay = sorted(previous)[:REPLAY_CAPACITY]
                if item["replay_fact_ids"] != [fact_id for _, fact_id in expected_replay]:
                    raise ValueError("V38 replay membership drift")
            previous.extend((expected_task, fact_id) for fact_id in item["current_fact_ids"])
        audits[strategy] = audit

    results = result["results"]
    for strategy in ("no_update", "task_adapter_bank", "naive_sequential", "replay_sequential"):
        for endpoint in ("acquisition", "retention_after_interference", "recovery_after_reacquisition"):
            if not metric_valid(results[strategy][endpoint]):
                raise ValueError(f"V38 metric shape drift: {strategy}/{endpoint}")

    gates = {
        "source_acquisition_eligible": True,
        "bank_retention_floor": results["task_adapter_bank"]["retention_after_interference"]["accuracy"] >= TARGET_FLOOR,
        "naive_acquisition_floor": results["naive_sequential"]["acquisition"]["accuracy"] >= TARGET_FLOOR,
        "replay_acquisition_floor": results["replay_sequential"]["acquisition"]["accuracy"] >= TARGET_FLOOR,
        "replay_retention_above_naive": results["replay_sequential"]["retention_after_interference"]["accuracy"]
        > results["naive_sequential"]["retention_after_interference"]["accuracy"],
    }
    if result["gates"] != gates or result["eligible"] != all(gates.values()):
        raise ValueError("V38 eligibility gate drift")
    if result["claim_ceiling"] != CLAIM_CEILING:
        raise ValueError("V38 claim ceiling drift")
    expected_audits = {strategy: base.digest(audit) for strategy, audit in audits.items()}
    if result["audit_sha256"] != expected_audits:
        raise ValueError("V38 audit digest drift")
    expected_manifest = base.digest({"config": config, "tasks": tasks, "audits": audits})
    if result["manifest_sha256"] != expected_manifest:
        raise ValueError("V38 manifest digest drift")
    expected_result = base.digest({key: value for key, value in result.items() if key != "result_sha256"})
    if result["result_sha256"] != expected_result:
        raise ValueError("V38 result digest drift")
    return {
        "valid": True,
        "eligible": result["eligible"],
        "gates": gates,
        "state_slice": STATE_SLICE,
        "protocol": PROTOCOL,
        "claim_ceiling": CLAIM_CEILING,
        "task_seed": expected_task_seed,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("case_root", type=Path)
    parser.add_argument("--source-case", type=Path, required=True)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--expected-task-seed", type=int, required=True)
    args = parser.parse_args()
    print(json.dumps(validate(args.case_root.resolve(), args.source_case.resolve(), args.model, args.expected_task_seed), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
