//! Phase O local reproducible-pack readiness metadata.
//!
//! Readiness reports are local metadata only. They do not create Level2
//! evidence, do not execute replay commands, do not import external results,
//! and do not mutate accepted evidence ledgers.

use serde::{Deserialize, Serialize};

use crate::error::Result;
use crate::evidence::{
    compute_artifact_digest, ArtifactDigest, ArtifactDigestAlgorithm, ArtifactKind, ArtifactRole,
    ClaimBoundary, EvidenceClass,
};

/// Phase O pack-readiness schema version.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct PackReadinessVersion {
    /// Logical version string.
    pub value: String,
}

impl Default for PackReadinessVersion {
    fn default() -> Self {
        Self {
            value: "phase-o-local-pack-readiness-v0".to_string(),
        }
    }
}

/// Local pack-readiness input kind.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
pub enum PackReadinessInputKind {
    /// Benchmark pack manifest metadata.
    BenchmarkPackManifest,
    /// Benchmark pack validation report metadata.
    BenchmarkPackValidationReport,
    /// Local replay manifest metadata.
    LocalReplayManifest,
    /// Local replay result metadata.
    LocalReplayResult,
    /// Local evidence ledger metadata.
    EvidenceLedger,
    /// Local score report metadata.
    ScoreReport,
    /// Local soak report bundle metadata.
    SoakReportBundle,
    /// Failure corpus metadata.
    FailureCorpus,
    /// Reproduction bundle metadata.
    ReproductionBundle,
    /// Evidence append preview metadata.
    EvidenceAppendPreview,
    /// Level2 eligibility report metadata.
    Level2EligibilityReport,
    /// Other local metadata.
    OtherLocalMetadata,
}

/// Local pack-readiness input reference.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct PackReadinessInputRef {
    /// Logical input id.
    pub input_id: String,
    /// Portable artifact URI or logical artifact id.
    pub artifact_uri: String,
    /// Input kind.
    pub kind: PackReadinessInputKind,
    /// Stable input digest.
    pub digest: ArtifactDigest,
    /// Input evidence class.
    pub evidence_class: EvidenceClass,
    /// Input claim boundary.
    pub claim_boundary: ClaimBoundary,
    /// Notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

/// Inert replay-command metadata for future local pack readiness checks.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct PackReadinessReplayCommandMetadata {
    /// Logical command id.
    pub command_id: String,
    /// Human-readable local action label.
    pub action_label: String,
    /// Portable input artifact URI or logical artifact id.
    pub input_artifact_uri: String,
    /// Portable output artifact URI or logical artifact id.
    pub output_artifact_uri: String,
    /// Whether this is inert metadata only.
    pub inert: bool,
    /// Notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

/// Local pack-readiness check kind.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
pub enum PackReadinessCheckKind {
    /// Pack paths are relative and portable.
    RelativePathCoverage,
    /// Pack files have SHA-256 digest coverage.
    Sha256DigestCoverage,
    /// Manifest summary counts match referenced local artifacts.
    ManifestSummaryConsistency,
    /// Replay manifests/results are deterministic metadata.
    ReplayRoundTripReady,
    /// Evidence ledger digest chain validation is represented.
    EvidenceLedgerDigestChainReady,
    /// Local score reports are claim-capped.
    ScoreReportClaimCap,
    /// Replay commands remain inert metadata.
    InertReplayCommandMetadata,
    /// Output claim boundary is capped by local inputs.
    WeakestClaimBoundaryCap,
    /// No Level2 evidence is created.
    NoLevel2Evidence,
    /// No external replay evidence is claimed.
    NoExternalReplay,
}

/// Local pack-readiness check result.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct PackReadinessCheck {
    /// Check kind.
    pub kind: PackReadinessCheckKind,
    /// Whether this local readiness check passed.
    pub passed: bool,
    /// Claim boundary for this check.
    pub claim_boundary: ClaimBoundary,
    /// Notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

/// Local reproducible-pack readiness report.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct PackReadinessReport {
    /// Report id.
    pub report_id: String,
    /// Schema version.
    pub version: PackReadinessVersion,
    /// Source benchmark pack id.
    pub source_pack_id: String,
    /// Source pack digest.
    pub source_pack_digest: ArtifactDigest,
    /// Source metadata inputs.
    #[serde(default)]
    pub inputs: Vec<PackReadinessInputRef>,
    /// Inert replay-command metadata.
    #[serde(default)]
    pub replay_commands: Vec<PackReadinessReplayCommandMetadata>,
    /// Local readiness checks.
    #[serde(default)]
    pub checks: Vec<PackReadinessCheck>,
    /// Whether external replay is authorized or claimed.
    #[serde(default)]
    pub external_replay_authorized: bool,
    /// Whether this report claims to create Level2 evidence.
    #[serde(default)]
    pub creates_level2_evidence: bool,
    /// Whether this report claims official benchmark evidence.
    #[serde(default)]
    pub official_benchmark_evidence: bool,
    /// Whether this report claims ZK backend performance evidence.
    #[serde(default)]
    pub zk_backend_performance_claims: bool,
    /// Output claim boundary.
    pub output_claim_boundary: ClaimBoundary,
    /// Explicit limitations.
    #[serde(default)]
    pub limitations: Vec<String>,
    /// Notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

/// Pack-readiness validation issue kind.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum PackReadinessValidationIssueKind {
    /// Required identity field is empty.
    EmptyIdentity,
    /// Source inputs are missing.
    MissingInputs,
    /// Required checks are missing.
    MissingRequiredCheck,
    /// Digest is missing, unsupported, or malformed.
    InvalidDigest,
    /// Artifact reference is not portable relative metadata.
    InvalidArtifactRef,
    /// Output or check claim boundary is too high.
    ClaimBoundaryEscalation,
    /// External replay was authorized or claimed.
    ExternalReplayAuthorized,
    /// Report claimed to create Level2 evidence.
    Level2EvidenceClaim,
    /// Report claimed official benchmark evidence.
    OfficialBenchmarkEvidenceClaim,
    /// Report claimed ZK backend performance.
    ZkBackendPerformanceClaim,
    /// Replay command metadata is executable or unsafe.
    NonInertReplayCommand,
    /// A required readiness check failed.
    FailedCheck,
    /// Append preview was treated above Level0 metadata.
    AppendPreviewBoundary,
    /// Level2 eligibility report was treated as Level2 evidence.
    Level2EligibilityBoundary,
    /// Required limitation text is missing.
    MissingLimitation,
}

/// Pack-readiness validation issue.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct PackReadinessValidationIssue {
    /// Issue kind.
    pub kind: PackReadinessValidationIssueKind,
    /// Path.
    pub path: String,
    /// Message.
    pub message: String,
}

/// Pack-readiness validation report.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct PackReadinessValidation {
    /// Whether validation passed.
    pub valid: bool,
    /// Issues.
    #[serde(default)]
    pub issues: Vec<PackReadinessValidationIssue>,
    /// Claim boundary of the validation report.
    pub claim_boundary: ClaimBoundary,
}

/// Compute a deterministic digest for a pack-readiness report.
pub fn compute_pack_readiness_report_digest(
    report: &PackReadinessReport,
) -> Result<ArtifactDigest> {
    compute_artifact_digest(
        report,
        Some(ArtifactKind::ScoreReport),
        Some(ArtifactRole::Report),
    )
}

/// Validate local reproducible-pack readiness metadata.
pub fn validate_pack_readiness_report(report: &PackReadinessReport) -> PackReadinessValidation {
    let mut issues = Vec::new();

    validate_identity(&mut issues, "report_id", &report.report_id);
    validate_identity(&mut issues, "version.value", &report.version.value);
    validate_identity(&mut issues, "source_pack_id", &report.source_pack_id);
    validate_digest(
        &mut issues,
        "source_pack_digest",
        &report.source_pack_digest,
    );

    if report.inputs.is_empty() {
        push_issue(
            &mut issues,
            PackReadinessValidationIssueKind::MissingInputs,
            "inputs",
            "pack-readiness report must bind at least one source input",
        );
    }

    for (index, input) in report.inputs.iter().enumerate() {
        let path = format!("inputs[{index}]");
        validate_identity(&mut issues, format!("{path}.input_id"), &input.input_id);
        if !is_portable_relative_artifact_ref(&input.artifact_uri) {
            push_issue(
                &mut issues,
                PackReadinessValidationIssueKind::InvalidArtifactRef,
                format!("{path}.artifact_uri"),
                "input artifact URI must be portable relative metadata",
            );
        }
        validate_digest(&mut issues, format!("{path}.digest"), &input.digest);
        if input.claim_boundary > ClaimBoundary::Level1LocalReplay {
            push_issue(
                &mut issues,
                PackReadinessValidationIssueKind::ClaimBoundaryEscalation,
                format!("{path}.claim_boundary"),
                "Phase O local readiness inputs must remain Level1LocalReplay or lower",
            );
        }
        if input.kind == PackReadinessInputKind::EvidenceAppendPreview
            && input.claim_boundary != ClaimBoundary::Level0DesignNote
        {
            push_issue(
                &mut issues,
                PackReadinessValidationIssueKind::AppendPreviewBoundary,
                format!("{path}.claim_boundary"),
                "append previews are metadata only and must remain Level0DesignNote",
            );
        }
        if input.kind == PackReadinessInputKind::Level2EligibilityReport
            && input.claim_boundary != ClaimBoundary::Level0DesignNote
        {
            push_issue(
                &mut issues,
                PackReadinessValidationIssueKind::Level2EligibilityBoundary,
                format!("{path}.claim_boundary"),
                "Level2 eligibility reports are not Level2 evidence",
            );
        }
    }

    for (index, command) in report.replay_commands.iter().enumerate() {
        let path = format!("replay_commands[{index}]");
        validate_identity(
            &mut issues,
            format!("{path}.command_id"),
            &command.command_id,
        );
        validate_identity(
            &mut issues,
            format!("{path}.action_label"),
            &command.action_label,
        );
        if !command.inert {
            push_issue(
                &mut issues,
                PackReadinessValidationIssueKind::NonInertReplayCommand,
                format!("{path}.inert"),
                "replay command metadata must be inert",
            );
        }
        if !is_portable_relative_artifact_ref(&command.input_artifact_uri) {
            push_issue(
                &mut issues,
                PackReadinessValidationIssueKind::InvalidArtifactRef,
                format!("{path}.input_artifact_uri"),
                "replay command input artifact URI must be portable relative metadata",
            );
        }
        if !is_portable_relative_artifact_ref(&command.output_artifact_uri) {
            push_issue(
                &mut issues,
                PackReadinessValidationIssueKind::InvalidArtifactRef,
                format!("{path}.output_artifact_uri"),
                "replay command output artifact URI must be portable relative metadata",
            );
        }
        if contains_shell_payload(&command.action_label) {
            push_issue(
                &mut issues,
                PackReadinessValidationIssueKind::NonInertReplayCommand,
                format!("{path}.action_label"),
                "replay command metadata must not contain shell payloads",
            );
        }
    }

    for required in required_check_kinds() {
        if !report
            .checks
            .iter()
            .any(|check| check.kind == required && check.passed)
        {
            push_issue(
                &mut issues,
                PackReadinessValidationIssueKind::MissingRequiredCheck,
                "checks",
                format!("required readiness check {required:?} is missing or not passed"),
            );
        }
    }

    for (index, check) in report.checks.iter().enumerate() {
        if !check.passed {
            push_issue(
                &mut issues,
                PackReadinessValidationIssueKind::FailedCheck,
                format!("checks[{index}].passed"),
                "readiness check failed",
            );
        }
        if check.claim_boundary > ClaimBoundary::Level0DesignNote {
            push_issue(
                &mut issues,
                PackReadinessValidationIssueKind::ClaimBoundaryEscalation,
                format!("checks[{index}].claim_boundary"),
                "readiness checks are Level0DesignNote metadata",
            );
        }
    }

    if report.external_replay_authorized {
        push_issue(
            &mut issues,
            PackReadinessValidationIssueKind::ExternalReplayAuthorized,
            "external_replay_authorized",
            "Phase O local readiness must not authorize external replay",
        );
    }
    if report.creates_level2_evidence {
        push_issue(
            &mut issues,
            PackReadinessValidationIssueKind::Level2EvidenceClaim,
            "creates_level2_evidence",
            "local pack-readiness metadata is not Level2 evidence",
        );
    }
    if report.official_benchmark_evidence {
        push_issue(
            &mut issues,
            PackReadinessValidationIssueKind::OfficialBenchmarkEvidenceClaim,
            "official_benchmark_evidence",
            "local pack-readiness metadata is not official benchmark evidence",
        );
    }
    if report.zk_backend_performance_claims {
        push_issue(
            &mut issues,
            PackReadinessValidationIssueKind::ZkBackendPerformanceClaim,
            "zk_backend_performance_claims",
            "local pack-readiness metadata is not ZK backend performance evidence",
        );
    }
    if report.output_claim_boundary != ClaimBoundary::Level0DesignNote {
        push_issue(
            &mut issues,
            PackReadinessValidationIssueKind::ClaimBoundaryEscalation,
            "output_claim_boundary",
            "pack-readiness reports remain Level0DesignNote",
        );
    }

    if !has_limitation(
        &report.limitations,
        &["pack-readiness", "not level2 evidence"],
    ) {
        push_issue(
            &mut issues,
            PackReadinessValidationIssueKind::MissingLimitation,
            "limitations",
            "limitations must state that pack-readiness is not Level2 evidence",
        );
    }
    if !has_limitation(
        &report.limitations,
        &["local replay", "not official benchmark evidence"],
    ) {
        push_issue(
            &mut issues,
            PackReadinessValidationIssueKind::MissingLimitation,
            "limitations",
            "limitations must state that local replay is not official benchmark evidence",
        );
    }
    if !has_limitation(
        &report.limitations,
        &["replay command metadata", "not execution evidence"],
    ) {
        push_issue(
            &mut issues,
            PackReadinessValidationIssueKind::MissingLimitation,
            "limitations",
            "limitations must state that replay command metadata is not execution evidence",
        );
    }

    PackReadinessValidation {
        valid: issues.is_empty(),
        issues,
        claim_boundary: ClaimBoundary::Level0DesignNote,
    }
}

/// Serialize a pack-readiness report as deterministic pretty JSON.
pub fn serialize_pack_readiness_report_json(report: &PackReadinessReport) -> Result<String> {
    serde_json::to_string_pretty(report).map_err(|error| {
        crate::error::ZkBenchError::serialization(
            "serialize_pack_readiness_report_json",
            error.to_string(),
        )
    })
}

/// Deserialize a pack-readiness report from JSON.
pub fn deserialize_pack_readiness_report_json(json: &str) -> Result<PackReadinessReport> {
    serde_json::from_str(json).map_err(|error| {
        crate::error::ZkBenchError::serialization(
            "deserialize_pack_readiness_report_json",
            error.to_string(),
        )
    })
}

fn required_check_kinds() -> [PackReadinessCheckKind; 5] {
    [
        PackReadinessCheckKind::RelativePathCoverage,
        PackReadinessCheckKind::Sha256DigestCoverage,
        PackReadinessCheckKind::InertReplayCommandMetadata,
        PackReadinessCheckKind::WeakestClaimBoundaryCap,
        PackReadinessCheckKind::NoLevel2Evidence,
    ]
}

fn validate_identity(
    issues: &mut Vec<PackReadinessValidationIssue>,
    path: impl Into<String>,
    value: &str,
) {
    if value.trim().is_empty() {
        push_issue(
            issues,
            PackReadinessValidationIssueKind::EmptyIdentity,
            path,
            "identity field must not be empty",
        );
    }
}

fn validate_digest(
    issues: &mut Vec<PackReadinessValidationIssue>,
    path: impl Into<String>,
    digest: &ArtifactDigest,
) {
    let path = path.into();
    if digest.algorithm != ArtifactDigestAlgorithm::Sha256 {
        push_issue(
            issues,
            PackReadinessValidationIssueKind::InvalidDigest,
            &path,
            "digest algorithm must be sha256",
        );
    }
    if digest.hex_digest.len() != 64 || !digest.hex_digest.chars().all(|ch| ch.is_ascii_hexdigit())
    {
        push_issue(
            issues,
            PackReadinessValidationIssueKind::InvalidDigest,
            &path,
            "digest must be 64 hex characters",
        );
    }
    if digest.byte_len == 0 {
        push_issue(
            issues,
            PackReadinessValidationIssueKind::InvalidDigest,
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

fn has_limitation(limitations: &[String], required_terms: &[&str]) -> bool {
    limitations.iter().any(|limitation| {
        let lower = limitation.to_ascii_lowercase();
        required_terms.iter().all(|term| lower.contains(term))
    })
}

fn push_issue(
    issues: &mut Vec<PackReadinessValidationIssue>,
    kind: PackReadinessValidationIssueKind,
    path: impl Into<String>,
    message: impl Into<String>,
) {
    issues.push(PackReadinessValidationIssue {
        kind,
        path: path.into(),
        message: message.into(),
    });
}
