//! Re-export Phase J review primitives for external-runner proposal state.
//!
//! The external-runner boundary stores review metadata, but review policy now
//! lives in `crate::evidence::review` so append proposals, candidates, and
//! previews share one checklist and decision model.

pub use crate::evidence::review::{
    build_default_evidence_review_checklist, deserialize_evidence_review_checklist_json,
    deserialize_evidence_review_decision_json, review_evidence_append_proposal,
    serialize_evidence_review_checklist_json, serialize_evidence_review_decision_json,
    validate_evidence_review_decision, EvidenceReviewChecklist, EvidenceReviewChecklistItem,
    EvidenceReviewDecision, EvidenceReviewDecisionId, EvidenceReviewDecisionKind,
    EvidenceReviewDecisionStatus, EvidenceReviewDecisionVersion, EvidenceReviewFinding,
    EvidenceReviewFindingSeverity, EvidenceReviewPolicy, EvidenceReviewReport,
    EvidenceReviewRequirement, EvidenceReviewerRole,
};
