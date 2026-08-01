from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
from pathlib import Path
from typing import Any


EXPECTED_VERSION = "mesh.astral_v41r10_single_task_acquisition_pilot.v1"
EXPECTED_SLICE = "V41R10AcquisitionPilotDesignAndImplementation"
EXPECTED_MODEL = "openai/gpt-oss-20b"
EXPECTED_REVISION = "d0e2aa76789354d715f8b22553b9feb6c462fcf0"
EXPECTED_CORPUS = "sha256:ab1c096ae51f72db83a0680f760cf3670da699b0745668272a8dc2cd74c85b3c"
EXPECTED_CONFIG = "sha256:3a2a26ded679375b7928ddeca59764df7cea83220c1961035f6d6e232659e9ce"
QUERY_CLASSES = ("direct", "paraphrase", "composition")
EXPECTED_RUNTIME = {
    "torch": "2.10.0+cu128",
    "transformers": "4.57.6",
    "peft": "0.18.1",
    "cuda": "12.8",
}
MODEL_READY_MAX_BYTES = 24 * 1024**3
ADAPTER_READY_MAX_BYTES = 32 * 1024**3
RUNTIME_PEAK_MAX_BYTES = 72 * 1024**3


def canonical_hash(value: Any) -> str:
    encoded = json.dumps(value, allow_nan=False, separators=(",", ":"), sort_keys=True).encode()
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def file_hash(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def metrics(rows: Any) -> dict[str, Any]:
    if not isinstance(rows, list) or len(rows) != 48:
        raise ValueError("row count")
    by_class: dict[str, float] = {}
    for query_class in QUERY_CLASSES:
        selected = [row for row in rows if row.get("query_class") == query_class]
        if len(selected) != 16:
            raise ValueError(f"class count:{query_class}")
        by_class[query_class] = sum(row.get("correct") is True for row in selected) / 16
    return {
        "overall_accuracy": sum(row.get("correct") is True for row in rows) / 48,
        "accuracy_by_class": by_class,
        "correct": sum(row.get("correct") is True for row in rows),
        "total": 48,
    }


def protected_accuracy(rows: Any) -> float:
    if not isinstance(rows, list) or len(rows) != 16:
        raise ValueError("protected count")
    return sum(row.get("correct") is True for row in rows) / 16


def validate_scored_rows(rows: Any, *, context_present: bool, label: str) -> list[str]:
    if not isinstance(rows, list):
        return [f"rows:{label}"]
    errors: list[str] = []
    for row in rows:
        if row.get("source_context_present") is not context_present:
            errors.append(f"context:{label}")
        scores = row.get("candidate_log_probabilities")
        candidates = row.get("candidates")
        if not isinstance(scores, dict) or not isinstance(candidates, list) or set(scores) != set(candidates):
            errors.append(f"scores:{label}")
            continue
        values = list(scores.values())
        if (
            len(values) != 4
            or any(not isinstance(value, (int, float)) or not math.isfinite(value) for value in values)
            or abs(sum(math.exp(value) for value in values) - 1.0) > 1.0e-5
        ):
            errors.append(f"probabilities:{label}")
        selected = min(candidates, key=lambda candidate: (-scores[candidate], candidate))
        if row.get("selected") != selected or row.get("correct") is not (selected == row.get("target")):
            errors.append(f"decision:{label}")
    return errors


def expected_contract() -> dict[str, Any]:
    body = {
        "version": "mesh.astral_v41r10_pilot_contract.v1",
        "state_slice": EXPECTED_SLICE,
        "task_id": "A",
        "seed": 410041,
        "query_classes": list(QUERY_CLASSES),
        "query_count_per_class": 16,
        "protected_count": 16,
        "arms": ["no_update", "context_only", "sequential_attention_lora"],
        "optimizer_steps": 32,
        "effective_batch_size": 4,
        "microbatch_size": 1,
        "corpus_sha256": EXPECTED_CORPUS,
        "gates": {
            "preupdate_overall_lower": 0.15,
            "preupdate_overall_upper": 0.35,
            "preupdate_class_maximum": 0.40,
            "context_overall_minimum": 0.90,
            "context_class_minimum": 0.85,
            "acquisition_overall_minimum": 0.70,
            "acquisition_class_minimum": 0.60,
            "acquisition_advantage_minimum": 0.20,
            "protected_drop_maximum": 0.02,
        },
    }
    return {**body, "contract_sha256": canonical_hash(body)}


def classification(
    no_update: dict[str, Any],
    context_only: dict[str, Any],
    persistent: dict[str, Any] | None,
    protected_before: float,
    protected_after: float | None,
    reload_exact: bool,
    steps: int,
) -> tuple[str, list[str]]:
    preflight = []
    if not 0.15 <= no_update["overall_accuracy"] <= 0.35:
        preflight.append("preupdate_overall")
    if any(value > 0.40 for value in no_update["accuracy_by_class"].values()):
        preflight.append("preupdate_class")
    if context_only["overall_accuracy"] < 0.90:
        preflight.append("context_overall")
    if any(value < 0.85 for value in context_only["accuracy_by_class"].values()):
        preflight.append("context_class")
    if preflight:
        return "PilotInstrumentInvalid", preflight
    errors: list[str] = []
    if persistent is None or protected_after is None:
        errors.append("persistent_missing")
    else:
        if persistent["overall_accuracy"] < 0.70:
            errors.append("acquisition_overall")
        if any(value < 0.60 for value in persistent["accuracy_by_class"].values()):
            errors.append("acquisition_class")
        if persistent["overall_accuracy"] - no_update["overall_accuracy"] < 0.20:
            errors.append("acquisition_advantage")
        if protected_before - protected_after > 0.02:
            errors.append("protected_drop")
    if reload_exact is not True:
        errors.append("reload_exact")
    if steps != 32:
        errors.append("optimizer_steps")
    return ("PilotAcquisitionSignal" if not errors else "PilotNoSignal"), errors


def validate(artifact: Path, rgs_root: Path) -> dict[str, Any]:
    result_path = artifact / "pilot-result.json"
    manifest_path = artifact / "MANIFEST.sha256"
    if not result_path.is_file() or not manifest_path.is_file():
        return {"valid": False, "errors": ["pilot artifact files missing"]}
    errors: list[str] = []
    result = json.loads(result_path.read_text())
    body = {key: value for key, value in result.items() if key != "result_sha256"}
    if result.get("result_sha256") != canonical_hash(body):
        errors.append("result_sha256")
    for key, value in {
        "version": EXPECTED_VERSION,
        "state_slice": EXPECTED_SLICE,
        "tune_opened": False,
        "assessment_opened": False,
        "scientific_result": False,
    }.items():
        if result.get(key) != value:
            errors.append(key)
    if result.get("contract") != expected_contract():
        errors.append("contract")
    model = result.get("model", {})
    if model.get("id") != EXPECTED_MODEL or model.get("revision") != EXPECTED_REVISION:
        errors.append("model")
    runtime = result.get("runtime", {})
    for key, value in EXPECTED_RUNTIME.items():
        if runtime.get(key) != value:
            errors.append(f"runtime:{key}")
    if "H100" not in str(runtime.get("gpu", "")).upper():
        errors.append("runtime:gpu")
    geometry = result.get("geometry", {})
    if (
        geometry.get("model_type") != "gpt_oss"
        or geometry.get("num_hidden_layers") != 24
        or geometry.get("checkpoint_config_sha256") != EXPECTED_CONFIG
        or len(geometry.get("layer_types", [])) != 24
    ):
        errors.append("geometry")
    if result.get("quantization") != {"quant_method": "mxfp4", "dequantize": False}:
        errors.append("quantization")

    no_update_rows = result.get("no_update", {}).get("rows")
    context_rows = result.get("context_only", {}).get("rows")
    before_rows = result.get("protected_before", {}).get("rows")
    errors.extend(validate_scored_rows(no_update_rows, context_present=False, label="no_update"))
    errors.extend(validate_scored_rows(context_rows, context_present=True, label="context_only"))
    try:
        no_update = metrics(no_update_rows)
        context_only = metrics(context_rows)
        before = protected_accuracy(before_rows)
        if result.get("no_update", {}).get("metrics") != no_update:
            errors.append("metrics:no_update")
        if result.get("context_only", {}).get("metrics") != context_only:
            errors.append("metrics:context_only")
        if result.get("protected_before", {}).get("accuracy") != before:
            errors.append("metrics:protected_before")
    except (TypeError, ValueError):
        errors.append("baseline structure")
        no_update = {"overall_accuracy": 0.0, "accuracy_by_class": {key: 0.0 for key in QUERY_CLASSES}}
        context_only = no_update
        before = 0.0

    persistent = None
    after = None
    reload_exact = False
    steps = 0
    if result.get("update_executed") is True:
        persistent_rows = result.get("persistent", {}).get("rows")
        after_rows = result.get("protected_after", {}).get("rows")
        errors.extend(validate_scored_rows(persistent_rows, context_present=False, label="persistent"))
        try:
            persistent = metrics(persistent_rows)
            after = protected_accuracy(after_rows)
            if result.get("persistent", {}).get("metrics") != persistent:
                errors.append("metrics:persistent")
            if result.get("protected_after", {}).get("accuracy") != after:
                errors.append("metrics:protected_after")
        except (TypeError, ValueError):
            errors.append("persistent structure")
        reload = result.get("reload", {})
        reload_exact = reload.get("state_exact") is True
        update = result.get("update", {})
        receipts = update.get("receipts")
        steps = update.get("optimizer_steps", 0)
        if not isinstance(receipts, list) or len(receipts) != 32 or steps != 32:
            errors.append("optimizer steps")
        else:
            for index, receipt in enumerate(receipts):
                weights = receipt.get("microbatch_weights")
                if (
                    receipt.get("step") != index
                    or receipt.get("microbatch_count") != 4
                    or not isinstance(weights, list)
                    or len(weights) != 4
                    or abs(sum(weights) - 1.0) > 1.0e-12
                ):
                    errors.append("step receipts")
        if update.get("post_update_state_sha256") != reload.get("state_sha256"):
            errors.append("reload hash")
        adapter = artifact / str(update.get("adapter_file", ""))
        if not adapter.is_file() or update.get("adapter_file_sha256") != file_hash(adapter):
            errors.append("adapter file")
        for packet, key, ceiling, label in (
            (result.get("model_ready_memory"), "allocated_bytes", MODEL_READY_MAX_BYTES, "model_ready"),
            (update.get("adapter_ready_memory"), "allocated_bytes", ADAPTER_READY_MAX_BYTES, "adapter_ready"),
            (update.get("update_memory"), "peak_allocated_bytes", RUNTIME_PEAK_MAX_BYTES, "update_peak"),
        ):
            if not isinstance(packet, dict) or not isinstance(packet.get(key), int) or packet[key] > ceiling:
                errors.append(f"memory:{label}")

    expected_class, gate_errors = classification(
        no_update, context_only, persistent, before, after, reload_exact, steps
    )
    if result.get("classification") != expected_class:
        errors.append("classification")
    if result.get("gate_errors") != gate_errors:
        errors.append("gate_errors")
    expected_ceiling = (
        "RemoteH100InstrumentInvalidV41R10"
        if expected_class == "PilotInstrumentInvalid"
        else "RemoteH100SingleTaskAcquisitionPilotV41R10"
    )
    if result.get("claim_ceiling") != expected_ceiling:
        errors.append("claim_ceiling")

    manifest_rows = []
    for name in ("pilot-result.json", "adapter-state.pt"):
        path = artifact / name
        if path.is_file():
            manifest_rows.append(file_hash(path).removeprefix("sha256:") + f"  {name}\n")
    if manifest_path.read_text() != "".join(manifest_rows):
        errors.append("manifest")

    source = result.get("source", {})
    commit = source.get("rgs_commit", "")
    for key, relative in (
        ("runner_sha256", "scripts/run_v41r10_acquisition_pilot.py"),
        ("pilot_source_sha256", "mesh_brain/meshmodel/v41r10_acquisition_pilot.py"),
        ("geometry_source_sha256", "mesh_brain/meshmodel/v41r9_checkpoint_geometry.py"),
        ("contract_source_sha256", "mesh_brain/meshmodel/v41_h100_acquisition.py"),
        ("requirements_sha256", "requirements-v41-h100-profile.txt"),
    ):
        try:
            content = subprocess.run(
                ["git", "show", f"{commit}:{relative}"],
                cwd=rgs_root,
                check=True,
                capture_output=True,
            ).stdout
            if source.get(key) != "sha256:" + hashlib.sha256(content).hexdigest():
                errors.append(key)
        except (subprocess.CalledProcessError, TypeError):
            errors.append(f"{key} unavailable")
    return {
        "version": "astral.v41r10_acquisition_pilot_validation.v1",
        "valid": not errors,
        "errors": sorted(set(errors)),
        "artifact": str(artifact),
        "classification": result.get("classification"),
        "result_sha256": result.get("result_sha256"),
        "claim_ceiling": result.get("claim_ceiling") if not errors else None,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact", type=Path, required=True)
    parser.add_argument("--rgs-root", type=Path, required=True)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args(argv)
    report = validate(args.artifact.resolve(), args.rgs_root.resolve())
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.report:
        args.report.write_text(text)
    print(text, end="")
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
