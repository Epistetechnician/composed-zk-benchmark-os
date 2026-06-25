//! Phase 164 — remaining four benchmark families.

use zkbench_core::{
    generate_family, list_available_local_generators, ClaimBoundary, FamilyKind, GeneratorConfig,
};

#[test]
fn all_nine_families_are_implemented() {
    let implemented: Vec<_> = list_available_local_generators()
        .into_iter()
        .filter(|template| template.implemented)
        .map(|template| template.kind)
        .collect();
    assert_eq!(implemented.len(), 9);
    for kind in [
        FamilyKind::BaselineFsm,
        FamilyKind::BranchingFsm,
        FamilyKind::BoundedCounterLoop,
        FamilyKind::NestedLoop,
        FamilyKind::GuardHeavyMachine,
        FamilyKind::RecursiveEnvelope,
        FamilyKind::MemoryHeavyStateMachine,
        FamilyKind::PublicPrivateBoundaryStress,
        FamilyKind::ZkMlControlFlowMixed,
    ] {
        assert!(implemented.contains(&kind));
        assert!(kind.is_implemented());
    }
}

#[test]
fn phase_164_families_carry_level1_claim_boundary() {
    for config in [
        GeneratorConfig::recursive_envelope(),
        GeneratorConfig::memory_heavy_state_machine(),
        GeneratorConfig::public_private_boundary_stress(),
        GeneratorConfig::zkml_control_flow_mixed(),
    ] {
        let family = generate_family(config).expect("family should generate");
        assert_eq!(family.claim_boundary, ClaimBoundary::Level1LocalReplay);
    }
}

#[test]
fn phase_164_families_generate_with_expected_surface_features() {
    let recursive = generate_family(GeneratorConfig::recursive_envelope()).expect("recursive");
    assert!(recursive
        .surface_spec
        .machine
        .loops
        .iter()
        .any(|entry| entry.metadata.contains_key("envelope_digest")));

    let boundary =
        generate_family(GeneratorConfig::public_private_boundary_stress()).expect("public/private");
    assert!(!boundary
        .surface_spec
        .machine
        .witness_policy
        .public_inputs
        .is_empty());

    let zkml = generate_family(GeneratorConfig::zkml_control_flow_mixed()).expect("zkml");
    assert!(zkml
        .surface_spec
        .machine
        .observations
        .iter()
        .any(|observe| observe.field == "confidence"));
}
