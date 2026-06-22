//! Phase W reviewed promotion preflight metadata.
//!
//! These types make promotion and official-submission prerequisites explicit.
//! They do not append to `EvidenceLedger`, execute external replay, submit to an
//! official benchmark endpoint, or populate score axes.

use serde::{Deserialize, Serialize};

use crate::error::{Result, ZkBenchError};

use super::digest::compute_artifact_digest;
use super::{
    ArtifactDigest, ArtifactDigestAlgorithm, ArtifactKind, ArtifactRole, ClaimBoundary,
    EvidenceAppendPreview, EvidenceAppendPreviewStatus, EvidenceClass, EvidenceRecordCandidate,
    EvidenceReviewDecision, EvidenceReviewDecisionKind, EvidenceReviewDecisionStatus,
};

/// Phase W promotion preflight schema version.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ReviewedPromotionPreflightVersion {
    /// Logical version string.
    pub value: String,
}

impl Default for ReviewedPromotionPreflightVersion {
    fn default() -> Self {
        Self {
            value: "phase-w-reviewed-promotion-preflight-v0".to_string(),
        }
    }
}

/// Reviewed promotion preflight request.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ReviewedPromotionPreflightRequest {
    /// Request id.
    pub id: String,
    /// Schema version.
    pub version: ReviewedPromotionPreflightVersion,
    /// Reviewed evidence-record candidate.
    pub candidate: EvidenceRecordCandidate,
    /// Append preview for the candidate.
    pub append_preview: EvidenceAppendPreview,
    /// Human review decision that led to the candidate/preview.
    pub review_decision: EvidenceReviewDecision,
    /// Expected current ledger tip at preflight time.
    #[serde(default)]
    pub expected_current_ledger_tip: Option<ArtifactDigest>,
    /// Source artifact digests bound to this preflight.
    #[serde(default)]
    pub source_artifact_digests: Vec<ArtifactDigest>,
    /// External replay provenance declarations.
    #[serde(default)]
    pub external_replay_provenance: Vec<String>,
    /// Unresolved quarantine markers.
    #[serde(default)]
    pub unresolved_quarantine_markers: Vec<String>,
    /// Other blocking markers.
    #[serde(default)]
    pub blocking_markers: Vec<String>,
    /// Requested evidence class for the future promotion.
    pub requested_evidence_class: EvidenceClass,
    /// Requested claim boundary for the future promotion.
    pub requested_claim_boundary: ClaimBoundary,
    /// Whether this request tries to populate score axes.
    #[serde(default)]
    pub populates_score_axes: bool,
    /// Whether official submission package metadata is requested.
    #[serde(default)]
    pub official_submission_package_requested: bool,
    /// Accepted evidence ids available to the request.
    #[serde(default)]
    pub accepted_evidence_ledger_entry_ids: Vec<String>,
    /// Claim text and operator notes to scan.
    #[serde(default)]
    pub claim_text: Vec<String>,
    /// Required limitation labels carried by the request.
    #[serde(default)]
    pub non_claims: Vec<String>,
}

/// Phase W promotion preflight validation issue kind.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
pub enum ReviewedPromotionPreflightIssueKind {
    /// Required id or text was empty.
    EmptyIdentity,
    /// Candidate validation failed.
    InvalidCandidate,
    /// Append preview validation failed.
    InvalidAppendPreview,
    /// Candidate and append preview disagree.
    CandidatePreviewMismatch,
    /// Append preview tried to mutate the ledger.
    AppendPreviewMutatesLedger,
    /// Ledger tip was stale or mismatched.
    StaleAppendPreview,
    /// Human review approval was missing.
    MissingHumanReviewApproval,
    /// Source artifact digest was missing or malformed.
    MissingSourceArtifactDigest,
    /// Quarantine or blocking marker is unresolved.
    UnresolvedBlockingMarker,
    /// External replay provenance is missing.
    MissingExternalReplayProvenance,
    /// Local-only evidence was promoted beyond its boundary.
    LocalOnlyEvidencePromotion,
    /// Local soak telemetry was treated as performance evidence.
    LocalSoakTelemetryPerformancePromotion,
    /// Forbidden claim text was detected.
    ForbiddenClaimText,
    /// Score axes were populated without matching evidence.
    ScoreAxisPopulationWithoutEvidenceClass,
    /// Required non-claim label was missing.
    MissingRequiredNonClaim,
    /// Official submission metadata was requested before accepted evidence.
    OfficialSubmissionBeforeAcceptedEvidence,
}

/// Phase W promotion preflight validation issue.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ReviewedPromotionPreflightIssue {
    /// Issue kind.
    pub kind: ReviewedPromotionPreflightIssueKind,
    /// Issue path.
    pub path: String,
    /// Human-readable message.
    pub message: String,
}

/// Phase W promotion preflight validation.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ReviewedPromotionPreflightValidation {
    /// Whether the request/report is valid metadata.
    pub valid: bool,
    /// Validation issues.
    #[serde(default)]
    pub issues: Vec<ReviewedPromotionPreflightIssue>,
}

/// Source summary included in a preflight report.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ReviewedPromotionSourceSummary {
    /// Candidate id.
    pub candidate_id: String,
    /// Append preview id.
    pub append_preview_id: String,
    /// Review decision id.
    pub review_decision_id: String,
    /// Requested evidence class.
    pub requested_evidence_class: EvidenceClass,
    /// Requested claim boundary.
    pub requested_claim_boundary: ClaimBoundary,
    /// Current ledger tip from the append preview.
    #[serde(default)]
    pub preview_current_ledger_tip: Option<ArtifactDigest>,
    /// Expected current ledger tip supplied by the caller.
    #[serde(default)]
    pub expected_current_ledger_tip: Option<ArtifactDigest>,
    /// Source artifact digest count.
    pub source_artifact_digest_count: usize,
    /// External replay provenance count.
    pub external_replay_provenance_count: usize,
    /// Accepted evidence id count.
    pub accepted_evidence_id_count: usize,
}

/// Phase W reviewed promotion preflight report.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ReviewedPromotionPreflightReport {
    /// Report id.
    pub report_id: String,
    /// Schema version.
    pub version: ReviewedPromotionPreflightVersion,
    /// Source summary.
    pub source_summary: ReviewedPromotionSourceSummary,
    /// Validation report.
    pub validation: ReviewedPromotionPreflightValidation,
    /// Preflight reports never mutate accepted ledgers.
    pub mutates_accepted_evidence_ledger: bool,
    /// Preflight reports never create official submissions.
    pub creates_official_submission: bool,
    /// Preflight reports never populate score axes.
    pub populates_score_axes: bool,
    /// Preflight report claim boundary.
    pub claim_boundary: ClaimBoundary,
    /// Required non-claim labels.
    pub non_claims: Vec<String>,
}

/// Official-submission package metadata version.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct OfficialSubmissionPackageVersion {
    /// Logical version string.
    pub value: String,
}

impl Default for OfficialSubmissionPackageVersion {
    fn default() -> Self {
        Self {
            value: "phase-w-official-submission-package-metadata-v0".to_string(),
        }
    }
}

/// Official-submission package metadata validation issue kind.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
pub enum OfficialSubmissionPackageIssueKind {
    /// Required field was empty.
    EmptyIdentity,
    /// Accepted evidence id was missing.
    MissingAcceptedEvidence,
    /// Artifact digest was missing or malformed.
    MissingArtifactDigest,
    /// External replay provenance was missing.
    MissingExternalReplayProvenance,
    /// Required non-claim label was missing.
    MissingRequiredNonClaim,
    /// Forbidden claim text was detected.
    ForbiddenClaimText,
    /// Metadata attempted to submit externally.
    ExternalSubmissionAttempted,
}

/// Official-submission package metadata validation issue.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct OfficialSubmissionPackageIssue {
    /// Issue kind.
    pub kind: OfficialSubmissionPackageIssueKind,
    /// Issue path.
    pub path: String,
    /// Human-readable message.
    pub message: String,
}

/// Official-submission package metadata validation.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct OfficialSubmissionPackageValidation {
    /// Whether the metadata is valid.
    pub valid: bool,
    /// Validation issues.
    #[serde(default)]
    pub issues: Vec<OfficialSubmissionPackageIssue>,
}

/// Inert official-submission package metadata.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct OfficialSubmissionPackageMetadata {
    /// Package id.
    pub package_id: String,
    /// Schema version.
    pub version: OfficialSubmissionPackageVersion,
    /// Benchmark suite id.
    pub benchmark_suite_id: String,
    /// Backend id.
    pub backend_id: String,
    /// Backend version.
    pub backend_version: String,
    /// Source pack ids.
    #[serde(default)]
    pub source_pack_ids: Vec<String>,
    /// External replay environment provenance.
    #[serde(default)]
    pub external_replay_environment_provenance: Vec<String>,
    /// Artifact digests bound to the package metadata.
    #[serde(default)]
    pub artifact_digests: Vec<ArtifactDigest>,
    /// Accepted Evidence Ledger entry ids.
    #[serde(default)]
    pub accepted_evidence_ledger_entry_ids: Vec<String>,
    /// Review decision ids.
    #[serde(default)]
    pub review_decision_ids: Vec<String>,
    /// Claim boundary.
    pub claim_boundary: ClaimBoundary,
    /// Non-claim labels.
    #[serde(default)]
    pub non_claims: Vec<String>,
    /// Reproduction instructions.
    #[serde(default)]
    pub reproduction_instructions: Vec<String>,
    /// Known limitations.
    #[serde(default)]
    pub known_limitations: Vec<String>,
    /// Must remain false in this metadata-only slice.
    #[serde(default)]
    pub submits_to_official_endpoint: bool,
}

/// Required Phase W promotion preflight non-claim labels.
pub fn required_reviewed_promotion_preflight_non_claims() -> Vec<&'static str> {
    vec![
        "Promotion preflight reports are not accepted evidence.",
        "Promotion preflight reports do not mutate EvidenceLedger.",
        "Local artifact campaigns are not accepted Evidence Ledger entries.",
        "Append previews are not accepted evidence.",
        "Evidence-record candidates are not accepted evidence.",
        "Local replay artifacts are not official benchmark evidence.",
        "Internal timing telemetry is not ZK backend performance.",
        "Official submission requires a separate external submission operation.",
        "Accepted evidence is scoped to the reviewed claim only.",
    ]
}

/// Build a reviewed promotion preflight report without mutating any ledger.
pub fn build_reviewed_promotion_preflight_report(
    request: &ReviewedPromotionPreflightRequest,
) -> ReviewedPromotionPreflightReport {
    ReviewedPromotionPreflightReport {
        report_id: format!("promotion_preflight_report_{}", request.id),
        version: ReviewedPromotionPreflightVersion::default(),
        source_summary: ReviewedPromotionSourceSummary {
            candidate_id: request.candidate.id.clone(),
            append_preview_id: request.append_preview.id.clone(),
            review_decision_id: request.review_decision.id.clone(),
            requested_evidence_class: request.requested_evidence_class.clone(),
            requested_claim_boundary: request.requested_claim_boundary,
            preview_current_ledger_tip: request
                .append_preview
                .transaction_preview
                .current_ledger_digest
                .clone(),
            expected_current_ledger_tip: request.expected_current_ledger_tip.clone(),
            source_artifact_digest_count: request.source_artifact_digests.len(),
            external_replay_provenance_count: request.external_replay_provenance.len(),
            accepted_evidence_id_count: request.accepted_evidence_ledger_entry_ids.len(),
        },
        validation: validate_reviewed_promotion_preflight_request(request),
        mutates_accepted_evidence_ledger: false,
        creates_official_submission: false,
        populates_score_axes: false,
        claim_boundary: ClaimBoundary::Level0DesignNote,
        non_claims: required_reviewed_promotion_preflight_non_claims()
            .into_iter()
            .map(str::to_string)
            .collect(),
    }
}

/// Validate a reviewed promotion preflight request.
pub fn validate_reviewed_promotion_preflight_request(
    request: &ReviewedPromotionPreflightRequest,
) -> ReviewedPromotionPreflightValidation {
    let mut issues = Vec::new();
    if request.id.trim().is_empty() {
        push_issue(
            &mut issues,
            ReviewedPromotionPreflightIssueKind::EmptyIdentity,
            "request.id",
            "preflight request id must be non-empty",
        );
    }

    let candidate_validation = super::validate_evidence_record_candidate(&request.candidate);
    if !candidate_validation.valid {
        push_issue(
            &mut issues,
            ReviewedPromotionPreflightIssueKind::InvalidCandidate,
            "request.candidate",
            format!(
                "candidate validation failed: {:?}",
                candidate_validation.issues
            ),
        );
    }
    let preview_validation = super::validate_evidence_append_preview(&request.append_preview);
    if !preview_validation.valid {
        push_issue(
            &mut issues,
            ReviewedPromotionPreflightIssueKind::InvalidAppendPreview,
            "request.append_preview",
            format!(
                "append preview validation failed: {:?}",
                preview_validation.issues
            ),
        );
    }
    if request.append_preview.mutates_ledger() || request.append_preview.mutates_evidence_ledger {
        push_issue(
            &mut issues,
            ReviewedPromotionPreflightIssueKind::AppendPreviewMutatesLedger,
            "request.append_preview.mutates_evidence_ledger",
            "append previews must not mutate EvidenceLedger",
        );
    }
    if request.append_preview.source_candidate_id != request.candidate.id {
        push_issue(
            &mut issues,
            ReviewedPromotionPreflightIssueKind::CandidatePreviewMismatch,
            "request.append_preview.source_candidate_id",
            "append preview source candidate must match the reviewed candidate",
        );
    }
    if request.append_preview.status != EvidenceAppendPreviewStatus::PreviewOnly {
        push_issue(
            &mut issues,
            ReviewedPromotionPreflightIssueKind::InvalidAppendPreview,
            "request.append_preview.status",
            "append preview must be PreviewOnly",
        );
    }
    if request.expected_current_ledger_tip
        != request
            .append_preview
            .transaction_preview
            .current_ledger_digest
    {
        push_issue(
            &mut issues,
            ReviewedPromotionPreflightIssueKind::StaleAppendPreview,
            "request.expected_current_ledger_tip",
            "expected ledger tip must match the append preview current ledger digest",
        );
    }
    validate_review_decision(request, &mut issues);
    validate_source_digests(
        &mut issues,
        "request.source_artifact_digests",
        &request.source_artifact_digests,
    );
    validate_required_non_claims(&mut issues, &request.non_claims);

    for (index, marker) in request.unresolved_quarantine_markers.iter().enumerate() {
        push_issue(
            &mut issues,
            ReviewedPromotionPreflightIssueKind::UnresolvedBlockingMarker,
            format!("request.unresolved_quarantine_markers[{index}]"),
            format!("unresolved quarantine marker blocks promotion: {marker}"),
        );
    }
    for (index, marker) in request.blocking_markers.iter().enumerate() {
        push_issue(
            &mut issues,
            ReviewedPromotionPreflightIssueKind::UnresolvedBlockingMarker,
            format!("request.blocking_markers[{index}]"),
            format!("blocking marker blocks promotion: {marker}"),
        );
    }
    if request.requested_claim_boundary >= ClaimBoundary::Level2ReproducibleBenchmarkArtifact
        && request.external_replay_provenance.is_empty()
    {
        push_issue(
            &mut issues,
            ReviewedPromotionPreflightIssueKind::MissingExternalReplayProvenance,
            "request.external_replay_provenance",
            "Level2+ promotion requires external replay provenance",
        );
    }
    if request.requested_claim_boundary > request.candidate.proposed_claim_boundary
        && request.candidate.proposed_claim_boundary <= ClaimBoundary::Level1LocalReplay
    {
        push_issue(
            &mut issues,
            ReviewedPromotionPreflightIssueKind::LocalOnlyEvidencePromotion,
            "request.requested_claim_boundary",
            "local-only candidate metadata cannot be promoted above its reviewed boundary",
        );
    }
    if request.populates_score_axes
        && (request.requested_claim_boundary < ClaimBoundary::Level2ReproducibleBenchmarkArtifact
            || matches!(
                request.requested_evidence_class,
                EvidenceClass::DesignNote | EvidenceClass::LocalReplay
            ))
    {
        push_issue(
            &mut issues,
            ReviewedPromotionPreflightIssueKind::ScoreAxisPopulationWithoutEvidenceClass,
            "request.populates_score_axes",
            "score axes require matching accepted external/reproducible evidence",
        );
    }
    if request.official_submission_package_requested
        && request.accepted_evidence_ledger_entry_ids.is_empty()
    {
        push_issue(
            &mut issues,
            ReviewedPromotionPreflightIssueKind::OfficialSubmissionBeforeAcceptedEvidence,
            "request.accepted_evidence_ledger_entry_ids",
            "official submission package metadata requires accepted evidence ids",
        );
    }
    scan_preflight_text(request, &mut issues);

    ReviewedPromotionPreflightValidation {
        valid: issues.is_empty(),
        issues,
    }
}

/// Serialize a reviewed promotion preflight report as deterministic pretty JSON.
pub fn serialize_reviewed_promotion_preflight_report_json(
    report: &ReviewedPromotionPreflightReport,
) -> Result<String> {
    serde_json::to_string_pretty(report).map_err(|error| {
        ZkBenchError::serialization(
            "serialize_reviewed_promotion_preflight_report_json",
            error.to_string(),
        )
    })
}

/// Deserialize a reviewed promotion preflight report from JSON.
pub fn deserialize_reviewed_promotion_preflight_report_json(
    json: &str,
) -> Result<ReviewedPromotionPreflightReport> {
    serde_json::from_str(json).map_err(|error| {
        ZkBenchError::deserialization(
            "deserialize_reviewed_promotion_preflight_report_json",
            error.to_string(),
        )
    })
}

/// Compute a deterministic digest for a promotion preflight report.
pub fn compute_reviewed_promotion_preflight_report_digest(
    report: &ReviewedPromotionPreflightReport,
) -> Result<ArtifactDigest> {
    compute_artifact_digest(
        report,
        Some(ArtifactKind::Other),
        Some(ArtifactRole::Report),
    )
}

/// Render deterministic Markdown for a reviewed promotion preflight report.
pub fn render_reviewed_promotion_preflight_markdown(
    report: &ReviewedPromotionPreflightReport,
) -> Result<String> {
    if missing_required_non_claims(&report.non_claims)
        .next()
        .is_some()
    {
        return Err(ZkBenchError::validation(
            "reviewed_promotion_preflight.non_claims",
            "preflight report is missing required non-claim labels",
        ));
    }

    let mut markdown = String::new();
    markdown.push_str("# Reviewed Promotion Preflight\n\n");
    markdown.push_str("Status: metadata-only preflight.\n\n");
    markdown.push_str("## Claim Boundary\n\n");
    markdown.push_str(&format!(
        "- Report claim boundary: `{}`\n",
        report.claim_boundary
    ));
    markdown.push_str("- Accepted Evidence Ledger mutation: `false`\n");
    markdown.push_str("- Official submission created: `false`\n");
    markdown.push_str("- Score axes populated: `false`\n\n");

    markdown.push_str("## Source Summary\n\n");
    markdown.push_str(&format!(
        "- Candidate: `{}`\n",
        report.source_summary.candidate_id
    ));
    markdown.push_str(&format!(
        "- Append preview: `{}`\n",
        report.source_summary.append_preview_id
    ));
    markdown.push_str(&format!(
        "- Review decision: `{}`\n",
        report.source_summary.review_decision_id
    ));
    markdown.push_str(&format!(
        "- Requested evidence class: `{:?}`\n",
        report.source_summary.requested_evidence_class
    ));
    markdown.push_str(&format!(
        "- Requested claim boundary: `{}`\n",
        report.source_summary.requested_claim_boundary
    ));
    markdown.push_str(&format!(
        "- Source artifact digests: `{}`\n",
        report.source_summary.source_artifact_digest_count
    ));
    markdown.push_str(&format!(
        "- External replay provenance records: `{}`\n",
        report.source_summary.external_replay_provenance_count
    ));
    markdown.push_str(&format!(
        "- Accepted evidence ids: `{}`\n\n",
        report.source_summary.accepted_evidence_id_count
    ));

    markdown.push_str("## Validation\n\n");
    markdown.push_str(&format!("- Valid: `{}`\n", report.validation.valid));
    for issue in &report.validation.issues {
        markdown.push_str(&format!(
            "- `{:?}` at `{}`: {}\n",
            issue.kind, issue.path, issue.message
        ));
    }

    markdown.push_str("\n## Required Non-Claims\n\n");
    for non_claim in &report.non_claims {
        markdown.push_str("- ");
        markdown.push_str(non_claim);
        markdown.push('\n');
    }
    Ok(markdown)
}

/// Validate inert official-submission package metadata.
pub fn validate_official_submission_package_metadata(
    package: &OfficialSubmissionPackageMetadata,
) -> OfficialSubmissionPackageValidation {
    let mut issues = Vec::new();
    for (path, value) in [
        ("package.package_id", package.package_id.as_str()),
        (
            "package.benchmark_suite_id",
            package.benchmark_suite_id.as_str(),
        ),
        ("package.backend_id", package.backend_id.as_str()),
        ("package.backend_version", package.backend_version.as_str()),
    ] {
        if value.trim().is_empty() {
            push_submission_issue(
                &mut issues,
                OfficialSubmissionPackageIssueKind::EmptyIdentity,
                path,
                "required identity field must be non-empty",
            );
        }
    }
    if package.source_pack_ids.is_empty() {
        push_submission_issue(
            &mut issues,
            OfficialSubmissionPackageIssueKind::EmptyIdentity,
            "package.source_pack_ids",
            "at least one source pack id is required",
        );
    }
    if package.accepted_evidence_ledger_entry_ids.is_empty() {
        push_submission_issue(
            &mut issues,
            OfficialSubmissionPackageIssueKind::MissingAcceptedEvidence,
            "package.accepted_evidence_ledger_entry_ids",
            "official submission metadata requires accepted evidence ids",
        );
    }
    if package.external_replay_environment_provenance.is_empty() {
        push_submission_issue(
            &mut issues,
            OfficialSubmissionPackageIssueKind::MissingExternalReplayProvenance,
            "package.external_replay_environment_provenance",
            "official submission metadata requires external replay provenance",
        );
    }
    validate_submission_digests(&mut issues, &package.artifact_digests);
    validate_submission_non_claims(&mut issues, &package.non_claims);
    if package.submits_to_official_endpoint {
        push_submission_issue(
            &mut issues,
            OfficialSubmissionPackageIssueKind::ExternalSubmissionAttempted,
            "package.submits_to_official_endpoint",
            "metadata-only package must not submit to an official endpoint",
        );
    }
    scan_submission_text(package, &mut issues);

    OfficialSubmissionPackageValidation {
        valid: issues.is_empty(),
        issues,
    }
}

/// Serialize official-submission package metadata as deterministic pretty JSON.
pub fn serialize_official_submission_package_metadata_json(
    package: &OfficialSubmissionPackageMetadata,
) -> Result<String> {
    serde_json::to_string_pretty(package).map_err(|error| {
        ZkBenchError::serialization(
            "serialize_official_submission_package_metadata_json",
            error.to_string(),
        )
    })
}

/// Deserialize official-submission package metadata from JSON.
pub fn deserialize_official_submission_package_metadata_json(
    json: &str,
) -> Result<OfficialSubmissionPackageMetadata> {
    serde_json::from_str(json).map_err(|error| {
        ZkBenchError::deserialization(
            "deserialize_official_submission_package_metadata_json",
            error.to_string(),
        )
    })
}

/// Compute a deterministic digest for official-submission package metadata.
pub fn compute_official_submission_package_metadata_digest(
    package: &OfficialSubmissionPackageMetadata,
) -> Result<ArtifactDigest> {
    compute_artifact_digest(
        package,
        Some(ArtifactKind::Other),
        Some(ArtifactRole::Report),
    )
}

/// Render deterministic Markdown for official-submission package metadata.
pub fn render_official_submission_package_markdown(
    package: &OfficialSubmissionPackageMetadata,
) -> Result<String> {
    let validation = validate_official_submission_package_metadata(package);
    if !validation.valid {
        return Err(ZkBenchError::validation(
            "official_submission_package",
            format!(
                "official-submission package metadata is invalid: {:?}",
                validation.issues
            ),
        ));
    }

    let mut markdown = String::new();
    markdown.push_str("# Official Submission Package Metadata\n\n");
    markdown.push_str("Status: metadata only; no external submission performed.\n\n");
    markdown.push_str(&format!("- Package id: `{}`\n", package.package_id));
    markdown.push_str(&format!(
        "- Benchmark suite id: `{}`\n",
        package.benchmark_suite_id
    ));
    markdown.push_str(&format!("- Backend id: `{}`\n", package.backend_id));
    markdown.push_str(&format!(
        "- Backend version: `{}`\n",
        package.backend_version
    ));
    markdown.push_str(&format!("- Claim boundary: `{}`\n", package.claim_boundary));
    markdown.push_str("- Submitted to official endpoint: `false`\n\n");

    markdown.push_str("## Accepted Evidence\n\n");
    for id in &package.accepted_evidence_ledger_entry_ids {
        markdown.push_str("- `");
        markdown.push_str(id);
        markdown.push_str("`\n");
    }

    markdown.push_str("\n## Required Non-Claims\n\n");
    for non_claim in &package.non_claims {
        markdown.push_str("- ");
        markdown.push_str(non_claim);
        markdown.push('\n');
    }
    Ok(markdown)
}

fn validate_review_decision(
    request: &ReviewedPromotionPreflightRequest,
    issues: &mut Vec<ReviewedPromotionPreflightIssue>,
) {
    if request.review_decision.id != request.candidate.source.review_decision_id {
        push_issue(
            issues,
            ReviewedPromotionPreflightIssueKind::MissingHumanReviewApproval,
            "request.review_decision.id",
            "review decision id must match candidate source review decision id",
        );
    }
    if request.review_decision.source_proposal_id != request.candidate.source.source_proposal_id {
        push_issue(
            issues,
            ReviewedPromotionPreflightIssueKind::MissingHumanReviewApproval,
            "request.review_decision.source_proposal_id",
            "review decision source proposal must match candidate source proposal",
        );
    }
    if !request.review_decision.reviewer_role.is_human_review_role() {
        push_issue(
            issues,
            ReviewedPromotionPreflightIssueKind::MissingHumanReviewApproval,
            "request.review_decision.reviewer_role",
            "promotion preflight requires a human review role",
        );
    }
    if !matches!(
        request.review_decision.decision_kind,
        EvidenceReviewDecisionKind::ApproveForCandidateOnly
            | EvidenceReviewDecisionKind::ApproveForFutureAppendPreview
    ) {
        push_issue(
            issues,
            ReviewedPromotionPreflightIssueKind::MissingHumanReviewApproval,
            "request.review_decision.decision_kind",
            "promotion preflight requires a positive review decision",
        );
    }
    if !matches!(
        request.review_decision.decision_status,
        EvidenceReviewDecisionStatus::FinalizedCandidateOnly
    ) {
        push_issue(
            issues,
            ReviewedPromotionPreflightIssueKind::MissingHumanReviewApproval,
            "request.review_decision.decision_status",
            "promotion preflight requires a finalized candidate-only decision",
        );
    }
}

fn validate_source_digests(
    issues: &mut Vec<ReviewedPromotionPreflightIssue>,
    path: &str,
    digests: &[ArtifactDigest],
) {
    if digests.is_empty() {
        push_issue(
            issues,
            ReviewedPromotionPreflightIssueKind::MissingSourceArtifactDigest,
            path,
            "at least one source artifact digest is required",
        );
    }
    for (index, digest) in digests.iter().enumerate() {
        if !digest_is_sha256(digest) {
            push_issue(
                issues,
                ReviewedPromotionPreflightIssueKind::MissingSourceArtifactDigest,
                format!("{path}[{index}]"),
                "source artifact digest must be a non-empty sha256 digest",
            );
        }
    }
}

fn validate_submission_digests(
    issues: &mut Vec<OfficialSubmissionPackageIssue>,
    digests: &[ArtifactDigest],
) {
    if digests.is_empty() {
        push_submission_issue(
            issues,
            OfficialSubmissionPackageIssueKind::MissingArtifactDigest,
            "package.artifact_digests",
            "at least one artifact digest is required",
        );
    }
    for (index, digest) in digests.iter().enumerate() {
        if !digest_is_sha256(digest) {
            push_submission_issue(
                issues,
                OfficialSubmissionPackageIssueKind::MissingArtifactDigest,
                format!("package.artifact_digests[{index}]"),
                "artifact digest must be a non-empty sha256 digest",
            );
        }
    }
}

fn digest_is_sha256(digest: &ArtifactDigest) -> bool {
    digest.algorithm == ArtifactDigestAlgorithm::Sha256
        && digest.hex_digest.len() == 64
        && digest.hex_digest.chars().all(|ch| ch.is_ascii_hexdigit())
        && digest.byte_len > 0
}

fn validate_required_non_claims(
    issues: &mut Vec<ReviewedPromotionPreflightIssue>,
    non_claims: &[String],
) {
    for missing in missing_required_non_claims(non_claims) {
        push_issue(
            issues,
            ReviewedPromotionPreflightIssueKind::MissingRequiredNonClaim,
            "request.non_claims",
            format!("missing required non-claim: {missing}"),
        );
    }
}

fn validate_submission_non_claims(
    issues: &mut Vec<OfficialSubmissionPackageIssue>,
    non_claims: &[String],
) {
    for missing in missing_required_non_claims(non_claims) {
        push_submission_issue(
            issues,
            OfficialSubmissionPackageIssueKind::MissingRequiredNonClaim,
            "package.non_claims",
            format!("missing required non-claim: {missing}"),
        );
    }
}

fn missing_required_non_claims(non_claims: &[String]) -> impl Iterator<Item = &'static str> + '_ {
    required_reviewed_promotion_preflight_non_claims()
        .into_iter()
        .filter(|required| !non_claims.iter().any(|non_claim| non_claim == required))
}

fn scan_preflight_text(
    request: &ReviewedPromotionPreflightRequest,
    issues: &mut Vec<ReviewedPromotionPreflightIssue>,
) {
    for (index, text) in request.claim_text.iter().enumerate() {
        if text_contains_forbidden_claim(text) {
            push_issue(
                issues,
                ReviewedPromotionPreflightIssueKind::ForbiddenClaimText,
                format!("request.claim_text[{index}]"),
                "forbidden claim text blocks promotion preflight",
            );
        }
        if text_contains_local_soak_performance_claim(text) {
            push_issue(
                issues,
                ReviewedPromotionPreflightIssueKind::LocalSoakTelemetryPerformancePromotion,
                format!("request.claim_text[{index}]"),
                "local soak telemetry cannot be promoted as ZK backend performance evidence",
            );
        }
    }
    for (index, provenance) in request.external_replay_provenance.iter().enumerate() {
        if text_contains_forbidden_claim(provenance) {
            push_issue(
                issues,
                ReviewedPromotionPreflightIssueKind::ForbiddenClaimText,
                format!("request.external_replay_provenance[{index}]"),
                "forbidden claim text blocks promotion preflight",
            );
        }
    }
}

fn scan_submission_text(
    package: &OfficialSubmissionPackageMetadata,
    issues: &mut Vec<OfficialSubmissionPackageIssue>,
) {
    for (section, values) in [
        (
            "package.reproduction_instructions",
            &package.reproduction_instructions,
        ),
        ("package.known_limitations", &package.known_limitations),
        (
            "package.external_replay_environment_provenance",
            &package.external_replay_environment_provenance,
        ),
    ] {
        for (index, text) in values.iter().enumerate() {
            if text_contains_forbidden_claim(text) {
                push_submission_issue(
                    issues,
                    OfficialSubmissionPackageIssueKind::ForbiddenClaimText,
                    format!("{section}[{index}]"),
                    "forbidden claim text blocks official-submission package metadata",
                );
            }
        }
    }
}

fn text_contains_forbidden_claim(text: &str) -> bool {
    crate::external_runner::contains_official_claim_text(text)
        || crate::external_runner::contains_formal_claim_text(text)
        || crate::external_runner::contains_soundness_claim_text(text)
        || text_contains_broad_leaderboard_claim(text)
}

fn text_contains_broad_leaderboard_claim(text: &str) -> bool {
    let lowered = text.to_ascii_lowercase();
    lowered.contains("leaderboard") || lowered.contains("ranking")
}

fn text_contains_local_soak_performance_claim(text: &str) -> bool {
    let lowered = text.to_ascii_lowercase();
    lowered.contains("local soak")
        && lowered.contains("zk backend")
        && lowered.contains("performance")
}

fn push_issue(
    issues: &mut Vec<ReviewedPromotionPreflightIssue>,
    kind: ReviewedPromotionPreflightIssueKind,
    path: impl Into<String>,
    message: impl Into<String>,
) {
    issues.push(ReviewedPromotionPreflightIssue {
        kind,
        path: path.into(),
        message: message.into(),
    });
}

fn push_submission_issue(
    issues: &mut Vec<OfficialSubmissionPackageIssue>,
    kind: OfficialSubmissionPackageIssueKind,
    path: impl Into<String>,
    message: impl Into<String>,
) {
    issues.push(OfficialSubmissionPackageIssue {
        kind,
        path: path.into(),
        message: message.into(),
    });
}
