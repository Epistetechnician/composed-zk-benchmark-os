from __future__ import annotations

import importlib.util
import json
import math
import statistics
import sys
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
PROTOCOL_PATH = HERE / "protocol.json"; PROTOCOL = json.loads(PROTOCOL_PATH.read_text())
V37_SPEC = importlib.util.spec_from_file_location("v37_for_v38", HERE.parent / "astral-rgs-interference-v37/v37.py")
assert V37_SPEC and V37_SPEC.loader
V37 = importlib.util.module_from_spec(V37_SPEC); sys.modules[V37_SPEC.name] = V37; V37_SPEC.loader.exec_module(V37)
V30 = V37.V30
SOURCE_LOCKS = ("rgs_core", "rgs_worker", "rgs_coordinator", "astral_protocol", "astral_validator", "astral_cli")
MATCHED = {"joint_recent_alt_25": "recent_task_25", "joint_reservoir_alt_25": "reservoir_task_25"}


def fixture() -> dict[str, Any]:
    base = V37.fixture()
    body = {**{key: value for key, value in base.items() if key not in {"version", "arms", "fixture_sha256"}}, "version": "mesh.astral_v38_fixed_allocation_fixture.v1", "arms": PROTOCOL["arms"]}
    return {**body, "fixture_sha256": V30.stable_hash(body)}


def accuracy(rows):
    if not rows: raise ValueError("rows")
    return sum(bool(row["correct"]) for row in rows) / len(rows)


def summary(cells):
    expected = {(a, s, o) for a in PROTOCOL["arms"] for s in PROTOCOL["seeds"] for o in PROTOCOL["orders"]}
    if len(cells) != 16 or {(c["arm_id"], c["seed"], c["order_id"]) for c in cells} != expected: raise ValueError("coverage")
    arms = {}
    for arm in PROTOCOL["arms"]:
        evaluated = []
        for cell in [c for c in cells if c["arm_id"] == arm]:
            order = tuple(cell["task_order"]); stages = cell["stage_evaluations"]
            acquisitions = {task: accuracy(stages[i]["direct"][task]) for i, task in enumerate(order)}
            final = {task: accuracy(stages[-1]["direct"][task]) for task in order}
            retention = statistics.mean(final[task] for task in order[:-1])
            forgetting = {task: acquisitions[task] - final[task] for task in order[:-1]}
            paraphrase = statistics.mean(accuracy(cell["final_paraphrase"][task]) for task in order)
            protected = accuracy(cell["protected_after_final"]); losses = [float(row["loss"]) for row in cell["loss_trace"]]
            gates = {"final_task_acquisition": acquisitions[order[-1]] >= .75, "protected": protected >= .95, "reload": cell["reload_max_score_delta"] <= 1e-5, "update_parity": cell["update_tokens"] == 49152, "finite_loss": len(losses) == 128 and all(math.isfinite(x) for x in losses)}
            evaluated.append({"seed": cell["seed"], "order_id": cell["order_id"], "acquisitions": acquisitions, "final_direct": final, "mean_prior_retention": retention, "forgetting": forgetting, "mean_forgetting": statistics.mean(forgetting.values()), "mean_final_paraphrase": paraphrase, "protected": protected, "gates": gates, "mechanically_qualified": all(gates.values())})
        arms[arm] = {"cells": evaluated, "all_cells_mechanically_qualified": all(c["mechanically_qualified"] for c in evaluated), "all_cells_protected": all(c["gates"]["protected"] for c in evaluated), "mean_prior_retention": statistics.mean(c["mean_prior_retention"] for c in evaluated), "mean_final_paraphrase": statistics.mean(c["mean_final_paraphrase"] for c in evaluated), "minimum_protected": min(c["protected"] for c in evaluated)}
    candidates = {}
    for joint, control in MATCHED.items():
        retention = arms[joint]["mean_prior_retention"]; drop = arms[control]["mean_prior_retention"] - retention
        gates = {"all_cells_mechanical": arms[joint]["all_cells_mechanically_qualified"], "retention_band": .6 <= retention <= .9, "paraphrase": arms[joint]["mean_final_paraphrase"] >= .7, "retention_drop": drop <= .1, "matched_control_misses_protection": not arms[control]["all_cells_protected"]}
        candidates[joint] = {"matched_control": control, "retention_drop": drop, "gates": gates, "qualified": all(gates.values())}
    eligible = [arm for arm, row in candidates.items() if row["qualified"]]
    selected = min(eligible, key=lambda arm: (-arms[arm]["mean_prior_retention"], arm)) if eligible else None
    return {"arms": arms, "candidates": candidates, "selected_arm": selected, "qualified": selected is not None, "status": "FixedProtectionAllocationQualified" if selected else "FixedProtectionAllocationBlocked", "retention_band": [.6, .9], "paraphrase_floor": .7, "retention_drop_ceiling": .1}


def validate(root: Path) -> dict[str, Any]:
    errors = []; names = ("artifact-manifest.json", "fixture.json", "model-result.json", "model-process.json", "allocation-packet.json", "preflight-receipt.json")
    if any(not (root / name).is_file() for name in names): return {"valid": False, "status": "Invalid", "errors": ["required"]}
    manifest, frozen, result, process, packet, preflight = [V30.read(root / name) for name in names]
    entries = manifest.get("files", [])
    if manifest.get("manifest_sha256") != V30.stable_hash(entries): errors.append("manifest.hash")
    listed = set()
    for entry in entries:
        path = root / entry["path"]; listed.add(entry["path"])
        if not path.is_file() or path.is_symlink() or entry["sha256"] != V30.sha256_file(path) or entry["size_bytes"] != path.stat().st_size: errors.append("manifest.entry")
    actual = {p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file() and p.name != "artifact-manifest.json" and not p.name.startswith("astral-validation-")}
    expected_name = f"astral-rgs-v38-fixed-allocation-{str(manifest.get('manifest_sha256',''))[7:19]}-r1"
    if actual != listed or root.name != expected_name: errors.append("manifest.census")
    if frozen != fixture(): errors.append("fixture")
    cells = result.get("cells", []); body = {key: value for key, value in result.items() if key != "result_sha256"}
    if result.get("result_sha256") != V30.stable_hash(body) or result.get("cells_sha256") != V30.stable_hash(cells) or result.get("version") != PROTOCOL["result_version"]: errors.append("result")
    for cell in cells:
        trace = cell.get("loss_trace", []); mixes = {(r["current_examples"], r["prior_examples"], r["protected_examples"]) for r in trace}
        if not mixes.issubset({(3, 0, 1), (3, 1, 0)}) or cell.get("update_tokens") != 49152: errors.append("schedule")
        if cell["arm_id"].startswith("joint_"):
            later = [r for r in trace if r["stage"] > 1]
            if sum(r["prior_examples"] for r in later) != 48 or sum(r["protected_examples"] for r in later) != 48: errors.append("alternation")
        for stage in cell.get("stage_evaluations", []):
            for rows in stage["direct"].values(): V37.validate_decision_rows(rows, errors)
            adapter = root / f"states/{cell['arm_id']}-{cell['seed']}-{cell['order_id']}/stage{stage['stage']}/adapters.safetensors"
            if not adapter.is_file() or stage.get("adapter_sha256") != V30.sha256_file(adapter): errors.append("adapter")
        for rows in cell.get("final_paraphrase", {}).values(): V37.validate_decision_rows(rows, errors)
        V37.validate_decision_rows(cell.get("protected_after_final", []), errors)
    try: derived = summary(cells)
    except Exception: errors.append("summary"); derived = None
    if result.get("summary") != derived: errors.append("summary.mismatch")
    if process.get("returncode") != 0 or process.get("result_present") is not True: errors.append("process")
    locks = preflight.get("source_locks", {})
    if set(locks) != set(SOURCE_LOCKS) or packet.get("source_locks") != locks or preflight.get("protocol_sha256") != V30.sha256_file(PROTOCOL_PATH): errors.append("sources")
    for name in SOURCE_LOCKS:
        path = root / f"source-locks/{name}.source"
        if not path.is_file() or locks.get(name) != V30.sha256_file(path): errors.append(f"source.{name}")
    for name, path in {"astral_protocol": PROTOCOL_PATH, "astral_validator": Path(__file__), "astral_cli": HERE / "validate_allocation.py"}.items():
        if locks.get(name) != V30.sha256_file(path): errors.append(f"local.{name}")
    if result.get("tokenizer_preflight") != {"prompt_count": 64, "maximum_tokens": 83, "window_tokens": 96, "all_fit": True}: errors.append("tokenizer")
    packet_body = {key: value for key, value in packet.items() if key != "packet_sha256"}
    if packet.get("packet_sha256") != V30.stable_hash(packet_body) or packet.get("version") != PROTOCOL["packet_version"] or packet.get("summary") != derived or packet.get("cell_count") != 16 or packet.get("total_update_tokens") != 786432: errors.append("packet")
    status = (derived or {}).get("status", "Invalid") if not errors else "Invalid"
    return {"version": "astral.v38_validation_report.v1", "valid": not errors, "status": status, "errors": errors, "artifact_manifest_sha256": manifest.get("manifest_sha256"), "claim_ceiling": PROTOCOL["claim_ceiling"], "model_execution": False, "external_review": "NotRun"}
