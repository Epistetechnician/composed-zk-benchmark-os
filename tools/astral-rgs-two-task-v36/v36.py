from __future__ import annotations

import importlib.util
import json
import math
import statistics
import sys
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
PROTOCOL_PATH = HERE / "protocol.json"
PROTOCOL = json.loads(PROTOCOL_PATH.read_text())
SPEC = importlib.util.spec_from_file_location("v30_for_v36", HERE.parent / "astral-rgs-response-free-v30/v30.py")
assert SPEC is not None and SPEC.loader is not None
V30 = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = V30
SPEC.loader.exec_module(V30)
SOURCE_LOCKS = ("rgs_core", "rgs_worker", "rgs_coordinator", "astral_protocol", "astral_validator", "astral_cli")


def _task(task_id: str, words: tuple[str, ...]) -> dict[str, Any]:
    cases = []
    for index, target in enumerate(words):
        key = f"v36{task_id.lower()}-{index:02d}"
        candidates = [target, words[(index + 1) % 8], words[(index + 3) % 8], words[(index + 5) % 8]]
        rotation = index % 4
        candidates = candidates[rotation:] + candidates[:rotation]
        cases.append({"case_id": f"v36{task_id.lower()}case-{index:02d}", "task_id": task_id, "key": key, "target": target, "candidates": candidates, "train_prompt": f"V36 task {task_id} registry key: {key}. Associated value:", "direct_prompt": f"V36 task {task_id} query: which value maps from {key}?\nReturn only the value.", "paraphrase_prompt": f"Using learned V36 task {task_id}, give the value associated with {key}.\nReturn only the value."})
    return {"task_id": task_id, "cases": cases}


def fixture() -> dict[str, Any]:
    body = {"version": "mesh.astral_v36_two_task_fixture.v1", "tasks": [_task("A", V30.WORDS[:8]), _task("B", V30.WORDS[8:16])], "protected_fixture": V30.expected_fixture(), "arms": PROTOCOL["arms"], "seeds": PROTOCOL["seeds"], "orders": PROTOCOL["orders"], "steps_per_task": 32, "tokens_per_example": 64, "update_tokens_per_task": 8192}
    return {**body, "fixture_sha256": V30.stable_hash(body)}


def accuracy(rows: list[dict[str, Any]]) -> float:
    return sum(bool(row["correct"]) for row in rows) / len(rows)


def summary(cells: list[dict[str, Any]]) -> dict[str, Any]:
    expected = {(arm, seed, order) for arm in PROTOCOL["arms"] for seed in PROTOCOL["seeds"] for order in PROTOCOL["orders"]}
    if len(cells) != 12 or {(c["arm_id"], c["seed"], c["order_id"]) for c in cells} != expected:
        raise ValueError("coverage")
    arms = {}
    for arm in PROTOCOL["arms"]:
        evaluated = []
        for cell in [c for c in cells if c["arm_id"] == arm]:
            first1 = accuracy(cell["first_after_first_direct"]); first2 = accuracy(cell["first_after_second_direct"]); second2 = accuracy(cell["second_after_second_direct"]); firstp = accuracy(cell["first_after_second_paraphrase"]); secondp = accuracy(cell["second_after_second_paraphrase"]); protected = accuracy(cell["protected_after_second"]); forgetting = first1 - first2; losses = [float(row["loss"]) for row in cell["loss_trace"]]
            gates = {"first_acquisition": first1 >= .75, "second_acquisition": second2 >= .75, "first_retention": first2 >= .75, "first_paraphrase": firstp >= .75, "second_paraphrase": secondp >= .75, "forgetting": forgetting <= .125, "protected": protected >= .95, "reload": cell["reload_max_score_delta"] <= 1e-5, "update_parity": cell["update_tokens"] == 16384, "finite_loss": len(losses) == 64 and all(math.isfinite(x) for x in losses)}
            evaluated.append({"seed": cell["seed"], "order_id": cell["order_id"], "first_after_first": first1, "first_after_second": first2, "second_after_second": second2, "first_paraphrase": firstp, "second_paraphrase": secondp, "protected": protected, "forgetting": forgetting, "gates": gates, "qualified": all(gates.values())})
        arms[arm] = {"cells": evaluated, "all_cells_qualified": all(c["qualified"] for c in evaluated), "mean_first_retention": statistics.mean(c["first_after_second"] for c in evaluated), "mean_forgetting": statistics.mean(c["forgetting"] for c in evaluated)}
    baseline_value, baseline_id = max((arms[a]["mean_first_retention"], a) for a in PROTOCOL["arms"][:2])
    advantage = arms["joint_replay_25"]["mean_first_retention"] - baseline_value
    qualified = arms["joint_replay_25"]["all_cells_qualified"] and advantage >= .1
    return {"arms": arms, "strongest_baseline": baseline_id, "retention_advantage": advantage, "advantage_floor": .1, "qualified": qualified, "status": "TwoTaskContinualLearningPilotQualified" if qualified else "TwoTaskContinualLearningPilotBlocked"}


def validate(root: Path) -> dict[str, Any]:
    errors = []
    names = ("artifact-manifest.json", "fixture.json", "model-result.json", "model-process.json", "stream-packet.json", "preflight-receipt.json")
    if any(not (root / name).is_file() for name in names):
        return {"valid": False, "status": "Invalid", "errors": ["required"]}
    manifest, frozen, result, process, packet, preflight = [V30.read(root / name) for name in names]
    entries = manifest.get("files", [])
    if manifest.get("manifest_sha256") != V30.stable_hash(entries):
        errors.append("manifest.hash")
    listed = set()
    for entry in entries:
        path = root / entry["path"]; listed.add(entry["path"])
        if not path.is_file() or path.is_symlink() or entry["sha256"] != V30.sha256_file(path) or entry["size_bytes"] != path.stat().st_size:
            errors.append("manifest.entry")
    actual = {p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file() and p.name != "artifact-manifest.json" and not p.name.startswith("astral-validation-")}
    if actual != listed or root.name != f"astral-rgs-v36-two-task-stream-{str(manifest.get('manifest_sha256',''))[7:19]}-r1":
        errors.append("manifest.census")
    if frozen != fixture():
        errors.append("fixture")
    body = {key: value for key, value in result.items() if key != "result_sha256"}
    cells = result.get("cells", [])
    if result.get("result_sha256") != V30.stable_hash(body) or result.get("cells_sha256") != V30.stable_hash(cells) or result.get("version") != PROTOCOL["result_version"]:
        errors.append("result")
    decision_keys = ("first_after_first_direct", "first_after_second_direct", "second_after_second_direct", "first_after_second_paraphrase", "second_after_second_paraphrase", "protected_after_second")
    for cell in cells:
        expected_mixes = ({(3, 0, 1)} if cell["arm_id"] == "no_task_replay" else {(3, 0, 1), (3, 1, 0)} if cell["arm_id"] == "task_replay_25" else {(3, 0, 1), (2, 1, 1)})
        observed_mixes = {(row["current_examples"], row["prior_examples"], row["protected_examples"]) for row in cell.get("loss_trace", [])}
        if not observed_mixes.issubset(expected_mixes) or cell.get("update_tokens") != 16384:
            errors.append("cell.schedule")
        for key in decision_keys:
            for row in cell.get(key, []):
                scores = row.get("candidate_scores", {})
                selected = min(row["candidates"], key=lambda word: (-scores[word], word))
                if set(scores) != set(row["candidates"]) or row.get("selected") != selected or row.get("correct") is not (selected == row["target"]):
                    errors.append("decision")
        state = root / f"states/{cell['arm_id']}-{cell['seed']}-{cell['order_id']}"
        for name, field in (("stage1", "stage1_adapter_sha256"), ("final", "final_adapter_sha256")):
            adapter = state / name / "adapters.safetensors"
            if not adapter.is_file() or cell.get(field) != V30.sha256_file(adapter):
                errors.append("adapter")
    try:
        derived = summary(cells)
    except Exception:
        errors.append("summary"); derived = None
    if result.get("summary") != derived:
        errors.append("summary.mismatch")
    if process.get("returncode") != 0 or process.get("result_present") is not True:
        errors.append("process")
    locks = preflight.get("source_locks", {})
    if set(locks) != set(SOURCE_LOCKS) or packet.get("source_locks") != locks or preflight.get("protocol_sha256") != V30.sha256_file(PROTOCOL_PATH):
        errors.append("sources")
    for name in SOURCE_LOCKS:
        path = root / f"source-locks/{name}.source"
        if not path.is_file() or locks.get(name) != V30.sha256_file(path):
            errors.append(f"source.{name}")
    for name, path in {"astral_protocol": PROTOCOL_PATH, "astral_validator": Path(__file__), "astral_cli": HERE / "validate_stream.py"}.items():
        if locks.get(name) != V30.sha256_file(path):
            errors.append(f"local.{name}")
    packet_body = {key: value for key, value in packet.items() if key != "packet_sha256"}
    if packet.get("packet_sha256") != V30.stable_hash(packet_body) or packet.get("version") != PROTOCOL["packet_version"] or packet.get("summary") != derived or packet.get("cell_count") != 12 or packet.get("total_update_tokens") != 196608:
        errors.append("packet")
    status = (derived or {}).get("status", "Invalid") if not errors else "Invalid"
    return {"version": "astral.v36_validation_report.v1", "valid": not errors, "status": status, "errors": errors, "artifact_manifest_sha256": manifest.get("manifest_sha256"), "claim_ceiling": PROTOCOL["claim_ceiling"], "model_execution": False, "external_review": "NotRun"}
