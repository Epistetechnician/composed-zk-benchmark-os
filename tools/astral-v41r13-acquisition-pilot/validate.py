from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import subprocess
from typing import Any


INSTRUMENT_PATH = Path(__file__).parents[1] / "astral-v41r11-novelty-instrument" / "validate.py"
SPEC = importlib.util.spec_from_file_location("v41r13_instrument", INSTRUMENT_PATH)
assert SPEC and SPEC.loader
INSTRUMENT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(INSTRUMENT)

VERSION = "mesh.astral_v41r13_persistent_acquisition_pilot.v1"
STATE_SLICE = "V41R13PersistentAcquisitionPilotDesignAndExecution"
MODEL = "openai/gpt-oss-20b"
REVISION = "d0e2aa76789354d715f8b22553b9feb6c462fcf0"
CONFIG = "sha256:3a2a26ded679375b7928ddeca59764df7cea83220c1961035f6d6e232659e9ce"
CLASSES = ("direct", "paraphrase", "composition")


def canonical_hash(value: Any) -> str:
    return "sha256:" + hashlib.sha256(json.dumps(value, allow_nan=False, separators=(",", ":"), sort_keys=True).encode()).hexdigest()


def file_hash(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def metrics(rows: Any) -> dict[str, Any]:
    if not isinstance(rows, list) or len(rows) != 96:
        raise ValueError("query census")
    by_class = {}
    for query_class in CLASSES:
        selected = [row for row in rows if row.get("query_class") == query_class]
        if len(selected) != 32:
            raise ValueError("class census")
        by_class[query_class] = sum(row.get("correct") is True for row in selected) / 32
    correct = sum(row.get("correct") is True for row in rows)
    return {"overall_accuracy": correct / 96, "accuracy_by_class": by_class, "correct": correct, "total": 96}


def protected_accuracy(rows: Any) -> float:
    if not isinstance(rows, list) or len(rows) != 16:
        raise ValueError("protected census")
    return sum(row.get("correct") is True for row in rows) / 16


def validate_rows(rows: Any, *, context: bool | None, label: str) -> list[str]:
    if not isinstance(rows, list):
        return [f"rows:{label}"]
    errors = []
    for row in rows:
        if context is not None and row.get("source_context_present") is not context:
            errors.append(f"context:{label}")
        candidates, scores = row.get("candidates"), row.get("candidate_log_probabilities")
        if not isinstance(candidates, list) or not isinstance(scores, dict) or set(candidates) != set(scores):
            errors.append(f"scores:{label}")
            continue
        values = list(scores.values())
        if len(values) != 4 or any(not isinstance(value, (int, float)) or not math.isfinite(value) for value in values) or abs(sum(math.exp(value) for value in values) - 1.0) > 1.0e-5:
            errors.append(f"probabilities:{label}")
        selected = min(candidates, key=lambda candidate: (-scores[candidate], candidate))
        if row.get("selected") != selected or row.get("correct") is not (selected == row.get("target")):
            errors.append(f"decision:{label}")
    return errors


def expected_contract(instrument_hash: str) -> dict[str, Any]:
    body = {
        "version": "mesh.astral_v41r13_pilot_contract.v1",
        "state_slice": STATE_SLICE,
        "seed": 411013,
        "instrument_sha256": instrument_hash,
        "query_classes": list(CLASSES),
        "query_count_per_class": 32,
        "method": "protected_replay_attention_lora",
        "optimizer_steps": 64,
        "effective_batch_size": 4,
        "acquisition_rows_per_batch": 3,
        "protected_rows_per_batch": 1,
        "protected_count": 16,
        "lora_rank": 8,
        "lora_alpha": 16,
        "learning_rate": 2.0e-4,
        "gradient_clip": 1.0,
        "gates": {"acquisition_overall_minimum": 0.70, "acquisition_class_minimum": 0.60, "acquisition_advantage_minimum": 0.20, "protected_drop_maximum": 0.02, "reload_exact": True},
    }
    return {**body, "contract_sha256": canonical_hash(body)}


def decision(no_update: dict[str, Any], persistent: dict[str, Any], before: float, after: float, reload_exact: bool, steps: int) -> tuple[str, list[str]]:
    errors = []
    if not 0.15 <= no_update["overall_accuracy"] <= 0.35 or any(value > 0.40 for value in no_update["accuracy_by_class"].values()):
        errors.append("baseline_novelty")
    if persistent["overall_accuracy"] < 0.70:
        errors.append("acquisition_overall")
    if any(value < 0.60 for value in persistent["accuracy_by_class"].values()):
        errors.append("acquisition_class")
    if persistent["overall_accuracy"] - no_update["overall_accuracy"] < 0.20:
        errors.append("acquisition_advantage")
    if before - after > 0.02:
        errors.append("protected_drop")
    if reload_exact is not True:
        errors.append("reload_exact")
    if steps != 64:
        errors.append("optimizer_steps")
    return ("PilotAcquisitionSignal" if not errors else "PilotNoSignal", errors)


def validate(
    artifact: Path,
    rgs_root: Path,
    *,
    expected_version: str = VERSION,
    expected_state_slice: str = STATE_SLICE,
    contract_builder=expected_contract,
    decision_builder=decision,
    expected_claim_ceiling: str = "RemoteH100PersistentAcquisitionPilotV41R13",
    runner_relative: str = "scripts/run_v41r13_acquisition_pilot.py",
    method_relative: str = "mesh_brain/meshmodel/v41r13_acquisition_pilot.py",
    report_version: str = "astral.v41r13_acquisition_pilot_validation.v1",
) -> dict[str, Any]:
    result_path, manifest_path, adapter_path = artifact / "pilot-result.json", artifact / "MANIFEST.sha256", artifact / "adapter-state.pt"
    if not all(path.is_file() for path in (result_path, manifest_path, adapter_path)):
        return {"valid": False, "errors": ["pilot artifact files missing"]}
    result = json.loads(result_path.read_text())
    errors: list[str] = []
    body = {key: value for key, value in result.items() if key != "result_sha256"}
    if result.get("result_sha256") != canonical_hash(body):
        errors.append("result_sha256")
    for key, expected in {"version": expected_version, "state_slice": expected_state_slice, "tune_opened": False, "assessment_opened": False}.items():
        if result.get(key) != expected:
            errors.append(key)
    instrument = result.get("instrument")
    instrument_report = INSTRUMENT.validate(instrument)
    if not instrument_report.get("valid"):
        errors.append("instrument")
    if result.get("contract") != contract_builder(instrument_report.get("instrument_sha256")):
        errors.append("contract")
    model, runtime = result.get("model", {}), result.get("runtime", {})
    if model.get("id") != MODEL or model.get("revision") != REVISION:
        errors.append("model")
    for key, expected in {"torch": "2.10.0+cu128", "transformers": "4.57.6", "peft": "0.18.1", "cuda": "12.8"}.items():
        if runtime.get(key) != expected:
            errors.append(f"runtime:{key}")
    if "H100" not in str(runtime.get("gpu", "")).upper():
        errors.append("runtime:gpu")
    if result.get("geometry", {}).get("checkpoint_config_sha256") != CONFIG or result.get("quantization") != {"quant_method": "mxfp4", "dequantize": False}:
        errors.append("model_binding")
    no_rows, persistent_rows = result.get("no_update", {}).get("rows"), result.get("persistent", {}).get("rows")
    before_rows, after_rows = result.get("protected_before", {}).get("rows"), result.get("protected_after", {}).get("rows")
    errors.extend(validate_rows(no_rows, context=False, label="no_update"))
    errors.extend(validate_rows(persistent_rows, context=False, label="persistent"))
    errors.extend(validate_rows(before_rows, context=None, label="protected_before"))
    errors.extend(validate_rows(after_rows, context=None, label="protected_after"))
    try:
        no_update, persistent = metrics(no_rows), metrics(persistent_rows)
        before, after = protected_accuracy(before_rows), protected_accuracy(after_rows)
        if result.get("no_update", {}).get("metrics") != no_update or result.get("persistent", {}).get("metrics") != persistent:
            errors.append("metrics:acquisition")
        if result.get("protected_before", {}).get("accuracy") != before or result.get("protected_after", {}).get("accuracy") != after:
            errors.append("metrics:protected")
    except (TypeError, ValueError):
        errors.append("metrics")
        no_update = persistent = {"overall_accuracy": 0.0, "accuracy_by_class": {key: 0.0 for key in CLASSES}}
        before = after = 0.0
    update, reload = result.get("update", {}), result.get("reload", {})
    receipts, steps = update.get("receipts"), update.get("optimizer_steps", 0)
    if not isinstance(receipts, list) or len(receipts) != 64:
        errors.append("receipts")
    else:
        for index, receipt in enumerate(receipts):
            weights = receipt.get("microbatch_weights")
            if receipt.get("step") != index or receipt.get("microbatch_count") != 4 or not isinstance(weights, list) or len(weights) != 4 or abs(sum(weights) - 1.0) > 1.0e-12:
                errors.append("receipt_structure")
    if update.get("adapter_file_sha256") != file_hash(adapter_path) or update.get("post_update_state_sha256") != reload.get("state_sha256"):
        errors.append("adapter_binding")
    expected_class, gate_errors = decision_builder(no_update, persistent, before, after, reload.get("state_exact") is True, steps)
    if result.get("classification") != expected_class or result.get("gate_errors") != gate_errors:
        errors.append("decision")
    if result.get("claim_ceiling") != expected_claim_ceiling:
        errors.append("claim_ceiling")
    expected_manifest = "".join(file_hash(path).removeprefix("sha256:") + f"  {path.name}\n" for path in (result_path, adapter_path))
    if manifest_path.read_text() != expected_manifest:
        errors.append("manifest")
    source, commit = result.get("source", {}), result.get("source", {}).get("rgs_commit", "")
    for key, relative in (("runner_sha256", runner_relative), ("pilot_source_sha256", method_relative), ("instrument_source_sha256", "mesh_brain/meshmodel/v41r11_novelty_instrument.py"), ("requirements_sha256", "requirements-v41-h100-profile.txt")):
        try:
            content = subprocess.run(["git", "show", f"{commit}:{relative}"], cwd=rgs_root, check=True, capture_output=True).stdout
            if source.get(key) != "sha256:" + hashlib.sha256(content).hexdigest():
                errors.append(key)
        except (subprocess.CalledProcessError, TypeError):
            errors.append(f"{key}:unavailable")
    return {"version": report_version, "valid": not errors, "errors": sorted(set(errors)), "classification": result.get("classification"), "result_sha256": result.get("result_sha256"), "claim_ceiling": result.get("claim_ceiling") if not errors else None}


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
