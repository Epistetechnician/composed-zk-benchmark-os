from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import subprocess
from typing import Any


BASE_PATH = Path(__file__).parents[1] / "astral-v41r13-acquisition-pilot" / "validate.py"
SPEC = importlib.util.spec_from_file_location("v41r21_base", BASE_PATH)
assert SPEC and SPEC.loader
BASE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BASE)

VERSION = "mesh.astral_v41r21_learnability.v1"
STATE_SLICE = "V41R21AcquisitionLearnabilityDecomposition"
CLAIM_CEILING = "RemoteH100AcquisitionLearnabilityDecompositionV41R21"
ARMS = ("no_update", "direct_oracle", "two_edge", "two_edge_protected")
UPDATE_ARMS = ARMS[1:]
RELATIONS = ("bridge_relation", "terminal_relation", "end_to_end")
FLOORS = {
    "direct_oracle_end_to_end": 0.90,
    "two_edge_bridge_relation": 0.90,
    "two_edge_terminal_relation": 0.90,
    "two_edge_composition": 0.60,
    "two_edge_overall": 0.70,
    "protected_drop_maximum": 0.02,
}


def expected_contract(instrument_sha256: str) -> dict[str, Any]:
    body = {
        "version": "mesh.astral_v41r21_learnability_contract.v1",
        "state_slice": STATE_SLICE,
        "seed": 411013,
        "instrument_sha256": instrument_sha256,
        "arms": list(ARMS),
        "optimizer_steps_per_update_arm": 64,
        "examples_per_step": 4,
        "examples_per_update_arm": 256,
        "loss_reduction": "token_mean_then_equal_example_mean",
        "raw_target_tokens": "measured_not_artificially_padded",
        "checkpoint_reset_between_arms": True,
        "fresh_process_equivalent_reload": True,
        "lora": {"rank": 8, "alpha": 16, "targets": "qkvo_all24"},
        "optimizer": "AdamW",
        "learning_rate": 2.0e-4,
        "gradient_clip": 1.0,
        "layer_selection": None,
        "tune_opened": False,
        "assessment_opened": False,
        "floors": FLOORS,
    }
    return {**body, "contract_sha256": BASE.canonical_hash(body)}


def valid_torch_runtime(runtime: dict[str, Any]) -> bool:
    return runtime.get("torch") in {"2.10.0", "2.10.0+cu128"} and runtime.get("cuda") == "12.8"


def metric(rows: Any) -> dict[str, Any]:
    return BASE.metrics(rows)


def relation_accuracy(rows: Any, expected: list[dict[str, Any]]) -> tuple[float, list[str]]:
    errors: list[str] = []
    if not isinstance(rows, list) or len(rows) != 32:
        return 0.0, ["relation_census"]
    expected_by_id = {row["case_id"]: row for row in expected}
    for row in rows:
        reference = expected_by_id.get(row.get("case_id"))
        if reference is None:
            errors.append("relation_identity")
            continue
        if row.get("target") != reference["target"] or row.get("candidates") != reference["candidates"]:
            errors.append("relation_binding")
        probabilities = row.get("candidate_log_probabilities")
        if not isinstance(probabilities, dict) or set(probabilities) != set(reference["candidates"]):
            errors.append("relation_scores")
        selected = row.get("selected")
        if selected not in reference["candidates"] or row.get("correct") is not (selected == reference["target"]):
            errors.append("relation_decision")
    return sum(row.get("correct") is True for row in rows) / 32, sorted(set(errors))


def expected_relations(instrument: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    cases = instrument["cases"]
    result = {name: [] for name in RELATIONS}
    for index, case in enumerate(cases):
        block = (index // 4) * 4
        result["bridge_relation"].append({"case_id": f'{case["case_id"]}-bridge-relation', "target": case["bridge"], "candidates": [cases[block + offset]["bridge"] for offset in range(4)]})
        result["terminal_relation"].append({"case_id": f'{case["case_id"]}-terminal-relation', "target": case["target"], "candidates": list(case["candidates"])})
        result["end_to_end"].append({"case_id": f'{case["case_id"]}-end-to-end', "target": case["target"], "candidates": list(case["candidates"])})
    return result


def decision(arms: dict[str, dict[str, Any]]) -> dict[str, Any]:
    oracle = arms["direct_oracle"]
    two_edge = arms["two_edge"]
    replay = arms["two_edge_protected"]
    oracle_pass = oracle["relations"]["end_to_end"]["accuracy"] >= 0.90
    primitives_pass = two_edge["relations"]["bridge_relation"]["accuracy"] >= 0.90 and two_edge["relations"]["terminal_relation"]["accuracy"] >= 0.90
    two_edge_pass = two_edge["queries"]["metrics"]["overall_accuracy"] >= 0.70 and two_edge["queries"]["metrics"]["accuracy_by_class"]["composition"] >= 0.60
    replay_pass = replay["queries"]["metrics"]["overall_accuracy"] >= 0.70 and replay["queries"]["metrics"]["accuracy_by_class"]["composition"] >= 0.60 and replay["protected_before"]["accuracy"] - replay["protected_after"]["accuracy"] <= 0.02
    if not oracle_pass:
        interpretation = "UpdateSubstrateUnqualified"
    elif not primitives_pass:
        interpretation = "PrimitiveRelationAcquisitionBottleneck"
    elif not two_edge_pass:
        interpretation = "CompositionalObjectiveBottleneck"
    elif not replay_pass:
        interpretation = "ProtectedReplayInterference"
    else:
        interpretation = "PriorOptimizationSpecificFailure"
    return {"classification": "LearnabilityDecompositionComplete", "interpretation": interpretation, "gates": {"oracle_pass": oracle_pass, "primitives_pass": primitives_pass, "two_edge_pass": two_edge_pass, "two_edge_protected_pass": replay_pass}}


def file_hash(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def validate(artifact: Path, rgs_root: Path) -> dict[str, Any]:
    result_path = artifact / "learnability-result.json"
    manifest_path = artifact / "MANIFEST.sha256"
    adapter_paths = {arm: artifact / f"{arm}-adapter-state.pt" for arm in UPDATE_ARMS}
    if not result_path.is_file() or not manifest_path.is_file() or not all(path.is_file() for path in adapter_paths.values()):
        return {"valid": False, "errors": ["learnability artifact files missing"]}
    result = json.loads(result_path.read_text())
    errors: set[str] = set()
    body = {key: value for key, value in result.items() if key != "result_sha256"}
    if result.get("result_sha256") != BASE.canonical_hash(body): errors.add("result_sha256")
    for key, expected in {"version": VERSION, "state_slice": STATE_SLICE, "classification": "LearnabilityDecompositionComplete", "tune_opened": False, "assessment_opened": False, "claim_ceiling": CLAIM_CEILING}.items():
        if result.get(key) != expected: errors.add(key)
    instrument = result.get("instrument")
    instrument_report = BASE.INSTRUMENT.validate(instrument)
    if not instrument_report.get("valid"): errors.add("instrument")
    if result.get("contract") != expected_contract(instrument_report.get("instrument_sha256")): errors.add("contract")
    runtime = result.get("runtime", {})
    if not valid_torch_runtime(runtime): errors.add("runtime:torch")
    for key, expected in {"python": "3.12.3", "transformers": "4.57.6", "peft": "0.18.1", "cuda": "12.8"}.items():
        if runtime.get(key) != expected: errors.add(f"runtime:{key}")
    if "H100" not in str(runtime.get("gpu", "")).upper(): errors.add("runtime:gpu")
    model = result.get("model", {})
    if model.get("id") != BASE.MODEL or model.get("revision") != BASE.REVISION: errors.add("model")
    arms = result.get("arms")
    if not isinstance(arms, dict) or set(arms) != set(ARMS):
        errors.add("arm_census")
        arms = {}
    expected_relation_rows = expected_relations(instrument) if instrument_report.get("valid") else {name: [] for name in RELATIONS}
    for arm in ARMS:
        packet = arms.get(arm, {})
        query_rows = packet.get("queries", {}).get("rows")
        errors.update(f"{arm}:{error}" for error in BASE.validate_rows(query_rows, context=False, label="queries"))
        try:
            if packet.get("queries", {}).get("metrics") != metric(query_rows): errors.add(f"{arm}:query_metrics")
        except (TypeError, ValueError): errors.add(f"{arm}:query_metrics")
        for relation in RELATIONS:
            relation_packet = packet.get("relations", {}).get(relation, {})
            accuracy, relation_errors = relation_accuracy(relation_packet.get("rows"), expected_relation_rows[relation])
            if relation_packet.get("accuracy") != accuracy: errors.add(f"{arm}:{relation}:accuracy")
            errors.update(f"{arm}:{relation}:{error}" for error in relation_errors)
        for label in ("protected_before", "protected_after"):
            rows = packet.get(label, {}).get("rows")
            errors.update(f"{arm}:{error}" for error in BASE.validate_rows(rows, context=None, label=label))
            if isinstance(rows, list) and len(rows) == 16:
                accuracy = sum(row.get("correct") is True for row in rows) / 16
                if packet.get(label, {}).get("accuracy") != accuracy: errors.add(f"{arm}:{label}:accuracy")
        update = packet.get("update", {})
        if arm == "no_update":
            if update != {"optimizer_steps": 0, "examples": 0, "target_tokens": 0, "receipts": []}: errors.add("no_update:update")
        else:
            receipts = update.get("receipts")
            if update.get("optimizer_steps") != 64 or update.get("examples") != 256 or not isinstance(receipts, list) or len(receipts) != 64: errors.add(f"{arm}:update_budget")
            elif any(receipt.get("step") != index or receipt.get("microbatch_count") != 4 or receipt.get("microbatch_weights") != [0.25] * 4 or not isinstance(receipt.get("target_tokens"), int) or receipt.get("target_tokens") <= 0 or not math.isfinite(receipt.get("loss", float("nan"))) for index, receipt in enumerate(receipts)): errors.add(f"{arm}:receipts")
            adapter = adapter_paths[arm]
            if update.get("adapter_file") != adapter.name or update.get("adapter_file_sha256") != file_hash(adapter): errors.add(f"{arm}:adapter_file")
            if update.get("post_update_state_sha256") != packet.get("reload", {}).get("state_sha256") or packet.get("reload", {}).get("state_exact") is not True: errors.add(f"{arm}:reload")
    if arms:
        expected_decision = decision(arms)
        for key, value in expected_decision.items():
            if result.get(key) != value: errors.add(f"decision:{key}")
    expected_manifest = "".join(file_hash(path).removeprefix("sha256:") + f"  {path.name}\n" for path in (result_path, *adapter_paths.values()))
    if manifest_path.read_text() != expected_manifest: errors.add("manifest")
    source = result.get("source", {}); commit = source.get("rgs_commit", "")
    for key, relative in (("runner_sha256", "scripts/run_v41r21_learnability.py"), ("method_sha256", "mesh_brain/meshmodel/v41r21_learnability.py"), ("instrument_sha256", "mesh_brain/meshmodel/v41r11_novelty_instrument.py"), ("requirements_sha256", "requirements-v41-h100-profile.txt")):
        try:
            content = subprocess.run(["git", "show", f"{commit}:{relative}"], cwd=rgs_root, check=True, capture_output=True).stdout
            if source.get(key) != "sha256:" + hashlib.sha256(content).hexdigest(): errors.add(key)
        except (subprocess.CalledProcessError, TypeError): errors.add(f"{key}:unavailable")
    return {"version": "astral.v41r21_learnability_validation.v1", "valid": not errors, "errors": sorted(errors), "classification": result.get("classification"), "interpretation": result.get("interpretation"), "result_sha256": result.get("result_sha256"), "claim_ceiling": result.get("claim_ceiling") if not errors else None}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact", type=Path, required=True)
    parser.add_argument("--rgs-root", type=Path, required=True)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    report = validate(args.artifact.resolve(), args.rgs_root.resolve())
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.report: args.report.write_text(text)
    print(text, end="")
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
