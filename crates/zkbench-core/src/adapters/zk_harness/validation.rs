//! Validation for zk-Harness dry-run plans.

use serde::{Deserialize, Serialize};

use crate::evidence::ClaimBoundary;

use super::dry_run::{ZkHarnessDryRunPlan, ZkHarnessExecutionPolicy, ZkHarnessPlannedCommand};
use super::mapping::{candidate_family_label, candidate_mutation_label};

/// Validation issue severity.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum ZkHarnessDryRunValidationIssueSeverity {
    /// Validation error.
    Error,
    /// Validation warning.
    Warning,
}

/// Dry-run validation issue.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ZkHarnessDryRunValidationIssue {
    /// Issue path.
    pub path: String,
    /// Issue message.
    pub message: String,
    /// Issue severity.
    pub severity: ZkHarnessDryRunValidationIssueSeverity,
}

/// Dry-run validation result.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ZkHarnessDryRunValidation {
    /// True when no errors were found.
    pub valid: bool,
    /// Errors.
    pub errors: Vec<ZkHarnessDryRunValidationIssue>,
    /// Warnings.
    pub warnings: Vec<ZkHarnessDryRunValidationIssue>,
}

/// Validate a zk-Harness dry-run plan.
pub fn validate_zk_harness_dry_run_plan(plan: &ZkHarnessDryRunPlan) -> ZkHarnessDryRunValidation {
    let mut errors = Vec::new();
    let mut warnings = Vec::new();

    require_non_empty(&plan.id, "plan.id", "plan id is empty", &mut errors);
    require_non_empty(
        &plan.adapter_manifest_id,
        "plan.adapter_manifest_id",
        "adapter manifest id is empty",
        &mut errors,
    );
    require_non_empty(
        &plan.source_benchmark_pack_id,
        "plan.source_benchmark_pack_id",
        "source benchmark pack id is empty",
        &mut errors,
    );

    if !plan.execution_policy.is_phase_g_allowed()
        || plan.execution_policy == ZkHarnessExecutionPolicy::FutureLiveExecution
    {
        errors.push(error(
            "plan.execution_policy",
            "execution policy is not allowed for Phase G dry-run planning",
        ));
    }
    if plan.claim_boundary != ClaimBoundary::Level0DesignNote {
        errors.push(error(
            "plan.claim_boundary",
            "zk-Harness dry-run plan claim boundary must be Level0DesignNote",
        ));
    }
    if plan.subject.local_pack_claim_boundary > ClaimBoundary::Level1LocalReplay {
        errors.push(error(
            "plan.subject.local_pack_claim_boundary",
            "local source pack evidence is elevated above Level1LocalReplay",
        ));
    }
    if plan.evidence_policy.dry_run_plan_claim_boundary != ClaimBoundary::Level0DesignNote {
        errors.push(error(
            "plan.evidence_policy.dry_run_plan_claim_boundary",
            "dry-run evidence policy must remain Level0DesignNote",
        ));
    }

    for (index, metric) in plan.metric_mappings.iter().enumerate() {
        if metric.observed_value.is_some() {
            errors.push(error(
                format!("plan.metric_mappings[{index}].observed_value"),
                "Phase G metric mappings must not contain observed values",
            ));
        }
        if !metric.planned_only {
            errors.push(error(
                format!("plan.metric_mappings[{index}].planned_only"),
                "Phase G metric mapping must be planned_only",
            ));
        }
    }

    if plan.unsupported_features.is_empty() {
        warnings.push(warning(
            "plan.unsupported_features",
            "dry-run plan should record unsupported live integration features",
        ));
    }

    for (index, step) in plan.planned_steps.iter().enumerate() {
        if !step.dry_run_only {
            errors.push(error(
                format!("plan.planned_steps[{index}].dry_run_only"),
                "planned step is not marked dry-run only",
            ));
        }
        validate_command(
            &step.planned_command,
            &format!("plan.planned_steps[{index}].planned_command"),
            &mut errors,
        );
    }

    for (index, artifact) in plan.pack_mapping.artifact_mappings.iter().enumerate() {
        if !artifact.local_only {
            errors.push(error(
                format!("plan.pack_mapping.artifact_mappings[{index}].local_only"),
                "source pack file is not marked local_only",
            ));
        }
        validate_relative_text(
            &artifact.source_relative_path,
            &format!("plan.pack_mapping.artifact_mappings[{index}].source_relative_path"),
            &mut errors,
        );
        if artifact.source_digest.byte_len == 0 {
            errors.push(error(
                format!("plan.pack_mapping.artifact_mappings[{index}].source_digest"),
                "source pack file digest was not preserved",
            ));
        }
    }

    for (index, family) in plan.pack_mapping.family_mappings.iter().enumerate() {
        if candidate_family_label(family.source_family_kind)
            != Some(family.candidate_workload_label.as_str())
        {
            errors.push(error(
                format!("plan.pack_mapping.family_mappings[{index}]"),
                "family mapping does not use the known Phase G candidate label",
            ));
        }
    }

    for (index, mutation) in plan.pack_mapping.mutation_mappings.iter().enumerate() {
        if candidate_mutation_label(mutation.source_mutation_class)
            != Some(mutation.candidate_negative_test_label.as_str())
        {
            errors.push(error(
                format!("plan.pack_mapping.mutation_mappings[{index}]"),
                "mutation mapping does not use the known Phase G candidate label",
            ));
        }
    }

    for (index, trace) in plan.pack_mapping.trace_mappings.iter().enumerate() {
        if !trace.local_only {
            errors.push(error(
                format!("plan.pack_mapping.trace_mappings[{index}].local_only"),
                "trace mapping must remain local-only",
            ));
        }
    }

    match serde_json::to_string(plan) {
        Ok(plan_text) => {
            if plan_text.contains("benchmark pass") {
                errors.push(error(
                    "plan",
                    "dry-run plan must not contain benchmark pass language",
                ));
            }
            if plan_text.contains("official benchmark evidence") {
                errors.push(error(
                    "plan",
                    "dry-run plan must not contain official benchmark evidence language",
                ));
            }
        }
        Err(error_value) => errors.push(error(
            "plan",
            format!("dry-run plan serialization failed during validation: {error_value}"),
        )),
    }

    ZkHarnessDryRunValidation {
        valid: errors.is_empty(),
        errors,
        warnings,
    }
}

fn validate_command(
    command: &ZkHarnessPlannedCommand,
    path: &str,
    errors: &mut Vec<ZkHarnessDryRunValidationIssue>,
) {
    if !command.inert {
        errors.push(error(path, "planned command is not marked inert"));
    }
    validate_relative_text(
        &command.display_program_name,
        &format!("{path}.display_program_name"),
        errors,
    );
    validate_relative_text(
        &command.working_directory_policy,
        &format!("{path}.working_directory_policy"),
        errors,
    );
    if command.display_program_name.contains("sh") || command.display_program_name.contains("bash")
    {
        errors.push(error(
            format!("{path}.display_program_name"),
            "planned command display name looks shell-like",
        ));
    }
    for (index, argument) in command.arguments.iter().enumerate() {
        if !argument.inert {
            errors.push(error(
                format!("{path}.arguments[{index}].inert"),
                "planned command argument is not inert",
            ));
        }
        validate_relative_text(
            &argument.value,
            &format!("{path}.arguments[{index}].value"),
            errors,
        );
    }
    for (index, environment) in command.environment.iter().enumerate() {
        if !environment.inert {
            errors.push(error(
                format!("{path}.environment[{index}].inert"),
                "planned command environment value is not inert",
            ));
        }
        validate_relative_text(
            &environment.value,
            &format!("{path}.environment[{index}].value"),
            errors,
        );
    }
    for (index, artifact) in command.input_artifacts.iter().enumerate() {
        validate_relative_text(
            &artifact.relative_uri,
            &format!("{path}.input_artifacts[{index}].relative_uri"),
            errors,
        );
    }
}

fn require_non_empty(
    value: &str,
    path: &str,
    message: &str,
    errors: &mut Vec<ZkHarnessDryRunValidationIssue>,
) {
    if value.is_empty() {
        errors.push(error(path, message));
    }
}

fn validate_relative_text(
    value: &str,
    path: &str,
    errors: &mut Vec<ZkHarnessDryRunValidationIssue>,
) {
    if value.starts_with('/') || value.contains("..") || value.contains('\\') {
        errors.push(error(path, "absolute or parent-traversing path-like value"));
    }
    if contains_shell_metacharacter(value) {
        errors.push(error(path, "shell metacharacter payload is not allowed"));
    }
}

fn contains_shell_metacharacter(value: &str) -> bool {
    value
        .chars()
        .any(|ch| matches!(ch, ';' | '|' | '&' | '>' | '<' | '`' | '$' | '\n' | '\r'))
}

fn error(path: impl Into<String>, message: impl Into<String>) -> ZkHarnessDryRunValidationIssue {
    ZkHarnessDryRunValidationIssue {
        path: path.into(),
        message: message.into(),
        severity: ZkHarnessDryRunValidationIssueSeverity::Error,
    }
}

fn warning(path: impl Into<String>, message: impl Into<String>) -> ZkHarnessDryRunValidationIssue {
    ZkHarnessDryRunValidationIssue {
        path: path.into(),
        message: message.into(),
        severity: ZkHarnessDryRunValidationIssueSeverity::Warning,
    }
}
