//! zk-Harness manual handoff mapping.
//!
//! This module converts inert zk-Harness dry-run plans into manual handoff
//! bundles. It never emits a zk-Harness result and does not execute any tool.

use serde::{Deserialize, Serialize};

use crate::error::{Result, ZkBenchError};
use crate::evidence::{ArtifactDigest, ClaimBoundary};
use crate::external_runner::{
    build_default_artifact_capture_contract, build_default_external_result_import_schema,
    build_default_provenance_contract, valid_manual_handoff_step_validation,
    validate_manual_handoff_bundle, ArtifactCaptureContract, ExpectedArtifactFormat,
    ExpectedArtifactRole, ExternalResultImportSchema, ExternalRunnerPolicy, ManualHandoffBundle,
    ManualHandoffBundleVersion, ManualHandoffExport, ManualHandoffInstruction, ManualHandoffStep,
    ManualHandoffStepKind, ManualHandoffSubject,
};

use super::dry_run::{
    ZkHarnessDryRunPlan, ZkHarnessPlanStep, ZkHarnessPlanStepKind, ZkHarnessPlannedCommand,
};

/// zk-Harness artifact expectation for future manual review.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ZkHarnessArtifactExpectation {
    /// Expected artifact id.
    pub id: String,
    /// Expected role.
    pub role: ExpectedArtifactRole,
    /// Expected format.
    pub format: ExpectedArtifactFormat,
    /// Required for future review.
    pub required_for_future_review: bool,
    /// Notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

/// zk-Harness result import expectation.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ZkHarnessResultImportExpectation {
    /// Result import schema id.
    pub import_schema_id: String,
    /// Whether candidates start quarantined.
    pub candidates_start_quarantined: bool,
    /// Whether metric values require source artifact refs.
    pub metric_values_require_source_artifact_refs: bool,
    /// Whether official benchmark claims are rejected.
    pub official_benchmark_claims_rejected: bool,
    /// Notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

/// Future zk-Harness execution prerequisite.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
pub enum ZkHarnessFutureExecutionPrerequisite {
    /// Verify official zk-Harness schema/source.
    VerifyOfficialZkHarnessSchemaSource,
    /// Review dry-run mapping.
    ReviewDryRunMapping,
    /// Review external tool installation process.
    ReviewExternalToolInstallationProcess,
    /// Review sandbox policy.
    ReviewSandboxPolicy,
    /// Review artifact capture contract.
    ReviewArtifactCaptureContract,
    /// Review result import validation.
    ReviewResultImportValidation,
    /// Review claim-boundary policy.
    ReviewClaimBoundaryPolicy,
    /// Run only with explicit future approval.
    RunOnlyWithExplicitFutureApproval,
}

/// Mapping from a zk-Harness dry-run plan to manual handoff metadata.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ZkHarnessManualHandoffMapping {
    /// Source dry-run plan id.
    pub dry_run_plan_id: String,
    /// Source benchmark pack id.
    pub source_benchmark_pack_id: String,
    /// Source pack digest.
    pub source_pack_digest: ArtifactDigest,
    /// Source artifact digests.
    #[serde(default)]
    pub source_artifact_digests: Vec<ArtifactDigest>,
    /// Planned manual instruction ids.
    pub manual_instruction_ids: Vec<String>,
    /// Claim boundary.
    pub claim_boundary: ClaimBoundary,
    /// Notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

/// zk-Harness manual handoff bundle.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ZkHarnessManualHandoffBundle {
    /// Handoff mapping.
    pub mapping: ZkHarnessManualHandoffMapping,
    /// Generic manual handoff bundle.
    pub handoff_bundle: ManualHandoffBundle,
    /// zk-Harness-specific artifact expectations.
    pub artifact_expectations: Vec<ZkHarnessArtifactExpectation>,
    /// Result import expectation.
    pub result_import_expectation: ZkHarnessResultImportExpectation,
    /// Future prerequisites.
    pub future_execution_prerequisites: Vec<ZkHarnessFutureExecutionPrerequisite>,
    /// Whether a zk-Harness result was emitted.
    pub emits_zk_harness_result: bool,
    /// Claim boundary.
    pub claim_boundary: ClaimBoundary,
    /// Notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

/// Build a generic manual handoff bundle from a zk-Harness dry-run plan.
pub fn build_manual_handoff_bundle_from_zk_harness_plan(
    plan: &ZkHarnessDryRunPlan,
) -> Result<ManualHandoffBundle> {
    let subject = ManualHandoffSubject {
        dry_run_plan_id: plan.id.clone(),
        source_benchmark_pack_id: plan.source_benchmark_pack_id.clone(),
        source_pack_digest: plan.source_pack_digest.clone(),
        source_artifact_digests: plan
            .pack_mapping
            .artifact_mappings
            .iter()
            .map(|artifact| artifact.source_digest.clone())
            .collect(),
        local_pack_claim_boundary: plan.subject.local_pack_claim_boundary,
        notes: vec![
            "Source local pack evidence remains local-only and is not elevated.".to_string(),
        ],
    };
    let artifact_capture_contract = build_default_artifact_capture_contract();
    let provenance_contract = build_default_provenance_contract();
    let result_import_schema = build_default_external_result_import_schema();
    let steps = manual_handoff_steps(plan);
    let bundle = ManualHandoffBundle {
        id: format!("manual_handoff_bundle_{}", plan.id),
        bundle_version: ManualHandoffBundleVersion::default(),
        subject,
        external_runner_policy: ExternalRunnerPolicy::phase_h_manual_handoff_only(),
        artifact_capture_contract,
        provenance_contract,
        result_import_schema,
        steps,
        export: ManualHandoffExport {
            id: format!("manual_handoff_export_{}", plan.id),
            format: "json".to_string(),
            relative_uri: format!("handoff/{}_manual_handoff_bundle.json", plan.id),
            claim_boundary: ClaimBoundary::Level0DesignNote,
            notes: vec!["Manual handoff export is inert JSON metadata only.".to_string()],
        },
        claim_boundary: ClaimBoundary::Level0DesignNote,
        notes: vec![
            "Manual handoff bundles are not benchmark results.".to_string(),
            "External execution is disabled by default.".to_string(),
            "zk-Harness dry-run plans are not benchmark results.".to_string(),
        ],
    };
    let validation = validate_manual_handoff_bundle(&bundle);
    if !validation.valid {
        return Err(ZkBenchError::zk_harness(
            "zk_harness.manual_handoff.validation",
            format!("manual handoff validation failed: {:?}", validation.issues),
        ));
    }
    Ok(bundle)
}

/// Build the zk-Harness-specific manual handoff bundle wrapper.
pub fn build_zk_harness_manual_handoff_bundle(
    plan: &ZkHarnessDryRunPlan,
) -> Result<ZkHarnessManualHandoffBundle> {
    let handoff_bundle = build_manual_handoff_bundle_from_zk_harness_plan(plan)?;
    let artifact_expectations = artifact_expectations(&handoff_bundle.artifact_capture_contract);
    let result_import_expectation = result_import_expectation(&handoff_bundle.result_import_schema);
    let mapping = ZkHarnessManualHandoffMapping {
        dry_run_plan_id: plan.id.clone(),
        source_benchmark_pack_id: plan.source_benchmark_pack_id.clone(),
        source_pack_digest: plan.source_pack_digest.clone(),
        source_artifact_digests: plan
            .pack_mapping
            .artifact_mappings
            .iter()
            .map(|artifact| artifact.source_digest.clone())
            .collect(),
        manual_instruction_ids: handoff_bundle
            .steps
            .iter()
            .map(|step| step.id.clone())
            .collect(),
        claim_boundary: ClaimBoundary::Level0DesignNote,
        notes: vec![
            "Mapping preserves dry-run plan id, source pack id, and source digests.".to_string(),
        ],
    };
    Ok(ZkHarnessManualHandoffBundle {
        mapping,
        handoff_bundle,
        artifact_expectations,
        result_import_expectation,
        future_execution_prerequisites: default_zk_harness_future_execution_prerequisites(),
        emits_zk_harness_result: false,
        claim_boundary: ClaimBoundary::Level0DesignNote,
        notes: vec![
            "No zk-Harness result is emitted by this manual handoff bundle.".to_string(),
            "Local replay results are not converted to zk-Harness results.".to_string(),
        ],
    })
}

/// Future execution prerequisites for zk-Harness.
pub fn default_zk_harness_future_execution_prerequisites(
) -> Vec<ZkHarnessFutureExecutionPrerequisite> {
    vec![
        ZkHarnessFutureExecutionPrerequisite::VerifyOfficialZkHarnessSchemaSource,
        ZkHarnessFutureExecutionPrerequisite::ReviewDryRunMapping,
        ZkHarnessFutureExecutionPrerequisite::ReviewExternalToolInstallationProcess,
        ZkHarnessFutureExecutionPrerequisite::ReviewSandboxPolicy,
        ZkHarnessFutureExecutionPrerequisite::ReviewArtifactCaptureContract,
        ZkHarnessFutureExecutionPrerequisite::ReviewResultImportValidation,
        ZkHarnessFutureExecutionPrerequisite::ReviewClaimBoundaryPolicy,
        ZkHarnessFutureExecutionPrerequisite::RunOnlyWithExplicitFutureApproval,
    ]
}

fn manual_handoff_steps(plan: &ZkHarnessDryRunPlan) -> Vec<ManualHandoffStep> {
    let mut steps = vec![
        standard_step(
            "review_dry_run_plan",
            ManualHandoffStepKind::ReviewDryRunPlan,
            "Review dry-run plan",
            "Review the dry-run plan as inert metadata before any external workspace is prepared.",
            Vec::new(),
        ),
        standard_step(
            "prepare_external_workspace",
            ManualHandoffStepKind::PrepareExternalWorkspace,
            "Prepare external workspace manually",
            "Prepare a separate reviewed workspace using relative handoff references only.",
            Vec::new(),
        ),
        standard_step(
            "copy_input_artifacts",
            ManualHandoffStepKind::CopyInputArtifacts,
            "Copy input artifacts manually",
            "Copy local pack inputs manually after checking artifact digests and relative references.",
            plan.pack_mapping
                .artifact_mappings
                .iter()
                .map(|artifact| artifact.source_relative_path.clone())
                .collect(),
        ),
    ];
    for planned_step in &plan.planned_steps {
        steps.push(planned_command_step(planned_step));
    }
    steps.extend([
        standard_step(
            "capture_artifacts",
            ManualHandoffStepKind::CaptureArtifacts,
            "Capture artifacts",
            "Capture only artifacts described by the artifact capture contract.",
            Vec::new(),
        ),
        standard_step(
            "record_provenance",
            ManualHandoffStepKind::RecordProvenance,
            "Record provenance",
            "Record every required provenance field before result import review.",
            Vec::new(),
        ),
        standard_step(
            "validate_result_import",
            ManualHandoffStepKind::ValidateResultImport,
            "Validate result import candidate",
            "Validate any result candidate against the import schema before review.",
            Vec::new(),
        ),
        standard_step(
            "quarantine_imported_results",
            ManualHandoffStepKind::QuarantineImportedResults,
            "Quarantine imported results",
            "Keep imported result candidates quarantined or pending review until future validation.",
            Vec::new(),
        ),
        standard_step(
            "claim_boundary_review",
            ManualHandoffStepKind::ClaimBoundaryReview,
            "Review claim boundary",
            "Keep manual handoff artifacts at Level0DesignNote and local replay references at Level1LocalReplay or lower.",
            Vec::new(),
        ),
    ]);
    steps
}

fn planned_command_step(planned_step: &ZkHarnessPlanStep) -> ManualHandoffStep {
    let command = &planned_step.planned_command;
    ManualHandoffStep {
        id: format!("manual_{}", planned_step.id),
        kind: ManualHandoffStepKind::RunExternalToolManually,
        instruction: ManualHandoffInstruction {
            title: format!("Manual review for planned {:?}", planned_step.kind),
            detail: planned_step_detail(planned_step.kind),
            inert_planned_program_name: Some(command.display_program_name.clone()),
            inert_arguments: inert_arguments(command),
            artifact_refs: command
                .input_artifacts
                .iter()
                .map(|artifact| artifact.relative_uri.clone())
                .collect(),
            manual_only: true,
            notes: vec!["This instruction preserves inert planned command data only.".to_string()],
        },
        validation: valid_manual_handoff_step_validation(),
        notes: vec!["No external process is launched by this instruction.".to_string()],
    }
}

fn standard_step(
    id: &str,
    kind: ManualHandoffStepKind,
    title: &str,
    detail: &str,
    artifact_refs: Vec<String>,
) -> ManualHandoffStep {
    ManualHandoffStep {
        id: id.to_string(),
        kind,
        instruction: ManualHandoffInstruction {
            title: title.to_string(),
            detail: detail.to_string(),
            inert_planned_program_name: None,
            inert_arguments: Vec::new(),
            artifact_refs,
            manual_only: true,
            notes: vec!["Manual handoff instruction only.".to_string()],
        },
        validation: valid_manual_handoff_step_validation(),
        notes: Vec::new(),
    }
}

fn planned_step_detail(kind: ZkHarnessPlanStepKind) -> String {
    match kind {
        ZkHarnessPlanStepKind::PrepareInputs => {
            "Review input preparation data manually; do not treat it as execution.".to_string()
        }
        ZkHarnessPlanStepKind::CompileCircuit => {
            "Review future circuit compilation data manually after source verification.".to_string()
        }
        ZkHarnessPlanStepKind::GenerateWitness => {
            "Review future witness generation data manually after provenance capture.".to_string()
        }
        ZkHarnessPlanStepKind::Prove => {
            "Review future proving data manually; no proof result is created here.".to_string()
        }
        ZkHarnessPlanStepKind::Verify => {
            "Review future verification data manually; no backend acceptance is created here."
                .to_string()
        }
        ZkHarnessPlanStepKind::CollectMetrics => {
            "Review future metric capture data manually; do not populate metric values in Phase H."
                .to_string()
        }
        ZkHarnessPlanStepKind::NormalizeResults => {
            "Review future result normalization data manually and keep candidates quarantined."
                .to_string()
        }
    }
}

fn inert_arguments(command: &ZkHarnessPlannedCommand) -> Vec<String> {
    command
        .arguments
        .iter()
        .map(|argument| format!("{}={}", argument.name, argument.value))
        .collect()
}

fn artifact_expectations(contract: &ArtifactCaptureContract) -> Vec<ZkHarnessArtifactExpectation> {
    contract
        .expected_artifacts
        .iter()
        .map(|artifact| ZkHarnessArtifactExpectation {
            id: artifact.id.clone(),
            role: artifact.role,
            format: artifact.format,
            required_for_future_review: matches!(
                artifact.requirement,
                crate::external_runner::ArtifactCaptureRequirement::Required
            ),
            notes: artifact.notes.clone(),
        })
        .collect()
}

fn result_import_expectation(
    schema: &ExternalResultImportSchema,
) -> ZkHarnessResultImportExpectation {
    ZkHarnessResultImportExpectation {
        import_schema_id: schema.id.clone(),
        candidates_start_quarantined: true,
        metric_values_require_source_artifact_refs: schema
            .import_policy
            .require_metric_source_artifact_refs,
        official_benchmark_claims_rejected: schema.import_policy.reject_official_benchmark_claims,
        notes: vec![
            "zk-Harness handoff mapping produces result import expectations only.".to_string(),
        ],
    }
}
