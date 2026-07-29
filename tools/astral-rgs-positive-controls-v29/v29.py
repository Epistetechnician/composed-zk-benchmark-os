from __future__ import annotations

import hashlib
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
PROTOCOL_PATH = HERE / "protocol.json"
PROTOCOL = json.loads(PROTOCOL_PATH.read_text(encoding="utf-8"))
LABELS = tuple(PROTOCOL["labels"])
RUNGS = tuple(PROTOCOL["rungs"])
FORMATS = tuple(PROTOCOL["formats"])
THRESHOLDS = PROTOCOL["thresholds"]
SOURCE_LOCKS = (
    "rgs_core", "rgs_worker", "rgs_coordinator",
    "astral_protocol", "astral_validator", "astral_cli",
)


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value, allow_nan=False, ensure_ascii=False, separators=(",", ":"), sort_keys=True
    ).encode("utf-8")


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
        raise ValueError(f"{path} must contain an object")
    return value


def _options(case_index: int, correct_index: int) -> list[str]:
    correct = f"v29value-{case_index:02d}-target"
    distractors = [f"v29value-{case_index:02d}-distractor-{item}" for item in range(3)]
    values: list[str] = []
    cursor = 0
    for position in range(4):
        if position == correct_index:
            values.append(correct)
        else:
            values.append(distractors[cursor])
            cursor += 1
    return values


def _choice_block(options: list[str]) -> str:
    return "\n".join(f"Candidate {label}: {value}" for label, value in zip(LABELS, options))


def expected_fixture() -> dict[str, Any]:
    cases: list[dict[str, Any]] = []
    for rung in RUNGS:
        for index in range(PROTOCOL["cases_per_rung"]):
            correct_index = index % 4
            expected = LABELS[correct_index]
            options = _options(index, correct_index)
            entity = f"v29fixture-entity-{index:02d}"
            alias = f"v29fixture-alias-{index:02d}"
            route = f"v29fixture-route-{index:02d}"
            target = options[correct_index]
            if rung == "literal_symbol":
                body = f"Positive-control instruction: return the uppercase symbol {expected}."
            elif rung == "direct_lookup":
                body = (
                    f"Dossier: {entity} carries {target}.\n"
                    f"Which value does {entity} carry?\n{_choice_block(options)}"
                )
            elif rung == "one_hop":
                body = (
                    f"Dossier: {alias} identifies {entity}. {entity} carries {target}.\n"
                    f"Follow {alias}; which value is reached?\n{_choice_block(options)}"
                )
            else:
                body = (
                    f"Dossier: {route} enters {entity}. {entity} carries {target}.\n"
                    f"Follow the two-edge path from {route}; which value is terminal?\n"
                    f"{_choice_block(options)}"
                )
            prompt = body + "\nReturn exactly one uppercase answer symbol: A, B, C, or D.\n"
            cases.append(
                {
                    "case_id": f"v29fixture-{rung}-{index:02d}",
                    "rung": rung,
                    "expected_label": expected,
                    "user_prompt": prompt,
                    "user_prompt_sha256": stable_hash(prompt),
                }
            )
    body = {"version": PROTOCOL["fixture_version"], "cases": cases}
    return {**body, "fixture_sha256": stable_hash(body)}


def expected_summary(observations: list[dict[str, Any]]) -> dict[str, Any]:
    cases = expected_fixture()["cases"]
    pairs = {(format_id, case["case_id"]) for format_id in FORMATS for case in cases}
    if len(observations) != len(pairs) or {(row.get("format_id"), row.get("case_id")) for row in observations} != pairs:
        raise ValueError("observation coverage mismatch")
    formats: dict[str, Any] = {}
    for format_id in FORMATS:
        rungs: dict[str, Any] = {}
        eligible = True
        for rung in RUNGS:
            rows = [row for row in observations if row["format_id"] == format_id and row["rung"] == rung]
            correct = sum(bool(row["correct"]) for row in rows)
            accuracy = correct / len(rows)
            passed = accuracy >= THRESHOLDS[rung]
            eligible = eligible and passed
            rungs[rung] = {
                "correct": correct,
                "total": len(rows),
                "accuracy": accuracy,
                "threshold": THRESHOLDS[rung],
                "passed": passed,
            }
        formats[format_id] = {"rungs": rungs, "eligible": eligible}
    selected = next((format_id for format_id in FORMATS if formats[format_id]["eligible"]), None)
    return {
        "formats": formats,
        "selected_format": selected,
        "status": "PositiveControlInstrumentQualified" if selected else "InstrumentStillBlocked",
    }


def validate_observations(observations: list[dict[str, Any]], errors: list[str]) -> dict[str, Any] | None:
    cases = {row["case_id"]: row for row in expected_fixture()["cases"]}
    for index, row in enumerate(observations):
        prefix = f"observations[{index}]"
        case = cases.get(row.get("case_id"))
        if case is None or row.get("format_id") not in FORMATS:
            errors.append(prefix + ".identity")
            continue
        if row.get("rung") != case["rung"] or row.get("expected_label") != case["expected_label"]:
            errors.append(prefix + ".answer_binding")
        if row.get("user_prompt_sha256") != case["user_prompt_sha256"]:
            errors.append(prefix + ".prompt_binding")
        tokens = row.get("input_token_ids")
        if not isinstance(tokens, list) or not tokens or not all(isinstance(value, int) for value in tokens):
            errors.append(prefix + ".tokens")
        elif row.get("input_token_ids_sha256") != stable_hash(tokens):
            errors.append(prefix + ".token_hash")
        scores = row.get("label_scores")
        if not isinstance(scores, list) or len(scores) != 4 or any(not isinstance(value, (int, float)) or not math.isfinite(value) for value in scores):
            errors.append(prefix + ".scores")
            continue
        predicted = LABELS[max(range(4), key=lambda choice: (scores[choice], -choice))]
        if row.get("predicted_label") != predicted:
            errors.append(prefix + ".argmax")
        if row.get("correct") is not (predicted == case["expected_label"]):
            errors.append(prefix + ".correct")
    try:
        return expected_summary(observations)
    except (KeyError, TypeError, ValueError):
        errors.append("observations.coverage")
        return None


def validate_artifact(root: Path) -> dict[str, Any]:
    errors: list[str] = []
    required = (
        "artifact-manifest.json", "fixture.json", "model-result.json",
        "model-process.json", "instrument-packet.json", "preflight-receipt.json",
    )
    if any(not (root / name).is_file() for name in required):
        return {"valid": False, "status": "Invalid", "errors": ["artifact.required_files"]}
    try:
        manifest = read(root / "artifact-manifest.json")
        fixture = read(root / "fixture.json")
        result = read(root / "model-result.json")
        process = read(root / "model-process.json")
        packet = read(root / "instrument-packet.json")
        preflight = read(root / "preflight-receipt.json")
    except (OSError, ValueError, json.JSONDecodeError):
        return {"valid": False, "status": "Invalid", "errors": ["artifact.json"]}

    entries = manifest.get("files")
    if not isinstance(entries, list) or manifest.get("manifest_sha256") != stable_hash(entries):
        errors.append("manifest.hash")
        entries = []
    listed: set[str] = set()
    for entry in entries:
        relative = entry.get("path") if isinstance(entry, dict) else None
        if not isinstance(relative, str) or relative in listed or relative.startswith("/") or ".." in Path(relative).parts:
            errors.append("manifest.path")
            continue
        listed.add(relative)
        path = root / relative
        if not path.is_file() or path.is_symlink():
            errors.append("manifest.file")
        elif entry.get("sha256") != sha256_file(path) or entry.get("size_bytes") != path.stat().st_size:
            errors.append("manifest.entry")
    actual = {
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.is_file() and path.name != "artifact-manifest.json" and not path.name.startswith("astral-validation-")
    }
    if actual != listed:
        errors.append("manifest.census")
    expected_name = f"astral-rgs-v29-positive-control-{str(manifest.get('manifest_sha256', ''))[7:19]}-r1"
    if root.name != expected_name:
        errors.append("manifest.artifact_name")

    if fixture != expected_fixture():
        errors.append("fixture.rederivation")
    for rung in RUNGS:
        labels = Counter(row["expected_label"] for row in fixture.get("cases", []) if row.get("rung") == rung)
        if labels != Counter({label: 4 for label in LABELS}):
            errors.append(f"fixture.balance.{rung}")

    if result.get("version") != PROTOCOL["result_version"] or result.get("state_slice") != PROTOCOL["state_slice"]:
        errors.append("result.identity")
    result_body = {key: value for key, value in result.items() if key != "result_sha256"}
    if result.get("result_sha256") != stable_hash(result_body):
        errors.append("result.hash")
    if result.get("fixture_sha256") != fixture.get("fixture_sha256"):
        errors.append("result.fixture")
    if result.get("formats") != list(FORMATS) or result.get("batch_size") != PROTOCOL["batch_size"]:
        errors.append("result.configuration")
    if result.get("model_load_count") != 1 or result.get("update_tokens") != 0 or result.get("training_run") is not False or result.get("adapter_created") is not False:
        errors.append("result.boundary")
    observations = result.get("observations")
    if not isinstance(observations, list) or result.get("observations_sha256") != stable_hash(observations):
        errors.append("result.observations_hash")
        observations = []
    summary = validate_observations(observations, errors)
    if summary is None or result.get("summary") != summary:
        errors.append("result.summary")

    inventory = result.get("model_inventory", {})
    if inventory.get("checkpoint_sha256") != PROTOCOL["checkpoint_sha256"] or inventory.get("tokenizer_sha256") != PROTOCOL["tokenizer_sha256"]:
        errors.append("model.identity")
    if preflight.get("model_inventory") != inventory:
        errors.append("preflight.model")
    if preflight.get("protocol_sha256") != sha256_file(PROTOCOL_PATH):
        errors.append("preflight.protocol")
    if process.get("returncode") != 0 or process.get("result_present") is not True:
        errors.append("process.outcome")
    argv = process.get("argv")
    if not isinstance(argv, list) or argv.count("mesh_brain.meshmodel.v29_positive_control_mlx") != 1:
        errors.append("process.worker")

    locks = preflight.get("source_locks")
    if not isinstance(locks, dict) or set(locks) != set(SOURCE_LOCKS) or packet.get("source_locks") != locks:
        errors.append("sources.binding")
        locks = {}
    for name in SOURCE_LOCKS:
        snapshot = root / "source-locks" / f"{name}.source"
        if not snapshot.is_file() or locks.get(name) != sha256_file(snapshot):
            errors.append(f"sources.{name}")
    local_sources = {
        "astral_protocol": PROTOCOL_PATH,
        "astral_validator": Path(__file__),
        "astral_cli": HERE / "validate_instrument.py",
    }
    for name, path in local_sources.items():
        if locks.get(name) != sha256_file(path):
            errors.append(f"sources.local.{name}")

    packet_body = {key: value for key, value in packet.items() if key != "packet_sha256"}
    if packet.get("packet_sha256") != stable_hash(packet_body):
        errors.append("packet.hash")
    if packet.get("version") != PROTOCOL["packet_version"] or packet.get("state_slice") != PROTOCOL["state_slice"]:
        errors.append("packet.identity")
    if packet.get("protocol_sha256") != sha256_file(PROTOCOL_PATH) or packet.get("model_result_sha256") != result.get("result_sha256"):
        errors.append("packet.binding")
    if packet.get("model_process_count") != 1 or packet.get("summary") != summary or packet.get("status") != (summary or {}).get("status"):
        errors.append("packet.decision")
    if packet.get("claim_ceiling") != PROTOCOL["claim_ceiling"]:
        errors.append("packet.claim")
    false_keys = (
        "training_run", "candidate_corpus_created", "assessment_opened",
        "acquisition_run", "confirmation_run", "independent_replication",
    )
    if any(packet.get(key) is not False for key in false_keys):
        errors.append("packet.boundary")

    return {
        "version": "astral.v29_positive_control_validation_report.v1",
        "valid": not errors,
        "status": (summary or {}).get("status", "Invalid") if not errors else "Invalid",
        "selected_format": (summary or {}).get("selected_format"),
        "errors": errors,
        "artifact_manifest_sha256": manifest.get("manifest_sha256"),
        "packet_sha256": packet.get("packet_sha256"),
        "claim_ceiling": PROTOCOL["claim_ceiling"],
        "model_execution": False,
        "training_run": False,
        "acquisition_run": False,
        "external_review": "NotRun",
    }
