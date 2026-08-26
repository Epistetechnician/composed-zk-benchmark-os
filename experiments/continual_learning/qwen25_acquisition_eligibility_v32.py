#!/usr/bin/env python3
"""V32 bounded Qwen2.5 acquisition-eligibility campaign.

State slice: continual-learning-qwen25-acquisition-eligibility-v32.

The V29 acquisition-only mechanism is reused unchanged.  V32 changes only
the model binding and three preregistered, previously unused seeds.  It does
not run retention, interference, reacquisition, provider, or production work.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from argparse import Namespace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from experiments.continual_learning import factorized_solvability_benchmark as base
from experiments.continual_learning import routed_adapter_bank_acquisition_v29 as v29


STATE_SLICE = "continual-learning-qwen25-acquisition-eligibility-v32"
PROTOCOL = "v32-qwen25-routed-bank-acquisition-eligibility-v1"
MODEL_DEFAULT = Path("/Users/shaanp/.lmstudio/models/mlx-community/Qwen2.5-0.5B-Instruct-4bit")
ORDER = (0, 1, 2, 3)
SEEDS = (20260853, 20260854, 20260855)
ITERS = 160
UPDATE_BUDGET = 32
CLAIM_CEILING = "LocalDevelopmentModelAcquisitionEligibilityPreflight"


def write_json(path: Path, value) -> None:
    if path.exists():
        raise RuntimeError(f"refusing overwrite of immutable artifact: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf8")


def _case_args(output: Path, model: Path, seed: int) -> Namespace:
    return Namespace(
        output=output,
        model=model,
        seed=seed,
        order=",".join(str(value) for value in ORDER),
        task_count=4,
        iters=ITERS,
        update_budget=UPDATE_BUDGET,
    )


def run_case(output: Path, model: Path, seed: int) -> dict:
    output = output.resolve()
    model = model.resolve()
    if output.exists():
        raise RuntimeError(f"refusing overwrite of immutable case: {output}")
    if model != MODEL_DEFAULT.resolve():
        raise ValueError("V32 fixed Qwen2.5 model drift")
    if seed not in SEEDS:
        raise ValueError("V32 seed is not in the preregistered disjoint set")

    patched = {
        "MODEL_DEFAULT": v29.MODEL_DEFAULT,
        "STATE_SLICE": v29.STATE_SLICE,
        "PROTOCOL": v29.PROTOCOL,
        "SEED": v29.SEED,
        "ORDER": v29.ORDER,
    }
    v29.MODEL_DEFAULT = model
    v29.STATE_SLICE = STATE_SLICE
    v29.PROTOCOL = PROTOCOL
    v29.SEED = seed
    v29.ORDER = ORDER
    try:
        result = v29.run(_case_args(output, model, seed))
    finally:
        for key, value in patched.items():
            setattr(v29, key, value)

    config = result["config"]
    config.update(
        {
            "state_slice": STATE_SLICE,
            "protocol": PROTOCOL,
            "model": str(model),
            "campaign_model_change": "Qwen2.5-0.5B-Instruct-4bit_v1",
            "parent_mechanism_state_slice": "continual-learning-model-acquisition-eligibility-v29",
            "assessment": "exact_train_and_heldout_acquisition_only_v1",
        }
    )
    config["contract_sha256"] = base.digest({key: value for key, value in config.items() if key != "contract_sha256"})
    result.update(
        {
            "state_slice": STATE_SLICE,
            "protocol": PROTOCOL,
            "claim_ceiling": CLAIM_CEILING,
            "classification": "Qwen25AcquisitionEligibilityPreflightNoRetentionClaim",
            "config": config,
            "network_access": False,
            "training": True,
            "retention_executed": False,
            "interference_executed": False,
            "provider_executed": False,
            "production_claim_eligible": False,
        }
    )
    audit = json.loads((output / "audit" / "task_adapter_bank.json").read_text(encoding="utf8"))
    result["audit_sha256"] = base.digest(audit)
    result["manifest_sha256"] = base.digest({"config": config, "tasks": result["tasks"], "audit": audit})
    result["result_sha256"] = base.digest({key: value for key, value in result.items() if key != "result_sha256"})
    (output / "config.json").write_text(json.dumps(config, indent=2, sort_keys=True) + "\n", encoding="utf8")
    (output / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf8")
    return result


def _run_case_command(args: argparse.Namespace) -> int:
    result = run_case(args.case_output, args.model, args.seed)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


def run_campaign(args: argparse.Namespace) -> dict:
    artifact_root = args.artifact_root.resolve()
    model = args.model.resolve()
    if artifact_root.exists():
        raise RuntimeError(f"refusing overwrite of immutable campaign: {artifact_root}")
    if not artifact_root.is_absolute() or Path(__file__).resolve().parents[2] in artifact_root.parents:
        raise ValueError("V32 artifacts must remain outside the repository")
    if model != MODEL_DEFAULT.resolve() or not model.is_dir():
        raise ValueError("V32 model binding is unavailable or drifted")

    artifact_root.mkdir(parents=True)
    contract = {
        "state_slice": STATE_SLICE,
        "protocol": PROTOCOL,
        "model": str(model),
        "seeds": list(SEEDS),
        "order": list(ORDER),
        "iters": ITERS,
        "update_budget": UPDATE_BUDGET,
        "primary_metric": "all_task_train_above_no_update_and_target_floors",
        "retention_executed": False,
        "interference_executed": False,
        "provider_executed": False,
        "production_claim_eligible": False,
        "network_access": False,
    }
    contract["contract_sha256"] = base.digest(contract)
    write_json(artifact_root / "campaign_contract.json", contract)
    records = []
    environment = os.environ.copy()
    environment.update({"HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1", "PYTHONDONTWRITEBYTECODE": "1"})
    for seed in SEEDS:
        case_name = f"seed-{seed}-order-0123"
        case_root = artifact_root / case_name
        runner_log = artifact_root / f"{case_name}.runner.log"
        validator_log = artifact_root / f"{case_name}.validator.log"
        runner = subprocess.run(
            [sys.executable, str(Path(__file__).resolve()), "--case-output", str(case_root), "--model", str(model), "--seed", str(seed)],
            env=environment,
            text=True,
            capture_output=True,
            check=False,
        )
        runner_log.write_text(runner.stdout + "\n" + runner.stderr, encoding="utf8")
        if runner.returncode != 0:
            records.append({"seed": seed, "order": "0123", "status": "runner_failed", "valid": False})
            break
        validator = subprocess.run(
            [
                sys.executable,
                str(Path(__file__).with_name("validate_qwen25_acquisition_eligibility_v32.py")),
                str(case_root),
                "--model",
                str(model),
                "--expected-seed",
                str(seed),
            ],
            env=environment,
            text=True,
            capture_output=True,
            check=False,
        )
        validator_log.write_text(validator.stdout + "\n" + validator.stderr, encoding="utf8")
        if validator.returncode != 0:
            records.append({"seed": seed, "order": "0123", "status": "validator_failed", "valid": False})
            break
        validation = json.loads(validator.stdout.strip().splitlines()[-1])
        records.append(
            {
                "seed": seed,
                "order": "0123",
                "status": "validated",
                "valid": validation["valid"],
                "eligible": validation["eligible"],
                "eligibility_gates": validation["eligibility_gates"],
                "result_sha256": json.loads((case_root / "result.json").read_text(encoding="utf8"))["result_sha256"],
            }
        )
        if not validation["valid"]:
            break

    report = {
        "state_slice": STATE_SLICE,
        "protocol": PROTOCOL,
        "claim_ceiling": CLAIM_CEILING,
        "model": str(model),
        "case_count": len(records),
        "expected_case_count": len(SEEDS),
        "cases": records,
        "all_cases_valid": len(records) == len(SEEDS) and all(row["valid"] for row in records),
        "all_cases_eligible": len(records) == len(SEEDS) and all(row.get("eligible") is True for row in records),
        "campaign_eligible": len(records) == len(SEEDS) and all(row.get("eligible") is True for row in records),
        "network_access": False,
        "training": True,
        "retention_executed": False,
        "interference_executed": False,
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
    parser.add_argument("--model", type=Path, default=MODEL_DEFAULT)
    parser.add_argument("--seed", type=int)
    args = parser.parse_args()
    if args.case_output is not None:
        if args.seed is None:
            raise ValueError("case mode requires --seed")
        return _run_case_command(args)
    if args.artifact_root is None:
        raise ValueError("campaign mode requires --artifact-root")
    report = run_campaign(args)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["campaign_eligible"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
