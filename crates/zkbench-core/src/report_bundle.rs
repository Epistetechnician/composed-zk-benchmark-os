//! Phase Q inert report-bundle metadata.
//!
//! Report bundles are read-only local integrity summaries. They do not create
//! accepted evidence, do not execute replay commands, do not claim official
//! benchmark evidence, and do not report ZK backend performance.

use std::collections::BTreeSet;

use serde::{Deserialize, Serialize};

use crate::dashboard::{
    build_dashboard_model_from_pack_readiness, build_dashboard_model_from_score_report,
    render_dashboard_markdown,
};
use crate::error::{Result, ZkBenchError};
use crate::evidence::{
    compute_artifact_digest, compute_artifact_digest_bytes, ArtifactDigest,
    ArtifactDigestAlgorithm, ArtifactKind, ArtifactRole, ClaimBoundary,
};
use crate::pack::{PackReadinessReport, PackReadinessValidation};
use crate::scoring::ScoreReport;

/// Phase Q report-bundle schema version.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ReportBundleVersion {
    /// Logical version string.
    pub value: String,
}

impl Default for ReportBundleVersion {
    fn default() -> Self {
        Self {
            value: "phase-q-report-bundle-v0".to_string(),
        }
    }
}

/// Inert report-bundle source kind.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
pub enum ReportBundleInputKind {
    /// Existing conservative score report metadata.
    ScoreReport,
    /// Existing pack-readiness report metadata.
    PackReadinessReport,
    /// Existing pack-readiness validation metadata.
    PackReadinessValidation,
    /// Rendered read-only Markdown report.
    RenderedMarkdown,
    /// Other local report metadata.
    OtherLocalMetadata,
}

/// Source reference included in an inert report bundle.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ReportBundleInputRef {
    /// Logical input id.
    pub input_id: String,
    /// Portable relative artifact URI or logical bundle path.
    pub artifact_uri: String,
    /// Input kind.
    pub kind: ReportBundleInputKind,
    /// Stable digest over the referenced local metadata bytes.
    pub digest: ArtifactDigest,
    /// Input claim boundary.
    pub claim_boundary: ClaimBoundary,
    /// True when this source represents failed pack-readiness validation.
    #[serde(default)]
    pub failed_readiness: bool,
    /// Notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

/// Rendered report entry included in an inert report bundle.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ReportBundleRenderedReport {
    /// Rendered report id.
    pub rendered_report_id: String,
    /// Human-readable title.
    pub title: String,
    /// Portable relative output URI for future materialization.
    pub artifact_uri: String,
    /// Digest over rendered Markdown bytes.
    pub markdown_digest: ArtifactDigest,
    /// Source input ids summarized by this rendered report.
    #[serde(default)]
    pub source_input_ids: Vec<String>,
    /// Whether failed readiness state is visible in the rendered text.
    pub failed_readiness_visible: bool,
    /// Whether local-only claim warnings are visible in the rendered text.
    pub local_only_warnings_visible: bool,
    /// Rendered report claim boundary.
    pub claim_boundary: ClaimBoundary,
    /// Notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

/// Existing pack-readiness metadata pair for report-bundle construction.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ReportBundlePackReadinessInput {
    /// Pack-readiness report.
    pub report: PackReadinessReport,
    /// Validation for the pack-readiness report.
    pub validation: PackReadinessValidation,
}

/// Inert report-bundle manifest.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ReportBundleManifest {
    /// Bundle id.
    pub bundle_id: String,
    /// Schema version.
    pub version: ReportBundleVersion,
    /// Source inputs.
    #[serde(default)]
    pub inputs: Vec<ReportBundleInputRef>,
    /// Rendered Markdown reports.
    #[serde(default)]
    pub rendered_reports: Vec<ReportBundleRenderedReport>,
    /// Human-readable claim-boundary summary.
    #[serde(default)]
    pub claim_boundary_summary: Vec<String>,
    /// Whether any replay-command execution output is included.
    #[serde(default)]
    pub replay_command_execution_output: bool,
    /// Whether external replay is authorized or claimed.
    #[serde(default)]
    pub external_replay_authorized: bool,
    /// Whether this bundle claims to create Level2 evidence.
    #[serde(default)]
    pub creates_level2_evidence: bool,
    /// Whether this bundle claims official benchmark evidence.
    #[serde(default)]
    pub official_benchmark_evidence: bool,
    /// Whether this bundle claims ZK backend performance evidence.
    #[serde(default)]
    pub zk_backend_performance_claims: bool,
    /// Whether this bundle mutates or claims to mutate the accepted Evidence Ledger.
    #[serde(default)]
    pub mutates_accepted_evidence_ledger: bool,
    /// Output claim boundary for the bundle.
    pub output_claim_boundary: ClaimBoundary,
    /// Explicit limitations.
    #[serde(default)]
    pub limitations: Vec<String>,
    /// Notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

/// Report-bundle validation issue kind.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum ReportBundleValidationIssueKind {
    /// Required identity field is empty.
    EmptyIdentity,
    /// Source inputs are missing.
    MissingInputs,
    /// Rendered Markdown reports are missing.
    MissingRenderedReport,
    /// Source reference is missing.
    MissingSourceRef,
    /// Duplicate source input id.
    DuplicateInputId,
    /// Duplicate rendered report id.
    DuplicateRenderedReportId,
    /// Artifact reference is not portable relative metadata.
    InvalidArtifactRef,
    /// Digest is missing, unsupported, or malformed.
    InvalidDigest,
    /// Bundle or rendered output claim boundary is too high.
    ClaimBoundaryEscalation,
    /// Bundle included replay-command execution output.
    ReplayCommandExecutionOutput,
    /// Bundle authorized or claimed external replay.
    ExternalReplayAuthorized,
    /// Bundle claimed to create Level2 evidence.
    Level2EvidenceClaim,
    /// Bundle claimed official benchmark evidence.
    OfficialBenchmarkEvidenceClaim,
    /// Bundle claimed ZK backend performance.
    ZkBackendPerformanceClaim,
    /// Bundle claimed accepted Evidence Ledger mutation.
    AcceptedEvidenceLedgerMutationClaim,
    /// Failed pack-readiness state was hidden.
    FailedReadinessHidden,
    /// Required limitation text is missing.
    MissingLimitation,
}

/// Report-bundle validation issue.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ReportBundleValidationIssue {
    /// Issue kind.
    pub kind: ReportBundleValidationIssueKind,
    /// Issue path.
    pub path: String,
    /// Issue message.
    pub message: String,
}

/// Report-bundle validation result.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ReportBundleValidation {
    /// Whether validation passed.
    pub valid: bool,
    /// Validation issues.
    #[serde(default)]
    pub issues: Vec<ReportBundleValidationIssue>,
    /// Claim boundary of this validation report.
    pub claim_boundary: ClaimBoundary,
}

/// Build an inert report-bundle manifest from existing local report metadata.
///
/// This function does not write files, execute replay commands, call external
/// backends, import results, or mutate the accepted Evidence Ledger.
pub fn build_report_bundle_manifest_from_reports(
    bundle_id: impl Into<String>,
    score_reports: &[ScoreReport],
    readiness_inputs: &[ReportBundlePackReadinessInput],
) -> Result<ReportBundleManifest> {
    let bundle_id = bundle_id.into();
    let mut inputs = Vec::new();
    let mut rendered_reports = Vec::new();

    for (index, report) in score_reports.iter().enumerate() {
        let input_id = format!("score_report_{index}");
        inputs.push(ReportBundleInputRef {
            artifact_uri: format!("score_reports/{input_id}.json"),
            digest: compute_artifact_digest(
                report,
                Some(ArtifactKind::ScoreReport),
                Some(ArtifactRole::Report),
            )?,
            input_id: input_id.clone(),
            kind: ReportBundleInputKind::ScoreReport,
            claim_boundary: report.claim_boundary_max,
            failed_readiness: false,
            notes: vec!["existing Score Report metadata".to_string()],
        });

        let dashboard_id = format!("{bundle_id}_{input_id}_dashboard");
        let model = build_dashboard_model_from_score_report(&dashboard_id, report);
        let markdown = render_dashboard_markdown(&model);
        rendered_reports.push(rendered_report(
            format!("{input_id}_markdown"),
            "Score Report Markdown".to_string(),
            format!("rendered/{input_id}.md"),
            &markdown,
            vec![input_id],
            false,
            true,
        ));
    }

    for (index, source) in readiness_inputs.iter().enumerate() {
        let report_input_id = format!("pack_readiness_report_{index}");
        let validation_input_id = format!("pack_readiness_validation_{index}");
        inputs.push(ReportBundleInputRef {
            artifact_uri: format!("pack_readiness/{report_input_id}.json"),
            digest: compute_artifact_digest(
                &source.report,
                Some(ArtifactKind::Other),
                Some(ArtifactRole::Report),
            )?,
            input_id: report_input_id.clone(),
            kind: ReportBundleInputKind::PackReadinessReport,
            claim_boundary: source.report.output_claim_boundary,
            failed_readiness: readiness_failed(&source.report, &source.validation),
            notes: vec!["existing PackReadinessReport metadata".to_string()],
        });
        inputs.push(ReportBundleInputRef {
            artifact_uri: format!("pack_readiness/{validation_input_id}.json"),
            digest: compute_artifact_digest(
                &source.validation,
                Some(ArtifactKind::Other),
                Some(ArtifactRole::Report),
            )?,
            input_id: validation_input_id.clone(),
            kind: ReportBundleInputKind::PackReadinessValidation,
            claim_boundary: source.validation.claim_boundary,
            failed_readiness: !source.validation.valid,
            notes: readiness_validation_notes(&source.validation),
        });

        let dashboard_id = format!("{bundle_id}_{report_input_id}_dashboard");
        let model = build_dashboard_model_from_pack_readiness(
            &dashboard_id,
            &source.report,
            &source.validation,
        );
        let markdown = render_dashboard_markdown(&model);
        rendered_reports.push(rendered_report(
            format!("{report_input_id}_markdown"),
            "Pack Readiness Markdown".to_string(),
            format!("rendered/{report_input_id}.md"),
            &markdown,
            vec![report_input_id, validation_input_id],
            readiness_failed(&source.report, &source.validation),
            true,
        ));
    }

    Ok(ReportBundleManifest {
        bundle_id,
        version: ReportBundleVersion::default(),
        inputs,
        rendered_reports,
        claim_boundary_summary: vec![
            "Report bundles are not accepted evidence.".to_string(),
            "Report bundles are local integrity summaries, not official benchmark evidence."
                .to_string(),
            "Report bundles do not create Level2+ evidence.".to_string(),
            "Report bundles do not prove backend performance.".to_string(),
            "Local replay artifacts are not official benchmark evidence.".to_string(),
            "Internal timing telemetry is not ZK backend performance.".to_string(),
        ],
        replay_command_execution_output: false,
        external_replay_authorized: false,
        creates_level2_evidence: false,
        official_benchmark_evidence: false,
        zk_backend_performance_claims: false,
        mutates_accepted_evidence_ledger: false,
        output_claim_boundary: ClaimBoundary::Level0DesignNote,
        limitations: vec![
            "Report bundles are not accepted evidence.".to_string(),
            "Local replay artifacts are not official benchmark evidence.".to_string(),
            "Internal timing telemetry is not ZK backend performance.".to_string(),
            "Report bundles do not mutate the accepted Evidence Ledger.".to_string(),
        ],
        notes: vec![
            "constructed from existing local reporting metadata only".to_string(),
            "no report-bundle files were generated by this manifest builder".to_string(),
        ],
    })
}

/// Compute a deterministic digest for a report-bundle manifest.
pub fn compute_report_bundle_manifest_digest(
    manifest: &ReportBundleManifest,
) -> Result<ArtifactDigest> {
    compute_artifact_digest(
        manifest,
        Some(ArtifactKind::Other),
        Some(ArtifactRole::Report),
    )
}

/// Serialize a report-bundle manifest to pretty JSON.
pub fn serialize_report_bundle_manifest_json(manifest: &ReportBundleManifest) -> Result<String> {
    serde_json::to_string_pretty(manifest)
        .map_err(|error| ZkBenchError::serialization("report_bundle.manifest", error.to_string()))
}

/// Deserialize a report-bundle manifest from JSON.
pub fn deserialize_report_bundle_manifest_json(json: &str) -> Result<ReportBundleManifest> {
    serde_json::from_str(json)
        .map_err(|error| ZkBenchError::deserialization("report_bundle.manifest", error.to_string()))
}

/// Validate inert report-bundle metadata.
pub fn validate_report_bundle_manifest(manifest: &ReportBundleManifest) -> ReportBundleValidation {
    let mut issues = Vec::new();

    validate_identity(&mut issues, "bundle_id", &manifest.bundle_id);
    validate_identity(&mut issues, "version.value", &manifest.version.value);

    if manifest.inputs.is_empty() {
        push_issue(
            &mut issues,
            ReportBundleValidationIssueKind::MissingInputs,
            "inputs",
            "report bundle must bind at least one source input",
        );
    }
    if manifest.rendered_reports.is_empty() {
        push_issue(
            &mut issues,
            ReportBundleValidationIssueKind::MissingRenderedReport,
            "rendered_reports",
            "report bundle must include at least one rendered Markdown report",
        );
    }

    let mut input_ids = BTreeSet::new();
    for (index, input) in manifest.inputs.iter().enumerate() {
        let path = format!("inputs[{index}]");
        validate_identity(&mut issues, format!("{path}.input_id"), &input.input_id);
        if !input_ids.insert(input.input_id.clone()) {
            push_issue(
                &mut issues,
                ReportBundleValidationIssueKind::DuplicateInputId,
                format!("{path}.input_id"),
                "input ids must be unique",
            );
        }
        if !is_portable_relative_artifact_ref(&input.artifact_uri) {
            push_issue(
                &mut issues,
                ReportBundleValidationIssueKind::InvalidArtifactRef,
                format!("{path}.artifact_uri"),
                "input artifact URI must be portable relative metadata",
            );
        }
        validate_digest(&mut issues, format!("{path}.digest"), &input.digest);
        if input.claim_boundary > ClaimBoundary::Level1LocalReplay {
            push_issue(
                &mut issues,
                ReportBundleValidationIssueKind::ClaimBoundaryEscalation,
                format!("{path}.claim_boundary"),
                "Phase Q local report-bundle inputs must remain Level1LocalReplay or lower",
            );
        }
    }

    let mut rendered_ids = BTreeSet::new();
    for (index, rendered) in manifest.rendered_reports.iter().enumerate() {
        let path = format!("rendered_reports[{index}]");
        validate_identity(
            &mut issues,
            format!("{path}.rendered_report_id"),
            &rendered.rendered_report_id,
        );
        if !rendered_ids.insert(rendered.rendered_report_id.clone()) {
            push_issue(
                &mut issues,
                ReportBundleValidationIssueKind::DuplicateRenderedReportId,
                format!("{path}.rendered_report_id"),
                "rendered report ids must be unique",
            );
        }
        validate_identity(&mut issues, format!("{path}.title"), &rendered.title);
        if !is_portable_relative_artifact_ref(&rendered.artifact_uri) {
            push_issue(
                &mut issues,
                ReportBundleValidationIssueKind::InvalidArtifactRef,
                format!("{path}.artifact_uri"),
                "rendered report URI must be portable relative metadata",
            );
        }
        validate_digest(
            &mut issues,
            format!("{path}.markdown_digest"),
            &rendered.markdown_digest,
        );
        if rendered.claim_boundary != ClaimBoundary::Level0DesignNote {
            push_issue(
                &mut issues,
                ReportBundleValidationIssueKind::ClaimBoundaryEscalation,
                format!("{path}.claim_boundary"),
                "rendered report output must remain Level0DesignNote",
            );
        }
        if rendered.source_input_ids.is_empty() {
            push_issue(
                &mut issues,
                ReportBundleValidationIssueKind::MissingSourceRef,
                format!("{path}.source_input_ids"),
                "rendered report must reference source input ids",
            );
        }
        for (source_index, source_input_id) in rendered.source_input_ids.iter().enumerate() {
            if !input_ids.contains(source_input_id) {
                push_issue(
                    &mut issues,
                    ReportBundleValidationIssueKind::MissingSourceRef,
                    format!("{path}.source_input_ids[{source_index}]"),
                    "rendered report references an unknown source input id",
                );
            }
        }
        if !rendered.local_only_warnings_visible {
            push_issue(
                &mut issues,
                ReportBundleValidationIssueKind::MissingLimitation,
                format!("{path}.local_only_warnings_visible"),
                "rendered reports must keep local-only warnings visible",
            );
        }
    }

    validate_failed_readiness_visibility(manifest, &mut issues);

    if manifest.output_claim_boundary != ClaimBoundary::Level0DesignNote {
        push_issue(
            &mut issues,
            ReportBundleValidationIssueKind::ClaimBoundaryEscalation,
            "output_claim_boundary",
            "Phase Q report-bundle output must remain Level0DesignNote",
        );
    }
    if manifest.replay_command_execution_output {
        push_issue(
            &mut issues,
            ReportBundleValidationIssueKind::ReplayCommandExecutionOutput,
            "replay_command_execution_output",
            "report bundles must not include replay-command execution output",
        );
    }
    if manifest.external_replay_authorized {
        push_issue(
            &mut issues,
            ReportBundleValidationIssueKind::ExternalReplayAuthorized,
            "external_replay_authorized",
            "report bundles must not authorize external replay",
        );
    }
    if manifest.creates_level2_evidence {
        push_issue(
            &mut issues,
            ReportBundleValidationIssueKind::Level2EvidenceClaim,
            "creates_level2_evidence",
            "report bundles do not create Level2+ evidence",
        );
    }
    if manifest.official_benchmark_evidence {
        push_issue(
            &mut issues,
            ReportBundleValidationIssueKind::OfficialBenchmarkEvidenceClaim,
            "official_benchmark_evidence",
            "report bundles are not official benchmark evidence",
        );
    }
    if manifest.zk_backend_performance_claims {
        push_issue(
            &mut issues,
            ReportBundleValidationIssueKind::ZkBackendPerformanceClaim,
            "zk_backend_performance_claims",
            "report bundles do not prove ZK backend performance",
        );
    }
    if manifest.mutates_accepted_evidence_ledger {
        push_issue(
            &mut issues,
            ReportBundleValidationIssueKind::AcceptedEvidenceLedgerMutationClaim,
            "mutates_accepted_evidence_ledger",
            "report bundles must not mutate the accepted Evidence Ledger",
        );
    }

    require_limitation(
        &mut issues,
        &manifest.limitations,
        &["not", "accepted", "evidence"],
    );
    require_limitation(
        &mut issues,
        &manifest.limitations,
        &["local replay", "not", "official"],
    );
    require_limitation(
        &mut issues,
        &manifest.limitations,
        &["zk backend performance"],
    );
    require_limitation(&mut issues, &manifest.limitations, &["evidence ledger"]);

    ReportBundleValidation {
        valid: issues.is_empty(),
        issues,
        claim_boundary: ClaimBoundary::Level0DesignNote,
    }
}

fn rendered_report(
    rendered_report_id: String,
    title: String,
    artifact_uri: String,
    markdown: &str,
    source_input_ids: Vec<String>,
    failed_readiness_visible: bool,
    local_only_warnings_visible: bool,
) -> ReportBundleRenderedReport {
    ReportBundleRenderedReport {
        rendered_report_id,
        title,
        artifact_uri,
        markdown_digest: compute_artifact_digest_bytes(
            markdown.as_bytes(),
            Some(ArtifactKind::Other),
            Some(ArtifactRole::Report),
        ),
        source_input_ids,
        failed_readiness_visible,
        local_only_warnings_visible,
        claim_boundary: ClaimBoundary::Level0DesignNote,
        notes: vec!["rendered Markdown is read-only local reporting metadata".to_string()],
    }
}

fn readiness_failed(report: &PackReadinessReport, validation: &PackReadinessValidation) -> bool {
    !validation.valid || report.checks.iter().any(|check| !check.passed)
}

fn readiness_validation_notes(validation: &PackReadinessValidation) -> Vec<String> {
    if validation.valid {
        vec!["existing PackReadinessValidation metadata".to_string()]
    } else {
        vec![
            "existing PackReadinessValidation metadata".to_string(),
            "failed readiness validation must remain visible".to_string(),
        ]
    }
}

fn validate_failed_readiness_visibility(
    manifest: &ReportBundleManifest,
    issues: &mut Vec<ReportBundleValidationIssue>,
) {
    let failed_readiness_inputs: BTreeSet<&str> = manifest
        .inputs
        .iter()
        .filter(|input| {
            matches!(
                input.kind,
                ReportBundleInputKind::PackReadinessReport
                    | ReportBundleInputKind::PackReadinessValidation
            ) && input.failed_readiness
        })
        .map(|input| input.input_id.as_str())
        .collect();

    for input_id in failed_readiness_inputs {
        let visible = manifest.rendered_reports.iter().any(|rendered| {
            rendered.failed_readiness_visible
                && rendered
                    .source_input_ids
                    .iter()
                    .any(|source_input_id| source_input_id == input_id)
        });
        if !visible {
            push_issue(
                issues,
                ReportBundleValidationIssueKind::FailedReadinessHidden,
                "rendered_reports",
                format!("failed readiness input {input_id} is not visibly rendered"),
            );
        }
    }
}

fn validate_identity(
    issues: &mut Vec<ReportBundleValidationIssue>,
    path: impl Into<String>,
    value: &str,
) {
    if value.trim().is_empty() {
        push_issue(
            issues,
            ReportBundleValidationIssueKind::EmptyIdentity,
            path,
            "identity field must not be empty",
        );
    }
}

fn validate_digest(
    issues: &mut Vec<ReportBundleValidationIssue>,
    path: impl Into<String>,
    digest: &ArtifactDigest,
) {
    let path = path.into();
    if digest.algorithm != ArtifactDigestAlgorithm::Sha256 {
        push_issue(
            issues,
            ReportBundleValidationIssueKind::InvalidDigest,
            &path,
            "digest algorithm must be sha256",
        );
    }
    if digest.hex_digest.len() != 64 || !digest.hex_digest.chars().all(|ch| ch.is_ascii_hexdigit())
    {
        push_issue(
            issues,
            ReportBundleValidationIssueKind::InvalidDigest,
            &path,
            "digest must be 64 hex characters",
        );
    }
    if digest.byte_len == 0 {
        push_issue(
            issues,
            ReportBundleValidationIssueKind::InvalidDigest,
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
        && !contains_shell_payload(trimmed)
}

fn contains_shell_payload(value: &str) -> bool {
    value.contains(';')
        || value.contains('|')
        || value.contains('&')
        || value.contains('$')
        || value.contains('`')
        || value.contains("&&")
        || value.contains("||")
}

fn require_limitation(
    issues: &mut Vec<ReportBundleValidationIssue>,
    limitations: &[String],
    required_terms: &[&str],
) {
    let found = limitations.iter().any(|limitation| {
        let lower = limitation.to_ascii_lowercase();
        required_terms.iter().all(|term| lower.contains(term))
    });
    if !found {
        push_issue(
            issues,
            ReportBundleValidationIssueKind::MissingLimitation,
            "limitations",
            format!("missing limitation containing {required_terms:?}"),
        );
    }
}

fn push_issue(
    issues: &mut Vec<ReportBundleValidationIssue>,
    kind: ReportBundleValidationIssueKind,
    path: impl Into<String>,
    message: impl Into<String>,
) {
    issues.push(ReportBundleValidationIssue {
        kind,
        path: path.into(),
        message: message.into(),
    });
}
