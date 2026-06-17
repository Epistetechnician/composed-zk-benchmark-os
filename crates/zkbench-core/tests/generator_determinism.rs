use zkbench_core::{generate_family, FamilyKind, GeneratorConfig, GeneratorLimits};

#[test]
fn same_seed_produces_identical_baseline_output() {
    let config = GeneratorConfig::baseline_fsm()
        .seed(7)
        .state_count(4)
        .trace_length(3);
    let left = generate_family(config.clone()).expect("baseline generation should succeed");
    let right = generate_family(config).expect("baseline generation should be deterministic");
    assert_eq!(left, right);
    assert_eq!(left.family_kind, FamilyKind::BaselineFsm);
}

#[test]
fn same_seed_produces_identical_bounded_loop_output() {
    let config = GeneratorConfig::bounded_counter_loop()
        .seed(11)
        .loop_bound(4);
    let left = generate_family(config.clone()).expect("bounded generation should succeed");
    let right = generate_family(config).expect("bounded generation should be deterministic");
    assert_eq!(left, right);
    assert_eq!(left.family_kind, FamilyKind::BoundedCounterLoop);
}

#[test]
fn different_seed_changes_generated_output_controlled() {
    let left = generate_family(GeneratorConfig::branching_fsm().seed(1))
        .expect("branching generation should succeed");
    let right = generate_family(GeneratorConfig::branching_fsm().seed(2))
        .expect("branching generation should succeed");
    assert_ne!(left.id, right.id);
    assert_ne!(left.surface_spec, right.surface_spec);
}

#[test]
fn generator_limits_reject_excessive_values() {
    let limits = GeneratorLimits {
        max_states: 3,
        ..GeneratorLimits::default()
    };
    let config = GeneratorConfig::baseline_fsm()
        .state_count(4)
        .trace_length(3)
        .limits(limits);
    let error = generate_family(config).expect_err("state limit should reject config");
    assert!(error.to_string().contains("exceeds max_states"));

    let limits = GeneratorLimits {
        max_loop_bound: 2,
        ..GeneratorLimits::default()
    };
    let config = GeneratorConfig::bounded_counter_loop()
        .loop_bound(3)
        .limits(limits);
    let error = generate_family(config).expect_err("loop limit should reject config");
    assert!(error.to_string().contains("exceeds max_loop_bound"));
}

#[test]
fn branching_fsm_validation_rejects_too_few_states_before_generation() {
    let error = GeneratorConfig::branching_fsm()
        .state_count(3)
        .validate()
        .expect_err("branching fsm with one branch state should fail validation");

    assert!(error.to_string().contains("state_count >= 4"));
}
