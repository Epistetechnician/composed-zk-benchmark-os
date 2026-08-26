#!/usr/bin/env python3
"""V40 Qwen2.5 fresh-task retention campaign.

State slice: continual-learning-qwen25-fresh-fixed-optimizer-retention-v40.

V40 consumes only the durable, campaign-eligible V40 acquisition source and
re-executes the V38 retention panel for the three fresh task seeds. It keeps
the fixed optimizer, task order, replay capacity, recovery budget, and
primary replay-minus-naive metric unchanged.
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
from experiments.continual_learning.qwen25_fresh_fixed_optimizer_acquisition_v40 import (
    MODEL_DEFAULT,
    TASK_SEEDS,
)


STATE_SLICE = "continual-learning-qwen25-fresh-fixed-optimizer-retention-v40"
PROTOCOL = "v40-qwen25-fresh-fixed-optimizer-retention-v1"
CLAIM_CEILING = "LocalDevelopmentFreshModelRetentionPreflight"
SOURCE_STATE_SLICE = "continual-learning-qwen25-fresh-fixed-optimizer-acquisition-v40"
SOURCE_ARTIFACT_ROOT = Path(
    "/Users/shaanp/.codex/research-artifacts/composed-zk-benchmark-os/"
    "continual-learning-qwen25-fresh-fixed-optimizer-acquisition-v40-20260824-r1"
)
FIXED_OPTIMIZER_SEED = v38.FIXED_OPTIMIZER_SEED
ORDER = v38.ORDER
ITERS = v38.ITERS
UPDATE_BUDGET = v38.UPDATE_BUDGET
REPLAY_CAPACITY = v38.REPLAY_CAPACITY
RECOVERY_ITERS = v38.RECOVERY_ITERS


def write_json(path: Path, value) -> None:
    if path.exists():
        raise RuntimeError(f"refusing overwrite of immutable artifact: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf8")


def case_name(task_seed: int) -> str:
    return f"task-seed-{task_seed}-order-0123-fixed-opt-{FIXED_OPTIMIZER_SEED}"


def run_case(output: Path, source_case: Path, model: Path, task_seed: int) -> dict:
    output = output.resolve()
    source_case = source_case.resolve()
    model = model.resolve()
    if task_seed not in TASK_SEEDS:
        raise ValueError("V40 retention task seed is not in the frozen fresh-task set")
    if model != MODEL_DEFAULT.resolve():
        raise ValueError("V40 retention fixed Qwen2.5 model drift")

    originals = {
        "STATE_SLICE": v38.STATE_SLICE,
        "PROTOCOL": v38.PROTOCOL,
        "MODEL_DEFAULT": v38.MODEL_DEFAULT,
        "TASK_SEEDS": v38.TASK_SEEDS,
        "SOURCE_STATE_SLICE": v38.SOURCE_STATE_SLICE,
        "CLAIM_CEILING": v38.CLAIM_CEILING,
    }
    v38.STATE_SLICE = STATE_SLICE
    v38.PROTOCOL = PROTOCOL
    v38.MODEL_DEFAULT = MODEL_DEFAULT
    v38.TASK_SEEDS = TASK_SEEDS
    v38.SOURCE_STATE_SLICE = SOURCE_STATE_SLICE
    v38.CLAIM_CEILING = CLAIM_CEILING
    try:
        result = v38.run_case(output, source_case, model, task_seed)
    finally:
        for key, value in originals.items():
            setattr(v38, key, value)

    config = result["config"]
    config.update(
        {
            "state_slice": STATE_SLICE,
            "protocol": PROTOCOL,
            "model": str(model),
            "task_seed": task_seed,
            "source_state_slice": SOURCE_STATE_SLICE,
            "optimizer_seed_base": FIXED_OPTIMIZER_SEED,
            "independence_status": "fresh_task_seed_retention_after_eligible_acquisition",
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
            "classification": "Qwen25FreshFixedOptimizerRetentionPreflightNoProviderOrProductionClaim",
            "config": config,
            "independence_status": "fresh_task_seed_retention_after_eligible_acquisition",
        }
    )
    result["manifest_sha256"] = base.digest(
        {
            "config": config,
            "tasks": result["tasks"],
            "audits": {
                strategy: json.loads((output / "audit" / f"{strategy}.json").read_text(encoding="utf8"))
                for strategy in ("naive_sequential", "replay_sequential")
            },
        }
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
    source_root = source_root.resolve()
    model = model.resolve()
    if artifact_root.exists():
        raise RuntimeError(f"refusing overwrite of immutable V40 retention campaign: {artifact_root}")
    if not artifact_root.is_absolute() or Path(__file__).resolve().parents[2] in artifact_root.parents:
        raise ValueError("V40 retention artifacts must remain outside the repository")
    if source_root != SOURCE_ARTIFACT_ROOT.resolve():
        raise ValueError("V40 acquisition source custody path drift")
    if model != MODEL_DEFAULT.resolve() or not model.is_dir():
        raise ValueError("V40 retention model binding is unavailable or drifted")

    artifact_root.mkdir(parents=True)
    source_validation = validate_source_campaign(source_root, artifact_root / "source.validator.log")
    if source_validation["campaign_eligible"] is not True:
        raise ValueError("V40 retention requires a campaign-wide eligible acquisition source")
    contract = {
        "state_slice": STATE_SLICE,
        "protocol": PROTOCOL,
        "model": str(model),
        "source_state_slice": SOURCE_STATE_SLICE,
        "source_artifact_root": str(source_root),
        "task_seeds": list(TASK_SEEDS),
        "optimizer_seed_base": FIXED_OPTIMIZER_SEED,
        "order": list(ORDER),
        "iters": ITERS,
        "recovery_iters": RECOVERY_ITERS,
        "update_budget": UPDATE_BUDGET,
        "replay_capacity": REPLAY_CAPACITY,
        "primary_metric": "replay_retention_minus_naive_retention",
        "training": True,
        "retention_executed": True,
        "interference_executed": True,
        "provider_executed": False,
        "production_claim_eligible": False,
        "network_access": False,
        "source_campaign_validation": source_validation,
    }
    contract["contract_sha256"] = base.digest(contract)
    write_json(artifact_root / "campaign_contract.json", contract)
    records = []
    environment = os.environ.copy()
    environment.update(
        {"HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1", "PYTHONDONTWRITEBYTECODE": "1"}
    )
    for task_seed in TASK_SEEDS:
        name = case_name(task_seed)
        case_root = artifact_root / name
        source_case = source_root / name
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
            records.append({"task_seed": task_seed, "status": "runner_failed", "valid": False})
            break
        validator = subprocess.run(
            [
                sys.executable,
                str(Path(__file__).with_name("validate_qwen25_fresh_fixed_optimizer_retention_v40.py")),
                str(case_root),
                "--source-case",
                str(source_case),
                "--model",
                str(model),
                "--expected-task-seed",
                str(task_seed),
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
            records.append({"task_seed": task_seed, "status": "validator_failed", "valid": False})
            break
        validation = json.loads(validator.stdout.strip().splitlines()[-1])
        result = json.loads((case_root / "result.json").read_text(encoding="utf8"))
        records.append(
            {
                "task_seed": task_seed,
                "status": "validated",
                "valid": validation["valid"],
                "eligible": validation["eligible"],
                "gates": validation["gates"],
                "result_sha256": result["result_sha256"],
            }
        )
    report = {
        "state_slice": STATE_SLICE,
        "protocol": PROTOCOL,
        "claim_ceiling": CLAIM_CEILING,
        "model": str(model),
        "source_state_slice": SOURCE_STATE_SLICE,
        "task_seeds": list(TASK_SEEDS),
        "optimizer_seed_base": FIXED_OPTIMIZER_SEED,
        "case_count": len(records),
        "expected_case_count": len(TASK_SEEDS),
        "cases": records,
        "all_cases_valid": len(records) == len(TASK_SEEDS) and all(row["valid"] for row in records),
        "all_cases_eligible": len(records) == len(TASK_SEEDS) and all(row.get("eligible") is True for row in records),
        "campaign_eligible": len(records) == len(TASK_SEEDS) and all(row.get("eligible") is True for row in records),
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
    args = parser.parse_args()
    if args.case_output is not None:
        if args.task_seed is None or args.source_case is None:
            raise ValueError("V40 retention case mode requires task-seed and source-case")
        result = run_case(args.case_output, args.source_case, args.model, args.task_seed)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if result["eligible"] else 1
    if args.artifact_root is None:
        raise ValueError("V40 retention campaign mode requires artifact-root")
    result = run_campaign(args.artifact_root, args.model, args.source_root)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["campaign_eligible"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
