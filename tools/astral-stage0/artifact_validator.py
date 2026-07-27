"""Strict validator for Stage 0 local measurement bundles."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

DECLARED_FILES = ("config.json", "records.jsonl", "summary.json")


def _reject_duplicate(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _check_finite(value: object) -> None:
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError("non-finite number")
    if isinstance(value, dict):
        for child in value.values():
            _check_finite(child)
    elif isinstance(value, list):
        for child in value:
            _check_finite(child)


def load_json(path: Path) -> object:
    raw = path.read_bytes()
    value = json.loads(raw, object_pairs_hook=_reject_duplicate)
    canonical = (
        json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)
        + "\n"
    ).encode()
    if raw != canonical:
        raise ValueError(f"noncanonical JSON: {path.name}")
    _check_finite(value)
    return value


def validate_bundle(root: Path) -> dict[str, object]:
    if root.is_symlink() or not root.is_dir():
        raise ValueError("bundle root must be a real directory")
    names = tuple(sorted(path.name for path in root.iterdir()))
    expected = tuple(sorted((*DECLARED_FILES, "manifest.json")))
    if names != expected:
        raise ValueError("bundle file census mismatch")
    manifest = load_json(root / "manifest.json")
    config = load_json(root / "config.json")
    summary = load_json(root / "summary.json")
    if (
        not isinstance(manifest, dict)
        or manifest.get("schema") != "astral.stage0.manifest.v1"
    ):
        raise ValueError("manifest schema mismatch")
    boundary = manifest.get("claim_boundary")
    if boundary != {
        "accepted_evidence": False,
        "level": "local_measurement_regression",
        "mechanistic_understanding": False,
        "self_modeling": False,
    }:
        raise ValueError("claim boundary escalation")
    declared = manifest.get("files")
    if not isinstance(declared, list) or len(declared) != len(DECLARED_FILES):
        raise ValueError("manifest file declarations mismatch")
    for row in declared:
        if not isinstance(row, dict) or row.get("path") not in DECLARED_FILES:
            raise ValueError("invalid manifest row")
        raw = (root / str(row["path"])).read_bytes()
        if row.get("bytes") != len(raw):
            raise ValueError("file byte count drift")
        if row.get("sha256") != hashlib.sha256(raw).hexdigest():
            raise ValueError("file digest drift")
    declared_paths = [row["path"] for row in declared]
    if sorted(declared_paths) != sorted(DECLARED_FILES):
        raise ValueError("manifest paths must be unique and complete")
    for name in (*DECLARED_FILES, "manifest.json"):
        path = root / name
        if path.is_symlink() or not path.is_file():
            raise ValueError("bundle children must be regular non-symlink files")
    if (
        not isinstance(config, dict)
        or config.get("schema") != "astral.stage0.config.v1"
    ):
        raise ValueError("config schema mismatch")
    if (
        not isinstance(summary, dict)
        or summary.get("schema") != "astral.stage0.summary.v1"
    ):
        raise ValueError("summary schema mismatch")
    if summary.get("claim_boundary") != boundary:
        raise ValueError("summary claim boundary drift")
    if summary.get("gate") not in {
        "positive_control_pass",
        "positive_control_fail",
    }:
        raise ValueError("scientific gate escalation")
    if summary.get("thresholds_registered_for_scientific_exit") is not False:
        raise ValueError("threshold registration drift")
    if config.get("candidate_components") != [
        "layer0.attn.distractor",
        "layer0.attn.signal",
    ]:
        raise ValueError("component census drift")
    if config.get("methods") != [
        "activation_magnitude",
        "candidate_tracer",
        "reversed_tracer",
        "zero",
    ]:
        raise ValueError("method census drift")
    lines = (root / "records.jsonl").read_bytes().splitlines(keepends=True)
    census = summary.get("census")
    if not isinstance(census, dict) or len(lines) != census.get("records"):
        raise ValueError("record census drift")
    previous = ""
    method_regrets = {method: [] for method in config["methods"]}
    for line in lines:
        row = json.loads(line, object_pairs_hook=_reject_duplicate)
        canonical = (
            json.dumps(row, sort_keys=True, separators=(",", ":"), allow_nan=False)
            + "\n"
        ).encode()
        if line != canonical:
            raise ValueError("noncanonical JSONL")
        record_id = row.get("record_id")
        if not isinstance(record_id, str) or record_id <= previous:
            raise ValueError("record ordering or identity drift")
        previous = record_id
        _check_finite(row)
        required = {
            "record_id",
            "ablation_effects",
            "base_label",
            "base_logits",
            "distractor",
            "donor_example_id",
            "expected_label",
            "family",
            "hooks",
            "patch_effects",
            "predictions",
            "regrets",
            "seed",
            "signal",
            "split",
        }
        if set(row) != required:
            raise ValueError("record schema drift")
        measured = row["ablation_effects"]
        predictions = row["predictions"]
        regrets = row["regrets"]
        if (
            not isinstance(measured, dict)
            or set(measured) != set(config["candidate_components"])
            or not isinstance(predictions, dict)
            or set(predictions) != set(config["methods"])
            or not isinstance(regrets, dict)
            or set(regrets) != set(config["methods"])
        ):
            raise ValueError("record method or component drift")
        best = max(abs(float(value)) for value in measured.values())
        for method in config["methods"]:
            scores = predictions[method]
            if not isinstance(scores, dict) or set(scores) != set(measured):
                raise ValueError("prediction census drift")
            selected = min(
                measured,
                key=lambda component: (-abs(float(scores[component])), component),
            )
            expected_regret = best - abs(float(measured[selected]))
            if abs(float(regrets[method]) - expected_regret) > 1e-12:
                raise ValueError("record regret mismatch")
            method_regrets[method].append(expected_regret)
    per_method = summary.get("per_method")
    if not isinstance(per_method, dict) or set(per_method) != set(method_regrets):
        raise ValueError("summary method census drift")
    for method, values in method_regrets.items():
        row = per_method[method]
        expected_mean = sum(values) / len(values)
        if row.get("n") != len(values):
            raise ValueError("summary method count drift")
        if abs(float(row.get("mean_selection_regret")) - expected_mean) > 1e-12:
            raise ValueError("summary method mean drift")
    expected_improvement = (
        sum(method_regrets["activation_magnitude"])
        / len(method_regrets["activation_magnitude"])
        - sum(method_regrets["candidate_tracer"])
        / len(method_regrets["candidate_tracer"])
    )
    if (
        abs(
            float(summary.get("mean_baseline_minus_tracer_regret"))
            - expected_improvement
        )
        > 1e-12
    ):
        raise ValueError("summary primary estimate drift")
    return {
        "schema": "astral.stage0.validation.v1",
        "bundle_sha256": hashlib.sha256(
            (root / "manifest.json").read_bytes()
        ).hexdigest(),
        "valid": True,
    }
