//! Formal lane interface stub.
//!
//! Inert seam for the "formal hooks" half of the SOTA wedge named in
//! `AGENTS.md`. Mirrors the `AttestationVerifier` pattern from
//! `hsai-attestation`: a trait, a reference verifier that always returns
//! "declared only", and a `FormalLane` that wraps it.
//!
//! Every `FormalLaneProof` produced here is `ClaimBoundary::Level0DesignNote`.
//! A `DeclaredOnly` proof is not proof, not benchmark evidence, not accepted
//! evidence, not formal evidence, and not evidence that any formal tool was
//! run. The seam's only value is establishing the attach point for a future
//! implementation phase that would integrate with a real formal tool
//! (clean, zkLean, Garden, Coq, Lean, Rocq, F*, Dafny, etc. — all out of
//! scope here).

use crate::error::ZkBenchError;
use crate::evidence::ClaimBoundary;

/// Scope at which a formal property is asserted.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum FormalPropertyScope {
    /// Property over a single transition's guard.
    TransitionGuard {
        /// Transition id.
        transition_id: String,
    },
    /// Property over a single invariant.
    Invariant {
        /// Invariant id.
        invariant_id: String,
    },
    /// Property over a single loop's bound.
    LoopBound {
        /// Loop id.
        loop_id: String,
    },
    /// Property over the whole machine.
    Machine,
}

/// A declared formal property assertion. Declaring one is not proving one.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct FormalPropertyAssertion {
    /// Assertion id.
    pub id: String,
    /// Scope.
    pub scope: FormalPropertyScope,
    /// Human-readable property statement.
    pub statement: String,
    /// Bound machine id.
    pub bound_machine_id: String,
    /// Mandatory nonclaims.
    pub nonclaims: Vec<String>,
}

impl FormalPropertyAssertion {
    /// Return the mandatory nonclaims every formal property assertion must
    /// carry. These prevent the assertion from being reinterpreted as a proof.
    pub fn mandatory_nonclaims() -> Vec<String> {
        vec![
            "A declared formal property is not a proof.".to_string(),
            "A formal property statement is not a machine-checked proof.".to_string(),
            "This assertion establishes intent only, not verification.".to_string(),
        ]
    }
}

/// Status of a formal lane proof attempt.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum FormalLaneProofStatus {
    /// Property was declared but no proof was attempted. The only status the
    /// shipped `NoopFormalVerifier` ever returns.
    DeclaredOnly,
    /// A proof was attempted but not completed. Reserved for a future
    /// implementation phase.
    ProofAttempted,
    /// A scoped machine-checked proof was produced. Reserved for a future
    /// implementation phase that integrates with a real formal tool.
    MachineCheckedScoped,
    /// The proof was independently reproduced. Reserved for a future
    /// implementation phase.
    IndependentlyReproduced,
}

impl FormalLaneProofStatus {
    /// Maximum claim boundary justified by this status. The shipped
    /// `DeclaredOnly` status caps at `Level0DesignNote`; higher statuses
    /// require a future implementation phase.
    pub fn claim_boundary(self) -> ClaimBoundary {
        match self {
            Self::DeclaredOnly => ClaimBoundary::Level0DesignNote,
            Self::ProofAttempted => ClaimBoundary::Level0DesignNote,
            Self::MachineCheckedScoped => ClaimBoundary::Level5MachineCheckedScopedProof,
            Self::IndependentlyReproduced => ClaimBoundary::Level6IndependentlyReproducedEvidence,
        }
    }
}

/// A formal lane proof record. Produced by a `FormalVerifier`.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct FormalLaneProof {
    /// Assertion being proven (or declared).
    pub assertion: FormalPropertyAssertion,
    /// Proof status.
    pub status: FormalLaneProofStatus,
    /// Claim boundary justified by this proof.
    pub claim_boundary: ClaimBoundary,
    /// Notes (free-form, must carry mandatory nonclaims for non-proofs).
    pub notes: Vec<String>,
}

/// Errors a formal verifier can return.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum FormalLaneError {
    /// Assertion was malformed.
    MalformedAssertion {
        /// Field path.
        path: String,
        /// Reason.
        reason: String,
    },
    /// Verifier cannot handle the requested scope.
    UnsupportedScope {
        /// Reason.
        reason: String,
    },
}

/// Trait implemented by formal verifiers. Mirrors `AttestationVerifier` in
/// `hsai-attestation`: a single `verify` method that takes an assertion and
/// returns a proof record or an error.
pub trait FormalVerifier {
    /// Verify (or, for stubs, declare) `assertion`. Returns the lane's own
    /// error type so callers can distinguish formal-lane failures from
    /// infrastructure failures.
    fn verify(
        &self,
        assertion: &FormalPropertyAssertion,
    ) -> std::result::Result<FormalLaneProof, FormalLaneError>;
}

/// Reference verifier that always returns `DeclaredOnly`. Never attempts a
/// proof, never escalates above `Level0DesignNote`, never integrates with any
/// real formal tool.
#[derive(Debug, Default, Clone, Copy, PartialEq, Eq)]
pub struct NoopFormalVerifier;

impl FormalVerifier for NoopFormalVerifier {
    fn verify(
        &self,
        assertion: &FormalPropertyAssertion,
    ) -> std::result::Result<FormalLaneProof, FormalLaneError> {
        if assertion.id.trim().is_empty() {
            return Err(FormalLaneError::MalformedAssertion {
                path: "id".to_string(),
                reason: "assertion id must be non-empty".to_string(),
            });
        }
        if assertion.statement.trim().is_empty() {
            return Err(FormalLaneError::MalformedAssertion {
                path: "statement".to_string(),
                reason: "assertion statement must be non-empty".to_string(),
            });
        }
        if assertion.bound_machine_id.trim().is_empty() {
            return Err(FormalLaneError::MalformedAssertion {
                path: "bound_machine_id".to_string(),
                reason: "bound machine id must be non-empty".to_string(),
            });
        }
        Ok(FormalLaneProof {
            assertion: assertion.clone(),
            status: FormalLaneProofStatus::DeclaredOnly,
            claim_boundary: FormalLaneProofStatus::DeclaredOnly.claim_boundary(),
            notes: vec![
                "No formal proof was attempted.".to_string(),
                "A declared formal property is not a proof.".to_string(),
                "This stub exists to establish the formal-lane seam only.".to_string(),
            ],
        })
    }
}

/// A formal lane wraps a verifier and exposes a single `evaluate` entry point.
#[derive(Debug, Clone)]
pub struct FormalLane<V: FormalVerifier> {
    /// Wrapped verifier.
    pub verifier: V,
}

pub mod cross_product;
pub mod pipeline;

pub use cross_product::{
    derive_formal_property_assertion_template, mandatory_cross_product_nonclaims,
    mutation_class_formal_stress, FormalPropertyScopeKind, MutationFormalStressProfile,
    CROSS_PRODUCT_CLAIM_BOUNDARY,
};
pub use pipeline::{
    evaluate_formal_lane_pipeline, formal_pipeline_nonclaims, pipeline_outcome_is_declared_only,
    FormalLanePipelineOutcome,
};

impl<V: FormalVerifier> FormalLane<V> {
    /// Construct a new lane wrapping `verifier`.
    pub fn new(verifier: V) -> Self {
        Self { verifier }
    }

    /// Evaluate `assertion`, returning a `FormalLaneOutcome` carrying the
    /// proof, claim boundary, and mandatory nonclaims.
    pub fn evaluate(
        &self,
        assertion: &FormalPropertyAssertion,
    ) -> crate::error::Result<FormalLaneOutcome> {
        let proof = self.verifier.verify(assertion).map_err(|lane_error| {
            ZkBenchError::evidence_ledger(
                "formal_lane.verify",
                match lane_error {
                    FormalLaneError::MalformedAssertion { path, reason } => {
                        format!("malformed assertion at {path}: {reason}")
                    }
                    FormalLaneError::UnsupportedScope { reason } => {
                        format!("unsupported scope: {reason}")
                    }
                },
            )
        })?;
        let claim_boundary = proof.claim_boundary;
        let nonclaims = mandatory_lane_outcome_nonclaims();
        Ok(FormalLaneOutcome {
            proof,
            claim_boundary,
            nonclaims,
        })
    }
}

/// Outcome of a formal lane evaluation. Pure data — callers inspect it; the
/// lane does not emit a `ClaimEnvelope` directly.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct FormalLaneOutcome {
    /// Proof record.
    pub proof: FormalLaneProof,
    /// Claim boundary (always `Level0DesignNote` under `NoopFormalVerifier`).
    pub claim_boundary: ClaimBoundary,
    /// Mandatory nonclaims.
    pub nonclaims: Vec<String>,
}

/// Mandatory nonclaims attached to every formal lane outcome.
pub fn mandatory_lane_outcome_nonclaims() -> Vec<String> {
    vec![
        "Formal lane evaluation under the shipped NoopFormalVerifier is declared-only and is not proof.".to_string(),
        "The formal-lane seam exists to establish an attach point for a future implementation phase; no formal tool was run.".to_string(),
        "A declared formal property is not a machine-checked proof, not benchmark evidence, not accepted evidence, not ZK backend performance evidence, and not semantic correctness.".to_string(),
    ]
}

#[cfg(test)]
mod tests {
    use super::*;

    fn sample_assertion() -> FormalPropertyAssertion {
        FormalPropertyAssertion {
            id: "prop_transition_guard_t0".to_string(),
            scope: FormalPropertyScope::TransitionGuard {
                transition_id: "t0".to_string(),
            },
            statement: "transition t0 guard holds for all reachable states".to_string(),
            bound_machine_id: "m0".to_string(),
            nonclaims: FormalPropertyAssertion::mandatory_nonclaims(),
        }
    }

    #[test]
    fn noop_verifier_returns_declared_only() {
        let verifier = NoopFormalVerifier;
        let assertion = sample_assertion();
        let proof = verifier
            .verify(&assertion)
            .expect("noop verifier should succeed");
        assert_eq!(proof.status, FormalLaneProofStatus::DeclaredOnly);
        assert_eq!(proof.claim_boundary, ClaimBoundary::Level0DesignNote);
    }

    #[test]
    fn noop_verifier_never_returns_high_status() {
        let verifier = NoopFormalVerifier;
        let assertion = sample_assertion();
        let proof = verifier
            .verify(&assertion)
            .expect("noop verifier should succeed");
        assert_ne!(proof.status, FormalLaneProofStatus::MachineCheckedScoped);
        assert_ne!(proof.status, FormalLaneProofStatus::IndependentlyReproduced);
    }

    #[test]
    fn noop_verifier_rejects_empty_id() {
        let verifier = NoopFormalVerifier;
        let mut assertion = sample_assertion();
        assertion.id = "  ".to_string();
        let err = verifier
            .verify(&assertion)
            .expect_err("empty id should be rejected");
        assert!(matches!(err, FormalLaneError::MalformedAssertion { .. }));
    }

    #[test]
    fn formal_lane_evaluate_carries_mandatory_nonclaims() {
        let lane = FormalLane::new(NoopFormalVerifier);
        let assertion = sample_assertion();
        let outcome = lane.evaluate(&assertion).expect("evaluate should succeed");
        assert_eq!(outcome.claim_boundary, ClaimBoundary::Level0DesignNote);
        assert!(outcome
            .nonclaims
            .iter()
            .any(|n| n.contains("declared-only")));
        assert!(outcome
            .nonclaims
            .iter()
            .any(|n| n.contains("no formal tool was run")));
    }

    #[test]
    fn formal_property_assertion_mandatory_nonclaims_include_not_a_proof() {
        let nonclaims = FormalPropertyAssertion::mandatory_nonclaims();
        assert!(nonclaims.iter().any(|n| n.contains("not a proof")));
    }

    #[test]
    fn formal_lane_proof_status_has_exactly_four_variants() {
        let all = [
            FormalLaneProofStatus::DeclaredOnly,
            FormalLaneProofStatus::ProofAttempted,
            FormalLaneProofStatus::MachineCheckedScoped,
            FormalLaneProofStatus::IndependentlyReproduced,
        ];
        assert_eq!(all.len(), 4);
    }

    #[test]
    fn formal_property_scope_has_exactly_four_variants() {
        let all = [
            FormalPropertyScope::TransitionGuard {
                transition_id: String::new(),
            },
            FormalPropertyScope::Invariant {
                invariant_id: String::new(),
            },
            FormalPropertyScope::LoopBound {
                loop_id: String::new(),
            },
            FormalPropertyScope::Machine,
        ];
        assert_eq!(all.len(), 4);
    }
}
