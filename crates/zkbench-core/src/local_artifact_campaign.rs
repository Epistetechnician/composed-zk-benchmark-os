//! Phase V durable local artifact campaigns.
//!
//! Local artifact campaigns retain already-valid local artifact bundles under a
//! caller-owned output root. They are not official benchmark evidence, not
//! accepted Evidence Ledger entries, not ZK backend performance evidence, and
//! not Level2+ evidence.

use std::collections::BTreeSet;
use std::fs;
use std::path::{Component, Path, PathBuf};

use serde::{Deserialize, Serialize};

use crate::error::{Result, ZkBenchError};
use crate::evidence::{
    compute_artifact_digest, compute_artifact_digest_bytes, ArtifactDigest,
    ArtifactDigestAlgorithm, ArtifactKind, ArtifactRole, ClaimBoundary,
};
use crate::local_benchmark_artifact::{
    read_local_benchmark_artifact_outputs, LocalBenchmarkArtifactOutput,
};

/// Local artifact campaign manifest path below a caller-owned output root.
pub const LOCAL_ARTIFACT_CAMPAIGN_MANIFEST_PATH: &str = "campaign-manifest.json";

/// Local artifact campaign validation report path below a caller-owned output root.
pub const LOCAL_ARTIFACT_CAMPAIGN_VALIDATION_PATH: &str = "campaign-validation-report.json";

/// Local artifact campaign rendered Markdown path below a caller-owned output root.
pub const LOCAL_ARTIFACT_CAMPAIGN_MARKDOWN_PATH: &str = "rendered/campaign-summary.md";

/// Local artifact campaign manifest digest sidecar path below a caller-owned output root.
pub const LOCAL_ARTIFACT_CAMPAIGN_MANIFEST_DIGEST_PATH: &str =
    "digests/campaign-manifest-json.sha256";

/// Local artifact campaign validation digest sidecar path below a caller-owned output root.
pub const LOCAL_ARTIFACT_CAMPAIGN_VALIDATION_DIGEST_PATH: &str =
    "digests/campaign-validation-report-json.sha256";

/// Local artifact campaign Markdown digest sidecar path below a caller-owned output root.
pub const LOCAL_ARTIFACT_CAMPAIGN_MARKDOWN_DIGEST_PATH: &str =
    "digests/campaign-summary-markdown.sha256";

/// Phase V local artifact campaign schema version.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct LocalArtifactCampaignVersion {
    /// Logical version string.
    pub value: String,
}

impl Default for LocalArtifactCampaignVersion {
    fn default() -> Self {
        Self {
            value: "phase-v-local-artifact-campaign-v0".to_string(),
        }
    }
}

/// Local artifact campaign input kind.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
pub enum LocalArtifactCampaignInputKind {
    /// Existing Phase U local benchmark artifact manifest metadata.
    LocalBenchmarkArtifactManifest,
    /// Existing Phase U local benchmark artifact output root metadata.
    LocalBenchmarkArtifactOutput,
    /// Existing benchmark pack manifest metadata.
    BenchmarkPackManifest,
    /// Existing pack-readiness report metadata.
    PackReadinessReport,
    /// Existing report-bundle manifest metadata.
    ReportBundleManifest,
    /// Existing local audit-index manifest metadata.
    LocalAuditIndexManifest,
    /// Existing Phase S audit-index ergonomics view metadata.
    AuditIndexErgonomicsView,
    /// Existing Phase T cross-bundle audit-index view metadata.
    CrossBundleAuditIndexView,
    /// Existing local evidence ledger metadata.
    EvidenceLedger,
    /// Other local metadata.
    OtherLocalMetadata,
}

/// Local artifact campaign input reference.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct LocalArtifactCampaignInputRef {
    /// Logical input id.
    pub input_id: String,
    /// Portable relative artifact URI or logical metadata path.
    pub artifact_uri: String,
    /// Input kind.
    pub kind: LocalArtifactCampaignInputKind,
    /// Stable digest over the referenced local metadata bytes.
    pub digest: ArtifactDigest,
    /// Input claim boundary.
    pub claim_boundary: ClaimBoundary,
    /// Notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

/// Local artifact campaign retention policy.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum LocalArtifactCampaignRetentionPolicy {
    /// Retain until an operator deletes the ignored output root.
    ManualDeletion,
    /// Retain until a later reviewed promotion phase supersedes the local copy.
    UntilReviewedPromotion,
}

/// Local artifact campaign manifest.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct LocalArtifactCampaignManifest {
    /// Campaign id.
    pub campaign_id: String,
    /// Schema version.
    pub version: LocalArtifactCampaignVersion,
    /// Source inputs included by reference.
    #[serde(default)]
    pub inputs: Vec<LocalArtifactCampaignInputRef>,
    /// Output claim boundary for the campaign package.
    pub output_claim_boundary: ClaimBoundary,
    /// Retention policy.
    pub retention_policy: LocalArtifactCampaignRetentionPolicy,
    /// Declared validation gates.
    #[serde(default)]
    pub validation_gates: Vec<String>,
    /// Whether this campaign mutates or claims to mutate the accepted Evidence Ledger.
    #[serde(default)]
    pub mutates_accepted_evidence_ledger: bool,
    /// Whether this campaign authorizes or claims external replay.
    #[serde(default)]
    pub external_replay_authorized: bool,
    /// Whether this campaign claims official benchmark evidence.
    #[serde(default)]
    pub official_benchmark_evidence: bool,
    /// Whether this campaign claims ZK backend performance.
    #[serde(default)]
    pub zk_backend_performance_claims: bool,
    /// Whether this campaign claims Level2+ evidence creation.
    #[serde(default)]
    pub creates_level2_evidence: bool,
    /// Whether this campaign populates score axes from local-only evidence.
    #[serde(default)]
    pub populates_score_axes_from_local_only: bool,
    /// Explicit limitations.
    #[serde(default)]
    pub limitations: Vec<String>,
    /// Notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

/// Local artifact campaign validation issue kind.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum LocalArtifactCampaignValidationIssueKind {
    /// Required identity field is empty.
    EmptyIdentity,
    /// Campaign id is not one portable path segment.
    InvalidCampaignId,
    /// Source inputs are missing.
    MissingInputs,
    /// A Phase U local benchmark artifact output reference is missing.
    MissingLocalBenchmarkArtifactOutput,
    /// Duplicate source input id.
    DuplicateInputId,
    /// Duplicate source artifact URI.
    DuplicateArtifactUri,
    /// Artifact reference is not portable relative metadata.
    InvalidArtifactRef,
    /// Digest is missing, unsupported, or malformed.
    InvalidDigest,
    /// Output or input claim boundary is too high.
    ClaimBoundaryEscalation,
    /// Validation gates are missing.
    MissingValidationGate,
    /// External replay was authorized or claimed.
    ExternalReplayAuthorized,
    /// Official benchmark evidence was claimed.
    OfficialBenchmarkEvidenceClaim,
    /// ZK backend performance was claimed.
    ZkBackendPerformanceClaim,
    /// Level2+ evidence was claimed.
    Level2EvidenceClaim,
    /// Accepted Evidence Ledger mutation was claimed.
    AcceptedEvidenceLedgerMutationClaim,
    /// Score axes were populated from local-only evidence.
    LocalOnlyScoreAxisPopulation,
    /// Required limitation text is missing.
    MissingLimitation,
}

/// Local artifact campaign validation issue.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct LocalArtifactCampaignValidationIssue {
    /// Issue kind.
    pub kind: LocalArtifactCampaignValidationIssueKind,
    /// Issue path.
    pub path: String,
    /// Human-readable message.
    pub message: String,
}

/// Local artifact campaign validation report.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct LocalArtifactCampaignValidation {
    /// Whether the campaign manifest is valid.
    pub valid: bool,
    /// Campaign id.
    pub campaign_id: String,
    /// Number of referenced source inputs.
    pub input_count: usize,
    /// Whether accepted Evidence Ledger mutation is absent.
    pub accepted_evidence_ledger_non_mutation: bool,
    /// Whether score axes remain unpopulated from local-only evidence.
    pub score_axes_remain_unpopulated: bool,
    /// Validation issues.
    #[serde(default)]
    pub issues: Vec<LocalArtifactCampaignValidationIssue>,
}

/// Materialized local artifact campaign output metadata.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct LocalArtifactCampaignOutput {
    /// Manifest digest.
    pub manifest_digest: ArtifactDigest,
    /// Manifest digest sidecar path relative to output root.
    pub manifest_digest_relative_path: String,
    /// Validation report digest.
    pub validation_digest: ArtifactDigest,
    /// Validation report digest sidecar path relative to output root.
    pub validation_digest_relative_path: String,
    /// Rendered Markdown digest.
    pub markdown_digest: ArtifactDigest,
    /// Rendered Markdown digest sidecar path relative to output root.
    pub markdown_digest_relative_path: String,
}

/// Required local artifact campaign limitation labels.
pub fn required_local_artifact_campaign_limitations() -> Vec<&'static str> {
    vec![
        "Local artifact campaigns are not official benchmark evidence.",
        "Local artifact campaigns are not accepted Evidence Ledger entries.",
        "Local artifact campaigns do not create Level2+ evidence.",
        "Local artifact campaigns do not prove ZK backend performance.",
        "Local artifact campaigns do not prove semantic correctness.",
        "Local replay artifacts are not official benchmark evidence.",
        "Internal timing telemetry is not ZK backend performance.",
        "Score axes remain unpopulated for local-only evidence.",
        "Accepted-evidence promotion requires a separate reviewed promotion phase.",
        "Official submission requires a separate explicit submission phase.",
    ]
}

/// Serialize a local artifact campaign manifest as deterministic pretty JSON.
pub fn serialize_local_artifact_campaign_manifest_json(
    manifest: &LocalArtifactCampaignManifest,
) -> Result<String> {
    serde_json::to_string_pretty(manifest).map_err(|error| {
        ZkBenchError::serialization("local_artifact_campaign.manifest", error.to_string())
    })
}

/// Deserialize a local artifact campaign manifest from JSON.
pub fn deserialize_local_artifact_campaign_manifest_json(
    json: &str,
) -> Result<LocalArtifactCampaignManifest> {
    serde_json::from_str(json).map_err(|error| {
        ZkBenchError::deserialization("local_artifact_campaign.manifest", error.to_string())
    })
}

/// Serialize a local artifact campaign validation report as deterministic pretty JSON.
pub fn serialize_local_artifact_campaign_validation_json(
    validation: &LocalArtifactCampaignValidation,
) -> Result<String> {
    serde_json::to_string_pretty(validation).map_err(|error| {
        ZkBenchError::serialization("local_artifact_campaign.validation", error.to_string())
    })
}

/// Compute a deterministic digest for a local artifact campaign manifest.
pub fn compute_local_artifact_campaign_manifest_digest(
    manifest: &LocalArtifactCampaignManifest,
) -> Result<ArtifactDigest> {
    compute_artifact_digest(
        manifest,
        Some(ArtifactKind::Other),
        Some(ArtifactRole::Report),
    )
}

/// Build a campaign input by validating an existing Phase U output root.
pub fn build_local_artifact_campaign_input_from_phase_u_output(
    input_id: impl Into<String>,
    artifact_uri: impl Into<String>,
    output_root: &Path,
    protected_paths: &[PathBuf],
    claim_boundary: ClaimBoundary,
    notes: Vec<String>,
) -> Result<LocalArtifactCampaignInputRef> {
    let artifact_uri = artifact_uri.into();
    validate_portable_ref(&artifact_uri).map_err(|error| campaign_error(&artifact_uri, error))?;
    let output = read_local_benchmark_artifact_outputs(output_root, protected_paths)?;
    let digest = compute_phase_u_output_digest(&output)?;
    Ok(LocalArtifactCampaignInputRef {
        input_id: input_id.into(),
        artifact_uri,
        kind: LocalArtifactCampaignInputKind::LocalBenchmarkArtifactOutput,
        digest,
        claim_boundary,
        notes,
    })
}

/// Validate a local artifact campaign manifest.
pub fn validate_local_artifact_campaign_manifest(
    manifest: &LocalArtifactCampaignManifest,
) -> LocalArtifactCampaignValidation {
    let mut issues = Vec::new();

    if manifest.campaign_id.trim().is_empty() {
        push_issue(
            &mut issues,
            LocalArtifactCampaignValidationIssueKind::EmptyIdentity,
            "campaign_id",
            "campaign id must be non-empty",
        );
    }
    if !campaign_id_is_portable_segment(&manifest.campaign_id) {
        push_issue(
            &mut issues,
            LocalArtifactCampaignValidationIssueKind::InvalidCampaignId,
            "campaign_id",
            "campaign id must be one portable path segment",
        );
    }
    if manifest.inputs.is_empty() {
        push_issue(
            &mut issues,
            LocalArtifactCampaignValidationIssueKind::MissingInputs,
            "inputs",
            "at least one local campaign input is required",
        );
    }
    if !manifest
        .inputs
        .iter()
        .any(|input| input.kind == LocalArtifactCampaignInputKind::LocalBenchmarkArtifactOutput)
    {
        push_issue(
            &mut issues,
            LocalArtifactCampaignValidationIssueKind::MissingLocalBenchmarkArtifactOutput,
            "inputs",
            "at least one Phase U local benchmark artifact output is required",
        );
    }
    if manifest.validation_gates.is_empty() {
        push_issue(
            &mut issues,
            LocalArtifactCampaignValidationIssueKind::MissingValidationGate,
            "validation_gates",
            "at least one local validation gate is required",
        );
    }

    let mut input_ids = BTreeSet::new();
    let mut artifact_uris = BTreeSet::new();
    let mut weakest_input_boundary = ClaimBoundary::Level1LocalReplay;
    for (index, input) in manifest.inputs.iter().enumerate() {
        let path = format!("inputs[{index}]");
        if input.input_id.trim().is_empty() {
            push_issue(
                &mut issues,
                LocalArtifactCampaignValidationIssueKind::EmptyIdentity,
                format!("{path}.input_id"),
                "input id must be non-empty",
            );
        }
        if !input_ids.insert(input.input_id.clone()) {
            push_issue(
                &mut issues,
                LocalArtifactCampaignValidationIssueKind::DuplicateInputId,
                format!("{path}.input_id"),
                "duplicate input id",
            );
        }
        if let Err(error) = validate_portable_ref(&input.artifact_uri) {
            push_issue(
                &mut issues,
                LocalArtifactCampaignValidationIssueKind::InvalidArtifactRef,
                format!("{path}.artifact_uri"),
                error,
            );
        }
        if !artifact_uris.insert(input.artifact_uri.clone()) {
            push_issue(
                &mut issues,
                LocalArtifactCampaignValidationIssueKind::DuplicateArtifactUri,
                format!("{path}.artifact_uri"),
                "duplicate artifact uri",
            );
        }
        validate_digest(&mut issues, format!("{path}.digest"), &input.digest);
        if input.claim_boundary.level() > ClaimBoundary::Level1LocalReplay.level() {
            push_issue(
                &mut issues,
                LocalArtifactCampaignValidationIssueKind::ClaimBoundaryEscalation,
                format!("{path}.claim_boundary"),
                "local artifact campaign inputs must remain Level1LocalReplay or below",
            );
        }
        if input.claim_boundary.level() < weakest_input_boundary.level() {
            weakest_input_boundary = input.claim_boundary;
        }
    }

    if manifest.output_claim_boundary.level() > ClaimBoundary::Level1LocalReplay.level() {
        push_issue(
            &mut issues,
            LocalArtifactCampaignValidationIssueKind::ClaimBoundaryEscalation,
            "output_claim_boundary",
            "local artifact campaign output must remain Level1LocalReplay or below",
        );
    }
    if !manifest.inputs.is_empty()
        && manifest.output_claim_boundary.level() > weakest_input_boundary.level()
    {
        push_issue(
            &mut issues,
            LocalArtifactCampaignValidationIssueKind::ClaimBoundaryEscalation,
            "output_claim_boundary",
            "output claim boundary must not exceed the weakest local input boundary",
        );
    }
    if manifest.external_replay_authorized {
        push_issue(
            &mut issues,
            LocalArtifactCampaignValidationIssueKind::ExternalReplayAuthorized,
            "external_replay_authorized",
            "local artifact campaigns must not authorize external replay",
        );
    }
    if manifest.official_benchmark_evidence {
        push_issue(
            &mut issues,
            LocalArtifactCampaignValidationIssueKind::OfficialBenchmarkEvidenceClaim,
            "official_benchmark_evidence",
            "local artifact campaigns must not claim official benchmark evidence",
        );
    }
    if manifest.zk_backend_performance_claims {
        push_issue(
            &mut issues,
            LocalArtifactCampaignValidationIssueKind::ZkBackendPerformanceClaim,
            "zk_backend_performance_claims",
            "local artifact campaigns must not claim ZK backend performance",
        );
    }
    if manifest.creates_level2_evidence {
        push_issue(
            &mut issues,
            LocalArtifactCampaignValidationIssueKind::Level2EvidenceClaim,
            "creates_level2_evidence",
            "local artifact campaigns must not create Level2+ evidence",
        );
    }
    if manifest.mutates_accepted_evidence_ledger {
        push_issue(
            &mut issues,
            LocalArtifactCampaignValidationIssueKind::AcceptedEvidenceLedgerMutationClaim,
            "mutates_accepted_evidence_ledger",
            "local artifact campaigns must not mutate accepted Evidence Ledgers",
        );
    }
    if manifest.populates_score_axes_from_local_only {
        push_issue(
            &mut issues,
            LocalArtifactCampaignValidationIssueKind::LocalOnlyScoreAxisPopulation,
            "populates_score_axes_from_local_only",
            "local-only campaigns must not populate score axes",
        );
    }
    for required in required_local_artifact_campaign_limitations() {
        if !manifest
            .limitations
            .iter()
            .any(|limitation| limitation == required)
        {
            push_issue(
                &mut issues,
                LocalArtifactCampaignValidationIssueKind::MissingLimitation,
                "limitations",
                format!("missing required limitation: {required}"),
            );
        }
    }

    LocalArtifactCampaignValidation {
        valid: issues.is_empty(),
        campaign_id: manifest.campaign_id.clone(),
        input_count: manifest.inputs.len(),
        accepted_evidence_ledger_non_mutation: !manifest.mutates_accepted_evidence_ledger,
        score_axes_remain_unpopulated: !manifest.populates_score_axes_from_local_only,
        issues,
    }
}

/// Render a deterministic Markdown summary for a local artifact campaign.
pub fn render_local_artifact_campaign_markdown(
    manifest: &LocalArtifactCampaignManifest,
    validation: &LocalArtifactCampaignValidation,
) -> Result<String> {
    ensure_valid_campaign(manifest)?;
    if !validation.valid {
        return Err(campaign_error(
            "local_artifact_campaign.validation",
            "validation report must be valid before rendering",
        ));
    }

    let mut markdown = String::new();
    markdown.push_str("# Local Artifact Campaign\n\n");
    markdown.push_str("Status: local durability artifact only.\n\n");
    markdown.push_str("## Claim Boundary\n\n");
    markdown.push_str(&format!(
        "- Output claim boundary: `{}`\n",
        manifest.output_claim_boundary
    ));
    markdown.push_str("- Official benchmark evidence: `false`\n");
    markdown.push_str("- Accepted Evidence Ledger mutation: `false`\n");
    markdown.push_str("- Level2+ evidence creation: `false`\n");
    markdown.push_str("- ZK backend performance claims: `false`\n");
    markdown.push_str("- Score-axis population from local-only evidence: `false`\n\n");

    markdown.push_str("## Inputs\n\n");
    markdown.push_str("| id | kind | artifact | digest | claim boundary |\n");
    markdown.push_str("| --- | --- | --- | --- | --- |\n");
    for input in &manifest.inputs {
        markdown.push_str(&format!(
            "| `{}` | `{:?}` | `{}` | `{}` | `{}` |\n",
            input.input_id,
            input.kind,
            input.artifact_uri,
            input.digest.hex_digest,
            input.claim_boundary
        ));
    }

    markdown.push_str("\n## Validation Gates\n\n");
    for gate in &manifest.validation_gates {
        markdown.push_str("- ");
        markdown.push_str(gate);
        markdown.push('\n');
    }

    markdown.push_str("\n## Required Limitations\n\n");
    for limitation in required_local_artifact_campaign_limitations() {
        markdown.push_str("- ");
        markdown.push_str(limitation);
        markdown.push('\n');
    }
    Ok(markdown)
}

/// Write local artifact campaign outputs under a caller-owned output root.
pub fn write_local_artifact_campaign_outputs(
    output_root: &Path,
    manifest: &LocalArtifactCampaignManifest,
    overwrite: bool,
    protected_paths: &[PathBuf],
) -> Result<LocalArtifactCampaignOutput> {
    ensure_valid_campaign(manifest)?;
    validate_output_root(output_root, protected_paths)?;

    if output_root.exists() {
        reject_symlink(output_root)?;
        if output_root.is_file() {
            return Err(campaign_error(
                output_root.display().to_string(),
                "output root is an existing file",
            ));
        }
        if directory_has_entries(output_root)? {
            if !overwrite {
                return Err(campaign_error(
                    output_root.display().to_string(),
                    "output root is not empty; explicit overwrite is required",
                ));
            }
            let existing = read_local_artifact_campaign_manifest(output_root, protected_paths)?;
            if existing != *manifest {
                return Err(campaign_error(
                    output_root.display().to_string(),
                    "existing output root does not match supplied manifest; refusing repair overwrite",
                ));
            }
        }
    }

    fs::create_dir_all(output_root)
        .map_err(|error| campaign_error(output_root.display().to_string(), error.to_string()))?;

    let validation = validate_local_artifact_campaign_manifest(manifest);
    let manifest_json = serialize_local_artifact_campaign_manifest_json(manifest)?;
    let validation_json = serialize_local_artifact_campaign_validation_json(&validation)?;
    let markdown = render_local_artifact_campaign_markdown(manifest, &validation)?;
    let manifest_digest = digest_local_artifact_campaign_output_bytes(manifest_json.as_bytes());
    let validation_digest = digest_local_artifact_campaign_output_bytes(validation_json.as_bytes());
    let markdown_digest = digest_local_artifact_campaign_output_bytes(markdown.as_bytes());

    write_relative_bytes(
        output_root,
        LOCAL_ARTIFACT_CAMPAIGN_MANIFEST_PATH,
        manifest_json.as_bytes(),
    )?;
    write_relative_bytes(
        output_root,
        LOCAL_ARTIFACT_CAMPAIGN_VALIDATION_PATH,
        validation_json.as_bytes(),
    )?;
    write_relative_bytes(
        output_root,
        LOCAL_ARTIFACT_CAMPAIGN_MARKDOWN_PATH,
        markdown.as_bytes(),
    )?;
    write_relative_bytes(
        output_root,
        LOCAL_ARTIFACT_CAMPAIGN_MANIFEST_DIGEST_PATH,
        format!("{}\n", manifest_digest.hex_digest).as_bytes(),
    )?;
    write_relative_bytes(
        output_root,
        LOCAL_ARTIFACT_CAMPAIGN_VALIDATION_DIGEST_PATH,
        format!("{}\n", validation_digest.hex_digest).as_bytes(),
    )?;
    write_relative_bytes(
        output_root,
        LOCAL_ARTIFACT_CAMPAIGN_MARKDOWN_DIGEST_PATH,
        format!("{}\n", markdown_digest.hex_digest).as_bytes(),
    )?;

    Ok(LocalArtifactCampaignOutput {
        manifest_digest,
        manifest_digest_relative_path: LOCAL_ARTIFACT_CAMPAIGN_MANIFEST_DIGEST_PATH.to_string(),
        validation_digest,
        validation_digest_relative_path: LOCAL_ARTIFACT_CAMPAIGN_VALIDATION_DIGEST_PATH.to_string(),
        markdown_digest,
        markdown_digest_relative_path: LOCAL_ARTIFACT_CAMPAIGN_MARKDOWN_DIGEST_PATH.to_string(),
    })
}

/// Read and validate local artifact campaign outputs.
pub fn read_local_artifact_campaign_outputs(
    output_root: &Path,
    protected_paths: &[PathBuf],
) -> Result<LocalArtifactCampaignOutput> {
    validate_output_root(output_root, protected_paths)?;
    reject_symlink(output_root)?;
    if !output_root.is_dir() {
        return Err(campaign_error(
            output_root.display().to_string(),
            "output root must be a directory",
        ));
    }
    reject_unexpected_existing_paths(output_root)?;

    let manifest_bytes = read_relative_bytes(output_root, LOCAL_ARTIFACT_CAMPAIGN_MANIFEST_PATH)?;
    let validation_bytes =
        read_relative_bytes(output_root, LOCAL_ARTIFACT_CAMPAIGN_VALIDATION_PATH)?;
    let markdown_bytes = read_relative_bytes(output_root, LOCAL_ARTIFACT_CAMPAIGN_MARKDOWN_PATH)?;
    let manifest_digest_sidecar = read_utf8_sidecar(
        output_root,
        LOCAL_ARTIFACT_CAMPAIGN_MANIFEST_DIGEST_PATH,
        "manifest digest sidecar",
    )?;
    let validation_digest_sidecar = read_utf8_sidecar(
        output_root,
        LOCAL_ARTIFACT_CAMPAIGN_VALIDATION_DIGEST_PATH,
        "validation digest sidecar",
    )?;
    let markdown_digest_sidecar = read_utf8_sidecar(
        output_root,
        LOCAL_ARTIFACT_CAMPAIGN_MARKDOWN_DIGEST_PATH,
        "Markdown digest sidecar",
    )?;

    let manifest_digest = digest_local_artifact_campaign_output_bytes(&manifest_bytes);
    if manifest_digest_sidecar.trim() != manifest_digest.hex_digest {
        return Err(campaign_error(
            LOCAL_ARTIFACT_CAMPAIGN_MANIFEST_DIGEST_PATH,
            "manifest JSON bytes do not match digest sidecar",
        ));
    }
    let validation_digest = digest_local_artifact_campaign_output_bytes(&validation_bytes);
    if validation_digest_sidecar.trim() != validation_digest.hex_digest {
        return Err(campaign_error(
            LOCAL_ARTIFACT_CAMPAIGN_VALIDATION_DIGEST_PATH,
            "validation JSON bytes do not match digest sidecar",
        ));
    }
    let markdown_digest = digest_local_artifact_campaign_output_bytes(&markdown_bytes);
    if markdown_digest_sidecar.trim() != markdown_digest.hex_digest {
        return Err(campaign_error(
            LOCAL_ARTIFACT_CAMPAIGN_MARKDOWN_DIGEST_PATH,
            "rendered Markdown bytes do not match digest sidecar",
        ));
    }

    let manifest_json = String::from_utf8(manifest_bytes).map_err(|error| {
        campaign_error(
            LOCAL_ARTIFACT_CAMPAIGN_MANIFEST_PATH,
            format!("manifest JSON is not UTF-8: {error}"),
        )
    })?;
    let validation_json = String::from_utf8(validation_bytes).map_err(|error| {
        campaign_error(
            LOCAL_ARTIFACT_CAMPAIGN_VALIDATION_PATH,
            format!("validation JSON is not UTF-8: {error}"),
        )
    })?;
    let markdown = String::from_utf8(markdown_bytes).map_err(|error| {
        campaign_error(
            LOCAL_ARTIFACT_CAMPAIGN_MARKDOWN_PATH,
            format!("rendered Markdown is not UTF-8: {error}"),
        )
    })?;
    let manifest = deserialize_local_artifact_campaign_manifest_json(&manifest_json)?;
    ensure_valid_campaign(&manifest)?;
    let validation: LocalArtifactCampaignValidation = serde_json::from_str(&validation_json)
        .map_err(|error| {
            ZkBenchError::deserialization("local_artifact_campaign.validation", error.to_string())
        })?;
    let expected_validation = validate_local_artifact_campaign_manifest(&manifest);
    if validation != expected_validation {
        return Err(campaign_error(
            LOCAL_ARTIFACT_CAMPAIGN_VALIDATION_PATH,
            "validation report does not match manifest",
        ));
    }
    let expected_markdown = render_local_artifact_campaign_markdown(&manifest, &validation)?;
    if markdown != expected_markdown {
        return Err(campaign_error(
            LOCAL_ARTIFACT_CAMPAIGN_MARKDOWN_PATH,
            "rendered Markdown does not match manifest and validation",
        ));
    }

    Ok(LocalArtifactCampaignOutput {
        manifest_digest,
        manifest_digest_relative_path: LOCAL_ARTIFACT_CAMPAIGN_MANIFEST_DIGEST_PATH.to_string(),
        validation_digest,
        validation_digest_relative_path: LOCAL_ARTIFACT_CAMPAIGN_VALIDATION_DIGEST_PATH.to_string(),
        markdown_digest,
        markdown_digest_relative_path: LOCAL_ARTIFACT_CAMPAIGN_MARKDOWN_DIGEST_PATH.to_string(),
    })
}

fn read_local_artifact_campaign_manifest(
    output_root: &Path,
    protected_paths: &[PathBuf],
) -> Result<LocalArtifactCampaignManifest> {
    read_local_artifact_campaign_outputs(output_root, protected_paths)?;
    let manifest_bytes = read_relative_bytes(output_root, LOCAL_ARTIFACT_CAMPAIGN_MANIFEST_PATH)?;
    let manifest_json = String::from_utf8(manifest_bytes).map_err(|error| {
        campaign_error(
            LOCAL_ARTIFACT_CAMPAIGN_MANIFEST_PATH,
            format!("manifest JSON is not UTF-8: {error}"),
        )
    })?;
    deserialize_local_artifact_campaign_manifest_json(&manifest_json)
}

fn ensure_valid_campaign(manifest: &LocalArtifactCampaignManifest) -> Result<()> {
    let validation = validate_local_artifact_campaign_manifest(manifest);
    if validation.valid {
        return Ok(());
    }
    let message = validation
        .issues
        .iter()
        .map(|issue| format!("{}: {}", issue.path, issue.message))
        .collect::<Vec<_>>()
        .join("; ");
    Err(campaign_error(
        "local_artifact_campaign.manifest",
        format!("invalid local artifact campaign manifest: {message}"),
    ))
}

fn campaign_id_is_portable_segment(campaign_id: &str) -> bool {
    let trimmed = campaign_id.trim();
    !trimmed.is_empty()
        && trimmed == campaign_id
        && !trimmed.contains('/')
        && !trimmed.contains('\\')
        && !trimmed.contains("..")
        && trimmed
            .chars()
            .all(|ch| ch.is_ascii_alphanumeric() || matches!(ch, '-' | '_' | '.'))
}

fn validate_output_root(output_root: &Path, protected_paths: &[PathBuf]) -> Result<()> {
    if output_root.as_os_str().is_empty() {
        return Err(campaign_error(
            "output_root",
            "output root must be non-empty",
        ));
    }
    let normalized_output = normalize_path(output_root)?;
    let resolved_output = resolve_existing_prefix(output_root)?;
    for protected in protected_paths {
        let normalized_protected = normalize_path(protected)?;
        let resolved_protected = resolve_existing_prefix(protected)?;
        if paths_overlap(&normalized_output, &normalized_protected)
            || paths_overlap(&resolved_output, &resolved_protected)
        {
            return Err(campaign_error(
                output_root.display().to_string(),
                format!(
                    "output root overlaps protected path {}",
                    protected.display()
                ),
            ));
        }
    }
    Ok(())
}

fn resolve_existing_prefix(path: &Path) -> Result<PathBuf> {
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
            Err(error) => {
                return Err(campaign_error(
                    cursor.display().to_string(),
                    error.to_string(),
                ));
            }
        }
    }
}

fn validate_portable_ref(artifact_uri: &str) -> std::result::Result<(), String> {
    let path = Path::new(artifact_uri);
    if artifact_uri.trim().is_empty() {
        return Err("artifact uri must be non-empty".to_string());
    }
    if path.is_absolute()
        || artifact_uri.contains("..")
        || artifact_uri.contains('\\')
        || artifact_uri.contains("://")
        || artifact_uri.contains('|')
        || artifact_uri.contains(';')
        || artifact_uri.contains('$')
    {
        return Err(format!("artifact uri is not portable: {artifact_uri:?}"));
    }
    Ok(())
}

fn validate_relative_output_path(relative_path: &str) -> Result<()> {
    validate_portable_ref(relative_path).map_err(|error| campaign_error(relative_path, error))
}

fn validate_digest(
    issues: &mut Vec<LocalArtifactCampaignValidationIssue>,
    path: String,
    digest: &ArtifactDigest,
) {
    if digest.algorithm != ArtifactDigestAlgorithm::Sha256 {
        push_issue(
            issues,
            LocalArtifactCampaignValidationIssueKind::InvalidDigest,
            path.clone(),
            "digest algorithm must be sha256",
        );
    }
    if digest.hex_digest.len() != 64 || !digest.hex_digest.chars().all(|ch| ch.is_ascii_hexdigit())
    {
        push_issue(
            issues,
            LocalArtifactCampaignValidationIssueKind::InvalidDigest,
            path.clone(),
            "digest must be 64 hex characters",
        );
    }
    if digest.byte_len == 0 {
        push_issue(
            issues,
            LocalArtifactCampaignValidationIssueKind::InvalidDigest,
            path,
            "digest byte length must be non-zero",
        );
    }
}

fn push_issue(
    issues: &mut Vec<LocalArtifactCampaignValidationIssue>,
    kind: LocalArtifactCampaignValidationIssueKind,
    path: impl Into<String>,
    message: impl Into<String>,
) {
    issues.push(LocalArtifactCampaignValidationIssue {
        kind,
        path: path.into(),
        message: message.into(),
    });
}

fn digest_local_artifact_campaign_output_bytes(bytes: &[u8]) -> ArtifactDigest {
    compute_artifact_digest_bytes(bytes, Some(ArtifactKind::Other), Some(ArtifactRole::Report))
}

fn compute_phase_u_output_digest(output: &LocalBenchmarkArtifactOutput) -> Result<ArtifactDigest> {
    compute_artifact_digest(
        output,
        Some(ArtifactKind::Other),
        Some(ArtifactRole::Report),
    )
}

fn expected_relative_paths() -> BTreeSet<String> {
    [
        LOCAL_ARTIFACT_CAMPAIGN_MANIFEST_PATH,
        LOCAL_ARTIFACT_CAMPAIGN_VALIDATION_PATH,
        LOCAL_ARTIFACT_CAMPAIGN_MARKDOWN_PATH,
        LOCAL_ARTIFACT_CAMPAIGN_MANIFEST_DIGEST_PATH,
        LOCAL_ARTIFACT_CAMPAIGN_VALIDATION_DIGEST_PATH,
        LOCAL_ARTIFACT_CAMPAIGN_MARKDOWN_DIGEST_PATH,
    ]
    .into_iter()
    .map(str::to_string)
    .collect()
}

fn reject_unexpected_existing_paths(root: &Path) -> Result<()> {
    let expected = expected_relative_paths();
    let mut seen = BTreeSet::new();
    collect_existing_relative_paths(root, root, &mut seen)?;
    for path in &seen {
        if !expected.contains(path) {
            return Err(campaign_error(path, "unexpected file in output root"));
        }
    }
    for path in &expected {
        if !seen.contains(path) {
            return Err(campaign_error(path, "missing required output file"));
        }
    }
    Ok(())
}

fn collect_existing_relative_paths(
    root: &Path,
    current: &Path,
    seen: &mut BTreeSet<String>,
) -> Result<()> {
    for entry in fs::read_dir(current)
        .map_err(|error| campaign_error(current.display().to_string(), error.to_string()))?
    {
        let entry = entry
            .map_err(|error| campaign_error(current.display().to_string(), error.to_string()))?;
        let path = entry.path();
        reject_symlink(&path)?;
        if path.is_dir() {
            collect_existing_relative_paths(root, &path, seen)?;
        } else {
            let relative = path.strip_prefix(root).map_err(|error| {
                campaign_error(
                    path.display().to_string(),
                    format!("strip prefix failed: {error}"),
                )
            })?;
            let relative = relative.to_string_lossy().replace('\\', "/");
            seen.insert(relative);
        }
    }
    Ok(())
}

fn read_utf8_sidecar(root: &Path, relative_path: &str, label: &str) -> Result<String> {
    String::from_utf8(read_relative_bytes(root, relative_path)?)
        .map_err(|error| campaign_error(relative_path, format!("{label} is not UTF-8: {error}")))
}

fn read_relative_bytes(root: &Path, relative_path: &str) -> Result<Vec<u8>> {
    validate_relative_output_path(relative_path)?;
    fs::read(root.join(relative_path)).map_err(|error| campaign_error(relative_path, error))
}

fn write_relative_bytes(root: &Path, relative_path: &str, bytes: &[u8]) -> Result<()> {
    validate_relative_output_path(relative_path)?;
    let path = root.join(relative_path);
    if let Some(parent) = path.parent() {
        fs::create_dir_all(parent)
            .map_err(|error| campaign_error(parent.display().to_string(), error.to_string()))?;
    }
    fs::write(&path, bytes).map_err(|error| campaign_error(path.display().to_string(), error))
}

fn directory_has_entries(path: &Path) -> Result<bool> {
    Ok(fs::read_dir(path)
        .map_err(|error| campaign_error(path.display().to_string(), error.to_string()))?
        .next()
        .is_some())
}

fn reject_symlink(path: &Path) -> Result<()> {
    let metadata = fs::symlink_metadata(path)
        .map_err(|error| campaign_error(path.display().to_string(), error.to_string()))?;
    if metadata.file_type().is_symlink() {
        return Err(campaign_error(
            path.display().to_string(),
            "symlinks are not allowed in local artifact campaign outputs",
        ));
    }
    Ok(())
}

fn normalize_path(path: &Path) -> Result<PathBuf> {
    let mut normalized = if path.is_absolute() {
        PathBuf::new()
    } else {
        std::env::current_dir().map_err(|error| campaign_error("cwd", error.to_string()))?
    };
    for component in path.components() {
        match component {
            Component::Prefix(prefix) => normalized.push(prefix.as_os_str()),
            Component::RootDir => normalized.push(component.as_os_str()),
            Component::CurDir => {}
            Component::ParentDir => {
                normalized.pop();
            }
            Component::Normal(segment) => normalized.push(segment),
        }
    }
    Ok(normalized)
}

fn paths_overlap(left: &Path, right: &Path) -> bool {
    left == right || left.starts_with(right) || right.starts_with(left)
}

fn campaign_error(path: impl Into<String>, message: impl ToString) -> ZkBenchError {
    ZkBenchError::artifact(path, message.to_string())
}
