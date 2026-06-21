//! Phase N inert zkML/control-flow workload manifest types.
//!
//! These types model narrow zkML workload metadata only. They do not execute
//! zkML backends, do not import external results, do not create benchmark
//! outputs, and do not raise claim boundaries.

use serde::{Deserialize, Serialize};

use crate::error::Result;
use crate::evidence::{
    compute_artifact_digest, ArtifactDigest, ArtifactDigestAlgorithm, ArtifactKind, ArtifactRole,
    ClaimBoundary, EvidenceClass,
};

/// Phase N zkML workload manifest schema version.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ZkMlWorkloadManifestVersion {
    /// Logical version string.
    pub value: String,
}

impl Default for ZkMlWorkloadManifestVersion {
    fn default() -> Self {
        Self {
            value: "phase-n-zkml-workload-manifest-v0".to_string(),
        }
    }
}

/// Local zkML workload input kind.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
pub enum ZkMlWorkloadInputKind {
    /// Benchmark family metadata.
    BenchmarkFamilyMetadata,
    /// Local replay manifest metadata.
    LocalReplayManifest,
    /// Local replay result metadata.
    LocalReplayResult,
    /// Benchmark pack manifest metadata.
    BenchmarkPackManifest,
    /// Artifact digest set metadata.
    ArtifactDigestSet,
    /// Public/private boundary fixture metadata.
    PublicPrivateBoundaryFixture,
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

/// zkML workload input reference.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ZkMlWorkloadInputRef {
    /// Logical input id.
    pub input_id: String,
    /// Portable artifact URI or logical artifact id.
    pub artifact_uri: String,
    /// Input kind.
    pub kind: ZkMlWorkloadInputKind,
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

/// Local metadata reference for a model-like artifact.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ZkMlModelArtifactRef {
    /// Logical model artifact id.
    pub artifact_id: String,
    /// Portable artifact URI or logical artifact id.
    pub artifact_uri: String,
    /// Stable artifact digest.
    pub digest: ArtifactDigest,
    /// Claim boundary for the model artifact metadata.
    pub claim_boundary: ClaimBoundary,
    /// Notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

/// zkML workload metric kind.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
pub enum ZkMlMetricKind {
    /// Whether a model artifact digest is present.
    ModelArtifactDigestPresent,
    /// Public input count.
    PublicInputCount,
    /// Private witness count.
    PrivateWitnessCount,
    /// Whether threshold policy metadata is present.
    ThresholdPolicyPresent,
    /// Boundary-check result metadata.
    BoundaryCheckResult,
    /// Observation-omission result metadata.
    ObservationOmissionResult,
    /// Future model accuracy metric, if source declares it.
    ModelAccuracyIfSourceDeclares,
    /// Future constraint-count metric.
    ConstraintCount,
    /// Future proof-size metric.
    ProofSizeBytes,
    /// Future prover timing metric.
    ProverTimeMs,
    /// Future verifier timing metric.
    VerifierTimeMs,
    /// Future memory metric.
    MemoryBytes,
}

impl ZkMlMetricKind {
    /// Whether this metric requires a future executable zkML adapter phase.
    pub fn requires_executable_adapter(self) -> bool {
        matches!(
            self,
            Self::ModelAccuracyIfSourceDeclares
                | Self::ConstraintCount
                | Self::ProofSizeBytes
                | Self::ProverTimeMs
                | Self::VerifierTimeMs
                | Self::MemoryBytes
        )
    }
}

/// zkML workload metric metadata.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ZkMlMetric {
    /// Metric kind.
    pub kind: ZkMlMetricKind,
    /// Integer value, if populated by an authorized metadata-only phase.
    #[serde(default)]
    pub value: Option<u64>,
    /// Claim boundary for the metric.
    pub claim_boundary: ClaimBoundary,
    /// Notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

/// Inert zkML/control-flow workload manifest.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ZkMlWorkloadManifest {
    /// Manifest id.
    pub manifest_id: String,
    /// Schema version.
    pub version: ZkMlWorkloadManifestVersion,
    /// Workload family id.
    pub workload_family_id: String,
    /// Source benchmark instance id.
    pub source_benchmark_instance_id: String,
    /// Control-flow machine id.
    pub control_flow_machine_id: String,
    /// Source inputs.
    #[serde(default)]
    pub inputs: Vec<ZkMlWorkloadInputRef>,
    /// Public input names.
    #[serde(default)]
    pub public_input_names: Vec<String>,
    /// Private witness names.
    #[serde(default)]
    pub private_witness_names: Vec<String>,
    /// Model-like artifact references as local metadata only.
    #[serde(default)]
    pub model_artifacts: Vec<ZkMlModelArtifactRef>,
    /// Threshold or decision policy metadata.
    pub threshold_policy: Option<String>,
    /// Expected verdict mapping metadata.
    pub expected_verdict_mapping: String,
    /// Digest root over source inputs and model artifact metadata.
    pub workload_digest_root: ArtifactDigest,
    /// Whether executable adapter work is authorized.
    #[serde(default)]
    pub executable_adapter_authorized: bool,
    /// Metric metadata.
    #[serde(default)]
    pub metrics: Vec<ZkMlMetric>,
    /// Output claim boundary.
    pub output_claim_boundary: ClaimBoundary,
    /// Explicit limitations.
    #[serde(default)]
    pub limitations: Vec<String>,
    /// Notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

/// zkML workload validation issue kind.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum ZkMlWorkloadValidationIssueKind {
    /// Required identity field is empty.
    EmptyIdentity,
    /// Source inputs are missing.
    MissingInputs,
    /// Public input names are missing.
    MissingPublicInputs,
    /// Private witness names are missing.
    MissingPrivateWitnesses,
    /// Model artifact metadata is missing.
    MissingModelArtifacts,
    /// Threshold policy metadata is missing.
    MissingThresholdPolicy,
    /// Digest is missing, unsupported, or malformed.
    InvalidDigest,
    /// Artifact reference is not portable relative metadata.
    InvalidArtifactRef,
    /// Digest root does not match inputs and model artifacts.
    WorkloadDigestRootMismatch,
    /// Output or metric claim boundary is too high.
    ClaimBoundaryEscalation,
    /// Future executable adapter authorization was enabled.
    ExecutableAdapterAuthorized,
    /// Future executable metric was populated without authorization.
    UnauthorizedExecutableMetric,
    /// Append preview was treated above Level0 metadata.
    AppendPreviewBoundary,
    /// Level2 eligibility report was treated as Level2 evidence.
    Level2EligibilityBoundary,
    /// Model artifact metadata was elevated above Level0.
    ModelArtifactBoundary,
    /// Required limitation text is missing.
    MissingLimitation,
}

/// zkML workload validation issue.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ZkMlWorkloadValidationIssue {
    /// Issue kind.
    pub kind: ZkMlWorkloadValidationIssueKind,
    /// Path.
    pub path: String,
    /// Message.
    pub message: String,
}

/// zkML workload validation report.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ZkMlWorkloadValidation {
    /// Whether validation passed.
    pub valid: bool,
    /// Issues.
    #[serde(default)]
    pub issues: Vec<ZkMlWorkloadValidationIssue>,
    /// Claim boundary of the validation report.
    pub claim_boundary: ClaimBoundary,
}

/// Compute the deterministic digest root for zkML workload metadata.
pub fn compute_zkml_workload_digest_root(
    inputs: &[ZkMlWorkloadInputRef],
    model_artifacts: &[ZkMlModelArtifactRef],
) -> Result<ArtifactDigest> {
    compute_artifact_digest(
        &(inputs, model_artifacts),
        Some(ArtifactKind::Other),
        Some(ArtifactRole::Digest),
    )
}

/// Validate an inert zkML/control-flow workload manifest.
pub fn validate_zkml_workload_manifest(manifest: &ZkMlWorkloadManifest) -> ZkMlWorkloadValidation {
    let mut issues = Vec::new();

    if manifest.manifest_id.trim().is_empty() {
        push_issue(
            &mut issues,
            ZkMlWorkloadValidationIssueKind::EmptyIdentity,
            "manifest_id",
            "manifest id must not be empty",
        );
    }
    if manifest.version.value.trim().is_empty() {
        push_issue(
            &mut issues,
            ZkMlWorkloadValidationIssueKind::EmptyIdentity,
            "version.value",
            "version value must not be empty",
        );
    }
    validate_required_identity(
        &mut issues,
        "workload_family_id",
        &manifest.workload_family_id,
    );
    validate_required_identity(
        &mut issues,
        "source_benchmark_instance_id",
        &manifest.source_benchmark_instance_id,
    );
    validate_required_identity(
        &mut issues,
        "control_flow_machine_id",
        &manifest.control_flow_machine_id,
    );
    validate_required_identity(
        &mut issues,
        "expected_verdict_mapping",
        &manifest.expected_verdict_mapping,
    );

    if manifest.inputs.is_empty() {
        push_issue(
            &mut issues,
            ZkMlWorkloadValidationIssueKind::MissingInputs,
            "inputs",
            "zkML workload manifest must contain at least one input",
        );
    }
    if manifest.public_input_names.is_empty() {
        push_issue(
            &mut issues,
            ZkMlWorkloadValidationIssueKind::MissingPublicInputs,
            "public_input_names",
            "zkML workload manifest must declare public inputs",
        );
    }
    if manifest.private_witness_names.is_empty() {
        push_issue(
            &mut issues,
            ZkMlWorkloadValidationIssueKind::MissingPrivateWitnesses,
            "private_witness_names",
            "zkML workload manifest must declare private witnesses",
        );
    }
    if manifest.model_artifacts.is_empty() {
        push_issue(
            &mut issues,
            ZkMlWorkloadValidationIssueKind::MissingModelArtifacts,
            "model_artifacts",
            "zkML workload manifest must declare model artifact metadata",
        );
    }
    if manifest
        .threshold_policy
        .as_ref()
        .map_or(true, |policy| policy.trim().is_empty())
    {
        push_issue(
            &mut issues,
            ZkMlWorkloadValidationIssueKind::MissingThresholdPolicy,
            "threshold_policy",
            "zkML workload manifest must declare threshold policy metadata",
        );
    }

    for (index, input) in manifest.inputs.iter().enumerate() {
        let path = format!("inputs[{index}]");
        if input.input_id.trim().is_empty() {
            push_issue(
                &mut issues,
                ZkMlWorkloadValidationIssueKind::EmptyIdentity,
                format!("{path}.input_id"),
                "input id must not be empty",
            );
        }
        if !is_portable_relative_artifact_ref(&input.artifact_uri) {
            push_issue(
                &mut issues,
                ZkMlWorkloadValidationIssueKind::InvalidArtifactRef,
                format!("{path}.artifact_uri"),
                "input artifact URI must be portable relative metadata",
            );
        }
        validate_digest(&mut issues, format!("{path}.digest"), &input.digest);
        if input.kind == ZkMlWorkloadInputKind::EvidenceAppendPreview
            && input.claim_boundary != ClaimBoundary::Level0DesignNote
        {
            push_issue(
                &mut issues,
                ZkMlWorkloadValidationIssueKind::AppendPreviewBoundary,
                format!("{path}.claim_boundary"),
                "append previews are metadata only and must remain Level0DesignNote",
            );
        }
        if input.kind == ZkMlWorkloadInputKind::Level2EligibilityReport
            && input.claim_boundary != ClaimBoundary::Level0DesignNote
        {
            push_issue(
                &mut issues,
                ZkMlWorkloadValidationIssueKind::Level2EligibilityBoundary,
                format!("{path}.claim_boundary"),
                "Level2 eligibility reports are not Level2 evidence",
            );
        }
    }

    for (index, artifact) in manifest.model_artifacts.iter().enumerate() {
        let path = format!("model_artifacts[{index}]");
        if artifact.artifact_id.trim().is_empty() {
            push_issue(
                &mut issues,
                ZkMlWorkloadValidationIssueKind::EmptyIdentity,
                format!("{path}.artifact_id"),
                "model artifact id must not be empty",
            );
        }
        if !is_portable_relative_artifact_ref(&artifact.artifact_uri) {
            push_issue(
                &mut issues,
                ZkMlWorkloadValidationIssueKind::InvalidArtifactRef,
                format!("{path}.artifact_uri"),
                "model artifact URI must be portable relative metadata",
            );
        }
        validate_digest(&mut issues, format!("{path}.digest"), &artifact.digest);
        if artifact.claim_boundary != ClaimBoundary::Level0DesignNote {
            push_issue(
                &mut issues,
                ZkMlWorkloadValidationIssueKind::ModelArtifactBoundary,
                format!("{path}.claim_boundary"),
                "model artifact references are local metadata only in Phase N",
            );
        }
    }

    validate_digest(
        &mut issues,
        "workload_digest_root",
        &manifest.workload_digest_root,
    );
    if let Ok(expected) =
        compute_zkml_workload_digest_root(&manifest.inputs, &manifest.model_artifacts)
    {
        if expected != manifest.workload_digest_root {
            push_issue(
                &mut issues,
                ZkMlWorkloadValidationIssueKind::WorkloadDigestRootMismatch,
                "workload_digest_root",
                "workload digest root must match source inputs and model artifacts",
            );
        }
    }

    if manifest.output_claim_boundary != ClaimBoundary::Level0DesignNote {
        push_issue(
            &mut issues,
            ZkMlWorkloadValidationIssueKind::ClaimBoundaryEscalation,
            "output_claim_boundary",
            "Phase N inert workload manifests remain Level0DesignNote",
        );
    }
    if let Some(weakest_input) = manifest
        .inputs
        .iter()
        .map(|input| input.claim_boundary)
        .min()
    {
        if manifest.output_claim_boundary > weakest_input {
            push_issue(
                &mut issues,
                ZkMlWorkloadValidationIssueKind::ClaimBoundaryEscalation,
                "output_claim_boundary",
                "output claim boundary must not exceed weakest input boundary",
            );
        }
    }
    if manifest.executable_adapter_authorized {
        push_issue(
            &mut issues,
            ZkMlWorkloadValidationIssueKind::ExecutableAdapterAuthorized,
            "executable_adapter_authorized",
            "executable zkML adapter authorization requires a future explicit phase",
        );
    }

    for (index, metric) in manifest.metrics.iter().enumerate() {
        if metric.kind.requires_executable_adapter() && metric.value.is_some() {
            push_issue(
                &mut issues,
                ZkMlWorkloadValidationIssueKind::UnauthorizedExecutableMetric,
                format!("metrics[{index}].value"),
                "future zkML execution metrics must not be populated in the inert Phase N slice",
            );
        }
        if metric.claim_boundary > manifest.output_claim_boundary {
            push_issue(
                &mut issues,
                ZkMlWorkloadValidationIssueKind::ClaimBoundaryEscalation,
                format!("metrics[{index}].claim_boundary"),
                "metric claim boundary must not exceed manifest output boundary",
            );
        }
    }

    if !manifest.limitations.iter().any(|limitation| {
        let lower = limitation.to_ascii_lowercase();
        lower.contains("model accuracy") && lower.contains("proof-system correctness")
    }) {
        push_issue(
            &mut issues,
            ZkMlWorkloadValidationIssueKind::MissingLimitation,
            "limitations",
            "limitations must state that model accuracy is not proof-system correctness",
        );
    }
    if !manifest.limitations.iter().any(|limitation| {
        let lower = limitation.to_ascii_lowercase();
        lower.contains("zkml metrics") && lower.contains("semantic soundness")
    }) {
        push_issue(
            &mut issues,
            ZkMlWorkloadValidationIssueKind::MissingLimitation,
            "limitations",
            "limitations must state that zkML metrics do not prove semantic soundness",
        );
    }

    ZkMlWorkloadValidation {
        valid: issues.is_empty(),
        issues,
        claim_boundary: ClaimBoundary::Level0DesignNote,
    }
}

/// Serialize a zkML workload manifest as deterministic pretty JSON.
pub fn serialize_zkml_workload_manifest_json(manifest: &ZkMlWorkloadManifest) -> Result<String> {
    serde_json::to_string_pretty(manifest).map_err(|error| {
        crate::error::ZkBenchError::serialization(
            "serialize_zkml_workload_manifest_json",
            error.to_string(),
        )
    })
}

/// Deserialize a zkML workload manifest from JSON.
pub fn deserialize_zkml_workload_manifest_json(json: &str) -> Result<ZkMlWorkloadManifest> {
    serde_json::from_str(json).map_err(|error| {
        crate::error::ZkBenchError::serialization(
            "deserialize_zkml_workload_manifest_json",
            error.to_string(),
        )
    })
}

fn validate_required_identity(
    issues: &mut Vec<ZkMlWorkloadValidationIssue>,
    path: &'static str,
    value: &str,
) {
    if value.trim().is_empty() {
        push_issue(
            issues,
            ZkMlWorkloadValidationIssueKind::EmptyIdentity,
            path,
            format!("{path} must not be empty"),
        );
    }
}

fn validate_digest(
    issues: &mut Vec<ZkMlWorkloadValidationIssue>,
    path: impl Into<String>,
    digest: &ArtifactDigest,
) {
    let path = path.into();
    if digest.algorithm != ArtifactDigestAlgorithm::Sha256 {
        push_issue(
            issues,
            ZkMlWorkloadValidationIssueKind::InvalidDigest,
            &path,
            "digest algorithm must be sha256",
        );
    }
    if digest.hex_digest.len() != 64 || !digest.hex_digest.chars().all(|ch| ch.is_ascii_hexdigit())
    {
        push_issue(
            issues,
            ZkMlWorkloadValidationIssueKind::InvalidDigest,
            &path,
            "digest must be 64 hex characters",
        );
    }
    if digest.byte_len == 0 {
        push_issue(
            issues,
            ZkMlWorkloadValidationIssueKind::InvalidDigest,
            &path,
            "digest byte length must be non-zero",
        );
    }
}

fn is_portable_relative_artifact_ref(value: &str) -> bool {
    let trimmed = value.trim();
    !trimmed.is_empty()
        && !trimmed.starts_with('/')
        && !trimmed.starts_with('\\')
        && !trimmed.contains("..")
        && !trimmed.contains("://")
        && !trimmed.contains('\\')
        && !trimmed.contains(';')
        && !trimmed.contains('|')
        && !trimmed.contains('&')
        && !trimmed.contains('$')
        && !trimmed.contains('`')
}

fn push_issue(
    issues: &mut Vec<ZkMlWorkloadValidationIssue>,
    kind: ZkMlWorkloadValidationIssueKind,
    path: impl Into<String>,
    message: impl Into<String>,
) {
    issues.push(ZkMlWorkloadValidationIssue {
        kind,
        path: path.into(),
        message: message.into(),
    });
}
