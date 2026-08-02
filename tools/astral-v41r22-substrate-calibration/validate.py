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
SPEC = importlib.util.spec_from_file_location("v41r22_base", BASE_PATH)
assert SPEC and SPEC.loader
BASE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BASE)

VERSION = "mesh.astral_v41r22_substrate_calibration.v1"
STATE_SLICE = "V41R22SingleCaseUpdateSubstrateCalibration"
CLAIM_CEILING = "RemoteH100SingleCaseSubstrateCalibrationV41R22"
ARMS = {
    "steps64_lr2e4": {"steps": 64, "learning_rate": 2.0e-4},
    "steps512_lr2e4": {"steps": 512, "learning_rate": 2.0e-4},
    "steps64_lr2e3": {"steps": 64, "learning_rate": 2.0e-3},
    "steps512_lr2e3": {"steps": 512, "learning_rate": 2.0e-3},
}
PASS_ORDER = ("steps64_lr2e4", "steps64_lr2e3", "steps512_lr2e4", "steps512_lr2e3")


def file_hash(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def expected_contract(instrument_sha256: str, case: dict[str, Any]) -> dict[str, Any]:
    body = {
        "version": "mesh.astral_v41r22_substrate_calibration_contract.v1",
        "state_slice": STATE_SLICE,
        "seed": 411013,
        "instrument_sha256": instrument_sha256,
        "case_index": 0,
        "case_id": case["case_id"],
        "prompt": case["composition_prompt"],
        "target": case["target"],
        "arms": ARMS,
        "pass_order": list(PASS_ORDER),
        "examples_per_step": 4,
        "identical_examples_batched_once": True,
        "loss_reduction": "batch_token_mean",
        "lora": {"rank": 8, "alpha": 16, "targets": "qkvo_all24"},
        "optimizer": "AdamW",
        "gradient_clip": 1.0,
        "checkpoint_reset_between_arms": True,
        "gates": {
            "selected_target": True,
            "target_margin_nats_minimum": 2.0,
            "last8_to_first8_loss_ratio_maximum": 0.10,
            "reload_exact": True,
        },
        "protected_accuracy_role": "collateral_diagnostic_only",
        "layer_selection": None,
        "tune_opened": False,
        "assessment_opened": False,
    }
    return {**body, "contract_sha256": BASE.canonical_hash(body)}


def valid_runtime(runtime: dict[str, Any]) -> bool:
    return (
        runtime.get("python") == "3.12.3"
        and runtime.get("torch") in {"2.10.0", "2.10.0+cu128"}
        and runtime.get("transformers") == "4.57.6"
        and runtime.get("peft") == "0.18.1"
        and runtime.get("cuda") == "12.8"
        and "H100" in str(runtime.get("gpu", "")).upper()
    )


def score_row_errors(row: Any, expected: dict[str, Any]) -> set[str]:
    errors: set[str] = set()
    if not isinstance(row, dict):
        return {"score_row_type"}
    for key in ("case_id", "prompt", "target", "candidates"):
        if row.get(key) != expected[key]: errors.add(f"score_row:{key}")
    scores = row.get("candidate_log_probabilities")
    if not isinstance(scores, dict) or set(scores) != set(expected["candidates"]):
        errors.add("score_row:scores")
    elif not all(isinstance(value, (int, float)) and math.isfinite(value) for value in scores.values()):
        errors.add("score_row:finite")
    selected = row.get("selected")
    if selected not in expected["candidates"] or row.get("correct") is not (selected == expected["target"]):
        errors.add("score_row:decision")
    return errors


def gate(packet: dict[str, Any]) -> dict[str, Any]:
    receipts = packet["update"]["receipts"]
    first = sum(row["loss"] for row in receipts[:8]) / 8
    last = sum(row["loss"] for row in receipts[-8:]) / 8
    ratio = last / first if first > 0 else math.inf
    scores = packet["exact_after"]["candidate_log_probabilities"]
    target = packet["exact_after"]["target"]
    margin = scores[target] - max(value for key, value in scores.items() if key != target)
    failures = []
    if packet["exact_after"].get("correct") is not True: failures.append("selected_target")
    if margin < 2.0: failures.append("target_margin")
    if ratio > 0.10: failures.append("loss_ratio")
    if packet["reload"].get("state_exact") is not True: failures.append("reload_exact")
    return {"pass": not failures, "errors": failures, "target_margin_nats": margin,
            "first8_mean_loss": first, "last8_mean_loss": last,
            "last8_to_first8_loss_ratio": ratio}


def decision(arms: dict[str, dict[str, Any]]) -> dict[str, Any]:
    gates = {name: gate(arms[name]) for name in ARMS}
    passing = [name for name in PASS_ORDER if gates[name]["pass"]]
    minimal = passing[0] if passing else None
    interpretations = {
        "steps64_lr2e4": "MultiCaseInterferenceSupported",
        "steps64_lr2e3": "LearningRateLimited",
        "steps512_lr2e4": "ExposureLimited",
        "steps512_lr2e3": "RateExposureInteractionRequired",
        None: "AttentionLoraSubstrateUnqualified",
    }
    return {"classification": "SingleCaseSubstrateCalibrationComplete",
            "interpretation": interpretations[minimal], "minimal_passing_arm": minimal,
            "arm_gates": gates}


def validate(artifact: Path, rgs_root: Path) -> dict[str, Any]:
    result_path = artifact / "calibration-result.json"
    manifest_path = artifact / "MANIFEST.sha256"
    adapters = {name: artifact / f"{name}-adapter-state.pt" for name in ARMS}
    if not result_path.is_file() or not manifest_path.is_file() or not all(path.is_file() for path in adapters.values()):
        return {"valid": False, "errors": ["calibration artifact files missing"]}
    result = json.loads(result_path.read_text())
    errors: set[str] = set()
    body = {key: value for key, value in result.items() if key != "result_sha256"}
    if result.get("result_sha256") != BASE.canonical_hash(body): errors.add("result_sha256")
    expected_top = {"version": VERSION, "state_slice": STATE_SLICE,
                    "classification": "SingleCaseSubstrateCalibrationComplete",
                    "tune_opened": False, "assessment_opened": False,
                    "claim_ceiling": CLAIM_CEILING}
    for key, value in expected_top.items():
        if result.get(key) != value: errors.add(key)
    instrument = BASE.INSTRUMENT.expected_packet()
    instrument_report = BASE.INSTRUMENT.validate(instrument)
    case = instrument["cases"][0]
    if not instrument_report.get("valid") or result.get("instrument_sha256") != instrument["instrument_sha256"]:
        errors.add("instrument")
    if result.get("contract") != expected_contract(instrument["instrument_sha256"], case): errors.add("contract")
    if not valid_runtime(result.get("runtime", {})): errors.add("runtime")
    model = result.get("model", {})
    if model.get("id") != BASE.MODEL or model.get("revision") != BASE.REVISION: errors.add("model")
    score_row = {"case_id": f'{case["case_id"]}-v41r22-exact', "prompt": case["composition_prompt"],
                 "target": case["target"], "candidates": list(case["candidates"])}
    if result.get("exact_score_row") != score_row: errors.add("exact_score_row")
    errors.update(f"exact_before:{item}" for item in score_row_errors(result.get("exact_before"), score_row))
    arms = result.get("arms")
    if not isinstance(arms, dict) or set(arms) != set(ARMS):
        errors.add("arm_census"); arms = {}
    for name, arm_contract in ARMS.items():
        packet = arms.get(name, {})
        if packet.get("arm") != name or packet.get("arm_contract") != arm_contract: errors.add(f"{name}:contract")
        errors.update(f"{name}:{item}" for item in score_row_errors(packet.get("exact_after"), score_row))
        for label in ("protected_before", "protected_after"):
            rows = packet.get(label, {}).get("rows")
            errors.update(f"{name}:{item}" for item in BASE.validate_rows(rows, context=None, label=label))
            if isinstance(rows, list) and len(rows) == 16:
                accuracy = sum(row.get("correct") is True for row in rows) / 16
                if packet.get(label, {}).get("accuracy") != accuracy: errors.add(f"{name}:{label}:accuracy")
        update = packet.get("update", {}); receipts = update.get("receipts")
        steps = arm_contract["steps"]
        if update.get("optimizer_steps") != steps or update.get("examples") != steps * 4 or not isinstance(receipts, list) or len(receipts) != steps:
            errors.add(f"{name}:budget"); receipts = []
        if receipts:
            for index, receipt in enumerate(receipts):
                if (receipt.get("step") != index or receipt.get("examples") != 4
                        or not isinstance(receipt.get("target_tokens"), int) or receipt["target_tokens"] <= 0
                        or not all(isinstance(receipt.get(key), (int, float)) and math.isfinite(receipt[key]) for key in ("loss", "gradient_norm"))):
                    errors.add(f"{name}:receipts"); break
            if update.get("target_tokens") != sum(row["target_tokens"] for row in receipts): errors.add(f"{name}:target_tokens")
        adapter = adapters[name]
        if update.get("adapter_file") != adapter.name or update.get("adapter_file_sha256") != file_hash(adapter): errors.add(f"{name}:adapter")
        reload = packet.get("reload", {})
        if reload.get("fresh_base_model") is not True or reload.get("state_exact") is not True or reload.get("state_sha256") != update.get("post_update_state_sha256"):
            errors.add(f"{name}:reload")
    if arms:
        expected_decision = decision(arms)
        for key, value in expected_decision.items():
            if result.get(key) != value: errors.add(f"decision:{key}")
    files = (result_path, *adapters.values())
    expected_manifest = "".join(file_hash(path).removeprefix("sha256:") + f"  {path.name}\n" for path in files)
    if manifest_path.read_text() != expected_manifest: errors.add("manifest")
    source = result.get("source", {}); commit = source.get("rgs_commit", "")
    mappings = (("runner_sha256", "scripts/run_v41r22_substrate_calibration.py"),
                ("method_sha256", "mesh_brain/meshmodel/v41r22_substrate_calibration.py"),
                ("instrument_sha256", "mesh_brain/meshmodel/v41r11_novelty_instrument.py"),
                ("requirements_sha256", "requirements-v41-h100-profile.txt"))
    for key, relative in mappings:
        try:
            content = subprocess.run(["git", "show", f"{commit}:{relative}"], cwd=rgs_root,
                                     check=True, capture_output=True).stdout
            if source.get(key) != "sha256:" + hashlib.sha256(content).hexdigest(): errors.add(key)
        except (subprocess.CalledProcessError, TypeError): errors.add(f"{key}:unavailable")
    return {"version": "astral.v41r22_substrate_calibration_validation.v1", "valid": not errors,
            "errors": sorted(errors), "classification": result.get("classification"),
            "interpretation": result.get("interpretation"), "minimal_passing_arm": result.get("minimal_passing_arm"),
            "result_sha256": result.get("result_sha256"),
            "claim_ceiling": result.get("claim_ceiling") if not errors else None}


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
