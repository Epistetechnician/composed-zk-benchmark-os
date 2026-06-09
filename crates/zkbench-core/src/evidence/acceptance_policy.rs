//! Phase J evidence acceptance policy.
//!
//! The policy creates evidence-record candidates only. It does not create
//! accepted evidence records and does not append to `EvidenceLedger`.

use serde::{Deserialize, Serialize};

use crate::error::{Result, ZkBenchError};

use super::escalation_guard::ClaimBoundaryEscalationGuard;
use super::review::{
    validate_evidence_review_decision, EvidenceReviewDecision, EvidenceReviewDecisionKind,
    EvidenceReviewerRole,
};
use super::{ClaimBoundary, EvidenceClass};

/// Evidence acceptance policy id.
pub type EvidenceAcceptancePolicyId = String;

/// Evidence acceptance policy version.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct EvidenceAcceptancePolicyVersion {
    /// Logical version string.
    pub value: String,
}

impl Default for EvidenceAcceptancePolicyVersion {
    fn default() -> Self {
        Self {
            value: "phase-j-evidence-acceptance-policy-v0".to_string(),
        }
    }
}

/// Phase J policy mode.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
pub enum EvidenceAcceptancePolicyMode {
    /// Proposals only; no candidate creation.
    ProposalOnly,
    /// Candidate creation only.
    CandidateOnly,
    /// Candidate creation capped at Level1LocalReplay.
    Level1LocalOnly,
    /// Level2 eligibility checks only; no Level2 evidence.
    Level2EligibilityCheckOnly,
}

/// Blocking reason for acceptance policy failures.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
pub enum EvidenceAcceptanceBlockingReason {
    /// Proposal was not reviewable.
    ProposalNotReviewable,
    /// Proposal was rejected.
    ProposalRejected,
    /// Proposal had changes requested.
    ProposalChangesRequested,
    /// Proposal has blocking issues.
    ProposalHasBlockingIssues,
    /// Review decision was invalid.
    InvalidReviewDecision,
    /// Automated review alone is insufficient.
    AutomatedReviewInsufficient,
    /// Claim boundary escalation was blocked.
    ClaimBoundaryEscalationBlocked,
    /// Level2 actual evidence is blocked.
    Level2ActualEvidenceBlocked,
    /// Formal evidence is blocked.
    FormalEvidenceBlocked,
    /// Official benchmark claim was detected.
    OfficialBenchmarkClaimDetected,
    /// Soundness claim was detected.
    SoundnessClaimDetected,
    /// Candidate metrics attempted to affect scoring.
    CandidateMetricsForScoring,
    /// Artifact digest was missing.
    MissingArtifactDigest,
    /// Provenance was missing.
    MissingProvenance,
    /// Evidence class is disallowed.
    DisallowedEvidenceClass,
}

/// Acceptance rule.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct EvidenceAcceptanceRule {
    /// Rule id.
    pub id: String,
    /// Rule description.
    pub description: String,
    /// Whether the rule is required.
    pub required: bool,
    /// Blocking reason when the rule fails.
    pub blocking_reason: EvidenceAcceptanceBlockingReason,
}

/// Acceptance rule result.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct EvidenceAcceptanceRuleResult {
    /// Rule id.
    pub rule_id: String,
    /// Whether the rule passed.
    pub passed: bool,
    /// Blocking reason when failed.
    #[serde(default)]
    pub blocking_reason: Option<EvidenceAcceptanceBlockingReason>,
    /// Message.
    pub message: String,
}

/// Acceptance validation issue.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct EvidenceAcceptanceValidationIssue {
    /// Issue path.
    pub path: String,
    /// Issue message.
    pub message: String,
    /// Blocking reason.
    pub blocking_reason: EvidenceAcceptanceBlockingReason,
}

/// Acceptance validation result.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct EvidenceAcceptanceValidation {
    /// True when no blocking issues were found.
    pub valid: bool,
    /// Issues.
    pub issues: Vec<EvidenceAcceptanceValidationIssue>,
    /// Rule results.
    pub rule_results: Vec<EvidenceAcceptanceRuleResult>,
}

/// Evidence acceptance policy.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct EvidenceAcceptancePolicy {
    /// Policy id.
    pub id: EvidenceAcceptancePolicyId,
    /// Policy version.
    pub version: EvidenceAcceptancePolicyVersion,
    /// Policy mode.
    pub mode: EvidenceAcceptancePolicyMode,
    /// Rules.
    pub rules: Vec<EvidenceAcceptanceRule>,
    /// Allowed source proposal statuses.
    pub allowed_source_proposal_statuses: Vec<crate::external_runner::EvidenceAppendProposalStatus>,
    /// Allowed review decision kinds.
    pub allowed_review_decision_kinds: Vec<EvidenceReviewDecisionKind>,
    /// Allowed claim boundaries.
    pub allowed_claim_boundaries: Vec<ClaimBoundary>,
    /// Disallowed evidence classes.
    pub disallowed_evidence_classes: Vec<EvidenceClass>,
    /// Required reviewer roles.
    pub required_reviewer_roles: Vec<EvidenceReviewerRole>,
    /// Claim-boundary escalation guard.
    pub claim_boundary_escalation_guard: ClaimBoundaryEscalationGuard,
    /// Notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

impl EvidenceAcceptancePolicy {
    /// Build the conservative default Phase J policy.
    pub fn phase_j_conservative() -> Self {
        Self {
            id: "phase_j_candidate_only_policy".to_string(),
            version: EvidenceAcceptancePolicyVersion::default(),
            mode: EvidenceAcceptancePolicyMode::CandidateOnly,
            rules: default_rules(),
            allowed_source_proposal_statuses: vec![
                crate::external_runner::EvidenceAppendProposalStatus::Draft,
                crate::external_runner::EvidenceAppendProposalStatus::PendingReview,
            ],
            allowed_review_decision_kinds: vec![
                EvidenceReviewDecisionKind::ApproveForCandidateOnly,
                EvidenceReviewDecisionKind::ApproveForFutureAppendPreview,
            ],
            allowed_claim_boundaries: vec![ClaimBoundary::Level0DesignNote],
            disallowed_evidence_classes: vec![
                EvidenceClass::ReproducibleBenchmarkArtifact,
                EvidenceClass::CrossBackendReplay,
                EvidenceClass::FormalPropertyStatement,
                EvidenceClass::MachineCheckedScopedProof,
                EvidenceClass::IndependentlyReproducedEvidence,
            ],
            required_reviewer_roles: vec![
                EvidenceReviewerRole::Maintainer,
                EvidenceReviewerRole::ResearchReviewer,
                EvidenceReviewerRole::EvidenceReviewer,
            ],
            claim_boundary_escalation_guard: ClaimBoundaryEscalationGuard::default(),
            notes: vec![
                "Evidence-record candidates are not accepted evidence.".to_string(),
                "Append previews do not mutate EvidenceLedger.".to_string(),
                "Level2 eligibility is not Level2 evidence.".to_string(),
            ],
        }
    }

    /// Build a strict local-only Level1 candidate policy.
    pub fn phase_j_level1_local_only() -> Self {
        let mut policy = Self::phase_j_conservative();
        policy.id = "phase_j_level1_local_only_policy".to_string();
        policy.mode = EvidenceAcceptancePolicyMode::Level1LocalOnly;
        policy.allowed_claim_boundaries = vec![
            ClaimBoundary::Level0DesignNote,
            ClaimBoundary::Level1LocalReplay,
        ];
        policy.claim_boundary_escalation_guard =
            ClaimBoundaryEscalationGuard::allowing_level1_local_candidates();
        policy
    }

    /// Validate whether proposal and review decision can create a candidate.
    pub fn validate_proposal_for_candidate(
        &self,
        proposal: &crate::external_runner::EvidenceAppendProposal,
        decision: &EvidenceReviewDecision,
        target_claim_boundary: ClaimBoundary,
    ) -> EvidenceAcceptanceValidation {
        let mut issues = Vec::new();
        let mut rule_results = Vec::new();
        push_rule_result(
            &mut rule_results,
            "policy_mode_allows_candidates",
            matches!(
                self.mode,
                EvidenceAcceptancePolicyMode::CandidateOnly
                    | EvidenceAcceptancePolicyMode::Level1LocalOnly
            ),
            EvidenceAcceptanceBlockingReason::ProposalNotReviewable,
            "policy mode allows candidate creation",
        );
        if !self
            .allowed_source_proposal_statuses
            .contains(&proposal.status)
        {
            issues.push(issue(
                "proposal.status",
                "proposal status is not reviewable",
                EvidenceAcceptanceBlockingReason::ProposalNotReviewable,
            ));
        }
        if proposal
            .review_state
            == crate::external_runner::EvidenceAppendProposalReviewState::Rejected
            || proposal.status == crate::external_runner::EvidenceAppendProposalStatus::Rejected
        {
            issues.push(issue(
                "proposal.review_state",
                "rejected proposals cannot create candidates",
                EvidenceAcceptanceBlockingReason::ProposalRejected,
            ));
        }
        if proposal.review_state
            == crate::external_runner::EvidenceAppendProposalReviewState::ChangesRequested
        {
            issues.push(issue(
                "proposal.review_state",
                "changes-requested proposals cannot create candidates",
                EvidenceAcceptanceBlockingReason::ProposalChangesRequested,
            ));
        }
        if !proposal.blocking_issues.is_empty() {
            issues.push(issue(
                "proposal.blocking_issues",
                "proposal has blocking issues",
                EvidenceAcceptanceBlockingReason::ProposalHasBlockingIssues,
            ));
        }
        let decision_report = validate_evidence_review_decision(decision);
        if !decision_report.valid {
            issues.push(issue(
                "review_decision",
                format!(
                    "review decision failed validation: {:?}",
                    decision_report.blocking_issues
                ),
                EvidenceAcceptanceBlockingReason::InvalidReviewDecision,
            ));
        }
        if !decision.reviewer_role.is_human_review_role() {
            issues.push(issue(
                "review_decision.reviewer_role",
                "AutomatedPolicyCheck alone cannot approve candidate creation",
                EvidenceAcceptanceBlockingReason::AutomatedReviewInsufficient,
            ));
        }
        if !self
            .allowed_review_decision_kinds
            .contains(&decision.decision_kind)
        {
            issues.push(issue(
                "review_decision.decision_kind",
                "review decision kind is not allowed by policy",
                EvidenceAcceptanceBlockingReason::InvalidReviewDecision,
            ));
        }
        if !self.allowed_claim_boundaries.contains(&target_claim_boundary) {
            issues.push(issue(
                "target_claim_boundary",
                "target claim boundary is not allowed by policy",
                EvidenceAcceptanceBlockingReason::ClaimBoundaryEscalationBlocked,
            ));
        }
        let guard_result = self
            .claim_boundary_escalation_guard
            .check_escalation(proposal.proposed_claim_boundary, target_claim_boundary);
        if !guard_result.allowed {
            issues.push(issue(
                "claim_boundary_escalation_guard",
                format!(
                    "claim boundary escalation blocked: {:?}",
                    guard_result.blocking_reasons
                ),
                EvidenceAcceptanceBlockingReason::ClaimBoundaryEscalationBlocked,
            ));
        }
        if target_claim_boundary >= ClaimBoundary::Level2ReproducibleBenchmarkArtifact {
            issues.push(issue(
                "target_claim_boundary",
                "Level2+ actual evidence is blocked in Phase J",
                EvidenceAcceptanceBlockingReason::Level2ActualEvidenceBlocked,
            ));
        }
        if self
            .disallowed_evidence_classes
            .contains(&proposal.proposed_evidence_class)
        {
            issues.push(issue(
                "proposal.proposed_evidence_class",
                "proposal evidence class is disallowed",
                EvidenceAcceptanceBlockingReason::DisallowedEvidenceClass,
            ));
        }
        if proposal.proposed_artifact_refs.is_empty() {
            issues.push(issue(
                "proposal.proposed_artifact_refs",
                "proposal lacks artifact digests",
                EvidenceAcceptanceBlockingReason::MissingArtifactDigest,
            ));
        }
        if proposal.proposed_provenance_summary.is_empty() {
            issues.push(issue(
                "proposal.proposed_provenance_summary",
                "proposal lacks provenance summary",
                EvidenceAcceptanceBlockingReason::MissingProvenance,
            ));
        }
        scan_forbidden_text(proposal, decision, &mut issues);

        EvidenceAcceptanceValidation {
            valid: issues.is_empty()
                && rule_results
                    .iter()
                    .all(|result| result.passed || result.blocking_reason.is_none()),
            issues,
            rule_results,
        }
    }
}

impl Default for EvidenceAcceptancePolicy {
    fn default() -> Self {
        Self::phase_j_conservative()
    }
}

/// Build the default Phase J acceptance policy.
pub fn build_default_evidence_acceptance_policy() -> EvidenceAcceptancePolicy {
    EvidenceAcceptancePolicy::phase_j_conservative()
}

/// Validate an acceptance policy.
pub fn validate_evidence_acceptance_policy(
    policy: &EvidenceAcceptancePolicy,
) -> EvidenceAcceptanceValidation {
    let mut issues = Vec::new();
    if policy.id.trim().is_empty() {
        issues.push(issue(
            "policy.id",
            "policy id is empty",
            EvidenceAcceptanceBlockingReason::ProposalNotReviewable,
        ));
    }
    if matches!(
        policy.mode,
        EvidenceAcceptancePolicyMode::Level2EligibilityCheckOnly
            | EvidenceAcceptancePolicyMode::ProposalOnly
    ) {
        issues.push(issue(
            "policy.mode",
            "default Phase J policy must support candidate-only or Level1 local-only checks",
            EvidenceAcceptanceBlockingReason::ProposalNotReviewable,
        ));
    }
    if policy
        .allowed_claim_boundaries
        .iter()
        .any(|boundary| *boundary >= ClaimBoundary::Level2ReproducibleBenchmarkArtifact)
    {
        issues.push(issue(
            "policy.allowed_claim_boundaries",
            "policy must not allow Level2+ actual evidence in Phase J",
            EvidenceAcceptanceBlockingReason::Level2ActualEvidenceBlocked,
        ));
    }
    EvidenceAcceptanceValidation {
        valid: issues.is_empty(),
        issues,
        rule_results: Vec::new(),
    }
}

/// Serialize an acceptance policy to pretty JSON.
pub fn serialize_evidence_acceptance_policy_json(
    policy: &EvidenceAcceptancePolicy,
) -> Result<String> {
    serde_json::to_string_pretty(policy).map_err(|error| {
        ZkBenchError::serialization(
            "serialize_evidence_acceptance_policy_json",
            error.to_string(),
        )
    })
}

/// Deserialize an acceptance policy from JSON.
pub fn deserialize_evidence_acceptance_policy_json(
    json: &str,
) -> Result<EvidenceAcceptancePolicy> {
    serde_json::from_str(json).map_err(|error| {
        ZkBenchError::deserialization(
            "deserialize_evidence_acceptance_policy_json",
            error.to_string(),
        )
    })
}

fn scan_forbidden_text(
    proposal: &crate::external_runner::EvidenceAppendProposal,
    decision: &EvidenceReviewDecision,
    issues: &mut Vec<EvidenceAcceptanceValidationIssue>,
) {
    for (index, note) in proposal.notes.iter().enumerate() {
        push_claim_issue(format!("proposal.notes[{index}]"), note, issues);
    }
    for (index, note) in decision.notes.iter().enumerate() {
        push_claim_issue(format!("review_decision.notes[{index}]"), note, issues);
    }
    for (index, summary) in proposal.proposed_provenance_summary.iter().enumerate() {
        push_claim_issue(
            format!("proposal.proposed_provenance_summary[{index}]"),
            summary,
            issues,
        );
    }
}

fn push_claim_issue(
    path: String,
    text: &str,
    issues: &mut Vec<EvidenceAcceptanceValidationIssue>,
) {
    if crate::external_runner::contains_official_claim_text(text) {
        issues.push(issue(
            path,
            "official benchmark claim language is blocked",
            EvidenceAcceptanceBlockingReason::OfficialBenchmarkClaimDetected,
        ));
    } else if crate::external_runner::contains_formal_claim_text(text) {
        issues.push(issue(
            path,
            "formal proof claim language is blocked",
            EvidenceAcceptanceBlockingReason::FormalEvidenceBlocked,
        ));
    } else if crate::external_runner::contains_soundness_claim_text(text) {
        issues.push(issue(
            path,
            "proof-system soundness claim language is blocked",
            EvidenceAcceptanceBlockingReason::SoundnessClaimDetected,
        ));
    }
}

fn default_rules() -> Vec<EvidenceAcceptanceRule> {
    vec![
        rule(
            "source_proposal_reviewable",
            "source proposal must be Draft or PendingReview",
            EvidenceAcceptanceBlockingReason::ProposalNotReviewable,
        ),
        rule(
            "manual_review_required",
            "positive decision requires a human reviewer role",
            EvidenceAcceptanceBlockingReason::AutomatedReviewInsufficient,
        ),
        rule(
            "level2_actual_blocked",
            "Level2+ actual evidence is blocked in Phase J",
            EvidenceAcceptanceBlockingReason::Level2ActualEvidenceBlocked,
        ),
        rule(
            "no_official_claims",
            "official benchmark claims are blocked",
            EvidenceAcceptanceBlockingReason::OfficialBenchmarkClaimDetected,
        ),
    ]
}

fn rule(
    id: impl Into<String>,
    description: impl Into<String>,
    blocking_reason: EvidenceAcceptanceBlockingReason,
) -> EvidenceAcceptanceRule {
    EvidenceAcceptanceRule {
        id: id.into(),
        description: description.into(),
        required: true,
        blocking_reason,
    }
}

fn issue(
    path: impl Into<String>,
    message: impl Into<String>,
    blocking_reason: EvidenceAcceptanceBlockingReason,
) -> EvidenceAcceptanceValidationIssue {
    EvidenceAcceptanceValidationIssue {
        path: path.into(),
        message: message.into(),
        blocking_reason,
    }
}

fn push_rule_result(
    results: &mut Vec<EvidenceAcceptanceRuleResult>,
    rule_id: impl Into<String>,
    passed: bool,
    blocking_reason: EvidenceAcceptanceBlockingReason,
    message: impl Into<String>,
) {
    results.push(EvidenceAcceptanceRuleResult {
        rule_id: rule_id.into(),
        passed,
        blocking_reason: if passed { None } else { Some(blocking_reason) },
        message: message.into(),
    });
}
