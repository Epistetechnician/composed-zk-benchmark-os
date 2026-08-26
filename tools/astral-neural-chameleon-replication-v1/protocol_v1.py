#!/usr/bin/env python3
"""Fail-closed custody preflight for a Neural Chameleon replication.

State slice: astral-neural-chameleon-replication-v1-preflight.

This module validates only an operator-supplied, repository-external artifact
manifest. It never loads a checkpoint, trains a model, contacts a network, or
opens a scientific assessment.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path
import stat
from typing import Any


PROTOCOL_ID = "astral-neural-chameleon-replication-v1"
STATE_SLICE = "astral-neural-chameleon-replication-v1-preflight"
CLAIM_CEILING = "LocalDevelopmentNeuralChameleonReplicationPreflightOnly"
MANIFEST_SCHEMA_VERSION = 1

READY = "ReadyForInstrumentQualification"
MISSING_ROOT = "MissingArtifactRoot"
MISSING_REQUIRED = "MissingRequiredArtifact"
INVALID = "ArtifactValidationFailed"

ROLE_KINDS = {
    "chameleon_checkpoint": "checkpoint",
    "precursor_checkpoint": "checkpoint",
    "activation_oracle_checkpoint": "oracle",
    "linear_monitor_bundle": "monitor",
    "oracle_corpus_bundle": "corpus",
    "mechanistic_corpus_bundle": "corpus",
    "runtime_manifest": "runtime",
}
REQUIRED_ROLES = tuple(sorted(ROLE_KINDS))
REQUIRED_CAPABILITIES = tuple(sorted({
    "teacher_forced_same_response",
    "residual_layer_capture",
    "attention_head_output_capture",
    "attention_qkv_capture",
    "residual_state_transplant",
    "weight_slice_hybridization",
    "linear_monitor_scoring",
    "activation_oracle_scoring",
}))
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
ENTRY_KEYS = {"role", "files", "role_sha256", "artifact_kind"}
FILE_KEYS = {"path", "byte_len", "sha256"}
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
EXECUTION_CONTRACT_KEYS = {
    "order", "prediction_lock_required", "arm_independence", "activation_oracle", "mechanistic"
}
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


def _open_regular_file(path: Path) -> Any:
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
        return os.fdopen(descriptor, "rb")
    except BaseException:
        os.close(descriptor)
        raise


def _read_stable_bytes(path: Path) -> bytes:
    with _open_regular_file(path) as handle:
        before = os.fstat(handle.fileno())
        payload = handle.read()
        after = os.fstat(handle.fileno())
    if _file_signature(before) != _file_signature(after):
        raise OSError("artifact changed during read")
    return payload


def _digest_and_size(path: Path) -> tuple[int, str]:
    digest = hashlib.sha256()
    with _open_regular_file(path) as handle:
        before = os.fstat(handle.fileno())
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
        after = os.fstat(handle.fileno())
    if _file_signature(before) != _file_signature(after):
        raise OSError("artifact changed during hashing")
    return before.st_size, digest.hexdigest()


def _file_signature(metadata: os.stat_result) -> tuple[int, int, int, int, int]:
    return (
        metadata.st_dev,
        metadata.st_ino,
        metadata.st_size,
        metadata.st_mtime_ns,
        metadata.st_ctime_ns,
    )


def sha256_file(path: Path) -> str:
    return _digest_and_size(path)[1]


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


def _safe_relative_path(value: Any) -> Path | None:
    if not isinstance(value, str) or not value:
        return None
    if "\x00" in value or "\\" in value or any(ord(character) < 32 for character in value):
        return None
    if value.startswith("/") or value.startswith("//") or ":" in value.split("/", 1)[0]:
        return None
    path = Path(value)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        return None
    if path.as_posix() != value:
        return None
    return path


def _unresolved_absolute(path: Path) -> Path:
    return path if path.is_absolute() else Path.cwd() / path


def _symlink_components(path: Path) -> list[str]:
    absolute = _unresolved_absolute(path)
    current = Path(absolute.anchor)
    found: list[str] = []
    for component in absolute.parts[1:]:
        current /= component
        if current.is_symlink():
            found.append(str(current))
    return found


def _repository_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _is_within(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def _base_result(root: Path) -> dict[str, Any]:
    return {
        "protocol": PROTOCOL_ID,
        "state_slice": STATE_SLICE,
        "claim_ceiling": CLAIM_CEILING,
        "artifact_root": str(root),
        "classification": MISSING_REQUIRED,
        "required_roles": list(REQUIRED_ROLES),
        "required_capabilities": list(REQUIRED_CAPABILITIES),
        "runtime_capabilities": [],
        "artifact_manifest_present": False,
        "artifact_manifest_sha256": None,
        "artifact_roles": [],
        "verified_artifact_count": 0,
        "model_execution": False,
        "model_training": False,
        "network_access": False,
        "assessment_opened": False,
        "raw_payloads_retained": False,
        "confirmation": "NotAuthorized",
        "stage_0c": "Blocked",
        "stage_1": "BlockedByStage0C",
        "accepted_evidence": False,
        "provider_claims": False,
        "benchmark_claims": False,
        "reasons": [],
    }


def _artifact_census(root: Path) -> set[str]:
    return {
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.is_file()
        and not path.is_symlink()
        and path.relative_to(root) != Path("artifact-manifest.json")
    }


def _symlink_paths(root: Path) -> list[str]:
    return sorted(
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.is_symlink()
    )


def _is_digest(value: Any, lengths: set[int] = {64}) -> bool:
    return isinstance(value, str) and len(value) in lengths and all(
        character in "0123456789abcdef" for character in value
    )


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
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) and 0 < value < 1


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


def _validate_arm_protocols(arms: Any, errors: list[str]) -> None:
    if not _object_shape(arms, ARM_KEYS, "manifest_arms", errors):
        return
    oracle = arms.get("activation_oracle")
    if _object_shape(oracle, ORACLE_ARM_KEYS, "manifest_activation_oracle", errors):
        for key, expected in ARM_ROLE_BINDINGS["activation_oracle"].items():
            if oracle.get(key) != expected:
                errors.append(f"manifest_activation_oracle_{key}_mismatch")
        if oracle.get("primary_endpoint") != "activation_oracle_robustness_at_fixed_fpr":
            errors.append("manifest_activation_oracle_primary_endpoint_mismatch")
        if not _nonempty_string(oracle.get("formula")):
            errors.append("manifest_activation_oracle_formula_invalid")
        if oracle.get("activation_position") != "last_token":
            errors.append("manifest_activation_oracle_activation_position_mismatch")
        if not _nonnegative_int(oracle.get("activation_layer")):
            errors.append("manifest_activation_oracle_activation_layer_invalid")
        for key in ("trigger_template", "score_rule"):
            if not _nonempty_string(oracle.get(key)):
                errors.append(f"manifest_activation_oracle_{key}_invalid")
        if oracle.get("metrics") != ORACLE_METRICS:
            errors.append("manifest_activation_oracle_metrics_mismatch")
        if oracle.get("controls") != ORACLE_CONTROLS:
            errors.append("manifest_activation_oracle_controls_mismatch")
        for key in ("fit_rows", "tune_rows", "assessment_rows"):
            if not _positive_int(oracle.get(key)):
                errors.append(f"manifest_activation_oracle_{key}_invalid")
        if not _finite_unit_interval(oracle.get("fixed_fpr")):
            errors.append("manifest_activation_oracle_fixed_fpr_invalid")
        if oracle.get("prediction_lock_required") is not True:
            errors.append("manifest_activation_oracle_prediction_lock_mismatch")

    mechanistic = arms.get("mechanistic")
    if _object_shape(mechanistic, MECHANISTIC_ARM_KEYS, "manifest_mechanistic", errors):
        for key, expected in ARM_ROLE_BINDINGS["mechanistic"].items():
            if mechanistic.get(key) != expected:
                errors.append(f"manifest_mechanistic_{key}_mismatch")
        if mechanistic.get("primary_endpoint") != "direct_held_out_intervention_effect":
            errors.append("manifest_mechanistic_primary_endpoint_mismatch")
        if not _nonempty_string(mechanistic.get("formula")):
            errors.append("manifest_mechanistic_formula_invalid")
        if not _nonnegative_int(mechanistic.get("monitor_layer")):
            errors.append("manifest_mechanistic_monitor_layer_invalid")
        for key in ("monitor_definition", "score_rule", "bootstrap_unit"):
            if not _nonempty_string(mechanistic.get(key)):
                errors.append(f"manifest_mechanistic_{key}_invalid")
        for key in ("transplant_sites", "head_set"):
            value = mechanistic.get(key)
            if not isinstance(value, list) or not value or any(not _nonempty_string(item) for item in value):
                errors.append(f"manifest_mechanistic_{key}_invalid")
            elif len(value) != len(set(value)):
                errors.append(f"manifest_mechanistic_{key}_duplicate")
        if mechanistic.get("qkv_factorial") != QKV_FACTORIAL:
            errors.append("manifest_mechanistic_qkv_factorial_mismatch")
        if mechanistic.get("hybridization_slices") != HYBRIDIZATION_SLICES:
            errors.append("manifest_mechanistic_hybridization_slices_mismatch")
        if mechanistic.get("metrics") != MECHANISTIC_METRICS:
            errors.append("manifest_mechanistic_metrics_mismatch")
        if mechanistic.get("controls") != MECHANISTIC_CONTROLS:
            errors.append("manifest_mechanistic_controls_mismatch")
        for key in ("fit_rows", "tune_rows", "assessment_rows"):
            if not _positive_int(mechanistic.get(key)):
                errors.append(f"manifest_mechanistic_{key}_invalid")
        if mechanistic.get("prediction_lock_required") is not True:
            errors.append("manifest_mechanistic_prediction_lock_mismatch")


def _validate_freshness(freshness: Any, errors: list[str]) -> None:
    if not _object_shape(freshness, FRESHNESS_KEYS, "manifest_freshness", errors):
        return
    if freshness.get("disallow_protocols") != DISALLOWED_PROTOCOLS:
        errors.append("manifest_freshness_disallow_protocols_mismatch")
    if freshness.get("disallow_concepts") is not True:
        errors.append("manifest_freshness_disallow_concepts_mismatch")
    if not _is_digest(freshness.get("concept_registry_sha256")):
        errors.append("manifest_freshness_concept_registry_sha256_invalid")
    for key in ("disallow_predictions", "disallow_assessment_rows", "disallow_artifacts"):
        if freshness.get(key) is not True:
            errors.append(f"manifest_freshness_{key}_mismatch")
    if freshness.get("source_study_reuse") != "ExplicitSourceInputsOnly":
        errors.append("manifest_freshness_source_study_reuse_mismatch")
    if freshness.get("astral_derived_selection") is not False:
        errors.append("manifest_freshness_astral_derived_selection_mismatch")


def _validate_provenance(provenance: Any, role_paths: dict[str, set[str]], errors: list[str]) -> dict[str, dict[str, int]]:
    panel_counts: dict[str, dict[str, int]] = {}
    if not _object_shape(provenance, PROVENANCE_KEYS, "manifest_provenance", errors):
        return panel_counts
    models = provenance.get("models")
    if _object_shape(models, MODEL_ROLES, "manifest_provenance_models", errors):
        for role in sorted(MODEL_ROLES):
            descriptor = models.get(role)
            prefix = f"manifest_provenance_model_{role}"
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
    if _object_shape(monitor, MONITOR_KEYS, "manifest_provenance_monitor", errors):
        for key in ("source_repository", "calibration", "score_definition"):
            if not _nonempty_string(monitor.get(key)):
                errors.append(f"manifest_provenance_monitor_{key}_invalid")
        source_repository = monitor.get("source_repository")
        if not isinstance(source_repository, str) or not source_repository.startswith("https://"):
            errors.append("manifest_provenance_monitor_source_repository_invalid")
        if not _is_digest(monitor.get("source_commit"), {40, 64}):
            errors.append("manifest_provenance_monitor_source_commit_invalid")
        if monitor.get("trained_on_role") != "mechanistic_corpus_bundle":
            errors.append("manifest_provenance_monitor_trained_on_role_mismatch")
        if not _nonnegative_int(monitor.get("layer")):
            errors.append("manifest_provenance_monitor_layer_invalid")
        if not _finite_unit_interval(monitor.get("threshold")):
            errors.append("manifest_provenance_monitor_threshold_invalid")
        if not _nonempty_string(monitor.get("pooling")):
            errors.append("manifest_provenance_monitor_pooling_invalid")

    corpora = provenance.get("corpora")
    if _object_shape(corpora, CORPUS_ROLES, "manifest_provenance_corpora", errors):
        for role in sorted(CORPUS_ROLES):
            descriptor = corpora.get(role)
            prefix = f"manifest_provenance_corpus_{role}"
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
    if _object_shape(runtime, RUNTIME_DESCRIPTOR_KEYS, "manifest_provenance_runtime", errors):
        if not _nonempty_string(runtime.get("python")):
            errors.append("manifest_provenance_runtime_python_invalid")
        libraries = runtime.get("libraries")
        if not isinstance(libraries, dict) or not libraries or any(
            not _nonempty_string(key) or not _nonempty_string(value) for key, value in libraries.items()
        ):
            errors.append("manifest_provenance_runtime_libraries_invalid")
        if not _is_digest(runtime.get("source_commit"), {40, 64}):
            errors.append("manifest_provenance_runtime_source_commit_invalid")
    return panel_counts


def _validate_execution_contract(contract: Any, arms: Any, errors: list[str]) -> None:
    if not _object_shape(contract, EXECUTION_CONTRACT_KEYS, "manifest_execution_contract", errors):
        return
    if contract.get("order") != EXECUTION_ORDER:
        errors.append("manifest_execution_contract_order_mismatch")
    if contract.get("prediction_lock_required") is not True:
        errors.append("manifest_execution_contract_prediction_lock_mismatch")
    independence = contract.get("arm_independence")
    independence_keys = {"shared_roles", "forbid_cross_arm_selection", "forbid_cross_arm_evidence"}
    if _object_shape(independence, independence_keys, "manifest_execution_contract_arm_independence", errors):
        if independence.get("shared_roles") != ["runtime_manifest"]:
            errors.append("manifest_execution_contract_shared_roles_mismatch")
        for key in ("forbid_cross_arm_selection", "forbid_cross_arm_evidence"):
            if independence.get(key) is not True:
                errors.append(f"manifest_execution_contract_{key}_mismatch")
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
        if not _object_shape(spec, keys, f"manifest_execution_contract_{name}", errors):
            continue
        source = arms.get(name)
        if not isinstance(source, dict):
            continue
        for key in ("formula", "metrics", "controls", "fit_rows", "tune_rows", "assessment_rows"):
            if spec.get(key) != source.get(key):
                errors.append(f"manifest_execution_contract_{name}_{key}_mismatch")
        if spec.get("assessment_requires_prediction_lock") is not True:
            errors.append(f"manifest_execution_contract_{name}_prediction_lock_mismatch")
        if name == "activation_oracle":
            if spec.get("fixed_fpr") != source.get("fixed_fpr"):
                errors.append("manifest_execution_contract_activation_oracle_fixed_fpr_mismatch")
        else:
            if spec.get("bootstrap_unit") != source.get("bootstrap_unit"):
                errors.append("manifest_execution_contract_mechanistic_bootstrap_unit_mismatch")
            if spec.get("qkv_combinations") != QKV_FACTORIAL:
                errors.append("manifest_execution_contract_mechanistic_qkv_mismatch")
            if spec.get("transplant_directions") != ["ordinary_to_triggered", "triggered_to_ordinary"]:
                errors.append("manifest_execution_contract_mechanistic_transplant_directions_mismatch")
            if spec.get("hybridization_slices") != HYBRIDIZATION_SLICES:
                errors.append("manifest_execution_contract_mechanistic_hybridization_slices_mismatch")


def _validate_manifest(root: Path, manifest: Any) -> tuple[list[str], list[str], int]:
    errors: list[str] = []
    roles: list[str] = []
    verified_count = 0
    if not isinstance(manifest, dict):
        return ["manifest_not_object"], roles, verified_count
    unknown = sorted(set(manifest) - MANIFEST_KEYS)
    missing = sorted(MANIFEST_KEYS - set(manifest))
    if unknown:
        errors.append(f"manifest_unknown_fields:{','.join(unknown)}")
    if missing:
        errors.append(f"manifest_missing_fields:{','.join(missing)}")
    expected = {
        "protocol": PROTOCOL_ID,
        "state_slice": STATE_SLICE,
        "claim_ceiling": CLAIM_CEILING,
    }
    for key, value in expected.items():
        if manifest.get(key) != value:
            errors.append(f"manifest_{key}_mismatch")
    schema_version = manifest.get("schema_version")
    if (
        isinstance(schema_version, bool)
        or not isinstance(schema_version, int)
        or schema_version != MANIFEST_SCHEMA_VERSION
    ):
        errors.append("manifest_schema_version_mismatch")

    capabilities = manifest.get("runtime_capabilities")
    if not isinstance(capabilities, list) or any(
        not isinstance(capability, str) for capability in capabilities
    ):
        errors.append("runtime_capabilities_invalid")
    elif len(capabilities) != len(set(capabilities)):
        errors.append("runtime_capabilities_duplicate")
    elif capabilities != list(REQUIRED_CAPABILITIES):
        errors.append("runtime_capabilities_mismatch")

    retention = manifest.get("retention")
    if not isinstance(retention, dict):
        errors.append("retention_not_object")
    else:
        unknown_retention = sorted(set(retention) - RETENTION_KEYS)
        missing_retention = sorted(RETENTION_KEYS - set(retention))
        if unknown_retention:
            errors.append(f"retention_unknown_fields:{','.join(unknown_retention)}")
        if missing_retention:
            errors.append(f"retention_missing_fields:{','.join(missing_retention)}")
        required_retention = {
            "artifact_root_external": True,
            "artifact_root_immutable": True,
            "raw_payloads_external_only": True,
            "raw_payloads_in_result": False,
            "network_access": False,
            "model_training": False,
            "assessment_opened": False,
        }
        for key, value in required_retention.items():
            if retention.get(key) is not value:
                errors.append(f"retention_{key}_mismatch")

    _validate_freshness(manifest.get("freshness"), errors)

    entries = manifest.get("artifact_entries")
    if not isinstance(entries, list):
        errors.append("artifact_entries_not_array")
        return errors, roles, verified_count
    if len(entries) != len(REQUIRED_ROLES):
        errors.append("artifact_entries_count_mismatch")

    seen_roles: set[str] = set()
    seen_paths: set[str] = set()
    declared_paths: set[str] = set()
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            errors.append(f"artifact_{index}_not_object")
            continue
        unknown_entry = sorted(set(entry) - ENTRY_KEYS)
        missing_entry = sorted(ENTRY_KEYS - set(entry))
        if unknown_entry:
            errors.append(f"artifact_{index}_unknown_fields:{','.join(unknown_entry)}")
        if missing_entry:
            errors.append(f"artifact_{index}_missing_fields:{','.join(missing_entry)}")
        role = entry.get("role")
        if not isinstance(role, str) or role not in ROLE_KINDS:
            errors.append(f"artifact_{index}_unknown_role")
            continue
        roles.append(role)
        if role in seen_roles:
            errors.append(f"duplicate_artifact_role:{role}")
        seen_roles.add(role)
        files = entry.get("files")
        if not isinstance(files, list) or not files:
            errors.append(f"artifact_{index}_files_invalid")
            continue
        if entry.get("artifact_kind") != ROLE_KINDS[role]:
            errors.append(f"artifact_{index}_kind_mismatch")
        role_errors_before = len(errors)
        role_rows: list[dict[str, Any]] = []
        if isinstance(files, list):
            for file_index, file_entry in enumerate(files):
                file_prefix = f"artifact_{index}_file_{file_index}"
                if not _object_shape(file_entry, FILE_KEYS, file_prefix, errors):
                    continue
                path = _safe_relative_path(file_entry.get("path"))
                if path is None:
                    errors.append(f"{file_prefix}_unsafe_path")
                    continue
                path_text = path.as_posix()
                declared_paths.add(path_text)
                if path_text == "artifact-manifest.json":
                    errors.append(f"{file_prefix}_manifest_self_reference")
                if path_text in seen_paths:
                    errors.append(f"duplicate_artifact_path:{path_text}")
                seen_paths.add(path_text)
                digest = file_entry.get("sha256")
                byte_len = file_entry.get("byte_len")
                role_rows.append({"path": path_text, "byte_len": byte_len, "sha256": digest})
                if not _is_digest(digest):
                    errors.append(f"{file_prefix}_digest_invalid")
                if not _nonnegative_int(byte_len):
                    errors.append(f"{file_prefix}_byte_len_invalid")
                candidate = root / path
                try:
                    candidate.resolve().relative_to(root.resolve())
                except (OSError, RuntimeError, ValueError):
                    errors.append(f"{file_prefix}_path_escapes_root")
                    continue
                try:
                    actual_size, actual_digest = _digest_and_size(candidate)
                except (OSError, ValueError, RuntimeError):
                    errors.append(f"{file_prefix}_missing_or_unreadable")
                    continue
                if _nonnegative_int(byte_len) and actual_size != byte_len:
                    errors.append(f"{file_prefix}_byte_len_mismatch")
                if _is_digest(digest) and actual_digest != digest:
                    errors.append(f"{file_prefix}_digest_mismatch")
        role_digest = entry.get("role_sha256")
        if not _is_digest(role_digest):
            errors.append(f"artifact_{index}_role_digest_invalid")
        elif role_rows and _role_digest(role_rows) != role_digest:
            errors.append(f"artifact_{index}_role_digest_mismatch")
        if len(errors) == role_errors_before:
            verified_count += 1

    if set(roles) != set(REQUIRED_ROLES):
        missing_roles = sorted(set(REQUIRED_ROLES) - set(roles))
        unknown_roles = sorted(set(roles) - set(REQUIRED_ROLES))
        if missing_roles:
            errors.append(f"missing_required_roles:{','.join(missing_roles)}")
        if unknown_roles:
            errors.append(f"unknown_roles:{','.join(unknown_roles)}")
    if root.is_dir() and not root.is_symlink():
        actual_paths = _artifact_census(root)
        if actual_paths != declared_paths:
            errors.append("artifact_manifest_census_mismatch")
    role_paths = {role: set[str]() for role in ROLE_KINDS}
    for entry in entries:
        if not isinstance(entry, dict) or entry.get("role") not in role_paths:
            continue
        files = entry.get("files")
        if not isinstance(files, list):
            continue
        for item in files:
            if isinstance(item, dict) and isinstance(item.get("path"), str):
                role_paths[entry["role"]].add(item["path"])
    panel_counts = _validate_provenance(manifest.get("provenance"), role_paths, errors)
    _validate_arm_protocols(manifest.get("arms"), errors)
    _validate_execution_contract(manifest.get("execution_contract"), manifest.get("arms"), errors)
    arms = manifest.get("arms")
    if isinstance(arms, dict):
        for arm_name, corpus_role in (
            ("activation_oracle", "oracle_corpus_bundle"),
            ("mechanistic", "mechanistic_corpus_bundle"),
        ):
            arm = arms.get(arm_name)
            counts = panel_counts.get(corpus_role)
            if isinstance(arm, dict) and counts is not None:
                for arm_key, corpus_key in (("fit_rows", "fit"), ("tune_rows", "tune"), ("assessment_rows", "assessment")):
                    if arm.get(arm_key) != counts.get(corpus_key):
                        errors.append(f"manifest_{arm_name}_{arm_key}_corpus_count_mismatch")
    return errors, sorted(set(roles)), verified_count


def inspect(root: Path, repository_root: Path | None = None) -> dict[str, Any]:
    """Inspect an external artifact root without executing any model code."""

    declared_root = Path(root)
    unresolved_root = _unresolved_absolute(declared_root)
    try:
        root = declared_root.resolve(strict=False)
    except (OSError, RuntimeError, ValueError) as exc:
        result = _base_result(unresolved_root)
        result["classification"] = INVALID
        result["reasons"] = [f"artifact_root_invalid:{type(exc).__name__}"]
        return result
    result = _base_result(root)
    if declared_root.is_symlink() or not root.is_dir():
        result["classification"] = MISSING_ROOT
        result["reasons"] = ["artifact_root_missing_or_not_directory"]
        return result
    ancestor_symlinks = _symlink_components(unresolved_root.parent)
    if ancestor_symlinks:
        result["classification"] = INVALID
        result["reasons"] = [f"artifact_root_ancestor_symlink:{path}" for path in ancestor_symlinks]
        return result
    trusted_repository_root = (repository_root or _repository_root()).resolve(strict=False)
    if _is_within(root, trusted_repository_root):
        result["classification"] = INVALID
        result["reasons"] = ["artifact_root_inside_repository"]
        return result
    try:
        symlinks = _symlink_paths(root)
    except (OSError, RuntimeError) as exc:
        result["classification"] = INVALID
        result["reasons"] = [f"artifact_root_scan_failed:{type(exc).__name__}"]
        return result
    if symlinks:
        result["classification"] = INVALID
        result["reasons"] = [f"symlinked_path:{path}" for path in symlinks]
        return result
    manifest_path = root / "artifact-manifest.json"
    if not manifest_path.is_file() or manifest_path.is_symlink():
        result["reasons"] = ["artifact_manifest_missing"]
        return result
    result["artifact_manifest_present"] = True
    try:
        manifest_bytes = _read_stable_bytes(manifest_path)
        result["artifact_manifest_sha256"] = hashlib.sha256(manifest_bytes).hexdigest()
        manifest = _strict_json_bytes(manifest_bytes)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError, RuntimeError) as exc:
        result["classification"] = INVALID
        result["reasons"] = [f"artifact_manifest_invalid:{type(exc).__name__}"]
        return result
    try:
        errors, roles, verified_count = _validate_manifest(root, manifest)
    except (OSError, UnicodeDecodeError, ValueError, RuntimeError, TypeError) as exc:
        result["classification"] = INVALID
        result["reasons"] = [f"artifact_validation_exception:{type(exc).__name__}"]
        return result
    result["artifact_roles"] = roles
    result["runtime_capabilities"] = manifest.get("runtime_capabilities", []) if isinstance(manifest, dict) else []
    result["verified_artifact_count"] = verified_count
    if errors:
        result["classification"] = INVALID if any(
            reason.startswith(
                ("manifest_", "runtime_", "retention_", "artifact_", "duplicate_", "unknown_", "artifact_manifest")
            )
            for reason in errors
        ) else MISSING_REQUIRED
        result["reasons"] = errors
        return result
    result["classification"] = READY
    return result
