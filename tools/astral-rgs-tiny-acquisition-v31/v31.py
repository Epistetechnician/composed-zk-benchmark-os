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
V30_PATH = HERE.parent / "astral-rgs-response-free-v30/v30.py"
SPEC = importlib.util.spec_from_file_location("astral_v30_for_v31", V30_PATH)
assert SPEC is not None and SPEC.loader is not None
V30 = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = V30
SPEC.loader.exec_module(V30)
TARGETS = V30.WORDS[16:]
SOURCE_LOCKS = ("rgs_core", "rgs_worker", "rgs_coordinator", "astral_protocol", "astral_validator", "astral_cli")


def expected_fixture() -> dict[str, Any]:
    cases = []
    for index, target in enumerate(TARGETS):
        key = f"v31key-{index:02d}"
        candidates = [target, TARGETS[(index + 1) % 16], TARGETS[(index + 5) % 16], TARGETS[(index + 9) % 16]]
        rotation = index % 4
        candidates = candidates[rotation:] + candidates[:rotation]
        cases.append({"case_id": f"v31case-{index:02d}", "key": key, "target": target, "candidates": candidates, "source": f"Private registry entry: {key} maps to {target}.", "train_prompt": f"Learn this private registry entry: {key} maps to {target}. Recall the mapped value.", "direct_prompt": f"Private registry query: which value maps from {key}?\nReturn only the value.", "paraphrase_prompt": f"Consult the learned private registry. Give the value associated with {key}.\nReturn only the value."})
    body = {"version": PROTOCOL["fixture_version"], "cases": cases, "protected_fixture": V30.expected_fixture()}
    return {**body, "fixture_sha256": V30.stable_hash(body)}


def summarize(phases: dict[str, list[dict[str, Any]]], reload_delta: float, no_update_exact: bool) -> dict[str, Any]:
    counts = {"pre_direct": 16, "no_update_direct": 16, "post_direct": 16, "reload_direct": 16, "reload_paraphrase": 16, "pre_protected": 32, "reload_protected": 32}
    if set(phases) != set(counts) or any(len(phases[key]) != count for key, count in counts.items()):
        raise ValueError("V31 coverage mismatch")
    metrics = {key: sum(bool(row["correct"]) for row in rows) / len(rows) for key, rows in phases.items()}
    improvement = metrics["reload_direct"] - metrics["pre_direct"]
    protected_drop = metrics["pre_protected"] - metrics["reload_protected"]
    g = PROTOCOL["gates"]
    gates = {"pre_direct": metrics["pre_direct"] <= g["pre_direct_ceiling"], "post_direct": metrics["reload_direct"] >= g["post_direct_floor"], "improvement": improvement >= g["improvement_floor"], "paraphrase": metrics["reload_paraphrase"] >= g["paraphrase_floor"], "protected": protected_drop <= g["protected_drop_ceiling"], "no_update_exact": no_update_exact, "reload_equivalent": reload_delta <= g["reload_score_tolerance"]}
    qualified = all(gates.values())
    return {"metrics": metrics, "improvement": improvement, "protected_drop": protected_drop, "reload_max_score_delta": reload_delta, "no_update_exact": no_update_exact, "gates": gates, "qualified": qualified, "status": "TinyAcquisitionQualified" if qualified else "TinyAcquisitionBlocked"}


def validate_artifact(root: Path) -> dict[str, Any]:
    errors: list[str] = []
    required = ("artifact-manifest.json", "fixture.json", "model-result.json", "model-process.json", "acquisition-packet.json", "preflight-receipt.json")
    if any(not (root / name).is_file() for name in required):
        return {"valid": False, "status": "Invalid", "errors": ["artifact.required"]}
    try:
        manifest, fixture, result, process, packet, preflight = [V30.read(root / name) for name in required]
    except Exception:
        return {"valid": False, "status": "Invalid", "errors": ["artifact.json"]}
    entries = manifest.get("files", [])
    if not isinstance(entries, list) or manifest.get("manifest_sha256") != V30.stable_hash(entries):
        errors.append("manifest.hash"); entries = []
    listed = set()
    for entry in entries:
        relative = entry.get("path") if isinstance(entry, dict) else None
        if not isinstance(relative, str) or relative in listed or ".." in Path(relative).parts:
            errors.append("manifest.path"); continue
        listed.add(relative)
        path = root / relative
        if not path.is_file() or path.is_symlink() or entry.get("sha256") != V30.sha256_file(path) or entry.get("size_bytes") != path.stat().st_size:
            errors.append("manifest.entry")
    actual = {path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file() and path.name != "artifact-manifest.json" and not path.name.startswith("astral-validation-")}
    if actual != listed or root.name != f"astral-rgs-v31-tiny-acquisition-{str(manifest.get('manifest_sha256',''))[7:19]}-r1":
        errors.append("manifest.census")
    expected = expected_fixture()
    if fixture != expected:
        errors.append("fixture")
    body = {key: value for key, value in result.items() if key != "result_sha256"}
    if result.get("result_sha256") != V30.stable_hash(body) or result.get("version") != PROTOCOL["result_version"]:
        errors.append("result.identity")
    phases = result.get("phases", {})
    if result.get("phases_sha256") != V30.stable_hash(phases):
        errors.append("phases.hash")
    for phase, rows in phases.items() if isinstance(phases, dict) else []:
        for row in rows:
            scores = row.get("candidate_scores", {})
            if set(scores) != set(row.get("candidates", [])) or any(not isinstance(value, (int, float)) or not math.isfinite(value) for value in scores.values()):
                errors.append(f"{phase}.scores"); continue
            selected = min(row["candidates"], key=lambda word: (-scores[word], word))
            if row.get("selected") != selected or row.get("correct") is not (selected == row.get("target")):
                errors.append(f"{phase}.decision")
    try:
        post, reload = phases["post_direct"], phases["reload_direct"]
        delta = max(abs(a["candidate_scores"][word] - b["candidate_scores"][word]) for a, b in zip(post, reload, strict=True) for word in a["candidates"])
        no_update_exact = phases["pre_direct"] == phases["no_update_direct"]
        derived = summarize(phases, delta, no_update_exact)
    except Exception:
        errors.append("summary.rederive"); derived = None
    if result.get("summary") != derived or result.get("budget") != PROTOCOL["budget"] or result.get("gradient_steps") != 64 or result.get("update_tokens", 999999) > 16384:
        errors.append("result.gates")
    inventory = result.get("model_inventory", {})
    if inventory.get("checkpoint_sha256") != PROTOCOL["checkpoint_sha256"] or inventory.get("tokenizer_sha256") != PROTOCOL["tokenizer_sha256"] or preflight.get("model_inventory") != inventory:
        errors.append("model")
    adapter = root / "adapter/adapters.safetensors"
    if not adapter.is_file() or result.get("adapter_sha256") != V30.sha256_file(adapter):
        errors.append("adapter")
    if process.get("returncode") != 0 or process.get("result_present") is not True:
        errors.append("process")
    locks = preflight.get("source_locks", {})
    if set(locks) != set(SOURCE_LOCKS) or packet.get("source_locks") != locks or preflight.get("protocol_sha256") != V30.sha256_file(PROTOCOL_PATH):
        errors.append("sources")
    for name in SOURCE_LOCKS:
        path = root / "source-locks" / f"{name}.source"
        if not path.is_file() or locks.get(name) != V30.sha256_file(path):
            errors.append(f"sources.{name}")
    for name, path in {"astral_protocol": PROTOCOL_PATH, "astral_validator": Path(__file__), "astral_cli": HERE / "validate_acquisition.py"}.items():
        if locks.get(name) != V30.sha256_file(path):
            errors.append(f"sources.local.{name}")
    packet_body = {key: value for key, value in packet.items() if key != "packet_sha256"}
    if packet.get("packet_sha256") != V30.stable_hash(packet_body) or packet.get("version") != PROTOCOL["packet_version"] or packet.get("summary") != derived or packet.get("claim_ceiling") != PROTOCOL["claim_ceiling"]:
        errors.append("packet")
    if any(packet.get(key) is not False for key in ("assessment_opened", "continual_learning_run", "confirmation_run")):
        errors.append("packet.boundary")
    status = (derived or {}).get("status", "Invalid") if not errors else "Invalid"
    return {"version": "astral.v31_validation_report.v1", "valid": not errors, "status": status, "errors": errors, "artifact_manifest_sha256": manifest.get("manifest_sha256"), "packet_sha256": packet.get("packet_sha256"), "claim_ceiling": PROTOCOL["claim_ceiling"], "model_execution": False, "external_review": "NotRun"}
