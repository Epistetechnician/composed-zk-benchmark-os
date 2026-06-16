//! Validation for gnark recursion envelope plans.

use serde::{Deserialize, Serialize};

use crate::evidence::ClaimBoundary;

use super::envelope::{
    GnarkRecursionEnvelopePlan, GnarkRecursionExecutionPolicy, GnarkRecursionPlannedCommand,
};

/// Validation issue severity.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum GnarkRecursionEnvelopeValidationIssueSeverity {
    /// Validation error.
    Error,
    /// Validation warning.
    Warning,
}

/// Envelope validation issue.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct GnarkRecursionEnvelopeValidationIssue {
    /// Issue path.
    pub path: String,
    /// Issue message.
    pub message: String,
    /// Issue severity.
    pub severity: GnarkRecursionEnvelopeValidationIssueSeverity,
}

/// Envelope validation result.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct GnarkRecursionEnvelopeValidation {
    /// True when no errors were found.
    pub valid: bool,
    /// Errors.
    pub errors: Vec<GnarkRecursionEnvelopeValidationIssue>,
    /// Warnings.
    pub warnings: Vec<GnarkRecursionEnvelopeValidationIssue>,
}

/// Validate a gnark recursion envelope plan.
pub fn validate_gnark_recursion_envelope_plan(
    plan: &GnarkRecursionEnvelopePlan,
) -> GnarkRecursionEnvelopeValidation {
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
        &plan.scope.machine_id,
        "plan.scope.machine_id",
        "semantic machine id is empty",
        &mut errors,
    );
    require_non_empty(
        &plan.scope.relative_fixture_path,
        "plan.scope.relative_fixture_path",
        "fixture path is empty",
        &mut errors,
    );

    if !plan.execution_policy.is_phase_k_allowed()
        || plan.execution_policy == GnarkRecursionExecutionPolicy::FutureLiveExecution
    {
        errors.push(error(
            "plan.execution_policy",
            "execution policy is not allowed for Phase K envelope planning",
        ));
    }
    if plan.claim_boundary != ClaimBoundary::Level0DesignNote {
        errors.push(error(
            "plan.claim_boundary",
            "gnark recursion envelope plan claim boundary must be Level0DesignNote",
        ));
    }
    if plan.evidence_policy.envelope_plan_claim_boundary != ClaimBoundary::Level0DesignNote {
        errors.push(error(
            "plan.evidence_policy.envelope_plan_claim_boundary",
            "envelope plan evidence policy must remain Level0DesignNote",
        ));
    }
    if plan.evidence_mapping.emits_evidence_records {
        errors.push(error(
            "plan.evidence_mapping.emits_evidence_records",
            "Phase K envelope plans must not emit evidence records",
        ));
    }
    if plan.scope.relative_fixture_path.starts_with('/') {
        errors.push(error(
            "plan.scope.relative_fixture_path",
            "fixture path must be relative",
        ));
    }
    if !plan.contains_no_executable_process() {
        errors.push(error(
            "plan.planned_steps",
            "all planned commands must be inert in Phase K",
        ));
    }
    for (index, step) in plan.planned_steps.iter().enumerate() {
        validate_planned_command(&step.planned_command, index, &mut errors);
    }
    for metric in &plan.metric_schema {
        if metric.contains(':') || metric.contains('=') {
            warnings.push(warning(
                "plan.metric_schema",
                "metric schema entries should remain label-only in Phase K",
            ));
            break;
        }
    }

    GnarkRecursionEnvelopeValidation {
        valid: errors.is_empty(),
        errors,
        warnings,
    }
}

fn validate_planned_command(
    command: &GnarkRecursionPlannedCommand,
    index: usize,
    errors: &mut Vec<GnarkRecursionEnvelopeValidationIssue>,
) {
    if !command.inert {
        errors.push(error(
            format!("plan.planned_steps[{index}].planned_command.inert"),
            "planned command must be inert in Phase K",
        ));
    }
    if command.display_program_name.starts_with('/') {
        errors.push(error(
            format!("plan.planned_steps[{index}].planned_command.display_program_name"),
            "display program name must not be an absolute path",
        ));
    }
    for fragment in [";", "|", "&", "`", "$("] {
        if command.display_program_name.contains(fragment) {
            errors.push(error(
                format!("plan.planned_steps[{index}].planned_command.display_program_name"),
                "display program name must not contain shell fragments",
            ));
        }
    }
}

fn require_non_empty(
    value: &str,
    path: &str,
    message: &str,
    errors: &mut Vec<GnarkRecursionEnvelopeValidationIssue>,
) {
    if value.trim().is_empty() {
        errors.push(error(path, message));
    }
}

fn error(
    path: impl Into<String>,
    message: impl Into<String>,
) -> GnarkRecursionEnvelopeValidationIssue {
    GnarkRecursionEnvelopeValidationIssue {
        path: path.into(),
        message: message.into(),
        severity: GnarkRecursionEnvelopeValidationIssueSeverity::Error,
    }
}

fn warning(
    path: impl Into<String>,
    message: impl Into<String>,
) -> GnarkRecursionEnvelopeValidationIssue {
    GnarkRecursionEnvelopeValidationIssue {
        path: path.into(),
        message: message.into(),
        severity: GnarkRecursionEnvelopeValidationIssueSeverity::Warning,
    }
}
