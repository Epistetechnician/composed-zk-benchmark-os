#!/usr/bin/env python3
"""Build a custody-bound local candidate dossier from V40/V41 evidence.

State slice: continual-learning-qwen25-candidate-dossier-v43.

This module performs no training, inference, network, provider, or production
operation. It executes the existing independent campaign validators in fresh
subprocesses and binds their outputs to one immutable external dossier.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from experiments.continual_learning.runtime_seam import digest, sha256_file, write_json


STATE_SLICE = "continual-learning-qwen25-candidate-dossier-v43"
PROTOCOL = "v43-qwen25-local-candidate-dossier-v1"
CLAIM_CEILING = "LocalDevelopmentCandidateSelectionDossier"
MODEL = "/Users/shaanp/.lmstudio/models/mlx-community/Qwen2.5-0.5B-Instruct-4bit"
ARTIFACT_BASE = Path("/Users/shaanp/.codex/research-artifacts/composed-zk-benchmark-os")
ACQUISITION_ROOT = ARTIFACT_BASE / "continual-learning-qwen25-fresh-fixed-optimizer-acquisition-v40-20260824-r1"
RETENTION_ROOT = ARTIFACT_BASE / "continual-learning-qwen25-fresh-fixed-optimizer-retention-v40-20260824-r1"
ORDER_ROOT = ARTIFACT_BASE / "continual-learning-qwen25-fresh-fixed-optimizer-order-retention-v41-20260824-r2"
SECOND_MODEL_ROOT = ARTIFACT_BASE / "continual-learning-nemotron-target160-recovery-v42-20260825-r2"
LANES = (
    {
        "name": "fresh_acquisition",
        "root": ACQUISITION_ROOT,
        "validator": "validate_qwen25_fresh_fixed_optimizer_campaign_v40.py",
        "expected_cases": 3,
        "report_file_sha256": "fdfaabd01ec5da19ac99403f783e0d51faf9400a5de682c6580271d2f0fd61bb",
    },
    {
        "name": "canonical_retention",
        "root": RETENTION_ROOT,
        "validator": "validate_qwen25_fresh_fixed_optimizer_retention_campaign_v40.py",
        "expected_cases": 3,
        "report_file_sha256": "aa40d5e137913a7147046a8adb379fa0b576edc63b90d73976d97bd6e34baae6",
    },
    {
        "name": "order_replication",
        "root": ORDER_ROOT,
        "validator": "validate_qwen25_fresh_fixed_optimizer_order_campaign_v41.py",
        "expected_cases": 9,
        "report_file_sha256": "081624933c9f430bdef189270c2f2566c36806c417bacad741684b21f97e2edb",
    },
)


def _ensure_external_new_root(root: Path) -> None:
    if root == REPO_ROOT or REPO_ROOT in root.parents:
        raise ValueError("V43 dossier output must remain outside the repository")
    if root.exists():
        raise FileExistsError(f"refusing overwrite of immutable output: {root}")


def _run_validator(script: str, root: Path) -> dict[str, Any]:
    command = [
        sys.executable,
        str(Path(__file__).with_name(script)),
        str(root.resolve()),
    ]
    environment = os.environ.copy()
    environment.update(
        {"HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1", "PYTHONDONTWRITEBYTECODE": "1"}
    )
    completed = subprocess.run(command, env=environment, text=True, capture_output=True, check=False)
    if completed.returncode != 0:
        raise RuntimeError(f"V43 source validator failed for {script}: {completed.stdout.strip()}")
    return json.loads(completed.stdout.strip().splitlines()[-1])


def _source_lane(lane: dict[str, Any]) -> dict[str, Any]:
    root = Path(lane["root"]).resolve()
    if not root.is_dir():
        raise FileNotFoundError(f"V43 source root missing: {root}")
    report_path = root / "campaign_report.json"
    contract_path = root / "campaign_contract.json"
    validation = _run_validator(str(lane["validator"]), root)
    if validation.get("valid") is not True:
        raise ValueError(f"V43 source lane invalid: {lane['name']}")
    if validation.get("campaign_eligible") is not True:
        raise ValueError(f"V43 source lane is not eligible: {lane['name']}")
    if validation.get("case_count") != lane["expected_cases"]:
        raise ValueError(f"V43 source lane case-count drift: {lane['name']}")
    report_file_sha256 = sha256_file(report_path)
    if report_file_sha256 != lane["report_file_sha256"]:
        raise ValueError(f"V43 source report identity drift: {lane['name']}")
    report = json.loads(report_path.read_text(encoding="utf-8"))
    if report.get("model") != MODEL:
        raise ValueError(f"V43 source model drift: {lane['name']}")
    return {
        "name": lane["name"],
        "root": str(root),
        "case_count": validation["case_count"],
        "valid": True,
        "campaign_eligible": True,
        "claim_ceiling": validation["claim_ceiling"],
        "state_slice": validation["state_slice"],
        "protocol": validation["protocol"],
        "report_sha256": report["report_sha256"],
        "report_file_sha256": report_file_sha256,
        "contract_file_sha256": sha256_file(contract_path),
        "validation_sha256": digest(validation),
        "validation": validation,
    }


def _second_model_boundary() -> dict[str, Any]:
    validation = _run_validator(
        "validate_nemotron_target_acquisition_recovery_v42.py", SECOND_MODEL_ROOT
    )
    if validation.get("valid") is not True or validation.get("eligible") is not False:
        raise ValueError("V43 second-model boundary drift")
    receipt_path = SECOND_MODEL_ROOT / "receipt.json"
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    return {
        "model_family": "nemotron_h",
        "root": str(SECOND_MODEL_ROOT),
        "valid": True,
        "eligible": False,
        "status": "validated_negative_not_second_model_replication",
        "receipt_sha256": receipt["receipt_sha256"],
        "receipt_file_sha256": sha256_file(receipt_path),
        "validation_sha256": digest(validation),
        "validation": validation,
    }


def selection_gates(lanes: list[dict[str, Any]]) -> dict[str, bool]:
    by_name = {lane["name"]: lane for lane in lanes}
    return {
        "fresh_acquisition_valid_and_eligible": bool(
            by_name.get("fresh_acquisition", {}).get("valid")
            and by_name["fresh_acquisition"].get("campaign_eligible")
        ),
        "canonical_retention_valid_and_eligible": bool(
            by_name.get("canonical_retention", {}).get("valid")
            and by_name["canonical_retention"].get("campaign_eligible")
        ),
        "order_replication_valid_and_eligible": bool(
            by_name.get("order_replication", {}).get("valid")
            and by_name["order_replication"].get("campaign_eligible")
        ),
        "expected_case_total_15": sum(lane.get("case_count", 0) for lane in lanes) == 15,
    }


def build_dossier(output: Path) -> dict[str, Any]:
    root = output.resolve()
    _ensure_external_new_root(root)
    lanes = [_source_lane(dict(lane)) for lane in LANES]
    second_model = _second_model_boundary()
    gates = selection_gates(lanes)
    selected = all(gates.values())
    contract = {
        "state_slice": STATE_SLICE,
        "protocol": PROTOCOL,
        "claim_ceiling": CLAIM_CEILING,
        "model": MODEL,
        "source_roots": {lane["name"]: lane["root"] for lane in lanes},
        "second_model_root": str(SECOND_MODEL_ROOT),
        "primary_metric": "all_local_candidate_evidence_lanes_valid_and_eligible",
        "expected_case_total": 15,
        "training_executed": False,
        "inference_executed": False,
        "network_access": False,
        "provider_executed": False,
        "production_executed": False,
        "second_model_replication_complete": False,
    }
    contract["contract_sha256"] = digest(contract)
    dossier = {
        "state_slice": STATE_SLICE,
        "protocol": PROTOCOL,
        "claim_ceiling": CLAIM_CEILING,
        "classification": (
            "Qwen25LocalCandidateSelectedProviderProductionAndSecondModelPending"
            if selected
            else "NoLocalCandidateSelected"
        ),
        "model": MODEL,
        "contract_sha256": contract["contract_sha256"],
        "lanes": lanes,
        "selection_gates": gates,
        "candidate_selected": selected,
        "local_case_count": sum(lane["case_count"] for lane in lanes),
        "second_model_evidence": second_model,
        "second_model_replication_complete": False,
        "provider_validation_complete": False,
        "production_validation_complete": False,
        "training_executed": False,
        "inference_executed": False,
        "network_access": False,
        "provider_executed": False,
        "production_executed": False,
    }
    dossier["dossier_sha256"] = digest(dossier)
    root.mkdir(parents=True)
    write_json(root / "contract.json", contract)
    write_json(root / "dossier.json", dossier)
    for lane in lanes:
        write_json(root / f"validation-{lane['name']}.json", lane["validation"])
    write_json(root / "validation-second-model-boundary.json", second_model["validation"])
    return dossier


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(build_dossier(args.output), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
