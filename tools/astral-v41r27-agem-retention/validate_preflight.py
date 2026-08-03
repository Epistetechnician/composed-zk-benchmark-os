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
CONTRACT_SPEC = importlib.util.spec_from_file_location("v41r27_preflight_contract", HERE / "validate.py")
assert CONTRACT_SPEC and CONTRACT_SPEC.loader
CONTRACT = importlib.util.module_from_spec(CONTRACT_SPEC); CONTRACT_SPEC.loader.exec_module(CONTRACT)
WORKER_SPEC = importlib.util.spec_from_file_location("v41r27_preflight_base", HERE / "validate_worker.py")
assert WORKER_SPEC and WORKER_SPEC.loader
WORKER = importlib.util.module_from_spec(WORKER_SPEC); WORKER_SPEC.loader.exec_module(WORKER)
PREFLIGHT_RESULT_VERSION = "mesh.astral_v41r27_agem_retention.v2"


def file_hash(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def expected_acquisition_rows() -> list[dict[str, Any]]:
    return [{"case_id": row["case_id"], "prompt": row["composition_prompt"],
             "target": row["target"], "candidates": row["candidates"]}
            for row in CONTRACT.acquisition()["cases"]]


def decision(acquisition: list[dict[str, Any]], protected: list[dict[str, Any]]) -> dict[str, Any]:
    protected_accuracy = sum(row.get("correct") is True for row in protected) / 256
    panel_incorrect = [sum(row.get("correct") is not True for row in acquisition[p * 4:p * 4 + 4])
                       for p in range(16)]
    errors = []
    if protected_accuracy != 1.0: errors.append("protected_accuracy")
    if any(count < 3 for count in panel_incorrect): errors.append("acquisition_novelty")
    return {"classification": "CampaignPreflightPassed" if not errors else "CampaignPreflightFailed",
            "errors": errors, "protected_accuracy": protected_accuracy,
            "panel_incorrect_acquisition_cases": panel_incorrect,
            "training_authorized": not errors}


def validate(artifact: Path, rgs_root: Path, *, result_name: str = "preflight-result.json",
             manifest_name: str = "MANIFEST.sha256") -> dict[str, Any]:
    result_path, manifest = artifact / result_name, artifact / manifest_name
    if not result_path.is_file() or not manifest.is_file():
        return {"valid": False, "errors": ["preflight artifact files missing"]}
    result = json.loads(result_path.read_text()); errors: set[str] = set()
    body = {key: value for key, value in result.items() if key != "result_sha256"}
    if result.get("result_sha256") != CONTRACT.canonical_hash(body): errors.add("result_sha256")
    for key, value in {"version": PREFLIGHT_RESULT_VERSION,
                       "state_slice": "V41R27ProspectiveRetentionStabilityMechanism",
                       "adapter_constructed": False, "optimizer_constructed": False,
                       "tune_opened": False, "assessment_opened": False,
                       "claim_ceiling": "RemoteH100AGEMCampaignPreflightV41R27"}.items():
        if result.get(key) != value: errors.add(key)
    if result.get("contract") != CONTRACT.expected_contract(): errors.add("contract")
    model = result.get("model", {})
    if model.get("id") != WORKER.BASE.BASE.MODEL or model.get("revision") != WORKER.BASE.BASE.REVISION: errors.add("model")
    runtime = result.get("runtime", {})
    if not (runtime.get("python") == "3.12.3" and runtime.get("torch") in {"2.10.0", "2.10.0+cu128"}
            and runtime.get("transformers") == "4.57.6" and runtime.get("cuda") == "12.8"
            and "H100" in str(runtime.get("gpu", "")).upper()): errors.add("runtime")
    expected_a = expected_acquisition_rows(); scored_a = result.get("acquisition_rows")
    if result.get("acquisition_score_rows") != expected_a: errors.add("acquisition_score_binding")
    if not isinstance(scored_a, list) or len(scored_a) != 64: errors.add("acquisition_census"); scored_a = []
    else:
        for index, row in enumerate(scored_a):
            errors.update(f"acquisition:{e}" for e in WORKER.BASE.BASE23.scored_errors(row, expected_a[index]))
    expected_p = CONTRACT.protected()["rows"]; scored_p = result.get("protected_rows")
    if not isinstance(scored_p, list) or len(scored_p) != 256: errors.add("protected_census"); scored_p = []
    else:
        errors.update(f"protected:{e}" for e in WORKER.BASE.BASE.validate_rows(scored_p, context=None, label="protected"))
        for index, row in enumerate(scored_p):
            if any(row.get(key) != expected_p[index][key] for key in ("case_id", "target", "candidates")): errors.add("protected_binding")
    if scored_a and scored_p:
        expected_decision = decision(scored_a, scored_p)
        for key, value in expected_decision.items():
            if result.get(key) != value: errors.add(f"decision:{key}")
    if manifest.read_text() != file_hash(result_path).removeprefix("sha256:") + "  preflight-result.json\n": errors.add("manifest")
    source = result.get("source", {}); commit = source.get("rgs_commit", "")
    for key, relative in (("runner_sha256", "scripts/run_v41r27_preflight.py"),
                          ("method_sha256", "mesh_brain/meshmodel/v41r27_agem_retention.py"),
                          ("requirements_sha256", "requirements-v41-h100-profile.txt")):
        try:
            content = subprocess.run(["git", "show", f"{commit}:{relative}"], cwd=rgs_root,
                                     check=True, capture_output=True).stdout
            if source.get(key) != "sha256:" + hashlib.sha256(content).hexdigest(): errors.add(key)
        except (subprocess.CalledProcessError, TypeError): errors.add(f"{key}:unavailable")
    return {"version": "astral.v41r27_preflight_artifact_validation.v1", "valid": not errors,
            "errors": sorted(errors), "classification": result.get("classification"),
            "training_authorized": result.get("training_authorized"),
            "result_sha256": result.get("result_sha256"),
            "claim_ceiling": result.get("claim_ceiling") if not errors else None}


def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--artifact", type=Path, required=True)
    parser.add_argument("--rgs-root", type=Path, required=True); args = parser.parse_args()
    report = validate(args.artifact.resolve(), args.rgs_root.resolve())
    print(json.dumps(report, indent=2, sort_keys=True)); return 0 if report["valid"] else 1


if __name__ == "__main__": raise SystemExit(main())
