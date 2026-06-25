//! Phase 158 — oracle completeness audit integration tests.

use zkbench_core::{
    audit_oracle_completeness, generate_instance, GeneratorConfig, InstanceParams,
    OracleCompletenessLabel,
};

#[test]
fn bounded_counter_loop_is_fully_executable() {
    let instance = generate_instance(
        GeneratorConfig::bounded_counter_loop().loop_bound(3),
        InstanceParams::default(),
    )
    .expect("bounded counter loop instance should generate");
    let audit = audit_oracle_completeness(&instance.surface_spec);
    assert!(
        audit.is_fully_executable,
        "BoundedCounterLoop should be fully executable, but {} constructs flagged",
        audit.capability_gap_count
    );
    assert_eq!(audit.capability_gap_count, 0);
    assert_eq!(audit.structurally_incapable_count, 0);
    assert!(audit.executable_count > 0);
}

#[test]
fn nested_loop_is_fully_executable() {
    let instance = generate_instance(GeneratorConfig::nested_loop(), InstanceParams::default())
        .expect("nested loop instance should generate");
    let audit = audit_oracle_completeness(&instance.surface_spec);
    assert!(
        audit.is_fully_executable,
        "NestedLoop should be fully executable, but {} constructs flagged",
        audit.capability_gap_count
    );
}

#[test]
fn guard_heavy_machine_is_fully_executable() {
    let instance = generate_instance(
        GeneratorConfig::guard_heavy_machine(),
        InstanceParams::default(),
    )
    .expect("guard heavy machine instance should generate");
    let audit = audit_oracle_completeness(&instance.surface_spec);
    assert!(
        audit.is_fully_executable,
        "GuardHeavyMachine should be fully executable, but {} constructs flagged",
        audit.capability_gap_count
    );
}

#[test]
fn audit_counts_are_self_consistent_for_every_shipped_family() {
    let configs = [
        GeneratorConfig::baseline_fsm(),
        GeneratorConfig::branching_fsm(),
        GeneratorConfig::bounded_counter_loop().loop_bound(3),
        GeneratorConfig::nested_loop(),
        GeneratorConfig::guard_heavy_machine(),
    ];
    for config in configs {
        let instance = generate_instance(config, InstanceParams::default())
            .expect("shipped family should generate");
        let audit = audit_oracle_completeness(&instance.surface_spec);
        assert_eq!(
            audit.constructs.len(),
            audit.executable_count
                + audit.capability_gap_count
                + audit.structurally_incapable_count,
            "audit counts must match construct vector length"
        );
        // Every shipped family must avoid raw-text and non-int-operand gaps.
        assert_eq!(
            audit.capability_gap_count, 0,
            "shipped family must have no capability gaps"
        );
    }
}

#[test]
fn audit_is_deterministic_across_runs() {
    let instance = generate_instance(
        GeneratorConfig::bounded_counter_loop().loop_bound(3),
        InstanceParams::default(),
    )
    .expect("bounded counter loop instance should generate");
    let left = audit_oracle_completeness(&instance.surface_spec);
    let right = audit_oracle_completeness(&instance.surface_spec);
    assert_eq!(left, right);
}

#[test]
fn no_structurally_incapable_constructs_in_shipped_families() {
    // The StructurallyIncapable variant is reserved for future constructs;
    // no shipped family should produce one.
    let configs = [
        GeneratorConfig::baseline_fsm(),
        GeneratorConfig::branching_fsm(),
        GeneratorConfig::bounded_counter_loop().loop_bound(3),
        GeneratorConfig::nested_loop(),
        GeneratorConfig::guard_heavy_machine(),
    ];
    for config in configs {
        let instance = generate_instance(config, InstanceParams::default())
            .expect("shipped family should generate");
        let audit = audit_oracle_completeness(&instance.surface_spec);
        assert!(
            audit
                .constructs
                .iter()
                .all(|c| c.label != OracleCompletenessLabel::StructurallyIncapable),
            "shipped family must not produce structurally incapable constructs"
        );
    }
}
