//! Local external replay and official-submission promotion preflight.
//!
//! This module validates local readiness metadata before any future external
//! replay or official-submission operation. It never runs external replay,
//! calls an endpoint, reads credentials, mutates accepted ledgers, writes
//! generated artifacts, or populates score axes.

use std::collections::BTreeSet;
use std::fs;
use std::path::{Component, Path, PathBuf};

use serde::{Deserialize, Serialize};

use crate::error::{Result, ZkBenchError};

use super::{
    compute_artifact_digest, read_official_submission_package_outputs, ArtifactDigest,
    ArtifactDigestAlgorithm, ArtifactKind, ArtifactRole, ClaimBoundary, EvidenceClass,
    EvidenceLedger, OfficialSubmissionPackageOutput,
};

/// Phase W external replay / official-submission preflight schema version.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ExternalReplaySubmissionPreflightVersion {
    /// Logical version string.
    pub value: String,
}

impl Default for ExternalReplaySubmissionPreflightVersion {
    fn default() -> Self {
        Self {
            value: "phase-w-external-replay-submission-preflight-v0".to_string(),
        }
    }
}

/// Non-secret benchmark target metadata for future external replay.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ExternalReplayBenchmarkTarget {
    /// Benchmark suite id.
    pub benchmark_suite_id: String,
    /// Backend id.
    pub backend_id: String,
    /// Backend version.
    pub backend_version: String,
    /// Target label selected by the operator.
    pub target_label: String,
}

/// Local preflight request for a future external replay or official submission.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ExternalReplaySubmissionPreflightRequest {
    /// Request id.
    pub id: String,
    /// Schema version.
    pub version: ExternalReplaySubmissionPreflightVersion,
    /// Existing accepted Evidence Ledger JSON path.
    pub accepted_ledger_path: PathBuf,
    /// Existing Phase 121 package output root.
    pub package_output_root: PathBuf,
    /// Expected package metadata digest from the operator.
    pub expected_package_metadata_digest: ArtifactDigest,
    /// Expected validation report digest from the operator.
    pub expected_validation_report_digest: ArtifactDigest,
    /// Non-secret benchmark target.
    pub benchmark_target: ExternalReplayBenchmarkTarget,
    /// External replay provenance declarations.
    #[serde(default)]
    pub external_replay_provenance: Vec<String>,
    /// Source artifact digests bound to this preflight.
    #[serde(default)]
    pub source_artifact_digests: Vec<ArtifactDigest>,
    /// Explicit operator acknowledgement for future live replay/submission.
    pub operator_acknowledged: bool,
    /// Future generated-output root, validated but not written.
    pub future_output_root: PathBuf,
    /// Protected paths the future output root must not overlap.
    #[serde(default)]
    pub protected_paths: Vec<PathBuf>,
    /// Whether a future non-empty output root is intentionally overwritten.
    pub overwrite: bool,
    /// Redaction policy notes for future generated outputs.
    #[serde(default)]
    pub redaction_policy: Vec<String>,
    /// Requested evidence class for the future operation.
    pub requested_evidence_class: EvidenceClass,
    /// Requested claim boundary for the future operation.
    pub requested_claim_boundary: ClaimBoundary,
    /// Whether this request tries to populate score axes.
    #[serde(default)]
    pub populates_score_axes: bool,
    /// Whether this request tries to submit to an official endpoint now.
    #[serde(default)]
    pub official_endpoint_submission_requested: bool,
    /// Unresolved quarantine markers.
    #[serde(default)]
    pub unresolved_quarantine_markers: Vec<String>,
    /// Other blocking review markers.
    #[serde(default)]
    pub blocking_markers: Vec<String>,
    /// Claim text and operator notes to scan.
    #[serde(default)]
    pub claim_text: Vec<String>,
    /// Required limitation labels carried by the request.
    #[serde(default)]
    pub non_claims: Vec<String>,
}

/// Phase W external replay / official-submission preflight issue kind.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
pub enum ExternalReplaySubmissionPreflightIssueKind {
    /// Required id or text was empty.
    EmptyIdentity,
    /// Operator acknowledgement was missing.
    MissingOperatorAcknowledgement,
    /// Accepted ledger was missing or invalid.
    InvalidAcceptedLedger,
    /// Package output was missing or invalid.
    InvalidPackageOutput,
    /// Package digest did not match the operator expectation.
    PackageDigestMismatch,
    /// Future output root was unsafe.
    UnsafeOutputRoot,
    /// External replay provenance was missing.
    MissingExternalReplayProvenance,
    /// Source artifact digest was missing.
    MissingSourceArtifactDigest,
    /// Redaction policy was missing.
    MissingRedactionPolicy,
    /// Quarantine or blocking marker is unresolved.
    UnresolvedBlockingMarker,
    /// Local-only evidence was promoted beyond its boundary.
    LocalOnlyEvidencePromotion,
    /// Unsupported evidence class was requested.
    UnsupportedEvidenceClass,
    /// Score axes were populated without matching evidence.
    ScoreAxisPopulationWithoutEvidenceClass,
    /// Endpoint submission was requested in this local preflight.
    EndpointSubmissionAttempt,
    /// Required non-claim label was missing.
    MissingRequiredNonClaim,
    /// Forbidden claim text was detected.
    ForbiddenClaimText,
}

/// Phase W external replay / official-submission preflight issue.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ExternalReplaySubmissionPreflightIssue {
    /// Issue kind.
    pub kind: ExternalReplaySubmissionPreflightIssueKind,
    /// Issue path.
    pub path: String,
    /// Human-readable message.
    pub message: String,
}

/// Phase W external replay / official-submission preflight validation.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ExternalReplaySubmissionPreflightValidation {
    /// Whether the preflight is valid local metadata.
    pub valid: bool,
    /// Validation issues.
    #[serde(default)]
    pub issues: Vec<ExternalReplaySubmissionPreflightIssue>,
}

/// Source summary included in a preflight report.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ExternalReplaySubmissionSourceSummary {
    /// Request id.
    pub request_id: String,
    /// Accepted ledger path.
    pub accepted_ledger_path: PathBuf,
    /// Package output root.
    pub package_output_root: PathBuf,
    /// Future output root.
    pub future_output_root: PathBuf,
    /// Accepted ledger entry count.
    pub accepted_ledger_entry_count: usize,
    /// Package id from the Phase 121 validation report.
    pub package_id: String,
    /// Matched accepted evidence id count.
    pub matched_accepted_evidence_id_count: usize,
    /// External replay provenance count.
    pub external_replay_provenance_count: usize,
    /// Source artifact digest count.
    pub source_artifact_digest_count: usize,
    /// Requested evidence class.
    pub requested_evidence_class: EvidenceClass,
    /// Requested claim boundary.
    pub requested_claim_boundary: ClaimBoundary,
}

/// Local preflight report for a future external replay or official submission.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ExternalReplaySubmissionPreflightReport {
    /// Report id.
    pub report_id: String,
    /// Schema version.
    pub version: ExternalReplaySubmissionPreflightVersion,
    /// Source summary.
    pub source_summary: ExternalReplaySubmissionSourceSummary,
    /// Validation report.
    pub validation: ExternalReplaySubmissionPreflightValidation,
    /// Preflight reports never run external replay.
    pub runs_external_replay: bool,
    /// Preflight reports never submit to official endpoints.
    pub submits_to_official_endpoint: bool,
    /// Preflight reports never mutate accepted ledgers.
    pub mutates_accepted_evidence_ledger: bool,
    /// Preflight reports never write generated artifacts.
    pub writes_generated_artifacts: bool,
    /// Preflight reports never populate score axes.
    pub populates_score_axes: bool,
    /// Preflight report claim boundary.
    pub claim_boundary: ClaimBoundary,
    /// Required non-claim labels.
    pub non_claims: Vec<String>,
}

/// Required Phase W external replay / submission preflight non-claim labels.
pub fn required_external_replay_submission_preflight_non_claims() -> Vec<&'static str> {
    vec![
        "External replay submission preflight reports are not external replay evidence.",
        "External replay submission preflight reports are not official benchmark submissions.",
        "External replay submission preflight reports do not mutate EvidenceLedger.",
        "External replay submission preflight reports do not call endpoints.",
        "External replay submission preflight reports do not use credentials.",
        "External replay submission preflight reports do not populate score axes.",
        "External replay submission preflight reports are not Level2+ evidence.",
        "Official submission requires a separate operator-only submission operation.",
    ]
}

/// Build a local preflight report without live replay, submission, or writes.
pub fn build_external_replay_submission_preflight_report(
    request: &ExternalReplaySubmissionPreflightRequest,
) -> ExternalReplaySubmissionPreflightReport {
    let validation_context = validate_inputs(request);
    ExternalReplaySubmissionPreflightReport {
        report_id: format!("external_replay_submission_preflight_{}", request.id),
        version: ExternalReplaySubmissionPreflightVersion::default(),
        source_summary: ExternalReplaySubmissionSourceSummary {
            request_id: request.id.clone(),
            accepted_ledger_path: request.accepted_ledger_path.clone(),
            package_output_root: request.package_output_root.clone(),
            future_output_root: request.future_output_root.clone(),
            accepted_ledger_entry_count: validation_context.accepted_ledger_entry_count,
            package_id: validation_context.package_id,
            matched_accepted_evidence_id_count: validation_context
                .matched_accepted_evidence_id_count,
            external_replay_provenance_count: request.external_replay_provenance.len(),
            source_artifact_digest_count: request.source_artifact_digests.len(),
            requested_evidence_class: request.requested_evidence_class.clone(),
            requested_claim_boundary: request.requested_claim_boundary,
        },
        validation: validation_context.validation,
        runs_external_replay: false,
        submits_to_official_endpoint: false,
        mutates_accepted_evidence_ledger: false,
        writes_generated_artifacts: false,
        populates_score_axes: false,
        claim_boundary: ClaimBoundary::Level0DesignNote,
        non_claims: required_external_replay_submission_preflight_non_claims()
            .into_iter()
            .map(str::to_string)
            .collect(),
    }
}

/// Validate a local preflight request.
pub fn validate_external_replay_submission_preflight_request(
    request: &ExternalReplaySubmissionPreflightRequest,
) -> ExternalReplaySubmissionPreflightValidation {
    validate_inputs(request).validation
}

/// Serialize a preflight report as deterministic pretty JSON.
pub fn serialize_external_replay_submission_preflight_report_json(
    report: &ExternalReplaySubmissionPreflightReport,
) -> Result<String> {
    serde_json::to_string_pretty(report).map_err(|error| {
        ZkBenchError::serialization(
            "serialize_external_replay_submission_preflight_report_json",
            error.to_string(),
        )
    })
}

/// Deserialize a preflight report from JSON.
pub fn deserialize_external_replay_submission_preflight_report_json(
    json: &str,
) -> Result<ExternalReplaySubmissionPreflightReport> {
    serde_json::from_str(json).map_err(|error| {
        ZkBenchError::deserialization(
            "deserialize_external_replay_submission_preflight_report_json",
            error.to_string(),
        )
    })
}

/// Compute a deterministic digest for a preflight report.
pub fn compute_external_replay_submission_preflight_report_digest(
    report: &ExternalReplaySubmissionPreflightReport,
) -> Result<ArtifactDigest> {
    compute_artifact_digest(
        report,
        Some(ArtifactKind::Other),
        Some(ArtifactRole::Report),
    )
}

/// Render deterministic Markdown for a preflight report.
pub fn render_external_replay_submission_preflight_markdown(
    report: &ExternalReplaySubmissionPreflightReport,
) -> Result<String> {
    if missing_required_non_claims(&report.non_claims)
        .next()
        .is_some()
    {
        return Err(ZkBenchError::validation(
            "external_replay_submission_preflight.non_claims",
            "preflight report is missing required non-claim labels",
        ));
    }

    let mut markdown = String::new();
    markdown.push_str("# External Replay Submission Preflight\n\n");
    markdown.push_str("Status: local metadata-only preflight.\n\n");
    markdown.push_str("## Claim Boundary\n\n");
    markdown.push_str(&format!(
        "- Report claim boundary: `{}`\n",
        report.claim_boundary
    ));
    markdown.push_str("- External replay run: `false`\n");
    markdown.push_str("- Official endpoint submitted: `false`\n");
    markdown.push_str("- Accepted Evidence Ledger mutation: `false`\n");
    markdown.push_str("- Generated artifacts written: `false`\n");
    markdown.push_str("- Score axes populated: `false`\n\n");

    markdown.push_str("## Source Summary\n\n");
    markdown.push_str(&format!(
        "- Request: `{}`\n",
        report.source_summary.request_id
    ));
    markdown.push_str(&format!(
        "- Package: `{}`\n",
        report.source_summary.package_id
    ));
    markdown.push_str(&format!(
        "- Accepted ledger entries: `{}`\n",
        report.source_summary.accepted_ledger_entry_count
    ));
    markdown.push_str(&format!(
        "- Matched accepted evidence ids: `{}`\n",
        report.source_summary.matched_accepted_evidence_id_count
    ));
    markdown.push_str(&format!(
        "- External replay provenance records: `{}`\n",
        report.source_summary.external_replay_provenance_count
    ));
    markdown.push_str(&format!(
        "- Source artifact digests: `{}`\n",
        report.source_summary.source_artifact_digest_count
    ));
    markdown.push_str(&format!(
        "- Requested evidence class: `{:?}`\n",
        report.source_summary.requested_evidence_class
    ));
    markdown.push_str(&format!(
        "- Requested claim boundary: `{}`\n\n",
        report.source_summary.requested_claim_boundary
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

#[derive(Debug, Clone)]
struct ValidationContext {
    validation: ExternalReplaySubmissionPreflightValidation,
    accepted_ledger_entry_count: usize,
    package_id: String,
    matched_accepted_evidence_id_count: usize,
}

fn validate_inputs(request: &ExternalReplaySubmissionPreflightRequest) -> ValidationContext {
    let mut issues = Vec::new();

    validate_identity(request, &mut issues);
    validate_required_non_claims(&mut issues, &request.non_claims);
    scan_forbidden_text(request, &mut issues);

    if !request.operator_acknowledged {
        push_issue(
            &mut issues,
            ExternalReplaySubmissionPreflightIssueKind::MissingOperatorAcknowledgement,
            "request.operator_acknowledged",
            "operator acknowledgement is required before future live replay or submission",
        );
    }
    if request.official_endpoint_submission_requested {
        push_issue(
            &mut issues,
            ExternalReplaySubmissionPreflightIssueKind::EndpointSubmissionAttempt,
            "request.official_endpoint_submission_requested",
            "this local preflight cannot submit to an official endpoint",
        );
    }
    if request.external_replay_provenance.is_empty() {
        push_issue(
            &mut issues,
            ExternalReplaySubmissionPreflightIssueKind::MissingExternalReplayProvenance,
            "request.external_replay_provenance",
            "external replay provenance declarations are required",
        );
    }
    validate_source_digests(
        &mut issues,
        "request.source_artifact_digests",
        &request.source_artifact_digests,
    );
    if request.redaction_policy.is_empty() {
        push_issue(
            &mut issues,
            ExternalReplaySubmissionPreflightIssueKind::MissingRedactionPolicy,
            "request.redaction_policy",
            "a redaction policy is required for future generated outputs",
        );
    }

    for (index, marker) in request.unresolved_quarantine_markers.iter().enumerate() {
        push_issue(
            &mut issues,
            ExternalReplaySubmissionPreflightIssueKind::UnresolvedBlockingMarker,
            format!("request.unresolved_quarantine_markers[{index}]"),
            format!("unresolved quarantine marker blocks promotion: {marker}"),
        );
    }
    for (index, marker) in request.blocking_markers.iter().enumerate() {
        push_issue(
            &mut issues,
            ExternalReplaySubmissionPreflightIssueKind::UnresolvedBlockingMarker,
            format!("request.blocking_markers[{index}]"),
            format!("blocking marker blocks promotion: {marker}"),
        );
    }

    validate_evidence_scope(request, &mut issues);
    validate_future_output_root(request, &mut issues);

    let ledger = load_accepted_ledger(request, &mut issues);
    let package = read_package_output(request, &mut issues);

    if let (Some(ledger), Some(package)) = (&ledger, &package) {
        validate_package_against_ledger(request, ledger, package, &mut issues);
    }

    ValidationContext {
        validation: ExternalReplaySubmissionPreflightValidation {
            valid: issues.is_empty(),
            issues,
        },
        accepted_ledger_entry_count: ledger.as_ref().map_or(0, |ledger| ledger.entries.len()),
        package_id: package.as_ref().map_or_else(
            || "unavailable".to_string(),
            |package| package.validation_report.package_id.clone(),
        ),
        matched_accepted_evidence_id_count: package.as_ref().map_or(0, |package| {
            package
                .validation_report
                .matched_accepted_evidence_ledger_entry_ids
                .len()
        }),
    }
}

fn validate_identity(
    request: &ExternalReplaySubmissionPreflightRequest,
    issues: &mut Vec<ExternalReplaySubmissionPreflightIssue>,
) {
    for (path, value) in [
        ("request.id", request.id.as_str()),
        (
            "request.benchmark_target.benchmark_suite_id",
            request.benchmark_target.benchmark_suite_id.as_str(),
        ),
        (
            "request.benchmark_target.backend_id",
            request.benchmark_target.backend_id.as_str(),
        ),
        (
            "request.benchmark_target.backend_version",
            request.benchmark_target.backend_version.as_str(),
        ),
        (
            "request.benchmark_target.target_label",
            request.benchmark_target.target_label.as_str(),
        ),
    ] {
        if value.trim().is_empty() {
            push_issue(
                issues,
                ExternalReplaySubmissionPreflightIssueKind::EmptyIdentity,
                path,
                "required identity field must be non-empty",
            );
        }
    }
}

fn validate_evidence_scope(
    request: &ExternalReplaySubmissionPreflightRequest,
    issues: &mut Vec<ExternalReplaySubmissionPreflightIssue>,
) {
    if matches!(
        request.requested_evidence_class,
        EvidenceClass::DesignNote | EvidenceClass::LocalReplay
    ) {
        push_issue(
            issues,
            ExternalReplaySubmissionPreflightIssueKind::UnsupportedEvidenceClass,
            "request.requested_evidence_class",
            "future external replay/submission preflight requires an external or reproducible evidence class",
        );
    }
    if request.requested_claim_boundary <= ClaimBoundary::Level1LocalReplay {
        push_issue(
            issues,
            ExternalReplaySubmissionPreflightIssueKind::LocalOnlyEvidencePromotion,
            "request.requested_claim_boundary",
            "local-only claim boundaries cannot be promoted to external replay or official submission",
        );
    }
    if request.populates_score_axes {
        push_issue(
            issues,
            ExternalReplaySubmissionPreflightIssueKind::ScoreAxisPopulationWithoutEvidenceClass,
            "request.populates_score_axes",
            "this local preflight cannot populate score axes",
        );
    }
}

fn load_accepted_ledger(
    request: &ExternalReplaySubmissionPreflightRequest,
    issues: &mut Vec<ExternalReplaySubmissionPreflightIssue>,
) -> Option<EvidenceLedger> {
    if let Err(message) = validate_existing_file_path(&request.accepted_ledger_path) {
        push_issue(
            issues,
            ExternalReplaySubmissionPreflightIssueKind::InvalidAcceptedLedger,
            "request.accepted_ledger_path",
            message,
        );
        return None;
    }
    match EvidenceLedger::load_json(&request.accepted_ledger_path) {
        Ok(ledger) => {
            let validation = ledger.validate();
            if validation.valid {
                Some(ledger)
            } else {
                push_issue(
                    issues,
                    ExternalReplaySubmissionPreflightIssueKind::InvalidAcceptedLedger,
                    "request.accepted_ledger_path",
                    format!("accepted ledger is invalid: {:?}", validation.errors),
                );
                None
            }
        }
        Err(error) => {
            push_issue(
                issues,
                ExternalReplaySubmissionPreflightIssueKind::InvalidAcceptedLedger,
                "request.accepted_ledger_path",
                error.to_string(),
            );
            None
        }
    }
}

fn read_package_output(
    request: &ExternalReplaySubmissionPreflightRequest,
    issues: &mut Vec<ExternalReplaySubmissionPreflightIssue>,
) -> Option<OfficialSubmissionPackageOutput> {
    match read_official_submission_package_outputs(
        &request.package_output_root,
        &request.protected_paths,
    ) {
        Ok(output) => {
            if output.package_metadata_digest != request.expected_package_metadata_digest {
                push_issue(
                    issues,
                    ExternalReplaySubmissionPreflightIssueKind::PackageDigestMismatch,
                    "request.expected_package_metadata_digest",
                    "package metadata digest does not match operator expectation",
                );
            }
            if output.validation_report_digest != request.expected_validation_report_digest {
                push_issue(
                    issues,
                    ExternalReplaySubmissionPreflightIssueKind::PackageDigestMismatch,
                    "request.expected_validation_report_digest",
                    "validation report digest does not match operator expectation",
                );
            }
            if output.validation_report.creates_official_submission
                || output.validation_report.submits_to_official_endpoint
                || output.validation_report.populates_score_axes
            {
                push_issue(
                    issues,
                    ExternalReplaySubmissionPreflightIssueKind::InvalidPackageOutput,
                    "request.package_output_root",
                    "package output validation report claims a forbidden side effect",
                );
            }
            Some(output)
        }
        Err(error) => {
            push_issue(
                issues,
                ExternalReplaySubmissionPreflightIssueKind::InvalidPackageOutput,
                "request.package_output_root",
                error.to_string(),
            );
            None
        }
    }
}

fn validate_package_against_ledger(
    request: &ExternalReplaySubmissionPreflightRequest,
    ledger: &EvidenceLedger,
    package: &OfficialSubmissionPackageOutput,
    issues: &mut Vec<ExternalReplaySubmissionPreflightIssue>,
) {
    if package.validation_report.accepted_ledger_path != request.accepted_ledger_path {
        push_issue(
            issues,
            ExternalReplaySubmissionPreflightIssueKind::InvalidPackageOutput,
            "request.accepted_ledger_path",
            "package output was validated against a different accepted ledger path",
        );
    }
    if package.validation_report.accepted_ledger_entry_count != ledger.entries.len() {
        push_issue(
            issues,
            ExternalReplaySubmissionPreflightIssueKind::InvalidPackageOutput,
            "request.package_output_root",
            "package output accepted ledger count does not match supplied ledger",
        );
    }
    let mut ledger_ids = BTreeSet::new();
    for entry in &ledger.entries {
        ledger_ids.insert(entry.sequence_number.to_string());
        ledger_ids.insert(entry.entry_digest.hex_digest.clone());
    }
    for id in &package
        .validation_report
        .matched_accepted_evidence_ledger_entry_ids
    {
        if !ledger_ids.contains(id) {
            push_issue(
                issues,
                ExternalReplaySubmissionPreflightIssueKind::InvalidPackageOutput,
                "request.package_output_root",
                format!("package accepted evidence id {id:?} is absent from supplied ledger"),
            );
        }
    }
}

fn validate_future_output_root(
    request: &ExternalReplaySubmissionPreflightRequest,
    issues: &mut Vec<ExternalReplaySubmissionPreflightIssue>,
) {
    if request.future_output_root.as_os_str().is_empty() {
        push_issue(
            issues,
            ExternalReplaySubmissionPreflightIssueKind::UnsafeOutputRoot,
            "request.future_output_root",
            "future output root must be non-empty",
        );
        return;
    }
    if let Err(message) = validate_no_parent_components(&request.future_output_root) {
        push_issue(
            issues,
            ExternalReplaySubmissionPreflightIssueKind::UnsafeOutputRoot,
            "request.future_output_root",
            message,
        );
        return;
    }
    let normalized_output = match normalize_path(&request.future_output_root) {
        Ok(path) => path,
        Err(message) => {
            push_issue(
                issues,
                ExternalReplaySubmissionPreflightIssueKind::UnsafeOutputRoot,
                "request.future_output_root",
                message,
            );
            return;
        }
    };
    let resolved_output = match resolve_existing_prefix(&request.future_output_root) {
        Ok(path) => path,
        Err(message) => {
            push_issue(
                issues,
                ExternalReplaySubmissionPreflightIssueKind::UnsafeOutputRoot,
                "request.future_output_root",
                message,
            );
            return;
        }
    };
    for protected in &request.protected_paths {
        if let Err(message) = validate_no_parent_components(protected) {
            push_issue(
                issues,
                ExternalReplaySubmissionPreflightIssueKind::UnsafeOutputRoot,
                "request.protected_paths",
                message,
            );
            continue;
        }
        let normalized_protected = match normalize_path(protected) {
            Ok(path) => path,
            Err(message) => {
                push_issue(
                    issues,
                    ExternalReplaySubmissionPreflightIssueKind::UnsafeOutputRoot,
                    "request.protected_paths",
                    message,
                );
                continue;
            }
        };
        let resolved_protected = match resolve_existing_prefix(protected) {
            Ok(path) => path,
            Err(message) => {
                push_issue(
                    issues,
                    ExternalReplaySubmissionPreflightIssueKind::UnsafeOutputRoot,
                    "request.protected_paths",
                    message,
                );
                continue;
            }
        };
        if paths_overlap(&normalized_output, &normalized_protected)
            || paths_overlap(&resolved_output, &resolved_protected)
        {
            push_issue(
                issues,
                ExternalReplaySubmissionPreflightIssueKind::UnsafeOutputRoot,
                "request.future_output_root",
                format!(
                    "future output root overlaps protected path {}",
                    protected.display()
                ),
            );
        }
    }
    if request.future_output_root.exists() {
        if let Err(message) = reject_symlink(&request.future_output_root) {
            push_issue(
                issues,
                ExternalReplaySubmissionPreflightIssueKind::UnsafeOutputRoot,
                "request.future_output_root",
                message,
            );
            return;
        }
        if request.future_output_root.is_file() {
            push_issue(
                issues,
                ExternalReplaySubmissionPreflightIssueKind::UnsafeOutputRoot,
                "request.future_output_root",
                "future output root is an existing file",
            );
            return;
        }
        match directory_has_entries(&request.future_output_root) {
            Ok(true) if !request.overwrite => push_issue(
                issues,
                ExternalReplaySubmissionPreflightIssueKind::UnsafeOutputRoot,
                "request.future_output_root",
                "future output root is not empty; explicit overwrite is required",
            ),
            Ok(_) => {}
            Err(message) => push_issue(
                issues,
                ExternalReplaySubmissionPreflightIssueKind::UnsafeOutputRoot,
                "request.future_output_root",
                message,
            ),
        }
    }
}

fn validate_existing_file_path(path: &Path) -> std::result::Result<(), String> {
    validate_no_parent_components(path)?;
    if !path.exists() {
        return Err(format!("{} is missing", path.display()));
    }
    reject_symlink(path)?;
    if path.is_dir() {
        return Err(format!("{} is a directory", path.display()));
    }
    Ok(())
}

fn validate_source_digests(
    issues: &mut Vec<ExternalReplaySubmissionPreflightIssue>,
    path: &str,
    digests: &[ArtifactDigest],
) {
    if digests.is_empty() {
        push_issue(
            issues,
            ExternalReplaySubmissionPreflightIssueKind::MissingSourceArtifactDigest,
            path,
            "at least one source artifact digest is required",
        );
    }
    for (index, digest) in digests.iter().enumerate() {
        if digest.algorithm != ArtifactDigestAlgorithm::Sha256 || digest.hex_digest.len() != 64 {
            push_issue(
                issues,
                ExternalReplaySubmissionPreflightIssueKind::MissingSourceArtifactDigest,
                format!("{path}[{index}]"),
                "source artifact digest must be sha256 with a 64-character hex digest",
            );
        }
    }
}

fn validate_required_non_claims(
    issues: &mut Vec<ExternalReplaySubmissionPreflightIssue>,
    non_claims: &[String],
) {
    for required in required_external_replay_submission_preflight_non_claims() {
        if !non_claims.iter().any(|non_claim| non_claim == required) {
            push_issue(
                issues,
                ExternalReplaySubmissionPreflightIssueKind::MissingRequiredNonClaim,
                "request.non_claims",
                format!("missing required non-claim label: {required}"),
            );
        }
    }
}

fn missing_required_non_claims<'a>(
    non_claims: &'a [String],
) -> impl Iterator<Item = &'static str> + 'a {
    required_external_replay_submission_preflight_non_claims()
        .into_iter()
        .filter(move |required| !non_claims.iter().any(|non_claim| non_claim == required))
}

fn scan_forbidden_text(
    request: &ExternalReplaySubmissionPreflightRequest,
    issues: &mut Vec<ExternalReplaySubmissionPreflightIssue>,
) {
    for (index, text) in request.claim_text.iter().enumerate() {
        let normalized = text.to_ascii_lowercase();
        for forbidden in [
            "sota",
            "leaderboard",
            "production ready",
            "production-ready",
            "semantic correctness",
            "formally proven",
            "soundness proof",
            "official benchmark evidence",
        ] {
            if normalized.contains(forbidden) {
                push_issue(
                    issues,
                    ExternalReplaySubmissionPreflightIssueKind::ForbiddenClaimText,
                    format!("request.claim_text[{index}]"),
                    format!("forbidden claim text contains {forbidden:?}"),
                );
            }
        }
    }
}

fn validate_no_parent_components(path: &Path) -> std::result::Result<(), String> {
    if path
        .components()
        .any(|component| component == Component::ParentDir)
    {
        return Err(format!(
            "{} must not contain parent-directory components",
            path.display()
        ));
    }
    Ok(())
}

fn reject_symlink(path: &Path) -> std::result::Result<(), String> {
    let metadata = fs::symlink_metadata(path).map_err(|error| error.to_string())?;
    if metadata.file_type().is_symlink() {
        return Err(format!("{} must not be a symlink", path.display()));
    }
    Ok(())
}

fn directory_has_entries(path: &Path) -> std::result::Result<bool, String> {
    Ok(fs::read_dir(path)
        .map_err(|error| error.to_string())?
        .next()
        .is_some())
}

fn normalize_path(path: &Path) -> std::result::Result<PathBuf, String> {
    let mut normalized = if path.is_absolute() {
        PathBuf::new()
    } else {
        std::env::current_dir().map_err(|error| error.to_string())?
    };
    for component in path.components() {
        match component {
            Component::Prefix(prefix) => normalized.push(prefix.as_os_str()),
            Component::RootDir => normalized.push(component.as_os_str()),
            Component::CurDir => {}
            Component::Normal(segment) => normalized.push(segment),
            Component::ParentDir => {
                return Err(format!(
                    "{} must not contain parent-directory components",
                    path.display()
                ));
            }
        }
    }
    Ok(normalized)
}

fn resolve_existing_prefix(path: &Path) -> std::result::Result<PathBuf, String> {
    let normalized = normalize_path(path)?;
    let mut missing = Vec::new();
    let mut cursor = normalized.as_path();
    loop {
        match fs::canonicalize(cursor) {
            Ok(mut resolved) => {
                for segment in missing.iter().rev() {
                    resolved.push(segment);
                }
                return Ok(resolved);
            }
            Err(error) if error.kind() == std::io::ErrorKind::NotFound => {
                let Some(segment) = cursor.file_name() else {
                    return Ok(normalized);
                };
                missing.push(segment.to_os_string());
                let Some(parent) = cursor.parent() else {
                    return Ok(normalized);
                };
                cursor = parent;
            }
            Err(error) => return Err(error.to_string()),
        }
    }
}

fn paths_overlap(left: &Path, right: &Path) -> bool {
    left.starts_with(right) || right.starts_with(left)
}

fn push_issue(
    issues: &mut Vec<ExternalReplaySubmissionPreflightIssue>,
    kind: ExternalReplaySubmissionPreflightIssueKind,
    path: impl Into<String>,
    message: impl Into<String>,
) {
    issues.push(ExternalReplaySubmissionPreflightIssue {
        kind,
        path: path.into(),
        message: message.into(),
    });
}
