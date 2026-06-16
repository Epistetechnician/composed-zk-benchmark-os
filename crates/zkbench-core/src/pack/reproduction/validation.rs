//! Validation for reproduction metadata and attachments.

use serde::{Deserialize, Serialize};

use crate::adapters::{
    validate_gnark_recursion_envelope_plan, validate_zk_harness_dry_run_plan,
    validate_zkml_narrow_workload_plan, GnarkRecursionExecutionPolicy, ZkmlNarrowExecutionPolicy,
};
use crate::evidence::ClaimBoundary;

use super::metadata::{
    BenchmarkPackReproductionMetadata, ExternalReplayPlanAttachment, ExternalReplayPlanKind,
};

/// Reproduction validation issue.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct BenchmarkPackReproductionValidationIssue {
    /// Issue path.
    pub path: String,
    /// Issue message.
    pub message: String,
}

/// Reproduction validation result.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct BenchmarkPackReproductionValidation {
    /// True when no issues were found.
    pub valid: bool,
    /// Validation issues.
    pub issues: Vec<BenchmarkPackReproductionValidationIssue>,
}

/// Validate reproduction metadata.
pub fn validate_benchmark_pack_reproduction_metadata(
    metadata: &BenchmarkPackReproductionMetadata,
) -> BenchmarkPackReproductionValidation {
    let mut issues = Vec::new();
    if metadata.id.trim().is_empty() {
        issues.push(issue("metadata.id", "reproduction metadata id is empty"));
    }
    if metadata.source_pack_id.trim().is_empty() {
        issues.push(issue(
            "metadata.source_pack_id",
            "source pack id is empty",
        ));
    }
    if metadata.claim_boundary != ClaimBoundary::Level0DesignNote {
        issues.push(issue(
            "metadata.claim_boundary",
            "reproduction metadata must remain Level0DesignNote in Phase M slice 1",
        ));
    }
    if metadata.level2_eligibility.eligible {
        issues.push(issue(
            "metadata.level2_eligibility.eligible",
            "Phase M slice 1 must not mark Level2 eligibility as true",
        ));
    }
    if !metadata.attachments_are_inert() {
        issues.push(issue(
            "metadata.attachments",
            "all external replay plan attachments must be inert",
        ));
    }
    for (index, attachment) in metadata.attachments.iter().enumerate() {
        validate_attachment(attachment, index, &mut issues);
    }
    BenchmarkPackReproductionValidation {
        valid: issues.is_empty(),
        issues,
    }
}

/// Validate one attachment against execution policy expectations.
pub fn validate_attachment_execution_policy_label(
    attachment: &ExternalReplayPlanAttachment,
) -> bool {
    match attachment.kind {
        ExternalReplayPlanKind::ZkHarnessDryRun => {
            attachment.execution_policy == "Disabled"
                || attachment.execution_policy == "ManualHandoffOnly"
        }
        ExternalReplayPlanKind::GnarkRecursionEnvelope => {
            attachment.execution_policy == "Disabled"
                || attachment.execution_policy == "ManualHandoffOnly"
        }
        ExternalReplayPlanKind::ZkmlNarrowWorkload => {
            attachment.execution_policy == "Disabled"
                || attachment.execution_policy == "ManualHandoffOnly"
        }
    }
}

fn validate_attachment(
    attachment: &ExternalReplayPlanAttachment,
    index: usize,
    issues: &mut Vec<BenchmarkPackReproductionValidationIssue>,
) {
    if attachment.plan_id.trim().is_empty() {
        issues.push(issue(
            format!("metadata.attachments[{index}].plan_id"),
            "plan id is empty",
        ));
    }
    if attachment.relative_path.starts_with('/') || attachment.relative_path.contains("..") {
        issues.push(issue(
            format!("metadata.attachments[{index}].relative_path"),
            "plan path must be relative",
        ));
    }
    if !attachment.inert {
        issues.push(issue(
            format!("metadata.attachments[{index}].inert"),
            "attachment must be inert",
        ));
    }
    if !validate_attachment_execution_policy_label(attachment) {
        issues.push(issue(
            format!("metadata.attachments[{index}].execution_policy"),
            "execution policy must remain disabled or manual-handoff-only",
        ));
    }
}

/// Return true when a serialized plan JSON validates for its attachment kind.
pub fn validate_attached_plan_json(
    kind: ExternalReplayPlanKind,
    json: &str,
) -> std::result::Result<bool, String> {
    match kind {
        ExternalReplayPlanKind::ZkHarnessDryRun => {
            let plan = crate::adapters::deserialize_zk_harness_dry_run_plan_json(json)
                .map_err(|error| error.to_string())?;
            Ok(validate_zk_harness_dry_run_plan(&plan).valid
                && plan.execution_policy.is_phase_g_allowed())
        }
        ExternalReplayPlanKind::GnarkRecursionEnvelope => {
            let plan = crate::adapters::deserialize_gnark_recursion_envelope_plan_json(json)
                .map_err(|error| error.to_string())?;
            Ok(validate_gnark_recursion_envelope_plan(&plan).valid
                && matches!(
                    plan.execution_policy,
                    GnarkRecursionExecutionPolicy::Disabled
                        | GnarkRecursionExecutionPolicy::ManualHandoffOnly
                ))
        }
        ExternalReplayPlanKind::ZkmlNarrowWorkload => {
            let plan = crate::adapters::deserialize_zkml_narrow_workload_plan_json(json)
                .map_err(|error| error.to_string())?;
            Ok(validate_zkml_narrow_workload_plan(&plan).valid
                && matches!(
                    plan.execution_policy,
                    ZkmlNarrowExecutionPolicy::Disabled | ZkmlNarrowExecutionPolicy::ManualHandoffOnly
                ))
        }
    }
}

fn issue(path: impl Into<String>, message: impl Into<String>) -> BenchmarkPackReproductionValidationIssue {
    BenchmarkPackReproductionValidationIssue {
        path: path.into(),
        message: message.into(),
    }
}
