use zkbench_core::{generate_family, ExpectedVerdict, GeneratorConfig, InstanceParams};

#[test]
fn generator_instance_uses_inconclusive_empty_primary_trace_without_oracle_traces() {
    let mut family = generate_family(GeneratorConfig::baseline_fsm())
        .expect("baseline family generation should succeed");
    family.semantic_ir.oracle.accepted_traces.clear();
    family.semantic_ir.oracle.rejected_traces.clear();
    family.surface_spec.oracle.accepted_traces.clear();
    family.surface_spec.oracle.rejected_traces.clear();

    let instance = family
        .instantiate(InstanceParams {
            id_suffix: "empty_oracle".to_string(),
        })
        .expect("instance generation should remain local data");

    assert_eq!(instance.id, format!("{}_empty_oracle", family.id));
    assert_eq!(instance.family_id, family.id);
    assert!(instance.accepted_traces.is_empty());
    assert!(instance.rejected_traces.is_empty());
    assert!(instance.expected_verdicts.is_empty());
    assert_eq!(instance.primary_trace.id, "empty_trace");
    assert!(instance.primary_trace.initial_state.is_none());
    assert!(instance.primary_trace.initial_fields.is_empty());
    assert!(instance.primary_trace.steps.is_empty());
    assert!(instance.primary_trace.expected_final_state.is_none());
    assert!(instance.primary_trace.expected_final_fields.is_empty());
    assert_eq!(
        instance.primary_trace.expected_verdict,
        Some(ExpectedVerdict::Inconclusive)
    );
    assert!(instance.primary_trace.requires_capabilities.is_empty());
    assert_eq!(instance.local_evidence, Vec::new());
    assert_eq!(instance.claim_boundary, family.claim_boundary);
}
