#!/usr/bin/env python3
"""V41 fresh-seed task-order retention replication.

State slice: continual-learning-qwen25-fresh-fixed-optimizer-order-retention-v41.

V41 consumes the durable V40 acquisition source and crosses its three fresh
task seeds with three frozen noncanonical task orders. The Qwen2.5 model,
optimizer, update budget, replay capacity, recovery budget, and retention
gates remain unchanged.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from experiments.continual_learning import factorized_solvability_benchmark as base
from experiments.continual_learning import qwen25_fixed_optimizer_retention_v38 as v38
from experiments.continual_learning import qwen25_fresh_fixed_optimizer_retention_v40 as v40
from experiments.continual_learning.qwen25_fresh_fixed_optimizer_acquisition_v40 import (
    MODEL_DEFAULT,
    TASK_SEEDS,
)


STATE_SLICE = "continual-learning-qwen25-fresh-fixed-optimizer-order-retention-v41"
PROTOCOL = "v41-qwen25-fresh-fixed-optimizer-order-retention-v1"
CLAIM_CEILING = "LocalDevelopmentFreshTaskOrderRetentionReplication"
SOURCE_STATE_SLICE = v40.SOURCE_STATE_SLICE
SOURCE_ARTIFACT_ROOT = v40.SOURCE_ARTIFACT_ROOT
FIXED_OPTIMIZER_SEED = v40.FIXED_OPTIMIZER_SEED
ORDERS = ((0, 2, 1, 3), (0, 3, 1, 2), (0, 1, 3, 2))


def order_code(order: tuple[int, ...]) -> str:
    return "".join(str(task_id) for task_id in order)


def case_name(task_seed: int, order: tuple[int, ...]) -> str:
    return f"task-seed-{task_seed}-order-{order_code(order)}-fixed-opt-{FIXED_OPTIMIZER_SEED}"


def write_json(path: Path, value) -> None:
    if path.exists():
        raise RuntimeError(f"refusing overwrite of immutable artifact: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf8")


def run_case(output: Path, source_case: Path, model: Path, task_seed: int, order: tuple[int, ...]) -> dict:
    output = output.resolve()
    source_case = source_case.resolve()
    model = model.resolve()
    order = tuple(order)
    if task_seed not in TASK_SEEDS:
        raise ValueError("V41 task seed is not in the frozen V40 source set")
    if order not in ORDERS:
        raise ValueError("V41 order is not in the frozen noncanonical set")
    if model != MODEL_DEFAULT.resolve():
        raise ValueError("V41 fixed Qwen2.5 model drift")

    original_v40_order = v40.ORDER
    original_v38_order = v38.ORDER
    v40.ORDER = order
    v38.ORDER = order
    try:
        result = v40.run_case(output, source_case, model, task_seed)
    finally:
        v40.ORDER = original_v40_order
        v38.ORDER = original_v38_order

    config = result["config"]
    config.update(
        {
            "state_slice": STATE_SLICE,
            "protocol": PROTOCOL,
            "task_seed": task_seed,
            "replication_order": list(order),
            "source_state_slice": SOURCE_STATE_SLICE,
            "independence_status": "fresh_task_order_retention_after_eligible_acquisition",
        }
    )
    config["contract_sha256"] = base.digest(
        {key: value for key, value in config.items() if key != "contract_sha256"}
    )
    result.update(
        {
            "state_slice": STATE_SLICE,
            "protocol": PROTOCOL,
            "claim_ceiling": CLAIM_CEILING,
            "classification": "Qwen25FreshTaskOrderRetentionReplicationNoSecondModelClaim",
            "config": config,
            "replication_order": list(order),
            "independence_status": "fresh_task_order_retention_after_eligible_acquisition",
        }
    )
    audits = {
        strategy: json.loads((output / "audit" / f"{strategy}.json").read_text(encoding="utf8"))
        for strategy in ("naive_sequential", "replay_sequential")
    }
    result["manifest_sha256"] = base.digest(
        {"config": config, "tasks": result["tasks"], "audits": audits}
    )
    result["result_sha256"] = base.digest(
        {key: value for key, value in result.items() if key != "result_sha256"}
    )
    (output / "config.json").write_text(json.dumps(config, indent=2, sort_keys=True) + "\n", encoding="utf8")
    (output / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf8")
    return result


def validate_source_campaign(source_root: Path, log_path: Path) -> dict:
    command = [
        sys.executable,
        str(Path(__file__).with_name("validate_qwen25_fresh_fixed_optimizer_campaign_v40.py")),
        str(source_root),
    ]
    completed = subprocess.run(command, text=True, capture_output=True, check=False)
    log_path.write_text(completed.stdout + "\n" + completed.stderr, encoding="utf8")
    if completed.returncode != 0:
        raise RuntimeError("V40 acquisition source campaign validation failed")
    return json.loads(completed.stdout.strip().splitlines()[-1])


def run_campaign(artifact_root: Path, model: Path, source_root: Path) -> dict:
    artifact_root = artifact_root.resolve()
    model = model.resolve()
    source_root = source_root.resolve()
    if artifact_root.exists():
        raise RuntimeError(f"refusing overwrite of immutable V41 campaign: {artifact_root}")
    if not artifact_root.is_absolute() or Path(__file__).resolve().parents[2] in artifact_root.parents:
        raise ValueError("V41 artifacts must remain outside the repository")
    if source_root != SOURCE_ARTIFACT_ROOT.resolve():
        raise ValueError("V41 acquisition source custody path drift")
    if model != MODEL_DEFAULT.resolve() or not model.is_dir():
        raise ValueError("V41 model binding is unavailable or drifted")

    artifact_root.mkdir(parents=True)
    source_validation = validate_source_campaign(source_root, artifact_root / "source.validator.log")
    if source_validation["campaign_eligible"] is not True:
        raise ValueError("V41 requires a campaign-wide eligible V40 acquisition source")
    contract = {
        "state_slice": STATE_SLICE,
        "protocol": PROTOCOL,
        "model": str(model),
        "source_state_slice": SOURCE_STATE_SLICE,
        "source_artifact_root": str(source_root),
        "task_seeds": list(TASK_SEEDS),
        "orders": [list(order) for order in ORDERS],
        "optimizer_seed_base": FIXED_OPTIMIZER_SEED,
        "primary_metric": "replay_retention_minus_naive_retention",
        "source_campaign_validation": source_validation,
        "network_access": False,
        "training": True,
        "retention_executed": True,
        "interference_executed": True,
        "provider_executed": False,
        "production_claim_eligible": False,
    }
    contract["contract_sha256"] = base.digest(contract)
    write_json(artifact_root / "campaign_contract.json", contract)
    records = []
    environment = os.environ.copy()
    environment.update(
        {"HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1", "PYTHONDONTWRITEBYTECODE": "1"}
    )
    for task_seed in TASK_SEEDS:
        for order in ORDERS:
            name = case_name(task_seed, order)
            case_root = artifact_root / name
            source_case = source_root / f"task-seed-{task_seed}-order-0123-fixed-opt-{FIXED_OPTIMIZER_SEED}"
            runner = subprocess.run(
                [
                    sys.executable,
                    str(Path(__file__).resolve()),
                    "--case-output",
                    str(case_root),
                    "--source-case",
                    str(source_case),
                    "--model",
                    str(model),
                    "--task-seed",
                    str(task_seed),
                    "--order",
                    order_code(order),
                ],
                env=environment,
                text=True,
                capture_output=True,
                check=False,
            )
            (artifact_root / f"{name}.runner.log").write_text(
                runner.stdout + "\n" + runner.stderr, encoding="utf8"
            )
            if runner.returncode != 0:
                records.append({"task_seed": task_seed, "order": order_code(order), "status": "runner_failed", "valid": False})
                break
            validator = subprocess.run(
                [
                    sys.executable,
                    str(Path(__file__).with_name("validate_qwen25_fresh_fixed_optimizer_order_retention_v41.py")),
                    str(case_root),
                    "--source-case",
                    str(source_case),
                    "--model",
                    str(model),
                    "--expected-task-seed",
                    str(task_seed),
                    "--expected-order",
                    order_code(order),
                ],
                env=environment,
                text=True,
                capture_output=True,
                check=False,
            )
            (artifact_root / f"{name}.validator.log").write_text(
                validator.stdout + "\n" + validator.stderr, encoding="utf8"
            )
            if validator.returncode != 0:
                records.append({"task_seed": task_seed, "order": order_code(order), "status": "validator_failed", "valid": False})
                break
            validation = json.loads(validator.stdout.strip().splitlines()[-1])
            result = json.loads((case_root / "result.json").read_text(encoding="utf8"))
            records.append(
                {
                    "task_seed": task_seed,
                    "order": order_code(order),
                    "status": "validated",
                    "valid": validation["valid"],
                    "eligible": validation["eligible"],
                    "gates": validation["gates"],
                    "result_sha256": result["result_sha256"],
                }
            )
        if records and records[-1]["valid"] is not True:
            break
    expected_count = len(TASK_SEEDS) * len(ORDERS)
    report = {
        "state_slice": STATE_SLICE,
        "protocol": PROTOCOL,
        "claim_ceiling": CLAIM_CEILING,
        "model": str(model),
        "source_state_slice": SOURCE_STATE_SLICE,
        "task_seeds": list(TASK_SEEDS),
        "orders": [order_code(order) for order in ORDERS],
        "optimizer_seed_base": FIXED_OPTIMIZER_SEED,
        "case_count": len(records),
        "expected_case_count": expected_count,
        "cases": records,
        "all_cases_valid": len(records) == expected_count and all(row["valid"] for row in records),
        "all_cases_eligible": len(records) == expected_count and all(row.get("eligible") is True for row in records),
        "campaign_eligible": len(records) == expected_count and all(row.get("eligible") is True for row in records),
        "network_access": False,
        "training": True,
        "retention_executed": True,
        "interference_executed": True,
        "provider_executed": False,
        "production_claim_eligible": False,
    }
    report["report_sha256"] = base.digest(report)
    write_json(artifact_root / "campaign_report.json", report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-root", type=Path)
    parser.add_argument("--case-output", type=Path)
    parser.add_argument("--source-case", type=Path)
    parser.add_argument("--source-root", type=Path, default=SOURCE_ARTIFACT_ROOT)
    parser.add_argument("--model", type=Path, default=MODEL_DEFAULT)
    parser.add_argument("--task-seed", type=int)
    parser.add_argument("--order")
    args = parser.parse_args()
    if args.case_output is not None:
        if args.task_seed is None or args.source_case is None or args.order is None:
            raise ValueError("V41 case mode requires task-seed, source-case, and order")
        order = tuple(int(value) for value in args.order)
        result = run_case(args.case_output, args.source_case, args.model, args.task_seed, order)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if result["eligible"] else 1
    if args.artifact_root is None:
        raise ValueError("V41 campaign mode requires artifact-root")
    result = run_campaign(args.artifact_root, args.model, args.source_root)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["campaign_eligible"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
