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
SPEC = importlib.util.spec_from_file_location(
    "v30_for_v37",
    HERE.parent / "astral-rgs-response-free-v30/v30.py",
)
assert SPEC is not None and SPEC.loader is not None
V30 = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = V30
SPEC.loader.exec_module(V30)
SOURCE_LOCKS = (
    "rgs_core",
    "rgs_worker",
    "rgs_coordinator",
    "astral_protocol",
    "astral_validator",
    "astral_cli",
)


def task(task_id: str, words: tuple[str, ...]) -> dict[str, Any]:
    cases = []
    for index, target in enumerate(words):
        key = f"v37{task_id.lower()}-{index:02d}"
        candidates = [target, words[(index + 1) % 8], words[(index + 3) % 8], words[(index + 5) % 8]]
        rotation = index % 4
        candidates = candidates[rotation:] + candidates[:rotation]
        cases.append({
            "case_id": f"v37{task_id.lower()}case-{index:02d}",
            "task_id": task_id,
            "key": key,
            "target": target,
            "candidates": candidates,
            "train_prompt": f"V37 task {task_id} registry key: {key}. Associated value:",
            "direct_prompt": f"V37 task {task_id} query: which value maps from {key}?\nReturn only the value.",
            "paraphrase_prompt": f"Using learned V37 task {task_id}, give the value associated with {key}.\nReturn only the value.",
        })
    return {"task_id": task_id, "cases": cases}


def fixture() -> dict[str, Any]:
    tasks = [
        task(task_id, V30.WORDS[index * 8:(index + 1) * 8])
        for index, task_id in enumerate(PROTOCOL["task_ids"])
    ]
    body = {
        "version": "mesh.astral_v37_interference_fixture.v1",
        "tasks": tasks,
        "protected_fixture": V30.expected_fixture(),
        "arms": PROTOCOL["arms"],
        "seeds": PROTOCOL["seeds"],
        "orders": PROTOCOL["orders"],
        "steps_per_task": 32,
        "tokens_per_example": 96,
        "update_tokens_per_task": 12288,
        "update_tokens_per_cell": 49152,
    }
    return {**body, "fixture_sha256": V30.stable_hash(body)}


def accuracy(rows: list[dict[str, Any]]) -> float:
    if not rows:
        raise ValueError("accuracy rows")
    return sum(bool(row["correct"]) for row in rows) / len(rows)


def summary(cells: list[dict[str, Any]]) -> dict[str, Any]:
    expected = {
        (arm, seed, order)
        for arm in PROTOCOL["arms"]
        for seed in PROTOCOL["seeds"]
        for order in PROTOCOL["orders"]
    }
    if len(cells) != 12 or {(c["arm_id"], c["seed"], c["order_id"]) for c in cells} != expected:
        raise ValueError("coverage")
    arms = {}
    for arm in PROTOCOL["arms"]:
        evaluated = []
        for cell in [row for row in cells if row["arm_id"] == arm]:
            order = tuple(cell["task_order"])
            stages = cell["stage_evaluations"]
            if len(stages) != 4 or [stage["stage"] for stage in stages] != [1, 2, 3, 4]:
                raise ValueError("stages")
            acquisitions = {
                task_id: accuracy(stages[index]["direct"][task_id])
                for index, task_id in enumerate(order)
            }
            final_direct = {
                task_id: accuracy(stages[-1]["direct"][task_id])
                for task_id in order
            }
            retention = statistics.mean(final_direct[task_id] for task_id in order[:-1])
            forgetting = {
                task_id: acquisitions[task_id] - final_direct[task_id]
                for task_id in order[:-1]
            }
            paraphrase = statistics.mean(
                accuracy(cell["final_paraphrase"][task_id]) for task_id in order
            )
            protected = accuracy(cell["protected_after_final"])
            losses = [float(row["loss"]) for row in cell["loss_trace"]]
            gates = {
                "final_task_acquisition": acquisitions[order[-1]] >= 0.75,
                "protected": protected >= 0.95,
                "reload": cell["reload_max_score_delta"] <= 1e-5,
                "update_parity": cell["update_tokens"] == 49152,
                "finite_loss": len(losses) == 128 and all(math.isfinite(value) for value in losses),
            }
            evaluated.append({
                "seed": cell["seed"],
                "order_id": cell["order_id"],
                "acquisitions": acquisitions,
                "final_direct": final_direct,
                "mean_prior_retention": retention,
                "forgetting": forgetting,
                "mean_forgetting": statistics.mean(forgetting.values()),
                "mean_final_paraphrase": paraphrase,
                "protected": protected,
                "gates": gates,
                "mechanically_qualified": all(gates.values()),
            })
        arms[arm] = {
            "cells": evaluated,
            "all_cells_mechanically_qualified": all(row["mechanically_qualified"] for row in evaluated),
            "mean_prior_retention": statistics.mean(row["mean_prior_retention"] for row in evaluated),
            "mean_forgetting": statistics.mean(row["mean_forgetting"] for row in evaluated),
            "mean_final_paraphrase": statistics.mean(row["mean_final_paraphrase"] for row in evaluated),
        }
    strongest_retention, strongest_replay = max(
        (arms[arm]["mean_prior_retention"], arm) for arm in PROTOCOL["arms"][1:]
    )
    no_replay_retention = arms["no_task_replay"]["mean_prior_retention"]
    advantage = strongest_retention - no_replay_retention
    mechanical = all(arms[arm]["all_cells_mechanically_qualified"] for arm in PROTOCOL["arms"][1:])
    forgetting_observed = any(
        row["mean_forgetting"] > 0
        for arm in PROTOCOL["arms"][1:]
        for row in arms[arm]["cells"]
    )
    if not mechanical:
        status = "MechanicalOrAcquisitionBlocked"
    elif strongest_retention > 0.9:
        status = "SaturatedTooEasy"
    elif strongest_retention < 0.6:
        status = "TooHardOrUnderAcquired"
    elif advantage < 0.1:
        status = "InsufficientReplaySeparation"
    elif not forgetting_observed:
        status = "NoObservedInterference"
    else:
        status = "InterferenceStreamQualified"
    return {
        "arms": arms,
        "strongest_replay": strongest_replay,
        "strongest_replay_retention": strongest_retention,
        "no_replay_retention": no_replay_retention,
        "replay_advantage": advantage,
        "retention_band": [0.6, 0.9],
        "replay_advantage_floor": 0.1,
        "replay_forgetting_observed": forgetting_observed,
        "qualified": status == "InterferenceStreamQualified",
        "status": status,
    }


def validate_decision_rows(rows: list[dict[str, Any]], errors: list[str]) -> None:
    for row in rows:
        scores = row.get("candidate_scores", {})
        candidates = row.get("candidates", [])
        if set(scores) != set(candidates):
            errors.append("decision.scores")
            continue
        selected = min(candidates, key=lambda word: (-scores[word], word))
        if row.get("selected") != selected or row.get("correct") is not (selected == row["target"]):
            errors.append("decision.value")


def validate(root: Path) -> dict[str, Any]:
    errors: list[str] = []
    names = (
        "artifact-manifest.json",
        "fixture.json",
        "model-result.json",
        "model-process.json",
        "stream-packet.json",
        "preflight-receipt.json",
    )
    if any(not (root / name).is_file() for name in names):
        return {"valid": False, "status": "Invalid", "errors": ["required"]}
    manifest, frozen, result, process, packet, preflight = [
        V30.read(root / name) for name in names
    ]
    entries = manifest.get("files", [])
    if manifest.get("manifest_sha256") != V30.stable_hash(entries):
        errors.append("manifest.hash")
    listed = set()
    for entry in entries:
        path = root / entry["path"]
        listed.add(entry["path"])
        if not path.is_file() or path.is_symlink() or entry["sha256"] != V30.sha256_file(path) or entry["size_bytes"] != path.stat().st_size:
            errors.append("manifest.entry")
    actual = {
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.is_file()
        and path.name != "artifact-manifest.json"
        and not path.name.startswith("astral-validation-")
    }
    expected_name = f"astral-rgs-v37-interference-stream-{str(manifest.get('manifest_sha256', ''))[7:19]}-r1"
    if actual != listed or root.name != expected_name:
        errors.append("manifest.census")
    if frozen != fixture():
        errors.append("fixture")
    body = {key: value for key, value in result.items() if key != "result_sha256"}
    cells = result.get("cells", [])
    if result.get("result_sha256") != V30.stable_hash(body) or result.get("cells_sha256") != V30.stable_hash(cells) or result.get("version") != PROTOCOL["result_version"]:
        errors.append("result")
    for cell in cells:
        trace = cell.get("loss_trace", [])
        mixes = {
            (row["current_examples"], row["prior_examples"], row["protected_examples"])
            for row in trace
        }
        allowed = {(3, 0, 1)} if cell["arm_id"] == "no_task_replay" else {(3, 0, 1), (3, 1, 0)}
        if not mixes.issubset(allowed) or cell.get("update_tokens") != 49152:
            errors.append("cell.schedule")
        for stage in cell.get("stage_evaluations", []):
            for rows in stage.get("direct", {}).values():
                validate_decision_rows(rows, errors)
            state = root / f"states/{cell['arm_id']}-{cell['seed']}-{cell['order_id']}/stage{stage['stage']}/adapters.safetensors"
            if not state.is_file() or stage.get("adapter_sha256") != V30.sha256_file(state):
                errors.append("adapter")
        for rows in cell.get("final_paraphrase", {}).values():
            validate_decision_rows(rows, errors)
        validate_decision_rows(cell.get("protected_after_final", []), errors)
    try:
        derived = summary(cells)
    except Exception:
        errors.append("summary")
        derived = None
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
    for name, path in {
        "astral_protocol": PROTOCOL_PATH,
        "astral_validator": Path(__file__),
        "astral_cli": HERE / "validate_stream.py",
    }.items():
        if locks.get(name) != V30.sha256_file(path):
            errors.append(f"local.{name}")
    token_preflight = result.get("tokenizer_preflight", {})
    if token_preflight != {
        "prompt_count": 64,
        "maximum_tokens": 83,
        "window_tokens": 96,
        "all_fit": True,
    }:
        errors.append("tokenizer.preflight")
    packet_body = {key: value for key, value in packet.items() if key != "packet_sha256"}
    if packet.get("packet_sha256") != V30.stable_hash(packet_body) or packet.get("version") != PROTOCOL["packet_version"] or packet.get("summary") != derived or packet.get("cell_count") != 12 or packet.get("total_update_tokens") != 589824:
        errors.append("packet")
    status = (derived or {}).get("status", "Invalid") if not errors else "Invalid"
    return {
        "version": "astral.v37_validation_report.v1",
        "valid": not errors,
        "status": status,
        "errors": errors,
        "artifact_manifest_sha256": manifest.get("manifest_sha256"),
        "claim_ceiling": PROTOCOL["claim_ceiling"],
        "model_execution": False,
        "external_review": "NotRun",
    }
