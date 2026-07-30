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
V30_PATH = HERE.parent / "astral-rgs-response-free-v30/v30.py"
SPEC = importlib.util.spec_from_file_location("astral_v30_for_v32", V30_PATH)
assert SPEC is not None and SPEC.loader is not None
V30 = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = V30
SPEC.loader.exec_module(V30)
TARGETS = V30.WORDS[:8]
SOURCE_LOCKS = ("rgs_core", "rgs_worker", "rgs_coordinator", "astral_protocol", "astral_validator", "astral_cli")


def expected_fixture() -> dict[str, Any]:
    cases = []
    for index, target in enumerate(TARGETS):
        key = f"v32dev-{index:02d}"
        candidates = [target, TARGETS[(index + 1) % 8], TARGETS[(index + 3) % 8], TARGETS[(index + 5) % 8]]
        rotation = index % 4
        candidates = candidates[rotation:] + candidates[:rotation]
        cases.append({"case_id": f"v32case-{index:02d}", "key": key, "target": target, "candidates": candidates, "train_prompt": f"Learn this development registry entry: {key} maps to {target}. Recall the mapped value.", "direct_prompt": f"Development registry query: which value maps from {key}?\nReturn only the value.", "paraphrase_prompt": f"Using the learned development registry, give the value associated with {key}.\nReturn only the value."})
    body = {"version": PROTOCOL["fixture_version"], "cases": cases, "protected_fixture": V30.expected_fixture(), "arms": PROTOCOL["arms"], "budget": PROTOCOL["budget"], "gates": PROTOCOL["gates"]}
    return {**body, "fixture_sha256": V30.stable_hash(body)}


def summary(base: list[dict[str, Any]], arms: dict[str, dict[str, Any]]) -> dict[str, Any]:
    base_accuracy = sum(bool(row["correct"]) for row in base) / 32
    evaluated = {}
    for arm_id in PROTOCOL["arms"]:
        arm = arms[arm_id]
        losses = [float(row["loss"]) for row in arm["loss_trace"]]
        direct = sum(bool(row["correct"]) for row in arm["direct"]) / 8
        paraphrase = sum(bool(row["correct"]) for row in arm["paraphrase"]) / 8
        protected = sum(bool(row["correct"]) for row in arm["protected"]) / 32
        gates = {"direct": direct >= PROTOCOL["gates"]["direct_floor"], "paraphrase": paraphrase >= PROTOCOL["gates"]["paraphrase_floor"], "protected": base_accuracy - protected <= PROTOCOL["gates"]["protected_drop_ceiling"], "finite_loss": len(losses) == 32 and all(math.isfinite(x) for x in losses), "nonincreasing_loss": statistics.mean(losses[-8:]) <= statistics.mean(losses[:8]), "max_loss": max(losses) <= PROTOCOL["gates"]["max_loss_ceiling"]}
        evaluated[arm_id] = {"direct_accuracy": direct, "paraphrase_accuracy": paraphrase, "protected_accuracy": protected, "protected_drop": base_accuracy - protected, "initial_loss_mean": statistics.mean(losses[:8]), "final_loss_mean": statistics.mean(losses[-8:]), "maximum_loss": max(losses), "gates": gates, "qualified": all(gates.values())}
    selected = next((arm for arm in PROTOCOL["arms"] if evaluated[arm]["qualified"]), None)
    return {"base_protected_accuracy": base_accuracy, "arms": evaluated, "selected_arm": selected, "qualified": selected is not None, "status": "OptimizerDevelopmentQualified" if selected else "OptimizerDevelopmentBlocked"}


def validate(root: Path) -> dict[str, Any]:
    errors = []
    names = ("artifact-manifest.json", "fixture.json", "model-result.json", "model-process.json", "optimizer-packet.json", "preflight-receipt.json")
    if any(not (root / name).is_file() for name in names):
        return {"valid": False, "status": "Invalid", "errors": ["artifact.required"]}
    manifest, fixture, result, process, packet, preflight = [V30.read(root / name) for name in names]
    entries = manifest.get("files", [])
    if not isinstance(entries, list) or manifest.get("manifest_sha256") != V30.stable_hash(entries):
        errors.append("manifest.hash"); entries = []
    listed = set()
    for entry in entries:
        relative = entry.get("path", "")
        path = root / relative
        listed.add(relative)
        if ".." in Path(relative).parts or not path.is_file() or path.is_symlink() or entry.get("sha256") != V30.sha256_file(path) or entry.get("size_bytes") != path.stat().st_size:
            errors.append("manifest.entry")
    actual = {p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file() and p.name != "artifact-manifest.json" and not p.name.startswith("astral-validation-")}
    if actual != listed or root.name != f"astral-rgs-v32-optimizer-development-{str(manifest.get('manifest_sha256',''))[7:19]}-r1":
        errors.append("manifest.census")
    if fixture != expected_fixture():
        errors.append("fixture")
    body = {k: v for k, v in result.items() if k != "result_sha256"}
    if result.get("result_sha256") != V30.stable_hash(body) or result.get("version") != PROTOCOL["result_version"]:
        errors.append("result.identity")
    for rows in [result.get("base_protected", [])] + [arm.get(kind, []) for arm in result.get("arms", {}).values() for kind in ("direct", "paraphrase", "protected")]:
        for row in rows:
            scores = row.get("candidate_scores", {})
            if set(scores) != set(row.get("candidates", [])) or any(not math.isfinite(value) for value in scores.values()):
                errors.append("scores"); continue
            selected = min(row["candidates"], key=lambda word: (-scores[word], word))
            if row.get("selected") != selected or row.get("correct") is not (selected == row.get("target")):
                errors.append("decision")
    try:
        derived = summary(result["base_protected"], result["arms"])
    except Exception:
        errors.append("summary"); derived = None
    if result.get("summary") != derived:
        errors.append("result.summary")
    inventory = result.get("model_inventory", {})
    if inventory.get("checkpoint_sha256") != PROTOCOL["checkpoint_sha256"] or inventory.get("tokenizer_sha256") != PROTOCOL["tokenizer_sha256"] or preflight.get("model_inventory") != inventory:
        errors.append("model")
    for arm_id, arm in result.get("arms", {}).items():
        adapter = root / f"states/{arm_id}/adapter/adapters.safetensors"
        if arm.get("update_tokens", 99999) > 8192 or not adapter.is_file() or arm.get("adapter_sha256") != V30.sha256_file(adapter):
            errors.append(f"arm.{arm_id}")
    if process.get("returncode") != 0 or process.get("result_present") is not True:
        errors.append("process")
    locks = preflight.get("source_locks", {})
    if set(locks) != set(SOURCE_LOCKS) or packet.get("source_locks") != locks or preflight.get("protocol_sha256") != V30.sha256_file(PROTOCOL_PATH):
        errors.append("sources")
    for name in SOURCE_LOCKS:
        source = root / f"source-locks/{name}.source"
        if not source.is_file() or locks.get(name) != V30.sha256_file(source):
            errors.append(f"sources.{name}")
    for name, path in {"astral_protocol": PROTOCOL_PATH, "astral_validator": Path(__file__), "astral_cli": HERE / "validate_optimizer.py"}.items():
        if locks.get(name) != V30.sha256_file(path):
            errors.append(f"sources.local.{name}")
    packet_body = {k: v for k, v in packet.items() if k != "packet_sha256"}
    if packet.get("packet_sha256") != V30.stable_hash(packet_body) or packet.get("version") != PROTOCOL["packet_version"] or packet.get("summary") != derived or packet.get("claim_ceiling") != PROTOCOL["claim_ceiling"]:
        errors.append("packet")
    status = (derived or {}).get("status", "Invalid") if not errors else "Invalid"
    return {"version": "astral.v32_validation_report.v1", "valid": not errors, "status": status, "errors": errors, "artifact_manifest_sha256": manifest.get("manifest_sha256"), "packet_sha256": packet.get("packet_sha256"), "claim_ceiling": PROTOCOL["claim_ceiling"], "model_execution": False, "external_review": "NotRun"}
