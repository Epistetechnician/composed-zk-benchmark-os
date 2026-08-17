//! Focused coverage for the second typed experiment plugin implementation.
//!
//! State slice: `benchmark-os-experiment-plugin-agnostic-composition-v1`.
//! Binding access slice: `benchmark-os-plugin-composition-binding-access-v1`.
//! Source binding integrity slice: `benchmark-os-plugin-composition-source-binding-integrity-v1`.
//! Ordered binding access slice: `benchmark-os-plugin-composition-ordered-binding-access-v1`.
//! Canonical order slice: `benchmark-os-plugin-composition-canonical-order-v1`.
//! Projection adapter slice: `benchmark-os-plugin-composition-projection-adapter-v1`.
//! Projector provenance slice: `benchmark-os-plugin-composition-projector-provenance-v1`.
//! Durable projector attribution slice: `benchmark-os-plugin-composition-projector-durable-attribution-v1`.
//! Durable composition-adapter attribution slice:
//! `benchmark-os-plugin-composition-adapter-durable-attribution-v1`.
//! Identity descriptor binding slice: `benchmark-os-plugin-composition-identity-descriptor-binding-v1`.
//! Artifact-reference policy locality slice: `benchmark-os-plugin-composition-artifact-reference-policy-locality-v1`.
//! Output handoff validation slice: `benchmark-os-plugin-composition-output-handoff-validation-v1`.
//! This is local pure-data contract coverage, not scientific evidence.

use zkbench_core::{
    compute_experiment_bundle_digest, compute_plugin_composition_config_digest,
    deserialize_plugin_composition_config_json, metacognitive_experiment_plugin_descriptor,
    serialize_plugin_composition_config_json, validate_experiment_bundle, ClaimBoundary,
    ExperimentArtifactKind, ExperimentBundle, ExperimentPluginFactoryCatalog, GeneratorConfig,
    PluginCompositionBinding, PluginCompositionIdentity, PluginCompositionProjector,
    PluginCompositionRunner, PluginCompositionSource, StandardPluginCompositionProjector,
    ValidatedPluginCompositionOutput, METACOGNITIVE_EXPERIMENT_PLUGIN_ID,
};

fn provenance(label: &str) -> zkbench_core::experiment_observability::ExperimentProvenance {
    zkbench_core::experiment_observability::ExperimentProvenance {
        who: "plugin-composition-test".to_string(),
        what: label.to_string(),
        when: "logical-test-time".to_string(),
        version: "plugin-composition-test-v1".to_string(),
        source_revision: "local-uncommitted".to_string(),
    }
}

#[test]
fn metacognitive_factory_runs_through_descriptor_binding() {
    let catalog = ExperimentPluginFactoryCatalog::metacognitive()
        .expect("synthetic factory catalog should construct");
    let bundle = catalog
        .run(METACOGNITIVE_EXPERIMENT_PLUGIN_ID)
        .expect("synthetic plugin should run through validated catalog dispatch");

    assert_eq!(bundle.config.plugin_id, METACOGNITIVE_EXPERIMENT_PLUGIN_ID);
    assert_eq!(
        bundle.model_version.model_id,
        metacognitive_experiment_plugin_descriptor().model_id
    );
    assert_eq!(bundle.artifacts.len(), 8);
    assert_eq!(bundle.claim_boundary, ClaimBoundary::Level0DesignNote);
    assert!(validate_experiment_bundle(&bundle).valid);
}

#[test]
fn combined_catalog_exports_two_descriptor_only_plugins() {
    let catalog = ExperimentPluginFactoryCatalog::local_json_with_metacognitive(
        GeneratorConfig::baseline_fsm(),
    )
    .expect("combined catalog should construct");
    let registry = catalog.metadata_registry();
    assert_eq!(registry.plugins.len(), 2);
    assert!(registry
        .resolve(zkbench_core::LOCAL_JSON_EXPERIMENT_PLUGIN_ID)
        .is_some());
    assert!(registry
        .resolve(METACOGNITIVE_EXPERIMENT_PLUGIN_ID)
        .is_some());

    let local = catalog
        .run(zkbench_core::LOCAL_JSON_EXPERIMENT_PLUGIN_ID)
        .expect("local plugin should remain runnable");
    let synthetic = catalog
        .run(METACOGNITIVE_EXPERIMENT_PLUGIN_ID)
        .expect("synthetic plugin should be independently runnable");
    assert_ne!(local.config.plugin_id, synthetic.config.plugin_id);
    assert_eq!(
        synthetic.report.claim_boundary,
        ClaimBoundary::Level0DesignNote
    );
}

#[test]
fn metacognitive_plugin_is_deterministic_and_non_authoritative() {
    let catalog = ExperimentPluginFactoryCatalog::metacognitive()
        .expect("synthetic factory catalog should construct");
    let first = catalog
        .run(METACOGNITIVE_EXPERIMENT_PLUGIN_ID)
        .expect("first synthetic run should succeed");
    let second = catalog
        .run(METACOGNITIVE_EXPERIMENT_PLUGIN_ID)
        .expect("second synthetic run should succeed");

    assert_eq!(first, second);
    assert!(first
        .report
        .non_claims
        .iter()
        .any(|non_claim| non_claim.contains("not a model execution")));
    assert!(first
        .mechanism_ledger
        .measurements
        .iter()
        .any(|measurement| measurement.status == zkbench_core::MeasurementStatus::Unsupported));
}

#[test]
fn generic_runner_composes_metacognitive_plugin_with_explicit_sources() {
    let catalog = ExperimentPluginFactoryCatalog::metacognitive()
        .expect("synthetic factory catalog should construct");
    let plugin = catalog
        .instantiate(METACOGNITIVE_EXPERIMENT_PLUGIN_ID)
        .expect("synthetic plugin should instantiate");
    let runner = PluginCompositionRunner::new(
        plugin,
        "generic-metacognitive-experiment",
        "generic-metacognitive-run",
        provenance("generic-metacognitive-composition"),
    )
    .expect("generic runner should construct");
    let output = runner.run().expect("generic composition should succeed");

    assert_eq!(output.config.bindings.len(), 9);
    let ordered_bindings = output
        .config
        .bindings_in_order()
        .expect("all generated bindings should have canonical order");
    assert_eq!(
        ordered_bindings
            .first()
            .expect("canonical bindings should not be empty")
            .outer_kind,
        zkbench_core::experiment_observability::ExperimentArtifactKind::Config
    );
    assert_eq!(
        ordered_bindings
            .last()
            .expect("canonical bindings should include report")
            .outer_kind,
        zkbench_core::experiment_observability::ExperimentArtifactKind::Report
    );
    assert_eq!(output.outer.claim_boundary, ClaimBoundary::Level0DesignNote);
    assert_eq!(
        output.outer.experiment_id,
        "generic-metacognitive-experiment"
    );
    assert_eq!(output.outer.run_id, "generic-metacognitive-run");
    let task_binding = output
        .config
        .bindings
        .iter()
        .find(|binding| {
            binding.outer_kind
                == zkbench_core::experiment_observability::ExperimentArtifactKind::Task
        })
        .expect("task binding should exist");
    assert_eq!(
        task_binding.sources[0].inner_kind,
        zkbench_core::experiment::ExperimentArtifactKind::DataVersion
    );

    let json = serialize_plugin_composition_config_json(&output.config)
        .expect("generic config should serialize");
    let restored = deserialize_plugin_composition_config_json(&json)
        .expect("generic config should deserialize");
    assert_eq!(restored, output.config);
    assert_eq!(
        compute_plugin_composition_config_digest(&restored)
            .expect("generic config digest should be deterministic"),
        compute_plugin_composition_config_digest(&output.config)
            .expect("generic config digest should remain deterministic")
    );
}

// State slice: benchmark-os-plugin-composition-artifact-reference-policy-locality-v1.
#[test]
fn generic_outer_artifacts_share_reference_policy_scope_and_provenance() {
    let catalog = ExperimentPluginFactoryCatalog::metacognitive()
        .expect("synthetic factory catalog should construct");
    let plugin = catalog
        .instantiate(METACOGNITIVE_EXPERIMENT_PLUGIN_ID)
        .expect("synthetic plugin should instantiate");
    let expected_provenance = provenance("generic-reference-policy");
    let runner = PluginCompositionRunner::new(
        plugin,
        "generic-reference-policy-experiment",
        "generic-reference-policy-run",
        expected_provenance.clone(),
    )
    .expect("generic runner should construct");
    let output = runner.run().expect("generic composition should succeed");

    for (kind, artifact) in output.outer.artifacts_in_order() {
        assert_eq!(artifact.kind, kind);
        assert_eq!(
            artifact.experiment_id,
            "generic-reference-policy-experiment"
        );
        assert_eq!(artifact.run_id, "generic-reference-policy-run");
        assert_eq!(artifact.provenance, expected_provenance);
    }
}

// State slice: benchmark-os-plugin-composition-output-handoff-validation-v1.
#[test]
fn plugin_composition_output_revalidates_the_complete_handoff_contract() {
    let catalog = ExperimentPluginFactoryCatalog::metacognitive()
        .expect("synthetic factory catalog should construct");
    let plugin = catalog
        .instantiate(METACOGNITIVE_EXPERIMENT_PLUGIN_ID)
        .expect("synthetic plugin should instantiate");
    let output = PluginCompositionRunner::new(
        plugin,
        "output-handoff-experiment",
        "output-handoff-run",
        provenance("output-handoff-validation"),
    )
    .expect("generic runner should construct")
    .run()
    .expect("generic composition should succeed");

    output
        .validate()
        .expect("runner output should satisfy the complete handoff contract");

    let mut tampered = output;
    tampered.outer.run_id = "drifted-output-handoff-run".to_string();
    let error = tampered
        .validate()
        .expect_err("outer identity drift must be rejected at the output handoff");
    assert!(!error.to_string().is_empty());
}

// State slice: benchmark-os-plugin-composition-output-handoff-validation-v1.
#[test]
fn validated_plugin_output_keeps_handoff_fields_private_and_compatibility_stable() {
    let catalog = ExperimentPluginFactoryCatalog::metacognitive()
        .expect("synthetic factory catalog should construct");
    let plugin = catalog
        .instantiate(METACOGNITIVE_EXPERIMENT_PLUGIN_ID)
        .expect("synthetic plugin should instantiate");
    let runner = PluginCompositionRunner::new(
        plugin,
        "validated-output-experiment",
        "validated-output-run",
        provenance("validated-output"),
    )
    .expect("generic runner should construct");
    let validated = runner
        .run_validated_output()
        .expect("validated output should construct");

    assert_eq!(validated.config().bindings.len(), 9);
    assert_eq!(
        validated.outer().claim_boundary,
        ClaimBoundary::Level0DesignNote
    );
    let compatibility = validated.clone().into_output();
    compatibility
        .validate()
        .expect("compatibility output should retain the validated contract");
    let (inner, config, outer) = validated.into_parts();
    assert_eq!(inner.bundle_id, compatibility.inner.bundle_id);
    assert_eq!(config, compatibility.config);
    assert_eq!(outer, compatibility.outer);

    let mut drifted_outer = compatibility.outer.clone();
    drifted_outer.run_id = "drifted-validated-output-run".to_string();
    assert!(ValidatedPluginCompositionOutput::new(
        compatibility.inner,
        compatibility.config,
        drifted_outer,
    )
    .is_err());
}

struct MetadataReportProjector;

struct EquivalentProjector;

impl PluginCompositionProjector for EquivalentProjector {
    fn descriptor(
        &self,
    ) -> zkbench_core::Result<zkbench_core::experiment_observability::ModuleDescriptor> {
        Ok(projector_descriptor("equivalent-projector-v1"))
    }

    fn project(
        &self,
        inner: &ExperimentBundle,
    ) -> zkbench_core::Result<Vec<PluginCompositionBinding>> {
        StandardPluginCompositionProjector.project(inner)
    }
}

impl PluginCompositionProjector for MetadataReportProjector {
    fn descriptor(
        &self,
    ) -> zkbench_core::Result<zkbench_core::experiment_observability::ModuleDescriptor> {
        Ok(projector_descriptor("metadata-report-projector-v1"))
    }

    fn project(
        &self,
        inner: &ExperimentBundle,
    ) -> zkbench_core::Result<Vec<PluginCompositionBinding>> {
        let mut bindings = StandardPluginCompositionProjector
            .project(inner)
            .expect("standard projector should construct the baseline bindings");
        let report = inner
            .artifact(ExperimentArtifactKind::Report)
            .expect("inner report artifact should exist");
        let metadata = bindings
            .iter_mut()
            .find(|binding| {
                binding.outer_kind
                    == zkbench_core::experiment_observability::ExperimentArtifactKind::Metadata
            })
            .ok_or_else(|| {
                zkbench_core::ZkBenchError::validation(
                    "projection-adapter-test",
                    "standard projector omitted metadata binding",
                )
            })?;
        metadata.sources.push(PluginCompositionSource {
            inner_kind: ExperimentArtifactKind::Report,
            inner_uri: report.uri.clone(),
            inner_digest: report.digest.clone(),
        });
        Ok(bindings)
    }
}

fn projector_descriptor(
    implementation_id: &str,
) -> zkbench_core::experiment_observability::ModuleDescriptor {
    zkbench_core::experiment_observability::ModuleDescriptor {
        module_id: "plugin-composition-projector".to_string(),
        implementation_id: implementation_id.to_string(),
        version: "1".to_string(),
        source_revision: "plugin-composition-test-v1".to_string(),
    }
}

struct WrongModuleProjector;

impl PluginCompositionProjector for WrongModuleProjector {
    fn descriptor(
        &self,
    ) -> zkbench_core::Result<zkbench_core::experiment_observability::ModuleDescriptor> {
        Ok(zkbench_core::experiment_observability::ModuleDescriptor {
            module_id: "wrong-module".to_string(),
            implementation_id: "wrong-projector-v1".to_string(),
            version: "1".to_string(),
            source_revision: "plugin-composition-test-v1".to_string(),
        })
    }

    fn project(
        &self,
        _inner: &ExperimentBundle,
    ) -> zkbench_core::Result<Vec<PluginCompositionBinding>> {
        panic!("invalid projector must fail during runner construction")
    }
}

struct MissingDescriptorProjector;

impl PluginCompositionProjector for MissingDescriptorProjector {
    fn project(
        &self,
        _inner: &ExperimentBundle,
    ) -> zkbench_core::Result<Vec<PluginCompositionBinding>> {
        panic!("missing projector descriptor must fail during runner construction")
    }
}

#[test]
fn projector_descriptor_is_validated_before_plugin_execution() {
    let catalog = ExperimentPluginFactoryCatalog::metacognitive()
        .expect("synthetic factory catalog should construct");
    let wrong_module_plugin = catalog
        .instantiate(METACOGNITIVE_EXPERIMENT_PLUGIN_ID)
        .expect("synthetic plugin should instantiate");
    let wrong_module_error = match PluginCompositionRunner::new_with_projector(
        wrong_module_plugin,
        "invalid-projector-experiment",
        "invalid-projector-run",
        provenance("invalid-projector"),
        Box::new(WrongModuleProjector),
    ) {
        Ok(_) => panic!("wrong projector module id must fail closed"),
        Err(error) => error,
    };
    assert!(wrong_module_error
        .to_string()
        .contains("unsupported module id"));

    let missing_descriptor_plugin = catalog
        .instantiate(METACOGNITIVE_EXPERIMENT_PLUGIN_ID)
        .expect("synthetic plugin should instantiate");
    let missing_descriptor_error = match PluginCompositionRunner::new_with_projector(
        missing_descriptor_plugin,
        "missing-projector-experiment",
        "missing-projector-run",
        provenance("missing-projector"),
        Box::new(MissingDescriptorProjector),
    ) {
        Ok(_) => panic!("missing projector descriptor must fail closed"),
        Err(error) => error,
    };
    assert!(missing_descriptor_error
        .to_string()
        .contains("projector descriptor is required"));
}

#[test]
fn standard_projector_descriptor_is_stable_and_module_scoped() {
    let catalog = ExperimentPluginFactoryCatalog::metacognitive()
        .expect("synthetic factory catalog should construct");
    let plugin = catalog
        .instantiate(METACOGNITIVE_EXPERIMENT_PLUGIN_ID)
        .expect("synthetic plugin should instantiate");
    let runner = PluginCompositionRunner::new(
        plugin,
        "standard-projector-experiment",
        "standard-projector-run",
        provenance("standard-projector"),
    )
    .expect("standard projector should declare a valid descriptor");

    assert_eq!(
        runner.projector_descriptor().module_id,
        "plugin-composition-projector"
    );
    assert_eq!(
        runner.projector_descriptor().implementation_id,
        "standard-plugin-composition-projector-v1"
    );
    assert_eq!(runner.projector_descriptor().version, "1");
    assert_eq!(
        runner.projector_descriptor().source_revision,
        "benchmark-os-plugin-composition-projection-adapter-v1"
    );
}

#[test]
fn explicit_projector_changes_source_bindings_without_changing_outer_contract() {
    let catalog = ExperimentPluginFactoryCatalog::metacognitive()
        .expect("synthetic factory catalog should construct");
    let plugin = catalog
        .instantiate(METACOGNITIVE_EXPERIMENT_PLUGIN_ID)
        .expect("synthetic plugin should instantiate");
    let runner = PluginCompositionRunner::new_with_projector(
        plugin,
        "projected-metacognitive-experiment",
        "projected-metacognitive-run",
        provenance("projected-metacognitive-composition"),
        Box::new(MetadataReportProjector),
    )
    .expect("generic runner should accept an explicit projector");
    assert_eq!(
        runner.projector_descriptor().implementation_id,
        "metadata-report-projector-v1"
    );
    let output = runner
        .run()
        .expect("explicit projector should compose successfully");

    let standard_bindings = StandardPluginCompositionProjector
        .project(&output.inner)
        .expect("standard projector should compose the same inner bundle");
    assert_ne!(output.config.bindings, standard_bindings);
    assert_eq!(output.config.bindings.len(), 9);
    let metadata = output
        .config
        .binding(zkbench_core::experiment_observability::ExperimentArtifactKind::Metadata)
        .expect("metadata binding should exist");
    assert!(metadata
        .sources
        .iter()
        .any(|source| source.inner_kind == ExperimentArtifactKind::Report));
    assert_eq!(output.outer.claim_boundary, ClaimBoundary::Level0DesignNote);
    output
        .config
        .validate_against_outer(&output.inner, &output.outer)
        .expect("explicitly projected output should retain strict validation");
}

#[test]
fn equivalent_projectors_preserve_config_and_outer_digests() {
    let catalog = ExperimentPluginFactoryCatalog::metacognitive()
        .expect("synthetic factory catalog should construct");
    let standard_plugin = catalog
        .instantiate(METACOGNITIVE_EXPERIMENT_PLUGIN_ID)
        .expect("standard plugin should instantiate");
    let equivalent_plugin = catalog
        .instantiate(METACOGNITIVE_EXPERIMENT_PLUGIN_ID)
        .expect("equivalent plugin should instantiate");

    let standard_runner = PluginCompositionRunner::new_with_projector(
        standard_plugin,
        "equivalent-projector-experiment",
        "equivalent-projector-run",
        provenance("equivalent-projector"),
        Box::new(StandardPluginCompositionProjector),
    )
    .expect("standard projector should construct");
    let equivalent_runner = PluginCompositionRunner::new_with_projector(
        equivalent_plugin,
        "equivalent-projector-experiment",
        "equivalent-projector-run",
        provenance("equivalent-projector"),
        Box::new(EquivalentProjector),
    )
    .expect("equivalent projector should construct");

    let standard = standard_runner
        .run()
        .expect("standard projection should succeed");
    let equivalent = equivalent_runner
        .run()
        .expect("equivalent projection should succeed");

    assert_ne!(
        standard_runner.projector_descriptor().implementation_id,
        equivalent_runner.projector_descriptor().implementation_id
    );
    assert_eq!(standard.config.bindings, equivalent.config.bindings);
    assert_eq!(
        standard
            .config
            .projector_descriptor()
            .expect("standard config should retain projector identity")
            .implementation_id,
        standard_runner.projector_descriptor().implementation_id
    );
    assert_eq!(
        equivalent
            .config
            .projector_descriptor()
            .expect("equivalent config should retain projector identity")
            .implementation_id,
        equivalent_runner.projector_descriptor().implementation_id
    );
    assert_ne!(standard.config, equivalent.config);
    let standard_json = serialize_plugin_composition_config_json(&standard.config)
        .expect("standard config should serialize");
    let equivalent_json = serialize_plugin_composition_config_json(&equivalent.config)
        .expect("equivalent config should serialize");
    assert!(standard_json.contains("projector_descriptor"));
    assert!(equivalent_json.contains("projector_descriptor"));
    assert_ne!(standard_json, equivalent_json);
    assert_ne!(
        compute_plugin_composition_config_digest(&standard.config)
            .expect("standard config digest should compute"),
        compute_plugin_composition_config_digest(&equivalent.config)
            .expect("equivalent config digest should compute")
    );
    assert_ne!(standard.outer.config.digest, equivalent.outer.config.digest);
    assert_eq!(
        standard
            .outer
            .artifact(zkbench_core::experiment_observability::ExperimentArtifactKind::Task)
            .digest,
        equivalent
            .outer
            .artifact(zkbench_core::experiment_observability::ExperimentArtifactKind::Task)
            .digest
    );
}

#[test]
fn generic_config_retains_durable_composition_adapter_attribution() {
    let catalog = ExperimentPluginFactoryCatalog::metacognitive()
        .expect("metacognitive catalog should construct");
    let plugin = catalog
        .instantiate(METACOGNITIVE_EXPERIMENT_PLUGIN_ID)
        .expect("metacognitive plugin should instantiate");
    let output = PluginCompositionRunner::new(
        plugin,
        "adapter-attribution-experiment",
        "adapter-attribution-run",
        provenance("adapter-attribution"),
    )
    .expect("generic runner should construct")
    .run()
    .expect("generic composition should run");

    let descriptor = output
        .config
        .adapter_descriptor
        .as_ref()
        .expect("new config should retain adapter identity");
    assert_eq!(descriptor.module_id, "plugin-composition-adapter");
    assert_eq!(
        descriptor.implementation_id,
        zkbench_core::PLUGIN_COMPOSITION_ADAPTER_ID
    );
    assert_eq!(descriptor.version, "1");
    assert_eq!(
        descriptor.source_revision,
        "benchmark-os-plugin-composition-adapter-durable-attribution-v1"
    );

    let mut drifted = output.config.clone();
    drifted
        .adapter_descriptor
        .as_mut()
        .expect("adapter identity should be present")
        .implementation_id = "replacement-adapter-v2".to_string();
    let error = drifted
        .validate(&output.inner)
        .expect_err("adapter identity drift must fail closed");
    assert!(error.to_string().contains("does not match adapter_id"));
}

#[test]
fn legacy_v1_config_without_projector_identity_remains_explicitly_unattributed() {
    let catalog = ExperimentPluginFactoryCatalog::metacognitive()
        .expect("metacognitive catalog should construct");
    let plugin = catalog
        .instantiate(METACOGNITIVE_EXPERIMENT_PLUGIN_ID)
        .expect("metacognitive plugin should instantiate");
    let output = PluginCompositionRunner::new(
        plugin,
        "legacy-projector-attribution-experiment",
        "legacy-projector-attribution-run",
        provenance("legacy-projector-attribution"),
    )
    .expect("generic runner should construct")
    .run()
    .expect("generic composition should run");

    let current_json = serialize_plugin_composition_config_json(&output.config)
        .expect("current config should serialize");
    let projector_json = serde_json::to_string(
        output
            .config
            .projector_descriptor()
            .expect("current config should retain projector identity"),
    )
    .expect("projector descriptor should serialize");
    let projector_field = format!(",\"projector_descriptor\":{projector_json}");
    assert!(current_json.contains(&projector_field));
    let adapter_json = serde_json::to_string(
        output
            .config
            .adapter_descriptor
            .as_ref()
            .expect("current config should retain adapter identity"),
    )
    .expect("adapter descriptor should serialize");
    let adapter_field = format!(",\"adapter_descriptor\":{adapter_json}");
    assert!(current_json.contains(&adapter_field));
    let legacy_json = current_json
        .replace(&projector_field, "")
        .replace(&adapter_field, "");
    let legacy = deserialize_plugin_composition_config_json(&legacy_json)
        .expect("v1 config without the additive field should remain readable");

    assert!(!legacy.has_durable_projector_attribution());
    assert!(legacy.projector_descriptor().is_none());
    assert!(legacy.adapter_descriptor.is_none());
    assert_eq!(
        serialize_plugin_composition_config_json(&legacy)
            .expect("legacy config should retain canonical serialization"),
        legacy_json
    );
    legacy
        .validate(&output.inner)
        .expect("legacy config should retain its existing semantic validation");
}

// State slice: benchmark-os-plugin-composition-identity-descriptor-binding-v1.
#[test]
fn runner_rejects_identity_plugin_descriptor_drift() {
    let catalog = ExperimentPluginFactoryCatalog::metacognitive()
        .expect("synthetic factory catalog should construct");
    let plugin = catalog
        .instantiate(METACOGNITIVE_EXPERIMENT_PLUGIN_ID)
        .expect("synthetic plugin should instantiate");
    let identity = PluginCompositionIdentity::new(
        "different-plugin-id",
        "descriptor-binding-experiment",
        "descriptor-binding-run",
    )
    .expect("test identity should be structurally valid");

    let error = match PluginCompositionRunner::new_with_identity(
        plugin,
        identity,
        provenance("descriptor-binding-drift"),
    ) {
        Ok(_) => panic!("identity and descriptor plugin ids must bind at the seam"),
        Err(error) => error,
    };
    assert!(error
        .to_string()
        .contains("plugin_composition.identity.plugin_id"));
}

#[test]
fn generic_runner_preserves_local_json_compatibility() {
    let catalog = ExperimentPluginFactoryCatalog::local_json(GeneratorConfig::baseline_fsm())
        .expect("local factory catalog should construct");
    let plugin = catalog
        .instantiate(zkbench_core::LOCAL_JSON_EXPERIMENT_PLUGIN_ID)
        .expect("local plugin should instantiate");
    let runner = PluginCompositionRunner::new(
        plugin,
        "generic-local-experiment",
        "generic-local-run",
        provenance("generic-local-composition"),
    )
    .expect("generic runner should construct for local plugin");
    let output = runner
        .run()
        .expect("generic runner should preserve local plugin composition");

    assert_eq!(
        output.inner.config.plugin_id,
        zkbench_core::LOCAL_JSON_EXPERIMENT_PLUGIN_ID
    );
    assert_eq!(output.config.bindings.len(), 9);
    assert!(validate_experiment_bundle(&output.inner).valid);
}

#[test]
fn generic_config_rejects_missing_binding_and_outer_digest_drift() {
    let catalog = ExperimentPluginFactoryCatalog::metacognitive()
        .expect("synthetic factory catalog should construct");
    let plugin = catalog
        .instantiate(METACOGNITIVE_EXPERIMENT_PLUGIN_ID)
        .expect("synthetic plugin should instantiate");
    let runner = PluginCompositionRunner::new(
        plugin,
        "generic-invalid-experiment",
        "generic-invalid-run",
        provenance("generic-invalid-composition"),
    )
    .expect("generic runner should construct");
    let output = runner.run().expect("generic composition should succeed");

    let mut missing = output.config.clone();
    missing.bindings.pop();
    let missing_error = missing
        .binding(zkbench_core::experiment_observability::ExperimentArtifactKind::Report)
        .expect_err("missing generated binding must fail closed");
    assert!(missing_error.to_string().contains("missing binding"));
    assert!(missing.validate(&output.inner).is_err());

    let mut duplicate = output.config.clone();
    duplicate.bindings.push(duplicate.bindings[0].clone());
    let duplicate_error = duplicate
        .binding(zkbench_core::experiment_observability::ExperimentArtifactKind::Config)
        .expect_err("duplicate generated bindings must fail closed");
    assert!(duplicate_error.to_string().contains("is duplicated"));
    assert!(duplicate.bindings_in_order().is_err());

    let mut missing_order = output.config.clone();
    missing_order.bindings.pop();
    assert!(missing_order.bindings_in_order().is_err());

    let mut permuted = output.config.clone();
    permuted.bindings.swap(1, 2);
    let permuted_error = permuted
        .validate(&output.inner)
        .expect_err("permuted bindings must fail canonical-order validation");
    assert!(permuted_error
        .to_string()
        .contains("canonical OuterKind::ALL order"));

    let task_binding = output
        .config
        .binding(zkbench_core::experiment_observability::ExperimentArtifactKind::Task)
        .expect("task binding should exist");
    assert_eq!(
        task_binding
            .source(zkbench_core::experiment::ExperimentArtifactKind::DataVersion)
            .expect("task source should exist")
            .inner_kind,
        zkbench_core::experiment::ExperimentArtifactKind::DataVersion
    );

    let mut duplicate_source = output.config.clone();
    let task_binding = duplicate_source
        .binding(zkbench_core::experiment_observability::ExperimentArtifactKind::Task)
        .expect("task binding should exist")
        .clone();
    let task_binding_mut = duplicate_source
        .bindings
        .iter_mut()
        .find(|binding| {
            binding.outer_kind
                == zkbench_core::experiment_observability::ExperimentArtifactKind::Task
        })
        .expect("task binding should exist");
    task_binding_mut.sources.push(
        task_binding
            .sources
            .first()
            .cloned()
            .expect("task binding should have one source"),
    );
    let duplicate_source_access_error = task_binding_mut
        .source(zkbench_core::experiment::ExperimentArtifactKind::DataVersion)
        .expect_err("duplicate inner source lookup must fail closed");
    assert!(duplicate_source_access_error
        .to_string()
        .contains("source for inner kind"));
    let duplicate_source_error = duplicate_source
        .validate(&output.inner)
        .expect_err("duplicate inner source kinds must fail closed");
    assert!(duplicate_source_error
        .to_string()
        .contains("inner source kind is duplicated"));

    let mut tampered_outer = output.outer.clone();
    tampered_outer.task.digest.hex_digest = "0".repeat(64);
    assert!(output
        .config
        .validate_against_outer(&output.inner, &tampered_outer)
        .is_err());
}

#[test]
fn generic_config_rejects_missing_and_duplicate_inner_artifacts_before_projection() {
    let catalog = ExperimentPluginFactoryCatalog::metacognitive()
        .expect("synthetic factory catalog should construct");
    let plugin = catalog
        .instantiate(METACOGNITIVE_EXPERIMENT_PLUGIN_ID)
        .expect("synthetic plugin should instantiate");
    let runner = PluginCompositionRunner::new(
        plugin,
        "generic-artifact-access-experiment",
        "generic-artifact-access-run",
        provenance("generic-artifact-access"),
    )
    .expect("generic runner should construct");
    let output = runner.run().expect("generic composition should succeed");

    let mut missing_inner = output.inner.clone();
    missing_inner.artifacts.retain(|artifact| {
        artifact.kind != zkbench_core::experiment::ExperimentArtifactKind::DataVersion
    });
    let mut missing_config = output.config.clone();
    missing_config.inner_bundle_digest = compute_experiment_bundle_digest(&missing_inner)
        .expect("missing-artifact bundle digest should compute");
    assert!(missing_config.validate(&missing_inner).is_err());

    let mut duplicate_inner = output.inner.clone();
    duplicate_inner
        .artifacts
        .push(duplicate_inner.artifacts[0].clone());
    let mut duplicate_config = output.config;
    duplicate_config.inner_bundle_digest = compute_experiment_bundle_digest(&duplicate_inner)
        .expect("duplicate-artifact bundle digest should compute");
    assert!(duplicate_config.validate(&duplicate_inner).is_err());
}
