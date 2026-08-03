from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
from typing import Any


HERE = Path(__file__).parent


def load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, HERE / filename)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module); return module


CONTRACT = load("v41r27_sentinel_contract", "validate.py")
WORKER = load("v41r27_sentinel_worker", "validate_worker.py")
PREFLIGHT = load("v41r27_sentinel_preflight", "validate_preflight.py")


def file_hash(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def sentinel_specs() -> list[dict[str, Any]]:
    specs = WORKER.expected_specs()
    return [specs[f"v41r27-panel-{panel}-seed-{seed}"] for panel in (0, 7, 15) for seed in CONTRACT.SEEDS]


def decision(workers: list[dict[str, Any]]) -> dict[str, Any]:
    passed = sum(row.get("pass") is True for row in workers)
    governance = sum(int(row.get("governance_violations", 1)) for row in workers)
    keep = len(workers) == 9 and passed == 9 and governance == 0
    return {"sentinel_keep": keep, "run_successes": passed, "run_total": 9,
            "governance_violations": governance}


def validate(artifact: Path, rgs_root: Path) -> dict[str, Any]:
    names = ("sentinel-result.json", "sentinel-contract.json", "preflight-binding.json",
             "preflight-result.json", "preflight-MANIFEST.sha256", "MANIFEST.sha256")
    paths = [artifact / name for name in names]
    if not all(path.is_file() for path in paths):
        return {"valid": False, "errors": ["sentinel artifact files missing"]}
    result = json.loads(paths[0].read_text()); errors: set[str] = set()
    if json.loads(paths[1].read_text()) != CONTRACT.expected_contract(): errors.add("contract")
    body = {key: value for key, value in result.items() if key != "result_sha256"}
    if result.get("result_sha256") != CONTRACT.canonical_hash(body): errors.add("result_sha256")
    preflight_report = PREFLIGHT.validate(artifact, rgs_root, manifest_name="preflight-MANIFEST.sha256")
    if not preflight_report.get("valid") or preflight_report.get("training_authorized") is not True:
        errors.add("preflight")
    binding = json.loads(paths[2].read_text())
    if binding != {"preflight_result_sha256": preflight_report.get("result_sha256")}:
        errors.add("preflight_binding")
    constants = {"version": "mesh.astral_v41r27_agem_retention.v1",
                 "state_slice": "V41R27ProspectiveRetentionStabilityMechanism",
                 "classification": "V41R27SentinelComplete", "worker_count": 9,
                 "adaptive_stopping": False, "tune_opened": False, "assessment_opened": False,
                 "claim_ceiling": "RemoteH100AGEMSentinelV41R27"}
    for key, value in constants.items():
        if result.get(key) != value: errors.add(key)
    expected_specs = sentinel_specs(); workers = []; summaries = []
    for spec in expected_specs:
        worker_dir = artifact / "workers" / spec["run_id"]
        report = WORKER.validate(worker_dir, rgs_root)
        if not report.get("valid"): errors.add(f'worker:{spec["run_id"]}')
        try: worker = json.loads((worker_dir / "worker-result.json").read_text())
        except (OSError, json.JSONDecodeError): continue
        workers.append(worker); summaries.append({"run_id": spec["run_id"],
                                                  "result_sha256": worker.get("result_sha256"),
                                                  "pass": worker.get("pass")})
    worker_root = artifact / "workers"
    if worker_root.is_dir() and sorted(path.name for path in worker_root.iterdir()) != sorted(
            spec["run_id"] for spec in expected_specs): errors.add("worker_directory_census")
    if result.get("worker_results") != summaries: errors.add("worker_results")
    for key, value in decision(workers).items():
        if result.get(key) != value: errors.add(f"decision:{key}")
    if result.get("operational_envelope") != {"maximum_sentinel_seconds": 3600,
                                               "maximum_worker_seconds": 600,
                                               "maximum_provider_spend_usd": 5.0,
                                               "restart_policy": "never"}:
        errors.add("operational_envelope")
    manifest_files = paths[:5]
    manifest_files.extend(item for spec in expected_specs for item in
                          (artifact / "workers" / spec["run_id"] / "worker-result.json",
                           artifact / "workers" / spec["run_id"] / "worker-adapter-state.pt",
                           artifact / "workers" / spec["run_id"] / "MANIFEST.sha256"))
    if all(path.is_file() for path in manifest_files):
        expected_manifest = "".join(
            f'{file_hash(path).removeprefix("sha256:")}  {path.relative_to(artifact)}\n'
            for path in manifest_files)
        if paths[5].read_text() != expected_manifest: errors.add("manifest")
    else: errors.add("manifest_census")
    source = result.get("source", {}); commit = source.get("rgs_commit", "")
    for key, relative in (("coordinator_sha256", "scripts/run_v41r27_sentinel.py"),
                          ("worker_sha256", "scripts/run_v41r27_worker.py"),
                          ("method_sha256", "mesh_brain/meshmodel/v41r27_agem_retention.py"),
                          ("requirements_sha256", "requirements-v41-h100-profile.txt")):
        try:
            content = subprocess.run(["git", "show", f"{commit}:{relative}"], cwd=rgs_root,
                                     check=True, capture_output=True).stdout
            if source.get(key) != "sha256:" + hashlib.sha256(content).hexdigest(): errors.add(key)
        except (subprocess.CalledProcessError, TypeError): errors.add(f"{key}:unavailable")
    return {"version": "astral.v41r27_sentinel_validation.v1", "valid": not errors,
            "errors": sorted(errors), "sentinel_keep": result.get("sentinel_keep") if not errors else None,
            "worker_count": len(workers), "result_sha256": result.get("result_sha256"),
            "claim_ceiling": result.get("claim_ceiling") if not errors else None}


def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--artifact", type=Path, required=True)
    parser.add_argument("--rgs-root", type=Path, required=True); args = parser.parse_args()
    report = validate(args.artifact.resolve(), args.rgs_root.resolve())
    print(json.dumps(report, indent=2, sort_keys=True)); return 0 if report["valid"] else 1


if __name__ == "__main__": raise SystemExit(main())
