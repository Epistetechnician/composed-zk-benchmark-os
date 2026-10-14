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
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module); return module


CONTRACT = load("v41r27_qualification_contract", "validate.py")
WORKER = load("v41r27_qualification_worker", "validate_worker.py")
SENTINEL = load("v41r27_qualification_sentinel", "validate_sentinel.py")
PARTIAL_ARCHIVE_SHA256 = "93d6bedc8e9e6ae3ab9595a5f924963539a3ac8476e0c5d39da270d588ba0577"
RECOVERED_RUN_IDS = {
    f"v41r27-panel-{panel}-seed-{seed}"
    for panel in range(1, 6) for seed in (412003, 412007, 412019)
} | {"v41r27-panel-6-seed-412003", "v41r27-panel-6-seed-412007"}


def file_hash(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def wilson_lower(successes: int, total: int) -> float:
    z = 1.959963984540054; proportion = successes / total; z_sq = z * z
    return ((proportion + z_sq / (2 * total)) - z * math.sqrt(
        proportion * (1 - proportion) / total + z_sq / (4 * total * total))) / (1 + z_sq / total)


def decision(workers: list[dict[str, Any]]) -> dict[str, Any]:
    passed = sum(row.get("pass") is True for row in workers)
    governance = sum(int(row.get("governance_violations", 1)) for row in workers)
    lower = wilson_lower(passed, 48)
    keep = len(workers) == 48 and passed == 48 and lower > 0.80 and governance == 0
    return {"qualification_keep": keep, "run_successes": passed, "run_total": 48,
            "wilson_95_lower_bound": lower, "governance_violations": governance}


def validate(artifact: Path, rgs_root: Path) -> dict[str, Any]:
    result_path = artifact / "qualification-result.json"; manifest = artifact / "MANIFEST.sha256"
    contract_path = artifact / "qualification-contract.json"; binding_path = artifact / "sentinel-binding.json"
    if not all(path.is_file() for path in (result_path, manifest, contract_path, binding_path)):
        return {"valid": False, "errors": ["qualification artifact files missing"]}
    result = json.loads(result_path.read_text()); errors: set[str] = set()
    body = {key: value for key, value in result.items() if key != "result_sha256"}
    if result.get("result_sha256") != CONTRACT.canonical_hash(body): errors.add("result_sha256")
    expected_contract = CONTRACT.expected_contract()
    if json.loads(contract_path.read_text()) != expected_contract or result.get("contract") != expected_contract:
        errors.add("contract")
    sentinel_path = artifact / "sentinel"; sentinel_report = SENTINEL.validate(sentinel_path, rgs_root)
    if not sentinel_report.get("valid") or sentinel_report.get("sentinel_keep") is not True:
        errors.add("sentinel")
    binding = json.loads(binding_path.read_text())
    if binding != {"sentinel_result_sha256": sentinel_report.get("result_sha256")}:
        errors.add("sentinel_binding")
    recovery_path = artifact / "recovery-binding.json"; recovery = recovery_path.is_file()
    constants = {"version": "mesh.astral_v41r27_agem_retention.v2",
                 "state_slice": "V41R27ProspectiveRetentionStabilityMechanism",
                 "classification": ("V41R27R3RecoveredQualificationComplete" if recovery
                                    else "V41R27QualificationComplete"), "worker_count": 48,
                 "imported_sentinel_workers": 9, "fresh_remaining_workers": 22 if recovery else 39,
                 "recovered_remaining_workers": 17 if recovery else 0,
                 "adaptive_stopping": False, "tune_opened": False, "assessment_opened": False,
                 "claim_ceiling": ("RemoteH100AGEMRecoveredQualificationV41R27R3" if recovery
                                   else "RemoteH100AGEMQualificationV41R27")}
    for key, value in constants.items():
        if result.get(key) != value: errors.add(key)
    sentinel_ids = {spec["run_id"] for spec in SENTINEL.sentinel_specs()}
    expected_specs = WORKER.expected_specs()
    expected_remaining = set(expected_specs) - sentinel_ids
    completion_ids = expected_remaining - RECOVERED_RUN_IDS
    if recovery:
        try: recovery_binding = json.loads(recovery_path.read_text())
        except (OSError, json.JSONDecodeError): recovery_binding = None
        expected_binding = {"partial_archive_sha256": PARTIAL_ARCHIVE_SHA256,
                            "recovered_run_ids": sorted(RECOVERED_RUN_IDS),
                            "completion_run_ids": [spec["run_id"] for spec in expected_specs.values()
                                                   if spec["run_id"] in completion_ids]}
        if recovery_binding != expected_binding: errors.add("recovery_binding")
    workers = []; summaries = []; expected_specs = WORKER.expected_specs()
    for run_id, spec in expected_specs.items():
        worker_dir = (sentinel_path / "workers" / run_id if run_id in sentinel_ids else
                      artifact / "recovered-workers" / run_id if recovery and run_id in RECOVERED_RUN_IDS else
                      artifact / "completion-workers" / run_id if recovery else
                      artifact / "remaining-workers" / run_id)
        report = WORKER.validate(worker_dir, rgs_root)
        if not report.get("valid"): errors.add(f"worker:{run_id}")
        try: worker = json.loads((worker_dir / "worker-result.json").read_text())
        except (OSError, json.JSONDecodeError): continue
        workers.append(worker); summaries.append({"run_id": run_id,
                                                  "result_sha256": worker.get("result_sha256"),
                                                  "pass": worker.get("pass")})
    if recovery:
        for root, expected, name in ((artifact / "recovered-workers", RECOVERED_RUN_IDS, "recovered_worker_census"),
                                     (artifact / "completion-workers", completion_ids, "completion_worker_census")):
            if not root.is_dir() or {path.name for path in root.iterdir()} != expected: errors.add(name)
    else:
        remaining_root = artifact / "remaining-workers"
        if not remaining_root.is_dir() or {path.name for path in remaining_root.iterdir()} != expected_remaining:
            errors.add("remaining_worker_census")
    if result.get("worker_results") != summaries: errors.add("worker_results")
    for key, value in decision(workers).items():
        actual = result.get(key)
        if isinstance(value, float):
            if not isinstance(actual, (int, float)) or not math.isclose(actual, value, rel_tol=1e-15):
                errors.add(f"decision:{key}")
        elif actual != value: errors.add(f"decision:{key}")
    if result.get("operational_envelope") != {"maximum_qualification_seconds": 14400,
                                               "maximum_worker_seconds": 600,
                                               "maximum_provider_spend_usd": 12.0,
                                               "restart_policy": "never"}:
        errors.add("operational_envelope")
    files = sorted((path for path in artifact.rglob("*") if path.is_file() and path != manifest),
                   key=lambda path: str(path.relative_to(artifact)))
    expected_manifest = "".join(
        f'{file_hash(path).removeprefix("sha256:")}  {path.relative_to(artifact)}\n' for path in files)
    if manifest.read_text() != expected_manifest: errors.add("manifest")
    source = result.get("source", {}); commit = source.get("rgs_commit", "")
    for key, relative in (("coordinator_sha256", ("scripts/run_v41r27r3_recovery.py" if recovery
                                                  else "scripts/run_v41r27_qualification.py")),
                          ("worker_sha256", "scripts/run_v41r27_worker.py"),
                          ("method_sha256", "mesh_brain/meshmodel/v41r27_agem_retention.py"),
                          ("requirements_sha256", "requirements-v41-h100-profile.txt")):
        try:
            content = subprocess.run(["git", "show", f"{commit}:{relative}"], cwd=rgs_root,
                                     check=True, capture_output=True).stdout
            if source.get(key) != "sha256:" + hashlib.sha256(content).hexdigest(): errors.add(key)
        except (subprocess.CalledProcessError, TypeError): errors.add(f"{key}:unavailable")
    return {"version": "astral.v41r27_qualification_validation.v1", "valid": not errors,
            "errors": sorted(errors),
            "qualification_keep": result.get("qualification_keep") if not errors else None,
            "worker_count": len(workers), "result_sha256": result.get("result_sha256"),
            "claim_ceiling": result.get("claim_ceiling") if not errors else None}


def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--artifact", type=Path, required=True)
    parser.add_argument("--rgs-root", type=Path, required=True); args = parser.parse_args()
    report = validate(args.artifact.resolve(), args.rgs_root.resolve())
    print(json.dumps(report, indent=2, sort_keys=True)); return 0 if report["valid"] else 1


if __name__ == "__main__": raise SystemExit(main())
