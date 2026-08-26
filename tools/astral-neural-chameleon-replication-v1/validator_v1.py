#!/usr/bin/env python3
"""Independently validate a V1 Neural Chameleon preflight result.

State slice: astral-neural-chameleon-replication-v1-preflight.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import stat
import sys
from pathlib import Path
from pathlib import PurePosixPath
from typing import Any


PROTOCOL_ID = "astral-neural-chameleon-replication-v1"
STATE_SLICE = "astral-neural-chameleon-replication-v1-preflight"
CLAIM_CEILING = "LocalDevelopmentNeuralChameleonReplicationPreflightOnly"
READY = "ReadyForInstrumentQualification"
MISSING_ROOT = "MissingArtifactRoot"
MISSING_REQUIRED = "MissingRequiredArtifact"
INVALID = "ArtifactValidationFailed"
REQUIRED_ROLES = sorted(
    {
        "chameleon_checkpoint",
        "precursor_checkpoint",
        "activation_oracle_checkpoint",
        "linear_monitor_bundle",
        "oracle_corpus_bundle",
        "mechanistic_corpus_bundle",
        "runtime_manifest",
    }
)
REQUIRED_CAPABILITIES = sorted(
    {
        "teacher_forced_same_response",
        "residual_layer_capture",
        "attention_head_output_capture",
        "attention_qkv_capture",
        "residual_state_transplant",
        "weight_slice_hybridization",
        "linear_monitor_scoring",
        "activation_oracle_scoring",
    }
)
KNOWN_CLASSIFICATIONS = {READY, MISSING_ROOT, MISSING_REQUIRED, INVALID}
RESULT_KEYS = {
    "protocol",
    "state_slice",
    "claim_ceiling",
    "artifact_root",
    "classification",
    "required_roles",
    "required_capabilities",
    "runtime_capabilities",
    "artifact_manifest_present",
    "artifact_manifest_sha256",
    "artifact_roles",
    "verified_artifact_count",
    "model_execution",
    "model_training",
    "network_access",
    "assessment_opened",
    "raw_payloads_retained",
    "confirmation",
    "stage_0c",
    "stage_1",
    "accepted_evidence",
    "provider_claims",
    "benchmark_claims",
    "reasons",
}
MANIFEST_SCHEMA_VERSION = 1
FORBIDDEN_KEYS = {
    "prompts",
    "raw_activations",
    "raw_logits",
    "raw_traces",
    "reasoning_traces",
    "credentials",
    "pii",
    "signatures",
}


def _contains_forbidden_key(value: Any) -> bool:
    pending = [value]
    while pending:
        current = pending.pop()
        if isinstance(current, dict):
            if any(key in FORBIDDEN_KEYS for key in current):
                return True
            pending.extend(current.values())
        elif isinstance(current, list):
            pending.extend(current)
    return False


def _strict_json_bytes(payload: bytes) -> Any:
    def reject_constant(value: str) -> Any:
        raise ValueError(f"non-standard JSON constant: {value}")

    def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate JSON key: {key}")
            result[key] = value
        return result

    return json.loads(
        payload.decode("utf-8"),
        object_pairs_hook=reject_duplicate_keys,
        parse_constant=reject_constant,
    )


def _strict_json(path: Path) -> Any:
    return _strict_json_bytes(_read_stable_bytes(path))


def _read_stable_bytes(path: Path) -> bytes:
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(path, flags)
    try:
        metadata = os.fstat(descriptor)
        if not stat.S_ISREG(metadata.st_mode):
            raise OSError("artifact is not a regular file")
    except BaseException:
        os.close(descriptor)
        raise
    try:
        handle = os.fdopen(descriptor, "rb")
    except BaseException:
        os.close(descriptor)
        raise
    with handle:
        before = os.fstat(handle.fileno())
        payload = handle.read()
        after = os.fstat(handle.fileno())
    if _file_signature(before) != _file_signature(after):
        raise OSError("artifact changed during read")
    return payload


def _file_signature(metadata: os.stat_result) -> tuple[int, int, int, int, int]:
    return (
        metadata.st_dev,
        metadata.st_ino,
        metadata.st_size,
        metadata.st_mtime_ns,
        metadata.st_ctime_ns,
    )


def _digest_and_size(path: Path) -> tuple[int, str]:
    payload = _read_stable_bytes(path)
    return len(payload), hashlib.sha256(payload).hexdigest()


def _safe_relative_path(value: Any) -> str | None:
    if not isinstance(value, str) or not value or "\x00" in value or "\\" in value:
        return None
    if any(ord(character) < 32 for character in value):
        return None
    if value.startswith("/") or value.startswith("//") or ":" in value.split("/", 1)[0]:
        return None
    if any(part in {"", ".", ".."} for part in value.split("/")):
        return None
    path = PurePosixPath(value)
    if path.is_absolute() or path.as_posix() != value:
        return None
    return value


def _is_digest(value: Any, lengths: set[int] = {64}) -> bool:
    return isinstance(value, str) and len(value) in lengths and all(
        character in "0123456789abcdef" for character in value
    )


def _is_schema_version(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value == MANIFEST_SCHEMA_VERSION


def _object_shape(value: Any, keys: set[str], prefix: str, errors: list[str]) -> bool:
    if not isinstance(value, dict):
        errors.append(f"{prefix}_not_object")
        return False
    unknown = sorted(set(value) - keys)
    missing = sorted(keys - set(value))
    if unknown:
        errors.append(f"{prefix}_unknown_fields:{','.join(unknown)}")
    if missing:
        errors.append(f"{prefix}_missing_fields:{','.join(missing)}")
    return True


def _nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value)


def _positive_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def _nonnegative_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _finite_unit_interval(value: Any) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
        and 0 < value < 1
    )


def _validate_arm_protocols(arms: Any, errors: list[str]) -> None:
    if not _object_shape(arms, ARM_KEYS, "artifact_manifest_arms", errors):
        return
    oracle = arms.get("activation_oracle")
    if _object_shape(oracle, ORACLE_ARM_KEYS, "artifact_manifest_activation_oracle", errors):
        for key, expected in ARM_ROLE_BINDINGS["activation_oracle"].items():
            if oracle.get(key) != expected:
                errors.append(f"artifact_manifest_activation_oracle_{key}_mismatch")
        if oracle.get("primary_endpoint") != "activation_oracle_robustness_at_fixed_fpr":
            errors.append("artifact_manifest_activation_oracle_primary_endpoint_mismatch")
        if not _nonempty_string(oracle.get("formula")):
            errors.append("artifact_manifest_activation_oracle_formula_invalid")
        if oracle.get("activation_position") != "last_token":
            errors.append("artifact_manifest_activation_oracle_activation_position_mismatch")
        if not _nonnegative_int(oracle.get("activation_layer")):
            errors.append("artifact_manifest_activation_oracle_activation_layer_invalid")
        for key in ("trigger_template", "score_rule"):
            if not _nonempty_string(oracle.get(key)):
                errors.append(f"artifact_manifest_activation_oracle_{key}_invalid")
        if oracle.get("metrics") != ORACLE_METRICS:
            errors.append("artifact_manifest_activation_oracle_metrics_mismatch")
        if oracle.get("controls") != ORACLE_CONTROLS:
            errors.append("artifact_manifest_activation_oracle_controls_mismatch")
        for key in ("fit_rows", "tune_rows", "assessment_rows"):
            if not _positive_int(oracle.get(key)):
                errors.append(f"artifact_manifest_activation_oracle_{key}_invalid")
        if not _finite_unit_interval(oracle.get("fixed_fpr")):
            errors.append("artifact_manifest_activation_oracle_fixed_fpr_invalid")
        if oracle.get("prediction_lock_required") is not True:
            errors.append("artifact_manifest_activation_oracle_prediction_lock_mismatch")

    mechanistic = arms.get("mechanistic")
    if _object_shape(mechanistic, MECHANISTIC_ARM_KEYS, "artifact_manifest_mechanistic", errors):
        for key, expected in ARM_ROLE_BINDINGS["mechanistic"].items():
            if mechanistic.get(key) != expected:
                errors.append(f"artifact_manifest_mechanistic_{key}_mismatch")
        if mechanistic.get("primary_endpoint") != "direct_held_out_intervention_effect":
            errors.append("artifact_manifest_mechanistic_primary_endpoint_mismatch")
        if not _nonempty_string(mechanistic.get("formula")):
            errors.append("artifact_manifest_mechanistic_formula_invalid")
        if not _nonnegative_int(mechanistic.get("monitor_layer")):
            errors.append("artifact_manifest_mechanistic_monitor_layer_invalid")
        for key in ("monitor_definition", "score_rule", "bootstrap_unit"):
            if not _nonempty_string(mechanistic.get(key)):
                errors.append(f"artifact_manifest_mechanistic_{key}_invalid")
        for key in ("transplant_sites", "head_set"):
            value = mechanistic.get(key)
            if not isinstance(value, list) or not value or any(not _nonempty_string(item) for item in value):
                errors.append(f"artifact_manifest_mechanistic_{key}_invalid")
            elif len(value) != len(set(value)):
                errors.append(f"artifact_manifest_mechanistic_{key}_duplicate")
        if mechanistic.get("qkv_factorial") != QKV_FACTORIAL:
            errors.append("artifact_manifest_mechanistic_qkv_factorial_mismatch")
        if mechanistic.get("hybridization_slices") != HYBRIDIZATION_SLICES:
            errors.append("artifact_manifest_mechanistic_hybridization_slices_mismatch")
        if mechanistic.get("metrics") != MECHANISTIC_METRICS:
            errors.append("artifact_manifest_mechanistic_metrics_mismatch")
        if mechanistic.get("controls") != MECHANISTIC_CONTROLS:
            errors.append("artifact_manifest_mechanistic_controls_mismatch")
        for key in ("fit_rows", "tune_rows", "assessment_rows"):
            if not _positive_int(mechanistic.get(key)):
                errors.append(f"artifact_manifest_mechanistic_{key}_invalid")
        if mechanistic.get("prediction_lock_required") is not True:
            errors.append("artifact_manifest_mechanistic_prediction_lock_mismatch")


def _validate_freshness(freshness: Any, errors: list[str]) -> None:
    if not _object_shape(freshness, FRESHNESS_KEYS, "artifact_manifest_freshness", errors):
        return
    if freshness.get("disallow_protocols") != DISALLOWED_PROTOCOLS:
        errors.append("artifact_manifest_freshness_disallow_protocols_mismatch")
    if freshness.get("disallow_concepts") is not True:
        errors.append("artifact_manifest_freshness_disallow_concepts_mismatch")
    if not _is_digest(freshness.get("concept_registry_sha256")):
        errors.append("artifact_manifest_freshness_concept_registry_sha256_invalid")
    for key in ("disallow_predictions", "disallow_assessment_rows", "disallow_artifacts"):
        if freshness.get(key) is not True:
            errors.append(f"artifact_manifest_freshness_{key}_mismatch")
    if freshness.get("source_study_reuse") != "ExplicitSourceInputsOnly":
        errors.append("artifact_manifest_freshness_source_study_reuse_mismatch")
    if freshness.get("astral_derived_selection") is not False:
        errors.append("artifact_manifest_freshness_astral_derived_selection_mismatch")


def _validate_provenance(
    provenance: Any, role_paths: dict[str, set[str]], errors: list[str]
) -> dict[str, dict[str, int]]:
    panel_counts: dict[str, dict[str, int]] = {}
    if not _object_shape(provenance, PROVENANCE_KEYS, "artifact_manifest_provenance", errors):
        return panel_counts
    models = provenance.get("models")
    if _object_shape(models, MODEL_ROLES, "artifact_manifest_provenance_models", errors):
        for role in sorted(MODEL_ROLES):
            descriptor = models.get(role)
            prefix = f"artifact_manifest_provenance_model_{role}"
            if not _object_shape(descriptor, MODEL_DESCRIPTOR_KEYS, prefix, errors):
                continue
            for key in ("model_family", "model_revision", "architecture", "source_repository"):
                if not _nonempty_string(descriptor.get(key)):
                    errors.append(f"{prefix}_{key}_invalid")
            source_repository = descriptor.get("source_repository")
            if not isinstance(source_repository, str) or not source_repository.startswith("https://"):
                errors.append(f"{prefix}_source_repository_invalid")
            if not _is_digest(descriptor.get("source_commit"), {40, 64}):
                errors.append(f"{prefix}_source_commit_invalid")
            dimensions = descriptor.get("dimensions")
            if _object_shape(dimensions, DIMENSION_KEYS, f"{prefix}_dimensions", errors):
                for key in DIMENSION_KEYS:
                    if not _positive_int(dimensions.get(key)):
                        errors.append(f"{prefix}_dimensions_{key}_invalid")
            tokenizer_files = descriptor.get("tokenizer_files")
            if not isinstance(tokenizer_files, list) or not tokenizer_files or any(
                not isinstance(path, str) or _safe_relative_path(path) is None for path in tokenizer_files
            ):
                errors.append(f"{prefix}_tokenizer_files_invalid")
            else:
                if len(tokenizer_files) != len(set(tokenizer_files)):
                    errors.append(f"{prefix}_tokenizer_files_duplicate")
                if not set(tokenizer_files).issubset(role_paths.get(role, set())):
                    errors.append(f"{prefix}_tokenizer_files_unbound")
            expectations = descriptor.get("tokenization_expectations")
            if not isinstance(expectations, list) or not expectations or any(
                not _nonempty_string(item) for item in expectations
            ):
                errors.append(f"{prefix}_tokenization_expectations_invalid")

    monitor = provenance.get("monitor")
    if _object_shape(monitor, MONITOR_KEYS, "artifact_manifest_provenance_monitor", errors):
        for key in ("source_repository", "calibration", "score_definition"):
            if not _nonempty_string(monitor.get(key)):
                errors.append(f"artifact_manifest_provenance_monitor_{key}_invalid")
        source_repository = monitor.get("source_repository")
        if not isinstance(source_repository, str) or not source_repository.startswith("https://"):
            errors.append("artifact_manifest_provenance_monitor_source_repository_invalid")
        if not _is_digest(monitor.get("source_commit"), {40, 64}):
            errors.append("artifact_manifest_provenance_monitor_source_commit_invalid")
        if monitor.get("trained_on_role") != "mechanistic_corpus_bundle":
            errors.append("artifact_manifest_provenance_monitor_trained_on_role_mismatch")
        if not _nonnegative_int(monitor.get("layer")):
            errors.append("artifact_manifest_provenance_monitor_layer_invalid")
        if not _finite_unit_interval(monitor.get("threshold")):
            errors.append("artifact_manifest_provenance_monitor_threshold_invalid")
        if not _nonempty_string(monitor.get("pooling")):
            errors.append("artifact_manifest_provenance_monitor_pooling_invalid")

    corpora = provenance.get("corpora")
    if _object_shape(corpora, CORPUS_ROLES, "artifact_manifest_provenance_corpora", errors):
        for role in sorted(CORPUS_ROLES):
            descriptor = corpora.get(role)
            prefix = f"artifact_manifest_provenance_corpus_{role}"
            if not _object_shape(descriptor, CORPUS_DESCRIPTOR_KEYS, prefix, errors):
                continue
            if not _nonempty_string(descriptor.get("lineage")):
                errors.append(f"{prefix}_lineage_invalid")
            counts = descriptor.get("panel_counts")
            if not _object_shape(counts, {"fit", "tune", "assessment"}, f"{prefix}_panel_counts", errors):
                continue
            panel_counts[role] = counts
            for key in ("fit", "tune", "assessment"):
                if not _positive_int(counts.get(key)):
                    errors.append(f"{prefix}_panel_counts_{key}_invalid")
            template_ids = descriptor.get("template_ids")
            if not isinstance(template_ids, list) or not template_ids or any(
                not _nonempty_string(item) for item in template_ids
            ):
                errors.append(f"{prefix}_template_ids_invalid")
            elif len(template_ids) != len(set(template_ids)):
                errors.append(f"{prefix}_template_ids_duplicate")
            for key in ("split_sha256", "concept_registry_sha256"):
                if not _is_digest(descriptor.get(key)):
                    errors.append(f"{prefix}_{key}_invalid")
            if descriptor.get("source_study_reuse") != "ExplicitSourceInputsOnly":
                errors.append(f"{prefix}_source_study_reuse_mismatch")

    runtime = provenance.get("runtime")
    if _object_shape(runtime, RUNTIME_DESCRIPTOR_KEYS, "artifact_manifest_provenance_runtime", errors):
        if not _nonempty_string(runtime.get("python")):
            errors.append("artifact_manifest_provenance_runtime_python_invalid")
        libraries = runtime.get("libraries")
        if not isinstance(libraries, dict) or not libraries or any(
            not _nonempty_string(key) or not _nonempty_string(value) for key, value in libraries.items()
        ):
            errors.append("artifact_manifest_provenance_runtime_libraries_invalid")
        if not _is_digest(runtime.get("source_commit"), {40, 64}):
            errors.append("artifact_manifest_provenance_runtime_source_commit_invalid")
    return panel_counts


def _validate_execution_contract(contract: Any, arms: Any, errors: list[str]) -> None:
    keys = {"order", "prediction_lock_required", "arm_independence", "activation_oracle", "mechanistic"}
    if not _object_shape(contract, keys, "artifact_manifest_execution_contract", errors):
        return
    if contract.get("order") != EXECUTION_ORDER:
        errors.append("artifact_manifest_execution_contract_order_mismatch")
    if contract.get("prediction_lock_required") is not True:
        errors.append("artifact_manifest_execution_contract_prediction_lock_mismatch")
    independence = contract.get("arm_independence")
    independence_keys = {"shared_roles", "forbid_cross_arm_selection", "forbid_cross_arm_evidence"}
    if _object_shape(independence, independence_keys, "artifact_manifest_execution_contract_arm_independence", errors):
        if independence.get("shared_roles") != ["runtime_manifest"]:
            errors.append("artifact_manifest_execution_contract_shared_roles_mismatch")
        for key in ("forbid_cross_arm_selection", "forbid_cross_arm_evidence"):
            if independence.get(key) is not True:
                errors.append(f"artifact_manifest_execution_contract_{key}_mismatch")
    if not isinstance(arms, dict):
        return
    for name, extra_keys in (
        ("activation_oracle", {"fixed_fpr"}),
        ("mechanistic", {"bootstrap_unit", "qkv_combinations", "transplant_directions", "hybridization_slices"}),
    ):
        spec = contract.get(name)
        keys = {
            "formula", "metrics", "controls", "fit_rows", "tune_rows", "assessment_rows",
            "assessment_requires_prediction_lock", *extra_keys,
        }
        if not _object_shape(spec, keys, f"artifact_manifest_execution_contract_{name}", errors):
            continue
        source = arms.get(name)
        if not isinstance(source, dict):
            continue
        for key in ("formula", "metrics", "controls", "fit_rows", "tune_rows", "assessment_rows"):
            if spec.get(key) != source.get(key):
                errors.append(f"artifact_manifest_execution_contract_{name}_{key}_mismatch")
        if spec.get("assessment_requires_prediction_lock") is not True:
            errors.append(f"artifact_manifest_execution_contract_{name}_prediction_lock_mismatch")
        if name == "activation_oracle":
            if spec.get("fixed_fpr") != source.get("fixed_fpr"):
                errors.append("artifact_manifest_execution_contract_activation_oracle_fixed_fpr_mismatch")
        else:
            if spec.get("bootstrap_unit") != source.get("bootstrap_unit"):
                errors.append("artifact_manifest_execution_contract_mechanistic_bootstrap_unit_mismatch")
            if spec.get("qkv_combinations") != QKV_FACTORIAL:
                errors.append("artifact_manifest_execution_contract_mechanistic_qkv_mismatch")
            if spec.get("transplant_directions") != ["ordinary_to_triggered", "triggered_to_ordinary"]:
                errors.append("artifact_manifest_execution_contract_mechanistic_transplant_directions_mismatch")
            if spec.get("hybridization_slices") != HYBRIDIZATION_SLICES:
                errors.append("artifact_manifest_execution_contract_mechanistic_hybridization_slices_mismatch")


def _validate_manifest_semantics(
    manifest: dict[str, Any], role_paths: dict[str, set[str]], errors: list[str]
) -> None:
    _validate_freshness(manifest.get("freshness"), errors)
    _validate_arm_protocols(manifest.get("arms"), errors)
    _validate_execution_contract(manifest.get("execution_contract"), manifest.get("arms"), errors)
    panel_counts = _validate_provenance(manifest.get("provenance"), role_paths, errors)
    arms = manifest.get("arms")
    if isinstance(arms, dict):
        for arm_name, corpus_role in (
            ("activation_oracle", "oracle_corpus_bundle"),
            ("mechanistic", "mechanistic_corpus_bundle"),
        ):
            arm = arms.get(arm_name)
            counts = panel_counts.get(corpus_role)
            if isinstance(arm, dict) and counts is not None:
                for arm_key, corpus_key in (
                    ("fit_rows", "fit"),
                    ("tune_rows", "tune"),
                    ("assessment_rows", "assessment"),
                ):
                    if arm.get(arm_key) != counts.get(corpus_key):
                        errors.append(f"artifact_manifest_{arm_name}_{arm_key}_corpus_count_mismatch")


def _role_digest(files: list[dict[str, Any]]) -> str:
    canonical = sorted(
        [
            {"path": item["path"], "byte_len": item["byte_len"], "sha256": item["sha256"]}
            for item in files
        ],
        key=lambda item: item["path"],
    )
    payload = json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _repository_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _is_within(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def _symlink_components(path: Path) -> list[str]:
    absolute = path if path.is_absolute() else Path.cwd() / path
    current = Path(absolute.anchor)
    found: list[str] = []
    for component in absolute.parts[1:]:
        current /= component
        if current.is_symlink():
            found.append(str(current))
    return found


ROLE_KINDS = {
    "chameleon_checkpoint": "checkpoint",
    "precursor_checkpoint": "checkpoint",
    "activation_oracle_checkpoint": "oracle",
    "linear_monitor_bundle": "monitor",
    "oracle_corpus_bundle": "corpus",
    "mechanistic_corpus_bundle": "corpus",
    "runtime_manifest": "runtime",
}
MANIFEST_KEYS = {
    "protocol",
    "state_slice",
    "claim_ceiling",
    "schema_version",
    "artifact_entries",
    "retention",
    "runtime_capabilities",
    "arms",
    "execution_contract",
    "provenance",
    "freshness",
}
RETENTION_KEYS = {
    "artifact_root_external",
    "artifact_root_immutable",
    "raw_payloads_external_only",
    "raw_payloads_in_result",
    "network_access",
    "model_training",
    "assessment_opened",
}
FRESHNESS_KEYS = {
    "disallow_protocols",
    "disallow_concepts",
    "concept_registry_sha256",
    "disallow_predictions",
    "disallow_assessment_rows",
    "disallow_artifacts",
    "source_study_reuse",
    "astral_derived_selection",
}
ARM_KEYS = {"activation_oracle", "mechanistic"}
ARM_ROLE_BINDINGS = {
    "activation_oracle": {
        "actor_role": "chameleon_checkpoint",
        "oracle_role": "activation_oracle_checkpoint",
        "corpus_role": "oracle_corpus_bundle",
        "runtime_role": "runtime_manifest",
    },
    "mechanistic": {
        "chameleon_role": "chameleon_checkpoint",
        "precursor_role": "precursor_checkpoint",
        "monitor_role": "linear_monitor_bundle",
        "corpus_role": "mechanistic_corpus_bundle",
        "runtime_role": "runtime_manifest",
    },
}
ORACLE_ARM_KEYS = {
    "actor_role", "oracle_role", "corpus_role", "runtime_role",
    "primary_endpoint", "formula", "activation_layer", "activation_position",
    "trigger_template", "score_rule", "metrics", "controls", "fit_rows",
    "tune_rows", "assessment_rows", "fixed_fpr", "prediction_lock_required",
}
MECHANISTIC_ARM_KEYS = {
    "chameleon_role", "precursor_role", "monitor_role", "corpus_role", "runtime_role",
    "primary_endpoint", "formula", "monitor_layer", "monitor_definition",
    "transplant_sites", "head_set", "qkv_factorial", "hybridization_slices",
    "score_rule", "metrics", "controls", "fit_rows", "tune_rows", "assessment_rows",
    "bootstrap_unit", "prediction_lock_required",
}
EXECUTION_ORDER = [
    "provenance_and_parity", "baseline_controls", "oracle_qualification",
    "mechanistic_localization", "route_and_prototype_diagnostics",
    "qkv_factorial_and_hybridization", "prediction_lock", "sealed_assessment",
    "aggregate_validation",
]
ORACLE_METRICS = [
    "clean_accuracy", "triggered_accuracy", "tpr_at_fixed_fpr", "false_positive_rate",
    "false_negative_rate", "trigger_selectivity",
]
ORACLE_CONTROLS = ["base", "precursor", "no_trigger"]
MECHANISTIC_METRICS = [
    "monitor_score", "output_capability_control", "rescue_recovery", "induction_recovery",
    "route_sensitivity", "radial_tangential_effect", "prototype_reconstruction",
]
MECHANISTIC_CONTROLS = ["matched_baseline", "zero_intervention", "random_site"]
QKV_FACTORIAL = ["Q", "K", "V", "QK", "QV", "KV", "QKV"]
HYBRIDIZATION_SLICES = ["K12", "early_blocks_0_8", "matched_control"]
DISALLOWED_PROTOCOLS = ["V22", "V23", "V24", "V25", "V26", "V38"]
PROVENANCE_KEYS = {"models", "monitor", "corpora", "runtime"}
MODEL_ROLES = {
    "chameleon_checkpoint", "precursor_checkpoint", "activation_oracle_checkpoint"
}
MODEL_DESCRIPTOR_KEYS = {
    "model_family", "model_revision", "architecture", "dimensions", "tokenizer_files",
    "tokenization_expectations", "source_repository", "source_commit",
}
DIMENSION_KEYS = {"hidden_size", "num_layers", "num_attention_heads", "num_kv_heads"}
MONITOR_KEYS = {
    "source_repository", "source_commit", "trained_on_role", "layer", "pooling",
    "threshold", "calibration", "score_definition",
}
CORPUS_ROLES = {"oracle_corpus_bundle", "mechanistic_corpus_bundle"}
CORPUS_DESCRIPTOR_KEYS = {
    "lineage", "panel_counts", "template_ids", "split_sha256", "concept_registry_sha256",
    "source_study_reuse",
}
RUNTIME_DESCRIPTOR_KEYS = {"python", "libraries", "source_commit"}


def _revalidate_root(result: dict[str, Any], trusted_root: Path | None) -> list[str]:
    errors: list[str] = []
    root_value = result.get("artifact_root")
    if not isinstance(root_value, str) or not root_value:
        return ["artifact_root_revalidation_invalid"]
    root = Path(root_value)
    if trusted_root is None:
        errors.append("artifact_root_revalidation_trusted_input_required")
    else:
        supplied = trusted_root if trusted_root.is_absolute() else Path.cwd() / trusted_root
        try:
            supplied_resolved = supplied.resolve(strict=False)
            root_resolved = root.resolve(strict=False)
        except (OSError, RuntimeError, ValueError):
            return errors + ["artifact_root_revalidation_invalid"]
        if root_resolved != supplied_resolved:
            errors.append("artifact_root_revalidation_trusted_input_mismatch")
        if supplied.is_symlink() or _symlink_components(supplied.parent):
            errors.append("artifact_root_revalidation_trusted_input_symlink")
    if not root.is_absolute():
        errors.append("artifact_root_revalidation_not_absolute")
    if root.is_symlink() or not root.is_dir():
        if result.get("classification") != MISSING_ROOT:
            errors.append("artifact_root_revalidation_missing_or_not_directory")
        if result.get("artifact_manifest_present") is not False:
            errors.append("missing_root_manifest_presence_mismatch")
        if result.get("artifact_manifest_sha256") is not None:
            errors.append("missing_root_manifest_digest_mismatch")
        if result.get("artifact_roles") != []:
            errors.append("missing_root_artifact_roles_mismatch")
        if result.get("verified_artifact_count") != 0:
            errors.append("missing_root_verified_artifact_count_mismatch")
        return errors
    if _symlink_components(root.parent):
        errors.append("artifact_root_revalidation_ancestor_symlink")
    resolved_root = root.resolve(strict=False)
    if resolved_root == _repository_root() or _is_within(resolved_root, _repository_root()):
        errors.append("artifact_root_revalidation_inside_repository")
    if any(path.is_symlink() for path in resolved_root.rglob("*")):
        errors.append("artifact_root_revalidation_symlinked_path")
    manifest_path = resolved_root / "artifact-manifest.json"
    manifest_present = manifest_path.is_file() and not manifest_path.is_symlink()
    if result.get("artifact_manifest_present") is not manifest_present:
        errors.append("artifact_manifest_presence_mismatch")
    if not manifest_present:
        if result.get("classification") != MISSING_REQUIRED:
            errors.append("artifact_manifest_revalidation_missing")
        if result.get("artifact_roles") != []:
            errors.append("missing_manifest_artifact_roles_mismatch")
        if result.get("verified_artifact_count") != 0:
            errors.append("missing_manifest_verified_artifact_count_mismatch")
        return errors
    try:
        manifest_bytes = _read_stable_bytes(manifest_path)
        manifest_digest = hashlib.sha256(manifest_bytes).hexdigest()
        manifest = _strict_json_bytes(manifest_bytes)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError, RuntimeError):
        errors.append("artifact_manifest_revalidation_invalid")
        return errors
    if result.get("artifact_manifest_sha256") != manifest_digest:
        errors.append("artifact_manifest_digest_mismatch")
    if not isinstance(manifest, dict):
        errors.append("artifact_manifest_revalidation_not_object")
        return errors
    if set(manifest) != MANIFEST_KEYS:
        errors.append("artifact_manifest_schema_keys_mismatch")
    if (
        manifest.get("protocol") != PROTOCOL_ID
        or manifest.get("state_slice") != STATE_SLICE
        or manifest.get("claim_ceiling") != CLAIM_CEILING
        or not _is_schema_version(manifest.get("schema_version"))
    ):
        errors.append("artifact_manifest_identity_mismatch")
    if manifest.get("runtime_capabilities") != result.get("runtime_capabilities"):
        errors.append("result_runtime_capabilities_mismatch")
    if manifest.get("runtime_capabilities") != REQUIRED_CAPABILITIES:
        errors.append("artifact_manifest_runtime_capabilities_mismatch")
    retention = manifest.get("retention")
    expected_retention = {
        "artifact_root_external": True,
        "artifact_root_immutable": True,
        "raw_payloads_external_only": True,
        "raw_payloads_in_result": False,
        "network_access": False,
        "model_training": False,
        "assessment_opened": False,
    }
    if not isinstance(retention, dict) or set(retention) != RETENTION_KEYS:
        errors.append("artifact_manifest_retention_schema_mismatch")
    elif any(retention.get(key) is not value for key, value in expected_retention.items()):
        errors.append("artifact_manifest_retention_boundary_mismatch")
    freshness = manifest.get("freshness")
    if not isinstance(freshness, dict) or set(freshness) != FRESHNESS_KEYS:
        errors.append("artifact_manifest_freshness_schema_mismatch")
    for section, keys in (
        ("arms", {"activation_oracle", "mechanistic"}),
        ("provenance", {"models", "monitor", "corpora", "runtime"}),
        ("execution_contract", {"order", "prediction_lock_required", "arm_independence", "activation_oracle", "mechanistic"}),
    ):
        value = manifest.get(section)
        if not isinstance(value, dict) or set(value) != keys:
            errors.append(f"artifact_manifest_{section}_schema_mismatch")
    entries = manifest.get("artifact_entries")
    roles: list[str] = []
    declared_paths: set[str] = set()
    role_paths = {role: set[str]() for role in ROLE_KINDS}
    if not isinstance(entries, list):
        errors.append("artifact_manifest_entries_revalidation_invalid")
        return errors
    if len(entries) != len(REQUIRED_ROLES):
        errors.append("artifact_manifest_entries_count_mismatch")
    for entry_index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            errors.append(f"artifact_{entry_index}_revalidation_not_object")
            continue
        if set(entry) != {"role", "files", "role_sha256", "artifact_kind"}:
            errors.append(f"artifact_{entry_index}_revalidation_schema_mismatch")
        role = entry.get("role")
        if not isinstance(role, str) or role not in ROLE_KINDS:
            errors.append(f"artifact_{entry_index}_revalidation_role_invalid")
            continue
        if role in roles:
            errors.append(f"artifact_{entry_index}_revalidation_duplicate_role")
        roles.append(role)
        if entry.get("artifact_kind") != ROLE_KINDS[role]:
            errors.append(f"artifact_{entry_index}_revalidation_kind_mismatch")
        files = entry.get("files")
        if not isinstance(files, list) or not files:
            errors.append(f"artifact_{entry_index}_revalidation_files_invalid")
            continue
        rows: list[dict[str, Any]] = []
        for file_index, file_entry in enumerate(files):
            prefix = f"artifact_{entry_index}_file_{file_index}_revalidation"
            if not isinstance(file_entry, dict):
                errors.append(f"{prefix}_not_object")
                continue
            if set(file_entry) != {"path", "byte_len", "sha256"}:
                errors.append(f"{prefix}_schema_mismatch")
            path_value = _safe_relative_path(file_entry.get("path"))
            if path_value is None:
                errors.append(f"{prefix}_unsafe_path")
                continue
            if path_value == "artifact-manifest.json":
                errors.append(f"{prefix}_manifest_self_reference")
            if path_value in declared_paths:
                errors.append(f"{prefix}_duplicate_path")
            declared_paths.add(path_value)
            role_paths[role].add(path_value)
            rows.append({
                "path": path_value,
                "byte_len": file_entry.get("byte_len"),
                "sha256": file_entry.get("sha256"),
            })
            candidate = resolved_root / PurePosixPath(path_value)
            try:
                actual_size, actual_digest = _digest_and_size(candidate)
            except (OSError, ValueError, RuntimeError):
                errors.append(f"{prefix}_missing_or_unreadable")
                continue
            if actual_size != file_entry.get("byte_len"):
                errors.append(f"{prefix}_byte_len_mismatch")
            if actual_digest != file_entry.get("sha256"):
                errors.append(f"{prefix}_digest_mismatch")
        role_digest = entry.get("role_sha256")
        if not _is_digest(role_digest):
            errors.append(f"artifact_{entry_index}_revalidation_role_digest_invalid")
        elif rows and _role_digest(rows) != role_digest:
            errors.append(f"artifact_{entry_index}_revalidation_role_digest_mismatch")
    actual_paths = {
        path.relative_to(resolved_root).as_posix()
        for path in resolved_root.rglob("*")
        if path.is_file() and not path.is_symlink() and path.relative_to(resolved_root) != PurePosixPath("artifact-manifest.json")
    }
    if actual_paths != declared_paths:
        errors.append("artifact_manifest_revalidation_census_mismatch")
    if sorted(roles) != REQUIRED_ROLES:
        errors.append("artifact_manifest_revalidation_roles_mismatch")
    if result.get("artifact_roles") != sorted(roles):
        errors.append("result_artifact_roles_mismatch")
    if result.get("verified_artifact_count") != len(REQUIRED_ROLES) and result.get("classification") == READY:
        errors.append("result_verified_artifact_count_mismatch")
    _validate_manifest_semantics(manifest, role_paths, errors)
    return errors


def validate(result: Any, artifact_root: Path | None = None) -> list[str]:
    errors: list[str] = []
    if not isinstance(result, dict):
        return ["result_not_object"]
    unknown = sorted(set(result) - RESULT_KEYS)
    for key in unknown:
        errors.append(f"result_unknown_field:{key}")
    expected = {
        "protocol": PROTOCOL_ID,
        "state_slice": STATE_SLICE,
        "claim_ceiling": CLAIM_CEILING,
    }
    for key, value in expected.items():
        if result.get(key) != value:
            errors.append(f"{key}_mismatch")
    for key in (
        "model_execution",
        "model_training",
        "network_access",
        "assessment_opened",
        "raw_payloads_retained",
        "accepted_evidence",
        "provider_claims",
        "benchmark_claims",
    ):
        if result.get(key) is not False:
            errors.append(f"{key}_mismatch")
    for key, value in (
        ("confirmation", "NotAuthorized"),
        ("stage_0c", "Blocked"),
        ("stage_1", "BlockedByStage0C"),
    ):
        if result.get(key) != value:
            errors.append(f"{key}_mismatch")
    if not isinstance(result.get("artifact_root"), str) or not result["artifact_root"]:
        errors.append("artifact_root_invalid")
    classification = result.get("classification")
    if classification not in KNOWN_CLASSIFICATIONS:
        errors.append("unknown_classification")
    if result.get("required_roles") != REQUIRED_ROLES:
        errors.append("required_roles_mismatch")
    if result.get("required_capabilities") != REQUIRED_CAPABILITIES:
        errors.append("required_capabilities_mismatch")
    manifest_present = result.get("artifact_manifest_present")
    if not isinstance(manifest_present, bool):
        errors.append("artifact_manifest_present_invalid")
        manifest_present = False
    manifest_digest = result.get("artifact_manifest_sha256")
    if manifest_present and not _is_digest(manifest_digest):
        errors.append("artifact_manifest_sha256_invalid")
    if not manifest_present and manifest_digest is not None:
        errors.append("artifact_manifest_sha256_without_manifest")
    runtime_capabilities = result.get("runtime_capabilities")
    if not isinstance(runtime_capabilities, list) or any(
        not isinstance(capability, str) for capability in runtime_capabilities
    ):
        errors.append("runtime_capabilities_mismatch")
    elif classification == READY and runtime_capabilities != REQUIRED_CAPABILITIES:
        errors.append("runtime_capabilities_mismatch")
    elif classification != READY and runtime_capabilities:
        errors.append("runtime_capabilities_present_while_not_ready")
    artifact_roles = result.get("artifact_roles")
    if not isinstance(artifact_roles, list) or any(not isinstance(role, str) for role in artifact_roles):
        errors.append("artifact_roles_invalid")
        artifact_roles = []
    if len(artifact_roles) != len(set(artifact_roles)):
        errors.append("artifact_roles_duplicate")
    reasons = result.get("reasons")
    if not isinstance(reasons, list) or any(not isinstance(reason, str) for reason in reasons):
        errors.append("reasons_invalid")
        reasons = []
    verified_count = result.get("verified_artifact_count")
    if isinstance(verified_count, bool) or not isinstance(verified_count, int) or verified_count < 0:
        errors.append("verified_artifact_count_invalid")
        verified_count = -1
    if classification == READY:
        if not manifest_present:
            errors.append("ready_without_manifest")
        if sorted(artifact_roles) != REQUIRED_ROLES:
            errors.append("ready_without_all_required_roles")
        if verified_count != len(REQUIRED_ROLES):
            errors.append("ready_without_all_verified_artifacts")
        if reasons:
            errors.append("ready_with_reasons")
    elif classification in {MISSING_ROOT, MISSING_REQUIRED, INVALID} and not reasons:
        errors.append("stop_without_reason")
    if _contains_forbidden_key(result):
        errors.append("forbidden_payload_field")
    errors.extend(_revalidate_root(result, artifact_root))
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("result", type=Path)
    parser.add_argument("--artifact-root", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        result = _strict_json(args.result)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        print(json.dumps({"valid": False, "errors": [f"result_invalid:{type(exc).__name__}"]}, sort_keys=True))
        return 2
    errors = validate(result, args.artifact_root)
    print(json.dumps({"valid": not errors, "errors": errors}, sort_keys=True))
    return 0 if not errors else 2


if __name__ == "__main__":
    sys.exit(main())
