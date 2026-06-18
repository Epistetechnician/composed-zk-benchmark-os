//! Phase Q inert report-bundle metadata.
//!
//! Report bundles are read-only local integrity summaries. They do not create
//! accepted evidence, do not execute replay commands, do not claim official
//! benchmark evidence, and do not report ZK backend performance.

use std::collections::{BTreeMap, BTreeSet};
use std::fs;
use std::path::{Component, Path};

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

/// Relative manifest path inside a materialized local report bundle.
pub const REPORT_BUNDLE_MANIFEST_PATH: &str = "report-bundle-manifest.json";

/// Relative rendered Markdown directory inside a materialized local report bundle.
pub const REPORT_BUNDLE_RENDERED_DIR: &str = "rendered";

/// Relative manifest digest sidecar path inside a materialized local report bundle.
pub const REPORT_BUNDLE_MANIFEST_DIGEST_PATH: &str = "digests/report-bundle-manifest.sha256";

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

/// Caller-supplied rendered Markdown payload for Phase Q-D materialization.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ReportBundleRenderedMarkdown {
    /// Rendered report id matching a manifest entry.
    pub rendered_report_id: String,
    /// Markdown bytes as UTF-8 text.
    pub markdown: String,
}

/// Materialized rendered Markdown file summary.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ReportBundleMaterializedReport {
    /// Rendered report id.
    pub rendered_report_id: String,
    /// Relative path written or read under the report-bundle root.
    pub relative_path: String,
    /// Digest over the Markdown bytes.
    pub markdown_digest: ArtifactDigest,
}

/// Local output summary for adjacent report-bundle files.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ReportBundleOutput {
    /// Relative path of the manifest JSON.
    pub manifest_relative_path: String,
    /// Digest over the manifest JSON bytes.
    pub manifest_digest: ArtifactDigest,
    /// Relative path of the manifest digest sidecar.
    pub manifest_digest_relative_path: String,
    /// Rendered Markdown file summaries.
    #[serde(default)]
    pub rendered_reports: Vec<ReportBundleMaterializedReport>,
    /// Manifest that was written or read.
    pub manifest: ReportBundleManifest,
    /// Validation result for the manifest.
    pub validation: ReportBundleValidation,
    /// Output claim boundary.
    pub output_claim_boundary: ClaimBoundary,
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

/// Build rendered Markdown payloads for an existing report-bundle manifest.
///
/// This helper recomputes the Phase Q rendered Markdown from the supplied
/// source reports, verifies that the rebuilt manifest matches the supplied
/// manifest, and returns payloads suitable for `write_report_bundle_outputs`.
/// It does not write files, execute replay commands, or mutate source metadata.
pub fn build_report_bundle_rendered_markdown_payloads(
    manifest: &ReportBundleManifest,
    score_reports: &[ScoreReport],
    readiness_inputs: &[ReportBundlePackReadinessInput],
) -> Result<Vec<ReportBundleRenderedMarkdown>> {
    let rebuilt_manifest = build_report_bundle_manifest_from_reports(
        manifest.bundle_id.clone(),
        score_reports,
        readiness_inputs,
    )?;
    if rebuilt_manifest.inputs != manifest.inputs {
        return Err(report_bundle_io_error(
            "report_bundle.inputs",
            "source reports do not match report-bundle manifest inputs",
        ));
    }
    if rebuilt_manifest.rendered_reports != manifest.rendered_reports {
        return Err(report_bundle_io_error(
            "report_bundle.rendered_reports",
            "source reports do not match report-bundle rendered report metadata",
        ));
    }
    build_rendered_markdown_payloads_unchecked(&manifest.bundle_id, score_reports, readiness_inputs)
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

/// Write adjacent local report-bundle output files.
///
/// The supplied `output_root` is the local `report-bundle/` directory. This
/// function writes only the manifest JSON, rendered Markdown files declared by
/// the manifest, and the manifest digest sidecar. It does not mutate source
/// packs, source reports, or accepted Evidence Ledgers.
pub fn write_report_bundle_outputs(
    output_root: impl AsRef<Path>,
    manifest: &ReportBundleManifest,
    rendered_markdown: &[ReportBundleRenderedMarkdown],
    overwrite: bool,
) -> Result<ReportBundleOutput> {
    let output_root = output_root.as_ref();
    validate_output_root(output_root)?;
    if output_root.exists() && !output_root.is_dir() {
        return Err(report_bundle_io_error(
            output_root.display().to_string(),
            "report-bundle output root exists and is not a directory",
        ));
    }

    let validation = validate_report_bundle_manifest(manifest);
    if !validation.valid {
        return Err(report_bundle_io_error(
            "report_bundle.manifest",
            format!("manifest validation failed: {:?}", validation.issues),
        ));
    }

    let targets = materialized_target_paths(manifest)?;
    if output_root.exists() && !overwrite && directory_has_entries(output_root)? {
        return Err(report_bundle_io_error(
            output_root.display().to_string(),
            "report-bundle output root is non-empty; explicit overwrite approval is required",
        ));
    }
    if output_root.exists() && overwrite {
        reject_unexpected_existing_files(output_root, &targets)?;
    }

    let payloads = rendered_markdown_by_id(rendered_markdown)?;
    let mut materialized_reports = Vec::new();
    let mut rendered_writes = Vec::new();
    for rendered in &manifest.rendered_reports {
        let markdown = payloads
            .get(rendered.rendered_report_id.as_str())
            .ok_or_else(|| {
                report_bundle_io_error(
                    format!("rendered_markdown.{}", rendered.rendered_report_id),
                    "missing rendered Markdown payload for manifest entry",
                )
            })?;
        let digest = digest_markdown_bytes(markdown.as_bytes());
        if digest != rendered.markdown_digest {
            return Err(report_bundle_io_error(
                rendered.artifact_uri.clone(),
                "rendered Markdown digest does not match manifest",
            ));
        }
        materialized_reports.push(ReportBundleMaterializedReport {
            rendered_report_id: rendered.rendered_report_id.clone(),
            relative_path: rendered.artifact_uri.clone(),
            markdown_digest: digest.clone(),
        });
        rendered_writes.push((rendered.artifact_uri.clone(), markdown.as_bytes().to_vec()));
    }
    if payloads.len() != manifest.rendered_reports.len() {
        return Err(report_bundle_io_error(
            "rendered_markdown",
            "extra rendered Markdown payload exists without a manifest entry",
        ));
    }

    let manifest_json = serialize_report_bundle_manifest_json(manifest)?;
    let manifest_bytes = manifest_json.as_bytes();
    let manifest_digest = digest_report_bundle_output_bytes(manifest_bytes);
    for (relative_path, markdown_bytes) in rendered_writes {
        write_relative_bytes(output_root, &relative_path, &markdown_bytes)?;
    }
    write_relative_bytes(output_root, REPORT_BUNDLE_MANIFEST_PATH, manifest_bytes)?;
    write_relative_bytes(
        output_root,
        REPORT_BUNDLE_MANIFEST_DIGEST_PATH,
        format!("{}\n", manifest_digest.hex_digest).as_bytes(),
    )?;

    Ok(ReportBundleOutput {
        manifest_relative_path: REPORT_BUNDLE_MANIFEST_PATH.to_string(),
        manifest_digest,
        manifest_digest_relative_path: REPORT_BUNDLE_MANIFEST_DIGEST_PATH.to_string(),
        rendered_reports: materialized_reports,
        manifest: manifest.clone(),
        validation,
        output_claim_boundary: ClaimBoundary::Level0DesignNote,
    })
}

/// Read and validate adjacent local report-bundle output files.
///
/// A successful read confirms local file integrity only. It is not accepted
/// evidence, not official benchmark evidence, and not ZK backend performance
/// evidence.
pub fn read_report_bundle_outputs(output_root: impl AsRef<Path>) -> Result<ReportBundleOutput> {
    let output_root = output_root.as_ref();
    validate_output_root(output_root)?;

    let manifest_bytes = read_relative_bytes(output_root, REPORT_BUNDLE_MANIFEST_PATH)?;
    let digest_sidecar = String::from_utf8(read_relative_bytes(
        output_root,
        REPORT_BUNDLE_MANIFEST_DIGEST_PATH,
    )?)
    .map_err(|error| {
        report_bundle_io_error(
            REPORT_BUNDLE_MANIFEST_DIGEST_PATH,
            format!("manifest digest sidecar is not UTF-8: {error}"),
        )
    })?;
    let manifest_digest = digest_report_bundle_output_bytes(&manifest_bytes);
    if digest_sidecar.trim() != manifest_digest.hex_digest {
        return Err(report_bundle_io_error(
            REPORT_BUNDLE_MANIFEST_DIGEST_PATH,
            "manifest JSON bytes do not match digest sidecar",
        ));
    }

    let manifest_json = String::from_utf8(manifest_bytes).map_err(|error| {
        report_bundle_io_error(
            REPORT_BUNDLE_MANIFEST_PATH,
            format!("manifest JSON is not UTF-8: {error}"),
        )
    })?;
    let manifest = deserialize_report_bundle_manifest_json(&manifest_json)?;
    let validation = validate_report_bundle_manifest(&manifest);
    if !validation.valid {
        return Err(report_bundle_io_error(
            "report_bundle.manifest",
            format!("manifest validation failed: {:?}", validation.issues),
        ));
    }

    let expected_paths = rendered_report_paths(&manifest)?;
    reject_extra_rendered_files(output_root, &expected_paths)?;

    let mut materialized_reports = Vec::new();
    for rendered in &manifest.rendered_reports {
        let markdown_bytes = read_relative_bytes(output_root, &rendered.artifact_uri)?;
        let markdown_digest = digest_markdown_bytes(&markdown_bytes);
        if markdown_digest != rendered.markdown_digest {
            return Err(report_bundle_io_error(
                rendered.artifact_uri.clone(),
                "rendered Markdown bytes do not match manifest digest",
            ));
        }
        materialized_reports.push(ReportBundleMaterializedReport {
            rendered_report_id: rendered.rendered_report_id.clone(),
            relative_path: rendered.artifact_uri.clone(),
            markdown_digest,
        });
    }

    Ok(ReportBundleOutput {
        manifest_relative_path: REPORT_BUNDLE_MANIFEST_PATH.to_string(),
        manifest_digest,
        manifest_digest_relative_path: REPORT_BUNDLE_MANIFEST_DIGEST_PATH.to_string(),
        rendered_reports: materialized_reports,
        manifest,
        validation,
        output_claim_boundary: ClaimBoundary::Level0DesignNote,
    })
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
    let mut rendered_artifact_uris = BTreeSet::new();
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
        if !rendered_artifact_uris.insert(rendered.artifact_uri.clone()) {
            push_issue(
                &mut issues,
                ReportBundleValidationIssueKind::InvalidArtifactRef,
                format!("{path}.artifact_uri"),
                "rendered report output URIs must be unique",
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

fn build_rendered_markdown_payloads_unchecked(
    bundle_id: &str,
    score_reports: &[ScoreReport],
    readiness_inputs: &[ReportBundlePackReadinessInput],
) -> Result<Vec<ReportBundleRenderedMarkdown>> {
    let mut payloads = Vec::new();
    for (index, report) in score_reports.iter().enumerate() {
        let input_id = format!("score_report_{index}");
        let dashboard_id = format!("{bundle_id}_{input_id}_dashboard");
        let model = build_dashboard_model_from_score_report(&dashboard_id, report);
        payloads.push(ReportBundleRenderedMarkdown {
            rendered_report_id: format!("{input_id}_markdown"),
            markdown: render_dashboard_markdown(&model),
        });
    }

    for (index, source) in readiness_inputs.iter().enumerate() {
        let report_input_id = format!("pack_readiness_report_{index}");
        let dashboard_id = format!("{bundle_id}_{report_input_id}_dashboard");
        let model = build_dashboard_model_from_pack_readiness(
            &dashboard_id,
            &source.report,
            &source.validation,
        );
        payloads.push(ReportBundleRenderedMarkdown {
            rendered_report_id: format!("{report_input_id}_markdown"),
            markdown: render_dashboard_markdown(&model),
        });
    }
    Ok(payloads)
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

fn rendered_markdown_by_id(
    rendered_markdown: &[ReportBundleRenderedMarkdown],
) -> Result<BTreeMap<&str, &str>> {
    let mut payloads = BTreeMap::new();
    for payload in rendered_markdown {
        validate_output_identity(
            "rendered_markdown.rendered_report_id",
            &payload.rendered_report_id,
        )?;
        if payload.markdown.is_empty() {
            return Err(report_bundle_io_error(
                format!("rendered_markdown.{}", payload.rendered_report_id),
                "rendered Markdown payload must not be empty",
            ));
        }
        if payloads
            .insert(
                payload.rendered_report_id.as_str(),
                payload.markdown.as_str(),
            )
            .is_some()
        {
            return Err(report_bundle_io_error(
                format!("rendered_markdown.{}", payload.rendered_report_id),
                "duplicate rendered Markdown payload id",
            ));
        }
    }
    Ok(payloads)
}

fn materialized_target_paths(manifest: &ReportBundleManifest) -> Result<BTreeSet<String>> {
    let mut targets = BTreeSet::from([
        REPORT_BUNDLE_MANIFEST_PATH.to_string(),
        REPORT_BUNDLE_MANIFEST_DIGEST_PATH.to_string(),
    ]);
    for rendered in &manifest.rendered_reports {
        validate_rendered_markdown_path(&rendered.artifact_uri)?;
        if !targets.insert(rendered.artifact_uri.clone()) {
            return Err(report_bundle_io_error(
                rendered.artifact_uri.clone(),
                "duplicate materialized report output path",
            ));
        }
    }
    Ok(targets)
}

fn rendered_report_paths(manifest: &ReportBundleManifest) -> Result<BTreeSet<String>> {
    manifest
        .rendered_reports
        .iter()
        .map(|rendered| {
            validate_rendered_markdown_path(&rendered.artifact_uri)?;
            Ok(rendered.artifact_uri.clone())
        })
        .collect()
}

fn validate_output_root(root: &Path) -> Result<()> {
    let value = root.as_os_str().to_string_lossy();
    if value.trim().is_empty() || value.contains("://") || value.contains('\\') {
        return Err(report_bundle_io_error(
            value.to_string(),
            "invalid report-bundle output root",
        ));
    }
    if root
        .components()
        .any(|component| matches!(component, Component::ParentDir))
    {
        return Err(report_bundle_io_error(
            value.to_string(),
            "report-bundle output root must not contain parent-directory components",
        ));
    }
    Ok(())
}

fn validate_rendered_markdown_path(relative_path: &str) -> Result<()> {
    validate_relative_output_path(relative_path)?;
    if !relative_path.starts_with(&format!("{REPORT_BUNDLE_RENDERED_DIR}/"))
        || !relative_path.ends_with(".md")
    {
        return Err(report_bundle_io_error(
            relative_path,
            "rendered report path must live under rendered/ and end with .md",
        ));
    }
    Ok(())
}

fn validate_relative_output_path(relative_path: &str) -> Result<()> {
    let path = Path::new(relative_path);
    if relative_path.trim().is_empty()
        || path.is_absolute()
        || relative_path.contains("..")
        || relative_path.contains('\\')
        || relative_path.contains("://")
        || contains_shell_payload(relative_path)
    {
        return Err(report_bundle_io_error(
            relative_path,
            "invalid report-bundle relative output path",
        ));
    }
    Ok(())
}

fn validate_output_identity(path: &str, value: &str) -> Result<()> {
    if value.trim().is_empty() || contains_shell_payload(value) || value.contains('/') {
        return Err(report_bundle_io_error(
            path,
            "invalid report-bundle output identity",
        ));
    }
    Ok(())
}

fn read_relative_bytes(root: &Path, relative_path: &str) -> Result<Vec<u8>> {
    validate_relative_output_path(relative_path)?;
    let path = root.join(relative_path);
    fs::read(&path).map_err(|error| report_bundle_io_error(path.display().to_string(), error))
}

fn write_relative_bytes(root: &Path, relative_path: &str, bytes: &[u8]) -> Result<()> {
    validate_relative_output_path(relative_path)?;
    let path = root.join(relative_path);
    if let Some(parent) = path.parent() {
        fs::create_dir_all(parent)
            .map_err(|error| report_bundle_io_error(parent.display().to_string(), error))?;
    }
    fs::write(&path, bytes)
        .map_err(|error| report_bundle_io_error(path.display().to_string(), error))
}

fn directory_has_entries(path: &Path) -> Result<bool> {
    let mut entries = fs::read_dir(path)
        .map_err(|error| report_bundle_io_error(path.display().to_string(), error))?;
    entries
        .next()
        .transpose()
        .map(|entry| entry.is_some())
        .map_err(|error| report_bundle_io_error(path.display().to_string(), error))
}

fn reject_unexpected_existing_files(root: &Path, expected: &BTreeSet<String>) -> Result<()> {
    let existing = collect_relative_files(root)?;
    for relative_path in existing {
        if !expected.contains(&relative_path) {
            return Err(report_bundle_io_error(
                relative_path,
                "existing report-bundle output root contains an unexpected file",
            ));
        }
    }
    Ok(())
}

fn reject_extra_rendered_files(root: &Path, expected: &BTreeSet<String>) -> Result<()> {
    let rendered_root = root.join(REPORT_BUNDLE_RENDERED_DIR);
    if !rendered_root.exists() {
        return Ok(());
    }
    for relative_path in collect_relative_files(&rendered_root)? {
        let bundle_relative_path = format!("{REPORT_BUNDLE_RENDERED_DIR}/{relative_path}");
        if !expected.contains(&bundle_relative_path) {
            return Err(report_bundle_io_error(
                bundle_relative_path,
                "rendered Markdown file exists without a manifest entry",
            ));
        }
    }
    Ok(())
}

fn collect_relative_files(root: &Path) -> Result<BTreeSet<String>> {
    let mut files = BTreeSet::new();
    if !root.exists() {
        return Ok(files);
    }
    collect_relative_files_inner(root, root, &mut files)?;
    Ok(files)
}

fn collect_relative_files_inner(
    root: &Path,
    current: &Path,
    files: &mut BTreeSet<String>,
) -> Result<()> {
    for entry in fs::read_dir(current)
        .map_err(|error| report_bundle_io_error(current.display().to_string(), error))?
    {
        let entry =
            entry.map_err(|error| report_bundle_io_error(current.display().to_string(), error))?;
        let file_type = entry
            .file_type()
            .map_err(|error| report_bundle_io_error(entry.path().display().to_string(), error))?;
        if file_type.is_symlink() {
            return Err(report_bundle_io_error(
                entry.path().display().to_string(),
                "report-bundle output must not contain symlinks",
            ));
        }
        if file_type.is_dir() {
            collect_relative_files_inner(root, &entry.path(), files)?;
        } else if file_type.is_file() {
            let relative_path = slash_relative_path(root, &entry.path())?;
            validate_relative_output_path(&relative_path)?;
            files.insert(relative_path);
        }
    }
    Ok(())
}

fn slash_relative_path(root: &Path, path: &Path) -> Result<String> {
    let relative_path = path
        .strip_prefix(root)
        .map_err(|error| report_bundle_io_error(path.display().to_string(), error))?;
    let mut parts = Vec::new();
    for component in relative_path.components() {
        match component {
            Component::Normal(value) => parts.push(value.to_string_lossy().to_string()),
            _ => {
                return Err(report_bundle_io_error(
                    relative_path.display().to_string(),
                    "invalid report-bundle relative path component",
                ))
            }
        }
    }
    Ok(parts.join("/"))
}

fn digest_report_bundle_output_bytes(bytes: &[u8]) -> ArtifactDigest {
    compute_artifact_digest_bytes(bytes, Some(ArtifactKind::Other), Some(ArtifactRole::Report))
}

fn digest_markdown_bytes(bytes: &[u8]) -> ArtifactDigest {
    compute_artifact_digest_bytes(bytes, Some(ArtifactKind::Other), Some(ArtifactRole::Report))
}

fn report_bundle_io_error(path: impl Into<String>, message: impl ToString) -> ZkBenchError {
    ZkBenchError::benchmark_pack(path, message.to_string())
}
