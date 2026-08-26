#!/usr/bin/env python3
"""V44 second-model replication of the Qwen2.5 V40/V41 contract.

State slice family: continual-learning-qwen25-second-model-replication-v44.

The scientific mechanism is frozen to V40/V41. Only the model identity and
fresh task/order units change. All model work is offline and each case runs in
its own subprocess. Retention and order phases are fail-closed on acquisition.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from experiments.continual_learning import qwen25_fresh_fixed_optimizer_acquisition_v40 as acquisition
from experiments.continual_learning import qwen25_fresh_fixed_optimizer_order_retention_v41 as order_retention
from experiments.continual_learning import qwen25_fresh_fixed_optimizer_retention_v40 as retention
from experiments.continual_learning.runtime_seam import digest, sha256_file, write_json


STATE_SLICE = "continual-learning-qwen25-second-model-replication-v44"
PROTOCOL = "v44-qwen25-second-model-replication-v1"
MODEL_DEFAULT = Path("/Users/shaanp/.lmstudio/models/mlx-community/Llama-3.2-1B-Instruct-4bit")
PARENT_MODEL = Path("/Users/shaanp/.lmstudio/models/mlx-community/Qwen2.5-0.5B-Instruct-4bit")
TASK_SEEDS = (20260862, 20260863, 20260864)
ORDERS = ((1, 0, 2, 3), (1, 2, 0, 3), (1, 3, 0, 2))
FIXED_OPTIMIZER_SEED = 20260856
ITERS = 160
UPDATE_BUDGET = 32
REPLAY_CAPACITY = 24
RECOVERY_ITERS = 20

ACQUISITION_STATE_SLICE = "continual-learning-qwen25-second-model-acquisition-v44"
ACQUISITION_PROTOCOL = "v44-qwen25-second-model-acquisition-v1"
ACQUISITION_CLAIM_CEILING = "LocalDevelopmentSecondModelAcquisitionReplication"
RETENTION_STATE_SLICE = "continual-learning-qwen25-second-model-retention-v44"
RETENTION_PROTOCOL = "v44-qwen25-second-model-retention-v1"
RETENTION_CLAIM_CEILING = "LocalDevelopmentSecondModelRetentionReplication"
ORDER_STATE_SLICE = "continual-learning-qwen25-second-model-order-retention-v44"
ORDER_PROTOCOL = "v44-qwen25-second-model-order-retention-v1"
ORDER_CLAIM_CEILING = "LocalDevelopmentSecondModelOrderRetentionReplication"
CLAIM_CEILING = "LocalDevelopmentSecondModelReplication"

PARENT_DOSSIER_ROOT = Path(
    "/Users/shaanp/.codex/research-artifacts/composed-zk-benchmark-os/"
    "continual-learning-qwen25-candidate-dossier-v43-20260825-r1"
)
PARENT_DOSSIER_FILE_SHA256 = "10eb4933f8b64efcb4a867bf3d8b35991fcb7f9bbc50fd8e3e014f9ffeeb43d4"
PARENT_DOSSIER_SHA256 = "331f7fca2ce43549fc569158b137361c1df89c7d42fb83405a2d08a022a5ab93"


def _ensure_external_new_root(root: Path) -> None:
    root = root.resolve()
    if root == REPO_ROOT or REPO_ROOT in root.parents:
        raise ValueError("V44 artifacts must remain outside the repository")
    if root.exists():
        raise FileExistsError(f"refusing overwrite of immutable V44 output: {root}")


@contextmanager
def _patched(module: Any, values: dict[str, Any]) -> Iterator[None]:
    originals = {key: getattr(module, key) for key in values}
    for key, value in values.items():
        setattr(module, key, value)
    try:
        yield
    finally:
        for key, value in originals.items():
            setattr(module, key, value)


def _finalize_case(
    output: Path,
    result: dict[str, Any],
    *,
    phase: str,
    state_slice: str,
    protocol: str,
    claim_ceiling: str,
    classification: str,
    model: Path,
    task_seed: int,
    replication_order: tuple[int, ...] | None = None,
) -> dict[str, Any]:
    config = result["config"]
    config.update(
        {
            "state_slice": state_slice,
            "protocol": protocol,
            "model": str(model),
            "task_seed": task_seed,
            "optimizer_seed_base": FIXED_OPTIMIZER_SEED,
            "iters": ITERS,
            "update_budget": UPDATE_BUDGET,
            "second_model_relation": "qwen25_candidate_to_llama_v44",
            "parent_candidate_model": str(PARENT_MODEL),
            "parent_candidate_dossier_sha256": PARENT_DOSSIER_SHA256,
            "parent_candidate_dossier_file_sha256": PARENT_DOSSIER_FILE_SHA256,
            "independence_status": "fresh_second_model_task_and_order_units_under_frozen_v40_v41_policy",
        }
    )
    if replication_order is not None:
        config["replication_order"] = list(replication_order)
    config["contract_sha256"] = digest(
        {key: value for key, value in config.items() if key != "contract_sha256"}
    )
    result.update(
        {
            "state_slice": state_slice,
            "protocol": protocol,
            "claim_ceiling": claim_ceiling,
            "classification": classification,
            "config": config,
            "model": str(model),
            "task_seed": task_seed,
            "second_model_relation": "qwen25_candidate_to_llama_v44",
            "parent_candidate_dossier_sha256": PARENT_DOSSIER_SHA256,
            "parent_candidate_dossier_file_sha256": PARENT_DOSSIER_FILE_SHA256,
            "independence_status": "fresh_second_model_task_and_order_units_under_frozen_v40_v41_policy",
            "provider_executed": False,
            "production_claim_eligible": False,
            "network_access": False,
        }
    )
    if replication_order is not None:
        result["replication_order"] = list(replication_order)
    if phase == "acquisition":
        audit = json.loads((output / "audit" / "task_adapter_bank.json").read_text(encoding="utf-8"))
        result["audit_sha256"] = digest(audit)
        result["manifest_sha256"] = digest(
            {"config": config, "tasks": result["tasks"], "audit": audit}
        )
    else:
        audits = {
            strategy: json.loads((output / "audit" / f"{strategy}.json").read_text(encoding="utf-8"))
            for strategy in ("naive_sequential", "replay_sequential")
        }
        result["manifest_sha256"] = digest(
            {"config": config, "tasks": result["tasks"], "audits": audits}
        )
    result["result_sha256"] = digest(
        {key: value for key, value in result.items() if key != "result_sha256"}
    )
    output.joinpath("config.json").write_text(
        json.dumps(config, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    output.joinpath("result.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return result


def run_acquisition_case(output: Path, model: Path, task_seed: int) -> dict[str, Any]:
    model = model.resolve()
    if model != MODEL_DEFAULT.resolve():
        raise ValueError("V44 acquisition model drift")
    if task_seed not in TASK_SEEDS:
        raise ValueError("V44 acquisition task seed drift")
    with _patched(
        acquisition,
        {
            "MODEL_DEFAULT": MODEL_DEFAULT,
            "TASK_SEEDS": TASK_SEEDS,
            "STATE_SLICE": ACQUISITION_STATE_SLICE,
            "PROTOCOL": ACQUISITION_PROTOCOL,
            "CLAIM_CEILING": ACQUISITION_CLAIM_CEILING,
        },
    ):
        result = acquisition.run_case(output, model, task_seed)
    return _finalize_case(
        output,
        result,
        phase="acquisition",
        state_slice=ACQUISITION_STATE_SLICE,
        protocol=ACQUISITION_PROTOCOL,
        claim_ceiling=ACQUISITION_CLAIM_CEILING,
        classification="LlamaSecondModelAcquisitionReplicationCase",
        model=model,
        task_seed=task_seed,
    )


def run_retention_case(output: Path, source_case: Path, model: Path, task_seed: int) -> dict[str, Any]:
    model = model.resolve()
    if model != MODEL_DEFAULT.resolve():
        raise ValueError("V44 retention model drift")
    if task_seed not in TASK_SEEDS:
        raise ValueError("V44 retention task seed drift")
    with _patched(
        retention,
        {
            "MODEL_DEFAULT": MODEL_DEFAULT,
            "TASK_SEEDS": TASK_SEEDS,
            "STATE_SLICE": RETENTION_STATE_SLICE,
            "PROTOCOL": RETENTION_PROTOCOL,
            "SOURCE_STATE_SLICE": ACQUISITION_STATE_SLICE,
            "CLAIM_CEILING": RETENTION_CLAIM_CEILING,
        },
    ):
        result = retention.run_case(output, source_case, model, task_seed)
    return _finalize_case(
        output,
        result,
        phase="retention",
        state_slice=RETENTION_STATE_SLICE,
        protocol=RETENTION_PROTOCOL,
        claim_ceiling=RETENTION_CLAIM_CEILING,
        classification="LlamaSecondModelRetentionReplicationCase",
        model=model,
        task_seed=task_seed,
    )


def run_order_case(
    output: Path,
    source_case: Path,
    model: Path,
    task_seed: int,
    replication_order: tuple[int, ...],
) -> dict[str, Any]:
    model = model.resolve()
    replication_order = tuple(replication_order)
    if model != MODEL_DEFAULT.resolve():
        raise ValueError("V44 order model drift")
    if task_seed not in TASK_SEEDS or replication_order not in ORDERS:
        raise ValueError("V44 order task or order drift")
    with _patched(
        retention,
        {
            "MODEL_DEFAULT": MODEL_DEFAULT,
            "TASK_SEEDS": TASK_SEEDS,
            "STATE_SLICE": RETENTION_STATE_SLICE,
            "PROTOCOL": RETENTION_PROTOCOL,
            "SOURCE_STATE_SLICE": ACQUISITION_STATE_SLICE,
            "CLAIM_CEILING": RETENTION_CLAIM_CEILING,
        },
    ), _patched(
        order_retention,
        {
            "MODEL_DEFAULT": MODEL_DEFAULT,
            "TASK_SEEDS": TASK_SEEDS,
            "STATE_SLICE": ORDER_STATE_SLICE,
            "PROTOCOL": ORDER_PROTOCOL,
            "SOURCE_STATE_SLICE": ACQUISITION_STATE_SLICE,
            "CLAIM_CEILING": ORDER_CLAIM_CEILING,
        },
    ):
        result = order_retention.run_case(
            output, source_case, model, task_seed, replication_order
        )
    return _finalize_case(
        output,
        result,
        phase="order_retention",
        state_slice=ORDER_STATE_SLICE,
        protocol=ORDER_PROTOCOL,
        claim_ceiling=ORDER_CLAIM_CEILING,
        classification="LlamaSecondModelOrderRetentionReplicationCase",
        model=model,
        task_seed=task_seed,
        replication_order=replication_order,
    )


def _offline_environment() -> dict[str, str]:
    environment = os.environ.copy()
    environment.update(
        {"HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1", "PYTHONDONTWRITEBYTECODE": "1"}
    )
    return environment


def _run_parent_validation() -> dict[str, Any]:
    validator = Path(__file__).with_name("validate_qwen25_candidate_dossier_v43.py")
    completed = subprocess.run(
        [sys.executable, str(validator), str(PARENT_DOSSIER_ROOT)],
        env=_offline_environment(),
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(f"V43 parent dossier validation failed: {completed.stdout.strip()}")
    validation = json.loads(completed.stdout.strip().splitlines()[-1])
    if validation.get("valid") is not True or validation.get("dossier_sha256") != PARENT_DOSSIER_SHA256:
        raise ValueError("V43 parent dossier binding drift")
    dossier_path = PARENT_DOSSIER_ROOT / "dossier.json"
    if sha256_file(dossier_path) != PARENT_DOSSIER_FILE_SHA256:
        raise ValueError("V43 parent dossier file identity drift")
    return validation


def _case_name(phase: str, task_seed: int, replication_order: tuple[int, ...] | None = None) -> str:
    if phase == "acquisition":
        return f"task-seed-{task_seed}-order-0123-fixed-opt-{FIXED_OPTIMIZER_SEED}"
    if phase == "retention":
        return f"task-seed-{task_seed}-order-0123-fixed-opt-{FIXED_OPTIMIZER_SEED}"
    if replication_order is None:
        raise ValueError("order-retention case requires an order")
    return f"task-seed-{task_seed}-order-{''.join(str(item) for item in replication_order)}-fixed-opt-{FIXED_OPTIMIZER_SEED}"


def _run_and_validate_case(
    root: Path,
    phase: str,
    model: Path,
    task_seed: int,
    *,
    source_case: Path | None = None,
    replication_order: tuple[int, ...] | None = None,
) -> dict[str, Any]:
    case_root = root / phase / _case_name(phase, task_seed, replication_order)
    command = [
        sys.executable,
        str(Path(__file__).resolve()),
        "--phase",
        f"{phase}-case",
        "--case-output",
        str(case_root),
        "--model",
        str(model),
        "--task-seed",
        str(task_seed),
    ]
    if source_case is not None:
        command.extend(["--source-case", str(source_case)])
    if replication_order is not None:
        command.extend(["--order", "".join(str(item) for item in replication_order)])
    runner = subprocess.run(
        command, env=_offline_environment(), text=True, capture_output=True, check=False
    )
    (root / f"{phase}-{case_root.name}.runner.log").write_text(
        runner.stdout + "\n" + runner.stderr, encoding="utf-8"
    )
    if runner.returncode != 0:
        return {
            "task_seed": task_seed,
            "order": "".join(str(item) for item in replication_order) if replication_order else "0123",
            "artifact": str(case_root),
            "status": "runner_failed",
            "valid": False,
            "eligible": False,
        }

    validator = Path(__file__).with_name("validate_qwen25_second_model_replication_v44.py")
    validation_command = [
        sys.executable,
        str(validator),
        "--phase",
        f"{phase}-case",
        "--case-root",
        str(case_root),
        "--model",
        str(model),
        "--task-seed",
        str(task_seed),
    ]
    if source_case is not None:
        validation_command.extend(["--source-case", str(source_case)])
    if replication_order is not None:
        validation_command.extend(["--order", "".join(str(item) for item in replication_order)])
    validated = subprocess.run(
        validation_command,
        env=_offline_environment(),
        text=True,
        capture_output=True,
        check=False,
    )
    (root / f"{phase}-{case_root.name}.validator.log").write_text(
        validated.stdout + "\n" + validated.stderr, encoding="utf-8"
    )
    if validated.returncode != 0:
        return {
            "task_seed": task_seed,
            "order": "".join(str(item) for item in replication_order) if replication_order else "0123",
            "artifact": str(case_root),
            "status": "validator_failed",
            "valid": False,
            "eligible": False,
        }
    validation = json.loads(validated.stdout.strip().splitlines()[-1])
    validation_root = root / "validation" / phase
    validation_root.mkdir(parents=True, exist_ok=True)
    write_json(validation_root / f"{case_root.name}.json", validation)
    result = json.loads((case_root / "result.json").read_text(encoding="utf-8"))
    return {
        "task_seed": task_seed,
        "order": "".join(str(item) for item in replication_order) if replication_order else "0123",
        "artifact": str(case_root),
        "status": "validated",
        "valid": validation["valid"],
        "eligible": validation["eligible"],
        "gates": validation.get("gates", validation.get("eligibility_gates")),
        "result_sha256": result["result_sha256"],
    }


def run_campaign(artifact_root: Path, model: Path, runtime_root: Path) -> dict[str, Any]:
    artifact_root = artifact_root.resolve()
    model = model.resolve()
    runtime_root = runtime_root.resolve()
    _ensure_external_new_root(artifact_root)
    if model != MODEL_DEFAULT.resolve() or not model.is_dir():
        raise ValueError("V44 fixed Llama model is unavailable or drifted")
    if not runtime_root.is_dir():
        raise FileNotFoundError(f"V44 runtime receipt root is missing: {runtime_root}")

    from experiments.continual_learning.validate_runtime_receipt import validate as validate_runtime

    runtime_validation = validate_runtime(runtime_root, model)
    if runtime_validation.get("valid") is not True or runtime_validation.get("training") is not False:
        raise ValueError("V44 runtime preflight is not a valid inference-only receipt")
    parent_validation = _run_parent_validation()
    artifact_root.mkdir(parents=True)
    runtime_receipt_path = runtime_root / "receipt.json"
    contract = {
        "state_slice": STATE_SLICE,
        "protocol": PROTOCOL,
        "model": str(model),
        "parent_candidate_model": str(PARENT_MODEL),
        "parent_candidate_dossier_root": str(PARENT_DOSSIER_ROOT),
        "parent_candidate_dossier_sha256": PARENT_DOSSIER_SHA256,
        "parent_candidate_dossier_file_sha256": PARENT_DOSSIER_FILE_SHA256,
        "parent_candidate_validation": parent_validation,
        "runtime_preflight_state_slice": runtime_validation["state_slice"],
        "runtime_preflight_root": str(runtime_root),
        "runtime_preflight_manifest_sha256": runtime_validation["manifest_sha256"],
        "runtime_preflight_receipt_file_sha256": sha256_file(runtime_receipt_path),
        "task_seeds": list(TASK_SEEDS),
        "orders": ["".join(str(item) for item in order) for order in ORDERS],
        "fixed_optimizer_seed": FIXED_OPTIMIZER_SEED,
        "iters": ITERS,
        "update_budget": UPDATE_BUDGET,
        "replay_capacity": REPLAY_CAPACITY,
        "recovery_iters": RECOVERY_ITERS,
        "mechanism_contract": "V40/V41 raw-text task-adapter-bank acquisition-retention-order-v1",
        "primary_metric": "all_expected_second_model_cases_valid_and_eligible",
        "expected_case_count": 15,
        "acquisition_expected_case_count": 3,
        "retention_expected_case_count": 3,
        "order_retention_expected_case_count": 9,
        "training": True,
        "network_access": False,
        "provider_executed": False,
        "production_claim_eligible": False,
        "adaptive_tuning": False,
        "result_reuse": False,
        "prediction_locking": True,
    }
    contract["contract_sha256"] = digest(contract)
    write_json(artifact_root / "contract.json", contract)

    acquisition_cases = []
    stop_reason: str | None = None
    for task_seed in TASK_SEEDS:
        record = _run_and_validate_case(artifact_root, "acquisition", model, task_seed)
        acquisition_cases.append(record)
        if record["valid"] is not True:
            stop_reason = "acquisition_case_validation_failed"
            break
    acquisition_complete = len(acquisition_cases) == len(TASK_SEEDS) and all(
        record["valid"] is True for record in acquisition_cases
    )
    acquisition_eligible = acquisition_complete and all(
        record["eligible"] is True for record in acquisition_cases
    )

    retention_cases: list[dict[str, Any]] = []
    order_cases: list[dict[str, Any]] = []
    if not acquisition_eligible and stop_reason is None:
        stop_reason = "acquisition_eligibility_gate_failed"
    if acquisition_eligible:
        for task_seed in TASK_SEEDS:
            source_case = artifact_root / "acquisition" / _case_name("acquisition", task_seed)
            record = _run_and_validate_case(
                artifact_root, "retention", model, task_seed, source_case=source_case
            )
            retention_cases.append(record)
            if record["valid"] is not True:
                stop_reason = "retention_case_validation_failed"
                break
        retention_complete = len(retention_cases) == len(TASK_SEEDS) and all(
            record["valid"] is True for record in retention_cases
        )
        retention_eligible = retention_complete and all(
            record["eligible"] is True for record in retention_cases
        )
        if not retention_eligible and stop_reason is None:
            stop_reason = "retention_eligibility_gate_failed"
        if retention_eligible:
            for task_seed in TASK_SEEDS:
                source_case = artifact_root / "acquisition" / _case_name("acquisition", task_seed)
                for replication_order in ORDERS:
                    record = _run_and_validate_case(
                        artifact_root,
                        "order_retention",
                        model,
                        task_seed,
                        source_case=source_case,
                        replication_order=replication_order,
                    )
                    order_cases.append(record)
                    if record["valid"] is not True:
                        stop_reason = "order_case_validation_failed"
                        break
                if stop_reason is not None:
                    break

    records = acquisition_cases + retention_cases + order_cases
    all_cases_valid = bool(records) and all(record["valid"] is True for record in records)
    all_cases_eligible = (
        len(records) == 15 and all(record["eligible"] is True for record in records)
    )
    replication_eligible = all_cases_valid and all_cases_eligible
    if replication_eligible:
        classification = "LlamaSecondModelReplicationEligibleLocalDevelopmentOnly"
    elif not acquisition_eligible:
        classification = "LlamaSecondModelReplicationStoppedAtAcquisitionEligibility"
    elif not retention_cases:
        classification = "LlamaSecondModelReplicationStoppedBeforeRetention"
    elif not order_cases:
        classification = "LlamaSecondModelReplicationStoppedBeforeOrderRetention"
    else:
        classification = "LlamaSecondModelReplicationIncomplete"
    report = {
        "state_slice": STATE_SLICE,
        "protocol": PROTOCOL,
        "claim_ceiling": CLAIM_CEILING,
        "classification": classification,
        "model": str(model),
        "parent_candidate_dossier_sha256": PARENT_DOSSIER_SHA256,
        "parent_candidate_dossier_file_sha256": PARENT_DOSSIER_FILE_SHA256,
        "runtime_preflight_manifest_sha256": runtime_validation["manifest_sha256"],
        "runtime_preflight_root": str(runtime_root),
        "runtime_preflight_receipt_file_sha256": sha256_file(runtime_receipt_path),
        "task_seeds": list(TASK_SEEDS),
        "orders": ["".join(str(item) for item in order) for order in ORDERS],
        "fixed_optimizer_seed": FIXED_OPTIMIZER_SEED,
        "expected_case_count": 15,
        "case_count": len(records),
        "acquisition_cases": acquisition_cases,
        "retention_cases": retention_cases,
        "order_retention_cases": order_cases,
        "acquisition_complete": acquisition_complete,
        "acquisition_eligible": acquisition_eligible,
        "retention_complete": len(retention_cases) == 3 and all(
            record["valid"] is True for record in retention_cases
        ),
        "retention_eligible": len(retention_cases) == 3
        and all(record["eligible"] is True for record in retention_cases),
        "order_retention_complete": len(order_cases) == 9 and all(
            record["valid"] is True for record in order_cases
        ),
        "all_cases_valid": all_cases_valid,
        "all_cases_eligible": all_cases_eligible,
        "replication_eligible": replication_eligible,
        "stop_reason": stop_reason,
        "training": True,
        "network_access": False,
        "provider_executed": False,
        "production_claim_eligible": False,
        "adaptive_tuning": False,
        "result_reuse": False,
        "prediction_locking": True,
    }
    report["report_sha256"] = digest(report)
    write_json(artifact_root / "report.json", report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--phase",
        required=True,
        choices=("campaign", "acquisition-case", "retention-case", "order_retention-case"),
    )
    parser.add_argument("--artifact-root", type=Path)
    parser.add_argument("--case-output", type=Path)
    parser.add_argument("--source-case", type=Path)
    parser.add_argument("--model", type=Path, default=MODEL_DEFAULT)
    parser.add_argument("--runtime-receipt", type=Path)
    parser.add_argument("--task-seed", type=int)
    parser.add_argument("--order")
    args = parser.parse_args()
    if args.phase == "campaign":
        if args.artifact_root is None or args.runtime_receipt is None:
            raise ValueError("V44 campaign requires artifact-root and runtime-receipt")
        report = run_campaign(args.artifact_root, args.model, args.runtime_receipt)
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0 if report["all_cases_valid"] else 1
    if args.case_output is None or args.task_seed is None:
        raise ValueError("V44 case requires case-output and task-seed")
    if args.phase == "acquisition-case":
        result = run_acquisition_case(args.case_output, args.model, args.task_seed)
    elif args.phase == "retention-case":
        if args.source_case is None:
            raise ValueError("V44 retention case requires source-case")
        result = run_retention_case(args.case_output, args.source_case, args.model, args.task_seed)
    else:
        if args.source_case is None or args.order is None:
            raise ValueError("V44 order case requires source-case and order")
        replication_order = tuple(int(value) for value in args.order)
        result = run_order_case(
            args.case_output,
            args.source_case,
            args.model,
            args.task_seed,
            replication_order,
        )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
