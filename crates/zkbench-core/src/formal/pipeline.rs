//! Inert formal-lane pipeline wiring over mutation × surface cross-product.
//!
//! Derives a formal property assertion template and evaluates it through the
//! shipped `NoopFormalVerifier`. No real formal tool is invoked.

use crate::dsl::SurfaceSpec;
use crate::error::Result;
use crate::evidence::ClaimBoundary;
use crate::formal::{
    derive_formal_property_assertion_template, FormalLane, FormalLaneOutcome,
    FormalLaneProofStatus, NoopFormalVerifier,
};
use crate::mutation::MutationClass;

/// Outcome of one inert formal-lane pipeline pass.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct FormalLanePipelineOutcome {
    /// Whether a template was derived for the mutation class and surface.
    pub template_derived: bool,
    /// Lane evaluation when a template was derived.
    pub evaluation: Option<FormalLaneOutcome>,
    /// Claim boundary for this pipeline pass.
    pub claim_boundary: ClaimBoundary,
}

/// Derive a formal property template when possible and evaluate it through the
/// noop formal lane.
pub fn evaluate_formal_lane_pipeline(
    mutation_class: MutationClass,
    surface: &SurfaceSpec,
) -> Result<FormalLanePipelineOutcome> {
    let template = derive_formal_property_assertion_template(mutation_class, surface);
    if let Some(assertion) = template {
        let lane = FormalLane::new(NoopFormalVerifier);
        let evaluation = lane.evaluate(&assertion)?;
        Ok(FormalLanePipelineOutcome {
            template_derived: true,
            claim_boundary: evaluation.claim_boundary,
            evaluation: Some(evaluation),
        })
    } else {
        Ok(FormalLanePipelineOutcome {
            template_derived: false,
            evaluation: None,
            claim_boundary: ClaimBoundary::Level0DesignNote,
        })
    }
}

/// Return true when the pipeline produced a `DeclaredOnly` formal lane outcome.
pub fn pipeline_outcome_is_declared_only(outcome: &FormalLanePipelineOutcome) -> bool {
    outcome
        .evaluation
        .as_ref()
        .is_some_and(|evaluation| evaluation.proof.status == FormalLaneProofStatus::DeclaredOnly)
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
        assert_eq!(outcome.claim_boundary, ClaimBoundary::Level0DesignNote);
        assert!(pipeline_outcome_is_declared_only(&outcome));
    }
}
