use std::collections::BTreeSet;

use zkbench_core::{
    list_available_local_generators, list_local_adapter_targets, local_benchmark_pack_schema,
    resolve_local_generator, zk_harness_adapter_registry_entry,
    zk_harness_dry_run_plan_registry_entry, LocalGeneratorRegistry, RegistryEntry,
    ZkHarnessAdapterRegistryEntry, ZkHarnessDryRunPlanRegistryEntry,
};

#[test]
fn local_generator_registry_metadata_is_unique_and_consistent() {
    let registry = LocalGeneratorRegistry::default();
    assert_eq!(registry.list_templates(), list_available_local_generators());

    let mut ids = BTreeSet::new();
    let mut implemented_count = 0usize;
    for template in registry.list_templates() {
        assert!(
            ids.insert(template.kind.id_segment()),
            "duplicate generator family id segment: {}",
            template.kind.id_segment()
        );
        assert_eq!(
            registry.resolve(template.kind),
            Some(template),
            "registry should resolve every listed template"
        );
        assert_eq!(resolve_local_generator(template.kind), *template);
        assert_eq!(template.implemented, template.kind.is_implemented());
        if template.implemented {
            implemented_count += 1;
            assert!(
                !template.supported_oracle_features.is_empty(),
                "implemented generator templates must disclose supported oracle features"
            );
        } else {
            assert!(
                template
                    .unsupported_features
                    .iter()
                    .any(|feature| feature == "future_placeholder"),
                "future generator templates must remain explicit placeholders"
            );
        }
    }

    assert!(
        implemented_count > 0,
        "registry should expose implemented local generators"
    );
}

#[test]
fn registry_entries_roundtrip_and_preserve_claim_boundaries() {
    let pack_schema = local_benchmark_pack_schema();
    let json = serde_json::to_string(&pack_schema).expect("registry entry should serialize");
    let parsed: RegistryEntry =
        serde_json::from_str(&json).expect("registry entry should deserialize");
    assert_eq!(pack_schema, parsed);
    assert_eq!(pack_schema.kind, "benchmark_pack_schema");
    assert!(pack_schema
        .description
        .as_deref()
        .expect("schema should disclose boundary")
        .contains("local replay is not official benchmark evidence"));

    let adapter_entry = zk_harness_adapter_registry_entry();
    let json = serde_json::to_string(&adapter_entry).expect("adapter entry should serialize");
    let parsed: ZkHarnessAdapterRegistryEntry =
        serde_json::from_str(&json).expect("adapter entry should deserialize");
    assert_eq!(adapter_entry, parsed);
    assert!(adapter_entry
        .notes
        .iter()
        .any(|note| note.contains("external execution is disabled")));

    let plan_entry = zk_harness_dry_run_plan_registry_entry();
    let json = serde_json::to_string(&plan_entry).expect("plan entry should serialize");
    let parsed: ZkHarnessDryRunPlanRegistryEntry =
        serde_json::from_str(&json).expect("plan entry should deserialize");
    assert_eq!(plan_entry, parsed);
    assert!(plan_entry
        .notes
        .iter()
        .any(|note| note.contains("not benchmark results")));
}

#[test]
fn local_adapter_registry_does_not_claim_proving_or_performance_capabilities() {
    let targets = list_local_adapter_targets();
    assert!(
        targets.iter().any(|target| target.kind == "local_json"),
        "local adapter registry should include the local JSON replay target"
    );

    for target in targets {
        assert!(
            !target.capabilities.supports_proving,
            "{} must not claim proving capability",
            target.id
        );
        assert!(
            !target.capabilities.supports_verification_timing,
            "{} must not claim verification timing capability",
            target.id
        );
        assert!(
            !target.capabilities.supports_formal_semantics,
            "{} must not claim formal-semantics capability",
            target.id
        );
        assert!(
            !target.capabilities.supports_machine_checked_proof,
            "{} must not claim machine-checked-proof capability",
            target.id
        );
    }
}
