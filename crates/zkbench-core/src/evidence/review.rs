//! Phase J manual review decisions and checklist primitives.
//!
//! Review decisions are policy artifacts. They are not accepted evidence and
//! they do not mutate evidence ledgers.

use serde::{Deserialize, Serialize};

use crate::error::{Result, ZkBenchError};

/// Evidence review decision id.
pub type EvidenceReviewDecisionId = String;

/// Evidence review decision schema version.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct EvidenceReviewDecisionVersion {
    /// Logical version string.
    pub value: String,
}

impl Default for EvidenceReviewDecisionVersion {
    fn default() -> Self {
        Self {
            value: "phase-j-evidence-review-decision-v0".to_string(),
        }
    }
}

/// Manual review decision kind.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
pub enum EvidenceReviewDecisionKind {
    /// Reject the proposal.
    Reject,
    /// Request changes to the proposal.
    RequestChanges,
    /// Approve candidate-only creation.
    ApproveForCandidateOnly,
    /// Approve an append preview only; future manual append is still required.
    ApproveForFutureAppendPreview,
}

/// Review decision status.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
pub enum EvidenceReviewDecisionStatus {
    /// Draft decision.
    Draft,
    /// Pending review.
    PendingReview,
    /// Finalized as rejected.
    FinalizedRejected,
    /// Finalized with changes requested.
    FinalizedChangesRequested,
    /// Finalized for candidate-only creation.
    FinalizedCandidateOnly,
    /// Superseded by another decision.
    Superseded,
}

/// Reviewer role.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
pub enum EvidenceReviewerRole {
    /// Maintainer.
    Maintainer,
    /// Research reviewer.
    ResearchReviewer,
    /// Evidence reviewer.
    EvidenceReviewer,
    /// Automated policy check.
    AutomatedPolicyCheck,
    /// Future external reviewer.
    FutureExternalReviewer,
}

impl EvidenceReviewerRole {
    /// Return true when the role is human-review-like for Phase J approvals.
    pub fn is_human_review_role(self) -> bool {
        matches!(
            self,
            Self::Maintainer | Self::ResearchReviewer | Self::EvidenceReviewer
        )
    }
}

/// Review finding severity.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
pub enum EvidenceReviewFindingSeverity {
    /// Informational finding.
    Info,
    /// Warning finding.
    Warning,
    /// Blocking finding.
    Blocking,
}

/// Review requirement declaration.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct EvidenceReviewRequirement {
    /// Requirement id.
    pub id: String,
    /// Requirement description.
    #[serde(default)]
    pub description: String,
    /// Whether the requirement is mandatory.
    pub required: bool,
    /// Whether this requirement is satisfied.
    #[serde(default)]
    pub satisfied: bool,
    /// Notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

/// Checklist item.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct EvidenceReviewChecklistItem {
    /// Checklist item id.
    pub id: String,
    /// Checklist item description.
    pub description: String,
    /// Whether the item is required for a positive decision.
    pub required: bool,
    /// Whether the item is satisfied.
    pub satisfied: bool,
    /// Finding severity to attach if unsatisfied.
    pub finding_severity_if_unsatisfied: EvidenceReviewFindingSeverity,
    /// Notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

/// Review finding.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct EvidenceReviewFinding {
    /// Finding id.
    pub id: String,
    /// Finding message.
    pub message: String,
    /// Finding severity.
    pub severity: EvidenceReviewFindingSeverity,
    /// Whether this finding blocks positive candidate creation.
    pub blocking: bool,
}

/// Review checklist.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct EvidenceReviewChecklist {
    /// Checklist items.
    #[serde(default)]
    pub items: Vec<EvidenceReviewChecklistItem>,
    /// Requirement declarations.
    #[serde(default)]
    pub requirements: Vec<EvidenceReviewRequirement>,
    /// Findings.
    #[serde(default)]
    pub findings: Vec<EvidenceReviewFinding>,
    /// Embedded prior decisions.
    #[serde(default)]
    pub decisions: Vec<EvidenceReviewDecision>,
}

impl EvidenceReviewChecklist {
    /// Build the default Phase J checklist with all required items unsatisfied.
    pub fn phase_j_default() -> Self {
        let items = phase_j_default_item_specs()
            .into_iter()
            .map(|(id, description)| EvidenceReviewChecklistItem {
                id: id.to_string(),
                description: description.to_string(),
                required: true,
                satisfied: false,
                finding_severity_if_unsatisfied: EvidenceReviewFindingSeverity::Blocking,
                notes: Vec::new(),
            })
            .collect::<Vec<_>>();
        let requirements = items
            .iter()
            .map(|item| EvidenceReviewRequirement {
                id: item.id.clone(),
                description: item.description.clone(),
                required: item.required,
                satisfied: item.satisfied,
                notes: Vec::new(),
            })
            .collect();
        Self {
            items,
            requirements,
            findings: Vec::new(),
            decisions: Vec::new(),
        }
    }

    /// Return a copy with every required item marked satisfied.
    pub fn satisfied_phase_j_default() -> Self {
        let mut checklist = Self::phase_j_default();
        for item in &mut checklist.items {
            item.satisfied = true;
        }
        checklist
    }

    /// Return true when every required checklist item is satisfied.
    pub fn required_items_satisfied(&self) -> bool {
        !self.items.is_empty()
            && self
                .items
                .iter()
                .all(|item| !item.required || item.satisfied)
    }

    /// Return ids of required items that are not satisfied.
    pub fn unsatisfied_required_item_ids(&self) -> Vec<String> {
        self.items
            .iter()
            .filter(|item| item.required && !item.satisfied)
            .map(|item| item.id.clone())
            .collect()
    }
}

impl Default for EvidenceReviewChecklist {
    fn default() -> Self {
        Self::phase_j_default()
    }
}

/// Manual review policy.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct EvidenceReviewPolicy {
    /// Policy id.
    pub id: String,
    /// Required reviewer roles for positive decisions.
    pub required_human_roles: Vec<EvidenceReviewerRole>,
    /// Notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

impl Default for EvidenceReviewPolicy {
    fn default() -> Self {
        Self {
            id: "phase_j_manual_review_policy".to_string(),
            required_human_roles: vec![
                EvidenceReviewerRole::Maintainer,
                EvidenceReviewerRole::ResearchReviewer,
                EvidenceReviewerRole::EvidenceReviewer,
            ],
            notes: vec![
                "Manual review decision objects are not accepted evidence.".to_string(),
                "AutomatedPolicyCheck alone cannot approve candidate creation.".to_string(),
            ],
        }
    }
}

/// Review report.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct EvidenceReviewReport {
    /// True when the review decision is valid.
    pub valid: bool,
    /// Review decision id.
    pub decision_id: String,
    /// Blocking issue messages.
    pub blocking_issues: Vec<String>,
    /// Notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

/// Review decision.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct EvidenceReviewDecision {
    /// Decision id.
    pub id: EvidenceReviewDecisionId,
    /// Decision version.
    pub version: EvidenceReviewDecisionVersion,
    /// Source proposal id.
    pub source_proposal_id: String,
    /// Reviewer role.
    pub reviewer_role: EvidenceReviewerRole,
    /// Decision kind.
    pub decision_kind: EvidenceReviewDecisionKind,
    /// Decision status.
    pub decision_status: EvidenceReviewDecisionStatus,
    /// Checklist.
    pub checklist: EvidenceReviewChecklist,
    /// Findings.
    #[serde(default)]
    pub findings: Vec<EvidenceReviewFinding>,
    /// Blocking issue messages.
    #[serde(default)]
    pub blocking_issues: Vec<String>,
    /// Claim-boundary decision.
    pub claim_boundary_decision: crate::evidence::ClaimBoundary,
    /// Notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

impl EvidenceReviewDecision {
    /// Build a finalized candidate-only approval decision.
    pub fn approve_for_candidate_only(
        reviewer_role: EvidenceReviewerRole,
        source_proposal_id: impl Into<String>,
        checklist: EvidenceReviewChecklist,
    ) -> Result<Self> {
        let source_proposal_id = source_proposal_id.into();
        if !reviewer_role.is_human_review_role() {
            return Err(ZkBenchError::evidence_review(
                "review_decision.reviewer_role",
                "AutomatedPolicyCheck alone cannot approve candidate creation",
            ));
        }
        if !checklist.required_items_satisfied() {
            return Err(ZkBenchError::evidence_review(
                "review_decision.checklist",
                format!(
                    "required checklist items are not satisfied: {:?}",
                    checklist.unsatisfied_required_item_ids()
                ),
            ));
        }
        Ok(Self {
            id: format!("review_decision_{source_proposal_id}_candidate_only"),
            version: EvidenceReviewDecisionVersion::default(),
            source_proposal_id,
            reviewer_role,
            decision_kind: EvidenceReviewDecisionKind::ApproveForCandidateOnly,
            decision_status: EvidenceReviewDecisionStatus::FinalizedCandidateOnly,
            checklist,
            findings: Vec::new(),
            blocking_issues: Vec::new(),
            claim_boundary_decision: crate::evidence::ClaimBoundary::Level0DesignNote,
            notes: vec![
                "reviewed proposal remains candidate-only".to_string(),
                "Evidence-record candidates are not accepted evidence.".to_string(),
            ],
        })
    }

    /// Build a finalized rejection decision.
    pub fn reject(
        reviewer_role: EvidenceReviewerRole,
        source_proposal_id: impl Into<String>,
        notes: Vec<String>,
    ) -> Self {
        let source_proposal_id = source_proposal_id.into();
        Self {
            id: format!("review_decision_{source_proposal_id}_rejected"),
            version: EvidenceReviewDecisionVersion::default(),
            source_proposal_id,
            reviewer_role,
            decision_kind: EvidenceReviewDecisionKind::Reject,
            decision_status: EvidenceReviewDecisionStatus::FinalizedRejected,
            checklist: EvidenceReviewChecklist::phase_j_default(),
            findings: Vec::new(),
            blocking_issues: vec!["proposal rejected by manual review decision".to_string()],
            claim_boundary_decision: crate::evidence::ClaimBoundary::Level0DesignNote,
            notes,
        }
    }

    /// Build a finalized changes-requested decision.
    pub fn request_changes(
        reviewer_role: EvidenceReviewerRole,
        source_proposal_id: impl Into<String>,
        notes: Vec<String>,
    ) -> Self {
        let source_proposal_id = source_proposal_id.into();
        Self {
            id: format!("review_decision_{source_proposal_id}_changes_requested"),
            version: EvidenceReviewDecisionVersion::default(),
            source_proposal_id,
            reviewer_role,
            decision_kind: EvidenceReviewDecisionKind::RequestChanges,
            decision_status: EvidenceReviewDecisionStatus::FinalizedChangesRequested,
            checklist: EvidenceReviewChecklist::phase_j_default(),
            findings: Vec::new(),
            blocking_issues: vec![
                "proposal changes requested by manual review decision".to_string()
            ],
            claim_boundary_decision: crate::evidence::ClaimBoundary::Level0DesignNote,
            notes,
        }
    }

    /// Return true when the decision can support candidate-only creation.
    pub fn approves_candidate_only(&self) -> bool {
        self.decision_kind == EvidenceReviewDecisionKind::ApproveForCandidateOnly
            && self.decision_status == EvidenceReviewDecisionStatus::FinalizedCandidateOnly
            && self.reviewer_role.is_human_review_role()
            && self.checklist.required_items_satisfied()
            && self.blocking_issues.is_empty()
    }
}

/// Validate a review decision.
pub fn validate_evidence_review_decision(
    decision: &EvidenceReviewDecision,
) -> EvidenceReviewReport {
    let mut blocking_issues = Vec::new();
    if decision.id.trim().is_empty() {
        blocking_issues.push("review decision id is empty".to_string());
    }
    if decision.source_proposal_id.trim().is_empty() {
        blocking_issues.push("source proposal id is empty".to_string());
    }
    if matches!(
        decision.decision_kind,
        EvidenceReviewDecisionKind::ApproveForCandidateOnly
            | EvidenceReviewDecisionKind::ApproveForFutureAppendPreview
    ) {
        if !decision.reviewer_role.is_human_review_role() {
            blocking_issues
                .push("AutomatedPolicyCheck alone cannot approve candidate creation".to_string());
        }
        if !decision.checklist.required_items_satisfied() {
            blocking_issues.push(format!(
                "required checklist items are not satisfied: {:?}",
                decision.checklist.unsatisfied_required_item_ids()
            ));
        }
    }
    scan_review_text(decision, &mut blocking_issues);
    let valid = blocking_issues.is_empty();
    EvidenceReviewReport {
        valid,
        decision_id: decision.id.clone(),
        blocking_issues,
        notes: vec!["manual review decision is not accepted evidence".to_string()],
    }
}

/// Review one evidence append proposal with an explicit decision kind.
pub fn review_evidence_append_proposal(
    proposal: &crate::external_runner::EvidenceAppendProposal,
    reviewer_role: EvidenceReviewerRole,
    decision_kind: EvidenceReviewDecisionKind,
    checklist: EvidenceReviewChecklist,
) -> Result<EvidenceReviewDecision> {
    match decision_kind {
        EvidenceReviewDecisionKind::ApproveForCandidateOnly => {
            EvidenceReviewDecision::approve_for_candidate_only(
                reviewer_role,
                proposal.id.clone(),
                checklist,
            )
        }
        EvidenceReviewDecisionKind::Reject => Ok(EvidenceReviewDecision::reject(
            reviewer_role,
            proposal.id.clone(),
            vec!["proposal rejected by manual review decision".to_string()],
        )),
        EvidenceReviewDecisionKind::RequestChanges => Ok(EvidenceReviewDecision::request_changes(
            reviewer_role,
            proposal.id.clone(),
            vec!["proposal requires changes before candidate creation".to_string()],
        )),
        EvidenceReviewDecisionKind::ApproveForFutureAppendPreview => {
            let mut decision = EvidenceReviewDecision::approve_for_candidate_only(
                reviewer_role,
                proposal.id.clone(),
                checklist,
            )?;
            decision.id = format!("review_decision_{}_append_preview", proposal.id);
            decision.decision_kind = EvidenceReviewDecisionKind::ApproveForFutureAppendPreview;
            Ok(decision)
        }
    }
}

/// Serialize a review decision to pretty JSON.
pub fn serialize_evidence_review_decision_json(
    decision: &EvidenceReviewDecision,
) -> Result<String> {
    serde_json::to_string_pretty(decision).map_err(|error| {
        ZkBenchError::serialization("serialize_evidence_review_decision_json", error.to_string())
    })
}

/// Deserialize a review decision from JSON.
pub fn deserialize_evidence_review_decision_json(json: &str) -> Result<EvidenceReviewDecision> {
    serde_json::from_str(json).map_err(|error| {
        ZkBenchError::deserialization(
            "deserialize_evidence_review_decision_json",
            error.to_string(),
        )
    })
}

/// Serialize a review checklist to pretty JSON.
pub fn serialize_evidence_review_checklist_json(
    checklist: &EvidenceReviewChecklist,
) -> Result<String> {
    serde_json::to_string_pretty(checklist).map_err(|error| {
        ZkBenchError::serialization(
            "serialize_evidence_review_checklist_json",
            error.to_string(),
        )
    })
}

/// Deserialize a review checklist from JSON.
pub fn deserialize_evidence_review_checklist_json(json: &str) -> Result<EvidenceReviewChecklist> {
    serde_json::from_str(json).map_err(|error| {
        ZkBenchError::deserialization(
            "deserialize_evidence_review_checklist_json",
            error.to_string(),
        )
    })
}

/// Build the default Phase J checklist.
pub fn build_default_evidence_review_checklist() -> EvidenceReviewChecklist {
    EvidenceReviewChecklist::phase_j_default()
}

fn scan_review_text(decision: &EvidenceReviewDecision, blocking_issues: &mut Vec<String>) {
    for (index, note) in decision.notes.iter().enumerate() {
        if crate::external_runner::contains_forbidden_claim_text(note) {
            blocking_issues.push(format!("decision notes[{index}] contain a forbidden claim"));
        }
    }
    for (index, issue) in decision.blocking_issues.iter().enumerate() {
        if crate::external_runner::contains_forbidden_claim_text(issue) {
            blocking_issues.push(format!(
                "decision blocking_issues[{index}] contain a forbidden claim"
            ));
        }
    }
    for (index, finding) in decision.findings.iter().enumerate() {
        if crate::external_runner::contains_forbidden_claim_text(&finding.message) {
            blocking_issues.push(format!(
                "decision findings[{index}] contain a forbidden claim"
            ));
        }
    }
    for (index, item) in decision.checklist.items.iter().enumerate() {
        for (note_index, note) in item.notes.iter().enumerate() {
            if crate::external_runner::contains_forbidden_claim_text(note) {
                blocking_issues.push(format!(
                    "decision checklist items[{index}].notes[{note_index}] contain a forbidden claim"
                ));
            }
        }
    }
}

fn phase_j_default_item_specs() -> Vec<(&'static str, &'static str)> {
    vec![
        ("source_proposal_exists", "source proposal exists"),
        (
            "source_proposal_status_reviewable",
            "source proposal status is PendingReview or Draft",
        ),
        (
            "source_normalized_draft_exists",
            "source normalized draft exists",
        ),
        ("validation_report_exists", "validation report exists"),
        ("artifact_digests_present", "artifact digests are present"),
        ("provenance_fields_present", "provenance fields are present"),
        ("no_official_benchmark_claim", "no official benchmark claim"),
        ("no_formal_evidence_claim", "no formal evidence claim"),
        (
            "no_proof_system_soundness_claim",
            "no proof-system soundness claim",
        ),
        (
            "no_level2_actual_claim_requested",
            "no Level2+ actual claim requested",
        ),
        (
            "local_only_claim_boundary_preserved",
            "local-only claim boundary preserved",
        ),
        (
            "candidate_metrics_not_score_inputs",
            "candidate metrics are not score inputs",
        ),
        ("reviewer_notes_present", "reviewer notes present"),
        (
            "future_manual_append_required",
            "future manual append required",
        ),
    ]
}
