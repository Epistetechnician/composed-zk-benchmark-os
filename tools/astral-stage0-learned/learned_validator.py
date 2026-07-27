"""Semantic validator for learned Stage 0 bundles."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

from learned_stage0 import METHODS, normalized_regret, selected


def _pairs(pairs):
    value = {}
    for key, child in pairs:
        if key in value:
            raise ValueError("duplicate JSON key")
        value[key] = child
    return value


def _load(path: Path):
    raw = path.read_bytes()
    value = json.loads(raw, object_pairs_hook=_pairs)
    expected = (
        json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)
        + "\n"
    ).encode()
    if raw != expected:
        raise ValueError("noncanonical JSON")
    return value


def validate(root: Path) -> dict[str, object]:
    if root.is_symlink() or not root.is_dir():
        raise ValueError("invalid bundle root")
    manifest = _load(root / "manifest.json")
    boundary = {
        "accepted_evidence": False,
        "level": "local_learned_model_measurement_candidate",
        "mechanistic_understanding": False,
        "self_modeling": False,
    }
    if manifest.get("claim_boundary") != boundary:
        raise ValueError("claim boundary drift")
    declared = manifest.get("files")
    if not isinstance(declared, list):
        raise ValueError("missing file declarations")
    declared_names = [row["path"] for row in declared]
    actual = sorted(path.name for path in root.iterdir() if path.name != "manifest.json")
    if sorted(declared_names) != actual or len(set(declared_names)) != len(actual):
        raise ValueError("file census drift")
    for row in declared:
        path = root / row["path"]
        if path.is_symlink() or not path.is_file():
            raise ValueError("artifact must be regular")
        raw = path.read_bytes()
        if row["bytes"] != len(raw) or row["sha256"] != hashlib.sha256(raw).hexdigest():
            raise ValueError("artifact digest drift")
    config = _load(root / "config.json")
    summary = _load(root / "summary.json")
    lock = _load(root / "protocol.lock.json")
    if summary.get("claim_boundary") != boundary:
        raise ValueError("summary boundary drift")
    if summary.get("protocol_sha256") != lock.get("protocol_sha256"):
        raise ValueError("protocol binding drift")
    lines = (root / "records.jsonl").read_bytes().splitlines()
    if len(lines) != summary.get("record_census"):
        raise ValueError("record census drift")
    method_values = {method: [] for method in METHODS}
    prior = ""
    for raw in lines:
        row = json.loads(raw, object_pairs_hook=_pairs)
        record_id = row.get("record_id")
        if not isinstance(record_id, str) or record_id <= prior:
            raise ValueError("record ordering drift")
        prior = record_id
        if row.get("split") != "evaluation" or row.get("family") not in range(256, 320):
            raise ValueError("evaluation split drift")
        effects = row.get("ablation_effects")
        scores = row.get("scores")
        regrets = row.get("regrets")
        if not (
            isinstance(effects, list) and len(effects) == 4
            and isinstance(scores, dict) and set(scores) == set(METHODS)
            and isinstance(regrets, dict) and set(regrets) == set(METHODS)
        ):
            raise ValueError("record schema drift")
        for number in effects:
            if not isinstance(number, (int, float)) or not math.isfinite(number):
                raise ValueError("invalid effect")
        for method in METHODS:
            expected_regret, _ = normalized_regret(effects, scores[method])
            if abs(float(regrets[method]) - expected_regret) > 1e-7:
                raise ValueError("regret drift")
            if row["selections"][method] != selected(scores[method]):
                raise ValueError("selection drift")
            method_values[method].append(expected_regret)
    for method, values in method_values.items():
        expected = sum(values) / len(values)
        if abs(float(summary["method_regret"][method]) - expected) > 1e-7:
            raise ValueError("method summary drift")
    if config.get("methods") != list(METHODS):
        raise ValueError("method config drift")
    if summary.get("verdict") == "Pass" and not all(
        (
            summary.get("eligibility"),
            summary.get("coverage_gate"),
            summary.get("placebo_control"),
            summary.get("patch_control"),
            summary.get("primary_gate"),
            all(summary.get("run_controls", {}).values()),
        )
    ):
        raise ValueError("pass gate drift")
    return {
        "schema": "astral.learned-stage0.validation.v1",
        "valid": True,
        "verdict": summary["verdict"],
    }
