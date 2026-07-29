from __future__ import annotations

import importlib.util
import json
import math
import sys
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
PROTOCOL_PATH = HERE / "protocol.json"
PROTOCOL = json.loads(PROTOCOL_PATH.read_text(encoding="utf-8"))
V29_PATH = HERE.parent / "astral-rgs-positive-controls-v29/v29.py"
SPEC = importlib.util.spec_from_file_location("astral_v29_for_r2", V29_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("V29 independent fixture is unavailable")
V29 = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = V29
SPEC.loader.exec_module(V29)
SOURCE_LOCKS = ("rgs_fixture_core", "rgs_r2_core", "rgs_worker", "rgs_coordinator", "astral_protocol", "astral_validator", "astral_cli")


def read(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("V29R2 input must be an object")
    return value


def summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    cases = V29.expected_fixture()["cases"]
    if len(rows) != 64 or {row.get("case_id") for row in rows} != {case["case_id"] for case in cases}:
        raise ValueError("V29R2 coverage mismatch")
    rungs = {}
    qualified = True
    for rung, threshold in PROTOCOL["thresholds"].items():
        selected = [row for row in rows if row["rung"] == rung]
        correct = sum(bool(row["correct"]) for row in selected)
        accuracy = correct / len(selected)
        passed = accuracy >= threshold
        qualified = qualified and passed
        rungs[rung] = {"correct": correct, "total": len(selected), "accuracy": accuracy, "threshold": threshold, "passed": passed}
    return {"format_id": PROTOCOL["format_id"], "rungs": rungs, "qualified": qualified, "status": "CanonicalBoundaryQualified" if qualified else "CanonicalBoundaryStillBlocked"}


def validate_artifact(root: Path) -> dict[str, Any]:
    errors: list[str] = []
    names = ("artifact-manifest.json", "fixture.json", "model-result.json", "model-process.json", "instrument-packet.json", "preflight-receipt.json")
    if any(not (root / name).is_file() for name in names):
        return {"valid": False, "status": "Invalid", "errors": ["artifact.required"]}
    try:
        manifest, fixture, result, process, packet, preflight = [read(root / name) for name in names]
    except (OSError, ValueError, json.JSONDecodeError):
        return {"valid": False, "status": "Invalid", "errors": ["artifact.json"]}
    entries = manifest.get("files", [])
    if not isinstance(entries, list) or manifest.get("manifest_sha256") != V29.stable_hash(entries):
        errors.append("manifest.hash"); entries = []
    listed = set()
    for entry in entries:
        relative = entry.get("path") if isinstance(entry, dict) else None
        if not isinstance(relative, str) or relative in listed or ".." in Path(relative).parts:
            errors.append("manifest.path"); continue
        listed.add(relative)
        path = root / relative
        if not path.is_file() or path.is_symlink() or entry.get("sha256") != V29.sha256_file(path) or entry.get("size_bytes") != path.stat().st_size:
            errors.append("manifest.entry")
    actual = {path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file() and path.name != "artifact-manifest.json" and not path.name.startswith("astral-validation-")}
    if actual != listed:
        errors.append("manifest.census")
    expected_name = f"astral-rgs-v29r2-canonical-boundary-{str(manifest.get('manifest_sha256',''))[7:19]}-r1"
    if root.name != expected_name:
        errors.append("manifest.name")
    expected_fixture = V29.expected_fixture()
    if fixture != expected_fixture or fixture.get("fixture_sha256") != PROTOCOL["fixture_sha256"]:
        errors.append("fixture.rederivation")
    body = {key: value for key, value in result.items() if key != "result_sha256"}
    if result.get("result_sha256") != V29.stable_hash(body) or result.get("version") != PROTOCOL["result_version"]:
        errors.append("result.identity")
    boundary = result.get("boundary_verification")
    expected_boundary = {"prefix_token_ids": PROTOCOL["prefix_token_ids"], "label_token_ids": {label: [token] for label, token in PROTOCOL["label_token_ids"].items()}, "canonical": True}
    if boundary != expected_boundary:
        errors.append("result.boundary")
    rows = result.get("observations")
    if not isinstance(rows, list) or result.get("observations_sha256") != V29.stable_hash(rows):
        errors.append("result.rows_hash"); rows = []
    cases = {case["case_id"]: case for case in expected_fixture["cases"]}
    for index, row in enumerate(rows):
        case = cases.get(row.get("case_id"))
        if case is None or row.get("rung") != case["rung"] or row.get("expected_label") != case["expected_label"] or row.get("user_prompt_sha256") != case["user_prompt_sha256"]:
            errors.append(f"rows[{index}].binding"); continue
        tokens = row.get("input_token_ids")
        if not isinstance(tokens, list) or tokens[-2:] != PROTOCOL["prefix_token_ids"] or row.get("input_token_ids_sha256") != V29.stable_hash(tokens):
            errors.append(f"rows[{index}].tokens")
        scores = row.get("label_scores")
        if not isinstance(scores, list) or len(scores) != 4 or any(not isinstance(value, (int, float)) or not math.isfinite(value) for value in scores):
            errors.append(f"rows[{index}].scores"); continue
        predicted = V29.LABELS[max(range(4), key=lambda choice: (scores[choice], -choice))]
        if row.get("predicted_label") != predicted or row.get("correct") is not (predicted == case["expected_label"]):
            errors.append(f"rows[{index}].decision")
    try:
        expected_summary = summary(rows)
    except (KeyError, TypeError, ValueError):
        errors.append("result.coverage"); expected_summary = None
    if result.get("summary") != expected_summary or result.get("format_id") != PROTOCOL["format_id"] or result.get("batch_size") != 8 or result.get("model_load_count") != 1 or result.get("update_tokens") != 0 or result.get("training_run") is not False or result.get("adapter_created") is not False:
        errors.append("result.gates")
    inventory = result.get("model_inventory", {})
    if inventory.get("checkpoint_sha256") != PROTOCOL["checkpoint_sha256"] or inventory.get("tokenizer_sha256") != PROTOCOL["tokenizer_sha256"] or preflight.get("model_inventory") != inventory:
        errors.append("model.identity")
    if process.get("returncode") != 0 or process.get("result_present") is not True or process.get("argv", []).count("mesh_brain.meshmodel.v29r2_positive_control_mlx") != 1:
        errors.append("process")
    locks = preflight.get("source_locks", {})
    if set(locks) != set(SOURCE_LOCKS) or packet.get("source_locks") != locks or preflight.get("protocol_sha256") != V29.sha256_file(PROTOCOL_PATH):
        errors.append("sources.binding")
    for name in SOURCE_LOCKS:
        path = root / "source-locks" / f"{name}.source"
        if not path.is_file() or locks.get(name) != V29.sha256_file(path):
            errors.append(f"sources.{name}")
    for name, path in {"astral_protocol": PROTOCOL_PATH, "astral_validator": Path(__file__), "astral_cli": HERE / "validate_instrument.py"}.items():
        if locks.get(name) != V29.sha256_file(path):
            errors.append(f"sources.local.{name}")
    packet_body = {key: value for key, value in packet.items() if key != "packet_sha256"}
    if packet.get("packet_sha256") != V29.stable_hash(packet_body) or packet.get("version") != PROTOCOL["packet_version"] or packet.get("summary") != expected_summary or packet.get("status") != (expected_summary or {}).get("status") or packet.get("claim_ceiling") != PROTOCOL["claim_ceiling"]:
        errors.append("packet")
    if any(packet.get(key) is not False for key in ("training_run", "candidate_corpus_created", "acquisition_run", "assessment_opened")):
        errors.append("packet.boundary")
    return {"version": "astral.v29r2_validation_report.v1", "valid": not errors, "status": (expected_summary or {}).get("status", "Invalid") if not errors else "Invalid", "errors": errors, "artifact_manifest_sha256": manifest.get("manifest_sha256"), "packet_sha256": packet.get("packet_sha256"), "claim_ceiling": PROTOCOL["claim_ceiling"], "model_execution": False, "training_run": False, "acquisition_run": False, "external_review": "NotRun"}
