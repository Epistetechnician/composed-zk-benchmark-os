//! External-runner policy types.
//!
//! These policies describe the boundary for a future external runner. They do
//! not provide any process execution API.

use serde::{Deserialize, Serialize};

use crate::evidence::ClaimBoundary;

use super::validation::{
    contains_rejected_path, phase_h_actual_claim_allowed, ExternalValidationIssue,
};

/// External-runner policy id.
pub type ExternalRunnerPolicyId = String;

/// External-runner policy version.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ExternalRunnerPolicyVersion {
    /// Logical version string.
    pub value: String,
}

impl Default for ExternalRunnerPolicyVersion {
    fn default() -> Self {
        Self {
            value: "phase-h-external-runner-policy-v0".to_string(),
        }
    }
}

/// External execution mode. Phase H artifacts may only use disabled or manual
/// handoff modes.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum ExternalExecutionMode {
    /// No external execution is permitted.
    Disabled,
    /// Manual handoff bundles may be produced, but no process is launched.
    ManualHandoffOnly,
    /// Future feature-gated execution marker. Not allowed for actual Phase H artifacts.
    FeatureGatedFutureExecution,
    /// Future live execution marker. Not implemented and not allowed in Phase H artifacts.
    FutureLiveExecutionNotImplemented,
}

impl ExternalExecutionMode {
    /// Return true when this mode would imply live external execution.
    pub fn implies_live_execution(self) -> bool {
        matches!(
            self,
            Self::FeatureGatedFutureExecution | Self::FutureLiveExecutionNotImplemented
        )
    }

    /// Return true when this mode is allowed for actual Phase H artifacts.
    pub fn is_phase_h_allowed(self) -> bool {
        matches!(self, Self::Disabled | Self::ManualHandoffOnly)
    }
}

/// Review status for an external-runner policy.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum ExternalExecutionReviewStatus {
    /// Draft policy.
    Draft,
    /// Pending manual review.
    PendingReview,
    /// Reviewed for manual handoff only.
    ReviewedForManualHandoff,
    /// Rejected policy.
    Rejected,
    /// Future approval marker, not used by Phase H generated artifacts.
    FutureApprovalRequired,
}

/// Gate requirements for any future external execution.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ExternalExecutionGate {
    /// Future live execution would require an explicit feature.
    pub requires_explicit_feature: bool,
    /// Manual review is required.
    pub requires_manual_review: bool,
    /// Clean worktree or recorded snapshot is required.
    pub requires_clean_worktree_or_recorded_snapshot: bool,
    /// Artifact capture contract is required.
    pub requires_artifact_capture_contract: bool,
    /// Provenance contract is required.
    pub requires_provenance_contract: bool,
    /// Result import validation is required.
    pub requires_result_import_validation: bool,
    /// Claim-boundary review is required.
    pub requires_claim_boundary_review: bool,
}

impl Default for ExternalExecutionGate {
    fn default() -> Self {
        Self {
            requires_explicit_feature: true,
            requires_manual_review: true,
            requires_clean_worktree_or_recorded_snapshot: true,
            requires_artifact_capture_contract: true,
            requires_provenance_contract: true,
            requires_result_import_validation: true,
            requires_claim_boundary_review: true,
        }
    }
}

/// Allowlist for future external tools.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ExternalToolAllowlist {
    /// Allowed external tool labels.
    pub allowed_tools: Vec<String>,
    /// Whether unlisted tools are allowed.
    pub allow_unlisted_tools: bool,
    /// Notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

impl Default for ExternalToolAllowlist {
    fn default() -> Self {
        Self {
            allowed_tools: vec!["zk-Harness".to_string()],
            allow_unlisted_tools: false,
            notes: vec![
                "Allowlist is metadata for manual handoff review only.".to_string(),
                "No external tool is launched by this policy.".to_string(),
            ],
        }
    }
}

/// Path policy for external-runner boundary artifacts.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ExternalPathPolicy {
    /// Absolute paths are allowed.
    pub allow_absolute_paths: bool,
    /// Parent directory traversal segments are allowed.
    pub allow_parent_dir_segments: bool,
    /// Allowed relative roots.
    pub allowed_relative_roots: Vec<String>,
    /// Notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

impl Default for ExternalPathPolicy {
    fn default() -> Self {
        Self {
            allow_absolute_paths: false,
            allow_parent_dir_segments: false,
            allowed_relative_roots: vec![
                "pack/".to_string(),
                "handoff/".to_string(),
                "artifacts/".to_string(),
                "provenance/".to_string(),
            ],
            notes: vec![
                "Phase H fixtures and handoff artifacts use relative references only.".to_string(),
            ],
        }
    }
}

/// Environment capture policy.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ExternalEnvironmentPolicy {
    /// Host environment capture is allowed.
    pub allow_host_environment_capture: bool,
    /// Allowed environment keys for future provenance drafts.
    pub allowed_environment_keys: Vec<String>,
    /// Secret-looking values must be redacted.
    pub redact_secret_values: bool,
    /// Notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

impl Default for ExternalEnvironmentPolicy {
    fn default() -> Self {
        Self {
            allow_host_environment_capture: false,
            allowed_environment_keys: vec![
                "host_os".to_string(),
                "hardware_summary".to_string(),
                "network_policy".to_string(),
            ],
            redact_secret_values: true,
            notes: vec![
                "Phase H records provenance requirements, not live host state.".to_string(),
            ],
        }
    }
}

/// Network policy for future external runs.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ExternalNetworkPolicy {
    /// Network access is allowed.
    pub allow_network: bool,
    /// Allowed host labels.
    pub allowed_hosts: Vec<String>,
    /// Notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

impl Default for ExternalNetworkPolicy {
    fn default() -> Self {
        Self {
            allow_network: false,
            allowed_hosts: Vec::new(),
            notes: vec![
                "Manual handoff review must record network policy before any future run."
                    .to_string(),
            ],
        }
    }
}

/// Result import policy.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ExternalResultPolicy {
    /// Result import candidate schemas may be produced.
    pub allow_result_import_candidates: bool,
    /// Imported candidates must begin in quarantine or pending review.
    pub require_quarantine_or_pending_review: bool,
    /// Metric values require source artifact references.
    pub require_metric_source_artifact_refs: bool,
    /// Official benchmark evidence claims are rejected.
    pub reject_official_benchmark_claims: bool,
    /// Formal evidence claims are rejected.
    pub reject_formal_evidence_claims: bool,
    /// Proof-system soundness claims are rejected.
    pub reject_proof_system_soundness_claims: bool,
    /// Notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

impl Default for ExternalResultPolicy {
    fn default() -> Self {
        Self {
            allow_result_import_candidates: true,
            require_quarantine_or_pending_review: true,
            require_metric_source_artifact_refs: true,
            reject_official_benchmark_claims: true,
            reject_formal_evidence_claims: true,
            reject_proof_system_soundness_claims: true,
            notes: vec![
                "Result import candidates are quarantined or pending review until validated."
                    .to_string(),
                "No official benchmark evidence is created by Phase H.".to_string(),
            ],
        }
    }
}

/// Claim-boundary policy for the external-runner boundary.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ExternalClaimBoundaryPolicy {
    /// Maximum actual claim boundary allowed in Phase H.
    pub maximum_actual_claim_boundary: ClaimBoundary,
    /// Level 2+ may be named only as planned future metadata.
    pub allow_future_planned_level2_metadata: bool,
    /// Actual Level 2+ evidence is rejected.
    pub reject_level2_plus_actual_evidence: bool,
    /// Notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

impl Default for ExternalClaimBoundaryPolicy {
    fn default() -> Self {
        Self {
            maximum_actual_claim_boundary: ClaimBoundary::Level1LocalReplay,
            allow_future_planned_level2_metadata: true,
            reject_level2_plus_actual_evidence: true,
            notes: vec![
                "Manual handoff bundles are Level0DesignNote.".to_string(),
                "Local replay references may remain Level1LocalReplay without elevation."
                    .to_string(),
                "Level2+ actual evidence is outside Phase H.".to_string(),
            ],
        }
    }
}

impl ExternalClaimBoundaryPolicy {
    /// Return true when the actual claim boundary is allowed by this policy.
    pub fn permits_actual_claim_boundary(&self, boundary: ClaimBoundary) -> bool {
        boundary <= self.maximum_actual_claim_boundary && phase_h_actual_claim_allowed(boundary)
    }
}

/// External-runner boundary policy.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ExternalRunnerPolicy {
    /// Policy id.
    pub id: ExternalRunnerPolicyId,
    /// Policy version.
    pub policy_version: ExternalRunnerPolicyVersion,
    /// Execution mode.
    pub mode: ExternalExecutionMode,
    /// Review status.
    pub review_status: ExternalExecutionReviewStatus,
    /// Required gates.
    pub gate: ExternalExecutionGate,
    /// Tool allowlist.
    pub tool_allowlist: ExternalToolAllowlist,
    /// Path policy.
    pub path_policy: ExternalPathPolicy,
    /// Environment policy.
    pub environment_policy: ExternalEnvironmentPolicy,
    /// Network policy.
    pub network_policy: ExternalNetworkPolicy,
    /// Result policy.
    pub result_policy: ExternalResultPolicy,
    /// Claim-boundary policy.
    pub claim_boundary_policy: ExternalClaimBoundaryPolicy,
    /// Claim boundary for this policy artifact.
    pub claim_boundary: ClaimBoundary,
    /// Notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

impl ExternalRunnerPolicy {
    /// Return true if this policy allows live external execution.
    pub fn allows_live_execution(&self) -> bool {
        self.mode.implies_live_execution()
    }

    /// Build the default disabled Phase H policy.
    pub fn phase_h_default() -> Self {
        build_default_external_runner_policy()
    }

    /// Build a manual-handoff-only policy for handoff bundles.
    pub fn phase_h_manual_handoff_only() -> Self {
        let mut policy = build_default_external_runner_policy();
        policy.id = "external_runner_policy_phase_h_manual_handoff_only".to_string();
        policy.mode = ExternalExecutionMode::ManualHandoffOnly;
        policy.review_status = ExternalExecutionReviewStatus::PendingReview;
        policy.notes.push(
            "Manual handoff only; this policy still provides no live execution API.".to_string(),
        );
        policy
    }
}

/// Build the conservative default external-runner boundary policy.
pub fn build_default_external_runner_policy() -> ExternalRunnerPolicy {
    ExternalRunnerPolicy {
        id: "external_runner_policy_phase_h_disabled".to_string(),
        policy_version: ExternalRunnerPolicyVersion::default(),
        mode: ExternalExecutionMode::Disabled,
        review_status: ExternalExecutionReviewStatus::Draft,
        gate: ExternalExecutionGate::default(),
        tool_allowlist: ExternalToolAllowlist::default(),
        path_policy: ExternalPathPolicy::default(),
        environment_policy: ExternalEnvironmentPolicy::default(),
        network_policy: ExternalNetworkPolicy::default(),
        result_policy: ExternalResultPolicy::default(),
        claim_boundary_policy: ExternalClaimBoundaryPolicy::default(),
        claim_boundary: ClaimBoundary::Level0DesignNote,
        notes: vec![
            "External execution is disabled by default.".to_string(),
            "Manual handoff bundles are not benchmark results.".to_string(),
            "No official benchmark evidence is created by this policy.".to_string(),
        ],
    }
}

/// Validate a Phase H external-runner policy.
pub fn validate_external_runner_policy(
    policy: &ExternalRunnerPolicy,
) -> Vec<ExternalValidationIssue> {
    let mut errors = Vec::new();
    if policy.id.trim().is_empty() {
        errors.push(ExternalValidationIssue::error(
            "policy.id",
            "external runner policy id is empty",
        ));
    }
    if !policy.mode.is_phase_h_allowed() {
        errors.push(ExternalValidationIssue::error(
            "policy.mode",
            "Phase H policy must be Disabled or ManualHandoffOnly",
        ));
    }
    if policy.allows_live_execution() {
        errors.push(ExternalValidationIssue::error(
            "policy.mode",
            "live external execution is not implemented in Phase H",
        ));
    }
    if policy.claim_boundary != ClaimBoundary::Level0DesignNote {
        errors.push(ExternalValidationIssue::error(
            "policy.claim_boundary",
            "external-runner policy artifacts must remain Level0DesignNote",
        ));
    }
    if !policy
        .claim_boundary_policy
        .permits_actual_claim_boundary(ClaimBoundary::Level1LocalReplay)
    {
        errors.push(ExternalValidationIssue::error(
            "policy.claim_boundary_policy",
            "claim policy must allow existing Level1LocalReplay references without elevation",
        ));
    }
    if policy
        .claim_boundary_policy
        .permits_actual_claim_boundary(ClaimBoundary::Level2ReproducibleBenchmarkArtifact)
    {
        errors.push(ExternalValidationIssue::error(
            "policy.claim_boundary_policy",
            "claim policy must reject Level2+ actual evidence in Phase H",
        ));
    }
    if !policy.gate.requires_manual_review
        || !policy.gate.requires_artifact_capture_contract
        || !policy.gate.requires_provenance_contract
        || !policy.gate.requires_result_import_validation
        || !policy.gate.requires_claim_boundary_review
    {
        errors.push(ExternalValidationIssue::error(
            "policy.gate",
            "Phase H policy must require manual review, capture, provenance, import validation, and claim-boundary review",
        ));
    }
    if policy.path_policy.allow_absolute_paths {
        errors.push(ExternalValidationIssue::error(
            "policy.path_policy.allow_absolute_paths",
            "absolute paths must be rejected",
        ));
    }
    for (index, root) in policy.path_policy.allowed_relative_roots.iter().enumerate() {
        if contains_rejected_path(root) {
            errors.push(ExternalValidationIssue::error(
                format!("policy.path_policy.allowed_relative_roots[{index}]"),
                "relative root is absolute or contains traversal",
            ));
        }
    }
    errors
}
