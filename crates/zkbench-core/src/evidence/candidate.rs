//! Evidence-record candidate primitives.
//!
//! Candidates are reviewed metadata objects. They are not `EvidenceRecord`
//! values and are not appended to `EvidenceLedger` in Phase J.

use serde::{Deserialize, Serialize};

use crate::error::{Result, ZkBenchError};

use super::acceptance_policy::{EvidenceAcceptancePolicy, EvidenceAcceptanceValidation};
use super::review::EvidenceReviewDecision;
use super::{ArtifactDigest, ClaimBoundary, EvidenceClass};

/// Evidence-record candidate id.
pub type EvidenceRecordCandidateId = String;

/// Evidence-record candidate version.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct EvidenceRecordCandidateVersion {
    /// Logical version string.
    pub value: String,
}

impl Default for EvidenceRecordCandidateVersion {
    fn default() -> Self {
        Self {
            value: "phase-j-evidence-record-candidate-v0".to_string(),
        }
    }
}

/// Candidate status.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
pub enum EvidenceRecordCandidateStatus {
    /// Candidate only; not accepted evidence.
    CandidateOnly,
    /// Future manual append is required before any evidence ledger mutation.
    PendingFutureManualAppend,
    /// Candidate was rejected.
    Rejected,
    /// Candidate was superseded.
    Superseded,
}

/// Candidate source metadata.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct EvidenceRecordCandidateSource {
    /// Source proposal id.
    pub source_proposal_id: String,
    /// Source normalized draft id, when available.
    #[serde(default)]
    pub source_normalized_draft_id: Option<String>,
    /// Local replay ids, when a strict local-only candidate exists.
    #[serde(default)]
    pub source_local_replay_ids: Vec<String>,
    /// Review decision id.
    pub review_decision_id: String,
    /// Acceptance policy id.
    pub acceptance_policy_id: String,
}

/// Candidate kind.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
pub enum EvidenceRecordCandidateKind {
    /// Local replay candidate metadata.
    LocalReplayEvidenceCandidate,
    /// Synthetic import candidate metadata.
    SyntheticImportEvidenceCandidate,
    /// Design-note-only candidate metadata.
    DesignNoteCandidate,
    /// Future external replay candidate metadata.
    FutureExternalReplayCandidate,
}

/// Candidate validation issue kind.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
pub enum EvidenceRecordCandidateIssueKind {
    /// Required id was empty.
    EmptyId,
    /// Candidate attempted to imply accepted evidence.
    AcceptedEvidenceClaim,
    /// Claim boundary exceeded the Phase J cap.
    ClaimBoundaryTooHigh,
    /// Evidence class is not allowed in Phase J candidates.
    DisallowedEvidenceClass,
    /// Provenance summary was missing.
    MissingProvenance,
    /// Artifact digest metadata was missing.
    MissingArtifactDigest,
    /// Acceptance validation failed.
    AcceptanceValidationFailed,
    /// Forbidden claim language was detected.
    ForbiddenClaimLanguage,
}

/// Candidate validation issue.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct EvidenceRecordCandidateValidationIssue {
    /// Issue path.
    pub path: String,
    /// Issue message.
    pub message: String,
    /// Issue kind.
    pub kind: EvidenceRecordCandidateIssueKind,
}

/// Candidate validation result.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct EvidenceRecordCandidateValidation {
    /// True when no validation issues were found.
    pub valid: bool,
    /// Validation issues.
    pub issues: Vec<EvidenceRecordCandidateValidationIssue>,
}

/// Evidence-record candidate.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct EvidenceRecordCandidate {
    /// Candidate id.
    pub id: EvidenceRecordCandidateId,
    /// Candidate version.
    pub version: EvidenceRecordCandidateVersion,
    /// Candidate status.
    pub status: EvidenceRecordCandidateStatus,
    /// Candidate source metadata.
    pub source: EvidenceRecordCandidateSource,
    /// Candidate kind.
    pub kind: EvidenceRecordCandidateKind,
    /// Proposed evidence class.
    pub proposed_evidence_class: EvidenceClass,
    /// Proposed claim boundary.
    pub proposed_claim_boundary: ClaimBoundary,
    /// Proposed provenance summary.
    pub proposed_provenance_summary: Vec<String>,
    /// Proposed artifact references.
    #[serde(default)]
    pub proposed_artifact_refs: Vec<crate::external_runner::NormalizedArtifactRef>,
    /// Digest of the validation report that led to the candidate.
    #[serde(default)]
    pub validation_report_digest: Option<ArtifactDigest>,
    /// Acceptance-policy validation used to create this candidate.
    pub acceptance_validation: EvidenceAcceptanceValidation,
    /// Blocking candidate issues.
    #[serde(default)]
    pub blocking_issues: Vec<String>,
    /// True would be invalid in Phase J.
    pub claims_accepted_evidence: bool,
    /// True would be invalid in Phase J.
    pub claims_official_benchmark_evidence: bool,
    /// True would be invalid in Phase J.
    pub claims_formal_evidence: bool,
    /// True would be invalid in Phase J.
    pub claims_proof_system_soundness: bool,
    /// Candidate metrics remain metadata and cannot feed scores in Phase J.
    pub candidate_metrics_are_score_inputs: bool,
    /// Notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

impl EvidenceRecordCandidate {
    /// Candidates are never accepted evidence in Phase J.
    pub fn is_accepted_evidence(&self) -> bool {
        false
    }

    /// Return true when a future manual append would be needed before ledger mutation.
    pub fn requires_future_manual_append(&self) -> bool {
        matches!(
            self.status,
            EvidenceRecordCandidateStatus::CandidateOnly
                | EvidenceRecordCandidateStatus::PendingFutureManualAppend
        )
    }

    /// Candidates are not official benchmark evidence in Phase J.
    pub fn is_official_benchmark_evidence(&self) -> bool {
        false
    }

    /// Return true when the proposed boundary is Level2 or above.
    pub fn is_level2_or_above_candidate(&self) -> bool {
        self.proposed_claim_boundary >= ClaimBoundary::Level2ReproducibleBenchmarkArtifact
    }
}

/// Create a candidate from a reviewed append proposal.
pub fn create_evidence_record_candidate(
    policy: &EvidenceAcceptancePolicy,
    proposal: &crate::external_runner::EvidenceAppendProposal,
    decision: &EvidenceReviewDecision,
) -> Result<EvidenceRecordCandidate> {
    let policy_validation = super::acceptance_policy::validate_evidence_acceptance_policy(policy);
    if !policy_validation.valid {
        return Err(ZkBenchError::evidence_acceptance_policy(
            "candidate.policy",
            format!(
                "acceptance policy is invalid: {:?}",
                policy_validation.issues
            ),
        ));
    }
    let target_claim_boundary = match policy.mode {
        super::acceptance_policy::EvidenceAcceptancePolicyMode::Level1LocalOnly => {
            ClaimBoundary::Level1LocalReplay
        }
        super::acceptance_policy::EvidenceAcceptancePolicyMode::CandidateOnly => {
            ClaimBoundary::Level0DesignNote
        }
        _ => {
            return Err(ZkBenchError::evidence_record_candidate(
                "candidate.policy.mode",
                "policy mode does not allow candidate creation",
            ));
        }
    };
    let acceptance_validation =
        policy.validate_proposal_for_candidate(proposal, decision, target_claim_boundary);
    if !acceptance_validation.valid {
        return Err(ZkBenchError::evidence_record_candidate(
            "candidate.acceptance_validation",
            format!(
                "candidate acceptance validation failed: {:?}",
                acceptance_validation.issues
            ),
        ));
    }

    let kind = match target_claim_boundary {
        ClaimBoundary::Level1LocalReplay => {
            EvidenceRecordCandidateKind::LocalReplayEvidenceCandidate
        }
        ClaimBoundary::Level0DesignNote => {
            EvidenceRecordCandidateKind::SyntheticImportEvidenceCandidate
        }
        _ => EvidenceRecordCandidateKind::FutureExternalReplayCandidate,
    };
    let proposed_evidence_class = if target_claim_boundary == ClaimBoundary::Level1LocalReplay {
        EvidenceClass::LocalReplay
    } else {
        EvidenceClass::DesignNote
    };
    let candidate = EvidenceRecordCandidate {
        id: format!("candidate_{}", proposal.id),
        version: EvidenceRecordCandidateVersion::default(),
        status: EvidenceRecordCandidateStatus::CandidateOnly,
        source: EvidenceRecordCandidateSource {
            source_proposal_id: proposal.id.clone(),
            source_normalized_draft_id: Some(proposal.source_normalized_draft_id.clone()),
            source_local_replay_ids: Vec::new(),
            review_decision_id: decision.id.clone(),
            acceptance_policy_id: policy.id.clone(),
        },
        kind,
        proposed_evidence_class,
        proposed_claim_boundary: target_claim_boundary,
        proposed_provenance_summary: proposal.proposed_provenance_summary.clone(),
        proposed_artifact_refs: proposal.proposed_artifact_refs.clone(),
        validation_report_digest: proposal.validation_report_digest.clone(),
        acceptance_validation,
        blocking_issues: Vec::new(),
        claims_accepted_evidence: false,
        claims_official_benchmark_evidence: false,
        claims_formal_evidence: false,
        claims_proof_system_soundness: false,
        candidate_metrics_are_score_inputs: false,
        notes: vec![
            "Evidence-record candidates are not accepted evidence.".to_string(),
            "Future manual append is required before any EvidenceLedger mutation.".to_string(),
        ],
    };
    let validation = validate_evidence_record_candidate(&candidate);
    if validation.valid {
        Ok(candidate)
    } else {
        Err(ZkBenchError::evidence_record_candidate(
            "candidate",
            format!(
                "created candidate failed validation: {:?}",
                validation.issues
            ),
        ))
    }
}

/// Validate an evidence-record candidate.
pub fn validate_evidence_record_candidate(
    candidate: &EvidenceRecordCandidate,
) -> EvidenceRecordCandidateValidation {
    let mut issues = Vec::new();
    if candidate.id.trim().is_empty() {
        issues.push(issue(
            "candidate.id",
            "candidate id is empty",
            EvidenceRecordCandidateIssueKind::EmptyId,
        ));
    }
    if candidate.source.source_proposal_id.trim().is_empty() {
        issues.push(issue(
            "candidate.source.source_proposal_id",
            "source proposal id is empty",
            EvidenceRecordCandidateIssueKind::EmptyId,
        ));
    }
    if candidate.source.review_decision_id.trim().is_empty() {
        issues.push(issue(
            "candidate.source.review_decision_id",
            "review decision id is empty",
            EvidenceRecordCandidateIssueKind::EmptyId,
        ));
    }
    if candidate.claims_accepted_evidence
        || candidate.claims_official_benchmark_evidence
        || candidate.claims_formal_evidence
        || candidate.claims_proof_system_soundness
    {
        issues.push(issue(
            "candidate.claim_flags",
            "candidate claim flags must remain false",
            EvidenceRecordCandidateIssueKind::AcceptedEvidenceClaim,
        ));
    }
    if candidate.candidate_metrics_are_score_inputs {
        issues.push(issue(
            "candidate.candidate_metrics_are_score_inputs",
            "candidate metrics cannot feed score reports in Phase J",
            EvidenceRecordCandidateIssueKind::AcceptedEvidenceClaim,
        ));
    }
    if candidate.proposed_claim_boundary >= ClaimBoundary::Level2ReproducibleBenchmarkArtifact {
        issues.push(issue(
            "candidate.proposed_claim_boundary",
            "candidate claim boundary must remain Level1LocalReplay or below",
            EvidenceRecordCandidateIssueKind::ClaimBoundaryTooHigh,
        ));
    }
    if matches!(
        candidate.proposed_evidence_class,
        EvidenceClass::ReproducibleBenchmarkArtifact
            | EvidenceClass::CrossBackendReplay
            | EvidenceClass::FormalPropertyStatement
            | EvidenceClass::MachineCheckedScopedProof
            | EvidenceClass::IndependentlyReproducedEvidence
    ) {
        issues.push(issue(
            "candidate.proposed_evidence_class",
            "Phase J candidates cannot use Level2+ or formal evidence classes",
            EvidenceRecordCandidateIssueKind::DisallowedEvidenceClass,
        ));
    }
    if candidate.proposed_provenance_summary.is_empty() {
        issues.push(issue(
            "candidate.proposed_provenance_summary",
            "candidate provenance summary is empty",
            EvidenceRecordCandidateIssueKind::MissingProvenance,
        ));
    }
    if candidate.proposed_artifact_refs.is_empty() && candidate.validation_report_digest.is_none() {
        issues.push(issue(
            "candidate.proposed_artifact_refs",
            "candidate has no artifact digest metadata",
            EvidenceRecordCandidateIssueKind::MissingArtifactDigest,
        ));
    }
    if !candidate.acceptance_validation.valid {
        issues.push(issue(
            "candidate.acceptance_validation",
            "candidate acceptance validation is not valid",
            EvidenceRecordCandidateIssueKind::AcceptanceValidationFailed,
        ));
    }
    scan_candidate_text(candidate, &mut issues);
    EvidenceRecordCandidateValidation {
        valid: issues.is_empty(),
        issues,
    }
}

/// Serialize a candidate to pretty JSON.
pub fn serialize_evidence_record_candidate_json(
    candidate: &EvidenceRecordCandidate,
) -> Result<String> {
    serde_json::to_string_pretty(candidate).map_err(|error| {
        ZkBenchError::serialization(
            "serialize_evidence_record_candidate_json",
            error.to_string(),
        )
    })
}

/// Deserialize a candidate from JSON.
pub fn deserialize_evidence_record_candidate_json(json: &str) -> Result<EvidenceRecordCandidate> {
    serde_json::from_str(json).map_err(|error| {
        ZkBenchError::deserialization(
            "deserialize_evidence_record_candidate_json",
            error.to_string(),
        )
    })
}

fn scan_candidate_text(
    candidate: &EvidenceRecordCandidate,
    issues: &mut Vec<EvidenceRecordCandidateValidationIssue>,
) {
    for (index, note) in candidate.notes.iter().enumerate() {
        push_claim_issue(format!("candidate.notes[{index}]"), note, issues);
    }
    for (index, summary) in candidate.proposed_provenance_summary.iter().enumerate() {
        push_claim_issue(
            format!("candidate.proposed_provenance_summary[{index}]"),
            summary,
            issues,
        );
    }
    for (index, issue_text) in candidate.blocking_issues.iter().enumerate() {
        push_claim_issue(
            format!("candidate.blocking_issues[{index}]"),
            issue_text,
            issues,
        );
    }
}

fn push_claim_issue(
    path: String,
    text: &str,
    issues: &mut Vec<EvidenceRecordCandidateValidationIssue>,
) {
    if crate::external_runner::contains_forbidden_claim_text(text) {
        issues.push(issue(
            path,
            "candidate text contains forbidden claim language",
            EvidenceRecordCandidateIssueKind::ForbiddenClaimLanguage,
        ));
    }
}

fn issue(
    path: impl Into<String>,
    message: impl Into<String>,
    kind: EvidenceRecordCandidateIssueKind,
) -> EvidenceRecordCandidateValidationIssue {
    EvidenceRecordCandidateValidationIssue {
        path: path.into(),
        message: message.into(),
        kind,
    }
}
