//! Mutation × formal cross-product mapping.
//!
//! The SOTA wedge — *"semantic benchmark generation with formal hooks and
//! adversarial mutation scoring"* — is only differentiated when the two halves
//! are connected. This module maps each of the 14 declared `MutationClass`
//! variants to the `FormalPropertyScope` it most directly stress-tests, and
//! derives a `FormalPropertyAssertion` template from an existing `SurfaceSpec`
//! when the surface contains a matching construct.
//!
//! All output is local metadata capped at `Level0DesignNote`. The mapping is
//! not proof, not benchmark evidence, not accepted evidence, not formal
//! evidence, and not evidence that any formal tool was run or that any
//! mutation would be detected by a real backend. The mapping's only value is
//! documenting which formal property each mutation class *would* stress-test
//! if a real formal lane were attached in a future phase.

use crate::evidence::ClaimBoundary;
use crate::formal::{FormalPropertyAssertion, FormalPropertyScope};
use crate::mutation::MutationClass;

/// Lightweight scope discriminator used by the mapping table. The full
/// `FormalPropertyScope` carries ids; this enum carries only the scope *kind*.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum FormalPropertyScopeKind {
    /// Property over a single transition's guard.
    TransitionGuard,
    /// Property over a single invariant.
    Invariant,
    /// Property over a single loop's bound.
    LoopBound,
    /// Property over the whole machine.
    Machine,
    /// Mutation has no formal analog in the current mapping. Reserved for
    /// future mutation classes; none of the 14 use it today.
    NotApplicable,
}

/// Stress profile mapping one `MutationClass` to a formal scope kind.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct MutationFormalStressProfile {
    /// Mutation class this profile describes.
    pub mutation_class: MutationClass,
    /// Primary formal scope kind this mutation stress-tests.
    pub primary_formal_scope: FormalPropertyScopeKind,
    /// Why this scope is the primary target.
    pub rationale: String,
    /// Mandatory nonclaims.
    pub nonclaims: Vec<String>,
}

/// Return the deterministic stress profile for `mutation_class`. Every one of
/// the 14 declared `MutationClass` variants has a profile; none returns
/// `NotApplicable` in the current mapping.
pub fn mutation_class_formal_stress(mutation_class: MutationClass) -> MutationFormalStressProfile {
    let (primary_formal_scope, rationale) = match mutation_class {
        MutationClass::MissingConstraints => (
            FormalPropertyScopeKind::TransitionGuard,
            "Removing a guard stress-tests whether the formal model enforces it.",
        ),
        MutationClass::CorruptedGuards => (
            FormalPropertyScopeKind::TransitionGuard,
            "Inverting a guard tests transition-guard soundness.",
        ),
        MutationClass::BadCounters => (
            FormalPropertyScopeKind::TransitionGuard,
            "Counter drift tests whether guards over counters hold.",
        ),
        MutationClass::StaleStateReads => (
            FormalPropertyScopeKind::TransitionGuard,
            "Ordering violation tests transition sequencing.",
        ),
        MutationClass::InvalidUnrollBounds => (
            FormalPropertyScopeKind::LoopBound,
            "Bound corruption tests loop-bound soundness.",
        ),
        MutationClass::NondeterministicTransitionInjection => (
            FormalPropertyScopeKind::Machine,
            "Injected transitions test machine-level determinism.",
        ),
        MutationClass::RecursionEnvelopeMismatch => (
            FormalPropertyScopeKind::Machine,
            "Envelope mismatch tests recursion-envelope integrity.",
        ),
        MutationClass::PublicPrivateBoundaryMismatch => (
            FormalPropertyScopeKind::Machine,
            "Boundary violation tests witness partitioning.",
        ),
        MutationClass::WitnessAliasing => (
            FormalPropertyScopeKind::Machine,
            "Aliasing tests witness-disjointness properties.",
        ),
        MutationClass::InvariantWeakening => (
            FormalPropertyScopeKind::Invariant,
            "Weakening tests whether the invariant is actually enforced.",
        ),
        MutationClass::InvariantStrengthening => (
            FormalPropertyScopeKind::Invariant,
            "Strengthening tests invariant tightness.",
        ),
        MutationClass::ObservationOmission => (
            FormalPropertyScopeKind::Machine,
            "Omission tests public-output commitment.",
        ),
        MutationClass::SemanticNoOpDrift => (
            FormalPropertyScopeKind::TransitionGuard,
            "No-op drift tests action-effect soundness.",
        ),
        MutationClass::TraceOrderingCorruption => (
            FormalPropertyScopeKind::TransitionGuard,
            "Ordering corruption tests transition sequencing.",
        ),
    };
    MutationFormalStressProfile {
        mutation_class,
        primary_formal_scope,
        rationale: rationale.to_string(),
        nonclaims: mandatory_cross_product_nonclaims(),
    }
}

/// Mandatory nonclaims attached to every cross-product profile and derived
/// assertion template.
pub fn mandatory_cross_product_nonclaims() -> Vec<String> {
    vec![
        "This mutation-to-formal mapping is local metadata only and is not proof.".to_string(),
        "The mapping documents which formal property each mutation class would stress-test; it does not prove any property was verified.".to_string(),
        "A derived formal property assertion template is not a formal property statement, not a machine-checked proof, not benchmark evidence, and not accepted evidence.".to_string(),
    ]
}

/// Derive a `FormalPropertyAssertion` template for `mutation_class` over
/// `surface`. Returns `Some(template)` when the surface contains a construct
/// matching the profile's primary scope, and `None` otherwise. The template
/// carries `ClaimBoundary::Level0DesignNote` and mandatory nonclaims.
pub fn derive_formal_property_assertion_template(
    mutation_class: MutationClass,
    surface: &crate::dsl::SurfaceSpec,
) -> Option<FormalPropertyAssertion> {
    let profile = mutation_class_formal_stress(mutation_class);
    let machine_id = surface.machine.id.clone();
    let scope = match profile.primary_formal_scope {
        FormalPropertyScopeKind::TransitionGuard => {
            let transition = surface.machine.transitions.first()?;
            FormalPropertyScope::TransitionGuard {
                transition_id: transition.id.clone(),
            }
        }
        FormalPropertyScopeKind::Invariant => {
            let invariant = surface.machine.invariants.first()?;
            FormalPropertyScope::Invariant {
                invariant_id: invariant.id.clone(),
            }
        }
        FormalPropertyScopeKind::LoopBound => {
            let entry = surface.machine.loops.first()?;
            FormalPropertyScope::LoopBound {
                loop_id: entry.id.clone(),
            }
        }
        FormalPropertyScopeKind::Machine => FormalPropertyScope::Machine,
        FormalPropertyScopeKind::NotApplicable => return None,
    };
    let statement = format!(
        "{} stress-tests the {:?} formal scope on machine {}",
        format!("{:?}", mutation_class).to_ascii_lowercase(),
        profile.primary_formal_scope,
        machine_id
    );
    Some(FormalPropertyAssertion {
        id: format!(
            "template_{}_{}",
            scope_kind_slug(profile.primary_formal_scope),
            machine_id
        ),
        scope,
        statement,
        bound_machine_id: machine_id,
        nonclaims: mandatory_cross_product_nonclaims(),
    })
}

/// Convert a scope kind to a deterministic id slug.
fn scope_kind_slug(kind: FormalPropertyScopeKind) -> &'static str {
    match kind {
        FormalPropertyScopeKind::TransitionGuard => "transition_guard",
        FormalPropertyScopeKind::Invariant => "invariant",
        FormalPropertyScopeKind::LoopBound => "loop_bound",
        FormalPropertyScopeKind::Machine => "machine",
        FormalPropertyScopeKind::NotApplicable => "not_applicable",
    }
}

/// Claim boundary cap for all cross-product output.
pub const CROSS_PRODUCT_CLAIM_BOUNDARY: ClaimBoundary = ClaimBoundary::Level0DesignNote;

#[cfg(test)]
mod tests {
    use super::*;

    fn all_fourteen_mutation_classes() -> Vec<MutationClass> {
        vec![
            MutationClass::MissingConstraints,
            MutationClass::CorruptedGuards,
            MutationClass::BadCounters,
            MutationClass::StaleStateReads,
            MutationClass::InvalidUnrollBounds,
            MutationClass::NondeterministicTransitionInjection,
            MutationClass::RecursionEnvelopeMismatch,
            MutationClass::PublicPrivateBoundaryMismatch,
            MutationClass::WitnessAliasing,
            MutationClass::InvariantWeakening,
            MutationClass::InvariantStrengthening,
            MutationClass::ObservationOmission,
            MutationClass::SemanticNoOpDrift,
            MutationClass::TraceOrderingCorruption,
        ]
    }

    #[test]
    fn every_mutation_class_has_a_profile() {
        for mutation_class in all_fourteen_mutation_classes() {
            let profile = mutation_class_formal_stress(mutation_class);
            assert_eq!(profile.mutation_class, mutation_class);
            assert_ne!(
                profile.primary_formal_scope,
                FormalPropertyScopeKind::NotApplicable,
                "no current MutationClass should map to NotApplicable"
            );
            assert!(!profile.rationale.is_empty());
            assert!(!profile.nonclaims.is_empty());
        }
    }

    #[test]
    fn invariant_weakening_maps_to_invariant_scope() {
        let profile = mutation_class_formal_stress(MutationClass::InvariantWeakening);
        assert_eq!(
            profile.primary_formal_scope,
            FormalPropertyScopeKind::Invariant
        );
    }

    #[test]
    fn invalid_unroll_bounds_maps_to_loop_bound_scope() {
        let profile = mutation_class_formal_stress(MutationClass::InvalidUnrollBounds);
        assert_eq!(
            profile.primary_formal_scope,
            FormalPropertyScopeKind::LoopBound
        );
    }

    #[test]
    fn profiles_carry_mandatory_nonclaims() {
        let profile = mutation_class_formal_stress(MutationClass::BadCounters);
        assert!(profile.nonclaims.iter().any(|n| n.contains("not proof")));
    }

    #[test]
    fn profile_is_deterministic() {
        let left = mutation_class_formal_stress(MutationClass::BadCounters);
        let right = mutation_class_formal_stress(MutationClass::BadCounters);
        assert_eq!(left, right);
    }

    #[test]
    fn scope_kind_has_five_variants() {
        let all = [
            FormalPropertyScopeKind::TransitionGuard,
            FormalPropertyScopeKind::Invariant,
            FormalPropertyScopeKind::LoopBound,
            FormalPropertyScopeKind::Machine,
            FormalPropertyScopeKind::NotApplicable,
        ];
        assert_eq!(all.len(), 5);
    }
}
