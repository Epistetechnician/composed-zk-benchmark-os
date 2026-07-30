from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
PROTOCOL_PATH = HERE / "protocol.json"
PROTOCOL = json.loads(PROTOCOL_PATH.read_text(encoding="utf-8"))
WORDS = (
    "amber", "cedar", "maple", "orbit", "comet", "violin", "trumpet", "silver",
    "golden", "purple", "orange", "winter", "summer", "river", "forest", "ocean",
    "mountain", "valley", "garden", "planet", "rocket", "tiger", "panda", "coral",
    "quartz", "copper", "marble", "velvet", "satin", "lemon", "cherry", "apple",
)
SOURCE_LOCKS = ("rgs_core", "rgs_worker", "rgs_coordinator", "astral_protocol", "astral_validator", "astral_cli")


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, allow_nan=False, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode()


def stable_hash(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical_bytes(value)).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return "sha256:" + digest.hexdigest()


def read(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("V30 input must be an object")
    return value


def expected_fixture() -> dict[str, Any]:
    rungs = PROTOCOL["rungs"]
    cases = []
    for index, target in enumerate(WORDS):
        rung = rungs[index // 8]
        entity, alias, route = f"v30entity-{index:02d}", f"v30alias-{index:02d}", f"v30route-{index:02d}"
        if rung == "literal_copy":
            dossier, question = f"Target value: {target}.", "Which target value was supplied?"
        elif rung == "direct_lookup":
            dossier, question = f"Registry: {entity} carries {target}.", f"Which value does {entity} carry?"
        elif rung == "one_hop":
            dossier, question = f"Registry: {alias} identifies {entity}. {entity} carries {target}.", f"Follow {alias}; which value is reached?"
        else:
            dossier, question = f"Registry: {route} enters {alias}. {alias} carries {target}.", f"Follow the two-edge path from {route}; which value is terminal?"
        ordered = [target, WORDS[(index + 1) % 32], WORDS[(index + 2) % 32], WORDS[(index + 3) % 32]]
        rotation = index % 4
        candidates = ordered[rotation:] + ordered[:rotation]
        positive = dossier + "\n" + question + "\nReturn only the value."
        null = "No registry or target value is supplied.\n" + question + "\nReturn only the value."
        cases.append({
            "case_id": f"v30case-{index:02d}", "case_index": index, "rung": rung,
            "target": target, "candidates": candidates,
            "positive_prompt": positive, "positive_prompt_sha256": stable_hash(positive),
            "null_prompt": null, "null_prompt_sha256": stable_hash(null),
            "shuffled_source_case_id": f"v30case-{(index + 1) % 32:02d}",
        })
    body = {"version": PROTOCOL["fixture_version"], "words": list(WORDS), "cases": cases}
    return {**body, "fixture_sha256": stable_hash(body)}


def _select(scores: dict[str, float], candidates: list[str]) -> str:
    return min(candidates, key=lambda word: (-scores[word], word))


def rederive_observations(model_id: str, evidence: list[dict[str, Any]], fixture: dict[str, Any]) -> list[dict[str, Any]]:
    by_id = {row["case_id"]: row for row in evidence}
    rows = []
    for index, case in enumerate(fixture["cases"]):
        current = by_id[case["case_id"]]
        shuffled = by_id[fixture["cases"][(index + 1) % 32]["case_id"]]
        for condition, source in (("positive", current), ("null", current), ("shuffled", shuffled)):
            raw = source["positive_word_scores"] if condition != "null" else current["null_word_scores"]
            delta = {word: source["positive_word_scores"][word] - current["null_word_scores"][word] for word in WORDS}
            greedy = source["positive_greedy_decoded"] if condition != "null" else current["null_greedy_decoded"]
            for method in PROTOCOL["methods"]:
                scores = raw if method == "content_likelihood" else delta if method == "contrastive_likelihood" else {}
                selected = _select(scores, case["candidates"]) if scores else greedy
                reversed_selected = _select(scores, list(reversed(case["candidates"]))) if scores else greedy
                rows.append({
                    "model_id": model_id, "method": method, "condition": condition,
                    "case_id": case["case_id"], "rung": case["rung"], "target": case["target"],
                    "candidates": case["candidates"], "selected": selected,
                    "correct": selected == case["target"], "permutation_invariant": selected == reversed_selected,
                    "candidate_scores": {word: scores[word] for word in case["candidates"]} if scores else {},
                    "source_case_id": case["case_id"] if condition != "shuffled" else case["shuffled_source_case_id"],
                })
    return rows


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    models = {}
    for model_id in PROTOCOL["models"]:
        methods = {}
        for method in PROTOCOL["methods"]:
            positive = [row for row in rows if row["model_id"] == model_id and row["method"] == method and row["condition"] == "positive"]
            rungs, positive_pass = {}, True
            for rung, threshold in PROTOCOL["thresholds"].items():
                selected = [row for row in positive if row["rung"] == rung]
                accuracy = sum(bool(row["correct"]) for row in selected) / len(selected)
                passed = accuracy >= threshold
                positive_pass = positive_pass and passed
                rungs[rung] = {"accuracy": accuracy, "correct": sum(bool(row["correct"]) for row in selected), "total": len(selected), "threshold": threshold, "passed": passed}
            controls, control_pass = {}, True
            for condition in ("null", "shuffled"):
                selected = [row for row in rows if row["model_id"] == model_id and row["method"] == method and row["condition"] == condition]
                accuracy = sum(bool(row["correct"]) for row in selected) / len(selected)
                passed = accuracy <= PROTOCOL["control_ceiling"]
                control_pass = control_pass and passed
                controls[condition] = {"accuracy": accuracy, "ceiling": PROTOCOL["control_ceiling"], "passed": passed}
            invariant = all(row["permutation_invariant"] is True for row in rows if row["model_id"] == model_id and row["method"] == method)
            methods[method] = {"rungs": rungs, "controls": controls, "permutation_invariant": invariant, "eligible": positive_pass and control_pass and invariant}
        selected_method = next((method for method in PROTOCOL["methods"] if methods[method]["eligible"]), None)
        models[model_id] = {"methods": methods, "selected_method": selected_method, "qualified": selected_method is not None}
    qualified = [model for model, value in models.items() if value["qualified"]]
    status = "DualCheckpointEvaluatorQualified" if len(qualified) == 2 else "SingleCheckpointEvaluatorQualified" if len(qualified) == 1 else "EvaluatorStillBlocked"
    return {"models": models, "qualified_models": qualified, "lowest_resource_qualified_model": next((model for model in PROTOCOL["models"] if model in qualified), None), "status": status}


def validate_artifact(root: Path) -> dict[str, Any]:
    errors: list[str] = []
    required = ("artifact-manifest.json", "fixture.json", "qwen_0_5b-result.json", "llama_1b-result.json", "qwen_0_5b-process.json", "llama_1b-process.json", "evaluator-packet.json", "preflight-receipt.json")
    if any(not (root / name).is_file() for name in required):
        return {"valid": False, "status": "Invalid", "errors": ["artifact.required"]}
    try:
        manifest, fixture, qwen, llama, qproc, lproc, packet, preflight = [read(root / name) for name in required]
    except (OSError, ValueError, json.JSONDecodeError):
        return {"valid": False, "status": "Invalid", "errors": ["artifact.json"]}
    entries = manifest.get("files", [])
    if not isinstance(entries, list) or manifest.get("manifest_sha256") != stable_hash(entries):
        errors.append("manifest.hash"); entries = []
    listed = set()
    for entry in entries:
        relative = entry.get("path") if isinstance(entry, dict) else None
        if not isinstance(relative, str) or relative in listed or ".." in Path(relative).parts:
            errors.append("manifest.path"); continue
        listed.add(relative)
        path = root / relative
        if not path.is_file() or path.is_symlink() or entry.get("sha256") != sha256_file(path) or entry.get("size_bytes") != path.stat().st_size:
            errors.append("manifest.entry")
    actual = {path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file() and path.name != "artifact-manifest.json" and not path.name.startswith("astral-validation-")}
    if actual != listed:
        errors.append("manifest.census")
    if root.name != f"astral-rgs-v30-response-free-{str(manifest.get('manifest_sha256', ''))[7:19]}-r1":
        errors.append("manifest.name")
    expected = expected_fixture()
    if fixture != expected:
        errors.append("fixture.rederivation")
    all_rows = []
    for model_id, result, process in (("qwen_0_5b", qwen, qproc), ("llama_1b", llama, lproc)):
        body = {key: value for key, value in result.items() if key != "result_sha256"}
        evidence, observations = result.get("raw_evidence"), result.get("observations")
        if result.get("result_sha256") != stable_hash(body) or result.get("version") != PROTOCOL["result_version"] or result.get("model_id") != model_id:
            errors.append(f"{model_id}.identity")
        if not isinstance(evidence, list) or len(evidence) != 32 or result.get("raw_evidence_sha256") != stable_hash(evidence):
            errors.append(f"{model_id}.evidence"); evidence = []
        for row in evidence:
            for key in ("positive_word_scores", "null_word_scores"):
                values = row.get(key, {})
                if set(values) != set(WORDS) or any(not isinstance(value, (int, float)) or not math.isfinite(value) for value in values.values()):
                    errors.append(f"{model_id}.scores")
        try:
            derived = rederive_observations(model_id, evidence, expected)
        except (KeyError, TypeError, ValueError):
            errors.append(f"{model_id}.rederive"); derived = []
        if observations != derived or result.get("observations_sha256") != stable_hash(observations):
            errors.append(f"{model_id}.observations")
        all_rows.extend(derived)
        inventory = result.get("model_inventory", {})
        model_spec = PROTOCOL["models"][model_id]
        if inventory.get("checkpoint_sha256") != model_spec["checkpoint_sha256"] or inventory.get("tokenizer_sha256") != model_spec["tokenizer_sha256"] or preflight.get("model_inventories", {}).get(model_id) != inventory:
            errors.append(f"{model_id}.model")
        token_ids = result.get("word_token_ids", {})
        if token_ids != PROTOCOL["word_token_ids"][model_id]:
            errors.append(f"{model_id}.tokens")
        if result.get("prompt_forward_count") != 64 or result.get("model_load_count") != 1 or result.get("batch_size") != 8 or result.get("training_run") is not False or result.get("adapter_created") is not False:
            errors.append(f"{model_id}.budget")
        if process.get("returncode") != 0 or process.get("result_present") is not True or process.get("argv", []).count("mesh_brain.meshmodel.v30_response_free_mlx") != 1:
            errors.append(f"{model_id}.process")
    try:
        expected_summary = summarize(all_rows)
    except (KeyError, TypeError, ValueError, ZeroDivisionError):
        errors.append("summary"); expected_summary = None
    locks = preflight.get("source_locks", {})
    if set(locks) != set(SOURCE_LOCKS) or packet.get("source_locks") != locks or preflight.get("protocol_sha256") != sha256_file(PROTOCOL_PATH):
        errors.append("sources.binding")
    for name in SOURCE_LOCKS:
        path = root / "source-locks" / f"{name}.source"
        if not path.is_file() or locks.get(name) != sha256_file(path):
            errors.append(f"sources.{name}")
    for name, path in {"astral_protocol": PROTOCOL_PATH, "astral_validator": Path(__file__), "astral_cli": HERE / "validate_evaluator.py"}.items():
        if locks.get(name) != sha256_file(path):
            errors.append(f"sources.local.{name}")
    packet_body = {key: value for key, value in packet.items() if key != "packet_sha256"}
    if packet.get("packet_sha256") != stable_hash(packet_body) or packet.get("version") != PROTOCOL["packet_version"] or packet.get("summary") != expected_summary or packet.get("status") != (expected_summary or {}).get("status") or packet.get("claim_ceiling") != PROTOCOL["claim_ceiling"]:
        errors.append("packet")
    if packet.get("model_process_count") != 2 or packet.get("prompt_forward_count") != 128 or any(packet.get(key) is not False for key in ("training_run", "candidate_corpus_created", "acquisition_run", "assessment_opened")):
        errors.append("packet.boundary")
    status = (expected_summary or {}).get("status", "Invalid") if not errors else "Invalid"
    return {"version": "astral.v30_validation_report.v1", "valid": not errors, "status": status, "errors": errors, "artifact_manifest_sha256": manifest.get("manifest_sha256"), "packet_sha256": packet.get("packet_sha256"), "claim_ceiling": PROTOCOL["claim_ceiling"], "model_execution": False, "training_run": False, "acquisition_run": False, "external_review": "NotRun"}
