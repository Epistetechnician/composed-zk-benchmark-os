from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import subprocess
from typing import Any


HERE = Path(__file__).parent


def load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, HERE / filename)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


CONTRACT = load("v41r26_campaign_contract", "validate.py")
WORKER = load("v41r26_campaign_worker", "validate_worker.py")
PREFLIGHT_RESULT_SHA256 = "sha256:e87b2e95ce6058bf0f00d556b8a8d900c89805b416b9983de21668ed6db7ed13"


def file_hash(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def aggregate(workers: list[dict[str, Any]]) -> dict[str, Any]:
    panel_passes = []
    for panel in CONTRACT.expected_contract()["panels"]:
        panel_rows = [row for row in workers if row.get("run_spec", {}).get("panel_id") == panel["panel_id"]]
        panel_passes.append(len(panel_rows) == 3 and all(row.get("pass") is True for row in panel_rows))
    successful = sum(panel_passes); total = len(panel_passes)
    lower = CONTRACT.wilson_lower(successful, total)
    governance = sum(row.get("governance_violations", 1) for row in workers)
    keep = (len(workers) == 48 and successful == 16 and lower > 0.80 and governance == 0
            and all(row.get("pass") is True for row in workers))
    return {"candidate_keep": keep, "successful_panels": successful, "total_panels": total,
            "successful_runs": sum(row.get("pass") is True for row in workers),
            "total_runs": len(workers), "wilson_95_lower": lower,
            "governance_violations": governance}


def validate(artifact: Path, rgs_root: Path) -> dict[str, Any]:
    result_path = artifact / "campaign-result.json"
    contract_path = artifact / "campaign-contract.json"
    binding_path = artifact / "preflight-binding.json"
    manifest_path = artifact / "MANIFEST.sha256"
    if not all(path.is_file() for path in (result_path, contract_path, binding_path, manifest_path)):
        return {"valid": False, "errors": ["campaign artifact files missing"]}
    errors: set[str] = set()
    try:
        result = json.loads(result_path.read_text())
        frozen_contract = json.loads(contract_path.read_text())
        binding = json.loads(binding_path.read_text())
    except (json.JSONDecodeError, OSError):
        return {"valid": False, "errors": ["campaign artifact parse"]}
    expected_contract = CONTRACT.expected_contract()
    if frozen_contract != expected_contract or result.get("contract") != expected_contract: errors.add("contract")
    if binding != {"preflight_result_sha256": PREFLIGHT_RESULT_SHA256}: errors.add("preflight_binding")
    if result.get("preflight_result_sha256") != PREFLIGHT_RESULT_SHA256: errors.add("preflight_result_sha256")
    body = {key: value for key, value in result.items() if key != "result_sha256"}
    if result.get("result_sha256") != CONTRACT.canonical_hash(body): errors.add("result_sha256")
    constants = {"version": "mesh.astral_v41r26_multipanel_qualification.v1",
                 "state_slice": "V41R26MultiPanelReplayQualificationDesign",
                 "classification": "V41R26CampaignComplete", "worker_count": 48,
                 "adaptive_stopping": False, "tune_opened": False, "assessment_opened": False,
                 "claim_ceiling": "RemoteH100MultiPanelReplayQualificationV41R26"}
    for key, value in constants.items():
        if result.get(key) != value: errors.add(key)
    if result.get("operational_envelope") != {
        "maximum_campaign_seconds": 14_400, "maximum_worker_seconds": 600,
        "maximum_provider_spend_usd": 15.0, "restart_policy": "never"
    }: errors.add("operational_envelope")
    specs = WORKER.expected_specs(); workers = []; summaries = []
    for run_id, spec in specs.items():
        worker_dir = artifact / "workers" / run_id
        report = WORKER.validate(worker_dir, rgs_root)
        if not report.get("valid"): errors.add(f"worker:{run_id}")
        try:
            worker = json.loads((worker_dir / "worker-result.json").read_text())
        except (json.JSONDecodeError, OSError):
            continue
        if worker.get("run_spec") != spec: errors.add(f"worker_spec:{run_id}")
        workers.append(worker)
        summaries.append({"run_id": run_id, "result_sha256": worker.get("result_sha256"),
                          "pass": worker.get("pass")})
    workers_root = artifact / "workers"
    if workers_root.is_dir() and sorted(path.name for path in workers_root.iterdir()) != sorted(specs):
        errors.add("worker_directory_census")
    if result.get("worker_results") != summaries: errors.add("worker_results")
    expected_decision = aggregate(workers)
    for key, value in expected_decision.items():
        actual = result.get(key)
        if isinstance(value, float):
            if not isinstance(actual, (int, float)) or not math.isclose(actual, value, rel_tol=0, abs_tol=1e-15):
                errors.add(f"decision:{key}")
        elif actual != value: errors.add(f"decision:{key}")
    files = [result_path, contract_path, binding_path]
    files.extend(item for run_id in specs for item in
                 (artifact / "workers" / run_id / "worker-result.json",
                  artifact / "workers" / run_id / "worker-adapter-state.pt",
                  artifact / "workers" / run_id / "MANIFEST.sha256"))
    if all(path.is_file() for path in files):
        expected_manifest = "".join(
            f'{file_hash(path).removeprefix("sha256:")}  {path.relative_to(artifact)}\n' for path in files)
        if manifest_path.read_text() != expected_manifest: errors.add("manifest")
    else: errors.add("manifest_census")
    source = result.get("source", {}); commit = source.get("rgs_commit", "")
    for key, relative in (("coordinator_sha256", "scripts/run_v41r26_campaign.py"),
                          ("worker_sha256", "scripts/run_v41r26_worker.py"),
                          ("method_sha256", "mesh_brain/meshmodel/v41r26_multipanel_qualification.py"),
                          ("requirements_sha256", "requirements-v41-h100-profile.txt")):
        try:
            content = subprocess.run(["git", "show", f"{commit}:{relative}"], cwd=rgs_root,
                                     check=True, capture_output=True).stdout
            if source.get(key) != "sha256:" + hashlib.sha256(content).hexdigest(): errors.add(key)
        except (subprocess.CalledProcessError, TypeError): errors.add(f"{key}:unavailable")
    return {"version": "astral.v41r26_campaign_artifact_validation.v1", "valid": not errors,
            "errors": sorted(errors), "classification": result.get("classification"),
            "candidate_keep": result.get("candidate_keep") if not errors else None,
            "worker_count": len(workers), "result_sha256": result.get("result_sha256"),
            "claim_ceiling": result.get("claim_ceiling") if not errors else None}


def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--artifact", type=Path, required=True)
    parser.add_argument("--rgs-root", type=Path, required=True); args = parser.parse_args()
    report = validate(args.artifact.resolve(), args.rgs_root.resolve())
    print(json.dumps(report, indent=2, sort_keys=True)); return 0 if report["valid"] else 1


if __name__ == "__main__": raise SystemExit(main())
