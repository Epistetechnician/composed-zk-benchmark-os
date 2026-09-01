"""Pure-data contract and custody helpers for Astral V39.

State slice: astral-stage0c-qwen36-layer-effect-v39.

This module deliberately contains no model imports and no execution path.  The
qualification runner and the independent validator both consume these frozen
constants and pure-data checks.
"""

from __future__ import annotations

import hashlib
import json
import os
import stat
from pathlib import Path
from typing import Any


PROTOCOL_ID = "astral-stage0c-qwen36-layer-effect-v39"
STATE_SLICE = PROTOCOL_ID
QUALIFICATION_CLAIM_CEILING = "LocalDevelopmentInstrumentFeasibilityOnly"
TARGET_VALIDITY_CLAIM_CEILING = "LocalDevelopmentStage0CQwen36CausalTargetValidity"
MODEL_ID = "Qwen3.6-35B-A3B-MLX-4bit"
MODEL_ARCHITECTURE = "Qwen3_5MoeForConditionalGeneration"
EXPECTED_LAYER_COUNT = 40
EXPECTED_HIDDEN_WIDTH = 2048
TARGET_LAYER = 19
REPLACEMENT_SCALE = 0.01
PARITY_TOLERANCE = 1e-4
REPEAT_TOLERANCE = 1e-5
ZERO_REPLACEMENT_TOLERANCE = 1e-5
NONZERO_LOGIT_DELTA_FLOOR = 1e-6
EXPECTED_MLX = "0.31.2"
EXPECTED_MLX_LM = "0.31.3"
QUALIFICATION_PROMPTS = (
    "A new neutral instrument qualification sentence. Continue the sentence:",
    "A second neutral layer seam qualification sentence. Continue the sentence:",
)
QUALIFICATION_PROMPT_DIGEST = hashlib.sha256(
    json.dumps(
        {
            "protocol": PROTOCOL_ID,
            "prompt_sha256": [
                hashlib.sha256(prompt.encode("utf-8")).hexdigest()
                for prompt in QUALIFICATION_PROMPTS
            ],
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
).hexdigest()

RESULT_KEYS = {
    "protocol",
    "state_slice",
    "claim_ceiling",
    "classification",
    "model_id",
    "model_architecture",
    "model_root",
    "model_manifest_sha256",
    "model_file_count",
    "runtime",
    "source",
    "prompt_count",
    "prompt_registry_sha256",
    "layer_count",
    "hidden_width_observed",
    "target_layer",
    "capture_shape_ok",
    "replacement_shape_ok",
    "native_parity_max_abs_logit_delta",
    "baseline_repeat_max_abs_logit_delta",
    "zero_replacement_max_abs_logit_delta",
    "nonzero_replacement_max_abs_logit_delta",
    "assessment_opened",
    "prediction_locked_before_assessment",
    "scientific_assessment",
    "model_loaded",
    "model_training",
    "network_access",
    "raw_intermediates_retained",
    "aggregate_only",
    "stage_0c",
    "stage_1",
    "accepted_evidence",
    "reasons",
}
RUNTIME_KEYS = {
    "python",
    "mlx",
    "mlx_lm",
    "qwen3_5_source_sha256",
    "qwen3_5_moe_source_sha256",
}
SOURCE_KEYS = {"runner_sha256", "protocol_sha256"}
FORBIDDEN_RESULT_KEYS = {
    "prompts",
    "tokens",
    "hidden_states",
    "raw_activations",
    "raw_logits",
    "raw_traces",
    "reasoning_traces",
    "credentials",
    "pii",
}


def canonical_digest(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _file_signature(metadata: os.stat_result) -> tuple[int, int, int, int, int]:
    return (
        metadata.st_dev,
        metadata.st_ino,
        metadata.st_size,
        metadata.st_mtime_ns,
        metadata.st_ctime_ns,
    )


def sha256_file(path: Path) -> str:
    descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode):
            raise OSError(f"not a regular file: {path}")
        digest = hashlib.sha256()
        while chunk := os.read(descriptor, 1024 * 1024):
            digest.update(chunk)
        after = os.fstat(descriptor)
        if _file_signature(before) != _file_signature(after):
            raise OSError(f"file changed during hashing: {path}")
        return digest.hexdigest()
    finally:
        os.close(descriptor)


def _external_to(path: Path, repository_root: Path) -> bool:
    try:
        path.resolve().relative_to(repository_root.resolve())
    except ValueError:
        return True
    return False


def assert_external(path: Path, repository_root: Path) -> None:
    if not _external_to(path, repository_root):
        raise ValueError("artifact root must be outside the repository")


def model_manifest(model_root: Path) -> dict[str, Any]:
    model_root = model_root.resolve()
    if not model_root.is_dir() or model_root.is_symlink():
        raise ValueError(f"model root is not a regular directory: {model_root}")
    entries: list[dict[str, Any]] = []
    for candidate in sorted(model_root.rglob("*")):
        if candidate.is_symlink():
            raise ValueError(f"symlink in model root: {candidate}")
        if not candidate.is_file():
            continue
        entries.append(
            {
                "path": candidate.relative_to(model_root).as_posix(),
                "byte_len": candidate.stat().st_size,
                "sha256": sha256_file(candidate),
            }
        )
    if not entries:
        raise ValueError("model root has no regular files")
    manifest = {"model_id": model_root.name, "files": entries}
    return {
        "manifest_sha256": canonical_digest(manifest),
        "file_count": len(entries),
    }


def _is_digest(value: Any) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


def _is_bool(value: Any) -> bool:
    return isinstance(value, bool)


def _is_finite_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and value >= 0


def _contains_forbidden_key(value: Any) -> bool:
    pending = [value]
    while pending:
        current = pending.pop()
        if isinstance(current, dict):
            if any(key in FORBIDDEN_RESULT_KEYS for key in current):
                return True
            pending.extend(current.values())
        elif isinstance(current, list):
            pending.extend(current)
    return False


def qualification_gate_errors(result: object) -> list[str]:
    """Return independent errors for a qualification result envelope."""

    errors: list[str] = []
    if not isinstance(result, dict):
        return ["result_not_object"]
    unknown = sorted(set(result) - RESULT_KEYS)
    missing = sorted(RESULT_KEYS - set(result))
    if unknown:
        errors.append(f"unknown_result_fields:{','.join(unknown)}")
    if missing:
        errors.append(f"missing_result_fields:{','.join(missing)}")
    if _contains_forbidden_key(result):
        errors.append("forbidden_raw_or_sensitive_field")

    for key, expected in (
        ("protocol", PROTOCOL_ID),
        ("state_slice", STATE_SLICE),
        ("claim_ceiling", QUALIFICATION_CLAIM_CEILING),
        ("model_id", MODEL_ID),
        ("model_architecture", MODEL_ARCHITECTURE),
        ("prompt_count", len(QUALIFICATION_PROMPTS)),
        ("prompt_registry_sha256", QUALIFICATION_PROMPT_DIGEST),
        ("layer_count", EXPECTED_LAYER_COUNT),
        ("hidden_width_observed", EXPECTED_HIDDEN_WIDTH),
        ("target_layer", TARGET_LAYER),
    ):
        if result.get(key) != expected:
            errors.append(f"{key}_mismatch")

    for key in ("model_manifest_sha256",):
        if not _is_digest(result.get(key)):
            errors.append(f"{key}_invalid")
    if not isinstance(result.get("model_root"), str) or not result.get("model_root"):
        errors.append("model_root_invalid")
    if (
        not isinstance(result.get("model_file_count"), int)
        or isinstance(result.get("model_file_count"), bool)
        or result.get("model_file_count", 0) <= 0
    ):
        errors.append("model_file_count_invalid")

    runtime = result.get("runtime")
    if not isinstance(runtime, dict) or set(runtime) != RUNTIME_KEYS:
        errors.append("runtime_shape_invalid")
    else:
        if runtime.get("mlx") != EXPECTED_MLX:
            errors.append("mlx_version_mismatch")
        if runtime.get("mlx_lm") != EXPECTED_MLX_LM:
            errors.append("mlx_lm_version_mismatch")
        for key in ("qwen3_5_source_sha256", "qwen3_5_moe_source_sha256"):
            if not _is_digest(runtime.get(key)):
                errors.append(f"{key}_invalid")

    source = result.get("source")
    if not isinstance(source, dict) or set(source) != SOURCE_KEYS:
        errors.append("source_shape_invalid")
    elif any(not _is_digest(source.get(key)) for key in SOURCE_KEYS):
        errors.append("source_digest_invalid")

    for key in ("capture_shape_ok", "replacement_shape_ok"):
        if result.get(key) is not True:
            errors.append(f"{key}_failed")
    for key in (
        "native_parity_max_abs_logit_delta",
        "baseline_repeat_max_abs_logit_delta",
        "zero_replacement_max_abs_logit_delta",
        "nonzero_replacement_max_abs_logit_delta",
    ):
        if not _is_finite_number(result.get(key)):
            errors.append(f"{key}_invalid")

    for key, expected in (
        ("assessment_opened", False),
        ("prediction_locked_before_assessment", False),
        ("scientific_assessment", False),
        ("model_training", False),
        ("network_access", False),
        ("raw_intermediates_retained", False),
        ("aggregate_only", True),
        ("stage_0c", False),
        ("stage_1", False),
        ("accepted_evidence", False),
    ):
        if not _is_bool(result.get(key)) or result.get(key) is not expected:
            errors.append(f"{key}_failed")
    if result.get("model_loaded") is not True:
        errors.append("model_loaded_failed")
    if not isinstance(result.get("reasons"), list) or any(
        not isinstance(reason, str) for reason in result.get("reasons", [])
    ):
        errors.append("reasons_invalid")

    if result.get("native_parity_max_abs_logit_delta", float("inf")) > PARITY_TOLERANCE:
        errors.append("native_parity_gate_failed")
    if result.get("baseline_repeat_max_abs_logit_delta", float("inf")) > REPEAT_TOLERANCE:
        errors.append("repeatability_gate_failed")
    if result.get("zero_replacement_max_abs_logit_delta", float("inf")) > ZERO_REPLACEMENT_TOLERANCE:
        errors.append("zero_replacement_gate_failed")
    if result.get("nonzero_replacement_max_abs_logit_delta", 0.0) <= NONZERO_LOGIT_DELTA_FLOOR:
        errors.append("nonzero_logit_reach_gate_failed")

    classification = result.get("classification")
    if classification not in {"InstrumentQualificationPassed", "InstrumentQualificationFailed"}:
        errors.append("classification_invalid")
    elif classification == "InstrumentQualificationPassed" and errors:
        errors.append("passed_classification_with_failed_gate")
    return errors
