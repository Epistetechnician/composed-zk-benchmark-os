//! Phase W accepted-ledger append transaction.
//!
//! This module is local-only. It appends only to a caller-supplied in-memory
//! `EvidenceLedger` after the reviewed promotion preflight, candidate, append
//! preview, review decision, artifact digests, and current ledger tip all align.
//! It does not submit to an official endpoint, run external replay, populate
//! score axes, or permit Level2+ promotion.

use serde::{Deserialize, Serialize};

use crate::error::{Result, ZkBenchError};

use super::digest::compute_artifact_digest;
use super::{
    ArtifactDigest, ArtifactKind, ArtifactRole, ClaimBoundary, EvidenceClass, EvidenceLedger,
    EvidenceRecord, ProvenanceRecord, ReviewedPromotionPreflightReport,
    ReviewedPromotionPreflightRequest,
};

/// Phase W accepted-ledger append transaction schema version.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct AcceptedLedgerAppendTransactionVersion {
    /// Logical version string.
    pub value: String,
}

impl Default for AcceptedLedgerAppendTransactionVersion {
    fn default() -> Self {
        Self {
            value: "phase-w-accepted-ledger-append-transaction-v0".to_string(),
        }
    }
}

/// Accepted-ledger append transaction request.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct AcceptedLedgerAppendTransactionRequest {
    /// Transaction id.
    pub transaction_id: String,
    /// Schema version.
    pub version: AcceptedLedgerAppendTransactionVersion,
    /// Explicit caller-selected target ledger id.
    pub target_evidence_ledger_id: String,
    /// Preflight request carrying the reviewed candidate, preview, and decision.
    pub preflight_request: ReviewedPromotionPreflightRequest,
    /// Preflight report built from the same request.
    pub preflight_report: ReviewedPromotionPreflightReport,
    /// Expected current ledger tip at append time.
    #[serde(default)]
    pub expected_current_ledger_tip: Option<ArtifactDigest>,
    /// Transaction notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

/// Accepted-ledger append transaction issue kind.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
pub enum AcceptedLedgerAppendTransactionIssueKind {
    /// Required id was empty.
    EmptyIdentity,
    /// Current ledger validation failed.
    InvalidLedger,
    /// Promotion preflight validation failed.
    InvalidPreflight,
    /// Preflight report and request disagree.
    PreflightReportMismatch,
    /// Candidate and append preview disagree.
    CandidatePreviewMismatch,
    /// Current ledger tip differs from the transaction expectation.
    StaleLedgerTip,
    /// Requested append exceeds the local accepted-ledger boundary.
    ClaimBoundaryTooHigh,
    /// Official submission was attempted.
    OfficialSubmissionAttempted,
    /// Score-axis population was attempted.
    ScoreAxisPopulationAttempted,
    /// Candidate digest or append-preview entry metadata mismatched.
    CandidateDigestMismatch,
    /// Source artifact digest was missing.
    MissingArtifactDigest,
    /// Transaction text contained forbidden claim language.
    ForbiddenClaimText,
}

/// Accepted-ledger append transaction validation issue.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct AcceptedLedgerAppendTransactionIssue {
    /// Issue kind.
    pub kind: AcceptedLedgerAppendTransactionIssueKind,
    /// Issue path.
    pub path: String,
    /// Human-readable message.
    pub message: String,
}

/// Accepted-ledger append transaction validation.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct AcceptedLedgerAppendTransactionValidation {
    /// Whether the transaction can append.
    pub valid: bool,
    /// Validation issues.
    #[serde(default)]
    pub issues: Vec<AcceptedLedgerAppendTransactionIssue>,
}

/// Accepted-ledger append transaction report.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct AcceptedLedgerAppendTransactionReport {
    /// Transaction id.
    pub transaction_id: String,
    /// Schema version.
    pub version: AcceptedLedgerAppendTransactionVersion,
    /// Explicit target ledger id.
    pub target_evidence_ledger_id: String,
    /// Source candidate id.
    pub source_candidate_id: String,
    /// Source append preview id.
    pub source_append_preview_id: String,
    /// Source review decision id.
    pub source_review_decision_id: String,
    /// Expected ledger tip before append.
    #[serde(default)]
    pub expected_previous_tip: Option<ArtifactDigest>,
    /// Appended ledger sequence number.
    #[serde(default)]
    pub appended_sequence_number: Option<u64>,
    /// Appended ledger entry digest.
    #[serde(default)]
    pub appended_entry_digest: Option<ArtifactDigest>,
    /// Validation result.
    pub validation: AcceptedLedgerAppendTransactionValidation,
    /// Whether this report records an accepted-ledger mutation.
    pub mutates_accepted_evidence_ledger: bool,
    /// Official submissions are not created by this transaction.
    pub creates_official_submission: bool,
    /// Score axes are not populated by this transaction.
    pub populates_score_axes: bool,
    /// Claim boundary of the appended evidence record.
    pub appended_claim_boundary: ClaimBoundary,
    /// Evidence class of the appended evidence record.
    pub appended_evidence_class: EvidenceClass,
    /// Required limitation labels carried from preflight.
    #[serde(default)]
    pub non_claims: Vec<String>,
}

/// Validate an accepted-ledger append transaction without mutating the ledger.
pub fn validate_accepted_ledger_append_transaction_request(
    request: &AcceptedLedgerAppendTransactionRequest,
    ledger: &EvidenceLedger,
) -> AcceptedLedgerAppendTransactionValidation {
    let mut issues = Vec::new();
    if request.transaction_id.trim().is_empty() {
        push_issue(
            &mut issues,
            AcceptedLedgerAppendTransactionIssueKind::EmptyIdentity,
            "request.transaction_id",
            "transaction id must be non-empty",
        );
    }
    if request.target_evidence_ledger_id.trim().is_empty() {
        push_issue(
            &mut issues,
            AcceptedLedgerAppendTransactionIssueKind::EmptyIdentity,
            "request.target_evidence_ledger_id",
            "target evidence ledger id must be explicit and non-empty",
        );
    }

    let ledger_validation = ledger.validate();
    if !ledger_validation.valid {
        push_issue(
            &mut issues,
            AcceptedLedgerAppendTransactionIssueKind::InvalidLedger,
            "ledger",
            format!("target ledger is invalid: {:?}", ledger_validation.errors),
        );
    }

    let preflight_validation =
        super::validate_reviewed_promotion_preflight_request(&request.preflight_request);
    if !preflight_validation.valid {
        push_issue(
            &mut issues,
            AcceptedLedgerAppendTransactionIssueKind::InvalidPreflight,
            "request.preflight_request",
            format!(
                "preflight request is invalid: {:?}",
                preflight_validation.issues
            ),
        );
    }
    let expected_report =
        super::build_reviewed_promotion_preflight_report(&request.preflight_request);
    if expected_report != request.preflight_report {
        push_issue(
            &mut issues,
            AcceptedLedgerAppendTransactionIssueKind::PreflightReportMismatch,
            "request.preflight_report",
            "preflight report must be built from the supplied preflight request",
        );
    }
    if !request.preflight_report.validation.valid {
        push_issue(
            &mut issues,
            AcceptedLedgerAppendTransactionIssueKind::InvalidPreflight,
            "request.preflight_report.validation",
            "preflight report validation must be valid",
        );
    }
    if request.preflight_report.mutates_accepted_evidence_ledger
        || request.preflight_report.creates_official_submission
        || request.preflight_report.populates_score_axes
    {
        push_issue(
            &mut issues,
            AcceptedLedgerAppendTransactionIssueKind::InvalidPreflight,
            "request.preflight_report",
            "preflight report must remain non-mutating and non-submitting",
        );
    }

    validate_current_tip(request, ledger, &mut issues);
    validate_candidate_preview_alignment(request, &mut issues);
    validate_local_append_boundary(request, &mut issues);
    scan_transaction_text(request, &mut issues);

    AcceptedLedgerAppendTransactionValidation {
        valid: issues.is_empty(),
        issues,
    }
}

/// Apply a validated accepted-ledger append transaction to a caller-supplied ledger.
pub fn apply_accepted_ledger_append_transaction(
    request: &AcceptedLedgerAppendTransactionRequest,
    ledger: &mut EvidenceLedger,
) -> Result<AcceptedLedgerAppendTransactionReport> {
    let validation = validate_accepted_ledger_append_transaction_request(request, ledger);
    if !validation.valid {
        return Err(ZkBenchError::evidence_ledger(
            "accepted_ledger_append_transaction",
            format!("transaction validation failed: {:?}", validation.issues),
        ));
    }

    let record = build_evidence_record_from_transaction(request)?;
    let expected_previous_tip = ledger
        .entries
        .last()
        .map(|entry| entry.entry_digest.clone());
    ledger.append(record)?;
    let appended = ledger.entries.last().ok_or_else(|| {
        ZkBenchError::evidence_ledger(
            "accepted_ledger_append_transaction",
            "append reported success but ledger has no entries",
        )
    })?;
    let report = AcceptedLedgerAppendTransactionReport {
        transaction_id: request.transaction_id.clone(),
        version: request.version.clone(),
        target_evidence_ledger_id: request.target_evidence_ledger_id.clone(),
        source_candidate_id: request.preflight_request.candidate.id.clone(),
        source_append_preview_id: request.preflight_request.append_preview.id.clone(),
        source_review_decision_id: request.preflight_request.review_decision.id.clone(),
        expected_previous_tip,
        appended_sequence_number: Some(appended.sequence_number),
        appended_entry_digest: Some(appended.entry_digest.clone()),
        validation,
        mutates_accepted_evidence_ledger: true,
        creates_official_submission: false,
        populates_score_axes: false,
        appended_claim_boundary: request.preflight_request.candidate.proposed_claim_boundary,
        appended_evidence_class: request
            .preflight_request
            .candidate
            .proposed_evidence_class
            .clone(),
        non_claims: request.preflight_request.non_claims.clone(),
    };
    let post_validation = ledger.validate();
    if !post_validation.valid {
        return Err(ZkBenchError::evidence_ledger(
            "accepted_ledger_append_transaction.post_validation",
            format!("ledger invalid after append: {:?}", post_validation.errors),
        ));
    }
    Ok(report)
}

/// Build the evidence record that would be appended by a valid transaction.
pub fn build_evidence_record_from_transaction(
    request: &AcceptedLedgerAppendTransactionRequest,
) -> Result<EvidenceRecord> {
    let candidate = &request.preflight_request.candidate;
    let artifact_digest = request
        .preflight_request
        .source_artifact_digests
        .first()
        .cloned()
        .ok_or_else(|| {
            ZkBenchError::evidence_ledger(
                "accepted_ledger_append_transaction.source_artifact_digests",
                "at least one source artifact digest is required",
            )
        })?;
    Ok(EvidenceRecord {
        evidence_class: candidate.proposed_evidence_class.clone(),
        claim_boundary: candidate.proposed_claim_boundary,
        provenance: ProvenanceRecord {
            source: format!("candidate:{}", candidate.id),
            captured_at: None,
            command: None,
            notes: candidate
                .proposed_provenance_summary
                .iter()
                .chain(request.preflight_request.external_replay_provenance.iter())
                .cloned()
                .collect(),
        },
        artifact_digest: Some(artifact_digest),
        notes: vec![
            format!(
                "accepted-ledger append transaction: {}",
                request.transaction_id
            ),
            format!(
                "source append preview: {}",
                request.preflight_request.append_preview.id
            ),
            "Official submission was not created.".to_string(),
            "Score axes were not populated.".to_string(),
        ],
        backend_target: None,
    })
}

fn validate_current_tip(
    request: &AcceptedLedgerAppendTransactionRequest,
    ledger: &EvidenceLedger,
    issues: &mut Vec<AcceptedLedgerAppendTransactionIssue>,
) {
    let current_tip = ledger
        .entries
        .last()
        .map(|entry| entry.entry_digest.clone());
    let preview_tip = &request
        .preflight_request
        .append_preview
        .transaction_preview
        .current_ledger_digest;
    for (path, expected) in [
        (
            "request.expected_current_ledger_tip",
            &request.expected_current_ledger_tip,
        ),
        (
            "request.preflight_request.expected_current_ledger_tip",
            &request.preflight_request.expected_current_ledger_tip,
        ),
        (
            "request.preflight_request.append_preview.transaction_preview.current_ledger_digest",
            preview_tip,
        ),
    ] {
        if expected != &current_tip {
            push_issue(
                issues,
                AcceptedLedgerAppendTransactionIssueKind::StaleLedgerTip,
                path,
                "expected ledger tip must match the current target ledger tip",
            );
        }
    }
}

fn validate_candidate_preview_alignment(
    request: &AcceptedLedgerAppendTransactionRequest,
    issues: &mut Vec<AcceptedLedgerAppendTransactionIssue>,
) {
    let candidate = &request.preflight_request.candidate;
    let preview = &request.preflight_request.append_preview;
    if preview.source_candidate_id != candidate.id {
        push_issue(
            issues,
            AcceptedLedgerAppendTransactionIssueKind::CandidatePreviewMismatch,
            "request.preflight_request.append_preview.source_candidate_id",
            "append preview source candidate must match the transaction candidate",
        );
    }
    if preview.proposed_append_entries.len() != 1 {
        push_issue(
            issues,
            AcceptedLedgerAppendTransactionIssueKind::CandidatePreviewMismatch,
            "request.preflight_request.append_preview.proposed_append_entries",
            "accepted-ledger append transaction requires exactly one candidate entry",
        );
        return;
    }
    let entry = &preview.proposed_append_entries[0];
    if entry.candidate_id != candidate.id {
        push_issue(
            issues,
            AcceptedLedgerAppendTransactionIssueKind::CandidatePreviewMismatch,
            "request.preflight_request.append_preview.proposed_append_entries[0].candidate_id",
            "append preview entry candidate id must match the transaction candidate",
        );
    }
    if entry.proposed_evidence_class != candidate.proposed_evidence_class {
        push_issue(
            issues,
            AcceptedLedgerAppendTransactionIssueKind::CandidatePreviewMismatch,
            "request.preflight_request.append_preview.proposed_append_entries[0].proposed_evidence_class",
            "append preview evidence class must match the candidate",
        );
    }
    if entry.proposed_claim_boundary != candidate.proposed_claim_boundary {
        push_issue(
            issues,
            AcceptedLedgerAppendTransactionIssueKind::CandidatePreviewMismatch,
            "request.preflight_request.append_preview.proposed_append_entries[0].proposed_claim_boundary",
            "append preview claim boundary must match the candidate",
        );
    }
    match compute_artifact_digest(
        candidate,
        Some(ArtifactKind::EvidenceLedger),
        Some(ArtifactRole::Evidence),
    ) {
        Ok(digest) if digest == entry.proposed_record_digest => {}
        Ok(_) => push_issue(
            issues,
            AcceptedLedgerAppendTransactionIssueKind::CandidateDigestMismatch,
            "request.preflight_request.append_preview.proposed_append_entries[0].proposed_record_digest",
            "append preview candidate digest does not match the supplied candidate",
        ),
        Err(error) => push_issue(
            issues,
            AcceptedLedgerAppendTransactionIssueKind::CandidateDigestMismatch,
            "request.preflight_request.candidate",
            error.to_string(),
        ),
    }
}

fn validate_local_append_boundary(
    request: &AcceptedLedgerAppendTransactionRequest,
    issues: &mut Vec<AcceptedLedgerAppendTransactionIssue>,
) {
    let candidate = &request.preflight_request.candidate;
    if candidate.proposed_claim_boundary > ClaimBoundary::Level1LocalReplay {
        push_issue(
            issues,
            AcceptedLedgerAppendTransactionIssueKind::ClaimBoundaryTooHigh,
            "request.preflight_request.candidate.proposed_claim_boundary",
            "accepted-ledger append transaction is limited to Level1LocalReplay or below",
        );
    }
    if matches!(
        candidate.proposed_evidence_class,
        EvidenceClass::ReproducibleBenchmarkArtifact
            | EvidenceClass::CrossBackendReplay
            | EvidenceClass::FormalPropertyStatement
            | EvidenceClass::MachineCheckedScopedProof
            | EvidenceClass::IndependentlyReproducedEvidence
    ) {
        push_issue(
            issues,
            AcceptedLedgerAppendTransactionIssueKind::ClaimBoundaryTooHigh,
            "request.preflight_request.candidate.proposed_evidence_class",
            "accepted-ledger append transaction cannot create Level2+ or formal evidence",
        );
    }
    if request
        .preflight_request
        .official_submission_package_requested
    {
        push_issue(
            issues,
            AcceptedLedgerAppendTransactionIssueKind::OfficialSubmissionAttempted,
            "request.preflight_request.official_submission_package_requested",
            "accepted-ledger append transaction must not create official submission metadata",
        );
    }
    if request.preflight_request.populates_score_axes {
        push_issue(
            issues,
            AcceptedLedgerAppendTransactionIssueKind::ScoreAxisPopulationAttempted,
            "request.preflight_request.populates_score_axes",
            "accepted-ledger append transaction must not populate score axes",
        );
    }
    if request.preflight_request.source_artifact_digests.is_empty() {
        push_issue(
            issues,
            AcceptedLedgerAppendTransactionIssueKind::MissingArtifactDigest,
            "request.preflight_request.source_artifact_digests",
            "accepted-ledger append transaction requires source artifact digests",
        );
    }
}

fn scan_transaction_text(
    request: &AcceptedLedgerAppendTransactionRequest,
    issues: &mut Vec<AcceptedLedgerAppendTransactionIssue>,
) {
    for (index, note) in request.notes.iter().enumerate() {
        if crate::external_runner::contains_forbidden_claim_text(note) {
            push_issue(
                issues,
                AcceptedLedgerAppendTransactionIssueKind::ForbiddenClaimText,
                format!("request.notes[{index}]"),
                "transaction note contains forbidden claim text",
            );
        }
    }
}

fn push_issue(
    issues: &mut Vec<AcceptedLedgerAppendTransactionIssue>,
    kind: AcceptedLedgerAppendTransactionIssueKind,
    path: impl Into<String>,
    message: impl Into<String>,
) {
    issues.push(AcceptedLedgerAppendTransactionIssue {
        kind,
        path: path.into(),
        message: message.into(),
    });
}
