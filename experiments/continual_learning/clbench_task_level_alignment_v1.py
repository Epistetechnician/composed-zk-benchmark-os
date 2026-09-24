"""Fail-closed design contract for the CL-Bench task-level alignment slice.

State slice: ``aligned-holistic-continual-learning-interpretability-monorepo-v1``.

This module validates a machine-readable protocol and exposes an execution
gate that remains closed until a separately administered review and execution
authorization exist.  It does not acquire benchmark data, load a model, call
a provider, spend money, retain traces, score assessment data, or mutate the
Evidence Ledger.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Mapping


STATE_SLICE = "aligned-holistic-continual-learning-interpretability-monorepo-v1"
PROTOCOL_ID = "clbench-task-level-alignment-v1"
SCHEMA_VERSION = f"{PROTOCOL_ID}-manifest"
STATUS = "DESIGN_ONLY_PENDING_INDEPENDENT_ACCEPT"
CLAIM_CEILING = "LocalDevelopmentCLBenchTaskLevelProtocolDesignV1"
REPO_ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = Path(__file__).with_name("clbench_task_level_alignment_v1.json")
REVIEW_PACKET_RELATIVE_PATH = Path("docs/research/continual-learning/311-clbench-task-level-alignment-v1-review-packet.md")
REVIEW_PACKET_PATH = REPO_ROOT / REVIEW_PACKET_RELATIVE_PATH
BENCHMARK_RELEASE_COMMIT = "9cc63c0f429048b843e8d43ac4f2b0ea4df13724"
BENCHMARK_RELEASE_TREE = "ec757e2d999d895a7beec03270c6d014c01f2915"
BENCHMARK_TASK_MANIFEST_PATHS = (
    "src/tasks",
    "configs",
    "src/registry.py",
    "src/system_manifest.py",
    "pyproject.toml",
    "uv.lock",
)
REVIEW_BUNDLE_PATHS = (
    "AGENTS.md",
    "docs/research/continual-learning/310-clbench-task-level-alignment-v1-protocol.md",
    "docs/research/continual-learning/311-clbench-task-level-alignment-v1-review-packet.md",
    "docs/research/independent-review-communication-v1.md",
    "experiments/continual_learning/README.md",
    "experiments/continual_learning/clbench_task_level_alignment_v1.py",
    "experiments/continual_learning/tests/test_clbench_task_level_alignment_v1.py",
    "experiments/continual_learning/clbench_task_level_alignment_review_bridge_v1.py",
    "experiments/continual_learning/tests/test_clbench_task_level_alignment_review_bridge_v1.py",
    "tools/independent_review_communication_v1/README.md",
    "tools/independent_review_communication_v1/cli.py",
    "tools/independent_review_communication_v1/protocol.py",
    "tools/independent_review_communication_v1/tests/test_protocol.py",
)

TASK_IDS = (
    "blind_spectrum_monitoring",
    "codebase_adaptation",
    "cohort_studies",
    "database_exploration",
    "exploitable_poker",
    "sales_prediction",
)
ARMS = (
    "no_update",
    "sgd",
    "replay",
    "ewc",
    "orthogonal",
    "icl",
    "external_memory",
)
SPLITS = ("fit", "tune", "assessment")
REPLICATION_SEEDS = (202609161, 202609162, 202609163, 202609164, 202609165)
ORDER_SEEDS = (73101, 73102, 73103)
REVIEW_STATUS = "PENDING_INDEPENDENT_ACCEPT"
REVIEW_TRANSPORT_PROTOCOL = "independent-review-communication-boundary-v1"


class ProtocolError(ValueError):
    """Raised when the frozen design contract is invalid."""


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ProtocolError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def load_json(path: Path) -> Any:
    """Load strict UTF-8 JSON without duplicate keys or non-standard numbers."""

    try:
        return json.loads(
            path.read_bytes().decode("utf-8"),
            object_pairs_hook=_reject_duplicate_keys,
            parse_constant=lambda value: (_ for _ in ()).throw(
                ProtocolError(f"non-standard JSON constant: {value}")
            ),
        )
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ProtocolError(f"cannot read JSON: {path}") from exc


def canonical_bytes(value: Any) -> bytes:
    """Return the protocol's canonical JSON representation."""

    try:
        return json.dumps(
            value,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise ProtocolError("value is not canonical JSON") from exc


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def canonical_digest(value: Any) -> str:
    return sha256_bytes(canonical_bytes(value))


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ProtocolError(message)


def _strict_keys(value: Mapping[str, Any], expected: set[str], label: str) -> None:
    _require(set(value) == expected, f"{label} schema")


def _require_bool(value: Any, label: str) -> None:
    _require(isinstance(value, bool), f"{label} must be boolean")


def _require_nonempty_text(value: Any, label: str) -> None:
    _require(isinstance(value, str) and bool(value.strip()), f"{label} must be non-empty text")


def _require_positive_int(value: Any, label: str) -> None:
    _require(isinstance(value, int) and not isinstance(value, bool) and value > 0, f"{label} must be positive")


def _require_nonnegative_int(value: Any, label: str) -> None:
    _require(isinstance(value, int) and not isinstance(value, bool) and value >= 0, f"{label} must be non-negative")


def _require_absolute_external_path(value: Any, label: str) -> None:
    _require(isinstance(value, str), f"{label} must be text")
    path = Path(value)
    _require(path.is_absolute(), f"{label} must be absolute")
    _require(".." not in path.parts, f"{label} cannot contain parent traversal")
    _require(not path.is_symlink(), f"{label} cannot be a symlink")
    repo_root = Path(__file__).resolve().parents[2]
    try:
        path.relative_to(repo_root)
    except ValueError:
        return
    raise ProtocolError(f"{label} must be outside the repository")


def _validate_benchmark(value: Any) -> None:
    _require(isinstance(value, Mapping), "benchmark must be an object")
    _strict_keys(
        value,
        {
            "name",
            "repository",
            "paper",
            "license",
            "dataset_policy",
            "task_ids",
            "task_semantics",
            "version_binding",
            "release_commit",
            "release_tree",
            "task_manifest_paths",
        },
        "benchmark",
    )
    _require(value["name"] == "Continual Learning Bench", "benchmark name")
    _require(value["repository"] == "https://github.com/pgasawa/continual-learning-bench", "benchmark repository")
    _require(value["paper"] == "https://arxiv.org/abs/2606.05661", "benchmark paper")
    _require(value["license"] == "Apache-2.0", "benchmark license")
    _require(value["dataset_policy"] == "external_after_review_no_repo_copy", "benchmark dataset policy")
    _require(tuple(value["task_ids"]) == TASK_IDS, "benchmark task roster")
    _require(value["task_semantics"] == "ordered_task_instances_with_feedback_and_reward", "benchmark task semantics")
    _require(value["version_binding"] == "external_release_commit_and_task_manifest_required", "benchmark version binding")
    _require(value["release_commit"] == BENCHMARK_RELEASE_COMMIT, "benchmark release commit")
    _require(value["release_tree"] == BENCHMARK_RELEASE_TREE, "benchmark release tree")
    _require(tuple(value["task_manifest_paths"]) == BENCHMARK_TASK_MANIFEST_PATHS, "benchmark task manifest paths")


def _validate_review_bundle(value: Any) -> None:
    _require(isinstance(value, Mapping), "review bundle must be an object")
    _strict_keys(value, {"schema_version", "files", "manifest_excluded", "all_paths_repository_relative"}, "review bundle")
    _require(value["schema_version"] == f"{PROTOCOL_ID}-review-bundle", "review bundle schema version")
    _require(value["manifest_excluded"] is True, "review bundle must exclude its manifest")
    _require(value["all_paths_repository_relative"] is True, "review bundle paths must be relative")
    files = value["files"]
    _require(isinstance(files, list), "review bundle files")
    _require(tuple(item.get("path") for item in files if isinstance(item, Mapping)) == REVIEW_BUNDLE_PATHS, "review bundle file roster")
    _require(len(files) == len(REVIEW_BUNDLE_PATHS), "review bundle file count")
    for item in files:
        _require(isinstance(item, Mapping), "review bundle file entry")
        _strict_keys(item, {"path", "sha256"}, "review bundle file entry")
        relative_path = Path(item["path"])
        _require(not relative_path.is_absolute() and ".." not in relative_path.parts, "review bundle path")
        _require(isinstance(item["sha256"], str) and len(item["sha256"]) == 64 and all(char in "0123456789abcdef" for char in item["sha256"]), "review bundle file digest")
        path = REPO_ROOT / relative_path
        _require(path.is_file() and not path.is_symlink(), f"review bundle file missing: {item['path']}")
        _require(sha256_bytes(path.read_bytes()) == item["sha256"], f"review bundle digest: {item['path']}")


def _validate_exclusion(value: Any) -> None:
    _require(isinstance(value, Mapping), "excluded benchmark must be an object")
    _strict_keys(value, {"name", "dataset_license", "reason", "future_use"}, "excluded benchmark")
    _require(value["name"] == "CL-bench Life", "excluded benchmark name")
    _require(value["dataset_license"] == "custom_evaluation_only", "excluded benchmark license")
    _require(
        value["reason"]
        == "evaluation_only_license_forbids_training_finetuning_calibration_adaptation_and_parameter_updates",
        "excluded benchmark reason",
    )
    _require(value["future_use"] == "separate_inference_only_protocol_after_license_review", "excluded benchmark future use")


def _validate_arms(value: Any) -> None:
    _require(isinstance(value, list), "arm roster")
    _require(all(isinstance(item, Mapping) for item in value), "arm entry must be an object")
    _require(tuple(item["id"] for item in value) == ARMS, "arm roster")
    expected = {
        "no_update": ("none", "fresh_state_per_instance"),
        "sgd": ("parameter_update", "one_shared_online_adapter"),
        "replay": ("parameter_update", "one_shared_online_adapter_plus_fixed_replay"),
        "ewc": ("parameter_update", "one_shared_online_adapter_plus_fisher_penalty"),
        "orthogonal": ("parameter_update", "one_shared_online_adapter_plus_update_projection"),
        "icl": ("in_context", "full_declared_history_context"),
        "external_memory": ("external_memory", "fixed_retrieval_memory"),
    }
    for item in value:
        _require(isinstance(item, Mapping), "arm entry must be an object")
        _strict_keys(item, {"id", "state_channel", "mechanism"}, "arm entry")
        arm_id = item["id"]
        _require(arm_id in expected, "unknown arm")
        _require(tuple(item[key] for key in ("state_channel", "mechanism")) == expected[arm_id], f"{arm_id} arm semantics")


def _validate_splits(value: Any) -> None:
    _require(isinstance(value, Mapping), "splits must be an object")
    _strict_keys(
        value,
        {
            "names",
            "families_per_split",
            "family_unit",
            "assignment",
            "disjointness",
            "assessment_is_unseen_at_lock",
        },
        "splits",
    )
    _require(tuple(value["names"]) == SPLITS, "split names")
    _require(value["families_per_split"] == 90, "families per split")
    _require(value["family_unit"] == "task_id:order_seed:replicate_seed:family_index", "family unit")
    _require(value["assignment"] == "fresh_external_instance_roster_before_fit", "split assignment")
    _require(
        tuple(value["disjointness"])
        == (
            "task_instance_ids_disjoint_across_fit_tune_assessment",
            "source_and_environment_ids_disjoint_across_splits",
            "feedback_and_labels_unavailable_to_other_splits",
        ),
        "split disjointness",
    )
    _require(value["assessment_is_unseen_at_lock"] is True, "assessment visibility")


def _validate_schedule(value: Any) -> None:
    _require(isinstance(value, Mapping), "schedule must be an object")
    _strict_keys(
        value,
        {
            "order_seeds",
            "replicate_seeds",
            "repeats_per_family",
            "paired_environment_seed",
            "protected_probe",
            "feedback_policy",
        },
        "schedule",
    )
    _require(tuple(value["order_seeds"]) == ORDER_SEEDS, "order seeds")
    _require(tuple(value["replicate_seeds"]) == REPLICATION_SEEDS, "replicate seeds")
    _require(value["repeats_per_family"] == 5, "repeats per family")
    _require(value["paired_environment_seed"] is True, "paired environment seed")
    _require(
        value["protected_probe"]
        == "fresh_disjoint_protected_task_instances_after_each_incoming_block_without_feedback",
        "protected probe policy",
    )
    _require(
        value["feedback_policy"]
        == "each_arm_receives_only_feedback_generated_by_its_own_actions_and_same_declared_observation_budget",
        "feedback policy",
    )


def _validate_estimands(value: Any) -> None:
    _require(isinstance(value, Mapping), "estimands must be an object")
    _strict_keys(value, {"reward", "incoming_learning", "protected_retention", "primary", "secondary"}, "estimands")
    _require(value["reward"] == "benchmark_native_reward_and_official_normalized_gain", "reward estimand")
    _require(
        value["incoming_learning"]
        == "mean_normalized_reward_arm_minus_no_update_on_paired_incoming_task_instances",
        "incoming learning estimand",
    )
    _require(
        value["protected_retention"]
        == "post_incoming_protected_probe_reward_arm_minus_no_update_protected_probe_reward",
        "protected retention estimand",
    )
    _require(
        value["primary"]
        == "task_level_incoming_learning_subject_to_protected_retention_and_equal_budget_gates",
        "primary estimand",
    )
    _require(
        tuple(value["secondary"])
        == (
            "official_stateful_minus_stateless_gain",
            "per_task_learning_curve",
            "protected_task_forgetting_harm",
            "resource_cost_by_channel",
            "order_sensitivity",
        ),
        "secondary estimands",
    )


def _validate_budgets(value: Any) -> None:
    _require(isinstance(value, Mapping), "budgets must be an object")
    _strict_keys(
        value,
        {
            "max_environment_steps_per_instance",
            "max_input_tokens_per_instance",
            "max_output_tokens_per_instance",
            "persistent_state_bytes_per_arm",
            "compute_budget_units_per_instance",
            "monitor_calls_per_instance",
            "monitor_tokens_per_call",
            "accounting",
        },
        "budgets",
    )
    expected = {
        "max_environment_steps_per_instance": 40,
        "max_input_tokens_per_instance": 8192,
        "max_output_tokens_per_instance": 2048,
        "persistent_state_bytes_per_arm": 262144,
        "compute_budget_units_per_instance": 100000,
        "monitor_calls_per_instance": 1,
        "monitor_tokens_per_call": 512,
    }
    for key, expected_value in expected.items():
        _require(value[key] == expected_value, f"{key} budget")
    _require(
        tuple(value["accounting"])
        == (
            "same_task_instance_roster_and_feedback_budget",
            "same_compute_ceiling_and_forward_backward_meter",
            "same_persistent_state_byte_ceiling_including_optimizer_memory",
            "same_frozen_monitor_call_and_token_ceiling",
            "base_model_bytes_excluded_and_immutable",
        ),
        "budget accounting",
    )


def _validate_statistics(value: Any) -> None:
    _require(isinstance(value, Mapping), "statistics must be an object")
    _strict_keys(
        value,
        {
            "unit_of_analysis",
            "bootstrap_replicates",
            "confidence_level",
            "multiplicity",
            "primary_task_gate",
            "protected_gate",
            "replication_gate",
            "missingness",
        },
        "statistics",
    )
    _require(value["unit_of_analysis"] == "family_then_task_macro_average", "statistical unit")
    _require(value["bootstrap_replicates"] == 10000, "bootstrap replicates")
    _require(value["confidence_level"] == 0.95, "confidence level")
    _require(value["multiplicity"] == "Holm_across_six_primary_task_tests", "multiplicity")
    _require(
        value["primary_task_gate"]
        == "at_least_four_of_six_tasks_have_positive_lower_95_ci_and_no_task_below_minus_0.02",
        "primary task gate",
    )
    _require(
        value["protected_gate"]
        == "no_task_protected_delta_below_minus_0.05_and_macro_delta_at_least_minus_0.02",
        "protected gate",
    )
    _require(
        value["replication_gate"]
        == "same_direction_and_all_hard_gates_on_fresh_runner_seed_and_custody_set",
        "replication gate",
    )
    _require(value["missingness"] == "fail_closed_no_imputation_no_selected_cell_exclusion", "missingness")


def _validate_prediction_lock(value: Any) -> None:
    _require(isinstance(value, Mapping), "prediction lock must be an object")
    _strict_keys(
        value,
        {
            "required",
            "sealed_before_assessment",
            "selection_source",
            "assessment_labels_available_at_lock",
            "assessment_effects_available_at_lock",
            "one_digest_per_assessment_family",
            "independent_validator_required",
            "lock_contents",
        },
        "prediction lock",
    )
    _require(value["required"] is True and value["sealed_before_assessment"] is True, "prediction lock required")
    _require(value["selection_source"] == "fit_and_tune_only", "prediction lock selection source")
    _require(value["assessment_labels_available_at_lock"] is False, "assessment labels at lock")
    _require(value["assessment_effects_available_at_lock"] is False, "assessment effects at lock")
    _require(value["one_digest_per_assessment_family"] is True, "prediction digest cardinality")
    _require(value["independent_validator_required"] is True, "independent lock validator")
    _require(
        tuple(value["lock_contents"])
        == (
            "selected_arm_or_no_candidate",
            "fixed_hyperparameters_and_update_budget",
            "fixed_monitor_and_thresholds",
            "assessment_family_ids_and_order_seeds_without_labels",
            "protocol_source_and_runtime_digests",
        ),
        "prediction lock contents",
    )


def _validate_custody(value: Any) -> None:
    _require(isinstance(value, Mapping), "custody must be an object")
    _strict_keys(
        value,
        {
            "raw_trace_root",
            "root_class",
            "mode",
            "prior_roots_excluded",
            "raw_trace_retention_hours",
            "aggregate_only_repository_artifacts",
            "deletion_receipt_required",
            "operator_and_validator_roots_distinct",
        },
        "custody",
    )
    _require_absolute_external_path(value["raw_trace_root"], "raw_trace_root")
    _require(value["root_class"] == "external_owner_only_ephemeral", "custody root class")
    _require(value["mode"] == "0700", "custody mode")
    _require(value["prior_roots_excluded"] is True, "prior roots exclusion")
    _require(value["raw_trace_retention_hours"] == 72, "raw trace retention")
    _require(value["aggregate_only_repository_artifacts"] is True, "aggregate-only repository policy")
    _require(value["deletion_receipt_required"] is True, "deletion receipt")
    _require(value["operator_and_validator_roots_distinct"] is True, "custody role separation")


def _validate_replication(value: Any) -> None:
    _require(isinstance(value, Mapping), "replication must be an object")
    _strict_keys(
        value,
        {
            "required",
            "fresh_runner_identity_required",
            "fresh_seed_set_required",
            "same_protocol_digest_required",
            "independent_recomputation_required",
            "independent_custody_root_required",
            "assessment_claim_blocked_until_replication",
        },
        "replication",
    )
    for key in (
        "required",
        "fresh_runner_identity_required",
        "fresh_seed_set_required",
        "same_protocol_digest_required",
        "independent_recomputation_required",
        "independent_custody_root_required",
        "assessment_claim_blocked_until_replication",
    ):
        _require(value[key] is True, f"{key} replication gate")


def _validate_execution_gates(value: Any) -> None:
    _require(isinstance(value, Mapping), "execution gates must be an object")
    _strict_keys(
        value,
        {
            "review_status",
            "review_receipt",
            "model_execution_authorized",
            "provider_calls_authorized",
            "spend_authorized_usd",
            "assessment_authorized",
            "raw_trace_retention_authorized",
            "evidence_ledger_mutation_authorized",
        },
        "execution gates",
    )
    _require(value["review_status"] == REVIEW_STATUS, "review status")
    _require(value["review_receipt"] is None, "review receipt must be absent before acceptance")
    for key in (
        "model_execution_authorized",
        "provider_calls_authorized",
        "assessment_authorized",
        "raw_trace_retention_authorized",
        "evidence_ledger_mutation_authorized",
    ):
        _require(value[key] is False, f"{key} must remain closed")
    _require(value["spend_authorized_usd"] == 0, "spend must remain zero")


def validate_manifest(manifest: Mapping[str, Any], *, manifest_path: Path = MANIFEST_PATH) -> str:
    """Validate the exact design manifest and return its canonical digest."""

    _strict_keys(
        manifest,
        {
            "schema_version",
            "protocol_id",
            "state_slice",
            "status",
            "claim_ceiling",
            "benchmark",
            "excluded_benchmark",
            "arms",
            "splits",
            "schedule",
            "estimands",
            "budgets",
            "statistics",
            "prediction_lock",
            "custody",
            "replication",
            "execution_gates",
            "forbidden_actions",
            "review_bundle",
            "review_packet_path",
            "review_packet_sha256",
        },
        "manifest",
    )
    _require(manifest["schema_version"] == SCHEMA_VERSION, "schema version")
    _require(manifest["protocol_id"] == PROTOCOL_ID, "protocol id")
    _require(manifest["state_slice"] == STATE_SLICE, "state slice")
    _require(manifest["status"] == STATUS, "status")
    _require(manifest["claim_ceiling"] == CLAIM_CEILING, "claim ceiling")
    _validate_benchmark(manifest["benchmark"])
    _validate_exclusion(manifest["excluded_benchmark"])
    _validate_arms(manifest["arms"])
    _validate_splits(manifest["splits"])
    _validate_schedule(manifest["schedule"])
    _validate_estimands(manifest["estimands"])
    _validate_budgets(manifest["budgets"])
    _validate_statistics(manifest["statistics"])
    _validate_prediction_lock(manifest["prediction_lock"])
    _validate_custody(manifest["custody"])
    _validate_replication(manifest["replication"])
    _validate_execution_gates(manifest["execution_gates"])
    _validate_review_bundle(manifest["review_bundle"])

    _require(tuple(manifest["forbidden_actions"]) == (
        "benchmark_data_acquisition_before_review",
        "model_execution_before_independent_accept_and_execution_authorization",
        "provider_call_or_spend",
        "assessment_before_prediction_lock_and_review",
        "raw_trace_storage_in_repository",
        "raw_trace_retention_beyond_72_hours",
        "assessment_tuning_or_selected_cell_exclusion",
        "self_signed_independent_review",
        "accepted_evidence_ledger_mutation",
        "general_alignment_or_production_claim",
    ), "forbidden action roster")

    packet_path = Path(manifest["review_packet_path"])
    _require(packet_path == REVIEW_PACKET_RELATIVE_PATH and not packet_path.is_absolute() and ".." not in packet_path.parts, "review packet path")
    packet_path = REPO_ROOT / packet_path
    _require(packet_path.is_file() and not packet_path.is_symlink(), "review packet missing")
    packet_digest = sha256_bytes(packet_path.read_bytes())
    _require(packet_digest == manifest["review_packet_sha256"], "review packet digest")
    _require(
        isinstance(manifest["review_packet_sha256"], str)
        and len(manifest["review_packet_sha256"]) == 64
        and all(char in "0123456789abcdef" for char in manifest["review_packet_sha256"]),
        "review packet digest format",
    )
    return canonical_digest(manifest)


def validate_manifest_file(path: Path = MANIFEST_PATH) -> dict[str, Any]:
    """Validate the checked-in manifest without acquiring any external input."""

    resolved = path.resolve()
    _require(resolved == MANIFEST_PATH.resolve(), "manifest path")
    manifest = load_json(resolved)
    _require(isinstance(manifest, Mapping), "manifest must be an object")
    digest = validate_manifest(manifest, manifest_path=resolved)
    return {
        "valid": True,
        "protocol_id": PROTOCOL_ID,
        "state_slice": STATE_SLICE,
        "status": STATUS,
        "protocol_digest": digest,
        "review_transport_protocol": REVIEW_TRANSPORT_PROTOCOL,
        "mailbox_packet_digest": f"sha256:{digest}",
        "execution_authorized": False,
    }


def execution_gate(manifest: Mapping[str, Any]) -> dict[str, Any]:
    """Return a non-authorizing gate result for all execution attempts."""

    validate_manifest(manifest)
    reasons = [
        "independent_packet_bound_accept_missing",
        "explicit_execution_authorization_missing",
        "model_execution_closed",
        "provider_calls_closed",
        "assessment_closed",
        "raw_trace_retention_closed",
        "evidence_ledger_mutation_closed",
    ]
    return {
        "allowed": False,
        "state_slice": STATE_SLICE,
        "protocol_id": PROTOCOL_ID,
        "reasons": reasons,
    }


def _main() -> int:
    parser = argparse.ArgumentParser(description="validate the CL-Bench task-level alignment design contract")
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    args = parser.parse_args()
    result = validate_manifest_file(args.manifest)
    print(json.dumps(result, sort_keys=True, indent=2))
    return os.EX_OK


if __name__ == "__main__":
    raise SystemExit(_main())
