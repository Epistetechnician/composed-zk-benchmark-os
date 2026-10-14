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
SPEC = importlib.util.spec_from_file_location("v41r23_base", BASE_PATH)
assert SPEC and SPEC.loader
BASE = importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(BASE)

VERSION = "mesh.astral_v41r23_multicase_interference.v1"
STATE_SLICE = "V41R23MultiCaseInterferenceIsolation"
CLAIM_CEILING = "RemoteH100FourCaseInterferenceIsolationV41R23"
INDICES = (0, 1, 2, 3)
STEPS = 64


def file_hash(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def expected_contract(instrument: dict[str, Any]) -> dict[str, Any]:
    cases = [instrument["cases"][index] for index in INDICES]
    body = {
        "version": "mesh.astral_v41r23_multicase_interference_contract.v1",
        "state_slice": STATE_SLICE, "seed": 411013,
        "instrument_sha256": instrument["instrument_sha256"], "case_indices": list(INDICES),
        "case_bindings": [{"case_id": case["case_id"], "prompt": case["composition_prompt"],
                           "target": case["target"], "candidates": list(case["candidates"])} for case in cases],
        "arms": {"shared": {"adapter_count": 1, "steps": 256,
                              "round_robin_case_order": list(INDICES)},
                 "modular": {"adapter_count": 4, "steps_per_adapter": 64,
                              "case_to_adapter": "one_to_one_oracle_upper_bound"}},
        "examples_per_step": 4, "identical_case_examples_batched_once": True,
        "examples_per_case_per_arm": 256, "optimizer_steps_per_arm": 256,
        "loss_reduction": "batch_token_mean",
        "lora": {"rank": 8, "alpha": 16, "targets": "qkvo_all24"},
        "optimizer": "AdamW", "learning_rate": 2.0e-4, "gradient_clip": 1.0,
        "checkpoint_reset_between_arms_and_modules": True,
        "gates": {"case_target_top1": True, "case_margin_nats_minimum": 2.0,
                  "case_last8_to_first8_loss_ratio_maximum": 0.10, "reload_exact": True,
                  "modular_all_cases_pass": True,
                  "modular_minus_shared_passing_cases_minimum": 2,
                  "maximum_protected_retention_drop": 0.02},
        "protected_evaluation": "same_adapter_worst_case_not_base_bypass",
        "oracle_module_routing": True, "layer_selection": None,
        "tune_opened": False, "assessment_opened": False,
    }
    return {**body, "contract_sha256": BASE.canonical_hash(body)}


def expected_score_rows(instrument: dict[str, Any]) -> list[dict[str, Any]]:
    return [{"case_id": f'{case["case_id"]}-v41r23-exact', "prompt": case["composition_prompt"],
             "target": case["target"], "candidates": list(case["candidates"])}
            for case in (instrument["cases"][index] for index in INDICES)]


def scored_errors(row: Any, expected: dict[str, Any]) -> set[str]:
    if not isinstance(row, dict): return {"type"}
    errors = {key for key in ("case_id", "target", "candidates") if row.get(key) != expected[key]}
    scores = row.get("candidate_log_probabilities")
    if not isinstance(scores, dict) or set(scores) != set(expected["candidates"]): errors.add("scores")
    elif (any(not isinstance(value, (int, float)) or not math.isfinite(value) for value in scores.values())
          or abs(sum(math.exp(value) for value in scores.values()) - 1.0) > 1.0e-5): errors.add("probabilities")
    else:
        selected = min(expected["candidates"], key=lambda candidate: (-scores[candidate], candidate))
        if row.get("selected") != selected or row.get("correct") is not (selected == expected["target"]): errors.add("decision")
    return errors


def gate(score: dict[str, Any], receipts: list[dict[str, Any]], reload_exact: bool) -> dict[str, Any]:
    first = sum(row["loss"] for row in receipts[:8]) / 8
    last = sum(row["loss"] for row in receipts[-8:]) / 8
    ratio = last / first if first > 0 else math.inf
    scores, target = score["candidate_log_probabilities"], score["target"]
    margin = scores[target] - max(value for key, value in scores.items() if key != target)
    errors = []
    if score.get("correct") is not True: errors.append("selected_target")
    if margin < 2.0: errors.append("target_margin")
    if ratio > 0.10: errors.append("loss_ratio")
    if reload_exact is not True: errors.append("reload_exact")
    return {"pass": not errors, "errors": errors, "target_margin_nats": margin,
            "first8_mean_loss": first, "last8_mean_loss": last,
            "last8_to_first8_loss_ratio": ratio}


def decision(shared: dict[str, Any], modular: dict[str, Any]) -> dict[str, Any]:
    shared_gates = {case_id: gate(packet["exact_after"], packet["receipts"], shared["reload"]["state_exact"])
                    for case_id, packet in shared["cases"].items()}
    modular_gates = {case_id: gate(packet["exact_after"], packet["receipts"], packet["reload"]["state_exact"])
                     for case_id, packet in modular["cases"].items()}
    shared_count = sum(value["pass"] for value in shared_gates.values())
    modular_count = sum(value["pass"] for value in modular_gates.values()); effect = modular_count - shared_count
    shared_drop = shared["protected_before"]["accuracy"] - shared["protected_after"]["accuracy"]
    modular_drops = {case_id: packet["protected_before"]["accuracy"] - packet["protected_after"]["accuracy"]
                     for case_id, packet in modular["cases"].items()}
    max_drop = max(modular_drops.values()); retention = max_drop <= 0.02
    keep = modular_count == 4 and effect >= 2 and retention
    if modular_count < 4: interpretation = "HeterogeneousSingleCaseLearnabilityBlocked"
    elif effect >= 2 and not retention: interpretation = "ModularAcquisitionOnlyRetentionBlocked"
    elif keep: interpretation = "RecoverableModularCandidateKept"
    elif shared_count == 4 and shared_drop <= 0.02: interpretation = "SharedFourCaseCandidate"
    elif shared_count == 4: interpretation = "FourCaseAcquisitionRetentionBlocked"
    else: interpretation = "InconclusiveSharedModularDifference"
    return {"classification": "MultiCaseInterferenceIsolationComplete", "interpretation": interpretation,
            "primary_metric_modular_minus_shared_passing_cases": effect,
            "shared_passing_cases": shared_count, "modular_passing_cases": modular_count,
            "shared_case_gates": shared_gates, "modular_case_gates": modular_gates,
            "shared_protected_drop": shared_drop, "modular_protected_drops": modular_drops,
            "modular_maximum_protected_drop": max_drop, "retention_pass": retention,
            "candidate_keep": keep}


def valid_runtime(runtime: dict[str, Any]) -> bool:
    return (runtime.get("python") == "3.12.3" and runtime.get("torch") in {"2.10.0", "2.10.0+cu128"}
            and runtime.get("transformers") == "4.57.6" and runtime.get("peft") == "0.18.1"
            and runtime.get("cuda") == "12.8" and "H100" in str(runtime.get("gpu", "")).upper())


def validate_receipts(receipts: Any, schedule: list[int], cases: list[dict[str, Any]]) -> set[str]:
    if not isinstance(receipts, list) or len(receipts) != len(schedule): return {"census"}
    errors = set()
    for step, (receipt, index) in enumerate(zip(receipts, schedule, strict=True)):
        if receipt.get("step") != step or receipt.get("case_index") != index or receipt.get("case_id") != cases[index]["case_id"] or receipt.get("examples") != 4:
            errors.add("binding")
        if not isinstance(receipt.get("target_tokens"), int) or receipt["target_tokens"] <= 0: errors.add("tokens")
        if any(not isinstance(receipt.get(key), (int, float)) or not math.isfinite(receipt[key]) for key in ("loss", "gradient_norm")): errors.add("finite")
    return errors


def validate(artifact: Path, rgs_root: Path) -> dict[str, Any]:
    result_path, manifest_path = artifact / "interference-result.json", artifact / "MANIFEST.sha256"
    instrument = BASE.INSTRUMENT.expected_packet(); cases = instrument["cases"]
    case_ids = [cases[index]["case_id"] for index in INDICES]
    adapters = {"shared": artifact / "shared-adapter-state.pt",
                **{case_id: artifact / f"modular-{case_id}-adapter-state.pt" for case_id in case_ids}}
    if not result_path.is_file() or not manifest_path.is_file() or not all(path.is_file() for path in adapters.values()):
        return {"valid": False, "errors": ["interference artifact files missing"]}
    result = json.loads(result_path.read_text()); errors: set[str] = set()
    body = {key: value for key, value in result.items() if key != "result_sha256"}
    if result.get("result_sha256") != BASE.canonical_hash(body): errors.add("result_sha256")
    for key, value in {"version": VERSION, "state_slice": STATE_SLICE,
                       "classification": "MultiCaseInterferenceIsolationComplete", "tune_opened": False,
                       "assessment_opened": False, "claim_ceiling": CLAIM_CEILING}.items():
        if result.get(key) != value: errors.add(key)
    if result.get("instrument_sha256") != instrument["instrument_sha256"]: errors.add("instrument")
    if result.get("contract") != expected_contract(instrument): errors.add("contract")
    if result.get("case_ids") != case_ids or result.get("exact_score_rows") != expected_score_rows(instrument): errors.add("case_binding")
    if not valid_runtime(result.get("runtime", {})): errors.add("runtime")
    model = result.get("model", {})
    if model.get("id") != BASE.MODEL or model.get("revision") != BASE.REVISION: errors.add("model")
    expected_rows = expected_score_rows(instrument)
    before = result.get("exact_before_rows")
    if not isinstance(before, list) or len(before) != 4: errors.add("before_census")
    else:
        for position, row in enumerate(before): errors.update(f"before:{e}" for e in scored_errors(row, expected_rows[position]))
    shared = result.get("shared", {}); shared_schedule = [index for _ in range(STEPS) for index in INDICES]
    if shared.get("schedule") != shared_schedule: errors.add("shared:schedule")
    errors.update(f"shared:receipt:{e}" for e in validate_receipts(shared.get("update", {}).get("receipts"), shared_schedule, cases))
    shared_rows = shared.get("exact_after_rows")
    if not isinstance(shared_rows, list) or len(shared_rows) != 4: errors.add("shared:score_census")
    else:
        for position, row in enumerate(shared_rows): errors.update(f"shared:score:{e}" for e in scored_errors(row, expected_rows[position]))
    if set(shared.get("cases", {})) != set(case_ids): errors.add("shared:case_census")
    else:
        for position, case_id in enumerate(case_ids):
            packet = shared["cases"][case_id]
            if packet.get("exact_after") != shared_rows[position] or packet.get("receipts") != [r for r in shared["update"]["receipts"] if r["case_id"] == case_id]: errors.add(f"shared:{case_id}:projection")
    for label in ("protected_before", "protected_after"):
        rows = shared.get(label, {}).get("rows"); errors.update(f"shared:{e}" for e in BASE.validate_rows(rows, context=None, label=label))
        if isinstance(rows, list) and len(rows) == 16 and shared[label].get("accuracy") != sum(row.get("correct") is True for row in rows) / 16: errors.add(f"shared:{label}:accuracy")
    update = shared.get("update", {}); reload = shared.get("reload", {})
    if update.get("optimizer_steps") != 256 or update.get("examples") != 1024 or update.get("target_tokens") != sum(r["target_tokens"] for r in update.get("receipts", [])): errors.add("shared:budget")
    if update.get("adapter_file") != adapters["shared"].name or update.get("adapter_file_sha256") != file_hash(adapters["shared"]): errors.add("shared:adapter")
    if reload.get("fresh_base_model") is not True or reload.get("state_exact") is not True or reload.get("state_sha256") != update.get("post_update_state_sha256"): errors.add("shared:reload")
    modular = result.get("modular", {}); modules = modular.get("cases", {})
    if set(modules) != set(case_ids): errors.add("modular:case_census"); modules = {}
    initial_hashes = {update.get("initial_state_sha256")}
    for position, (index, case_id) in enumerate(zip(INDICES, case_ids, strict=True)):
        packet = modules.get(case_id, {}); schedule = [index] * STEPS
        if packet.get("schedule") != schedule: errors.add(f"modular:{case_id}:schedule")
        receipts = packet.get("update", {}).get("receipts")
        errors.update(f"modular:{case_id}:receipt:{e}" for e in validate_receipts(receipts, schedule, cases))
        errors.update(f"modular:{case_id}:score:{e}" for e in scored_errors(packet.get("exact_after"), expected_rows[position]))
        if packet.get("exact_after_rows") != [packet.get("exact_after")] or packet.get("receipts") != receipts: errors.add(f"modular:{case_id}:projection")
        for label in ("protected_before", "protected_after"):
            rows = packet.get(label, {}).get("rows"); errors.update(f"modular:{case_id}:{e}" for e in BASE.validate_rows(rows, context=None, label=label))
            if isinstance(rows, list) and len(rows) == 16 and packet[label].get("accuracy") != sum(row.get("correct") is True for row in rows) / 16: errors.add(f"modular:{case_id}:{label}:accuracy")
        module_update, module_reload = packet.get("update", {}), packet.get("reload", {})
        if module_update.get("optimizer_steps") != 64 or module_update.get("examples") != 256 or module_update.get("target_tokens") != sum(r["target_tokens"] for r in receipts or []): errors.add(f"modular:{case_id}:budget")
        if module_update.get("adapter_file") != adapters[case_id].name or module_update.get("adapter_file_sha256") != file_hash(adapters[case_id]): errors.add(f"modular:{case_id}:adapter")
        if module_reload.get("fresh_base_model") is not True or module_reload.get("state_exact") is not True or module_reload.get("state_sha256") != module_update.get("post_update_state_sha256"): errors.add(f"modular:{case_id}:reload")
        initial_hashes.add(module_update.get("initial_state_sha256"))
    if len(initial_hashes) != 1: errors.add("initial_state_reset")
    if modules:
        expected_decision = decision(shared, modular)
        for key, value in expected_decision.items():
            if result.get(key) != value: errors.add(f"decision:{key}")
    files = [result_path, adapters["shared"], *(adapters[case_id] for case_id in case_ids)]
    if manifest_path.read_text() != "".join(file_hash(path).removeprefix("sha256:") + f"  {path.name}\n" for path in files): errors.add("manifest")
    source = result.get("source", {}); commit = source.get("rgs_commit", "")
    mappings = (("runner_sha256", "scripts/run_v41r23_multicase_interference.py"),
                ("method_sha256", "mesh_brain/meshmodel/v41r23_multicase_interference.py"),
                ("instrument_sha256", "mesh_brain/meshmodel/v41r11_novelty_instrument.py"),
                ("requirements_sha256", "requirements-v41-h100-profile.txt"))
    for key, relative in mappings:
        try:
            content = subprocess.run(["git", "show", f"{commit}:{relative}"], cwd=rgs_root, check=True, capture_output=True).stdout
            if source.get(key) != "sha256:" + hashlib.sha256(content).hexdigest(): errors.add(key)
        except (subprocess.CalledProcessError, TypeError): errors.add(f"{key}:unavailable")
    return {"version": "astral.v41r23_multicase_interference_validation.v1", "valid": not errors,
            "errors": sorted(errors), "classification": result.get("classification"),
            "interpretation": result.get("interpretation"),
            "primary_metric": result.get("primary_metric_modular_minus_shared_passing_cases"),
            "candidate_keep": result.get("candidate_keep"), "result_sha256": result.get("result_sha256"),
            "claim_ceiling": result.get("claim_ceiling") if not errors else None}


def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--artifact", type=Path, required=True)
    parser.add_argument("--rgs-root", type=Path, required=True); parser.add_argument("--report", type=Path)
    args = parser.parse_args(); report = validate(args.artifact.resolve(), args.rgs_root.resolve())
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.report: args.report.write_text(text)
    print(text, end=""); return 0 if report["valid"] else 1


if __name__ == "__main__": raise SystemExit(main())
