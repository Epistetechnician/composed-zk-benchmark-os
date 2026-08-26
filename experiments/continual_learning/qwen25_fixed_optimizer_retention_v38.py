#!/usr/bin/env python3
"""V38 Qwen2.5 fixed-optimizer retention preflight.

State slice: continual-learning-qwen25-fixed-optimizer-retention-v38.

V38 consumes only the durable, acquisition-eligible V37 task manifests and
task-routed adapters. It independently trains raw-text naive and bounded
replay sequential controls with the same fixed optimizer-seed policy, then
evaluates acquisition, post-interference retention, and recovery through the
fresh V34 readout seam. This is a local retention preflight, not an
independent model confirmation or production claim.
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
from experiments.continual_learning import qwen25_fixed_optimizer_acquisition_v37 as v37
from experiments.continual_learning import qwen25_raw_text_acquisition_v34 as v34
from experiments.continual_learning.compositional_model_benchmark import Fact, Task


STATE_SLICE = "continual-learning-qwen25-fixed-optimizer-retention-v38"
PROTOCOL = "v38-qwen25-fixed-optimizer-retention-preflight-v1"
MODEL_DEFAULT = v37.MODEL_DEFAULT
TASK_SEEDS = v37.TASK_SEEDS
FIXED_OPTIMIZER_SEED = v37.FIXED_OPTIMIZER_SEED
ORDER = v37.ORDER
ITERS = v37.ITERS
UPDATE_BUDGET = v37.UPDATE_BUDGET
REPLAY_CAPACITY = 24
RECOVERY_ITERS = 20
RECOVERY_SEED_OFFSET = 100
TARGET_TASK_ID = 0
TARGET_FLOOR = 0.75
CLAIM_CEILING = "LocalDevelopmentModelRetentionPreflight"
SOURCE_STATE_SLICE = v37.STATE_SLICE
SOURCE_ARTIFACT_ROOT = Path(
    "/Users/shaanp/.codex/research-artifacts/composed-zk-benchmark-os/"
    "continual-learning-qwen25-fixed-optimizer-acquisition-v37-20260824-r1"
)


def write_json(path: Path, value) -> None:
    if path.exists():
        raise RuntimeError(f"refusing overwrite of immutable artifact: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf8")


def case_name(task_seed: int) -> str:
    return f"task-seed-{task_seed}-order-0123-fixed-opt-{FIXED_OPTIMIZER_SEED}"


def tasks_from_json(value: list[dict]) -> tuple[Task, ...]:
    tasks = []
    for item in value:
        def make_fact(fact: dict) -> Fact:
            return Fact(
                task_id=fact["task_id"],
                task_token=fact["task_token"],
                fact_id=fact["fact_id"],
                left=fact["left"],
                right=fact["right"],
                residue=fact["residue"],
                label=fact["label"],
                split=fact["split"],
            )

        tasks.append(
            Task(
                task_id=item["task_id"],
                task_token=item["task_token"],
                mapping=tuple(item["mapping"]),
                train_facts=tuple(make_fact(fact) for fact in item["train_facts"]),
                test_facts=tuple(make_fact(fact) for fact in item["test_facts"]),
            )
        )
    return tuple(tasks)


def raw_text_rows(facts: list[Fact]) -> list[dict[str, str]]:
    rows = [v34.raw_text_training_example(fact) for fact in facts]
    return (rows * ((UPDATE_BUDGET + len(rows) - 1) // len(rows)))[:UPDATE_BUDGET]


def replay_facts(previous: list[Fact], current: list[Fact]) -> list[Fact]:
    prior = sorted(previous, key=lambda fact: (fact.task_id, fact.fact_id))
    return prior[:REPLAY_CAPACITY]


def replay_counts(facts: list[Fact]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for fact in facts:
        key = str(fact.task_id)
        counts[key] = counts.get(key, 0) + 1
    return dict(sorted(counts.items()))


def train_sequential(
    root: Path,
    model: Path,
    tasks: tuple[Task, ...],
    strategy: str,
    task_seed: int,
) -> tuple[list[Path], list[dict]]:
    if strategy not in {"naive_sequential", "replay_sequential"}:
        raise ValueError(f"unsupported V38 strategy: {strategy}")
    data_root = root / "data" / strategy
    adapter_root = root / "adapters" / strategy
    audit_root = root / "audit"
    data_root.mkdir(parents=True, exist_ok=False)
    adapter_root.mkdir(parents=True, exist_ok=False)
    audit_root.mkdir(parents=True, exist_ok=True)
    task_by_id = {task.task_id: task for task in tasks}
    previous_facts: list[Fact] = []
    previous_adapter: Path | None = None
    adapters: list[Path] = []
    audit: list[dict] = []
    for step, task_id in enumerate(ORDER):
        current = list(task_by_id[task_id].train_facts)
        replay = replay_facts(previous_facts, current) if strategy == "replay_sequential" else []
        selected = current + replay
        dataset = data_root / f"step-{step}"
        base.write_dataset(dataset, raw_text_rows(selected))
        adapter = adapter_root / f"step-{step}"
        training_seed = FIXED_OPTIMIZER_SEED + task_id
        command = v34.raw_text_training_command(
            model,
            dataset,
            adapter,
            training_seed,
            ITERS,
            previous_adapter / "adapters.safetensors" if previous_adapter else None,
        )
        environment = os.environ.copy()
        environment.update({"HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1"})
        completed = subprocess.run(command, env=environment, text=True, capture_output=True, check=False)
        (adapter_root / f"step-{step}.log").write_text(
            completed.stdout + "\n" + completed.stderr, encoding="utf8"
        )
        if completed.returncode != 0:
            raise RuntimeError(f"V38 {strategy} training failed at step {step}: {completed.returncode}")
        adapters.append(adapter)
        audit.append(
            {
                "step": step,
                "task_id": task_id,
                "route_key": task_by_id[task_id].task_token,
                "adapter_relative_path": str(adapter.relative_to(root)),
                "resumed_from": str(previous_adapter.relative_to(root)) if previous_adapter else None,
                "current_fact_ids": [fact.fact_id for fact in current],
                "replay_fact_ids": [fact.fact_id for fact in replay],
                "replay_counts_by_task": replay_counts(replay),
                "selected_fact_ids": [fact.fact_id for fact in selected],
                "dataset_row_count": UPDATE_BUDGET,
                "optimizer_seed_base": FIXED_OPTIMIZER_SEED,
                "training_seed": training_seed,
            }
        )
        previous_adapter = adapter
        previous_facts.extend(current)
    base.write_json(audit_root / f"{strategy}.json", audit)
    return adapters, audit


def train_recovery(root: Path, model: Path, tasks: tuple[Task, ...], strategy: str, final_adapter: Path) -> Path:
    data_root = root / "data" / strategy
    adapter_root = root / "adapters" / strategy
    dataset = data_root / "recovery"
    base.write_dataset(dataset, raw_text_rows(list(tasks[TARGET_TASK_ID].train_facts)))
    adapter = adapter_root / "recovery"
    recovery_seed = FIXED_OPTIMIZER_SEED + RECOVERY_SEED_OFFSET + (0 if strategy == "naive_sequential" else 1)
    command = v34.raw_text_training_command(
        model,
        dataset,
        adapter,
        recovery_seed,
        RECOVERY_ITERS,
        final_adapter / "adapters.safetensors",
    )
    environment = os.environ.copy()
    environment.update({"HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1"})
    completed = subprocess.run(command, env=environment, text=True, capture_output=True, check=False)
    (adapter_root / "recovery.log").write_text(completed.stdout + "\n" + completed.stderr, encoding="utf8")
    if completed.returncode != 0:
        raise RuntimeError(f"V38 {strategy} recovery failed: {completed.returncode}")
    return adapter


def metric(model: Path, tasks_path: Path, task_id: int, adapter: Path | None, split: str) -> dict:
    return v34._isolated_metric(model, tasks_path, task_id, adapter, split)


def run_case(output: Path, source_case: Path, model: Path, task_seed: int) -> dict:
    output = output.resolve()
    source_case = source_case.resolve()
    model = model.resolve()
    if output.exists():
        raise RuntimeError(f"refusing overwrite of immutable V38 case: {output}")
    if model != MODEL_DEFAULT.resolve():
        raise ValueError("V38 fixed Qwen2.5 model drift")
    if task_seed not in TASK_SEEDS:
        raise ValueError("V38 task seed is not preregistered")
    source_result = json.loads((source_case / "result.json").read_text(encoding="utf8"))
    if source_result["state_slice"] != SOURCE_STATE_SLICE or source_result["eligible"] is not True:
        raise ValueError("V38 requires an acquisition-eligible V37 source case")
    if any(source_result[key] is not False for key in ("retention_executed", "interference_executed")):
        raise ValueError("V38 source case retention boundary drift")
    tasks_json = json.loads((source_case / "tasks.json").read_text(encoding="utf8"))
    tasks = tasks_from_json(tasks_json)
    if len(tasks) != 4 or sorted(task.task_id for task in tasks) != list(range(4)):
        raise ValueError("V38 source task manifest drift")

    output.mkdir(parents=True)
    base.write_json(output / "tasks.json", tasks_json)
    config = {
        "state_slice": STATE_SLICE,
        "protocol": PROTOCOL,
        "model": str(model),
        "task_seed": task_seed,
        "source_state_slice": SOURCE_STATE_SLICE,
        "source_case": str(source_case),
        "source_result_sha256": source_result["result_sha256"],
        "optimizer_seed_base": FIXED_OPTIMIZER_SEED,
        "optimizer_seed_policy": "fixed_v36_first_declared_seed_plus_task_id_v1",
        "order": list(ORDER),
        "iters": ITERS,
        "recovery_iters": RECOVERY_ITERS,
        "update_budget": UPDATE_BUDGET,
        "replay_capacity": REPLAY_CAPACITY,
        "dataset_format": "raw_text_prompt_plus_completion_v1",
        "completion_masking": False,
        "memory_mechanisms": [
            "immutable_task_routed_adapter_bank_v1",
            "naive_sequential_raw_text_lora_v1",
            "bounded_replay_sequential_raw_text_lora_v1",
        ],
        "primary_metric": "replay_retention_minus_naive_retention",
        "target_task_id": TARGET_TASK_ID,
        "target_floor": TARGET_FLOOR,
        "network_access": False,
        "training": True,
        "retention_executed": True,
        "interference_executed": True,
        "provider_executed": False,
        "production_claim_eligible": False,
        "source_context_removed_for": ["acquisition", "retention_after_interference", "recovery_after_reacquisition"],
    }
    config["contract_sha256"] = base.digest(config)
    base.write_json(output / "config.json", config)

    bank_adapter = source_case / "adapters" / "task_adapter_bank" / "task-0"
    naive_adapters, naive_audit = train_sequential(output, model, tasks, "naive_sequential", task_seed)
    replay_adapters, replay_audit = train_sequential(output, model, tasks, "replay_sequential", task_seed)
    naive_recovery = train_recovery(output, model, tasks, "naive_sequential", naive_adapters[-1])
    replay_recovery = train_recovery(output, model, tasks, "replay_sequential", replay_adapters[-1])
    tasks_path = output / "tasks.json"

    no_update = {
        "acquisition": metric(model, tasks_path, TARGET_TASK_ID, None, "test"),
        "retention_after_interference": metric(model, tasks_path, TARGET_TASK_ID, None, "test"),
        "recovery_after_reacquisition": metric(model, tasks_path, TARGET_TASK_ID, None, "test"),
    }
    bank = {
        "acquisition": metric(model, tasks_path, TARGET_TASK_ID, bank_adapter, "test"),
        "retention_after_interference": metric(model, tasks_path, TARGET_TASK_ID, bank_adapter, "test"),
        "recovery_after_reacquisition": metric(model, tasks_path, TARGET_TASK_ID, bank_adapter, "test"),
    }

    def sequential_panel(adapters: list[Path], recovery: Path) -> dict:
        return {
            "acquisition": metric(model, tasks_path, TARGET_TASK_ID, adapters[0], "test"),
            "retention_after_interference": metric(model, tasks_path, TARGET_TASK_ID, adapters[-1], "test"),
            "recovery_after_reacquisition": metric(model, tasks_path, TARGET_TASK_ID, recovery, "test"),
        }

    naive = sequential_panel(naive_adapters, naive_recovery)
    replay = sequential_panel(replay_adapters, replay_recovery)
    results = {"no_update": no_update, "task_adapter_bank": bank, "naive_sequential": naive, "replay_sequential": replay}
    gates = {
        "source_acquisition_eligible": True,
        "bank_retention_floor": bank["retention_after_interference"]["accuracy"] >= TARGET_FLOOR,
        "naive_acquisition_floor": naive["acquisition"]["accuracy"] >= TARGET_FLOOR,
        "replay_acquisition_floor": replay["acquisition"]["accuracy"] >= TARGET_FLOOR,
        "replay_retention_above_naive": replay["retention_after_interference"]["accuracy"]
        > naive["retention_after_interference"]["accuracy"],
    }
    audits = {"naive_sequential": naive_audit, "replay_sequential": replay_audit}
    result = {
        "state_slice": STATE_SLICE,
        "protocol": PROTOCOL,
        "claim_ceiling": CLAIM_CEILING,
        "classification": "Qwen25FixedOptimizerRetentionPreflightNoProviderOrProductionClaim",
        "config": config,
        "tasks": tasks_json,
        "results": results,
        "gates": gates,
        "eligible": all(gates.values()),
        "source_result_sha256": source_result["result_sha256"],
        "audit_sha256": {strategy: base.digest(audit) for strategy, audit in audits.items()},
        "manifest_sha256": base.digest({"config": config, "tasks": tasks_json, "audits": audits}),
        "network_access": False,
        "training": True,
        "retention_executed": True,
        "interference_executed": True,
        "provider_executed": False,
        "production_claim_eligible": False,
    }
    result["result_sha256"] = base.digest(result)
    base.write_json(output / "result.json", result)
    return result


def validate_source_campaign(source_root: Path, model: Path, log_path: Path) -> dict:
    command = [
        sys.executable,
        str(Path(__file__).with_name("validate_qwen25_fixed_optimizer_campaign_v37.py")),
        str(source_root),
    ]
    completed = subprocess.run(command, text=True, capture_output=True, check=False)
    log_path.write_text(completed.stdout + "\n" + completed.stderr, encoding="utf8")
    if completed.returncode != 0:
        raise RuntimeError("V37 source campaign validation failed")
    return json.loads(completed.stdout.strip().splitlines()[-1])


def run_campaign(artifact_root: Path, model: Path, source_root: Path) -> dict:
    artifact_root = artifact_root.resolve()
    source_root = source_root.resolve()
    model = model.resolve()
    if artifact_root.exists():
        raise RuntimeError(f"refusing overwrite of immutable V38 campaign: {artifact_root}")
    if not artifact_root.is_absolute() or Path(__file__).resolve().parents[2] in artifact_root.parents:
        raise ValueError("V38 artifacts must remain outside the repository")
    if source_root != SOURCE_ARTIFACT_ROOT.resolve():
        raise ValueError("V38 source custody path drift")
    if model != MODEL_DEFAULT.resolve() or not model.is_dir():
        raise ValueError("V38 model binding is unavailable or drifted")
    artifact_root.mkdir(parents=True)
    source_validation = validate_source_campaign(source_root, model, artifact_root / "source.validator.log")
    if source_validation["campaign_eligible"] is not True:
        raise ValueError("V38 requires a campaign-wide eligible V37 source")
    contract = {
        "state_slice": STATE_SLICE,
        "protocol": PROTOCOL,
        "model": str(model),
        "source_state_slice": SOURCE_STATE_SLICE,
        "source_artifact_root": str(source_root),
        "task_seeds": list(TASK_SEEDS),
        "optimizer_seed_base": FIXED_OPTIMIZER_SEED,
        "optimizer_seed_policy": "fixed_v36_first_declared_seed_plus_task_id_v1",
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
    environment.update({"HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1", "PYTHONDONTWRITEBYTECODE": "1"})
    for task_seed in TASK_SEEDS:
        name = case_name(task_seed)
        case_root = artifact_root / name
        source_case = source_root / name
        runner = subprocess.run(
            [sys.executable, str(Path(__file__).resolve()), "--case-output", str(case_root), "--source-case", str(source_case), "--model", str(model), "--task-seed", str(task_seed)],
            env=environment,
            text=True,
            capture_output=True,
            check=False,
        )
        (artifact_root / f"{name}.runner.log").write_text(runner.stdout + "\n" + runner.stderr, encoding="utf8")
        if runner.returncode != 0:
            records.append({"task_seed": task_seed, "status": "runner_failed", "valid": False})
            break
        validator = subprocess.run(
            [sys.executable, str(Path(__file__).with_name("validate_qwen25_fixed_optimizer_retention_v38.py")), str(case_root), "--source-case", str(source_case), "--model", str(model), "--expected-task-seed", str(task_seed)],
            env=environment,
            text=True,
            capture_output=True,
            check=False,
        )
        (artifact_root / f"{name}.validator.log").write_text(validator.stdout + "\n" + validator.stderr, encoding="utf8")
        if validator.returncode != 0:
            records.append({"task_seed": task_seed, "status": "validator_failed", "valid": False})
            break
        validation = json.loads(validator.stdout.strip().splitlines()[-1])
        result = json.loads((case_root / "result.json").read_text(encoding="utf8"))
        records.append({"task_seed": task_seed, "status": "validated", "valid": validation["valid"], "eligible": validation["eligible"], "gates": validation["gates"], "result_sha256": result["result_sha256"]})
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
            raise ValueError("V38 case mode requires task-seed and source-case")
        result = run_case(args.case_output, args.source_case, args.model, args.task_seed)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if result["eligible"] else 1
    if args.artifact_root is None:
        raise ValueError("V38 campaign mode requires artifact-root")
    result = run_campaign(args.artifact_root, args.model, args.source_root)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["campaign_eligible"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
