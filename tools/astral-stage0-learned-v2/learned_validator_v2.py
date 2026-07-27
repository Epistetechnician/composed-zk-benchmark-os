"""Semantic validation for Stage 0 V2 bundles."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

V1_ROOT = Path(__file__).resolve().parents[1] / "astral-stage0-learned"
sys.path.insert(0, str(V1_ROOT))
from learned_stage0 import METHODS, normalized_regret, selected  # noqa: E402


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate key")
        result[key] = value
    return result


def _load(path):
    raw = path.read_bytes()
    value = json.loads(raw, object_pairs_hook=_pairs)
    canonical = (
        json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)
        + "\n"
    ).encode()
    if raw != canonical:
        raise ValueError("noncanonical JSON")
    return value


def validate(root: Path) -> dict[str, object]:
    manifest = _load(root / "manifest.json")
    actual = sorted(
        path.name for path in root.iterdir() if path.name != "manifest.json"
    )
    declared = manifest["files"]
    if sorted(row["path"] for row in declared) != actual:
        raise ValueError("file census drift")
    for row in declared:
        path = root / row["path"]
        if path.is_symlink() or not path.is_file():
            raise ValueError("artifact type drift")
        raw = path.read_bytes()
        if len(raw) != row["bytes"] or hashlib.sha256(raw).hexdigest() != row["sha256"]:
            raise ValueError("artifact digest drift")
    summary = _load(root / "summary.json")
    boundary = manifest["claim_boundary"]
    if summary["claim_boundary"] != boundary:
        raise ValueError("boundary drift")
    if summary["verdict"] in {"QualificationFailed", "Inconclusive"}:
        if (root / "records.jsonl").exists():
            raise ValueError("early-stop bundle contains evaluation")
        return {"valid": True, "verdict": summary["verdict"]}
    lines = (root / "records.jsonl").read_bytes().splitlines()
    if len(lines) != 3 * 64 * 16 or summary["record_census"] != len(lines):
        raise ValueError("record census drift")
    method_values = {method: [] for method in METHODS}
    previous = ""
    for raw in lines:
        row = json.loads(raw, object_pairs_hook=_pairs)
        if row["record_id"] <= previous:
            raise ValueError("record order drift")
        previous = row["record_id"]
        if row["split"] != "evaluation_v2" or row["family"] not in range(320, 384):
            raise ValueError("holdout drift")
        for method in METHODS:
            regret, _ = normalized_regret(
                row["ablation_effects"], row["scores"][method]
            )
            if abs(regret - row["regrets"][method]) > 1e-7:
                raise ValueError("regret drift")
            if selected(row["scores"][method]) != row["selections"][method]:
                raise ValueError("selection drift")
            method_values[method].append(regret)
    for method, values in method_values.items():
        if abs(sum(values) / len(values) - summary["method_regret"][method]) > 1e-7:
            raise ValueError("method mean drift")
    if summary["verdict"] == "Pass" and not (
        summary["primary_gate"]
        and summary["placebo_gate"]
        and summary["patch_gate"]
        and all(value >= 0.80 for value in summary["informative_coverage"].values())
    ):
        raise ValueError("pass gate drift")
    return {"valid": True, "verdict": summary["verdict"]}
