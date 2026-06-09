//! Provenance contract and draft validation for future external result imports.

use serde::{Deserialize, Serialize};

use crate::evidence::{ArtifactDigest, ClaimBoundary};

use super::validation::{phase_h_design_artifact_claim_allowed, ExternalValidationIssueSeverity};

/// Provenance field required by the Phase H contract.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
pub enum RequiredProvenanceField {
    /// operator_or_agent
    OperatorOrAgent,
    /// execution_date_declared_by_operator
    ExecutionDateDeclaredByOperator,
    /// external_tool_name
    ExternalToolName,
    /// external_tool_version
    ExternalToolVersion,
    /// external_tool_source
    ExternalToolSource,
    /// external_tool_commit_or_release
    ExternalToolCommitOrRelease,
    /// host_os
    HostOs,
    /// hardware_summary
    HardwareSummary,
    /// command_plan_id
    CommandPlanId,
    /// benchmark_pack_id
    BenchmarkPackId,
    /// artifact_digest_set
    ArtifactDigestSet,
    /// network_policy
    NetworkPolicy,
    /// notes
    Notes,
}

impl RequiredProvenanceField {
    /// Return the stable schema key for this required field.
    pub fn as_key(self) -> &'static str {
        match self {
            Self::OperatorOrAgent => "operator_or_agent",
            Self::ExecutionDateDeclaredByOperator => "execution_date_declared_by_operator",
            Self::ExternalToolName => "external_tool_name",
            Self::ExternalToolVersion => "external_tool_version",
            Self::ExternalToolSource => "external_tool_source",
            Self::ExternalToolCommitOrRelease => "external_tool_commit_or_release",
            Self::HostOs => "host_os",
            Self::HardwareSummary => "hardware_summary",
            Self::CommandPlanId => "command_plan_id",
            Self::BenchmarkPackId => "benchmark_pack_id",
            Self::ArtifactDigestSet => "artifact_digest_set",
            Self::NetworkPolicy => "network_policy",
            Self::Notes => "notes",
        }
    }
}

/// Requirement declaration for a provenance field.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ProvenanceFieldRequirement {
    /// Required field.
    pub field: RequiredProvenanceField,
    /// Whether the field is required.
    pub required: bool,
    /// Notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

/// Provenance contract.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ProvenanceContract {
    /// Contract id.
    pub id: String,
    /// Schema version.
    pub schema_version: String,
    /// Required fields.
    pub required_fields: Vec<ProvenanceFieldRequirement>,
    /// Claim boundary for the contract artifact.
    pub claim_boundary: ClaimBoundary,
    /// Notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

/// External tool provenance draft.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize, Default)]
pub struct ExternalToolProvenance {
    /// external_tool_name
    #[serde(default)]
    pub external_tool_name: Option<String>,
    /// external_tool_version
    #[serde(default)]
    pub external_tool_version: Option<String>,
    /// external_tool_source
    #[serde(default)]
    pub external_tool_source: Option<String>,
    /// external_tool_commit_or_release
    #[serde(default)]
    pub external_tool_commit_or_release: Option<String>,
}

/// Environment provenance draft.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize, Default)]
pub struct EnvironmentProvenance {
    /// host_os
    #[serde(default)]
    pub host_os: Option<String>,
    /// hardware_summary
    #[serde(default)]
    pub hardware_summary: Option<String>,
    /// network_policy
    #[serde(default)]
    pub network_policy: Option<String>,
}

/// Operator provenance draft.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize, Default)]
pub struct OperatorProvenance {
    /// operator_or_agent
    #[serde(default)]
    pub operator_or_agent: Option<String>,
    /// execution_date_declared_by_operator
    #[serde(default)]
    pub execution_date_declared_by_operator: Option<String>,
}

/// Source provenance draft.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize, Default)]
pub struct SourceProvenance {
    /// command_plan_id
    #[serde(default)]
    pub command_plan_id: Option<String>,
    /// benchmark_pack_id
    #[serde(default)]
    pub benchmark_pack_id: Option<String>,
    /// artifact_digest_set
    #[serde(default)]
    pub artifact_digest_set: Vec<ArtifactDigest>,
}

/// External run provenance draft.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize, Default)]
pub struct ExternalRunProvenanceDraft {
    /// Draft id.
    #[serde(default)]
    pub id: Option<String>,
    /// Operator provenance.
    pub operator: OperatorProvenance,
    /// External tool provenance.
    pub external_tool: ExternalToolProvenance,
    /// Environment provenance.
    pub environment: EnvironmentProvenance,
    /// Source provenance.
    pub source: SourceProvenance,
    /// Notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

/// Provenance validation issue.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ProvenanceValidationIssue {
    /// Issue path.
    pub path: String,
    /// Issue message.
    pub message: String,
    /// Issue severity.
    pub severity: ExternalValidationIssueSeverity,
}

impl ProvenanceValidationIssue {
    fn error(path: impl Into<String>, message: impl Into<String>) -> Self {
        Self {
            path: path.into(),
            message: message.into(),
            severity: ExternalValidationIssueSeverity::Error,
        }
    }
}

/// Provenance validation result.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ProvenanceValidation {
    /// True when there are no errors.
    pub valid: bool,
    /// Validation issues.
    pub issues: Vec<ProvenanceValidationIssue>,
}

/// Build the default Phase H provenance contract.
pub fn build_default_provenance_contract() -> ProvenanceContract {
    ProvenanceContract {
        id: "provenance_contract_phase_h".to_string(),
        schema_version: "phase-h-provenance-contract-v0".to_string(),
        required_fields: required_provenance_fields()
            .into_iter()
            .map(|field| ProvenanceFieldRequirement {
                field,
                required: true,
                notes: vec![format!("Required provenance key: {}", field.as_key())],
            })
            .collect(),
        claim_boundary: ClaimBoundary::Level0DesignNote,
        notes: vec![
            "Provenance contract only; no live external run is represented by this document."
                .to_string(),
            "Result import candidates are quarantined or pending review until validated."
                .to_string(),
        ],
    }
}

/// Return the required provenance fields in deterministic order.
pub fn required_provenance_fields() -> Vec<RequiredProvenanceField> {
    vec![
        RequiredProvenanceField::OperatorOrAgent,
        RequiredProvenanceField::ExecutionDateDeclaredByOperator,
        RequiredProvenanceField::ExternalToolName,
        RequiredProvenanceField::ExternalToolVersion,
        RequiredProvenanceField::ExternalToolSource,
        RequiredProvenanceField::ExternalToolCommitOrRelease,
        RequiredProvenanceField::HostOs,
        RequiredProvenanceField::HardwareSummary,
        RequiredProvenanceField::CommandPlanId,
        RequiredProvenanceField::BenchmarkPackId,
        RequiredProvenanceField::ArtifactDigestSet,
        RequiredProvenanceField::NetworkPolicy,
        RequiredProvenanceField::Notes,
    ]
}

/// Validate a provenance contract.
pub fn validate_provenance_contract(contract: &ProvenanceContract) -> ProvenanceValidation {
    let mut issues = Vec::new();
    if contract.id.trim().is_empty() {
        issues.push(ProvenanceValidationIssue::error(
            "contract.id",
            "provenance contract id is empty",
        ));
    }
    if !phase_h_design_artifact_claim_allowed(contract.claim_boundary) {
        issues.push(ProvenanceValidationIssue::error(
            "contract.claim_boundary",
            "provenance contracts must remain Level0DesignNote",
        ));
    }
    for field in required_provenance_fields() {
        if !contract
            .required_fields
            .iter()
            .any(|requirement| requirement.field == field && requirement.required)
        {
            issues.push(ProvenanceValidationIssue::error(
                format!("contract.required_fields.{}", field.as_key()),
                "required provenance field is missing",
            ));
        }
    }
    ProvenanceValidation {
        valid: issues.is_empty(),
        issues,
    }
}

/// Validate a provenance draft against the default required fields.
pub fn validate_external_run_provenance_draft(
    draft: &ExternalRunProvenanceDraft,
) -> ProvenanceValidation {
    let mut issues = Vec::new();
    require_some(
        &draft.operator.operator_or_agent,
        "provenance.operator.operator_or_agent",
        &mut issues,
    );
    require_some(
        &draft.operator.execution_date_declared_by_operator,
        "provenance.operator.execution_date_declared_by_operator",
        &mut issues,
    );
    require_some(
        &draft.external_tool.external_tool_name,
        "provenance.external_tool.external_tool_name",
        &mut issues,
    );
    require_some(
        &draft.external_tool.external_tool_version,
        "provenance.external_tool.external_tool_version",
        &mut issues,
    );
    require_some(
        &draft.external_tool.external_tool_source,
        "provenance.external_tool.external_tool_source",
        &mut issues,
    );
    require_some(
        &draft.external_tool.external_tool_commit_or_release,
        "provenance.external_tool.external_tool_commit_or_release",
        &mut issues,
    );
    require_some(
        &draft.environment.host_os,
        "provenance.environment.host_os",
        &mut issues,
    );
    require_some(
        &draft.environment.hardware_summary,
        "provenance.environment.hardware_summary",
        &mut issues,
    );
    require_some(
        &draft.environment.network_policy,
        "provenance.environment.network_policy",
        &mut issues,
    );
    require_some(
        &draft.source.command_plan_id,
        "provenance.source.command_plan_id",
        &mut issues,
    );
    require_some(
        &draft.source.benchmark_pack_id,
        "provenance.source.benchmark_pack_id",
        &mut issues,
    );
    if draft.source.artifact_digest_set.is_empty() {
        issues.push(ProvenanceValidationIssue::error(
            "provenance.source.artifact_digest_set",
            "artifact_digest_set is required",
        ));
    }
    if draft.notes.is_empty() {
        issues.push(ProvenanceValidationIssue::error(
            "provenance.notes",
            "notes are required",
        ));
    }
    ProvenanceValidation {
        valid: issues.is_empty(),
        issues,
    }
}

fn require_some(value: &Option<String>, path: &str, issues: &mut Vec<ProvenanceValidationIssue>) {
    let missing = match value {
        Some(text) => text.trim().is_empty(),
        None => true,
    };
    if missing {
        issues.push(ProvenanceValidationIssue::error(
            path,
            "required provenance value is missing",
        ));
    }
}
