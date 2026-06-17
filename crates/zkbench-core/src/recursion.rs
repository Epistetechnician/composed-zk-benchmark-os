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
