//! Phase M inert recursion-envelope contract types.
//!
//! These types model recursion envelopes as local metadata only. They do not
//! execute gnark, do not verify proofs, do not create benchmark outputs, and do
//! not raise claim boundaries.

use serde::{Deserialize, Serialize};

use crate::error::{Result, ZkBenchError};
use crate::evidence::{
    compute_artifact_digest, ArtifactDigest, ArtifactDigestAlgorithm, ArtifactKind, ArtifactRole,
    ClaimBoundary, EvidenceClass,
};
use crate::external_runner::{
    build_default_artifact_capture_contract, build_default_external_result_import_schema,
    build_default_provenance_contract, valid_manual_handoff_step_validation,
    validate_manual_handoff_bundle, ExternalRunnerPolicy, ManualHandoffBundle,
    ManualHandoffBundleVersion, ManualHandoffExport, ManualHandoffInstruction, ManualHandoffStep,
    ManualHandoffStepKind, ManualHandoffSubject, ManualHandoffValidation,
    ManualHandoffValidationIssue,
};

/// Phase M recursion-envelope schema version.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct RecursionEnvelopeVersion {
    /// Logical version string.
    pub value: String,
}

impl Default for RecursionEnvelopeVersion {
    fn default() -> Self {
        Self {
            value: "phase-m-recursion-envelope-v0".to_string(),
        }
    }
}

/// Local recursion-envelope input kind.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
pub enum RecursionEnvelopeInputKind {
    /// Local replay manifest metadata.
    LocalReplayManifest,
    /// Local replay result metadata.
    LocalReplayResult,
    /// Benchmark pack manifest metadata.
    BenchmarkPackManifest,
    /// Artifact digest set metadata.
    ArtifactDigestSet,
    /// Evidence-record candidate metadata.
    EvidenceRecordCandidate,
    /// Evidence append preview metadata.
    EvidenceAppendPreview,
    /// Local soak health report metadata.
    LocalHealthReport,
    /// Level2 eligibility report metadata.
    Level2EligibilityReport,
    /// Other local metadata.
    OtherLocalMetadata,
}

/// Recursion-envelope input reference.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct RecursionEnvelopeInputRef {
    /// Logical input id.
    pub input_id: String,
    /// Portable artifact URI or logical artifact id.
    pub artifact_uri: String,
    /// Input kind.
    pub kind: RecursionEnvelopeInputKind,
    /// Stable input digest.
    pub digest: ArtifactDigest,
    /// Input evidence class.
    pub evidence_class: EvidenceClass,
    /// Input claim boundary.
    pub claim_boundary: ClaimBoundary,
    /// Notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

/// Recursion-envelope metric kind.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
pub enum RecursionEnvelopeMetricKind {
    /// Recursion depth.
    RecursionDepth,
    /// Aggregation width.
    AggregationWidth,
    /// Digest chain length.
    EnvelopeDigestChainLength,
    /// Input count.
    EnvelopeInputCount,
    /// Verification status metric.
    EnvelopeVerificationStatus,
    /// Future proof-size metric.
    RecursionProofSizeBytes,
    /// Future verifier timing metric.
    RecursionVerifierTimeMs,
    /// Future prover timing metric.
    RecursionProverTimeMs,
    /// Future memory metric.
    RecursionMemoryBytes,
}

impl RecursionEnvelopeMetricKind {
    /// Whether this metric requires a future executable adapter phase.
    pub fn requires_executable_adapter(self) -> bool {
        matches!(
            self,
            Self::EnvelopeVerificationStatus
                | Self::RecursionProofSizeBytes
                | Self::RecursionVerifierTimeMs
                | Self::RecursionProverTimeMs
                | Self::RecursionMemoryBytes
        )
    }
}

/// Recursion-envelope metric metadata.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct RecursionEnvelopeMetric {
    /// Metric kind.
    pub kind: RecursionEnvelopeMetricKind,
    /// Integer value, if populated by an authorized phase.
    #[serde(default)]
    pub value: Option<u64>,
    /// Claim boundary for the metric.
    pub claim_boundary: ClaimBoundary,
    /// Notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

/// Future verifier acceptance status metadata.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum RecursionVerifierAcceptanceStatus {
    /// Verifier accepted.
    Accepted,
    /// Verifier rejected.
    Rejected,
    /// Verifier errored.
    Error,
    /// Verifier timed out.
    Timeout,
    /// Result was inconclusive.
    Inconclusive,
}

/// Inert recursion-envelope candidate.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct RecursionEnvelopeCandidate {
    /// Envelope id.
    pub envelope_id: String,
    /// Schema version.
    pub version: RecursionEnvelopeVersion,
    /// Source inputs.
    pub inputs: Vec<RecursionEnvelopeInputRef>,
    /// Declared recursion depth.
    pub recursion_depth: u32,
    /// Declared aggregation width.
    pub aggregation_width: usize,
    /// Digest-chain root over input refs.
    pub digest_chain_root: ArtifactDigest,
    /// Future verifier acceptance status.
    #[serde(default)]
    pub verifier_acceptance_status: Option<RecursionVerifierAcceptanceStatus>,
    /// Whether a future executable adapter phase authorized executable metrics.
    #[serde(default)]
    pub executable_adapter_authorized: bool,
    /// Candidate metrics.
    #[serde(default)]
    pub metrics: Vec<RecursionEnvelopeMetric>,
    /// Output claim boundary.
    pub output_claim_boundary: ClaimBoundary,
    /// Explicit limitations.
    #[serde(default)]
    pub limitations: Vec<String>,
    /// Notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

/// Recursion-envelope validation issue kind.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum RecursionEnvelopeValidationIssueKind {
    /// Required identity field is empty.
    EmptyIdentity,
    /// Candidate has no inputs.
    MissingInputs,
    /// Digest is missing, unsupported, or malformed.
    InvalidDigest,
    /// Digest-chain root does not match inputs.
    DigestChainRootMismatch,
    /// Output claim boundary exceeds input or phase boundary.
    ClaimBoundaryEscalation,
    /// Future executable status was populated without authorization.
    UnauthorizedVerifierStatus,
    /// Future executable metric was populated without authorization.
    UnauthorizedExecutableMetric,
    /// Append preview was treated above Level0 metadata.
    AppendPreviewBoundary,
    /// Level2 eligibility report was treated as Level2 evidence.
    Level2EligibilityBoundary,
    /// Required limitation text is missing.
    MissingLimitation,
}

/// Recursion-envelope validation issue.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct RecursionEnvelopeValidationIssue {
    /// Issue kind.
    pub kind: RecursionEnvelopeValidationIssueKind,
    /// Path.
    pub path: String,
    /// Message.
    pub message: String,
}

/// Recursion-envelope validation report.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct RecursionEnvelopeValidation {
    /// Whether validation passed.
    pub valid: bool,
    /// Issues.
    #[serde(default)]
    pub issues: Vec<RecursionEnvelopeValidationIssue>,
    /// Claim boundary of the validation report.
    pub claim_boundary: ClaimBoundary,
}

/// Future recursion-adapter target metadata.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum RecursionAdapterPreparationTarget {
    /// Future gnark Groth16 recursion adapter metadata.
    GnarkGroth16,
    /// Future gnark Plonk recursion adapter metadata.
    GnarkPlonk,
    /// Other future recursion adapter metadata.
    OtherFutureAdapter,
}

/// Adapter-preparation artifact role.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum RecursionAdapterPreparationArtifactRole {
    /// Input manifest metadata.
    InputManifest,
    /// Circuit descriptor metadata.
    CircuitDescriptor,
    /// Witness-shape metadata.
    WitnessShape,
    /// Evidence mapping metadata.
    EvidenceMapping,
    /// Output envelope candidate metadata.
    OutputEnvelopeCandidate,
    /// Other local metadata.
    OtherLocalMetadata,
}

/// Inert expected artifact metadata for future recursion-adapter work.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct RecursionAdapterPreparationArtifact {
    /// Logical artifact id.
    pub artifact_id: String,
    /// Portable relative artifact URI or logical artifact id.
    pub artifact_uri: String,
    /// Artifact role.
    pub role: RecursionAdapterPreparationArtifactRole,
    /// Whether the future adapter would require this artifact.
    pub required: bool,
    /// Notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

/// Inert future adapter-preparation plan.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct RecursionAdapterPreparationPlan {
    /// Plan id.
    pub plan_id: String,
    /// Schema version.
    pub version: RecursionEnvelopeVersion,
    /// Future adapter target.
    pub target: RecursionAdapterPreparationTarget,
    /// Source inputs the future adapter would bind.
    #[serde(default)]
    pub source_inputs: Vec<RecursionEnvelopeInputRef>,
    /// Expected local metadata artifacts.
    #[serde(default)]
    pub expected_artifacts: Vec<RecursionAdapterPreparationArtifact>,
    /// Whether executable adapter work is authorized.
    #[serde(default)]
    pub executable_adapter_authorized: bool,
    /// Executable steps are forbidden in Phase M preparation metadata.
    #[serde(default)]
    pub executable_steps: Vec<String>,
    /// Claim boundary for this preparation metadata.
    pub claim_boundary: ClaimBoundary,
    /// Explicit limitations.
    #[serde(default)]
    pub limitations: Vec<String>,
    /// Notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

/// Adapter-preparation validation issue kind.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum RecursionAdapterPreparationIssueKind {
    /// Required identity field is empty.
    EmptyIdentity,
    /// Source inputs are missing.
    MissingInputs,
    /// Expected artifacts are missing.
    MissingExpectedArtifacts,
    /// Artifact reference is not portable relative metadata.
    InvalidArtifactRef,
    /// Preparation metadata elevated its claim boundary.
    ClaimBoundaryEscalation,
    /// Executable adapter authorization was enabled.
    ExecutableAdapterAuthorized,
    /// Executable step metadata was populated.
    ExecutableStepPresent,
    /// Required limitation text is missing.
    MissingLimitation,
    /// Nested recursion-envelope input metadata is invalid.
    InvalidInput,
}

/// Adapter-preparation validation issue.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct RecursionAdapterPreparationIssue {
    /// Issue kind.
    pub kind: RecursionAdapterPreparationIssueKind,
    /// Path.
    pub path: String,
    /// Message.
    pub message: String,
}

/// Adapter-preparation validation report.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct RecursionAdapterPreparationValidation {
    /// Whether validation passed.
    pub valid: bool,
    /// Issues.
    #[serde(default)]
    pub issues: Vec<RecursionAdapterPreparationIssue>,
    /// Claim boundary of the validation report.
    pub claim_boundary: ClaimBoundary,
}

/// Mapping from adapter-preparation metadata to manual handoff instructions.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct RecursionAdapterManualHandoffMapping {
    /// Source adapter-preparation plan id.
    pub preparation_plan_id: String,
    /// Source input ids.
    #[serde(default)]
    pub source_input_ids: Vec<String>,
    /// Expected artifact ids.
    #[serde(default)]
    pub expected_artifact_ids: Vec<String>,
    /// Manual instruction ids.
    #[serde(default)]
    pub manual_instruction_ids: Vec<String>,
    /// Claim boundary.
    pub claim_boundary: ClaimBoundary,
    /// Notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

/// Phase M manual handoff wrapper for future recursion-adapter review.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct RecursionAdapterManualHandoffBundle {
    /// Handoff mapping.
    pub mapping: RecursionAdapterManualHandoffMapping,
    /// Generic manual handoff bundle.
    pub handoff_bundle: ManualHandoffBundle,
    /// Whether this bundle emits a recursion adapter result.
    pub emits_recursion_adapter_result: bool,
    /// Claim boundary.
    pub claim_boundary: ClaimBoundary,
    /// Notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

/// Compute the deterministic digest-chain root for recursion-envelope inputs.
pub fn compute_recursion_envelope_digest_chain_root(
    inputs: &[RecursionEnvelopeInputRef],
) -> Result<ArtifactDigest> {
    compute_artifact_digest(
        &inputs,
        Some(ArtifactKind::Other),
        Some(ArtifactRole::Digest),
    )
}

/// Validate an inert recursion-envelope candidate.
pub fn validate_recursion_envelope_candidate(
    candidate: &RecursionEnvelopeCandidate,
) -> RecursionEnvelopeValidation {
    let mut issues = Vec::new();

    if candidate.envelope_id.trim().is_empty() {
        push_issue(
            &mut issues,
            RecursionEnvelopeValidationIssueKind::EmptyIdentity,
            "envelope_id",
            "envelope id must not be empty",
        );
    }
    if candidate.version.value.trim().is_empty() {
        push_issue(
            &mut issues,
            RecursionEnvelopeValidationIssueKind::EmptyIdentity,
            "version.value",
            "version value must not be empty",
        );
    }
    if candidate.inputs.is_empty() {
        push_issue(
            &mut issues,
            RecursionEnvelopeValidationIssueKind::MissingInputs,
            "inputs",
            "recursion envelope must contain at least one input",
        );
    }

    for (index, input) in candidate.inputs.iter().enumerate() {
        let path = format!("inputs[{index}]");
        if input.input_id.trim().is_empty() {
            push_issue(
                &mut issues,
                RecursionEnvelopeValidationIssueKind::EmptyIdentity,
                format!("{path}.input_id"),
                "input id must not be empty",
            );
        }
        if input.artifact_uri.trim().is_empty() {
            push_issue(
                &mut issues,
                RecursionEnvelopeValidationIssueKind::EmptyIdentity,
                format!("{path}.artifact_uri"),
                "artifact uri must not be empty",
            );
        }
        validate_digest(&mut issues, format!("{path}.digest"), &input.digest);
        if input.kind == RecursionEnvelopeInputKind::EvidenceAppendPreview
            && input.claim_boundary != ClaimBoundary::Level0DesignNote
        {
            push_issue(
                &mut issues,
                RecursionEnvelopeValidationIssueKind::AppendPreviewBoundary,
                format!("{path}.claim_boundary"),
                "append previews are metadata only and must remain Level0DesignNote",
            );
        }
        if input.kind == RecursionEnvelopeInputKind::Level2EligibilityReport
            && input.claim_boundary != ClaimBoundary::Level0DesignNote
        {
            push_issue(
                &mut issues,
                RecursionEnvelopeValidationIssueKind::Level2EligibilityBoundary,
                format!("{path}.claim_boundary"),
                "Level2 eligibility reports are not Level2 evidence",
            );
        }
    }

    validate_digest(
        &mut issues,
        "digest_chain_root",
        &candidate.digest_chain_root,
    );
    if let Ok(expected) = compute_recursion_envelope_digest_chain_root(&candidate.inputs) {
        if expected != candidate.digest_chain_root {
            push_issue(
                &mut issues,
                RecursionEnvelopeValidationIssueKind::DigestChainRootMismatch,
                "digest_chain_root",
                "digest-chain root must match recursion envelope inputs",
            );
        }
    }

    if let Some(weakest_input) = candidate
        .inputs
        .iter()
        .map(|input| input.claim_boundary)
        .min()
    {
        if candidate.output_claim_boundary > weakest_input {
            push_issue(
                &mut issues,
                RecursionEnvelopeValidationIssueKind::ClaimBoundaryEscalation,
                "output_claim_boundary",
                "output claim boundary must not exceed weakest input boundary",
            );
        }
    }
    if candidate.output_claim_boundary > ClaimBoundary::Level1LocalReplay {
        push_issue(
            &mut issues,
            RecursionEnvelopeValidationIssueKind::ClaimBoundaryEscalation,
            "output_claim_boundary",
            "Phase M inert contracts cannot create Level2+ evidence",
        );
    }

    if candidate.verifier_acceptance_status.is_some() && !candidate.executable_adapter_authorized {
        push_issue(
            &mut issues,
            RecursionEnvelopeValidationIssueKind::UnauthorizedVerifierStatus,
            "verifier_acceptance_status",
            "verifier acceptance status requires a future executable adapter phase",
        );
    }

    for (index, metric) in candidate.metrics.iter().enumerate() {
        if metric.kind.requires_executable_adapter() && !candidate.executable_adapter_authorized {
            push_issue(
                &mut issues,
                RecursionEnvelopeValidationIssueKind::UnauthorizedExecutableMetric,
                format!("metrics[{index}].kind"),
                "metric requires a future executable adapter phase",
            );
        }
        if metric.claim_boundary > candidate.output_claim_boundary {
            push_issue(
                &mut issues,
                RecursionEnvelopeValidationIssueKind::ClaimBoundaryEscalation,
                format!("metrics[{index}].claim_boundary"),
                "metric claim boundary must not exceed envelope output boundary",
            );
        }
    }

    if !candidate.limitations.iter().any(|limitation| {
        limitation
            .to_ascii_lowercase()
            .contains("recursion proof is not semantic proof")
    }) {
        push_issue(
            &mut issues,
            RecursionEnvelopeValidationIssueKind::MissingLimitation,
            "limitations",
            "limitations must state that recursion proof is not semantic proof",
        );
    }

    RecursionEnvelopeValidation {
        valid: issues.is_empty(),
        issues,
        claim_boundary: ClaimBoundary::Level0DesignNote,
    }
}

/// Validate inert future recursion-adapter preparation metadata.
pub fn validate_recursion_adapter_preparation_plan(
    plan: &RecursionAdapterPreparationPlan,
) -> RecursionAdapterPreparationValidation {
    let mut issues = Vec::new();

    if plan.plan_id.trim().is_empty() {
        push_preparation_issue(
            &mut issues,
            RecursionAdapterPreparationIssueKind::EmptyIdentity,
            "plan_id",
            "plan id must not be empty",
        );
    }
    if plan.version.value.trim().is_empty() {
        push_preparation_issue(
            &mut issues,
            RecursionAdapterPreparationIssueKind::EmptyIdentity,
            "version.value",
            "version value must not be empty",
        );
    }
    if plan.source_inputs.is_empty() {
        push_preparation_issue(
            &mut issues,
            RecursionAdapterPreparationIssueKind::MissingInputs,
            "source_inputs",
            "adapter-preparation metadata must bind at least one source input",
        );
    }
    if plan.expected_artifacts.is_empty() {
        push_preparation_issue(
            &mut issues,
            RecursionAdapterPreparationIssueKind::MissingExpectedArtifacts,
            "expected_artifacts",
            "adapter-preparation metadata must declare expected local artifacts",
        );
    }

    for (index, input) in plan.source_inputs.iter().enumerate() {
        let path = format!("source_inputs[{index}]");
        if input.input_id.trim().is_empty() {
            push_preparation_issue(
                &mut issues,
                RecursionAdapterPreparationIssueKind::EmptyIdentity,
                format!("{path}.input_id"),
                "input id must not be empty",
            );
        }
        if !is_portable_relative_artifact_ref(&input.artifact_uri) {
            push_preparation_issue(
                &mut issues,
                RecursionAdapterPreparationIssueKind::InvalidArtifactRef,
                format!("{path}.artifact_uri"),
                "source input artifact URI must be portable relative metadata",
            );
        }
        let mut input_digest_issues = Vec::new();
        validate_digest(
            &mut input_digest_issues,
            format!("{path}.digest"),
            &input.digest,
        );
        if !input_digest_issues.is_empty() {
            for issue in input_digest_issues {
                push_preparation_issue(
                    &mut issues,
                    RecursionAdapterPreparationIssueKind::InvalidInput,
                    issue.path,
                    issue.message,
                );
            }
        }
        if input.kind == RecursionEnvelopeInputKind::EvidenceAppendPreview
            && input.claim_boundary != ClaimBoundary::Level0DesignNote
        {
            push_preparation_issue(
                &mut issues,
                RecursionAdapterPreparationIssueKind::InvalidInput,
                format!("{path}.claim_boundary"),
                "append previews are metadata only and must remain Level0DesignNote",
            );
        }
        if input.kind == RecursionEnvelopeInputKind::Level2EligibilityReport
            && input.claim_boundary != ClaimBoundary::Level0DesignNote
        {
            push_preparation_issue(
                &mut issues,
                RecursionAdapterPreparationIssueKind::InvalidInput,
                format!("{path}.claim_boundary"),
                "Level2 eligibility reports are not Level2 evidence",
            );
        }
    }

    for (index, artifact) in plan.expected_artifacts.iter().enumerate() {
        let path = format!("expected_artifacts[{index}]");
        if artifact.artifact_id.trim().is_empty() {
            push_preparation_issue(
                &mut issues,
                RecursionAdapterPreparationIssueKind::EmptyIdentity,
                format!("{path}.artifact_id"),
                "expected artifact id must not be empty",
            );
        }
        if !is_portable_relative_artifact_ref(&artifact.artifact_uri) {
            push_preparation_issue(
                &mut issues,
                RecursionAdapterPreparationIssueKind::InvalidArtifactRef,
                format!("{path}.artifact_uri"),
                "expected artifact URI must be portable relative metadata",
            );
        }
    }

    if plan.claim_boundary != ClaimBoundary::Level0DesignNote {
        push_preparation_issue(
            &mut issues,
            RecursionAdapterPreparationIssueKind::ClaimBoundaryEscalation,
            "claim_boundary",
            "Phase M adapter-preparation metadata remains Level0DesignNote",
        );
    }
    if plan.executable_adapter_authorized {
        push_preparation_issue(
            &mut issues,
            RecursionAdapterPreparationIssueKind::ExecutableAdapterAuthorized,
            "executable_adapter_authorized",
            "executable adapter authorization requires a future explicit phase",
        );
    }
    if !plan.executable_steps.is_empty() {
        push_preparation_issue(
            &mut issues,
            RecursionAdapterPreparationIssueKind::ExecutableStepPresent,
            "executable_steps",
            "Phase M adapter-preparation metadata must not contain executable steps",
        );
    }
    if !plan.limitations.iter().any(|limitation| {
        limitation
            .to_ascii_lowercase()
            .contains("recursion proof is not semantic proof")
    }) {
        push_preparation_issue(
            &mut issues,
            RecursionAdapterPreparationIssueKind::MissingLimitation,
            "limitations",
            "limitations must state that recursion proof is not semantic proof",
        );
    }

    RecursionAdapterPreparationValidation {
        valid: issues.is_empty(),
        issues,
        claim_boundary: ClaimBoundary::Level0DesignNote,
    }
}

/// Build a manual handoff bundle from inert recursion-adapter preparation metadata.
pub fn build_recursion_adapter_manual_handoff_bundle(
    plan: &RecursionAdapterPreparationPlan,
) -> Result<RecursionAdapterManualHandoffBundle> {
    let preparation_validation = validate_recursion_adapter_preparation_plan(plan);
    if !preparation_validation.valid {
        return Err(ZkBenchError::validation(
            "recursion_adapter_preparation_plan",
            format!(
                "recursion adapter preparation plan is invalid: {:?}",
                preparation_validation.issues
            ),
        ));
    }

    let preparation_digest =
        compute_artifact_digest(plan, Some(ArtifactKind::Other), Some(ArtifactRole::Digest))?;
    let handoff_bundle = ManualHandoffBundle {
        id: format!("recursion_adapter_manual_handoff_{}", plan.plan_id),
        bundle_version: ManualHandoffBundleVersion::default(),
        subject: ManualHandoffSubject {
            dry_run_plan_id: plan.plan_id.clone(),
            source_benchmark_pack_id: format!("recursion_adapter_preparation_{}", plan.plan_id),
            source_pack_digest: preparation_digest,
            source_artifact_digests: plan
                .source_inputs
                .iter()
                .map(|input| input.digest.clone())
                .collect(),
            local_pack_claim_boundary: weakest_or_level0(&plan.source_inputs),
            notes: vec![
                "Source recursion-adapter preparation metadata remains local-only.".to_string(),
            ],
        },
        external_runner_policy: ExternalRunnerPolicy::phase_h_manual_handoff_only(),
        artifact_capture_contract: build_default_artifact_capture_contract(),
        provenance_contract: build_default_provenance_contract(),
        result_import_schema: build_default_external_result_import_schema(),
        steps: recursion_adapter_manual_handoff_steps(plan),
        export: ManualHandoffExport {
            id: format!("recursion_adapter_manual_handoff_export_{}", plan.plan_id),
            format: "json".to_string(),
            relative_uri: format!(
                "handoff/{}_recursion_adapter_manual_handoff.json",
                plan.plan_id
            ),
            claim_boundary: ClaimBoundary::Level0DesignNote,
            notes: vec!["Manual handoff export is inert JSON metadata only.".to_string()],
        },
        claim_boundary: ClaimBoundary::Level0DesignNote,
        notes: vec![
            "Manual handoff bundles are not benchmark results.".to_string(),
            "No recursion adapter result is emitted by this bundle.".to_string(),
            "Recursion proof is not semantic proof.".to_string(),
        ],
    };

    let mapping = RecursionAdapterManualHandoffMapping {
        preparation_plan_id: plan.plan_id.clone(),
        source_input_ids: plan
            .source_inputs
            .iter()
            .map(|input| input.input_id.clone())
            .collect(),
        expected_artifact_ids: plan
            .expected_artifacts
            .iter()
            .map(|artifact| artifact.artifact_id.clone())
            .collect(),
        manual_instruction_ids: handoff_bundle
            .steps
            .iter()
            .map(|step| step.id.clone())
            .collect(),
        claim_boundary: ClaimBoundary::Level0DesignNote,
        notes: vec![
            "Mapping preserves preparation plan id, input ids, and expected artifact ids."
                .to_string(),
        ],
    };

    let bundle = RecursionAdapterManualHandoffBundle {
        mapping,
        handoff_bundle,
        emits_recursion_adapter_result: false,
        claim_boundary: ClaimBoundary::Level0DesignNote,
        notes: vec![
            "Future recursion-adapter review remains manual-only.".to_string(),
            "No official benchmark evidence is created by this handoff bundle.".to_string(),
        ],
    };
    let validation = validate_recursion_adapter_manual_handoff_bundle(&bundle);
    if !validation.valid {
        return Err(ZkBenchError::validation(
            "recursion_adapter_manual_handoff_bundle",
            format!(
                "recursion adapter manual handoff validation failed: {:?}",
                validation.issues
            ),
        ));
    }
    Ok(bundle)
}

/// Validate a Phase M recursion-adapter manual handoff bundle.
pub fn validate_recursion_adapter_manual_handoff_bundle(
    bundle: &RecursionAdapterManualHandoffBundle,
) -> ManualHandoffValidation {
    let mut validation = validate_manual_handoff_bundle(&bundle.handoff_bundle);
    if bundle.claim_boundary != ClaimBoundary::Level0DesignNote {
        validation.issues.push(ManualHandoffValidationIssue::error(
            "recursion_adapter_manual_handoff.claim_boundary",
            "recursion adapter manual handoff bundles must remain Level0DesignNote",
        ));
    }
    if bundle.mapping.claim_boundary != ClaimBoundary::Level0DesignNote {
        validation.issues.push(ManualHandoffValidationIssue::error(
            "recursion_adapter_manual_handoff.mapping.claim_boundary",
            "recursion adapter handoff mapping must remain Level0DesignNote",
        ));
    }
    if bundle.emits_recursion_adapter_result {
        validation.issues.push(ManualHandoffValidationIssue::error(
            "recursion_adapter_manual_handoff.emits_recursion_adapter_result",
            "Phase M manual handoff must not emit recursion adapter results",
        ));
    }
    if bundle.handoff_bundle.allows_live_execution() {
        validation.issues.push(ManualHandoffValidationIssue::error(
            "recursion_adapter_manual_handoff.handoff_bundle.external_runner_policy",
            "Phase M manual handoff must not allow live execution",
        ));
    }
    validation.valid = validation.issues.is_empty();
    validation
}

/// Serialize a recursion-envelope candidate to pretty JSON.
pub fn serialize_recursion_envelope_candidate_json(
    candidate: &RecursionEnvelopeCandidate,
) -> Result<String> {
    serde_json::to_string_pretty(candidate).map_err(|error| {
        ZkBenchError::serialization(
            "serialize_recursion_envelope_candidate_json",
            error.to_string(),
        )
    })
}

/// Deserialize a recursion-envelope candidate from JSON.
pub fn deserialize_recursion_envelope_candidate_json(
    json: &str,
) -> Result<RecursionEnvelopeCandidate> {
    serde_json::from_str(json).map_err(|error| {
        ZkBenchError::deserialization(
            "deserialize_recursion_envelope_candidate_json",
            error.to_string(),
        )
    })
}

/// Serialize adapter-preparation metadata to pretty JSON.
pub fn serialize_recursion_adapter_preparation_plan_json(
    plan: &RecursionAdapterPreparationPlan,
) -> Result<String> {
    serde_json::to_string_pretty(plan).map_err(|error| {
        ZkBenchError::serialization(
            "serialize_recursion_adapter_preparation_plan_json",
            error.to_string(),
        )
    })
}

/// Deserialize adapter-preparation metadata from JSON.
pub fn deserialize_recursion_adapter_preparation_plan_json(
    json: &str,
) -> Result<RecursionAdapterPreparationPlan> {
    serde_json::from_str(json).map_err(|error| {
        ZkBenchError::deserialization(
            "deserialize_recursion_adapter_preparation_plan_json",
            error.to_string(),
        )
    })
}

/// Serialize a recursion-adapter manual handoff bundle to pretty JSON.
pub fn serialize_recursion_adapter_manual_handoff_bundle_json(
    bundle: &RecursionAdapterManualHandoffBundle,
) -> Result<String> {
    serde_json::to_string_pretty(bundle).map_err(|error| {
        ZkBenchError::serialization(
            "serialize_recursion_adapter_manual_handoff_bundle_json",
            error.to_string(),
        )
    })
}

/// Deserialize a recursion-adapter manual handoff bundle from JSON.
pub fn deserialize_recursion_adapter_manual_handoff_bundle_json(
    json: &str,
) -> Result<RecursionAdapterManualHandoffBundle> {
    serde_json::from_str(json).map_err(|error| {
        ZkBenchError::deserialization(
            "deserialize_recursion_adapter_manual_handoff_bundle_json",
            error.to_string(),
        )
    })
}

fn validate_digest(
    issues: &mut Vec<RecursionEnvelopeValidationIssue>,
    path: impl Into<String>,
    digest: &ArtifactDigest,
) {
    let path = path.into();
    if digest.algorithm != ArtifactDigestAlgorithm::Sha256 {
        push_issue(
            issues,
            RecursionEnvelopeValidationIssueKind::InvalidDigest,
            &path,
            "digest algorithm must be Sha256",
        );
    }
    if digest.byte_len == 0 {
        push_issue(
            issues,
            RecursionEnvelopeValidationIssueKind::InvalidDigest,
            &path,
            "digest byte length must be nonzero",
        );
    }
    if !is_lower_hex_digest(&digest.hex_digest) || digest.hex_digest.len() != 64 {
        push_issue(
            issues,
            RecursionEnvelopeValidationIssueKind::InvalidDigest,
            path,
            "digest must be 64 lowercase hexadecimal characters",
        );
    }
}

fn is_lower_hex_digest(value: &str) -> bool {
    value
        .bytes()
        .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte))
}

fn recursion_adapter_manual_handoff_steps(
    plan: &RecursionAdapterPreparationPlan,
) -> Vec<ManualHandoffStep> {
    vec![
        manual_step(
            "review_recursion_adapter_preparation",
            ManualHandoffStepKind::ReviewDryRunPlan,
            "Review recursion adapter preparation",
            "Review the recursion adapter preparation metadata before any external workspace is prepared.",
            Vec::new(),
            None,
            Vec::new(),
        ),
        manual_step(
            "copy_recursion_source_inputs",
            ManualHandoffStepKind::CopyInputArtifacts,
            "Copy recursion source inputs",
            "Copy only the declared recursion source inputs after checking their digests and claim boundaries.",
            plan.source_inputs
                .iter()
                .map(|input| input.artifact_uri.clone())
                .collect(),
            None,
            Vec::new(),
        ),
        manual_step(
            "review_recursion_expected_artifacts",
            ManualHandoffStepKind::CaptureArtifacts,
            "Review expected recursion artifacts",
            "Review expected artifact declarations before any future result import is considered.",
            plan.expected_artifacts
                .iter()
                .map(|artifact| artifact.artifact_uri.clone())
                .collect(),
            None,
            Vec::new(),
        ),
        manual_step(
            "manual_future_recursion_adapter_review",
            ManualHandoffStepKind::RunExternalToolManually,
            "Manual future recursion adapter review",
            "Record future adapter review metadata manually; this instruction is not an executable command.",
            plan.source_inputs
                .iter()
                .map(|input| input.artifact_uri.clone())
                .collect(),
            Some("future_recursion_adapter".to_string()),
            vec![
                "adapter_target".to_string(),
                format!("{:?}", plan.target),
                "preparation_plan".to_string(),
                plan.plan_id.clone(),
            ],
        ),
        manual_step(
            "validate_recursion_result_import_candidate",
            ManualHandoffStepKind::ValidateResultImport,
            "Validate recursion result import candidate",
            "Validate any future result candidate against the import schema before review.",
            Vec::new(),
            None,
            Vec::new(),
        ),
        manual_step(
            "quarantine_recursion_result_candidate",
            ManualHandoffStepKind::QuarantineImportedResults,
            "Quarantine recursion result candidate",
            "Keep any future result candidate quarantined or pending review until explicitly accepted.",
            Vec::new(),
            None,
            Vec::new(),
        ),
        manual_step(
            "review_recursion_claim_boundary",
            ManualHandoffStepKind::ClaimBoundaryReview,
            "Review recursion claim boundary",
            "Keep handoff artifacts at Level0DesignNote and never treat recursion proof as semantic proof.",
            Vec::new(),
            None,
            Vec::new(),
        ),
    ]
}

fn manual_step(
    id: &str,
    kind: ManualHandoffStepKind,
    title: &str,
    detail: &str,
    artifact_refs: Vec<String>,
    inert_planned_program_name: Option<String>,
    inert_arguments: Vec<String>,
) -> ManualHandoffStep {
    ManualHandoffStep {
        id: id.to_string(),
        kind,
        instruction: ManualHandoffInstruction {
            title: title.to_string(),
            detail: detail.to_string(),
            inert_planned_program_name,
            inert_arguments,
            artifact_refs,
            manual_only: true,
            notes: vec!["Manual handoff instruction only.".to_string()],
        },
        validation: valid_manual_handoff_step_validation(),
        notes: vec!["No process is launched by this instruction.".to_string()],
    }
}

fn weakest_or_level0(inputs: &[RecursionEnvelopeInputRef]) -> ClaimBoundary {
    inputs
        .iter()
        .map(|input| input.claim_boundary)
        .min()
        .unwrap_or(ClaimBoundary::Level0DesignNote)
}

fn is_portable_relative_artifact_ref(value: &str) -> bool {
    let value = value.trim();
    !value.is_empty()
        && !value.starts_with('/')
        && !value.starts_with('~')
        && !value.contains('\\')
        && !value.contains("://")
        && !value
            .split('/')
            .any(|component| component.is_empty() || component == "." || component == "..")
}

fn push_issue(
    issues: &mut Vec<RecursionEnvelopeValidationIssue>,
    kind: RecursionEnvelopeValidationIssueKind,
    path: impl Into<String>,
    message: impl Into<String>,
) {
    issues.push(RecursionEnvelopeValidationIssue {
        kind,
        path: path.into(),
        message: message.into(),
    });
}

fn push_preparation_issue(
    issues: &mut Vec<RecursionAdapterPreparationIssue>,
    kind: RecursionAdapterPreparationIssueKind,
    path: impl Into<String>,
    message: impl Into<String>,
) {
    issues.push(RecursionAdapterPreparationIssue {
        kind,
        path: path.into(),
        message: message.into(),
    });
}
