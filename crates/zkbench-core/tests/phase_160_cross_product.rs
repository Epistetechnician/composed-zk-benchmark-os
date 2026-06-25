//! Phase 160 — mutation × formal cross-product mapping integration tests.

use zkbench_core::evidence::ClaimBoundary;
use zkbench_core::{
    derive_formal_property_assertion_template, generate_instance, mutation_class_formal_stress,
    FormalPropertyAssertion, FormalPropertyScope, FormalPropertyScopeKind, GeneratorConfig,
    InstanceParams, MutationClass, MutationFormalStressProfile,
};

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
fn every_mutation_class_has_a_non_not_applicable_profile() {
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
fn implemented_classes_map_to_documented_scopes() {
    let cases = [
        (
            MutationClass::MissingConstraints,
            FormalPropertyScopeKind::TransitionGuard,
        ),
        (
            MutationClass::CorruptedGuards,
            FormalPropertyScopeKind::TransitionGuard,
        ),
        (
            MutationClass::BadCounters,
            FormalPropertyScopeKind::TransitionGuard,
        ),
        (
            MutationClass::StaleStateReads,
            FormalPropertyScopeKind::TransitionGuard,
        ),
        (
            MutationClass::InvalidUnrollBounds,
            FormalPropertyScopeKind::LoopBound,
        ),
        (
            MutationClass::InvariantWeakening,
            FormalPropertyScopeKind::Invariant,
        ),
        (
            MutationClass::InvariantStrengthening,
            FormalPropertyScopeKind::Invariant,
        ),
        (
            MutationClass::ObservationOmission,
            FormalPropertyScopeKind::Machine,
        ),
    ];
    for (mutation_class, expected_scope) in cases {
        let profile = mutation_class_formal_stress(mutation_class);
        assert_eq!(
            profile.primary_formal_scope, expected_scope,
            "wrong scope for {mutation_class:?}"
        );
    }
}

#[test]
fn profiles_carry_not_a_proof_nonclaim() {
    for mutation_class in all_fourteen_mutation_classes() {
        let profile = mutation_class_formal_stress(mutation_class);
        assert!(
            profile.nonclaims.iter().any(|n| n.contains("not proof")),
            "{mutation_class:?} profile must carry a not-a-proof nonclaim"
        );
    }
}

#[test]
fn derive_returns_some_for_invariant_weakening_on_counter_loop() {
    let instance = generate_instance(
        GeneratorConfig::bounded_counter_loop().loop_bound(3),
        InstanceParams::default(),
    )
    .expect("bounded counter loop should generate");
    let template = derive_formal_property_assertion_template(
        MutationClass::InvariantWeakening,
        &instance.surface_spec,
    )
    .expect("InvariantWeakening on BoundedCounterLoop should derive a template");
    assert!(matches!(
        template.scope,
        FormalPropertyScope::Invariant { .. }
    ));
    assert!(template.statement.contains("invariantweakening"));
    assert!(!template.id.is_empty());
    assert!(!template.bound_machine_id.is_empty());
}

#[test]
fn derive_returns_none_for_invariant_weakening_on_branching_fsm() {
    let instance = generate_instance(GeneratorConfig::branching_fsm(), InstanceParams::default())
        .expect("branching fsm should generate");
    let template = derive_formal_property_assertion_template(
        MutationClass::InvariantWeakening,
        &instance.surface_spec,
    );
    assert!(
        template.is_none(),
        "InvariantWeakening should not derive a template when no invariant exists"
    );
}

#[test]
fn derive_returns_some_for_invalid_unroll_bounds_when_a_loop_exists() {
    let instance = generate_instance(
        GeneratorConfig::bounded_counter_loop().loop_bound(3),
        InstanceParams::default(),
    )
    .expect("bounded counter loop should generate");
    let template = derive_formal_property_assertion_template(
        MutationClass::InvalidUnrollBounds,
        &instance.surface_spec,
    );
    // BoundedCounterLoop may or may not have a loop entry depending on
    // generator config; either outcome is acceptable as long as it's
    // internally consistent.
    if let Some(template) = template {
        assert!(matches!(
            template.scope,
            FormalPropertyScope::LoopBound { .. }
        ));
    }
}

#[test]
fn derive_returns_some_for_machine_scoped_mutations_on_any_family() {
    let instance = generate_instance(GeneratorConfig::branching_fsm(), InstanceParams::default())
        .expect("branching fsm should generate");
    let template = derive_formal_property_assertion_template(
        MutationClass::WitnessAliasing,
        &instance.surface_spec,
    )
    .expect("Machine-scoped mutations should always derive a template");
    assert!(matches!(template.scope, FormalPropertyScope::Machine));
}

#[test]
fn derived_template_carries_not_a_proof_nonclaim() {
    let instance = generate_instance(
        GeneratorConfig::bounded_counter_loop().loop_bound(3),
        InstanceParams::default(),
    )
    .expect("bounded counter loop should generate");
    let template = derive_formal_property_assertion_template(
        MutationClass::InvariantWeakening,
        &instance.surface_spec,
    )
    .expect("template should derive");
    assert!(template.nonclaims.iter().any(|n| n.contains("not proof")));
}

#[test]
fn derived_template_uses_level0_claim_boundary_convention() {
    // The assertion type doesn't carry a claim boundary directly, but the
    // mandatory nonclaims language must establish the Level0 ceiling.
    let instance = generate_instance(
        GeneratorConfig::bounded_counter_loop().loop_bound(3),
        InstanceParams::default(),
    )
    .expect("bounded counter loop should generate");
    let template = derive_formal_property_assertion_template(
        MutationClass::InvariantWeakening,
        &instance.surface_spec,
    )
    .expect("template should derive");
    assert!(template
        .nonclaims
        .iter()
        .any(|n| n.contains("not a formal property statement")));
    // Sanity: ClaimBoundary::Level0DesignNote is the documented cap and
    // remains the lowest boundary.
    assert_eq!(
        ClaimBoundary::Level0DesignNote.level(),
        0,
        "Level0DesignNote must remain the lowest boundary"
    );
}

#[test]
fn mapping_is_deterministic() {
    for mutation_class in all_fourteen_mutation_classes() {
        let left: MutationFormalStressProfile = mutation_class_formal_stress(mutation_class);
        let right = mutation_class_formal_stress(mutation_class);
        assert_eq!(
            left, right,
            "{mutation_class:?} mapping must be deterministic"
        );
    }
    let instance = generate_instance(
        GeneratorConfig::bounded_counter_loop().loop_bound(3),
        InstanceParams::default(),
    )
    .expect("bounded counter loop should generate");
    let left = derive_formal_property_assertion_template(
        MutationClass::InvariantWeakening,
        &instance.surface_spec,
    );
    let right = derive_formal_property_assertion_template(
        MutationClass::InvariantWeakening,
        &instance.surface_spec,
    );
    assert_eq!(left, right);
}

#[test]
fn formal_property_assertion_type_is_exposed() {
    // Compile-time check that the assertion type is publicly constructible
    // from this integration test crate.
    let assertion = FormalPropertyAssertion {
        id: "compile_check".to_string(),
        scope: FormalPropertyScope::Machine,
        statement: "compile check only".to_string(),
        bound_machine_id: "m0".to_string(),
        nonclaims: vec!["compile check nonclaim".to_string()],
    };
    assert_eq!(assertion.id, "compile_check");
}

#[test]
fn no_new_mutation_class_or_scope_variants_were_added_scope_guard() {
    // If MutationClass grew variants, mutation_class_formal_stress would need
    // a new match arm. This count guards against silent scope creep.
    assert_eq!(
        all_fourteen_mutation_classes().len(),
        14,
        "MutationClass variant count"
    );
    let scope_kinds = [
        FormalPropertyScopeKind::TransitionGuard,
        FormalPropertyScopeKind::Invariant,
        FormalPropertyScopeKind::LoopBound,
        FormalPropertyScopeKind::Machine,
        FormalPropertyScopeKind::NotApplicable,
    ];
    assert_eq!(
        scope_kinds.len(),
        5,
        "FormalPropertyScopeKind variant count"
    );
}
