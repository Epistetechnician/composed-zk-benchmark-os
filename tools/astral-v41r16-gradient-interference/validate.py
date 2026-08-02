from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess
from typing import Any


VERSION = "mesh.astral_v41r16_gradient_interference_profile.v1"
STATE_SLICE = "V41R16GradientInterferenceProfileDesignAndExecution"
MODEL = "openai/gpt-oss-20b"
REVISION = "d0e2aa76789354d715f8b22553b9feb6c462fcf0"
CONFIG = "sha256:3a2a26ded679375b7928ddeca59764df7cea83220c1961035f6d6e232659e9ce"
V41R15_RESULT = "sha256:893451b417e6654096e87e7494e638f37daf0efe5cb73c2eacf28a6b415966b3"
PANELS = ("bridge", "terminal", "protected")
PAIRS = {
    "bridge_terminal": ("bridge", "terminal"),
    "bridge_protected": ("bridge", "protected"),
    "terminal_protected": ("terminal", "protected"),
    "acquisition_protected": ("acquisition", "protected"),
}
LAYER = re.compile(r"\.layers\.(\d+)\.")


def canonical_hash(value: Any) -> str:
    return "sha256:" + hashlib.sha256(json.dumps(value, allow_nan=False, separators=(",", ":"), sort_keys=True).encode()).hexdigest()


def file_hash(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def expected_contract(instrument_hash: str) -> dict[str, Any]:
    body = {
        "version": "mesh.astral_v41r16_gradient_contract.v1",
        "state_slice": STATE_SLICE,
        "instrument_sha256": instrument_hash,
        "source_v41r15_result_sha256": V41R15_RESULT,
        "seed": 411013,
        "panels": list(PANELS),
        "panel_examples": {"bridge": 32, "terminal": 32, "protected": 16},
        "gradient_reduction": "equal_example_mean",
        "adapter_state": "initialized_rank8_alpha16_qkvo_all24",
        "optimizer_constructed": False,
        "optimizer_steps": 0,
        "parameter_update_permitted": False,
        "raw_gradient_artifact_required": True,
        "pairwise_geometry": list(PAIRS),
        "selection_rule": None,
        "tune_opened": False,
        "assessment_opened": False,
    }
    return {**body, "contract_sha256": canonical_hash(body)}


def _layer(name: str) -> int:
    match = LAYER.search(name)
    if match is None:
        raise ValueError(name)
    return int(match.group(1))


def _geometry(left: dict[str, Any], right: dict[str, Any], names: list[str]) -> dict[str, float | None]:
    dot = left_norm = right_norm = 0.0
    for name in names:
        a = left[name].detach().double().reshape(-1)
        b = right[name].detach().double().reshape(-1)
        dot += float((a * b).sum().item())
        left_norm += float((a * a).sum().item())
        right_norm += float((b * b).sum().item())
    denominator = math.sqrt(left_norm * right_norm)
    return {"left_norm": math.sqrt(left_norm), "right_norm": math.sqrt(right_norm), "dot": dot, "cosine": dot / denominator if denominator > 0.0 else None}


def recompute(panels: Any) -> tuple[dict[str, Any] | None, list[str]]:
    errors: list[str] = []
    if not isinstance(panels, dict) or set(panels) != set(PANELS):
        return None, ["panel_names"]
    names = [set(panels[key]) for key in PANELS]
    if any(len(value) != 192 for value in names):
        errors.append("tensor_count")
    if any(value != names[0] for value in names[1:]):
        errors.append("tensor_names")
    try:
        if {_layer(name) for name in names[0]} != set(range(24)):
            errors.append("layer_coverage")
    except ValueError:
        errors.append("layer_binding")
    for panel in PANELS:
        for tensor in panels[panel].values():
            if getattr(tensor, "ndim", None) is None or not bool(tensor.is_floating_point()):
                errors.append("tensor_type")
                break
            if not bool(tensor.isfinite().all().item()):
                errors.append("tensor_finite")
                break
    if errors:
        return None, sorted(set(errors))
    acquisition = {
        name: (panels["bridge"][name].detach().double() + panels["terminal"][name].detach().double()) / 2.0
        for name in names[0]
    }
    augmented = {**panels, "acquisition": acquisition}
    ordered = sorted(names[0])
    global_geometry = {key: _geometry(augmented[left], augmented[right], ordered) for key, (left, right) in PAIRS.items()}
    by_layer = []
    for layer in range(24):
        selected = [name for name in ordered if _layer(name) == layer]
        by_layer.append({"layer": layer, "tensor_count": len(selected), "pairs": {key: _geometry(augmented[left], augmented[right], selected) for key, (left, right) in PAIRS.items()}})
    return {
        "global": global_geometry,
        "by_layer": by_layer,
        "negative_layer_counts": {
            key: sum(row["pairs"][key]["cosine"] is not None and row["pairs"][key]["cosine"] < 0.0 for row in by_layer)
            for key in PAIRS
        },
    }, []


def close(left: Any, right: Any) -> bool:
    if isinstance(left, dict) and isinstance(right, dict) and set(left) == set(right):
        return all(close(left[key], right[key]) for key in left)
    if isinstance(left, list) and isinstance(right, list) and len(left) == len(right):
        return all(close(a, b) for a, b in zip(left, right, strict=True))
    if isinstance(left, (int, float)) and isinstance(right, (int, float)):
        return math.isclose(float(left), float(right), rel_tol=1.0e-12, abs_tol=1.0e-12)
    return left == right


def valid_torch_runtime(runtime: dict[str, Any]) -> bool:
    # PyPI distribution metadata omits the CUDA local-version suffix that
    # torch.__version__ exposes. CUDA is bound independently below, so both
    # metadata spellings identify the same frozen torch 2.10/cu128 runtime.
    return runtime.get("torch") in {"2.10.0", "2.10.0+cu128"} and runtime.get("cuda") == "12.8"


def validate(artifact: Path, rgs_root: Path) -> dict[str, Any]:
    result_path = artifact / "profile-result.json"
    gradients_path = artifact / "gradient-state.pt"
    manifest_path = artifact / "MANIFEST.sha256"
    if not all(path.is_file() for path in (result_path, gradients_path, manifest_path)):
        return {"valid": False, "errors": ["profile artifact files missing"]}
    result = json.loads(result_path.read_text())
    errors: list[str] = []
    body = {key: value for key, value in result.items() if key != "result_sha256"}
    if result.get("result_sha256") != canonical_hash(body):
        errors.append("result_sha256")
    for key, expected in {
        "version": VERSION,
        "state_slice": STATE_SLICE,
        "classification": "GradientInterferenceProfileComplete",
        "optimizer_constructed": False,
        "optimizer_steps": 0,
        "tune_opened": False,
        "assessment_opened": False,
    }.items():
        if result.get(key) != expected:
            errors.append(key)
    instrument_hash = result.get("instrument_sha256")
    if result.get("contract") != expected_contract(instrument_hash):
        errors.append("contract")
    if result.get("source_v41r15_result_sha256") != V41R15_RESULT:
        errors.append("v41r15_binding")
    model, runtime = result.get("model", {}), result.get("runtime", {})
    if model.get("id") != MODEL or model.get("revision") != REVISION:
        errors.append("model")
    for key, expected in {"transformers": "4.57.6", "peft": "0.18.1", "cuda": "12.8"}.items():
        if runtime.get(key) != expected:
            errors.append(f"runtime:{key}")
    if not valid_torch_runtime(runtime):
        errors.append("runtime:torch")
    if "H100" not in str(runtime.get("gpu", "")).upper():
        errors.append("runtime:gpu")
    if result.get("geometry", {}).get("checkpoint_config_sha256") != CONFIG or result.get("quantization") != {"quant_method": "mxfp4", "dequantize": False}:
        errors.append("model_binding")
    inventory = result.get("inventory", {})
    if inventory.get("layers") != 24 or inventory.get("trainable_tensors") != 192 or inventory.get("trainable_parameters") != 3981312:
        errors.append("inventory")
    state = result.get("state", {})
    if state.get("exact") is not True or state.get("before_sha256") != state.get("after_sha256"):
        errors.append("state_exact")
    gradient = result.get("gradient_artifact", {})
    if gradient.get("sha256") != file_hash(gradients_path) or gradient.get("panels") != list(PANELS) or gradient.get("tensor_count_per_panel") != 192:
        errors.append("gradient_binding")
    try:
        import torch

        panels = torch.load(gradients_path, map_location="cpu", weights_only=True)
        summary, panel_errors = recompute(panels)
        errors.extend(panel_errors)
        if summary is not None and not close(summary, result.get("summary")):
            errors.append("summary")
    except (OSError, RuntimeError, TypeError, ValueError):
        errors.append("gradient_load")
    losses = result.get("panel_losses", {})
    if set(losses) != set(PANELS) or any(not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0.0 for value in losses.values()):
        errors.append("panel_losses")
    expected_manifest = "".join(file_hash(path).removeprefix("sha256:") + f"  {path.name}\n" for path in (result_path, gradients_path))
    if manifest_path.read_text() != expected_manifest:
        errors.append("manifest")
    source, commit = result.get("source", {}), result.get("source", {}).get("rgs_commit", "")
    for key, relative in (
        ("runner_sha256", "scripts/run_v41r16_gradient_interference_profile.py"),
        ("profile_source_sha256", "mesh_brain/meshmodel/v41r16_gradient_interference.py"),
        ("instrument_source_sha256", "mesh_brain/meshmodel/v41r11_novelty_instrument.py"),
        ("requirements_sha256", "requirements-v41-h100-profile.txt"),
    ):
        try:
            content = subprocess.run(["git", "show", f"{commit}:{relative}"], cwd=rgs_root, check=True, capture_output=True).stdout
            if source.get(key) != "sha256:" + hashlib.sha256(content).hexdigest():
                errors.append(key)
            if key == "runner_sha256" and any(
                marker in content for marker in (b"torch.optim.", b"optimizer.step(", b"score_rows")
            ):
                errors.append("runner_forbidden_operation")
        except (subprocess.CalledProcessError, TypeError):
            errors.append(f"{key}:unavailable")
    if result.get("claim_ceiling") != "RemoteH100GradientInterferenceDiagnosticV41R16":
        errors.append("claim_ceiling")
    errors = sorted(set(errors))
    return {
        "version": "astral.v41r16_gradient_interference_validation.v1",
        "valid": not errors,
        "errors": errors,
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
