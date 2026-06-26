//! Manual handoff bundle types.
//!
//! Manual handoff bundles are review artifacts only. They are not benchmark
//! results and do not launch external tools.

use serde::{Deserialize, Serialize};

use crate::evidence::{ArtifactDigest, ClaimBoundary};

use super::artifact_capture::{validate_artifact_capture_contract, ArtifactCaptureContract};
use super::policy::{validate_external_runner_policy, ExternalRunnerPolicy};
use super::provenance::{validate_provenance_contract, ProvenanceContract};
use super::result_import::{validate_external_result_import_schema, ExternalResultImportSchema};
use super::validation::{
    contains_rejected_path, contains_shell_payload, phase_h_design_artifact_claim_allowed,
    ExternalValidationIssueSeverity,
};

/// Manual handoff bundle id.
pub type ManualHandoffBundleId = String;

/// Manual handoff bundle version.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ManualHandoffBundleVersion {
    /// Logical version string.
    pub value: String,
}

impl Default for ManualHandoffBundleVersion {
    fn default() -> Self {
        Self {
            value: "phase-h-manual-handoff-bundle-v0".to_string(),
        }
    }
}

/// Subject described by a manual handoff bundle.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ManualHandoffSubject {
    /// Source dry-run plan id.
    pub dry_run_plan_id: String,
    /// Source benchmark pack id.
    pub source_benchmark_pack_id: String,
    /// Source pack manifest digest.
    pub source_pack_digest: ArtifactDigest,
    /// Source artifact digests.
    #[serde(default)]
    pub source_artifact_digests: Vec<ArtifactDigest>,
    /// Claim boundary of the referenced local pack.
    pub local_pack_claim_boundary: ClaimBoundary,
    /// Notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

/// Manual handoff step kind.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
pub enum ManualHandoffStepKind {
    /// Review the dry-run plan.
    ReviewDryRunPlan,
    /// Prepare external workspace manually.
    PrepareExternalWorkspace,
    /// Copy input artifacts manually.
    CopyInputArtifacts,
    /// Run external tool manually in a future reviewed environment.
    RunExternalToolManually,
    /// Capture artifacts.
    CaptureArtifacts,
    /// Record provenance.
    RecordProvenance,
    /// Validate result import.
    ValidateResultImport,
    /// Quarantine imported results.
    QuarantineImportedResults,
    /// Review claim boundary.
    ClaimBoundaryReview,
}

/// Manual handoff instruction.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ManualHandoffInstruction {
    /// Instruction title.
    pub title: String,
    /// Instruction detail.
    pub detail: String,
    /// Planned program label as inert data.
    #[serde(default)]
    pub inert_planned_program_name: Option<String>,
    /// Inert argument data.
    #[serde(default)]
    pub inert_arguments: Vec<String>,
    /// Relative artifact references.
    #[serde(default)]
    pub artifact_refs: Vec<String>,
    /// True when this instruction is manual-only.
    pub manual_only: bool,
    /// Notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

/// Manual handoff validation issue.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ManualHandoffValidationIssue {
    /// Issue path.
    pub path: String,
    /// Issue message.
    pub message: String,
    /// Issue severity.
    pub severity: ExternalValidationIssueSeverity,
}

impl ManualHandoffValidationIssue {
    /// Build an error issue.
    pub fn error(path: impl Into<String>, message: impl Into<String>) -> Self {
        Self {
            path: path.into(),
            message: message.into(),
            severity: ExternalValidationIssueSeverity::Error,
        }
    }
}

/// Validation summary for a manual handoff bundle.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ManualHandoffValidation {
    /// True when there are no validation errors.
    pub valid: bool,
    /// Validation issues.
    pub issues: Vec<ManualHandoffValidationIssue>,
}

/// Manual handoff step.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ManualHandoffStep {
    /// Step id.
    pub id: String,
    /// Step kind.
    pub kind: ManualHandoffStepKind,
    /// Instruction.
    pub instruction: ManualHandoffInstruction,
    /// Local validation summary for this step.
    pub validation: ManualHandoffValidation,
    /// Notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

/// Manual handoff export metadata.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ManualHandoffExport {
    /// Export id.
    pub id: String,
    /// Export format.
    pub format: String,
    /// Relative URI.
    pub relative_uri: String,
    /// Claim boundary.
    pub claim_boundary: ClaimBoundary,
    /// Notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

/// Manual handoff bundle.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ManualHandoffBundle {
    /// Bundle id.
    pub id: ManualHandoffBundleId,
    /// Bundle version.
    pub bundle_version: ManualHandoffBundleVersion,
    /// Subject.
    pub subject: ManualHandoffSubject,
    /// External-runner policy.
    pub external_runner_policy: ExternalRunnerPolicy,
    /// Artifact capture contract.
    pub artifact_capture_contract: ArtifactCaptureContract,
    /// Provenance contract.
    pub provenance_contract: ProvenanceContract,
    /// Result import schema.
    pub result_import_schema: ExternalResultImportSchema,
    /// Manual handoff steps.
    pub steps: Vec<ManualHandoffStep>,
    /// Export metadata.
    pub export: ManualHandoffExport,
    /// Claim boundary for this bundle artifact.
    pub claim_boundary: ClaimBoundary,
    /// Notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

impl ManualHandoffBundle {
    /// Return true if this bundle's policy allows live execution.
    pub fn allows_live_execution(&self) -> bool {
        self.external_runner_policy.allows_live_execution()
    }

    /// Return true when every instruction is manual-only.
    pub fn contains_manual_instructions_only(&self) -> bool {
        self.steps
            .iter()
            .all(|step| step.instruction.manual_only && step.validation.valid)
    }
}

/// Validate a manual handoff bundle.
pub fn validate_manual_handoff_bundle(bundle: &ManualHandoffBundle) -> ManualHandoffValidation {
    let mut issues = Vec::new();
    if bundle.id.trim().is_empty() {
        issues.push(ManualHandoffValidationIssue::error(
            "bundle.id",
            "manual handoff bundle id is empty",
        ));
    }
    if !phase_h_design_artifact_claim_allowed(bundle.claim_boundary) {
        issues.push(ManualHandoffValidationIssue::error(
            "bundle.claim_boundary",
            "manual handoff bundles must remain Level0DesignNote",
        ));
    }
    if !bundle.external_runner_policy.mode.is_phase_h_allowed() {
        issues.push(ManualHandoffValidationIssue::error(
            "bundle.external_runner_policy.mode",
            "manual handoff bundle requested live execution",
        ));
    }
    if bundle.subject.dry_run_plan_id.trim().is_empty() {
        issues.push(ManualHandoffValidationIssue::error(
            "bundle.subject.dry_run_plan_id",
            "dry-run plan id is empty",
        ));
    }
    if bundle.subject.source_benchmark_pack_id.trim().is_empty() {
        issues.push(ManualHandoffValidationIssue::error(
            "bundle.subject.source_benchmark_pack_id",
            "source benchmark pack id is empty",
        ));
    }
    if bundle.subject.local_pack_claim_boundary > ClaimBoundary::Level1LocalReplay {
        issues.push(ManualHandoffValidationIssue::error(
            "bundle.subject.local_pack_claim_boundary",
            "manual handoff cannot elevate local pack evidence above Level1LocalReplay",
        ));
    }
    for issue in validate_external_runner_policy(&bundle.external_runner_policy) {
        issues.push(ManualHandoffValidationIssue::error(
            format!("bundle.external_runner_policy.{}", issue.path),
            issue.message,
        ));
    }
    let artifact_validation = validate_artifact_capture_contract(&bundle.artifact_capture_contract);
    for issue in artifact_validation.errors {
        issues.push(ManualHandoffValidationIssue::error(
            format!("bundle.artifact_capture_contract.{}", issue.path),
            issue.message,
        ));
    }
    let provenance_validation = validate_provenance_contract(&bundle.provenance_contract);
    for issue in provenance_validation.issues {
        issues.push(ManualHandoffValidationIssue::error(
            format!("bundle.provenance_contract.{}", issue.path),
            issue.message,
        ));
    }
    let schema_validation = validate_external_result_import_schema(&bundle.result_import_schema);
    for issue in schema_validation.issues {
        issues.push(ManualHandoffValidationIssue::error(
            format!("bundle.result_import_schema.{}", issue.path),
            issue.message,
        ));
    }
    if bundle.steps.is_empty() {
        issues.push(ManualHandoffValidationIssue::error(
            "bundle.steps",
            "manual handoff bundle has no steps",
        ));
    }
    for (index, step) in bundle.steps.iter().enumerate() {
        validate_step(step, index, &mut issues);
    }
    validate_export(&bundle.export, &mut issues);
    ManualHandoffValidation {
        valid: issues.is_empty(),
        issues,
    }
}

/// Build a valid step-level validation marker.
pub fn valid_manual_handoff_step_validation() -> ManualHandoffValidation {
    ManualHandoffValidation {
        valid: true,
        issues: Vec::new(),
    }
}

fn validate_step(
    step: &ManualHandoffStep,
    index: usize,
    issues: &mut Vec<ManualHandoffValidationIssue>,
) {
    if step.id.trim().is_empty() {
        issues.push(ManualHandoffValidationIssue::error(
            format!("bundle.steps[{index}].id"),
            "step id is empty",
        ));
    }
    if !step.instruction.manual_only {
        issues.push(ManualHandoffValidationIssue::error(
            format!("bundle.steps[{index}].instruction.manual_only"),
            "manual handoff step is not manual-only",
        ));
    }
    validate_instruction_text(
        &step.instruction.title,
        &format!("bundle.steps[{index}].instruction.title"),
        issues,
    );
    validate_instruction_text(
        &step.instruction.detail,
        &format!("bundle.steps[{index}].instruction.detail"),
        issues,
    );
    if let Some(program) = &step.instruction.inert_planned_program_name {
        validate_instruction_text(
            program,
            &format!("bundle.steps[{index}].instruction.inert_planned_program_name"),
            issues,
        );
    }
    for (argument_index, argument) in step.instruction.inert_arguments.iter().enumerate() {
        validate_instruction_text(
            argument,
            &format!("bundle.steps[{index}].instruction.inert_arguments[{argument_index}]"),
            issues,
        );
    }
    for (artifact_index, artifact_ref) in step.instruction.artifact_refs.iter().enumerate() {
        if contains_rejected_path(artifact_ref) {
            issues.push(ManualHandoffValidationIssue::error(
                format!("bundle.steps[{index}].instruction.artifact_refs[{artifact_index}]"),
                "artifact ref is absolute or contains traversal",
            ));
        }
    }
}

fn validate_instruction_text(
    value: &str,
    path: &str,
    issues: &mut Vec<ManualHandoffValidationIssue>,
) {
    if contains_rejected_path(value) {
        issues.push(ManualHandoffValidationIssue::error(
            path,
            "instruction text contains an absolute path or traversal",
        ));
    }
    if contains_shell_payload(value) {
        issues.push(ManualHandoffValidationIssue::error(
            path,
            "instruction text contains shell-like payload",
        ));
    }
}

fn validate_export(export: &ManualHandoffExport, issues: &mut Vec<ManualHandoffValidationIssue>) {
    if export.id.trim().is_empty() {
        issues.push(ManualHandoffValidationIssue::error(
            "bundle.export.id",
            "manual handoff export id is empty",
        ));
    }
    if contains_rejected_path(&export.relative_uri) {
        issues.push(ManualHandoffValidationIssue::error(
            "bundle.export.relative_uri",
            "manual handoff export URI is absolute or contains traversal",
        ));
    }
    if export.claim_boundary != ClaimBoundary::Level0DesignNote {
        issues.push(ManualHandoffValidationIssue::error(
            "bundle.export.claim_boundary",
            "manual handoff exports must remain Level0DesignNote",
        ));
    }
}
