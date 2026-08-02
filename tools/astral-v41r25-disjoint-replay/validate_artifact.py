from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import subprocess
from typing import Any


BASE_PATH = Path(__file__).parents[1] / "astral-v41r23-multicase-interference" / "validate.py"
SPEC = importlib.util.spec_from_file_location("v41r25_base", BASE_PATH)
assert SPEC and SPEC.loader
BASE23 = importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(BASE23)
BASE = BASE23.BASE

VERSION = "mesh.astral_v41r25_disjoint_protected_replay.v1"
STATE_SLICE = "V41R25DisjointProtectedReplayReplication"
CLAIM_CEILING = "RemoteH100DisjointProtectedReplayDevelopmentV41R25"
INDICES = (4, 5, 6, 7)
PROTECTED_INDICES = tuple(range(16, 32))
CORPUS_SHA256 = "sha256:ab1c096ae51f72db83a0680f760cf3670da699b0745668272a8dc2cd74c85b3c"
PRIOR_RESULT_SHA256 = "sha256:e7ac404080c2c75a977c956420ff3934dc563aadd75fcae94dd4361f36e52eb5"


def file_hash(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def expected_contract(instrument: dict[str, Any]) -> dict[str, Any]:
    cases = [instrument["cases"][i] for i in INDICES]
    protected = expected_protected_rows()
    body = {"version": "mesh.astral_v41r25_disjoint_protected_replay_contract.v1",
            "state_slice": STATE_SLICE, "seed": 411013,
            "instrument_sha256": instrument["instrument_sha256"], "corpus_sha256": CORPUS_SHA256,
            "acquisition_case_indices": list(INDICES), "protected_case_indices": list(PROTECTED_INDICES),
            "acquisition_case_ids": [row["case_id"] for row in cases],
            "protected_case_ids": [row["case_id"] for row in protected],
            "prior_result": {"version": "V41R24R2", "result_sha256": PRIOR_RESULT_SHA256,
                             "protected_case_indices": list(range(16)), "protected_accuracy": 0.875},
            "optimizer_steps": 256, "steps_per_acquisition_case": 64,
            "examples_per_panel_per_step": 4, "protected_schedule": "cyclic_four_of_sixteen",
            "panel_weights": {"acquisition": 0.75, "protected": 0.25},
            "loss_reduction": "token_mean_within_panel_then_frozen_panel_weight",
            "lora": {"rank": 8, "alpha": 16, "targets": "qkvo_all24"}, "optimizer": "AdamW",
            "learning_rate": 2.0e-4, "gradient_clip": 1.0,
            "gates": {"all_four_acquisition_cases_pass": True, "case_margin_nats_minimum": 2.0,
                      "case_last8_to_first8_loss_ratio_maximum": 0.10,
                      "protected_accuracy_minimum": 0.98, "reload_exact": True},
            "freshness": {"acquisition_disjoint_from_v41r24": True,
                          "protected_disjoint_from_v41r24": True},
            "tune_opened": False, "assessment_opened": False}
    return {**body, "contract_sha256": BASE.canonical_hash(body)}


def expected_protected_rows() -> list[dict[str, Any]]:
    rows = []
    for index in PROTECTED_INDICES:
        left, right = index + 11, (index * 7) % 19 + 3
        target = left + right
        rows.append({"case_id": f"v41-protected-{index:02d}",
                     "prompt": f"Compute {left} + {right}. Return only the integer.",
                     "target": str(target),
                     "candidates": [str(target), str(target + 1), str(target - 1), str(target + 2)]})
    return rows


def score_rows(instrument: dict[str, Any]) -> list[dict[str, Any]]:
    return [{"case_id": f'{case["case_id"]}-v41r25-exact', "prompt": case["composition_prompt"],
             "target": case["target"], "candidates": list(case["candidates"])}
            for case in (instrument["cases"][i] for i in INDICES)]


def gate(score: dict[str, Any], receipts: list[dict[str, Any]], reload_exact: bool) -> dict[str, Any]:
    first = sum(row["acquisition_loss"] for row in receipts[:8]) / 8
    last = sum(row["acquisition_loss"] for row in receipts[-8:]) / 8
    ratio = last / first if first > 0 else math.inf
    scores, target = score["candidate_log_probabilities"], score["target"]
    margin = scores[target] - max(value for key, value in scores.items() if key != target)
    errors = []
    if score.get("correct") is not True: errors.append("selected_target")
    if margin < 2.0: errors.append("target_margin")
    if ratio > 0.10: errors.append("loss_ratio")
    if reload_exact is not True: errors.append("reload_exact")
    return {"pass": not errors, "errors": errors, "target_margin_nats": margin,
            "first8_mean_acquisition_loss": first, "last8_mean_acquisition_loss": last,
            "last8_to_first8_acquisition_loss_ratio": ratio}


def decision(candidate: dict[str, Any]) -> dict[str, Any]:
    gates = {case_id: gate(packet["exact_after"], packet["receipts"], candidate["reload"]["state_exact"])
             for case_id, packet in candidate["cases"].items()}
    passing = sum(value["pass"] for value in gates.values()); protected = candidate["protected_after"]["accuracy"]
    drop = candidate["protected_before"]["accuracy"] - protected
    retention = protected >= 0.98; keep = passing == 4 and retention
    return {"classification": "DisjointProtectedReplayReplicationComplete",
            "interpretation": "DisjointReplayQualified" if keep else "DisjointReplayNotQualified",
            "acquisition_cases_passing": passing, "case_gates": gates, "protected_accuracy": protected,
            "protected_drop": drop,
            "retention_pass": retention, "candidate_keep": keep, "replication_only": True}


def validate(artifact: Path, rgs_root: Path) -> dict[str, Any]:
    result_path, adapter, manifest = artifact / "disjoint-replay-result.json", artifact / "disjoint-replay-adapter-state.pt", artifact / "MANIFEST.sha256"
    if not result_path.is_file() or not adapter.is_file() or not manifest.is_file():
        return {"valid": False, "errors": ["disjoint replay artifact files missing"]}
    result = json.loads(result_path.read_text()); errors: set[str] = set()
    body = {k: v for k, v in result.items() if k != "result_sha256"}
    if result.get("result_sha256") != BASE.canonical_hash(body): errors.add("result_sha256")
    for key, value in {"version": VERSION, "state_slice": STATE_SLICE,
                       "classification": "DisjointProtectedReplayReplicationComplete",
                       "tune_opened": False, "assessment_opened": False, "claim_ceiling": CLAIM_CEILING}.items():
        if result.get(key) != value: errors.add(key)
    instrument = BASE.INSTRUMENT.expected_packet(); expected_rows = score_rows(instrument)
    if result.get("instrument_sha256") != instrument["instrument_sha256"]: errors.add("instrument")
    if result.get("contract") != expected_contract(instrument): errors.add("contract")
    if result.get("case_ids") != [instrument["cases"][i]["case_id"] for i in INDICES] or result.get("exact_score_rows") != expected_rows: errors.add("case_binding")
    if not BASE23.valid_runtime(result.get("runtime", {})): errors.add("runtime")
    model = result.get("model", {})
    if model.get("id") != BASE.MODEL or model.get("revision") != BASE.REVISION: errors.add("model")
    before = result.get("exact_before_rows")
    if not isinstance(before, list) or len(before) != 4: errors.add("before_census")
    else:
        for i, row in enumerate(before): errors.update(f"before:{e}" for e in BASE23.scored_errors(row, expected_rows[i]))
    candidate = result.get("candidate", {}); after = candidate.get("exact_after_rows")
    if not isinstance(after, list) or len(after) != 4: errors.add("after_census")
    else:
        for i, row in enumerate(after): errors.update(f"after:{e}" for e in BASE23.scored_errors(row, expected_rows[i]))
    case_ids = result.get("case_ids", []); cases = candidate.get("cases", {})
    if set(cases) != set(case_ids): errors.add("case_census")
    receipts = candidate.get("update", {}).get("receipts")
    schedule = [index for _ in range(64) for index in INDICES]
    if not isinstance(receipts, list) or len(receipts) != 256: errors.add("receipt_census"); receipts = []
    for step, receipt in enumerate(receipts):
        index = schedule[step]; expected_protected = [16 + ((step % 4) * 4 + j) % 16 for j in range(4)]
        numeric = ("acquisition_loss", "protected_loss", "weighted_loss", "gradient_norm")
        if receipt.get("step") != step or receipt.get("case_index") != index or receipt.get("case_id") != instrument["cases"][index]["case_id"] or receipt.get("protected_indices") != expected_protected: errors.add("receipt_binding")
        if receipt.get("acquisition_examples") != 4 or receipt.get("protected_examples") != 4 or receipt.get("acquisition_target_tokens", 0) <= 0 or receipt.get("protected_target_tokens", 0) <= 0: errors.add("receipt_budget")
        if any(not isinstance(receipt.get(k), (int, float)) or not math.isfinite(receipt[k]) for k in numeric): errors.add("receipt_finite")
        elif abs(receipt["weighted_loss"] - (0.75 * receipt["acquisition_loss"] + 0.25 * receipt["protected_loss"])) > 1e-9: errors.add("receipt_weight")
    if receipts:
        for i, case_id in enumerate(case_ids):
            packet = cases[case_id]
            if packet.get("exact_after") != after[i] or packet.get("receipts") != [r for r in receipts if r["case_id"] == case_id]: errors.add(f"{case_id}:projection")
    for label in ("protected_before", "protected_after"):
        rows = candidate.get(label, {}).get("rows"); errors.update(f"{label}:{e}" for e in BASE.validate_rows(rows, context=None, label=label))
        expected_protected = expected_protected_rows()
        if isinstance(rows, list) and len(rows) == 16:
            if candidate[label].get("accuracy") != sum(row.get("correct") is True for row in rows) / 16: errors.add(f"{label}:accuracy")
            for position, row in enumerate(rows):
                if any(row.get(key) != expected_protected[position][key]
                       for key in ("case_id", "target", "candidates")): errors.add(f"{label}:binding")
    update, reload = candidate.get("update", {}), candidate.get("reload", {})
    if update.get("optimizer_steps") != 256 or update.get("acquisition_examples") != 1024 or update.get("protected_examples") != 1024: errors.add("update_budget")
    if update.get("adapter_file") != adapter.name or update.get("adapter_file_sha256") != file_hash(adapter): errors.add("adapter")
    if reload.get("fresh_base_model") is not True or reload.get("state_exact") is not True or reload.get("state_sha256") != update.get("post_update_state_sha256"): errors.add("reload")
    if cases:
        expected = decision(candidate)
        for key, value in expected.items():
            if result.get(key) != value: errors.add(f"decision:{key}")
    expected_manifest = "".join(file_hash(path).removeprefix("sha256:") + f"  {path.name}\n" for path in (result_path, adapter))
    if manifest.read_text() != expected_manifest: errors.add("manifest")
    source = result.get("source", {}); commit = source.get("rgs_commit", "")
    mappings = (("runner_sha256", "scripts/run_v41r25_disjoint_replay.py"),
                ("method_sha256", "mesh_brain/meshmodel/v41r25_disjoint_replay_replication.py"),
                ("instrument_sha256", "mesh_brain/meshmodel/v41r11_novelty_instrument.py"),
                ("requirements_sha256", "requirements-v41-h100-profile.txt"))
    for key, relative in mappings:
        try:
            content = subprocess.run(["git", "show", f"{commit}:{relative}"], cwd=rgs_root, check=True, capture_output=True).stdout
            if source.get(key) != "sha256:" + hashlib.sha256(content).hexdigest(): errors.add(key)
        except (subprocess.CalledProcessError, TypeError): errors.add(f"{key}:unavailable")
    return {"version": "astral.v41r25_disjoint_replay_artifact_validation.v1", "valid": not errors,
            "errors": sorted(errors), "classification": result.get("classification"),
            "interpretation": result.get("interpretation"), "protected_accuracy": result.get("protected_accuracy"),
            "candidate_keep": result.get("candidate_keep"), "result_sha256": result.get("result_sha256"),
            "claim_ceiling": result.get("claim_ceiling") if not errors else None}


def main() -> int:
    p = argparse.ArgumentParser(); p.add_argument("--artifact", type=Path, required=True)
    p.add_argument("--rgs-root", type=Path, required=True); p.add_argument("--report", type=Path); a = p.parse_args()
    report = validate(a.artifact.resolve(), a.rgs_root.resolve()); text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if a.report: a.report.write_text(text)
    print(text, end=""); return 0 if report["valid"] else 1


if __name__ == "__main__": raise SystemExit(main())
