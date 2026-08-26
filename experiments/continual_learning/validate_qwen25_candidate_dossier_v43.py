#!/usr/bin/env python3
"""Independent validator for the V43 Qwen2.5 local-candidate dossier."""

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

from experiments.continual_learning.qwen25_candidate_dossier_v43 import (
    CLAIM_CEILING,
    LANES,
    MODEL,
    PROTOCOL,
    SECOND_MODEL_ROOT,
    STATE_SLICE,
    selection_gates,
)
from experiments.continual_learning.runtime_seam import digest, sha256_file


CLASSIFICATION = "Qwen25LocalCandidateSelectedProviderProductionAndSecondModelPending"
BOUNDARY_FALSE = (
    "training_executed",
    "inference_executed",
    "network_access",
    "provider_executed",
    "production_executed",
)


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"V43 object shape drift: {path.name}")
    return value


def _validate_signed(payload: dict[str, Any], field: str, label: str) -> None:
    expected = payload.get(field)
    unsigned = {key: value for key, value in payload.items() if key != field}
    if expected != digest(unsigned):
        raise ValueError(f"{label} digest mismatch")


def _run_validator(script: str, root: Path) -> dict[str, Any]:
    command = [sys.executable, str(Path(__file__).with_name(script)), str(root.resolve())]
    environment = os.environ.copy()
    environment.update(
        {"HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1", "PYTHONDONTWRITEBYTECODE": "1"}
    )
    completed = subprocess.run(command, env=environment, text=True, capture_output=True, check=False)
    if completed.returncode != 0:
        reason = completed.stdout.strip() or completed.stderr.strip()
        raise ValueError(f"V43 source revalidation failed for {script}: {reason}")
    return json.loads(completed.stdout.strip().splitlines()[-1])


def _validate_lane(root: Path, lane: dict[str, Any], recorded: dict[str, Any]) -> dict[str, Any]:
    expected_root = Path(lane["root"]).resolve()
    if recorded.get("name") != lane["name"] or recorded.get("root") != str(expected_root):
        raise ValueError(f"V43 source identity drift: {lane['name']}")
    if recorded.get("case_count") != lane["expected_cases"]:
        raise ValueError(f"V43 source case-count drift: {lane['name']}")
    if recorded.get("valid") is not True or recorded.get("campaign_eligible") is not True:
        raise ValueError(f"V43 source eligibility drift: {lane['name']}")

    fresh = _run_validator(str(lane["validator"]), expected_root)
    stored = _read_json(root / f"validation-{lane['name']}.json")
    if stored != fresh or recorded.get("validation") != fresh:
        raise ValueError(f"V43 source validation receipt drift: {lane['name']}")
    if recorded.get("validation_sha256") != digest(fresh):
        raise ValueError(f"V43 source validation digest drift: {lane['name']}")

    report_path = expected_root / "campaign_report.json"
    contract_path = expected_root / "campaign_contract.json"
    report = _read_json(report_path)
    report_file_sha256 = sha256_file(report_path)
    if report_file_sha256 != lane["report_file_sha256"]:
        raise ValueError(f"V43 frozen source report drift: {lane['name']}")
    if recorded.get("report_file_sha256") != report_file_sha256:
        raise ValueError(f"V43 recorded report digest drift: {lane['name']}")
    if recorded.get("contract_file_sha256") != sha256_file(contract_path):
        raise ValueError(f"V43 recorded contract digest drift: {lane['name']}")
    if recorded.get("report_sha256") != report.get("report_sha256"):
        raise ValueError(f"V43 signed report binding drift: {lane['name']}")
    if report.get("model") != MODEL:
        raise ValueError(f"V43 source model drift: {lane['name']}")
    return {
        "name": lane["name"],
        "case_count": fresh["case_count"],
        "valid": fresh["valid"],
        "campaign_eligible": fresh["campaign_eligible"],
    }


def validate(root: Path) -> dict[str, Any]:
    root = root.resolve()
    contract = _read_json(root / "contract.json")
    dossier = _read_json(root / "dossier.json")
    _validate_signed(contract, "contract_sha256", "V43 contract")
    _validate_signed(dossier, "dossier_sha256", "V43 dossier")

    for payload in (contract, dossier):
        if payload.get("state_slice") != STATE_SLICE or payload.get("protocol") != PROTOCOL:
            raise ValueError("V43 state or protocol drift")
        if payload.get("claim_ceiling") != CLAIM_CEILING or payload.get("model") != MODEL:
            raise ValueError("V43 claim or model drift")
        if any(payload.get(key) is not False for key in BOUNDARY_FALSE):
            raise ValueError("V43 execution boundary drift")
    if dossier.get("contract_sha256") != contract["contract_sha256"]:
        raise ValueError("V43 dossier/contract binding drift")
    if contract.get("primary_metric") != "all_local_candidate_evidence_lanes_valid_and_eligible":
        raise ValueError("V43 primary metric drift")
    if contract.get("expected_case_total") != 15:
        raise ValueError("V43 expected case total drift")
    if contract.get("second_model_root") != str(SECOND_MODEL_ROOT.resolve()):
        raise ValueError("V43 second-model source drift")

    expected_roots = {lane["name"]: str(Path(lane["root"]).resolve()) for lane in LANES}
    if contract.get("source_roots") != expected_roots:
        raise ValueError("V43 source root map drift")
    recorded_lanes = dossier.get("lanes")
    if not isinstance(recorded_lanes, list) or len(recorded_lanes) != len(LANES):
        raise ValueError("V43 lane cardinality drift")
    summaries = []
    for lane in LANES:
        recorded = next((item for item in recorded_lanes if item.get("name") == lane["name"]), None)
        if not isinstance(recorded, dict):
            raise ValueError(f"V43 source lane missing: {lane['name']}")
        summaries.append(_validate_lane(root, dict(lane), recorded))

    gates = selection_gates(summaries)
    if dossier.get("selection_gates") != gates or not all(gates.values()):
        raise ValueError("V43 candidate selection gate drift")
    if dossier.get("candidate_selected") is not True or dossier.get("local_case_count") != 15:
        raise ValueError("V43 local candidate result drift")
    if dossier.get("classification") != CLASSIFICATION:
        raise ValueError("V43 classification drift")

    fresh_second_model = _run_validator(
        "validate_nemotron_target_acquisition_recovery_v42.py", SECOND_MODEL_ROOT
    )
    stored_second_model = _read_json(root / "validation-second-model-boundary.json")
    second_model = dossier.get("second_model_evidence")
    if not isinstance(second_model, dict):
        raise ValueError("V43 second-model boundary missing")
    if stored_second_model != fresh_second_model or second_model.get("validation") != fresh_second_model:
        raise ValueError("V43 second-model validation receipt drift")
    if fresh_second_model.get("valid") is not True or fresh_second_model.get("eligible") is not False:
        raise ValueError("V43 second-model negative boundary drift")
    receipt_path = SECOND_MODEL_ROOT / "receipt.json"
    receipt = _read_json(receipt_path)
    if second_model.get("receipt_sha256") != receipt.get("receipt_sha256"):
        raise ValueError("V43 second-model signed receipt drift")
    if second_model.get("receipt_file_sha256") != sha256_file(receipt_path):
        raise ValueError("V43 second-model receipt file drift")
    if second_model.get("validation_sha256") != digest(fresh_second_model):
        raise ValueError("V43 second-model validation digest drift")
    if second_model.get("status") != "validated_negative_not_second_model_replication":
        raise ValueError("V43 second-model status drift")

    for key in (
        "second_model_replication_complete",
        "provider_validation_complete",
        "production_validation_complete",
    ):
        if dossier.get(key) is not False:
            raise ValueError(f"V43 completion boundary drift: {key}")
    if contract.get("second_model_replication_complete") is not False:
        raise ValueError("V43 contract second-model boundary drift")

    return {
        "valid": True,
        "state_slice": STATE_SLICE,
        "claim_ceiling": CLAIM_CEILING,
        "candidate_selected": True,
        "classification": CLASSIFICATION,
        "local_case_count": 15,
        "selection_gates": gates,
        "second_model_replication_complete": False,
        "provider_validation_complete": False,
        "production_validation_complete": False,
        "dossier_sha256": dossier["dossier_sha256"],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    args = parser.parse_args()
    try:
        print(json.dumps(validate(args.root), sort_keys=True))
        return 0
    except Exception as exc:
        print(json.dumps({"valid": False, "reason": str(exc)}, sort_keys=True))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
