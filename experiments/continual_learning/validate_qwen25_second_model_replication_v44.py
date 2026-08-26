#!/usr/bin/env python3
"""Independent validator for the V44 second-model replication.

State slice family: continual-learning-qwen25-second-model-replication-v44.

This validator never executes model training. It independently revalidates the
immutable runtime receipt, V43 parent dossier, V40/V41 case contracts, case
digests, subprocess-produced validation records, and fail-closed aggregation.
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

from experiments.continual_learning import validate_qwen25_fresh_fixed_optimizer_acquisition_v40 as acquisition_validator
from experiments.continual_learning import validate_qwen25_fresh_fixed_optimizer_order_retention_v41 as order_validator
from experiments.continual_learning import validate_qwen25_fresh_fixed_optimizer_retention_v40 as retention_validator
from experiments.continual_learning import validate_runtime_receipt as runtime_validator
from experiments.continual_learning.qwen25_second_model_replication_v44 import (
    ACQUISITION_CLAIM_CEILING,
    ACQUISITION_PROTOCOL,
    ACQUISITION_STATE_SLICE,
    CLAIM_CEILING,
    FIXED_OPTIMIZER_SEED,
    ITERS,
    MODEL_DEFAULT,
    ORDERS,
    ORDER_CLAIM_CEILING,
    ORDER_PROTOCOL,
    ORDER_STATE_SLICE,
    PARENT_DOSSIER_FILE_SHA256,
    PARENT_DOSSIER_ROOT,
    PARENT_DOSSIER_SHA256,
    PARENT_MODEL,
    PROTOCOL,
    RECOVERY_ITERS,
    REPLAY_CAPACITY,
    RETENTION_CLAIM_CEILING,
    RETENTION_PROTOCOL,
    RETENTION_STATE_SLICE,
    STATE_SLICE,
    TASK_SEEDS,
    UPDATE_BUDGET,
    _case_name,
)
from experiments.continual_learning.runtime_seam import digest, sha256_file


def _load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _reject_repo_path(path: Path, label: str) -> Path:
    resolved = path.resolve()
    if resolved == REPO_ROOT or REPO_ROOT in resolved.parents:
        raise ValueError(f"{label} must remain outside the repository")
    return resolved


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


def _validate_case_identity(
    case_root: Path,
    model: Path,
    task_seed: int,
    phase: str,
    replication_order: tuple[int, ...] | None,
) -> None:
    config = _load(case_root / "config.json")
    result = _load(case_root / "result.json")
    if config["model"] != str(model) or result["model"] != str(model):
        raise ValueError("V44 case model binding drift")
    if config["task_seed"] != task_seed or result["task_seed"] != task_seed:
        raise ValueError("V44 case task seed binding drift")
    if config["iters"] != ITERS or config["update_budget"] != UPDATE_BUDGET:
        raise ValueError("V44 case schedule drift")
    if config["optimizer_seed_base"] != FIXED_OPTIMIZER_SEED:
        raise ValueError("V44 case optimizer seed drift")
    if config["second_model_relation"] != "qwen25_candidate_to_llama_v44":
        raise ValueError("V44 second-model relation drift")
    if config["parent_candidate_model"] != str(PARENT_MODEL):
        raise ValueError("V44 parent model binding drift")
    if config["parent_candidate_dossier_sha256"] != PARENT_DOSSIER_SHA256:
        raise ValueError("V44 parent dossier digest drift")
    if config["parent_candidate_dossier_file_sha256"] != PARENT_DOSSIER_FILE_SHA256:
        raise ValueError("V44 parent dossier file digest drift")
    if result["parent_candidate_dossier_sha256"] != PARENT_DOSSIER_SHA256:
        raise ValueError("V44 result parent dossier digest drift")
    if result["parent_candidate_dossier_file_sha256"] != PARENT_DOSSIER_FILE_SHA256:
        raise ValueError("V44 result parent dossier file digest drift")
    if result["provider_executed"] is not False or result["production_claim_eligible"] is not False:
        raise ValueError("V44 provider or production boundary drift")
    if result["network_access"] is not False:
        raise ValueError("V44 network boundary drift")
    expected = {
        "acquisition": (ACQUISITION_STATE_SLICE, ACQUISITION_PROTOCOL, ACQUISITION_CLAIM_CEILING),
        "retention": (RETENTION_STATE_SLICE, RETENTION_PROTOCOL, RETENTION_CLAIM_CEILING),
        "order_retention": (ORDER_STATE_SLICE, ORDER_PROTOCOL, ORDER_CLAIM_CEILING),
    }[phase]
    state_slice, protocol, claim_ceiling = expected
    if (config["state_slice"], config["protocol"]) != (state_slice, protocol):
        raise ValueError("V44 case config state/protocol drift")
    if (result["state_slice"], result["protocol"], result["claim_ceiling"]) != (
        state_slice,
        protocol,
        claim_ceiling,
    ):
        raise ValueError("V44 case result state/protocol/claim drift")
    if result["config"] != config:
        raise ValueError("V44 case config identity drift")
    if replication_order is None:
        if "replication_order" in config or "replication_order" in result:
            raise ValueError("V44 canonical case unexpectedly carries an order override")
    else:
        if tuple(replication_order) not in ORDERS:
            raise ValueError("V44 order is outside the frozen order set")
        if config.get("replication_order") != list(replication_order):
            raise ValueError("V44 case order binding drift")
        if result.get("replication_order") != list(replication_order):
            raise ValueError("V44 result order binding drift")


def validate_case(
    phase: str,
    case_root: Path,
    model: Path,
    task_seed: int,
    source_case: Path | None = None,
    replication_order: tuple[int, ...] | None = None,
) -> dict[str, Any]:
    case_root = _reject_repo_path(case_root, "V44 case artifacts")
    model = model.resolve()
    if model != MODEL_DEFAULT.resolve():
        raise ValueError("V44 fixed model drift")
    if task_seed not in TASK_SEEDS:
        raise ValueError("V44 task seed is outside the frozen set")
    if phase not in {"acquisition", "retention", "order_retention"}:
        raise ValueError("V44 phase is invalid")
    _validate_case_identity(case_root, model, task_seed, phase, replication_order)

    if phase == "acquisition":
        with _patched(
            acquisition_validator,
            {
                "MODEL": str(model),
                "STATE_SLICE": ACQUISITION_STATE_SLICE,
                "PROTOCOL": ACQUISITION_PROTOCOL,
                "TASK_SEEDS": list(TASK_SEEDS),
                "FIXED_OPTIMIZER_SEED": FIXED_OPTIMIZER_SEED,
                "ORDER": [0, 1, 2, 3],
                "CLAIM_CEILING": ACQUISITION_CLAIM_CEILING,
            },
        ):
            validation = acquisition_validator.validate(case_root, model, task_seed)
    elif phase == "retention":
        if source_case is None:
            raise ValueError("V44 retention validation requires an acquisition source")
        source_case = _reject_repo_path(source_case, "V44 source case")
        with _patched(
            retention_validator,
            {
                "MODEL_DEFAULT": model,
                "TASK_SEEDS": list(TASK_SEEDS),
                "STATE_SLICE": RETENTION_STATE_SLICE,
                "PROTOCOL": RETENTION_PROTOCOL,
                "SOURCE_STATE_SLICE": ACQUISITION_STATE_SLICE,
                "FIXED_OPTIMIZER_SEED": FIXED_OPTIMIZER_SEED,
                "CLAIM_CEILING": RETENTION_CLAIM_CEILING,
            },
        ):
            validation = retention_validator.validate(case_root, source_case, model, task_seed)
    else:
        if source_case is None or replication_order is None:
            raise ValueError("V44 order validation requires source and order")
        source_case = _reject_repo_path(source_case, "V44 source case")
        with _patched(
            order_validator,
            {
                "MODEL_DEFAULT": model,
                "TASK_SEEDS": list(TASK_SEEDS),
                "STATE_SLICE": ORDER_STATE_SLICE,
                "PROTOCOL": ORDER_PROTOCOL,
                "SOURCE_STATE_SLICE": ACQUISITION_STATE_SLICE,
                "FIXED_OPTIMIZER_SEED": FIXED_OPTIMIZER_SEED,
                "ORDERS": ORDERS,
                "CLAIM_CEILING": ORDER_CLAIM_CEILING,
            },
        ):
            validation = order_validator.validate(
                case_root, source_case, model, task_seed, replication_order
            )
    if validation.get("valid") is not True:
        raise ValueError("V44 delegated case validator did not return valid=true")
    return validation


def _validate_parent_dossier() -> dict[str, Any]:
    validator = Path(__file__).with_name("validate_qwen25_candidate_dossier_v43.py")
    environment = os.environ.copy()
    environment.update(
        {"HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1", "PYTHONDONTWRITEBYTECODE": "1"}
    )
    completed = subprocess.run(
        [sys.executable, str(validator), str(PARENT_DOSSIER_ROOT)],
        env=environment,
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        raise ValueError("V44 parent dossier validator failed")
    validation = json.loads(completed.stdout.strip().splitlines()[-1])
    if validation.get("valid") is not True or validation.get("dossier_sha256") != PARENT_DOSSIER_SHA256:
        raise ValueError("V44 parent dossier validation drift")
    dossier_file = PARENT_DOSSIER_ROOT / "dossier.json"
    if sha256_file(dossier_file) != PARENT_DOSSIER_FILE_SHA256:
        raise ValueError("V44 parent dossier file drift")
    return validation


def _validate_record(
    root: Path,
    phase: str,
    row: dict[str, Any],
    model: Path,
    task_seed: int,
    source_case: Path | None = None,
    replication_order: tuple[int, ...] | None = None,
) -> dict[str, Any]:
    if row.get("status") != "validated" or row.get("valid") is not True:
        raise ValueError(f"V44 case was not independently validated: {phase}/{task_seed}")
    case_root = root / phase / _case_name(phase, task_seed, replication_order)
    if row.get("artifact") != str(case_root):
        raise ValueError("V44 case artifact path drift")
    expected_order = "".join(str(value) for value in replication_order) if replication_order else "0123"
    if row.get("task_seed") != task_seed or row.get("order") != expected_order:
        raise ValueError("V44 case index drift")
    validation = validate_case(phase, case_root, model, task_seed, source_case, replication_order)
    saved_validation = _load(root / "validation" / phase / f"{case_root.name}.json")
    if saved_validation != validation:
        raise ValueError("V44 saved independent validation drift")
    result = _load(case_root / "result.json")
    if row.get("result_sha256") != result.get("result_sha256"):
        raise ValueError("V44 result digest binding drift")
    expected_gates = validation.get("gates", validation.get("eligibility_gates"))
    if row.get("gates") != expected_gates:
        raise ValueError("V44 aggregate gate record drift")
    return validation


def _assert_case_directory_shape(root: Path, phase: str, expected_names: set[str]) -> None:
    phase_root = root / phase
    actual_names = {path.name for path in phase_root.iterdir() if path.is_dir()} if phase_root.is_dir() else set()
    if actual_names != expected_names:
        raise ValueError(f"V44 {phase} case directory set drift")


def validate(root: Path) -> dict[str, Any]:
    root = _reject_repo_path(root, "V44 aggregate artifacts")
    contract = _load(root / "contract.json")
    report = _load(root / "report.json")
    if contract["state_slice"] != STATE_SLICE or contract["protocol"] != PROTOCOL:
        raise ValueError("V44 contract state/protocol drift")
    if contract["model"] != str(MODEL_DEFAULT.resolve()):
        raise ValueError("V44 contract model drift")
    if contract["parent_candidate_model"] != str(PARENT_MODEL):
        raise ValueError("V44 contract parent model drift")
    if contract["parent_candidate_dossier_root"] != str(PARENT_DOSSIER_ROOT):
        raise ValueError("V44 contract parent root drift")
    if contract["parent_candidate_dossier_sha256"] != PARENT_DOSSIER_SHA256:
        raise ValueError("V44 contract parent dossier drift")
    if contract["parent_candidate_dossier_file_sha256"] != PARENT_DOSSIER_FILE_SHA256:
        raise ValueError("V44 contract parent file drift")
    if contract["task_seeds"] != list(TASK_SEEDS):
        raise ValueError("V44 contract task seeds drift")
    if contract["orders"] != ["".join(str(value) for value in order) for order in ORDERS]:
        raise ValueError("V44 contract orders drift")
    if contract["fixed_optimizer_seed"] != FIXED_OPTIMIZER_SEED:
        raise ValueError("V44 contract optimizer seed drift")
    if contract["iters"] != ITERS or contract["update_budget"] != UPDATE_BUDGET:
        raise ValueError("V44 contract schedule drift")
    if contract["replay_capacity"] != REPLAY_CAPACITY or contract["recovery_iters"] != RECOVERY_ITERS:
        raise ValueError("V44 contract retention budget drift")
    if contract["expected_case_count"] != 15:
        raise ValueError("V44 contract expected count drift")
    for key in ("network_access", "provider_executed", "production_claim_eligible", "adaptive_tuning", "result_reuse"):
        if contract[key] is not False:
            raise ValueError(f"V44 contract boundary drift: {key}")
    if contract["training"] is not True or contract["prediction_locking"] is not True:
        raise ValueError("V44 contract execution policy drift")
    if contract["contract_sha256"] != digest({key: value for key, value in contract.items() if key != "contract_sha256"}):
        raise ValueError("V44 contract digest mismatch")

    runtime_root = _reject_repo_path(Path(contract["runtime_preflight_root"]), "V44 runtime receipt")
    runtime_validation = runtime_validator.validate(runtime_root, MODEL_DEFAULT.resolve())
    if runtime_validation.get("valid") is not True or runtime_validation.get("training") is not False:
        raise ValueError("V44 runtime receipt is not valid inference-only evidence")
    if contract["runtime_preflight_manifest_sha256"] != runtime_validation["manifest_sha256"]:
        raise ValueError("V44 runtime manifest binding drift")
    runtime_receipt = runtime_root / "receipt.json"
    if contract["runtime_preflight_receipt_file_sha256"] != sha256_file(runtime_receipt):
        raise ValueError("V44 runtime receipt file binding drift")
    parent_validation = _validate_parent_dossier()
    if contract["parent_candidate_validation"] != parent_validation:
        raise ValueError("V44 saved parent validation drift")

    if report["state_slice"] != STATE_SLICE or report["protocol"] != PROTOCOL:
        raise ValueError("V44 report state/protocol drift")
    if report["claim_ceiling"] != CLAIM_CEILING:
        raise ValueError("V44 report claim ceiling drift")
    if report["model"] != str(MODEL_DEFAULT.resolve()):
        raise ValueError("V44 report model drift")
    if report["task_seeds"] != list(TASK_SEEDS) or report["orders"] != contract["orders"]:
        raise ValueError("V44 report unit drift")
    if report["fixed_optimizer_seed"] != FIXED_OPTIMIZER_SEED:
        raise ValueError("V44 report optimizer seed drift")
    if report["expected_case_count"] != 15:
        raise ValueError("V44 report expected count drift")
    if report["runtime_preflight_root"] != str(runtime_root):
        raise ValueError("V44 report runtime root drift")
    if report["runtime_preflight_manifest_sha256"] != runtime_validation["manifest_sha256"]:
        raise ValueError("V44 report runtime manifest drift")
    if report["runtime_preflight_receipt_file_sha256"] != sha256_file(runtime_receipt):
        raise ValueError("V44 report runtime receipt drift")
    for key in ("network_access", "provider_executed", "production_claim_eligible", "adaptive_tuning", "result_reuse"):
        if report[key] is not False:
            raise ValueError(f"V44 report boundary drift: {key}")
    if report["training"] is not True or report["prediction_locking"] is not True:
        raise ValueError("V44 report execution policy drift")
    if report["report_sha256"] != digest({key: value for key, value in report.items() if key != "report_sha256"}):
        raise ValueError("V44 report digest mismatch")

    model = MODEL_DEFAULT.resolve()
    acquisition_rows = report["acquisition_cases"]
    retention_rows = report["retention_cases"]
    order_rows = report["order_retention_cases"]
    if len(acquisition_rows) != 3:
        raise ValueError("V44 acquisition case count drift")
    acquisition_names = {_case_name("acquisition", seed) for seed in TASK_SEEDS}
    _assert_case_directory_shape(root, "acquisition", acquisition_names)
    acquisition_validation: dict[int, dict[str, Any]] = {}
    for seed, row in zip(TASK_SEEDS, acquisition_rows, strict=True):
        acquisition_validation[seed] = _validate_record(root, "acquisition", row, model, seed)
    acquisition_complete = all(row["valid"] is True for row in acquisition_rows)
    acquisition_eligible = acquisition_complete and all(
        acquisition_validation[seed]["eligible"] is True for seed in TASK_SEEDS
    )
    if report["acquisition_complete"] != acquisition_complete:
        raise ValueError("V44 acquisition completion aggregation drift")
    if report["acquisition_eligible"] != acquisition_eligible:
        raise ValueError("V44 acquisition eligibility aggregation drift")

    if acquisition_eligible:
        if len(retention_rows) != 3:
            raise ValueError("V44 retention case count drift")
        _assert_case_directory_shape(
            root, "retention", {_case_name("retention", seed) for seed in TASK_SEEDS}
        )
        retention_validation: dict[int, dict[str, Any]] = {}
        for seed, row in zip(TASK_SEEDS, retention_rows, strict=True):
            source_case = root / "acquisition" / _case_name("acquisition", seed)
            retention_validation[seed] = _validate_record(
                root, "retention", row, model, seed, source_case=source_case
            )
        retention_complete = all(row["valid"] is True for row in retention_rows)
        retention_eligible = retention_complete and all(
            retention_validation[seed]["eligible"] is True for seed in TASK_SEEDS
        )
        if report["retention_complete"] != retention_complete:
            raise ValueError("V44 retention completion aggregation drift")
        if report["retention_eligible"] != retention_eligible:
            raise ValueError("V44 retention eligibility aggregation drift")
        if retention_eligible:
            if len(order_rows) != 9:
                raise ValueError("V44 order-retention case count drift")
            _assert_case_directory_shape(
                root,
                "order_retention",
                {
                    _case_name("order_retention", seed, order)
                    for seed in TASK_SEEDS
                    for order in ORDERS
                },
            )
            index = 0
            for seed in TASK_SEEDS:
                source_case = root / "acquisition" / _case_name("acquisition", seed)
                for order in ORDERS:
                    _validate_record(
                        root,
                        "order_retention",
                        order_rows[index],
                        model,
                        seed,
                        source_case=source_case,
                        replication_order=order,
                    )
                    index += 1
        else:
            if order_rows:
                raise ValueError("V44 order-retention executed after failed retention gate")
            _assert_case_directory_shape(root, "order_retention", set())
    else:
        if retention_rows or order_rows:
            raise ValueError("V44 downstream phases executed after failed acquisition gate")
        _assert_case_directory_shape(root, "retention", set())
        _assert_case_directory_shape(root, "order_retention", set())

    all_cases_valid = bool(acquisition_rows) and all(
        row["valid"] is True for row in acquisition_rows + retention_rows + order_rows
    )
    all_cases_eligible = (
        len(acquisition_rows + retention_rows + order_rows) == 15
        and all(row["eligible"] is True for row in acquisition_rows + retention_rows + order_rows)
    )
    replication_eligible = all_cases_valid and all_cases_eligible
    if report["case_count"] != len(acquisition_rows + retention_rows + order_rows):
        raise ValueError("V44 report case count drift")
    if report["all_cases_valid"] != all_cases_valid:
        raise ValueError("V44 report validity aggregation drift")
    if report["all_cases_eligible"] != all_cases_eligible:
        raise ValueError("V44 report eligibility aggregation drift")
    if report["replication_eligible"] != replication_eligible:
        raise ValueError("V44 report replication aggregation drift")
    expected_classification = (
        "LlamaSecondModelReplicationEligibleLocalDevelopmentOnly"
        if replication_eligible
        else "LlamaSecondModelReplicationStoppedAtAcquisitionEligibility"
        if not acquisition_eligible
        else "LlamaSecondModelReplicationStoppedBeforeRetention"
        if not retention_rows
        else "LlamaSecondModelReplicationStoppedBeforeOrderRetention"
        if not order_rows
        else "LlamaSecondModelReplicationIncomplete"
    )
    if report["classification"] != expected_classification:
        raise ValueError("V44 classification aggregation drift")
    return {
        "valid": True,
        "state_slice": STATE_SLICE,
        "protocol": PROTOCOL,
        "claim_ceiling": CLAIM_CEILING,
        "model": str(model),
        "case_count": report["case_count"],
        "expected_case_count": 15,
        "all_cases_valid": all_cases_valid,
        "all_cases_eligible": all_cases_eligible,
        "replication_eligible": replication_eligible,
        "classification": report["classification"],
        "stop_reason": report["stop_reason"],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path, nargs="?")
    parser.add_argument("--phase", choices=("acquisition-case", "retention-case", "order_retention-case"))
    parser.add_argument("--case-root", type=Path)
    parser.add_argument("--model", type=Path, default=MODEL_DEFAULT)
    parser.add_argument("--task-seed", type=int)
    parser.add_argument("--source-case", type=Path)
    parser.add_argument("--order")
    args = parser.parse_args()
    try:
        if args.phase:
            if args.case_root is None or args.task_seed is None:
                raise ValueError("V44 case validation requires case-root and task-seed")
            phase = args.phase.removesuffix("-case")
            order = tuple(int(value) for value in args.order) if args.order else None
            validation = validate_case(
                phase,
                args.case_root,
                args.model,
                args.task_seed,
                source_case=args.source_case,
                replication_order=order,
            )
        else:
            if args.root is None:
                raise ValueError("V44 aggregate validation requires a root")
            validation = validate(args.root)
        print(json.dumps(validation, sort_keys=True))
        return 0
    except Exception as exc:
        print(json.dumps({"valid": False, "reason": str(exc)}, sort_keys=True))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
