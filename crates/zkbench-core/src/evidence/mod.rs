//! Evidence, claim-boundary, expected-verdict, backend-outcome, result
//! classification, artifact digest, and local ledger primitives.

pub mod acceptance_policy;
pub mod accepted_append;
pub mod append_preview;
pub mod artifact;
pub mod candidate;
pub mod digest;
pub mod eligibility;
pub mod escalation_guard;
pub mod ledger;
pub mod promotion_preflight;
pub mod review;
pub mod review_ledger;

use std::fmt;

use serde::{Deserialize, Serialize};

use crate::adapters::BackendTarget;

pub use acceptance_policy::{
    build_default_evidence_acceptance_policy, deserialize_evidence_acceptance_policy_json,
    serialize_evidence_acceptance_policy_json, validate_evidence_acceptance_policy,
    EvidenceAcceptanceBlockingReason, EvidenceAcceptancePolicy, EvidenceAcceptancePolicyId,
    EvidenceAcceptancePolicyMode, EvidenceAcceptancePolicyVersion, EvidenceAcceptanceRule,
    EvidenceAcceptanceRuleResult, EvidenceAcceptanceValidation, EvidenceAcceptanceValidationIssue,
};
pub use accepted_append::{
    apply_accepted_ledger_append_transaction, build_evidence_record_from_transaction,
    validate_accepted_ledger_append_transaction_request, AcceptedLedgerAppendTransactionIssue,
    AcceptedLedgerAppendTransactionIssueKind, AcceptedLedgerAppendTransactionReport,
    AcceptedLedgerAppendTransactionRequest, AcceptedLedgerAppendTransactionValidation,
    AcceptedLedgerAppendTransactionVersion,
};
pub use append_preview::{
    create_evidence_append_preview, deserialize_evidence_append_preview_json,
    serialize_evidence_append_preview_json, validate_evidence_append_preview,
    EvidenceAppendPreview, EvidenceAppendPreviewId, EvidenceAppendPreviewIssueKind,
    EvidenceAppendPreviewStatus, EvidenceAppendPreviewValidation,
    EvidenceAppendPreviewValidationIssue, EvidenceAppendPreviewVersion,
    EvidenceLedgerAppendPreviewEntry, EvidenceLedgerAppendTransactionPreview,
};
pub use artifact::{
    ArtifactDigest, ArtifactDigestAlgorithm, ArtifactKind, ArtifactRef, ArtifactRole,
};
pub use candidate::{
    create_evidence_record_candidate, deserialize_evidence_record_candidate_json,
    serialize_evidence_record_candidate_json, validate_evidence_record_candidate,
    EvidenceRecordCandidate, EvidenceRecordCandidateId, EvidenceRecordCandidateIssueKind,
    EvidenceRecordCandidateKind, EvidenceRecordCandidateSource, EvidenceRecordCandidateStatus,
    EvidenceRecordCandidateValidation, EvidenceRecordCandidateValidationIssue,
    EvidenceRecordCandidateVersion,
};
pub use digest::{
    canonical_json_bytes, compute_artifact_digest, compute_artifact_digest_bytes,
    compute_artifact_digest_for_json,
};
pub use eligibility::{
    check_level2_eligibility, deserialize_level2_eligibility_report_json,
    serialize_level2_eligibility_report_json, Level2EligibilityBlockingReason,
    Level2EligibilityChecker, Level2EligibilityFinding, Level2EligibilityReport,
    Level2EligibilityRequirement, Level2EligibilityStatus,
};
pub use escalation_guard::{
    guard_claim_boundary_escalation, ClaimBoundaryEscalationGuard,
    ClaimBoundaryEscalationGuardResult,
};
pub use ledger::{
    EvidenceAppendPolicy, EvidenceChainDigest, EvidenceLedger, EvidenceLedgerEntry,
    EvidenceLedgerSummary, EvidenceLedgerSummaryCount, EvidenceLedgerValidation,
    EvidenceLedgerValidationError, EvidenceLedgerVersion,
};
pub use promotion_preflight::{
    build_reviewed_promotion_preflight_report, compute_official_submission_package_metadata_digest,
    compute_reviewed_promotion_preflight_report_digest,
    deserialize_official_submission_package_metadata_json,
    deserialize_reviewed_promotion_preflight_report_json,
    render_official_submission_package_markdown, render_reviewed_promotion_preflight_markdown,
    required_reviewed_promotion_preflight_non_claims,
    serialize_official_submission_package_metadata_json,
    serialize_reviewed_promotion_preflight_report_json,
    validate_official_submission_package_metadata, validate_reviewed_promotion_preflight_request,
    OfficialSubmissionPackageIssue, OfficialSubmissionPackageIssueKind,
    OfficialSubmissionPackageMetadata, OfficialSubmissionPackageValidation,
    OfficialSubmissionPackageVersion, ReviewedPromotionPreflightIssue,
    ReviewedPromotionPreflightIssueKind, ReviewedPromotionPreflightReport,
    ReviewedPromotionPreflightRequest, ReviewedPromotionPreflightValidation,
    ReviewedPromotionPreflightVersion, ReviewedPromotionSourceSummary,
};
pub use review::{
    build_default_evidence_review_checklist, deserialize_evidence_review_checklist_json,
    deserialize_evidence_review_decision_json, review_evidence_append_proposal,
    serialize_evidence_review_checklist_json, serialize_evidence_review_decision_json,
    validate_evidence_review_decision, EvidenceReviewChecklist, EvidenceReviewChecklistItem,
    EvidenceReviewDecision, EvidenceReviewDecisionId, EvidenceReviewDecisionKind,
    EvidenceReviewDecisionStatus, EvidenceReviewDecisionVersion, EvidenceReviewFinding,
    EvidenceReviewFindingSeverity, EvidenceReviewPolicy, EvidenceReviewReport,
    EvidenceReviewRequirement, EvidenceReviewerRole,
};
pub use review_ledger::{
    deserialize_evidence_review_ledger_json, serialize_evidence_review_ledger_json,
    EvidenceReviewLedger, EvidenceReviewLedgerDigest, EvidenceReviewLedgerEntry,
    EvidenceReviewLedgerEntrySubject, EvidenceReviewLedgerEntryVersion,
    EvidenceReviewLedgerSummary, EvidenceReviewLedgerSummaryCount, EvidenceReviewLedgerValidation,
    EvidenceReviewLedgerValidationIssue, EvidenceReviewLedgerVersion,
};

/// Expected semantic verdict declared before backend replay.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum ExpectedVerdict {
    /// Semantic accept.
    #[serde(alias = "expected_accept", alias = "accept")]
    Accept,
    /// Semantic reject.
    #[serde(alias = "expected_reject", alias = "reject")]
    Reject,
    /// Backend error is expected for malformed or unsupported input.
    #[serde(alias = "expected_backend_error", alias = "backend_error")]
    BackendError,
    /// Outcome is expected to be inconclusive.
    #[serde(alias = "expected_inconclusive", alias = "inconclusive")]
    Inconclusive,
    /// Capability gap is expected.
    #[serde(alias = "expected_capability_gap", alias = "capability_gap")]
    CapabilityGap,
    /// Acceptance would be an unsound acceptance candidate, not a proven exploit.
    #[serde(alias = "expected_unsound_if_accepted", alias = "unsound_if_accepted")]
    UnsoundIfAccepted,
}

/// Normalized backend outcome.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum BackendOutcome {
    /// Backend accepted the artifact.
    #[serde(alias = "accepted")]
    Accepted,
    /// Backend rejected the artifact.
    #[serde(alias = "rejected")]
    Rejected,
    /// Backend errored.
    #[serde(alias = "backend_error", alias = "error")]
    Error,
    /// Backend timed out.
    #[serde(alias = "timeout")]
    Timeout,
    /// Backend reported a capability gap.
    #[serde(alias = "capability_gap")]
    CapabilityGap,
    /// Backend reported malformed artifact.
    #[serde(alias = "malformed_artifact")]
    MalformedArtifact,
    /// Backend outcome is inconclusive.
    #[serde(alias = "inconclusive")]
    Inconclusive,
}

/// Pure classification of expected verdict and backend outcome.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum ResultClassification {
    /// Expected accept and backend accepted.
    ExpectedAcceptAccepted,
    /// Expected accept and backend rejected; this is a false rejection candidate.
    ExpectedAcceptRejected,
    /// Expected reject and backend rejected.
    ExpectedRejectRejected,
    /// Expected reject and backend accepted; this is an unsound acceptance candidate.
    ExpectedRejectAcceptedUnsoundCandidate,
    /// Expected reject and backend errored.
    ExpectedRejectBackendError,
    /// Expected backend error was observed.
    ExpectedBackendErrorObserved,
    /// Backend or expected verdict was a capability gap.
    CapabilityGap,
    /// Backend timed out; timeout is not automatically a soundness failure.
    Timeout,
    /// Outcome is inconclusive.
    Inconclusive,
    /// Backend reported malformed artifact.
    MalformedArtifact,
    /// Outcome was unexpected for the declared expected verdict.
    UnexpectedOutcome,
}

/// Classify expected verdict and backend outcome.
pub fn classify_result(expected: ExpectedVerdict, backend: BackendOutcome) -> ResultClassification {
    match backend {
        BackendOutcome::Timeout => ResultClassification::Timeout,
        BackendOutcome::CapabilityGap => ResultClassification::CapabilityGap,
        BackendOutcome::MalformedArtifact => ResultClassification::MalformedArtifact,
        BackendOutcome::Inconclusive => ResultClassification::Inconclusive,
        BackendOutcome::Accepted => match expected {
            ExpectedVerdict::Accept => ResultClassification::ExpectedAcceptAccepted,
            ExpectedVerdict::Reject | ExpectedVerdict::UnsoundIfAccepted => {
                ResultClassification::ExpectedRejectAcceptedUnsoundCandidate
            }
            ExpectedVerdict::CapabilityGap => ResultClassification::CapabilityGap,
            ExpectedVerdict::Inconclusive => ResultClassification::Inconclusive,
            ExpectedVerdict::BackendError => ResultClassification::UnexpectedOutcome,
        },
        BackendOutcome::Rejected => match expected {
            ExpectedVerdict::Accept => ResultClassification::ExpectedAcceptRejected,
            ExpectedVerdict::Reject | ExpectedVerdict::UnsoundIfAccepted => {
                ResultClassification::ExpectedRejectRejected
            }
            ExpectedVerdict::CapabilityGap => ResultClassification::CapabilityGap,
            ExpectedVerdict::Inconclusive => ResultClassification::Inconclusive,
            ExpectedVerdict::BackendError => ResultClassification::UnexpectedOutcome,
        },
        BackendOutcome::Error => match expected {
            ExpectedVerdict::BackendError => ResultClassification::ExpectedBackendErrorObserved,
            ExpectedVerdict::Reject | ExpectedVerdict::UnsoundIfAccepted => {
                ResultClassification::ExpectedRejectBackendError
            }
            ExpectedVerdict::CapabilityGap => ResultClassification::CapabilityGap,
            ExpectedVerdict::Inconclusive => ResultClassification::Inconclusive,
            ExpectedVerdict::Accept => ResultClassification::UnexpectedOutcome,
        },
    }
}

/// Evidence class.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub enum EvidenceClass {
    /// Design note only.
    DesignNote,
    /// Local replay evidence.
    LocalReplay,
    /// Reproducible benchmark artifact.
    ReproducibleBenchmarkArtifact,
    /// Cross-backend replay evidence.
    CrossBackendReplay,
    /// Formal property statement.
    FormalPropertyStatement,
    /// Machine-checked scoped proof.
    MachineCheckedScopedProof,
    /// Independently reproduced evidence.
    IndependentlyReproducedEvidence,
}

/// Evidence strength label used by score primitives.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub enum EvidenceStrength {
    /// No evidence beyond design.
    None,
    /// Weak local evidence.
    Weak,
    /// Medium local evidence with clear provenance.
    Medium,
    /// Strong reproducible evidence.
    Strong,
    /// Scoped proof evidence.
    ScopedProof,
    /// Independent reproduction.
    Independent,
}

/// Claim boundary levels. Ordering is evidence strength ordering.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
pub enum ClaimBoundary {
    /// Level 0: design note only.
    Level0DesignNote,
    /// Level 1: local replay evidence.
    Level1LocalReplay,
    /// Level 2: reproducible benchmark artifact.
    Level2ReproducibleBenchmarkArtifact,
    /// Level 3: cross-backend replay evidence.
    Level3CrossBackendReplay,
    /// Level 4: formal property statement.
    Level4FormalPropertyStatement,
    /// Level 5: machine-checked proof for a scoped property.
    Level5MachineCheckedScopedProof,
    /// Level 6: independently reproduced evidence.
    Level6IndependentlyReproducedEvidence,
}

impl ClaimBoundary {
    /// Numeric level.
    pub fn level(self) -> u8 {
        match self {
            Self::Level0DesignNote => 0,
            Self::Level1LocalReplay => 1,
            Self::Level2ReproducibleBenchmarkArtifact => 2,
            Self::Level3CrossBackendReplay => 3,
            Self::Level4FormalPropertyStatement => 4,
            Self::Level5MachineCheckedScopedProof => 5,
            Self::Level6IndependentlyReproducedEvidence => 6,
        }
    }
}

impl fmt::Display for ClaimBoundary {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str(match self {
            Self::Level0DesignNote => "Level0DesignNote",
            Self::Level1LocalReplay => "Level1LocalReplay",
            Self::Level2ReproducibleBenchmarkArtifact => "Level2ReproducibleBenchmarkArtifact",
            Self::Level3CrossBackendReplay => "Level3CrossBackendReplay",
            Self::Level4FormalPropertyStatement => "Level4FormalPropertyStatement",
            Self::Level5MachineCheckedScopedProof => "Level5MachineCheckedScopedProof",
            Self::Level6IndependentlyReproducedEvidence => "Level6IndependentlyReproducedEvidence",
        })
    }
}

/// Provenance metadata for evidence.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ProvenanceRecord {
    /// Source identifier or path.
    pub source: String,
    /// Optional capture time string.
    #[serde(default)]
    pub captured_at: Option<String>,
    /// Optional command string.
    #[serde(default)]
    pub command: Option<String>,
    /// Additional provenance notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

/// Evidence record. This structure records claim boundaries; it does not
/// imply external reproducibility unless Level 2+ artifacts exist in a future
/// phase.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct EvidenceRecord {
    /// Evidence class.
    pub evidence_class: EvidenceClass,
    /// Maximum claim boundary justified by the record.
    pub claim_boundary: ClaimBoundary,
    /// Provenance metadata.
    pub provenance: ProvenanceRecord,
    /// Optional artifact digest.
    #[serde(default)]
    pub artifact_digest: Option<ArtifactDigest>,
    /// Notes about limitations and scope.
    #[serde(default)]
    pub notes: Vec<String>,
    /// Optional backend target metadata.
    #[serde(default)]
    pub backend_target: Option<BackendTarget>,
}

#[cfg(test)]
mod tests {
    use super::ClaimBoundary;

    #[test]
    fn claim_boundary_ordering_is_monotonic() {
        assert!(ClaimBoundary::Level0DesignNote < ClaimBoundary::Level1LocalReplay);
        assert!(
            ClaimBoundary::Level1LocalReplay < ClaimBoundary::Level2ReproducibleBenchmarkArtifact
        );
        assert_eq!(ClaimBoundary::Level5MachineCheckedScopedProof.level(), 5);
        assert_eq!(
            ClaimBoundary::Level1LocalReplay.to_string(),
            "Level1LocalReplay"
        );
    }
}
