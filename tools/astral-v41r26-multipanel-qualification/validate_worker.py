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
SPEC = importlib.util.spec_from_file_location("v41r26_contract", HERE / "validate.py")
assert SPEC and SPEC.loader
CONTRACT = importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(CONTRACT)
BASE_PATH = Path(__file__).parents[1] / "astral-v41r25-disjoint-replay" / "validate_artifact.py"
BASE_SPEC = importlib.util.spec_from_file_location("v41r26_worker_base", BASE_PATH)
assert BASE_SPEC and BASE_SPEC.loader
BASE = importlib.util.module_from_spec(BASE_SPEC); BASE_SPEC.loader.exec_module(BASE)


def file_hash(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def expected_specs() -> dict[str, dict[str, Any]]:
    packet = CONTRACT.expected_contract(); result = {}
    for panel in packet["panels"]:
        for seed in packet["seeds"]:
            run_id = f'{panel["panel_id"]}-seed-{seed}'
            result[run_id] = {"run_id": run_id, "panel_id": panel["panel_id"], "seed": seed,
                              "contract_sha256": packet["contract_sha256"],
                              "acquisition_case_ids": panel["acquisition_case_ids"],
                              "protected_case_ids": panel["protected_case_ids"]}
    return result


def validate(artifact: Path, rgs_root: Path) -> dict[str, Any]:
    result_path = artifact / "worker-result.json"; adapter = artifact / "worker-adapter-state.pt"
    manifest = artifact / "MANIFEST.sha256"
    if not all(path.is_file() for path in (result_path, adapter, manifest)):
        return {"valid": False, "errors": ["worker artifact files missing"]}
    result = json.loads(result_path.read_text()); errors: set[str] = set()
    body = {key: value for key, value in result.items() if key != "result_sha256"}
    if result.get("result_sha256") != CONTRACT.canonical_hash(body): errors.add("result_sha256")
    expected_constants = {"version": "mesh.astral_v41r26_multipanel_qualification.v1",
                          "state_slice": "V41R26MultiPanelReplayQualificationDesign",
                          "classification": "V41R26WorkerComplete", "status": "completed",
                          "tune_opened": False, "assessment_opened": False,
                          "claim_ceiling": "RemoteH100MultiPanelReplayWorkerV41R26"}
    for key, value in expected_constants.items():
        if result.get(key) != value: errors.add(key)
    specs = expected_specs(); run_id = result.get("run_id"); spec = specs.get(run_id)
    if spec is None or result.get("run_spec") != spec or result.get("seed") != spec.get("seed"): errors.add("run_spec")
    if result.get("contract") != CONTRACT.expected_contract(): errors.add("contract")
    if not BASE.BASE23.valid_runtime(result.get("runtime", {})): errors.add("runtime")
    model = result.get("model", {})
    if model.get("id") != BASE.BASE.MODEL or model.get("revision") != BASE.BASE.REVISION: errors.add("model")
    if spec is not None:
        panel = int(spec["panel_id"].rsplit("-", 1)[1]); acquisition = CONTRACT.expected_acquisition()["cases"]
        protected = CONTRACT.expected_protected()["rows"]; selected = acquisition[panel * 4:panel * 4 + 4]
        protected_selected = protected[panel * 16:panel * 16 + 16]
        score_rows = [{"case_id": f'{row["case_id"]}-v41r26-exact', "prompt": row["composition_prompt"],
                       "target": row["target"], "candidates": row["candidates"]} for row in selected]
        if result.get("case_ids") != spec["acquisition_case_ids"] or result.get("exact_score_rows") != score_rows: errors.add("case_binding")
        for label, rows in (("before", result.get("exact_before_rows")),
                            ("after", result.get("candidate", {}).get("exact_after_rows"))):
            if not isinstance(rows, list) or len(rows) != 4: errors.add(f"{label}_census")
            else:
                for index, row in enumerate(rows): errors.update(f"{label}:{e}" for e in BASE.BASE23.scored_errors(row, score_rows[index]))
        candidate = result.get("candidate", {}); receipts = candidate.get("update", {}).get("receipts")
        schedule = [index for _ in range(64) for index in range(panel * 4, panel * 4 + 4)]
        if not isinstance(receipts, list) or len(receipts) != 256: errors.add("receipt_census"); receipts = []
        for step, receipt in enumerate(receipts):
            expected_protected = [panel * 16 + ((step % 4) * 4 + j) % 16 for j in range(4)]
            index = schedule[step]
            if receipt.get("step") != step or receipt.get("case_index") != index or receipt.get("case_id") != acquisition[index]["case_id"] or receipt.get("protected_indices") != expected_protected: errors.add("receipt_binding")
            values = (receipt.get("acquisition_loss"), receipt.get("protected_loss"), receipt.get("weighted_loss"), receipt.get("gradient_norm"))
            if any(not isinstance(value, (int, float)) or not math.isfinite(value) for value in values): errors.add("receipt_finite")
            elif abs(receipt["weighted_loss"] - (0.75 * receipt["acquisition_loss"] + 0.25 * receipt["protected_loss"])) > 1e-9: errors.add("receipt_weight")
        for label in ("protected_before", "protected_after"):
            rows = candidate.get(label, {}).get("rows"); errors.update(f"{label}:{e}" for e in BASE.BASE.validate_rows(rows, context=None, label=label))
            if isinstance(rows, list) and len(rows) == 16:
                for index, row in enumerate(rows):
                    if any(row.get(key) != protected_selected[index][key] for key in ("case_id", "target", "candidates")): errors.add(f"{label}:binding")
                accuracy = sum(row.get("correct") is True for row in rows) / 16
                if candidate[label].get("accuracy") != accuracy: errors.add(f"{label}:accuracy")
        update, reload = candidate.get("update", {}), candidate.get("reload", {})
        if update.get("optimizer_steps") != 256 or result.get("fresh_adapter") is not True or result.get("fresh_optimizer") is not True: errors.add("state_reset")
        if update.get("adapter_file") != adapter.name or update.get("adapter_file_sha256") != file_hash(adapter): errors.add("adapter")
        if reload.get("state_exact") is not True or reload.get("state_sha256") != update.get("post_update_state_sha256"): errors.add("reload")
        preflight = result.get("preflight", {})
        if preflight.get("protected_accuracy") != 1.0 or preflight.get("incorrect_acquisition_cases", 0) < 3 or preflight.get("pass") is not True: errors.add("preflight")
        gates = {case_id: BASE.gate(packet["exact_after"], packet["receipts"], reload.get("state_exact") is True)
                 for case_id, packet in candidate.get("cases", {}).items()}
        passing = sum(gate["pass"] for gate in gates.values()); protected_accuracy = candidate.get("protected_after", {}).get("accuracy")
        worker_pass = passing == 4 and isinstance(protected_accuracy, (int, float)) and protected_accuracy >= 0.98 and reload.get("state_exact") is True
        for key, value in {"case_gates": gates, "acquisition_cases_passing": passing,
                           "protected_accuracy": protected_accuracy, "pass": worker_pass}.items():
            if result.get(key) != value: errors.add(f"decision:{key}")
    expected_manifest = "".join(file_hash(path).removeprefix("sha256:") + f"  {path.name}\n" for path in (result_path, adapter))
    if manifest.read_text() != expected_manifest: errors.add("manifest")
    source = result.get("source", {}); commit = source.get("rgs_commit", "")
    for key, relative in (("runner_sha256", "scripts/run_v41r26_worker.py"),
                          ("method_sha256", "mesh_brain/meshmodel/v41r26_multipanel_qualification.py"),
                          ("instrument_sha256", "mesh_brain/meshmodel/v41r26_multipanel_qualification.py"),
                          ("requirements_sha256", "requirements-v41-h100-profile.txt")):
        try:
            content = subprocess.run(["git", "show", f"{commit}:{relative}"], cwd=rgs_root,
                                     check=True, capture_output=True).stdout
            if source.get(key) != "sha256:" + hashlib.sha256(content).hexdigest(): errors.add(key)
        except (subprocess.CalledProcessError, TypeError): errors.add(f"{key}:unavailable")
    return {"version": "astral.v41r26_worker_artifact_validation.v1", "valid": not errors,
            "errors": sorted(errors), "run_id": run_id, "pass": result.get("pass"),
            "result_sha256": result.get("result_sha256"),
            "claim_ceiling": result.get("claim_ceiling") if not errors else None}


def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--artifact", type=Path, required=True)
    parser.add_argument("--rgs-root", type=Path, required=True); args = parser.parse_args()
    report = validate(args.artifact.resolve(), args.rgs_root.resolve())
    print(json.dumps(report, indent=2, sort_keys=True)); return 0 if report["valid"] else 1


if __name__ == "__main__": raise SystemExit(main())
