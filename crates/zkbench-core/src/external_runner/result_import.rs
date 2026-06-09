//! External result import schema and candidate validation.
//!
//! Phase H validates candidate metadata only. It does not accept benchmark
//! evidence, performance values, or proof-system claims.

use serde::{Deserialize, Serialize};

use crate::evidence::{ArtifactDigest, ClaimBoundary};

use super::provenance::{
    required_provenance_fields, validate_external_run_provenance_draft, ExternalRunProvenanceDraft,
    RequiredProvenanceField,
};
use super::validation::{
    contains_forbidden_claim_text, contains_rejected_path, phase_h_design_artifact_claim_allowed,
    ExternalValidationIssueSeverity,
};

/// External result import schema id.
pub type ExternalResultImportSchemaId = String;

/// External result candidate id.
pub type ExternalResultCandidateId = String;

/// External result candidate status.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum ExternalResultStatus {
    /// Candidate is quarantined.
    Quarantined,
    /// Candidate is pending review.
    PendingReview,
    /// Candidate was rejected.
    Rejected,
    /// Accepted only as a local import candidate after future validation.
    AcceptedAsLocalImportOnly,
    /// Future eligibility marker for Level2 review, not actual evidence.
    FutureEligibleForLevel2Review,
}

impl ExternalResultStatus {
    /// Return true when the status is safe for a new Phase H candidate.
    pub fn is_phase_h_initial_status(self) -> bool {
        matches!(
            self,
            Self::Quarantined | Self::PendingReview | Self::Rejected
        )
    }
}

/// External metric unit.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
pub enum ExternalMetricUnit {
    /// Milliseconds.
    Milliseconds,
    /// Seconds.
    Seconds,
    /// Bytes.
    Bytes,
    /// Count.
    Count,
    /// Boolean.
    Boolean,
    /// Text.
    Text,
    /// Unknown or unsupported unit.
    Unknown,
}

/// External metric candidate.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ExternalMetricCandidate {
    /// Metric kind label.
    pub metric_kind: String,
    /// Metric unit.
    pub unit: ExternalMetricUnit,
    /// Optional metric value. Phase H generated artifacts should leave this empty.
    #[serde(default)]
    pub value: Option<String>,
    /// Relative source artifact reference for the metric value.
    #[serde(default)]
    pub source_artifact_ref: Option<String>,
    /// Notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

/// External result import policy.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ExternalResultImportPolicy {
    /// Require source pack id.
    pub require_source_benchmark_pack_id: bool,
    /// Require dry-run plan id.
    pub require_dry_run_plan_id: bool,
    /// Require provenance.
    pub require_provenance: bool,
    /// Reject absolute paths.
    pub reject_absolute_paths: bool,
    /// Reject Level2+ claim requests.
    pub reject_level2_plus_claim_requests: bool,
    /// Reject official benchmark evidence claims.
    pub reject_official_benchmark_claims: bool,
    /// Reject formal evidence claims.
    pub reject_formal_evidence_claims: bool,
    /// Reject proof-system soundness claims.
    pub reject_proof_system_soundness_claims: bool,
    /// Require metric source refs when values are present.
    pub require_metric_source_artifact_refs: bool,
    /// Notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

impl Default for ExternalResultImportPolicy {
    fn default() -> Self {
        Self {
            require_source_benchmark_pack_id: true,
            require_dry_run_plan_id: true,
            require_provenance: true,
            reject_absolute_paths: true,
            reject_level2_plus_claim_requests: true,
            reject_official_benchmark_claims: true,
            reject_formal_evidence_claims: true,
            reject_proof_system_soundness_claims: true,
            require_metric_source_artifact_refs: true,
            notes: vec![
                "External result candidates are quarantined or pending review until validated."
                    .to_string(),
                "Imported metric candidates do not affect scoring in Phase H.".to_string(),
            ],
        }
    }
}

/// External result import schema.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ExternalResultImportSchema {
    /// Schema id.
    pub id: ExternalResultImportSchemaId,
    /// Logical schema version.
    pub schema_version: String,
    /// Import policy.
    pub import_policy: ExternalResultImportPolicy,
    /// Allowed units.
    pub allowed_units: Vec<ExternalMetricUnit>,
    /// Required provenance fields.
    pub required_provenance_fields: Vec<RequiredProvenanceField>,
    /// Claim boundary for the schema artifact.
    pub claim_boundary: ClaimBoundary,
    /// Notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

/// External result candidate.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ExternalResultCandidate {
    /// Candidate id.
    pub result_candidate_id: ExternalResultCandidateId,
    /// Source benchmark pack id.
    pub source_benchmark_pack_id: String,
    /// Source dry-run plan id.
    pub dry_run_plan_id: String,
    /// Raw output artifact refs.
    #[serde(default)]
    pub raw_output_artifact_refs: Vec<String>,
    /// Normalized metric candidates.
    #[serde(default)]
    pub normalized_metrics: Vec<ExternalMetricCandidate>,
    /// Candidate status.
    pub result_status: ExternalResultStatus,
    /// Provenance draft.
    #[serde(default)]
    pub provenance_draft: Option<ExternalRunProvenanceDraft>,
    /// Artifact digests.
    #[serde(default)]
    pub artifact_digests: Vec<ArtifactDigest>,
    /// Requested claim boundary.
    pub claim_boundary_requested: ClaimBoundary,
    /// True if the candidate claims official benchmark evidence. Rejected in Phase H.
    pub claims_official_benchmark_evidence: bool,
    /// True if the candidate claims formal evidence. Rejected in Phase H.
    pub claims_formal_evidence: bool,
    /// True if the candidate claims proof-system soundness. Rejected in Phase H.
    pub claims_proof_system_soundness: bool,
    /// Notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

/// Result validation issue.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ExternalResultValidationIssue {
    /// Issue path.
    pub path: String,
    /// Issue message.
    pub message: String,
    /// Issue severity.
    pub severity: ExternalValidationIssueSeverity,
}

impl ExternalResultValidationIssue {
    /// Build an error issue.
    pub fn error(path: impl Into<String>, message: impl Into<String>) -> Self {
        Self {
            path: path.into(),
            message: message.into(),
            severity: ExternalValidationIssueSeverity::Error,
        }
    }
}

/// Result validation output.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ExternalResultValidation {
    /// True when there are no validation errors.
    pub valid: bool,
    /// Validation issues.
    pub issues: Vec<ExternalResultValidationIssue>,
}

/// Result quarantine record summary.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ExternalResultQuarantineRecord {
    /// Candidate result id.
    pub result_candidate_id: ExternalResultCandidateId,
    /// Candidate status.
    pub status: ExternalResultStatus,
    /// Validation issues.
    pub validation_issues: Vec<ExternalResultValidationIssue>,
    /// Claim boundary requested by the candidate.
    pub claim_boundary_requested: ClaimBoundary,
    /// Notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

/// Build the default Phase H external result import schema.
pub fn build_default_external_result_import_schema() -> ExternalResultImportSchema {
    ExternalResultImportSchema {
        id: "external_result_import_schema_phase_h".to_string(),
        schema_version: "phase-h-external-result-import-schema-v0".to_string(),
        import_policy: ExternalResultImportPolicy::default(),
        allowed_units: vec![
            ExternalMetricUnit::Milliseconds,
            ExternalMetricUnit::Seconds,
            ExternalMetricUnit::Bytes,
            ExternalMetricUnit::Count,
            ExternalMetricUnit::Boolean,
            ExternalMetricUnit::Text,
        ],
        required_provenance_fields: required_provenance_fields(),
        claim_boundary: ClaimBoundary::Level0DesignNote,
        notes: vec![
            "Result import validation schema only; no external results are accepted in Phase H."
                .to_string(),
            "Manual handoff bundles are not benchmark results.".to_string(),
            "Local replay is not official benchmark evidence.".to_string(),
        ],
    }
}

/// Validate an import schema.
pub fn validate_external_result_import_schema(
    schema: &ExternalResultImportSchema,
) -> ExternalResultValidation {
    let mut issues = Vec::new();
    if schema.id.trim().is_empty() {
        issues.push(ExternalResultValidationIssue::error(
            "schema.id",
            "external result import schema id is empty",
        ));
    }
    if !phase_h_design_artifact_claim_allowed(schema.claim_boundary) {
        issues.push(ExternalResultValidationIssue::error(
            "schema.claim_boundary",
            "external result import schemas must remain Level0DesignNote",
        ));
    }
    if schema.allowed_units.contains(&ExternalMetricUnit::Unknown) {
        issues.push(ExternalResultValidationIssue::error(
            "schema.allowed_units",
            "unknown metric unit must not be allowed",
        ));
    }
    for field in required_provenance_fields() {
        if !schema.required_provenance_fields.contains(&field) {
            issues.push(ExternalResultValidationIssue::error(
                format!("schema.required_provenance_fields.{}", field.as_key()),
                "required provenance field is missing from import schema",
            ));
        }
    }
    ExternalResultValidation {
        valid: issues.is_empty(),
        issues,
    }
}

/// Validate an external result candidate against the default Phase H rules.
pub fn validate_external_result_candidate(
    candidate: &ExternalResultCandidate,
) -> ExternalResultValidation {
    let schema = build_default_external_result_import_schema();
    validate_external_result_candidate_with_schema(candidate, &schema)
}

/// Validate an external result candidate against a provided schema.
pub fn validate_external_result_candidate_with_schema(
    candidate: &ExternalResultCandidate,
    schema: &ExternalResultImportSchema,
) -> ExternalResultValidation {
    let mut issues = Vec::new();
    let policy = &schema.import_policy;

    if candidate.result_candidate_id.trim().is_empty() {
        issues.push(ExternalResultValidationIssue::error(
            "candidate.result_candidate_id",
            "result candidate id is empty",
        ));
    }
    if policy.require_source_benchmark_pack_id
        && candidate.source_benchmark_pack_id.trim().is_empty()
    {
        issues.push(ExternalResultValidationIssue::error(
            "candidate.source_benchmark_pack_id",
            "source benchmark pack id is required",
        ));
    }
    if policy.require_dry_run_plan_id && candidate.dry_run_plan_id.trim().is_empty() {
        issues.push(ExternalResultValidationIssue::error(
            "candidate.dry_run_plan_id",
            "dry-run plan id is required",
        ));
    }
    if policy.require_provenance && candidate.provenance_draft.is_none() {
        issues.push(ExternalResultValidationIssue::error(
            "candidate.provenance_draft",
            "provenance draft is required",
        ));
    }
    if let Some(provenance) = &candidate.provenance_draft {
        let provenance_validation = validate_external_run_provenance_draft(provenance);
        for issue in provenance_validation.issues {
            issues.push(ExternalResultValidationIssue::error(
                issue.path,
                issue.message,
            ));
        }
    }
    if policy.reject_level2_plus_claim_requests
        && candidate.claim_boundary_requested >= ClaimBoundary::Level2ReproducibleBenchmarkArtifact
    {
        issues.push(ExternalResultValidationIssue::error(
            "candidate.claim_boundary_requested",
            "Level2+ claim boundary requests are rejected in Phase H",
        ));
    }
    if !candidate.result_status.is_phase_h_initial_status() {
        issues.push(ExternalResultValidationIssue::error(
            "candidate.result_status",
            "result candidates must start quarantined, pending review, or rejected",
        ));
    }
    if policy.reject_official_benchmark_claims && candidate.claims_official_benchmark_evidence {
        issues.push(ExternalResultValidationIssue::error(
            "candidate.claims_official_benchmark_evidence",
            "official benchmark evidence claims are rejected",
        ));
    }
    if policy.reject_formal_evidence_claims && candidate.claims_formal_evidence {
        issues.push(ExternalResultValidationIssue::error(
            "candidate.claims_formal_evidence",
            "formal evidence claims are rejected",
        ));
    }
    if policy.reject_proof_system_soundness_claims && candidate.claims_proof_system_soundness {
        issues.push(ExternalResultValidationIssue::error(
            "candidate.claims_proof_system_soundness",
            "proof-system soundness claims are rejected",
        ));
    }
    for (index, reference) in candidate.raw_output_artifact_refs.iter().enumerate() {
        if policy.reject_absolute_paths && contains_rejected_path(reference) {
            issues.push(ExternalResultValidationIssue::error(
                format!("candidate.raw_output_artifact_refs[{index}]"),
                "raw output artifact ref is absolute or contains traversal",
            ));
        }
    }
    for (index, metric) in candidate.normalized_metrics.iter().enumerate() {
        validate_metric(metric, index, schema, &mut issues);
    }
    for (index, note) in candidate.notes.iter().enumerate() {
        if contains_forbidden_claim_text(note) {
            issues.push(ExternalResultValidationIssue::error(
                format!("candidate.notes[{index}]"),
                "candidate notes contain a forbidden Phase H claim",
            ));
        }
    }

    ExternalResultValidation {
        valid: issues.is_empty(),
        issues,
    }
}

/// Build a validation-backed quarantine record summary.
pub fn external_result_quarantine_record(
    candidate: &ExternalResultCandidate,
) -> ExternalResultQuarantineRecord {
    let validation = validate_external_result_candidate(candidate);
    ExternalResultQuarantineRecord {
        result_candidate_id: candidate.result_candidate_id.clone(),
        status: ExternalResultStatus::Quarantined,
        validation_issues: validation.issues,
        claim_boundary_requested: candidate.claim_boundary_requested,
        notes: vec![
            "Result candidate remains quarantined or pending review until validated.".to_string(),
        ],
    }
}

fn validate_metric(
    metric: &ExternalMetricCandidate,
    index: usize,
    schema: &ExternalResultImportSchema,
    issues: &mut Vec<ExternalResultValidationIssue>,
) {
    if metric.metric_kind.trim().is_empty() {
        issues.push(ExternalResultValidationIssue::error(
            format!("candidate.normalized_metrics[{index}].metric_kind"),
            "metric kind is empty",
        ));
    }
    if !schema.allowed_units.contains(&metric.unit) || metric.unit == ExternalMetricUnit::Unknown {
        issues.push(ExternalResultValidationIssue::error(
            format!("candidate.normalized_metrics[{index}].unit"),
            "unrecognized metric unit",
        ));
    }
    let source_ref_missing = match &metric.source_artifact_ref {
        Some(value) => value.trim().is_empty(),
        None => true,
    };
    if metric.value.is_some() && source_ref_missing {
        issues.push(ExternalResultValidationIssue::error(
            format!("candidate.normalized_metrics[{index}].source_artifact_ref"),
            "metric values require source artifact refs",
        ));
    }
    if let Some(reference) = &metric.source_artifact_ref {
        if contains_rejected_path(reference) {
            issues.push(ExternalResultValidationIssue::error(
                format!("candidate.normalized_metrics[{index}].source_artifact_ref"),
                "metric source artifact ref is absolute or contains traversal",
            ));
        }
    }
    for (note_index, note) in metric.notes.iter().enumerate() {
        if contains_forbidden_claim_text(note) {
            issues.push(ExternalResultValidationIssue::error(
                format!("candidate.normalized_metrics[{index}].notes[{note_index}]"),
                "metric notes contain a forbidden Phase H claim",
            ));
        }
    }
}
