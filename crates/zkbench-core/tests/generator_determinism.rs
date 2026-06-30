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
fn generator_limits_reject_derived_new_family_resource_counts() {
    let limits = GeneratorLimits {
        max_trace_steps: 7,
        ..GeneratorLimits::default()
    };
    let error = GeneratorConfig::nested_loop()
        .loop_bound(2)
        .limits(limits)
        .validate()
        .expect_err("nested loop derived trace length should be checked");
    assert!(error.to_string().contains("generated trace steps"));

    let limits = GeneratorLimits {
        max_fields: 3,
        ..GeneratorLimits::default()
    };
    let error = GeneratorConfig::memory_heavy_state_machine()
        .limits(limits)
        .validate()
        .expect_err("memory-heavy derived field count should be checked");
    assert!(error.to_string().contains("requested field count"));
}

#[test]
fn branching_fsm_validation_rejects_too_few_states_before_generation() {
    let error = GeneratorConfig::branching_fsm()
        .state_count(3)
        .validate()
        .expect_err("branching fsm with one branch state should fail validation");

    assert!(error.to_string().contains("state_count >= 4"));
}

#[test]
fn generator_config_validation_reports_reachable_limit_edges() {
    let trace_limit_error = GeneratorConfig::baseline_fsm()
        .trace_length(65)
        .validate()
        .expect_err("explicit trace length over max_trace_steps should fail");
    assert!(trace_limit_error
        .to_string()
        .contains("trace_length 65 exceeds max_trace_steps 64"));

    let transition_limit_error = GeneratorConfig::branching_fsm()
        .branching_factor(3)
        .limits(GeneratorLimits {
            max_transitions: 3,
            ..GeneratorLimits::default()
        })
        .validate()
        .expect_err("derived branching transitions over max_transitions should fail");
    assert!(transition_limit_error
        .to_string()
        .contains("generated transition count 4 exceeds max_transitions 3"));
}

#[test]
fn generator_config_validation_reports_family_specific_reachable_edges() {
    let baseline_state_error = GeneratorConfig::baseline_fsm()
        .state_count(1)
        .validate()
        .expect_err("baseline with fewer than two states should fail");
    assert!(baseline_state_error
        .to_string()
        .contains("BaselineFsm requires state_count >= 2"));

    let baseline_trace_error = GeneratorConfig::baseline_fsm()
        .state_count(4)
        .trace_length(2)
        .validate()
        .expect_err("baseline trace shorter than required transitions should fail");
    assert!(baseline_trace_error
        .to_string()
        .contains("BaselineFsm requires trace_length >= state_count - 1 (3)"));

    let branching_factor_error = GeneratorConfig::branching_fsm()
        .branching_factor(1)
        .validate()
        .expect_err("branching fsm with one branch should fail validation");
    assert!(branching_factor_error
        .to_string()
        .contains("BranchingFsm requires branching_factor >= 2"));

    let bounded_loop_error = GeneratorConfig::bounded_counter_loop()
        .loop_bound(0)
        .validate()
        .expect_err("bounded counter loop with zero bound should fail validation");
    assert!(bounded_loop_error
        .to_string()
        .contains("BoundedCounterLoop requires loop_bound >= 1"));
}
