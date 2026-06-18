//! Phase R inert local audit-index metadata.
//!
//! Audit indexes are read-only local integrity summaries over existing local
//! metadata. They do not create accepted evidence, execute replay commands,
//! claim official benchmark evidence, or report ZK backend performance.

use std::collections::BTreeSet;

use serde::{Deserialize, Serialize};

use crate::error::{Result, ZkBenchError};
use crate::evidence::{
    compute_artifact_digest, compute_artifact_digest_bytes, ArtifactDigest,
    ArtifactDigestAlgorithm, ArtifactKind, ArtifactRole, ClaimBoundary,
};
use crate::report_bundle::{
    compute_report_bundle_manifest_digest, ReportBundleInputKind, ReportBundleManifest,
    REPORT_BUNDLE_MANIFEST_DIGEST_PATH, REPORT_BUNDLE_MANIFEST_PATH,
};

/// Phase R audit-index schema version.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct LocalAuditIndexVersion {
    /// Logical version string.
    pub value: String,
}

impl Default for LocalAuditIndexVersion {
    fn default() -> Self {
        Self {
            value: "phase-r-local-audit-index-v0".to_string(),
        }
    }
}

/// Local audit-index input kind.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
pub enum LocalAuditIndexInputKind {
    /// Existing benchmark pack manifest metadata.
    BenchmarkPackManifest,
    /// Existing pack-readiness report metadata.
    PackReadinessReport,
    /// Existing pack-readiness validation metadata.
    PackReadinessValidation,
    /// Existing score report metadata.
    ScoreReport,
    /// Existing report-bundle manifest metadata.
    ReportBundleManifest,
    /// Existing report-bundle rendered Markdown metadata.
    ReportBundleRenderedMarkdown,
    /// Existing report-bundle manifest digest sidecar metadata.
    ReportBundleDigestSidecar,
    /// Other local metadata.
    OtherLocalMetadata,
}

/// Source reference included in a local audit index.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct LocalAuditIndexInputRef {
    /// Logical input id.
    pub input_id: String,
    /// Portable relative artifact URI or logical metadata path.
    pub artifact_uri: String,
    /// Input kind.
    pub kind: LocalAuditIndexInputKind,
    /// Stable digest over the referenced local metadata bytes.
    pub digest: ArtifactDigest,
    /// Input claim boundary.
    pub claim_boundary: ClaimBoundary,
    /// True when this input represents failed pack-readiness or validation state.
    #[serde(default)]
    pub failed_readiness: bool,
    /// True when local-only warnings remain visible for this input.
    #[serde(default)]
    pub local_only_warnings_visible: bool,
    /// Source input ids summarized by this input, when applicable.
    #[serde(default)]
    pub source_input_ids: Vec<String>,
    /// Notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

/// Inert local audit-index manifest.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct LocalAuditIndexManifest {
    /// Index id.
    pub index_id: String,
    /// Schema version.
    pub version: LocalAuditIndexVersion,
    /// Local pack or pack-family id being indexed.
    pub indexed_pack_id: String,
    /// Referenced report-bundle ids.
    #[serde(default)]
    pub report_bundle_ids: Vec<String>,
    /// Source inputs.
    #[serde(default)]
    pub inputs: Vec<LocalAuditIndexInputRef>,
    /// Human-readable claim-boundary summary.
    #[serde(default)]
    pub claim_boundary_summary: Vec<String>,
    /// Whether failed readiness is visible in the index.
    #[serde(default)]
    pub failed_readiness_visible: bool,
    /// Whether local-only warnings are visible in the index.
    #[serde(default)]
    pub local_only_warnings_visible: bool,
    /// Whether this index claims to mutate source pack metadata.
    #[serde(default)]
    pub mutates_source_pack: bool,
    /// Whether this index claims to mutate source report metadata.
    #[serde(default)]
    pub mutates_source_report: bool,
    /// Whether this index claims to mutate report-bundle metadata.
    #[serde(default)]
    pub mutates_report_bundle: bool,
    /// Whether this index includes replay-command execution output.
    #[serde(default)]
    pub replay_command_execution_output: bool,
    /// Whether external replay is authorized or claimed.
    #[serde(default)]
    pub external_replay_authorized: bool,
    /// Whether this index claims to create Level2 evidence.
    #[serde(default)]
    pub creates_level2_evidence: bool,
    /// Whether this index claims official benchmark evidence.
    #[serde(default)]
    pub official_benchmark_evidence: bool,
    /// Whether this index claims ZK backend performance evidence.
    #[serde(default)]
    pub zk_backend_performance_claims: bool,
    /// Whether this index mutates or claims to mutate the accepted Evidence Ledger.
    #[serde(default)]
    pub mutates_accepted_evidence_ledger: bool,
    /// Whether this index populates score axes from local-only metadata.
    #[serde(default)]
    pub populates_score_axes_from_local_only: bool,
    /// Output claim boundary for the index.
    pub output_claim_boundary: ClaimBoundary,
    /// Explicit limitations.
    #[serde(default)]
    pub limitations: Vec<String>,
    /// Notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

/// Local audit-index validation issue kind.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum LocalAuditIndexValidationIssueKind {
    /// Required identity field is empty.
    EmptyIdentity,
    /// Source inputs are missing.
    MissingInputs,
    /// Duplicate source input id.
    DuplicateInputId,
    /// Duplicate source artifact URI.
    DuplicateArtifactUri,
    /// Source reference is missing.
    MissingSourceRef,
    /// Artifact reference is not portable relative metadata.
    InvalidArtifactRef,
    /// Digest is missing, unsupported, or malformed.
    InvalidDigest,
    /// Index or input claim boundary is too high.
    ClaimBoundaryEscalation,
    /// Failed pack-readiness state was hidden.
    FailedReadinessHidden,
    /// Local-only warnings were hidden.
    LocalOnlyWarningsHidden,
    /// Source pack/report/bundle mutation was claimed.
    SourceMutationClaim,
    /// Index included replay-command execution output.
    ReplayCommandExecutionOutput,
    /// Index authorized or claimed external replay.
    ExternalReplayAuthorized,
    /// Index claimed to create Level2 evidence.
    Level2EvidenceClaim,
    /// Index claimed official benchmark evidence.
    OfficialBenchmarkEvidenceClaim,
    /// Index claimed ZK backend performance.
    ZkBackendPerformanceClaim,
    /// Index claimed accepted Evidence Ledger mutation.
    AcceptedEvidenceLedgerMutationClaim,
    /// Index populated score axes from local-only metadata.
    LocalOnlyScoreAxisPopulation,
    /// Required limitation text is missing.
    MissingLimitation,
}

/// Local audit-index validation issue.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct LocalAuditIndexValidationIssue {
    /// Issue kind.
    pub kind: LocalAuditIndexValidationIssueKind,
    /// Issue path.
    pub path: String,
    /// Issue message.
    pub message: String,
}

/// Local audit-index validation result.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct LocalAuditIndexValidation {
    /// Whether validation passed.
    pub valid: bool,
    /// Validation issues.
    #[serde(default)]
    pub issues: Vec<LocalAuditIndexValidationIssue>,
    /// Claim boundary of this validation report.
    pub claim_boundary: ClaimBoundary,
}

/// Build an inert local audit-index manifest from existing report-bundle
/// metadata.
///
/// This function does not write files, execute replay commands, call external
/// backends, import results, or mutate source packs, source reports, report
/// bundles, or the accepted Evidence Ledger.
pub fn build_local_audit_index_manifest_from_report_bundles(
    index_id: impl Into<String>,
    indexed_pack_id: impl Into<String>,
    report_bundles: &[ReportBundleManifest],
) -> Result<LocalAuditIndexManifest> {
    let mut inputs = Vec::new();
    let mut report_bundle_ids = Vec::new();
    let mut any_failed_readiness = false;
    let mut all_local_only_warnings_visible = true;

    for (bundle_index, bundle) in report_bundles.iter().enumerate() {
        let bundle_prefix = format!("report_bundles/{bundle_index}");
        report_bundle_ids.push(bundle.bundle_id.clone());

        let manifest_digest = compute_report_bundle_manifest_digest(bundle)?;
        inputs.push(LocalAuditIndexInputRef {
            input_id: format!("report_bundle_manifest_{bundle_index}"),
            artifact_uri: format!("{bundle_prefix}/{REPORT_BUNDLE_MANIFEST_PATH}"),
            kind: LocalAuditIndexInputKind::ReportBundleManifest,
            digest: manifest_digest.clone(),
            claim_boundary: bundle.output_claim_boundary,
            failed_readiness: bundle.inputs.iter().any(|input| input.failed_readiness),
            local_only_warnings_visible: bundle
                .rendered_reports
                .iter()
                .all(|rendered| rendered.local_only_warnings_visible),
            source_input_ids: Vec::new(),
            notes: vec!["existing report-bundle manifest metadata".to_string()],
        });

        let sidecar_digest = compute_artifact_digest_bytes(
            manifest_digest.hex_digest.as_bytes(),
            Some(ArtifactKind::Other),
            Some(ArtifactRole::Report),
        );
        inputs.push(LocalAuditIndexInputRef {
            input_id: format!("report_bundle_manifest_digest_{bundle_index}"),
            artifact_uri: format!("{bundle_prefix}/{REPORT_BUNDLE_MANIFEST_DIGEST_PATH}"),
            kind: LocalAuditIndexInputKind::ReportBundleDigestSidecar,
            digest: sidecar_digest,
            claim_boundary: ClaimBoundary::Level0DesignNote,
            failed_readiness: false,
            local_only_warnings_visible: true,
            source_input_ids: vec![format!("report_bundle_manifest_{bundle_index}")],
            notes: vec!["existing report-bundle manifest digest sidecar metadata".to_string()],
        });

        for source in &bundle.inputs {
            any_failed_readiness |= source.failed_readiness;
            inputs.push(LocalAuditIndexInputRef {
                input_id: format!("report_bundle_{bundle_index}_{}", source.input_id),
                artifact_uri: format!("{bundle_prefix}/sources/{}", source.artifact_uri),
                kind: map_report_bundle_input_kind(source.kind),
                digest: source.digest.clone(),
                claim_boundary: source.claim_boundary,
                failed_readiness: source.failed_readiness,
                local_only_warnings_visible: true,
                source_input_ids: Vec::new(),
                notes: vec!["existing report-bundle source input metadata".to_string()],
            });
        }

        for rendered in &bundle.rendered_reports {
            all_local_only_warnings_visible &=
                rendered.local_only_warnings_visible && bundle.local_only_warnings_visible();
            inputs.push(LocalAuditIndexInputRef {
                input_id: format!(
                    "report_bundle_{bundle_index}_{}",
                    rendered.rendered_report_id
                ),
                artifact_uri: format!("{bundle_prefix}/{}", rendered.artifact_uri),
                kind: LocalAuditIndexInputKind::ReportBundleRenderedMarkdown,
                digest: rendered.markdown_digest.clone(),
                claim_boundary: rendered.claim_boundary,
                failed_readiness: rendered.failed_readiness_visible,
                local_only_warnings_visible: rendered.local_only_warnings_visible,
                source_input_ids: rendered
                    .source_input_ids
                    .iter()
                    .map(|source_id| format!("report_bundle_{bundle_index}_{source_id}"))
                    .collect(),
                notes: vec!["existing report-bundle rendered Markdown metadata".to_string()],
            });
        }
    }

    Ok(LocalAuditIndexManifest {
        index_id: index_id.into(),
        version: LocalAuditIndexVersion::default(),
        indexed_pack_id: indexed_pack_id.into(),
        report_bundle_ids,
        inputs,
        claim_boundary_summary: vec![
            "Audit indexes are not accepted evidence.".to_string(),
            "Audit indexes are local integrity summaries, not official benchmark evidence."
                .to_string(),
            "Audit indexes do not create Level2+ evidence.".to_string(),
            "Audit indexes do not prove backend performance.".to_string(),
            "Local replay artifacts are not official benchmark evidence.".to_string(),
            "Internal timing telemetry is not ZK backend performance.".to_string(),
        ],
        failed_readiness_visible: any_failed_readiness,
        local_only_warnings_visible: all_local_only_warnings_visible,
        mutates_source_pack: false,
        mutates_source_report: false,
        mutates_report_bundle: false,
        replay_command_execution_output: false,
        external_replay_authorized: false,
        creates_level2_evidence: false,
        official_benchmark_evidence: false,
        zk_backend_performance_claims: false,
        mutates_accepted_evidence_ledger: false,
        populates_score_axes_from_local_only: false,
        output_claim_boundary: ClaimBoundary::Level0DesignNote,
        limitations: vec![
            "Audit indexes are not accepted evidence.".to_string(),
            "Audit indexes are local integrity summaries, not official benchmark evidence."
                .to_string(),
            "Audit indexes do not create Level2+ evidence.".to_string(),
            "Audit indexes do not prove ZK backend performance.".to_string(),
            "Audit indexes do not mutate source packs, source reports, report bundles, or the accepted Evidence Ledger.".to_string(),
        ],
        notes: vec![
            "constructed from existing local report-bundle metadata only".to_string(),
            "no audit-index files were generated by this manifest builder".to_string(),
        ],
    })
}

/// Compute a deterministic digest for a local audit-index manifest.
pub fn compute_local_audit_index_manifest_digest(
    manifest: &LocalAuditIndexManifest,
) -> Result<ArtifactDigest> {
    compute_artifact_digest(
        manifest,
        Some(ArtifactKind::Other),
        Some(ArtifactRole::Report),
    )
}

/// Serialize a local audit-index manifest to pretty JSON.
pub fn serialize_local_audit_index_manifest_json(
    manifest: &LocalAuditIndexManifest,
) -> Result<String> {
    serde_json::to_string_pretty(manifest)
        .map_err(|error| ZkBenchError::serialization("audit_index.manifest", error.to_string()))
}

/// Deserialize a local audit-index manifest from JSON.
pub fn deserialize_local_audit_index_manifest_json(json: &str) -> Result<LocalAuditIndexManifest> {
    serde_json::from_str(json)
        .map_err(|error| ZkBenchError::deserialization("audit_index.manifest", error.to_string()))
}

/// Validate local audit-index metadata.
pub fn validate_local_audit_index_manifest(
    manifest: &LocalAuditIndexManifest,
) -> LocalAuditIndexValidation {
    let mut issues = Vec::new();

    validate_identity(&mut issues, "index_id", &manifest.index_id);
    validate_identity(&mut issues, "version.value", &manifest.version.value);
    validate_identity(&mut issues, "indexed_pack_id", &manifest.indexed_pack_id);

    if manifest.inputs.is_empty() {
        push_issue(
            &mut issues,
            LocalAuditIndexValidationIssueKind::MissingInputs,
            "inputs",
            "audit index must bind at least one existing local metadata input",
        );
    }

    let mut input_ids = BTreeSet::new();
    let mut artifact_uris = BTreeSet::new();
    for (index, input) in manifest.inputs.iter().enumerate() {
        let path = format!("inputs[{index}]");
        validate_identity(&mut issues, format!("{path}.input_id"), &input.input_id);
        if !input_ids.insert(input.input_id.clone()) {
            push_issue(
                &mut issues,
                LocalAuditIndexValidationIssueKind::DuplicateInputId,
                format!("{path}.input_id"),
                "input ids must be unique",
            );
        }
        if !artifact_uris.insert(input.artifact_uri.clone()) {
            push_issue(
                &mut issues,
                LocalAuditIndexValidationIssueKind::DuplicateArtifactUri,
                format!("{path}.artifact_uri"),
                "audit-index artifact URIs must be unique",
            );
        }
        if !is_portable_relative_artifact_ref(&input.artifact_uri) {
            push_issue(
                &mut issues,
                LocalAuditIndexValidationIssueKind::InvalidArtifactRef,
                format!("{path}.artifact_uri"),
                "input artifact URI must be portable relative metadata",
            );
        }
        validate_digest(&mut issues, format!("{path}.digest"), &input.digest);
        if input.claim_boundary > ClaimBoundary::Level1LocalReplay {
            push_issue(
                &mut issues,
                LocalAuditIndexValidationIssueKind::ClaimBoundaryEscalation,
                format!("{path}.claim_boundary"),
                "Phase R local audit-index inputs must remain Level1LocalReplay or lower",
            );
        }
        if input.failed_readiness && !manifest.failed_readiness_visible {
            push_issue(
                &mut issues,
                LocalAuditIndexValidationIssueKind::FailedReadinessHidden,
                format!("{path}.failed_readiness"),
                "failed readiness input is hidden by the audit index",
            );
        }
        if matches!(
            input.kind,
            LocalAuditIndexInputKind::ReportBundleManifest
                | LocalAuditIndexInputKind::ReportBundleRenderedMarkdown
        ) && !input.local_only_warnings_visible
        {
            push_issue(
                &mut issues,
                LocalAuditIndexValidationIssueKind::LocalOnlyWarningsHidden,
                format!("{path}.local_only_warnings_visible"),
                "report-bundle local-only warnings must remain visible",
            );
        }
    }

    for (index, input) in manifest.inputs.iter().enumerate() {
        for (source_index, source_input_id) in input.source_input_ids.iter().enumerate() {
            if !input_ids.contains(source_input_id) {
                push_issue(
                    &mut issues,
                    LocalAuditIndexValidationIssueKind::MissingSourceRef,
                    format!("inputs[{index}].source_input_ids[{source_index}]"),
                    "audit-index input references an unknown source input id",
                );
            }
        }
    }

    if manifest.output_claim_boundary != ClaimBoundary::Level0DesignNote {
        push_issue(
            &mut issues,
            LocalAuditIndexValidationIssueKind::ClaimBoundaryEscalation,
            "output_claim_boundary",
            "Phase R audit-index output must remain Level0DesignNote",
        );
    }
    if !manifest.local_only_warnings_visible {
        push_issue(
            &mut issues,
            LocalAuditIndexValidationIssueKind::LocalOnlyWarningsHidden,
            "local_only_warnings_visible",
            "audit indexes must keep local-only warnings visible",
        );
    }
    if manifest.mutates_source_pack
        || manifest.mutates_source_report
        || manifest.mutates_report_bundle
    {
        push_issue(
            &mut issues,
            LocalAuditIndexValidationIssueKind::SourceMutationClaim,
            "source_mutation_flags",
            "audit indexes must not mutate source packs, source reports, or report bundles",
        );
    }
    if manifest.replay_command_execution_output {
        push_issue(
            &mut issues,
            LocalAuditIndexValidationIssueKind::ReplayCommandExecutionOutput,
            "replay_command_execution_output",
            "audit indexes must not include replay-command execution output",
        );
    }
    if manifest.external_replay_authorized {
        push_issue(
            &mut issues,
            LocalAuditIndexValidationIssueKind::ExternalReplayAuthorized,
            "external_replay_authorized",
            "audit indexes must not authorize external replay",
        );
    }
    if manifest.creates_level2_evidence {
        push_issue(
            &mut issues,
            LocalAuditIndexValidationIssueKind::Level2EvidenceClaim,
            "creates_level2_evidence",
            "audit indexes do not create Level2+ evidence",
        );
    }
    if manifest.official_benchmark_evidence {
        push_issue(
            &mut issues,
            LocalAuditIndexValidationIssueKind::OfficialBenchmarkEvidenceClaim,
            "official_benchmark_evidence",
            "audit indexes are not official benchmark evidence",
        );
    }
    if manifest.zk_backend_performance_claims {
        push_issue(
            &mut issues,
            LocalAuditIndexValidationIssueKind::ZkBackendPerformanceClaim,
            "zk_backend_performance_claims",
            "audit indexes do not prove ZK backend performance",
        );
    }
    if manifest.mutates_accepted_evidence_ledger {
        push_issue(
            &mut issues,
            LocalAuditIndexValidationIssueKind::AcceptedEvidenceLedgerMutationClaim,
            "mutates_accepted_evidence_ledger",
            "audit indexes must not mutate the accepted Evidence Ledger",
        );
    }
    if manifest.populates_score_axes_from_local_only {
        push_issue(
            &mut issues,
            LocalAuditIndexValidationIssueKind::LocalOnlyScoreAxisPopulation,
            "populates_score_axes_from_local_only",
            "audit indexes must not populate score axes from local-only metadata",
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
        &["official", "benchmark", "evidence"],
    );
    require_limitation(&mut issues, &manifest.limitations, &["level2"]);
    require_limitation(
        &mut issues,
        &manifest.limitations,
        &["zk", "backend", "performance"],
    );
    require_limitation(&mut issues, &manifest.limitations, &["evidence ledger"]);

    LocalAuditIndexValidation {
        valid: issues.is_empty(),
        issues,
        claim_boundary: ClaimBoundary::Level0DesignNote,
    }
}

fn map_report_bundle_input_kind(kind: ReportBundleInputKind) -> LocalAuditIndexInputKind {
    match kind {
        ReportBundleInputKind::ScoreReport => LocalAuditIndexInputKind::ScoreReport,
        ReportBundleInputKind::PackReadinessReport => LocalAuditIndexInputKind::PackReadinessReport,
        ReportBundleInputKind::PackReadinessValidation => {
            LocalAuditIndexInputKind::PackReadinessValidation
        }
        ReportBundleInputKind::RenderedMarkdown => {
            LocalAuditIndexInputKind::ReportBundleRenderedMarkdown
        }
        ReportBundleInputKind::OtherLocalMetadata => LocalAuditIndexInputKind::OtherLocalMetadata,
    }
}

trait ReportBundleWarningVisibility {
    fn local_only_warnings_visible(&self) -> bool;
}

impl ReportBundleWarningVisibility for ReportBundleManifest {
    fn local_only_warnings_visible(&self) -> bool {
        self.rendered_reports
            .iter()
            .all(|rendered| rendered.local_only_warnings_visible)
    }
}

fn validate_identity(
    issues: &mut Vec<LocalAuditIndexValidationIssue>,
    path: impl Into<String>,
    value: &str,
) {
    if value.trim().is_empty() {
        push_issue(
            issues,
            LocalAuditIndexValidationIssueKind::EmptyIdentity,
            path,
            "identity field must not be empty",
        );
    }
}

fn validate_digest(
    issues: &mut Vec<LocalAuditIndexValidationIssue>,
    path: impl Into<String>,
    digest: &ArtifactDigest,
) {
    let path = path.into();
    if digest.algorithm != ArtifactDigestAlgorithm::Sha256 {
        push_issue(
            issues,
            LocalAuditIndexValidationIssueKind::InvalidDigest,
            &path,
            "digest algorithm must be sha256",
        );
    }
    if digest.hex_digest.len() != 64 || !digest.hex_digest.chars().all(|ch| ch.is_ascii_hexdigit())
    {
        push_issue(
            issues,
            LocalAuditIndexValidationIssueKind::InvalidDigest,
            &path,
            "digest must be 64 hex characters",
        );
    }
    if digest.byte_len == 0 {
        push_issue(
            issues,
            LocalAuditIndexValidationIssueKind::InvalidDigest,
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
    issues: &mut Vec<LocalAuditIndexValidationIssue>,
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
            LocalAuditIndexValidationIssueKind::MissingLimitation,
            "limitations",
            format!("missing limitation containing {required_terms:?}"),
        );
    }
}

fn push_issue(
    issues: &mut Vec<LocalAuditIndexValidationIssue>,
    kind: LocalAuditIndexValidationIssueKind,
    path: impl Into<String>,
    message: impl Into<String>,
) {
    issues.push(LocalAuditIndexValidationIssue {
        kind,
        path: path.into(),
        message: message.into(),
    });
}
