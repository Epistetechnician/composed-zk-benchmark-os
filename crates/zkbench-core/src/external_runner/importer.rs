//! Synthetic result candidate importer and validator.
//!
//! The importer accepts explicit JSON candidates and caller-provided local
//! artifact bytes. It never executes external tools, never scans repositories,
//! and never appends accepted evidence.

use std::fs;
use std::path::Path;

use serde::{Deserialize, Serialize};

use crate::error::{Result, ZkBenchError};
use crate::evidence::{
    compute_artifact_digest_bytes, ArtifactDigest, ArtifactDigestAlgorithm, ArtifactKind,
    ArtifactRole, ClaimBoundary,
};

use super::artifact_capture::{
    build_default_artifact_capture_contract, validate_artifact_capture_contract,
    ArtifactCaptureContract,
};
use super::import_bundle::SyntheticResultImportBundle;
use super::normalization::normalize_synthetic_result_candidate;
use super::provenance::{
    build_default_provenance_contract, validate_external_run_provenance_draft,
    validate_provenance_contract, ProvenanceContract,
};
use super::quarantine::QuarantineManifest;
use super::result_import::{
    build_default_external_result_import_schema, validate_external_result_candidate_with_schema,
    ExternalMetricCandidate, ExternalMetricUnit, ExternalResultCandidate,
    ExternalResultImportSchema, ExternalResultValidationIssue,
};
use super::synthetic::{quarantine_synthetic_result_candidate, PHASE_I_SYNTHETIC_CLAIM_BOUNDARY};
use super::validation::{
    contains_forbidden_claim_text, contains_formal_claim_text, contains_official_claim_text,
    contains_rejected_path, contains_soundness_claim_text, ExternalValidationIssueSeverity,
};

/// Source kind for a synthetic candidate.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
pub enum ResultCandidateSourceKind {
    /// Source was an in-memory test fixture or caller buffer.
    InMemory,
    /// Source was a local fixture file.
    SyntheticFixture,
    /// Source was a caller-provided relative local file.
    RelativeFile,
}

/// Source metadata for a synthetic result candidate.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ResultCandidateSource {
    /// Source id.
    pub id: String,
    /// Source kind.
    pub kind: ResultCandidateSourceKind,
    /// Optional relative URI.
    #[serde(default)]
    pub relative_uri: Option<String>,
    /// Claim boundary for this source metadata.
    pub claim_boundary: ClaimBoundary,
    /// Notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

impl Default for ResultCandidateSource {
    fn default() -> Self {
        Self {
            id: "synthetic_candidate_source_in_memory".to_string(),
            kind: ResultCandidateSourceKind::InMemory,
            relative_uri: None,
            claim_boundary: ClaimBoundary::Level0DesignNote,
            notes: vec!["Synthetic result candidates are not benchmark results.".to_string()],
        }
    }
}

/// Local lookup entry for an artifact reference.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ResultCandidateArtifactLookup {
    /// Relative artifact reference.
    pub artifact_ref: String,
    /// Expected digest for the artifact material.
    pub expected_digest: ArtifactDigest,
    /// Optional local bytes used to recompute the digest.
    #[serde(default)]
    pub bytes: Option<Vec<u8>>,
    /// Source kind for this lookup.
    pub source_kind: ResultCandidateSourceKind,
    /// Notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

/// Deterministic artifact resolver for synthetic candidate imports.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize, Default)]
pub struct ResultCandidateArtifactResolver {
    /// Lookup table in deterministic insertion order.
    #[serde(default)]
    pub lookups: Vec<ResultCandidateArtifactLookup>,
}

impl ResultCandidateArtifactResolver {
    /// Build an empty resolver.
    pub fn new() -> Self {
        Self {
            lookups: Vec::new(),
        }
    }

    /// Build a resolver from explicit lookups.
    pub fn with_lookups(lookups: Vec<ResultCandidateArtifactLookup>) -> Self {
        Self { lookups }
    }

    /// Build a resolver from in-memory bytes.
    pub fn from_in_memory_bytes(entries: Vec<(String, Vec<u8>)>) -> Self {
        let lookups = entries
            .into_iter()
            .map(|(artifact_ref, bytes)| ResultCandidateArtifactLookup {
                expected_digest: compute_artifact_digest_bytes(
                    &bytes,
                    Some(ArtifactKind::Other),
                    Some(ArtifactRole::Output),
                ),
                artifact_ref,
                bytes: Some(bytes),
                source_kind: ResultCandidateSourceKind::InMemory,
                notes: vec!["synthetic in-memory artifact bytes".to_string()],
            })
            .collect();
        Self { lookups }
    }

    /// Build a resolver by reading a declared list of relative files under a root.
    pub fn from_relative_files(root: &Path, refs: &[String]) -> Result<Self> {
        let mut lookups = Vec::new();
        for artifact_ref in refs {
            if contains_rejected_path(artifact_ref) {
                return Err(ZkBenchError::synthetic_import(
                    "artifact_resolver.from_relative_files.artifact_ref",
                    "artifact reference is absolute or contains traversal",
                ));
            }
            let path = root.join(artifact_ref);
            let bytes = fs::read(&path).map_err(|error| {
                ZkBenchError::synthetic_import(path.display().to_string(), error.to_string())
            })?;
            lookups.push(ResultCandidateArtifactLookup {
                expected_digest: compute_artifact_digest_bytes(
                    &bytes,
                    Some(ArtifactKind::Other),
                    Some(ArtifactRole::Output),
                ),
                artifact_ref: artifact_ref.clone(),
                bytes: Some(bytes),
                source_kind: ResultCandidateSourceKind::RelativeFile,
                notes: vec![
                    "synthetic local file artifact bytes; no external execution implied"
                        .to_string(),
                ],
            });
        }
        Ok(Self { lookups })
    }

    /// Add one lookup.
    pub fn push_lookup(&mut self, lookup: ResultCandidateArtifactLookup) {
        self.lookups.push(lookup);
    }

    /// Find a lookup by relative artifact reference.
    pub fn lookup(&self, artifact_ref: &str) -> Option<&ResultCandidateArtifactLookup> {
        self.lookups
            .iter()
            .find(|lookup| lookup.artifact_ref == artifact_ref)
    }
}

/// Synthetic import configuration.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct SyntheticResultImportConfig {
    /// External result import schema.
    pub result_import_schema: ExternalResultImportSchema,
    /// Provenance contract.
    pub provenance_contract: ProvenanceContract,
    /// Artifact capture contract.
    pub artifact_capture_contract: ArtifactCaptureContract,
    /// Claim boundary for synthetic import artifacts.
    pub claim_boundary: ClaimBoundary,
}

impl Default for SyntheticResultImportConfig {
    fn default() -> Self {
        Self {
            result_import_schema: build_default_external_result_import_schema(),
            provenance_contract: build_default_provenance_contract(),
            artifact_capture_contract: build_default_artifact_capture_contract(),
            claim_boundary: PHASE_I_SYNTHETIC_CLAIM_BOUNDARY,
        }
    }
}

/// Import validation issue kind.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
pub enum SyntheticImportValidationIssueKind {
    /// Base result schema validation failed.
    SchemaValidationFailed,
    /// Provenance contract or draft validation failed.
    ProvenanceValidationFailed,
    /// Metric validation failed.
    MetricValidationFailed,
    /// Candidate artifact digest is missing.
    ArtifactDigestMissing,
    /// Candidate artifact digest mismatched local material.
    ArtifactDigestMismatch,
    /// Candidate artifact digest algorithm is unsupported.
    ArtifactDigestUnsupported,
    /// Artifact lookup was missing from the resolver.
    ArtifactLookupMissing,
    /// Claim boundary exceeded Phase I limits.
    ClaimBoundaryTooHigh,
    /// Official benchmark claim was detected.
    OfficialClaimDetected,
    /// Formal claim was detected.
    FormalClaimDetected,
    /// Soundness claim was detected.
    SoundnessClaimDetected,
    /// Rejected absolute or traversal path was detected.
    PathRejected,
}

/// Synthetic import validation issue.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct SyntheticImportValidationIssue {
    /// Issue path.
    pub path: String,
    /// Issue message.
    pub message: String,
    /// Issue severity.
    pub severity: ExternalValidationIssueSeverity,
    /// Issue kind.
    pub kind: SyntheticImportValidationIssueKind,
}

impl SyntheticImportValidationIssue {
    /// Build an error issue.
    pub fn error(
        kind: SyntheticImportValidationIssueKind,
        path: impl Into<String>,
        message: impl Into<String>,
    ) -> Self {
        Self {
            path: path.into(),
            message: message.into(),
            severity: ExternalValidationIssueSeverity::Error,
            kind,
        }
    }

    /// Convert to the older external result issue shape used by quarantine manifests.
    pub fn as_external_result_issue(&self) -> ExternalResultValidationIssue {
        ExternalResultValidationIssue {
            path: self.path.clone(),
            message: self.message.clone(),
            severity: self.severity,
        }
    }
}

/// Artifact digest validation summary.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ArtifactDigestValidation {
    /// True when all artifact refs had matching supported digests.
    pub valid: bool,
    /// Number of refs checked.
    pub checked_artifact_ref_count: usize,
    /// Number of matching refs.
    pub matched_artifact_ref_count: usize,
    /// Issues.
    pub issues: Vec<SyntheticImportValidationIssue>,
}

/// Provenance validation summary.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ProvenanceContractValidation {
    /// True when provenance contract and draft checks pass.
    pub valid: bool,
    /// Issues.
    pub issues: Vec<SyntheticImportValidationIssue>,
}

/// Metric validation summary.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct MetricCandidateValidation {
    /// True when all metric candidates are locally well-formed.
    pub valid: bool,
    /// Number of metrics checked.
    pub checked_metric_count: usize,
    /// Issues.
    pub issues: Vec<SyntheticImportValidationIssue>,
}

/// Claim-boundary validation summary.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ClaimBoundaryValidation {
    /// True when requested and produced claim boundaries stay in Phase I limits.
    pub valid: bool,
    /// Requested candidate claim boundary.
    pub requested: ClaimBoundary,
    /// Produced import artifact claim boundary.
    pub produced: ClaimBoundary,
    /// Issues.
    pub issues: Vec<SyntheticImportValidationIssue>,
}

/// Official claim detection summary.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct OfficialClaimDetection {
    /// True when official benchmark claim text or flags were found.
    pub detected: bool,
    /// Issues.
    pub issues: Vec<SyntheticImportValidationIssue>,
}

/// Formal claim detection summary.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct FormalClaimDetection {
    /// True when formal evidence claim text or flags were found.
    pub detected: bool,
    /// Issues.
    pub issues: Vec<SyntheticImportValidationIssue>,
}

/// Soundness claim detection summary.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct SoundnessClaimDetection {
    /// True when proof-system soundness claim text or flags were found.
    pub detected: bool,
    /// Issues.
    pub issues: Vec<SyntheticImportValidationIssue>,
}

/// Full synthetic import validation report.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct SyntheticImportValidation {
    /// True when no errors were found.
    pub valid: bool,
    /// Source candidate id.
    pub result_candidate_id: String,
    /// Claim boundary for validation report artifact.
    pub claim_boundary: ClaimBoundary,
    /// Base external result validation issues.
    pub base_result_issues: Vec<ExternalResultValidationIssue>,
    /// Artifact digest validation.
    pub artifact_digest_validation: ArtifactDigestValidation,
    /// Provenance validation.
    pub provenance_contract_validation: ProvenanceContractValidation,
    /// Metric validation.
    pub metric_candidate_validation: MetricCandidateValidation,
    /// Claim-boundary validation.
    pub claim_boundary_validation: ClaimBoundaryValidation,
    /// Official claim detection.
    pub official_claim_detection: OfficialClaimDetection,
    /// Formal claim detection.
    pub formal_claim_detection: FormalClaimDetection,
    /// Soundness claim detection.
    pub soundness_claim_detection: SoundnessClaimDetection,
    /// Flattened issues.
    pub issues: Vec<SyntheticImportValidationIssue>,
    /// Notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

impl SyntheticImportValidation {
    /// Return true when validation rejected the candidate.
    pub fn is_rejected(&self) -> bool {
        !self.valid
    }
}

/// Inert synthetic result importer.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct SyntheticResultImporter {
    /// Import config.
    pub config: SyntheticResultImportConfig,
    /// Local artifact resolver.
    pub resolver: ResultCandidateArtifactResolver,
    /// Candidate source metadata.
    pub source: ResultCandidateSource,
}

impl SyntheticResultImporter {
    /// Build an importer from a resolver and default config.
    pub fn new(resolver: ResultCandidateArtifactResolver) -> Self {
        Self {
            config: SyntheticResultImportConfig::default(),
            resolver,
            source: ResultCandidateSource::default(),
        }
    }

    /// Build an importer from explicit config, resolver, and source metadata.
    pub fn with_config(
        config: SyntheticResultImportConfig,
        resolver: ResultCandidateArtifactResolver,
        source: ResultCandidateSource,
    ) -> Self {
        Self {
            config,
            resolver,
            source,
        }
    }

    /// Import one candidate from JSON text.
    pub fn import_candidate_json(&self, json: &str) -> Result<SyntheticResultImportBundle> {
        let candidate = serde_json::from_str::<ExternalResultCandidate>(json).map_err(|error| {
            ZkBenchError::deserialization("import_candidate_json", error.to_string())
        })?;
        self.import_candidate(candidate)
    }

    /// Import one parsed candidate.
    pub fn import_candidate(
        &self,
        candidate: ExternalResultCandidate,
    ) -> Result<SyntheticResultImportBundle> {
        let validation = validate_synthetic_result_candidate_with_config(
            &candidate,
            &self.config,
            &self.resolver,
        );
        if validation.valid {
            let normalized_draft =
                normalize_synthetic_result_candidate(&candidate, &validation, &self.resolver)?;
            Ok(SyntheticResultImportBundle::new(
                self.source.clone(),
                candidate,
                validation,
                Some(normalized_draft),
                None,
            ))
        } else {
            let quarantine_manifest =
                quarantine_synthetic_result_candidate(&candidate, &validation);
            Ok(SyntheticResultImportBundle::new(
                self.source.clone(),
                candidate,
                validation,
                None,
                Some(quarantine_manifest),
            ))
        }
    }
}

/// Import one synthetic result candidate from JSON using a resolver and defaults.
pub fn import_synthetic_result_candidate_json(
    json: &str,
    resolver: &ResultCandidateArtifactResolver,
) -> Result<SyntheticResultImportBundle> {
    SyntheticResultImporter::new(resolver.clone()).import_candidate_json(json)
}

/// Validate a synthetic result candidate using default Phase I contracts.
pub fn validate_synthetic_result_candidate(
    candidate: &ExternalResultCandidate,
    resolver: &ResultCandidateArtifactResolver,
) -> SyntheticImportValidation {
    let config = SyntheticResultImportConfig::default();
    validate_synthetic_result_candidate_with_config(candidate, &config, resolver)
}

/// Validate a synthetic result candidate using explicit Phase I contracts.
pub fn validate_synthetic_result_candidate_with_config(
    candidate: &ExternalResultCandidate,
    config: &SyntheticResultImportConfig,
    resolver: &ResultCandidateArtifactResolver,
) -> SyntheticImportValidation {
    let base_validation =
        validate_external_result_candidate_with_schema(candidate, &config.result_import_schema);
    let mut issues = base_validation
        .issues
        .iter()
        .map(|issue| {
            SyntheticImportValidationIssue::error(
                base_issue_kind(issue),
                issue.path.clone(),
                issue.message.clone(),
            )
        })
        .collect::<Vec<_>>();

    let artifact_digest_validation = validate_artifact_digests(candidate, resolver);
    issues.extend(artifact_digest_validation.issues.clone());

    let provenance_contract_validation =
        validate_candidate_provenance(candidate, &config.provenance_contract);
    issues.extend(provenance_contract_validation.issues.clone());

    let metric_candidate_validation = validate_metric_candidates(candidate);
    issues.extend(metric_candidate_validation.issues.clone());

    let claim_boundary_validation = validate_candidate_claim_boundary(candidate, config);
    issues.extend(claim_boundary_validation.issues.clone());

    let official_claim_detection = detect_official_claims(candidate);
    issues.extend(official_claim_detection.issues.clone());

    let formal_claim_detection = detect_formal_claims(candidate);
    issues.extend(formal_claim_detection.issues.clone());

    let soundness_claim_detection = detect_soundness_claims(candidate);
    issues.extend(soundness_claim_detection.issues.clone());

    let capture_validation = validate_artifact_capture_contract(&config.artifact_capture_contract);
    for issue in capture_validation.errors {
        issues.push(SyntheticImportValidationIssue::error(
            SyntheticImportValidationIssueKind::SchemaValidationFailed,
            issue.path,
            issue.message,
        ));
    }

    let valid = issues
        .iter()
        .all(|issue| issue.severity != ExternalValidationIssueSeverity::Error);

    SyntheticImportValidation {
        valid,
        result_candidate_id: candidate.result_candidate_id.clone(),
        claim_boundary: ClaimBoundary::Level0DesignNote,
        base_result_issues: base_validation.issues,
        artifact_digest_validation,
        provenance_contract_validation,
        metric_candidate_validation,
        claim_boundary_validation,
        official_claim_detection,
        formal_claim_detection,
        soundness_claim_detection,
        issues,
        notes: vec![
            "Synthetic import validation is local metadata validation only.".to_string(),
            "Synthetic result candidates are not benchmark results.".to_string(),
        ],
    }
}

fn validate_artifact_digests(
    candidate: &ExternalResultCandidate,
    resolver: &ResultCandidateArtifactResolver,
) -> ArtifactDigestValidation {
    let mut issues = Vec::new();
    let mut matched_artifact_ref_count = 0usize;

    let artifact_refs = candidate_artifact_refs(candidate);
    for (path, artifact_ref) in &artifact_refs {
        if contains_rejected_path(artifact_ref) {
            issues.push(SyntheticImportValidationIssue::error(
                SyntheticImportValidationIssueKind::PathRejected,
                path,
                "artifact reference is absolute or contains traversal",
            ));
            continue;
        }
        let Some(lookup) = resolver.lookup(artifact_ref) else {
            issues.push(SyntheticImportValidationIssue::error(
                SyntheticImportValidationIssueKind::ArtifactLookupMissing,
                path,
                "artifact reference is missing from the synthetic resolver",
            ));
            continue;
        };
        if lookup.expected_digest.algorithm != ArtifactDigestAlgorithm::Sha256 {
            issues.push(SyntheticImportValidationIssue::error(
                SyntheticImportValidationIssueKind::ArtifactDigestUnsupported,
                path,
                "resolver digest algorithm is unsupported",
            ));
            continue;
        }
        if let Some(bytes) = &lookup.bytes {
            let recomputed = compute_artifact_digest_bytes(
                bytes,
                lookup.expected_digest.kind,
                lookup.expected_digest.role,
            );
            if !digest_material_matches(&recomputed, &lookup.expected_digest) {
                issues.push(SyntheticImportValidationIssue::error(
                    SyntheticImportValidationIssueKind::ArtifactDigestMismatch,
                    path,
                    "resolver digest does not match resolver bytes",
                ));
                continue;
            }
        }

        if candidate
            .artifact_digests
            .iter()
            .any(|digest| digest.algorithm != ArtifactDigestAlgorithm::Sha256)
        {
            issues.push(SyntheticImportValidationIssue::error(
                SyntheticImportValidationIssueKind::ArtifactDigestUnsupported,
                path,
                "candidate contains an unsupported artifact digest algorithm",
            ));
            continue;
        }
        let matching_candidate_digest = candidate
            .artifact_digests
            .iter()
            .find(|digest| digest_material_matches(digest, &lookup.expected_digest));
        match matching_candidate_digest {
            Some(digest) if digest.algorithm == ArtifactDigestAlgorithm::Sha256 => {
                matched_artifact_ref_count += 1;
            }
            Some(_) => issues.push(SyntheticImportValidationIssue::error(
                SyntheticImportValidationIssueKind::ArtifactDigestUnsupported,
                path,
                "candidate digest algorithm is unsupported",
            )),
            None if candidate.artifact_digests.is_empty() => {
                issues.push(SyntheticImportValidationIssue::error(
                    SyntheticImportValidationIssueKind::ArtifactDigestMissing,
                    path,
                    "candidate has no artifact digest for referenced artifact",
                ))
            }
            None => issues.push(SyntheticImportValidationIssue::error(
                SyntheticImportValidationIssueKind::ArtifactDigestMismatch,
                path,
                "candidate artifact digest does not match local artifact material",
            )),
        }
    }

    ArtifactDigestValidation {
        valid: issues.is_empty(),
        checked_artifact_ref_count: artifact_refs.len(),
        matched_artifact_ref_count,
        issues,
    }
}

fn validate_candidate_provenance(
    candidate: &ExternalResultCandidate,
    contract: &ProvenanceContract,
) -> ProvenanceContractValidation {
    let mut issues = Vec::new();
    let contract_validation = validate_provenance_contract(contract);
    for issue in contract_validation.issues {
        issues.push(SyntheticImportValidationIssue::error(
            SyntheticImportValidationIssueKind::ProvenanceValidationFailed,
            issue.path,
            issue.message,
        ));
    }
    match &candidate.provenance_draft {
        Some(draft) => {
            let draft_validation = validate_external_run_provenance_draft(draft);
            for issue in draft_validation.issues {
                issues.push(SyntheticImportValidationIssue::error(
                    SyntheticImportValidationIssueKind::ProvenanceValidationFailed,
                    issue.path,
                    issue.message,
                ));
            }
            for (index, note) in draft.notes.iter().enumerate() {
                if contains_forbidden_claim_text(note) {
                    issues.push(SyntheticImportValidationIssue::error(
                        SyntheticImportValidationIssueKind::ProvenanceValidationFailed,
                        format!("candidate.provenance_draft.notes[{index}]"),
                        "provenance notes contain a forbidden claim",
                    ));
                }
            }
        }
        None => issues.push(SyntheticImportValidationIssue::error(
            SyntheticImportValidationIssueKind::ProvenanceValidationFailed,
            "candidate.provenance_draft",
            "provenance draft is required",
        )),
    }

    ProvenanceContractValidation {
        valid: issues.is_empty(),
        issues,
    }
}

fn validate_metric_candidates(candidate: &ExternalResultCandidate) -> MetricCandidateValidation {
    let mut issues = Vec::new();
    for (index, metric) in candidate.normalized_metrics.iter().enumerate() {
        validate_one_metric(metric, index, &mut issues);
    }
    MetricCandidateValidation {
        valid: issues.is_empty(),
        checked_metric_count: candidate.normalized_metrics.len(),
        issues,
    }
}

fn validate_one_metric(
    metric: &ExternalMetricCandidate,
    index: usize,
    issues: &mut Vec<SyntheticImportValidationIssue>,
) {
    if metric.unit == ExternalMetricUnit::Unknown {
        issues.push(SyntheticImportValidationIssue::error(
            SyntheticImportValidationIssueKind::MetricValidationFailed,
            format!("candidate.normalized_metrics[{index}].unit"),
            "metric unit is unknown",
        ));
    }
    let missing_source_ref = match &metric.source_artifact_ref {
        Some(source_ref) => source_ref.trim().is_empty(),
        None => true,
    };
    if metric.value.is_some() && missing_source_ref {
        issues.push(SyntheticImportValidationIssue::error(
            SyntheticImportValidationIssueKind::MetricValidationFailed,
            format!("candidate.normalized_metrics[{index}].source_artifact_ref"),
            "metric values require source artifact refs",
        ));
    }
    if let Some(source_ref) = &metric.source_artifact_ref {
        if contains_rejected_path(source_ref) {
            issues.push(SyntheticImportValidationIssue::error(
                SyntheticImportValidationIssueKind::PathRejected,
                format!("candidate.normalized_metrics[{index}].source_artifact_ref"),
                "metric source artifact ref is absolute or contains traversal",
            ));
        }
    }
    if let Some(value) = &metric.value {
        validate_metric_value(value, metric.unit, index, issues);
    }
    for (note_index, note) in metric.notes.iter().enumerate() {
        if contains_forbidden_claim_text(note) {
            issues.push(SyntheticImportValidationIssue::error(
                SyntheticImportValidationIssueKind::MetricValidationFailed,
                format!("candidate.normalized_metrics[{index}].notes[{note_index}]"),
                "metric notes contain a forbidden claim",
            ));
        }
    }
}

fn validate_metric_value(
    value: &str,
    unit: ExternalMetricUnit,
    index: usize,
    issues: &mut Vec<SyntheticImportValidationIssue>,
) {
    if matches!(
        unit,
        ExternalMetricUnit::Milliseconds
            | ExternalMetricUnit::Seconds
            | ExternalMetricUnit::Bytes
            | ExternalMetricUnit::Count
    ) {
        match value.trim().parse::<i128>() {
            Ok(parsed) if parsed >= 0 => {}
            Ok(_) => issues.push(SyntheticImportValidationIssue::error(
                SyntheticImportValidationIssueKind::MetricValidationFailed,
                format!("candidate.normalized_metrics[{index}].value"),
                "numeric metric values must be non-negative",
            )),
            Err(_) => issues.push(SyntheticImportValidationIssue::error(
                SyntheticImportValidationIssueKind::MetricValidationFailed,
                format!("candidate.normalized_metrics[{index}].value"),
                "numeric metric values must parse as integers",
            )),
        }
    }
}

fn validate_candidate_claim_boundary(
    candidate: &ExternalResultCandidate,
    config: &SyntheticResultImportConfig,
) -> ClaimBoundaryValidation {
    let mut issues = Vec::new();
    if config.claim_boundary != ClaimBoundary::Level0DesignNote {
        issues.push(SyntheticImportValidationIssue::error(
            SyntheticImportValidationIssueKind::ClaimBoundaryTooHigh,
            "config.claim_boundary",
            "Phase I synthetic import config must remain Level0DesignNote",
        ));
    }
    if candidate.claim_boundary_requested != ClaimBoundary::Level0DesignNote {
        issues.push(SyntheticImportValidationIssue::error(
            SyntheticImportValidationIssueKind::ClaimBoundaryTooHigh,
            "candidate.claim_boundary_requested",
            "synthetic result imports must request Level0DesignNote only in Phase I",
        ));
    }
    ClaimBoundaryValidation {
        valid: issues.is_empty(),
        requested: candidate.claim_boundary_requested,
        produced: config.claim_boundary,
        issues,
    }
}

fn detect_official_claims(candidate: &ExternalResultCandidate) -> OfficialClaimDetection {
    let mut issues = Vec::new();
    if candidate.claims_official_benchmark_evidence {
        issues.push(SyntheticImportValidationIssue::error(
            SyntheticImportValidationIssueKind::OfficialClaimDetected,
            "candidate.claims_official_benchmark_evidence",
            "official benchmark evidence claims are rejected",
        ));
    }
    scan_candidate_notes(
        candidate,
        contains_official_claim_text,
        SyntheticImportValidationIssueKind::OfficialClaimDetected,
        "official benchmark claim text is rejected",
        &mut issues,
    );
    OfficialClaimDetection {
        detected: !issues.is_empty(),
        issues,
    }
}

fn detect_formal_claims(candidate: &ExternalResultCandidate) -> FormalClaimDetection {
    let mut issues = Vec::new();
    if candidate.claims_formal_evidence {
        issues.push(SyntheticImportValidationIssue::error(
            SyntheticImportValidationIssueKind::FormalClaimDetected,
            "candidate.claims_formal_evidence",
            "formal evidence claims are rejected",
        ));
    }
    scan_candidate_notes(
        candidate,
        contains_formal_claim_text,
        SyntheticImportValidationIssueKind::FormalClaimDetected,
        "formal evidence claim text is rejected",
        &mut issues,
    );
    FormalClaimDetection {
        detected: !issues.is_empty(),
        issues,
    }
}

fn detect_soundness_claims(candidate: &ExternalResultCandidate) -> SoundnessClaimDetection {
    let mut issues = Vec::new();
    if candidate.claims_proof_system_soundness {
        issues.push(SyntheticImportValidationIssue::error(
            SyntheticImportValidationIssueKind::SoundnessClaimDetected,
            "candidate.claims_proof_system_soundness",
            "proof-system soundness claims are rejected",
        ));
    }
    scan_candidate_notes(
        candidate,
        contains_soundness_claim_text,
        SyntheticImportValidationIssueKind::SoundnessClaimDetected,
        "proof-system soundness claim text is rejected",
        &mut issues,
    );
    SoundnessClaimDetection {
        detected: !issues.is_empty(),
        issues,
    }
}

fn scan_candidate_notes(
    candidate: &ExternalResultCandidate,
    detector: fn(&str) -> bool,
    kind: SyntheticImportValidationIssueKind,
    message: &str,
    issues: &mut Vec<SyntheticImportValidationIssue>,
) {
    for (index, note) in candidate.notes.iter().enumerate() {
        if detector(note) {
            issues.push(SyntheticImportValidationIssue::error(
                kind,
                format!("candidate.notes[{index}]"),
                message,
            ));
        }
    }
    for (metric_index, metric) in candidate.normalized_metrics.iter().enumerate() {
        for (note_index, note) in metric.notes.iter().enumerate() {
            if detector(note) {
                issues.push(SyntheticImportValidationIssue::error(
                    kind,
                    format!("candidate.normalized_metrics[{metric_index}].notes[{note_index}]"),
                    message,
                ));
            }
        }
    }
}

fn base_issue_kind(issue: &ExternalResultValidationIssue) -> SyntheticImportValidationIssueKind {
    if issue.path.contains("provenance") {
        SyntheticImportValidationIssueKind::ProvenanceValidationFailed
    } else if issue.path.contains("normalized_metrics") {
        SyntheticImportValidationIssueKind::MetricValidationFailed
    } else if issue.path.contains("claim_boundary") {
        SyntheticImportValidationIssueKind::ClaimBoundaryTooHigh
    } else if issue.path.contains("official") {
        SyntheticImportValidationIssueKind::OfficialClaimDetected
    } else if issue.path.contains("formal") {
        SyntheticImportValidationIssueKind::FormalClaimDetected
    } else if issue.path.contains("soundness") {
        SyntheticImportValidationIssueKind::SoundnessClaimDetected
    } else if issue.message.contains("absolute") {
        SyntheticImportValidationIssueKind::PathRejected
    } else {
        SyntheticImportValidationIssueKind::SchemaValidationFailed
    }
}

fn candidate_artifact_refs(candidate: &ExternalResultCandidate) -> Vec<(String, String)> {
    let mut refs = candidate
        .raw_output_artifact_refs
        .iter()
        .enumerate()
        .map(|(index, artifact_ref)| {
            (
                format!("candidate.raw_output_artifact_refs[{index}]"),
                artifact_ref.clone(),
            )
        })
        .collect::<Vec<_>>();
    refs.extend(
        candidate
            .normalized_metrics
            .iter()
            .enumerate()
            .filter_map(|(index, metric)| {
                metric.source_artifact_ref.as_ref().map(|artifact_ref| {
                    (
                        format!("candidate.normalized_metrics[{index}].source_artifact_ref"),
                        artifact_ref.clone(),
                    )
                })
            }),
    );
    refs
}

fn digest_material_matches(left: &ArtifactDigest, right: &ArtifactDigest) -> bool {
    left.algorithm == right.algorithm
        && left.hex_digest.eq_ignore_ascii_case(&right.hex_digest)
        && left.byte_len == right.byte_len
        && left.hex_digest.len() == 64
        && left
            .hex_digest
            .chars()
            .all(|character| character.is_ascii_hexdigit())
}

#[allow(dead_code)]
fn _quarantine_manifest_type_is_used(_: QuarantineManifest) {}
