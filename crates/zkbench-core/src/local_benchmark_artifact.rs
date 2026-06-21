//! Phase U local benchmark artifact packaging.
//!
//! Local benchmark artifacts are declared-file packaging metadata over existing
//! local outputs. They are not official benchmark evidence, not accepted
//! Evidence Ledger entries, not ZK backend performance evidence, and not
//! Level2+ evidence.

use std::collections::BTreeSet;
use std::fs;
use std::path::{Component, Path, PathBuf};

use serde::{Deserialize, Serialize};

use crate::error::{Result, ZkBenchError};
use crate::evidence::{
    compute_artifact_digest, compute_artifact_digest_bytes, ArtifactDigest,
    ArtifactDigestAlgorithm, ArtifactKind, ArtifactRole, ClaimBoundary,
};

/// Local benchmark artifact manifest path below a caller-owned output root.
pub const LOCAL_BENCHMARK_ARTIFACT_MANIFEST_PATH: &str = "local-benchmark-artifact-manifest.json";

/// Local benchmark artifact rendered Markdown path below a caller-owned output root.
pub const LOCAL_BENCHMARK_ARTIFACT_MARKDOWN_PATH: &str = "rendered/local-benchmark-artifact.md";

/// Local benchmark artifact manifest digest sidecar path below a caller-owned output root.
pub const LOCAL_BENCHMARK_ARTIFACT_MANIFEST_DIGEST_PATH: &str =
    "digests/local-benchmark-artifact-manifest-json.sha256";

/// Local benchmark artifact Markdown digest sidecar path below a caller-owned output root.
pub const LOCAL_BENCHMARK_ARTIFACT_MARKDOWN_DIGEST_PATH: &str =
    "digests/local-benchmark-artifact-markdown.sha256";

/// Phase U local benchmark artifact schema version.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct LocalBenchmarkArtifactVersion {
    /// Logical version string.
    pub value: String,
}

impl Default for LocalBenchmarkArtifactVersion {
    fn default() -> Self {
        Self {
            value: "phase-u-local-benchmark-artifact-v0".to_string(),
        }
    }
}

/// Local benchmark artifact input kind.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
pub enum LocalBenchmarkArtifactInputKind {
    /// Existing benchmark pack manifest metadata.
    BenchmarkPackManifest,
    /// Existing pack-readiness report metadata.
    PackReadinessReport,
    /// Existing pack-readiness validation metadata.
    PackReadinessValidation,
    /// Existing report-bundle manifest metadata.
    ReportBundleManifest,
    /// Existing local audit-index manifest metadata.
    LocalAuditIndexManifest,
    /// Existing Phase S audit-index ergonomics view metadata.
    AuditIndexErgonomicsView,
    /// Existing Phase T cross-bundle audit-index view metadata.
    CrossBundleAuditIndexView,
    /// Existing local replay manifest metadata.
    LocalReplayManifest,
    /// Existing local replay result metadata.
    LocalReplayResult,
    /// Existing local evidence ledger metadata.
    EvidenceLedger,
    /// Existing local score report metadata.
    ScoreReport,
    /// Other local metadata.
    OtherLocalMetadata,
}

/// Local benchmark artifact source input reference.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct LocalBenchmarkArtifactInputRef {
    /// Logical input id.
    pub input_id: String,
    /// Portable relative artifact URI or logical metadata path.
    pub artifact_uri: String,
    /// Input kind.
    pub kind: LocalBenchmarkArtifactInputKind,
    /// Stable digest over the referenced local metadata bytes.
    pub digest: ArtifactDigest,
    /// Input claim boundary.
    pub claim_boundary: ClaimBoundary,
    /// Notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

/// Local benchmark artifact manifest.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct LocalBenchmarkArtifactManifest {
    /// Artifact id.
    pub artifact_id: String,
    /// Schema version.
    pub version: LocalBenchmarkArtifactVersion,
    /// Source inputs included by reference.
    #[serde(default)]
    pub inputs: Vec<LocalBenchmarkArtifactInputRef>,
    /// Output claim boundary for the artifact package.
    pub output_claim_boundary: ClaimBoundary,
    /// Whether this artifact mutates or claims to mutate the accepted Evidence Ledger.
    #[serde(default)]
    pub mutates_accepted_evidence_ledger: bool,
    /// Whether this artifact authorizes or claims external replay.
    #[serde(default)]
    pub external_replay_authorized: bool,
    /// Whether this artifact claims official benchmark evidence.
    #[serde(default)]
    pub official_benchmark_evidence: bool,
    /// Whether this artifact claims ZK backend performance.
    #[serde(default)]
    pub zk_backend_performance_claims: bool,
    /// Whether this artifact claims Level2+ evidence creation.
    #[serde(default)]
    pub creates_level2_evidence: bool,
    /// Whether this artifact populates score axes from local-only evidence.
    #[serde(default)]
    pub populates_score_axes_from_local_only: bool,
    /// Explicit limitations.
    #[serde(default)]
    pub limitations: Vec<String>,
    /// Notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

/// Local benchmark artifact validation issue kind.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum LocalBenchmarkArtifactValidationIssueKind {
    /// Required identity field is empty.
    EmptyIdentity,
    /// Source inputs are missing.
    MissingInputs,
    /// A benchmark pack manifest input is missing.
    MissingBenchmarkPackManifest,
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

/// Local benchmark artifact validation issue.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct LocalBenchmarkArtifactValidationIssue {
    /// Issue kind.
    pub kind: LocalBenchmarkArtifactValidationIssueKind,
    /// Issue path.
    pub path: String,
    /// Human-readable message.
    pub message: String,
}

/// Local benchmark artifact validation report.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct LocalBenchmarkArtifactValidation {
    /// Whether the artifact manifest is valid.
    pub valid: bool,
    /// Validation issues.
    #[serde(default)]
    pub issues: Vec<LocalBenchmarkArtifactValidationIssue>,
}

/// Materialized local benchmark artifact output metadata.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct LocalBenchmarkArtifactOutput {
    /// Manifest digest.
    pub manifest_digest: ArtifactDigest,
    /// Manifest digest sidecar path relative to output root.
    pub manifest_digest_relative_path: String,
    /// Rendered Markdown digest.
    pub markdown_digest: ArtifactDigest,
    /// Rendered Markdown digest sidecar path relative to output root.
    pub markdown_digest_relative_path: String,
}

/// Required local benchmark artifact limitation labels.
pub fn required_local_benchmark_artifact_limitations() -> Vec<&'static str> {
    vec![
        "Local benchmark artifacts are not official benchmark evidence.",
        "Local benchmark artifacts are not accepted Evidence Ledger entries.",
        "Local benchmark artifacts do not create Level2+ evidence.",
        "Local benchmark artifacts do not prove ZK backend performance.",
        "Local benchmark artifacts do not prove semantic correctness.",
        "Local replay artifacts are not official benchmark evidence.",
        "Internal timing telemetry is not ZK backend performance.",
        "Score axes remain unpopulated for local-only evidence.",
        "Acceptance requires a separate reviewed promotion phase.",
    ]
}

/// Serialize a local benchmark artifact manifest as deterministic pretty JSON.
pub fn serialize_local_benchmark_artifact_manifest_json(
    manifest: &LocalBenchmarkArtifactManifest,
) -> Result<String> {
    serde_json::to_string_pretty(manifest).map_err(|error| {
        ZkBenchError::serialization("local_benchmark_artifact.manifest", error.to_string())
    })
}

/// Deserialize a local benchmark artifact manifest from JSON.
pub fn deserialize_local_benchmark_artifact_manifest_json(
    json: &str,
) -> Result<LocalBenchmarkArtifactManifest> {
    serde_json::from_str(json).map_err(|error| {
        ZkBenchError::deserialization("local_benchmark_artifact.manifest", error.to_string())
    })
}

/// Compute a deterministic digest for a local benchmark artifact manifest.
pub fn compute_local_benchmark_artifact_manifest_digest(
    manifest: &LocalBenchmarkArtifactManifest,
) -> Result<ArtifactDigest> {
    compute_artifact_digest(
        manifest,
        Some(ArtifactKind::Other),
        Some(ArtifactRole::Report),
    )
}

/// Validate a local benchmark artifact manifest.
pub fn validate_local_benchmark_artifact_manifest(
    manifest: &LocalBenchmarkArtifactManifest,
) -> LocalBenchmarkArtifactValidation {
    let mut issues = Vec::new();

    if manifest.artifact_id.trim().is_empty() {
        push_issue(
            &mut issues,
            LocalBenchmarkArtifactValidationIssueKind::EmptyIdentity,
            "artifact_id",
            "artifact id must be non-empty",
        );
    }

    if manifest.inputs.is_empty() {
        push_issue(
            &mut issues,
            LocalBenchmarkArtifactValidationIssueKind::MissingInputs,
            "inputs",
            "at least one local input is required",
        );
    }

    if !manifest
        .inputs
        .iter()
        .any(|input| input.kind == LocalBenchmarkArtifactInputKind::BenchmarkPackManifest)
    {
        push_issue(
            &mut issues,
            LocalBenchmarkArtifactValidationIssueKind::MissingBenchmarkPackManifest,
            "inputs",
            "at least one benchmark pack manifest input is required",
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
                LocalBenchmarkArtifactValidationIssueKind::EmptyIdentity,
                format!("{path}.input_id"),
                "input id must be non-empty",
            );
        }
        if !input_ids.insert(input.input_id.clone()) {
            push_issue(
                &mut issues,
                LocalBenchmarkArtifactValidationIssueKind::DuplicateInputId,
                format!("{path}.input_id"),
                "duplicate input id",
            );
        }
        if let Err(error) = validate_portable_ref(&input.artifact_uri) {
            push_issue(
                &mut issues,
                LocalBenchmarkArtifactValidationIssueKind::InvalidArtifactRef,
                format!("{path}.artifact_uri"),
                error,
            );
        }
        if !artifact_uris.insert(input.artifact_uri.clone()) {
            push_issue(
                &mut issues,
                LocalBenchmarkArtifactValidationIssueKind::DuplicateArtifactUri,
                format!("{path}.artifact_uri"),
                "duplicate artifact uri",
            );
        }
        validate_digest(&mut issues, format!("{path}.digest"), &input.digest);
        if input.claim_boundary.level() > ClaimBoundary::Level1LocalReplay.level() {
            push_issue(
                &mut issues,
                LocalBenchmarkArtifactValidationIssueKind::ClaimBoundaryEscalation,
                format!("{path}.claim_boundary"),
                "local benchmark artifact inputs must remain Level1LocalReplay or below",
            );
        }
        if input.claim_boundary.level() < weakest_input_boundary.level() {
            weakest_input_boundary = input.claim_boundary;
        }
    }

    if manifest.output_claim_boundary.level() > ClaimBoundary::Level1LocalReplay.level() {
        push_issue(
            &mut issues,
            LocalBenchmarkArtifactValidationIssueKind::ClaimBoundaryEscalation,
            "output_claim_boundary",
            "local benchmark artifact output must remain Level1LocalReplay or below",
        );
    }
    if !manifest.inputs.is_empty()
        && manifest.output_claim_boundary.level() > weakest_input_boundary.level()
    {
        push_issue(
            &mut issues,
            LocalBenchmarkArtifactValidationIssueKind::ClaimBoundaryEscalation,
            "output_claim_boundary",
            "output claim boundary must not exceed the weakest local input boundary",
        );
    }
    if manifest.external_replay_authorized {
        push_issue(
            &mut issues,
            LocalBenchmarkArtifactValidationIssueKind::ExternalReplayAuthorized,
            "external_replay_authorized",
            "local benchmark artifacts must not authorize external replay",
        );
    }
    if manifest.official_benchmark_evidence {
        push_issue(
            &mut issues,
            LocalBenchmarkArtifactValidationIssueKind::OfficialBenchmarkEvidenceClaim,
            "official_benchmark_evidence",
            "local benchmark artifacts must not claim official benchmark evidence",
        );
    }
    if manifest.zk_backend_performance_claims {
        push_issue(
            &mut issues,
            LocalBenchmarkArtifactValidationIssueKind::ZkBackendPerformanceClaim,
            "zk_backend_performance_claims",
            "local benchmark artifacts must not claim ZK backend performance",
        );
    }
    if manifest.creates_level2_evidence {
        push_issue(
            &mut issues,
            LocalBenchmarkArtifactValidationIssueKind::Level2EvidenceClaim,
            "creates_level2_evidence",
            "local benchmark artifacts must not create Level2+ evidence",
        );
    }
    if manifest.mutates_accepted_evidence_ledger {
        push_issue(
            &mut issues,
            LocalBenchmarkArtifactValidationIssueKind::AcceptedEvidenceLedgerMutationClaim,
            "mutates_accepted_evidence_ledger",
            "local benchmark artifacts must not mutate accepted Evidence Ledgers",
        );
    }
    if manifest.populates_score_axes_from_local_only {
        push_issue(
            &mut issues,
            LocalBenchmarkArtifactValidationIssueKind::LocalOnlyScoreAxisPopulation,
            "populates_score_axes_from_local_only",
            "local-only artifacts must not populate score axes",
        );
    }
    for required in required_local_benchmark_artifact_limitations() {
        if !manifest
            .limitations
            .iter()
            .any(|limitation| limitation == required)
        {
            push_issue(
                &mut issues,
                LocalBenchmarkArtifactValidationIssueKind::MissingLimitation,
                "limitations",
                format!("missing required limitation: {required}"),
            );
        }
    }

    LocalBenchmarkArtifactValidation {
        valid: issues.is_empty(),
        issues,
    }
}

/// Render a deterministic Markdown summary for a local benchmark artifact manifest.
pub fn render_local_benchmark_artifact_markdown(
    manifest: &LocalBenchmarkArtifactManifest,
) -> Result<String> {
    ensure_valid_manifest(manifest)?;

    let mut markdown = String::new();
    markdown.push_str("# Local Benchmark Artifact\n\n");
    markdown.push_str("Status: local reproducibility packaging only.\n\n");
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
    markdown.push_str("\n## Required Limitations\n\n");
    for limitation in required_local_benchmark_artifact_limitations() {
        markdown.push_str("- ");
        markdown.push_str(limitation);
        markdown.push('\n');
    }
    Ok(markdown)
}

/// Write local benchmark artifact outputs under a caller-owned output root.
pub fn write_local_benchmark_artifact_outputs(
    output_root: &Path,
    manifest: &LocalBenchmarkArtifactManifest,
    overwrite: bool,
    protected_paths: &[PathBuf],
) -> Result<LocalBenchmarkArtifactOutput> {
    ensure_valid_manifest(manifest)?;
    validate_output_root(output_root, protected_paths)?;

    if output_root.exists() {
        reject_symlink(output_root)?;
        if output_root.is_file() {
            return Err(artifact_error(
                output_root.display().to_string(),
                "output root is an existing file",
            ));
        }
        if directory_has_entries(output_root)? {
            if !overwrite {
                return Err(artifact_error(
                    output_root.display().to_string(),
                    "output root is not empty; explicit overwrite is required",
                ));
            }
            let existing = read_local_benchmark_artifact_manifest(output_root, protected_paths)?;
            if existing != *manifest {
                return Err(artifact_error(
                    output_root.display().to_string(),
                    "existing output root does not match supplied manifest; refusing repair overwrite",
                ));
            }
        }
    }

    fs::create_dir_all(output_root)
        .map_err(|error| artifact_error(output_root.display().to_string(), error.to_string()))?;

    let manifest_json = serialize_local_benchmark_artifact_manifest_json(manifest)?;
    let markdown = render_local_benchmark_artifact_markdown(manifest)?;
    let manifest_bytes = manifest_json.as_bytes();
    let markdown_bytes = markdown.as_bytes();
    let manifest_digest = digest_local_benchmark_artifact_output_bytes(manifest_bytes);
    let markdown_digest = digest_local_benchmark_artifact_output_bytes(markdown_bytes);

    write_relative_bytes(
        output_root,
        LOCAL_BENCHMARK_ARTIFACT_MANIFEST_PATH,
        manifest_bytes,
    )?;
    write_relative_bytes(
        output_root,
        LOCAL_BENCHMARK_ARTIFACT_MARKDOWN_PATH,
        markdown_bytes,
    )?;
    write_relative_bytes(
        output_root,
        LOCAL_BENCHMARK_ARTIFACT_MANIFEST_DIGEST_PATH,
        format!("{}\n", manifest_digest.hex_digest).as_bytes(),
    )?;
    write_relative_bytes(
        output_root,
        LOCAL_BENCHMARK_ARTIFACT_MARKDOWN_DIGEST_PATH,
        format!("{}\n", markdown_digest.hex_digest).as_bytes(),
    )?;

    Ok(LocalBenchmarkArtifactOutput {
        manifest_digest,
        manifest_digest_relative_path: LOCAL_BENCHMARK_ARTIFACT_MANIFEST_DIGEST_PATH.to_string(),
        markdown_digest,
        markdown_digest_relative_path: LOCAL_BENCHMARK_ARTIFACT_MARKDOWN_DIGEST_PATH.to_string(),
    })
}

/// Read and validate local benchmark artifact outputs.
pub fn read_local_benchmark_artifact_outputs(
    output_root: &Path,
    protected_paths: &[PathBuf],
) -> Result<LocalBenchmarkArtifactOutput> {
    validate_output_root(output_root, protected_paths)?;
    reject_symlink(output_root)?;
    if !output_root.is_dir() {
        return Err(artifact_error(
            output_root.display().to_string(),
            "output root must be a directory",
        ));
    }
    reject_unexpected_existing_paths(output_root)?;

    let manifest_bytes = read_relative_bytes(output_root, LOCAL_BENCHMARK_ARTIFACT_MANIFEST_PATH)?;
    let markdown_bytes = read_relative_bytes(output_root, LOCAL_BENCHMARK_ARTIFACT_MARKDOWN_PATH)?;
    let manifest_digest_sidecar = String::from_utf8(read_relative_bytes(
        output_root,
        LOCAL_BENCHMARK_ARTIFACT_MANIFEST_DIGEST_PATH,
    )?)
    .map_err(|error| {
        artifact_error(
            LOCAL_BENCHMARK_ARTIFACT_MANIFEST_DIGEST_PATH,
            format!("manifest digest sidecar is not UTF-8: {error}"),
        )
    })?;
    let markdown_digest_sidecar = String::from_utf8(read_relative_bytes(
        output_root,
        LOCAL_BENCHMARK_ARTIFACT_MARKDOWN_DIGEST_PATH,
    )?)
    .map_err(|error| {
        artifact_error(
            LOCAL_BENCHMARK_ARTIFACT_MARKDOWN_DIGEST_PATH,
            format!("Markdown digest sidecar is not UTF-8: {error}"),
        )
    })?;

    let manifest_digest = digest_local_benchmark_artifact_output_bytes(&manifest_bytes);
    if manifest_digest_sidecar.trim() != manifest_digest.hex_digest {
        return Err(artifact_error(
            LOCAL_BENCHMARK_ARTIFACT_MANIFEST_DIGEST_PATH,
            "manifest JSON bytes do not match digest sidecar",
        ));
    }
    let markdown_digest = digest_local_benchmark_artifact_output_bytes(&markdown_bytes);
    if markdown_digest_sidecar.trim() != markdown_digest.hex_digest {
        return Err(artifact_error(
            LOCAL_BENCHMARK_ARTIFACT_MARKDOWN_DIGEST_PATH,
            "rendered Markdown bytes do not match digest sidecar",
        ));
    }

    let manifest_json = String::from_utf8(manifest_bytes).map_err(|error| {
        artifact_error(
            LOCAL_BENCHMARK_ARTIFACT_MANIFEST_PATH,
            format!("manifest JSON is not UTF-8: {error}"),
        )
    })?;
    let markdown = String::from_utf8(markdown_bytes).map_err(|error| {
        artifact_error(
            LOCAL_BENCHMARK_ARTIFACT_MARKDOWN_PATH,
            format!("rendered Markdown is not UTF-8: {error}"),
        )
    })?;
    let manifest = deserialize_local_benchmark_artifact_manifest_json(&manifest_json)?;
    ensure_valid_manifest(&manifest)?;
    let expected_markdown = render_local_benchmark_artifact_markdown(&manifest)?;
    if markdown != expected_markdown {
        return Err(artifact_error(
            LOCAL_BENCHMARK_ARTIFACT_MARKDOWN_PATH,
            "rendered Markdown does not match manifest",
        ));
    }

    Ok(LocalBenchmarkArtifactOutput {
        manifest_digest,
        manifest_digest_relative_path: LOCAL_BENCHMARK_ARTIFACT_MANIFEST_DIGEST_PATH.to_string(),
        markdown_digest,
        markdown_digest_relative_path: LOCAL_BENCHMARK_ARTIFACT_MARKDOWN_DIGEST_PATH.to_string(),
    })
}

fn read_local_benchmark_artifact_manifest(
    output_root: &Path,
    protected_paths: &[PathBuf],
) -> Result<LocalBenchmarkArtifactManifest> {
    read_local_benchmark_artifact_outputs(output_root, protected_paths)?;
    let manifest_bytes = read_relative_bytes(output_root, LOCAL_BENCHMARK_ARTIFACT_MANIFEST_PATH)?;
    let manifest_json = String::from_utf8(manifest_bytes).map_err(|error| {
        artifact_error(
            LOCAL_BENCHMARK_ARTIFACT_MANIFEST_PATH,
            format!("manifest JSON is not UTF-8: {error}"),
        )
    })?;
    deserialize_local_benchmark_artifact_manifest_json(&manifest_json)
}

fn ensure_valid_manifest(manifest: &LocalBenchmarkArtifactManifest) -> Result<()> {
    let validation = validate_local_benchmark_artifact_manifest(manifest);
    if validation.valid {
        return Ok(());
    }
    let message = validation
        .issues
        .iter()
        .map(|issue| format!("{}: {}", issue.path, issue.message))
        .collect::<Vec<_>>()
        .join("; ");
    Err(artifact_error(
        "local_benchmark_artifact.manifest",
        format!("invalid local benchmark artifact manifest: {message}"),
    ))
}

fn validate_output_root(output_root: &Path, protected_paths: &[PathBuf]) -> Result<()> {
    if output_root.as_os_str().is_empty() {
        return Err(artifact_error(
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
            return Err(artifact_error(
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
                return Err(artifact_error(
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
    validate_portable_ref(relative_path).map_err(|error| artifact_error(relative_path, error))
}

fn validate_digest(
    issues: &mut Vec<LocalBenchmarkArtifactValidationIssue>,
    path: String,
    digest: &ArtifactDigest,
) {
    if digest.algorithm != ArtifactDigestAlgorithm::Sha256 {
        push_issue(
            issues,
            LocalBenchmarkArtifactValidationIssueKind::InvalidDigest,
            path.clone(),
            "digest algorithm must be sha256",
        );
    }
    if digest.hex_digest.len() != 64 || !digest.hex_digest.chars().all(|ch| ch.is_ascii_hexdigit())
    {
        push_issue(
            issues,
            LocalBenchmarkArtifactValidationIssueKind::InvalidDigest,
            path.clone(),
            "digest must be 64 hex characters",
        );
    }
    if digest.byte_len == 0 {
        push_issue(
            issues,
            LocalBenchmarkArtifactValidationIssueKind::InvalidDigest,
            path,
            "digest byte length must be non-zero",
        );
    }
}

fn push_issue(
    issues: &mut Vec<LocalBenchmarkArtifactValidationIssue>,
    kind: LocalBenchmarkArtifactValidationIssueKind,
    path: impl Into<String>,
    message: impl Into<String>,
) {
    issues.push(LocalBenchmarkArtifactValidationIssue {
        kind,
        path: path.into(),
        message: message.into(),
    });
}

fn digest_local_benchmark_artifact_output_bytes(bytes: &[u8]) -> ArtifactDigest {
    compute_artifact_digest_bytes(bytes, Some(ArtifactKind::Other), Some(ArtifactRole::Report))
}

fn expected_relative_paths() -> BTreeSet<String> {
    [
        LOCAL_BENCHMARK_ARTIFACT_MANIFEST_PATH,
        LOCAL_BENCHMARK_ARTIFACT_MARKDOWN_PATH,
        LOCAL_BENCHMARK_ARTIFACT_MANIFEST_DIGEST_PATH,
        LOCAL_BENCHMARK_ARTIFACT_MARKDOWN_DIGEST_PATH,
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
            return Err(artifact_error(path, "unexpected file in output root"));
        }
    }
    for path in &expected {
        if !seen.contains(path) {
            return Err(artifact_error(path, "missing required output file"));
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
        .map_err(|error| artifact_error(current.display().to_string(), error.to_string()))?
    {
        let entry = entry
            .map_err(|error| artifact_error(current.display().to_string(), error.to_string()))?;
        let path = entry.path();
        reject_symlink(&path)?;
        if path.is_dir() {
            collect_existing_relative_paths(root, &path, seen)?;
        } else {
            let relative = path.strip_prefix(root).map_err(|error| {
                artifact_error(
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

fn read_relative_bytes(root: &Path, relative_path: &str) -> Result<Vec<u8>> {
    validate_relative_output_path(relative_path)?;
    fs::read(root.join(relative_path))
        .map_err(|error| artifact_error(relative_path, error.to_string()))
}

fn write_relative_bytes(root: &Path, relative_path: &str, bytes: &[u8]) -> Result<()> {
    validate_relative_output_path(relative_path)?;
    let path = root.join(relative_path);
    if let Some(parent) = path.parent() {
        fs::create_dir_all(parent)
            .map_err(|error| artifact_error(parent.display().to_string(), error.to_string()))?;
    }
    fs::write(&path, bytes).map_err(|error| artifact_error(path.display().to_string(), error))
}

fn directory_has_entries(path: &Path) -> Result<bool> {
    Ok(fs::read_dir(path)
        .map_err(|error| artifact_error(path.display().to_string(), error.to_string()))?
        .next()
        .is_some())
}

fn reject_symlink(path: &Path) -> Result<()> {
    let metadata = fs::symlink_metadata(path)
        .map_err(|error| artifact_error(path.display().to_string(), error.to_string()))?;
    if metadata.file_type().is_symlink() {
        return Err(artifact_error(
            path.display().to_string(),
            "symlinks are not allowed in local benchmark artifact outputs",
        ));
    }
    Ok(())
}

fn normalize_path(path: &Path) -> Result<PathBuf> {
    let mut normalized = if path.is_absolute() {
        PathBuf::new()
    } else {
        std::env::current_dir().map_err(|error| artifact_error("cwd", error.to_string()))?
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

fn artifact_error(path: impl Into<String>, message: impl ToString) -> ZkBenchError {
    ZkBenchError::artifact(path, message.to_string())
}
