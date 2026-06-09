//! Artifact capture contract for future external result review.

use serde::{Deserialize, Serialize};

use crate::evidence::{ArtifactDigest, ClaimBoundary};

use super::validation::{
    contains_rejected_path, phase_h_design_artifact_claim_allowed, ExternalValidationIssueSeverity,
};

/// Artifact capture contract id.
pub type ArtifactCaptureContractId = String;

/// Artifact capture contract version.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ArtifactCaptureContractVersion {
    /// Logical version string.
    pub value: String,
}

impl Default for ArtifactCaptureContractVersion {
    fn default() -> Self {
        Self {
            value: "phase-h-artifact-capture-contract-v0".to_string(),
        }
    }
}

/// Expected future artifact role.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
pub enum ExpectedArtifactRole {
    /// Input manifest.
    InputManifest,
    /// Candidate workload manifest.
    CandidateWorkloadManifest,
    /// External tool version metadata.
    ExternalToolVersion,
    /// Raw external output.
    RawExternalOutput,
    /// Normalized result candidate.
    NormalizedResultCandidate,
    /// Provenance record.
    ProvenanceRecord,
    /// Validation report.
    ValidationReport,
    /// Evidence append proposal.
    EvidenceAppendProposal,
}

/// Expected future artifact format.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
pub enum ExpectedArtifactFormat {
    /// JSON artifact.
    Json,
    /// Markdown artifact.
    Markdown,
    /// Directory digest artifact.
    DirectoryDigest,
    /// Plain text artifact.
    Text,
    /// Unknown future format.
    UnknownFutureFormat,
}

/// Capture requirement for an expected artifact.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum ArtifactCaptureRequirement {
    /// Required before result import review.
    Required,
    /// Optional future artifact.
    Optional,
    /// Forbidden as an actual Phase H artifact.
    ForbiddenInPhaseH,
}

/// Expected artifact declaration.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ExpectedArtifact {
    /// Artifact id.
    pub id: String,
    /// Expected role.
    pub role: ExpectedArtifactRole,
    /// Expected format.
    pub format: ExpectedArtifactFormat,
    /// Capture requirement.
    pub requirement: ArtifactCaptureRequirement,
    /// Optional relative path hint.
    #[serde(default)]
    pub relative_path_hint: Option<String>,
    /// Notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

/// Captured artifact metadata. Phase H default contracts contain no actual
/// captured external artifacts.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct CapturedArtifactMetadata {
    /// Artifact id.
    pub id: String,
    /// Artifact role.
    pub role: ExpectedArtifactRole,
    /// Artifact format.
    pub format: ExpectedArtifactFormat,
    /// Relative URI.
    pub relative_uri: String,
    /// Optional artifact digest.
    #[serde(default)]
    pub digest: Option<ArtifactDigest>,
    /// Review status.
    pub reviewed: bool,
    /// Notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

/// Artifact validation issue.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct CapturedArtifactValidationIssue {
    /// Issue path.
    pub path: String,
    /// Issue message.
    pub message: String,
    /// Issue severity.
    pub severity: ExternalValidationIssueSeverity,
}

impl CapturedArtifactValidationIssue {
    fn error(path: impl Into<String>, message: impl Into<String>) -> Self {
        Self {
            path: path.into(),
            message: message.into(),
            severity: ExternalValidationIssueSeverity::Error,
        }
    }

    fn warning(path: impl Into<String>, message: impl Into<String>) -> Self {
        Self {
            path: path.into(),
            message: message.into(),
            severity: ExternalValidationIssueSeverity::Warning,
        }
    }
}

/// Artifact capture validation result.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct CapturedArtifactValidation {
    /// True when there are no errors.
    pub valid: bool,
    /// Errors.
    pub errors: Vec<CapturedArtifactValidationIssue>,
    /// Warnings.
    pub warnings: Vec<CapturedArtifactValidationIssue>,
}

/// Artifact capture contract.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ArtifactCaptureContract {
    /// Contract id.
    pub id: ArtifactCaptureContractId,
    /// Contract version.
    pub contract_version: ArtifactCaptureContractVersion,
    /// Expected future artifacts.
    pub expected_artifacts: Vec<ExpectedArtifact>,
    /// Captured artifact metadata. Empty for default Phase H contracts.
    #[serde(default)]
    pub captured_artifacts: Vec<CapturedArtifactMetadata>,
    /// Claim boundary for the contract artifact.
    pub claim_boundary: ClaimBoundary,
    /// Notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

impl ArtifactCaptureContract {
    /// Return true when no actual external artifacts are recorded.
    pub fn has_no_actual_external_artifacts(&self) -> bool {
        self.captured_artifacts.is_empty()
    }
}

/// Build the default Phase H artifact capture contract.
pub fn build_default_artifact_capture_contract() -> ArtifactCaptureContract {
    ArtifactCaptureContract {
        id: "artifact_capture_contract_phase_h".to_string(),
        contract_version: ArtifactCaptureContractVersion::default(),
        expected_artifacts: default_expected_artifacts(),
        captured_artifacts: Vec::new(),
        claim_boundary: ClaimBoundary::Level0DesignNote,
        notes: vec![
            "Artifact capture contract only; no external artifacts are captured in Phase H."
                .to_string(),
            "Manual handoff bundles are not benchmark results.".to_string(),
            "No official benchmark evidence is created by this contract.".to_string(),
        ],
    }
}

/// Validate an artifact capture contract.
pub fn validate_artifact_capture_contract(
    contract: &ArtifactCaptureContract,
) -> CapturedArtifactValidation {
    let mut errors = Vec::new();
    let mut warnings = Vec::new();

    if contract.id.trim().is_empty() {
        errors.push(CapturedArtifactValidationIssue::error(
            "contract.id",
            "artifact capture contract id is empty",
        ));
    }
    if !phase_h_design_artifact_claim_allowed(contract.claim_boundary) {
        errors.push(CapturedArtifactValidationIssue::error(
            "contract.claim_boundary",
            "artifact capture contracts must remain Level0DesignNote",
        ));
    }
    if contract.expected_artifacts.is_empty() {
        errors.push(CapturedArtifactValidationIssue::error(
            "contract.expected_artifacts",
            "artifact capture contract has no expected artifacts",
        ));
    }
    for (index, expected) in contract.expected_artifacts.iter().enumerate() {
        if expected.id.trim().is_empty() {
            errors.push(CapturedArtifactValidationIssue::error(
                format!("contract.expected_artifacts[{index}].id"),
                "expected artifact id is empty",
            ));
        }
        if let Some(path) = &expected.relative_path_hint {
            if contains_rejected_path(path) {
                errors.push(CapturedArtifactValidationIssue::error(
                    format!("contract.expected_artifacts[{index}].relative_path_hint"),
                    "expected artifact path hint is absolute or contains traversal",
                ));
            }
        }
    }
    if !contract.captured_artifacts.is_empty() {
        warnings.push(CapturedArtifactValidationIssue::warning(
            "contract.captured_artifacts",
            "Phase H contracts should describe expectations; captured external artifacts require future review",
        ));
    }
    for (index, captured) in contract.captured_artifacts.iter().enumerate() {
        if contains_rejected_path(&captured.relative_uri) {
            errors.push(CapturedArtifactValidationIssue::error(
                format!("contract.captured_artifacts[{index}].relative_uri"),
                "captured artifact URI is absolute or contains traversal",
            ));
        }
        if !captured.reviewed {
            warnings.push(CapturedArtifactValidationIssue::warning(
                format!("contract.captured_artifacts[{index}].reviewed"),
                "captured artifact is not reviewed",
            ));
        }
    }

    CapturedArtifactValidation {
        valid: errors.is_empty(),
        errors,
        warnings,
    }
}

fn default_expected_artifacts() -> Vec<ExpectedArtifact> {
    vec![
        expected(
            "input_manifest",
            ExpectedArtifactRole::InputManifest,
            ExpectedArtifactFormat::Json,
            ArtifactCaptureRequirement::Required,
            Some("handoff/input_manifest.json"),
        ),
        expected(
            "candidate_workload_manifest",
            ExpectedArtifactRole::CandidateWorkloadManifest,
            ExpectedArtifactFormat::Json,
            ArtifactCaptureRequirement::Required,
            Some("handoff/candidate_workload_manifest.json"),
        ),
        expected(
            "external_tool_version",
            ExpectedArtifactRole::ExternalToolVersion,
            ExpectedArtifactFormat::Text,
            ArtifactCaptureRequirement::Required,
            Some("provenance/external_tool_version.txt"),
        ),
        expected(
            "raw_external_output",
            ExpectedArtifactRole::RawExternalOutput,
            ExpectedArtifactFormat::UnknownFutureFormat,
            ArtifactCaptureRequirement::ForbiddenInPhaseH,
            Some("artifacts/raw_external_output"),
        ),
        expected(
            "normalized_result_candidate",
            ExpectedArtifactRole::NormalizedResultCandidate,
            ExpectedArtifactFormat::Json,
            ArtifactCaptureRequirement::Required,
            Some("handoff/normalized_result_candidate.json"),
        ),
        expected(
            "provenance_record",
            ExpectedArtifactRole::ProvenanceRecord,
            ExpectedArtifactFormat::Json,
            ArtifactCaptureRequirement::Required,
            Some("provenance/provenance_record.json"),
        ),
        expected(
            "validation_report",
            ExpectedArtifactRole::ValidationReport,
            ExpectedArtifactFormat::Json,
            ArtifactCaptureRequirement::Required,
            Some("handoff/validation_report.json"),
        ),
        expected(
            "evidence_append_proposal",
            ExpectedArtifactRole::EvidenceAppendProposal,
            ExpectedArtifactFormat::Json,
            ArtifactCaptureRequirement::ForbiddenInPhaseH,
            Some("handoff/evidence_append_proposal.json"),
        ),
    ]
}

fn expected(
    id: &str,
    role: ExpectedArtifactRole,
    format: ExpectedArtifactFormat,
    requirement: ArtifactCaptureRequirement,
    relative_path_hint: Option<&str>,
) -> ExpectedArtifact {
    ExpectedArtifact {
        id: id.to_string(),
        role,
        format,
        requirement,
        relative_path_hint: relative_path_hint.map(str::to_string),
        notes: vec!["Expected future artifact only; not captured by Phase H.".to_string()],
    }
}
