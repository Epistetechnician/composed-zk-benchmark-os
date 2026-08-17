//! Fail-closed Astral execution-eligibility gate.
//!
//! A positive result means only that a separately authorized human review may
//! consider a future run. This module never authorizes, launches, or opens an
//! assessment.

use serde::{Deserialize, Serialize};

use crate::evidence::ClaimBoundary;

use super::custody_replay_manifest::{
    compute_fresh_actor_custody_replay_manifest_digest, FreshActorCustodyReplayManifest,
};

/// State slice governed by this execution gate.
pub const ASTRAL_EXECUTION_ELIGIBILITY_GATE_STATE_SLICE: &str =
    "astral-execution-eligibility-gate-v37";

/// Declared actor readiness. These are declarations consumed by the gate, not
/// independent verification of the underlying actor or checkpoint.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum AstralActorReadinessDeclaration {
    /// A fresh actor and instrument are declared available.
    DeclaredFreshInstrumentedActor,
    /// No fresh actor is available.
    NoFreshActor,
    /// The actor is reserved by an earlier protocol.
    ReservedActor,
}

/// Declared instrument readiness.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum AstralInstrumentReadinessDeclaration {
    /// A per-layer intervention surface is declared available.
    DeclaredPerLayerInterventionSurface,
    /// Only final-embedding observation is available.
    FinalEmbeddingOnly,
    /// No eligible intervention surface is available.
    MissingInstrument,
}

/// Declared review disposition.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum AstralReviewDisposition {
    /// Independent review is recorded for this future-eligibility request.
    IndependentReviewRecorded,
    /// Review is not complete.
    Pending,
    /// Review rejected the request.
    Rejected,
}

/// Request for a future Astral run eligibility decision.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct AstralExecutionEligibilityRequest {
    /// Stable request identifier.
    pub request_id: String,
    /// Required state slice.
    pub state_slice: String,
    /// Digest of the V36 replay manifest under review.
    pub replay_manifest_digest: String,
    /// Declared actor readiness.
    pub actor_readiness: AstralActorReadinessDeclaration,
    /// Declared instrument readiness.
    pub instrument_readiness: AstralInstrumentReadinessDeclaration,
    /// Declared independent review disposition.
    pub review_disposition: AstralReviewDisposition,
    /// Reviewer identity, never a credential.
    pub reviewer_id: String,
    /// Requested claim ceiling.
    pub requested_claim_boundary: ClaimBoundary,
    /// Whether the nonclaim checklist was acknowledged.
    pub nonclaims_acknowledged: bool,
    /// Assessment must remain unopened.
    pub assessment_opened: bool,
    /// External execution must remain disabled at this gate.
    pub external_execution_disabled: bool,
}

/// Gate decision.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum AstralExecutionEligibilityDecision {
    /// The request cannot proceed to human authorization review.
    Denied,
    /// The request may be considered by a separate human authorization step.
    EligibleForSeparateHumanAuthorization,
}

/// Gate issue.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct AstralExecutionEligibilityIssue {
    /// Field path.
    pub path: String,
    /// Human-readable reason.
    pub message: String,
}

/// Gate evaluation result.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct AstralExecutionEligibilityEvaluation {
    /// Decision.
    pub decision: AstralExecutionEligibilityDecision,
    /// Issues; empty only for eligibility.
    pub issues: Vec<AstralExecutionEligibilityIssue>,
    /// Claim ceiling remains design-only.
    pub claim_boundary: ClaimBoundary,
    /// Always false: this gate cannot open execution.
    pub assessment_opened: bool,
}

/// Evaluate a future-run eligibility request against a V36 manifest.
pub fn evaluate_astral_execution_eligibility(
    request: &AstralExecutionEligibilityRequest,
    manifest: &FreshActorCustodyReplayManifest,
) -> AstralExecutionEligibilityEvaluation {
    let mut issues = Vec::new();
    if request.request_id.trim().is_empty() {
        issues.push(issue("request_id", "request id is required"));
    }
    if request.state_slice != ASTRAL_EXECUTION_ELIGIBILITY_GATE_STATE_SLICE {
        issues.push(issue(
            "state_slice",
            "request state slice does not match V37",
        ));
    }
    if request.reviewer_id.trim().is_empty() {
        issues.push(issue("reviewer_id", "reviewer identity is required"));
    }
    if request.actor_readiness != AstralActorReadinessDeclaration::DeclaredFreshInstrumentedActor {
        issues.push(issue(
            "actor_readiness",
            "a fresh non-reserved actor declaration is required",
        ));
    }
    if request.instrument_readiness
        != AstralInstrumentReadinessDeclaration::DeclaredPerLayerInterventionSurface
    {
        issues.push(issue(
            "instrument_readiness",
            "a declared per-layer intervention surface is required",
        ));
    }
    if request.review_disposition != AstralReviewDisposition::IndependentReviewRecorded {
        issues.push(issue(
            "review_disposition",
            "independent review must be recorded before eligibility",
        ));
    }
    if request.requested_claim_boundary != ClaimBoundary::Level0DesignNote {
        issues.push(issue(
            "requested_claim_boundary",
            "V37 eligibility remains Level0DesignNote",
        ));
    }
    if !request.nonclaims_acknowledged {
        issues.push(issue(
            "nonclaims_acknowledged",
            "explicit nonclaim acknowledgement is required",
        ));
    }
    if request.assessment_opened {
        issues.push(issue(
            "assessment_opened",
            "eligibility gate cannot accept an opened assessment",
        ));
    }
    if !request.external_execution_disabled {
        issues.push(issue(
            "external_execution_disabled",
            "external execution must remain disabled at V37",
        ));
    }

    let manifest_validation = manifest.validate();
    if !manifest_validation.valid {
        issues.push(issue(
            "replay_manifest",
            "V36 replay manifest failed validation",
        ));
    }
    if manifest.entries.is_empty() {
        issues.push(issue(
            "replay_manifest.entries",
            "an accepted custody packet is required",
        ));
    }
    match compute_fresh_actor_custody_replay_manifest_digest(manifest) {
        Ok(expected) if expected.hex_digest == request.replay_manifest_digest => {}
        Ok(_) => issues.push(issue(
            "replay_manifest_digest",
            "request digest does not match the V36 manifest",
        )),
        Err(_) => issues.push(issue(
            "replay_manifest_digest",
            "manifest digest could not be recomputed",
        )),
    }

    AstralExecutionEligibilityEvaluation {
        decision: if issues.is_empty() {
            AstralExecutionEligibilityDecision::EligibleForSeparateHumanAuthorization
        } else {
            AstralExecutionEligibilityDecision::Denied
        },
        issues,
        claim_boundary: ClaimBoundary::Level0DesignNote,
        assessment_opened: false,
    }
}

fn issue(path: &str, message: &str) -> AstralExecutionEligibilityIssue {
    AstralExecutionEligibilityIssue {
        path: path.to_string(),
        message: message.to_string(),
    }
}
