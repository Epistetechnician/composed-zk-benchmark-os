//! Phase R inert local audit-index metadata and Phase S in-memory ergonomics views.
//!
//! Audit indexes are read-only local integrity summaries over existing local
//! metadata. They do not create accepted evidence, execute replay commands,
//! claim official benchmark evidence, or report ZK backend performance.

use std::collections::{BTreeMap, BTreeSet};
use std::fs;
use std::path::{Component, Path};

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

/// Adjacent local audit-index manifest path below an `audit-index/` root.
pub const AUDIT_INDEX_MANIFEST_PATH: &str = "audit-index-manifest.json";

/// Adjacent local audit-index manifest digest sidecar path below an
/// `audit-index/` root.
pub const AUDIT_INDEX_MANIFEST_DIGEST_PATH: &str = "digests/audit-index-manifest.sha256";

/// Phase S ergonomics selected-view JSON path below an
/// `audit-index-ergonomics/` root.
pub const AUDIT_INDEX_ERGONOMICS_VIEW_PATH: &str = "ergonomics-view.json";

/// Phase S ergonomics rendered Markdown path below an
/// `audit-index-ergonomics/` root.
pub const AUDIT_INDEX_ERGONOMICS_MARKDOWN_PATH: &str = "rendered/ergonomics-view.md";

/// Phase S ergonomics selected-view JSON digest sidecar path below an
/// `audit-index-ergonomics/` root.
pub const AUDIT_INDEX_ERGONOMICS_VIEW_DIGEST_PATH: &str = "digests/ergonomics-view-json.sha256";

/// Phase S ergonomics rendered Markdown digest sidecar path below an
/// `audit-index-ergonomics/` root.
pub const AUDIT_INDEX_ERGONOMICS_MARKDOWN_DIGEST_PATH: &str =
    "digests/ergonomics-view-markdown.sha256";

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

/// Materialized adjacent local audit-index output summary.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct LocalAuditIndexOutput {
    /// Manifest path relative to the caller-supplied `audit-index/` root.
    pub manifest_relative_path: String,
    /// Digest over the materialized manifest JSON bytes.
    pub manifest_digest: ArtifactDigest,
    /// Digest sidecar path relative to the caller-supplied `audit-index/` root.
    pub manifest_digest_relative_path: String,
    /// Parsed and validated manifest.
    pub manifest: LocalAuditIndexManifest,
    /// Validation result for the parsed manifest.
    pub validation: LocalAuditIndexValidation,
    /// Output claim boundary.
    pub output_claim_boundary: ClaimBoundary,
}

/// Materialized adjacent local Phase S audit-index ergonomics output summary.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct LocalAuditIndexErgonomicsOutput {
    /// Selected-view JSON path relative to the caller-supplied
    /// `audit-index-ergonomics/` root.
    pub view_relative_path: String,
    /// Digest over the materialized selected-view JSON bytes.
    pub view_digest: ArtifactDigest,
    /// Selected-view digest sidecar path relative to the output root.
    pub view_digest_relative_path: String,
    /// Rendered Markdown path relative to the output root.
    pub markdown_relative_path: String,
    /// Digest over the materialized Markdown bytes.
    pub markdown_digest: ArtifactDigest,
    /// Rendered Markdown digest sidecar path relative to the output root.
    pub markdown_digest_relative_path: String,
    /// Source manifest used to validate and rederive the view.
    pub manifest: LocalAuditIndexManifest,
    /// Source request used to validate and rederive the view.
    pub request: LocalAuditIndexErgonomicsRequest,
    /// Parsed and validated ergonomics view.
    pub view: LocalAuditIndexErgonomicsView,
    /// Validation result for the source manifest/request.
    pub validation: LocalAuditIndexErgonomicsValidation,
    /// Output claim boundary.
    pub output_claim_boundary: ClaimBoundary,
}

/// Phase S exact-match filter field for in-memory audit-index ergonomics.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
pub enum LocalAuditIndexErgonomicsFilterField {
    /// Filter on `LocalAuditIndexInputRef.kind`.
    InputKind,
    /// Filter on `LocalAuditIndexInputRef.claim_boundary`.
    ClaimBoundary,
    /// Filter on `LocalAuditIndexInputRef.failed_readiness`.
    FailedReadiness,
    /// Filter on `LocalAuditIndexInputRef.local_only_warnings_visible`.
    LocalOnlyWarningsVisible,
}

/// Phase S exact-match filter over already-present manifest fields.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct LocalAuditIndexErgonomicsFilter {
    /// Manifest field selected by the filter.
    pub field: LocalAuditIndexErgonomicsFilterField,
    /// Exact string value. No path, URL, shell, or expression syntax is accepted.
    pub value: String,
}

/// Phase S grouping key for selected audit-index inputs.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
pub enum LocalAuditIndexErgonomicsGroupKey {
    /// Group by input kind.
    InputKind,
    /// Group by claim boundary.
    ClaimBoundary,
    /// Group by failed-readiness flag.
    FailedReadiness,
    /// Group by local-only-warning visibility flag.
    LocalOnlyWarningsVisible,
}

/// Phase S deterministic sort key for selected audit-index inputs.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
pub enum LocalAuditIndexErgonomicsSortKey {
    /// Sort by input id.
    InputId,
    /// Sort by artifact URI.
    ArtifactUri,
    /// Sort by input kind, then input id.
    InputKind,
    /// Sort by claim boundary, then input id.
    ClaimBoundary,
}

/// Phase S in-memory audit-index ergonomics request.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct LocalAuditIndexErgonomicsRequest {
    /// Exact-match filters over manifest fields.
    #[serde(default)]
    pub filters: Vec<LocalAuditIndexErgonomicsFilter>,
    /// Deterministic grouping key.
    pub group_by: LocalAuditIndexErgonomicsGroupKey,
    /// Deterministic sort key.
    pub sort_by: LocalAuditIndexErgonomicsSortKey,
}

impl Default for LocalAuditIndexErgonomicsRequest {
    fn default() -> Self {
        Self {
            filters: Vec::new(),
            group_by: LocalAuditIndexErgonomicsGroupKey::InputKind,
            sort_by: LocalAuditIndexErgonomicsSortKey::InputId,
        }
    }
}

/// Phase S ergonomics validation issue kind.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum LocalAuditIndexErgonomicsIssueKind {
    /// Source manifest failed the existing local audit-index validation.
    InvalidManifest,
    /// Filter value used unsafe or expression-like syntax.
    InvalidFilterValue,
    /// Bool filter value was not `true` or `false`.
    InvalidBooleanFilterValue,
}

/// Phase S ergonomics validation issue.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct LocalAuditIndexErgonomicsIssue {
    /// Issue kind.
    pub kind: LocalAuditIndexErgonomicsIssueKind,
    /// Issue path.
    pub path: String,
    /// Issue message.
    pub message: String,
}

/// Phase S ergonomics validation result.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct LocalAuditIndexErgonomicsValidation {
    /// Whether validation passed.
    pub valid: bool,
    /// Validation issues.
    #[serde(default)]
    pub issues: Vec<LocalAuditIndexErgonomicsIssue>,
    /// Claim boundary of this validation report.
    pub claim_boundary: ClaimBoundary,
}

/// Phase S group summary for selected audit-index inputs.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct LocalAuditIndexErgonomicsGroupSummary {
    /// Group key.
    pub group_key: LocalAuditIndexErgonomicsGroupKey,
    /// Deterministic group value.
    pub group_value: String,
    /// Number of selected inputs in the group.
    pub input_count: usize,
    /// Number of selected inputs that carry failed-readiness state.
    pub failed_readiness_input_count: usize,
    /// Number of selected inputs with hidden local-only warnings.
    pub hidden_local_only_warning_input_count: usize,
}

/// Phase S warning summary for selected audit-index inputs.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct LocalAuditIndexErgonomicsWarningSummary {
    /// Whether failed-readiness state remains visible at manifest level.
    pub failed_readiness_visible: bool,
    /// Number of selected inputs with failed-readiness state.
    pub failed_readiness_input_count: usize,
    /// Whether local-only warnings remain visible at manifest level.
    pub local_only_warnings_visible: bool,
    /// Number of selected inputs with hidden local-only warnings.
    pub hidden_local_only_warning_input_count: usize,
    /// Whether the manifest claims any source mutation.
    pub source_mutation_claimed: bool,
    /// Source mutation flags present on the manifest.
    #[serde(default)]
    pub source_mutation_flags: Vec<String>,
}

/// Phase S in-memory audit-index ergonomics view.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct LocalAuditIndexErgonomicsView {
    /// Source audit-index id.
    pub index_id: String,
    /// Source pack id.
    pub indexed_pack_id: String,
    /// Selected input ids after validation, filtering, and sorting.
    #[serde(default)]
    pub selected_input_ids: Vec<String>,
    /// Rejected filter diagnostics. Successful builds keep this empty.
    #[serde(default)]
    pub rejected_filters: Vec<LocalAuditIndexErgonomicsIssue>,
    /// Group summaries for selected inputs.
    #[serde(default)]
    pub groups: Vec<LocalAuditIndexErgonomicsGroupSummary>,
    /// Warning summary for selected inputs.
    pub warning_summary: LocalAuditIndexErgonomicsWarningSummary,
    /// Required claim-boundary limitation labels repeated in the view.
    #[serde(default)]
    pub limitation_labels: Vec<String>,
    /// Output claim boundary. Phase S remains `Level0DesignNote`.
    pub output_claim_boundary: ClaimBoundary,
    /// Deterministic Markdown rendering.
    pub markdown: String,
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

/// Write adjacent local audit-index output files.
///
/// The supplied `output_root` is the local `audit-index/` directory. This
/// function writes only `audit-index-manifest.json` and
/// `digests/audit-index-manifest.sha256`. It does not mutate source packs,
/// source reports, report bundles, or accepted Evidence Ledgers.
pub fn write_local_audit_index_outputs(
    output_root: impl AsRef<Path>,
    manifest: &LocalAuditIndexManifest,
    overwrite: bool,
) -> Result<LocalAuditIndexOutput> {
    let output_root = output_root.as_ref();
    validate_output_root(output_root)?;
    if output_root.exists() && !output_root.is_dir() {
        return Err(audit_index_io_error(
            output_root.display().to_string(),
            "audit-index output root exists and is not a directory",
        ));
    }

    let validation = validate_local_audit_index_manifest(manifest);
    if !validation.valid {
        return Err(audit_index_io_error(
            "audit_index.manifest",
            format!("manifest validation failed: {:?}", validation.issues),
        ));
    }

    let targets = audit_index_target_paths();
    if output_root.exists() && !overwrite && directory_has_entries(output_root)? {
        return Err(audit_index_io_error(
            output_root.display().to_string(),
            "audit-index output root is non-empty; explicit overwrite approval is required",
        ));
    }
    if output_root.exists() && overwrite {
        reject_unexpected_existing_files(output_root, &targets)?;
        let existing = collect_relative_files(output_root)?;
        if !existing.is_empty() {
            let existing_output = read_local_audit_index_outputs(output_root)?;
            if existing_output.manifest != *manifest {
                return Err(audit_index_io_error(
                    output_root.display().to_string(),
                    "existing audit-index output does not match supplied manifest",
                ));
            }
        }
    }

    let manifest_json = serialize_local_audit_index_manifest_json(manifest)?;
    let manifest_bytes = manifest_json.as_bytes();
    let manifest_digest = digest_audit_index_output_bytes(manifest_bytes);

    write_relative_bytes(output_root, AUDIT_INDEX_MANIFEST_PATH, manifest_bytes)?;
    write_relative_bytes(
        output_root,
        AUDIT_INDEX_MANIFEST_DIGEST_PATH,
        format!("{}\n", manifest_digest.hex_digest).as_bytes(),
    )?;

    Ok(LocalAuditIndexOutput {
        manifest_relative_path: AUDIT_INDEX_MANIFEST_PATH.to_string(),
        manifest_digest,
        manifest_digest_relative_path: AUDIT_INDEX_MANIFEST_DIGEST_PATH.to_string(),
        manifest: manifest.clone(),
        validation,
        output_claim_boundary: ClaimBoundary::Level0DesignNote,
    })
}

/// Read and validate adjacent local audit-index output files.
///
/// A successful read confirms local file integrity only. It is not accepted
/// evidence, not official benchmark evidence, and not ZK backend performance
/// evidence.
pub fn read_local_audit_index_outputs(
    output_root: impl AsRef<Path>,
) -> Result<LocalAuditIndexOutput> {
    let output_root = output_root.as_ref();
    validate_output_root(output_root)?;
    reject_unexpected_existing_files(output_root, &audit_index_target_paths())?;

    let manifest_bytes = read_relative_bytes(output_root, AUDIT_INDEX_MANIFEST_PATH)?;
    let digest_sidecar = String::from_utf8(read_relative_bytes(
        output_root,
        AUDIT_INDEX_MANIFEST_DIGEST_PATH,
    )?)
    .map_err(|error| {
        audit_index_io_error(
            AUDIT_INDEX_MANIFEST_DIGEST_PATH,
            format!("manifest digest sidecar is not UTF-8: {error}"),
        )
    })?;
    let manifest_digest = digest_audit_index_output_bytes(&manifest_bytes);
    if digest_sidecar.trim() != manifest_digest.hex_digest {
        return Err(audit_index_io_error(
            AUDIT_INDEX_MANIFEST_DIGEST_PATH,
            "manifest JSON bytes do not match digest sidecar",
        ));
    }

    let manifest_json = String::from_utf8(manifest_bytes).map_err(|error| {
        audit_index_io_error(
            AUDIT_INDEX_MANIFEST_PATH,
            format!("manifest JSON is not UTF-8: {error}"),
        )
    })?;
    let manifest = deserialize_local_audit_index_manifest_json(&manifest_json)?;
    let validation = validate_local_audit_index_manifest(&manifest);
    if !validation.valid {
        return Err(audit_index_io_error(
            "audit_index.manifest",
            format!("manifest validation failed: {:?}", validation.issues),
        ));
    }

    Ok(LocalAuditIndexOutput {
        manifest_relative_path: AUDIT_INDEX_MANIFEST_PATH.to_string(),
        manifest_digest,
        manifest_digest_relative_path: AUDIT_INDEX_MANIFEST_DIGEST_PATH.to_string(),
        manifest,
        validation,
        output_claim_boundary: ClaimBoundary::Level0DesignNote,
    })
}

/// Required Phase S audit-index ergonomics limitation labels.
pub fn required_local_audit_index_ergonomics_limitations() -> Vec<String> {
    vec![
        "Audit-index ergonomics are not accepted evidence.".to_string(),
        "Audit-index ergonomics are local presentation metadata only.".to_string(),
        "Audit-index ergonomics do not create official benchmark evidence.".to_string(),
        "Audit-index ergonomics do not create Level2+ evidence.".to_string(),
        "Audit-index ergonomics do not prove backend performance.".to_string(),
        "Local replay artifacts are not official benchmark evidence.".to_string(),
        "Internal timing telemetry is not ZK backend performance.".to_string(),
    ]
}

/// Validate a Phase S in-memory ergonomics request against one audit-index
/// manifest. This does not write files, run commands, or call external services.
pub fn validate_local_audit_index_ergonomics_request(
    manifest: &LocalAuditIndexManifest,
    request: &LocalAuditIndexErgonomicsRequest,
) -> LocalAuditIndexErgonomicsValidation {
    let mut issues = Vec::new();
    let manifest_validation = validate_local_audit_index_manifest(manifest);
    if !manifest_validation.valid {
        issues.push(LocalAuditIndexErgonomicsIssue {
            kind: LocalAuditIndexErgonomicsIssueKind::InvalidManifest,
            path: "manifest".to_string(),
            message: format!(
                "audit-index ergonomics require a valid local audit-index manifest: {:?}",
                manifest_validation.issues
            ),
        });
    }

    for (index, filter) in request.filters.iter().enumerate() {
        let path = format!("filters[{index}].value");
        if !is_safe_ergonomics_filter_value(&filter.value) {
            issues.push(LocalAuditIndexErgonomicsIssue {
                kind: LocalAuditIndexErgonomicsIssueKind::InvalidFilterValue,
                path,
                message: "filter values must be exact manifest-field values without path, URL, shell, wildcard, or expression syntax".to_string(),
            });
            continue;
        }
        if matches!(
            filter.field,
            LocalAuditIndexErgonomicsFilterField::FailedReadiness
                | LocalAuditIndexErgonomicsFilterField::LocalOnlyWarningsVisible
        ) && !matches!(filter.value.as_str(), "true" | "false")
        {
            issues.push(LocalAuditIndexErgonomicsIssue {
                kind: LocalAuditIndexErgonomicsIssueKind::InvalidBooleanFilterValue,
                path,
                message: "boolean ergonomics filters must use exactly true or false".to_string(),
            });
        }
    }

    LocalAuditIndexErgonomicsValidation {
        valid: issues.is_empty(),
        issues,
        claim_boundary: ClaimBoundary::Level0DesignNote,
    }
}

/// Build a Phase S in-memory audit-index ergonomics view.
///
/// The view is presentation metadata over one valid `LocalAuditIndexManifest`.
/// It does not write files, execute replay commands, import results, mutate
/// source metadata, populate score axes, or create accepted/official/Level2+
/// evidence.
pub fn build_local_audit_index_ergonomics_view(
    manifest: &LocalAuditIndexManifest,
    request: &LocalAuditIndexErgonomicsRequest,
) -> Result<LocalAuditIndexErgonomicsView> {
    let validation = validate_local_audit_index_ergonomics_request(manifest, request);
    if !validation.valid {
        return Err(ZkBenchError::validation(
            "audit_index.ergonomics",
            format!(
                "audit-index ergonomics validation failed: {:?}",
                validation.issues
            ),
        ));
    }

    let mut selected: Vec<&LocalAuditIndexInputRef> = manifest
        .inputs
        .iter()
        .filter(|input| {
            request
                .filters
                .iter()
                .all(|filter| ergonomics_filter_matches(input, filter))
        })
        .collect();
    sort_ergonomics_inputs(&mut selected, request.sort_by);

    let selected_input_ids = selected
        .iter()
        .map(|input| input.input_id.clone())
        .collect::<Vec<_>>();
    let groups = build_ergonomics_groups(&selected, request.group_by);
    let warning_summary = build_ergonomics_warning_summary(manifest, &selected);
    let limitation_labels = required_local_audit_index_ergonomics_limitations();
    let markdown = render_local_audit_index_ergonomics_markdown(
        manifest,
        &selected_input_ids,
        &groups,
        &warning_summary,
        &limitation_labels,
    );

    Ok(LocalAuditIndexErgonomicsView {
        index_id: manifest.index_id.clone(),
        indexed_pack_id: manifest.indexed_pack_id.clone(),
        selected_input_ids,
        rejected_filters: Vec::new(),
        groups,
        warning_summary,
        limitation_labels,
        output_claim_boundary: ClaimBoundary::Level0DesignNote,
        markdown,
    })
}

/// Serialize a Phase S audit-index ergonomics view to pretty JSON.
pub fn serialize_local_audit_index_ergonomics_view_json(
    view: &LocalAuditIndexErgonomicsView,
) -> Result<String> {
    serde_json::to_string_pretty(view).map_err(|error| {
        ZkBenchError::serialization("audit_index.ergonomics_view", error.to_string())
    })
}

/// Deserialize a Phase S audit-index ergonomics view from JSON.
pub fn deserialize_local_audit_index_ergonomics_view_json(
    json: &str,
) -> Result<LocalAuditIndexErgonomicsView> {
    serde_json::from_str(json).map_err(|error| {
        ZkBenchError::deserialization("audit_index.ergonomics_view", error.to_string())
    })
}

/// Write adjacent local Phase S audit-index ergonomics output files.
///
/// The supplied `output_root` is the local `audit-index-ergonomics/` directory.
/// This function writes only the selected-view JSON, deterministic rendered
/// Markdown, and two SHA-256 digest sidecars. It rederives the supplied view
/// from the source manifest and request before writing and does not mutate
/// source packs, source reports, report bundles, audit-index outputs, or
/// accepted Evidence Ledgers.
pub fn write_local_audit_index_ergonomics_outputs(
    output_root: impl AsRef<Path>,
    manifest: &LocalAuditIndexManifest,
    request: &LocalAuditIndexErgonomicsRequest,
    view: &LocalAuditIndexErgonomicsView,
    overwrite: bool,
    protected_paths: &[impl AsRef<Path>],
) -> Result<LocalAuditIndexErgonomicsOutput> {
    let output_root = output_root.as_ref();
    validate_output_root(output_root)?;
    reject_protected_path_overlap(output_root, protected_paths)?;
    if output_root.exists() && !output_root.is_dir() {
        return Err(audit_index_io_error(
            output_root.display().to_string(),
            "audit-index ergonomics output root exists and is not a directory",
        ));
    }

    let validation = validate_local_audit_index_ergonomics_request(manifest, request);
    if !validation.valid {
        return Err(audit_index_io_error(
            "audit_index.ergonomics",
            format!("ergonomics validation failed: {:?}", validation.issues),
        ));
    }
    let expected_view = build_local_audit_index_ergonomics_view(manifest, request)?;
    validate_materialized_ergonomics_view(&expected_view, view)?;

    let targets = audit_index_ergonomics_target_paths();
    if output_root.exists() && !overwrite && directory_has_entries(output_root)? {
        return Err(audit_index_io_error(
            output_root.display().to_string(),
            "audit-index ergonomics output root is non-empty; explicit overwrite approval is required",
        ));
    }
    if output_root.exists() && overwrite {
        reject_unexpected_existing_files(output_root, &targets)?;
        let existing = collect_relative_files(output_root)?;
        if !existing.is_empty() {
            let existing_output = read_local_audit_index_ergonomics_outputs(
                output_root,
                manifest,
                request,
                protected_paths,
            )?;
            if existing_output.view != *view {
                return Err(audit_index_io_error(
                    output_root.display().to_string(),
                    "existing audit-index ergonomics output does not match supplied view",
                ));
            }
        }
    }

    let view_json = serialize_local_audit_index_ergonomics_view_json(view)?;
    let view_bytes = view_json.as_bytes();
    let markdown_bytes = view.markdown.as_bytes();
    let view_digest = digest_audit_index_output_bytes(view_bytes);
    let markdown_digest = digest_audit_index_output_bytes(markdown_bytes);

    write_relative_bytes(output_root, AUDIT_INDEX_ERGONOMICS_VIEW_PATH, view_bytes)?;
    write_relative_bytes(
        output_root,
        AUDIT_INDEX_ERGONOMICS_MARKDOWN_PATH,
        markdown_bytes,
    )?;
    write_relative_bytes(
        output_root,
        AUDIT_INDEX_ERGONOMICS_VIEW_DIGEST_PATH,
        format!("{}\n", view_digest.hex_digest).as_bytes(),
    )?;
    write_relative_bytes(
        output_root,
        AUDIT_INDEX_ERGONOMICS_MARKDOWN_DIGEST_PATH,
        format!("{}\n", markdown_digest.hex_digest).as_bytes(),
    )?;

    Ok(LocalAuditIndexErgonomicsOutput {
        view_relative_path: AUDIT_INDEX_ERGONOMICS_VIEW_PATH.to_string(),
        view_digest,
        view_digest_relative_path: AUDIT_INDEX_ERGONOMICS_VIEW_DIGEST_PATH.to_string(),
        markdown_relative_path: AUDIT_INDEX_ERGONOMICS_MARKDOWN_PATH.to_string(),
        markdown_digest,
        markdown_digest_relative_path: AUDIT_INDEX_ERGONOMICS_MARKDOWN_DIGEST_PATH.to_string(),
        manifest: manifest.clone(),
        request: request.clone(),
        view: view.clone(),
        validation,
        output_claim_boundary: ClaimBoundary::Level0DesignNote,
    })
}

/// Read and validate adjacent local Phase S audit-index ergonomics output files.
///
/// A successful read confirms local file integrity and deterministic
/// rederivation from the supplied source manifest/request only. It is not
/// accepted evidence, not official benchmark evidence, and not ZK backend
/// performance evidence.
pub fn read_local_audit_index_ergonomics_outputs(
    output_root: impl AsRef<Path>,
    manifest: &LocalAuditIndexManifest,
    request: &LocalAuditIndexErgonomicsRequest,
    protected_paths: &[impl AsRef<Path>],
) -> Result<LocalAuditIndexErgonomicsOutput> {
    let output_root = output_root.as_ref();
    validate_output_root(output_root)?;
    reject_protected_path_overlap(output_root, protected_paths)?;
    reject_unexpected_existing_files(output_root, &audit_index_ergonomics_target_paths())?;

    let view_bytes = read_relative_bytes(output_root, AUDIT_INDEX_ERGONOMICS_VIEW_PATH)?;
    let markdown_bytes = read_relative_bytes(output_root, AUDIT_INDEX_ERGONOMICS_MARKDOWN_PATH)?;
    let view_digest_sidecar = String::from_utf8(read_relative_bytes(
        output_root,
        AUDIT_INDEX_ERGONOMICS_VIEW_DIGEST_PATH,
    )?)
    .map_err(|error| {
        audit_index_io_error(
            AUDIT_INDEX_ERGONOMICS_VIEW_DIGEST_PATH,
            format!("ergonomics view digest sidecar is not UTF-8: {error}"),
        )
    })?;
    let markdown_digest_sidecar = String::from_utf8(read_relative_bytes(
        output_root,
        AUDIT_INDEX_ERGONOMICS_MARKDOWN_DIGEST_PATH,
    )?)
    .map_err(|error| {
        audit_index_io_error(
            AUDIT_INDEX_ERGONOMICS_MARKDOWN_DIGEST_PATH,
            format!("ergonomics Markdown digest sidecar is not UTF-8: {error}"),
        )
    })?;

    let view_digest = digest_audit_index_output_bytes(&view_bytes);
    if view_digest_sidecar.trim() != view_digest.hex_digest {
        return Err(audit_index_io_error(
            AUDIT_INDEX_ERGONOMICS_VIEW_DIGEST_PATH,
            "ergonomics view JSON bytes do not match digest sidecar",
        ));
    }
    let markdown_digest = digest_audit_index_output_bytes(&markdown_bytes);
    if markdown_digest_sidecar.trim() != markdown_digest.hex_digest {
        return Err(audit_index_io_error(
            AUDIT_INDEX_ERGONOMICS_MARKDOWN_DIGEST_PATH,
            "ergonomics Markdown bytes do not match digest sidecar",
        ));
    }

    let view_json = String::from_utf8(view_bytes).map_err(|error| {
        audit_index_io_error(
            AUDIT_INDEX_ERGONOMICS_VIEW_PATH,
            format!("ergonomics view JSON is not UTF-8: {error}"),
        )
    })?;
    let markdown = String::from_utf8(markdown_bytes).map_err(|error| {
        audit_index_io_error(
            AUDIT_INDEX_ERGONOMICS_MARKDOWN_PATH,
            format!("ergonomics Markdown is not UTF-8: {error}"),
        )
    })?;
    let view = deserialize_local_audit_index_ergonomics_view_json(&view_json)?;
    if view.markdown != markdown {
        return Err(audit_index_io_error(
            AUDIT_INDEX_ERGONOMICS_MARKDOWN_PATH,
            "ergonomics Markdown bytes do not match selected view",
        ));
    }

    let validation = validate_local_audit_index_ergonomics_request(manifest, request);
    if !validation.valid {
        return Err(audit_index_io_error(
            "audit_index.ergonomics",
            format!("ergonomics validation failed: {:?}", validation.issues),
        ));
    }
    let expected_view = build_local_audit_index_ergonomics_view(manifest, request)?;
    validate_materialized_ergonomics_view(&expected_view, &view)?;

    Ok(LocalAuditIndexErgonomicsOutput {
        view_relative_path: AUDIT_INDEX_ERGONOMICS_VIEW_PATH.to_string(),
        view_digest,
        view_digest_relative_path: AUDIT_INDEX_ERGONOMICS_VIEW_DIGEST_PATH.to_string(),
        markdown_relative_path: AUDIT_INDEX_ERGONOMICS_MARKDOWN_PATH.to_string(),
        markdown_digest,
        markdown_digest_relative_path: AUDIT_INDEX_ERGONOMICS_MARKDOWN_DIGEST_PATH.to_string(),
        manifest: manifest.clone(),
        request: request.clone(),
        view,
        validation,
        output_claim_boundary: ClaimBoundary::Level0DesignNote,
    })
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

fn ergonomics_filter_matches(
    input: &LocalAuditIndexInputRef,
    filter: &LocalAuditIndexErgonomicsFilter,
) -> bool {
    let value = match filter.field {
        LocalAuditIndexErgonomicsFilterField::InputKind => format!("{:?}", input.kind),
        LocalAuditIndexErgonomicsFilterField::ClaimBoundary => {
            format!("{:?}", input.claim_boundary)
        }
        LocalAuditIndexErgonomicsFilterField::FailedReadiness => input.failed_readiness.to_string(),
        LocalAuditIndexErgonomicsFilterField::LocalOnlyWarningsVisible => {
            input.local_only_warnings_visible.to_string()
        }
    };
    value == filter.value
}

fn sort_ergonomics_inputs(
    inputs: &mut Vec<&LocalAuditIndexInputRef>,
    sort_by: LocalAuditIndexErgonomicsSortKey,
) {
    match sort_by {
        LocalAuditIndexErgonomicsSortKey::InputId => {
            inputs.sort_by(|left, right| left.input_id.cmp(&right.input_id));
        }
        LocalAuditIndexErgonomicsSortKey::ArtifactUri => {
            inputs.sort_by(|left, right| {
                left.artifact_uri
                    .cmp(&right.artifact_uri)
                    .then_with(|| left.input_id.cmp(&right.input_id))
            });
        }
        LocalAuditIndexErgonomicsSortKey::InputKind => {
            inputs.sort_by(|left, right| {
                left.kind
                    .cmp(&right.kind)
                    .then_with(|| left.input_id.cmp(&right.input_id))
            });
        }
        LocalAuditIndexErgonomicsSortKey::ClaimBoundary => {
            inputs.sort_by(|left, right| {
                left.claim_boundary
                    .cmp(&right.claim_boundary)
                    .then_with(|| left.input_id.cmp(&right.input_id))
            });
        }
    }
}

fn build_ergonomics_groups(
    selected: &[&LocalAuditIndexInputRef],
    group_by: LocalAuditIndexErgonomicsGroupKey,
) -> Vec<LocalAuditIndexErgonomicsGroupSummary> {
    let mut grouped: BTreeMap<String, LocalAuditIndexErgonomicsGroupSummary> = BTreeMap::new();
    for input in selected {
        let group_value = ergonomics_group_value(input, group_by);
        let entry = grouped.entry(group_value.clone()).or_insert_with(|| {
            LocalAuditIndexErgonomicsGroupSummary {
                group_key: group_by,
                group_value,
                input_count: 0,
                failed_readiness_input_count: 0,
                hidden_local_only_warning_input_count: 0,
            }
        });
        entry.input_count += 1;
        if input.failed_readiness {
            entry.failed_readiness_input_count += 1;
        }
        if !input.local_only_warnings_visible {
            entry.hidden_local_only_warning_input_count += 1;
        }
    }
    grouped.into_values().collect()
}

fn ergonomics_group_value(
    input: &LocalAuditIndexInputRef,
    group_by: LocalAuditIndexErgonomicsGroupKey,
) -> String {
    match group_by {
        LocalAuditIndexErgonomicsGroupKey::InputKind => format!("{:?}", input.kind),
        LocalAuditIndexErgonomicsGroupKey::ClaimBoundary => format!("{:?}", input.claim_boundary),
        LocalAuditIndexErgonomicsGroupKey::FailedReadiness => input.failed_readiness.to_string(),
        LocalAuditIndexErgonomicsGroupKey::LocalOnlyWarningsVisible => {
            input.local_only_warnings_visible.to_string()
        }
    }
}

fn build_ergonomics_warning_summary(
    manifest: &LocalAuditIndexManifest,
    selected: &[&LocalAuditIndexInputRef],
) -> LocalAuditIndexErgonomicsWarningSummary {
    let mut source_mutation_flags = Vec::new();
    if manifest.mutates_source_pack {
        source_mutation_flags.push("mutates_source_pack".to_string());
    }
    if manifest.mutates_source_report {
        source_mutation_flags.push("mutates_source_report".to_string());
    }
    if manifest.mutates_report_bundle {
        source_mutation_flags.push("mutates_report_bundle".to_string());
    }

    LocalAuditIndexErgonomicsWarningSummary {
        failed_readiness_visible: manifest.failed_readiness_visible,
        failed_readiness_input_count: selected
            .iter()
            .filter(|input| input.failed_readiness)
            .count(),
        local_only_warnings_visible: manifest.local_only_warnings_visible,
        hidden_local_only_warning_input_count: selected
            .iter()
            .filter(|input| !input.local_only_warnings_visible)
            .count(),
        source_mutation_claimed: !source_mutation_flags.is_empty(),
        source_mutation_flags,
    }
}

fn render_local_audit_index_ergonomics_markdown(
    manifest: &LocalAuditIndexManifest,
    selected_input_ids: &[String],
    groups: &[LocalAuditIndexErgonomicsGroupSummary],
    warning_summary: &LocalAuditIndexErgonomicsWarningSummary,
    limitation_labels: &[String],
) -> String {
    let mut markdown = String::new();
    markdown.push_str("# Local Audit-Index Ergonomics View\n\n");
    markdown.push_str(&format!("- index_id: {}\n", manifest.index_id));
    markdown.push_str(&format!(
        "- indexed_pack_id: {}\n",
        manifest.indexed_pack_id
    ));
    markdown.push_str("- output_claim_boundary: Level0DesignNote\n");
    markdown.push_str(&format!(
        "- selected_input_count: {}\n\n",
        selected_input_ids.len()
    ));

    markdown.push_str("## Limitation Labels\n\n");
    for label in limitation_labels {
        markdown.push_str(&format!("- {label}\n"));
    }

    markdown.push_str("\n## Warning Summary\n\n");
    markdown.push_str(&format!(
        "- failed_readiness_visible: {}\n",
        warning_summary.failed_readiness_visible
    ));
    markdown.push_str(&format!(
        "- failed_readiness_input_count: {}\n",
        warning_summary.failed_readiness_input_count
    ));
    markdown.push_str(&format!(
        "- local_only_warnings_visible: {}\n",
        warning_summary.local_only_warnings_visible
    ));
    markdown.push_str(&format!(
        "- hidden_local_only_warning_input_count: {}\n",
        warning_summary.hidden_local_only_warning_input_count
    ));
    markdown.push_str(&format!(
        "- source_mutation_claimed: {}\n\n",
        warning_summary.source_mutation_claimed
    ));

    markdown.push_str("## Groups\n\n");
    markdown.push_str("| key | value | inputs | failed readiness | hidden local-only warnings |\n");
    markdown.push_str("| --- | --- | ---: | ---: | ---: |\n");
    for group in groups {
        markdown.push_str(&format!(
            "| {:?} | {} | {} | {} | {} |\n",
            group.group_key,
            group.group_value,
            group.input_count,
            group.failed_readiness_input_count,
            group.hidden_local_only_warning_input_count
        ));
    }

    markdown.push_str("\n## Selected Inputs\n\n");
    for input_id in selected_input_ids {
        markdown.push_str(&format!("- {input_id}\n"));
    }

    markdown
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

fn is_safe_ergonomics_filter_value(value: &str) -> bool {
    let trimmed = value.trim();
    !trimmed.is_empty()
        && trimmed == value
        && !trimmed.contains('/')
        && !trimmed.contains('\\')
        && !trimmed.contains("..")
        && !trimmed.contains("://")
        && !contains_shell_payload(trimmed)
        && !trimmed.chars().any(|ch| {
            matches!(
                ch,
                '*' | '?' | '[' | ']' | '(' | ')' | '{' | '}' | '^' | '+' | '<' | '>'
            )
        })
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

fn audit_index_target_paths() -> BTreeSet<String> {
    BTreeSet::from([
        AUDIT_INDEX_MANIFEST_PATH.to_string(),
        AUDIT_INDEX_MANIFEST_DIGEST_PATH.to_string(),
    ])
}

fn audit_index_ergonomics_target_paths() -> BTreeSet<String> {
    BTreeSet::from([
        AUDIT_INDEX_ERGONOMICS_VIEW_PATH.to_string(),
        AUDIT_INDEX_ERGONOMICS_MARKDOWN_PATH.to_string(),
        AUDIT_INDEX_ERGONOMICS_VIEW_DIGEST_PATH.to_string(),
        AUDIT_INDEX_ERGONOMICS_MARKDOWN_DIGEST_PATH.to_string(),
    ])
}

fn validate_materialized_ergonomics_view(
    expected: &LocalAuditIndexErgonomicsView,
    supplied: &LocalAuditIndexErgonomicsView,
) -> Result<()> {
    if supplied.output_claim_boundary != ClaimBoundary::Level0DesignNote {
        return Err(audit_index_io_error(
            "audit_index.ergonomics.output_claim_boundary",
            "audit-index ergonomics output must remain Level0DesignNote",
        ));
    }
    for limitation in required_local_audit_index_ergonomics_limitations() {
        if !supplied.limitation_labels.contains(&limitation) {
            return Err(audit_index_io_error(
                "audit_index.ergonomics.limitation_labels",
                format!("missing required ergonomics limitation label: {limitation}"),
            ));
        }
        if !supplied.markdown.contains(&limitation) {
            return Err(audit_index_io_error(
                "audit_index.ergonomics.markdown",
                format!("materialized ergonomics Markdown omits limitation label: {limitation}"),
            ));
        }
    }
    if supplied != expected {
        return Err(audit_index_io_error(
            "audit_index.ergonomics",
            "supplied audit-index ergonomics view does not match deterministic source manifest/request derivation",
        ));
    }
    Ok(())
}

fn validate_output_root(root: &Path) -> Result<()> {
    let value = root.as_os_str().to_string_lossy();
    if value.trim().is_empty()
        || value.contains("://")
        || value.contains('\\')
        || contains_shell_payload(&value)
    {
        return Err(audit_index_io_error(
            value.to_string(),
            "invalid audit-index output root",
        ));
    }
    if root
        .components()
        .any(|component| matches!(component, Component::ParentDir))
    {
        return Err(audit_index_io_error(
            value.to_string(),
            "audit-index output root must not contain parent-directory components",
        ));
    }
    Ok(())
}

fn reject_protected_path_overlap(root: &Path, protected_paths: &[impl AsRef<Path>]) -> Result<()> {
    let comparable_root = comparable_output_path(root)?;
    for protected_path in protected_paths {
        let protected_path = protected_path.as_ref();
        validate_protected_path(protected_path)?;
        let comparable_protected = comparable_output_path(protected_path)?;
        if comparable_root == comparable_protected
            || comparable_root.starts_with(&comparable_protected)
            || comparable_protected.starts_with(&comparable_root)
        {
            return Err(audit_index_io_error(
                root.display().to_string(),
                format!(
                    "audit-index ergonomics output root must not overlap protected path {}",
                    protected_path.display()
                ),
            ));
        }
    }
    Ok(())
}

fn comparable_output_path(path: &Path) -> Result<std::path::PathBuf> {
    let base = if path.is_absolute() {
        std::path::PathBuf::new()
    } else {
        std::env::current_dir()
            .map_err(|error| audit_index_io_error(path.display().to_string(), error))?
    };
    let mut comparable = base;
    for component in path.components() {
        match component {
            Component::Prefix(prefix) => comparable.push(prefix.as_os_str()),
            Component::RootDir => comparable.push(component.as_os_str()),
            Component::CurDir => {}
            Component::ParentDir => {
                return Err(audit_index_io_error(
                    path.display().to_string(),
                    "audit-index ergonomics paths must not contain parent-directory components",
                ))
            }
            Component::Normal(value) => comparable.push(value),
        }
    }
    Ok(comparable)
}

fn validate_protected_path(path: &Path) -> Result<()> {
    let value = path.as_os_str().to_string_lossy();
    if value.trim().is_empty()
        || value.contains("://")
        || value.contains('\\')
        || contains_shell_payload(&value)
    {
        return Err(audit_index_io_error(
            value.to_string(),
            "invalid protected audit-index ergonomics path",
        ));
    }
    if path
        .components()
        .any(|component| matches!(component, Component::ParentDir))
    {
        return Err(audit_index_io_error(
            value.to_string(),
            "protected audit-index ergonomics paths must not contain parent-directory components",
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
        return Err(audit_index_io_error(
            relative_path,
            "invalid audit-index relative output path",
        ));
    }
    Ok(())
}

fn read_relative_bytes(root: &Path, relative_path: &str) -> Result<Vec<u8>> {
    validate_relative_output_path(relative_path)?;
    let path = root.join(relative_path);
    fs::read(&path).map_err(|error| audit_index_io_error(path.display().to_string(), error))
}

fn write_relative_bytes(root: &Path, relative_path: &str, bytes: &[u8]) -> Result<()> {
    validate_relative_output_path(relative_path)?;
    let path = root.join(relative_path);
    if let Some(parent) = path.parent() {
        fs::create_dir_all(parent)
            .map_err(|error| audit_index_io_error(parent.display().to_string(), error))?;
    }
    fs::write(&path, bytes).map_err(|error| audit_index_io_error(path.display().to_string(), error))
}

fn directory_has_entries(path: &Path) -> Result<bool> {
    let mut entries = fs::read_dir(path)
        .map_err(|error| audit_index_io_error(path.display().to_string(), error))?;
    entries
        .next()
        .transpose()
        .map(|entry| entry.is_some())
        .map_err(|error| audit_index_io_error(path.display().to_string(), error))
}

fn reject_unexpected_existing_files(root: &Path, expected: &BTreeSet<String>) -> Result<()> {
    let existing = collect_relative_files(root)?;
    for relative_path in existing {
        if !expected.contains(&relative_path) {
            return Err(audit_index_io_error(
                relative_path,
                "existing audit-index output root contains an unexpected file",
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
        .map_err(|error| audit_index_io_error(current.display().to_string(), error))?
    {
        let entry =
            entry.map_err(|error| audit_index_io_error(current.display().to_string(), error))?;
        let file_type = entry
            .file_type()
            .map_err(|error| audit_index_io_error(entry.path().display().to_string(), error))?;
        if file_type.is_symlink() {
            return Err(audit_index_io_error(
                entry.path().display().to_string(),
                "audit-index output must not contain symlinks",
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
        .map_err(|error| audit_index_io_error(path.display().to_string(), error))?;
    let mut parts = Vec::new();
    for component in relative_path.components() {
        match component {
            Component::Normal(value) => parts.push(value.to_string_lossy().to_string()),
            _ => {
                return Err(audit_index_io_error(
                    relative_path.display().to_string(),
                    "invalid audit-index relative path component",
                ))
            }
        }
    }
    Ok(parts.join("/"))
}

fn digest_audit_index_output_bytes(bytes: &[u8]) -> ArtifactDigest {
    compute_artifact_digest_bytes(bytes, Some(ArtifactKind::Other), Some(ArtifactRole::Report))
}

fn audit_index_io_error(path: impl Into<String>, message: impl ToString) -> ZkBenchError {
    ZkBenchError::benchmark_pack(path, message.to_string())
}
