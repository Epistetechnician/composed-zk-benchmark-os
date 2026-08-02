from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import subprocess
from typing import Any


INSTRUMENT_VALIDATOR = Path(__file__).parents[1] / "astral-v41r11-novelty-instrument" / "validate.py"
SPEC = importlib.util.spec_from_file_location("v41r11_instrument_validator", INSTRUMENT_VALIDATOR)
assert SPEC and SPEC.loader
INSTRUMENT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(INSTRUMENT)

EXPECTED_VERSION = "mesh.astral_v41r11_model_backed_novelty_preflight.v1"
EXPECTED_SLICE = "V41R11NoveltyInstrumentDesignAndLocalQualification"
EXPECTED_MODEL = "openai/gpt-oss-20b"
EXPECTED_REVISION = "d0e2aa76789354d715f8b22553b9feb6c462fcf0"
EXPECTED_CONFIG = "sha256:3a2a26ded679375b7928ddeca59764df7cea83220c1961035f6d6e232659e9ce"
QUERY_CLASSES = ("direct", "paraphrase", "composition")
EXPECTED_RUNTIME = {
    "torch": "2.10.0+cu128",
    "transformers": "4.57.6",
    "peft": "0.18.1",
    "cuda": "12.8",
}


def canonical_hash(value: Any) -> str:
    encoded = json.dumps(value, allow_nan=False, separators=(",", ":"), sort_keys=True).encode()
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def file_hash(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def metrics(rows: Any) -> dict[str, Any]:
    if not isinstance(rows, list) or len(rows) != 96:
        raise ValueError("row_count")
    by_class = {}
    for query_class in QUERY_CLASSES:
        selected = [row for row in rows if row.get("query_class") == query_class]
        if len(selected) != 32:
            raise ValueError(f"class_count:{query_class}")
        by_class[query_class] = sum(row.get("correct") is True for row in selected) / 32
    correct = sum(row.get("correct") is True for row in rows)
    return {
        "overall_accuracy": correct / 96,
        "accuracy_by_class": by_class,
        "correct": correct,
        "total": 96,
    }


def validate_rows(rows: Any, *, context: bool, label: str) -> list[str]:
    if not isinstance(rows, list):
        return [f"rows:{label}"]
    errors = []
    for row in rows:
        if row.get("source_context_present") is not context:
            errors.append(f"context:{label}")
        candidates = row.get("candidates")
        scores = row.get("candidate_log_probabilities")
        if not isinstance(candidates, list) or not isinstance(scores, dict) or set(candidates) != set(scores):
            errors.append(f"scores:{label}")
            continue
        values = list(scores.values())
        if len(values) != 4 or any(not isinstance(value, (int, float)) or not math.isfinite(value) for value in values):
            errors.append(f"probabilities:{label}")
            continue
        if abs(sum(math.exp(value) for value in values) - 1.0) > 1.0e-5:
            errors.append(f"normalization:{label}")
        selected = min(candidates, key=lambda candidate: (-scores[candidate], candidate))
        if row.get("selected") != selected or row.get("correct") is not (selected == row.get("target")):
            errors.append(f"decision:{label}")
    return errors


def decision(no_update: dict[str, Any], context_only: dict[str, Any]) -> tuple[str, list[str]]:
    errors = []
    if not 0.15 <= no_update["overall_accuracy"] <= 0.35:
        errors.append("no_update_overall")
    if any(value > 0.40 for value in no_update["accuracy_by_class"].values()):
        errors.append("no_update_class")
    if context_only["overall_accuracy"] < 0.90:
        errors.append("context_overall")
    if any(value < 0.85 for value in context_only["accuracy_by_class"].values()):
        errors.append("context_class")
    return ("NoveltyPreflightPassed" if not errors else "NoveltyPreflightFailed", errors)


def validate(artifact: Path, rgs_root: Path) -> dict[str, Any]:
    result_path = artifact / "preflight-result.json"
    manifest_path = artifact / "MANIFEST.sha256"
    if not result_path.is_file() or not manifest_path.is_file():
        return {"valid": False, "errors": ["preflight artifact files missing"]}
    result = json.loads(result_path.read_text())
    errors: list[str] = []
    body = {key: value for key, value in result.items() if key != "result_sha256"}
    if result.get("result_sha256") != canonical_hash(body):
        errors.append("result_sha256")
    for key, expected in {
        "version": EXPECTED_VERSION,
        "state_slice": EXPECTED_SLICE,
        "adapter_constructed": False,
        "update_executed": False,
        "optimizer_steps": 0,
        "tune_opened": False,
        "assessment_opened": False,
    }.items():
        if result.get(key) != expected:
            errors.append(key)
    instrument_report = INSTRUMENT.validate(result.get("instrument"))
    if not instrument_report.get("valid"):
        errors.append("instrument")
    model = result.get("model", {})
    if model.get("id") != EXPECTED_MODEL or model.get("revision") != EXPECTED_REVISION:
        errors.append("model")
    runtime = result.get("runtime", {})
    for key, expected in EXPECTED_RUNTIME.items():
        if runtime.get(key) != expected:
            errors.append(f"runtime:{key}")
    if "H100" not in str(runtime.get("gpu", "")).upper():
        errors.append("runtime:gpu")
    geometry = result.get("geometry", {})
    if geometry.get("checkpoint_config_sha256") != EXPECTED_CONFIG or geometry.get("num_hidden_layers") != 24:
        errors.append("geometry")
    if result.get("quantization") != {"quant_method": "mxfp4", "dequantize": False}:
        errors.append("quantization")
    no_rows = result.get("no_update", {}).get("rows")
    context_rows = result.get("context_only", {}).get("rows")
    errors.extend(validate_rows(no_rows, context=False, label="no_update"))
    errors.extend(validate_rows(context_rows, context=True, label="context_only"))
    try:
        no_update = metrics(no_rows)
        context_only = metrics(context_rows)
        if result.get("no_update", {}).get("metrics") != no_update:
            errors.append("metrics:no_update")
        if result.get("context_only", {}).get("metrics") != context_only:
            errors.append("metrics:context_only")
    except (TypeError, ValueError):
        errors.append("metrics")
        no_update = {"overall_accuracy": 0.0, "accuracy_by_class": {key: 0.0 for key in QUERY_CLASSES}}
        context_only = no_update
    expected_class, gate_errors = decision(no_update, context_only)
    if result.get("classification") != expected_class:
        errors.append("classification")
    if result.get("gate_errors") != gate_errors:
        errors.append("gate_errors")
    expected_ceiling = (
        "RemoteH100ModelBackedNoveltyPreflightV41R11"
        if expected_class == "NoveltyPreflightPassed"
        else "RemoteH100NoveltyPreflightFailedV41R11"
    )
    if result.get("claim_ceiling") != expected_ceiling:
        errors.append("claim_ceiling")
    if result.get("scientific_result") is not (expected_class == "NoveltyPreflightPassed"):
        errors.append("scientific_result")
    expected_manifest = file_hash(result_path).removeprefix("sha256:") + "  preflight-result.json\n"
    if manifest_path.read_text() != expected_manifest:
        errors.append("manifest")
    source = result.get("source", {})
    commit = source.get("rgs_commit", "")
    for key, relative in (
        ("runner_sha256", "scripts/run_v41r11_novelty_preflight.py"),
        ("instrument_source_sha256", "mesh_brain/meshmodel/v41r11_novelty_instrument.py"),
        ("scorer_source_sha256", "scripts/run_v41_h100_profile.py"),
        ("loader_source_sha256", "scripts/run_v41r10_acquisition_pilot.py"),
        ("requirements_sha256", "requirements-v41-h100-profile.txt"),
    ):
        try:
            content = subprocess.run(
                ["git", "show", f"{commit}:{relative}"], cwd=rgs_root, check=True, capture_output=True
            ).stdout
            if source.get(key) != "sha256:" + hashlib.sha256(content).hexdigest():
                errors.append(key)
        except (subprocess.CalledProcessError, TypeError):
            errors.append(f"{key}:unavailable")
    return {
        "version": "astral.v41r11_novelty_preflight_validation.v1",
        "valid": not errors,
        "errors": sorted(set(errors)),
        "classification": result.get("classification"),
        "result_sha256": result.get("result_sha256"),
        "claim_ceiling": result.get("claim_ceiling") if not errors else None,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact", type=Path, required=True)
    parser.add_argument("--rgs-root", type=Path, required=True)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    report = validate(args.artifact.resolve(), args.rgs_root.resolve())
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.report:
        args.report.write_text(text)
    print(text, end="")
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
