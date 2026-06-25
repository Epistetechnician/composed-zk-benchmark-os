//! Inert formal-lane pipeline wiring over mutation × surface cross-product.
//!
//! Derives a formal property assertion template and evaluates it through the
//! shipped `NoopFormalVerifier`. No real formal tool is invoked.

use crate::dsl::SurfaceSpec;
use crate::error::Result;
use crate::evidence::ClaimBoundary;
use crate::formal::{
    derive_formal_property_assertion_template, FormalLane, FormalLaneOutcome,
    FormalLaneProofStatus, FormalPropertyScopeKind, NoopFormalVerifier,
};
use crate::mutation::MutationClass;

/// Outcome of one inert formal-lane pipeline pass.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct FormalLanePipelineOutcome {
    /// Mutation class that produced this pipeline pass.
    pub mutation_class: MutationClass,
    /// Primary formal scope kind selected by the mutation × formal mapping.
    pub primary_formal_scope: FormalPropertyScopeKind,
    /// Whether a template was derived for the mutation class and surface.
    pub template_derived: bool,
    /// Lane evaluation when a template was derived.
    pub evaluation: Option<FormalLaneOutcome>,
    /// Proof status when a lane evaluation exists.
    pub proof_status: Option<FormalLaneProofStatus>,
    /// Reason a template was not derived.
    pub no_template_reason: Option<String>,
    /// Claim boundary for this pipeline pass.
    pub claim_boundary: ClaimBoundary,
    /// Mandatory nonclaims carried by this pipeline pass.
    pub nonclaims: Vec<String>,
}

/// Derive a formal property template when possible and evaluate it through the
/// noop formal lane.
pub fn evaluate_formal_lane_pipeline(
    mutation_class: MutationClass,
    surface: &SurfaceSpec,
) -> Result<FormalLanePipelineOutcome> {
    let profile = crate::formal::mutation_class_formal_stress(mutation_class);
    let template = derive_formal_property_assertion_template(mutation_class, surface);
    if let Some(assertion) = template {
        let lane = FormalLane::new(NoopFormalVerifier);
        let evaluation = lane.evaluate(&assertion)?;
        let proof_status = evaluation.proof.status;
        Ok(FormalLanePipelineOutcome {
            mutation_class,
            primary_formal_scope: profile.primary_formal_scope,
            template_derived: true,
            claim_boundary: evaluation.claim_boundary,
            evaluation: Some(evaluation),
            proof_status: Some(proof_status),
            no_template_reason: None,
            nonclaims: formal_pipeline_nonclaims(),
        })
    } else {
        Ok(FormalLanePipelineOutcome {
            mutation_class,
            primary_formal_scope: profile.primary_formal_scope,
            template_derived: false,
            evaluation: None,
            proof_status: None,
            no_template_reason: Some(no_template_reason(profile.primary_formal_scope)),
            claim_boundary: ClaimBoundary::Level0DesignNote,
            nonclaims: formal_pipeline_nonclaims(),
        })
    }
}

/// Return true when the pipeline produced a `DeclaredOnly` formal lane outcome.
pub fn pipeline_outcome_is_declared_only(outcome: &FormalLanePipelineOutcome) -> bool {
    outcome.proof_status == Some(FormalLaneProofStatus::DeclaredOnly)
}

/// Mandatory nonclaims attached to every formal pipeline outcome.
pub fn formal_pipeline_nonclaims() -> Vec<String> {
    vec![
        "The formal pipeline is local observability metadata only and is not proof.".to_string(),
        "A declared-only formal lane outcome is not a machine-checked proof, accepted evidence, benchmark evidence, ZK backend performance evidence, or semantic correctness.".to_string(),
        "The shipped pipeline uses NoopFormalVerifier and invokes no real formal tool.".to_string(),
    ]
}

fn no_template_reason(scope: FormalPropertyScopeKind) -> String {
    match scope {
        FormalPropertyScopeKind::TransitionGuard => {
            "surface has no transition guard construct for this mutation class".to_string()
        }
        FormalPropertyScopeKind::Invariant => {
            "surface has no invariant construct for this mutation class".to_string()
        }
        FormalPropertyScopeKind::LoopBound => {
            "surface has no loop-bound construct for this mutation class".to_string()
        }
        FormalPropertyScopeKind::Machine => {
            "machine-scoped template was unexpectedly unavailable".to_string()
        }
        FormalPropertyScopeKind::NotApplicable => {
            "mutation class has no applicable formal scope".to_string()
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::generator::{generate_instance, GeneratorConfig, InstanceParams};
    use crate::mutation::MutationClass;

    #[test]
    fn pipeline_evaluates_derived_template_as_declared_only() {
        let instance = generate_instance(
            GeneratorConfig::bounded_counter_loop(),
            InstanceParams::default(),
        )
        .expect("instance should generate");
        let outcome = evaluate_formal_lane_pipeline(
            MutationClass::MissingConstraints,
            &instance.surface_spec,
        )
        .expect("pipeline should evaluate");
        assert!(outcome.template_derived);
        assert_eq!(
            outcome.primary_formal_scope,
            FormalPropertyScopeKind::TransitionGuard
        );
        assert_eq!(outcome.claim_boundary, ClaimBoundary::Level0DesignNote);
        assert_eq!(
            outcome.proof_status,
            Some(FormalLaneProofStatus::DeclaredOnly)
        );
        assert!(outcome.no_template_reason.is_none());
        assert!(outcome
            .nonclaims
            .iter()
            .any(|item| item.contains("not proof")));
        assert!(pipeline_outcome_is_declared_only(&outcome));
    }

    #[test]
    fn pipeline_preserves_no_template_reason() {
        let instance =
            generate_instance(GeneratorConfig::branching_fsm(), InstanceParams::default())
                .expect("instance should generate");
        let outcome = evaluate_formal_lane_pipeline(
            MutationClass::InvariantWeakening,
            &instance.surface_spec,
        )
        .expect("pipeline should evaluate");
        assert!(!outcome.template_derived);
        assert_eq!(
            outcome.primary_formal_scope,
            FormalPropertyScopeKind::Invariant
        );
        assert_eq!(outcome.claim_boundary, ClaimBoundary::Level0DesignNote);
        assert_eq!(outcome.proof_status, None);
        assert!(outcome
            .no_template_reason
            .as_deref()
            .is_some_and(|reason| reason.contains("no invariant")));
        assert!(!pipeline_outcome_is_declared_only(&outcome));
    }
}
