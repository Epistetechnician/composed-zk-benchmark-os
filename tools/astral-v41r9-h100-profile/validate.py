from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import subprocess
from pathlib import Path
from typing import Any

EXPECTED_VERSION = "mesh.astral_v41r9_h100_runtime_profile.v1"
EXPECTED_SLICE = "V41R9CheckpointBoundLayerGeometryCorrection"
EXPECTED_MODEL = "openai/gpt-oss-20b"
EXPECTED_REVISION = "d0e2aa76789354d715f8b22553b9feb6c462fcf0"
EXPECTED_CEILING = "RemoteH100RuntimeProfileOnlyV41R9"
EXPECTED_TARGETS = ["q_proj", "k_proj", "v_proj", "o_proj"]
EXPECTED_CONFIG_SHA256 = (
    "sha256:3a2a26ded679375b7928ddeca59764df7cea83220c1961035f6d6e232659e9ce"
)
EXPECTED_LAYER_TYPES = [
    "sliding_attention" if (index + 1) % 2 else "full_attention"
    for index in range(24)
]
EXPECTED_GEOMETRY = {
    "model_type": "gpt_oss",
    "num_hidden_layers": 24,
    "layer_types": EXPECTED_LAYER_TYPES,
    "checkpoint_config_sha256": EXPECTED_CONFIG_SHA256,
}
EXPECTED_RUNTIME = {
    "torch": "2.10.0+cu128",
    "transformers": "4.57.6",
    "peft": "0.18.1",
    "cuda": "12.8",
}
MODEL_READY_MAX_BYTES = 24 * 1024**3
ADAPTER_READY_MAX_BYTES = 32 * 1024**3
RUNTIME_PEAK_MAX_BYTES = 72 * 1024**3
TRAINABLE_RE = re.compile(
    r"(?:^|\.)layers\.(?P<layer>\d+)\.self_attn\."
    r"(?P<projection>q_proj|k_proj|v_proj|o_proj)\."
    r"lora_(?P<side>A|B)\.[^.]+\.weight$"
)


def canonical_hash(value: Any) -> str:
    encoded = json.dumps(
        value, allow_nan=False, separators=(",", ":"), sort_keys=True
    ).encode()
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def file_hash(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def validate_memory(memory: Any, *, key: str, ceiling: int, label: str) -> list[str]:
    if not isinstance(memory, dict):
        return [f"memory:{label}"]
    value = memory.get(key)
    if not isinstance(value, int) or value < 0 or value > ceiling:
        return [f"memory:{label}"]
    return []


def validate_inventory(inventory: Any) -> list[str]:
    if not isinstance(inventory, dict):
        return ["inventory"]
    errors: list[str] = []
    expected_scalars = {
        "layers": 24,
        "targeted_modules": 96,
        "trainable_tensors": 192,
        "trainable_parameters": 3_981_312,
    }
    if inventory.get("target_modules") != EXPECTED_TARGETS:
        errors.append("inventory targets")
    for key, value in expected_scalars.items():
        if inventory.get(key) != value:
            errors.append(f"inventory:{key}")
    names = inventory.get("trainable_names")
    observed: set[tuple[int, str, str]] = set()
    if not isinstance(names, list) or len(names) != 192 or len(set(names)) != 192:
        errors.append("inventory names")
    else:
        for name in names:
            if not isinstance(name, str) or any(
                token in name.lower() for token in (".mlp.", "expert", "router", "sinks")
            ):
                errors.append("inventory forbidden name")
                continue
            match = TRAINABLE_RE.search(name)
            if match is None:
                errors.append("inventory name shape")
                continue
            observed.add(
                (
                    int(match.group("layer")),
                    match.group("projection"),
                    match.group("side"),
                )
            )
    expected = {
        (layer, projection, side)
        for layer in range(24)
        for projection in EXPECTED_TARGETS
        for side in ("A", "B")
    }
    if observed != expected:
        errors.append("inventory coverage")
    body = {key: value for key, value in inventory.items() if key != "inventory_sha256"}
    if inventory.get("inventory_sha256") != canonical_hash(body):
        errors.append("inventory_sha256")
    return errors


def score_delta(left: Any, right: Any) -> float:
    if not isinstance(left, list) or not isinstance(right, list) or len(left) != len(right):
        raise ValueError("row count")
    maximum = 0.0
    for left_row, right_row in zip(left, right, strict=True):
        if left_row.get("case_id") != right_row.get("case_id"):
            raise ValueError("case")
        left_scores = left_row.get("candidate_log_probabilities")
        right_scores = right_row.get("candidate_log_probabilities")
        if not isinstance(left_scores, dict) or not isinstance(right_scores, dict):
            raise ValueError("scores")
        if set(left_scores) != set(right_scores):
            raise ValueError("candidates")
        for candidate in left_scores:
            maximum = max(
                maximum,
                abs(float(left_scores[candidate]) - float(right_scores[candidate])),
            )
    return maximum


def validate_score_rows(rows: Any, label: str) -> list[str]:
    if not isinstance(rows, list) or len(rows) != 4:
        return [f"forward:{label}"]
    errors: list[str] = []
    for row in rows:
        scores = row.get("candidate_log_probabilities")
        values = list(scores.values()) if isinstance(scores, dict) else []
        if (
            len(values) != 4
            or any(not isinstance(value, (int, float)) or not math.isfinite(value) for value in values)
            or abs(sum(math.exp(value) for value in values) - 1.0) > 1.0e-5
        ):
            errors.append(f"scores:{label}:{row.get('case_id')}")
    return errors


def validate_microbatches(update: Any) -> list[str]:
    if not isinstance(update, dict):
        return ["update"]
    rows = update.get("microbatches")
    if not isinstance(rows, list) or len(rows) != 4:
        return ["microbatch count"]
    errors: list[str] = []
    if [(row.get("start"), row.get("end")) for row in rows] != [
        (0, 1), (1, 2), (2, 3), (3, 4)
    ]:
        errors.append("microbatch coverage")
    weights = [row.get("weight") for row in rows]
    if any(not isinstance(value, (int, float)) or not math.isfinite(value) for value in weights):
        errors.append("microbatch weights")
    elif abs(sum(weights) - 1.0) > 1.0e-12:
        errors.append("microbatch weight sum")
    if any(not isinstance(row.get("target_tokens"), int) or row["target_tokens"] <= 0 for row in rows):
        errors.append("microbatch target tokens")
    return errors


def validate(artifact: Path, rgs_root: Path) -> dict[str, Any]:
    result_path = artifact / "profile-result.json"
    manifest_path = artifact / "MANIFEST.sha256"
    if not result_path.is_file() or not manifest_path.is_file():
        return {"valid": False, "errors": ["profile artifact files missing"]}
    errors: list[str] = []
    result = json.loads(result_path.read_text())
    expected_manifest = file_hash(result_path).removeprefix("sha256:") + "  profile-result.json\n"
    if manifest_path.read_text() != expected_manifest:
        errors.append("manifest")
    for key, value in {
        "version": EXPECTED_VERSION,
        "state_slice": EXPECTED_SLICE,
        "classification": "RuntimeProfileOperational",
        "tune_opened": False,
        "assessment_opened": False,
        "scientific_result": False,
        "claim_ceiling": EXPECTED_CEILING,
    }.items():
        if result.get(key) != value:
            errors.append(key)
    body = {key: value for key, value in result.items() if key != "result_sha256"}
    if result.get("result_sha256") != canonical_hash(body):
        errors.append("result_sha256")

    model = result.get("model", {})
    if model.get("id") != EXPECTED_MODEL or model.get("revision") != EXPECTED_REVISION:
        errors.append("model binding")
    runtime = result.get("runtime", {})
    if "H100" not in str(runtime.get("gpu", "")).upper():
        errors.append("gpu")
    for key, value in EXPECTED_RUNTIME.items():
        if runtime.get(key) != value:
            errors.append(f"runtime:{key}")

    correction = result.get("correction", {})
    if correction != {
        "quantization": {"quant_method": "mxfp4", "dequantize": False},
        "checkpoint_geometry": EXPECTED_GEOMETRY,
        "experts_frozen": True,
        "routers_frozen": True,
        "attention_sinks_frozen": True,
        "target_modules": EXPECTED_TARGETS,
        "target_parameters": [],
        "microbatch_size": 1,
        "effective_batch_size": 4,
        "loss_weighting": "nonignored_causal_target_tokens",
        "optimizer_steps": 1,
        "dropout_required_zero": True,
    }:
        errors.append("correction binding")
    errors.extend(validate_inventory(result.get("inventory")))
    if result.get("memory_ceilings") != {
        "model_ready_max_bytes": MODEL_READY_MAX_BYTES,
        "adapter_ready_max_bytes": ADAPTER_READY_MAX_BYTES,
        "runtime_peak_max_bytes": RUNTIME_PEAK_MAX_BYTES,
    }:
        errors.append("memory ceilings")

    update = result.get("update_evidence", {})
    if (
        update.get("gradient_steps") != 1
        or update.get("microbatch_forwards") != 4
        or update.get("training_examples") != 4
        or update.get("rollback_exact") is not True
        or update.get("pre_state_sha256") != update.get("rollback_state_sha256")
        or update.get("pre_state_sha256") == update.get("post_state_sha256")
    ):
        errors.append("update and rollback evidence")
    for key in ("loss", "gradient_norm"):
        value = update.get(key)
        if not isinstance(value, (int, float)) or not math.isfinite(value):
            errors.append(f"update:{key}")
    errors.extend(validate_microbatches(update))
    errors.extend(validate_memory(update.get("memory_model_ready"), key="allocated_bytes", ceiling=MODEL_READY_MAX_BYTES, label="model_ready"))
    errors.extend(validate_memory(update.get("memory_adapter_ready"), key="allocated_bytes", ceiling=ADAPTER_READY_MAX_BYTES, label="adapter_ready"))
    errors.extend(validate_memory(update.get("memory_after_update"), key="peak_allocated_bytes", ceiling=RUNTIME_PEAK_MAX_BYTES, label="runtime_peak"))

    forward = result.get("forward_evidence", {})
    if forward.get("real_tokenizer") is not True or forward.get("real_logits") is not True:
        errors.append("real forward flags")
    for group in ("base_direct", "base_protected", "adapted_pre_direct", "post_rollback_direct"):
        errors.extend(validate_score_rows(forward.get(group), group))
    try:
        zero_delta = score_delta(forward.get("base_direct"), forward.get("adapted_pre_direct"))
        rollback_delta = score_delta(forward.get("adapted_pre_direct"), forward.get("post_rollback_direct"))
        if zero_delta > 1.0e-7 or forward.get("zero_update_max_logit_delta") != zero_delta:
            errors.append("zero-update logit parity")
        if rollback_delta > 1.0e-7 or forward.get("rollback_max_logit_delta") != rollback_delta:
            errors.append("rollback logit parity")
        if forward.get("zero_update_tolerance") != 1.0e-7:
            errors.append("zero-update tolerance")
    except (TypeError, ValueError):
        errors.append("logit parity structure")

    source = result.get("source", {})
    commit = source.get("rgs_commit", "")
    if not isinstance(commit, str) or len(commit) != 40:
        errors.append("source commit")
    else:
        for key, relative in (
            ("runner_sha256", "scripts/run_v41r9_h100_profile.py"),
            ("baseline_runner_sha256", "scripts/run_v41r7_h100_profile.py"),
            ("microbatch_source_sha256", "mesh_brain/meshmodel/v41r7_microbatch.py"),
            ("attention_contract_sha256", "mesh_brain/meshmodel/v41r9_checkpoint_geometry.py"),
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
            except subprocess.CalledProcessError:
                errors.append(f"{key} unavailable")
    return {
        "version": "astral.v41r9_h100_profile_validation.v1",
        "valid": not errors,
        "errors": sorted(set(errors)),
        "artifact": str(artifact),
        "result_sha256": result.get("result_sha256"),
        "claim_ceiling": EXPECTED_CEILING if not errors else None,
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
